from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD, NMF
from sklearn.neighbors import NearestNeighbors
import numpy as np

app = Flask(__name__)
CORS(app)

# Absolute path to db.sqlite and book_info.csv
DB_PATH = os.path.join(os.path.dirname(__file__), 'db.sqlite')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'book_info.csv')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Deleted existing database at {DB_PATH}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            preferredLanguage TEXT NOT NULL,
            favoriteAuthor TEXT NOT NULL,
            genres TEXT NOT NULL
        )
    ''')
    conn.commit()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    table_exists = cursor.fetchone()
    if table_exists:
        print(f"Users table created successfully in {DB_PATH}")
    else:
        print(f"Failed to create users table in {DB_PATH}")
    
    conn.close()
    print(f"Database initialized at {DB_PATH}")

# Load and prepare ML model at startup
df = pd.read_csv(DATA_PATH)

def clean_data(df):
    df.replace(r'<function.*?>', 'Unknown', regex=True, inplace=True)
    df.fillna('Unknown', inplace=True)
    return df

df = clean_data(df)
df = df.head(5000)

def create_combined_features(df):
    combined = df[['genre', 'language', 'country', 'publisher', 'author']].astype(str).agg(' '.join, axis=1)
    df['combined_features'] = combined
    return df

df = create_combined_features(df)

label_encoders = {}
for col in ['author', 'genre', 'language', 'country', 'publisher']:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    label_encoders[col] = le

scaler = StandardScaler()
df[['author', 'genre', 'language', 'country', 'publisher']] = scaler.fit_transform(df[['author', 'genre', 'language', 'country', 'publisher']])

tfidf = TfidfVectorizer(stop_words='english', max_features=1000)
tfidf_matrix = tfidf.fit_transform(df['combined_features'])

cosine_sim = cosine_similarity(tfidf_matrix)

svd = TruncatedSVD(n_components=50, random_state=42)
nmf = NMF(n_components=50, random_state=42)
book_matrix_svd = svd.fit_transform(tfidf_matrix)
book_matrix_nmf = nmf.fit_transform(tfidf_matrix)
book_matrix_combined = np.hstack((book_matrix_svd, book_matrix_nmf))

knn = NearestNeighbors(n_neighbors=5, metric='cosine', algorithm='auto')
knn.fit(book_matrix_combined)

def recommend_books(book_name, df, knn, cosine_sim, book_matrix_combined):
    if book_name not in df['title'].values:
        return []
    
    book_idx = df[df['title'] == book_name].index[0]
    sim_scores = list(enumerate(cosine_sim[book_idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    content_recs = [df['title'].iloc[i[0]] for i in sim_scores[1:4]]

    distances, indices = knn.kneighbors([book_matrix_combined[book_idx]])
    collab_recs = [df['title'].iloc[i] for i in indices[0][1:4]]

    combined_recommendations = list(dict.fromkeys(content_recs + collab_recs))
    return combined_recommendations[:5]

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if data is None:
        print("No JSON data received")
        return jsonify({'message': 'No JSON data received'}), 400

    print('Received signup data:', data)
    username = data.get('username')
    password = data.get('password')
    preferredLanguage = data.get('preferredLanguage')
    favoriteAuthor = data.get('favoriteAuthor')
    genres = data.get('genres')

    print('Username:', username)
    print('Password:', password)
    print('PreferredLanguage:', preferredLanguage)
    print('FavoriteAuthor:', favoriteAuthor)
    print('Genres:', genres)

    missing_fields = []
    if not username:
        missing_fields.append('username')
    if not password:
        missing_fields.append('password')
    if not preferredLanguage:
        missing_fields.append('preferredLanguage')
    if not favoriteAuthor:
        missing_fields.append('favoriteAuthor')
    if not genres or len(genres) != 5:
        missing_fields.append('genres (must select exactly 5)')

    if missing_fields:
        print('Missing fields:', missing_fields)
        return jsonify({'message': 'Missing required fields', 'missing': missing_fields}), 400

    genres_str = ','.join(genres)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password, preferredLanguage, favoriteAuthor, genres)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password, preferredLanguage, favoriteAuthor, genres_str))
        conn.commit()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        inserted_user = cursor.fetchone()
        print(f"Inserted user data: {dict(inserted_user) if inserted_user else 'Not found'}")
        
        conn.close()
        return jsonify({'message': 'User created successfully', 'username': username}), 201
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        return jsonify({'message': 'Database error', 'error': str(e)}), 500
    except sqlite3.IntegrityError:
        print(f"Username {username} already exists")
        return jsonify({'message': 'Username already exists'}), 400
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'message': 'Server error', 'error': str(e)}), 500

@app.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    if data is None:
        print("No JSON data received")
        return jsonify({'message': 'No JSON data received', 'success': False}), 400

    print('Received signin data:', data)
    username = data.get('username')
    password = data.get('password')

    print('Username:', username)
    print('Password:', password)

    if not username or not password:
        missing_fields = []
        if not username:
            missing_fields.append('username')
        if not password:
            missing_fields.append('password')
        print('Missing fields:', missing_fields)
        return jsonify({'message': 'Missing username or password', 'missing': missing_fields, 'success': False}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        print('Fetched user:', dict(user) if user else None)
        conn.close()

        if not user:
            print(f"Signin failed: No user found for {username}")
            return jsonify({'message': 'Invalid username or password', 'success': False}), 401

        stored_password = user['password']
        print('Stored password:', stored_password)
        if password == stored_password:
            print(f"Signin successful for {username}")
            return jsonify({
                'message': 'Signin successful',
                'success': True,
                'username': username,
                'preferredLanguage': user['preferredLanguage'],
                'favoriteAuthor': user['favoriteAuthor']
            }), 200
        else:
            print(f"Signin failed: Incorrect password for {username}")
            return jsonify({'message': 'Invalid username or password', 'success': False}), 401
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        return jsonify({'message': 'Database error', 'error': str(e), 'success': False}), 500
    except Exception as e:
        print(f"Signin error: {e}")
        return jsonify({'message': 'Server error', 'error': str(e), 'success': False}), 500

@app.route('/trending-books', methods=['GET'])
def get_trending_books():
    # Updated with your manually provided trending books
    trending_books = [
        {"title": "You Are Fatally Invited", "image": "https://images1.penguinrandomhouse.com/cover/9780593871577"},
        {"title": "Harlem Rhapsody", "image": "https://images1.penguinrandomhouse.com/cover/9780593638484"},
        {"title": "I Am the Cage", "image": "https://images3.penguinrandomhouse.com/cover/9780593616918"},
        {"title": "Three Days in June", "image": "https://images2.penguinrandomhouse.com/cover/9780593803486"},
        {"title": "First-Time Caller", "image": "https://images1.penguinrandomhouse.com/cover/9780593641194"}
    ]
    return jsonify({'trending_books': trending_books}), 200

@app.route('/recommend-books', methods=['POST'])
def recommend_books_endpoint():
    data = request.get_json()
    if data is None or 'book_name' not in data:
        return jsonify({'message': 'Book name is required'}), 400

    book_name = data['book_name']
    print(f"Recommending books for: {book_name}")
    recommendations = recommend_books(book_name, df, knn, cosine_sim, book_matrix_combined)
    
    if not recommendations:
        return jsonify({'message': 'Book not found or no recommendations available', 'recommendations': []}), 404
    
    return jsonify({'message': 'Recommendations found', 'recommendations': recommendations}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000, threaded=False)