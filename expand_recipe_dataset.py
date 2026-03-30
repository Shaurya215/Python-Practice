"""
Dataset expansion script for the recipe recommendation system.
==============================================================

Purpose
-------
For a content‑based recommender to work well, we need a reasonably
large and diverse dataset of recipes. This script shows how we can
*synthetically* grow the dataset by:
    - Defining hand‑crafted recipe templates for multiple cuisines.
    - Appending them to the existing CSV file.
    - Removing duplicates by recipe name.

This is very useful in an academic project where:
    - Real scraping / API calls may be slow or limited.
    - We still want to demonstrate how a larger dataset can
      improve coverage and recommendation quality.
"""

import pandas as pd
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "Data", "cuisine_updated.csv")  # Overwrite original

def load_dataset():
    """Load existing dataset from CSV and report the number of recipes."""
    try:
        df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
        print(f"Loaded {len(df)} existing recipes")
        return df
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None

def generate_additional_recipes():
    """
    Generate additional recipe templates in code.

    Notes
    -----
    - In a real production system, new recipes would come from:
        * Public recipe APIs,
        * Web scraping (with permission), or
        * User‑generated content.
    - Here we hard‑code templates so we can easily demonstrate
      dataset expansion in a controlled way.
    """
    
    # Recipe templates with diverse cuisines and diets
    new_recipes = []
    
    # Italian recipes
    italian_recipes = [
        {
            'name': 'Spaghetti Carbonara',
            'cuisine': 'Italian',
            'course': 'Main Course',
            'diet': 'High Protein Non Vegetarian',
            'prep_time': 'Total in 30 M',
            'ingredients': 'spaghetti, eggs, pancetta, parmesan cheese, black pepper, salt',
            'description': 'Classic Roman pasta dish with eggs, cheese, and pancetta.',
            'instructions': 'Cook spaghetti. Fry pancetta. Mix eggs and cheese. Combine hot pasta with pancetta, then add egg mixture off heat. Toss quickly and serve with black pepper.'
        },
        {
            'name': 'Margherita Pizza',
            'cuisine': 'Italian',
            'course': 'Main Course',
            'diet': 'Vegetarian',
            'prep_time': 'Total in 60 M',
            'ingredients': 'pizza dough, tomato sauce, fresh mozzarella, basil leaves, olive oil, salt',
            'description': 'Traditional Italian pizza with fresh tomatoes, mozzarella, and basil.',
            'instructions': 'Preheat oven to 475°F. Roll dough. Spread sauce. Add mozzarella. Bake 12-15 minutes. Top with basil and drizzle olive oil.'
        },
        {
            'name': 'Risotto ai Funghi',
            'cuisine': 'Italian',
            'course': 'Main Course',
            'diet': 'Vegetarian',
            'prep_time': 'Total in 45 M',
            'ingredients': 'arborio rice, mushrooms, onion, white wine, vegetable broth, parmesan cheese, butter, garlic',
            'description': 'Creamy Italian rice dish with mushrooms.',
            'instructions': 'Sauté mushrooms. Cook onion. Add rice and wine. Gradually add hot broth, stirring constantly. Finish with butter and parmesan.'
        }
    ]
    
    # Indian recipes
    indian_recipes = [
        {
            'name': 'Butter Chicken',
            'cuisine': 'Indian',
            'course': 'Main Course',
            'diet': 'High Protein Non Vegetarian',
            'prep_time': 'Total in 90 M',
            'ingredients': 'chicken, yogurt, butter, tomato puree, cream, garam masala, turmeric, cumin, coriander, garlic, ginger',
            'description': 'Creamy and rich Indian curry with tender chicken pieces.',
            'instructions': 'Marinate chicken in yogurt and spices. Grill or pan-fry chicken. Prepare tomato-based sauce with spices. Add cream and cooked chicken. Simmer 15 minutes.'
        },
        {
            'name': 'Palak Paneer',
            'cuisine': 'Indian',
            'course': 'Main Course',
            'diet': 'Vegetarian',
            'prep_time': 'Total in 40 M',
            'ingredients': 'spinach, paneer, onions, tomatoes, garam masala, cumin, coriander, garlic, ginger, cream',
            'description': 'Creamy spinach curry with Indian cottage cheese.',
            'instructions': 'Blanch and puree spinach. Sauté onions and spices. Add tomatoes. Add spinach puree. Add paneer cubes. Simmer and finish with cream.'
        },
        {
            'name': 'Chana Masala',
            'cuisine': 'Indian',
            'course': 'Main Course',
            'diet': 'Vegan',
            'prep_time': 'Total in 50 M',
            'ingredients': 'chickpeas, onions, tomatoes, garam masala, turmeric, cumin, coriander, amchur, garlic, ginger',
            'description': 'Spicy and tangy chickpea curry.',
            'instructions': 'Sauté onions and spices. Add tomatoes. Add cooked chickpeas. Simmer with water. Add amchur for tanginess. Garnish with cilantro.'
        }
    ]
    
    # Chinese recipes
    chinese_recipes = [
        {
            'name': 'Kung Pao Chicken',
            'cuisine': 'Chinese',
            'course': 'Main Course',
            'diet': 'High Protein Non Vegetarian',
            'prep_time': 'Total in 30 M',
            'ingredients': 'chicken, peanuts, bell peppers, dried chilies, soy sauce, rice vinegar, sugar, garlic, ginger, cornstarch',
            'description': 'Spicy Sichuan dish with chicken and peanuts.',
            'instructions': 'Marinate chicken. Stir-fry chicken until cooked. Add vegetables and chilies. Add sauce mixture. Toss with peanuts and serve.'
        },
        {
            'name': 'Mapo Tofu',
            'cuisine': 'Chinese',
            'course': 'Main Course',
            'diet': 'Vegetarian',
            'prep_time': 'Total in 25 M',
            'ingredients': 'tofu, ground meat substitute, doubanjiang, soy sauce, garlic, ginger, scallions, Sichuan peppercorns',
            'description': 'Spicy Sichuan tofu dish with fermented bean paste.',
            'instructions': 'Cut tofu into cubes. Sauté aromatics and doubanjiang. Add tofu and sauce. Simmer gently. Garnish with scallions and Sichuan pepper.'
        }
    ]
    
    # Thai recipes
    thai_recipes = [
        {
            'name': 'Pad Thai',
            'cuisine': 'Thai',
            'course': 'Main Course',
            'diet': 'High Protein Non Vegetarian',
            'prep_time': 'Total in 30 M',
            'ingredients': 'rice noodles, shrimp, eggs, bean sprouts, peanuts, tamarind paste, fish sauce, sugar, lime, garlic',
            'description': 'Classic Thai stir-fried noodle dish.',
            'instructions': 'Soak noodles. Prepare tamarind sauce. Stir-fry shrimp and eggs. Add noodles and sauce. Toss with bean sprouts. Serve with lime and peanuts.'
        },
        {
            'name': 'Green Curry',
            'cuisine': 'Thai',
            'course': 'Main Course',
            'diet': 'High Protein Non Vegetarian',
            'prep_time': 'Total in 45 M',
            'ingredients': 'chicken, green curry paste, coconut milk, eggplant, basil, fish sauce, sugar, kaffir lime leaves',
            'description': 'Aromatic Thai curry with coconut milk.',
            'instructions': 'Fry curry paste. Add coconut milk. Add chicken and vegetables. Simmer until cooked. Season with fish sauce and sugar. Garnish with basil.'
        }
    ]
    
    # Mexican recipes
    mexican_recipes = [
        {
            'name': 'Chicken Tacos',
            'cuisine': 'Mexican',
            'course': 'Main Course',
            'diet': 'High Protein Non Vegetarian',
            'prep_time': 'Total in 40 M',
            'ingredients': 'chicken, tortillas, onions, cilantro, lime, cumin, chili powder, garlic, tomatoes',
            'description': 'Traditional Mexican tacos with seasoned chicken.',
            'instructions': 'Season and cook chicken. Warm tortillas. Serve chicken in tortillas with onions, cilantro, and lime. Add salsa if desired.'
        },
        {
            'name': 'Vegetarian Enchiladas',
            'cuisine': 'Mexican',
            'course': 'Main Course',
            'diet': 'Vegetarian',
            'prep_time': 'Total in 60 M',
            'ingredients': 'tortillas, black beans, cheese, onions, bell peppers, enchilada sauce, cumin, chili powder',
            'description': 'Cheesy vegetarian enchiladas with beans and vegetables.',
            'instructions': 'Sauté vegetables and beans. Fill tortillas. Roll and place in baking dish. Cover with sauce and cheese. Bake 25 minutes.'
        }
    ]
    
    # Combine all recipes
    all_new = italian_recipes + indian_recipes + chinese_recipes + thai_recipes + mexican_recipes
    
    # Add image_available column (default to 0, can be updated later)
    for recipe in all_new:
        recipe['image_url'] = ''
        recipe['image_available'] = 0
    
    return all_new

