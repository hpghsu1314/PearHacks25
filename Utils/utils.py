import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import pymupdf
import anthropic
from restaurant import Restaurant
from dish import Dish


api_key="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"


# Receives a pdf file received from streamlit and returns a string of text
def pdf_to_text(file):
    assert isinstance(file, UploadedFile), "You did not upload a valid PDF file"
    
    file.seek(0)
    pdf = pymupdf.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in pdf:
        text += page.get_text()
    return text


# Receives a string and returns a processed string in the format defined below (in system prompt)
def parse_text_of_menu(text):
    """Use Claude API to analyze menu compatibility with dietary restrictions"""
    response = ""
    # Create the client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Build the system prompt
    system_prompt = """
    You are a helpful assistant that extracts structured information from restaurant menus.

    Given a string of text extracted from a menu, identify each dish and its associated ingredients.

    Output the results in a clean text format, exactly like this:
    - Dish Name; Price; ingredient1, ingredient2, ingredient3
    - Dish Name; Price; ingredient1, ingredient2, ingredient3
    - ...

    Guidelines:
    - Only list actual dishes, not section headers (like "Appetizers", "Mains", "Desserts").
    - Assume ingredients are separated by commas. If the ingredients are listed across multiple lines, combine them.
    - Preserve the dish names as written (including capitalization) unless clearly misspelled.
    - Ignore prices, calorie counts, and other non-ingredient information.
    - Be strict: Do not invent dishes or ingredients not present in the text.
    - If an ingredient list is missing, leave it empty after the colon.
    - Do not include any currency symbols anywhere

    Your entire response should only contain the final formatted list, no explanations or extra commentary.
    """
    
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
                        Please analyze this restaurant menu and return a string.

                        {text}    

                        Output the results in a clean text format, exactly like this:
                        - Dish Name; Price; ingredient1, ingredient2, ingredient3
                        - Dish Name; Price; ingredient1, ingredient2, ingredient3
                        - ...

                        Guidelines:
                        - Only list actual dishes, not section headers (like "Appetizers", "Mains", "Desserts").
                        - Assume ingredients are separated by commas. If the ingredients are listed across multiple lines, combine them.
                        - Preserve the dish names as written (including capitalization) unless clearly misspelled.
                        - Ignore prices, calorie counts, and other non-ingredient information.
                        - Be strict: Do not invent dishes or ingredients not present in the text.
                        - If an ingredient list is missing, leave it empty after the colon.
                        - Do not include any currency symbols anywhere
                        """
                    }
                ]
            }
        ]
    )

    if isinstance(message.content, list):
        response = ''.join(block.text for block in message.content if hasattr(block, 'text'))
    else:
        response = str(message.content)
    
    return response


# Given a response from parse_text_of_menu, returns a json-like object of the menu
def parse_menu_from_json(text):
    menu_items = []
    text = '\n'.join(line.lstrip('- ').strip() for line in text.strip().split('\n'))
    lines = text.strip().split('\n')
    
    for line in lines:
        # Each line is: dish ; price ; ingredients
        parts = line.split(';')
        if len(parts) == 3:
            dish = parts[0].strip()
            price = float(parts[1].strip())
            ingredients = [ingredient.strip() for ingredient in parts[2].split(',')]
            
            menu_items.append({
                "dish": dish,
                "price": price,
                "ingredients": ingredients
            })
    
    return menu_items


# Given a json-like object and a name of the restaurant, returns a new Restaurant object including all of the dishes
def create_restaurant(menu_json_object, name="Default Restaurant"):
    new_menu = []
    for dish in menu_json_object:
        new_dish = Dish(dish["dish"], dish["ingredients"], dish["price"])
        new_menu.append(new_dish)
    new_restaurant = Restaurant(new_menu, name)
    return new_restaurant


# Create new restaurant given pdf file and restaurant name
def from_pdf_to_restaurant(pdf_file, restaurant_name="Default Restaurant"):
    pdf_string = pdf_to_text(pdf_file)
    json_like_text_object = parse_text_of_menu(pdf_string)
    json_like_object = parse_menu_from_json(json_like_text_object)
    return create_restaurant(json_like_object, restaurant_name)


# Helper function for fast dish Creation without breaking abstraction
def create_new_dish(dish_name, ingredients, price):
    return Dish(dish_name, ingredients, price)


# Example usage
text = """
- Garlic Bread with cheese; 6.50; cheese
- Grilled calamari; 12; lemon aioli
- bruschetta; 9.5; tomatoes, basil, garlic, olive oil
- Caesar Salad; 10.00; Romaine lettuce, parmesan, croutons
- Spinach&Strawberry Salad; 11; spinach, fresh Strawberries, feta cheese
- CHIKEN Parmigiana; 18; Breaded chicken breast, mozzarella, tomato sauce, side pasta
- Grilled Salmon; 23.00; lemon-butter sauce, asparagus
- Pasta Alfredo; 16; Fettucine, cream sauce, parmesan
- Classic Cheeseburger; 14; beef patty, cheddar, lettuce, tomato, pickles, Fries
- Veggie burger; 12; blackbean patty, avocado, arugula, spicy mayo
- Chocolate Lava Cake; 8.5; molten chocolate center, vanilla icecream
- tiramisu; 7; espresso-soaked lady fingers, mascarpone, cocoa dusting
"""
