
import os
import pandas as pd

# Create benchmark folder if it does not exist
os.makedirs("data/benchmark", exist_ok=True)

# Create queries.csv
queries = pd.DataFrame(columns=[
    "query_id",
    "query_text",
    "query_type"
])

queries.to_csv(
    "data/benchmark/queries.csv",
    index=False
)

# Create query_generation_log.csv
generation_log = pd.DataFrame(columns=[
    "query_id",
    "query_type",
    "source_scheme_id",
    "difficulty",
    "creator",
    "notes"
])

generation_log.to_csv(
    "data/benchmark/query_generation_log.csv",
    index=False
)

# Create relevance_judgments.csv
judgments = pd.DataFrame(columns=[
    "query_id",
    "scheme_id",
    "relevance_label",
    "relevance_score",
    "justification"
])

judgments.to_csv(
    "data/benchmark/relevance_judgments.csv",
    index=False
)

print("Day 5 benchmark files created successfully.")