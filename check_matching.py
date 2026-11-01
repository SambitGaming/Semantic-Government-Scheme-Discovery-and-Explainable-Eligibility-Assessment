
import pandas as pd

results = pd.read_csv("data/benchmark/mpnet_results.csv")
judgments = pd.read_csv("data/benchmark/relevance_judgments.csv")

print("MPNet result rows:", len(results))
print("Judgment rows:", len(judgments))

print("\nMPNet result columns:")
print(results.columns.tolist())

print("\nJudgment columns:")
print(judgments.columns.tolist())

if {"query_id", "scheme_id"}.issubset(results.columns) and {
    "query_id", "scheme_id"
}.issubset(judgments.columns):

    results["query_id"] = results["query_id"].astype(str).str.strip()
    judgments["query_id"] = judgments["query_id"].astype(str).str.strip()

    results["scheme_id"] = results["scheme_id"].astype(str).str.strip()
    judgments["scheme_id"] = judgments["scheme_id"].astype(str).str.strip()

    matches = results.merge(
        judgments[["query_id", "scheme_id"]],
        on=["query_id", "scheme_id"],
        how="left",
        indicator=True
    )

    print("\nMatched result rows:", (matches["_merge"] == "both").sum())
    print("Unmatched result rows:", (matches["_merge"] == "left_only").sum())

else:
    print("\nThe query_id or scheme_id columns are missing.")