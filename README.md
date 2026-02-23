# 🛍️ Product Recommendation System

A production-ready, content-based product recommendation engine with an interactive Streamlit frontend — optimised for local execution on **Apple M4 / MacBook Air**.

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        app.py  (UI Layer)                   │
│   ┌──────────────┐  ┌──────────────────┐  ┌─────────────┐  │
│   │  Searchable  │  │  Recommendation  │  │ Cold Start  │  │
│   │  Dropdown    │  │  Gallery (grid)  │  │  Trending   │  │
│   └──────────────┘  └──────────────────┘  └─────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ calls
┌────────────────────────────▼────────────────────────────────┐
│                     engine.py  (ML Layer)                   │
│                                                             │
│   products.csv  →  TfidfVectorizer  →  Cosine Similarity    │
│                     (ngram 1-2)         matrix (float32)    │
│                                                             │
│   get_recommendations(product_id, top_n) → pd.DataFrame    │
│   get_trending_products(n)               → pd.DataFrame    │
└────────────────────────────┬────────────────────────────────┘
                             │ reads
┌────────────────────────────▼────────────────────────────────┐
│                 data_generator.py  (Data Layer)             │
│                                                             │
│   8 categories × adj/noun combos → 520 products → CSV      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (macOS / Apple M4)

### Prerequisites
- **Python 3.11+** — check with `python3 --version`
- **VS Code** with the Python extension installed (recommended)

### Step 1 — Clone / Download the project

Place all four files in the same folder:
```
product_recommender/
├── data_generator.py
├── engine.py
├── app.py
└── requirements.txt
```

### Step 2 — Create a virtual environment

```bash
cd product_recommender
python3 -m venv venv
```

### Step 3 — Activate the virtual environment

```bash
source venv/bin/activate
```

Your terminal prompt will now show `(venv)`.

### Step 4 — Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **M4 note:** NumPy and scikit-learn ship native ARM64 wheels — no Rosetta overhead.

### Step 5 — Generate the synthetic dataset

```bash
python data_generator.py
```

Expected output:
```
✅  Generated 520 products → /path/to/product_recommender/products.csv
```

### Step 6 — Launch the Streamlit app

```bash
streamlit run app.py
```

Streamlit will open **http://localhost:8501** in your default browser automatically.

---

## 📁 File Reference

| File | Purpose |
|------|---------|
| `data_generator.py` | Generates `products.csv` with 520 synthetic products across 8 categories |
| `engine.py` | ML recommendation engine (TF-IDF + Cosine Similarity, caching, public API) |
| `app.py` | Interactive Streamlit UI (dropdown, gallery, cold-start section) |
| `requirements.txt` | Pinned Python dependencies |

---

## 🧠 How the Recommendation Engine Works

### 1. Corpus Construction
Each product's `Description` and `Tags` fields are concatenated into a single text corpus. Tags are repeated once to give them additional TF-IDF weight relative to prose descriptions.

### 2. TF-IDF Vectorisation
```
TfidfVectorizer(
    ngram_range=(1, 2),   # unigrams + bigrams
    sublinear_tf=True,    # log(1 + tf) dampening
    stop_words="english",
    max_features=8_000,   # vocabulary cap for M4 RAM
)
```

### 3. Cosine Similarity Matrix
A full `n × n` pairwise cosine similarity matrix is computed once and stored as **float32** (halves memory vs float64). On 520 products this is a ~1 MB matrix — trivial on M4.

### 4. Top-N Retrieval
`numpy.argpartition` (O(n) partial sort) is used instead of a full `argsort` for efficient top-N extraction. Results are cached with `functools.lru_cache` so repeated queries cost nothing.

---

## 🖥️ UI Features

### Feature 1 — Searchable Product Dropdown
A Streamlit `selectbox` lists all products. Type any substring (name, category, price) to instantly filter the list. Category and price filters in the sidebar further narrow the selection.

### Feature 2 — Recommendation Gallery
Once a product is selected, the engine returns the **Top-N most similar products** (configurable 1–10 via sidebar slider). Results render in a responsive 5-column card grid, each showing:
- Category, name, truncated description
- Tag pills
- Price and similarity percentage badge

### Feature 3 — Cold Start / Trending Section
When no product is selected, a curated "Trending Right Now" section is shown. It selects the highest-priced product per category (a proxy for premium/popular items) to ensure cross-category variety. After a product is selected this section remains as "Also Trending."

---

## ⚙️ Configuration

| Constant | File | Default | Description |
|----------|------|---------|-------------|
| `NUM_PRODUCTS` | `data_generator.py` | `520` | Total products generated |
| `TOP_N_DEFAULT` | `engine.py` | `5` | Default recommendation count |
| `max_features` | `engine.py` | `8_000` | TF-IDF vocabulary cap |
| `RANDOM_SEED` | `data_generator.py` | `42` | Reproducibility seed |

---

## 🍎 Apple M4 Optimisations

| Technique | Benefit |
|-----------|---------|
| `float32` similarity matrix | 50% RAM reduction vs float64 |
| Pandas `category` dtype for low-cardinality columns | 4–8× less memory for string columns |
| Explicit dtype mapping on CSV load | Avoids dtype inference overhead |
| `numpy.argpartition` for top-N | O(n) vs O(n log n) full sort |
| `functools.lru_cache` on recommendations | Repeated queries cost O(1) |
| `@st.cache_data` on data load | TF-IDF matrix built once per session |
| Native ARM64 wheels (NumPy, scikit-learn) | No Rosetta 2 translation overhead |

---

## 🔧 VS Code Setup (Recommended)

1. Open the `product_recommender/` folder: **File → Open Folder**
2. Select the Python interpreter: `Ctrl+Shift+P` → *Python: Select Interpreter* → choose `./venv/bin/python`
3. Install recommended extensions: **Python**, **Pylance**, **Ruff**

To run the app from the VS Code integrated terminal:
```bash
source venv/bin/activate
streamlit run app.py
```

---

## 🛠️ Extending the System

### Add a new product category
Edit the `CATEGORIES` dict in `data_generator.py`, add a hex colour to `CATEGORY_COLOURS` in `app.py`, then re-run `python data_generator.py`.

### Swap to a real dataset
Replace `products.csv` with your own CSV. Ensure it contains the same column names: `Product_ID`, `Product_Name`, `Category`, `Description`, `Tags`, `Price`.

### Add collaborative filtering
Implement a user-item interaction matrix in a new `collaborative_engine.py` and surface a toggle in `app.py` to switch between content-based and collaborative recommendations.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `scikit-learn` | ≥ 1.4 | TfidfVectorizer, cosine_similarity |
| `numpy` | ≥ 1.26 | Matrix ops, argpartition |
| `pandas` | ≥ 2.2 | Data loading and manipulation |
| `streamlit` | ≥ 1.35 | Interactive web UI |

---

## 📄 License

MIT — free to use, modify, and distribute.
