"""
Simple entry point to run the main analysis pipeline.
"""

from src.analysis.flow_analysis import run_flow_analysis
from src.analysis.prediction import run_predictions


def main():
    print("=" * 60)
    print("  Urban Mobility Flow Analysis - Pipeline")
    print("=" * 60)

    year = input("\nEnter year for flow analysis (e.g. 2021): ").strip()
    if year.isdigit():
        run_flow_analysis(int(year), output_path=f"maps/fluxo_social_SP_{year}.html")
    else:
        print("Invalid year. Skipping flow analysis.")

    run = input("\nRun regression forecasts? (y/n): ").strip().lower()
    if run == "y":
        run_predictions()


if __name__ == "__main__":
    main()
