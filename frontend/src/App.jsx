import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'
import { CartProvider } from './context/CartContext'

import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import ProductDetail from './pages/ProductDetail'
import { UserLogin, UserRegister } from './pages/Auth'
import Cart from './pages/Cart'
import { Checkout, OrderList, OrderDetail, Wishlist } from './pages/Shopping'
import { SellerLogin, SellerRegister, SellerDashboard } from './pages/Seller'
import Membership from './pages/Membership'

function ProtectedUser({ children }) {
  const { role, loading } = useAuth()
  if (loading) return null
  return role === 'user' ? children : <Navigate to="/login" />
}

function ProtectedSeller({ children }) {
  const { role, loading } = useAuth()
  if (loading) return null
  return role === 'seller' ? children : <Navigate to="/seller/login" />
}

function AppRoutes() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/products/:id" element={<ProductDetail />} />

        {/* Auth */}
        <Route path="/login" element={<UserLogin />} />
        <Route path="/register" element={<UserRegister />} />

        {/* User routes */}
        <Route path="/cart" element={<ProtectedUser><Cart /></ProtectedUser>} />
        <Route path="/checkout" element={<ProtectedUser><Checkout /></ProtectedUser>} />
        <Route path="/orders" element={<ProtectedUser><OrderList /></ProtectedUser>} />
        <Route path="/orders/:id" element={<ProtectedUser><OrderDetail /></ProtectedUser>} />
        <Route path="/wishlist" element={<ProtectedUser><Wishlist /></ProtectedUser>} />
        <Route path="/membership" element={<Membership />} />

        {/* Seller routes */}
        <Route path="/seller/login" element={<SellerLogin />} />
        <Route path="/seller/register" element={<SellerRegister />} />
        <Route path="/seller/dashboard" element={<ProtectedSeller><SellerDashboard /></ProtectedSeller>} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
      <Footer />
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
          <AppRoutes />
          <Toaster position="top-center" toastOptions={{
            duration: 3000,
            style: { borderRadius: '8px', fontWeight: '500' }
          }} />
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
