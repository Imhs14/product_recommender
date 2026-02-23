"""
data_generator.py
-----------------
Generates a synthetic products.csv dataset with 500+ items
across multiple categories for the recommendation engine.

Author: Senior AI Engineer
Optimized for: macOS / Apple M4 (memory-efficient Pandas ops)
"""

import random
import csv
import pathlib
from typing import Final

# ── Constants ────────────────────────────────────────────────────────────────
OUTPUT_PATH: Final[pathlib.Path] = pathlib.Path("products.csv")
NUM_PRODUCTS: Final[int] = 520
RANDOM_SEED: Final[int] = 42

random.seed(RANDOM_SEED)

# ── Catalog Data ─────────────────────────────────────────────────────────────
CATEGORIES: dict[str, dict] = {
    "Electronics": {
        "adjectives": ["Wireless", "Smart", "Ultra", "Pro", "Compact", "Portable", "4K", "Bluetooth", "AI-Powered"],
        "nouns":      ["Headphones", "Speaker", "Monitor", "Keyboard", "Mouse", "Webcam", "Charger",
                       "Earbuds", "Smartwatch", "Tablet", "Laptop Stand", "USB Hub", "Microphone"],
        "desc_templates": [
            "High-performance {adj} {noun} with advanced noise-cancellation and {feat}.",
            "Experience crystal-clear audio with this {adj} {noun} featuring {feat}.",
            "Engineered for professionals, this {adj} {noun} delivers {feat} and seamless connectivity.",
            "Next-generation {adj} {noun} powered by AI with {feat}.",
        ],
        "features": ["40-hour battery life", "fast charging", "multi-device pairing", "USB-C connectivity",
                     "HD video support", "low-latency streaming", "ergonomic design", "touch controls"],
        "tags_pool": ["wireless", "bluetooth", "tech", "gadget", "portable", "audio", "smart", "usb-c",
                      "productivity", "streaming", "noise-cancelling", "ergonomic"],
        "price_range": (19.99, 499.99),
    },
    "Books": {
        "adjectives": ["Essential", "Illustrated", "Complete", "Beginner's", "Advanced", "Comprehensive", "Definitive"],
        "nouns":      ["Guide", "Handbook", "Manual", "Encyclopedia", "Workbook", "Anthology",
                       "Primer", "Compendium", "Atlas", "Journal"],
        "desc_templates": [
            "A {adj} {noun} covering {feat} with real-world examples and exercises.",
            "This bestselling {adj} {noun} on {feat} has transformed how professionals learn.",
            "From basics to mastery: the {adj} {noun} for anyone interested in {feat}.",
            "Packed with insights, this {adj} {noun} explores {feat} in depth.",
        ],
        "features": ["machine learning", "data science", "history", "philosophy", "creative writing",
                     "software engineering", "biohacking", "economics", "psychology", "astronomy"],
        "tags_pool": ["book", "learning", "education", "reference", "nonfiction", "fiction",
                      "bestseller", "knowledge", "reading", "study"],
        "price_range": (9.99, 59.99),
    },
    "Fitness": {
        "adjectives": ["Professional", "Heavy-Duty", "Adjustable", "Resistance", "Compact", "Premium", "Foldable"],
        "nouns":      ["Dumbbells", "Resistance Bands", "Yoga Mat", "Pull-Up Bar", "Jump Rope",
                       "Foam Roller", "Kettlebell", "Ab Wheel", "Balance Board", "Exercise Bike"],
        "desc_templates": [
            "{adj} {noun} designed for home and gym use, featuring {feat}.",
            "Build strength at home with this {adj} {noun} — perfect for {feat}.",
            "Durable and versatile, the {adj} {noun} supports {feat} training regimens.",
            "Elevate your workout with this {adj} {noun} optimized for {feat}.",
        ],
        "features": ["full-body workouts", "core training", "cardio sessions", "flexibility exercises",
                     "HIIT routines", "strength building", "recovery sessions", "yoga practice"],
        "tags_pool": ["fitness", "gym", "workout", "health", "exercise", "strength", "cardio",
                      "yoga", "home-gym", "recovery", "training"],
        "price_range": (14.99, 299.99),
    },
    "Kitchen": {
        "adjectives": ["Non-Stick", "Stainless Steel", "Eco-Friendly", "Multi-Function", "Cast Iron",
                       "Ceramic", "BPA-Free", "Insulated"],
        "nouns":      ["Pan", "Pot", "Blender", "Air Fryer", "Coffee Maker", "Cutting Board",
                       "Knife Set", "Instant Pot", "Toaster", "Food Processor", "Dutch Oven"],
        "desc_templates": [
            "{adj} {noun} built for {feat} — perfect for everyday cooking and entertaining.",
            "Professional-grade {adj} {noun} engineered for {feat} and easy cleanup.",
            "The {adj} {noun} every kitchen needs for {feat}.",
            "Cook smarter with this {adj} {noun}, ideal for {feat}.",
        ],
        "features": ["meal prep", "slow cooking", "quick sautéing", "baking", "deep frying",
                     "pressure cooking", "smoothie making", "precision slicing", "batch cooking"],
        "tags_pool": ["kitchen", "cooking", "food", "chef", "baking", "meal-prep", "healthy-eating",
                      "eco-friendly", "nonstick", "appliance"],
        "price_range": (12.99, 349.99),
    },
    "Clothing": {
        "adjectives": ["Slim-Fit", "Relaxed", "Moisture-Wicking", "Organic", "Thermal", "Stretch",
                       "Windproof", "Breathable", "Recycled"],
        "nouns":      ["T-Shirt", "Hoodie", "Joggers", "Jacket", "Leggings", "Shorts",
                       "Polo", "Vest", "Sweatshirt", "Track Pants"],
        "desc_templates": [
            "{adj} {noun} crafted for {feat} with premium sustainable materials.",
            "Stay comfortable all day in this {adj} {noun}, designed for {feat}.",
            "Versatile {adj} {noun} that transitions seamlessly from {feat} to casual wear.",
            "Performance-ready {adj} {noun} built for {feat} in any weather.",
        ],
        "features": ["athletic performance", "everyday comfort", "outdoor adventures", "travel",
                     "yoga sessions", "running", "office wear", "weekend lounging"],
        "tags_pool": ["clothing", "fashion", "apparel", "activewear", "sustainable", "comfort",
                      "organic", "style", "sportswear", "eco-friendly"],
        "price_range": (19.99, 149.99),
    },
    "Beauty": {
        "adjectives": ["Hydrating", "Organic", "Vegan", "SPF-Protected", "Anti-Aging", "Brightening",
                       "Soothing", "Purifying", "Nourishing"],
        "nouns":      ["Moisturizer", "Serum", "Face Wash", "Sunscreen", "Eye Cream",
                       "Toner", "Lip Balm", "Body Lotion", "Face Mask", "Exfoliant"],
        "desc_templates": [
            "{adj} {noun} formulated with natural ingredients for {feat}.",
            "Dermatologist-tested {adj} {noun} for {feat} and long-lasting radiance.",
            "Achieve glowing skin with this {adj} {noun} designed for {feat}.",
            "Luxury skincare: {adj} {noun} packed with actives for {feat}.",
        ],
        "features": ["daily hydration", "anti-aging benefits", "oil control", "sensitive skin",
                     "UV protection", "brightening", "pore minimizing", "overnight repair"],
        "tags_pool": ["beauty", "skincare", "vegan", "organic", "spf", "moisturizing",
                      "anti-aging", "cruelty-free", "clean-beauty", "glow"],
        "price_range": (8.99, 119.99),
    },
    "Home Decor": {
        "adjectives": ["Minimalist", "Boho", "Scandinavian", "Rustic", "Modern", "Vintage",
                       "Industrial", "Coastal", "Artisan"],
        "nouns":      ["Wall Art", "Throw Pillow", "Candle", "Vase", "Picture Frame",
                       "Bookshelf", "Table Lamp", "Mirror", "Rug", "Planter"],
        "desc_templates": [
            "{adj} {noun} that adds character and warmth to any {feat} space.",
            "Hand-crafted {adj} {noun} inspired by {feat} design traditions.",
            "Transform your room with this {adj} {noun}, perfect for {feat} aesthetics.",
            "Elegant {adj} {noun} designed to complement {feat} interior styles.",
        ],
        "features": ["living room", "bedroom", "home office", "Scandinavian", "bohemian",
                     "mid-century modern", "coastal", "minimalist", "eclectic"],
        "tags_pool": ["home-decor", "interior-design", "minimalist", "boho", "rustic", "modern",
                      "handmade", "artisan", "cozy", "aesthetic"],
        "price_range": (14.99, 249.99),
    },
    "Gaming": {
        "adjectives": ["Mechanical", "RGB", "Wireless", "Ergonomic", "Ultra-Light", "Pro", "Wired", "Optical"],
        "nouns":      ["Gaming Mouse", "Mechanical Keyboard", "Headset", "Controller", "Mouse Pad",
                       "Gaming Chair", "Monitor", "Capture Card", "Stream Deck", "GPU Cooler"],
        "desc_templates": [
            "{adj} {noun} engineered for competitive gaming with {feat}.",
            "Dominate the game with this {adj} {noun} featuring {feat}.",
            "Professional-grade {adj} {noun} built for {feat} and marathon sessions.",
            "The {adj} {noun} trusted by esports pros — delivers {feat}.",
        ],
        "features": ["ultra-low latency", "customizable RGB lighting", "tactile switches", "6-axis tracking",
                     "surround sound", "anti-ghosting", "hot-swap switches", "60Hz+ refresh rate"],
        "tags_pool": ["gaming", "esports", "rgb", "mechanical", "fps", "mmorpg", "streamer",
                      "controller", "peripheral", "pc-gaming"],
        "price_range": (24.99, 599.99),
    },
}


