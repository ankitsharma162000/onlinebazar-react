import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authAPI, sellerAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'
import PincodeInput from '../components/PincodeInput'
import { Spinner, Empty } from '../components/UI'
import toast from 'react-hot-toast'
import { Store, Package, BarChart2, Plus, Edit2, Trash2, CheckCircle, XCircle, Truck, Eye, EyeOff } from 'lucide-react'

// ─── SELLER LOGIN ─────────────────────────────────────────────
export function SellerLogin() {
  const { loginSeller } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [showPwd, setShowPwd] = useState(false)

  const submit = async (e) => {
    e.preventDefault(); setLoading(true)
    try {
      const r = await authAPI.sellerLogin(form)
      loginSeller(r.data)
      toast.success(`Welcome, ${r.data.seller.name}!`)
      navigate('/seller/dashboard')
    } catch (e) { toast.error(e.response?.data?.error || 'Login failed') }
    finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-8">
        <div className="text-center mb-6">
          <div className="flex justify-center mb-2">
            <div className="bg-green-600 text-white rounded-full p-3"><Store size={28} /></div>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Seller Login</h1>
          <p className="text-gray-500 text-sm mt-1">Manage your OnlineBazar store</p>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-sm font-semibold text-gray-600 block mb-1">Email</label>
            <input type="email" required value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className="input" />
          </div>
          <div>
            <label className="text-sm font-semibold text-gray-600 block mb-1">Password</label>
            <div className="relative">
              <input type={showPwd ? 'text' : 'password'} required value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))} className="input pr-10" />
              <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-2.5 text-gray-400">
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
          <button type="submit" disabled={loading} className="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded font-semibold transition-colors">
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-500">
          New seller? <Link to="/seller/register" className="text-green-600 font-semibold">Register here</Link>
        </p>
        <p className="text-center mt-2 text-sm text-gray-400">
          Shopping? <Link to="/login" className="text-primary font-semibold">Buyer Login</Link>
        </p>
      </div>
    </div>
  )
}

// ─── SELLER REGISTER ─────────────────────────────────────────
export function SellerRegister() {
  const { loginSeller } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name:'', email:'', phone_number:'', password:'', confirm_password:'', address_line:'', district:'', state:'', pincode:'' })
  const [loading, setLoading] = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm_password) { toast.error('Passwords do not match!'); return }
    setLoading(true)
    try {
      const { confirm_password, ...payload } = form
      const r = await authAPI.sellerRegister(payload)
      loginSeller(r.data)
      toast.success('Seller account created! 🎉')
      navigate('/seller/dashboard')
    } catch (e) { toast.error(e.response?.data?.error || 'Registration failed') }
    finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-lg mx-auto bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-6">
          <div className="flex justify-center mb-2">
            <div className="bg-green-600 text-white rounded-full p-3"><Store size={28} /></div>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Create Seller Account</h1>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs font-semibold text-gray-500 block mb-1">Full Name *</label>
              <input required value={form.name} onChange={e => set('name', e.target.value)} className="input" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Email *</label>
              <input type="email" required value={form.email} onChange={e => set('email', e.target.value)} className="input" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Phone *</label>
              <input maxLength={10} required value={form.phone_number} onChange={e => set('phone_number', e.target.value)} className="input" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Password *</label>
              <input type="password" required minLength={6} value={form.password} onChange={e => set('password', e.target.value)} className="input" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Confirm Password *</label>
              <input type="password" required value={form.confirm_password} onChange={e => set('confirm_password', e.target.value)} className="input" />
            </div>
            <div className="col-span-2">
              <label className="text-xs font-semibold text-gray-500 block mb-1">Business Address *</label>
              <input required value={form.address_line} onChange={e => set('address_line', e.target.value)} className="input" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Pincode *</label>
              <PincodeInput value={form.pincode} onChange={v => set('pincode', v)}
                onAreaFound={({ district, state }) => { if (district) set('district', district); if (state) set('state', state) }} />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">District *</label>
              <input required value={form.district} onChange={e => set('district', e.target.value)} className="input" placeholder="Auto-filled" />
            </div>
            <div className="col-span-2">
              <label className="text-xs font-semibold text-gray-500 block mb-1">State *</label>
              <input required value={form.state} onChange={e => set('state', e.target.value)} className="input" placeholder="Auto-filled" />
            </div>
          </div>
          <button type="submit" disabled={loading} className="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded font-semibold transition-colors">
            {loading ? 'Creating...' : 'Create Seller Account'}
          </button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-500">
          Already registered? <Link to="/seller/login" className="text-green-600 font-semibold">Login</Link>
        </p>
      </div>
    </div>
  )
}

