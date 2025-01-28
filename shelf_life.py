#K88117951388957
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def print_shelf_life(search_term):
    # Search URL (the URL for submitting search)
    search_url = "https://stilltasty.com/searchitems/search"
    
    # Create the search payload
    payload = {'search': search_term}
    
    # Send POST request to the search page
    response = requests.post(search_url, data=payload)
    
    # Check if the response was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first result, based on <p class="srclisting">
        first_result = soup.find('p', class_='srclisting')
        
        if first_result:
            # Extract the link from the first result
            first_result_link = first_result.find('a')['href']
            
            # Use urljoin to correctly resolve the full URL
            full_url = urljoin("https://stilltasty.com", first_result_link)
            
            # Fetch the HTML content of the first result page
            result_page = requests.get(full_url)
            
            if result_page.status_code == 200:
                # Parse the page content
                result_soup = BeautifulSoup(result_page.content, 'html.parser')
                
                # Locate the shelf life element using the provided CSS selector
                shelf_life_element = result_soup.select_one(
                    "body > section > div > div:nth-child(2) > div.col-lg-8.col-sm-8.col-md-8.col-xs-12.mobile-padding-space.colpadding > div > div.food-inside.clearfix > div.food-storage-right.image3 > div > span"
                )
                
                if shelf_life_element:
                    result = "Shelf Life: " + shelf_life_element.get_text(strip=True)
                    return result


                else:
                    result = "Shelf life information not found."
                    return result


