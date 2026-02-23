from pathlib import Path
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import (CHART_DPI, NAVY, MID, CHART_BACKGROUND, GREEN, BLUE,
                     GREY, DARK_BLUE, LIGHT_BLUE, STYLE_COLOURS, ALL_INVESTOR_STYLES)


plt.rcParams.update({
    "figure.facecolor": CHART_BACKGROUND,
    "axes.facecolor": CHART_BACKGROUND,
    "axes.edgecolor": MID,
    "axes.labelcolor": NAVY,
    "axes.titlecolor": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "text.color": NAVY,
    "grid.color": MID,
    "grid.alpha": 0.25,
    "legend.facecolor" : CHART_BACKGROUND,
    "legend.edgecolor" : MID,
    "legend.labelcolor" : NAVY,
    "font.family" : "DejaVu Serif"
})


def _save(fig: plt.Figure, filename: str, output_dir: Path) -> Path:
    path = output_dir / filename
    fig.savefig(path, dpi=CHART_DPI, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [charts] Saved  {path.name}")
    return path


def _spine_style(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(MID)
    ax.spines["left"].set_color(MID)


def _legend(ax: plt.Axes, **kwargs) -> None:
    ax.legend(**{"fontsize": 8, "facecolor": CHART_BACKGROUND,
                 "edgecolor": MID, "labelcolor": NAVY, **kwargs})


def _annotate_bar(ax, bar, fmt="{:.0f}", color=NAVY, offset=4):
    h = bar.get_height()
    ax.annotate(
        fmt.format(h),
        xy=(bar.get_x() + bar.get_width() / 2, h),
        xytext=(0, offset), textcoords="offset points",
        ha="center", color=color, fontsize=8,
    )

# 01_FINANCIAL_PERFORMANCE.CSV
def chart_tsr_waterfall(summary: dict, output_dir: Path) -> Path:
    target_company = summary["target_company"]
    target_ticker  = summary["target_ticker"]

    all_df = pd.concat([
        summary["large_cap_peers"],
        summary["sector_peers"][summary["sector_peers"]["Company Name"] == target_company],
    ]).sort_values("tsr_pct")

    colours = [
        GREEN if r["Company Name"] == target_company
        else (BLUE if r["tsr_pct"] >= 0 else DARK_BLUE)
        for _, r in all_df.iterrows()
    ]
    labels = [
        target_ticker if r["Company Name"] == target_company else r["Ticker"]
        for _, r in all_df.iterrows()
    ]

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor(CHART_BACKGROUND)
    ax.set_facecolor(CHART_BACKGROUND)

    ax.bar(range(len(all_df)), all_df["tsr_pct"], color=colours, edgecolor="none", width=0.72)
    ax.axhline(0, color=MID, lw=0.8, linestyle="--", zorder=0)

    peer_med = summary["peer_medians"]["tsr_pct"]
    ax.axhline(peer_med, color=NAVY, lw=1.2, linestyle=":", alpha=0.7,
               label=f"Peer Median  {peer_med:.1f}%")

    aurex_idx = list(all_df["Company Name"]).index(target_company)
    aurex_tsr = all_df.iloc[aurex_idx]["tsr_pct"]
    ax.annotate(
        f"{target_ticker}\n{aurex_tsr:.1f}%",
        xy=(aurex_idx, aurex_tsr), xytext=(aurex_idx + 2.5, aurex_tsr - 25),
        color=NAVY, fontsize=8, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=NAVY, lw=1),
    )

    ax.set_xticks(range(len(all_df)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7.5)
    ax.set_ylabel("3-Year TSR (%)", fontsize=9)
    ax.set_title("3-Year Total Shareholder Return — Large-Cap Sector Peers", fontsize=11, pad=12)
    ax.legend(handles=[
        mpatches.Patch(color=GREEN,     label=target_company),
        mpatches.Patch(color=BLUE,      label="Positive TSR"),
        mpatches.Patch(color=DARK_BLUE, label="Negative TSR"),
    ], loc="upper left", fontsize=8, facecolor=CHART_BACKGROUND, edgecolor=MID, labelcolor=NAVY)

    _spine_style(ax)
    fig.tight_layout()
    return _save(fig, "01_tsr_waterfall.png", output_dir)


# 02_VALUATION_BUBBLE.PNG
def chart_valuation_bubble(summary: dict, output_dir: Path) -> Path:
    """EV/EBITDA (y) vs 3yr TSR (x); bubble size = market cap."""
    target_company = summary["target_company"]
    target_ticker  = summary["target_ticker"]

    df = summary["sector_peers"].dropna(subset=["EV/EBITDA", "tsr_pct"]).copy()
    df["mc_scaled"] = df["Market_cap_million"].clip(lower=1_000) / 2_000

    peers_df = df[df["Company Name"] != target_company]
    aurex_df = df[df["Company Name"] == target_company]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor(CHART_BACKGROUND)
    ax.set_facecolor(CHART_BACKGROUND)

    ax.scatter(peers_df["tsr_pct"], peers_df["EV/EBITDA"],
               s=peers_df["mc_scaled"], c=DARK_BLUE, alpha=0.55,
               edgecolors="none", label="Sector Peers")
    ax.scatter(aurex_df["tsr_pct"], aurex_df["EV/EBITDA"],
               s=aurex_df["mc_scaled"], c=LIGHT_BLUE,
               edgecolors=NAVY, linewidths=1.5, zorder=5, label=target_company)

    med_tsr = summary["peer_medians"]["tsr_pct"]
    med_ev  = summary["peer_medians"]["ev_ebitda"]
    ax.axhline(med_ev,  color=MID, lw=0.8, linestyle="--", alpha=0.6)
    ax.axvline(med_tsr, color=MID, lw=0.8, linestyle="--", alpha=0.6)
    ax.text(med_tsr + 1, ax.get_ylim()[1] * 0.97,
            f"Peer median TSR\n{med_tsr:.0f}%", color=MID, fontsize=7, va="top")

    ax.annotate(
        target_ticker,
        xy=(aurex_df.iloc[0]["tsr_pct"], aurex_df.iloc[0]["EV/EBITDA"]),
        xytext=(-50, 32), textcoords="offset points",
        color=DARK_BLUE, fontsize=9, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=LIGHT_BLUE, lw=1),
    )

    ax.set_xlabel("3-Year TSR (%)", fontsize=9)
    ax.set_ylabel("EV / EBITDA (x)", fontsize=9)
    ax.set_title(
        "Valuation vs. Total Shareholder Return — Sector Universe\n"
        "(bubble size proportional to market capitalisation)",
        fontsize=10, pad=10,
    )
    _spine_style(ax)
    _legend(ax, loc="upper right")
    fig.tight_layout()
    return _save(fig, "02_valuation_bubble.png", output_dir)

# 03_EBITDA_MARGINS.PNG
def chart_ebitda_margins(summary: dict, output_dir: Path) -> Path:
    target_company = summary["target_company"]
    target_ticker  = summary["target_ticker"]
    peers  = summary["hc_peers_excl"]
    aurexa = summary["aurexa"]
    meds   = summary["peer_medians"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.patch.set_facecolor(CHART_BACKGROUND)
    for ax in (ax1, ax2):
        ax.set_facecolor(CHART_BACKGROUND)
        _spine_style(ax)

    ax1.boxplot(
        peers["ebitda_margin_fy1"].dropna().values,
        patch_artist=True, widths=0.45,
        boxprops=dict(facecolor=DARK_BLUE, color=MID, alpha=0.8),
        whiskerprops=dict(color=MID),
        capprops=dict(color=MID),
        medianprops=dict(color=LIGHT_BLUE, lw=2.5),
        flierprops=dict(marker="o", color=MID, alpha=0.4, ms=4),
    )
    aurex_m = aurexa["ebitda_margin_fy1"]
    ax1.axhline(aurex_m, color=LIGHT_BLUE, lw=2, linestyle="--",
                label=f"{target_ticker} FY1  {aurex_m:.1f}%")
    ax1.set_xticklabels(["Sector Peers"])
    ax1.set_ylabel("EBITDA Margin (%)", fontsize=9)
    ax1.set_title("EBITDA Margin Distribution\nvs. Sector Peer Universe (FY1)", fontsize=9)
    _legend(ax1)

    yrs           = ["FY1", "FY2", "FY3"]
    aurex_margins = [aurexa["ebitda_margin_fy1"], aurexa["ebitda_margin_fy2"], aurexa["ebitda_margin_fy3"]]
    peer_meds     = [meds["ebitda_margin_fy1"],   meds["ebitda_margin_fy2"],   meds["ebitda_margin_fy3"]]

    ax2.plot(yrs, aurex_margins, color=LIGHT_BLUE, marker="o", lw=2.2, ms=8, label=target_company)
    ax2.plot(yrs, peer_meds,    color=DARK_BLUE,  marker="s", lw=1.5, linestyle="--", ms=6, label="Peer Median")
    ax2.fill_between(yrs, aurex_margins, alpha=0.1, color=LIGHT_BLUE)
    for yr, m in zip(yrs, aurex_margins):
        ax2.annotate(f"{m:.0f}%", xy=(yr, m), xytext=(0, 10),
                     textcoords="offset points", ha="center",
                     color=LIGHT_BLUE, fontsize=8.5, fontweight="bold")
    ax2.set_ylabel("EBITDA Margin (%)", fontsize=9)
    ax2.set_title("Margin Trajectory vs. Peer Median", fontsize=9)
    _legend(ax2)

    fig.suptitle("EBITDA Profitability Analysis", fontsize=12, color=NAVY, y=1.01, fontweight="bold")
    fig.tight_layout()
    return _save(fig, "03_ebitda_margins.png", output_dir)


# 04_REVENUE_BRIDGE.PNG
def chart_revenue_bridge(summary: dict, output_dir: Path) -> Path:
    target_company = summary["target_company"]
    aurexa = summary["aurexa"]

    yrs    = ["FY1", "FY2", "FY3"]
    rev    = [aurexa[f"Sales_{y}"]  / 1_000 for y in yrs]
    ebitda = [aurexa[f"EBITDA_{y}"] / 1_000 for y in yrs]

    x, w = np.arange(len(yrs)), 0.38

    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor(CHART_BACKGROUND)
    ax.set_facecolor(CHART_BACKGROUND)

    for bar in ax.bar(x - w / 2, rev,    w, color=DARK_BLUE,  alpha=0.9, label="Revenue (ESDbn)"):
        _annotate_bar(ax, bar, "{:.0f}", NAVY)
    for bar in ax.bar(x + w / 2, ebitda, w, color=LIGHT_BLUE, alpha=0.9, label="EBITDA (ESDbn)"):
        _annotate_bar(ax, bar, "{:.0f}", NAVY)

    ax.set_xticks(x)
    ax.set_xticklabels(yrs)
    ax.set_ylabel("ESD (bn)", fontsize=9)
    ax.set_title(f"{target_company} — Revenue & EBITDA FY1 to FY3 (ESDbn)", fontsize=11, pad=10)
    _spine_style(ax)
    _legend(ax)
    fig.tight_layout()
    return _save(fig, "04_revenue_bridge.png", output_dir)


# 05_INVESTOR_STYLE_COMPARE.PNG
def chart_investor_style_compare(summary: dict, output_dir: Path) -> Path:
    target_company = summary["target_company"]
    styles      = ["Index", "Growth", "Agg. Growth", "GARP", "Value", "Deep Value", "Yield"]
    target_vals = [summary["target_sh"].get(k, 0)   for k in ALL_INVESTOR_STYLES]
    peer_vals   = [summary["peer_sh_avg"].get(k, 0) for k in ALL_INVESTOR_STYLES]

    x, w = np.arange(len(styles)), 0.38

    fig, ax = plt.subplots(figsize=(11, 4.5))
    fig.patch.set_facecolor(CHART_BACKGROUND)
    ax.set_facecolor(CHART_BACKGROUND)

    ax.bar(x - w / 2, target_vals, w, color=DARK_BLUE,  alpha=0.9, label=target_company)
    ax.bar(x + w / 2, peer_vals,   w, color=LIGHT_BLUE, alpha=0.9, label="LC Peer Average")

    ax.set_xticks(x)
    ax.set_xticklabels(styles, fontsize=9)
    ax.set_ylabel("% Ownership (%OS)", fontsize=9)
    ax.set_title(
        f"Investor Style Breakdown: {target_company} vs. Large-Cap Sector Peer Average",
        fontsize=11, pad=10,
    )
    _spine_style(ax)
    _legend(ax)
    fig.tight_layout()
    return _save(fig, "05_investor_style_compare.png", output_dir)


# 06_DONUT_TARGET.PNG, 07_DONUT_PEERS.PNG
def chart_investor_donut(title: str, style_dict: dict, filename: str, output_dir: Path) -> Path:
    pairs = [
        (style, style_dict.get(style, 0), STYLE_COLOURS.get(style, GREY))
        for style in ALL_INVESTOR_STYLES
        if style_dict.get(style, 0) > 0.05
    ] or [("No Data", 100, MID)]

    labels = [p[0] for p in pairs]
    vals   = [p[1] for p in pairs]
    cols   = [p[2] for p in pairs]

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    fig.patch.set_facecolor(CHART_BACKGROUND)
    ax.set_facecolor(CHART_BACKGROUND)

    _, _, autotexts = ax.pie(
        vals, labels=None, colors=cols,
        autopct="%1.0f%%", startangle=90,
        wedgeprops=dict(width=0.58, edgecolor=CHART_BACKGROUND, linewidth=2.5),
        pctdistance=0.77,
    )
    for at in autotexts:
        at.set_color(NAVY)
        at.set_fontsize(7.5)
        at.set_fontweight("bold")

    ax.legend(labels, loc="lower center", ncol=2, fontsize=7.5,
              facecolor=CHART_BACKGROUND, edgecolor=MID, labelcolor=NAVY,
              bbox_to_anchor=(0.5, -0.18))
    ax.set_title(title, color=NAVY, fontsize=10, pad=8, fontweight="bold")
    # ax.text(0, 0, f"{sum(vals):.0f}%\nIdentified",
    #         ha="center", va="center", color=NAVY, fontsize=9, fontweight="bold")

    fig.tight_layout()
    return _save(fig, filename, output_dir)


# 08_DPS_TREND.PNG
def chart_dps_trend(summary: dict, output_dir: Path) -> Path:
    target_company = summary["target_company"]
    aurexa = summary["aurexa"]
    yrs    = ["FY1", "FY2", "FY3"]
    dps    = [aurexa[f"DPS_{y}"] for y in yrs]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    fig.patch.set_facecolor(CHART_BACKGROUND)
    ax.set_facecolor(CHART_BACKGROUND)

    bars = ax.bar(yrs, dps, color=[LIGHT_BLUE, DARK_BLUE, DARK_BLUE], alpha=0.9, width=0.45)
    for bar, d in zip(bars, dps):
        ax.annotate(f"{d:.2f}",
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 5), textcoords="offset points",
                    ha="center", color=NAVY, fontsize=10, fontweight="bold")

    pct_chg = ((dps[2] - dps[0]) / abs(dps[0])) * 100
    ax.annotate(
        f"{pct_chg:+.0f}% vs FY1",
        xy=(2, dps[2]), xytext=(1.3, max(dps) * 0.6),
        color=DARK_BLUE, fontsize=10, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=DARK_BLUE, lw=1.3),
    )

    ax.set_ylabel("Dividend Per Share (ESD)", fontsize=9)
    ax.set_title(f"{target_company} — Dividend Per Share FY1 to FY3", fontsize=10, pad=10)
    _spine_style(ax)
    fig.tight_layout()
    return _save(fig, "08_dps_trend.png", output_dir)