def _generate_product(product_id: int, category: str, catalog: dict) -> dict[str, str | float]:
    """Build a single product record."""
    adj  = random.choice(catalog["adjectives"])
    noun = random.choice(catalog["nouns"])
    feat = random.choice(catalog["features"])
    tmpl = random.choice(catalog["desc_templates"])

    name        = f"{adj} {noun}"
    description = tmpl.format(adj=adj, noun=noun, feat=feat)

    # Sample 3-6 tags; always include the category slug
    n_tags = random.randint(3, 6)
    tags   = random.sample(catalog["tags_pool"], min(n_tags, len(catalog["tags_pool"])))
    tags.append(category.lower().replace(" ", "-"))
    tags   = list(dict.fromkeys(tags))  # deduplicate while preserving order

    lo, hi = catalog["price_range"]
    price  = round(random.uniform(lo, hi), 2)

    return {
        "Product_ID":   product_id,
        "Product_Name": name,
        "Category":     category,
        "Description":  description,
        "Tags":         ", ".join(tags),
        "Price":        price,
    }


def generate_dataset(num_products: int = NUM_PRODUCTS, output: pathlib.Path = OUTPUT_PATH) -> None:
    """Generate the synthetic product CSV and write it to disk."""
    categories  = list(CATEGORIES.keys())
    fieldnames  = ["Product_ID", "Product_Name", "Category", "Description", "Tags", "Price"]
    seen_names: set[str] = set()
    records: list[dict] = []

    product_id = 1
    attempts   = 0
    max_attempts = num_products * 5  # guard against infinite loop

    while len(records) < num_products and attempts < max_attempts:
        attempts += 1
        category = categories[len(records) % len(categories)]  # round-robin for balance
        catalog  = CATEGORIES[category]
        record   = _generate_product(product_id, category, catalog)

        # Deduplicate by name
        if record["Product_Name"] not in seen_names:
            seen_names.add(record["Product_Name"])
            records.append(record)
            product_id += 1

    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"✅  Generated {len(records)} products → {output.resolve()}")


if __name__ == "__main__":
    generate_dataset()
