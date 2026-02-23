from pathlib import Path
import numpy as np
import pandas as pd

def _fmt_m(v):
    return f"{v:,.0f}" if pd.notna(v) else "n/a"

def _fmt_pct(v, dp=1):
    return f"{v:.{dp}f}%" if pd.notna(v) else "n/a"

def _fmt_x(v, dp=1):
    return f"{v:.{dp}f}x" if pd.notna(v) else "n/a"

def _fmt_ratio(v, dp=2):
    return f"{v:.{dp}f}" if pd.notna(v) else "n/a"

def _cagr(v_start, v_end, periods=2):
    if pd.isna(v_start) or pd.isna(v_end) or v_start <= 0:
        return np.nan
    return ((v_end / v_start) ** (1 / periods) - 1) * 100

def _vs_peers(target_val, peer_median, lower_is_better=False):
    if pd.isna(target_val) or pd.isna(peer_median) or peer_median == 0:
        return "n/a"
    rel = (target_val - peer_median) / abs(peer_median)
    if abs(rel) < 0.05:
        return "In-line"
    above = rel > 0
    if lower_is_better:
        return "Below" if above else "Above"
    return "Above" if above else "Below"

def _write(df: pd.DataFrame, path: Path) -> Path:
    df.to_csv(path, index=False)
    print(f"  [tables] Saved  {path.name}")
    return path

# 01_financial_performance.csv
def create_financial_performance_table(summary: dict) -> pd.DataFrame:
    t = summary["target"]
    tc = summary["target_company"]
    sec = summary["hc_peers_excl"].copy()
    lc = summary["large_cap_peers"].copy()

    def med(df, col):
        return df[col].median() if col in df.columns else np.nan

    for df in (sec, lc):
        df["_sales_cagr"] = df.apply(lambda r: _cagr(r["Sales_FY1"],  r["Sales_FY3"]), axis=1)
        df["_ebitda_cagr"] = df.apply(lambda r: _cagr(r["EBITDA_FY1"], r["EBITDA_FY3"]), axis=1)
        df["_ebitda_m_fy3"] = df["EBITDA_FY3"] / df["Sales_FY3"].replace(0, np.nan) * 100
        df["_nd_ebitda_fy3"] = df["Net_Debt_FY3"] / df["EBITDA_FY3"].replace(0, np.nan)
        df["_div_payout"] = df["DPS_FY3"] / df["EPS"].replace(0, np.nan)

    t_sales_cagr = _cagr(t["Sales_FY1"], t["Sales_FY3"])
    t_ebitda_cagr = _cagr(t["EBITDA_FY1"], t["EBITDA_FY3"])
    t_ebitda_m_fy3 = t["EBITDA_FY3"] / t["Sales_FY3"] * 100 if t["Sales_FY3"]  else np.nan
    t_nd_ebitda_fy3 = t["Net_Debt_FY3"] / t["EBITDA_FY3"] if t["EBITDA_FY3"] else np.nan
    t_div_payout = t["DPS_FY3"] / t["EPS"] if t["EPS"] else np.nan

    rows = [
        ("Sales FY1 (m)", _fmt_m(t["Sales_FY1"]), _fmt_m(med(sec,"Sales_FY1")), _fmt_m(med(lc,"Sales_FY1"))),
        ("Sales FY3 (m)", _fmt_m(t["Sales_FY3"]), _fmt_m(med(sec,"Sales_FY3")), _fmt_m(med(lc,"Sales_FY3"))),
        ("Sales CAGR FY1-FY3", _fmt_pct(t_sales_cagr), _fmt_pct(med(sec,"_sales_cagr")), _fmt_pct(med(lc,"_sales_cagr"))),
        ("EBITDA margin FY3", _fmt_pct(t_ebitda_m_fy3), _fmt_pct(med(sec,"_ebitda_m_fy3")), _fmt_pct(med(lc,"_ebitda_m_fy3"))),
        ("EBITDA CAGR FY1-FY3", _fmt_pct(t_ebitda_cagr), _fmt_pct(med(sec,"_ebitda_cagr")), _fmt_pct(med(lc,"_ebitda_cagr"))),
        ("Net debt / EBITDA FY3", _fmt_x(t_nd_ebitda_fy3), _fmt_x(med(sec,"_nd_ebitda_fy3")), _fmt_x(med(lc,"_nd_ebitda_fy3"))),
        ("Dividend payout (DPS/EPS)", _fmt_ratio(t_div_payout), _fmt_ratio(med(sec,"_div_payout")), _fmt_ratio(med(lc,"_div_payout"))),
        ("3-year TSR", _fmt_pct(t["tsr_pct"]), _fmt_pct(med(sec,"tsr_pct")), _fmt_pct(med(lc,"tsr_pct"))),
        ("EV/EBITDA", _fmt_x(t["EV/EBITDA"]), _fmt_x(med(sec,"EV/EBITDA")), _fmt_x(med(lc,"EV/EBITDA"))),
    ]

    return pd.DataFrame(rows, columns=["Metric", tc, "Sector median", "Large-cap peer median"])


