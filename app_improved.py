"""
IMPROVED VERSION - Higher Accuracy Recipe Recommendation
Changes to increase accuracy:
1. Increased TF-IDF features (5000 → 10000)
2. Added ngram_range (1,2) to capture word pairs
3. Better text preprocessing
4. Weighted feature combination
5. Optimized KNN parameters
"""

from flask import Flask, render_template, request, session, jsonify
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'recipe-app-secret-key-change-in-production')

# File to store liked recipes (simple JSON file storage)
LIKED_RECIPES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "liked_recipes.json")

def load_liked_recipes():
    """Load liked recipes from JSON file"""
    if os.path.exists(LIKED_RECIPES_FILE):
        try:
            with open(LIKED_RECIPES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_liked_recipes(liked_recipes):
    """Save liked recipes to JSON file"""
    try:
        with open(LIKED_RECIPES_FILE, 'w', encoding='utf-8') as f:
            json.dump(liked_recipes, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving liked recipes: {e}")
        return False

def get_recipe_by_name(recipe_name):
    """Get recipe by name from dataframe"""
    matches = df[df['name'].str.lower() == recipe_name.lower()]
    if len(matches) > 0:
        recipe = matches.iloc[0].to_dict()
        recipe['image_url'] = fix_image_url(recipe.get('image_url'))
        add_youtube_to_recipe(recipe)
        return recipe
    return None

# Use relative path - works on any computer/location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")

# Load and clean the recipe dataset
df = pd.read_csv(DATA_PATH)

# Clean missing values
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

# IMPROVEMENT 2: Weighted feature combination (give more importance to cuisine and ingredients)
df['combined_text'] = (
    df['cuisine'].apply(preprocess_text) + " " + 
    df['cuisine'].apply(preprocess_text) + " " +  # Repeat cuisine for more weight
    df['diet'].apply(preprocess_text) + " " + 
    df['prep_time'].apply(preprocess_text) + " " + 
    df['ingredients'].apply(preprocess_text) + " " +
    df['ingredients'].apply(preprocess_text)  # Repeat ingredients for more weight
)

# IMPROVEMENT 3: Enhanced TF-IDF parameters for better accuracy
vectorizer = TfidfVectorizer(
    max_features=15000,  # Increased to 15000 for more feature coverage
    stop_words='english',
    ngram_range=(1, 3),  # Captures single words, pairs, AND triplets (e.g., "chicken curry recipe")
    min_df=2,  # Ignore words that appear in less than 2 recipes
    max_df=0.9,  # Tighter filter: ignore words in more than 90% of recipes
    sublinear_tf=True  # Apply sublinear TF scaling (log scale) for better normalization
)
X_combined = vectorizer.fit_transform(df['combined_text'])

# IMPROVEMENT 4: Optimized KNN parameters for better recommendations
knn = NearestNeighbors(
    n_neighbors=10,  # Increased to 10 neighbors for better average recommendations
    metric='cosine',
    algorithm='brute'  # Explicit algorithm
)
knn.fit(X_combined)

def recommend_recipes(input_features):
    # IMPROVEMENT 5: Same preprocessing for user input
    cuisine = preprocess_text(input_features[0])
    diet = preprocess_text(input_features[1])
    prep_time = preprocess_text(input_features[2])
    ingredients = preprocess_text(input_features[3])
    
    # Weighted combination (same as training)
    combined_input = f"{cuisine} {cuisine} {diet} {prep_time} {ingredients} {ingredients}"
    
    # Transform the combined input using the same TF-IDF vectorizer
    input_vector = vectorizer.transform([combined_input])
    
    # Find nearest neighbors
    distances, indices = knn.kneighbors(input_vector)
    
    # IMPROVEMENT 6: Enhanced similarity filtering with dynamic threshold
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
    
    # Get recommended recipes
    recommendations = df.iloc[valid_indices]
    
    # Select relevant columns for display (include youtube_url if exists)
    cols = ['name', 'ingredients', 'image_url', 'cuisine', 'diet', 'prep_time', 'description', 'instructions']
    if 'youtube_url' in df.columns:
        cols.append('youtube_url')
    out = recommendations[[c for c in cols if c in df.columns]].fillna('').head(5)
    return out

# Function to truncate product name
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text

# Custom filter to split ingredients into list
def split_ingredients(text):
    if not text:
        return []
    return [item.strip() for item in str(text).split(',') if item.strip()]

# Custom filter to split instructions into steps
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

# Placeholder when image URL is invalid or blocked
PLACEHOLDER_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect fill='%23f0ebe3' width='400' height='300'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='14'%3ERecipe Image%3C/text%3E%3C/svg%3E"

# Load local image mapping if exists (run download_images.py first)
IMAGE_MAPPING = {}
_mapping_path = os.path.join(BASE_DIR, "image_mapping.json")
if os.path.exists(_mapping_path):
    import json
    with open(_mapping_path) as f:
        IMAGE_MAPPING = json.load(f)

def fix_image_url(url):
    """Use local image if downloaded, else original URL, else placeholder."""
    if pd.isna(url) or not str(url).strip():
        return PLACEHOLDER_IMAGE
    url = str(url).strip()
    if not any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
        return PLACEHOLDER_IMAGE
    if url in IMAGE_MAPPING:
        return IMAGE_MAPPING[url]
    return url

def get_youtube_video_id(url):
    """Extract YouTube video ID from url."""
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
    """Add youtube_video_id and youtube_search_url to recipe."""
    name = recipe.get('name', '')
    vid = get_youtube_video_id(recipe.get('youtube_url'))
    if not vid and name in YOUTUBE_MAPPING:
        vid = YOUTUBE_MAPPING[name]
    recipe['youtube_video_id'] = vid
    from urllib.parse import quote_plus
    recipe['youtube_search_url'] = 'https://www.youtube.com/results?search_query=' + quote_plus(name)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cuisine = (request.form['cuisine'])
        diet = (request.form['diet'])
        prep_time = (request.form['prep_time'])
        ingredients = (request.form['ingredients'])
        input_features = [cuisine, diet, prep_time, ingredients]
        recommendations = recommend_recipes(input_features)
        recs = recommendations.to_dict(orient='records')
        for r in recs:
            r['image_url'] = fix_image_url(r.get('image_url'))
            add_youtube_to_recipe(r)
        return render_template('index.html', recommendations=recs, truncate=truncate)
    return render_template('index.html', recommendations=[])

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search recipes by name, cuisine, ingredients, etc."""
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
def like_recipe():
    """Add or remove recipe from favorites"""
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
def favorites():
    """View all liked/favorite recipes"""
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
