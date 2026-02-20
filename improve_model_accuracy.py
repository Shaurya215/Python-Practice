"""
Script to improve ML model accuracy for recipe recommendations.
Tests different model parameters and provides recommendations.
"""

import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")

def preprocess_text(text):
    """Enhanced text preprocessing"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    # Remove special characters but keep spaces
    text = re.sub(r'[^\w\s-]', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def create_feature_combinations(df):
    """Create different feature combinations for testing"""
    combinations = {}
    
    # Combination 1: Basic (original)
    combinations['basic'] = (
        df['cuisine'].apply(preprocess_text) + " " + 
        df['diet'].apply(preprocess_text) + " " + 
        df['prep_time'].apply(preprocess_text) + " " + 
        df['ingredients'].apply(preprocess_text)
    )
    
    # Combination 2: Weighted (cuisine and ingredients repeated)
    combinations['weighted'] = (
        df['cuisine'].apply(preprocess_text) + " " + 
        df['cuisine'].apply(preprocess_text) + " " + 
        df['diet'].apply(preprocess_text) + " " + 
        df['prep_time'].apply(preprocess_text) + " " + 
        df['ingredients'].apply(preprocess_text) + " " +
        df['ingredients'].apply(preprocess_text)
    )
    
    # Combination 3: Include description
    combinations['with_description'] = (
        df['cuisine'].apply(preprocess_text) + " " + 
        df['diet'].apply(preprocess_text) + " " + 
        df['prep_time'].apply(preprocess_text) + " " + 
        df['ingredients'].apply(preprocess_text) + " " +
        df['description'].apply(preprocess_text)
    )
    
    # Combination 4: Include course
    combinations['with_course'] = (
        df['cuisine'].apply(preprocess_text) + " " + 
        df['course'].apply(preprocess_text) + " " +
        df['diet'].apply(preprocess_text) + " " + 
        df['prep_time'].apply(preprocess_text) + " " + 
        df['ingredients'].apply(preprocess_text)
    )
    
    return combinations

def test_model_configuration(feature_text, max_features=15000, ngram_range=(1, 3), n_neighbors=10):
    """Test a model configuration and return metrics"""
    try:
        # Create vectorizer
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            ngram_range=ngram_range,
            min_df=2,
            max_df=0.9,
            sublinear_tf=True
        )
        
        # Transform features
        X = vectorizer.fit_transform(feature_text)
        
        # Create KNN model
        knn = NearestNeighbors(
            n_neighbors=n_neighbors,
            metric='cosine',
            algorithm='brute'
        )
        knn.fit(X)
        
        # Calculate average feature density
        avg_features = X.mean()
        
        return {
            'max_features': max_features,
            'ngram_range': ngram_range,
            'n_neighbors': n_neighbors,
            'feature_matrix_shape': X.shape,
            'avg_feature_density': float(avg_features),
            'vocabulary_size': len(vectorizer.vocabulary_)
        }
    except Exception as e:
        return {'error': str(e)}

def evaluate_recommendations(df, knn, vectorizer, test_cases):
    """Evaluate recommendation quality on test cases"""
    results = []
    
    for test_case in test_cases:
        cuisine = preprocess_text(test_case['cuisine'])
        diet = preprocess_text(test_case['diet'])
        prep_time = preprocess_text(test_case['prep_time'])
        ingredients = preprocess_text(test_case['ingredients'])
        
        # Create input
        combined_input = f"{cuisine} {cuisine} {diet} {prep_time} {ingredients} {ingredients}"
        input_vector = vectorizer.transform([combined_input])
        
        # Get recommendations
        distances, indices = knn.kneighbors(input_vector)
        cosine_similarities = 1 - distances[0]
        
        # Check if recommendations match expected cuisine
        recommended_recipes = df.iloc[indices[0]]
        cuisine_match = (recommended_recipes['cuisine'].str.lower() == test_case['cuisine'].lower()).sum()
        
        results.append({
            'test_case': test_case,
            'avg_similarity': float(cosine_similarities.mean()),
            'min_similarity': float(cosine_similarities.min()),
            'cuisine_matches': int(cuisine_match),
            'top_similarity': float(cosine_similarities[0])
        })
    
    return results

def main():
    """Main function to analyze and improve model"""
    print("="*60)
    print("ML MODEL ACCURACY IMPROVEMENT ANALYSIS")
    print("="*60)
    
    # Load dataset
    print("\nLoading dataset...")
    df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
    df = df.dropna(subset=['cuisine', 'diet', 'prep_time', 'ingredients'])
    print(f"Loaded {len(df)} recipes")
    
    # Create feature combinations
    print("\nCreating feature combinations...")
    feature_combinations = create_feature_combinations(df)
    
    # Test different configurations
    print("\nTesting model configurations...")
    print("-"*60)
    
    configs = [
        {'max_features': 10000, 'ngram_range': (1, 2), 'n_neighbors': 7, 'name': 'Current (app_improved.py)'},
        {'max_features': 15000, 'ngram_range': (1, 3), 'n_neighbors': 10, 'name': 'Enhanced'},
        {'max_features': 20000, 'ngram_range': (1, 3), 'n_neighbors': 15, 'name': 'Maximum'},
    ]
    
    best_config = None
    best_score = 0
    
    for config in configs:
        print(f"\nTesting: {config['name']}")
        result = test_model_configuration(
            feature_combinations['weighted'],
            max_features=config['max_features'],
            ngram_range=config['ngram_range'],
            n_neighbors=config['n_neighbors']
        )
        
        if 'error' not in result:
            score = result['avg_feature_density'] * result['vocabulary_size'] / 1000
            print(f"  Features: {result['max_features']}, N-grams: {result['ngram_range']}, Neighbors: {result['n_neighbors']}")
            print(f"  Vocabulary: {result['vocabulary_size']}, Matrix shape: {result['feature_matrix_shape']}")
            print(f"  Score: {score:.2f}")
            
            if score > best_score:
                best_score = score
                best_config = {**config, **result}
        else:
            print(f"  Error: {result['error']}")
    
    # Recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS FOR IMPROVED ACCURACY")
    print("="*60)
    
    if best_config:
        print(f"\n✓ Best configuration: {best_config['name']}")
        print(f"  - max_features: {best_config['max_features']}")
        print(f"  - ngram_range: {best_config['ngram_range']}")
        print(f"  - n_neighbors: {best_config['n_neighbors']}")
        print(f"  - vocabulary_size: {best_config['vocabulary_size']}")
    
    print("\nAdditional improvements:")
    print("1. Increase dataset size (more recipes = better patterns)")
    print("2. Use weighted features (repeat important fields)")
    print("3. Include description field for better context")
    print("4. Use sublinear_tf=True for better normalization")
    print("5. Filter by min_similarity threshold (0.25-0.3)")
    print("6. Consider ensemble methods (combine multiple models)")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
