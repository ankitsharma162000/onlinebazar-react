import { createContext, useContext, useState, useEffect } from 'react'
import { cartAPI } from '../api/client'
import { useAuth } from './AuthContext'

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const { role } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchCart = async () => {
    if (role !== 'user') return
    setLoading(true)
    try {
      const r = await cartAPI.list()
      setItems(r.data)
    } catch { setItems([]) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchCart() }, [role])

  const addToCart = async (productId) => {
    await cartAPI.add({ product_id: productId })
    fetchCart()
  }

  const updateCart = async (cartId, action) => {
    await cartAPI.update(cartId, { action })
    fetchCart()
  }

  const clearCart = () => setItems([])

  const cartCount = items.reduce((s, i) => s + i.quantity, 0)
  const cartTotal = items.reduce((s, i) => s + (parseFloat(i.product.price) * i.quantity), 0)

  return (
    <CartContext.Provider value={{ items, loading, cartCount, cartTotal, addToCart, updateCart, fetchCart, clearCart }}>
      {children}
    </CartContext.Provider>
  )
}

export const useCart = () => useContext(CartContext)
