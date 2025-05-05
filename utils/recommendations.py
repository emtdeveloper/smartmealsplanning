import itertools
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from utils.data_processing import calculate_calorie_needs, calculate_macros, filter_foods_by_preference
import logging
from sklearn.preprocessing import MinMaxScaler
from utils.data_processing import filter_recipes_by_allergies_and_cuisines,load_optimized_meals
from utils.user_management import save_meal_plan


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

def recommend_exercises(user_data, exercise_data, num_recommendations=5):
    """
    Recommend exercises based on user's fitness goal and health status
    
    Parameters:
    - user_data: Dict containing user information
    - exercise_data: DataFrame with exercise data
    - num_recommendations: Number of exercises to recommend
    
    Returns:
    - Dict containing recommended exercises by category
    """
    if exercise_data.empty:
        return {"error": "No exercise data available"}
    
    goal = user_data.get('goal', '').lower()
    health_status = user_data.get('health_status', '').lower()
    health_conditions = user_data.get('health_conditions', '').lower()
    
    # Determine appropriate exercise intensity based on health status
    low_intensity = ('underweight' in health_status or 
                    'obese' in health_status or 
                    any(condition in health_conditions for condition in ['heart', 'diabetes', 'respiratory', 'joint']))
    
    # Select exercises based on goal and intensity
    if 'weight loss' in goal:
        # Weight loss: mix of cardio, flexibility, and some strength
        weights = {'Cardio': 0.5, 'Flexibility': 0.3, 'Strength': 0.2}
    elif 'muscle gain' in goal:
        # Muscle gain: emphasis on strength training
        weights = {'Strength': 0.7, 'Cardio': 0.1, 'Flexibility': 0.2}
    else:
        # Balanced approach for maintenance or other goals
        weights = {'Cardio': 0.3, 'Strength': 0.4, 'Flexibility': 0.3}
    
    # Initialize recommendations
    recommendations = {
        "Cardio": [],
        "Strength": [],
        "Flexibility": []
    }
    
    # Map exercise types to categories
    exercise_categories = {
        'Cardio': ['Cardio', 'HIIT', 'Aerobic'],
        'Strength': ['Strength', 'Resistance', 'Weight', 'Bodyweight'],
        'Flexibility': ['Stretch', 'Yoga', 'Mobility', 'Flexibility']
    }
    
    # Define muscle groups to ensure diversity in strength training
    muscle_groups = {
        'Upper Body': ['Shoulder', 'Upper Arms', 'Forearm', 'Chest', 'Back', 'Neck', 'Deltoid', 'Triceps', 'Biceps', 'Pectoralis', 'Latissimus', 'Trapezius'],
        'Core': ['Waist', 'Abs', 'Core', 'Erector Spinae'],
        'Lower Body': ['Hips', 'Thighs', 'Calves', 'Glutes', 'Quadriceps', 'Hamstrings', 'Gastrocnemius', 'Soleus', 'Gluteus Maximus']
    }
    
    # Track selected muscles to ensure diversity
    selected_muscles = []
    
    # First categorize exercises
    categorized_exercises = {
        "Cardio": [],
        "Strength": [],
        "Flexibility": []
    }
    
    for _, exercise in exercise_data.iterrows():
        exercise_type = exercise.get('Equipment Type', '').strip()
        exercise_name = exercise.get('Exercise', '').strip()
        main_muscle = str(exercise.get('Main Muscle', '')).strip()
        
        # Skip exercises with empty names
        if not exercise_name:
            continue
        
        # Categorize the exercise
        category = None
        for cat, keywords in exercise_categories.items():
            if any(keyword.lower() in exercise_type.lower() for keyword in keywords):
                category = cat
                break
        
        # Default to Strength if not categorized but has a valid main muscle group
        if not category:
            if any(muscle.lower() in main_muscle.lower() for group in muscle_groups.values() for muscle in group):
                category = 'Strength'
            else:
                category = 'Flexibility'  # Default to flexibility for general exercises
        
        # Create exercise dictionary
        exercise_dict = {
            "name": exercise_name,
            "type": exercise_type,
            "main_muscle": main_muscle,
            "preparation": exercise.get('Preparation', ''),
            "execution": exercise.get('Execution', ''),
            "target_muscles": exercise.get('Target Muscles', ''),
            "synergist_muscles": exercise.get('Synergist Muscles', '')
        }
        
        # Add to categorized exercises
        categorized_exercises[category].append(exercise_dict)
    
    # Select exercises for each category with focus on diversity for Strength
    if categorized_exercises['Strength']:
        # Group strength exercises by muscle groups
        strength_by_muscle = {
            'Upper Body': [],
            'Core': [],
            'Lower Body': []
        }
        
        for exercise in categorized_exercises['Strength']:
            main_muscle = str(exercise['main_muscle']).lower()
            
            # Assign to a muscle group
            assigned = False
            for group_name, muscles in muscle_groups.items():
                if any(muscle.lower() in main_muscle for muscle in muscles):
                    strength_by_muscle[group_name].append(exercise)
                    assigned = True
                    break
            
            # If not assigned to any group, put in a default group
            if not assigned:
                strength_by_muscle['Core'].append(exercise)
        
        # Select a balanced distribution from each muscle group
        strength_recommendations = []
        
        # Define how many exercises to take from each group
        num_strength = int(num_recommendations * weights['Strength'])
        
        # Allocate proportions based on complete body workout principles
        upper_count = max(1, int(num_strength * 0.4))
        lower_count = max(1, int(num_strength * 0.4))
        core_count = max(1, num_strength - upper_count - lower_count)
        
        # Select exercises from each group
        if strength_by_muscle['Upper Body']:
            strength_recommendations.extend(
                sorted(strength_by_muscle['Upper Body'], key=lambda x: x['name'])[:upper_count]
            )
        
        if strength_by_muscle['Lower Body']:
            strength_recommendations.extend(
                sorted(strength_by_muscle['Lower Body'], key=lambda x: x['name'])[:lower_count]
            )
        
        if strength_by_muscle['Core']:
            strength_recommendations.extend(
                sorted(strength_by_muscle['Core'], key=lambda x: x['name'])[:core_count]
            )
        
        # Fill if we didn't get enough exercises
        while len(strength_recommendations) < num_strength and categorized_exercises['Strength']:
            # Add random exercises that aren't already included
            available = [ex for ex in categorized_exercises['Strength'] 
                         if ex not in strength_recommendations]
            if not available:
                break
                
            strength_recommendations.append(available[0])
        
        recommendations['Strength'] = strength_recommendations
    
    # Fill Cardio and Flexibility categories
    num_cardio = int(num_recommendations * weights['Cardio'])
    if categorized_exercises['Cardio']:
        recommendations['Cardio'] = categorized_exercises['Cardio'][:num_cardio]
    
    num_flexibility = int(num_recommendations * weights['Flexibility'])
    if categorized_exercises['Flexibility']:
        recommendations['Flexibility'] = categorized_exercises['Flexibility'][:num_flexibility]
    
    # If any category is still empty, fill with random exercises from the dataset
    for category, exercises in recommendations.items():
        if not exercises:
            random_exercises = [
                {
                    "name": exercise.get('Exercise', 'Unknown Exercise'),
                    "type": exercise.get('Equipment Type', ''),
                    "main_muscle": exercise.get('Main Muscle', ''),
                    "preparation": exercise.get('Preparation', ''),
                    "execution": exercise.get('Execution', ''),
                    "target_muscles": exercise.get('Target Muscles', ''),
                    "synergist_muscles": exercise.get('Synergist Muscles', '')
                }
                for _, exercise in exercise_data.sample(min(5, len(exercise_data))).iterrows()
                if exercise.get('Exercise', '')
            ]
            
            recommendations[category] = random_exercises[:int(num_recommendations * weights[category])]
    
    return recommendations
