import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'
import PincodeInput from '../components/PincodeInput'
import toast from 'react-hot-toast'
import { ShoppingCart, Eye, EyeOff } from 'lucide-react'

export function UserLogin() {
  const { loginUser } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [showPwd, setShowPwd] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const r = await authAPI.userLogin(form)
      loginUser(r.data)
      toast.success(`Welcome back, ${r.data.user.name.split(' ')[0]}!`)
      navigate('/')
    } catch (e) {
      toast.error(e.response?.data?.error || 'Login failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-8">
        <div className="text-center mb-6">
          <div className="flex justify-center mb-2">
            <div className="bg-primary text-white rounded-full p-3"><ShoppingCart size={28} /></div>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Login to OnlineBazar</h1>
          <p className="text-gray-500 text-sm mt-1">India's Growing Marketplace</p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-sm font-semibold text-gray-600 block mb-1">Email</label>
            <input type="email" required value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              className="input" placeholder="you@example.com" />
          </div>
          <div>
            <label className="text-sm font-semibold text-gray-600 block mb-1">Password</label>
            <div className="relative">
              <input type={showPwd ? 'text' : 'password'} required value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                className="input pr-10" placeholder="••••••" />
              <button type="button" onClick={() => setShowPwd(!showPwd)}
                className="absolute right-3 top-2.5 text-gray-400">
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full py-3 text-base">
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="mt-6 text-center space-y-2 text-sm">
          <p className="text-gray-500">Don't have an account? <Link to="/register" className="text-primary font-semibold">Register</Link></p>
          <p className="text-gray-400">Are you a seller? <Link to="/seller/login" className="text-green-600 font-semibold">Seller Login</Link></p>
        </div>
      </div>
    </div>
  )
}

export function UserRegister() {
  const { loginUser } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '', email: '', phone_number: '', gender: '',
    password: '', confirm_password: '',
    house_no: '', address_line: '', nearby_landmark: '',
    district: '', state: '', pincode: '',
  })
  const [loading, setLoading] = useState(false)
  const [showPwd, setShowPwd] = useState(false)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handlePincode = ({ district, state }) => {
    if (district) set('district', district)
    if (state) set('state', state)
  }

  const submit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm_password) { toast.error('Passwords do not match!'); return }
    setLoading(true)
    try {
      const { confirm_password, ...payload } = form
      const r = await authAPI.userRegister(payload)
      loginUser(r.data)
      toast.success('Account created! Welcome to OnlineBazar 🎉')
      navigate('/')
    } catch (e) {
      toast.error(e.response?.data?.error || JSON.stringify(e.response?.data?.errors) || 'Registration failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-xl mx-auto bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-6">
          <div className="flex justify-center mb-2">
            <div className="bg-primary text-white rounded-full p-3"><ShoppingCart size={28} /></div>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Create Buyer Account</h1>
          <p className="text-gray-500 text-sm">OnlineBazar — MCA Project</p>
          <div className="flex justify-center gap-3 mt-3">
            <Link to="/login" className="text-xs border border-primary text-primary px-3 py-1 rounded-full">Buyer Login</Link>
            <Link to="/seller/register" className="text-xs border border-green-600 text-green-600 px-3 py-1 rounded-full">Become a Seller</Link>
          </div>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2 sm:col-span-1">
              <label className="text-xs font-semibold text-gray-500 block mb-1">Full Name *</label>
              <input required value={form.name} onChange={e => set('name', e.target.value)} className="input" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Gender *</label>
              <select required value={form.gender} onChange={e => set('gender', e.target.value)} className="input">
                <option value="">Select</option>
                <option>Male</option><option>Female</option><option>Other</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Email *</label>
              <input type="email" required value={form.email} onChange={e => set('email', e.target.value)} className="input" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Phone *</label>
              <input maxLength={10} required value={form.phone_number} onChange={e => set('phone_number', e.target.value)} className="input" placeholder="10 digits" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Password *</label>
              <div className="relative">
                <input type={showPwd ? 'text' : 'password'} required minLength={6} value={form.password}
                  onChange={e => set('password', e.target.value)} className="input pr-9" />
                <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-2 top-2.5 text-gray-400">
                  {showPwd ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Confirm Password *</label>
              <input type="password" required value={form.confirm_password}
                onChange={e => set('confirm_password', e.target.value)}
                className={`input ${form.confirm_password && form.password !== form.confirm_password ? 'border-red-400' : ''}`} />
              {form.confirm_password && form.password !== form.confirm_password && (
                <p className="text-xs text-red-500 mt-0.5">Passwords don't match</p>
              )}
            </div>
          </div>

          <div className="border-t pt-4">
            <h3 className="text-sm font-bold text-primary mb-3">📍 Address Details</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-gray-500 block mb-1">House No. *</label>
                <input required value={form.house_no} onChange={e => set('house_no', e.target.value)} className="input" />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 block mb-1">Pincode *</label>
                <PincodeInput value={form.pincode} onChange={v => set('pincode', v)} onAreaFound={handlePincode} />
              </div>
              <div className="col-span-2">
                <label className="text-xs font-semibold text-gray-500 block mb-1">Address Line *</label>
                <input required value={form.address_line} onChange={e => set('address_line', e.target.value)} className="input" placeholder="Street, Colony, Area" />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 block mb-1">District *</label>
                <input required value={form.district} onChange={e => set('district', e.target.value)} className="input" placeholder="Auto-filled from pincode" />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 block mb-1">State *</label>
                <input required value={form.state} onChange={e => set('state', e.target.value)} className="input" placeholder="Auto-filled from pincode" />
              </div>
              <div className="col-span-2">
                <label className="text-xs font-semibold text-gray-500 block mb-1">Nearby Landmark</label>
                <input value={form.nearby_landmark} onChange={e => set('nearby_landmark', e.target.value)} className="input" placeholder="Optional" />
              </div>
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full py-3 text-base mt-2">
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <p className="text-center mt-4 text-sm text-gray-500">
          Already have an account? <Link to="/login" className="text-primary font-semibold">Login</Link>
        </p>
      </div>
    </div>
  )
}
