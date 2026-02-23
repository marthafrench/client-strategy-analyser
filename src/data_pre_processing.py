import logging
import re
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

EXPECTED_COMPANY_COLS = [
    "Company Name", "Ticker", "Reporting Currency", "Sector",
    "DPS_FY1", "DPS_FY2", "DPS_FY3",
    "EBITDA_FY1", "EBITDA_FY2", "EBITDA_FY3",
    "EPS", "Market_cap_million", "Share Price", "3yr TSR", "EV/EBITDA",
    "Sales_FY1", "Sales_FY2", "Sales_FY3",
    "Net_Debt_FY1", "Net_Debt_FY2", "Net_Debt_FY3",
]

EXPECTED_SHAREHOLDER_COLS = ["Investor ticker", "Name of Investor", "%OS", "Inv Style"]
FORMATTED_NUM_COLS = ["Market_cap_million"]
FLOAT_COLS = [
    "DPS_FY1", "DPS_FY2", "DPS_FY3",
    "EBITDA_FY1", "EBITDA_FY2", "EBITDA_FY3",
    "EPS", "Share Price", "3yr TSR", "EV/EBITDA",
    "Sales_FY1", "Sales_FY2", "Sales_FY3",
    "Net_Debt_FY1", "Net_Debt_FY2", "Net_Debt_FY3",
]
NUMERIC_COLS_TO_CONVERT = FLOAT_COLS + FORMATTED_NUM_COLS

# 4 data cols + 1 blank spacer per company block
SHAREHOLDER_GROUP = len(EXPECTED_SHAREHOLDER_COLS) + 1


def get_paths():
    base = Path.cwd()
    return base / "raw", base / "enriched"


def load_fx_rates(base_dir: Path) -> dict:
    fx_path = base_dir / "raw" / "fx_rates.csv"
    if not fx_path.exists():
        log.error("FX rates file not found: %s", fx_path)
        sys.exit(1)
    df = pd.read_csv(fx_path)
    rates = {}
    # for each row, if to_c is ESD and from_c is valid, add from_c: rate to the dict
    for _, row in df.iterrows():
        from_c = str(row.get("from_currency",""))
        to_c = str(row.get("to_currency",""))
        rate = float(row.get("rate", float("nan")))
        if to_c == "ESD" and from_c and from_c not in ("NAN", ""):
            rates[from_c] = rate
    rates["ESD"] = 1.0
    log.info("FX rates loaded: %s", rates)
    return rates


def apply_fx_conversion(df: pd.DataFrame, fx_rates: dict) -> pd.DataFrame:
    if "Reporting Currency" not in df.columns:
        log.warning("No 'Reporting Currency' column — skipping FX conversion")
        return df
    df = df.copy()
    # ensure numeric cols are float before writing converted values into them
    cols = [c for c in NUMERIC_COLS_TO_CONVERT if c in df.columns]
    df[cols] = df[cols].apply(pd.to_numeric, errors="coerce").astype(float)
    # check for any currencies in the data that are not in the fx_rates dict and log a warning if found
    unknown = set(df["Reporting Currency"].dropna().str.strip().str.upper().unique()) - set(fx_rates)
    if unknown:
        log.warning("Unknown currencies (rows left unconverted): %s", unknown)
    # for each row, if the reporting currency is in fx_rates dict, convert the
    # numeric cols to ESD using the rate and update the reporting currency to ESD
    converted = 0
    for idx, row in df.iterrows():
        ccy = str(row["Reporting Currency"]).strip().upper()
        if ccy == "ESD" or ccy not in fx_rates:
            continue
        df.loc[idx, cols] = pd.to_numeric(df.loc[idx, cols], errors="coerce") * fx_rates[ccy]
        df.loc[idx, "Reporting Currency"] = "ESD"
        converted += 1
    log.info("FX conversion applied to %d rows", converted)
    return df


def read_tab_separated_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", dtype=str, na_values=["#N/A", ""])


