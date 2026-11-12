"""Build the analysis-ready month-end panel from cached raw source files."""

from __future__ import annotations

from term_premium.data import build_monthly_panel, save_monthly_panel


def main() -> None:
    panel = build_monthly_panel()
    output_path = save_monthly_panel(panel)

    print(f"Saved: {output_path}")
    print(f"Rows: {len(panel):,}")
    print(f"Columns: {len(panel.columns):,}")
    print(f"First month: {panel.index.min()}")
    print(f"Last month: {panel.index.max()}")
    excluded = panel.attrs.get("excluded_partial_months", {})
    if excluded:
        print("\nExcluded incomplete final-month observations:")
        for series_id, month in sorted(excluded.items()):
            print(f"{series_id}: {month} (snapshot retrieved during that month)")
    print("\nMissing observations by variable:")
    print(panel.isna().sum().to_string())


if __name__ == "__main__":
    main()
