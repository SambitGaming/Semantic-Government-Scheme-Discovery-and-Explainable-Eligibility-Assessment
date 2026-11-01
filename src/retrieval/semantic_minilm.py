from pathlib import Path

import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer


# ==================================================
# PROJECT PATH
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ==================================================
# FILE PATHS
# ==================================================

CORPUS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "semantic_corpus.csv"
)

EMBEDDING_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "minilm_document_embeddings.npy"
)


# ==================================================
# MODEL
# ==================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class MiniLMSemanticSearch:

    def __init__(self):

        # ------------------------------------------
        # Load MiniLM
        # ------------------------------------------

        self.model = SentenceTransformer(
            MODEL_NAME
        )


        # ------------------------------------------
        # Load semantic corpus
        # ------------------------------------------

        self.corpus = pd.read_csv(
            CORPUS_FILE
        )


        # ------------------------------------------
        # Replace missing values
        # ------------------------------------------

        self.corpus = self.corpus.fillna("")


        # ------------------------------------------
        # Load or create embeddings
        # ------------------------------------------

        if EMBEDDING_FILE.exists():

            self.embeddings = np.load(
                EMBEDDING_FILE
            )

        else:

            self.embeddings = self.model.encode(
                self.corpus["search_text"].astype(str).tolist(),
                normalize_embeddings=True,
                show_progress_bar=True
            )

            np.save(
                EMBEDDING_FILE,
                self.embeddings
            )


    def search(
        self,
        query,
        top_k=10
    ):

        # ------------------------------------------
        # Encode query
        # ------------------------------------------

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True
        )[0]


        # ------------------------------------------
        # Calculate cosine similarity
        # ------------------------------------------

        scores = np.dot(
            self.embeddings,
            query_embedding
        )


        # ------------------------------------------
        # Get top results
        # ------------------------------------------

        top_indices = np.argsort(
            scores
        )[::-1][:top_k]


        results = []


        # ------------------------------------------
        # Build results
        # ------------------------------------------

        for index in top_indices:

            row = self.corpus.iloc[index]


            scheme_id = str(
                row.get("scheme_id", "")
            ).strip()


            scheme_name = str(
                row.get("scheme_name", "")
            ).strip()


            description = str(
                row.get("description", "")
            ).strip()


            category = str(
                row.get("category", "")
            ).strip()


            official_url = str(
                row.get("official_url", "")
            ).strip()


            # --------------------------------------
            # Extra protection against "nan"
            # --------------------------------------

            if scheme_id.lower() in ["nan", "none"]:
                scheme_id = ""

            if scheme_name.lower() in ["nan", "none"]:
                scheme_name = "Government Scheme"

            if description.lower() in ["nan", "none", ""]:
                description = "No description available."

            if category.lower() in ["nan", "none"]:
                category = ""

            if official_url.lower() in ["nan", "none"]:
                official_url = ""


            results.append({

                "scheme_id": scheme_id,

                "scheme_name": scheme_name,

                "description": description,

                "category": category,

                "official_url": official_url,

                "score": float(
                    scores[index]
                )

            })


        return results
