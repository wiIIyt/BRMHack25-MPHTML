from fatsecret import Fatsecret
import spacy

fs = Fatsecret('9ad9d6c509b541e397e45f3eaeee2259', '594ec0639817489abd7a391f229f3b60')

def foodSearch(food):
    try:
        foods = fs.foods_search(food)
        for f in foods:
            return f["food_name"]
    except Exception as e:
        # If an error occurs, skip the search and print the error message
        print(f"Error occurred while searching food: {e}")


# Load the pre-trained word vectors
nlp = spacy.load("en_core_web_md")

def is_semantically_similar(word1, word2, threshold=0.8):
    """
    Function to check if two words are semantically similar based on cosine similarity of word vectors.
    """
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
a = foodSearch("baby")
# Example usage
word1 = "baby"
word2 = a


result = is_semantically_similar(word1, word2)
if result:
    print(f"Words are semantically similar: {result}")
else:
    print("Words are not semantically similar, skipping.")


