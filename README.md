# 🏔️ Gantabya Sahayak — गन्तब्य सहायक
### Nepal Smart Tourism WebGIS Platform

A comprehensive web-based geospatial platform for Nepal tourism, combining interactive mapping, spatial analysis, and real-time data to help tourists navigate Nepal safely and intelligently.

---

## 🚀 Quick Start

### Option 1 — Double-click Launcher (Easiest)
```
Double-click: start.bat
```

### Option 2 — PowerShell
```powershell
.\start.ps1
```

### Option 3 — Manual
```bash
# Single FastAPI server
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000

# Open browser: http://localhost:8000
```

**Requirements:** Python 3.10+

---

## 🗂️ System Modules

| # | Module | Page | Key Feature |
|---|--------|------|------------|
| 1 | Smart Road Condition Monitor | `roads.html` | Real-time status + alternative routes |
| 2 | Trekking Navigation | `trekking.html` | Routes + elevation profile + waypoints |
| 3 | Emergency Assistance | `emergency.html` | SOS + GPS nearest facility (Turf.js) |
| 4 | Seasonal Tourism Map | `seasonal.html` | Month-by-month suitability + charts |
| 5 | Risk & Hazard Mapping | `hazards.html` | Risk zones + location check (Turf.js) |
| 6 | Smart Trip Planner | `planner.html` | Budget itinerary + route map |
| 7 | Hidden Destinations | `discover.html` | 25+ off-beat places + table view |
| 8 | Cultural Heritage | `heritage.html` | UNESCO sites + Audio Guide |
| 9 | About / Documentation | `about.html` | Tech stack, architecture, links |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (served by FastAPI)           │
│  HTML5 + CSS3 + JS + MapLibre GL JS + Turf.js + Chart.js│
└───────────────────┬─────────────────────────────────────┘
                    │ REST API (JSON / GeoJSON)
┌───────────────────▼─────────────────────────────────────┐
│                    BACKEND + STATIC SERVER (Port 8000)   │
│          FastAPI (Python) + Uvicorn                      │
│    Spatial: GeoPandas • Haversine • Python stdlib        │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                  DATA LAYER                              │
│  GeoJSON Files (./data/) • Open-Meteo API (Weather)     │
│  [ PostgreSQL + PostGIS — for production deployment ]    │
└─────────────────────────────────────────────────────────┘
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/provinces` | Nepal province boundaries |
| GET | `/api/districts` | District boundaries |
| GET | `/api/local-levels` | Local level (Palika) boundaries |
| GET | `/api/roads` | Road conditions |
| GET | `/api/trekking` | Trekking routes |
| GET | `/api/trekking-waypoints` | Campsites, water, rescue |
| GET | `/api/emergency` | Emergency facilities |
| GET | `/api/emergency/nearest?lat=&lng=&type=` | Nearest facility (Haversine) |
| GET | `/api/hazards` | Hazard zones |
| GET | `/api/seasonal` | Seasonal tourism data |
| POST | `/api/trip/plan` | Generate itinerary |
| GET | `/api/destinations` | Hidden destinations |
| GET | `/api/heritage` | Heritage sites |
| GET | `/api/heritage/search?q=` | Search heritage |
| GET | `/api/weather?lat=&lng=` | Live weather (Open-Meteo) |
| GET | `/api/stats` | Platform statistics |
| GET | `/docs` | Interactive Swagger UI |

---

## 🗺️ Spatial Functions (Turf.js)

| Function | Module | Purpose |
|----------|--------|---------|
| `turf.nearestPoint()` | Emergency | Find nearest hospital/rescue to GPS |
| `turf.buffer()` | Emergency, Hazards, Discover | Proximity radius zones |
| `turf.distance()` | Trip Planner, Emergency | Distance between coordinates |
| `turf.booleanPointInPolygon()` | Hazards, Discover | Location in risk zone check |
| `turf.length()` | Trekking | Route distance in km |

---

## 📁 Project Structure

```
gantabya-sahayak/
├── start.bat              # Windows launcher (double-click to run)
├── start.ps1              # PowerShell launcher
├── README.md
│
├── backend/
│   ├── main.py            # FastAPI application (all routes)
│   └── requirements.txt   # Python dependencies
│
├── frontend/
│   ├── index.html         # Landing page (auth, hero, module grid)
│   ├── styles/
│   │   └── main.css       # Global design system (#468432 theme)
│   ├── js/
│   │   └── app.js         # Shared utilities (auth, API, maps, turf)
│   └── pages/
│       ├── roads.html     # Module 1
│       ├── trekking.html  # Module 2
│       ├── emergency.html # Module 3
│       ├── seasonal.html  # Module 4
│       ├── hazards.html   # Module 5
│       ├── planner.html   # Module 6
│       ├── discover.html  # Module 7
│       ├── heritage.html  # Module 8
│       └── about.html     # Documentation
│
└── data/
    ├── nepal-provinces.geojson
    ├── nepal-districts.geojson
    ├── nepal-local-levels.geojson
    ├── road-conditions.geojson
    ├── trekking-routes.geojson
    ├── trekking-waypoints.geojson
    ├── emergency-facilities.geojson
    ├── hazard-zones.geojson
    ├── hidden-destinations.geojson
    ├── heritage-sites.geojson
    └── seasonal-data.json
