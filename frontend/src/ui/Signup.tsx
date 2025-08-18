import React from 'react'
import { Login } from './Login'

export const Signup: React.FC = () => {
  return (
    <Login onBackToSignup={() => { window.location.hash = '#/' }} />
  )
}
