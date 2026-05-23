import { useState, useEffect } from 'react'
import { membershipAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Spinner } from '../components/UI'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Star, Check } from 'lucide-react'

export default function Membership() {
  const { role } = useAuth()
  const [membership, setMembership] = useState(null)
  const [loading, setLoading]       = useState(true)
  const [joining, setJoining]       = useState(false)
  const [plan, setPlan]             = useState('monthly')

  useEffect(() => {
    if (role !== 'user') { setLoading(false); return }
    membershipAPI.status().then(r => setMembership(r.data)).catch(() => {}).finally(() => setLoading(false))
  }, [role])

  const handleJoin = async () => {
    setJoining(true)
    try {
      const r = await membershipAPI.join(plan)
      setMembership(r.data)
      toast.success('🎉 Welcome to Bazar Prime!')
    } catch { toast.error('Failed to join membership') }
    finally { setJoining(false) }
  }

  if (loading) return <Spinner />

  const isActive = membership?.is_valid

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-50 to-orange-50">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-10">
          <div className="text-5xl mb-3">⭐</div>
          <h1 className="text-3xl font-bold text-gray-800">Bazar Prime Membership</h1>
          <p className="text-gray-500 mt-2">Unlock exclusive benefits and save more on every order</p>
        </div>

        {/* Active membership */}
        {isActive && (
          <div className="bg-gradient-to-r from-yellow-400 to-orange-400 text-white rounded-2xl shadow-lg p-6 mb-8 text-center">
            <Star size={40} className="mx-auto mb-2 fill-white" />
            <h2 className="text-2xl font-bold mb-1">You're a Bazar Prime Member! 🎉</h2>
            <p className="text-yellow-100 capitalize">{membership.plan} Plan</p>
            <p className="mt-2 text-lg font-semibold">{membership.days_remaining} days remaining</p>
            <p className="text-sm text-yellow-100">Valid till {new Date(membership.end_date).toLocaleDateString('en-IN')}</p>
          </div>
        )}

        {/* Benefits */}
        <div className="grid md:grid-cols-2 gap-4 mb-8">
          {[
            { icon: '🚚', title: 'Free Delivery', desc: 'Free delivery on all orders, no minimum order value' },
            { icon: '💰', title: 'No Platform Fee', desc: 'Save ₹5 on every order — no platform fee ever' },
            { icon: '⚡', title: 'Priority Support', desc: 'Get faster resolution on returns and queries' },
            { icon: '🎁', title: 'Exclusive Deals', desc: 'Early access to sales and member-only discounts' },
          ].map(b => (
            <div key={b.title} className="bg-white rounded-xl shadow p-5 flex gap-4">
              <div className="text-3xl">{b.icon}</div>
              <div>
                <h3 className="font-bold text-gray-800 mb-1">{b.title}</h3>
                <p className="text-sm text-gray-500">{b.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Pricing */}
        {!isActive && (
          <>
            {!role || role !== 'user' ? (
              <div className="text-center bg-white rounded-xl shadow p-8">
                <p className="text-gray-500 mb-4">Please login as a buyer to join Bazar Prime</p>
                <Link to="/login" className="btn-primary">Login Now</Link>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-lg p-8">
                <h2 className="text-xl font-bold text-gray-800 mb-6 text-center">Choose Your Plan</h2>
                <div className="grid sm:grid-cols-2 gap-4 mb-6">
                  {[
                    { value: 'monthly', label: 'Monthly', price: '₹199', period: '/month', saving: 'Flexible' },
                    { value: 'yearly', label: 'Yearly', price: '₹999', period: '/year', saving: 'Save ₹1,389!' },
                  ].map(p => (
                    <label key={p.value}
                      className={`flex flex-col items-center p-6 rounded-xl border-2 cursor-pointer transition-all
                        ${plan === p.value ? 'border-accent bg-orange-50' : 'border-gray-200 hover:border-gray-300'}`}>
                      <input type="radio" value={p.value} checked={plan === p.value}
                        onChange={() => setPlan(p.value)} className="sr-only" />
                      <span className="font-bold text-gray-700 mb-1">{p.label}</span>
                      <span className="text-3xl font-bold text-accent">{p.price}</span>
                      <span className="text-gray-400 text-sm">{p.period}</span>
                      <span className="mt-2 text-xs font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">{p.saving}</span>
                      {plan === p.value && <Check size={20} className="mt-2 text-accent" />}
                    </label>
                  ))}
                </div>
                <button onClick={handleJoin} disabled={joining}
                  className="w-full py-4 bg-accent hover:bg-accent-dark text-white font-bold text-lg rounded-xl transition-colors disabled:opacity-50">
                  {joining ? 'Processing...' : `Join Bazar Prime — ${plan === 'monthly' ? '₹199/month' : '₹999/year'}`}
                </button>
                <p className="text-xs text-gray-400 text-center mt-3">Cancel anytime. No questions asked.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
