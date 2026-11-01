import pandas as pd
import os


INPUT_FILE = "results/eligibility/explainability_results.csv"

OUTPUT_FILE = "results/eligibility/rule_level_summary.csv"


# --------------------------------------------------
# Load explainability results
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("Loaded rule evaluations:", len(df))


# --------------------------------------------------
# Display available columns
# --------------------------------------------------

print("\nColumns:")
print(df.columns.tolist())


# --------------------------------------------------
# Normalize rule result
# --------------------------------------------------

df["rule_result_normalized"] = (
    df["rule_result"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# --------------------------------------------------
# Rule-level summary
# --------------------------------------------------

summary = (
    df.groupby("field")
    .agg(
        total_rules=("rule_id", "count"),
        passed=(
            "rule_result_normalized",
            lambda x: (x == "PASS").sum()
        ),
        failed=(
            "rule_result_normalized",
            lambda x: (x == "FAIL").sum()
        )
    )
    .reset_index()
)


# --------------------------------------------------
# Calculate pass rate
# --------------------------------------------------

summary["pass_rate"] = (
    summary["passed"] /
    summary["total_rules"]
)


# --------------------------------------------------
# Create output directory
# --------------------------------------------------

os.makedirs(
    "../../results/eligibility",
    exist_ok=True
)


# --------------------------------------------------
# Save result
# --------------------------------------------------

summary.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# Display result
# --------------------------------------------------

print("\nRule-Level Evaluation")
print("=====================")

print(summary.to_string(index=False))

print("\nFile created:")
print(OUTPUT_FILE)