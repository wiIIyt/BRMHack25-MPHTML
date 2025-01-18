from flask import Flask, request, jsonify
from views import views
import os
import easyocr as es
from fatsecret import Fatsecret
import spacy
nlp = spacy.load("en_core_web_md")


fs = Fatsecret('9ad9d6c509b541e397e45f3eaeee2259', '594ec0639817489abd7a391f229f3b60')

# Function to perform OCR using EasyOCR
def EasyOCR(path: str) -> list:
    reader = es.Reader(['en'])
    text = reader.readtext(path)
    return text

# Set up the upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.register_blueprint(views, url_prefix="/views")

# Route for processing JSON data
@app.route('/process', methods=['POST'])
def process():
    try:
        # Safely parse JSON from the request
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        input_text = data['text']
        print(f"Received text: {input_text}")

        # Reverse the input text as an example
        reversed_text = input_text[::-1]
        return jsonify({"original": input_text, "reversed": reversed_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def foodSearch(food):
    try:
        foods = fs.foods_search(food)
        if foods:
            return foods[0]["food_name"]  # Return the first match
    except Exception as e:
        # If an error occurs, skip the search and print the error message
        a=''
    return None

nlp = spacy.load("en_core_web_md")

def is_semantically_similar(word1, word2, threshold=0.8):
    try:
        # Process the words using spaCy to get their word vectors
        token1 = nlp(word1)
        token2 = nlp(word2)
        
        # Calculate the cosine similarity between the two word vectors
        similarity = token1.similarity(token2)
        
        print(f"Cosine similarity between '{word1}' and '{word2}': {similarity}")
        
        # If the similarity is above the threshold, return the first word
        if similarity >= threshold:
            return word1
        else:
            return None  # Skip if not similar
    except Exception as e:
        a = ''
        return None

# Route for uploading files
@app.route('/upload', methods=['PUT'])

def upload_file():
    try:
        foodItems = []
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Save the file to the upload folder
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        attempts = 0
        confidence_threshold = 0.90  # 90% confidence
        ocr_result = []

        while attempts < 1:
            ocr_result = EasyOCR(file_path)
            # Check if confidence is high enough (above 90%)
            if all(detection[2] >= confidence_threshold for detection in ocr_result):
                break  # Stop repeating OCR if confidence is high enough
            attempts += 1

        # Extract only the text part of the OCR result
        text_result = [detection[1] for detection in ocr_result]
        for text in text_result:
            food_name = foodSearch(text)
            # Example usage
            word1 = text
            word2 = food_name
            print(text)
            result = is_semantically_similar(word1, word2)
            if result:
                foodItems.append(food_name)

        return jsonify({"message": "File uploaded and processed successfully!", "ocr_result": foodItems})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(app.url_map)  # Prints all the routes registered with Flask
    app.run(debug=True, port=8000)
