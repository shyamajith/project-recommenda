from flask import Blueprint, request, jsonify
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

recommendation_blueprint = Blueprint('recommend', __name__)

# Load dataset
df = pd.read_csv('book_info.csv')

# Generate TF-IDF for genre + language
tfidf = TfidfVectorizer(stop_words='english')
df['combined_features'] = df['genre'].astype(str) + " " + df['language'].astype(str)
tfidf_matrix = tfidf.fit_transform(df['combined_features'])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

@recommendation_blueprint.route('/recommend/<username>', methods=['GET'])
def recommend(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_genres = user.genres.split(',')
    filtered_books = df[df['genre'].isin(user_genres)]
    
    recommendations = filtered_books['title'].tolist()[:10]
    return jsonify({"recommendations": recommendations})
