import { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { orderAPI, wishlistAPI } from '../api/client'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import { Spinner, Empty, TrackingBar } from '../components/UI'
import { useEffect } from 'react'
import ProductCard from '../components/ProductCard'
import toast from 'react-hot-toast'
import { Package, CheckCircle, Heart } from 'lucide-react'

// ─── CHECKOUT ────────────────────────────────────────────────
export function Checkout() {
  const { user } = useAuth()
  const { items, clearCart } = useCart()
  const navigate = useNavigate()
  const location = useLocation()
  const [method, setMethod] = useState('COD')
  const [loading, setLoading] = useState(false)

  const state = location.state || {}
  const coupon_code = state.coupon_code || ''
  const total = state.total || items.reduce((s, i) => s + parseFloat(i.product.price) * i.quantity, 0)

  const handlePlace = async () => {
    setLoading(true)
    try {
      const r = await orderAPI.checkout({ payment_method: method, coupon_code })
      clearCart()
      toast.success('Order placed successfully! 🎉')
      navigate('/orders/' + r.data.order_id)
    } catch (e) {
      toast.error(e.response?.data?.error || 'Checkout failed')
    } finally { setLoading(false) }
  }

  if (!items.length) return (
    <div className="text-center py-20">
      <Empty icon="🛒" message="Nothing to checkout" />
      <Link to="/" className="btn-primary mt-4 inline-block">Shop Now</Link>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">Checkout</h1>
        <div className="grid md:grid-cols-2 gap-6">
          {/* Delivery address */}
          <div className="bg-white rounded-xl shadow p-5">
            <h2 className="font-bold text-gray-700 mb-3">📍 Delivery Address</h2>
            <p className="text-sm text-gray-600">{user?.name}</p>
            <p className="text-sm text-gray-500">{user?.house_no}, {user?.address_line}</p>
            {user?.nearby_landmark && <p className="text-sm text-gray-500">Near {user.nearby_landmark}</p>}
            <p className="text-sm text-gray-500">{user?.district}, {user?.state} — {user?.pincode}</p>
            <p className="text-sm text-gray-500">📱 {user?.phone_number}</p>
          </div>

          {/* Payment method */}
          <div className="bg-white rounded-xl shadow p-5">
            <h2 className="font-bold text-gray-700 mb-3">💳 Payment Method</h2>
            {[
              { value: 'COD', label: '💵 Cash on Delivery' },
              { value: 'UPI', label: '📱 UPI' },
              { value: 'Card', label: '💳 Debit/ATM Card' },
              { value: 'NetBanking', label: '🏦 Net Banking' },
            ].map(m => (
              <label key={m.value} className={`flex items-center gap-3 p-3 rounded-lg border-2 mb-2 cursor-pointer transition-colors
                ${method === m.value ? 'border-primary bg-blue-50' : 'border-gray-100 hover:border-gray-300'}`}>
                <input type="radio" value={m.value} checked={method === m.value}
                  onChange={() => setMethod(m.value)} className="accent-primary" />
                <span className="text-sm font-medium">{m.label}</span>
              </label>
            ))}
          </div>

          {/* Order items */}
          <div className="bg-white rounded-xl shadow p-5">
            <h2 className="font-bold text-gray-700 mb-3">📦 Items</h2>
            <div className="space-y-2">
              {items.map(item => (
                <div key={item.id} className="flex justify-between text-sm text-gray-600">
                  <span className="flex-1 truncate mr-2">{item.product.product_name} × {item.quantity}</span>
                  <span className="font-semibold">₹{(parseFloat(item.product.price) * item.quantity).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Summary + Place order */}
          <div className="bg-white rounded-xl shadow p-5">
            <h2 className="font-bold text-gray-700 mb-3">🧾 Order Summary</h2>
            <div className="space-y-2 text-sm mb-4">
              <div className="flex justify-between text-gray-600"><span>Subtotal</span><span>₹{total.toFixed(2)}</span></div>
              <div className="flex justify-between font-bold text-base border-t pt-2"><span>Total</span><span>₹{total.toFixed(2)}</span></div>
            </div>
            <button onClick={handlePlace} disabled={loading} className="btn-primary w-full py-3 text-base">
              {loading ? 'Placing Order...' : `Place Order — ₹${total.toFixed(2)}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── ORDERS LIST ─────────────────────────────────────────────
export function OrderList() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    orderAPI.list().then(r => setOrders(r.data)).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <Package size={24} /> My Orders
        </h1>
        {orders.length === 0 ? (
          <Empty icon="📦" message="No orders yet" />
        ) : (
          <div className="space-y-4">
            {orders.map(order => (
              <Link key={order.order_id} to={`/orders/${order.order_id}`}
                className="bg-white rounded-xl shadow p-5 block hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="font-bold text-gray-800">Order #{order.order_id.slice(0, 8).toUpperCase()}</p>
                    <p className="text-sm text-gray-400">{new Date(order.order_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900">₹{parseFloat(order.total_amount).toLocaleString()}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold
                      ${order.order_status === 'Delivered' ? 'bg-green-100 text-green-700' :
                        order.order_status === 'Cancelled' ? 'bg-red-100 text-red-700' :
                        'bg-blue-100 text-blue-700'}`}>
                      {order.order_status}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap mt-2">
                  {order.items.slice(0, 3).map(item => (
                    <span key={item.id} className="text-xs bg-gray-50 text-gray-500 px-2 py-0.5 rounded">
                      {item.product_name} × {item.quantity}
                    </span>
                  ))}
                  {order.items.length > 3 && <span className="text-xs text-gray-400">+{order.items.length - 3} more</span>}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── ORDER DETAIL ─────────────────────────────────────────────
export function OrderDetail() {
  const { id } = { id: window.location.pathname.split('/').at(-1) }
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const params = window.location.pathname.split('/')
  const orderId = params[params.length - 1]

  useEffect(() => {
    orderAPI.detail(orderId).then(r => setOrder(r.data)).catch(() => {}).finally(() => setLoading(false))
  }, [orderId])

  if (loading) return <Spinner />
  if (!order) return <Empty icon="📦" message="Order not found" />

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center gap-3 mb-6">
          <CheckCircle size={28} className="text-green-500" />
          <div>
            <h1 className="text-xl font-bold text-gray-800">Order #{order.order_id.slice(0, 8).toUpperCase()}</h1>
            <p className="text-gray-400 text-sm">{new Date(order.order_date).toLocaleString('en-IN')}</p>
          </div>
        </div>

        {/* Tracking */}
        <div className="bg-white rounded-xl shadow p-6 mb-4">
          <h2 className="font-bold text-gray-700 mb-4">Order Tracking</h2>
          <TrackingBar steps={order.tracking_steps} />
        </div>

        {/* Items */}
        <div className="bg-white rounded-xl shadow p-6 mb-4">
          <h2 className="font-bold text-gray-700 mb-4">Items</h2>
          <div className="space-y-3">
            {order.items.map(item => (
              <div key={item.id} className="flex gap-4 items-center">
                {item.product_image_url ? (
                  <img src={item.product_image_url} alt={item.product_name}
                    className="w-16 h-16 object-cover rounded-lg" />
                ) : (
                  <div className="w-16 h-16 bg-blue-50 rounded-lg flex items-center justify-center text-2xl">🛍️</div>
                )}
                <div className="flex-1">
                  <p className="font-semibold text-gray-800 text-sm">{item.product_name}</p>
                  <p className="text-xs text-gray-400">Qty: {item.quantity} × ₹{parseFloat(item.price_at_purchase).toLocaleString()}</p>
                </div>
                <p className="font-bold">₹{parseFloat(item.subtotal).toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Bill */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="font-bold text-gray-700 mb-3">Bill Summary</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-gray-500"><span>Subtotal</span><span>₹{parseFloat(order.subtotal).toLocaleString()}</span></div>
            <div className="flex justify-between text-gray-500"><span>Delivery</span><span>{parseFloat(order.delivery_charge) === 0 ? 'FREE' : `₹${order.delivery_charge}`}</span></div>
            <div className="flex justify-between text-gray-500"><span>Platform Fee</span><span>₹{order.platform_fee}</span></div>
            <div className="flex justify-between font-bold text-base border-t pt-2"><span>Total</span><span>₹{parseFloat(order.total_amount).toLocaleString()}</span></div>
          </div>
          <div className="mt-3 flex gap-2 text-xs">
            <span className={`px-2 py-0.5 rounded-full ${order.payment_status === 'Paid' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
              {order.payment_method} — {order.payment_status}
            </span>
            {order.is_bazar_member && <span className="px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">⭐ Bazar Prime</span>}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── WISHLIST ─────────────────────────────────────────────────
export function Wishlist() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    wishlistAPI.list().then(r => setItems(r.data)).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleWishlistChange = (productId, isWishlisted) => {
    if (!isWishlisted) setItems(items => items.filter(i => i.product.product_id !== productId))
  }

  if (loading) return <Spinner />

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <Heart size={24} className="fill-red-500 text-red-500" /> Wishlist
          <span className="text-base font-normal text-gray-400">({items.length} items)</span>
        </h1>
        {items.length === 0 ? (
          <Empty icon="💝" message="Your wishlist is empty" />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {items.map(item => (
              <ProductCard key={item.id} product={item.product}
                wishlisted={true} onWishlistChange={handleWishlistChange} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
