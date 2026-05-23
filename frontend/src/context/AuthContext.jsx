import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [seller, setSeller]   = useState(null)
  const [role, setRole]       = useState(null)  // 'user' | 'seller'
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const savedRole = localStorage.getItem('role')
    if (!token) { setLoading(false); return }
    if (savedRole === 'user') {
      authAPI.userMe().then(r => { setUser(r.data); setRole('user') })
        .catch(() => localStorage.clear())
        .finally(() => setLoading(false))
    } else if (savedRole === 'seller') {
      authAPI.sellerMe().then(r => { setSeller(r.data); setRole('seller') })
        .catch(() => localStorage.clear())
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const loginUser = (data) => {
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('role', 'user')
    setUser(data.user); setRole('user')
  }

  const loginSeller = (data) => {
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('role', 'seller')
    setSeller(data.seller); setRole('seller')
  }

  const logout = () => {
    localStorage.clear()
    setUser(null); setSeller(null); setRole(null)
  }

  return (
    <AuthContext.Provider value={{ user, seller, role, loading, loginUser, loginSeller, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
