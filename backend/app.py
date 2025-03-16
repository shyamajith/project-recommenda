from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/')
def home():
    return "Backend is running!"

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if not data:
        return jsonify({"message": "Invalid data"}), 400
    
    username = data.get("username")
    password = data.get("password")
    preferred_language = data.get("preferredLanguage")
    favorite_author = data.get("favoriteAuthor")

    if not username or not password or not preferred_language or not favorite_author:
        return jsonify({"message": "All fields are required"}), 400

    # Inserting into database logic here
    return jsonify({"message": "Signup successful!"}), 201

if __name__ == "__main__":
    app.run(debug=True)
