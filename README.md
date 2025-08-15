## Multi-Agent AI Farm Advisory System (MVP)

This repo contains a working MVP:
- FastAPI backend with agents (irrigation, fertilizer, pest, market) and a coordination layer
- React + Vite dashboard to fetch and display the unified plan

### Backend (Windows PowerShell)
```powershell
cd "backend"
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend (new terminal)
```powershell
cd "frontend"
npm install
npm run dev -- --port 5173
```

Open `http://localhost:5173` and click "Get Advisory".

### API
- GET `/api/health`
- POST `/api/advisory`
```json
{
  "profile": {
    "farmer_id": "farmer_001",
    "location_lat": 28.6,
    "location_lon": 77.2,
    "farm_size_hectares": 2.0,
    "crop": "wheat",
    "growth_stage": "tillering",
    "soil_type": "loam"
  },
  "sensors": {"soil_moisture_pct": 18.5, "soil_temperature_c": 23.5},
  "horizon_days": 7
}
```

### Next steps
- Integrate NASA POWER, AGMARKNET, Soil Health Card, PlantVillage
- Replace rules with ML models
- Add DB (PostgreSQL), auth, i18n, voice prompts

