import pandas as pd
import os

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


INPUT_FILE = "results/eligibility/gold_profile_results.csv"

METRICS_FILE = "results/eligibility/eligibility_metrics.csv"

ERROR_FILE = "results/eligibility/eligibility_errors.csv"


# --------------------------------------------------
# Load evaluation results
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("Loaded profiles:", len(df))


# --------------------------------------------------
# Convert expected results to binary
# Eligible = 1
# Not Eligible = 0
# --------------------------------------------------

y_true = (
    df["expected_result"]
    .astype(str)
    .str.strip()
    .str.lower()
    .map({
        "eligible": 1,
        "not eligible": 0
    })
)


# --------------------------------------------------
# Convert actual results to binary
# --------------------------------------------------

y_pred = (
    df["actual_result"]
    .astype(str)
    .str.strip()
    .str.lower()
    .map({
        "eligible": 1,
        "not eligible": 0
    })
)


# --------------------------------------------------
# Validate labels
# --------------------------------------------------

invalid_expected = y_true.isna().sum()
invalid_actual = y_pred.isna().sum()

if invalid_expected > 0 or invalid_actual > 0:
    print("\nWARNING")
    print("Invalid expected labels:", invalid_expected)
    print("Invalid actual labels:", invalid_actual)


# --------------------------------------------------
# Keep only valid rows
# --------------------------------------------------

valid = y_true.notna() & y_pred.notna()

y_true = y_true[valid]
y_pred = y_pred[valid]

df_valid = df.loc[valid].copy()


# --------------------------------------------------
# Calculate metrics
# --------------------------------------------------

accuracy = accuracy_score(y_true, y_pred)

precision = precision_score(
    y_true,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_true,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0
)


# --------------------------------------------------
# Confusion matrix
# --------------------------------------------------

tn, fp, fn, tp = confusion_matrix(
    y_true,
    y_pred,
    labels=[0, 1]
).ravel()


# --------------------------------------------------
# Create metrics dataframe
# --------------------------------------------------

metrics = pd.DataFrame([
    {
        "metric": "Accuracy",
        "value": accuracy
    },
    {
        "metric": "Precision",
        "value": precision
    },
    {
        "metric": "Recall",
        "value": recall
    },
    {
        "metric": "F1",
        "value": f1
    },
    {
        "metric": "True Positives",
        "value": tp
    },
    {
        "metric": "True Negatives",
        "value": tn
    },
    {
        "metric": "False Positives",
        "value": fp
    },
    {
        "metric": "False Negatives",
        "value": fn
    }
])


# --------------------------------------------------
# Create output directory
# --------------------------------------------------

os.makedirs(
    "results/eligibility",
    exist_ok=True
)


# --------------------------------------------------
# Save metrics
# --------------------------------------------------

metrics.to_csv(
    METRICS_FILE,
    index=False
)


# --------------------------------------------------
# Identify errors
# --------------------------------------------------

df_valid["error_type"] = "Correct"


# False Positive
df_valid.loc[
    (y_true.to_numpy() == 0) &
    (y_pred.to_numpy() == 1),
    "error_type"
] = "False Positive"


# False Negative
df_valid.loc[
    (y_true.to_numpy() == 1) &
    (y_pred.to_numpy() == 0),
    "error_type"
] = "False Negative"


# --------------------------------------------------
# Keep only errors
# --------------------------------------------------

errors = df_valid[
    df_valid["error_type"] != "Correct"
].copy()


# --------------------------------------------------
# Save errors
# --------------------------------------------------

errors.to_csv(
    ERROR_FILE,
    index=False
)


# --------------------------------------------------
# Display results
# --------------------------------------------------

print("\nEligibility Evaluation")
print("======================")

print(f"Profiles evaluated: {len(df_valid)}")

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")

print("\nConfusion Matrix")
print("----------------")

print("True Negatives :", tn)
print("False Positives:", fp)
print("False Negatives:", fn)
print("True Positives :", tp)

print("\nErrors:", len(errors))

print("\nFiles created:")
print(METRICS_FILE)
print(ERROR_FILE)
