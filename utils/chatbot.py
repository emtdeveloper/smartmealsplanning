import re
import random
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class NutritionChatbot:
    def __init__(self, food_data, exercise_data, user_data=None):
        """
        Initialize the nutritional chatbot with food and exercise data
        """
        self.food_data = food_data
        self.exercise_data = exercise_data
        self.user_data = user_data or {}
        
        # Prepare intents
        self.intents = {
            'greeting': [r'hi', r'hello', r'hey', r'greetings', r'good morning', r'good afternoon', r'good evening'],
            'goodbye': [r'bye', r'goodbye', r'see you', r'farewell', r'quit', r'exit'],
            'thanks': [r'thanks', r'thank you', r'appreciate it', r'thank', r'thx'],
            'help': [r'help', r'assist', r'guide', r'instructions', r'how (do|can) I'],
            'food_recommendation': [r'recommend food', r'food suggestion', r'what (should|can) I eat', r'meal idea', r'food to eat'],
            'low_calorie': [r'low(\s|-)calorie', r'low(\s|-)cal', r'diet food', r'fewer calories', r'lose weight'],
            'high_protein': [r'high(\s|-)protein', r'protein rich', r'more protein', r'build muscle', r'protein food'],
            'exercise_recommendation': [r'recommend exercise', r'workout suggestion', r'exercise idea', r'what (should|can) I do for exercise', r'fitness suggestion', r'stretching', r'strength training'],
            'nutrition_info': [r'nutrition (in|of|for)', r'calories in', r'how many calories', r'nutritional value', r'macros in', r'carbs in', r'protein in', r'fat in'],
            'goal_setting': [r'set goal', r'fitness goal', r'weight goal', r'target weight', r'lose \d+ (pounds|kg|kilos)', r'gain \d+ (pounds|kg|kilos)'],
            'water_intake': [r'water intake', r'hydration', r'how much water', r'drink water', r'stay hydrated'],
            'meal_timing': [r'meal timing', r'when (should|to) eat', r'best time to eat', r'eating schedule', r'meal frequency'],
            'cheat_meal': [r'cheat meal', r'cheat day', r'indulge', r'treat', r'dessert', r'sweets', r'junk food'],
            'vitamins': [r'vitamin', r'minerals', r'supplements', r'micronutrient'],
            'weight_loss': [r'lose weight', r'weight loss', r'fat loss', r'burn fat', r'slim down', r'get leaner'],
            'weight_gain': [r'gain weight', r'weight gain', r'bulk', r'bulking', r'gain muscle', r'put on mass'],
            'diet_type': [r'keto', r'paleo', r'vegan', r'vegetarian', r'carnivore', r'mediterranean', r'low(\s|-)carb', r'intermittent fasting'],
            'health_condition': [r'diabetes', r'high blood pressure', r'hypertension', r'cholesterol', r'heart disease', r'celiac', r'gluten', r'allergy']
        }
        
        # Compile regex patterns for each intent
        self.intent_patterns = {}
        for intent, patterns in self.intents.items():
            self.intent_patterns[intent] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def detect_intent(self, message):
        """
        Detect the user's intent from their message
        """
        message = message.lower()
        
        # Multiple intents can be found in a single message
        matched_intents = []
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern.search(message):
                    matched_intents.append(intent)
                    break  # Found one match for this intent, move to next intent
        
        # If found exactly one intent, return it
        if len(matched_intents) == 1:
            return matched_intents[0]
        
        # If found multiple intents, prioritize specific intents over general ones
        if len(matched_intents) > 1:
            # Priority order (most specific to most general)
            priority_order = [
                'food_recommendation', 'exercise_recommendation',
                'low_calorie', 'high_protein', 
                'diet_type', 'health_condition',
                'weight_loss', 'weight_gain',
                'water_intake', 'meal_timing', 'vitamins', 'cheat_meal',
                'nutrition_info', 'goal_setting',
                'greeting', 'goodbye', 'thanks', 'help',
                'general'
            ]
            
            # Return the most specific matching intent
            for intent in priority_order:
                if intent in matched_intents:
                    return intent
        
        # If no intent is matched, return general intent
        return 'general'
    
    def detect_food_query(self, message):
        """
        Check if the message is asking about a specific food
        """
        if not isinstance(self.food_data, pd.DataFrame) or self.food_data.empty:
            return None
        
        # Convert message to lowercase
        message = message.lower()
        
        # First, check if this is about a specific food (using common phrase patterns)
        food_query_patterns = [
            r'what\'s in (.+)\??',
            r'nutrients? in (.+)',
            r'calories in (.+)',
            r'how (healthy|nutritious) is (.+)\??',
            r'tell me about (.+) nutrition',
            r'macros? in (.+)'
        ]
        
        for pattern in food_query_patterns:
            match = re.search(pattern, message)
            if match:
                # Get the food name from the regex match
                if len(match.groups()) == 1:
                    food_term = match.group(1).strip()
                else:
                    food_term = match.group(2).strip()
                
                # Search for this food in our database
                best_match = None
                best_score = 0
                
                for _, food in self.food_data.iterrows():
                    food_name = str(food.get('Food Name', '')).lower()
                    
                    # Check for exact match
                    if food_name == food_term:
                        return food
                    
                    # Check for food name contained in the query term
                    if food_name and food_name in food_term:
                        # Calculate match score based on length ratio
                        score = len(food_name) / len(food_term)
                        if score > best_score:
                            best_score = score
                            best_match = food
                
                # If we found a reasonable match (at least 50% of the query term)
                if best_match is not None and best_score > 0.5:
                    return best_match
        
        # Fallback: Check if any food name in our database is directly mentioned
        for _, food in self.food_data.iterrows():
            food_name = str(food.get('Food Name', '')).lower()
            if food_name and food_name in message and len(food_name) > 3:  # Avoid short names that could be common words
                return food
        
        return None
    
    def detect_exercise_query(self, message):
        """
        Check if the message is asking about a specific exercise
        """
        if not isinstance(self.exercise_data, pd.DataFrame) or self.exercise_data.empty:
            return None
        
        # Convert message to lowercase
        message = message.lower()
        
        # First check if the message is asking about exercises for specific muscle groups
        exercise_query_patterns = [
            r'exercises? for (my )?(.*?) (muscles?|strength|training)',
            r'how to (train|work|exercise) (my )?(.*?)( muscles?)?',
            r'(best|good|recommended|top) (.*?) exercises?',
            r'(strengthen|tone|build) (my )?(.*?)( muscles?)?',
            r'what (exercises?|workouts?) (should I do|are good|can I do) for (my )?(.*?)( muscles?)?'
        ]
        
        for pattern in exercise_query_patterns:
            match = re.search(pattern, message)
            if match:
                # Extract the muscle group from the match
                matched_groups = match.groups()
                if len(matched_groups) >= 3:
                    muscle_term = matched_groups[2].strip() if matched_groups[2] else ''
                    if not muscle_term and len(matched_groups) >= 4:
                        muscle_term = matched_groups[3].strip() if matched_groups[3] else ''
                    
                    if muscle_term:
                        # Check against known muscle groups
                        muscle_groups = {
                            'neck': 'neck', 
                            'shoulder': 'shoulder', 'shoulders': 'shoulder',
                            'upper arm': 'upper arms', 'bicep': 'upper arms', 'tricep': 'upper arms',
                            'biceps': 'upper arms', 'triceps': 'upper arms', 'arm': 'upper arms',
                            'arms': 'upper arms', 'upper body': 'upper arms',
                            'forearm': 'forearm', 'forearms': 'forearm', 'wrist': 'forearm',
                            'back': 'back', 'lats': 'back', 'traps': 'back',
                            'chest': 'chest', 'pecs': 'chest', 'pectorals': 'chest',
                            'hip': 'hips', 'hips': 'hips',
                            'thigh': 'thighs', 'thighs': 'thighs', 'quad': 'thighs',
                            'quads': 'thighs', 'quadriceps': 'thighs',
                            'hamstring': 'thighs', 'hamstrings': 'thighs',
                            'calf': 'calves', 'calves': 'calves', 'lower leg': 'calves',
                            'waist': 'waist', 'abs': 'waist', 'abdominals': 'waist',
                            'core': 'waist', 'stomach': 'waist', 'midsection': 'waist',
                            'glute': 'hips', 'glutes': 'hips', 'butt': 'hips', 'buttocks': 'hips'
                        }
                        
                        normalized_muscle = None
                        for key, value in muscle_groups.items():
                            if key in muscle_term:
                                normalized_muscle = value
                                break
                        
                        if normalized_muscle:
                            # Return a suitable exercise for this muscle group
                            matching_exercises = self.exercise_data[
                                self.exercise_data['Main Muscle'].str.lower().str.contains(normalized_muscle, na=False) |
                                self.exercise_data['Target Muscles'].str.lower().str.contains(normalized_muscle, na=False)
                            ]
                            
                            if not matching_exercises.empty:
                                return matching_exercises.sample(1).iloc[0]
        
        # Next, check for direct queries about specific exercises
        for _, exercise in self.exercise_data.iterrows():
            exercise_name = str(exercise.get('Exercise', '')).lower()
            if exercise_name and (
                exercise_name in message or
                f"how to do {exercise_name}" in message or
                f"what is {exercise_name}" in message or
                f"tell me about {exercise_name}" in message
            ):
                return exercise
        
        # Check if message directly mentions a specific muscle group
        muscle_groups = [
            'neck', 'shoulder', 'upper arms', 'forearm', 'back', 'chest', 
            'hips', 'thighs', 'calves', 'waist', 'abs', 'core', 'glutes',
            'quadriceps', 'hamstrings', 'biceps', 'triceps'
        ]
        
        for muscle in muscle_groups:
            if muscle in message:
                # Return a random exercise for this muscle group
                matching_exercises = self.exercise_data[
                    self.exercise_data['Main Muscle'].str.lower().str.contains(muscle, na=False) |
                    self.exercise_data['Target Muscles'].str.lower().str.contains(muscle, na=False)
                ]
                if not matching_exercises.empty:
                    return matching_exercises.sample(1).iloc[0]
        
        return None
    
    def get_response(self, message):
        """
        Generate a response based on the user's message
        """
        intent = self.detect_intent(message)
        food_query = self.detect_food_query(message)
        exercise_query = self.detect_exercise_query(message)
        
        # If a specific food was mentioned, provide info about it
        if food_query is not None:
            return self.food_info_response(food_query)
        
        # If a specific exercise was mentioned, provide info about it
        if exercise_query is not None:
            return self.exercise_info_response(exercise_query)
        
        # Otherwise, respond based on intent
        if intent == 'greeting':
            return self.greeting_response()
        elif intent == 'goodbye':
            return self.goodbye_response()
        elif intent == 'thanks':
            return self.thanks_response()
        elif intent == 'help':
            return self.help_response()
        elif intent == 'food_recommendation':
            return self.food_recommendation_response()
        elif intent == 'low_calorie':
            return self.low_calorie_response()
        elif intent == 'high_protein':
            return self.high_protein_response()
        elif intent == 'exercise_recommendation':
            return self.exercise_recommendation_response()
        elif intent == 'nutrition_info':
            return self.general_nutrition_response()
        elif intent == 'goal_setting':
            return self.goal_setting_response()
        elif intent == 'water_intake':
            return self.water_intake_response()
        elif intent == 'meal_timing':
            return self.meal_timing_response()
        elif intent == 'cheat_meal':
            return self.cheat_meal_response()
        elif intent == 'vitamins':
            return self.vitamins_response()
        elif intent == 'weight_loss':
            return self.weight_loss_response()
        elif intent == 'weight_gain':
            return self.weight_gain_response()
        elif intent == 'diet_type':
            return self.diet_type_response(message)
        elif intent == 'health_condition':
            return self.health_condition_response()
        else:
            return self.general_response()
    
    def food_info_response(self, food):
        """
        Generate response with information about a specific food
        """
        food_name = food.get('Food Name', 'this food')
        calories = food.get('Calories', 0)
        protein = food.get('Protein', 0)
        carbs = food.get('Carbs', 0)
        fat = food.get('Total Fat', 0)
        
        response = f"📊 **{food_name}** contains approximately:\n\n"
        response += f"- Calories: {calories:.0f} kcal\n"
        response += f"- Protein: {protein:.1f}g\n"
        response += f"- Carbs: {carbs:.1f}g\n"
        response += f"- Fat: {fat:.1f}g\n\n"
        
        # Add a recommendation based on the food's macros
        if protein > 15:
            response += "This is a good source of protein! 💪\n"
        if carbs > 30:
            response += "This food is relatively high in carbohydrates. 🍚\n"
        if fat > 15:
            response += "This contains a significant amount of fat. 🥑\n"
        
        # Add a contextual suggestion
        user_goal = self.user_data.get('goal', '').lower() if self.user_data else ''
        
        if 'weight loss' in user_goal and calories > 300:
            response += "\nTip: Since you're focused on weight loss, consider this as a more substantial meal and adjust portion sizes accordingly. 👍"
        elif 'muscle gain' in user_goal and protein > 10:
            response += "\nTip: This food can be helpful for your muscle gain goals due to its protein content! 💪"
        else:
            response += f"\nWould you like to know how {food_name} could fit into your meal plan? Just ask! 😊"
        
        return response
    
    def exercise_info_response(self, exercise):
        """
        Generate response with information about a specific exercise
        """
        exercise_name = exercise.get('Exercise', 'this exercise')
        equipment_type = exercise.get('Equipment Type', 'N/A')
        target_muscles = exercise.get('Target Muscles', 'various muscles')
        preparation = exercise.get('Preparation', 'N/A')
        execution = exercise.get('Execution', 'N/A')
        
        response = f"🏋️‍♂️ **{exercise_name}**\n\n"
        response += f"**Type:** {equipment_type}\n"
        response += f"**Target Muscles:** {target_muscles}\n\n"
        
        if preparation and preparation != '0':
            response += f"**Preparation:** {preparation}\n\n"
        
        if execution and execution != '0':
            response += f"**Execution:** {execution}\n\n"
        
        # Add a contextual suggestion
        user_goal = self.user_data.get('goal', '').lower() if self.user_data else ''
        
        if 'muscle gain' in user_goal:
            response += "Tip: For muscle gain, focus on controlled movements and gradually increasing resistance. 💪"
        elif 'weight loss' in user_goal:
            response += "Tip: For weight loss, consider incorporating this into a circuit with minimal rest between exercises. 🔥"
        else:
            response += "Remember to maintain proper form for safety and effectiveness! 👍"
        
        return response
    
    def greeting_response(self):
        greetings = [
            "Hello! How can I help with your nutrition or fitness today? 😊",
            "Hi there! I'm your nutrition and fitness assistant. What can I help you with? 🥗🏋️‍♂️",
            "Welcome! Looking for meal ideas or exercise tips? I'm here to help! 🍎",
            "Hey! Ready to chat about nutrition and fitness? What's on your mind? 💪",
            "Greetings! I'm here to help with your health and wellness questions. What do you need? 🌱"
        ]
        return random.choice(greetings)
    
    def goodbye_response(self):
        goodbyes = [
            "Goodbye! Remember to stay hydrated and make healthy choices! 🚰",
            "Take care! Come back anytime for more nutrition and fitness tips. 👋",
            "See you later! Keep up the great work on your health journey! 🌟",
            "Farewell! Remember, consistency is key to achieving your health goals. 🔑",
            "Bye for now! Looking forward to helping you again soon! 😊"
        ]
        return random.choice(goodbyes)
    
    def thanks_response(self):
        responses = [
            "You're welcome! I'm happy to help with your nutrition and fitness needs. 😊",
            "My pleasure! Feel free to ask if you have any other questions. 👍",
            "Glad I could help! Remember, small changes add up to big results over time. 🌱",
            "Anytime! Consistency is key to reaching your health and fitness goals. 🔑",
            "No problem! Stay motivated and keep making healthy choices! 💪"
        ]
        return random.choice(responses)
    
    def help_response(self):
        return (
            "Here's how I can help you:\n\n"
            "🍽️ **Food Information** - Ask about any food's nutritional content\n"
            "🏋️‍♂️ **Exercise Guidance** - Get info on specific exercises or workouts\n"
            "💡 **Recommendations** - Request food or exercise ideas based on your goals\n"
            "📊 **Nutrition Tips** - Learn about diet types, meal timing, and more\n\n"
            "Try asking things like:\n"
            "- 'What's in chicken breast?'\n"
            "- 'Recommend high protein foods'\n"
            "- 'Tell me about bench press'\n"
            "- 'How much water should I drink?'\n"
            "- 'What should I eat for muscle gain?'"
        )
    
    def food_recommendation_response(self):
        """
        Recommend foods based on user profile if available, otherwise general recommendations
        """
        user_goal = self.user_data.get('goal', '').lower() if self.user_data else ''
        diet_pref = self.user_data.get('diet', '').lower() if self.user_data else ''
        
        # Default recommendations
        if not isinstance(self.food_data, pd.DataFrame) or self.food_data.empty:
            return "I'd recommend incorporating a variety of whole foods including lean proteins, fruits, vegetables, whole grains, and healthy fats. This ensures you get a wide range of nutrients to support your health goals."
        
        # Filter by dietary preference if specified
        if diet_pref in ['vegetarian', 'vegan']:
            filtered_foods = self.food_data[~self.food_data['Food Name'].str.lower().str.contains('meat|chicken|beef|pork|fish|seafood', na=False)]
            if diet_pref == 'vegan':
                filtered_foods = filtered_foods[~filtered_foods['Food Name'].str.lower().str.contains('milk|cheese|egg|yogurt|butter', na=False)]
        else:
            filtered_foods = self.food_data
        
        # Get a few random, healthy food options
        healthy_foods = filtered_foods[
            (filtered_foods['Calories'] > 0) & 
            (filtered_foods['Calories'] < 500) &
            (filtered_foods['Protein'] > 3)
        ]
        
        if healthy_foods.empty:
            healthy_foods = filtered_foods
        
        # Select 3-5 foods
        sample_size = min(5, len(healthy_foods))
        recommendations = healthy_foods.sample(sample_size)
        
        response = "Based on your profile, I recommend these foods:\n\n"
        
        for _, food in recommendations.iterrows():
            food_name = food.get('Food Name', 'Food')
            calories = food.get('Calories', 0)
            protein = food.get('Protein', 0)
            
            response += f"🍽️ **{food_name}** - {calories:.0f} calories, {protein:.1f}g protein\n"
        
        # Add goal-specific advice
        if 'weight loss' in user_goal:
            response += "\nThese options can help with weight loss due to their protein content and reasonable calorie levels. Remember to control portions and pair with plenty of vegetables! 🥦"
        elif 'muscle gain' in user_goal or 'weight gain' in user_goal:
            response += "\nThese foods provide good nutrition for muscle building. Consider increasing portion sizes to meet your calorie needs for growth. 💪"
        else:
            response += "\nThese nutritious options can support your overall health and well-being. Variety is key to getting all the nutrients you need! 🌈"
        
        return response
    
    def low_calorie_response(self):
        if not isinstance(self.food_data, pd.DataFrame) or self.food_data.empty:
            return "Low-calorie foods include leafy greens, berries, broccoli, cauliflower, cucumber, lean proteins like chicken breast and white fish, and eggs. These foods provide nutrients while keeping calories low."
        
        # Find low calorie foods
        low_cal_foods = self.food_data[
            (self.food_data['Calories'] > 0) & 
            (self.food_data['Calories'] < 100)
        ].sort_values('Calories')
        
        if low_cal_foods.empty:
            return "I couldn't find specific low-calorie foods in my database, but generally, vegetables, lean proteins, and fruits are good low-calorie options."
        
        # Select a few low calorie foods
        sample_size = min(5, len(low_cal_foods))
        recommendations = low_cal_foods.head(sample_size)
        
        response = "Here are some low-calorie food options:\n\n"
        
        for _, food in recommendations.iterrows():
            food_name = food.get('Food Name', 'Food')
            calories = food.get('Calories', 0)
            
            response += f"🥬 **{food_name}** - only {calories:.0f} calories\n"
        
        response += "\nLow-calorie foods help create a calorie deficit for weight loss while still providing essential nutrients. Try building meals around these foods with plenty of vegetables! 🥗"
        
        return response
    
    def high_protein_response(self):
        if not isinstance(self.food_data, pd.DataFrame) or self.food_data.empty:
            return "High-protein foods include chicken breast, turkey, fish, lean beef, eggs, Greek yogurt, cottage cheese, tofu, legumes, and protein supplements like whey protein. These support muscle recovery and growth."
        
        # Find high protein foods
        high_protein_foods = self.food_data[
            (self.food_data['Protein'] > 10) & 
            (self.food_data['Calories'] > 0)
        ].sort_values('Protein', ascending=False)
        
        if high_protein_foods.empty:
            return "I couldn't find specific high-protein foods in my database, but chicken, fish, eggs, dairy, legumes, and tofu are excellent protein sources."
        
        # Select a few high protein foods
        sample_size = min(5, len(high_protein_foods))
        recommendations = high_protein_foods.head(sample_size)
        
        response = "Here are some high-protein food options:\n\n"
        
        for _, food in recommendations.iterrows():
            food_name = food.get('Food Name', 'Food')
            protein = food.get('Protein', 0)
            calories = food.get('Calories', 0)
            
            response += f"💪 **{food_name}** - {protein:.1f}g protein, {calories:.0f} calories\n"
        
        response += "\nProtein is essential for muscle repair and growth. Aim to consume protein throughout the day, especially after workouts! 🏋️‍♂️"
        
        return response
    
    def exercise_recommendation_response(self):
        if not isinstance(self.exercise_data, pd.DataFrame) or self.exercise_data.empty:
            return "A balanced exercise routine includes cardio (like walking, running, or cycling), strength training (with bodyweight or resistance), and flexibility work (stretching or yoga). Aim for at least 150 minutes of moderate activity weekly."
        
        # Get user goal if available
        user_goal = self.user_data.get('goal', '').lower() if self.user_data else ''
        
        # Select exercises based on goal
        if 'weight loss' in user_goal:
            exercise_focus = ['Cardio', 'HIIT', 'Circuit']
        elif 'muscle gain' in user_goal:
            exercise_focus = ['Strength', 'Resistance', 'Weight']
        else:
            exercise_focus = ['Stretch', 'Cardio', 'Strength']
        
        # Filter exercises
        filtered_exercises = self.exercise_data[
            self.exercise_data['Equipment Type'].str.contains('|'.join(exercise_focus), case=False, na=False)
        ]
        
        if filtered_exercises.empty:
            filtered_exercises = self.exercise_data
        
        # Select a few exercises
        sample_size = min(5, len(filtered_exercises))
        recommendations = filtered_exercises.sample(sample_size)
        
        response = "Here are some exercise recommendations:\n\n"
        
        for _, exercise in recommendations.iterrows():
            exercise_name = exercise.get('Exercise', 'Exercise')
            equipment = exercise.get('Equipment Type', 'N/A')
            target = exercise.get('Main Muscle', 'muscles')
            
            response += f"🏋️‍♂️ **{exercise_name}** ({equipment}) - Targets: {target}\n"
        
        # Add goal-specific advice
        if 'weight loss' in user_goal:
            response += "\nFor weight loss, focus on creating a calorie deficit through a mix of cardio and strength training. Aim for consistency rather than intensity when starting out! 🔥"
        elif 'muscle gain' in user_goal:
            response += "\nFor muscle gain, focus on progressive overload by gradually increasing weight or reps. Don't forget that adequate protein and recovery are essential! 💪"
        else:
            response += "\nA balanced approach to fitness includes strength, cardio, and flexibility work. Listen to your body and adjust intensity as needed! 🌟"
        
        return response
    
    def general_nutrition_response(self):
        nutrition_facts = [
            "Protein contains 4 calories per gram and is essential for muscle repair and growth. 💪",
            "Carbohydrates provide 4 calories per gram and are your body's primary energy source. 🍚",
            "Fats contain 9 calories per gram and are important for hormone production and vitamin absorption. 🥑",
            "Dietary fiber supports digestive health and can help manage hunger. Most adults should aim for 25-30g daily. 🌱",
            "Staying hydrated is crucial - aim for around 3-4 liters of water daily, more if you're active or in hot weather. 💧",
            "Micronutrients (vitamins and minerals) don't provide calories but are essential for health and metabolism. 🍎",
            "Meal timing is less important than total daily nutrition, but spreading protein intake throughout the day can benefit muscle protein synthesis. ⏰",
            "Whole foods typically provide better nutrition than processed alternatives, with more fiber and micronutrients. 🥦",
            "A balanced plate includes protein, complex carbs, healthy fats, and plenty of colorful vegetables. 🍽️",
            "The thermic effect of food means your body burns calories digesting what you eat - protein has the highest thermic effect. 🔥"
        ]
        
        return random.choice(nutrition_facts)
    
    def goal_setting_response(self):
        return (
            "Setting effective health and fitness goals involves the SMART approach:\n\n"
            "✅ **Specific** - Define exactly what you want to achieve\n"
            "✅ **Measurable** - Identify metrics to track progress\n"
            "✅ **Achievable** - Set realistic goals based on your circumstances\n"
            "✅ **Relevant** - Ensure goals align with your overall health vision\n"
            "✅ **Time-bound** - Set a deadline for accountability\n\n"
            "For weight management:\n"
            "- Healthy weight loss is typically 0.5-1kg (1-2lbs) per week\n"
            "- Muscle gain is slower, around 0.25-0.5kg (0.5-1lb) per week for beginners\n\n"
            "Start with small, achievable targets and build on your successes! 🎯"
        )
    
    def water_intake_response(self):
        return (
            "💧 **Hydration Guidelines**\n\n"
            "A general recommendation is to drink about 3-4 liters (100-135 oz) of water daily. However, individual needs vary based on:\n\n"
            "- Body weight (roughly 30-40ml per kg of body weight)\n"
            "- Activity level (more during exercise)\n"
            "- Climate (more in hot/humid conditions)\n"
            "- Overall health\n\n"
            "Signs of good hydration include:\n"
            "- Clear or light yellow urine\n"
            "- Rarely feeling thirsty\n"
            "- Normal energy levels\n\n"
            "Tips for staying hydrated:\n"
            "- Carry a reusable water bottle\n"
            "- Set reminders to drink regularly\n"
            "- Flavor water with fruit if you prefer\n"
            "- Consume water-rich foods like cucumber and watermelon\n\n"
            "Remember that caffeinated and alcoholic beverages can contribute to dehydration. 🚰"
        )
    
    def meal_timing_response(self):
        return (
            "⏰ **Meal Timing Insights**\n\n"
            "The truth about meal timing:\n\n"
            "- Total daily nutrition typically matters more than specific timing\n"
            "- Meal frequency (3 large vs 6 small meals) doesn't significantly impact metabolism\n"
            "- Finding a pattern that works with YOUR schedule and hunger cues is most important\n\n"
            "Performance considerations:\n"
            "- Pre-workout nutrition (1-3 hours before): Carbs for energy, moderate protein, low fat\n"
            "- Post-workout (within 2 hours): Protein for recovery, carbs to replenish glycogen\n\n"
            "Some people benefit from eating most calories earlier in the day, while others prefer time-restricted eating (like 16:8 intermittent fasting).\n\n"
            "Experiment to find what works best for YOUR energy, hunger, and lifestyle! 🍽️"
        )
    
    def cheat_meal_response(self):
        return (
            "🍕 **About Cheat Meals**\n\n"
            "Occasional indulgences can be part of a sustainable approach to nutrition:\n\n"
            "- They can provide psychological relief from strict dieting\n"
            "- May help prevent binges through planned flexibility\n"
            "- Can temporarily boost metabolism and leptin levels\n\n"
            "Best practices:\n"
            "- Consider 'planned treats' rather than 'cheats'\n"
            "- Aim for 80/20 balance (80% nutrient-focused, 20% enjoyment)\n"
            "- Be mindful and savor the experience\n"
            "- Return to your regular eating pattern afterward\n\n"
            "Remember that consistency matters more than perfection, and no single meal will ruin your progress! 🌈"
        )
    
    def vitamins_response(self):
        return (
            "💊 **Vitamins & Minerals**\n\n"
            "Essential micronutrients support numerous bodily functions:\n\n"
            "- **Vitamin D**: Supports bone health and immune function (sources: sunlight, fatty fish, fortified foods)\n"
            "- **Vitamin B12**: Critical for nerve function and energy (sources: animal products, fortified foods)\n"
            "- **Iron**: Carries oxygen in blood (sources: red meat, lentils, spinach)\n"
            "- **Calcium**: Builds bones and teeth (sources: dairy, fortified plant milks, leafy greens)\n"
            "- **Magnesium**: Supports muscle function and sleep (sources: nuts, seeds, whole grains)\n"
            "- **Zinc**: Supports immune system and wound healing (sources: meat, shellfish, legumes)\n\n"
            "The best approach is getting nutrients from whole foods first, with supplements addressing specific deficiencies or needs. Consider a blood test to identify any deficiencies before supplementing. 🍏"
        )
    
    def weight_loss_response(self):
        return (
            "🔻 **Sustainable Weight Loss Approach**\n\n"
            "Fundamentals:\n"
            "- Create a moderate calorie deficit (300-500 calories below maintenance)\n"
            "- Focus on protein (helps preserve muscle and manage hunger)\n"
            "- Include plenty of fiber-rich foods (vegetables, fruits, whole grains)\n"
            "- Stay hydrated\n"
            "- Combine cardio and strength training\n\n"
            "Practical tips:\n"
            "- Track portions/calories at least initially to understand intake\n"
            "- Prepare meals at home when possible\n"
            "- Fill half your plate with vegetables\n"
            "- Limit ultra-processed foods and added sugars\n"
            "- Prioritize sleep and stress management\n\n"
            "Healthy rate of loss: 0.5-1kg (1-2lbs) per week\n\n"
            "Remember that sustainable changes lead to lasting results! 🌱"
        )
    
    def weight_gain_response(self):
        return (
            "🔺 **Healthy Weight Gain Strategy**\n\n"
            "Fundamentals:\n"
            "- Create a calorie surplus (300-500 calories above maintenance)\n"
            "- Prioritize nutrient-dense foods rather than empty calories\n"
            "- Consume adequate protein (1.6-2.2g/kg of body weight)\n"
            "- Incorporate strength training to build muscle, not just fat\n\n"
            "Practical tips:\n"
            "- Eat more frequently or increase portion sizes\n"
            "- Include healthy calorie-dense foods (nuts, nut butters, avocados, olive oil)\n"
            "- Use liquid calories strategically (smoothies with protein, fruit, nut butter)\n"
            "- Time largest meals around workouts\n"
            "- Ensure adequate recovery and sleep\n\n"
            "Healthy rate of gain: 0.25-0.5kg (0.5-1lb) per week\n\n"
            "Quality nutrition + progressive overload in training = optimal results! 💪"
        )
    
    def diet_type_response(self, message):
        message = message.lower()
        
        if 'keto' in message:
            return (
                "🥑 **Ketogenic Diet**\n\n"
                "The ketogenic diet is very low in carbohydrates, moderate in protein, and high in fat:\n\n"
                "- Typically 5-10% calories from carbs, 15-20% from protein, 70-80% from fat\n"
                "- Aims to put body in ketosis, burning fat for fuel instead of carbs\n"
                "- Can be effective for weight loss, blood sugar control, and certain medical conditions\n\n"
                "Common foods include: meats, fatty fish, eggs, butter, oils, cheese, nuts, seeds, and low-carb vegetables.\n\n"
                "Potential challenges include initial 'keto flu,' difficulty with adherence, and limited long-term research."
            )
        elif 'paleo' in message:
            return (
                "🦖 **Paleo Diet**\n\n"
                "The paleolithic diet focuses on foods presumed to be available to our hunter-gatherer ancestors:\n\n"
                "- Emphasizes whole foods, eliminates processed foods and agricultural products\n"
                "- Includes meats, fish, eggs, vegetables, fruits, nuts, and seeds\n"
                "- Excludes grains, legumes, dairy, refined sugar, and salt\n\n"
                "Benefits may include reduced inflammation and improved blood lipids for some people.\n\n"
                "Criticisms include the difficulty of accurately recreating prehistoric diets and the exclusion of nutritious food groups like whole grains and legumes."
            )
        elif 'vegan' in message:
            return (
                "🌱 **Vegan Diet**\n\n"
                "A vegan diet excludes all animal products:\n\n"
                "- Plant-based sources of protein include legumes, tofu, tempeh, seitan, and certain grains\n"
                "- Nutrients requiring special attention: vitamin B12, omega-3s, iron, zinc, calcium, vitamin D\n"
                "- Environmental and ethical benefits are commonly cited reasons for adoption\n\n"
                "A well-planned vegan diet can be nutritionally complete with proper attention to key nutrients.\n\n"
                "Consider supplementing vitamin B12, which is not naturally found in plant foods."
            )
        elif 'vegetarian' in message:
            return (
                "🥚 **Vegetarian Diet**\n\n"
                "Vegetarian diets exclude meat but vary in other animal product inclusion:\n\n"
                "- Lacto-ovo vegetarians: include dairy and eggs\n"
                "- Lacto vegetarians: include dairy, exclude eggs\n"
                "- Ovo vegetarians: include eggs, exclude dairy\n\n"
                "Protein sources include legumes, dairy (if included), eggs (if included), tofu, tempeh, and seitan.\n\n"
                "A well-balanced vegetarian diet can provide all necessary nutrients, with special attention to iron, zinc, and vitamin B12 depending on the specific type."
            )
        elif 'mediterranean' in message:
            return (
                "🫒 **Mediterranean Diet**\n\n"
                "Based on traditional eating patterns of Mediterranean countries:\n\n"
                "- Emphasizes vegetables, fruits, whole grains, legumes, nuts, seeds, and olive oil\n"
                "- Includes moderate amounts of fish, poultry, eggs, and dairy\n"
                "- Limits red meat and sweets\n"
                "- Often includes moderate wine consumption with meals\n\n"
                "One of the most well-researched dietary patterns, associated with reduced risk of heart disease, certain cancers, and cognitive decline.\n\n"
                "Focuses on overall pattern rather than strict rules, making it adaptable and sustainable for many people."
            )
        elif 'low carb' in message or 'low-carb' in message:
            return (
                "🥩 **Low-Carb Diet**\n\n"
                "Low-carbohydrate diets restrict carbohydrate intake to varying degrees:\n\n"
                "- Moderate low-carb: 100-150g carbs daily\n"
                "- Low-carb: 50-100g carbs daily\n"
                "- Very low-carb/keto: under 50g carbs daily\n\n"
                "Protein and fat intake typically increase to compensate for reduced carbs.\n\n"
                "May be effective for weight loss, blood sugar control, and reducing triglycerides. Individual response varies based on metabolism, activity level, and health status."
            )
        elif 'intermittent fasting' in message or 'fasting' in message:
            return (
                "⏱️ **Intermittent Fasting**\n\n"
                "Cycling between periods of eating and fasting:\n\n"
                "- 16:8 method: 16-hour fast, 8-hour eating window\n"
                "- 5:2 method: 5 regular eating days, 2 very low-calorie days (500-600 calories)\n"
                "- Alternate-day fasting: alternating between regular eating and fasting/very low-calorie days\n\n"
                "Potential benefits include improved insulin sensitivity, cellular repair processes, and simplified meal planning.\n\n"
                "Not recommended for pregnant/breastfeeding women, those with history of eating disorders, or those with certain medical conditions."
            )
        else:
            return (
                "There are many dietary approaches, each with potential benefits and considerations:\n\n"
                "- Mediterranean: emphasizes vegetables, fruits, whole grains, olive oil, moderate dairy and fish\n"
                "- Low-carb/Keto: restricts carbs, higher in protein and fats\n"
                "- Vegetarian/Vegan: plant-focused with varying degrees of animal product restriction\n"
                "- Paleo: based on foods presumed available to our ancestors (meats, fish, fruits, vegetables, nuts, seeds)\n"
                "- Intermittent fasting: focuses on when you eat rather than what you eat\n\n"
                "The best diet is one that provides adequate nutrition, works with your lifestyle, and that you can maintain long-term. Would you like details about a specific approach?"
            )
    
    def health_condition_response(self):
        return (
            "🩺 **Nutrition & Health Conditions**\n\n"
            "Different health conditions may benefit from specific dietary approaches:\n\n"
            "- **Diabetes**: Monitor carbohydrate intake, emphasize fiber, maintain consistent meal timing\n"
            "- **Heart Disease**: Limit saturated fats and sodium, increase fiber, consider plant sterols/stanols\n"
            "- **Hypertension**: Reduce sodium, increase potassium, follow DASH diet principles\n"
            "- **IBS/Digestive Issues**: Consider FODMAPs, identify trigger foods, increase soluble fiber as tolerated\n"
            "- **Osteoporosis**: Ensure adequate calcium and vitamin D, consider vitamin K2\n\n"
            "**Important**: Always consult healthcare providers for personalized nutrition advice for medical conditions. Dietary needs vary significantly between individuals, and what works for one person may not be appropriate for another. 🏥"
        )
    
    def general_response(self):
        general_responses = [
            "I'm not sure I understand. Could you rephrase that or ask about a specific food, exercise, or nutrition topic? 🤔",
            "I'd love to help you with nutrition or fitness! Try asking about a specific food, exercise recommendations, or general health tips. 🍎",
            "I can provide information about food nutrition, exercise recommendations, and healthy lifestyle tips. What specifically would you like to know about? 💪",
            "Feel free to ask me about food nutrition, exercise suggestions, or general health advice. I'm here to help! 🥗",
            "If you're looking for nutrition or fitness guidance, I can help! Try asking about specific foods, workout recommendations, or health goals. 🏋️‍♂️"
        ]
        return random.choice(general_responses)
