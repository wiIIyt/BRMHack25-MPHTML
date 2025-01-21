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
nlp = spacy.load("en_core_web_md")

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

def ocr_space_api(file_path):
    """
    Use OCR.space API to extract text from an image.
    """
    try:
        with open(file_path, 'rb') as file:
            payload = {
                'apikey': 'K88117951388957',
                'isOverlayRequired': False,
                'language': 'eng',
                'OCREngine': 2,
            }
            response = requests.post('https://api.ocr.space/parse/image', files={'file': file}, data=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("OCRExitCode") == 1:
                parsed_text = result["ParsedResults"][0]["ParsedText"]
                print(parsed_text)
                return parsed_text.split('\n')
            else:
                print(f"OCR API Error: {result.get('ErrorMessage')}")
                return []

    except Exception as e:
        print(f"Error querying OCR.space API: {e}")
        return []

def postprocess_text(detected_text):
    """
    Filter and clean the detected text using SpellChecker.
    """
    if not detected_text:
        return []
    
    filtered_text = [word for word in detected_text if re.match(r'^[A-Za-z]+$', word)]
    spell = SpellChecker()
    cleaned_text = [spell.correction(word) for word in filtered_text]
    return cleaned_text

def search_recipes_by_ingredients(ingredients):
    """
    Search for recipes using Spoonacular API.
    """
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
    """
    Search for food using Fatsecret API.
    """
    try:
        foods = fs.foods_search(food)
        if foods:
            return foods[0]["food_name"]
    except Exception as e:
        print(f"Error with Fatsecret API: {e}")
    return None

def is_semantically_similar(word1, word2, threshold=0.6):
    """
    Check if two words are semantically similar using SpaCy.
    """
    try:
        token1 = nlp(word1.lower())
        token2 = nlp(word2.lower())
        return token1.similarity(token2) >= threshold
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return False

def process_receipt(path):
    """
    Process the receipt image using OCR.space API and perform post-processing.
    """
    print("Step 6: Processing receipt")
    detected_text = ocr_space_api(path)
    processed_text = postprocess_text(detected_text)
    print("Step 6 Completed: Receipt processed")
    return processed_text

@app.route('/upload', methods=['PUT'])
def upload_file():
    """
    Handle file upload and process it to detect foods and find recipes.
    """
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
        formatted_recipes = [{"title": recipe.get("title"), "image": recipe.get("image")} for recipe in recipes]
        print(formatted_recipes)
        return jsonify({
            "message": "File uploaded and processed successfully!",
            "detected_foods": detected_foods,
            "recipes": formatted_recipes
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)