"""
Configuration for Recipe EDA Project
Update DATA_PATH if your dataset is in a different location
"""
import os

# Path to recipe dataset - relative to project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), "Recipe", "recipe_final.csv")

# Alternative: Use absolute path if running from different directory
# DATA_PATH = r"C:\Users\shaur\Recipe\recipe_final.csv"
