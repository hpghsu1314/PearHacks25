import anthropic

# You need to provide your API key when creating the clien

import anthropic
import json
from Utils.restaurant import Restaurant
from Utils.dish import Dish
from Utils.user import User

# Your API key
api_key="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"

def serialize_restaurant_data(restaurant, user):
    """Convert Restaurant and User objects to a dictionary structure that can be sent in the API"""
    
    # Convert menu (list of Dish objects) to a list of dictionaries
    serialized_menu = []
    for dish in restaurant.menu:
        serialized_menu.append({
            "name": dish.name,
            "ingredients": dish.ingredients,
            "price": dish.price
        })
    
    # Create the complete data structure
    data = {
        "restaurant": {
            "name": restaurant.name,
            "menu": serialized_menu
        },
        "user": {
            "username": user.username,
            "dietary_restrictions": user.restrictions  # Now this is a dictionary with scales
        }
    }
    
    return data

def analyze_menu_compatibility(restaurant, user):
    """Use Claude API to analyze menu compatibility with dietary restrictions"""
    
    # Prepare the data
    data = serialize_restaurant_data(restaurant, user)
    
    # Create the client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Build the system prompt
    system_prompt = """
    You are a helpful assistant that analyzes restaurant menus and determines which dishes are compatible 
    with a user's dietary restrictions. For each dish, calculate a recommendation score based on the user's ingredient restrictions.
    
    The user has assigned each restricted ingredient a value from 0-3, where:
    0 = completely acceptable to eat
    1 = mild preference against eating
    2 = strong preference against eating
    3 = absolutely cannot eat (severe allergy or other restriction)
    
    Convert these to a final recommendation score between 0 and 1 for each dish:
    - If ANY ingredient in a dish has a restriction level of 3, the dish gets a score of 0 (highly risky, not recommended)
    - Otherwise, calculate a score where 1 is most highly recommended and lower values are less recommended
    """
    
    # Format the restrictions for better readability in the prompt
    formatted_restrictions = json.dumps(data['user']['dietary_restrictions'], indent=2)
    
    # Create the API request
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1000,
        temperature=0.7,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""
                        Please analyze this restaurant menu and compare it with the user's dietary restrictions.
                        
                        Restaurant: {data['restaurant']['name']}
                        
                        Menu items:
                        {json.dumps(data['restaurant']['menu'], indent=2)}
                        
                        User: {data['user']['username']}
                        Dietary restrictions (ingredient: severity scale 0-3):
                        {formatted_restrictions}
                        
                        For each dish:
                        1. Check if ANY ingredient has restriction level 3. If so, score = 0
                        2. Otherwise, calculate a score from 0 to 1, where 1 is most recommended and 0 is least recommended
                        3. Higher restriction levels should result in lower scores
                        4. Create a final dictionary object that ranks dishes from highest to lowest score (most recommended to least)
                        5. Include a brief reason (max 10 words) for each dish recommendation
                        
                        Return a Python dictionary object with dish names as keys and a list containing [score, reason] as values, sorted from highest to lowest score.
                        """
                    }
                ]
            }
        ]
    )
    
    # Return the response
    return message.content

def extract_dish_scores(api_response):
    """
    Extract the dictionary of dish scores from Claude's API response.
    
    Args:
        api_response: The response from Claude's API (could be string or structured)
        
    Returns:
        dict: A dictionary with dish names as keys and [score, reason] lists as values
    """
    try:
        # Check if response is already a string
        if isinstance(api_response, str):
            text_content = api_response
        # Check if response contains a content attribute (Anthropic response object)
        elif hasattr(api_response, 'content'):
            text_content = api_response.content
        # Check if response is a list of TextBlock objects
        elif hasattr(api_response, '__iter__') and hasattr(api_response[0], 'text'):
            # Extract text from first TextBlock
            text_content = api_response[0].text
        else:
            # Try to convert to string
            text_content = str(api_response)
            
        # Remove code block markers if present
        text_content = text_content.replace('```python', '').replace('```', '').strip()
        
        # Find the dictionary in the response
        start_idx = text_content.find('{')
        end_idx = text_content.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("Could not find a dictionary in the API response")
        
        # Extract the dictionary string
        dict_str = text_content[start_idx:end_idx]
        
        # Convert string to actual Python dictionary
        dish_scores = json.loads(dict_str)
        
        # Verify it's a dictionary
        if not isinstance(dish_scores, dict):
            raise TypeError("Extracted content is not a dictionary")
            
        return dish_scores
        
    except Exception as e:
        print(f"Error extracting dish scores: {e}")
        print(f"Raw API response: {api_response}")
        return {}

def analyze_user_sentiment(user_reaction):
    """
    Analyze the sentiment of the user's reaction to food recommendations.
    
    Args:
        user_reaction (str): The user's reaction text
        
    Returns:
        bool: True if user is satisfied, False if dissatisfied
    """
    # Create the client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Make the API request for sentiment analysis
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=100,
        temperature=0,
        system="You are a sentiment analysis assistant. Given a user's free-text reaction to food recommendations, decide whether they are 'satisfied' or 'dissatisfied'. Only output 'satisfied' or 'dissatisfied'. No other text.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""
                        Analyze the sentiment in this user reaction:
                        "{user_reaction}"
                        
                        Only output "satisfied" or "dissatisfied".
                        """
                    }
                ]
            }
        ]
    )

    # Handle Anthropic output safely
    if isinstance(message.content, list):
        text = ''.join(block.text for block in message.content if hasattr(block, 'text'))
    else:
        text = str(message.content)
    
    sentiment = text.strip().lower()

    # Only accept exact "satisfied" or "dissatisfied"
    if sentiment == "satisfied":
        return True
    elif sentiment == "dissatisfied":
        return False
    else:
        raise ValueError(f"Unexpected sentiment response: {sentiment}")