# 09_LEVERAGE.PNG
def chart_leverage(summary: dict, output_dir: Path) -> Path:
    """Net Debt bars (left axis) + ND/EBITDA line (right axis) vs peer median."""
    target_company = summary["target_company"]
    aurexa = summary["aurexa"]
    meds   = summary["peer_medians"]

    yrs = ["FY1", "FY2", "FY3"]
    nd  = [aurexa[f"Net_Debt_{y}"] / 1_000 for y in yrs]
    lev = [aurexa[f"Net_Debt_{y}"] / aurexa[f"EBITDA_{y}"] for y in yrs]

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor(CHART_BACKGROUND)
    ax1.set_facecolor(CHART_BACKGROUND)
    ax2 = ax1.twinx()
    ax2.set_facecolor(CHART_BACKGROUND)

    ax1.bar(yrs, nd,  color=LIGHT_BLUE, alpha=0.7, width=0.45, label="Net Debt (ESDbn)")
    ax2.plot(yrs, lev, color=DARK_BLUE, marker="o", lw=2.2, ms=8, label="ND / EBITDA (FY1) (x)")

    peer_med_lev = meds["nd_ebitda_fy1"]
    ax2.axhline(peer_med_lev, color=NAVY, lw=1.2, linestyle="--")
    ax2.text(2.05, peer_med_lev + 0.06, f"Peer median\n{peer_med_lev:.1f}x", color=NAVY, fontsize=7.5)

    ax1.set_ylabel("Net Debt (ESDbn)", fontsize=9)
    ax2.set_ylabel("ND / EBITDA (FY1) (x)", color=DARK_BLUE, fontsize=9)
    ax1.tick_params(axis="y", colors=NAVY)
    ax2.tick_params(axis="y", colors=DARK_BLUE)
    ax1.tick_params(axis="x", colors=NAVY)
    for sp in ("top", "right"): ax1.spines[sp].set_visible(False)
    ax1.spines["bottom"].set_color(MID)
    ax1.spines["left"].set_color(MID)

    ax1.set_title(f"{target_company} — Leverage Profile vs. Peer Median", fontsize=11, pad=10)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=8,
               facecolor=CHART_BACKGROUND, edgecolor=NAVY, labelcolor=NAVY, loc="upper left")

    fig.tight_layout()
    return _save(fig, "09_leverage.png", output_dir)


