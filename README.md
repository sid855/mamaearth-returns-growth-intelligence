# Mamaearth Returns & Growth Intelligence Pipeline

A learning capstone that connects a raw-data SQL reporting layer, an independent pandas cleaning/EDA pipeline, and a GenAI-powered business narrative. All source CSVs remain unchanged; cleaning happens in Python.

## Repository map

- `sql/schema.sql` — relational table definitions and foreign keys.
- `sql/seed_data.sql` — re-runnable `INSERT` statements generated from the provided CSVs, including SQL `NULL` values for blank source cells.
- `sql/reports.sql` — the nine requested SQL report exercises with expected result notes.
- `data/` — original `customers.csv`, `products.csv`, and `orders.csv`.
- `analysis/clean_and_eda.py` — pandas cleaning, validation, EDA, and generated findings export.
- `analysis/visualize.py` — creates the two requested PNG charts from the raw CSV files.
- `visualizations/` — generated charts.
- `narrator/findings.json` — generated verified metrics for the narrative layer.
- `narrator/generate_narrative.py` — Gemini SCR narrative with a deterministic offline fallback.
- `narrator/sample_output.txt` — the narrative produced the last time the narrator script ran.

## Setup

Use Python 3.10+ and SQLite 3. The commands below assume you are in the repository root.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
```

## Run the pipeline in order

### 1. SQL relational layer

Create a fresh SQLite database and run the schema, loader, and reports in this order:

```bash
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 -header -column mamaearth.db < sql/reports.sql
```

The seed script deletes existing rows before re-inserting the supplied source records, so it can be rerun without duplicating records. The reports script includes an `ALTER TABLE` exercise for `loyalty_tier`; because SQLite does not support `ADD COLUMN IF NOT EXISTS` across all versions, run `reports.sql` once per fresh database. The SQL layer intentionally uses raw data and should report 180 orders.

### 2. Python cleaning, EDA, and visualizations

```bash
python analysis/clean_and_eda.py
python analysis/visualize.py
```

`clean_and_eda.py` independently reads the original three CSVs, standardizes payment-method casing, removes duplicates based on the natural order key, imputes missing values, computes the order-value reconciliation, flags quantity outliers without deleting them, prints return-rate and correlation analyses, and computes both monthly revenue series. At the end, it writes `narrator/findings.json` directly from calculated values. `visualize.py` reads the same raw CSVs and regenerates both chart PNGs; the monthly chart uses the outlier-corrected series.

### 3. GenAI narrative layer

The narrator reads `narrator/findings.json` and returns a Situation–Complication–Resolution narrative. It uses Gemini only if `GEMINI_API_KEY` is set. Set a key in your environment if you want to test the online path:

```bash
# Windows PowerShell
$env:GEMINI_API_KEY = "your-google-ai-studio-key"
python narrator/generate_narrative.py

# macOS/Linux
export GEMINI_API_KEY="your-google-ai-studio-key"
python narrator/generate_narrative.py
```

Use a key from Google AI Studio's available free usage tier; check current account limits before use. Never commit the key to GitHub. If `GEMINI_API_KEY` is absent, the script uses `generate_scr_narrative_offline(findings)` with no network call or API spend. If the Gemini request fails, it also falls back offline. Both paths save the resulting narrative to `narrator/sample_output.txt` and print the numeric-accuracy checks.

## Data flow

`data/*.csv` → SQL tables → `sql/reports.sql` for the raw-data reports.

Independently, `data/*.csv` → `analysis/clean_and_eda.py` → verified calculations → `narrator/findings.json` → `narrator/generate_narrative.py` → `narrator/sample_output.txt`.

`analysis/visualize.py` also reads the raw CSVs and reproduces the two figures from the cleaned analysis logic. The narrator does not calculate metrics itself: it uses the findings JSON produced by the pandas layer.

## Important interpretation notes

- Missing discount values are treated as 0% only in the cleaning/reporting calculation, and missing ratings are filled with the median after duplicate removal.
- Five duplicate submissions are removed by comparing the natural key that excludes `order_id`; source CSV files are not edited.
- Quantity outliers remain in the dataset but are excluded from the corrected monthly revenue visualization.
- Correlation indicates association, not causation. The analysis does not prove why an order was returned.
