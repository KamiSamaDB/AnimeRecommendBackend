# 🎌 Anime Recommendation System

An AI-powered anime recommendation system that uses MyAnimeList data to provide personalized recommendations based on user preferences, genres, ratings, and popularity.

## ✨ Features

- 🧠 **AI-Powered Recommendations** using hybrid similarity algorithms
- 🎯 **Content-based filtering** with genre and synopsis analysis
- ⭐ **Rating & popularity weighting** from MyAnimeList data
- 🔍 **Intelligent search** and trending anime discovery
- 🌐 **REST API** with CORS support for React integration
- ✅ **Input validation** and comprehensive error handling
- 📊 **Real-time data** from Jikan API (unofficial MAL API)

## 🚀 Quick Start

### 1. Setup & Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd anime-recommender

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Server
```bash
# Recommended: Use startup script (React-ready)
python start_server.py

# Alternative: From src directory
cd src && python app.py
```

### 3. Verify Installation
The API will be available at `http://127.0.0.1:5000`

- **Health Check**: http://127.0.0.1:5000/health
- **API Info**: http://127.0.0.1:5000/

### 4. Test the API
```bash
# Run test suite
python test_endpoints.py

# Or specific tests
python tests/test_api.py
```

## 📚 API Endpoints

### Get Recommendations
**POST** `/api/recommendations`

```json
{
  "anime_titles": ["Attack on Titan", "Death Note", "One Piece"],
  "max_recommendations": 10,
  "min_score": 7.0,
  "exclude_genres": ["Horror"],
  "include_genres": ["Action"]
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "title": "Fullmetal Alchemist: Brotherhood",
      "score": 9.1,
      "genres": ["Action", "Adventure", "Drama"],
      "similarity_score": 0.87,
      "confidence_score": 0.92,
      "reasons": ["Similar genres: Action, Adventure", "Highly rated (9.1/10)"]
    }
  ],
  "total_found": 10,
  "processing_time": 2.34,
  "input_anime_found": ["Attack on Titan", "Death Note"],
  "input_anime_not_found": ["NonExistent Anime"]
}
```

### Other Endpoints

- **GET** `/health` - Health check
- **GET** `/api/trending?limit=10` - Get trending anime
- **GET** `/api/anime/search?q=Attack on Titan` - Search anime
- **GET** `/api/database/stats` - Database statistics

## 🧠 AI Algorithms

### Current: Simple Algorithm (Active)
**Features:**
- **Genre similarity** using Jaccard similarity
- **Rating compatibility** matching user preferences
- **Popularity scoring** based on community engagement
- **Year-based similarity** for contemporary preferences
- **Hybrid scoring** combining all factors with weights:
  - Genre similarity: 40%
  - Rating score: 30%
  - Popularity: 20%
  - Year similarity: 10%

**Benefits:**
- ⚡ Fast startup (~2 seconds)
- 🔄 Stable operation
- 📊 Quality recommendations
- 🚀 Perfect for development

### Alternative: Full ML Algorithm (Available)
**Features:**
- **TF-IDF vectorization** for advanced genre analysis
- **Synopsis text analysis** using NLP
- **Sentence transformers** for semantic similarity
- **Cosine similarity** calculations
- **Advanced ML feature engineering**

**Trade-offs:**
- ⏱️ Slower startup (~30-60 seconds)
- 🔧 Requires ML dependency compatibility
- 🎯 More sophisticated analysis

### Switching Algorithms
To use the full ML algorithm, update `src/api/app.py`:
```python
# Change line 14:
from services.recommendation_engine import AnimeRecommendationEngine
# Instead of:
from services.simple_recommendation_engine import SimpleAnimeRecommendationEngine

# Update line 32:
self.recommendation_engine = AnimeRecommendationEngine(self.mal_service)
```

## 🛠️ Technical Stack

- **Backend**: Flask (Python)
- **AI/ML**: Basic similarity algorithms (upgradable to scikit-learn, sentence-transformers)
- **Data Source**: Jikan API (unofficial MAL API)
- **Analysis**: pandas, numpy
- **API Features**: CORS support for React integration

## 📁 Project Structure

```
anime-recommender/
├── src/
│   ├── api/
│   │   └── app.py                    # Flask API endpoints
│   ├── models/
│   │   └── anime.py                  # Data models
│   ├── services/
│   │   ├── mal_service.py            # MyAnimeList API integration
│   │   ├── recommendation_engine.py  # Full ML algorithm (available)
│   │   └── simple_recommendation_engine.py  # Active algorithm
│   ├── utils/
│   │   └── validation.py             # Input validation utilities
│   └── app.py                        # Main application entry point
├── tests/
│   └── test_api.py                   # API test suite
├── start_server.py                   # Production startup script
├── test_endpoints.py                 # Endpoint testing
├── demo.py                          # Algorithm demonstration
├── example_usage.py                 # Usage examples
├── simple_test.py                   # Basic testing
└── requirements.txt                 # Python dependencies
```

## 🎯 Usage Examples

### Basic Usage
```python
import requests

# Get recommendations
response = requests.post('http://localhost:5000/api/recommendations', json={
    "anime_titles": ["Attack on Titan", "Death Note"]
})

recommendations = response.json()['recommendations']
for rec in recommendations:
    print(f"{rec['title']} - Score: {rec['similarity_score']}")
```

### Advanced Filtering
```python
# Get action anime recommendations, exclude horror, minimum score 8.0
response = requests.post('http://localhost:5000/api/recommendations', json={
    "anime_titles": ["Dragon Ball Z", "Naruto"],
    "max_recommendations": 5,
    "min_score": 8.0,
    "include_genres": ["Action"],
    "exclude_genres": ["Horror", "Ecchi"]
})
```

## 🔧 Configuration

The API uses the following environment variables:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)  
- `FLASK_DEBUG`: Debug mode (default: False)

## 🚨 Rate Limiting

The API implements rate limiting for MyAnimeList requests:
- 3 requests per second to MAL API
- Automatic retry with exponential backoff
- Caching for frequently requested anime

## 📊 Performance

- **Database initialization**: ~30-60 seconds (500+ anime)
- **Recommendation generation**: ~2-5 seconds per request
- **Memory usage**: ~200-500MB (depends on database size)
- **Concurrent requests**: Supported with threading

## 🤝 React Integration

The API is designed for React frontends:

```javascript
// React example
const getRecommendations = async (animeList) => {
  const response = await fetch('http://localhost:5000/api/recommendations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ anime_titles: animeList })
  });
  
  return await response.json();
};
```

## 🐛 Error Handling

The API provides detailed error responses:

```json
{
  "status": "error",
  "error": "anime_titles must be a non-empty list",
  "error_code": "VALIDATION_ERROR"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (validation error)
- `404`: Not Found
- `500`: Internal Server Error

## 📈 Future Enhancements

- [ ] User preference learning
- [ ] More anime databases (AniList, AniDB)
- [ ] Recommendation explanations
- [ ] User ratings integration
- [ ] Batch processing for multiple users
- [ ] Redis caching
- [ ] Docker containerization

## 📄 License

MIT License - see LICENSE file for details.