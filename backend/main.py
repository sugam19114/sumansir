"""
Gantabya Sahayak (गन्तब्य सहायक) — Nepal Tourism WebGIS Platform
FastAPI Backend — serves spatial data, user auth (mock), and trip planning
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json, os, random
from pathlib import Path

app = FastAPI(
    title="Gantabya Sahayak API",
    description="Nepal Tourism WebGIS Platform — Backend API",
    version="1.0.0"
)

# Allow frontend to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent.parent / "data"
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# GeoJSON boundary files are much faster to deliver as static files than by
# serialising several megabytes of JSON for every request.  The frontend uses
# this endpoint for map layers and retains the /api routes for API consumers.
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

# ─── Helper ─────────────────────────────────────────────────────────────────
def load_geojson(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Data file {filename} not found")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# ─── Auth Models ─────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    name: str
    photo: str = ""

class TripRequest(BaseModel):
    budget: int
    days: int
    interests: list[str]
    vehicle: str
    start_location: str

# ─── Root ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/api/health")
def health():
    return {"status": "healthy", "platform": "Gantabya Sahayak", "country": "Nepal"}

# ─── Auth (Mock Google Login) ─────────────────────────────────────────────────
@app.post("/api/auth/login")
def login(req: LoginRequest):
    """Simulate Google OAuth login. In production, verify Google ID token here."""
    if not req.email or not req.name:
        raise HTTPException(status_code=400, detail="Email and name are required")
    token = f"gs_token_{abs(hash(req.email)) % 999999:06d}"
    return {
        "success": True,
        "token": token,
        "user": {
            "email": req.email,
            "name": req.name,
            "photo": req.photo or "https://ui-avatars.com/api/?name=" + req.name.replace(" ", "+") + "&background=468432&color=fff",
            "role": "tourist"
        },
        "message": "Login successful"
    }

@app.post("/api/auth/logout")
def logout():
    return {"success": True, "message": "Logged out successfully"}

# ─── Spatial / Map Data ───────────────────────────────────────────────────────
@app.get("/api/provinces")
def get_provinces():
    """Nepal province boundaries (GeoJSON)"""
    return load_geojson("province.geojson")

@app.get("/api/districts")
def get_districts():
    """Nepal district boundaries (GeoJSON)"""
    return load_geojson("district.geojson")

@app.get("/api/local-levels")
def get_local_levels():
    """Nepal local level (Palika) simplified boundaries"""
    return load_geojson("local.geojson")

# ─── Module 1: Road Conditions ────────────────────────────────────────────────
@app.get("/api/roads")
def get_roads():
    """Road conditions with status across Nepal"""
    return load_geojson("road-conditions.geojson")

@app.get("/api/roads/{status}")
def get_roads_by_status(status: str):
    """Filter roads by status: good, caution, damaged, closed, construction"""
    data = load_geojson("road-conditions.geojson")
    filtered = [f for f in data["features"] if f["properties"].get("status", "").lower() == status.lower()]
    return {"type": "FeatureCollection", "features": filtered}

# ─── Module 4: Trekking ───────────────────────────────────────────────────────
@app.get("/api/trekking")
def get_trekking_routes():
    """All trekking routes with metadata"""
    return load_geojson("trekking-routes.geojson")

@app.get("/api/trekking-waypoints")
def get_trekking_waypoints():
    """Campsites, water sources, shelters, rescue points"""
    return load_geojson("trekking-waypoints.geojson")

# OpenStreetMap relations contain the real, mapped footpath segments used by
# trekkers.  Cache them locally in memory so selecting a route does not keep
# sending requests to the public Overpass service.
_trail_geometry_cache = {}
_osm_trail_names = {
    "Langtang Valley Trek": "Langtang",
    "Mardi Himal Trek": "Mardi Himal",
    "Everest Base Camp Trek": "Everest Base Camp",
    "Annapurna Circuit": "Annapurna Circuit",
    "Manaslu Circuit Trek": "Manaslu Circuit",
    "Dhorpatan Hunting Reserve Trek": "Dhorpatan",
    "Rara Lake Trek": "Rara Lake",
    "Kanchenjunga Base Camp Trek": "Kanchenjunga",
}

@app.get("/api/trekking/{route_name}/geometry")
def get_mapped_trek_geometry(route_name: str):
    """Return mapped OpenStreetMap hiking segments for a trek when available."""
    import re
    import urllib.parse
    import urllib.request

    if route_name in _trail_geometry_cache:
        return _trail_geometry_cache[route_name]

    search_name = _osm_trail_names.get(route_name)
    if not search_name:
        return {"source": "Detailed offline route geometry", "geometry": None}

    # Nepal bounding box keeps the query small and avoids matching similarly
    # named trails in other countries.
    query = (
        '[out:json][timeout:35];'
        f'relation["route"="hiking"]["name"~"{re.escape(search_name)}",i](26,80,31,89);'
        'out geom;'
    )
    try:
        import math
        body = urllib.parse.urlencode({"data": query}).encode()
        req = urllib.request.Request(
            "https://overpass-api.de/api/interpreter", body,
            headers={"User-Agent": "GantabyaSahayak/1.0 (educational WebGIS)"}
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            osm = json.loads(response.read())
        relation = next((e for e in osm.get("elements", []) if e.get("members")), None)
        lines = []
        if relation:
            for member in relation.get("members", []):
                geometry = member.get("geometry") or []
                if len(geometry) > 1:
                    lines.append([[point["lon"], point["lat"]] for point in geometry])
        if lines:
            result = {
                "source": "OpenStreetMap hiking relation (ODbL)",
                "geometry": {"type": "MultiLineString", "coordinates": lines}
            }
            _trail_geometry_cache[route_name] = result
            return result
    except Exception:
        # The UI will use its offline checkpoint geometry if Overpass is busy
        # or temporarily unavailable.
        pass
    return {"source": "Detailed offline route geometry", "geometry": None}

@app.get("/api/trekking/{route_name}")
def get_trekking_route(route_name: str):
    """Get specific trekking route details."""
    data = load_geojson("trekking-routes.geojson")
    filtered = [f for f in data["features"] if route_name.lower() in f["properties"].get("name", "").lower()]
    if not filtered:
        raise HTTPException(status_code=404, detail="Trekking route not found")
    return {"type": "FeatureCollection", "features": filtered}

# ─── Module 5: Emergency ─────────────────────────────────────────────────────
@app.get("/api/emergency")
def get_emergency_facilities():
    """All emergency facilities: hospitals, police, rescue centers, helicopter pads"""
    return load_geojson("emergency-facilities.geojson")

@app.get("/api/emergency/nearest")
def get_nearest_facility(lat: float, lng: float, type: str = "all", limit: int = 5):
    """
    Find nearest emergency facilities to a given coordinate.
    Uses simple Haversine distance calculation.
    (In production: use PostGIS ST_Distance and network analysis)
    """
    import math
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    data = load_geojson("emergency-facilities.geojson")
    features = data["features"]
    if type != "all":
        features = [f for f in features if f["properties"].get("type", "").lower() == type.lower()]

    for f in features:
        coords = f["geometry"]["coordinates"]
        f["properties"]["distance_km"] = round(haversine(lat, lng, coords[1], coords[0]), 2)

    features.sort(key=lambda f: f["properties"]["distance_km"])
    return {"type": "FeatureCollection", "features": features[:limit]}

_live_emergency_cache = {}

@app.get("/api/emergency/nearby")
def get_live_emergency_facilities(lat: float, lng: float, type: str = "all", radius_km: float = 25):
    """Find nearby mapped emergency services and rank leading candidates by road distance."""
    import math
    import urllib.parse
    import urllib.request

    allowed = {"all", "hospital", "health_post", "police_station"}
    if type not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported emergency service type")
    radius_km = max(1, min(radius_km, 25))
    cache_key = (round(lat, 3), round(lng, 3), radius_km, type)
    if cache_key in _live_emergency_cache:
        return _live_emergency_cache[cache_key]

    radius_m = int(radius_km * 1000)
    groups = []
    if type in {"all", "hospital"}:
        groups.append(f'nwr["amenity"="hospital"](around:{radius_m},{lat},{lng});')
    if type in {"all", "health_post"}:
        groups.append(f'nwr["amenity"~"clinic|doctors"](around:{radius_m},{lat},{lng});')
    if type in {"all", "police_station"}:
        groups.append(f'nwr["amenity"="police"](around:{radius_m},{lat},{lng});')
    query = "[out:json][timeout:25];(" + "".join(groups) + ");out center 100;"
    try:
        body = urllib.parse.urlencode({"data": query}).encode()
        request = urllib.request.Request("https://overpass-api.de/api/interpreter", body, headers={"User-Agent": "GantabyaSahayak/1.0 (educational WebGIS)"})
        with urllib.request.urlopen(request, timeout=35) as response:
            raw = json.loads(response.read())
        features = []
        for element in raw.get("elements", []):
            tags = element.get("tags", {})
            point = element.get("center", element)
            if "lat" not in point or "lon" not in point:
                continue
            amenity = tags.get("amenity", "")
            kind = "hospital" if amenity == "hospital" else "police_station" if amenity == "police" else "health_post"
            lat2, lng2 = point["lat"], point["lon"]
            dlat, dlon = math.radians(lat2 - lat), math.radians(lng2 - lng)
            a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
            direct_distance = 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lng2, lat2]}, "properties": {
                "name": tags.get("name") or f"Unnamed {kind.replace('_', ' ')}", "type": kind,
                "address": " ".join(filter(None, [tags.get("addr:street"), tags.get("addr:city")])),
                "phone": tags.get("phone") or tags.get("contact:phone", ""), "website": tags.get("website") or tags.get("contact:website", ""),
                "opening_hours": tags.get("opening_hours", ""), "operator": tags.get("operator", ""),
                "emergency": tags.get("emergency", ""), "wheelchair": tags.get("wheelchair", ""),
                "direct_distance_km": round(direct_distance, 2)
            }})
        features.sort(key=lambda f: f["properties"]["direct_distance_km"])
        # Road-distance ranking is only needed for the closest candidates and
        # avoids sending a large number of requests to the public router.
        for feature in features[:5]:
            coords = feature["geometry"]["coordinates"]
            route_url = f"https://router.project-osrm.org/route/v1/driving/{lng},{lat};{coords[0]},{coords[1]}?overview=false"
            try:
                with urllib.request.urlopen(route_url, timeout=12) as response:
                    route = json.loads(response.read()).get("routes", [])[0]
                feature["properties"]["road_distance_km"] = round(route["distance"] / 1000, 2)
                feature["properties"]["travel_time_min"] = round(route["duration"] / 60)
            except Exception:
                feature["properties"]["road_distance_km"] = feature["properties"]["direct_distance_km"]
        features.sort(key=lambda f: f["properties"].get("road_distance_km", f["properties"]["direct_distance_km"]))
        result = {"type": "FeatureCollection", "features": features, "source": "OpenStreetMap + OSRM (ODbL)", "radius_km": radius_km}
        _live_emergency_cache[cache_key] = result
        return result
    except Exception:
        return {"type": "FeatureCollection", "features": [], "source": "Live emergency data temporarily unavailable", "radius_km": radius_km}

# Live OpenStreetMap points of interest for the hotel/restaurant buffer tool.
# Results are intentionally bounded and cached to be respectful of the public
# Overpass service.
_hospitality_cache = {}

@app.get("/api/hospitality/nearby")
def get_nearby_hospitality(lat: float, lng: float, radius_km: float = 10, type: str = "all"):
    import urllib.parse
    import urllib.request

    if type not in {"all", "hotel", "restaurant"}:
        raise HTTPException(status_code=400, detail="type must be all, hotel, or restaurant")
    radius_km = max(1, min(radius_km, 25))
    cache_key = (round(lat, 3), round(lng, 3), round(radius_km, 1), type)
    if cache_key in _hospitality_cache:
        return _hospitality_cache[cache_key]

    radius_m = int(radius_km * 1000)
    groups = []
    if type in {"all", "hotel"}:
        groups.append(f'nwr["tourism"~"hotel|guest_house|hostel"](around:{radius_m},{lat},{lng});')
    if type in {"all", "restaurant"}:
        groups.append(f'nwr["amenity"~"restaurant|cafe|fast_food"](around:{radius_m},{lat},{lng});')
    query = "[out:json][timeout:25];(" + "".join(groups) + ");out center 100;"

    try:
        import math
        body = urllib.parse.urlencode({"data": query}).encode()
        req = urllib.request.Request(
            "https://overpass-api.de/api/interpreter", body,
            headers={"User-Agent": "GantabyaSahayak/1.0 (educational WebGIS)"}
        )
        with urllib.request.urlopen(req, timeout=35) as response:
            raw = json.loads(response.read())
        features = []
        for element in raw.get("elements", []):
            tags = element.get("tags", {})
            point = element.get("center", element)
            if "lat" not in point or "lon" not in point:
                continue
            kind = "hotel" if tags.get("tourism") in {"hotel", "guest_house", "hostel"} else "restaurant"
            stars = tags.get("stars", "")
            if stars:
                price_level = "$" * min(4, max(1, int(float(stars))))
                price_note = f"Indicative {stars}-star property; confirm current prices directly."
            elif kind == "hotel":
                price_level = "$$"
                price_note = "Price not mapped; typical mid-range estimate only."
            else:
                price_level = "$$"
                price_note = "Price not mapped; check the menu or contact the venue."
            services = []
            for label, key in [("Wi-Fi", "internet_access"), ("Wheelchair access", "wheelchair"), ("Toilets", "toilets"), ("Takeaway", "takeaway"), ("Outdoor seating", "outdoor_seating")]:
                if tags.get(key) in {"yes", "designated", "limited"}:
                    services.append(label)
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [point["lon"], point["lat"]]},
                "properties": {
                    "name": tags.get("name") or f"Unnamed {kind}",
                    "type": kind,
                    "category": tags.get("tourism") or tags.get("amenity"),
                    "address": " ".join(filter(None, [tags.get("addr:street"), tags.get("addr:city")])),
                    "phone": tags.get("phone") or tags.get("contact:phone", ""),
                    "website": tags.get("website") or tags.get("contact:website", ""),
                    "opening_hours": tags.get("opening_hours", ""),
                    "cuisine": tags.get("cuisine", ""),
                    "stars": stars,
                    "rooms": tags.get("rooms", ""),
                    "price_level": price_level,
                    "price_note": price_note,
                    "services": services
                }
            })
        def distance_km(coords):
            lon, latitude = coords
            dlat = math.radians(latitude - lat)
            dlon = math.radians(lon - lng)
            a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat)) * math.cos(math.radians(latitude)) * math.sin(dlon / 2) ** 2
            return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        for feature in features:
            feature["properties"]["distance_km"] = round(distance_km(feature["geometry"]["coordinates"]), 2)
        features.sort(key=lambda feature: feature["properties"]["distance_km"])
        result = {"type": "FeatureCollection", "features": features, "source": "OpenStreetMap (ODbL)", "radius_km": radius_km}
        _hospitality_cache[cache_key] = result
        return result
    except Exception:
        return {"type": "FeatureCollection", "features": [], "source": "Live data temporarily unavailable", "radius_km": radius_km}

# ─── Module 6: Seasonal Tourism ───────────────────────────────────────────────
@app.get("/api/seasonal")
def get_seasonal_data():
    """Seasonal tourism data for all major destinations"""
    with open(DATA_DIR / "seasonal-data.json", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/seasonal/{destination}")
def get_seasonal_by_destination(destination: str):
    """Seasonal info for a specific destination"""
    with open(DATA_DIR / "seasonal-data.json", encoding="utf-8") as f:
        data = json.load(f)
    result = [d for d in data["destinations"] if destination.lower() in d["name"].lower()]
    if not result:
        raise HTTPException(status_code=404, detail="Destination not found")
    return result[0]

# ─── Module 7: Hazards ────────────────────────────────────────────────────────
@app.get("/api/hazards")
def get_hazards():
    """All hazard zones: landslide, flood, avalanche, rockfall, wildlife"""
    return load_geojson("hazard-zones.geojson")

@app.get("/api/hazards/{hazard_type}")
def get_hazards_by_type(hazard_type: str):
    """Filter hazards by type"""
    data = load_geojson("hazard-zones.geojson")
    filtered = [f for f in data["features"] if hazard_type.lower() in f["properties"].get("hazard_type", "").lower()]
    return {"type": "FeatureCollection", "features": filtered}

# ─── Module 8: Trip Planner ───────────────────────────────────────────────────
@app.post("/api/trip/plan")
def plan_trip(req: TripRequest):
    """
    GIS-based trip optimization.
    Generates recommended itinerary based on budget, days, interests.
    (In production: use network analysis with PostGIS + pgRouting)
    """
    with open(DATA_DIR / "seasonal-data.json", encoding="utf-8") as f:
        seasonal = json.load(f)

    # Filter destinations matching interests
    interest_map = {
        "trekking": ["Langtang", "Manaslu", "Annapurna", "Everest Region", "Kanchenjunga"],
        "culture": ["Kathmandu", "Bhaktapur", "Patan", "Lumbini", "Pokhara"],
        "wildlife": ["Chitwan", "Bardia", "Koshi Tappu"],
        "adventure": ["Pokhara", "Mustang", "Dolpa"],
        "nature": ["Rara Lake", "Phewa Lake", "Tilicho Lake", "Gosaikunda"]
    }

    recommended = []
    for interest in req.interests:
        dests = interest_map.get(interest.lower(), [])
        recommended.extend(dests)

    # Remove duplicates and limit by days
    recommended = list(dict.fromkeys(recommended))[:req.days]
    if not recommended:
        recommended = ["Kathmandu", "Pokhara", "Chitwan"][:req.days]

    # Generate itinerary
    itinerary = []
    vehicle_speeds = {"walk": 4, "bike": 30, "car": 60, "bus": 40}
    speed = vehicle_speeds.get(req.vehicle.lower(), 60)

    for i, dest in enumerate(recommended):
        itinerary.append({
            "day": i + 1,
            "destination": dest,
            "activities": _get_activities(dest, req.interests),
            "estimated_cost_npr": _estimate_cost(dest, req.budget, len(recommended)),
            "travel_time_hrs": round(random.uniform(2, 8), 1),
            "accommodation": _get_accommodation(req.budget)
        })

    return {
        "success": True,
        "trip": {
            "days": req.days,
            "budget_npr": req.budget,
            "vehicle": req.vehicle,
            "start": req.start_location,
            "itinerary": itinerary,
            "total_estimated_cost": sum(d["estimated_cost_npr"] for d in itinerary),
            "tips": [
                "Carry a paper map as backup in remote areas",
                "Acclimatize properly above 3000m",
                "Register with TIMS card for trekking routes",
                "Check road conditions before departure"
            ]
        }
    }

def _get_activities(dest: str, interests: list) -> list:
    activity_map = {
        "Kathmandu": ["Pashupatinath Temple", "Boudhanath Stupa", "Swayambhunath", "Thamel Market"],
        "Pokhara": ["Phewa Lake boat ride", "Paragliding", "Davis Falls", "World Peace Pagoda"],
        "Chitwan": ["Jungle safari", "Elephant back ride", "Canoe ride", "Bird watching"],
        "Langtang": ["Kyanjin Gompa", "Tserko Ri viewpoint", "Glacier trek"],
        "Manaslu": ["Manaslu Circuit Trek", "Larkya La Pass", "Tsum Valley"],
        "Bhaktapur": ["Durbar Square", "Pottery Square", "Dattatreya Temple"],
        "Lumbini": ["Maya Devi Temple", "Sacred Garden", "Peace Flame", "International Monasteries"],
        "Rara Lake": ["Lake walk", "Rara National Park", "Wildlife spotting"],
        "Annapurna": ["Base Camp trek", "Poon Hill sunrise", "Ghorepani trek"]
    }
    return activity_map.get(dest, [f"Explore {dest}", f"Local culture tour", f"Photography"])

def _estimate_cost(dest: str, total_budget: int, num_dests: int) -> int:
    per_dest = total_budget // max(num_dests, 1)
    return max(per_dest, 2000)

def _get_accommodation(budget: int) -> str:
    if budget > 50000: return "3-4 Star Hotel"
    elif budget > 20000: return "Guesthouse / Lodge"
    else: return "Tea House / Budget Hostel"

# ─── Module 9: Hidden Destinations ───────────────────────────────────────────
@app.get("/api/destinations")
def get_destinations():
    """Hidden and lesser-known destinations"""
    return load_geojson("hidden-destinations.geojson")

@app.get("/api/destinations/filter")
def filter_destinations(category: str = "all", province: str = "all", search: str = ""):
    """Filter hidden destinations by category, province, or search term"""
    data = load_geojson("hidden-destinations.geojson")
    features = data["features"]
    if category != "all":
        features = [f for f in features if f["properties"].get("category", "").lower() == category.lower()]
    if province != "all":
        features = [f for f in features if f["properties"].get("province", "").lower() == province.lower()]
    if search:
        features = [f for f in features if search.lower() in f["properties"].get("name", "").lower()]
    return {"type": "FeatureCollection", "features": features, "count": len(features)}

# ─── Module 10: Cultural Heritage ─────────────────────────────────────────────
@app.get("/api/heritage")
def get_heritage():
    """Cultural heritage sites with full information"""
    return load_geojson("heritage-sites.geojson")

@app.get("/api/heritage/search")
def search_heritage(q: str = "", type: str = "all", province: str = "all"):
    """Search heritage sites by name, type, or province"""
    data = load_geojson("heritage-sites.geojson")
    features = data["features"]
    if q:
        features = [f for f in features if q.lower() in f["properties"].get("name", "").lower()]
    if type != "all":
        features = [f for f in features if f["properties"].get("type", "").lower() == type.lower()]
    if province != "all":
        features = [f for f in features if f["properties"].get("province", "").lower() == province.lower()]
    return {"type": "FeatureCollection", "features": features, "count": len(features)}

# ─── Weather ──────────────────────────────────────────────────────────────────
@app.get("/api/weather")
def get_weather(lat: float = 27.7172, lng: float = 85.3240):
    """
    Fetch weather for a location.
    Uses Open-Meteo API (free, no API key needed).
    Returns current temperature and weather code.
    """
    import urllib.request
    url = (f"https://api.open-meteo.com/v1/forecast?"
           f"latitude={lat}&longitude={lng}"
           f"&current=temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m"
           f"&timezone=Asia%2FKathmandu")
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read())
    except Exception:
        # Fallback mock data if API unreachable
        return {
            "current": {
                "temperature_2m": 22.5,
                "weather_code": 2,
                "wind_speed_10m": 8.3,
                "relative_humidity_2m": 65
            },
            "note": "Live weather unavailable — showing sample data"
        }

# ─── Stats ────────────────────────────────────────────────────────────────────
@app.get("/api/stats")
def get_stats():
    """Platform statistics for homepage display"""
    return {
        "total_destinations": 127,
        "trekking_routes": 24,
        "heritage_sites": 89,
        "emergency_centers": 312,
        "provinces": 7,
        "districts": 77,
        "tourists_helped": "10,000+",
        "platform": "Gantabya Sahayak"
    }

# Keep this catch-all static frontend mount last. Starlette matches routes in
# registration order, so mounting "/" before "/api" routes would intercept API
# and docs requests.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
