"""
IMPROVED VERSION - Higher Accuracy Recipe Recommendation
=========================================================

This Flask application exposes a web interface where a user can:
    - Enter cuisine, diet, preparation time and ingredients
    - Receive recipe recommendations from a content‑based ML model
    - Search recipes by free‑text query
    - Like / favorite recipes and view them later

Main technical improvements compared to a basic baseline:
1. Richer TF‑IDF representation:
   - More features (max_features=15000)
   - Uses n‑grams up to length 3 (single words, bi‑grams and tri‑grams)
2. Better text preprocessing:
   - Lower‑casing and whitespace normalization
3. Weighted feature combination:
   - Cuisine and ingredients are repeated to give them extra weight
4. Tuned KNN recommender:
   - Cosine similarity with more neighbors and a similarity threshold
5. Simple persistence of “liked recipes” using a JSON file.
"""

from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import os
import json
from functools import wraps

app = Flask(__name__)
# Secret key is required for sessions; in production this should come
# from a secure environment variable, not be hard‑coded.
app.secret_key = os.environ.get('SECRET_KEY', 'recipe-app-secret-key-change-in-production')

# File to store liked recipes (very lightweight file‑based "database").
LIKED_RECIPES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "liked_recipes.json")

# Optional: set FLAVORFORGE_USERNAME and FLAVORFORGE_PASSWORD in the environment
# to require a specific login. If either is unset, any non-empty username + password is accepted.
_FLAVOR_USER = os.environ.get("FLAVORFORGE_USERNAME")
_FLAVOR_PASS = os.environ.get("FLAVORFORGE_PASSWORD")

