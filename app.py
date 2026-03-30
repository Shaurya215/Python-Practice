
"""
Baseline Flask application for the recipe recommendation system.

This version uses a simple content‑based recommender:
    - Combines cuisine, diet, prep time and ingredients into one text field
    - Uses TF‑IDF to convert text into numeric vectors
    - Uses K‑Nearest‑Neighbors (KNN) with cosine similarity to find similar recipes

`app_improved.py` is a more advanced version with higher accuracy; this file
is useful to show the basic idea first, then compare with the improved model.
"""

from flask import Flask, render_template, request
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
import os

app = Flask(__name__)

# Path setup: always relative to this file, so it works on any machine/location.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")

# ---------------------------------------------------------------------------
# 1. LOAD DATASET AND BUILD TEXT FEATURES
# ---------------------------------------------------------------------------

# Load CSV containing all recipes.
df = pd.read_csv(DATA_PATH)

# Remove rows that are missing core descriptive fields.
df = df.dropna(subset=['cuisine', 'diet', 'prep_time', 'ingredients'])

# Combine the key descriptive columns into a single text field.
df['combined_text'] = (
    df['cuisine'].astype(str) + " " + 
    df['diet'].astype(str) + " " + 
    df['prep_time'].astype(str) + " " + 
    df['ingredients'].astype(str)
)

# Convert the combined text into TF‑IDF vectors (bag‑of‑words features).
vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
X_combined = vectorizer.fit_transform(df['combined_text'])

# Train a KNN model on the TF‑IDF vectors (content‑based recommendation).
knn = NearestNeighbors(n_neighbors=5, metric='cosine')
knn.fit(X_combined)


def recommend_recipes(input_features):
    """
    Recommend recipes for a given [cuisine, diet, prep_time, ingredients] input.

    This function mirrors the feature engineering used during training:
    it creates the same combined text representation and then queries the
    trained KNN model to get the nearest recipes.
    """
    # Combine user inputs into one text string (same format as training data).
    # input_features = [cuisine, diet, prep_time, ingredients]
    combined_input = f"{input_features[0]} {input_features[1]} {input_features[2]} {input_features[3]}"
    
    # Transform the combined input using the same TF‑IDF vectorizer.
    input_vector = vectorizer.transform([combined_input])
    
    # Find nearest neighbors (most similar recipes).
    distances, indices = knn.kneighbors(input_vector)
    
    # Select those recipe rows from the DataFrame.
    recommendations = df.iloc[indices[0]]
    
    # Select relevant columns for display (include youtube_url if it exists).
    cols = ['name', 'ingredients', 'image_url', 'cuisine', 'diet', 'prep_time', 'description', 'instructions']
    if 'youtube_url' in df.columns:
        cols.append('youtube_url')
    out = recommendations[[c for c in cols if c in df.columns]].fillna('').head(5)
    return out
# Helper function to truncate long recipe names for nicer display in the UI.
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text

# Jinja2 filter: turn a comma‑separated ingredient string into a Python list.
def split_ingredients(text):
    if not text:
        return []
    return [item.strip() for item in str(text).split(',') if item.strip()]

# Jinja2 filter: split the long instructions string into individual steps.
def split_instructions(text):
    if not text:
        return []
    text_str = str(text)
    # Try splitting by newlines first
    steps = [s.strip() for s in text_str.split('\n') if s.strip()]
    # If only one step, try splitting by periods
    if len(steps) <= 1:
        steps = [s.strip() for s in text_str.split('. ') if s.strip()]
    # If still one, return as single step
    if len(steps) == 0:
        return [text_str]
    return steps

app.jinja_env.filters['split_ingredients'] = split_ingredients
app.jinja_env.filters['split_instructions'] = split_instructions

# Simple SVG placeholder used when we cannot load a real recipe image.
PLACEHOLDER_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect fill='%23f0ebe3' width='400' height='300'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='14'%3ERecipe Image%3C/text%3E%3C/svg%3E"

# Load local image mapping if it exists (created by `download_images.py`).
IMAGE_MAPPING = {}
_mapping_path = os.path.join(BASE_DIR, "image_mapping.json")
if os.path.exists(_mapping_path):
    import json
    with open(_mapping_path) as f:
        IMAGE_MAPPING = json.load(f)

def fix_image_url(url):
    """
    Use local image if downloaded, else original URL, else placeholder.

    This keeps the frontend logic simple and robust.
    """
    if pd.isna(url) or not str(url).strip():
        return PLACEHOLDER_IMAGE
    url = str(url).strip()
    if not any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
        return PLACEHOLDER_IMAGE
    if url in IMAGE_MAPPING:
        return IMAGE_MAPPING[url]
    return url

def get_youtube_video_id(url):
    """Extract YouTube video ID from url (youtube.com/watch?v=ID or youtu.be/ID)."""
    if not url or pd.isna(url):
        return None
    url = str(url).strip()
    if 'youtube.com/watch?v=' in url:
        try:
            return url.split('v=')[1].split('&')[0]
        except IndexError:
            return None
    if 'youtu.be/' in url:
        try:
            return url.split('youtu.be/')[1].split('?')[0]
        except IndexError:
            return None
    if len(url) == 11 and url.replace('-', '').replace('_', '').isalnum():
        return url
    return None

# Recipe name -> YouTube video ID (add manually in recipe_youtube_mapping.json for embed)
YOUTUBE_MAPPING = {}
_yt_path = os.path.join(BASE_DIR, "recipe_youtube_mapping.json")
if os.path.exists(_yt_path):
    import json
    with open(_yt_path) as f:
        raw = json.load(f)
        YOUTUBE_MAPPING = {k: v for k, v in raw.items() if v and isinstance(v, str) and len(v) == 11}

def add_youtube_to_recipe(recipe):
    """Add youtube_video_id and youtube_search_url to a recipe dictionary."""
    name = recipe.get('name', '')
    vid = get_youtube_video_id(recipe.get('youtube_url'))
    if not vid and name in YOUTUBE_MAPPING:
        vid = YOUTUBE_MAPPING[name]
    recipe['youtube_video_id'] = vid
    from urllib.parse import quote_plus
    recipe['youtube_search_url'] = 'https://www.youtube.com/results?search_query=' + quote_plus(name)

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Main route for the baseline app.

    GET  -> show empty form (no recommendations yet).
    POST -> take user form input, run recommender, and render top recipes.
    """
    if request.method == 'POST':
        cuisine = (request.form['cuisine'])
        diet = (request.form['diet'])
        prep_time = (request.form['prep_time'])
        ingredients = (request.form['ingredients'])
        input_features = [cuisine,diet,prep_time, ingredients]
        recommendations = recommend_recipes(input_features)
        recs = recommendations.to_dict(orient='records')
        for r in recs:
            r['image_url'] = fix_image_url(r.get('image_url'))
            add_youtube_to_recipe(r)
        return render_template('index.html', recommendations=recs, truncate=truncate)
    return render_template('index.html', recommendations=[])


@app.route('/about')
def about():
    """Static About page (used by the project presentation)."""
    return render_template('about.html')


@app.route('/contact')
def contact():
    """Static Contact page."""
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)
