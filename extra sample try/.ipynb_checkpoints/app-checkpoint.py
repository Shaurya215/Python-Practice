
from flask import Flask, render_template, request
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer

app = Flask(__name__)



# Absolute path example
df = pd.read_csv("/home/petpooja-1084/Downloads/Project CLG/archive/cuisine_updated.csv")

df = df.dropna()

# Preprocess Ingredients
vectorizer = TfidfVectorizer()

vectorizer.fit(df["cuisine"] + " " + df["diet"] + " " + df["prep_time"] + " " + df["ingredients"])

# Now transform each column using the same vocabulary
x_vect_cuisine = vectorizer.transform(df["cuisine"])
x_vect_diet = vectorizer.transform(df["diet"])
x_vect_time = vectorizer.transform(df["prep_time"])
X_ingredients = vectorizer.transform(df["ingredients"])

# Combine transformed features
X_combined = np.hstack([x_vect_cuisine.toarray(), x_vect_diet.toarray(), 
                         x_vect_time.toarray(), X_ingredients.toarray()])


# Train KNN Model
knn = NearestNeighbors(n_neighbors=3, metric='euclidean')
knn.fit(X_combined)


def recommend_recipes(input_features):
    input_ingredients_transformed_1 = vectorizer.transform([input_features[0]])
    input_ingredients_transformed_2 = vectorizer.transform([input_features[1]])
    input_ingredients_transformed_3 = vectorizer.transform([input_features[2]])
    input_ingredients_transformed_4 = vectorizer.transform([input_features[3]])
    input_combined = np.hstack([input_ingredients_transformed_1.toarray(), input_ingredients_transformed_2.toarray(),input_ingredients_transformed_3.toarray(),input_ingredients_transformed_4.toarray()])
    distances, indices = knn.kneighbors(input_combined)
    recommendations = df.iloc[indices[0]]
    return recommendations[['name', 'ingredients', 'image_url']].head(5
                                                                      )
# Function to truncate product name
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cuisine = (request.form['cuisine'])
        diet = (request.form['diet'])
        prep_time = (request.form['prep_time'])
        ingredients = (request.form['ingredients'])
        # cholesterol = float(request.form['cholesterol'])
        # sodium = float(request.form['sodium'])
        # fiber = float(request.form['fiber'])
        # ingredients = request.form['ingredients']
        input_features = [cuisine,diet,prep_time, ingredients]
        recommendations = recommend_recipes(input_features)
        return render_template('index.html', recommendations=recommendations.to_dict(orient='records'),truncate = truncate)
    return render_template('index.html', recommendations=[])

if __name__ == '__main__':
    app.run(debug=True)