def expand_dataset(df, target_count=6000):
    """
    Expand the dataset with new recipes until we reach a target size.

    Parameters
    ----------
    df : pandas.DataFrame
        Original dataset loaded from CSV.
    target_count : int
        Desired minimum number of recipes after expansion.
    """
    current_count = len(df)
    print(f"\nCurrent dataset: {current_count} recipes")
    print(f"Target: {target_count} recipes")
    print(f"Need to add: {max(0, target_count - current_count)} recipes\n")
    
    # Generate new recipes
    new_recipes = generate_additional_recipes()
    new_df = pd.DataFrame(new_recipes)
    
    if len(new_df) > 0:
        # Combine with existing
        df_expanded = pd.concat([df, new_df], ignore_index=True)
        
        # Remove duplicates based on name
        df_expanded = df_expanded.drop_duplicates(subset=['name'], keep='first')
        
        print(f"Added {len(new_df)} new recipes")
        print(f"Total recipes after expansion: {len(df_expanded)}")
        print(f"Removed {len(df) + len(new_df) - len(df_expanded)} duplicates")
        
        return df_expanded
    else:
        print("No new recipes generated")
        return df

def analyze_dataset(df):
    """
    Print basic descriptive statistics for the dataset.

    This is helpful when explaining the data distribution to faculty:
    - Number of recipes
    - Top cuisines, diets and courses.
    """
    print("\n" + "="*60)
    print("DATASET ANALYSIS")
    print("="*60)
    print(f"Total recipes: {len(df)}")
    try:
        print(f"\nCuisine distribution:")
        cuisine_counts = df['cuisine'].value_counts().head(10)
        for cuisine, count in cuisine_counts.items():
            print(f"  {cuisine}: {count}")
        
        print(f"\nDiet distribution:")
        diet_counts = df['diet'].value_counts()
        for diet, count in diet_counts.items():
            print(f"  {diet}: {count}")
        
        print(f"\nCourse distribution:")
        course_counts = df['course'].value_counts().head(10)
        for course, count in course_counts.items():
            print(f"  {course}: {count}")
    except Exception as e:
        print(f"Error displaying statistics: {e}")
    print("="*60)

def main():
    """Entry‑point for dataset expansion when running this file as a script."""
    print("="*60)
    print("RECIPE DATASET EXPANSION FOR ML MODEL")
    print("="*60)
    
    # Load dataset
    df = load_dataset()
    if df is None:
        return
    
    # Analyze current dataset
    analyze_dataset(df)
    
    # Expand dataset
    print("\nExpanding dataset...")
    df_expanded = expand_dataset(df, target_count=6000)
    
    # Save expanded dataset
    if len(df_expanded) > len(df):
        df_expanded.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
        print(f"\nSaved expanded dataset to: {OUTPUT_PATH}")
        
        # Analyze expanded dataset
        analyze_dataset(df_expanded)
    else:
        print("\nDataset already at or above target size, or no new recipes added.")
    
    print("\n" + "="*60)
    print("NOTE: To add more recipes, you can:")
    print("1. Use recipe APIs (Spoonacular, Edamam, Recipe Puppy)")
    print("2. Scrape recipe websites (with permission)")
    print("3. Use public datasets from Kaggle")
    print("4. Manually add recipes following the same structure")
    print("="*60)

if __name__ == '__main__':
    main()
