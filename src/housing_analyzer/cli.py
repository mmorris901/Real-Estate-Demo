"""Command-line entry point: build the dataset and print a market summary."""

from __future__ import annotations

import argparse
import logging

from housing_analyzer import analysis, pipeline


def _fmt_pct(x: float) -> str:
    return f"{x:+.1%}"


def print_summary(years_back: int = 5, top_n: int = 100) -> None:
    df = pipeline.load()
    snap = analysis.latest_snapshot(df, years_back=years_back, top_n=top_n)
    latest = df["date"].max().strftime("%B %Y")
    growth_col = f"growth_{years_back}y"

    print(f"\nU.S. housing snapshot - {latest} - largest {top_n} metros\n")

    sections = [
        (f"Fastest {years_back}-year price growth", growth_col, False, _fmt_pct),
        ("Biggest price drops (last 12 months)", "yoy_change", True, _fmt_pct),
        ("Highest price-to-rent (renting is relatively cheaper)", "price_to_rent", False,
         lambda x: f"{x:.1f}"),
        ("Lowest estimated monthly payment", "monthly_payment", True, lambda x: f"${x:,.0f}"),
    ]
    for title, col, asc, fmt in sections:
        print(title)
        for i, row in analysis.rank(snap, col, n=5, ascending=asc).iterrows():
            print(f"  {i + 1}. {row['region']:<40} {fmt(row[col])}")
        print()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Analyze U.S. metro housing markets.")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Download data and build the processed dataset")
    build.add_argument("--force", action="store_true", help="Re-download even if cached")

    summary = sub.add_parser("summary", help="Print a market summary")
    summary.add_argument("--years", type=int, default=5, help="Growth lookback in years")
    summary.add_argument("--top", type=int, default=100, help="Number of largest metros")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.command == "build":
        pipeline.run(force_download=args.force)
    elif args.command == "summary":
        print_summary(years_back=args.years, top_n=args.top)


if __name__ == "__main__":
    main()
