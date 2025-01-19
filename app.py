import cv2
import numpy as np
from flask import Flask, request, jsonify
from views import views
import os
import easyocr as es
from fatsecret import Fatsecret
import spacy
import requests
import pytesseract
from spellchecker import SpellChecker
import re

# Lazy-load SpaCy model for similarity comparison
nlp = spacy.load("en_core_web_sm")

# Initialize Fatsecret API
fs = Fatsecret('9ad9d6c509b541e397e45f3eaeee2259', 'e432c812a68347ffa7f967da78d60a19')

# Spoonacular API setup
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY", "bb9a18056ae6421d9219bc8287111653")
SPOONACULAR_BASE_URL = "https://api.spoonacular.com/recipes/findByIngredients"

# Set up the upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.register_blueprint(views, url_prefix="/views")

# Function to adjust image by inverting colors using OpenCV
def invert_image(image_path, output_path):
    # Read the image using OpenCV
    image = cv2.imread(image_path)

    # Invert the colors (white text on black background becomes black text on white background)
    inverted_image = cv2.bitwise_not(image)

    # Save the processed image
    cv2.imwrite(output_path, inverted_image)
    print(f"Processed image saved as {output_path}")

def preprocess_image(image_path):
    print("Step 1: Processing image")
    if not os.path.exists(image_path):
        print(f"Error: Image file {image_path} not found.")
        return None
    
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        print(f"Error: Image at {image_path} could not be loaded.")
        return None
    print("Image loaded successfully")
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply thresholding (binary inversion using Otsu's method)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    print("Step 1 Completed: Image processed")
    return thresh
# Function to perform OCR using EasyOCR
def EasyOCR(path: str) -> list:
    print("Step 2: Running EasyOCR")
    reader = es.Reader(['en'])
    text = reader.readtext(path)
    print("Step 2 Completed: EasyOCR finished")
    return text

def TesseractOCR(image_path):
    print("Step 3: Running TesseractOCR")
    text = pytesseract.image_to_string(image_path, lang='eng')
    print("Step 3 Completed: TesseractOCR finished")
    return text.split('\n')

def combined_ocr(path):
    print("Step 4: Combining OCR results")
    easy_results = EasyOCR(path)
    tesseract_results = TesseractOCR(path)
    
    # Combine and deduplicate results
    combined_results = set(detection[1] for detection in easy_results) | set(tesseract_results)
    combined_results_list = list(combined_results)
    print(f"Combined OCR Results (size: {len(combined_results_list)}): {combined_results_list[:10]}...")
    print("Step 4 Completed: OCR results combined")
    return combined_results_list

def postprocess_text(detected_text):
    print("Step 5: Post-processing text")
    if not detected_text:
        print("No text detected, skipping post-processing.")
        return []
    
    filtered_text = [word for word in detected_text if re.match(r'^[A-Za-z]+$', word)]
    if len(filtered_text) == 0:
        print("No valid words to process")
        return []
    
    spell = SpellChecker()
    cleaned_text = []
    
    for text in filtered_text:
        corrected = spell.correction(text)
        cleaned_text.append(corrected)
    
    print(f"Step 5 Completed: Text post-processed (processed {len(cleaned_text)} words)")
    return cleaned_text

def search_recipes_by_ingredients(ingredients):
    global nlp
    if nlp is None:
        nlp = spacy.load("en_core_web_md")
    try:
        params = {
            "ingredients": ",".join(ingredients),
            "number": 5,
            "apiKey": SPOONACULAR_API_KEY
        }
        response = requests.get(SPOONACULAR_BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching recipes: {e}")
        return []

def foodSearch(food):
    try:
        foods = fs.foods_search(food)
        if foods:
            return foods[0]["food_name"]
    except Exception as e:
        print(f"Error with Fatsecret API: {e}")
    return None

def is_semantically_similar(word1, word2, threshold=0.8):
    try:
        token1 = nlp(word1.lower())
        token2 = nlp(word2.lower())
        return token1.similarity(token2) >= threshold
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return False

def process_receipt(path):
    print("Step 6: Processing receipt")
    # Invert the image before OCR
    inverted_image_path = path.replace('uploads', 'uploads/processed')
    os.makedirs(os.path.dirname(inverted_image_path), exist_ok=True)
    invert_image(path, inverted_image_path)

    detected_text = combined_ocr(inverted_image_path)
    processed_text = postprocess_text(detected_text)
    print("Step 6 Completed: Receipt processed")
    return processed_text

@app.route('/upload', methods=['PUT'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Process the image and perform OCR
        ocr_result = process_receipt(file_path)
        detected_foods = []

        for text in ocr_result:
            food_name = foodSearch(text)
            if food_name and is_semantically_similar(text, food_name):
                detected_foods.append(food_name)

        detected_foods = list(set(detected_foods))
        print(f"Detected foods: {detected_foods}")

        recipes = search_recipes_by_ingredients(detected_foods)
        formatted_recipes = [{"title": recipe.get("title")} for recipe in recipes]

        return jsonify({
            "message": "File uploaded and processed successfully!",
            "detected_foods": detected_foods,
            "recipes": formatted_recipes
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