def read_shareholder_csv(path: Path) -> tuple:
    raw = pd.read_csv(path, sep="\t", header=None, dtype=str, na_values=["#N/A", ""])
    # metadata is the first 2 rows (company tickers and names)
    metadata = raw.iloc[:2].reset_index(drop=True)
    # data is everything from the 4th row, with columns named according to the 3rd row
    data = raw.iloc[3:].reset_index(drop=True)
    data.columns = raw.iloc[2].values
    log.info("shareholder_data.csv: %d data rows, %d company groups",
             len(data), data.shape[1] // SHAREHOLDER_GROUP)
    return metadata, data


def extract_company_lookup(metadata: pd.DataFrame) -> pd.DataFrame:
    records = []
    # for each company group in metadata, extract ticker and company name from first 2 rows and add to lookup list
    for g in range(metadata.shape[1] // SHAREHOLDER_GROUP):
        col = g * SHAREHOLDER_GROUP
        ticker = str(metadata.iloc[0, col]).strip() if col < metadata.shape[1] else ""
        name = str(metadata.iloc[1, col]).strip() if col < metadata.shape[1] else ""
        if ticker and ticker.lower() not in ("nan", ""):
            records.append({"company_index": g, "Ticker": ticker, "Company Name": name})
    lookup = pd.DataFrame(records)
    log.info("Company lookup: %d companies", len(lookup))
    return lookup


def validate_company_data(df: pd.DataFrame):
    actual = list(df.columns[:len(EXPECTED_COMPANY_COLS)])
    # validate that the columns in the company data match the expected columns exactly
    if actual != EXPECTED_COMPANY_COLS:
        log.error("company_data.csv schema mismatch\n expected: %s\n got: %s",EXPECTED_COMPANY_COLS, actual)
        sys.exit(1)
    log.info("company_data.csv schema OK")


def validate_shareholder_schema(df: pd.DataFrame):
    mismatched = []
    for g in range(df.shape[1] // SHAREHOLDER_GROUP):
        # normalise column names by stripping whitespace and removing any trailing .1, .2 etc. which have been added by pandas for duplicate column names
        cols = [re.sub(r"\.\d+$", "", str(c).strip())
                for c in df.columns[g * SHAREHOLDER_GROUP : g * SHAREHOLDER_GROUP + len(EXPECTED_SHAREHOLDER_COLS)]]
        if cols != EXPECTED_SHAREHOLDER_COLS:
            mismatched.append((g, cols))
    if mismatched:
        for g, cols in mismatched:
            log.error("shareholder_data.csv — group %d header mismatch: %s", g, cols)
        sys.exit(1)
    log.info("shareholder_data.csv schema OK")


def clean_company_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.apply(lambda s: s.str.strip() if s.dtype == "object" else s)
    # convert numeric columns to float, removing commas and coercing errors to NaN
    for col in FORMATTED_NUM_COLS:df[col] = pd.to_numeric(df[col].str.replace(",", "", regex=False).str.strip(), errors="coerce")
    for col in FLOAT_COLS:df[col] = pd.to_numeric(df[col], errors="coerce")
    # check for any negative values in numeric columns and log a warning if found (some may be valid, but flag to review)
    before = len(df)
    df = df.dropna(how="all")
    if len(df) < before: log.info("  Dropped %d blank rows", before - len(df))
    log.info("company_data cleaned (%d rows)", len(df))
    return df


def clean_shareholder_data(df: pd.DataFrame) -> pd.DataFrame:
    n_groups = df.shape[1] // SHAREHOLDER_GROUP
    chunks = []
    for g in range(n_groups):
        chunk = df.iloc[:, g * SHAREHOLDER_GROUP : g * SHAREHOLDER_GROUP + len(EXPECTED_SHAREHOLDER_COLS)].copy()
        chunk.columns = EXPECTED_SHAREHOLDER_COLS
        chunk["company_index"] = g
        chunks.append(chunk)
    out = pd.concat(chunks, ignore_index=True)
    out = out.apply(lambda s: s.str.strip() if s.dtype == "object" else s)
    out.replace({"#N/A": pd.NA, "N/A": pd.NA, "": pd.NA}, inplace=True)
    # log how many rows have a non-empty 'Investor ticker' value, as all records with empty values can be dropped
    before = len(out)
    out = out.dropna(subset=["Investor ticker"])
    log.info("  Dropped %d empty rows", before - len(out))
    # convert %OS to numeric and log any negative values found (some may be valid, but flag to review)
    out["%OS"] = pd.to_numeric(out["%OS"], errors="coerce")
    if (out["%OS"] < 0).any():
        log.warning("  Negative %%OS values found — review before use")
    log.info("shareholder_data cleaned (%d rows)", len(out))
    return out[["company_index"] + EXPECTED_SHAREHOLDER_COLS]


def main():
    raw_dir, enriched_dir = get_paths()
    enriched_dir.mkdir(parents=True, exist_ok=True)
    company_path = raw_dir / "company_data.csv"
    shareholder_path = raw_dir / "shareholder_data.csv"
    missing = [f for f in (company_path, shareholder_path) if not f.exists()]
    if missing:
        for f in missing: log.error("File not found: %s", f)
        sys.exit(1)
    # process company data
    company_raw = read_tab_separated_csv(company_path)
    validate_company_data(company_raw)
    company_df = clean_company_data(company_raw)
    company_df = apply_fx_conversion(company_df, load_fx_rates(Path.cwd()))
    company_df.to_csv(enriched_dir / "company_data_enriched.csv", index=False)
    log.info("Saved company_data_enriched.csv")
    # process shareholder data
    shareholder_metadata, sh_raw = read_shareholder_csv(shareholder_path)
    validate_shareholder_schema(sh_raw)
    shareholder_df = clean_shareholder_data(sh_raw)
    shareholder_df = shareholder_df.merge(
        extract_company_lookup(shareholder_metadata), on="company_index", how="left"
    )
    shareholder_df.to_csv(enriched_dir / "shareholder_data_enriched.csv", index=False)
    log.info("Saved shareholder_data_enriched.csv")

if __name__ == "__main__":
    main()