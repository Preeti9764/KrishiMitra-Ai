import React, { useEffect, useState } from 'react'
import { Login } from './Login'

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

type FarmerData = {
  name: string
  farmerId: string
  phone: string
}

export const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [farmerData, setFarmerData] = useState<FarmerData | null>(null)
  const [showLogin, setShowLogin] = useState(false)
  const [route, setRoute] = useState<string>(() => window.location.hash || '#/')

  useEffect(() => {
    const onHashChange = () => setRoute(window.location.hash || '#/')
    window.addEventListener('hashchange', onHashChange)
    // Restore auth from storage
    try {
      const saved = localStorage.getItem('farmerAuth')
      if (saved) {
        const parsed = JSON.parse(saved)
        if (parsed?.isAuthenticated && parsed?.farmer) {
          setIsAuthenticated(true)
          setFarmerData(parsed.farmer)
          setFormData(prev => ({ ...prev, farmerId: parsed.farmer.farmerId, name: parsed.farmer.name }))
        }
      }
    } catch { }
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<AdvisoryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Language translations for UI elements
  const translations = {
    en: {
      title: "Farm Advisory AI",
      subtitle: "Multi-Agent AI System v2.0",
      farmerProfile: "Farmer Profile",
      sensorData: "Sensor Data & Conditions",
      generateAdvisory: "Generate Advisory",
      clear: "Clear",
      logout: "Logout",
      login: "Login",
      farmerId: "Farmer ID",
      name: "Name",
      latitude: "Latitude",
      longitude: "Longitude",
      district: "District",
      state: "State",
      farmSize: "Farm Size (ha)",
      crop: "Crop",
      growthStage: "Growth Stage",
      soilType: "Soil Type",
      soilMoisture: "Soil Moisture (%)",
      soilTemperature: "Soil Temperature (°C)",
      irrigationType: "Irrigation Type",
      farmingPractice: "Farming Practice",
      advisoryHorizon: "Advisory Horizon (days)",
      languagePreference: "Language Preference",
      confidence: "Confidence",
      riskLevel: "Risk Level",
      agentsActive: "Agents Active",
      responseTime: "Response Time"
    },
    hi: {
      title: "फार्म सलाहकार AI",
      subtitle: "मल्टी-एजेंट AI सिस्टम v2.0",
      farmerProfile: "किसान प्रोफाइल",
      sensorData: "सेंसर डेटा और स्थितियां",
      generateAdvisory: "सलाह उत्पन्न करें",
      clear: "साफ़ करें",
      logout: "लॉगआउट",
      login: "लॉगिन",
      farmerId: "किसान ID",
      name: "नाम",
      latitude: "अक्षांश",
      longitude: "देशांतर",
      district: "जिला",
      state: "राज्य",
      farmSize: "खेत का आकार (हेक्टेयर)",
      crop: "फसल",
      growthStage: "विकास चरण",
      soilType: "मिट्टी का प्रकार",
      soilMoisture: "मिट्टी की नमी (%)",
      soilTemperature: "मिट्टी का तापमान (°C)",
      irrigationType: "सिंचाई का प्रकार",
      farmingPractice: "खेती का तरीका",
      advisoryHorizon: "सलाह क्षितिज (दिन)",
      languagePreference: "भाषा वरीयता",
      confidence: "विश्वास",
      riskLevel: "जोखिम स्तर",
      agentsActive: "सक्रिय एजेंट",
      responseTime: "प्रतिक्रिया समय"
    },
    pa: {
      title: "ਫਾਰਮ ਸਲਾਹਕਾਰ AI",
      subtitle: "ਮਲਟੀ-ਏਜੰਟ AI ਸਿਸਟਮ v2.0",
      farmerProfile: "ਕਿਸਾਨ ਪ੍ਰੋਫਾਈਲ",
      sensorData: "ਸੈਂਸਰ ਡੇਟਾ ਅਤੇ ਸਥਿਤੀਆਂ",
      generateAdvisory: "ਸਲਾਹ ਤਿਆਰ ਕਰੋ",
      clear: "ਸਾਫ਼ ਕਰੋ",
      logout: "ਲੌਗਆਊਟ",
      login: "ਲੌਗਿਨ",
      farmerId: "ਕਿਸਾਨ ID",
      name: "ਨਾਮ",
      latitude: "ਅਕਸ਼ਾਂਸ਼",
      longitude: "ਦੇਸ਼ਾਂਤਰ",
      district: "ਜ਼ਿਲ੍ਹਾ",
      state: "ਰਾਜ",
      farmSize: "ਖੇਤ ਦਾ ਆਕਾਰ (ਹੈਕਟੇਅਰ)",
      crop: "ਫਸਲ",
      growthStage: "ਵਿਕਾਸ ਪੜਾਅ",
      soilType: "ਮਿੱਟੀ ਦਾ ਕਿਸਮ",
      soilMoisture: "ਮਿੱਟੀ ਦੀ ਨਮੀ (%)",
      soilTemperature: "ਮਿੱਟੀ ਦਾ ਤਾਪਮਾਨ (°C)",
      irrigationType: "ਸਿੰਚਾਈ ਦਾ ਕਿਸਮ",
      farmingPractice: "ਖੇਤੀਬਾੜੀ ਦਾ ਤਰੀਕਾ",
      advisoryHorizon: "ਸਲਾਹ ਦਾ ਖੇਤਰ (ਦਿਨ)",
      languagePreference: "ਭਾਸ਼ਾ ਤਰਜੀਹ",
      confidence: "ਭਰੋਸਾ",
      riskLevel: "ਜੋਖਮ ਦਾ ਪੱਧਰ",
      agentsActive: "ਸਰਗਰਮ ਏਜੰਟ",
      responseTime: "ਜਵਾਬ ਦਾ ਸਮਾਂ"
    },
    bn: {
      title: "ফার্ম উপদেষ্টা AI",
      subtitle: "মাল্টি-এজেন্ট AI সিস্টেম v2.0",
      farmerProfile: "কৃষক প্রোফাইল",
      sensorData: "সেন্সর ডেটা এবং অবস্থা",
      generateAdvisory: "পরামর্শ তৈরি করুন",
      clear: "মুছুন",
      logout: "লগআউট",
      login: "লগইন",
      farmerId: "কৃষক ID",
      name: "নাম",
      latitude: "অক্ষাংশ",
      longitude: "দ্রাঘিমাংশ",
      district: "জেলা",
      state: "রাজ্য",
      farmSize: "খামারের আকার (হেক্টর)",
      crop: "ফসল",
      growthStage: "বৃদ্ধির পর্যায়",
      soilType: "মাটির ধরন",
      soilMoisture: "মাটির আর্দ্রতা (%)",
      soilTemperature: "মাটির তাপমাত্রা (°C)",
      irrigationType: "সেচের ধরন",
      farmingPractice: "চাষের পদ্ধতি",
      advisoryHorizon: "পরামর্শের সময়সীমা (দিন)",
      languagePreference: "ভাষার পছন্দ",
      confidence: "আত্মবিশ্বাস",
      riskLevel: "ঝুঁকির মাত্রা",
      agentsActive: "সক্রিয় এজেন্ট",
      responseTime: "প্রতিক্রিয়ার সময়"
    }
  }

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

  // Get current language translations
  const currentLang = translations[formData.language as keyof typeof translations] || translations.en

  const handleLogin = (data: FarmerData) => {
    setFarmerData(data)
    setIsAuthenticated(true)
    setShowLogin(false)

    // Update form data with logged-in farmer info
    setFormData(prev => ({
      ...prev,
      farmerId: data.farmerId,
      name: data.name
    }))

    // Clear any previous responses
    setResponse(null)
    setError(null)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    setFarmerData(null)
    setResponse(null)
    setError(null)
    try { localStorage.removeItem('farmerAuth') } catch { }

    // Reset form to demo values
    setFormData(prev => ({
      ...prev,
      farmerId: 'farmer_demo',
      name: 'Ramesh Kumar'
    }))
  }

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

    // If language is changed, clear the response to show new language
    if (field === 'language') {
      setResponse(null)
      setError(null)

      // Show language change notification
      const languageNames = {
        'en': 'English',
        'hi': 'हिंदी (Hindi)',
        'pa': 'ਪੰਜਾਬੀ (Punjabi)',
        'bn': 'বাংলা (Bengali)',
        'te': 'తెలుగు (Telugu)',
        'ta': 'தமிழ் (Tamil)',
        'mr': 'मराठी (Marathi)',
        'gu': 'ગુજરાતી (Gujarati)'
      }

      const newLangName = languageNames[value as keyof typeof languageNames] || 'Unknown'
      alert(`Language changed to: ${newLangName}`)
    }
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

  // Simple hash-based routing (/#/signup shows dedicated signup page)
  if (route.startsWith('#/signup')) {
    return <Login />
  }
  if (showLogin) {
    return <Login onLogin={handleLogin} onBackToSignup={() => setShowLogin(false)} />
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">🌾</div>
            <div>
              <div className="title">{currentLang.title}</div>
              <div className="subtitle">{currentLang.subtitle}</div>
            </div>
          </div>

          <div className="row">
            {isAuthenticated ? (
              <>
                <div className="user-info" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginRight: '16px',
                  padding: '8px 16px',
                  background: 'rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: 'white'
                }}>
                  <span>👤 {farmerData?.name}</span>
                  <span style={{ fontSize: '12px', opacity: 0.8 }}>{farmerData?.farmerId}</span>
                </div>
                <button
                  className="btn secondary"
                  onClick={handleLogout}
                >
                  {currentLang.logout}
                </button>
              </>
            ) : (
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn"
                  onClick={() => setShowLogin(true)}
                >
                  {currentLang.login}
                </button>
                <button
                  className="btn secondary"
                  onClick={() => { window.location.hash = '#/signup' }}
                >
                  Sign Up
                </button>
              </div>
            )}

            <button
              className="btn"
              onClick={callApi}
              disabled={loading || !isAuthenticated}
            >
              {loading ? (
                <>
                  <span className="loading"></span>
                  Generating...
                </>
              ) : (
                currentLang.generateAdvisory
              )}
            </button>
            <button
              className="btn secondary"
              onClick={() => setResponse(null)}
              disabled={loading}
            >
              {currentLang.clear}
            </button>
          </div>
        </div>
      </header>

      <div className="container">
        {/* Authentication Notice */}
        {!isAuthenticated && (
          <div className="panel" style={{
            background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
            border: '1px solid #f59e0b',
            marginBottom: '24px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '24px' }}>🔐</span>
              <div>
                <h3 style={{ margin: '0 0 8px 0', color: '#92400e' }}>Authentication Required</h3>
                <p style={{ margin: 0, color: '#92400e', fontSize: '14px' }}>
                  Please login to access personalized farm advisory services. You can use either your Farmer ID and password, or sign up with your name and phone number.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Form */}
        <div className="grid">
          {/* Farmer Profile */}
          <div className="panel">
            <h3 className="title" style={{ fontSize: '18px', marginBottom: '16px' }}>{currentLang.farmerProfile}</h3>

            <div className="grid" style={{ gap: '16px' }}>
              <div className="row">
                <div className="field grow">
                  <label>{currentLang.farmerId}</label>
                  <input
                    value={formData.farmerId}
                    onChange={(e) => updateFormData('farmerId', e.target.value)}
                    disabled={isAuthenticated}
                    style={{
                      backgroundColor: isAuthenticated ? '#f3f4f6' : 'white',
                      cursor: isAuthenticated ? 'not-allowed' : 'text'
                    }}
                  />
                  {isAuthenticated && (
                    <small style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                      🔒 Locked after login
                    </small>
                  )}
                </div>
                <div className="field grow">
                  <label>{currentLang.name}</label>
                  <input
                    value={formData.name}
                    onChange={(e) => updateFormData('name', e.target.value)}
                    disabled={isAuthenticated}
                    style={{
                      backgroundColor: isAuthenticated ? '#f3f4f6' : 'white',
                      cursor: isAuthenticated ? 'not-allowed' : 'text'
                    }}
                  />
                  {isAuthenticated && (
                    <small style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                      🔒 Locked after login
                    </small>
                  )}
                </div>
              </div>



              <div className="row">
                <div className="field grow">
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {currentLang.latitude}
                    <button
                      type="button"
                      onClick={() => {
                        const infoBox = document.querySelector('.coordinate-info-box') as HTMLElement;
                        if (infoBox) {
                          infoBox.style.display = infoBox.style.display === 'none' ? 'block' : 'none';
                        }
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--primary)',
                        fontSize: '16px',
                        cursor: 'pointer',
                        padding: '0',
                        width: '20px',
                        height: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                      title="How to get coordinates?"
                    >
                      ?
                    </button>
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.lat}
                      onChange={(e) => updateFormData('lat', parseFloat(e.target.value))}
                      placeholder="e.g., 28.6"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        if (navigator.geolocation) {
                          navigator.geolocation.getCurrentPosition(
                            (position) => {
                              updateFormData('lat', position.coords.latitude);
                              updateFormData('lon', position.coords.longitude);
                              alert('Location detected! Please verify the coordinates match your farm location.');
                            },
                            (error) => {
                              alert('Could not get location. Please use manual methods from the toolkit above.');
                            }
                          );
                        } else {
                          alert('Geolocation not supported. Please use manual methods from the toolkit above.');
                        }
                      }}
                      style={{
                        position: 'absolute',
                        right: '8px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        background: 'var(--primary)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '4px 8px',
                        fontSize: '11px',
                        cursor: 'pointer'
                      }}
                      title="Get current location"
                    >
                      📍
                    </button>
                  </div>
                  <small style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                    Example: 28.6 (North of equator)
                  </small>
                </div>
                <div className="field grow">
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {currentLang.longitude}
                    <button
                      type="button"
                      onClick={() => {
                        const infoBox = document.querySelector('.coordinate-info-box') as HTMLElement;
                        if (infoBox) {
                          infoBox.style.display = infoBox.style.display === 'none' ? 'block' : 'none';
                        }
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--primary)',
                        fontSize: '16px',
                        cursor: 'pointer',
                        padding: '0',
                        width: '20px',
                        height: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                      title="How to get coordinates?"
                    >
                      ?
                    </button>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.lon}
                    onChange={(e) => updateFormData('lon', parseFloat(e.target.value))}
                    placeholder="e.g., 77.2"
                  />
                  <small style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                    Example: 77.2 (East of prime meridian)
                  </small>
                </div>
              </div>

              {/* Compact Coordinate Info Box */}
              <div className="coordinate-info-box" style={{
                display: 'none',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: '8px',
                padding: '12px',
                marginTop: '8px',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.2)',
                fontSize: '13px',
                lineHeight: '1.4'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <strong style={{ fontSize: '14px' }}>📍 Quick Coordinate Guide</strong>
                  <button
                    type="button"
                    onClick={() => {
                      const infoBox = document.querySelector('.coordinate-info-box') as HTMLElement;
                      if (infoBox) {
                        infoBox.style.display = 'none';
                      }
                    }}
                    style={{
                      background: 'rgba(255,255,255,0.2)',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      padding: '2px 6px',
                      fontSize: '10px',
                      cursor: 'pointer'
                    }}
                  >
                    ✕
                  </button>
                </div>

                <div style={{ marginBottom: '8px' }}>
                  <strong>🌐 Google Maps:</strong> Long press on farm location → Copy coordinates
                </div>

                <div style={{ marginBottom: '8px' }}>
                  <strong>📱 GPS App:</strong> Download "GPS Coordinates" → Go to farm → Get coordinates
                </div>

                <div style={{ marginBottom: '8px' }}>
                  <strong>👨‍🌾 Extension Worker:</strong> Ask agricultural officer during farm visits
                </div>

                <div style={{
                  background: 'rgba(255,255,255,0.1)',
                  padding: '6px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  border: '1px solid rgba(255,255,255,0.2)'
                }}>
                  <strong>💡 Tip:</strong> Use village center coordinates if exact farm coordinates aren't available!
                </div>
              </div>

              <div className="row">
                <div className="field grow">
                  <label>{currentLang.district}</label>
                  <input
                    value={formData.district}
                    onChange={(e) => updateFormData('district', e.target.value)}
                  />
                </div>
                <div className="field grow">
                  <label>{currentLang.state}</label>
                  <input
                    value={formData.state}
                    onChange={(e) => updateFormData('state', e.target.value)}
                  />
                </div>
              </div>

              <div className="row">
                <div className="field grow">
                  <label>{currentLang.farmSize}</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.farmSize}
                    onChange={(e) => updateFormData('farmSize', parseFloat(e.target.value))}
                  />
                </div>
                <div className="field grow">
                  <label>{currentLang.crop}</label>
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
                  <label>{currentLang.growthStage}</label>
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
                  <label>{currentLang.soilType}</label>
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
            <h3 className="title" style={{ fontSize: '18px', marginBottom: '16px' }}>{currentLang.sensorData}</h3>

            <div className="grid" style={{ gap: '16px' }}>
              <div className="row">
                <div className="field grow">
                  <label>{currentLang.soilMoisture}</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.moisture}
                    onChange={(e) => updateFormData('moisture', parseFloat(e.target.value))}
                  />
                </div>
                <div className="field grow">
                  <label>{currentLang.soilTemperature}</label>
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
                  <label>{currentLang.irrigationType}</label>
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
                  <label>{currentLang.farmingPractice}</label>
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

              <div className="row">
                <div className="field grow">
                  <label>{currentLang.advisoryHorizon}</label>
                  <input
                    type="number"
                    min="1"
                    max="30"
                    value={formData.horizon}
                    onChange={(e) => updateFormData('horizon', parseInt(e.target.value))}
                  />
                </div>
                <div className="field grow">
                  <label>{currentLang.languagePreference}</label>
                  <select
                    value={formData.language}
                    onChange={(e) => updateFormData('language', e.target.value)}
                  >
                    <option value="en">English</option>
                    <option value="hi">हिंदी (Hindi)</option>
                    <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                    <option value="bn">বাংলা (Bengali)</option>
                    <option value="te">తెలుగు (Telugu)</option>
                    <option value="ta">தமிழ் (Tamil)</option>
                    <option value="mr">मराठी (Marathi)</option>
                    <option value="gu">ગુજરાતી (Gujarati)</option>
                  </select>
                </div>
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
                <div className="l">{currentLang.confidence}</div>
              </div>
              <div className="kpi">
                <div className="v" style={{ textTransform: 'capitalize' }}>{response.risk_assessment.overall_risk_level}</div>
                <div className="l">{currentLang.riskLevel}</div>
              </div>
              <div className="kpi">
                <div className="v">{response.recommendations.length}</div>
                <div className="l">{currentLang.agentsActive}</div>
              </div>
              <div className="kpi">
                <div className="v">{response.response_time_ms ? Math.round(response.response_time_ms) : 'N/A'}ms</div>
                <div className="l">{currentLang.responseTime}</div>
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


