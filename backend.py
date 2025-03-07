from flask import Flask, request, jsonify
from flask_cors import CORS  # To avoid CORS issues when frontend & backend are separate
import pickle
import pandas as pd
import requests
import gdown  # For downloading from Google Drive
import os
import gzip  # For handling compressed files

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load movies list from local directory (assuming it's already available)
movies_df = pickle.load(open("movie_list.pkl", "rb"))

# Load similarity.pkl.gz from Google Drive if missing
SIMILARITY_FILE_ID = "1g0sN-DPJix37wjcMRPCq1f7BH9bqZwkG"
SIMILARITY_PATH = "similarity.pkl"
COMPRESSED_SIMILARITY_PATH = "similarity.pkl.gz"

if not os.path.exists(SIMILARITY_PATH):
    print("Downloading similarity.pkl.gz from Google Drive...")
    gdown.download(f"https://drive.google.com/uc?id={SIMILARITY_FILE_ID}", COMPRESSED_SIMILARITY_PATH, quiet=False)
    
    # Decompress the file
    print("Decompressing similarity.pkl.gz...")
    with gzip.open(COMPRESSED_SIMILARITY_PATH, "rb") as f_in, open(SIMILARITY_PATH, "wb") as f_out:
        f_out.write(f_in.read())

    print("Decompression complete.")

# Check if similarity.pkl exists before loading
if os.path.exists(SIMILARITY_PATH):
    with open(SIMILARITY_PATH, "rb") as f:
        similarity = pickle.load(f)
else:
    similarity = None
    print("Error: similarity.pkl could not be loaded.")

# Function to fetch movie poster from TMDB
def fetch_poster(movie_id):
    API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"

    try:
        data = requests.get(url).json()
        if "poster_path" in data and data["poster_path"]:
            return f"https://image.tmdb.org/t/p/w500/{data['poster_path']}"
    except requests.RequestException as e:
        print(f"Error fetching poster: {e}")

    return "https://via.placeholder.com/500x750?text=No+Image"

# API Endpoint to Recommend Movies
@app.route("/recommend", methods=["GET"])
def recommend():
    if similarity is None:
        return jsonify({"error": "Similarity data not available"}), 500

    movie = request.args.get("movie")  # Get movie name from request
    if movie not in movies_df["title"].values:
        return jsonify({"error": "Movie not found"}), 404

    index = movies_df[movies_df["title"] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movies = []
    for i in distances[1:6]:  # Get top 5 recommendations
        movie_id = movies_df.iloc[i[0]].movie_id
        recommended_movies.append(
            {
                "title": movies_df.iloc[i[0]].title,
                "poster": fetch_poster(movie_id),  # Fetch poster with error handling
            }
        )

    return jsonify(recommended_movies)

if __name__ == "__main__":
    app.run(debug=True)
