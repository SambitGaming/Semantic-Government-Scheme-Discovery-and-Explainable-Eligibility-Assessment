import pandas as pd

queries = pd.read_csv(
    "data/benchmark/queries.csv"
)

judgments = pd.read_csv(
    "data/benchmark/relevance_judgments.csv"
)

generation_log = pd.read_csv(
    "data/benchmark/query_generation_log.csv"
)

print("Queries:", len(queries))
print("Judgments:", len(judgments))
print("Generation log:", len(generation_log))

print("\nQuery columns:")
print(list(queries.columns))

print("\nJudgment columns:")
print(list(judgments.columns))

print("\nGeneration log columns:")
print(list(generation_log.columns))

print("\nDay 4 CSV files loaded successfully!")