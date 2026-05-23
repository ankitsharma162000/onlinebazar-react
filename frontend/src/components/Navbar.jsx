import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ShoppingCart, Heart, User, Store, Search, Menu, X, LogOut, Package } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'

export default function Navbar() {
  const { user, seller, role, logout } = useAuth()
  const { cartCount } = useCart()
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)

  const handleSearch = (e) => {
    e.preventDefault()
    if (q.trim()) navigate(`/?q=${encodeURIComponent(q.trim())}`)
  }

  const handleLogout = () => { logout(); navigate('/') }

  return (
    <nav className="bg-primary text-white shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center gap-4 h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 shrink-0">
            <ShoppingCart size={24} />
            <span className="font-bold text-xl hidden sm:block">OnlineBazar</span>
          </Link>

          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1 max-w-xl">
            <div className="flex">
              <input
                value={q}
                onChange={e => setQ(e.target.value)}
                placeholder="Search products..."
                className="w-full px-3 py-2 text-gray-900 text-sm rounded-l focus:outline-none"
              />
              <button type="submit"
                className="bg-accent hover:bg-accent-dark px-3 py-2 rounded-r transition-colors">
                <Search size={18} />
              </button>
            </div>
          </form>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-4">
            {role === 'seller' ? (
              <>
                <Link to="/seller/dashboard" className="flex items-center gap-1 hover:text-yellow-200 text-sm">
                  <Store size={18} /><span>Dashboard</span>
                </Link>
                <button onClick={handleLogout} className="flex items-center gap-1 hover:text-yellow-200 text-sm">
                  <LogOut size={18} /><span>Logout</span>
                </button>
              </>
            ) : role === 'user' ? (
              <>
                <Link to="/wishlist" className="hover:text-yellow-200"><Heart size={20} /></Link>
                <Link to="/orders" className="flex items-center gap-1 hover:text-yellow-200 text-sm">
                  <Package size={18} /><span>Orders</span>
                </Link>
                <Link to="/cart" className="relative hover:text-yellow-200">
                  <ShoppingCart size={20} />
                  {cartCount > 0 && (
                    <span className="absolute -top-2 -right-2 bg-accent text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                      {cartCount}
                    </span>
                  )}
                </Link>
                <div className="relative group">
                  <button className="flex items-center gap-1 hover:text-yellow-200 text-sm">
                    <User size={18} /><span>{user?.name?.split(' ')[0]}</span>
                  </button>
                  <div className="absolute right-0 top-8 bg-white text-gray-800 rounded shadow-lg min-w-40 hidden group-hover:block">
                    <Link to="/profile" className="block px-4 py-2 hover:bg-gray-50 text-sm">Profile</Link>
                    <Link to="/membership" className="block px-4 py-2 hover:bg-gray-50 text-sm">⭐ Membership</Link>
                    <button onClick={handleLogout} className="block w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-red-600">
                      Logout
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                <Link to="/login" className="hover:text-yellow-200 text-sm">Login</Link>
                <Link to="/register" className="bg-accent hover:bg-accent-dark px-3 py-1.5 rounded text-sm font-semibold transition-colors">
                  Register
                </Link>
                <Link to="/seller/login" className="border border-white hover:bg-white hover:text-primary px-3 py-1.5 rounded text-sm font-semibold transition-colors">
                  Sell
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu toggle */}
          <button className="md:hidden ml-auto" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden pb-3 border-t border-blue-400 mt-1 pt-3 flex flex-col gap-2 text-sm">
            {role === 'user' && <>
              <Link to="/cart" onClick={() => setMenuOpen(false)} className="flex items-center gap-2">
                <ShoppingCart size={16} /> Cart ({cartCount})
              </Link>
              <Link to="/wishlist" onClick={() => setMenuOpen(false)} className="flex items-center gap-2">
                <Heart size={16} /> Wishlist
              </Link>
              <Link to="/orders" onClick={() => setMenuOpen(false)} className="flex items-center gap-2">
                <Package size={16} /> Orders
              </Link>
              <Link to="/membership" onClick={() => setMenuOpen(false)}>⭐ Membership</Link>
              <button onClick={handleLogout} className="text-left text-red-200">Logout</button>
            </>}
            {role === 'seller' && <>
              <Link to="/seller/dashboard" onClick={() => setMenuOpen(false)}>Dashboard</Link>
              <button onClick={handleLogout} className="text-left text-red-200">Logout</button>
            </>}
            {!role && <>
              <Link to="/login" onClick={() => setMenuOpen(false)}>Login</Link>
              <Link to="/register" onClick={() => setMenuOpen(false)}>Register as Buyer</Link>
              <Link to="/seller/login" onClick={() => setMenuOpen(false)}>Login as Seller</Link>
            </>}
          </div>
        )}
      </div>
    </nav>
  )
}
