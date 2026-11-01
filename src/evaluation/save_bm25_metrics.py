import pandas as pd
from pathlib import Path


# --------------------------------------------------
# Your final BM25 metric values
# Replace the XXXX values with your actual results
# --------------------------------------------------

metrics = {
    "Precision@5": 0.1604,
    "Recall@5": 0.6167,
    "Precision@10": 0.1084,
    "Recall@10": 0.6930,
    "MRR": 0.5986,
    "nDCG@5": 0.5560,
    "nDCG@10": 0.5866
}


# Create results directory
output_dir = Path("results\\bm25")
output_dir.mkdir(
    parents=True,
    exist_ok=True
)


# Convert to DataFrame
metrics_df = pd.DataFrame(
    metrics.items(),
    columns=["metric", "value"]
)


# Save CSV
output_file = output_dir / "bm25_metrics.csv"

metrics_df.to_csv(
    output_file,
    index=False
)


print("BM25 metrics saved successfully!")
print("Saved to:", output_file)