def recommend_food(restaurant, user, user_reaction=None):
    """
    Recommend food to the user and check satisfaction
    
    Args:
        restaurant (Restaurant): The restaurant object
        user (User): The user object
        user_reaction (str, optional): User's reaction to previous recommendations
        
    Returns:
        dict: The final dictionary of dish recommendations
    """
    # If there's a user reaction, check satisfaction
    if user_reaction:
        is_satisfied = analyze_user_sentiment(user_reaction)
        if is_satisfied:
            print("User is satisfied with the recommendations.")
            return None  # No need to generate new recommendations
        print("User is not satisfied. Generating new recommendations...")
    
    # Get new recommendations
    api_response = analyze_menu_compatibility(restaurant, user)
    dish_recommendations = extract_dish_scores(api_response)
    
    return dish_recommendations

# Example usage
if __name__ == "__main__":
    # Create sample dishes
    margherita = Dish(
        name="Margherita Pizza", 
        ingredients=["tomato sauce", "mozzarella cheese", "basil", "flour", "yeast"], 
        price=12.99
    )
    
    vegan_salad = Dish(
        name="Garden Salad", 
        ingredients=["lettuce", "tomato", "cucumber", "olive oil", "balsamic vinegar"], 
        price=8.99
    )
    
    chicken_parm = Dish(
        name="Chicken Parmesan", 
        ingredients=["chicken breast", "tomato sauce", "mozzarella cheese", "parmesan cheese", "flour", "eggs"], 
        price=15.99
    )
    
    # Create a restaurant with these dishes
    italian_restaurant = Restaurant(
        name="Luigi's Italian Bistro",
        menu=[margherita, vegan_salad, chicken_parm]
    )
    
    # Create a user with dietary restrictions using the new dictionary format
    user = User(
        username="john_doe",
        restrictions={
            "dairy": 2,              # strong preference against
            "eggs": 3,               # absolutely cannot eat
            "gluten": 1,             # mild preference against
            "tomato": 0              # acceptable
        }
    )
    
    # Initial recommendation
    recommendations = recommend_food(italian_restaurant, user)
    print("Initial recommendations:")
    for dish, [score, reason] in recommendations.items():
        print(f"{dish}: {score} - {reason}")
    
    # Simulate user reaction
    user_reaction = input("\nHow do you feel about these recommendations? ")
    
    # Generate new recommendations if user is not satisfied
    new_recommendations = recommend_food(italian_restaurant, user, user_reaction)
    
    if new_recommendations:
        print("\nUpdated recommendations:")
        for dish, [score, reason] in new_recommendations.items():
            print(f"{dish}: {score} - {reason}")