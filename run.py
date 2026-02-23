"""
How to run:
From project root, run:
    python run.py --target "Company Name"
"""

import subprocess
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src import config
from src.data_loader import load_companies, load_shareholders
from src.analytics import calculate_company_metrics, create_investor_mix, summarise_analytics
from src.charts import create_charts
from src.tables import create_all_tables


def parse_args():
    p = argparse.ArgumentParser(description="IB Analytics & Chart Generator")
    p.add_argument("--target", required=True,
                   help="Company name to analyse — must match 'Company Name' in the CSV exactly")
    return p.parse_args()


def banner(msg: str) -> None:
    print("\n" + "═" * 64)
    print(f"  {msg}")
    print("═" * 64)


def run_preprocessing(target: str) -> None:
    """
    Call data_pre_processing.py with cwd=data/ so its get_paths() resolves correctly.
    Streams output live and exits if the script fails.
    """
    data_dir      = config.BASE_DIR / "data"
    preprocess_script = config.BASE_DIR / "src" / "data_pre_processing.py"

    cmd = [sys.executable, str(preprocess_script), "--company", target]
    result = subprocess.run(cmd, cwd=str(data_dir))

    if result.returncode != 0:
        print(f"\n  [run] Preprocessing failed (exit {result.returncode}) — aborting.")
        sys.exit(result.returncode)


def main():
    args = parse_args()
    t0   = time.time()

    banner(f"IB Analytics & Chart Generator  |  {args.target}")

    # ── 1. Preprocessing ──────────────────────────────────────────────────────
    banner("Step 1 / 5  |  Preprocessing raw data")
    run_preprocessing(args.target)

    # ── 2. Load ───────────────────────────────────────────────────────────────
    banner("Step 2 / 5  |  Loading enriched data")
    companies    = load_companies(config.COMPANY_CSV)
    shareholders = load_shareholders(config.SHAREHOLDER_CSV)

    # ── 3. Analytics ──────────────────────────────────────────────────────────
    banner("Step 3 / 5  |  Running analytics")
    metrics      = calculate_company_metrics(companies, args.target)
    style_matrix = create_investor_mix(shareholders)
    summary      = summarise_analytics(metrics, style_matrix, args.target)

    target = summary["target"]
    meds   = summary["peer_medians"]
    sh     = summary["target_sh"]
    ticker     = summary["target_ticker"]
    output_dir = config.OUTPUT_DIR / ticker
    print(f"\n  {args.target} snapshot:")
    print(f"    Ticker         : {summary['target_ticker']}")
    print(f"    Market Cap     : ESD {target['Market_cap_million'] / 1000:,.0f}bn")
    print(f"    EV/EBITDA      : {target['EV/EBITDA']:.1f}x  (peer median {meds['ev_ebitda']:.1f}x)")
    print(f"    3yr TSR        : {target['tsr_pct']:.1f}%  (peer median {meds['tsr_pct']:.1f}%)")
    print(f"    EBITDA Margin  : {target['ebitda_margin_fy1']:.1f}%  (peer median {meds['ebitda_margin_fy1']:.1f}%)")
    print(f"    ND/EBITDA      : {target['nd_ebitda_fy1']:.1f}x  (peer median {meds['nd_ebitda_fy1']:.1f}x)")
    print(f"    Growth OS      : {sh.get('Growth', 0) + sh.get('Aggressive Growth', 0) + sh.get('GARP', 0):.1f}%")
    print(f"    Index OS       : {sh.get('Index', 0):.1f}%")

    # ── 4. Tables ─────────────────────────────────────────────────────────────
    banner("Step 4 / 5  |  Building summary tables")
    create_all_tables(summary, shareholders, output_dir)

    # ── 5. Charts ─────────────────────────────────────────────────────────────
    banner("Step 5 / 5  |  Rendering charts")
    chart_paths = create_charts(summary, output_dir)

    elapsed = time.time() - t0
    banner(f"Complete  |  {elapsed:.1f}s")
    print(f"  {len(chart_paths)} charts saved to {output_dir}")
    print()


if __name__ == "__main__":
    main()
