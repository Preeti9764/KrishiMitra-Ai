import React, { useMemo, useState } from 'react'

type AdvisoryResponse = {
  farmer_id: string
  crop: string
  horizon_days: number
  recommendations: Array<{
    agent: string
    priority: number
    summary: string
    tasks: string[]
    details: Record<string, any>
  }>
  unified_plan: string[]
}

export const App: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [resp, setResp] = useState<AdvisoryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [farmerId, setFarmerId] = useState('farmer_demo')
  const [lat, setLat] = useState(28.6)
  const [lon, setLon] = useState(77.2)
  const [size, setSize] = useState(2)
  const [crop, setCrop] = useState('wheat')
  const [stage, setStage] = useState('tillering')
  const [soilType, setSoilType] = useState('loam')
  const [moisture, setMoisture] = useState<number | ''>(18.5)
  const [soilTemp, setSoilTemp] = useState<number | ''>(24.1)
  const [horizon, setHorizon] = useState(7)

  const payload = useMemo(() => ({
    profile: {
      farmer_id: farmerId,
      location_lat: Number(lat),
      location_lon: Number(lon),
      farm_size_hectares: Number(size),
      crop,
      growth_stage: stage,
      soil_type: soilType
    },
    sensors: {
      soil_moisture_pct: moisture === '' ? undefined : Number(moisture),
      soil_temperature_c: soilTemp === '' ? undefined : Number(soilTemp)
    },
    horizon_days: Number(horizon)
  }), [farmerId, lat, lon, size, crop, stage, soilType, moisture, soilTemp, horizon])

  const callApi = async () => {
    setLoading(true)
    setError(null)
    setResp(null)
    try {
      const r = await fetch('http://localhost:8000/api/advisory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const data: AdvisoryResponse = await r.json()
      setResp(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="header">
        <div className="title">Farm Advisory Dashboard</div>
        <div className="row">
          <button className="btn" onClick={callApi} disabled={loading}>
            {loading ? 'Generating...' : 'Get Advisory'}
          </button>
          <button className="btn secondary" onClick={() => setResp(null)} disabled={loading}>
            Clear
          </button>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: 16 }}>
        <div className="grid">
          <div className="field">
            <label>Farmer ID</label>
            <input value={farmerId} onChange={(e) => setFarmerId(e.target.value)} />
          </div>
          <div className="row">
            <div className="field grow">
              <label>Latitude</label>
              <input type="number" value={lat} onChange={(e) => setLat(Number(e.target.value))} />
            </div>
            <div className="field grow">
              <label>Longitude</label>
              <input type="number" value={lon} onChange={(e) => setLon(Number(e.target.value))} />
            </div>
          </div>

          <div className="row">
            <div className="field grow">
              <label>Farm size (ha)</label>
              <input type="number" value={size} onChange={(e) => setSize(Number(e.target.value))} />
            </div>
            <div className="field grow">
              <label>Crop</label>
              <select value={crop} onChange={(e) => setCrop(e.target.value)}>
                <option value="wheat">Wheat</option>
                <option value="rice">Rice</option>
              </select>
            </div>
          </div>

          <div className="row">
            <div className="field grow">
              <label>Growth stage</label>
              <select value={stage} onChange={(e) => setStage(e.target.value)}>
                <option value="sowing">Sowing</option>
                <option value="tillering">Tillering</option>
                <option value="booting">Booting</option>
                <option value="flowering">Flowering</option>
              </select>
            </div>
            <div className="field grow">
              <label>Soil type</label>
              <select value={soilType} onChange={(e) => setSoilType(e.target.value)}>
                <option value="loam">Loam</option>
                <option value="clay">Clay</option>
                <option value="sandy">Sandy</option>
              </select>
            </div>
          </div>

          <div className="row">
            <div className="field grow">
              <label>Soil moisture (%)</label>
              <input type="number" value={moisture} onChange={(e) => setMoisture(e.target.value === '' ? '' : Number(e.target.value))} />
            </div>
            <div className="field grow">
              <label>Soil temp (°C)</label>
              <input type="number" value={soilTemp} onChange={(e) => setSoilTemp(e.target.value === '' ? '' : Number(e.target.value))} />
            </div>
          </div>

          <div className="field">
            <label>Horizon (days)</label>
            <input type="number" value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} />
          </div>
        </div>
      </div>

      {error && <div className="toast">Error: {error}</div>}

      {resp && (
        <div className="grid">
          <div className="panel">
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <div>
                <div className="muted">Unified Plan</div>
                <div className="title" style={{ fontSize: 18 }}>Next {resp.horizon_days} days</div>
              </div>
              <div className="badge">{resp.crop.toUpperCase()}</div>
            </div>
            <ol className="plan">
              {resp.unified_plan.map((t, i) => (
                <li key={i}>{t}</li>
              ))}
            </ol>

            <div className="divider" />

            <div className="kpis">
              <div className="kpi"><div className="v">{resp.recommendations.length}</div><div className="l">Agents</div></div>
              <div className="kpi"><div className="v">{resp.unified_plan.length}</div><div className="l">Tasks</div></div>
              <div className="kpi"><div className="v">{Math.max(...resp.recommendations.map(r => r.priority))}</div><div className="l">Max priority</div></div>
              <div className="kpi"><div className="v">{resp.farmer_id}</div><div className="l">Farmer</div></div>
            </div>
          </div>

          <div className="panel">
            <div className="muted">Agent Recommendations</div>
            <div className="cards">
              {resp.recommendations.map((rec, idx) => (
                <div className="card" key={idx}>
                  <div className="card-header">
                    <strong>{rec.agent.toUpperCase()}</strong>
                    <span className="badge">Priority {rec.priority}</span>
                  </div>
                  <div className="muted" style={{ marginBottom: 6 }}>{rec.summary}</div>
                  <ul>
                    {rec.tasks.map((t, i) => (
                      <li key={i}>{t}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


