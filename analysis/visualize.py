"""Create the two required figures from the same raw CSV source files."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "visualizations"
OUT.mkdir(exist_ok=True)

def prepare():
    customers = pd.read_csv(DATA / "customers.csv")
    products = pd.read_csv(DATA / "products.csv")
    orders = pd.read_csv(DATA / "orders.csv")
    orders["payment_method"] = orders["payment_method"].str.strip().str.upper()
    key = ["customer_id", "product_id", "order_date", "quantity", "discount_pct",
           "payment_method", "rating", "returned"]
    orders = orders.drop_duplicates(subset=key, keep="first").copy()
    median_rating = orders["rating"].median()
    orders["discount_pct"] = orders["discount_pct"].fillna(0)
    orders["rating"] = orders["rating"].fillna(median_rating)
    merged = orders.merge(products, on="product_id").merge(customers, on="customer_id")
    merged["order_value"] = merged["quantity"] * merged["price"] * (1 - merged["discount_pct"] / 100)
    q1, q3 = merged["quantity"].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    merged["is_outlier"] = ~merged["quantity"].between(lower, upper, inclusive="both")
    merged["order_date"] = pd.to_datetime(merged["order_date"])
    merged["year_month"] = merged["order_date"].dt.to_period("M").astype(str)
    return merged

def main():
    merged = prepare()
    rates = (merged.groupby("payment_method")["returned"].mean() * 100).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(rates.index, rates.values)
    ax.set_ylabel("Return rate (%)")
    ax.set_xlabel("Payment method")
    lead = rates.index[0]
    ax.set_title(f"{lead} Returns at {rates.loc[lead]:.1f}% — {rates.loc[lead]/rates.loc['CARD']:.1f}x Card")
    ax.set_ylim(0, max(rates.values) * 1.22)
    for bar, value in zip(bars, rates.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8, f"{value:.1f}%", ha="center")
    fig.tight_layout()
    fig.savefig(OUT / "return_rate_by_payment.png", dpi=160)
    plt.close(fig)

    monthly = merged.loc[~merged["is_outlier"]].groupby("year_month")["order_value"].sum()
    peak_month = monthly.idxmax()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(monthly.index, monthly.values, marker="o")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (INR)")
    ax.set_title(f"Outlier-Corrected Monthly Revenue — Peak: {peak_month}")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(OUT / "monthly_revenue_trend.png", dpi=160)
    plt.close(fig)
    print("Saved visualizations/return_rate_by_payment.png")
    print("Saved visualizations/monthly_revenue_trend.png")
    print(f"Outlier-corrected peak month: {peak_month} (₹{monthly.max():,.2f})")

if __name__ == "__main__":
    main()
