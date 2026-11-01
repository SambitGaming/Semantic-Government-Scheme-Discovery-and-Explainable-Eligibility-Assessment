import pandas as pd
from rank_bm25 import BM25Okapi


BENCHMARK_FILE = "data/benchmark/queries.csv"
CORPUS_FILE = "data/processed/bm25_corpus.csv"
OUTPUT_FILE = "data/benchmark/bm25_results.csv"


def run_benchmark():

    # Load benchmark queries
    queries = pd.read_csv(BENCHMARK_FILE)

    # Load BM25 corpus
    corpus = pd.read_csv(CORPUS_FILE)

    # Tokenize documents
    tokenized_documents = [
        str(document).lower().split()
        for document in corpus["bm25_document"]
    ]

    # Create BM25 model
    bm25 = BM25Okapi(tokenized_documents)

    results = []

    for _, query_row in queries.iterrows():

        query_id = query_row["query_id"]
        query_text = query_row["query_text"]

        # Tokenize query
        tokenized_query = str(query_text).lower().split()

        # Calculate BM25 scores
        scores = bm25.get_scores(tokenized_query)

        # Get top 5 results
        top_indices = scores.argsort()[::-1][:10]

        for rank, index in enumerate(top_indices, start=1):

            results.append({
                "query_id": query_id,
                "query_text": query_text,
                "rank": rank,
                "scheme_id": corpus.iloc[index]["scheme_id"],
                "scheme_name": corpus.iloc[index]["scheme_name"],
                "bm25_score": scores[index]
            })

    results_df = pd.DataFrame(results)

    results_df.to_csv(OUTPUT_FILE, index=False)

    print("BM25 benchmark completed successfully!")
    print("Queries:", len(queries))
    print("Results:", len(results_df))
    print("Saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    run_benchmark()