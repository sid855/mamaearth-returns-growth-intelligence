# Mamaearth Returns & Growth Intelligence Pipeline

Capstone project for the Data Analytics with AI & GenAI program. This repository contains an end-to-end analysis of retail revenue, returns, customer behavior, and growth opportunities using SQL, Python, data visualization, and an optional GenAI narrative. Source CSVs remain unchanged; data cleaning happens in Python.

## Project objectives

- Report on raw order, customer, product, and revenue data with SQL.
- Standardize payment methods, identify duplicate orders, and handle missing values.
- Compare revenue before and after duplicate removal and analyze return behavior.
- Segment returns by payment method and customer city tier.
- Identify quantity outliers and compare monthly revenue before and after outlier correction.
- Visualize payment-method return rates and corrected monthly revenue.
- Generate an SCR (Situation–Complication–Resolution) narrative from computed findings.

## Project overview

The project has three layers: SQL reports raw relational data; Python independently cleans the CSV data, calculates findings, and creates charts; the narrative script turns the generated findings JSON into a business summary. SQL report output is not passed to Python. The JSON file is the explicit handoff from Python to the narrative layer.

## Repository map

```text
repo/
|-- README.md
|-- sql/
|   |-- schema.sql
|   |-- seed_data.sql
|   `-- reports.sql
|-- data/
|   |-- customers.csv
|   |-- products.csv
|   `-- orders.csv
|-- analysis/
|   |-- clean_and_eda.py
|   `-- visualize.py
|-- visualizations/
|   |-- return_rate_by_payment.png
|   `-- monthly_revenue_trend.png
`-- narrator/
    |-- findings.json
    `-- generate_narrative.py
```

`requirements.txt` is also present at the repository root to install Python dependencies. Running the narrator creates `narrator/sample_output.txt` as a generated text result; it is not a separate submission deliverable.

## Key verified figures

These figures are recorded in the committed datasets and generated findings. Run the pipeline to reproduce them.

| Metric | Result |
| --- | ---: |
| Raw SQL orders | 180 |
| Raw revenue | INR 99,860.20 |
| Cleaned revenue after duplicate removal | INR 97,358.30 |
| Revenue difference from five duplicate rows | INR 2,501.90 |
| COD return rate | 44.4% |
| CARD return rate | 14.7% |
| UPI return rate | 18.9% |
| Highest-risk segment | COD, Tier 2: 54.5% return rate |
| Outlier-corrected peak month | March 2026: INR 20,318.90 |

These are descriptive results from this dataset. Return-rate differences and correlations do not establish causation.

## Setup

Use Python 3.10+ and SQLite 3. The commands below assume you are in the repository root. The `sqlite3` command-line tool must be installed and available on your PATH.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
```

## Installation and execution

Run the three layers in order: SQL reporting, Python analysis and visualization, then narrative generation. SQL reports and Python analysis each start from the supplied CSV data; SQL report results are not passed into Python. The generated findings JSON is the handoff from Python to the narrative layer.

### 1. SQL relational layer

Create a fresh SQLite database and run the schema, loader, and reports in this order:

```bash
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 -header -column mamaearth.db < sql/reports.sql
```

The SQL layer prints report results in the terminal. The seed script inserts the supplied records and clears existing table rows first, so it can be rerun without duplicating records. The reports script includes an `ALTER TABLE` exercise for `loyalty_tier`; because SQLite does not support `ADD COLUMN IF NOT EXISTS` across all versions, run `reports.sql` once per fresh database. The SQL layer intentionally uses raw data and should report 180 orders. Its report results are not an input file for the Python layer.

### 2. Python cleaning, EDA, and visualizations

```bash
python analysis/clean_and_eda.py
python analysis/visualize.py
```

Both scripts read the original three CSVs. `clean_and_eda.py` standardizes payment-method casing, removes duplicates based on the natural order key, imputes missing values, computes the order-value reconciliation, flags quantity outliers without deleting them, and prints return-rate, correlation, and monthly revenue analyses. It writes calculated metrics to `narrator/findings.json`. `visualize.py` regenerates the two PNGs in `visualizations/`; the monthly chart uses the outlier-corrected series. The findings JSON is the input to the next layer, while the charts are final visual outputs.

### 3. GenAI narrative layer

The narrator reads `narrator/findings.json` from Layer 2 and creates a Situation–Complication–Resolution narrative. It uses Gemini only if `GEMINI_API_KEY` is set. Set a key in your environment if you want to test the online path:

```bash
# Windows PowerShell
$env:GEMINI_API_KEY = "your-google-ai-studio-key"
python narrator/generate_narrative.py

# macOS/Linux
export GEMINI_API_KEY="your-google-ai-studio-key"
python narrator/generate_narrative.py
```

Use a key from Google AI Studio's available free usage tier; check current account limits before use. Never commit the key to GitHub. If `GEMINI_API_KEY` is absent, the script uses `generate_scr_narrative_offline(findings)` with no network call or API spend. If the Gemini request fails, it also falls back offline. Both paths save the resulting narrative to `narrator/sample_output.txt` and print the numeric-accuracy checks.

## How the three layers connect

```text
                         +--> SQL schema + seed data --> SQL reports --> terminal results
Source CSV files --------+
                         +--> Python cleaning and EDA --> narrator/findings.json --+
                         |                                                        +--> SCR narrative
                         +--> Python visualization --> visualizations/*.png       |   --> terminal and
                                                                                  |       narrator/sample_output.txt
                                                                                  +--> numeric checks
```

The SQL and Python layers both use the source data but serve different purposes. `analysis/clean_and_eda.py` calculates and writes `narrator/findings.json`; `analysis/visualize.py` independently prepares the CSV data to create the charts. `narrator/generate_narrative.py` reads the findings JSON and formats its verified metrics; it does not calculate the metrics itself. Without `GEMINI_API_KEY`, the narrative uses the offline fallback.

## Business value

The reports and analysis help stakeholders compare raw and cleaned revenue, identify segments with higher observed return rates, review how bulk-order outliers affect monthly trends, and communicate the results in charts and a concise business narrative. These results can guide further investigation; they do not by themselves explain why an order was returned.

## Technologies

- SQLite for relational tables and SQL reporting.
- Python and pandas for cleaning, validation, and exploratory analysis.
- Matplotlib for chart generation.
- JSON for the verified metrics passed to the narrative layer.
- Google GenAI SDK for optional Gemini narrative generation, with an offline fallback.

## Troubleshooting

- If `sqlite3` is not recognized, install the SQLite command-line tool and add it to your PATH.
- If Python packages are missing, activate the project environment and run `pip install -r requirements.txt`.
- If `narrator/findings.json` is missing or stale, run `python analysis/clean_and_eda.py` before the narrator script.
- Gemini is optional. Without a valid `GEMINI_API_KEY`, the script runs its offline narrative fallback.

The public GitHub repository is the complete project deliverable; no separate PDF, slide deck, screenshots, or video are required.

## Important interpretation notes

- Missing discount values are treated as 0% only in the cleaning/reporting calculation, and missing ratings are filled with the median after duplicate removal.
- Five duplicate submissions are removed by comparing the natural key that excludes `order_id`; source CSV files are not edited.
- Quantity outliers remain in the dataset but are excluded from the corrected monthly revenue visualization.
- Correlation indicates association, not causation. The analysis does not prove why an order was returned.
