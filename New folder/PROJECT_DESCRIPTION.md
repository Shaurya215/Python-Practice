# FlavorForge - AI-Powered Recipe Recommendation System

## Project Overview
**FlavorForge** is a machine learning-based web application that recommends recipes to users based on their preferences for cuisine, diet type, preparation time, and available ingredients. The system uses Natural Language Processing (NLP) and machine learning algorithms to find similar recipes from a dataset.

## Project Name
**FlavorForge** - AI-Powered Recipe Discovery Using TF-IDF and K-Nearest Neighbors

## Core Technology Stack
- **Backend Framework**: Flask (Python web framework)
- **Machine Learning Library**: scikit-learn
- **Data Processing**: pandas, NumPy
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **ML Algorithms**: 
  - TF-IDF (Term Frequency-Inverse Document Frequency) for text vectorization
  - K-Nearest Neighbors (KNN) for similarity matching

## How It Works

### 1. Data Preprocessing
- Loads recipe dataset from CSV file (`cuisine_updated.csv`)
- Dataset contains: recipe name, cuisine, diet, prep_time, ingredients, image_url, description, instructions
- Removes missing values (NaN) from dataset

### 2. Feature Vectorization (TF-IDF)
- Combines recipe features: `cuisine + diet + prep_time + ingredients`
- Converts each feature into a single string
- Applies TF-IDF vectorization to convert text into numerical vectors
- TF-IDF measures importance of words: frequent words in specific recipes get higher weights
- Creates a unified vocabulary from all combined features

### 3. Model Training (K-Nearest Neighbors)
- Combines TF-IDF vectors from all features into a single feature matrix
- Trains KNN model with:
  - `n_neighbors=3` (finds 3 most similar recipes)
  - `metric='euclidean'` (measures distance between vectors)
- Model learns patterns in recipe features

### 4. Recommendation Process
When user submits form:
1. User inputs: cuisine, diet, prep_time, ingredients
2. System transforms user inputs using same TF-IDF vectorizer
3. Combines user's feature vectors
4. KNN finds 3-5 most similar recipes using euclidean distance
5. Returns top recommendations with full details

## Key Features

### User Interface
- **Home Page**: Search form with 4 inputs (Cuisine, Diet, Prep Time, Ingredients)
- **Recipe Cards**: Display recommended recipes with:
  - Recipe image (with fallback for missing images)
  - Recipe name
  - Truncated ingredients preview
  - "View full recipe" button

### Full Recipe Modal
- Clicking "View full recipe" opens a modal showing:
  - Large recipe image
  - Complete recipe name
  - Metadata: Cuisine, Diet, Prep Time
  - About section (description)
  - **Formatted Ingredients List**: Each ingredient in styled boxes with proper alignment
  - **Numbered Instructions**: Step-by-step cooking instructions with circular badges
- Modal can be closed via X button, clicking outside, or pressing Escape key

### Navigation
- **Home**: Main search and recommendations
- **About Us**: Project description and technical details
- **Contact Us**: Developer and project information

## Project Structure
```
Recipe/
├── app.py                    # Flask backend, ML model, routes
├── templates/
│   ├── base.html            # Base template with navbar/footer
│   ├── index.html           # Home page with form and results
│   ├── about.html           # About page
│   └── contact.html         # Contact page
└── Data/
    └── cuisine_updated.csv  # Recipe dataset
```

## Technical Implementation Details

### Backend (app.py)
- **Flask Routes**:
  - `GET/POST /`: Home page with recommendation form
  - `GET /about`: About page
  - `GET /contact`: Contact page

- **ML Pipeline**:
  - Loads CSV → Preprocesses → Trains TF-IDF → Trains KNN → Serves recommendations
  - Custom Jinja filters: `split_ingredients`, `split_instructions` for formatting

- **Data Flow**:
  1. CSV → pandas DataFrame
  2. Text features → TF-IDF vectors
  3. User input → Same TF-IDF transformation
  4. KNN similarity search → Top matches
  5. Results → HTML template

### Frontend (templates/)
- **Responsive Design**: Works on desktop and mobile
- **Modern UI**: Clean cards, smooth animations, professional styling
- **Accessibility**: ARIA labels, keyboard navigation (Escape to close modal)
- **Image Handling**: 
  - `referrerpolicy="no-referrer"` to bypass hotlink protection
  - Fallback SVG placeholder for missing/broken images

## Dataset Information
- **Source**: `cuisine_updated.csv`
- **Columns**: name, image_url, description, cuisine, course, diet, prep_time, ingredients, instructions, image_available
- **Size**: Multiple recipes with Indian and international cuisines
- **Preprocessing**: NaN values filled with empty strings

## Academic Context
- **Project Type**: Machine Learning / Web Technologies
- **Purpose**: Academic demonstration of NLP and ML algorithms
- **Technologies Demonstrated**: 
  - Text vectorization (TF-IDF)
  - Similarity search (KNN)
  - Web application development (Flask)
  - Frontend development (HTML/CSS/JS)

## Key Algorithms Explained

### TF-IDF (Term Frequency-Inverse Document Frequency)
- **Purpose**: Converts text into numerical vectors
- **How it works**:
  - Counts word frequency in each recipe
  - Weights words: common words get lower weight, unique words get higher weight
  - Creates a vector representing each recipe's text features
- **Why used**: Allows mathematical comparison of text-based recipe features

### K-Nearest Neighbors (KNN)
- **Purpose**: Finds most similar recipes
- **How it works**:
  - Calculates euclidean distance between user's input vector and all recipe vectors
  - Returns recipes with smallest distances (most similar)
- **Why used**: Simple, effective for recommendation systems based on feature similarity

## User Experience Flow
1. User visits homepage
2. Enters preferences: cuisine (e.g., "Indian"), diet (e.g., "Vegetarian"), prep_time (e.g., "30 min"), ingredients (e.g., "paneer, sugar")
3. Clicks "Get Recommendations"
4. System processes input, finds similar recipes
5. Displays 3-5 recipe cards
6. User clicks "View full recipe" on any card
7. Modal opens showing complete recipe details with formatted ingredients and instructions
8. User can close modal and try another recipe

## Project Highlights
- ✅ Clean, professional UI suitable for college presentation
- ✅ Full recipe details with proper formatting
- ✅ Responsive design
- ✅ Error handling (missing images, empty data)
- ✅ Academic documentation (About page explains ML concepts)
- ✅ Contact information for project submission

## Development Details
- **Language**: Python 3
- **Framework**: Flask
- **Libraries**: scikit-learn, pandas, NumPy
- **Frontend**: Vanilla JavaScript (no frameworks)
- **Styling**: Custom CSS with CSS variables
- **Fonts**: Google Fonts (Fraunces for headings, DM Sans for body)

---

**This project demonstrates practical application of machine learning algorithms (TF-IDF and KNN) in a real-world web application for recipe recommendation.**
