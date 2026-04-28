"""
Flask API for the Vue chat: POST /api/chat → OpenAI with tool calling (key stays on the server only).
POST /api/chat/feedback — receive assistant reply text and thumbs up/down (no OpenAI call).

Local dev:
  cd server
  python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
  pip install -r requirements.txt
  export OPENAI_API_KEY=sk-...
  python app.py

Vue (Vite) should proxy /api → http://127.0.0.1:5000 (see vite.config.js), or set
VITE_UBUNTU_SERVER=http://127.0.0.1:5000 in .env for direct requests.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials as firebase_credentials, firestore as firebase_firestore
from flask import Flask, Response, jsonify, request
from openai import OpenAI

from book1_pdf import build_book1_pdf_bytes, default_report_filename
from book1_revenue import (
    describe_book1_ledger,
    latest_year_and_monthly_revenue,
    sum_revenue as sum_revenue_from_ledger,
)

app = Flask(__name__)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Firebase Admin — required for per-user token-cost tracking
# ---------------------------------------------------------------------------
_fb_db = None
try:
    _cred_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
    if _cred_path:
        firebase_admin.initialize_app(firebase_credentials.Certificate(_cred_path))
    else:
        firebase_admin.initialize_app()
    _fb_db = firebase_firestore.client()
except Exception as _fb_err:
    print(f"[WARN] Firebase Admin not initialized: {_fb_err}")
    print("[WARN] Token-cost tracking will be disabled.")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOOL_ROUNDS = 10


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# Caps assistant verbosity (including tool-call JSON). Raise only if tool calls fail or replies truncate.
OPENAI_MAX_COMPLETION_TOKENS = _env_int("OPENAI_MAX_COMPLETION_TOKENS", 256)
OPENAI_TEMPERATURE = _env_float("OPENAI_TEMPERATURE", 0.2)

# Per-token dollar rates (defaults: gpt-4o-mini pricing)
INPUT_COST_PER_TOKEN = _env_float("INPUT_COST_PER_TOKEN", 0.00000015)
OUTPUT_COST_PER_TOKEN = _env_float("OUTPUT_COST_PER_TOKEN", 0.0000006)
TOKEN_COST_LIMIT = _env_float("TOKEN_COST_LIMIT", 1.0)


def _verify_firebase_token(req) -> str | None:
    """Return the uid from a valid Firebase ID token, or None."""
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    try:
        decoded = firebase_auth.verify_id_token(auth_header[7:])
        return decoded.get("uid")
    except Exception:
        return None


def _get_token_cost(uid: str) -> float:
    doc = _fb_db.collection("users").document(uid).get()
    if doc.exists:
        return float(doc.to_dict().get("token_cost", 0.0))
    return 0.0


def _add_token_cost(uid: str, cost: float) -> None:
    ref = _fb_db.collection("users").document(uid)
    ref.set({"token_cost": firebase_firestore.firestore.Increment(cost)}, merge=True)


def _calculate_cost(usage) -> float:
    if not usage:
        return 0.0
    prompt = getattr(usage, "prompt_tokens", 0) or 0
    completion = getattr(usage, "completion_tokens", 0) or 0
    return prompt * INPUT_COST_PER_TOKEN + completion * OUTPUT_COST_PER_TOKEN

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a helpful assistant for café and small-business owners. "
        "OUTPUT RULES (strict): "
        "1. Reply with ONLY the direct answer — a single number with units, or one very short sentence (under 15 words). "
        "2. NEVER include formulas, LaTeX, displayed math, markdown equations, step-by-step work, bullet lists, "
        "preambles (e.g. 'To calculate', 'You can use', 'To determine'), or closing commentary. "
        "3. Do not restate the question. Do not explain methodology. "
        "4. If a question cannot be answered because information is missing, say ONLY what is missing in one short sentence "
        "(e.g. 'I need the average revenue per customer to answer that.'). Never show how the user could calculate it themselves. "
        "5. If the user explicitly asks for explanation or steps, then you may elaborate — otherwise do not. "
        "TOOL RULES (strict): "
        "Never guess or compute from memory — always call a tool when data is involved. "
        "Daily revenue is stored in a ledger CSV as column `price` (USD), with dates in column `date` (M/D/YY). "
        "For total revenue by month, year, or date range → call `sum_revenue`. "
        "For questions about variables, typical ranges, correlations, what drives profit, "
        "or how many customers appeared on days near a revenue level → call `describe_book1_ledger` "
        "(set `revenue_target_usd` for what-if daily revenue questions). "
        "When the user asks for a report, PDF, download, or summary of the data → immediately call "
        "`generate_book1_pdf_report` with no arguments. This tool takes NO parameters and produces a "
        "ready-made PDF with monthly/yearly revenue summaries and a bar chart for the latest year. "
        "NEVER ask the user for details, format, or preferences before calling it — just call it. "
        "Treat correlations as observational, not causal."
    ),
}

SUM_REVENUE_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "sum_revenue",
        "description": (
            "Sum daily revenue (USD) from the café ledger for a calendar year, or for one month within that year. "
            "Use this for questions like total revenue in March 2025 or total for 2024."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "year": {
                    "type": "integer",
                    "description": "Four-digit calendar year, e.g. 2025",
                },
                "month": {
                    "type": "integer",
                    "description": "Optional month 1–12. Omit to sum every day in that year present in the ledger.",
                },
            },
            "required": ["year"],
        },
    },
}

DESCRIBE_BOOK1_LEDGER_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "describe_book1_ledger",
        "description": (
            "Return all ledger variables (CSV columns) with short definitions, per-column numeric summaries, "
            "Pearson correlations between each metric and daily revenue (`price`), and optional example days "
            "closest to a target daily revenue (useful for questions like which fields matter or how many "
            "customers occurred near $X revenue)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "include_correlations": {
                    "type": "boolean",
                    "description": "If true (default), include correlations with daily revenue (`price`).",
                },
                "revenue_target_usd": {
                    "type": "number",
                    "description": (
                        "Optional daily revenue in USD. When set, includes a few real days from the ledger "
                        "closest to this revenue so you can compare customer counts and other metrics."
                    ),
                },
            },
            "required": [],
        },
    },
}

GENERATE_BOOK1_PDF_REPORT_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "generate_book1_pdf_report",
        "description": (
            "Generate and deliver a pre-built PDF report of the café ledger. The report always includes: "
            "a text summary of monthly and yearly revenues, and a bar chart of monthly revenue for the "
            "latest calendar year. Takes NO parameters — call it immediately whenever the user mentions "
            "report, PDF, download, summary, or export. Do NOT ask the user for any extra details first."
        ),
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

TOOLS: list[dict[str, Any]] = [
    SUM_REVENUE_TOOL,
    DESCRIBE_BOOK1_LEDGER_TOOL,
    GENERATE_BOOK1_PDF_REPORT_TOOL,
]


def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


@app.after_request
def apply_cors(response):
    return _cors(response)


def _assistant_message_to_dict(msg) -> dict[str, Any]:
    d: dict[str, Any] = {"role": "assistant", "content": msg.content}
    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": getattr(tc, "type", None) or "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls
        ]
    return d


def _run_sum_revenue(arguments: dict[str, Any]) -> dict[str, Any]:
    year = arguments.get("year")
    month = arguments.get("month")
    if year is None:
        return {"error": "Missing required parameter: year."}
    try:
        y = int(year)
    except (TypeError, ValueError):
        return {"error": "year must be an integer."}
    m: int | None
    if month is None:
        m = None
    else:
        try:
            m = int(month)
        except (TypeError, ValueError):
            return {"error": "month must be an integer when provided."}
    return sum_revenue_from_ledger(y, m)


def _run_describe_book1_ledger(arguments: dict[str, Any]) -> dict[str, Any]:
    raw_inc = arguments.get("include_correlations", True)
    if isinstance(raw_inc, str):
        include_correlations = raw_inc.strip().lower() in ("1", "true", "yes")
    else:
        include_correlations = bool(raw_inc)

    tgt = arguments.get("revenue_target_usd")
    revenue_target: float | None
    if tgt is None or tgt == "":
        revenue_target = None
    else:
        try:
            revenue_target = float(tgt)
        except (TypeError, ValueError):
            return {"error": "revenue_target_usd must be a number when provided."}

    return describe_book1_ledger(
        include_correlations=include_correlations,
        revenue_target_usd=revenue_target,
    )


def _run_generate_book1_pdf_report(arguments: dict[str, Any]) -> dict[str, Any]:
    _ = arguments
    info = latest_year_and_monthly_revenue()
    if info.get("error"):
        return {"ready": False, "error": info["error"]}
    return {
        "ready": True,
        "year": info["year"],
        "currency": "USD",
        "download_path": "/api/reports/book1.pdf",
        "summary": {
            "year_total_revenue_usd": info.get("year_total_revenue"),
            "row_count_in_year": info.get("row_count_in_year"),
            "row_count_ledger": info.get("row_count_ledger"),
            "ledger_date_range": info.get("ledger_date_range"),
            "date_range_in_year": info.get("date_range_in_year"),
            "monthly_totals_usd": info.get("monthly"),
            "best_month": info.get("best_month"),
            "worst_month": info.get("worst_month"),
        },
    }


def _dispatch_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "sum_revenue":
        return _run_sum_revenue(arguments)
    if name == "describe_book1_ledger":
        return _run_describe_book1_ledger(arguments)
    if name == "generate_book1_pdf_report":
        return _run_generate_book1_pdf_report(arguments)
    return {"error": f"Unknown tool: {name}."}


@app.route("/api/reports/book1.pdf", methods=["GET", "OPTIONS"])
def book1_report_pdf():
    if request.method == "OPTIONS":
        return ("", 204)
    raw, err = build_book1_pdf_bytes()
    if raw is None:
        return jsonify({"error": err or "Could not build PDF."}), 500
    fn = default_report_filename()
    return Response(
        raw,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )


@app.route("/api/chat", methods=["OPTIONS"])
def chat_options():
    return ("", 204)


@app.route("/api/chat/feedback", methods=["OPTIONS"])
def chat_feedback_options():
    return ("", 204)


@app.route("/api/chat/feedback", methods=["POST"])
def chat_feedback():
    """Store or log user thumbs up/down for an assistant message (does not call OpenAI)."""
    uid: str | None = None
    if _fb_db is not None:
        uid = _verify_firebase_token(request)
        if uid is None:
            return jsonify({"error": "Authentication required."}), 401

    body = request.get_json(silent=True) or {}
    text = body.get("assistant_response")
    fb = body.get("feedback")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "assistant_response must be a non-empty string."}), 400
    if fb not in ("up", "down"):
        return jsonify({"error": 'feedback must be "up" or "down".'}), 400

    mid = body.get("message_id")
    message_id: int | None
    if isinstance(mid, int):
        message_id = mid
    elif mid is not None:
        try:
            message_id = int(mid)
        except (TypeError, ValueError):
            message_id = None
    else:
        message_id = None

    record: dict[str, Any] = {
        "assistant_response": text,
        "feedback": fb,
        "message_id": message_id,
        "uid": uid,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    log_payload = {**record, "assistant_response": text[:500] + ("…" if len(text) > 500 else "")}
    logger.info("chat_feedback %s", json.dumps(log_payload, default=str))

    if _fb_db is not None and uid is not None:
        try:
            doc: dict[str, Any] = {
                "assistant_response": text,
                "feedback": fb,
                "created_at": datetime.now(timezone.utc),
            }
            if message_id is not None:
                doc["message_id"] = message_id
            _fb_db.collection("chat_feedback").add(doc)
        except Exception as e:
            logger.exception("chat_feedback Firestore write failed")
            return jsonify({"error": f"Could not store feedback: {e!s}"}), 500

    return jsonify({"ok": True})


@app.route("/api/chat", methods=["POST"])
def chat():
    if not OPENAI_API_KEY:
        return jsonify({"error": "OPENAI_API_KEY is not set on the server."}), 500

    # --- Auth & token-cost gate ---
    uid: str | None = None
    current_cost = 0.0
    if _fb_db is not None:
        uid = _verify_firebase_token(request)
        if uid is None:
            return jsonify({"error": "Authentication required."}), 401
        current_cost = _get_token_cost(uid)
        if current_cost >= TOKEN_COST_LIMIT:
            return jsonify({
                "error": "Token cost limit exceeded.",
                "token_cost": current_cost,
                "token_cost_limit": TOKEN_COST_LIMIT,
                "limit_exceeded": True,
            }), 403

    body = request.get_json(silent=True) or {}
    messages_in = body.get("messages")
    if not isinstance(messages_in, list):
        return jsonify({"error": "Expected JSON body with a messages array."}), 400

    for m in messages_in:
        if not isinstance(m, dict):
            return jsonify({"error": "Each message must be an object."}), 400
        if m.get("role") not in ("user", "assistant"):
            return jsonify({"error": "Message role must be user or assistant."}), 400
        if not isinstance(m.get("content"), str):
            return jsonify({"error": "Message content must be a string."}), 400

    messages: list[dict[str, Any]] = [SYSTEM_MESSAGE, *messages_in]
    client = OpenAI(api_key=OPENAI_API_KEY)
    offer_pdf_download = False
    total_cost = 0.0

    for _ in range(MAX_TOOL_ROUNDS):
        try:
            completion = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=TOOLS,
                temperature=OPENAI_TEMPERATURE,
                max_completion_tokens=OPENAI_MAX_COMPLETION_TOKENS,
                timeout=120.0,
            )
        except Exception as e:
            return jsonify({"error": f"OpenAI error: {e!s}"}), 502

        total_cost += _calculate_cost(completion.usage)
        choice = completion.choices[0]
        msg = choice.message
        finish = choice.finish_reason

        if finish == "tool_calls" or (msg.tool_calls and len(msg.tool_calls) > 0):
            messages.append(_assistant_message_to_dict(msg))
            for tc in msg.tool_calls or []:
                fn = tc.function
                try:
                    args = json.loads(fn.arguments) if fn.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                if not isinstance(args, dict):
                    args = {}
                result = _dispatch_tool(fn.name, args)
                if fn.name == "generate_book1_pdf_report" and isinstance(result, dict) and result.get("ready"):
                    offer_pdf_download = True
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
            continue

        # --- Persist accumulated cost ---
        if uid is not None and _fb_db is not None and total_cost > 0:
            _add_token_cost(uid, total_cost)

        text = msg.content
        if text is None or text == "":
            return jsonify({"error": "Model returned no text response."}), 502
        payload: dict[str, Any] = {"reply": text, "token_cost": current_cost + total_cost}
        if offer_pdf_download:
            payload["downloads"] = [
                {"url": "/api/reports/book1.pdf", "filename": default_report_filename()},
            ]
        return jsonify(payload)

    return jsonify({"error": "Too many tool rounds; aborting."}), 502


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
