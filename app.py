from flask import Flask, request, jsonify
from views import views

app = Flask(__name__)
app.register_blueprint(views, url_prefix="/veiws")

@app.route('/process', methods=['POST'])  # This listens for POST requests at the "/process" URL
def process():
    # Get the JSON data sent by the frontend
    data = request.json
    
    # Extract the "text" field from the JSON data
    input_text = data.get('text', '')  # If "text" is missing, use an empty string as a default

    # Process the text (reverse it, just as an example)
    reversed_text = input_text[::-1]  # This slices the string backward to reverse it

    # Send a response back to the frontend as JSON
    return jsonify({"original": input_text, "reversed": reversed_text})


if __name__ == '__main__':
    app.run(debug=True,port=8000)
