import React, { useMemo, useRef, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

type Props = {
  defaultLanguage?: string
}

type ChatMsg = {
  role: 'user' | 'assistant'
  text: string
}

export const Chatbot: React.FC<Props> = ({ defaultLanguage = 'en' }) => {
  const [language, setLanguage] = useState<string>(defaultLanguage)
  const [input, setInput] = useState<string>('')
  const [sending, setSending] = useState<boolean>(false)
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  const ctx = useMemo(() => {
    try {
      const saved = localStorage.getItem('farmerAuth')
      if (saved) {
        const parsed = JSON.parse(saved)
        return parsed?.farmer || null
      }
    } catch { }
    return null
  }, [])

  const send = async () => {
    const text = input.trim()
    if (!text) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text }])
    setSending(true)
    try {
      const payload: any = {
        message: text,
        language,
      }
      if (ctx?.farmerId) payload.farmer_id = ctx.farmerId
      if (ctx?.name) payload.name = ctx.name
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.detail || 'Chat failed')
      setMessages(prev => [...prev, { role: 'assistant', text: data.reply }])
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', text: `⚠️ ${e.message || 'Chat failed'}` }])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div className="min-h-screen">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">💬</div>
            <div>
              <div className="title">Farmer Chatbot</div>
              <div className="subtitle">Multilingual help for irrigation, pests, fertilizer, weather and markets</div>
            </div>
          </div>
          <div className="row">
            <button className="btn secondary" onClick={() => { window.location.hash = '#/' }}>← Back</button>
          </div>
        </div>
      </header>

      <div className="container">
        <div className="panel">
          <div className="row" style={{ marginBottom: 12 }}>
            <div className="field grow">
              <label>Language</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="en">English</option>
                <option value="hi">हिंदी (Hindi)</option>
                <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                <option value="bn">বাংলা (Bengali)</option>
              </select>
            </div>
          </div>

          <div style={{ maxHeight: 400, overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 12, padding: 12, background: '#fff' }}>
            {messages.length === 0 && (
              <div className="muted">Ask anything about your crop. Example: "How often should I irrigate wheat this week?"</div>
            )}
            {messages.map((m, i) => (
              <div key={i} className="row" style={{ alignItems: 'flex-start', marginBottom: 8 }}>
                <div style={{ fontSize: 20 }}>{m.role === 'user' ? '👨‍🌾' : '🤖'}</div>
                <div style={{ whiteSpace: 'pre-wrap' }}>{m.text}</div>
              </div>
            ))}
          </div>

          <div className="row" style={{ marginTop: 12 }}>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') send() }}
              placeholder="Type your question..."
              className="grow"
              style={{ padding: 12, border: '2px solid var(--border)', borderRadius: 12 }}
            />
            <button className="btn" onClick={send} disabled={sending || !input.trim()}>{sending ? 'Sending...' : 'Send'}</button>
          </div>
        </div>
      </div>
    </div>
  )
}


