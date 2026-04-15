"""
Load café ledger CSV: sum revenue by period and describe columns/stats for analysis.
"""

from __future__ import annotations

import csv
import math
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

COLUMN_DESCRIPTIONS: dict[str, str] = {
    "date": "Calendar date for the row (M/D/YY).",
    "price": "Daily revenue in USD (outcome to maximize in this dataset).",
    "customers": "Customer count for the day.",
    "avg_order_val": "Average order value (revenue per customer proxy).",
    "hours": "Operating or staffed hours (context-dependent).",
    "employees": "Employees scheduled or on duty.",
    "spend": "Spend (e.g. costs) for the day in USD.",
    "foot_traffic": "Foot traffic count (volume indicator).",
}


def default_book1_csv_path() -> str:
    env = os.environ.get("BOOK1_CSV_PATH")
    if env:
        return os.path.abspath(env)
    server_dir = Path(__file__).resolve().parent
    return str((server_dir.parent / "src" / "data" / "book1.csv").resolve())


def _parse_us_date(s: str) -> date | None:
    try:
        return datetime.strptime(s.strip(), "%m/%d/%y").date()
    except ValueError:
        return None


def sum_revenue(year: int, month: int | None = None, csv_path: str | None = None) -> dict[str, Any]:
    """
    Sum `price` for rows whose `date` falls in `year`, and if `month` is set, that month only.
    Returns a JSON-serializable dict (for OpenAI tool output).
    """
    path = csv_path or default_book1_csv_path()

    if month is not None and (month < 1 or month > 12):
        return {"error": "month must be between 1 and 12 when provided."}

    if not os.path.isfile(path):
        return {
            "error": f"Ledger file not found: {path}. Set BOOK1_CSV_PATH or add src/data/book1.csv.",
        }

    total = 0.0
    row_count = 0
    dates_matched: list[date] = []

    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fnames = reader.fieldnames or []
            if not fnames or "date" not in fnames or "price" not in fnames:
                return {"error": "CSV must have 'date' and 'price' columns."}
            for row in reader:
                raw_date = row.get("date") or ""
                raw_price = row.get("price") or ""
                d = _parse_us_date(raw_date)
                if d is None:
                    continue
                if d.year != year:
                    continue
                if month is not None and d.month != month:
                    continue
                try:
                    p = float(raw_price)
                except ValueError:
                    continue
                total += p
                row_count += 1
                dates_matched.append(d)
    except OSError as e:
        return {"error": f"Could not read ledger: {e}"}

    if row_count == 0:
        period = f"{year}" if month is None else f"{year}-{month:02d}"
        return {
            "sum": 0.0,
            "currency": "USD",
            "row_count": 0,
            "period": period,
            "date_range": None,
            "note": f"No rows matched period {period} in the ledger.",
        }

    mn, mx = min(dates_matched), max(dates_matched)
    period = f"{year}" if month is None else f"{year}-{month:02d}"

    return {
        "sum": round(total, 2),
        "currency": "USD",
        "row_count": row_count,
        "period": period,
        "date_range": {"min": mn.isoformat(), "max": mx.isoformat()},
    }


