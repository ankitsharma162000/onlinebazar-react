import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Trash2, Plus, Minus, ShoppingBag, Tag } from 'lucide-react'
import { useCart } from '../context/CartContext'
import { couponAPI } from '../api/client'
import { Spinner, Empty } from '../components/UI'
import toast from 'react-hot-toast'

export default function Cart() {
  const { items, loading, updateCart, cartTotal } = useCart()
  const navigate = useNavigate()
  const [coupon, setCoupon] = useState('')
  const [discount, setDiscount] = useState(null)
  const [applying, setApplying] = useState(false)

  const handleUpdate = async (id, action) => {
    try { await updateCart(id, action) }
    catch { toast.error('Failed to update cart') }
  }

  const handleCoupon = async () => {
    if (!coupon.trim()) return
    setApplying(true)
    try {
      const r = await couponAPI.apply(coupon)
      setDiscount(r.data)
      toast.success('Coupon applied!')
    } catch { toast.error('Invalid or expired coupon') }
    finally { setApplying(false) }
  }

  const discountAmount = discount
    ? discount.discount_type === 'flat' ? discount.value : cartTotal * discount.value / 100
    : 0
  const delivery  = cartTotal >= 500 ? 0 : 50
  const platform  = 5
  const total     = Math.max(0, cartTotal - discountAmount + delivery + platform)

  if (loading) return <Spinner />

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <ShoppingBag size={24} /> My Cart
          <span className="text-base font-normal text-gray-400">({items.length} items)</span>
        </h1>

        {items.length === 0 ? (
          <div className="text-center py-20">
            <Empty icon="🛒" message="Your cart is empty" />
            <Link to="/" className="btn-primary mt-4 inline-block">Shop Now</Link>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Items */}
            <div className="lg:col-span-2 space-y-3">
              {items.map(item => (
                <div key={item.id} className="bg-white rounded-xl shadow p-4 flex gap-4">
                  <Link to={`/products/${item.product.product_id}`}>
                    {item.product.product_image_url ? (
                      <img src={item.product.product_image_url} alt={item.product.product_name}
                        className="w-20 h-20 object-cover rounded-lg" />
                    ) : (
                      <div className="w-20 h-20 bg-blue-50 rounded-lg flex items-center justify-center text-3xl">🛍️</div>
                    )}
                  </Link>
                  <div className="flex-1">
                    <Link to={`/products/${item.product.product_id}`} className="font-semibold text-gray-800 hover:text-primary text-sm line-clamp-2">
                      {item.product.product_name}
                    </Link>
                    <p className="text-lg font-bold text-gray-900 mt-1">
                      ₹{(parseFloat(item.product.price) * item.quantity).toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-400">₹{parseFloat(item.product.price).toLocaleString()} each</p>
                    <div className="flex items-center gap-3 mt-2">
                      <div className="flex items-center gap-2 border rounded-lg">
                        <button onClick={() => handleUpdate(item.id, 'decrease')}
                          className="p-1.5 hover:bg-gray-50 rounded-l-lg"><Minus size={14} /></button>
                        <span className="w-8 text-center text-sm font-semibold">{item.quantity}</span>
                        <button onClick={() => handleUpdate(item.id, 'increase')}
                          className="p-1.5 hover:bg-gray-50 rounded-r-lg"><Plus size={14} /></button>
                      </div>
                      <button onClick={() => handleUpdate(item.id, 'remove')}
                        className="text-red-400 hover:text-red-600 flex items-center gap-1 text-xs">
                        <Trash2 size={14} /> Remove
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Summary */}
            <div className="space-y-4">
              {/* Coupon */}
              <div className="bg-white rounded-xl shadow p-4">
                <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-1">
                  <Tag size={16} /> Apply Coupon
                </h3>
                <div className="flex gap-2">
                  <input value={coupon} onChange={e => setCoupon(e.target.value.toUpperCase())}
                    placeholder="Enter code" className="input flex-1" />
                  <button onClick={handleCoupon} disabled={applying}
                    className="btn-accent px-3 text-sm">{applying ? '...' : 'Apply'}</button>
                </div>
                {discount && (
                  <p className="text-green-600 text-xs mt-2">
                    ✅ Saved ₹{discountAmount.toFixed(2)}
                    <button onClick={() => setDiscount(null)} className="ml-2 text-red-400">✕</button>
                  </p>
                )}
              </div>

              {/* Price breakdown */}
              <div className="bg-white rounded-xl shadow p-4">
                <h3 className="font-semibold text-gray-700 mb-3">Price Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between text-gray-600">
                    <span>Subtotal</span><span>₹{cartTotal.toFixed(2)}</span>
                  </div>
                  {discountAmount > 0 && (
                    <div className="flex justify-between text-green-600">
                      <span>Discount</span><span>−₹{discountAmount.toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-gray-600">
                    <span>Delivery</span>
                    <span>{delivery === 0 ? <span className="text-green-600">FREE</span> : `₹${delivery}`}</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Platform Fee</span><span>₹{platform}</span>
                  </div>
                  <div className="flex justify-between font-bold text-base border-t pt-2">
                    <span>Total</span><span>₹{total.toFixed(2)}</span>
                  </div>
                </div>
                <button onClick={() => navigate('/checkout', { state: { coupon_code: discount ? coupon : '', discountAmount, total } })}
                  className="btn-primary w-full py-3 mt-4 text-base">
                  Proceed to Checkout
                </button>
                {cartTotal < 500 && (
                  <p className="text-xs text-center text-gray-400 mt-2">
                    Add ₹{(500 - cartTotal).toFixed(0)} more for free delivery
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
