from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allows frontend requests

# Database connection
def get_db_connection():
    conn = sqlite3.connect("users.db")  # Ensure correct database file
    conn.row_factory = sqlite3.Row
    return conn

# Create 'user' table if it doesn't exist
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            preferred_language TEXT,
            favorite_author TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_table()  # Ensure table is created when backend starts

# Signup Route
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        username = data['username']
        password = data['password']
        preferred_language = data['preferredLanguage']
        favorite_author = data['favoriteAuthor']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert user data into database
        cursor.execute('''
            INSERT INTO user (username, password, preferred_language, favorite_author) 
            VALUES (?, ?, ?, ?)
        ''', (username, password, preferred_language, favorite_author))

        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully!"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"message": "Username already exists!"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
