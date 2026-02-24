from pathlib import Path

# DIRECTORY PATHS
BASE_DIR     = Path(__file__).resolve().parent.parent
ENRICHED_DIR = BASE_DIR / "data" / "enriched"
OUTPUT_DIR   = BASE_DIR / "data" / "output"

COMPANY_CSV     = ENRICHED_DIR / "company_data_enriched.csv"
SHAREHOLDER_CSV = ENRICHED_DIR / "shareholder_data_enriched.csv"

# CREATE OUTPUT DIRECTORY IF IT DOESN'T EXIST
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ANALYTICS PARAMETERS
PEER_SECTOR    = "Health Care"
CHART_DPI   = 150

# CHART COLOR PALETTE
CHART_BACKGROUND = "#F4F6FA"
DARK_BLUE = "#00395d"
LIGHT_BLUE = "#00aeef"
NAVY   = "#0A1931"
LIGHT  = "#F4F6FA"
MID    = "#BDC6D1"
DARK   = "#1A1A2E"
GREEN  = "#13D36A"
RED    = "#FF3B30"
BLUE   = "#00aeef"
ORANGE = "#FF8C00"
GREY   = "#808285"
YELLOW = "#FF7F00"

# INVESTOR STYLES
ALL_INVESTOR_STYLES = ["Index", "Growth", "Aggressive Growth", "GARP", "Value", "Deep Value", "Yield"]
GROWTH_STYLES       = ["Growth", "Aggressive Growth", "GARP"]

# COLOUR TO REPRESENT EACH INVESTOR STYLE IN DONUT CHARTS
STYLE_COLOURS = {
    "Index": ORANGE,
    "Growth": LIGHT_BLUE,
    "Aggressive Growth": DARK_BLUE,
    "GARP": GREEN,
    "Value": GREY,
    "Deep Value": RED,
    "Yield": YELLOW,
}