```

---

## 🎨 Design

- **Primary Color:** `#468432` (Himalayan Forest Green)
- **Theme:** Dark mode with glassmorphism
- **Fonts:** Outfit (English) + Noto Sans Devanagari (Nepali)
- **Maps:** MapLibre GL JS v4.3 (OpenStreetMap / Satellite / Terrain)
- **Charts:** Chart.js v4.4

## ☁️ Deploying to Render

Render can host this app as a single Python web service because the FastAPI backend now serves the frontend static files directly.

1. Create a Render account at https://render.com and connect your GitHub/GitLab repo.
2. Add a new **Web Service**.
3. Use `python` as the environment.
4. Set the repo root as the deploy root.
5. Set the build command to:
   ```bash
   pip install -r backend/requirements.txt
   ```
6. Set the start command to:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
7. Ensure `render.yaml` is present at the repo root so Render can auto-detect the service.

### Notes
- The frontend now uses `window.location.origin` for API calls, so the same domain serves both UI and API.
- The FastAPI app mounts `frontend/` as static files and serves `index.html` at `/`.
- `data/` is also mounted at `/data` so GeoJSON assets remain available.

If you want, I can also add a simple `README` badge for the Render URL after deployment.
---

## 🌐 Base Maps

| Name | Provider | URL Pattern |
|------|----------|-------------|
| Street Map | OpenStreetMap | `tile.openstreetmap.org/{z}/{x}/{y}.png` |
| Satellite | Esri World Imagery | ArcGIS REST tile service |
| Terrain | OpenTopoMap | `tile.opentopomap.org/{z}/{x}/{y}.png` |

---

## 📊 Data Sources

- **Admin Boundaries:** geoBoundaries.org / OpenStreetMap
- **Trekking Routes:** OpenStreetMap (Overpass API)
- **Heritage Sites:** UNESCO World Heritage List + OpenStreetMap
- **Emergency Facilities:** OpenStreetMap + Government of Nepal
- **Hazard Zones:** BIPAD Portal Nepal / ICIMOD
- **Road Conditions:** Department of Roads Nepal (DoR)
- **Weather:** Open-Meteo API (free, no API key needed)

---

## 📝 Submission Checklist

- [ ] Add your GitHub repository link in `about.html`
- [ ] Add YouTube demo video link in `about.html`
- [ ] Add your deployed URL in `about.html`
- [ ] Fill in your institution and department name in `about.html`
- [ ] Deploy to a hosting platform (Render, Railway, or VPS)

---

## 👨‍💻 Academic Project

**Institution:** Tribhuvan University, Institute of Engineering  
**Department:** Department of Geomatics Engineering  
**Course:** Web-Based GIS / Advanced GIS  
**Year:** 2025/2026  
**Study Area:** Nepal (Province → District → Local Level)

---

*Built with ❤️ for Nepal Tourism — Gantabya Sahayak | गन्तब्य सहायक*