# 02_valuation_vs_delivery.csv
def create_valuation_vs_delivery_table(summary: dict) -> pd.DataFrame:
    t = summary["target"]
    sec = summary["hc_peers_excl"].copy()

    sec["_sales_cagr"] = sec.apply(lambda r: _cagr(r["Sales_FY1"], r["Sales_FY3"]), axis=1)
    sec["_ebitda_m_fy3"] = sec["EBITDA_FY3"] / sec["Sales_FY3"].replace(0, np.nan) * 100
    sec["_nd_ebitda_fy3"] = sec["Net_Debt_FY3"] / sec["EBITDA_FY3"].replace(0, np.nan)

    t_sales_cagr = _cagr(t["Sales_FY1"], t["Sales_FY3"])
    t_ebitda_m_fy3 = t["EBITDA_FY3"] / t["Sales_FY3"] * 100 if t["Sales_FY3"] else np.nan
    t_nd_ebitda_fy3 = t["Net_Debt_FY3"] / t["EBITDA_FY3"] if t["EBITDA_FY3"] else np.nan

    rows = [
        ("Sales CAGR FY1-FY3", _vs_peers(t_sales_cagr, sec["_sales_cagr"].median()), _fmt_pct(t_sales_cagr)),
        ("EBITDA margin FY3", _vs_peers(t_ebitda_m_fy3, sec["_ebitda_m_fy3"].median()), _fmt_pct(t_ebitda_m_fy3)),
        ("Net debt / EBITDA FY3 (lower is better)", _vs_peers(t_nd_ebitda_fy3, sec["_nd_ebitda_fy3"].median(), lower_is_better=True), _fmt_x(t_nd_ebitda_fy3)),
        ("3-year TSR", _vs_peers(t["tsr_pct"], sec["tsr_pct"].median()), _fmt_pct(t["tsr_pct"])),
        ("EV/EBITDA", _vs_peers(t["EV/EBITDA"], sec["EV/EBITDA"].median()), _fmt_x(t["EV/EBITDA"])),
    ]

    return pd.DataFrame(rows, columns=["Metric", "Target position vs Sector peers", "Target value"])



# 03_shareholder_base.csv
def create_shareholder_base_table(summary: dict, shareholders: pd.DataFrame) -> pd.DataFrame:
    tc = summary["target_company"]
    target_sh = summary["target_sh"]
    style_matrix = summary["style_matrix"]
    sector_names = summary["hc_peers_excl"]["Company Name"].tolist()

    target_rows = shareholders[shareholders["Company Name"] == tc].copy()
    target_rows["%OS"] = pd.to_numeric(target_rows["%OS"], errors="coerce")
    identified_os = target_rows["%OS"].sum()

    def _share(val):
        return (val / identified_os * 100) if identified_os > 0 else np.nan

    t_growth = target_sh.get("Growth", 0) + target_sh.get("Aggressive Growth", 0) + target_sh.get("GARP", 0)
    t_index = target_sh.get("Index", 0)
    t_value = target_sh.get("Value", 0) + target_sh.get("Deep Value", 0)
    t_yield = target_sh.get("Yield", 0)
    t_top10 = target_rows.nlargest(10, "%OS")["%OS"].sum()

    sm = style_matrix.loc[[n for n in sector_names if n in style_matrix.index]]

    def _sec_med(cols):
        return sm[cols].sum(axis=1).median() if not sm.empty else np.nan

    sec_holder_counts = (
        shareholders[shareholders["Company Name"].isin(sector_names)]
        .groupby("Company Name")["Name of Investor"].nunique()
    )

    def _top10_conc(company):
        rows = shareholders[shareholders["Company Name"] == company].copy()
        rows["%OS"] = pd.to_numeric(rows["%OS"], errors="coerce")
        tot = rows["%OS"].sum()
        return (rows.nlargest(10,"%OS")["%OS"].sum() / tot * 100) if tot > 0 else np.nan

    sec_top10 = pd.Series({n: _top10_conc(n) for n in sector_names})

    rows = [
        ("Growth-oriented (Growth + Aggressive + GARP)", _fmt_pct(_share(t_growth)), _fmt_pct(_sec_med(["Growth", "Aggressive Growth", "GARP"]))),
        ("Index / passive", _fmt_pct(_share(t_index)), _fmt_pct(_sec_med(["Index"]))),
        ("Value-oriented (Value + Deep Value)", _fmt_pct(_share(t_value)), _fmt_pct(_sec_med(["Value", "Deep Value"]))),
        ("Yield", _fmt_pct(_share(t_yield)),  _fmt_pct(_sec_med(["Yield"]))),
        ("Number of holders (covered)", str(target_rows["Name of Investor"].nunique()), _fmt_ratio(sec_holder_counts.median(), dp=0)),
        ("Top-10 concentration (share of covered)", _fmt_pct(_share(t_top10)), _fmt_pct(sec_top10.median())),
    ]

    return pd.DataFrame(rows, columns=["Investor base metric", "Target (share of covered)", "Sector median"])


# function to create all tables and save to output dir
def create_all_tables(summary: dict, shareholders: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[tables] Building summary tables → {output_dir}")

    paths = {
        "financial_performance": _write(
            create_financial_performance_table(summary),
            output_dir / "01_financial_performance.csv",
        ),
        "valuation_vs_delivery": _write(
            create_valuation_vs_delivery_table(summary),
            output_dir / "02_valuation_vs_delivery.csv",
        ),
        "shareholder_base": _write(
            create_shareholder_base_table(summary, shareholders),
            output_dir / "03_shareholder_base.csv",
        )
    }

    print(f"[tables] {len(paths)} tables saved\n")
    return paths