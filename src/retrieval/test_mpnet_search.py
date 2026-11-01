from src.retrieval.semantic_mpnet import (
    MPNetSemanticSearch
)


retriever = MPNetSemanticSearch()

query = (
    "I am an MCA student looking "
    "for financial assistance for higher education"
)

results = retriever.search(
    query,
    top_k=5
)

print()
print("MPNet Semantic Search")
print()

for rank, result in enumerate(
    results,
    start=1
):

    print(
        f"{rank}. "
        f"{result['scheme_name']} "
        f"(score={result['score']:.4f})"
    )