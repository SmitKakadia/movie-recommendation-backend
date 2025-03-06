from flask import Flask, request, jsonify
from flask_cors import CORS  # To avoid CORS issues when frontend & backend are separate
import pickle
import pandas as pd
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load preprocessed data
movies_df = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Function to fetch movie poster from TMDB
def fetch_poster(movie_id):
    API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    
    try:
        data = requests.get(url).json()
        if data.get('poster_path'):
            return f"https://image.tmdb.org/t/p/w500/{data['poster_path']}"
    except:
        pass
    
    return "https://via.placeholder.com/500x750?text=No+Image"

# API Endpoint to Recommend Movies
@app.route('/recommend', methods=['GET'])
def recommend():
    movie = request.args.get('movie')  # Get movie name from request
    if movie not in movies_df['title'].values:
        return jsonify({"error": "Movie not found"}), 404

    index = movies_df[movies_df['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movies = []
    for i in distances[1:6]:  # Get top 5 recommendations
        movie_id = movies_df.iloc[i[0]].movie_id
        recommended_movies.append({
            "title": movies_df.iloc[i[0]].title,
            "poster": fetch_poster(movie_id)  # Fixing the key to match frontend
        })

    return jsonify(recommended_movies)

if __name__ == '__main__':
    app.run(debug=True)
