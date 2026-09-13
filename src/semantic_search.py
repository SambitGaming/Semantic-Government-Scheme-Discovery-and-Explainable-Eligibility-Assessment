
import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# --------------------------------------------------
# 1. Load the dataset
# --------------------------------------------------

DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "processed",
    "retrieval_corpus.csv"
)

df = pd.read_csv(DATA_PATH)

print("Dataset loaded successfully!")
print("Total schemes:", len(df))

# --------------------------------------------------
# 2. Check the required column
# --------------------------------------------------

if "retrieval_text" not in df.columns:
    raise ValueError(
        "The dataset must contain a 'retrieval_text' column."
    )

# Replace missing text values with empty strings
df["retrieval_text"] = df["retrieval_text"].fillna("").astype(str)

# Remove empty rows
df = df[df["retrieval_text"].str.strip() != ""].reset_index(drop=True)

# --------------------------------------------------
# 3. Load the sentence embedding model
# --------------------------------------------------

print("Loading sentence embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Model loaded successfully!")

# --------------------------------------------------
# 4. Convert all scheme text into embeddings
# --------------------------------------------------

print("Creating embeddings for all schemes...")

scheme_embeddings = model.encode(
    df["retrieval_text"].tolist(),
    normalize_embeddings=True,
    show_progress_bar=True
)

print("Embeddings created successfully!")

# --------------------------------------------------
# 5. Define semantic search function
# --------------------------------------------------

def semantic_search(query, top_k=5):

    # Convert user query into an embedding
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    # Calculate similarity between query and all schemes
    similarity_scores = cosine_similarity(
        query_embedding,
        scheme_embeddings
    )[0]

    # Copy dataset so original data is not modified
    results = df.copy()

    # Add similarity scores
    results["similarity_score"] = similarity_scores

    # Sort by highest similarity
    results = results.sort_values(
        by="similarity_score",
        ascending=False
    )

    # Return top matching schemes
    return results.head(top_k)


# --------------------------------------------------
# 6. Test queries
# --------------------------------------------------

queries = [
    "Scholarships for undergraduate students",
    "Financial assistance for economically weaker students",
    "Scholarships for school students"
]

for query in queries:

    print("\n" + "=" * 70)
    print("QUERY:", query)
    print("=" * 70)

    results = semantic_search(query, top_k=5)

    display_columns = [
        "scheme_id",
        "scheme_name",
        "similarity_score"
    ]

    print(
        results[display_columns].to_string(index=False)
    )


# --------------------------------------------------
# 7. Interactive search
# --------------------------------------------------

while True:

    user_query = input(
        "\nEnter your scholarship search query "
        "(or type 'exit' to stop): "
    )

    if user_query.lower() == "exit":
        print("Semantic search stopped.")
        break

    if not user_query.strip():
        print("Please enter a search query.")
        continue

    results = semantic_search(user_query, top_k=5)

    print("\nTop matching schemes:\n")

    print(
        results[
            [
                "scheme_id",
                "scheme_name",
                "similarity_score",
                "official_url"
            ]
        ].to_string(index=False)
    )