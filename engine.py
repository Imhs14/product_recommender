"""
engine.py
---------
Content-Based Filtering recommendation engine.

Pipeline:
  1. Load products.csv into a memory-efficient Pandas DataFrame.
  2. Build a combined "corpus" field from Description + Tags.
  3. Vectorize with TfidfVectorizer (sublinear_tf for better term weighting).
  4. Compute pairwise Cosine Similarity matrix (float32 to halve memory vs float64).
  5. Expose get_recommendations() — the single public API consumed by app.py.

Optimised for Apple M4:
  - float32 similarity matrix (halves RAM vs float64).
  - Vectorizer strips accents and stop-words at fit time (no runtime overhead).
  - All heavy work cached after first load via module-level singletons.

Author: Senior AI Engineer
"""

from __future__ import annotations

import pathlib
from functools import lru_cache
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Config ────────────────────────────────────────────────────────────────────
DATA_PATH: pathlib.Path = pathlib.Path("products.csv")
TOP_N_DEFAULT: int = 5

# ── Module-level singletons (populated on first call) ─────────────────────────
_df: Optional[pd.DataFrame] = None
_similarity_matrix: Optional[np.ndarray] = None
_id_to_index: Optional[dict[int, int]] = None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_and_build() -> None:
    """
    Load the CSV, build the TF-IDF matrix, and compute cosine similarities.
    Called once; results stored in module globals for O(1) subsequent access.
    """
    global _df, _similarity_matrix, _id_to_index

    # --- 1. Load data with explicit dtypes (memory-efficient) -----------------
    _df = pd.read_csv(
        DATA_PATH,
        dtype={
            "Product_ID":   "int32",
            "Product_Name": "string",
            "Category":     "category",   # low-cardinality → category dtype
            "Description":  "string",
            "Tags":         "string",
            "Price":        "float32",
        },
    )

    # --- 2. Build corpus: description + tags (give tags extra weight) ---------
    _df["_corpus"] = (
        _df["Description"].fillna("") + " "
        + _df["Tags"].fillna("") + " "
        + _df["Tags"].fillna("")   # repeat tags to boost their TF-IDF weight
    )

    # --- 3. TF-IDF vectorisation ----------------------------------------------
    vectorizer = TfidfVectorizer(
        strip_accents="unicode",
        analyzer="word",
        stop_words="english",
        ngram_range=(1, 2),      # unigrams + bigrams for richer matching
        sublinear_tf=True,       # log(1 + tf) → reduces dominance of frequent terms
        min_df=1,
        max_features=8_000,      # cap vocab for memory efficiency on M4
    )
    tfidf_matrix = vectorizer.fit_transform(_df["_corpus"])

    # --- 4. Cosine similarity (float32 to halve RAM) --------------------------
    _similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix).astype(np.float32)

    # --- 5. Reverse lookup: Product_ID → DataFrame row index -----------------
    _id_to_index = dict(zip(_df["Product_ID"].tolist(), range(len(_df))))

    # Drop the temporary corpus column; we're done with it
    _df.drop(columns=["_corpus"], inplace=True)


def _ensure_loaded() -> None:
    """Lazy initialiser — safe to call many times, builds only once."""
    if _df is None:
        _load_and_build()


# ── Public API ────────────────────────────────────────────────────────────────

def get_all_products() -> pd.DataFrame:
    """
    Return the full products DataFrame.

    Returns
    -------
    pd.DataFrame
        All products with columns: Product_ID, Product_Name, Category,
        Description, Tags, Price.
    """
    _ensure_loaded()
    assert _df is not None  # type narrowing for mypy
    return _df


@lru_cache(maxsize=512)
def get_recommendations(product_id: int, top_n: int = TOP_N_DEFAULT) -> pd.DataFrame:
    """
    Return the top-N most similar products for a given Product_ID.

    Uses cosine similarity on TF-IDF vectors built from Description + Tags.
    Results are cached with lru_cache so repeated queries are O(1).

    Parameters
    ----------
    product_id : int
        The ID of the seed product.
    top_n : int
        Number of recommendations to return (default 5).

    Returns
    -------
    pd.DataFrame
        DataFrame of top_n recommended products sorted by similarity score,
        with an additional ``Similarity`` column (0–1 float).

    Raises
    ------
    ValueError
        If product_id is not found in the dataset.
    """
    _ensure_loaded()
    assert _df is not None and _similarity_matrix is not None and _id_to_index is not None

    if product_id not in _id_to_index:
        raise ValueError(f"Product_ID {product_id!r} not found in dataset.")

    idx: int = _id_to_index[product_id]

    # Similarity scores for this product against every other product
    sim_scores: np.ndarray = _similarity_matrix[idx]

    # Exclude the product itself; get top_n indices sorted descending
    # np.argpartition for O(n) partial sort — faster than full argsort on M4
    candidate_indices = np.delete(np.arange(len(sim_scores)), idx)
    scores_candidates = sim_scores[candidate_indices]

    # Take top_n (partial sort then sort just those)
    k = min(top_n, len(scores_candidates))
    top_k_local = np.argpartition(scores_candidates, -k)[-k:]
    top_k_local_sorted = top_k_local[np.argsort(scores_candidates[top_k_local])[::-1]]
    top_indices = candidate_indices[top_k_local_sorted]

    recommendations: pd.DataFrame = _df.iloc[top_indices].copy()
    recommendations["Similarity"] = np.round(sim_scores[top_indices].astype(float), 4)
    recommendations.reset_index(drop=True, inplace=True)

    return recommendations


def get_trending_products(n: int = 8) -> pd.DataFrame:
    """
    Return a deterministic "trending" selection for the Cold Start section.

    Strategy: sort by price descending (proxy for premium/popular items)
    then sample evenly across categories to ensure variety.

    Parameters
    ----------
    n : int
        Number of trending products to return.

    Returns
    -------
    pd.DataFrame
    """
    _ensure_loaded()
    assert _df is not None

    categories = _df["Category"].unique().tolist()
    per_cat    = max(1, n // len(categories))

    frames: list[pd.DataFrame] = []
    for cat in categories:
        cat_df = (
            _df[_df["Category"] == cat]
            .sort_values("Price", ascending=False)
            .head(per_cat)
        )
        frames.append(cat_df)

    trending = pd.concat(frames, ignore_index=True).head(n)
    return trending
