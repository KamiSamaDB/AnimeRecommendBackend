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

## ☁️ Deployment Options

### 🚀 Vercel Deployment (Recommended for React Apps)

**Prerequisites:**
- [Vercel CLI](https://vercel.com/cli) installed: `npm i -g vercel`
- Vercel account (free tier available)
- GitHub repository (recommended)

#### Quick Deploy
```bash
# 1. Login to Vercel
vercel login

# 2. Deploy from project directory
vercel

# 3. Follow prompts:
#    - Link to existing project? N
#    - Project name: anime-recommender-api
#    - Directory: ./
#    - Override settings? N
```

#### Production Deploy
```bash
# Deploy to production
vercel --prod
```

#### Checking Deployment Success
1. **Vercel Dashboard**: Visit [vercel.com/dashboard](https://vercel.com/dashboard)
2. **Disable Deployment Protection** (for API access):
   - Go to Project Settings → Deployment Protection
   - Turn off protection for public API access
3. **Test Health Endpoint**:
   ```bash
   curl https://anime-recommend-backend.vercel.app/health
   ```
4. **Test API Endpoint**:
   ```bash
   curl -X POST https://anime-recommend-backend.vercel.app/api/recommendations \
   -H "Content-Type: application/json" \
   -d '{"user_anime_list": [1, 5, 16], "max_recommendations": 5}'
   ```

#### Your Deployed URLs
- **Production**: `https://anime-recommend-backend.vercel.app`
- **Latest Preview**: `https://anime-recommend-backend-2tsxy8qge-kamisamadbs-projects.vercel.app`

#### Troubleshooting Vercel Issues
- **Authentication Required**: Disable "Deployment Protection" in Vercel project settings
- **Import Errors**: The API includes fallback error handling for serverless environment
- **Build Failures**: Check the minimal `requirements.txt` contains only essential dependencies

#### Environment Variables (Optional)
If you need environment variables, set them in Vercel:
```bash
vercel env add ENVIRONMENT_VARIABLE_NAME
```

### 🔵 Azure Deployment (Alternative)

**Prerequisites:**
- Azure account with active subscription
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed

#### Deploy to Azure App Service
```bash
# 1. Login to Azure
az login

# 2. Create resource group
az group create --name anime-recommender-rg --location "East US"

# 3. Create App Service plan
az appservice plan create --name anime-recommender-plan --resource-group anime-recommender-rg --sku FREE --is-linux

# 4. Create web app
az webapp create --resource-group anime-recommender-rg --plan anime-recommender-plan --name your-anime-api --runtime "PYTHON|3.10" --deployment-local-git

# 5. Configure startup command
az webapp config set --resource-group anime-recommender-rg --name your-anime-api --startup-file "start_server.py"

# 6. Deploy code
git remote add azure https://your-anime-api.scm.azurewebsites.net:443/your-anime-api.git
git push azure main
```

### 🌐 Updating Your React App for Production

#### Environment Configuration
**Create `.env` file in your React app:**
```env
# For local development
REACT_APP_API_URL=http://localhost:5000

# For production (update when deploying)
# REACT_APP_API_URL=https://your-app-name.vercel.app
```

#### Updated API Integration
**Replace your React API calls:**

```javascript
// Before (hardcoded localhost)
const API_BASE_URL = 'http://localhost:5000';

// After (production ready)
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://anime-recommend-backend.vercel.app';

// Example recommendation function
const getRecommendations = async (userAnimeList) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/recommendations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_anime_list: userAnimeList,
        max_recommendations: 10
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.recommendations;
  } catch (error) {
    console.error('Error fetching recommendations:', error);
    throw error;
  }
};

// Example search function
const searchAnime = async (query) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Search failed');
    return await response.json();
  } catch (error) {
    console.error('Search error:', error);
    throw error;
  }
};
```

#### Production Checklist for React App
- [ ] Update `REACT_APP_API_URL` in `.env.production`
- [ ] Test API endpoints after deployment
- [ ] Verify CORS is working between domains
- [ ] Update any hardcoded localhost references
- [ ] Test error handling for network failures

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