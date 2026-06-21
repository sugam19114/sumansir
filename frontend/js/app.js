/**
 * Gantabya Sahayak — Shared JavaScript Utilities
 * Auth, API client, map setup, common helpers
 */

const API_BASE = window.location.protocol.startsWith('http')
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : 'http://localhost:8000';

// ── Auth ──────────────────────────────────────────────────────
const Auth = {
  getUser() {
    const u = localStorage.getItem('gs_user');
    return u ? JSON.parse(u) : null;
  },
  getToken() { return localStorage.getItem('gs_token'); },
  isLoggedIn() { return !!this.getUser() && !!this.getToken(); },
  logout() {
    localStorage.removeItem('gs_user');
    localStorage.removeItem('gs_token');
    window.location.href = '../index.html';
  },
  requireLogin() {
    if (!this.isLoggedIn()) window.location.href = '../index.html';
  }
};

// ── API Client ────────────────────────────────────────────────
const API = {
  async get(path) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        headers: { 'Authorization': `Bearer ${Auth.getToken()}` }
      });
      return res.ok ? res.json() : null;
    } catch (e) {
      console.warn(`API offline — ${path}`);
      return null;
    }
  },
  async post(path, body) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${Auth.getToken()}`
        },
        body: JSON.stringify(body)
      });
      return res.ok ? res.json() : null;
    } catch (e) { return null; }
  }
};

// ── Map Setup ─────────────────────────────────────────────────
const basemapStyles = {
  osm: {
    version: 8,
    sources: {
      osm: {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors'
      }
    },
    layers: [{ id: 'osm-layer', type: 'raster', source: 'osm' }],
    glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf'
  },
  satellite: {
    version: 8,
    sources: {
      satellite: {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        attribution: '© Esri, Maxar, GeoEye, Earthstar Geographics'
      }
    },
    layers: [{ id: 'satellite-layer', type: 'raster', source: 'satellite' }],
    glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf'
  },
  terrain: {
    version: 8,
    sources: {
      terrain: {
        type: 'raster',
        tiles: ['https://tile.opentopomap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenTopoMap contributors'
      }
    },
    layers: [{ id: 'terrain-layer', type: 'raster', source: 'terrain' }],
    glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf'
  }
};

function createMap(containerId, center = [84.124, 28.394], zoom = 6) {
  const map = new maplibregl.Map({
    container: containerId,
    style: basemapStyles.osm,
    center,
    zoom,
    attributionControl: { compact: true }
  });
  map.addControl(new maplibregl.NavigationControl(), 'top-left');
  map.addControl(new maplibregl.ScaleControl({ maxWidth: 80, unit: 'metric' }), 'bottom-left');
  return map;
}

function switchBasemap(map, type) {
  const currentCenter = map.getCenter();
  const currentZoom = map.getZoom();
  // setStyle removes all custom sources/layers. Keep GeoJSON overlays (roads,
  // boundaries, analysis buffers, etc.) so a basemap change does not make a
  // module appear to stop working.
  const previousStyle = map.getStyle();
  const overlaySources = Object.entries(previousStyle.sources)
    .filter(([, source]) => source.type === 'geojson');
  const overlaySourceIds = new Set(overlaySources.map(([id]) => id));
  const overlayLayers = previousStyle.layers
    .filter(layer => overlaySourceIds.has(layer.source));

  map.setStyle(basemapStyles[type]);
  map.once('style.load', () => {
    map.setCenter(currentCenter);
    map.setZoom(currentZoom);
    overlaySources.forEach(([id, source]) => {
      if (!map.getSource(id)) map.addSource(id, source);
    });
    overlayLayers.forEach(layer => {
      if (!map.getLayer(layer.id)) map.addLayer(layer);
    });
  });
  document.querySelectorAll('.basemap-opt').forEach(b => {
    b.classList.toggle('active', b.dataset.type === type);
  });
}

// ── Navbar Injection ──────────────────────────────────────────
function injectNavbar(activePage) {
  const user = Auth.getUser();
  if (!user) return Auth.requireLogin();

  const pages = [
    { id: 'nearest', icon: '📍', label: 'Nearest', href: 'tools.html?tool=nearest' },
    { id: 'trek', icon: '🏔️', label: 'Trek Analyzer', href: 'tools.html?tool=trek' },
    { id: 'buffer', icon: '🏨', label: 'Hotel Buffer', href: 'tools.html?tool=buffer' },
    { id: 'emergency', icon: '🚑', label: 'Emergency', href: 'tools.html?tool=emergency' },
    { id: 'planner', icon: '🗺️', label: 'Trip Planner', href: 'tools.html?tool=planner' },
    { id: 'about', icon: '📄', label: 'About', href: 'about.html' },
  ];

  const navLinks = pages.map(p =>
    `<a class="nav-link ${p.id === activePage ? 'active' : ''}" href="${p.href}">${p.icon} ${p.label}</a>`
  ).join('');

  const navHTML = `
    <nav class="navbar">
      <a class="navbar-brand" href="../index.html">
        <div class="navbar-logo">🏔️</div>
        <div class="navbar-title">Gantabya Sahayak<small>गन्तब्य सहायक</small></div>
      </a>
      <div class="navbar-nav">${navLinks}</div>
      <div class="navbar-user">
        <div class="user-avatar">
          <img src="${user.photo || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(user.name) + '&background=468432&color=fff'}" alt="${user.name}" />
        </div>
        <span class="user-name">${user.name.split(' ')[0]}</span>
        <button class="logout-btn" onclick="Auth.logout()">Sign Out</button>
      </div>
    </nav>
  `;
  document.body.insertAdjacentHTML('afterbegin', navHTML);
}

// ── GeoJSON Fallback Loader ───────────────────────────────────
async function loadGeoJSON(apiPath, localPath) {
  // Static GeoJSON avoids repeatedly serialising large boundary files through
  // FastAPI, and works regardless of which frontend host (localhost/127.0.0.1)
  // the user opened.
  const fileName = localPath?.split('/').pop();
  if (fileName) {
    try {
      const res = await fetch(`${API_BASE}/data/${fileName}`);
      if (res.ok) return await res.json();
    } catch (_) { /* API fallback below */ }
  }
  const data = await API.get(apiPath);
  if (data) return data;
  try {
    const res = await fetch(localPath);
    return res.ok ? res.json() : null;
  } catch(e) {
    // Return a valid empty collection so map setup can still complete.
  }
  console.warn('Could not load', localPath);
  return { type: 'FeatureCollection', features: [] };
}

// ── Province/District/LocalLevel Overlay ─────────────────────
// Province colors keyed by STATE_CODE (0-7, FID=0 is a blank border artifact)
const PROVINCE_COLORS = {
  1: '#e74c3c', 2: '#e67e22', 3: '#f1c40f',
  4: '#2ecc71', 5: '#3498db', 6: '#9b59b6', 7: '#1abc9c'
};
const PROVINCE_NAMES = {
  1: 'Koshi Province', 2: 'Madhesh Province', 3: 'Bagmati Province',
  4: 'Gandaki Province', 5: 'Lumbini Province', 6: 'Karnali Province', 7: 'Sudurpashchim Province'
};

async function addAdminLayers(map) {
  // Province and district load fine (small files)
  const [provinces, districts] = await Promise.all([
    loadGeoJSON('/api/provinces', '../../data/province.geojson'),
    loadGeoJSON('/api/districts', '../../data/district.geojson')
  ]);

  // ── Province layer ── (property: STATE_CODE)
  if (provinces && !map.getSource('provinces')) {
    map.addSource('provinces', { type: 'geojson', data: provinces });
    map.addLayer({
      id: 'provinces-fill', type: 'fill', source: 'provinces', layout: {},
      paint: {
        'fill-color': [
          'match', ['get', 'STATE_CODE'],
          1, '#e74c3c', 2, '#e67e22', 3, '#f1c40f',
          4, '#2ecc71', 5, '#3498db', 6, '#9b59b6', 7, '#1abc9c',
          '#888888'
        ],
        'fill-opacity': 0.1
      }
    });
    map.addLayer({
      id: 'provinces-line', type: 'line', source: 'provinces', layout: {},
      paint: { 'line-color': '#468432', 'line-width': 2.5, 'line-opacity': 0.85 }
    });
  }

  // ── District layer ── (property: DISTRICT_1)
  if (districts && !map.getSource('districts')) {
    map.addSource('districts', { type: 'geojson', data: districts });
    map.addLayer({
      id: 'districts-line', type: 'line', source: 'districts',
      layout: { visibility: 'none' },
      paint: { 'line-color': '#a8d890', 'line-width': 1, 'line-opacity': 0.65, 'line-dasharray': [3, 2] }
    });
  }

  // ── Local level layer ── (property: GaPa_NaPa)
  // NOTE: local.geojson is 42MB — loaded on-demand only when user toggles it
  // Source is registered here as empty; data is fetched when first toggled ON
  if (!map.getSource('local-levels')) {
    map.addSource('local-levels', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({
      id: 'local-levels-line', type: 'line', source: 'local-levels',
      layout: { visibility: 'none' },
      paint: { 'line-color': '#68c048', 'line-width': 0.6, 'line-opacity': 0.55 }
    });
  }
}

// Called when user toggles Local Level checkbox — lazy loads the 42MB file
let _localLoaded = false;
async function loadLocalLevelOnDemand(map, visible) {
  if (visible && !_localLoaded) {
    _localLoaded = true;
    const data = await loadGeoJSON('/api/local-levels', '../../data/local.geojson');
    if (data && map.getSource('local-levels')) {
      map.getSource('local-levels').setData(data);
    }
  }
  toggleLayer(map, 'local-levels-line', visible);
}

function toggleLayer(map, layerId, visible) {
  if (map.getLayer(layerId)) {
    map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
  }
}

// ── Province Popup on Click ───────────────────────────────────
function addProvincePopup(map) {
  map.on('click', 'provinces-fill', (e) => {
    const p = e.features[0].properties;
    // Skip the blank FID=0 artifact feature
    if (!p.STATE_CODE) return;
    const name = PROVINCE_NAMES[p.STATE_CODE] || `Province ${p.STATE_CODE}`;
    const color = PROVINCE_COLORS[p.STATE_CODE] || '#888';
    new maplibregl.Popup()
      .setLngLat(e.lngLat)
      .setHTML(`
        <div class="popup-content">
          <div class="popup-title" style="color:${color}">${name}</div>
          <div class="popup-type">Nepal Province — State ${p.STATE_CODE}</div>
          <div class="popup-row"><span>Province No.</span><strong>${p.STATE_CODE}</strong></div>
          <div class="popup-row"><span>Feature ID</span><strong>${p.FID}</strong></div>
        </div>`)
      .addTo(map);
  });
  map.on('mouseenter', 'provinces-fill', () => { map.getCanvas().style.cursor = 'pointer'; });
  map.on('mouseleave', 'provinces-fill', () => { map.getCanvas().style.cursor = ''; });
}

// ── Weather Widget ────────────────────────────────────────────
const WEATHER_CODES = {
  0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
  45: '🌫️', 48: '🌫️',
  51: '🌦️', 61: '🌧️', 80: '🌦️',
  71: '🌨️', 85: '🌨️',
  95: '⛈️', 99: '⛈️'
};

async function loadWeatherWidget(containerId, lat = 27.7172, lng = 85.324) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const data = await API.get(`/api/weather?lat=${lat}&lng=${lng}`);
  if (data?.current) {
    const c = data.current;
    const icon = WEATHER_CODES[c.weather_code] || '🌡️';
    el.innerHTML = `
      <div class="weather-widget">
        <div class="weather-icon">${icon}</div>
        <div>
          <div class="weather-temp">${Math.round(c.temperature_2m)}°C</div>
          <div class="weather-desc">Wind: ${c.wind_speed_10m} km/h · Humidity: ${c.relative_humidity_2m}%</div>
        </div>
      </div>`;
  }
}

// ── Turf Spatial Tools ────────────────────────────────────────
const SpatialTools = {
  // Find nearest feature to a point
  findNearest(point, featureCollection) {
    if (!featureCollection?.features?.length) return null;
    const points = featureCollection.features.filter(f => f.geometry.type === 'Point');
    if (!points.length) return null;
    const fc = { type: 'FeatureCollection', features: points };
    return turf.nearestPoint(point, fc);
  },

  // Buffer analysis around a point (in km)
  createBuffer(point, radiusKm) {
    return turf.buffer(point, radiusKm, { units: 'kilometers' });
  },

  // Distance between two coordinates
  calcDistance(from, to) {
    const f = turf.point(from);
    const t = turf.point(to);
    return turf.distance(f, t, { units: 'kilometers' });
  },

  // Check if point is in polygon
  pointInPolygon(point, polygon) {
    return turf.booleanPointInPolygon(point, polygon);
  },

  // Calculate route length from LineString
  lineLength(lineFeature) {
    return turf.length(lineFeature, { units: 'kilometers' });
  }
};

// ── Utility: Format Distance ──────────────────────────────────
function fmtDist(km) {
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`;
}

function fmtTime(hrs) {
  const h = Math.floor(hrs);
  const m = Math.round((hrs - h) * 60);
  return h > 0 ? `${h}h ${m}m` : `${m} min`;
}

// ── Status Colour Map ─────────────────────────────────────────
const STATUS_COLORS = {
  good: '#2ecc71',
  caution: '#f39c12',
  damaged: '#e67e22',
  closed: '#e74c3c',
  construction: '#3498db',
  high: '#e74c3c',
  medium: '#f39c12',
  low: '#2ecc71',
  extreme: '#8e44ad'
};
