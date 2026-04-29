"""
Flask API for the Vue chat: POST /api/chat → OpenAI with tool calling (key stays on the server only).
POST /api/chat/feedback → append JSON lines to user_responses.log.

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
import os
import base64
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
    top_daily_revenue as top_daily_revenue_from_ledger,
)

app = Flask(__name__)

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
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-2026-03-05")
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


def _get_user_entries(uid: str) -> list[dict[str, Any]]:
    if _fb_db is None:
        return []
    docs = _fb_db.collection("users").document(uid).collection("entries").stream()
    out: list[dict[str, Any]] = []
    for doc in docs:
        data = doc.to_dict() or {}
        if isinstance(data, dict):
            out.append(data)
    return out


def _calculate_cost(usage) -> float:
    if not usage:
        return 0.0
    prompt = getattr(usage, "prompt_tokens", 0) or 0
    completion = getattr(usage, "completion_tokens", 0) or 0
    return prompt * INPUT_COST_PER_TOKEN + completion * OUTPUT_COST_PER_TOKEN


_USER_RESPONSES_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_responses.log")


def _log_chat_feedback(
    assistant_response: str,
    feedback: str,
    message_id: str | int | None,
) -> None:
    line = json.dumps(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "assistant_response": assistant_response,
            "feedback": feedback,
            "message_id": message_id,
        },
        ensure_ascii=False,
    )
    with open(_USER_RESPONSES_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

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
        "Daily revenue comes from the authenticated user's ledger entries where `price` is USD and `date` is the day. "
        "For total revenue by month, year, or date range → call `sum_revenue`. "
        "For which calendar day had the highest revenue, best day, or top revenue days → call `top_daily_revenue` "
        "(optional `year` and `month` for e.g. best day in February 2025 or in all of 2024; do not infer the date from column max alone). "
        "For questions about variables, typical ranges, correlations, what drives profit, "
        "or how many customers appeared on days near a revenue level → call `describe_book1_ledger` "
        "(set `revenue_target_usd` for what-if daily revenue questions). "
        "When the user asks for a report, PDF, download, or summary of the data → immediately call "
        "`generate_book1_pdf_report` with no arguments. This tool takes NO parameters and produces a "
        "ready-made PDF with monthly/yearly revenue summaries and one page per calendar year in the data. "
        "The server response includes downloadable PDF bytes directly from /api/chat; no separate report endpoint is required. "
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

TOP_DAILY_REVENUE_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "top_daily_revenue",
        "description": (
            "List the highest-revenue days in the ledger with their calendar dates and amounts (column `price`). "
            "Use for: best day, which day made the most money, top N revenue days, record sales day. "
            "Pass `year` to restrict to that calendar year (e.g. best day in 2024). Pass `year` and `month` (1–12) "
            "for a single month (e.g. best day in February 2025). Omit both for best days across the whole ledger."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "How many days to return, highest first (default 5, max 50).",
                },
                "year": {
                    "type": "integer",
                    "description": (
                        "Optional four-digit calendar year. When set, only days in that year are considered. "
                        "Required when `month` is set."
                    ),
                },
                "month": {
                    "type": "integer",
                    "description": "Optional month 1–12; must be used together with `year`.",
                },
            },
            "required": [],
        },
    },
}

DESCRIBE_BOOK1_LEDGER_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "describe_book1_ledger",
        "description": (
            "Return all ledger variables (user entry fields) with short definitions, per-column numeric summaries, "
            "Pearson correlations between each metric and daily revenue (`price`), and optional example days "
            "closest to a target daily revenue (useful for questions like which fields matter or how many "
            "customers occurred near $X revenue). Does not identify which date had the highest revenue — use "
            "top_daily_revenue for that."
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
            "a text summary of monthly and yearly revenues, with one report page per calendar year in the "
            "ledger and a monthly bar chart for each year. The PDF bytes are returned in the /api/chat response payload. "
            "Takes NO parameters — call it immediately whenever the user mentions "
            "report, PDF, download, summary, or export. Do NOT ask the user for any extra details first."
        ),
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

TOOLS: list[dict[str, Any]] = [
    SUM_REVENUE_TOOL,
    TOP_DAILY_REVENUE_TOOL,
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
    return sum_revenue_from_ledger(y, m, entries=arguments.get("_entries"))


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
        entries=arguments.get("_entries"),
    )


def _run_top_daily_revenue(arguments: dict[str, Any]) -> dict[str, Any]:
    raw_lim = arguments.get("limit")
    if raw_lim is None or raw_lim == "":
        lim = 5
    else:
        try:
            lim = int(raw_lim)
        except (TypeError, ValueError):
            return {"error": "limit must be an integer when provided."}

    raw_y = arguments.get("year")
    year: int | None
    if raw_y is None or raw_y == "":
        year = None
    else:
        try:
            year = int(raw_y)
        except (TypeError, ValueError):
            return {"error": "year must be an integer when provided."}

    raw_m = arguments.get("month")
    month: int | None
    if raw_m is None or raw_m == "":
        month = None
    else:
        try:
            month = int(raw_m)
        except (TypeError, ValueError):
            return {"error": "month must be an integer when provided."}

    return top_daily_revenue_from_ledger(lim, year=year, month=month, entries=arguments.get("_entries"))


def _run_generate_book1_pdf_report(arguments: dict[str, Any]) -> dict[str, Any]:
    entries = arguments.get("_entries")
    if isinstance(entries, list):
        print(f"[REPORT] Tool source: Firebase entries ({len(entries)} rows)")
    else:
        print("[REPORT] Tool source: default CSV path")
    if not isinstance(entries, list) or len(entries) == 0:
        return {"ready": False, "error": "No Firebase entries found for this user."}

    years: dict[int, dict[str, Any]] = {}
    ledger_min: str | None = None
    ledger_max: str | None = None
    for row in entries:
        if not isinstance(row, dict):
            continue
        raw_date = row.get("date")
        d = None
        if raw_date is not None:
            raw = str(raw_date).strip()
            for fmt in ("%m/%d/%y", "%Y-%m-%d", "%m/%d/%Y"):
                try:
                    d = datetime.strptime(raw, fmt).date()
                    break
                except ValueError:
                    pass
            if d is None:
                try:
                    d = datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
                except ValueError:
                    d = None
        if d is None:
            continue
        try:
            revenue = float(row.get("price"))
        except (TypeError, ValueError):
            continue

        d_iso = d.isoformat()
        if ledger_min is None or d_iso < ledger_min:
            ledger_min = d_iso
        if ledger_max is None or d_iso > ledger_max:
            ledger_max = d_iso

        bucket = years.setdefault(
            d.year,
            {
                "year": d.year,
                "currency": "USD",
                "monthly_totals_usd": {str(m): 0.0 for m in range(1, 13)},
                "year_total_revenue_usd": 0.0,
                "row_count_in_year": 0,
                "date_range_in_year": {"min": d_iso, "max": d_iso},
            },
        )
        bucket["monthly_totals_usd"][str(d.month)] += revenue
        bucket["year_total_revenue_usd"] += revenue
        bucket["row_count_in_year"] += 1
        if d_iso < bucket["date_range_in_year"]["min"]:
            bucket["date_range_in_year"]["min"] = d_iso
        if d_iso > bucket["date_range_in_year"]["max"]:
            bucket["date_range_in_year"]["max"] = d_iso

    if not years:
        return {"ready": False, "error": "No rows with valid dates and revenue in Firebase entries."}

    month_labels = (
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    )
    year_items: list[dict[str, Any]] = []
    for y in sorted(years.keys()):
        item = years[y]
        monthly_pairs = [(m, float(item["monthly_totals_usd"][str(m)])) for m in range(1, 13)]
        nonzero = [(m, v) for m, v in monthly_pairs if v > 0]
        if nonzero:
            best_m, best_v = max(nonzero, key=lambda t: t[1])
            worst_m, worst_v = min(nonzero, key=lambda t: t[1])
        else:
            best_m = worst_m = None
            best_v = worst_v = 0.0

        item["monthly_totals_usd"] = {str(m): round(v, 2) for m, v in monthly_pairs}
        item["year_total_revenue_usd"] = round(float(item["year_total_revenue_usd"]), 2)
        item["best_month"] = {
            "month": best_m,
            "label": month_labels[best_m - 1] if best_m else None,
            "revenue_usd": round(best_v, 2),
        }
        item["worst_month"] = {
            "month": worst_m,
            "label": month_labels[worst_m - 1] if worst_m else None,
            "revenue_usd": round(worst_v, 2),
        }
        year_items.append(item)

    print(f"[REPORT] Years in dataset: {[item['year'] for item in year_items]}")

    latest_year = year_items[-1]
    return {
        "ready": True,
        "year": latest_year["year"],
        "currency": "USD",
        "download_path": "/api/reports/book1.pdf",
        "row_count_ledger": len(entries),
        "ledger_date_range": {"min": ledger_min, "max": ledger_max},
        "years": year_items,
        "summary": {"years_count": len(year_items), "latest_year": latest_year},
    }


def _dispatch_tool(name: str, arguments: dict[str, Any], entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    args = dict(arguments)
    args["_entries"] = entries or []
    if name == "sum_revenue":
        return _run_sum_revenue(args)
    if name == "top_daily_revenue":
        return _run_top_daily_revenue(args)
    if name == "describe_book1_ledger":
        return _run_describe_book1_ledger(args)
    if name == "generate_book1_pdf_report":
        return _run_generate_book1_pdf_report(args)
    return {"error": f"Unknown tool: {name}."}


@app.route("/api/reports/book1.pdf", methods=["GET", "OPTIONS"])
def book1_report_pdf():
    if request.method == "OPTIONS":
        return ("", 204)
    if _fb_db is None:
        return jsonify({"error": "Firebase is not configured on the server."}), 503
    uid = _verify_firebase_token(request)
    if uid is None:
        return jsonify({"error": "Authentication required."}), 401
    user_entries = _get_user_entries(uid)
    print(f"[REPORT] Download source: Firebase entries ({len(user_entries)} rows)")
    raw, err = build_book1_pdf_bytes(entries=user_entries)
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
    body = request.get_json(silent=True) or {}
    assistant_response = body.get("assistant_response")
    feedback = body.get("feedback")
    message_id = body.get("message_id")

    if not isinstance(assistant_response, str) or not assistant_response.strip():
        return jsonify({"error": "assistant_response must be a non-empty string."}), 400
    if feedback not in ("up", "down"):
        return jsonify({"error": 'feedback must be "up" or "down".'}), 400
    if message_id is not None and not isinstance(message_id, (str, int)):
        return jsonify({"error": "message_id must be a string or number if provided."}), 400

    _log_chat_feedback(assistant_response.strip(), feedback, message_id)
    return jsonify({"ok": True})


@app.route("/api/chat", methods=["POST"])
def chat():
    if not OPENAI_API_KEY:
        return jsonify({"error": "OPENAI_API_KEY is not set on the server."}), 500

    # --- Auth & token-cost gate ---
    uid: str | None = None
    user_entries: list[dict[str, Any]] = []
    current_cost = 0.0
    if _fb_db is not None:
        uid = _verify_firebase_token(request)
        if uid is None:
            return jsonify({"error": "Authentication required."}), 401
        user_entries = _get_user_entries(uid)
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
    inline_downloads: list[dict[str, Any]] = []
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
                result = _dispatch_tool(fn.name, args, entries=user_entries)
                if fn.name == "generate_book1_pdf_report" and isinstance(result, dict) and result.get("ready"):
                    pdf_bytes, pdf_err = build_book1_pdf_bytes(entries=user_entries)
                    if pdf_bytes is None:
                        result = {
                            "ready": False,
                            "error": pdf_err or "Could not build PDF.",
                        }
                    else:
                        inline_downloads.append(
                            {
                                "filename": default_report_filename(),
                                "mime_type": "application/pdf",
                                "content_base64": base64.b64encode(pdf_bytes).decode("ascii"),
                            }
                        )
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
        updated_cost = current_cost + total_cost
        print(
            f"[INFO] Token cost request=${total_cost:.6f}, total=${updated_cost:.6f}, "
            f"user={uid or 'anonymous'}"
        )
        payload: dict[str, Any] = {"reply": text, "token_cost": updated_cost}
        if inline_downloads:
            payload["downloads"] = inline_downloads
        return jsonify(payload)

    return jsonify({"error": "Too many tool rounds; aborting."}), 502


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