_MONTH_NAMES = (
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


def latest_year_and_monthly_revenue(csv_path: str | None = None) -> dict[str, Any]:
    """
    Find the latest calendar year present in the ledger and sum daily `price` by month (1–12) for that year.
    Includes summary fields for reports and API responses.
    """
    path = csv_path or default_book1_csv_path()

    if not os.path.isfile(path):
        return {
            "error": f"Ledger file not found: {path}. Set BOOK1_CSV_PATH or add src/data/book1.csv.",
        }

    ledger_rows = 0
    date_vals: list[date] = []
    parsed: list[tuple[date, float]] = []

    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fnames = reader.fieldnames or []
            if not fnames or "date" not in fnames or "price" not in fnames:
                return {"error": "CSV must have 'date' and 'price' columns."}
            for row in reader:
                ledger_rows += 1
                raw_date = row.get("date") or ""
                raw_price = row.get("price") or ""
                d = _parse_us_date(raw_date)
                if d is None:
                    continue
                date_vals.append(d)
                try:
                    p = float(raw_price)
                except ValueError:
                    continue
                parsed.append((d, p))
    except OSError as e:
        return {"error": f"Could not read ledger: {e}"}

    if not parsed:
        return {
            "error": "No rows with valid dates and revenue in the ledger.",
            "row_count": ledger_rows,
        }

    latest_year = max(d.year for d, _ in parsed)
    monthly: dict[int, float] = {m: 0.0 for m in range(1, 13)}
    dates_in_year: list[date] = []

    for d, p in parsed:
        if d.year != latest_year:
            continue
        monthly[d.month] = monthly.get(d.month, 0.0) + p
        dates_in_year.append(d)

    year_total = sum(monthly.values())
    month_amounts = [(m, monthly[m]) for m in range(1, 13)]
    nonzero = [(m, v) for m, v in month_amounts if v > 0]
    if nonzero:
        best_m, best_v = max(nonzero, key=lambda t: t[1])
        worst_m, worst_v = min(nonzero, key=lambda t: t[1])
    else:
        best_m = worst_m = None
        best_v = worst_v = 0.0

    ledger_range = None
    if date_vals:
        mn, mx = min(date_vals), max(date_vals)
        ledger_range = {"min": mn.isoformat(), "max": mx.isoformat()}

    date_range_year = None
    if dates_in_year:
        mn_y, mx_y = min(dates_in_year), max(dates_in_year)
        date_range_year = {"min": mn_y.isoformat(), "max": mx_y.isoformat()}

    return {
        "year": latest_year,
        "currency": "USD",
        "monthly": {str(m): round(monthly[m], 2) for m in range(1, 13)},
        "year_total_revenue": round(year_total, 2),
        "row_count_in_year": len(dates_in_year),
        "row_count_ledger": ledger_rows,
        "date_range_in_year": date_range_year,
        "ledger_date_range": ledger_range,
        "best_month": {"month": best_m, "label": _MONTH_NAMES[best_m - 1] if best_m else None, "revenue_usd": round(best_v, 2)},
        "worst_month": {"month": worst_m, "label": _MONTH_NAMES[worst_m - 1] if worst_m else None, "revenue_usd": round(worst_v, 2)},
    }


def _pearson_r(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n != len(ys) or n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx < 1e-18 or vy < 1e-18:
        return None
    cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    return cov / math.sqrt(vx * vy)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _stdev(xs: list[float]) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    m = _mean(xs)
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return math.sqrt(v)


def describe_book1_ledger(
    include_correlations: bool = True,
    revenue_target_usd: float | None = None,
    csv_path: str | None = None,
) -> dict[str, Any]:
    """
    Profile the ledger: variable names, numeric summaries, correlations with daily revenue,
    and optional rows closest to a target daily revenue (for what-if style questions).
    """
    path = csv_path or default_book1_csv_path()

    if not os.path.isfile(path):
        return {
            "error": f"Ledger file not found: {path}. Set BOOK1_CSV_PATH or add src/data/book1.csv.",
        }

    rows: list[dict[str, str]] = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fnames = reader.fieldnames or []
            if not fnames:
                return {"error": "CSV has no header row."}
            for row in reader:
                rows.append(dict(row))
    except OSError as e:
        return {"error": f"Could not read ledger: {e}"}

    n = len(rows)
    if n == 0:
        return {"row_count": 0, "note": "Ledger file has no data rows.", "columns": []}

    dates: list[date | None] = []
    numeric_keys: list[str] = []
    for key in fnames:
        if key == "date":
            continue
        ok = 0
        for row in rows:
            try:
                float((row.get(key) or "").strip())
                ok += 1
            except (TypeError, ValueError):
                pass
        if ok >= max(1, (n + 1) // 2):
            numeric_keys.append(key)

    for row in rows:
        raw = (row.get("date") or "").strip()
        dates.append(_parse_us_date(raw))

    date_vals = [d for d in dates if d is not None]
    date_range = None
    if date_vals:
        mn, mx = min(date_vals), max(date_vals)
        date_range = {"min": mn.isoformat(), "max": mx.isoformat()}

    series: dict[str, list[float]] = {k: [] for k in numeric_keys}
    for row in rows:
        for key in numeric_keys:
            raw = (row.get(key) or "").strip()
            try:
                v = float(raw)
            except (TypeError, ValueError):
                v = float("nan")
            series[key].append(v)

    date_col_meta = {
        "name": "date",
        "description": COLUMN_DESCRIPTIONS["date"],
        "role": "time_index",
        "date_range_in_data": date_range,
    }
    columns_out = [date_col_meta]
    for key in numeric_keys:
        vals = [x for x in series[key] if not math.isnan(x)]
        col = {
            "name": key,
            "description": COLUMN_DESCRIPTIONS.get(key, "Numeric column from the ledger."),
            "role": "outcome" if key == "price" else "numeric_metric",
        }
        if vals:
            sd = _stdev(vals)
            col["stats"] = {
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
                "mean": round(_mean(vals), 4),
                "stdev": round(sd, 4) if sd is not None else None,
                "n_non_missing": len(vals),
            }
        columns_out.append(col)

    out: dict[str, Any] = {
        "row_count": n,
        "columns": columns_out,
        "hint": (
            "Use stats and correlations for qualitative tradeoffs; this is observational data, not proof of causation. "
            "For revenue totals by month/year, use sum_revenue."
        ),
    }

    price_series = series.get("price", [])
    if include_correlations and "price" in numeric_keys and price_series:
        corr_with_price: list[dict[str, Any]] = []
        for key in numeric_keys:
            if key == "price":
                continue
            xs: list[float] = []
            ys: list[float] = []
            for i in range(n):
                p = price_series[i]
                o = series[key][i]
                if math.isnan(p) or math.isnan(o):
                    continue
                xs.append(p)
                ys.append(o)
            r = _pearson_r(xs, ys)
            if r is not None:
                corr_with_price.append(
                    {"variable": key, "pearson_r_with_price": round(r, 4), "paired_rows": len(xs)}
                )
        corr_with_price.sort(key=lambda x: abs(x["pearson_r_with_price"]), reverse=True)
        out["correlations_with_daily_revenue_price"] = corr_with_price

    if revenue_target_usd is not None and "price" in numeric_keys:
        target = float(revenue_target_usd)
        scored: list[tuple[float, int]] = []
        for i in range(n):
            p = price_series[i]
            if math.isnan(p):
                continue
            scored.append((abs(p - target), i))
        scored.sort(key=lambda t: t[0])
        examples: list[dict[str, Any]] = []
        int_like = {"customers", "employees", "foot_traffic", "hours"}
        for _, i in scored[:5]:
            row = rows[i]
            ex: dict[str, Any] = {"date": (row.get("date") or "").strip()}
            for k in numeric_keys:
                v = series[k][i]
                if math.isnan(v):
                    continue
                if k in int_like:
                    ex[k] = int(round(v))
                else:
                    ex[k] = round(v, 2) if k == "price" else round(v, 4)
            examples.append(ex)
        out["examples_closest_to_revenue_target_usd"] = {
            "target": round(target, 2),
            "rows": examples,
            "note": "Days with daily revenue closest to the target; compare customer counts and other metrics.",
        }

    return out
