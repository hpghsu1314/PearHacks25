import anthropic

# You need to provide your API key when creating the clien

import anthropic
import json
from Utils.restaurant import Restaurant
from Utils.dish import Dish
from Utils.user import User

# Your API key
api_key="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"

def process_api_response(response_text):
    try:
        # Ensure response is a string
        if isinstance(response_text, list):
            response_text = ''.join([str(item) for item in response_text])  # Join list items into a single string

        # Extract the JSON-like part from the response
        start_index = response_text.find("```python\n{")
        end_index = response_text.find("\n}\n```")
        
        if start_index != -1 and end_index != -1:
            json_part = response_text[start_index + len("```python\n"):end_index + 1]
            # Remove the leading "```python" and trailing "```" to isolate the JSON object
            json_part = json_part.replace("```python\n", "").replace("\n```", "")
            
            # Parse the cleaned JSON
            dish_scores = json.loads(json_part)
            return dish_scores
        else:
            print("Error: Unable to find JSON block in the response.")
            return None
    except Exception as e:
        print(f"Error parsing API response: {e}")
        return None

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
    #print(message.content)
    return message.content
import json

def extract_dish_scores(api_response): 
    """
    Extract the dictionary of dish scores from Claude's API response.
    
    Args:
        api_response: The response from Claude's API (could be a string or a structured object like a TextBlock)
        
    Returns:
        dict: A dictionary with dish names as keys and [score, reason] lists as values
    """
    try:
        # Check if the response is a list containing TextBlock objects
        if isinstance(api_response, list) and hasattr(api_response[0], 'text'):
            # Extract the text from the first TextBlock
            text_content = api_response[0].text
        elif hasattr(api_response, 'text'):  # In case it's a single TextBlock
            text_content = api_response.text
        elif isinstance(api_response, str):  # If it's already a string
            text_content = api_response
        else:
            # Try to convert to string if it's some other object
            text_content = str(api_response)
        
        # Extract the JSON part from the response, focusing on content after ```python and before ```
        start_idx = text_content.find('{')
        end_idx = text_content.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("Could not find a dictionary in the API response")
        
        # Extract the dictionary string
        dict_str = text_content[start_idx:end_idx]
        
        # Clean up the string: replace single quotes with double quotes to ensure proper JSON formatting
        dict_str = dict_str.replace("'", "\"")  # Ensure proper double quotes in the dictionary
        
        # Optionally, remove non-JSON-friendly characters (e.g., escape sequences)
        dict_str = dict_str.strip().replace("\n", "").replace("\t", "")  # Remove extra whitespace or escape sequences
        
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
def process_user_feedback(user, user_feedback):
    # Create the client
    client = anthropic.Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=400,  # Increase token limit for more complex responses
        temperature=0.5,  # Slight temperature increase for more dynamic responses
        system=(
            "You are an assistant that classifies and processes user feedback about restaurant recommendations. "
            "Your task is to categorize feedback and make dynamic adjustments to restaurant recommendations. "
            "Classify the feedback into the following categories:\n"
            "1. 'sentiment': If the feedback is about the user's feelings or experience with the recommendations (e.g., happy, unhappy, satisfied, etc.).\n"
            "2. 'requirement': If the feedback contains new food requirements or preferences (e.g., no sugar, prefers vegan, etc.).\n"
            "3. 'mixed': If the feedback contains both sentiment and food requirements, extract and categorize both aspects separately.\n"
            "Provide additional context-aware adjustments based on the user's feedback, ensuring that the recommendations align with their specific requirements.\n"
            "Only output 'sentiment', 'requirement', or 'mixed' for the classification, followed by a brief explanation."
        ),
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Classify and process this user feedback: \"{user_feedback}\""
                }
            ]
        }]
    )
    
    classification = message.content[0].text.strip().lower()
    #print(classification)
    if classification == "sentiment":
        print("User is expressing sentiment. No changes to recommendations required.")
        return False

    elif classification == "requirement":
        print("User has provided new food requirements.")
        process_new_requirement(user, user_feedback)  # Process new requirements
        return True

    elif classification == "mixed":
        # Handle mixed feedback by first extracting both sentiment and requirement
        extraction_message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=400,
            temperature=0.5,  # Slight temperature increase for better handling of mixed feedback
            system=(
                "You are an assistant that extracts both sentiment and new food requirements from mixed feedback. "
                "Given the feedback, output two separate parts: the first part should be a brief sentiment (e.g., 'User is unhappy', 'User is satisfied'). "
                "The second part should be a plain sentence with the new food requirement or preference (e.g., 'User wants no gluten', 'User prefers plant-based options'). "
                "Provide a brief analysis and ensure the extracted parts are clear."
            ),
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Extract both sentiment and requirements from this mixed feedback: \"{user_feedback}\""
                    }
                ]
            }]
        )
        
        extracted_parts = extraction_message.content[0].text.strip().split("\n")
        print(extracted_parts)
        if len(extracted_parts) == 2:
            sentiment = extracted_parts[0].strip()
            new_requirement = extracted_parts[1].strip()
            print(f"Extracted sentiment: {sentiment}")
            print(f"Extracted requirement: {new_requirement}")
            process_new_requirement(user, new_requirement)  # Process new requirement
        else:
            print("Unable to extract both parts from mixed feedback.")
            return False

        return True

Restaurant.get_dish_price = lambda self, dish_name: next(
    (dish.price for dish in self.menu if dish.name == dish_name), None
)

