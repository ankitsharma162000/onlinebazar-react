import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// ── Auth ──────────────────────────────────────────────────────
export const authAPI = {
  userRegister: d => api.post('/auth/user/register/', d),
  userLogin:    d => api.post('/auth/user/login/', d),
  sellerRegister: d => api.post('/auth/seller/register/', d),
  sellerLogin:  d => api.post('/auth/seller/login/', d),
  userMe:       () => api.get('/auth/user/me/'),
  sellerMe:     () => api.get('/auth/seller/me/'),
}

// ── Products ──────────────────────────────────────────────────
export const productAPI = {
  list:        params => api.get('/products/', { params }),
  detail:      id => api.get(`/products/${id}/`),
  featured:    () => api.get('/products/featured/'),
  recommended: () => api.get('/products/recommended/'),
  categories:  () => api.get('/products/categories/'),
  addReview:   (id, d) => api.post(`/products/${id}/review/`, d),
}

// ── Cart ──────────────────────────────────────────────────────
export const cartAPI = {
  list:   () => api.get('/cart/'),
  add:    d => api.post('/cart/add/', d),
  update: (id, d) => api.patch(`/cart/${id}/`, d),
}

// ── Wishlist ──────────────────────────────────────────────────
export const wishlistAPI = {
  list:   () => api.get('/wishlist/'),
  toggle: d => api.post('/wishlist/toggle/', d),
}

// ── Orders ────────────────────────────────────────────────────
export const orderAPI = {
  list:     () => api.get('/orders/'),
  detail:   id => api.get(`/orders/${id}/`),
  checkout: d => api.post('/orders/checkout/', d),
}

// ── Coupon ────────────────────────────────────────────────────
export const couponAPI = {
  apply: code => api.post('/coupon/apply/', { code }),
}

// ── Membership ────────────────────────────────────────────────
export const membershipAPI = {
  status: () => api.get('/membership/'),
  join:   plan => api.post('/membership/join/', { plan }),
}

// ── Seller ────────────────────────────────────────────────────
export const sellerAPI = {
  stats:         () => api.get('/seller/stats/'),
  products:      () => api.get('/seller/products/'),
  addProduct:    d => api.post('/seller/products/add/', d),
  updateProduct: (id, d) => api.patch(`/seller/products/${id}/`, d),
  deleteProduct: id => api.delete(`/seller/products/${id}/`),
  orders:        () => api.get('/seller/orders/'),
  orderAction:   (id, d) => api.patch(`/seller/orders/${id}/action/`, d),
}

// ── Utility ───────────────────────────────────────────────────
export const utilAPI = {
  pincode: pin => api.get('/pincode/', { params: { pincode: pin } }),
}
