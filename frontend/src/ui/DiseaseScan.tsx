import React, { useState } from 'react'

type Props = {
  defaultLanguage?: string
}

type DiagnoseResult = {
  crop: string
  disease: string
  confidence: number
  stats?: { [k: string]: any }
  suggestions?: string[]
}

export const DiseaseScan: React.FC<Props> = ({ defaultLanguage = 'en' }) => {
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [language, setLanguage] = useState<string>(defaultLanguage)
  const [crop, setCrop] = useState<string>('wheat')
  const [loading, setLoading] = useState<boolean>(false)
  const [result, setResult] = useState<DiagnoseResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    setImageFile(f || null)
    setResult(null)
    setError(null)
    if (f) {
      const url = URL.createObjectURL(f)
      setPreviewUrl(url)
    } else {
      setPreviewUrl(null)
    }
  }

  const submit = async () => {
    try {
      if (!imageFile) {
        setError('Please select an image')
        return
      }
      setLoading(true)
      setError(null)
      setResult(null)
      const fd = new FormData()
      fd.append('crop', crop)
      fd.append('language', language)
      fd.append('image', imageFile)
      const res = await fetch('http://localhost:8000/api/disease/diagnose', {
        method: 'POST',
        body: fd,
      })
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data = await res.json()
      setResult(data)
    } catch (e: any) {
      setError(e.message || 'Failed to analyze image')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">🩺</div>
            <div>
              <div className="title">Crop Disease Scan</div>
              <div className="subtitle">Upload a leaf photo to get a quick diagnosis</div>
            </div>
          </div>
          <div className="row">
            <button className="btn secondary" onClick={() => { window.location.hash = '#/' }}>← Back</button>
          </div>
        </div>
      </header>

      <div className="container">
        <div className="panel">
          <div className="grid" style={{ gap: '16px' }}>
            <div className="field">
              <label>Crop</label>
              <select value={crop} onChange={(e) => setCrop(e.target.value)}>
                <option value="wheat">Wheat</option>
                <option value="rice">Rice</option>
                <option value="maize">Maize</option>
                <option value="cotton">Cotton</option>
                <option value="vegetables">Vegetables</option>
              </select>
            </div>

            <div className="field">
              <label>Language</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="en">English</option>
                <option value="hi">हिंदी (Hindi)</option>
                <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                <option value="bn">বাংলা (Bengali)</option>
              </select>
            </div>

            <div className="field">
              <label>Leaf Image (JPG/PNG)</label>
              <input type="file" accept="image/*" onChange={onFileChange} />
              {previewUrl && (
                <img src={previewUrl} alt="preview" style={{ marginTop: 12, maxWidth: 280, borderRadius: 8, border: '1px solid var(--border)' }} />
              )}
            </div>

            <div className="row">
              <button className="btn" onClick={submit} disabled={loading || !imageFile}>
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
              <button className="btn secondary" onClick={() => { setImageFile(null); setPreviewUrl(null); setResult(null); setError(null) }}>Clear</button>
            </div>
          </div>
        </div>

        {error && (
          <div className="toast error">
            <div className="row"><span style={{ color: 'var(--danger)' }}>⚠️</span><span style={{ color: 'var(--danger)', fontWeight: 600 }}>Error: {error}</span></div>
          </div>
        )}

        {result && (
          <div className="panel">
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <div>
                <div className="muted">Detected</div>
                <div className="title" style={{ textTransform: 'capitalize' }}>{result.disease.replace('_', ' ')}</div>
              </div>
              <span className="badge">Confidence {(result.confidence * 100).toFixed(0)}%</span>
            </div>
            {result.stats && (
              <div className="grid" style={{ marginTop: 12 }}>
                {Object.entries(result.stats).filter(([k]) => k !== 'reasons').map(([k, v]) => (
                  <div key={k} className="kpi">
                    <div className="v">{String(v)}</div>
                    <div className="l" style={{ textTransform: 'capitalize' }}>{k.replace('_', ' ')}</div>
                  </div>
                ))}
              </div>
            )}
            {result.stats?.reasons && result.stats.reasons.length > 0 && (
              <div className="muted" style={{ marginTop: 12 }}>
                Reasons: {result.stats.reasons.join('; ')}
              </div>
            )}
            {result.suggestions && result.suggestions.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div className="muted" style={{ marginBottom: 8 }}>Suggested Actions</div>
                <ul>
                  {result.suggestions.map((s, i) => (
                    <li key={i} style={{ marginBottom: 6 }}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}


