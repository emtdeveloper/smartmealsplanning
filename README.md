# 🍽️ Smart Meal & Activity Planner (SMA)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Framework-Streamlit-red)
![Pandas](https://img.shields.io/badge/Data-Pandas-blueviolet)
![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange)
![Matplotlib](https://img.shields.io/badge/Visualization-Matplotlib-green)

---

## 📖 Overview

The **Smart Meal & Activity Planner (SMA)** is a user-centric web application built using Streamlit. It provides personalized meal recommendations based on content-based filtering, user's dietary preferences, fitness goals, activity levels, and nutritional needs. SMA intelligently suggests optimized meals tailored to individual users using advanced machine learning techniques.

---

## 🚀 Key Features

- **Personalized Meal Planning**
  - Custom meal plans based on user-specific dietary restrictions, fitness goals, and activity levels.
  - Dynamic calorie and macronutrient targets calculation.
  
- **Content-Based Filtering**
  - Cosine similarity used to match meals with user’s nutritional goals precisely.
  - Intelligent dietary filtering (Vegetarian, Vegan, Non-Vegetarian).
  
- **User Profile Management**
  - BMI calculation & tracking.
  - Easy profile creation and updating, including weight progress tracking.
  
- **Visual Analytics**
  - Macronutrient distribution visualization.
  - Meal plan calories and nutritional content visualization.

- **Interactive Interface**
  - Easy-to-navigate Streamlit frontend.
  - Dynamic search and exploration of the food database.

---

## 🛠️ Tech Stack

- **Python**: Main programming language for the project
- **Streamlit**: Front-end interactive UI
- **Pandas**: Data manipulation & processing
- **Scikit-Learn**: Machine learning functions & cosine similarity
- **Matplotlib**: Visualization of nutritional data
- **JSON**: Simple and effective data storage

## 📋 Prerequisites

Make sure you have **Python 3.8 or higher** installed.

Install the required Python libraries by running:

```bash
pip install -r requirements.txt
```

## ▶️ How to Run

### 1. Clone the repository

```bash
git clone https://github.com/emtdeveloper/SMA.git
cd SMA
```

2. Install dependencies
Make sure you have Python 3.8 or higher installed. Then, install the required libraries:

```bash
pip install -r requirements.txt
```
⚠️ If requirements.txt is missing, install manually:

```bash
pip install streamlit pandas numpy scikit-learn
```
3. Launch the Streamlit app
```bash
streamlit run app.py
```

4. Open your browser
Go to the URL displayed in your terminal (usually http://localhost:8501) to view the app


## 📋 Prerequisites

Make sure you have **Python 3.8 or higher** installed.

Install the required Python libraries by running:

```bash
pip install -r requirements.txt
```
## ▶️ How to Run

### 1. Clone the repository

```bash
git clone https://github.com/emtdeveloper/SMA.git
cd SMA
```

2. Install dependencies
Make sure you have Python 3.8 or higher installed. Then, install the required libraries:

```bash
pip install -r requirements.txt
```
⚠️ If requirements.txt is missing, install manually:

```bash
pip install streamlit pandas numpy scikit-learn
```
3. Launch the Streamlit app
```bash
streamlit run app.py
```
incluse your .env files with openAI API key and MongoDB URI. and change st.secrects[] to loaddotenv to access the keys


4. Open your browser
Go to the URL displayed in your terminal (usually http://localhost:8501) to view the app
