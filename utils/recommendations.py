import itertools
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from utils.data_processing import calculate_calorie_needs, calculate_macros, filter_foods_by_preference
import logging
from sklearn.preprocessing import MinMaxScaler
from utils.data_processing import filter_recipes_by_allergies_and_cuisines,load_optimized_meals
from utils.user_management import save_meal_plan
#added by tushar start
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import os
#end
def load_user_ratings():
    """
    Load user-exercise ratings from CSV or initialize empty DataFrame.
    """
    ratings_file = 'attached_assets/user_exercise_ratings.csv'
    if os.path.exists(ratings_file):
        return pd.read_csv(ratings_file)
    return pd.DataFrame(columns=['user_id', 'exercise_title', 'rating'])
def save_user_ratings(ratings_df):
    """
    Save user-exercise ratings to CSV.
    """
    ratings_df.to_csv('attached_assets/user_exercise_ratings.csv', index=False)

#end

def generate_meal_plan_with_cosine_similarity(user_data, recipes_df, days,meals_per_day):
    """
    Generate a meal plan using cosine similarity to find the best matching meals

    Parameters:
    - user_data: Dict containing user information
    - recipes_df: DataFrame containing recipe information
    - days: Number of days for the plan

    Returns:
    - Dict containing meal plan information or an error message
    """
    # Debug information
    logging.info(f"Generating meal plan for user with data: {user_data}")

    # Extract user profile fields with defaults
    weight = user_data.get('weight', 70)
    height = user_data.get('height', 170)
    age = user_data.get('age', 30)
    gender = user_data.get('gender', 'male').lower()
    goal = user_data.get('goal', 'Maintain Weight')
    activity_level = user_data.get('activity_level', 'moderately_active')

    calories_needed= calculate_calorie_needs(weight, height, age, gender, activity_level, goal)

    # Adjust calories for goals
   
    macros_needed = calculate_macros(calories_needed, goal)    

   
    carbs_goal = macros_needed['carbs']
    protein_goal = macros_needed['protein'] 
    fat_goal = macros_needed['fat']   
    calorie_goal = round((protein_goal * 4) + (carbs_goal * 4) + (fat_goal * 9))
    
    
    
    recipes_df = load_optimized_meals()
    print(f"Loaded {recipes_df.shape[0]} recipes from optimized meals")
    

    # Filter recipes
    allergies = user_data.get('allergies', [])
    preferred_cuisines = user_data.get('preferred_cuisines', [])
    logging.info(f"Filtering recipes with allergies={allergies} and cuisines={preferred_cuisines}")
    filtered_df = filter_recipes_by_allergies_and_cuisines(recipes_df, allergies, preferred_cuisines)
    if filtered_df.empty:
        return {"error": "No recipes available that match your preferences. Try adjusting filters."}
     
     # Build similarity-based week plan
    week_plan = {}
    for meal_type in ['breakfast', 'lunch', 'dinner']:
        meal_df = filtered_df[filtered_df['meal_type'] == meal_type]
        if meal_df.empty:
            return {"error": f"No {meal_type} recipes found. Adjust preferences."}
        print(f"Filtered recipes: {meal_df.shape[0]} recipes available")
        scaler = MinMaxScaler()
        features = ['calories','fat','carbs','protein']

        # Fit on the underlying values array
        scaler = MinMaxScaler()
        scaler.fit(meal_df[features].values)

        # Transform meals
        nutrition_scaled = scaler.transform(meal_df[features].values)

        # Make your user vector as a 2D array of the same shape
        user_vector = np.array([[calorie_goal, fat_goal, carbs_goal, protein_goal]])
        user_scaled = scaler.transform(user_vector)

        similarity = cosine_similarity(user_scaled, nutrition_scaled)[0]
        meal_df = meal_df.copy()
        meal_df['similarity'] = similarity
        week_plan[meal_type] = meal_df.sort_values('similarity', ascending=False).head(days).reset_index(drop=True)

    # Assemble final plan structure
    meal_plan = {
        "user": user_data.get('name', 'User'),
        "daily_calories": round(calorie_goal, 1),
        "macros": {"protein": round(protein_goal), "carbs": round(carbs_goal), "fat": round(fat_goal)},
        "days": []
    }

    for day in range(1, days + 1):
        day_plan = {
            "day": day,
            "meals": [],
            "logged": False 
        }

        total_calories = total_protein = total_carbs = total_fat = 0

        for meal_num, meal_type in enumerate(['breakfast', 'lunch', 'dinner'], 1):
            # Select meal based on similarity, rotate daily
            meal_idx = (day - 1) % len(week_plan[meal_type])
            meal_rec = week_plan[meal_type].iloc[meal_idx]

            meal = {
                "meal_number": meal_num,
                "meal_name": meal_type.capitalize(),
                "foods": [{
                    "name": meal_rec['name'],
                    "calories": meal_rec['calories'],
                    "protein": meal_rec['protein'],
                    "carbs": meal_rec['carbs'],
                    "fat": meal_rec['fat']
                }]
            }

            day_plan["meals"].append(meal)

            # Update running totals
            total_calories += meal_rec['calories']
            total_protein += meal_rec['protein']
            total_carbs += meal_rec['carbs']
            total_fat += meal_rec['fat']

        # Add extra meals/snacks only if calorie goal not yet met
        meal_types_cycle = itertools.cycle(['breakfast', 'lunch', 'dinner'])
        pointers = {'breakfast': 0, 'lunch': 0, 'dinner': 0}

        while total_calories < calorie_goal - 50:  # Small buffer
            current_meal_type = next(meal_types_cycle)
            pointer = pointers[current_meal_type]

            if pointer >= len(week_plan[current_meal_type]):
                continue  # No more meals available

            extra_meal_rec = week_plan[current_meal_type].iloc[pointer]
            pointers[current_meal_type] += 1

            if total_calories + extra_meal_rec['calories'] > calorie_goal + 50:
                # Try to add a fraction of the meal if possible
                remaining_calories = calorie_goal - total_calories
                fraction = remaining_calories / extra_meal_rec['calories']

                if fraction >= 0.4:  # Only add if at least 40% of the meal
                    extra_food = {
                        "name": extra_meal_rec['name'] + f" (x{round(fraction,2)})",
                        "calories": extra_meal_rec['calories'] * fraction,
                        "protein": extra_meal_rec['protein'] * fraction,
                        "carbs": extra_meal_rec['carbs'] * fraction,
                        "fat": extra_meal_rec['fat'] * fraction
                    }

                    lowest_meal = min(day_plan["meals"], key=lambda m: sum(f["calories"] for f in m["foods"]))
                    lowest_meal["foods"].append(extra_food)

                    total_calories += extra_food['calories']
                    total_protein += extra_food['protein']
                    total_carbs += extra_food['carbs']
                    total_fat += extra_food['fat']

                break  # Whether or not fraction added, stop the loop

            else:
                # Normal full addition
                extra_food = {
                    "name": extra_meal_rec['name'],
                    "calories": extra_meal_rec['calories'],
                    "protein": extra_meal_rec['protein'],
                    "carbs": extra_meal_rec['carbs'],
                    "fat": extra_meal_rec['fat']
                }

                lowest_meal = min(day_plan["meals"], key=lambda m: sum(f["calories"] for f in m["foods"]))
                lowest_meal["foods"].append(extra_food)

                total_calories += extra_meal_rec['calories']
                total_protein += extra_meal_rec['protein']
                total_carbs += extra_meal_rec['carbs']
                total_fat += extra_meal_rec['fat']


        # Store totals neatly
        day_plan.update({
            'total_calories': round(total_calories, 1),
            'total_protein': round(total_protein, 1),
            'total_carbs': round(total_carbs, 1),
            'total_fat': round(total_fat, 1)
        })

        meal_plan['days'].append(day_plan)
    user_id = user_data.get("_id")  # Ensure user_data contains the MongoDB user ID
    if user_id:
        save_meal_plan(user_id, meal_plan)
        
        
    return meal_plan


