import React, { useState } from 'react'

type LoginProps = {
  onLogin?: (farmerData: { name: string; farmerId: string; phone: string }) => void
  onBackToSignup?: () => void
}

export const Login: React.FC<LoginProps> = ({ onLogin, onBackToSignup }) => {
  const [step, setStep] = useState<'login' | 'otp'>('login')
  const [loginMethod, setLoginMethod] = useState<'farmerId' | 'phone'>('farmerId')
  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

  // Login with Farmer ID
  const [farmerId, setFarmerId] = useState('')
  const [password, setPassword] = useState('')

  // Login with Phone + OTP
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFarmerIdLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Simulate API call for farmer ID login
      await new Promise(resolve => setTimeout(resolve, 1000))

      // For demo purposes, accept any farmer ID with password "1234"
      if (password === '1234') {
        // Try to hydrate from backend store if it exists
        let resolvedName = 'Farmer'
        try {
          const res = await fetch(`${API_BASE}/api/user/by-id/${encodeURIComponent(farmerId)}`)
          if (res.ok) {
            const rec = await res.json()
            resolvedName = rec?.name || rec?.profile?.name || resolvedName
          }
        } catch { }

        const farmer = { name: resolvedName, farmerId, phone: '' }
        try { localStorage.setItem('farmerAuth', JSON.stringify({ isAuthenticated: true, farmer })) } catch { }
        if (onLogin) {
          onLogin(farmer)
        } else {
          window.location.hash = '#/'
        }
      } else {
        setError('Invalid farmer ID or password')
      }
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !phone.trim()) {
      setError('Please enter both name and phone number')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`${API_BASE}/api/auth/send-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, name })
      })
      if (!res.ok) {
        const msg = await res.text()
        throw new Error(msg || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setOtpSent(true)
      setStep('otp')
      const expires = data.expires_at ? new Date(data.expires_at).toLocaleTimeString() : 'soon'
      const devNote = data.dev_code ? `\n(Dev OTP: ${data.dev_code})` : ''
      alert(`OTP sent to ${phone}. Expires at ${expires}.${devNote}`)
    } catch (err: any) {
      setError(err.message || 'Failed to send OTP. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!otp.trim()) {
      setError('Please enter OTP')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`${API_BASE}/api/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, otp })
      })
      const data = await res.json()
      if (!res.ok || !data.success) {
        const msg = data?.detail || data?.message || `HTTP ${res.status}`
        throw new Error(msg)
      }
      const farmer = { name: data.name || name || 'Farmer', farmerId: data.farmer_id, phone }
      try {
        localStorage.setItem('farmerAuth', JSON.stringify({ isAuthenticated: true, farmer }))
      } catch { }
      if (onLogin) {
        onLogin(farmer)
      }
      // Navigate to app if running standalone
      if (!onLogin) {
        window.location.hash = '#/'
      }
    } catch (err: any) {
      setError(err.message || 'OTP verification failed')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setStep('login')
    // Do NOT change loginMethod here; respect the selected tab
    setFarmerId('')
    setPassword('')
    setName('')
    setPhone('')
    setOtp('')
    setOtpSent(false)
    setError(null)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 p-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">🌾</div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">KrishiMitra AI</h1>
          <p className="text-gray-600">Login to access your personalized farm recommendations</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Login Method Tabs */}
          <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => {
                setLoginMethod('farmerId')
                resetForm()
              }}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${loginMethod === 'farmerId'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
                }`}
            >
              Farmer ID Login
            </button>
            <button
              onClick={() => {
                setLoginMethod('phone')
                resetForm()
              }}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${loginMethod === 'phone'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
                }`}
            >
              Phone + OTP
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <span className="text-red-600 mr-2">⚠️</span>
                <span className="text-red-700 text-sm">{error}</span>
              </div>
            </div>
          )}

          {/* Farmer ID Login Form */}
          {loginMethod === 'farmerId' && (
            <form onSubmit={handleFarmerIdLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Farmer ID
                </label>
                <input
                  type="text"
                  value={farmerId}
                  onChange={(e) => setFarmerId(e.target.value)}
                  placeholder="Enter your farmer ID"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Demo password: 1234</p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Logging in...
                  </span>
                ) : (
                  'Login'
                )}
              </button>
            </form>
          )}

          {/* Phone + OTP Login Form */}
          {loginMethod === 'phone' && step === 'login' && (
            <form onSubmit={handleSendOtp} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your full name"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91-9876543210"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Sending OTP...
                  </span>
                ) : (
                  'Send OTP'
                )}
              </button>
            </form>
          )}

          {/* OTP Verification Form */}
          {loginMethod === 'phone' && step === 'otp' && (
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div className="text-center mb-4">
                <p className="text-sm text-gray-600">
                  OTP sent to <span className="font-medium">{phone}</span>
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter OTP
                </label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="Enter 4-digit OTP"
                  maxLength={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-lg tracking-widest"
                  required
                />
              </div>

              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setStep('login')}
                  className="flex-1 bg-gray-200 text-gray-700 py-3 px-4 rounded-lg font-medium hover:bg-gray-300 transition-colors"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Verifying...
                    </span>
                  ) : (
                    'Verify OTP'
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Back to Signup */}
          <div className="mt-6 text-center">
            <button
              onClick={() => {
                if (onBackToSignup) onBackToSignup()
                else window.location.hash = '#/signup'
              }}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              ← Back
            </button>
          </div>
        </div>

        {/* Demo Info */}
        <div className="mt-6 text-center">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-800 mb-2">Demo Credentials</h3>
            <div className="text-xs text-blue-700 space-y-1">
              <p><strong>Farmer ID Login:</strong> Any ID + Password: 1234</p>
              <p><strong>Phone + OTP:</strong> Any name/phone + OTP: 1234</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
