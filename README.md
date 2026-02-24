# Client Strategy Analyser

A comprehensive financial analysis and visualization tool for evaluating company performance, market positioning, investor base alignment, and growth strategy effectiveness.

## Overview

Client Strategy Analyser processes raw financial data to generate insightful analytics, comparative peer analysis, and publication-ready visualizations. It's designed for investment banking and corporate strategy teams to quickly assess a company's financial health and strategic positioning against sector peers.

## Features

- **Financial Analytics**: Calculate key metrics including EV/EBITDA, TSR, EBITDA margins, leverage ratios, and more
- **Peer Comparison**: Automatically benchmark against peer companies in the same sector
- **Investor Base Analysis**: Analyze shareholder composition and classify by investment style (Index, Growth, Value, etc.)
- **Data Enrichment**: Automatic data preprocessing with FX conversion and enrichment
- **Professional Visualizations**: Generate 10+ publication-ready charts including:
  - TSR waterfalls
  - Valuation bubbles and comparables
  - EBITDA margin trends
  - Shareholder composition donuts
  - Revenue bridges
  - Leverage analysis
  - Balance sheet strength metrics

## Project Structure

```
client-strategy-analyser/
├── run.py                          # Main entry point
├── requirements.txt                # Python dependencies
├── src/
│   ├── config.py                   # Configuration & constants
│   ├── data_loader.py              # CSV data loading utilities
│   ├── data_pre_processing.py      # Data enrichment & preprocessing
│   ├── analytics.py                # Financial calculations & analysis
│   ├── charts.py                   # Visualization generation
│   └── tables.py                   # Summary table creation
└── data/
    ├── raw/                        # Source CSV files
    │   ├── company_data.csv
    │   ├── shareholder_data.csv
    │   └── fx_rates.csv
    ├── enriched/                   # Processed & enriched data
    └── output/                     # Generated charts & tables
```

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`:
  - pandas >= 2.0.0
  - numpy >= 1.23.0
  - matplotlib >= 3.6.0
  - scipy >= 1.9.0
  - seaborn 0.13.2

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd client-strategy-analyser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the analysis for a specific company using:

```bash
python run.py --target "Company Name"
```

**Important**: The company name must match exactly as it appears in the source CSV file.

### Example

```bash
python run.py --target "Aurexa PLC"
```

### What Happens

The tool runs a 5-step pipeline:

1. **Preprocessing**: Enriches raw data with FX conversions and calculated fields
2. **Loading**: Imports enriched company and shareholder data
3. **Analytics**: Calculates financial metrics and investor composition analysis
4. **Tables**: Generates summary CSV tables
5. **Charts**: Creates 10+ visualization charts

### Output

Results are saved to `data/output/{TICKER}/` including:
- Financial performance metrics CSV
- Shareholder composition CSV
- 10+ publication-ready PNG charts

### Example Output

```
IB Analytics & Chart Generator  |  AUREX
================================================================
  ✓ Step 1 / 5  |  Preprocessing raw data
  ✓ Step 2 / 5  |  Loading enriched data
  ✓ Step 3 / 5  |  Running analytics

  AUREX snapshot:
    Ticker         : AUREX
    Market Cap     : ESD 123.5bn
    EV/EBITDA      : 12.5x  (peer median 11.8x)
    3yr TSR        : 15.2%  (peer median 9.1%)
    ...

  ✓ Step 4 / 5  |  Building summary tables
  ✓ Step 5 / 5  |  Rendering charts
  
================================================================
Complete  |  8.3s

10 charts saved to data/output/AUREX/
```

## Configuration

Edit `src/config.py` to customize:

- **Thresholds**: Large-cap definition, peer sector selection
- **Colors**: Chart color palette and investor style colors
- **Output**: Chart DPI, directory paths
- **Investor Styles**: Classification categories (Index, Growth, Value, etc.)

### Key Settings

```python
PEER_SECTOR = "Health Care"      # Sector for peer comparison
CHART_DPI = 150                  # Output chart resolution
```

## Data Requirements

### Input Files (Raw)

**company_data.csv**
- Company Name
- Ticker
- Sector
- Market Cap (ESD millions)
- Financial metrics (Revenue, EBITDA, etc.)
- 3-year TSR

**shareholder_data.csv**
- Company Name
- Shareholder name
- Ownership %
- Investor style classification

**fx_rates.csv**
- Currency conversion rates

### Output Files

Generated automatically in `data/output/{TICKER}/`:

- `01_financial_performance.csv` - Key financial metrics
- `02_valuation_vs_delivery.csv` - Valuation analysis
- `03_shareholder_base.csv` - Investor composition
- `06_balance_sheet_strength.csv` - Balance sheet metrics
- Multiple PNG charts for presentations

## Analysis Metrics

The tool calculates:

- **Valuation**: EV/EBITDA, EV/Sales, P/E ratios
- **Profitability**: EBITDA margins, ROE, ROIC
- **Growth**: Revenue growth, EBITDA growth rates
- **Leverage**: Net Debt/EBITDA, Interest coverage
- **Returns**: Total Shareholder Return (TSR), CAGR
- **Investor Mix**: Breakdown by investment style

## Architecture

- **Modular Design**: Separated concerns (data, analytics, visualization)
- **Configuration-Driven**: Easy customization without code changes
- **Error Handling**: Robust preprocessing with detailed logging
- **Performance**: Efficient pandas operations for large datasets

## Troubleshooting

### Company Not Found
```
[run] Company not found in data — check spelling and CSV file
```
- Verify the company name exactly matches `company_data.csv`
- Check that the file has been properly loaded

### Missing Data
If key metrics are missing from output:
- Check source CSV has all required columns
- Verify data preprocessing completed successfully
- Review data types in `data_pre_processing.py`

### Chart Generation Issues
- Ensure all required financial data is available
- Check matplotlib/seaborn compatibility
- Verify sufficient disk space in `data/output/`

## License

See LICENSE file for details.

