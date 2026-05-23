import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ShoppingCart, Heart, Star, Truck, Shield, ArrowLeft } from 'lucide-react'
import { productAPI, wishlistAPI } from '../api/client'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import { Spinner, StockBadge, StarRating } from '../components/UI'
import ProductCard from '../components/ProductCard'
import toast from 'react-hot-toast'

export default function ProductDetail() {
  const { id } = useParams()
  const { addToCart } = useCart()
  const { role } = useAuth()
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [wishlisted, setWishlisted] = useState(false)
  const [review, setReview]   = useState({ rating: 5, review_text: '' })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    setLoading(true)
    productAPI.detail(id).then(r => {
      setData(r.data)
    }).catch(() => toast.error('Product not found'))
    .finally(() => setLoading(false))
  }, [id])

  const handleAddToCart = async () => {
    if (role !== 'user') { toast.error('Please login first'); return }
    try {
      await addToCart(id)
      toast.success('Added to cart!')
    } catch (e) { toast.error(e.response?.data?.error || 'Failed') }
  }

  const handleWishlist = async () => {
    if (role !== 'user') { toast.error('Please login first'); return }
    try {
      const r = await wishlistAPI.toggle({ product_id: id })
      setWishlisted(r.data.wishlisted)
      toast.success(r.data.wishlisted ? 'Added to wishlist!' : 'Removed from wishlist')
    } catch { toast.error('Failed') }
  }

  const handleReview = async (e) => {
    e.preventDefault()
    if (role !== 'user') { toast.error('Login to submit review'); return }
    setSubmitting(true)
    try {
      await productAPI.addReview(id, review)
      toast.success('Review submitted!')
      // Reload
      const r = await productAPI.detail(id)
      setData(r.data)
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed to submit review')
    } finally { setSubmitting(false) }
  }

  if (loading) return <Spinner />
  if (!data) return <div className="text-center py-20 text-gray-400">Product not found.</div>

  const { product, reviews, related } = data

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <Link to="/" className="flex items-center gap-1 text-primary hover:underline text-sm mb-4">
          <ArrowLeft size={16} /> Back to Products
        </Link>

        <div className="grid md:grid-cols-2 gap-8 bg-white rounded-xl shadow p-6 mb-8">
          {/* Image */}
          <div>
            {product.product_image_url ? (
              <img src={product.product_image_url} alt={product.product_name}
                className="w-full h-80 object-contain rounded-lg bg-gray-50" />
            ) : (
              <div className="w-full h-80 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg flex items-center justify-center text-8xl">
                🛍️
              </div>
            )}
          </div>

          {/* Info */}
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{product.category}</p>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">{product.product_name}</h1>

            <StarRating rating={product.average_rating} count={product.review_count} />

            <div className="flex items-center gap-3 my-4">
              <span className="text-3xl font-bold text-gray-900">₹{parseFloat(product.price).toLocaleString()}</span>
              <StockBadge badge={product.stock_badge} />
            </div>

            <p className="text-gray-600 text-sm mb-4">{product.description}</p>

            <div className="flex gap-3 mb-6">
              <button onClick={handleAddToCart}
                disabled={product.stock_badge?.status === 'out'}
                className="flex-1 flex items-center justify-center gap-2 btn-primary py-3 disabled:opacity-40">
                <ShoppingCart size={18} /> Add to Cart
              </button>
              <button onClick={handleWishlist}
                className={`p-3 rounded border-2 transition-colors ${wishlisted ? 'border-red-500 text-red-500' : 'border-gray-300 text-gray-400 hover:border-red-400'}`}>
                <Heart size={18} className={wishlisted ? 'fill-red-500' : ''} />
              </button>
            </div>

            <div className="flex flex-col gap-2 text-sm text-gray-500 border-t pt-4">
              <div className="flex items-center gap-2"><Truck size={16} className="text-green-500" /> Free delivery above ₹500</div>
              <div className="flex items-center gap-2"><Shield size={16} className="text-blue-500" /> Seller: {product.seller?.name}</div>
              <div className="flex items-center gap-2">📦 Stock: {product.stock_quantity} units</div>
            </div>
          </div>
        </div>

        {/* Reviews */}
        <div className="bg-white rounded-xl shadow p-6 mb-8">
          <h2 className="text-lg font-bold mb-4">Customer Reviews ({reviews.length})</h2>
          {reviews.length === 0 ? (
            <p className="text-gray-400 text-sm">No reviews yet. Be the first!</p>
          ) : (
            <div className="space-y-4">
              {reviews.map(r => (
                <div key={r.id} className="border-b pb-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-sm">{r.user_name}</span>
                    <div className="flex">
                      {[1,2,3,4,5].map(s => (
                        <span key={s} className={s <= r.rating ? 'text-yellow-400' : 'text-gray-200'}>★</span>
                      ))}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{r.review_text}</p>
                  <p className="text-xs text-gray-400 mt-1">{new Date(r.created_at).toLocaleDateString('en-IN')}</p>
                </div>
              ))}
            </div>
          )}

          {/* Submit review */}
          {role === 'user' && (
            <form onSubmit={handleReview} className="mt-6 border-t pt-4">
              <h3 className="font-semibold mb-3">Write a Review</h3>
              <div className="flex gap-1 mb-3">
                {[1,2,3,4,5].map(s => (
                  <button type="button" key={s} onClick={() => setReview(r => ({ ...r, rating: s }))}
                    className={`text-2xl transition-transform hover:scale-110 ${s <= review.rating ? 'text-yellow-400' : 'text-gray-200'}`}>
                    ★
                  </button>
                ))}
              </div>
              <textarea value={review.review_text}
                onChange={e => setReview(r => ({ ...r, review_text: e.target.value }))}
                placeholder="Share your experience..."
                className="input h-24 resize-none mb-3" />
              <button type="submit" disabled={submitting} className="btn-primary">
                {submitting ? 'Submitting...' : 'Submit Review'}
              </button>
            </form>
          )}
        </div>

        {/* Related products */}
        {related.length > 0 && (
          <div>
            <h2 className="text-lg font-bold mb-4">Related Products</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {related.map(p => <ProductCard key={p.product_id} product={p} />)}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
