import bcrypt
from bson.objectid import ObjectId 
from utils.db import users_collection, meal_plans_collection
from datetime import datetime

def authenticate_user(username, password):
    user = users_collection.find_one({"username": username})
    if not user:
        return False, None, None

    if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        is_admin = user.get("is_admin", False)  # Default False if missing
        return True, str(user["_id"]), is_admin
    else:
        return False, None, None
    
def register_user(username, email, password):
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        return False, "Username already exists.", None

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "is_admin": False,
        "profile_complete": False,

        # Initialize the "profile fields" empty
        "name": "",
        "gender": "",
        "age": None,
        "height": None,
        "weight": None,
        "bmi": None,
        "goal": "",
        "diet": "",
        "activity_level": "",
        "allergies": [],
        "preferred_cuisines": [],
        "health_conditions": "",
        "progress_history": [],
        "health_status": ""
    }

    result = users_collection.insert_one(new_user)
    return True, "User registered successfully!", str(result.inserted_id)

def update_user(user_id, data):
    try:
        # Recalculate BMI if weight or height updated
        if "height" in data or "weight" in data:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
            height = data.get("height", user.get("height"))
            weight = data.get("weight", user.get("weight"))
            
            # Only calculate BMI if both height and weight exist
            if height and weight and isinstance(height, (int, float)) and isinstance(weight, (int, float)):
                bmi = weight / ((height / 100) ** 2)
                health_status = (
                    "Healthy" if 18.5 <= bmi < 24.9
                    else "Underweight" if bmi < 18.5
                    else "Overweight" if 24.9 <= bmi < 29.9
                    else "Obese"
                )
                data["bmi"] = bmi
                data["health_status"] = health_status

        # Update the user record
        result = users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": data})
        if result.modified_count:
            return True, f"User {user_id} updated successfully!"
        else:
            return False, "No changes were made."
    except Exception as e:
        return False, f"Error updating user: {str(e)}"

def delete_user(user_id):
    try:
        result = users_collection.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count:
            return True, f"User {user_id} deleted successfully!"
        else:
            return False, f"User ID {user_id} not found."
    except Exception as e:
        return False, f"Error deleting user: {str(e)}"

def get_user(user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])  # Make ObjectId JSON serializable
        return user
    except Exception as e:
        print(f"Error getting user: {str(e)}")
        return None

def update_user_progress(user_id, weight):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return False, f"User ID {user_id} not found."
        
        height = user["height"]
        bmi = weight / ((height / 100) ** 2)
        health_status = "Healthy" if 18.5 <= bmi < 24.9 else "Underweight" if bmi < 18.5 else "Overweight" if 24.9 <= bmi < 29.9 else "Obese"

        progress_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "weight": float(weight),
            "bmi": bmi
        }

        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$push": {"progress_history": progress_entry},
                "$set": {
                    "weight": float(weight),
                    "bmi": bmi,
                    "health_status": health_status
                }
            }
        )
        return True, "Progress updated successfully!"
    except Exception as e:
        return False, f"Error updating progress: {str(e)}"

def get_all_users():
    try:
        users = list(users_collection.find())
        for user in users:
            user["_id"] = str(user["_id"])
        return users
    except Exception as e:
        print(f"Error getting users: {str(e)}")
        return []
    
    
def save_meal_plan(user_id, meal_plan):
    """
    Save a meal plan to the database.
    """
    meal_plan_entry = {
        "user_id": ObjectId(user_id),
        "meal_plan": meal_plan,
        "created_at": datetime.utcnow()
    }
    result = meal_plans_collection.insert_one(meal_plan_entry)
    return str(result.inserted_id)

def get_meal_plan(user_id):
    """
    Retrieve the latest meal plan for a user.
    """
    meal_plan = meal_plans_collection.find_one({"user_id": ObjectId(user_id)}, sort=[("created_at", -1)])
    return meal_plan["meal_plan"] if meal_plan else None

def update_logged_status(user_id, day, logged):
    """
    Update the logged status of a specific day in the meal plan.
    """
    
    meal_plans_collection.update_one(
        {"user_id": ObjectId(user_id), "meal_plan.days.day": day},
        {"$set": {"meal_plan.days.$.logged": logged}}
    )

    