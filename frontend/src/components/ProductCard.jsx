import { Link } from 'react-router-dom'
import { Heart, ShoppingCart, Star } from 'lucide-react'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import { wishlistAPI } from '../api/client'
import toast from 'react-hot-toast'

export default function ProductCard({ product, wishlisted = false, onWishlistChange }) {
  const { addToCart } = useCart()
  const { role } = useAuth()

  const handleAddToCart = async (e) => {
    e.preventDefault()
    if (role !== 'user') { toast.error('Please login to add to cart'); return }
    try {
      await addToCart(product.product_id)
      toast.success('Added to cart!')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to add to cart')
    }
  }

  const handleWishlist = async (e) => {
    e.preventDefault()
    if (role !== 'user') { toast.error('Please login first'); return }
    try {
      const r = await wishlistAPI.toggle({ product_id: product.product_id })
      toast.success(r.data.wishlisted ? 'Added to wishlist!' : 'Removed from wishlist')
      onWishlistChange?.(product.product_id, r.data.wishlisted)
    } catch { toast.error('Failed') }
  }

  const badge = product.stock_badge
  const img = product.product_image_url

  return (
    <Link to={`/products/${product.product_id}`} className="card block group">
      <div className="relative overflow-hidden rounded-t-lg">
        {img ? (
          <img src={img} alt={product.product_name}
            className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300" />
        ) : (
          <div className="w-full h-48 bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center text-5xl">
            🛍️
          </div>
        )}
        {/* Wishlist btn */}
        <button onClick={handleWishlist}
          className="absolute top-2 right-2 bg-white rounded-full p-1.5 shadow hover:bg-red-50 transition-colors">
          <Heart size={16} className={wishlisted ? 'fill-red-500 text-red-500' : 'text-gray-400'} />
        </button>
        {/* Stock badge */}
        {badge && (
          <span className={`absolute top-2 left-2 text-xs px-2 py-0.5 rounded-full font-semibold
            ${badge.color === 'danger' ? 'bg-red-500 text-white' :
              badge.color === 'warning' ? 'bg-yellow-400 text-gray-900' :
              'bg-green-500 text-white'}`}>
            {badge.label}
          </span>
        )}
      </div>

      <div className="p-3">
        <p className="text-xs text-gray-500 mb-1">{product.category}</p>
        <h3 className="font-semibold text-gray-800 text-sm line-clamp-2 mb-1 group-hover:text-primary transition-colors">
          {product.product_name}
        </h3>

        {/* Rating */}
        <div className="flex items-center gap-1 mb-2">
          <div className="flex">
            {[1,2,3,4,5].map(s => (
              <Star key={s} size={12}
                className={s <= Math.round(product.average_rating) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-200 fill-gray-200'} />
            ))}
          </div>
          <span className="text-xs text-gray-500">({product.review_count})</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-gray-900">₹{parseFloat(product.price).toLocaleString()}</span>
          <button onClick={handleAddToCart}
            disabled={badge?.status === 'out'}
            className="flex items-center gap-1 bg-primary text-white text-xs px-2.5 py-1.5 rounded hover:bg-primary-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
            <ShoppingCart size={13} /> Add
          </button>
        </div>

        <p className="text-xs text-gray-400 mt-1 truncate">by {product.seller?.name}</p>
      </div>
    </Link>
  )
}
