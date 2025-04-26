import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import pymupdf
import anthropic
from Utils.restaurant import Restaurant
from Utils.dish import Dish

import cv2
import numpy as np
from PIL import Image
import pytesseract
import io


api_key="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"


class FakeUploadedFile(io.BytesIO):
    def __init__(self, file_bytes, name):
        super().__init__(file_bytes.getvalue())
        self.name = name
        self.type = "application/pdf"
        
    def getvalue(self):
        return super().getvalue()


# Receives a pdf file received from streamlit and returns a string of text
def pdf_to_text(file):
    assert isinstance(file, UploadedFile) or isinstance(file, FakeUploadedFile), "You did not upload a valid PDF file"
    
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
def create_restaurant(menu_json_object, menu_pdf, name="Default Restaurant"):
    new_menu = []
    for dish in menu_json_object:
        new_dish = Dish(dish["dish"], dish["ingredients"], dish["price"])
        new_menu.append(new_dish)
    new_restaurant = Restaurant(new_menu, menu_pdf, name)
    return new_restaurant


# Create new restaurant given pdf file and restaurant name
def from_pdf_to_restaurant(pdf_file, restaurant_name="Default Restaurant"):
    pdf_string = pdf_to_text(pdf_file)
    json_like_text_object = parse_text_of_menu(pdf_string)
    json_like_object = parse_menu_from_json(json_like_text_object)
    return create_restaurant(json_like_object, pdf_file, restaurant_name)


# Helper function for fast dish Creation without breaking abstraction
def create_new_dish(dish_name, ingredients, price):
    return Dish(dish_name, ingredients, price)


def deskew_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return img

    largest_contour = max(contours, key=cv2.contourArea)
    rect = cv2.minAreaRect(largest_contour)

    angle = rect[-1]
    if angle < -45:
        angle = 90 + angle

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated


def correct_text_orientation(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    try:
        osd = pytesseract.image_to_osd(img_rgb)
    except pytesseract.TesseractError:
        return img  # fallback if OCR fails

    rotation = 0
    for line in osd.split('\n'):
        if 'Rotate:' in line:
            rotation = int(line.split(':')[-1].strip())
            break

    if rotation == 0:
        return img

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, -rotation, 1.0)  # negative to correct
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated


def crop_menu(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return img

    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)

    cropped = img[y:y+h, x:x+w]
    return cropped


def image_to_pdf_bytes(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)

    pdf_bytes = io.BytesIO()
    pil_img.save(pdf_bytes, format="PDF")
    pdf_bytes.seek(0)
    return pdf_bytes


def process_uploaded_image(image_file):
    """
    Full flow:
    Given an image file (jpg, jpeg, png),
    returns a FakeUploadedFile representing the correctly oriented, cropped menu as a PDF.
    """
    image_bytes = image_file.read()

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    deskewed = deskew_image(img)
    correctly_oriented = correct_text_orientation(deskewed)
    cropped_menu = crop_menu(correctly_oriented)
    pdf_bytes = image_to_pdf_bytes(cropped_menu)
    uploaded_pdf = FakeUploadedFile(pdf_bytes, name="menu.pdf")

    return uploaded_pdf


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

uploaded_image = st.file_uploader("Upload a menu image", type=["jpg", "jpeg", "png"])

if uploaded_image:
    uploaded_pdf = process_uploaded_image(uploaded_image)

    st.download_button(
        label="Download Corrected Menu PDF",
        data=uploaded_pdf.getvalue(),
        file_name=uploaded_pdf.name,
        mime=uploaded_pdf.type
    )