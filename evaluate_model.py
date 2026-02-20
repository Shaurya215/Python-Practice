"""
Model Evaluation Script for FlavorForge Recipe Recommendation System
This script measures the accuracy and quality of TF-IDF + KNN recommendations
"""

import os
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

# Use relative path - works on any computer/location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")

# Load dataset
df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=['cuisine', 'diet', 'prep_time', 'ingredients'])

# Create combined text column
df['combined_text'] = (
    df['cuisine'].astype(str) + " " + 
    df['diet'].astype(str) + " " + 
    df['prep_time'].astype(str) + " " + 
    df['ingredients'].astype(str)
)

# Split data for evaluation (80% train, 20% test)
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# Train TF-IDF on training data
vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
X_train = vectorizer.fit_transform(train_df['combined_text'])
X_test = vectorizer.transform(test_df['combined_text'])

# Train KNN model
knn = NearestNeighbors(n_neighbors=5, metric='cosine')
knn.fit(X_train)

print("=" * 60)
print("MODEL EVALUATION REPORT")
print("=" * 60)
print(f"\nDataset Size: {len(df)} recipes")
print(f"Training Set: {len(train_df)} recipes")
print(f"Test Set: {len(test_df)} recipes")
print("\n" + "-" * 60)

# 1. Average Similarity Score (Cosine Similarity)
print("\n1. AVERAGE SIMILARITY SCORE")
print("-" * 60)
similarities = []
for i in range(min(100, len(test_df))):  # Test on 100 samples
    test_vector = X_test[i:i+1]
    distances, indices = knn.kneighbors(test_vector, n_neighbors=5)
    # Convert cosine distance to similarity (1 - distance)
    cosine_similarities = 1 - distances[0]
    similarities.extend(cosine_similarities)

avg_similarity = np.mean(similarities)
print(f"Average Cosine Similarity: {avg_similarity:.4f} ({avg_similarity*100:.2f}%)")
print(f"Min Similarity: {np.min(similarities):.4f}")
print(f"Max Similarity: {np.max(similarities):.4f}")
print(f"Interpretation: {'Excellent' if avg_similarity > 0.7 else 'Good' if avg_similarity > 0.5 else 'Needs Improvement'}")

# 2. Feature Matching Accuracy
print("\n2. FEATURE MATCHING ACCURACY")
print("-" * 60)
cuisine_matches = []
diet_matches = []
prep_time_matches = []

for i in range(min(100, len(test_df))):
    test_recipe = test_df.iloc[i]
    test_vector = X_test[i:i+1]
    distances, indices = knn.kneighbors(test_vector, n_neighbors=5)
    
    # Get recommended recipes
    recommended = train_df.iloc[indices[0]]
    
    # Check how many match each feature
    cuisine_match = (recommended['cuisine'] == test_recipe['cuisine']).sum()
    diet_match = (recommended['diet'] == test_recipe['diet']).sum()
    prep_match = (recommended['prep_time'] == test_recipe['prep_time']).sum()
    
    cuisine_matches.append(cuisine_match / 5)  # Out of 5 recommendations
    diet_matches.append(diet_match / 5)
    prep_time_matches.append(prep_match / 5)

print(f"Cuisine Match Accuracy: {np.mean(cuisine_matches)*100:.2f}%")
print(f"Diet Match Accuracy: {np.mean(diet_matches)*100:.2f}%")
print(f"Prep Time Match Accuracy: {np.mean(prep_time_matches)*100:.2f}%")
print(f"Overall Feature Match: {(np.mean(cuisine_matches) + np.mean(diet_matches) + np.mean(prep_time_matches))/3*100:.2f}%")

# 3. Self-Consistency Test (Leave-One-Out)
print("\n3. SELF-CONSISTENCY TEST")
print("-" * 60)
print("Testing: If we recommend recipes similar to a known recipe,")
print("do we get recipes with matching features?")

consistency_scores = []
for i in range(min(50, len(test_df))):
    test_recipe = test_df.iloc[i]
    test_vector = X_test[i:i+1]
    distances, indices = knn.kneighbors(test_vector, n_neighbors=5)
    
    recommended = train_df.iloc[indices[0]]
    
    # Score: How many recommendations match at least 2 features?
    matches = (
        (recommended['cuisine'] == test_recipe['cuisine']).astype(int) +
        (recommended['diet'] == test_recipe['diet']).astype(int) +
        (recommended['prep_time'] == test_recipe['prep_time']).astype(int)
    )
    consistency = (matches >= 2).sum() / 5
    consistency_scores.append(consistency)

print(f"Consistency Score: {np.mean(consistency_scores)*100:.2f}%")
print("(Percentage of recommendations matching at least 2 features)")

# 4. Diversity Score (Are recommendations diverse?)
print("\n4. RECOMMENDATION DIVERSITY")
print("-" * 60)
diversity_scores = []
for i in range(min(100, len(test_df))):
    test_vector = X_test[i:i+1]
    distances, indices = knn.kneighbors(test_vector, n_neighbors=5)
    recommended = train_df.iloc[indices[0]]
    
    # Count unique cuisines in recommendations
    unique_cuisines = recommended['cuisine'].nunique()
    diversity_scores.append(unique_cuisines / 5)

print(f"Average Unique Cuisines per Recommendation Set: {np.mean(diversity_scores):.2f} out of 5")
print(f"Diversity Score: {np.mean(diversity_scores)*100:.2f}%")
print("(Higher = more diverse recommendations)")

# 5. Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"\n✅ Average Similarity: {avg_similarity*100:.2f}%")
print(f"✅ Feature Match Accuracy: {(np.mean(cuisine_matches) + np.mean(diet_matches) + np.mean(prep_time_matches))/3*100:.2f}%")
print(f"✅ Consistency Score: {np.mean(consistency_scores)*100:.2f}%")
print(f"✅ Diversity Score: {np.mean(diversity_scores)*100:.2f}%")

overall_score = (
    avg_similarity * 0.4 +  # 40% weight on similarity
    (np.mean(cuisine_matches) + np.mean(diet_matches) + np.mean(prep_time_matches))/3 * 0.4 +  # 40% on feature match
    np.mean(consistency_scores) * 0.2  # 20% on consistency
)

print(f"\n🎯 OVERALL MODEL ACCURACY: {overall_score*100:.2f}%")
print("\n" + "=" * 60)
