Multi-Agent AI Farm Advisory System - Backend (FastAPI)

Run locally

1. Create venv and install deps

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start API

```bash
uvicorn app.main:app --port 8001
```

3. Test health

```bash
curl http://localhost:8001/api/health
```

Example request

```bash
curl -X POST http://localhost:8001/api/advisory \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```
