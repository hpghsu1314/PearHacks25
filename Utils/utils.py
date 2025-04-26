import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import pymupdf
import anthropic
from restaurant import Restaurant
from dish import Dish

import cv2
import numpy as np
from PIL import Image, ExifTags, ImageFile
import pytesseract
import io
import warnings


api_key="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"
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"


class FakeUploadedFile(io.BytesIO):
    def __init__(self, file_bytes, name):
        super().__init__(file_bytes.getvalue())
        self.name = name
        self.type = "application/pdf"
        
    def getvalue(self):
        return super().getvalue()

# Allow larger image sizes (adjust according to your needs)
Image.MAX_IMAGE_PIXELS = 1_000_000_000  # 1 billion pixels
ImageFile.LOAD_TRUNCATED_IMAGES = True

def safe_get_pixmap(page, max_pixels=256_000_000):
    """Smart rendering of PDF pages with size checks"""
    # Calculate dimensions in inches (PDF uses points: 1 inch = 72 points)
    width_in = page.rect.width / 72
    height_in = page.rect.height / 72
    
    # Calculate maximum DPI that keeps total pixels under limit
    max_dim = (max_pixels / (width_in * height_in)) ** 0.5
    dpi = min(300, max_dim)  # Never exceed 300 DPI
    
    # For very large pages, use a minimum DPI of 72
    dpi = max(72, dpi)
    
    return page.get_pixmap(matrix=pymupdf.Matrix(dpi/72, dpi/72))

def preprocess_image(image):
    """Modified preprocessing with size checks"""
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Original dimensions
    h, w = img.shape[:2]
    
    # Calculate scaling factor safely
    max_dimension = 4000  # Keep under common screen resolutions
    scale = min(1.0, max_dimension / max(h, w))
    
    if scale < 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale, 
                        interpolation=cv2.INTER_AREA)
    
    # Rest of processing remains the same
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, 
                                      templateWindowSize=7, 
                                      searchWindowSize=21)
    thresh = cv2.adaptiveThreshold(denoised, 255, 
                                  cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpened = cv2.filter2D(thresh, -1, kernel)
    
    return sharpened

def pdf_to_text(file):
    file.seek(0)
    pdf = pymupdf.open(stream=file.read(), filetype="pdf")
    text = ""

    for page_num, page in enumerate(pdf):
        try:
            # First try text extraction
            page_text = page.get_text()
            if len(page_text.strip()) > 20:
                text += page_text
                continue

            # OCR fallback with safe rendering
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # Ignore decompression bomb warnings
                
                pix = safe_get_pixmap(page)
                img = Image.open(io.BytesIO(pix.tobytes()))
                
                # Temporary increase of decompression bomb limit
                original_pixel_limit = Image.MAX_IMAGE_PIXELS
                try:
                    Image.MAX_IMAGE_PIXELS = 1_000_000_000
                    processed = preprocess_image(img)
                finally:
                    Image.MAX_IMAGE_PIXELS = original_pixel_limit
                
                # OCR processing
                custom_config = r'--oem 3 --psm 6 -l eng+equ'
                page_text = pytesseract.image_to_string(processed, config=custom_config)
                text += page_text + "\n"

        except Exception as e:
            print(f"Error processing page {page_num}: {str(e)}")
            continue

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


def apply_exif_rotation(image):
    """Correct orientation based on EXIF data."""
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            exif = dict(exif.items())
            if orientation in exif:
                if exif[orientation] == 3:
                    image = image.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    image = image.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError, TypeError):
        pass  # No EXIF data or issues reading it
    return image


def deskew_image(img):
    """Fix small angular skew (not 90/180/270 rotations)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 50, 150)

    # Find contours focusing on text regions (ignore borders)
    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]  # Top 5 contours

    if not contours:
        return img

    largest_contour = max(contours, key=cv2.contourArea)
    rect = cv2.minAreaRect(largest_contour)
    angle = rect[-1]

    # Adjust angle for OpenCV's coordinate system
    if angle < -45:
        angle = 90 + angle
    if abs(angle) > 45:  # Likely orientation issue, not deskew
        return img

    # Rotate the image to deskew
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    
    return cv2.warpAffine(img, M, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))


def correct_text_orientation(img):
    """Fix 90/180/270 rotations using Tesseract."""
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    try:
        osd = pytesseract.image_to_osd(img_rgb)
        rotation = int(osd.split('Rotate: ')[1].split('\n')[0])
    except:
        return img  # Fallback if Tesseract fails

    # Rotate image according to Tesseract's recommendation
    if rotation not in [0, 90, 180, 270]:
        return img

    # Convert Tesseract's clockwise rotation to OpenCV's CCW
    rotation_angle = -rotation  # Negative for OpenCV's rotation direction
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    
    M = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    
    return cv2.warpAffine(img, M, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))


def image_to_pdf_bytes(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    pdf_bytes = io.BytesIO()
    pil_img.save(pdf_bytes, format="PDF")
    pdf_bytes.seek(0)
    return pdf_bytes


def process_uploaded_image(image_file):
    # Read image with EXIF correction
    image_bytes = image_file.read()
    pil_image = Image.open(io.BytesIO(image_bytes))
    pil_image = apply_exif_rotation(pil_image)
    img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    # Processing order: Correct orientation first, then deskew
    oriented = correct_text_orientation(img)
    deskewed = deskew_image(oriented)
    
    pdf_bytes = image_to_pdf_bytes(deskewed)
    return FakeUploadedFile(pdf_bytes, name="menu.pdf")


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