// ─── SELLER DASHBOARD ─────────────────────────────────────────
export function SellerDashboard() {
  const { seller } = useAuth()
  const [stats, setStats]     = useState(null)
  const [products, setProducts] = useState([])
  const [orders, setOrders]   = useState([])
  const [tab, setTab]         = useState('overview')
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editProduct, setEditProduct]   = useState(null)

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [s, p, o] = await Promise.all([sellerAPI.stats(), sellerAPI.products(), sellerAPI.orders()])
      setStats(s.data); setProducts(p.data); setOrders(o.data)
    } catch { toast.error('Failed to load data') }
    finally { setLoading(false) }
  }

  const handleOrderAction = async (id, action, extra = {}) => {
    try {
      await sellerAPI.orderAction(id, { action, ...extra })
      toast.success('Updated!')
      loadData()
    } catch { toast.error('Failed') }
  }

  if (loading) return <Spinner />

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Seller Dashboard</h1>
            <p className="text-gray-500 text-sm">Welcome, {seller?.name}</p>
          </div>
          <button onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded font-semibold transition-colors">
            <Plus size={18} /> Add Product
          </button>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            {[
              { label: 'Products', value: stats.total_products, icon: '📦', color: 'blue' },
              { label: 'Active', value: stats.active_products, icon: '✅', color: 'green' },
              { label: 'Pending Orders', value: stats.pending_orders, icon: '⏳', color: 'yellow' },
              { label: 'Total Orders', value: stats.total_orders, icon: '🛒', color: 'purple' },
              { label: 'Revenue', value: `₹${stats.total_revenue.toLocaleString()}`, icon: '💰', color: 'green' },
            ].map(s => (
              <div key={s.label} className="bg-white rounded-xl shadow p-4 text-center">
                <div className="text-2xl mb-1">{s.icon}</div>
                <div className="text-xl font-bold text-gray-800">{s.value}</div>
                <div className="text-xs text-gray-500">{s.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-4 border-b">
          {[{ id: 'overview', label: 'Products', icon: <Package size={16} /> },
            { id: 'orders', label: 'Orders', icon: <BarChart2 size={16} /> }
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors -mb-px
                ${tab === t.id ? 'border-green-600 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* Products tab */}
        {tab === 'overview' && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {products.length === 0 ? <Empty icon="📦" message="No products yet. Add your first!" /> :
              products.map(p => (
                <div key={p.product_id} className="bg-white rounded-xl shadow p-4">
                  {p.product_image_url ? (
                    <img src={p.product_image_url} alt={p.product_name} className="w-full h-36 object-cover rounded-lg mb-3" />
                  ) : (
                    <div className="w-full h-36 bg-blue-50 rounded-lg mb-3 flex items-center justify-center text-4xl">🛍️</div>
                  )}
                  <p className="text-xs text-gray-400 mb-0.5">{p.category}</p>
                  <h3 className="font-semibold text-gray-800 text-sm line-clamp-2 mb-1">{p.product_name}</h3>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-gray-900">₹{parseFloat(p.price).toLocaleString()}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${p.stock_quantity <= 0 ? 'bg-red-100 text-red-600' : p.stock_quantity <= 10 ? 'bg-yellow-100 text-yellow-600' : 'bg-green-100 text-green-600'}`}>
                      Stock: {p.stock_quantity}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => setEditProduct(p)}
                      className="flex-1 flex items-center justify-center gap-1 border border-blue-300 text-blue-600 rounded py-1.5 text-xs hover:bg-blue-50 transition-colors">
                      <Edit2 size={13} /> Edit
                    </button>
                    <button onClick={async () => { await sellerAPI.deleteProduct(p.product_id); loadData(); toast.success('Deactivated') }}
                      className="flex-1 flex items-center justify-center gap-1 border border-red-300 text-red-500 rounded py-1.5 text-xs hover:bg-red-50 transition-colors">
                      <Trash2 size={13} /> Remove
                    </button>
                  </div>
                </div>
              ))
            }
          </div>
        )}

        {/* Orders tab */}
        {tab === 'orders' && (
          <div className="space-y-4">
            {orders.length === 0 ? <Empty icon="📬" message="No orders yet" /> :
              orders.map(req => (
                <div key={req.id} className="bg-white rounded-xl shadow p-5">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <p className="font-bold text-gray-800">{req.product_name} × {req.quantity}</p>
                      <p className="text-sm text-gray-500">Customer: {req.customer_name}</p>
                      <p className="text-xs text-gray-400">{req.delivery_address}</p>
                      <p className="text-xs text-gray-400">{new Date(req.order_date).toLocaleDateString('en-IN')}</p>
                    </div>
                    <span className={`text-xs px-2.5 py-1 rounded-full font-semibold
                      ${req.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                        req.status === 'accepted' ? 'bg-blue-100 text-blue-700' :
                        req.status === 'shipped' ? 'bg-purple-100 text-purple-700' :
                        req.status === 'delivered' ? 'bg-green-100 text-green-700' :
                        'bg-red-100 text-red-700'}`}>
                      {req.status.toUpperCase()}
                    </span>
                  </div>
                  {req.status === 'pending' && (
                    <div className="flex gap-2">
                      <button onClick={() => handleOrderAction(req.id, 'accept')}
                        className="flex items-center gap-1 bg-green-600 text-white text-xs px-3 py-1.5 rounded hover:bg-green-700 transition-colors">
                        <CheckCircle size={14} /> Accept
                      </button>
                      <button onClick={() => handleOrderAction(req.id, 'reject', { reason: 'Out of stock' })}
                        className="flex items-center gap-1 bg-red-500 text-white text-xs px-3 py-1.5 rounded hover:bg-red-600 transition-colors">
                        <XCircle size={14} /> Reject
                      </button>
                    </div>
                  )}
                  {req.status === 'accepted' && (
                    <div className="flex gap-2 mt-2">
                      <select id={`dp-${req.id}`} className="input text-xs flex-1">
                        {[['bluedart','Blue Dart'],['delhivery','Delhivery'],['dtdc','DTDC'],['ecom','Ecom Express'],['xpressbees','XpressBees']].map(([v, l]) => (
                          <option key={v} value={v}>{l}</option>
                        ))}
                      </select>
                      <button onClick={() => {
                        const dp = document.getElementById(`dp-${req.id}`).value
                        handleOrderAction(req.id, 'ship', { delivery_partner: dp, tracking_id: 'TRK' + Date.now() })
                      }} className="flex items-center gap-1 bg-purple-600 text-white text-xs px-3 py-1.5 rounded hover:bg-purple-700 transition-colors">
                        <Truck size={14} /> Mark Shipped
                      </button>
                    </div>
                  )}
                  {req.tracking_id && (
                    <p className="text-xs text-gray-400 mt-1">Tracking: {req.tracking_id} via {req.delivery_partner_name}</p>
                  )}
                </div>
              ))
            }
          </div>
        )}
      </div>

      {/* Add/Edit Product Modal */}
      {(showAddModal || editProduct) && (
        <ProductModal
          product={editProduct}
          onClose={() => { setShowAddModal(false); setEditProduct(null) }}
          onSave={() => { setShowAddModal(false); setEditProduct(null); loadData() }}
        />
      )}
    </div>
  )
}

// ─── PRODUCT MODAL ────────────────────────────────────────────
function ProductModal({ product, onClose, onSave }) {
  const [form, setForm] = useState({
    product_name: product?.product_name || '',
    category: product?.category || '',
    price: product?.price || '',
    description: product?.description || '',
    stock_quantity: product?.stock_quantity || '',
  })
  const [saving, setSaving] = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const CATS = ['Electronics','Clothing','Food','Beauty','Sports','Home','Books','Toys','Health','Other']

  const submit = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      if (product) {
        await sellerAPI.updateProduct(product.product_id, form)
        toast.success('Product updated!')
      } else {
        await sellerAPI.addProduct(form)
        toast.success('Product added!')
      }
      onSave()
    } catch { toast.error('Failed to save product') }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold">{product ? 'Edit Product' : 'Add New Product'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="text-xs font-semibold text-gray-500 block mb-1">Product Name *</label>
            <input required value={form.product_name} onChange={e => set('product_name', e.target.value)} className="input" />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 block mb-1">Category *</label>
            <select required value={form.category} onChange={e => set('category', e.target.value)} className="input">
              <option value="">Select Category</option>
              {CATS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Price (₹) *</label>
              <input type="number" required step="0.01" value={form.price} onChange={e => set('price', e.target.value)} className="input" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Stock *</label>
              <input type="number" required value={form.stock_quantity} onChange={e => set('stock_quantity', e.target.value)} className="input" />
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 block mb-1">Description</label>
            <textarea value={form.description} onChange={e => set('description', e.target.value)} className="input h-20 resize-none" />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 border border-gray-300 text-gray-600 rounded py-2 text-sm hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={saving} className="flex-1 bg-green-600 text-white rounded py-2 text-sm font-semibold hover:bg-green-700 disabled:opacity-50">
              {saving ? 'Saving...' : 'Save Product'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
