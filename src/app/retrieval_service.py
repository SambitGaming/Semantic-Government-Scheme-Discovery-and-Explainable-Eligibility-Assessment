
"""Semantic search service for the Government Scheme Assistant."""

from pathlib import Path
import logging

import pandas as pd

from src.retrieval.semantic_minilm import MiniLMSemanticSearch
from src.retrieval.semantic_mpnet import MPNetSemanticSearch


logger = logging.getLogger(__name__)


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCHEMES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "schemes_clean.csv"
)


# --------------------------------------------------
# Load scheme metadata
# --------------------------------------------------

def load_scheme_metadata():
    """Load scheme metadata used to enrich search results."""

    if not SCHEMES_FILE.exists():
        raise FileNotFoundError(
            f"Scheme metadata file not found: {SCHEMES_FILE}"
        )

    df = pd.read_csv(
        SCHEMES_FILE,
        dtype=str,
        keep_default_na=False,
    )

    required_columns = [
        "ID",
        "Scholarship",
        "Description",
        "Category",
        "Official_url",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Scheme metadata CSV is missing required columns: "
            + ", ".join(missing_columns)
        )

    lookup = {}

    for _, row in df.iterrows():
        scheme_id = str(row["ID"]).strip()

        if not scheme_id:
            continue

        lookup[scheme_id] = {
            "scheme_id": scheme_id,
            "scheme_name": str(
                row["Scholarship"]
            ).strip(),
            "description": str(
                row["Description"]
            ).strip(),
            "category": str(
                row["Category"]
            ).strip(),
            "official_url": str(
                row["Official_url"]
            ).strip(),
        }

    logger.info(
        "Loaded metadata for %d schemes.",
        len(lookup),
    )

    return lookup


scheme_lookup = load_scheme_metadata()


# --------------------------------------------------
# Lazy-loaded semantic models
# --------------------------------------------------

_minilm = None
_mpnet = None


def get_minilm():
    """Load MiniLM only when it is first requested."""

    global _minilm

    if _minilm is None:
        logger.info("Loading MiniLM semantic search model.")
        _minilm = MiniLMSemanticSearch()

    return _minilm


def get_mpnet():
    """Load MPNet only when it is first requested."""

    global _mpnet

    if _mpnet is None:
        logger.info("Loading MPNet semantic search model.")
        _mpnet = MPNetSemanticSearch()

    return _mpnet


# --------------------------------------------------
# Semantic search
# --------------------------------------------------

def semantic_search(
    query,
    model="minilm",
    top_k=10,
):
    """
    Search government schemes using MiniLM or MPNet.

    Args:
        query: User's search query.
        model: 'minilm' or 'mpnet'.
        top_k: Maximum number of results.

    Returns:
        A list of scheme dictionaries containing metadata and scores.
    """

    if not isinstance(query, str):
        raise ValueError("Search query must be a string.")

    query = query.strip()

    if not query:
        return []

    model = str(model).strip().lower()

    if model not in ("minilm", "mpnet"):
        raise ValueError(
            "Unsupported model. Use 'minilm' or 'mpnet'."
        )

    if isinstance(top_k, bool) or not isinstance(top_k, int):
        raise ValueError("top_k must be an integer.")

    if not 1 <= top_k <= 100:
        raise ValueError(
            "top_k must be between 1 and 100."
        )

    # Select the requested retrieval model.
    if model == "minilm":
        retriever = get_minilm()
    else:
        retriever = get_mpnet()

    # Perform semantic retrieval.
    search_results = retriever.search(
        query,
        top_k,
    )

    if not search_results:
        return []

    # Enrich results using the scheme metadata CSV.
    final_results = []

    for result in search_results:
        scheme_id = str(
            result.get("scheme_id", "")
        ).strip()

        scheme = scheme_lookup.get(scheme_id)

        if scheme:
            final_results.append({
                "scheme_id": scheme["scheme_id"],
                "scheme_name": scheme["scheme_name"],
                "description": scheme["description"],
                "category": scheme["category"],
                "official_url": scheme["official_url"],
                "score": float(result.get("score", 0)),
            })
        else:
            # Preserve results that do not have a metadata match.
            final_results.append(result)

    return final_results
