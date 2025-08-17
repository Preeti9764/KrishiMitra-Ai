import React, { useState } from 'react'

type AdvisoryResponse = {
  farmer_id: string
  crop: string
  horizon_days: number
  generated_at: string
  recommendations: Array<{
    agent: string
    priority: number
    confidence_score: number
    summary: string
    explanation: string
    data_sources: string[]
    tasks: string[]
    risk_level?: string
    estimated_impact?: string
    cost_estimate?: any
    details: any
  }>
  unified_plan: string[]
  confidence_overall: number
  risk_assessment: {
    overall_risk_level: string
    agent_risks: Record<string, string>
    high_risk_agents: string[]
    medium_risk_agents: string[]
  }
  weather_summary?: any
  market_summary?: any
  soil_summary?: any
  response_time_ms?: number
}

export const App: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<AdvisoryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    farmerId: 'farmer_demo',
    name: 'Ramesh Kumar',
    lat: 28.6,
    lon: 77.2,
    district: 'Gurgaon',
    state: 'Haryana',
    farmSize: 2.0,
    crop: 'wheat',
    growthStage: 'tillering',
    soilType: 'loam',
    irrigationType: 'drip',
    farmingPractice: 'conventional',
    moisture: 18.5,
    soilTemp: 24.1,
    horizon: 7,
    language: 'en'
  })

  const callApi = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const payload = {
        profile: {
          farmer_id: formData.farmerId,
          name: formData.name,
          location_lat: formData.lat,
          location_lon: formData.lon,
          district: formData.district,
          state: formData.state,
          farm_size_hectares: formData.farmSize,
          crop: formData.crop,
          growth_stage: formData.growthStage,
          soil_type: formData.soilType,
          irrigation_type: formData.irrigationType,
          farming_practice: formData.farmingPractice
        },
        sensors: {
          soil_moisture_pct: formData.moisture,
          soil_temperature_c: formData.soilTemp
        },
        horizon_days: formData.horizon,
        language: formData.language
      }

      const res = await fetch('http://localhost:8000/api/advisory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }

      const data: AdvisoryResponse = await res.json()
      setResponse(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const updateFormData = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const getRiskColor = (risk: string) => {
    const colors = {
      low: 'success',
      medium: 'warning',
      high: 'danger',
      critical: 'danger'
    }
    return colors[risk as keyof typeof colors] || 'success'
  }

  const getPriorityColor = (priority: number) => {
    if (priority >= 9) return 'danger'
    if (priority >= 7) return 'warning'
    return 'success'
  }

  const getAgentIcon = (agent: string) => {
    const icons: Record<string, string> = {
      irrigation: '💧',
      fertilizer: '🌱',
      pest: '🐛',
      market: '📈',
      weather_risk: '🌤️',
      seed_crop: '🌾',
      finance_policy: '💰'
    }
    return icons[agent] || '🤖'
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">🌾</div>
            <div>
              <div className="title">Farm Advisory AI</div>
              <div className="subtitle">Multi-Agent AI System v2.0</div>
            </div>
          </div>

          <div className="row">
            <button
              className="btn"
              onClick={callApi}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="loading"></span>
                  Generating...
                </>
              ) : (
                'Generate Advisory'
              )}
            </button>
            <button
              className="btn secondary"
              onClick={() => setResponse(null)}
              disabled={loading}
            >
              Clear
            </button>
          </div>
        </div>
      </header>

      <div className="container">
        {/* Form */}
        <div className="grid">
          {/* Farmer Profile */}
          <div className="panel">
            <h3 className="title" style={{ fontSize: '18px', marginBottom: '16px' }}>🌱 Farmer Profile</h3>

            <div className="grid" style={{ gap: '16px' }}>
              <div className="row">
                <div className="field grow">
                  <label>Farmer ID</label>
                  <input
                    value={formData.farmerId}
                    onChange={(e) => updateFormData('farmerId', e.target.value)}
                  />
                </div>
                <div className="field grow">
                  <label>Name</label>
                  <input
                    value={formData.name}
                    onChange={(e) => updateFormData('name', e.target.value)}
                  />
                </div>
              </div>

              <div className="row">
                <div className="field grow">
                  <label>Latitude</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.lat}
                    onChange={(e) => updateFormData('lat', parseFloat(e.target.value))}
                  />
                </div>
                <div className="field grow">
                  <label>Longitude</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.lon}
                    onChange={(e) => updateFormData('lon', parseFloat(e.target.value))}
                  />
                </div>
              </div>

              <div className="row">
                <div className="field grow">
                  <label>District</label>
                  <input
                    value={formData.district}
                    onChange={(e) => updateFormData('district', e.target.value)}
                  />
                </div>
                <div className="field grow">
                  <label>State</label>
                  <input
                    value={formData.state}
                    onChange={(e) => updateFormData('state', e.target.value)}
                  />
                </div>
              </div>

              <div className="row">
                <div className="field grow">
                  <label>Farm Size (ha)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.farmSize}
                    onChange={(e) => updateFormData('farmSize', parseFloat(e.target.value))}
                  />
                </div>
                <div className="field grow">
                  <label>Crop</label>
                  <select
                    value={formData.crop}
                    onChange={(e) => updateFormData('crop', e.target.value)}
                  >
                    <option value="wheat">Wheat</option>
                    <option value="rice">Rice</option>
                    <option value="maize">Maize</option>
                    <option value="cotton">Cotton</option>
                    <option value="sugarcane">Sugarcane</option>
                    <option value="pulses">Pulses</option>
                    <option value="oilseeds">Oilseeds</option>
                    <option value="vegetables">Vegetables</option>
                  </select>
                </div>
              </div>

              <div className="row">
                <div className="field grow">
                  <label>Growth Stage</label>
                  <select
                    value={formData.growthStage}
                    onChange={(e) => updateFormData('growthStage', e.target.value)}
                  >
                    <option value="sowing">Sowing</option>
                    <option value="germination">Germination</option>
                    <option value="vegetative">Vegetative</option>
                    <option value="tillering">Tillering</option>
                    <option value="booting">Booting</option>
                    <option value="flowering">Flowering</option>
                    <option value="grain_filling">Grain Filling</option>
                    <option value="maturity">Maturity</option>
                    <option value="harvesting">Harvesting</option>
                  </select>
                </div>
                <div className="field grow">
                  <label>Soil Type</label>
                  <select
                    value={formData.soilType}
                    onChange={(e) => updateFormData('soilType', e.target.value)}
                  >
                    <option value="loam">Loam</option>
                    <option value="clay">Clay</option>
                    <option value="sandy">Sandy</option>
                    <option value="silt">Silt</option>
                    <option value="clay_loam">Clay Loam</option>
                    <option value="sandy_loam">Sandy Loam</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Sensor Data */}
          <div className="panel">
            <h3 className="title" style={{ fontSize: '18px', marginBottom: '16px' }}>📊 Sensor Data & Conditions</h3>

            <div className="grid" style={{ gap: '16px' }}>
              <div className="row">
                <div className="field grow">
                  <label>Soil Moisture (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.moisture}
                    onChange={(e) => updateFormData('moisture', parseFloat(e.target.value))}
                  />
                </div>
                <div className="field grow">
                  <label>Soil Temperature (°C)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.soilTemp}
                    onChange={(e) => updateFormData('soilTemp', parseFloat(e.target.value))}
                  />
                </div>
              </div>

              <div className="row">
                <div className="field grow">
                  <label>Irrigation Type</label>
                  <select
                    value={formData.irrigationType}
                    onChange={(e) => updateFormData('irrigationType', e.target.value)}
                  >
                    <option value="drip">Drip</option>
                    <option value="sprinkler">Sprinkler</option>
                    <option value="flood">Flood</option>
                    <option value="rainfed">Rainfed</option>
                  </select>
                </div>
                <div className="field grow">
                  <label>Farming Practice</label>
                  <select
                    value={formData.farmingPractice}
                    onChange={(e) => updateFormData('farmingPractice', e.target.value)}
                  >
                    <option value="conventional">Conventional</option>
                    <option value="organic">Organic</option>
                    <option value="mixed">Mixed</option>
                  </select>
                </div>
              </div>

              <div className="field">
                <label>Advisory Horizon (days)</label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={formData.horizon}
                  onChange={(e) => updateFormData('horizon', parseInt(e.target.value))}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="toast">
            <div className="row">
              <span style={{ color: 'var(--danger)' }}>⚠️</span>
              <span style={{ color: 'var(--danger)', fontWeight: '600' }}>Error: {error}</span>
            </div>
          </div>
        )}

        {/* Results */}
        {response && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="kpis">
              <div className="kpi">
                <div className="v">{(response.confidence_overall * 100).toFixed(1)}%</div>
                <div className="l">Confidence</div>
              </div>
              <div className="kpi">
                <div className="v" style={{ textTransform: 'capitalize' }}>{response.risk_assessment.overall_risk_level}</div>
                <div className="l">Risk Level</div>
              </div>
              <div className="kpi">
                <div className="v">{response.recommendations.length}</div>
                <div className="l">Agents Active</div>
              </div>
              <div className="kpi">
                <div className="v">{response.response_time_ms ? Math.round(response.response_time_ms) : 'N/A'}ms</div>
                <div className="l">Response Time</div>
              </div>
            </div>

            {/* Unified Plan */}
            <div className="panel">
              <div className="row" style={{ justifyContent: 'space-between', marginBottom: '16px' }}>
                <div>
                  <div className="muted">📋 Unified Advisory Plan</div>
                  <div className="title" style={{ fontSize: '18px' }}>Next {response.horizon_days} days</div>
                </div>
                <div className="badge">{response.crop.toUpperCase()}</div>
              </div>

              <ol className="plan">
                {response.unified_plan.map((task, i) => (
                  <li key={i}>{task}</li>
                ))}
              </ol>
            </div>

            {/* Agent Recommendations */}
            <div className="panel">
              <div className="muted" style={{ marginBottom: '16px' }}>🤖 Agent Recommendations</div>
              <div className="cards">
                {response.recommendations.map((rec, idx) => (
                  <div className="card" key={idx}>
                    <div className="card-header">
                      <div className="row">
                        <span style={{ fontSize: '20px', marginRight: '8px' }}>{getAgentIcon(rec.agent)}</span>
                        <strong style={{ textTransform: 'capitalize' }}>{rec.agent.replace('_', ' ')}</strong>
                      </div>
                      <div className="row">
                        <span className={`badge ${getPriorityColor(rec.priority)}`}>Priority {rec.priority}</span>
                        {rec.risk_level && (
                          <span className={`badge ${getRiskColor(rec.risk_level)}`}>{rec.risk_level}</span>
                        )}
                      </div>
                    </div>

                    <div className="muted" style={{ marginBottom: '8px' }}>{rec.summary}</div>

                    <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                      {rec.tasks.map((task, i) => (
                        <li key={i} style={{
                          padding: '4px 0',
                          fontSize: '14px',
                          display: 'flex',
                          alignItems: 'flex-start'
                        }}>
                          <span style={{
                            width: '6px',
                            height: '6px',
                            backgroundColor: 'var(--primary)',
                            borderRadius: '50%',
                            margin: '6px 8px 0 0',
                            flexShrink: 0
                          }}></span>
                          {task}
                        </li>
                      ))}
                    </ul>

                    <div className="divider"></div>

                    <div className="muted" style={{ fontSize: '12px' }}>
                      Confidence: {(rec.confidence_score * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