def recommend_food(restaurant, user, user_feedback=None):
    """Recommend food and dynamically handle new requirements."""
    
    # Process user feedback if provided
    if user_feedback:
        handled_new_requirement = process_user_feedback(user, user_feedback)
        
        if not handled_new_requirement:
            is_satisfied = analyze_user_sentiment(user_feedback)
            if is_satisfied:
                print("User is satisfied with the recommendations.")
                return None
            print("User is not satisfied. Generating new recommendations...")
        else:
            print("User provided new requirements. Updating recommendations...")

    # Analyze menu and extract dish scores from API response
    api_response = analyze_menu_compatibility(restaurant, user)
    dish_recommendations = extract_dish_scores(api_response)

    # NEW: Apply price filtering after extracting dish recommendations
    if hasattr(user, 'max_price'):
        print(f"Filtering recommendations to dishes under ${user.max_price}...")
        filtered_recommendations = {
            dish: [score, reason] for dish, [score, reason] in dish_recommendations.items()
            if restaurant.get_dish_price(dish) <= user.max_price
        }
        
        # Display filtered recommendations
        if filtered_recommendations:
            print(f"Updated Recommendations within budget (${user.max_price}):")
            for dish, (score, reason) in filtered_recommendations.items():
                price = restaurant.get_dish_price(dish)
                print(f"{dish} - ${price}: Score {score}, Reason: {reason}")
        else:
            print(f"No dishes found within the ${user.max_price} budget.")
        
        return filtered_recommendations
    if hasattr(user, 'min_price_feedback'):
        min_price_feedback = user.min_price_feedback
        print(f"User's feedback: They want meals with more than ${min_price_feedback}. Filtering recommendations...")
        
        # Filter dishes that meet the user's minimum price requirement
        filtered_recommendations = {
            dish: [score, reason] for dish, [score, reason] in dish_recommendations.items()
            if restaurant.get_dish_price(dish) > min_price_feedback
        }
        
        # Display updated recommendations based on the feedback
        if filtered_recommendations:
            print(f"Updated Recommendations (greater than ${min_price_feedback}):")
            for dish, (score, reason) in filtered_recommendations.items():
                price = restaurant.get_dish_price(dish)
                print(f"{dish} - ${price}: Score {score}, Reason: {reason}")
        else:
            print(f"No dishes found above the ${min_price_feedback} budget.")
        
        return filtered_recommendations

    else:
        # No minimum price feedback provided, return all recommendations
        print("No minimum budget feedback provided. Returning all recommendations.")
        return dish_recommendations

def process_new_requirement(user, requirement_text):
    """Parse new requirements like 'I want price < 15' and update the User object."""
    if "price" in requirement_text:
        import re
        match = re.search(r"price.*?(\d+)", requirement_text)
        if match:
            max_price = float(match.group(1))
            user.max_price = max_price
            print(f"Updated user preference: max price set to {max_price}")
        else:
            print("No valid price found in the requirement text.")
if __name__ == "__main__":
    # Expanded Dishes
    margherita = Dish(
        name="Margherita Pizza",
        ingredients=["tomato sauce", "mozzarella", "basil", "flour", "yeast"],
        price=12.99
    )
    vegan_salad = Dish(
        name="Garden Salad",
        ingredients=["lettuce", "tomato", "cucumber", "olive oil", "balsamic vinegar"],
        price=8.99
    )
    chicken_parm = Dish(
        name="Chicken Parmesan",
        ingredients=["chicken breast", "tomato sauce", "mozzarella", "parmesan", "flour", "eggs"],
        price=15.99
    )
    lemonade = Dish(
        name="Fresh Lemonade",
        ingredients=["lemon", "sugar", "water", "ice"],
        price=4.99
    )
    coke = Dish(
        name="Coca-Cola",
        ingredients=["carbonated water", "sugar", "caffeine"],
        price=2.99
    )
    espresso = Dish(
        name="Espresso",
        ingredients=["coffee"],
        price=3.99
    )
    vegan_burger = Dish(
        name="Vegan Burger",
        ingredients=["plant-based patty", "lettuce", "vegan cheese", "tomato", "bun"],
        price=13.49
    )
    pork_stew = Dish(
        name="pork stew",
        ingredients=["pork","red wine sause","spices"],
        price=13.49
    )
    steak = Dish(
        name="steak",
        ingredients=["beef"],
        price=14.49
    )

    # Restaurant with more variety
    italian_restaurant = Restaurant(
        name="Luigi's Italian Bistro",
        menu=[margherita, vegan_salad, chicken_parm, lemonade, coke, espresso, vegan_burger,pork_stew,]
    )

    user = User(
        username="john_doe",
        restrictions={
            "dairy": 2,
            "eggs": 3,
            "gluten": 1,
            "tomato": 0
        }
    )

    recommendations = recommend_food(italian_restaurant, user)
    print("\nInitial Recommendations:")
    for dish, (score, reason) in recommendations.items():
        price = italian_restaurant.get_dish_price(dish)
        print(f"{dish} - ${price:.2f}: Score {score}, Reason: {reason}")

    user_reaction = input("\nHow do you feel about these recommendations? ")

    new_recommendations = recommend_food(italian_restaurant, user, user_reaction)

    if new_recommendations:
        print("\nUpdated Recommendations:")
        for dish, (score, reason) in new_recommendations.items():
            price = italian_restaurant.get_dish_price(dish)
            print(f"{dish} - ${price:.2f}: Score {score}, Reason: {reason}")