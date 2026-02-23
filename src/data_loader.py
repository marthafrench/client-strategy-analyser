import pandas as pd
from pathlib import Path

from .config import COMPANY_CSV, SHAREHOLDER_CSV

def load_companies(path: Path = COMPANY_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"  [data_loader] Loaded {len(df)} companies from {path.name}")
    return df


def load_shareholders(path: Path = SHAREHOLDER_CSV):
    df = pd.read_csv(path)
    print(f"  [data_loader] Loaded {len(df)} shareholder rows "
        f"across {df['Company Name'].nunique()} companies from {path.name}")
    return df


def load_all():
    companies = load_companies()
    shareholders = load_shareholders()
    return companies, shareholders