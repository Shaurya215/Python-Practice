# REVIEW 2: Technical Implementation - 15-20 Slides
**Duration**: 15-20 minutes

---

## 📊 **SLIDE STRUCTURE**

### **SLIDE 1: Title Slide**
- **Title**: Review 2 - Technical Implementation
- **Subtitle**: How FlavorForge Works
- **Your Name**, Date

---

### **SLIDE 2: Agenda**
- System Architecture
- Data Preprocessing
- TF-IDF Vectorization
- KNN Algorithm
- Recommendation Process
- Live Demo

---

### **SLIDE 3: System Architecture - Overview**
- **Title**: Complete System Flow
- **Content**: High-level diagram
  ```
  User Input → Preprocessing → TF-IDF → KNN → Recommendations
  ```
- **Visual**: Architecture flowchart

---

### **SLIDE 4: System Architecture - Detailed**
- **Title**: Detailed Architecture
- **Content**: Component breakdown
  - Data Layer
  - Processing Layer
  - ML Layer
  - Output Layer
- **Visual**: Detailed diagram

---

### **SLIDE 5: Dataset Overview**
- **Title**: Dataset Information
- **Content**:
  - File: cuisine_updated.csv
  - Records: 4,415 recipes
  - Columns: name, cuisine, diet, prep_time, ingredients, etc.
- **Visual**: Dataset sample or icon

---

### **SLIDE 6: Step 1 - Data Loading**
- **Title**: Data Loading
- **Content**:
  - Load CSV using pandas
  - Check data structure
  - Initial data exploration
- **Code**: `df = pd.read_csv('cuisine_updated.csv')`
- **Visual**: Code snippet

---

### **SLIDE 7: Step 2 - Data Cleaning**
- **Title**: Data Preprocessing
- **Content**:
  - Remove missing values (dropna)
  - Handle empty fields
  - Ensure data quality
- **Code**: `df.dropna(subset=['cuisine', 'diet', 'prep_time', 'ingredients'])`
- **Visual**: Before/After data comparison

---

### **SLIDE 8: Step 3 - Feature Combination**
- **Title**: Combining Features
- **Content**:
  - Combine: cuisine + diet + prep_time + ingredients
  - Create single text column
  - Why combine? (For TF-IDF processing)
- **Code**: `df['combined_text'] = cuisine + " " + diet + " " + prep_time + " " + ingredients`
- **Visual**: Feature combination diagram

---

### **SLIDE 9: TF-IDF - What is it?**
- **Title**: TF-IDF Introduction
- **Content**:
  - TF (Term Frequency): Word count in document
  - IDF (Inverse Document Frequency): Word rarity
  - Purpose: Convert text to numbers
- **Visual**: TF-IDF concept diagram

---

### **SLIDE 10: TF-IDF - How It Works**
- **Title**: TF-IDF Process
- **Content**:
  - Step 1: Count word frequency
  - Step 2: Calculate IDF weights
  - Step 3: Create vector representation
- **Visual**: Step-by-step process diagram

---

### **SLIDE 11: TF-IDF - Implementation**
- **Title**: TF-IDF Code
- **Content**:
  - Initialize TfidfVectorizer
  - Parameters: max_features=5000, stop_words='english'
  - Fit and transform data
- **Code**: 
  ```python
  vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
  X_combined = vectorizer.fit_transform(df['combined_text'])
  ```
- **Visual**: Code snippet

---

### **SLIDE 12: TF-IDF - Example**
- **Title**: TF-IDF Example
- **Content**:
  - Input: "Indian Vegetarian 30min paneer tomato"
  - Process: Text → TF-IDF calculation
  - Output: Vector [0.2, 0.5, 0.1, 0.8, ...]
- **Visual**: Example calculation

---

### **SLIDE 13: KNN - What is it?**
- **Title**: K-Nearest Neighbors Introduction
- **Content**:
  - Finds K most similar items
  - Uses distance metric
  - Returns nearest neighbors
- **Visual**: KNN concept diagram

---

### **SLIDE 14: KNN - How It Works**
- **Title**: KNN Process
- **Content**:
  - Step 1: Calculate distances
  - Step 2: Find K nearest neighbors
  - Step 3: Return top matches
- **Visual**: KNN visualization

---

### **SLIDE 15: KNN - Cosine Similarity**
- **Title**: Cosine Similarity
- **Content**:
  - Measures angle between vectors
  - Range: 0 to 1
  - Better than euclidean for text
- **Visual**: Cosine similarity diagram

---

### **SLIDE 16: KNN - Implementation**
- **Title**: KNN Code
- **Content**:
  - Initialize NearestNeighbors
  - Parameters: n_neighbors=5, metric='cosine'
  - Train model
- **Code**:
  ```python
  knn = NearestNeighbors(n_neighbors=5, metric='cosine')
  knn.fit(X_combined)
  ```
- **Visual**: Code snippet

---

### **SLIDE 17: Recommendation Process - Step 1**
- **Title**: User Input Processing
- **Content**:
  - User enters preferences
  - Combine into text string
  - Same format as training data
- **Code**: `combined_input = "Indian Vegetarian 30 min paneer"`
- **Visual**: Input processing diagram

---

### **SLIDE 18: Recommendation Process - Step 2**
- **Title**: Vector Transformation
- **Content**:
  - Transform user input using TF-IDF
  - Same vectorizer as training
  - Get user vector representation
- **Code**: `input_vector = vectorizer.transform([combined_input])`
- **Visual**: Transformation diagram

---

### **SLIDE 19: Recommendation Process - Step 3**
- **Title**: Finding Similar Recipes
- **Content**:
  - KNN finds nearest neighbors
  - Calculates cosine distances
  - Returns top 5 matches
- **Code**: `distances, indices = knn.kneighbors(input_vector)`
- **Visual**: Similarity search diagram

---

### **SLIDE 20: Complete Flow Summary**
- **Title**: Complete Process Summary
- **Content**: Full pipeline
  1. Load & clean data
  2. Combine features
  3. TF-IDF vectorization
  4. Train KNN
  5. User input → Transform → Find neighbors → Return results
- **Visual**: Complete flowchart

---

## ⏱️ **TIMING GUIDE**

- **Slides 1-2**: 2 min (Introduction)
- **Slides 3-4**: 3 min (Architecture)
- **Slides 5-8**: 4 min (Data Processing)
- **Slides 9-12**: 5 min (TF-IDF)
- **Slides 13-16**: 4 min (KNN)
- **Slides 17-19**: 3 min (Recommendation Process)
- **Slide 20**: 1 min (Summary)

**Total**: ~22 minutes (can adjust to 15-20 min)

---

## ✅ **CHECKLIST**

- [ ] All 15-20 slides created
- [ ] Code snippets formatted
- [ ] Diagrams created
- [ ] Examples prepared
- [ ] Live demo ready
- [ ] Timing practiced

---

**End of Review 2 Presentation**
