import pandas as pd
from rank_bm25 import BM25Okapi

# Load BM25 corpus
INPUT_FILE = "data/processed/bm25_corpus.csv"

df = pd.read_csv(INPUT_FILE)

# Convert documents into tokens
tokenized_documents = [
    str(doc).lower().split()
    for doc in df["bm25_document"]
]

# Create BM25 model
bm25 = BM25Okapi(tokenized_documents)

# Test queries
queries = [
    "scholarship for postgraduate students",
    "financial assistance for Karnataka students",
    "scholarship for economically weaker students",
    "education assistance for students",
    "scholarship for engineering students"
]

print("=" * 70)
print("BM25 MANUAL TEST")
print("=" * 70)

for query in queries:

    # Tokenize query
    tokenized_query = query.lower().split()

    # Get BM25 scores
    scores = bm25.get_scores(tokenized_query)

    # Get top 5 results
    top_indices = scores.argsort()[::-1][:5]

    print("\nQuery:", query)
    print("-" * 70)

    for rank, index in enumerate(top_indices, start=1):

        print(
            f"{rank}. "
            f"{df.iloc[index]['scheme_name']} "
            f"(Score: {scores[index]:.2f})"
        )