def get_meal_name(meal_number, total_meals):
    """
    Get a meal name based on the meal number and total meals per day
    """
    if total_meals == 3:
        meal_names = {1: "Breakfast", 2: "Lunch", 3: "Dinner"}
        return meal_names.get(meal_number, f"Meal {meal_number}")
    elif total_meals == 5:
        meal_names = {1: "Breakfast", 2: "Morning Snack", 3: "Lunch", 4: "Afternoon Snack", 5: "Dinner"}
        return meal_names.get(meal_number, f"Meal {meal_number}")
    else:
        if meal_number == 1:
            return "Breakfast"
        elif meal_number == total_meals:
            return "Dinner"
        elif meal_number == (total_meals // 2) + 1:
            return "Lunch"
        elif meal_number < (total_meals // 2) + 1:
            return f"Morning Meal {meal_number}"
        else:
            return f"Afternoon Meal {meal_number}"

def recommend_foods_by_goal(user_data, recipe_data, num_recommendations=10):
    """
    Recommend recipes based on user's fitness goal using recipe_details.csv columns
    
    Parameters:
    - user_data: Dict containing user information
    - recipe_data: DataFrame with recipe nutrition data
    - num_recommendations: Number of recipes to recommend
    
    Returns:
    - List of recommended recipes (dicts with name, calories, protein, carbs, fat, image_url, and link)
    """
    # No dietary filtering for now (can be added if needed)
    filtered_recipes = recipe_data.copy()
    if filtered_recipes.empty:
        return []

    # Remove any non-numeric characters (like 'g', '%', etc.)
    unit_cols = ['Protein', 'Fibre', 'Fat_percent', 'Carbs', 'Sugars_percent','Salt_percent','Saturates_percent']
    for col in unit_cols:
        if col in filtered_recipes.columns:
            filtered_recipes[col] = (
                filtered_recipes[col]
                .astype(str)
                .str.replace(r'[^0-9.]+', '', regex=True)
            )
            filtered_recipes[col] = pd.to_numeric(filtered_recipes[col], errors='coerce').fillna(0)

    goal = user_data.get('goal', '').lower()
    scores = []
    for _, recipe in filtered_recipes.iterrows():
        score = 0
        # Skip recipes with missing data
        if pd.isna(recipe.get('Calories', 0)) or recipe.get('Calories', 0) <= 0:
            scores.append(-1)
            continue
        # Weight Loss: Favor high protein, low calories, high fibre
        if 'weight loss' in goal:
            protein_per_calorie = recipe.get('Protein', 0) / max(recipe.get('Calories', 1), 1)
            fibre_per_calorie = recipe.get('Fibre', 0) / max(recipe.get('Calories', 1), 1)
            score = (protein_per_calorie * 5) + (fibre_per_calorie * 3) - (recipe.get('Sugars_percent', 0) * 0.1)
        # Weight Gain: Favor high calories, balanced macros
        elif 'weight gain' in goal:
            calorie_density = recipe.get('Calories', 0) / 100
            protein_ratio = recipe.get('Protein', 0) / max(recipe.get('Calories', 1), 1)
            score = (calorie_density * 3) + (protein_ratio * 2)
        # Muscle Gain: Favor high protein and moderate calories
        elif 'muscle gain' in goal:
            protein_content = recipe.get('Protein', 0)
            protein_ratio = protein_content / max(recipe.get('Calories', 1), 1)
            score = (protein_content * 2) + (protein_ratio * 5)
        # Maintain Weight: Favor balanced, nutrient-dense recipes
        else:
            nutrition_density = (
                recipe.get('Protein', 0) +
                recipe.get('Fibre', 0) * 2
            ) / max(recipe.get('Calories', 1), 1)
            score = nutrition_density * 5
        scores.append(score)
    filtered_recipes_with_scores = filtered_recipes.copy()
    filtered_recipes_with_scores['score'] = scores
    top_recommendations = filtered_recipes_with_scores.sort_values('score', ascending=False).head(num_recommendations)
    recommendations = []
    for _, recipe in top_recommendations.iterrows():
        if recipe.get('score', 0) > 0:
            recommendations.append({
                "name": recipe.get('Product Name', 'Unknown Recipe'),
                "calories": recipe.get('Calories', 0),
                "protein": recipe.get('Protein', 0),
                "carbs": recipe.get('Carbs', 0),
                "fat": recipe.get('Fat_percent', 0),
                "image_url": recipe.get('Image URL', ''),
                "link": recipe.get('Link', ''),
                "ingredients": recipe.get('Ingredients', ''),
                "serves": recipe.get('Serves', ''),
                "time": recipe.get('Time', ''),
                "freezable": recipe.get('Freezable', ''),
                "gluten_free": recipe.get('Gluten-free', ''),
                "dairy_free": recipe.get('Dairy-free', ''),
                "instructions": recipe.get('Instructions', ''),
                "additional_notes": recipe.get('Additional Notes', ''),
                "category": recipe.get('Category Title', ''),
                "Energy_percent": recipe.get('Energy_percent', ''),
                "Energy_kcal": recipe.get('Energy_kcal', ''),
                "Fibre": recipe.get('Fibre', ''),
                "Sugars_percent": recipe.get('Sugars_percent', ''),
                "Salt_percent": recipe.get('Salt_percent', ''),
                "Saturates_percent": recipe.get('Saturates_percent', ''),
                "Recipe Info": recipe.get('Recipe Info', ''),
            })
    return recommendations

def recommend_exercises(user_data, exercise_data, num_recommendations=10):
    """
    Recommend exercises using KNN collaborative filtering combined with rule-based filtering.
    
    Parameters:
    - user_data: Dict with user info (height, weight, age, gender, goal, health_status, health_conditions, activity_level, user_id)
    - exercise_data: DataFrame with exercise data (Title, Type, BodyPart, Equipment, Level, Rating, Desc, RatingDesc)
    - num_recommendations: Total number of exercises to recommend
    
    Returns:
    - Dict with recommended exercises by category (Cardio, Strength, Flexibility)
    """
    if exercise_data.empty:
        return {"error": "No exercise data available"}
    
    # Get user profile attributes
    user_id = user_data.get('user_id', 'default_user')  # Assume user_id is provided
    goal = user_data.get('goal', 'Maintain Weight')
    health_status = user_data.get('health_status', 'Healthy').lower()
    health_conditions = user_data.get('health_conditions', 'None').lower()
    age = user_data.get('age', 30)
    gender = user_data.get('gender', 'male').lower()
    activity_level = user_data.get('activity_level', 'Moderately Active').lower()
    
    # Calculate BMI
    weight = user_data.get('weight', 70)
    height = user_data.get('height', 170)
    bmi = weight / ((height / 100) ** 2)
    
    # Get exercise plan level (1-7)
    exercise_plan = get_exercise_recommendation_plan(user_data)
    
    # Map plan level to intensity
    intensity_level = 'Beginner' if exercise_plan <= 3 else 'Expert' if exercise_plan >= 6 else 'Intermediate'
    
    # Adjust intensity based on health status and conditions
    low_intensity_conditions = ['heart', 'diabetes', 'respiratory', 'joint', 'knee pain', 'back pain']
    if health_status in ['underweight', 'obese', 'poor'] or any(cond in health_conditions for cond in low_intensity_conditions):
        intensity_level = 'Beginner'
    elif health_status == 'moderate':
        intensity_level = min(intensity_level, 'Intermediate', key=lambda x: ['Beginner', 'Intermediate', 'Expert'].index(x))
    
    # Adjust intensity based on age
    age_group = 'Young' if age < 30 else 'Adult' if age <= 50 else 'Older'
    if age_group == 'Older':
        intensity_level = 'Beginner'
    
    # Adjust intensity based on activity level
    activity_map = {
        'sedentary': {'level': 'Beginner', 'days': 3, 'sets': 2},
        'lightly active': {'level': 'Beginner', 'days': 4, 'sets': 3},
        'moderately active': {'level': 'Intermediate', 'days': 5, 'sets': 4},
        'very active': {'level': 'Expert', 'days': 6, 'sets': 5}
    }
    activity_settings = activity_map.get(activity_level, activity_map['moderately active'])
    intensity_level = min(intensity_level, activity_settings['level'], key=lambda x: ['Beginner', 'Intermediate', 'Expert'].index(x))
    
    # Define goal-based weights
    weights = {
        'Weight Loss': {'Cardio': 0.5, 'Strength': 0.3, 'Flexibility': 0.2},
        'Muscle Gain': {'Strength': 0.6, 'Cardio': 0.2, 'Flexibility': 0.2},
        'Weight Gain': {'Strength': 0.7, 'Cardio': 0.1, 'Flexibility': 0.2},
        'Maintain Weight': {'Strength': 0.4, 'Cardio': 0.3, 'Flexibility': 0.3}
    }.get(goal, {'Strength': 0.4, 'Cardio': 0.3, 'Flexibility': 0.3})
    
    # Adjust weights based on gender and age
    for key in weights:
        weights[key] = float(weights.get(key, 0.0))
    if gender == 'female':
        weights['Flexibility'] = min(0.4, weights['Flexibility'] + 0.1)
        weights['Strength'] = max(0.2, weights['Strength'] - 0.05)
        weights['Cardio'] = max(0.1, 1.0 - weights['Strength'] - weights['Flexibility'])
    if age_group == 'Older':
        weights['Flexibility'] = min(0.5, weights['Flexibility'] + 0.2)
        weights['Cardio'] = max(0.2, weights['Cardio'] - 0.1)
        weights['Strength'] = max(0.1, 1.0 - weights['Cardio'] - weights['Flexibility'])
    
    # Normalize weights to sum to 1
    total = sum(weights.values())
    if total > 0:
        for key in weights:
            weights[key] = weights[key] / total
    
    # Load user ratings
    ratings_df = load_user_ratings()
    
    # Initialize recommendations
    recommendations = {
        "Cardio": [],
        "Strength": [],
        "Flexibility": []
    }
    
    # Filter exercise data based on health conditions
    condition_exclusions = {
        'knee pain': {'BodyPart': ['Quadriceps', 'Hamstrings', 'Calves'], 'Type': ['HIIT', 'Plyometrics']},
        'back pain': {'BodyPart': ['Lower Back'], 'Equipment': ['Barbell']},
        'heart': {'Type': ['HIIT', 'Plyometrics'], 'Level': ['Expert']},
        'joint': {'Type': ['Plyometrics'], 'Equipment': ['Barbell']}
    }
    
    df = exercise_data.copy()
    for condition, exclusions in condition_exclusions.items():
        if condition in health_conditions:
            for key, values in exclusions.items():
                df = df[~df[key].str.contains('|'.join(values), case=False, na=False)]
    
    # Filter by intensity level
    allowed_levels = [intensity_level]
    if intensity_level == 'Expert':
        allowed_levels.append('Intermediate')
    elif intensity_level == 'Intermediate':
        allowed_levels.append('Beginner')
    df = df[df['Level'].isin(allowed_levels)]
    
    # Map exercise types to categories
    exercise_categories = {
        'Cardio': ['Cardio', 'HIIT', 'Aerobic'],
        'Strength': ['Strength', 'Olympic Weightlifting', 'Plyometrics', 'Powerlifting', 'Strongman'],
        'Flexibility': ['Stretching', 'Yoga', 'Mobility', 'Flexibility']
    }
    
    # Define muscle groups for Strength diversity
    muscle_groups = {
        'Upper Body': ['Shoulders', 'Chest', 'Upper Back', 'Lats', 'Biceps', 'Triceps', 'Forearms', 'Trapezius'],
        'Core': ['Abdominals', 'Obliques', 'Lower Back', 'Core'],
        'Lower Body': ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves', 'Adductors', 'Abductors']
    }
    
    # Apply KNN collaborative filtering if sufficient ratings are available
    predictions = []
    if not ratings_df.empty:
        # Create user-exercise rating matrix
        rating_matrix = ratings_df.pivot_table(
            index='user_id', 
            columns='exercise_title', 
            values='rating', 
            fill_value=0
        )
        
        # Check number of samples
        n_samples = rating_matrix.shape[0]
        max_neighbors = min(5, n_samples)  # Adjust n_neighbors dynamically
        
        if max_neighbors >= 1:
            # Fit KNN model
            knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=max_neighbors)
            knn.fit(rating_matrix)
            
            # Get user ratings
            if user_id in rating_matrix.index:
                user_ratings = rating_matrix.loc[user_id].values.reshape(1, -1)
            else:
                # For new users, use average ratings
                user_ratings = rating_matrix.mean(axis=0).values.reshape(1, -1)
            
            # Find similar users
            distances, indices = knn.kneighbors(user_ratings, n_neighbors=max_neighbors)
            
            # Get exercises not rated by the user
            all_exercises = exercise_data['Title'].tolist()
            rated_exercises = ratings_df[ratings_df['user_id'] == user_id]['exercise_title'].tolist()
            unrated_exercises = [ex for ex in all_exercises if ex not in rated_exercises]
            
            # Predict ratings based on similar users
            for ex in unrated_exercises:
                if ex in rating_matrix.columns:
                    similar_user_ratings = rating_matrix.iloc[indices[0]][ex]
                    # Weighted average of ratings from similar users (weighted by similarity)
                    similarity_weights = 1 - distances[0]  # Renamed to avoid collision with 'weights'
                    similarity_weights = similarity_weights / similarity_weights.sum()
                    pred_rating = np.average(similar_user_ratings, weights=similarity_weights, axis=0)
                    predictions.append((ex, pred_rating))
                else:
                    predictions.append((ex, 3.0))  # Default for exercises not in rating matrix
        else:
            # Insufficient samples: use default ratings
            predictions = [(title, 3.0) for title in exercise_data['Title'].tolist()]
    else:
        # No ratings: use default ratings
        predictions = [(title, 3.0) for title in exercise_data['Title'].tolist()]
    
    # Fallback to rule-based recommendations if no predictions
    if not predictions:
        # Sort by Rating from exercise_data
        sorted_df = df.sort_values('Rating', ascending=False)
        predictions = [(row['Title'], row.get('Rating', 3.0)) for _, row in sorted_df.iterrows()]
    
    # Categorize predicted exercises
    predicted_exercises = []
    for ex_title, pred_rating in predictions:
        if ex_title not in df['Title'].values:
            continue
        exercise = df[df['Title'] == ex_title].iloc[0]
        exercise_type = exercise.get('Type', '').strip()
        main_muscle = str(exercise.get('BodyPart', '')).strip()
        
        category = None
        for cat, keywords in exercise_categories.items():
            if any(keyword.lower() in exercise_type.lower() for keyword in keywords):
                category = cat
                break
        if not category:
            if any(muscle.lower() in main_muscle.lower() for group in muscle_groups.values() for muscle in group):
                category = 'Strength'
            else:
                category = 'Flexibility'
        
        exercise_dict = {
            "name": ex_title,
            "type": exercise_type,
            "main_muscle": main_muscle,
            "equipment": exercise.get('Equipment', ''),
            "level": exercise.get('Level', ''),
            "description": exercise.get('Desc', ''),
            "rating": exercise.get('Rating', pred_rating),  # Use predicted rating if available
            "rating_desc": exercise.get('RatingDesc', ''),
            "sets": activity_settings['sets'],
            "predicted_rating": pred_rating
        }
        predicted_exercises.append((category, exercise_dict))
    
    # Select exercises for each category
    for category in recommendations:
        num_ex = int(num_recommendations * weights.get(category, 0.0) / sum(weights.values()))
        if not num_ex:
            continue
        
        cat_exercises = [ex for cat, ex in predicted_exercises if cat == category]
        cat_exercises.sort(key=lambda x: x['predicted_rating'], reverse=True)
        
        # For Strength, ensure muscle group diversity
        if category == 'Strength' and cat_exercises:
            strength_by_muscle = {'Upper Body': [], 'Core': [], 'Lower Body': []}
            for ex in cat_exercises:
                main_muscle = str(ex['main_muscle']).lower()
                assigned = False
                for group_name, muscles in muscle_groups.items():
                    if any(muscle.lower() in main_muscle for muscle in muscles):
                        strength_by_muscle[group_name].append(ex)
                        assigned = True
                        break
                if not assigned:
                    strength_by_muscle['Core'].append(ex)
            
            upper_count = max(1, int(num_ex * 0.4))
            lower_count = max(1, int(num_ex * 0.4))
            core_count = max(1, num_ex - upper_count - lower_count)
            
            strength_recommendations = []
            for ex in strength_by_muscle['Upper Body'][:upper_count]:
                strength_recommendations.append(ex)
            for ex in strength_by_muscle['Lower Body'][:lower_count]:
                strength_recommendations.append(ex)
            for ex in strength_by_muscle['Core'][:core_count]:
                strength_recommendations.append(ex)
            
            # Fill remaining slots
            remaining = num_ex - len(strength_recommendations)
            if remaining > 0:
                available = [ex for ex in cat_exercises if ex not in strength_recommendations]
                strength_recommendations.extend(available[:remaining])
            
            recommendations['Strength'] = strength_recommendations
        else:
            recommendations[category] = cat_exercises[:num_ex]
    
    # Fall back to rule-based if insufficient KNN recommendations
    for category, exercises in recommendations.items():
        if len(exercises) < int(num_recommendations * weights.get(category, 0.0) / sum(weights.values())):
            cat_df = df[df['Type'].str.contains('|'.join(exercise_categories[category]), case=False, na=False)]
            if not cat_df.empty:
                num_needed = int(num_recommendations * weights.get(category, 0.0) / sum(weights.values())   ) - len(exercises)
                # Sort by Rating for fallback
                cat_df = cat_df.sort_values('Rating', ascending=False)
                sampled = cat_df.head(min(num_needed, len(cat_df)))
                for _, exercise in sampled.iterrows():
                    exercise_dict = {
                        "name": exercise.get('Title', 'Unknown Exercise'),
                        "type": exercise.get('Type', ''),
                        "main_muscle": exercise.get('BodyPart', ''),
                        "equipment": exercise.get('Equipment', ''),
                        "level": exercise.get('Level', ''),
                        "description": exercise.get('Desc', ''),
                        "rating": exercise.get('Rating', 0),
                        "rating_desc": exercise.get('RatingDesc', ''),
                        "sets": activity_settings['sets'],
                        "predicted_rating": 3.0  # Default rating
                    }
                    recommendations[category].append(exercise_dict)
    
    return recommendations


def calculate_body_fat_percentage(user_data):
    """
    Estimate body fat percentage using the Boer Formula.
    Height is already in cm, so no conversion needed.
    """
    weight = user_data.get('weight', 70)
    height = user_data.get('height', 170)
    age = user_data.get('age', 30)
    gender = user_data.get('gender', 'male').lower()

    if gender == 'female':
        bfp = (0.252 * weight) + (0.131 * height) - 9.0 + (0.1 * age)
    else:  # male or other
        bfp = (0.407 * weight) + (0.267 * height) - 19.2 + (0.1 * age)

    # Apply realistic bounds
    bfp = max(5.0, min(50.0, bfp))
    return bfp

def get_form_points(user_data):
    """
    Calculate form points based on estimated body fat percentage.
    Lower BFP generally indicates better fitness, so higher form points.
    """
    bfp = calculate_body_fat_percentage(user_data)
    # Scale BFP to a 0-100 score (lower BFP = higher form points)
    form_points = max(0, 100 - (bfp * 2))  # Simplified formula
    return form_points

def get_exercise_recommendation_plan(user_data):
    """
    Determine exercise plan level (1-7) based on user metrics.
    """
    bmi = user_data.get('bmi', 0)
    if bmi == 0:  # Calculate BMI if not provided
        weight = user_data.get('weight', 70)
        height = user_data.get('height', 170)
        bmi = weight / ((height / 100) ** 2)
    
    bfp = calculate_body_fat_percentage(user_data)
    age = user_data.get('age', 30)

    # Simplified logic for plan level
    if bfp < 15 and bmi < 25:
        return 7  # Very Challenging
    elif bfp < 20 and bmi < 27:
        return 6  # Challenging
    elif bfp < 25 and bmi < 30:
        return 5  # Moderate to Challenging
    elif bfp < 30 and bmi < 32:
        return 4  # Moderate
    elif bfp < 35 and bmi < 35:
        return 3  # Light to Moderate
    elif bfp < 40:
        return 2  # Light
    else:
        return 1  # Very Light
