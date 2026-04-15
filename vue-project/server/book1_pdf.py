"""
Build a one-page PDF summary of book1.csv: text summary + monthly revenue bar chart (latest year).
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from book1_revenue import default_book1_csv_path, latest_year_and_monthly_revenue


def build_book1_pdf_bytes(csv_path: str | None = None) -> tuple[bytes | None, str]:
    """
    Returns (pdf_bytes, error_message). On success error_message is "".
    """
    path = csv_path or default_book1_csv_path()
    info: dict[str, Any] = latest_year_and_monthly_revenue(path)
    if info.get("error"):
        return None, str(info["error"])

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    year = int(info["year"])
    monthly_raw = info.get("monthly") or {}
    values = [float(monthly_raw.get(str(m), 0.0)) for m in range(1, 13)]
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    ledger_rng = info.get("ledger_date_range") or {}
    y_rng = info.get("date_range_in_year") or {}
    best = info.get("best_month") or {}
    worst = info.get("worst_month") or {}

    lines = [
        f"Café ledger summary (book1) — calendar year {year}",
        f"Total revenue for {year}: ${info.get('year_total_revenue', 0):,.2f} USD ({info.get('row_count_in_year', 0)} days in ledger).",
        f"Full ledger span: {ledger_rng.get('min', 'n/a')} to {ledger_rng.get('max', 'n/a')} ({info.get('row_count_ledger', 0)} rows).",
        f"Highest month: {best.get('label') or 'n/a'} (${best.get('revenue_usd', 0):,.2f}); "
        f"lowest nonzero month: {worst.get('label') or 'n/a'} (${worst.get('revenue_usd', 0):,.2f}).",
        f"Daily revenue column: price (USD). Chart: monthly revenue for {year}.",
    ]
    if y_rng:
        lines.insert(2, f"Dates in {year}: {y_rng.get('min')} to {y_rng.get('max')}.")

    buf = BytesIO()
    fig = plt.figure(figsize=(8.5, 11))
    fig.subplots_adjust(left=0.1, right=0.95, top=0.92, bottom=0.08)
    ax_text = fig.add_axes([0.1, 0.52, 0.85, 0.38])
    ax_text.axis("off")
    ax_text.text(
        0,
        1,
        "\n".join(lines),
        transform=ax_text.transAxes,
        fontsize=10,
        verticalalignment="top",
        fontfamily="sans-serif",
        wrap=True,
    )

    ax_bar = fig.add_axes([0.12, 0.12, 0.76, 0.36])
    bars = ax_bar.bar(labels, values, color="#2c5282", edgecolor="#1a365d", linewidth=0.5)
    ax_bar.set_ylabel("Revenue (USD)")
    ax_bar.set_title(f"Monthly revenue — {year}")
    ax_bar.tick_params(axis="x", rotation=45)
    ymax = max(values) if values else 1.0
    ax_bar.set_ylim(0, ymax * 1.12 if ymax > 0 else 1.0)
    for b, v in zip(bars, values):
        if v > 0:
            ax_bar.text(
                b.get_x() + b.get_width() / 2,
                b.get_height(),
                f"{v:,.0f}",
                ha="center",
                va="bottom",
                fontsize=7,
            )

    fig.savefig(buf, format="pdf", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read(), ""


def default_report_filename() -> str:
    return "cafe-book1-report.pdf"
