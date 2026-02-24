import pandas as pd
import numpy as np

from .config import PEER_SECTOR, ALL_INVESTOR_STYLES

def calculate_company_metrics(companies, target_company):
    """Enrich raw company data with calculated metrics like EBITDA margin, revenue growth, and Net Debt / EBITDA."""
    # checking if target company specified as a runtime parameter is present in the company data
    if target_company not in companies["Company Name"].values:
        raise ValueError(
            f"'{target_company}' not found in company data. "
            f"Check --target matches a 'Company Name' value exactly."
        )
    # copy to avoid mutating original DataFrame as we'll be adding calculated columns
    df = companies.copy()
    # calculate EBITDA margin for each fiscal year as a new column, handling division by zero
    for yr in ("FY1", "FY2", "FY3"):
        df[f"ebitda_margin_{yr.lower()}"] = (
            df[f"EBITDA_{yr}"] / df[f"Sales_{yr}"].replace(0, np.nan) * 100
        )
    # for each fiscal year, calculate Net Debt / EBITDA as a new column, handling division by zero
    for yr in ("FY1", "FY2", "FY3"):
        df[f"nd_ebitda_{yr.lower()}"] = (df[f"Net_Debt_{yr}"] / df[f"EBITDA_{yr}"].replace(0, np.nan))
    df["tsr_pct"] = df["3yr TSR"] * 100
    df["is_target"] = df["Company Name"] == target_company
    return df


def create_investor_mix(shareholders):
    """Pivot shareholder data to a company & investor-style matrix of summed %OS."""
    # create a pivot table with companies as rows, investor styles as columns, and summed %OS as values
    pivot = (
        shareholders
        .groupby(["Company Name", "Inv Style"])["%OS"]
        .sum()
        .unstack(fill_value=0.0)
    )

    # add metrics for growth/value/yield/index-oriented OS by summing relevant investor styles
    pivot["growth_oriented"] = (
        pivot.get("Growth", 0) + pivot.get("Aggressive Growth", 0) + pivot.get("GARP", 0)
    )
    pivot["value_oriented"] = pivot.get("Value", 0) + pivot.get("Deep Value", 0)
    pivot["yield_os"] = pivot.get("Yield", 0)
    pivot["index_os"] = pivot.get("Index", 0)
    pivot["identified_os"] = pivot[ALL_INVESTOR_STYLES].sum(axis=1)
    return pivot


def get_target_profile(metrics, target_company):
    """Get company profile for the target company from the metrics DataFrames"""
    # compare company name in metrics df to runtime param.
    row = metrics[metrics["Company Name"] == target_company]
    if row.empty:
        raise ValueError(f"'{target_company}' not found in metrics DataFrame.")
    return row.iloc[0]


def get_sector_peers(metrics, sector=PEER_SECTOR):
    """Get all companies that are in the same sector as the target company, including target company"""
    return metrics[metrics["Sector"] == sector].copy()


def get_large_cap_peers(metrics, n=10, exclude_target=True):
    """Get the top N companies by market cap in the same sector as the target company,
    optionally excluding the target company itself."""
    # get sector peers from metrics df
    peers = get_sector_peers(metrics)
    # optionally exclude the target company before ranking
    if exclude_target:
        peers = peers[~peers["is_target"]]
    # return the top N by market cap
    return peers.nlargest(n, "Market_cap_million").copy()


def get_investor_style_summary(style_matrix, company_names):
    """Returns investor breakdown for a list of companies, such as large cap peers and the target company"""
    result = {}
    # iterate over the list of company names and extract their investor style breakdown from the style matrix
    for name in company_names:
        row = style_matrix.loc[name] if name in style_matrix.index \
              else pd.Series({s: 0.0 for s in ALL_INVESTOR_STYLES})
        result[name] = {s: float(row.get(s, 0.0)) for s in ALL_INVESTOR_STYLES}
    # return a dict where keys are company names and values are dicts of investor style breakdowns
    return result


def summarise_analytics(metrics, style_matrix, target_company):
    """Roll up everything the chart modules need into one dict."""
    target = get_target_profile(metrics, target_company)
    sector_peers = get_sector_peers(metrics)
    hc_peers_excl = sector_peers[~sector_peers["is_target"]].copy()
    lc_peers = get_large_cap_peers(metrics)
    lc_names = lc_peers["Company Name"].tolist()
    style_data = get_investor_style_summary(style_matrix, lc_names + [target_company])
    target_sh = style_data[target_company]

    # derive average investor style breakdown across the large cap peer group by averaging the %OS for each style
    peer_sh_avg = {
        style: float(np.mean([style_data[n][style] for n in lc_names if n in style_data]) or 0.0)
        for style in ALL_INVESTOR_STYLES
    }

    # calculate median values for key financial metrics across the sector peer group
    # (excluding the target company) to provide benchmarks for comparison in the charts
    peer_medians = {
        "ev_ebitda": hc_peers_excl["EV/EBITDA"].median(),
        "tsr_pct": hc_peers_excl["tsr_pct"].median(),
        "ebitda_margin_fy1": hc_peers_excl["ebitda_margin_fy1"].median(),
        "ebitda_margin_fy2": hc_peers_excl["ebitda_margin_fy2"].median(),
        "ebitda_margin_fy3": hc_peers_excl["ebitda_margin_fy3"].median(),
        "nd_ebitda_fy1": hc_peers_excl["nd_ebitda_fy1"].median(),
        "market_cap": hc_peers_excl["Market_cap_million"].median(),
        "growth_oriented": (style_matrix.loc[style_matrix.index.isin(lc_names), "growth_oriented"].median()
            if "growth_oriented" in style_matrix.columns else 0.0)
    }

    # key financial metrics which can be used by chart fns to generate visualizations
    return {
        "target": target,
        "target_company": target_company,
        "target_ticker": target["Ticker"],
        "aurexa": target,
        "aurexa_sh": target_sh,
        "sector_peers": sector_peers,
        "hc_peers_excl": hc_peers_excl,
        "large_cap_peers": lc_peers,
        "style_matrix": style_matrix,
        "target_sh": target_sh,
        "peer_sh_avg": peer_sh_avg,
        "peer_medians": peer_medians
    }