# 010_VALUATION_COMPS.PNG
def chart_valuation_comps(summary: dict, output_dir: Path) -> Path:
    target_company = summary["target_company"]
    target_ticker  = summary["target_ticker"]

    df = (
        summary["sector_peers"]
        .dropna(subset=["EV/EBITDA"])
        .loc[lambda d: d["Market_cap_million"] >= 50_000]
        .sort_values("EV/EBITDA", ascending=False)
        .head(20)
    )

    bar_cols    = [LIGHT_BLUE if n == target_company else DARK_BLUE for n in df["Company Name"]]
    tick_labels = [target_ticker if n == target_company else t
                   for n, t in zip(df["Company Name"], df["Ticker"])]

    fig, ax = plt.subplots(figsize=(12, 4.5))
    fig.patch.set_facecolor(CHART_BACKGROUND)
    ax.set_facecolor(CHART_BACKGROUND)

    ax.bar(range(len(df)), df["EV/EBITDA"], color=bar_cols, edgecolor="none", width=0.72)

    peer_med = summary["peer_medians"]["ev_ebitda"]
    ax.axhline(peer_med, color=NAVY, lw=1.2, linestyle=":", label=f"Peer Median  {peer_med:.1f}x")

    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=7.5)
    ax.set_ylabel("EV / EBITDA (x)", fontsize=9)
    ax.set_title("EV/EBITDA Comparison — Large-Cap Sector Universe (Top 20)", fontsize=11, pad=10)
    _spine_style(ax)
    ax.legend(handles=[
        mpatches.Patch(color=LIGHT_BLUE, label=target_company),
        mpatches.Patch(color=DARK_BLUE,  label="Sector Peers"),
    ], fontsize=8, facecolor=CHART_BACKGROUND, edgecolor=MID, labelcolor=NAVY)

    fig.tight_layout()
    return _save(fig, "10_valuation_comps.png", output_dir)

# main function to create all charts
def create_charts(summary: dict, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_company = summary["target_company"]
    print(f"\n[charts] Creating charts for {target_company} in {output_dir}")
    paths = {
        "tsr_waterfall":chart_tsr_waterfall(summary, output_dir),
        "valuation_bubble":chart_valuation_bubble(summary, output_dir),
        "ebitda_margins":chart_ebitda_margins(summary, output_dir),
        "revenue_bridge":chart_revenue_bridge(summary, output_dir),
        "investor_compare":chart_investor_style_compare(summary, output_dir),
        "donut_target":chart_investor_donut(f"{target_company} — Register Composition",summary["target_sh"], "06_donut_target.png", output_dir),
        "donut_peers":chart_investor_donut("Large-Cap Sector Peer Average",summary["peer_sh_avg"], "07_donut_peers.png", output_dir),
        "dps_trend":chart_dps_trend(summary, output_dir),
        "leverage":chart_leverage(summary, output_dir),
        "valuation_comps":chart_valuation_comps(summary, output_dir),
    }

    print(f"[charts] {len(paths)} charts saved\n")
    return paths