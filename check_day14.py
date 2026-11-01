
import pandas as pd

base = "data/benchmark/"

queries = pd.read_csv(base + "queries.csv")
judgments = pd.read_csv(base + "relevance_judgments.csv")

print("Queries:", len(queries))
print("Unique query IDs:", queries["query_id"].nunique())
print("Judgment rows:", len(judgments))
print("Judgment columns:", judgments.columns.tolist())

for model in ["bm25", "minilm", "mpnet"]:
    df = pd.read_csv(base + f"{model}_results.csv")

    print(f"\n{model.upper()}")
    print("Rows:", len(df))
    print("Unique queries:", df["query_id"].nunique())
    print("Columns:", df.columns.tolist())

    if "rank" in df.columns:
        print("Maximum rank per query:")
        print(df.groupby("query_id")["rank"].max().value_counts())