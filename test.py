#K88117951388957

import requests

def ocr_space_file(filename, overlay=False, api_key='K88117951388957', language='eng'):
    payload = {
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': language,
        'OCREngine': 2,
    }
    
    try:
        with open(filename, 'rb') as file:
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files={filename: file},
                data=payload
            )
        result = response.json()

        # Check if OCR processing was successful
        if result.get("OCRExitCode") == 1:
            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                # Extract ParsedText
                extracted_text = parsed_results[0].get("ParsedText", "")
                return extracted_text.strip()
            else:
                return "No text found in the image."
        else:
            return f"Error: {result.get('ErrorMessage', 'Unknown error occurred')}"

    except Exception as e:
        return f"An error occurred: {str(e)}"
    
extracted_text = ocr_space_file(r'uploads\Screenshot 2025-01-17 182529.png')
print("Extracted Text:\n", extracted_text)
import requests
from bs4 import BeautifulSoup

def scrape_stilltasty(food_item):
    """
    Scrape shelf life information for a food item from StillTasty.
    
    :param food_item: The name of the food item (e.g., "milk").
    :return: Shelf life information or a message if no data is found.
    """
    base_url = "https://www.stilltasty.com/searchitems/search"
    params = {"q": food_item}
    
    try:
        # Send GET request
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Check for HTTP request errors

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Locate results (adjust based on inspected HTML structure)
        results = soup.find_all('div', class_='search-result')
        if not results:
            return f"No shelf life information found for '{food_item}'."

        # Extract shelf life details
        shelf_life_info = []
        for result in results:
            # Extract food name and shelf life details
            food_name = result.find('h2').get_text(strip=True)
            details = result.find('p').get_text(strip=True)
            shelf_life_info.append(f"{food_name}: {details}")
        
        return "\n".join(shelf_life_info)

    except Exception as e:
        return f"An error occurred: {str(e)}"

# Example usage
food_item = "Almond milk"
print(scrape_stilltasty(food_item))
