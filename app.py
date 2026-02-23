"""
app.py
------
Streamlit-based interactive frontend for the Product Recommendation System.

Features:
  1. Searchable product dropdown with live filtering.
  2. Recommendation Gallery — 5 similar products in a responsive grid.
  3. Cold Start section — trending/popular items when nothing is selected.

Design philosophy: clean, editorial aesthetic with consistent card layout.
Optimised for local MacBook Air M4 execution (no external API calls).

Author: Senior AI Engineer
Run:    streamlit run app.py
"""

from __future__ import annotations

import pathlib

import pandas as pd
import streamlit as st

from engine import get_all_products, get_recommendations, get_trending_products

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Product Recommender",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global reset & palette ── */
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    .main { background: #f8f7f4; }

    /* ── Header ── */
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 18px;
        padding: 2.5rem 3rem;
        margin-bottom: 2rem;
        color: #fff;
    }
    .hero h1 {
        font-family: 'DM Serif Display', serif;
        font-size: 2.8rem;
        margin: 0 0 .4rem 0;
        letter-spacing: -0.5px;
    }
    .hero p  { color: #a8b2d8; font-size: 1.05rem; margin: 0; }

    /* ── Section headings ── */
    .section-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.6rem;
        color: #1a1a2e;
        margin: 1.8rem 0 1rem 0;
        border-left: 4px solid #e63946;
        padding-left: 12px;
    }

    /* ── Product card ── */
    .product-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.3rem 1.4rem;
        height: 100%;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border: 1px solid #edecea;
        transition: box-shadow .2s, transform .2s;
        position: relative;
        overflow: hidden;
    }
    .product-card:hover {
        box-shadow: 0 8px 28px rgba(0,0,0,0.13);
        transform: translateY(-3px);
    }

    /* coloured top accent derived from category */
    .product-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: var(--accent, #e63946);
        border-radius: 14px 14px 0 0;
    }

    .card-category {
        font-size: .7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: var(--accent, #e63946);
        margin-bottom: .3rem;
    }
    .card-name {
        font-size: 1rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: .5rem;
        line-height: 1.3;
    }
    .card-desc {
        font-size: .82rem;
        color: #555;
        line-height: 1.5;
        margin-bottom: .7rem;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        margin-bottom: .7rem;
    }
    .tag {
        background: #f0f0ee;
        color: #444;
        font-size: .68rem;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 500;
    }
    .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: .5rem;
    }
    .card-price {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1a1a2e;
    }
    .similarity-badge {
        background: #e8f5e9;
        color: #2e7d32;
        font-size: .72rem;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 20px;
    }
    .trending-badge {
        background: #fff3e0;
        color: #e65100;
        font-size: .72rem;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 20px;
    }

    /* ── Seed product highlight ── */
    .seed-card {
        background: linear-gradient(135deg, #1a1a2e, #0f3460);
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        color: #fff;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,.2);
    }
    .seed-card .card-category { color: #a8b2d8; }
    .seed-card .card-name     { color: #fff; font-size: 1.2rem; }
    .seed-card .card-desc     { color: #c5cde8; }
    .seed-card .card-price    { color: #7ed8a4; font-size: 1.3rem; }
    .seed-card .tag           { background: rgba(255,255,255,.15); color: #dde; }

    /* ── Divider ── */
    hr { border: none; border-top: 1px solid #e5e3de; margin: 1.5rem 0; }

    /* ── Streamlit tweaks ── */
    div[data-testid="stSelectbox"] label { font-weight: 600; color: #1a1a2e; }
    .stSelectbox > div > div { border-radius: 10px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Category → accent colour map ─────────────────────────────────────────────
CATEGORY_COLOURS: dict[str, str] = {
    "Electronics": "#3a86ff",
    "Books":       "#fb5607",
    "Fitness":     "#8338ec",
    "Kitchen":     "#e63946",
    "Clothing":    "#06d6a0",
    "Beauty":      "#f72585",
    "Home Decor":  "#ffb703",
    "Gaming":      "#00b4d8",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _accent(category: str) -> str:
    return CATEGORY_COLOURS.get(str(category), "#e63946")


def _tags_html(tags_str: str, max_tags: int = 5) -> str:
    tags = [t.strip() for t in str(tags_str).split(",") if t.strip()][:max_tags]
    return "".join(f'<span class="tag">{t}</span>' for t in tags)


def _render_card(
    row: pd.Series,
    similarity: float | None = None,
    is_trending: bool = False,
) -> str:
    """Render a product as an HTML card string."""
    accent  = _accent(row["Category"])
    badge   = ""
    if similarity is not None:
        pct   = int(similarity * 100)
        badge = f'<span class="similarity-badge">⚡ {pct}% match</span>'
    elif is_trending:
        badge = '<span class="trending-badge">🔥 Trending</span>'

    return f"""
    <div class="product-card" style="--accent:{accent}">
        <div class="card-category">{row['Category']}</div>
        <div class="card-name">{row['Product_Name']}</div>
        <div class="card-desc">{row['Description']}</div>
        <div class="card-tags">{_tags_html(row['Tags'])}</div>
        <div class="card-footer">
            <span class="card-price">${float(row['Price']):.2f}</span>
            {badge}
        </div>
    </div>
    """


def _render_seed_card(row: pd.Series) -> str:
    return f"""
    <div class="seed-card">
        <div class="card-category">🎯 &nbsp;Selected Product</div>
        <div class="card-name">{row['Product_Name']}</div>
        <div class="card-desc">{row['Description']}</div>
        <div class="card-tags">{_tags_html(row['Tags'])}</div>
        <div class="card-footer">
            <span class="card-price">${float(row['Price']):.2f}</span>
            <span class="tag">ID #{int(row['Product_ID'])}</span>
        </div>
    </div>
    """


def _render_grid(products: pd.DataFrame, similarity_col: bool = False, trending: bool = False) -> None:
    """Render products in a 5-column responsive grid."""
    cols = st.columns(5, gap="medium")
    for i, (_, row) in enumerate(products.iterrows()):
        sim = float(row["Similarity"]) if similarity_col and "Similarity" in row else None
        with cols[i % 5]:
            st.markdown(_render_card(row, similarity=sim, is_trending=trending), unsafe_allow_html=True)


# ── Data loading (cached at Streamlit session level) ─────────────────────────

@st.cache_data(show_spinner="Loading product catalogue…")
def load_data() -> pd.DataFrame:
    """Cached wrapper so the CSV + TF-IDF build runs only once per session."""
    return get_all_products()


# ── Main App ──────────────────────────────────────────────────────────────────

def main() -> None:
    # ── Hero header ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero">
            <h1>🛍️ Product Recommender</h1>
            <p>Content-based recommendations powered by TF-IDF & Cosine Similarity</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Load data ─────────────────────────────────────────────────────────────
    df = load_data()

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🔧 Filters")
        categories  = ["All Categories"] + sorted(df["Category"].unique().tolist())
        selected_cat = st.selectbox("Category", categories)

        price_min, price_max = float(df["Price"].min()), float(df["Price"].max())
        price_range = st.slider(
            "Price Range ($)",
            min_value=price_min,
            max_value=price_max,
            value=(price_min, price_max),
            step=1.0,
        )
        st.markdown("---")
        st.markdown("**Top-N Recommendations**")
        top_n = st.slider("How many recommendations?", min_value=1, max_value=10, value=5)

    # ── Filter product list for dropdown ─────────────────────────────────────
    filtered_df = df.copy()
    if selected_cat != "All Categories":
        filtered_df = filtered_df[filtered_df["Category"] == selected_cat]
    filtered_df = filtered_df[
        (filtered_df["Price"] >= price_range[0]) &
        (filtered_df["Price"] <= price_range[1])
    ]

    # ── Feature 1: Searchable product dropdown ────────────────────────────────
    st.markdown('<div class="section-title">🔍 Select a Product</div>', unsafe_allow_html=True)

    if filtered_df.empty:
        st.warning("No products match the current filters. Adjust the sidebar settings.")
        return

    product_options: dict[str, int] = {
        f"{row['Product_Name']} — {row['Category']} (${float(row['Price']):.2f})": int(row["Product_ID"])
        for _, row in filtered_df.sort_values("Product_Name").iterrows()
    }

    placeholder     = "— Type to search or select a product —"
    option_keys     = [placeholder] + list(product_options.keys())
    selected_label  = st.selectbox(
        "Product",
        option_keys,
        label_visibility="collapsed",
    )

    # ── Feature 2: Recommendation Gallery ────────────────────────────────────
    if selected_label != placeholder:
        product_id = product_options[selected_label]
        seed_row   = df[df["Product_ID"] == product_id].iloc[0]

        st.markdown(_render_seed_card(seed_row), unsafe_allow_html=True)

        st.markdown(
            f'<div class="section-title">✨ Top {top_n} Recommendations</div>',
            unsafe_allow_html=True,
        )

        with st.spinner("Finding similar products…"):
            recs = get_recommendations(product_id, top_n=top_n)

        if recs.empty:
            st.info("No recommendations found for this product.")
        else:
            _render_grid(recs, similarity_col=True)

        st.markdown("<hr>", unsafe_allow_html=True)

    # ── Feature 3: Cold Start — Trending Products ─────────────────────────────
    trending_title = "🔥 Trending Right Now" if selected_label == placeholder else "🔥 Also Trending"
    st.markdown(f'<div class="section-title">{trending_title}</div>', unsafe_allow_html=True)

    if selected_label == placeholder:
        st.markdown(
            "<p style='color:#777; margin-bottom:1rem;'>Select a product above for personalised recommendations, "
            "or explore what's popular today.</p>",
            unsafe_allow_html=True,
        )

    trending = get_trending_products(n=8)
    _render_grid(trending, similarity_col=False, trending=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:#aaa; font-size:.8rem;'>"
        "Built with Streamlit · Scikit-Learn · Pandas &nbsp;|&nbsp; Optimised for Apple M4"
        "</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
