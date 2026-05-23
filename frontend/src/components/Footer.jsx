import { Link } from 'react-router-dom'
import { ShoppingCart } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-gray-800 text-gray-300 mt-12">
      <div className="max-w-7xl mx-auto px-4 py-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 text-white font-bold text-lg mb-3">
              <ShoppingCart size={20} /> OnlineBazar
            </div>
            <p className="text-sm text-gray-400">India's Growing Marketplace. MCA Project by Ankit Sharma & Niraj Kumar.</p>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3">Shop</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/?category=Electronics" className="hover:text-white transition-colors">Electronics</Link></li>
              <li><Link to="/?category=Clothing" className="hover:text-white transition-colors">Clothing</Link></li>
              <li><Link to="/?category=Food" className="hover:text-white transition-colors">Food</Link></li>
              <li><Link to="/?category=Beauty" className="hover:text-white transition-colors">Beauty</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3">Account</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/login" className="hover:text-white transition-colors">Login</Link></li>
              <li><Link to="/register" className="hover:text-white transition-colors">Register</Link></li>
              <li><Link to="/orders" className="hover:text-white transition-colors">My Orders</Link></li>
              <li><Link to="/membership" className="hover:text-white transition-colors">⭐ Prime Membership</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3">Seller</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/seller/register" className="hover:text-white transition-colors">Become a Seller</Link></li>
              <li><Link to="/seller/login" className="hover:text-white transition-colors">Seller Login</Link></li>
              <li><Link to="/seller/dashboard" className="hover:text-white transition-colors">Dashboard</Link></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-700 pt-6 text-center text-xs text-gray-500">
          © {new Date().getFullYear()} OnlineBazar. MCA Project — Ankit Sharma (34) & Niraj Kumar (8). All rights reserved.
        </div>
      </div>
    </footer>
  )
}