def load_liked_recipes():
    """
    Load the dictionary of liked recipes from disk.

    Returns
    -------
    dict
        Mapping from recipe name (string) to small metadata dict.
    """
    if os.path.exists(LIKED_RECIPES_FILE):
        try:
            with open(LIKED_RECIPES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_liked_recipes(liked_recipes):
    """
    Persist liked recipes dictionary to a JSON file.

    Parameters
    ----------
    liked_recipes : dict
        Mapping from recipe name to metadata to be written to disk.
    """
    try:
        with open(LIKED_RECIPES_FILE, 'w', encoding='utf-8') as f:
            json.dump(liked_recipes, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving liked recipes: {e}")
        return False

def get_recipe_by_name(recipe_name):
    """
    Look up a single recipe by its exact name in the loaded DataFrame.

    This helper is used both for the favorites feature and when
    we want full details (including fixed image URL and YouTube info)
    for a particular recipe.
    """
    matches = df[df['name'].str.lower() == recipe_name.lower()]
    if len(matches) > 0:
        recipe = matches.iloc[0].to_dict()
        recipe['image_url'] = fix_image_url(recipe.get('image_url'))
        add_youtube_to_recipe(recipe)
        return recipe
    return None

# Use a path that is always relative to this file, so the app works
# regardless of where the project folder is located.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")

# ---------------------------------------------------------------------------
# 1. LOAD DATA AND BUILD FEATURE MATRIX FOR RECOMMENDER
# ---------------------------------------------------------------------------

# Load and lightly clean the recipe dataset from CSV.
df = pd.read_csv(DATA_PATH)

# Drop rows that are missing core descriptive features; they are hard to use
# for a text‑based recommendation model.
df = df.dropna(subset=['cuisine', 'diet', 'prep_time', 'ingredients'])

# IMPROVEMENT 1: Better text preprocessing
def preprocess_text(text):
    """Clean and normalize text"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# IMPROVEMENT 2: Weighted feature combination (give more importance
# to cuisine and ingredients, which are strong signals of similarity).
df['combined_text'] = (
    df['cuisine'].apply(preprocess_text) + " " + 
    df['cuisine'].apply(preprocess_text) + " " +  # Repeat cuisine for more weight
    df['diet'].apply(preprocess_text) + " " + 
    df['prep_time'].apply(preprocess_text) + " " + 
    df['ingredients'].apply(preprocess_text) + " " +
    df['ingredients'].apply(preprocess_text)  # Repeat ingredients for more weight
)

# IMPROVEMENT 3: Enhanced TF‑IDF parameters for better accuracy.
# We project every recipe into a high‑dimensional text feature space.
vectorizer = TfidfVectorizer(
    max_features=15000,  # Increased to 15000 for more feature coverage
    stop_words='english',
    ngram_range=(1, 3),  # Captures single words, pairs, AND triplets (e.g., "chicken curry recipe")
    min_df=2,  # Ignore words that appear in less than 2 recipes
    max_df=0.9,  # Tighter filter: ignore words in more than 90% of recipes
    sublinear_tf=True  # Apply sublinear TF scaling (log scale) for better normalization
)
X_combined = vectorizer.fit_transform(df['combined_text'])

# IMPROVEMENT 4: KNN model over the TF‑IDF vectors.
# NearestNeighbors with cosine distance gives us “similar recipes”
# in terms of their combined text description.
knn = NearestNeighbors(
    n_neighbors=10,  # Increased to 10 neighbors for better average recommendations
    metric='cosine',
    algorithm='brute'  # Explicit algorithm
)
knn.fit(X_combined)

def recommend_recipes(input_features):
    """
    Recommend recipes based on user‑provided filters.

    Parameters
    ----------
    input_features : list[str]
        [cuisine, diet, prep_time, ingredients] from the HTML form.

    Returns
    -------
    pandas.DataFrame
        Top 5 recommended recipes, with key columns ready for display.
    """
    # IMPROVEMENT 5: Apply the same preprocessing to user input as to training data.
    cuisine = preprocess_text(input_features[0])
    diet = preprocess_text(input_features[1])
    prep_time = preprocess_text(input_features[2])
    ingredients = preprocess_text(input_features[3])
    
    # Weighted combination (same as training) to keep the representation consistent.
    combined_input = f"{cuisine} {cuisine} {diet} {prep_time} {ingredients} {ingredients}"
    
    # Transform the combined input using the same TF‑IDF vectorizer.
    input_vector = vectorizer.transform([combined_input])
    
    # Find nearest neighbors
    distances, indices = knn.kneighbors(input_vector)
    
    # IMPROVEMENT 6: Enhanced similarity filtering with a minimum similarity threshold.
    min_similarity = 0.25  # Lowered to 25% to show more results, but still filter low-quality matches
    cosine_similarities = 1 - distances[0]
    valid_indices = [idx for idx, sim in zip(indices[0], cosine_similarities) if sim >= min_similarity]
    
    if len(valid_indices) == 0:
        # If no recipes meet threshold, return top 5 anyway
        valid_indices = indices[0][:5]
    else:
        # Sort by similarity and take top 5
        sorted_pairs = sorted(zip(valid_indices, cosine_similarities[:len(valid_indices)]), 
                            key=lambda x: x[1], reverse=True)
        valid_indices = [idx for idx, _ in sorted_pairs[:5]]
    
    # Select the relevant rows from the original DataFrame.
    recommendations = df.iloc[valid_indices]
    
    # Select relevant columns for display (include youtube_url if it exists).
    cols = ['name', 'ingredients', 'image_url', 'cuisine', 'diet', 'prep_time', 'description', 'instructions']
    if 'youtube_url' in df.columns:
        cols.append('youtube_url')
    out = recommendations[[c for c in cols if c in df.columns]].fillna('').head(5)
    return out

# Helper to truncate long recipe names in the UI so that cards remain tidy.
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text

# Jinja2 filter: split a comma‑separated ingredient string into a clean list.
def split_ingredients(text):
    if not text:
        return []
    return [item.strip() for item in str(text).split(',') if item.strip()]

# Jinja2 filter: split the long instructions text into individual steps.
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

# Fallback SVG image shown when we cannot load a real image.
PLACEHOLDER_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect fill='%23f0ebe3' width='400' height='300'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='14'%3ERecipe Image%3C/text%3E%3C/svg%3E"

# Load local image mapping if it exists.
# NOTE: This mapping is created by running the separate script `download_images.py`.
IMAGE_MAPPING = {}
_mapping_path = os.path.join(BASE_DIR, "image_mapping.json")
if os.path.exists(_mapping_path):
    import json
    with open(_mapping_path) as f:
        IMAGE_MAPPING = json.load(f)

def fix_image_url(url):
    """
    Normalize any recipe image URL so the frontend can safely display it.

    Priority:
    1. If we have a locally downloaded image for this URL, use that.
    2. Else, if the original URL looks like an image, keep it.
    3. Otherwise, fall back to a neutral placeholder SVG.
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
    """
    Extract the 11‑character YouTube video ID from various URL formats.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - Or a bare 11‑character ID.
    """
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

YOUTUBE_MAPPING = {}
_yt_path = os.path.join(BASE_DIR, "recipe_youtube_mapping.json")
if os.path.exists(_yt_path):
    import json
    with open(_yt_path) as f:
        raw = json.load(f)
        YOUTUBE_MAPPING = {k: v for k, v in raw.items() if v and isinstance(v, str) and len(v) == 11}

def add_youtube_to_recipe(recipe):
    """
    Enrich a recipe dictionary with:
        - youtube_video_id: for embedding a specific video (if known)
        - youtube_search_url: fallback search link on YouTube.
    """
    name = recipe.get('name', '')
    vid = get_youtube_video_id(recipe.get('youtube_url'))
    if not vid and name in YOUTUBE_MAPPING:
        vid = YOUTUBE_MAPPING[name]
    recipe['youtube_video_id'] = vid
    from urllib.parse import quote_plus
    recipe['youtube_search_url'] = 'https://www.youtube.com/results?search_query=' + quote_plus(name)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_globals():
    return {
        "PLACEHOLDER_IMAGE": PLACEHOLDER_IMAGE,
        "current_user": session.get("user"),
    }

@app.route('/', methods=['GET'])
def home():
    """Landing page: welcome screen with CTA to login."""
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Session-based login with username and password (no database)."""
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        if not username or not password.strip():
            return render_template(
                'login.html',
                error="Please enter both username and password.",
                username=username,
            )

        if _FLAVOR_USER is not None and _FLAVOR_PASS is not None:
            if username != _FLAVOR_USER or password != _FLAVOR_PASS:
                return render_template(
                    'login.html',
                    error="Invalid username or password.",
                    username=username,
                )

        session['user'] = username
        raw_next = (
            (request.form.get('next') or '').strip()
            or (request.args.get('next') or '').strip()
        )
        if raw_next.startswith('/') and not raw_next.startswith('//'):
            dest = raw_next
        else:
            dest = url_for('app_page')
        return redirect(dest)

    return render_template('login.html', error=None, username='')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/app', methods=['GET', 'POST'])
@login_required
def app_page():
    """
    Recommendations page: accepts user preferences and shows recommended recipes.
    """
    if request.method == 'POST':
        cuisine = (request.form.get('cuisine') or '')
        diet = (request.form.get('diet') or '')
        prep_time = (request.form.get('prep_time') or '')
        ingredients = (request.form.get('ingredients') or '')
        input_features = [cuisine, diet, prep_time, ingredients]
        recommendations = recommend_recipes(input_features)
        recs = recommendations.to_dict(orient='records')
        for r in recs:
            r['image_url'] = fix_image_url(r.get('image_url'))
            add_youtube_to_recipe(r)
        liked_recipes = load_liked_recipes()
        for r in recs:
            r['is_liked'] = r.get('name', '') in liked_recipes
        return render_template('index.html', recommendations=recs, truncate=truncate)
    return render_template('index.html', recommendations=[])

@app.route('/about')
def about():
    """Static About page describing the project."""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Static Contact page for basic project contact info."""
    return render_template('contact.html')

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """
    Free‑text search across multiple columns (name, cuisine, ingredients, etc.).

    This does not use the KNN model; it is a simple substring search that
    is easy for users and faculty to understand.
    """
    query = request.args.get('q', '').strip() if request.method == 'GET' else request.form.get('q', '').strip()
    results = []
    
    if query:
        # Search in multiple fields: name, cuisine, ingredients, description
        query_lower = query.lower()
        
        # Filter recipes that match the query
        mask = (
            df['name'].str.lower().str.contains(query_lower, na=False) |
            df['cuisine'].str.lower().str.contains(query_lower, na=False) |
            df['ingredients'].str.lower().str.contains(query_lower, na=False) |
            df['description'].str.lower().str.contains(query_lower, na=False) |
            df['diet'].str.lower().str.contains(query_lower, na=False)
        )
        
        matching_recipes = df[mask].head(50)  # Limit to 50 results
        
        if len(matching_recipes) > 0:
            results = matching_recipes.to_dict(orient='records')
            for r in results:
                r['image_url'] = fix_image_url(r.get('image_url'))
                add_youtube_to_recipe(r)
    
    # Load liked recipes to show which are favorited
    liked_recipes = load_liked_recipes()
    for r in results:
        r['is_liked'] = r.get('name', '') in liked_recipes
    
    return render_template('search.html', query=query, results=results, truncate=truncate)

@app.route('/like', methods=['POST'])
@login_required
def like_recipe():
    """
    Toggle a recipe in the favorites list (AJAX endpoint).

    If the recipe is not yet liked, it will be added to the JSON file.
    If it is already liked, it will be removed.
    """
    data = request.get_json()
    recipe_name = data.get('recipe_name', '').strip()
    
    if not recipe_name:
        return jsonify({'success': False, 'message': 'Recipe name required'})
    
    liked_recipes = load_liked_recipes()
    
    if recipe_name in liked_recipes:
        # Unlike - remove from favorites
        del liked_recipes[recipe_name]
        action = 'removed'
    else:
        # Like - add to favorites
        recipe = get_recipe_by_name(recipe_name)
        if recipe:
            liked_recipes[recipe_name] = {
                'name': recipe_name,
                'cuisine': recipe.get('cuisine', ''),
                'diet': recipe.get('diet', ''),
                'prep_time': recipe.get('prep_time', ''),
                'image_url': recipe.get('image_url', ''),
                'added_at': pd.Timestamp.now().isoformat()
            }
            action = 'added'
        else:
            return jsonify({'success': False, 'message': 'Recipe not found'})
    
    if save_liked_recipes(liked_recipes):
        return jsonify({'success': True, 'action': action, 'message': f'Recipe {action} from favorites'})
    else:
        return jsonify({'success': False, 'message': 'Error saving favorite'})

@app.route('/favorites')
@login_required
def favorites():
    """
    Show a page with all liked / favorite recipes.

    It merges:
    - Up‑to‑date data from the main DataFrame (if the recipe still exists)
    - Stored snapshot data from the JSON file (as a fallback).
    """
    liked_recipes = load_liked_recipes()
    favorites_list = []
    
    for recipe_name, recipe_data in liked_recipes.items():
        # Try to get full recipe details from dataframe
        recipe = get_recipe_by_name(recipe_name)
        if recipe:
            recipe['is_liked'] = True
            favorites_list.append(recipe)
        else:
            # If not found in dataframe, use stored data
            recipe_data['is_liked'] = True
            recipe_data['image_url'] = fix_image_url(recipe_data.get('image_url', ''))
            favorites_list.append(recipe_data)
    
    return render_template('favorites.html', favorites=favorites_list, truncate=truncate)

if __name__ == '__main__':
    app.run(debug=True)
