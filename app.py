from flask import Flask, request, jsonify
from views import views

app = Flask(__name__)
app.register_blueprint(views, url_prefix="/veiws")

def process():
    try:
        # Safely parse JSON from the request
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        # Extract the text and process it
        input_text = data['text']
        print(f"Received text: {input_text}")

        reversed_text = input_text[::-1]

        return jsonify({"original": input_text, "reversed": reversed_text})
    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)

print(app.url_map)  # Prints all the routes registered with Flask
