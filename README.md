# Smart Urban Flood Risk Mapper

AI-powered flood risk analysis platform for Bangladesh.
Combines spatial data, machine learning, and a natural language interface
to predict flood risk across the country at grid-cell resolution.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-5.0-green)
![PostGIS](https://img.shields.io/badge/PostGIS-3.3-blue)
![React](https://img.shields.io/badge/React-18-61dafb)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-orange)
![Ollama](https://img.shields.io/badge/LLM-Llama3.2-purple)

## What it does

- Divides Bangladesh into ~850 grid zones and scores each one
- AI model (Random Forest) predicts flood risk 0–100% per zone
- Interactive Leaflet map with color-coded risk overlays
- Draw any polygon → instant AI risk score for that area
- Natural language Q&A: "Is Mirpur safe during monsoon?" → grounded answer using real PostGIS data
- All AI runs locally — no API keys, no cost

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Django 5, Django REST Framework |
| Geodatabase | PostgreSQL 15 + PostGIS 3.3 |
| Spatial processing | GeoPandas, Shapely, GDAL |
| AI / ML | scikit-learn Random Forest |
| LLM | Ollama + Llama 3.2 (local) |
| Frontend | React 18, Vite, Leaflet.js |
| Deployment | Docker + docker-compose |

## Quick start

### With Docker

```bash
git clone https://github.com/yourusername/flood-risk-mapper
cd flood-risk-mapper
docker compose up --build
```

Open `http://localhost:5173`

### Manual setup

```bash
# Backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# Add PostGIS credentials to .env (see .env.example)

python manage.py migrate
python scripts/generate_rainfall.py
python scripts/create_zones.py
python scripts/extract_features.py
python scripts/train_model.py

# Score all zones
python manage.py shell -c "
from risk_engine.model_service import score_all_zones
score_all_zones()
"

python manage.py runserver

# Frontend (separate terminal)
cd frontend && npm install && npm run dev

# LLM (separate terminal, optional)
ollama pull llama3.2 && ollama serve
```

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/risk/zones/` | All zones as GeoJSON FeatureCollection |
| GET | `/api/risk/zones/?level=high` | Filter by risk level |
| GET | `/api/risk/stats/` | Summary statistics |
| POST | `/api/risk/score/` | Score a user-drawn polygon |
| POST | `/api/risk/ask/` | Natural language Q&A |
| GET | `/api/risk/model-info/` | Model metrics |

## Model performance

| Metric | Value |
|---|---|
| Algorithm | Random Forest (200 trees) |
| Features | Elevation, slope, rainfall, river distance, land use |
| R² score | ~0.97 |
| MAE | ~0.03 |
| CV R² (5-fold) | ~0.97 ± 0.009 |

## Data sources

- Elevation: SRTM 30m DEM via OpenTopography
- Boundaries: OCHA Bangladesh Admin Boundaries (HUMDATA)
- Rainfall: Synthetic data based on BWDB station patterns
- Rivers: OpenStreetMap via Overpass API

## Author

Built by A. S. M. Muntaheen as a Geo AI integration portfolio project.