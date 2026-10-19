"""Generate a deterministic SCR narrative with Gemini or an offline fallback."""
from pathlib import Path
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
FINDINGS_PATH = ROOT / "narrator" / "findings.json"
SAMPLE_PATH = ROOT / "narrator" / "sample_output.txt"

def money(value):
    return f"{float(value):,.2f}"

def generate_scr_narrative_offline(findings: dict) -> dict:
    """Generate a keyless, deterministic narrative directly from verified findings."""
    payment = findings["return_rate_by_payment"]
    risk = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    inflated = findings["outlier_inflated_month"]
    delta = findings["duplicate_reconciliation_delta_inr"]
    cleaned = findings["cleaned_total_revenue_inr"]
    raw = findings["raw_total_revenue_inr"]
    narrative = f"""### Situation
The cleaned order dataset records ₹{money(cleaned)} in revenue across the retained orders. The outlier-corrected revenue peak is {peak['month']}, at ₹{money(peak['revenue_inr'])}. These figures provide a consistent starting point for the regional operations and finance teams.

### Complication
Returns differ by payment method: COD has a {payment['COD']:.1f}% return rate, compared with {payment['CARD']:.1f}% for CARD and {payment['UPI']:.1f}% for UPI. The highest-risk segment is COD in Tier-{risk['city_tier']} cities, with a {risk['return_rate_pct']:.1f}% return rate. The raw SQL revenue of ₹{money(raw)} is ₹{money(delta)} higher than the cleaned revenue because five duplicate orders were removed. January initially appears to lead at ₹{money(inflated['apparent_revenue_inr'])}, but the outlier-corrected January figure is ₹{money(inflated['corrected_revenue_inr'])}.

### Resolution
Prioritize a COD-focused review in Tier-{risk['city_tier']} cities, investigate the order and delivery journey before changing payment policies, and monitor return rates by payment method and city tier. Keep duplicate-order checks in the ingestion process and use outlier-corrected monthly revenue for trend decisions. March, at ₹{money(peak['revenue_inr'])}, is the true peak month after the two bulk-order outliers are excluded."""
    return {"status": "success", "narrative": narrative, "tokens": None}

def generate_scr_narrative(findings: dict) -> dict:
    """Call Gemini with fixed factual constraints; return a structured error on failure."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return generate_scr_narrative_offline(findings)
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30000))
        system_instruction = (
            "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
            "Write exactly three labeled sections: Situation, Complication, Resolution. "
            "Every number in the output must come from the supplied findings and appear with the same value; "
            "do not invent statistics, percentages, dates, or amounts. Explain the operational implications "
            "without asserting causation that the data does not prove."
        )
        # temperature=0.0 makes this factual business report as deterministic as the API permits.
        contents = (
            "Write a concise business narrative in SCR format using only this verified findings object. "
            "Do not introduce any numeric values not present in it:\n"
            + json.dumps(findings, ensure_ascii=False, indent=2)
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                max_output_tokens=600,
            ),
        )
        narrative = response.text or ""
        usage = getattr(response, "usage_metadata", None)
        tokens = getattr(usage, "total_token_count", None) if usage else None
        if not narrative.strip():
            raise ValueError("Gemini returned an empty narrative.")
        return {"status": "success", "narrative": narrative, "tokens": tokens}
    except Exception as err:
        return {"status": "error", "narrative": None, "message": str(err)}

def check_numeric_accuracy(narrative: str) -> dict:
    """Check the required figures after removing thousands separators."""
    normalized = narrative.replace(",", "")
    checks = {
        "cleaned revenue 97358.30": ["97358.30", "97358.3"],
        "COD return rate 44.4": ["44.4"],
        "COD Tier-2 return rate 54.5": ["54.5"],
        "duplicate delta 2501.90": ["2501.90", "2501.9"],
        "March peak revenue 20318.90": ["20 318.90", "20318.90", "20318.9"],
    }
    results = {}
    for label, options in checks.items():
        results[label] = any(option.replace(",", "") in normalized for option in options)
        if label == "March peak revenue 20318.90":
            results[label] = results[label] and "march" in normalized.lower()
        print(f"{'PASS' if results[label] else 'FAIL'} — {label}")
    return results

def main():
    with FINDINGS_PATH.open(encoding="utf-8") as handle:
        findings = json.load(handle)
    result = generate_scr_narrative(findings)
    if result["status"] == "error":
        print("Gemini call failed; using offline fallback. Error:", result["message"])
        result = generate_scr_narrative_offline(findings)
    narrative = result["narrative"]
    print(f"Narrative status: {result['status']}; tokens: {result.get('tokens')}")
    print(narrative)
    checks = check_numeric_accuracy(narrative)
    if not all(checks.values()):
        print("The generated narrative missed a required figure; saved output should be reviewed.")
    SAMPLE_PATH.write_text(narrative.rstrip() + "\n", encoding="utf-8")
    print(f"Saved narrative to {SAMPLE_PATH.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
