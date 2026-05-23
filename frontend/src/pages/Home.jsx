import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { productAPI } from '../api/client'
import ProductCard from '../components/ProductCard'
import { Spinner, Empty } from '../components/UI'
import { ChevronLeft, ChevronRight, SlidersHorizontal } from 'lucide-react'

const CATEGORIES = [
  { value: '', label: '🏪 All', icon: '' },
  { value: 'Electronics', label: '📱 Electronics' },
  { value: 'Clothing', label: '👗 Clothing' },
  { value: 'Food', label: '🍎 Food' },
  { value: 'Beauty', label: '💄 Beauty' },
  { value: 'Sports', label: '⚽ Sports' },
  { value: 'Home', label: '🏠 Home' },
  { value: 'Books', label: '📚 Books' },
  { value: 'Toys', label: '🧸 Toys' },
  { value: 'Health', label: '💊 Health' },
]

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [products, setProducts]   = useState([])
  const [featured, setFeatured]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [page, setPage]           = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [showFilters, setShowFilters] = useState(false)

  const q        = searchParams.get('q') || ''
  const category = searchParams.get('category') || ''
  const sort     = searchParams.get('sort') || 'newest'
  const minPrice = searchParams.get('min_price') || ''
  const maxPrice = searchParams.get('max_price') || ''

  useEffect(() => {
    setPage(1)
  }, [q, category, sort, minPrice, maxPrice])

  useEffect(() => {
    fetchProducts()
  }, [q, category, sort, minPrice, maxPrice, page])

  useEffect(() => {
    productAPI.featured().then(r => setFeatured(r.data)).catch(() => {})
  }, [])

  const fetchProducts = async () => {
    setLoading(true)
    try {
      const r = await productAPI.list({ q, category, sort, min_price: minPrice, max_price: maxPrice, page })
      setProducts(r.data.results)
      setTotalPages(r.data.num_pages)
    } catch { setProducts([]) }
    finally { setLoading(false) }
  }

  const setParam = (key, val) => {
    const p = new URLSearchParams(searchParams)
    if (val) p.set(key, val); else p.delete(key)
    setSearchParams(p)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Banner */}
      {!q && !category && (
        <div className="bg-gradient-to-r from-primary to-blue-700 text-white py-10 px-4">
          <div className="max-w-7xl mx-auto text-center">
            <h1 className="text-3xl md:text-4xl font-bold mb-2">Welcome to OnlineBazar 🛒</h1>
            <p className="text-blue-100 text-lg mb-6">India's Growing Marketplace</p>
            <div className="flex flex-wrap justify-center gap-3">
              {CATEGORIES.filter(c => c.value).slice(0, 5).map(c => (
                <button key={c.value} onClick={() => setParam('category', c.value)}
                  className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-full text-sm font-medium transition-colors">
                  {c.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Featured carousel — only on homepage */}
        {!q && !category && featured.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-800 mb-4">🔥 Featured Products</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {featured.slice(0, 4).map(p => <ProductCard key={p.product_id} product={p} />)}
            </div>
          </div>
        )}

        {/* Category pills */}
        <div className="flex gap-2 overflow-x-auto pb-2 mb-4 scrollbar-hide">
          {CATEGORIES.map(c => (
            <button key={c.value}
              onClick={() => setParam('category', c.value)}
              className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-medium border transition-colors
                ${category === c.value
                  ? 'bg-primary text-white border-primary'
                  : 'bg-white text-gray-700 border-gray-200 hover:border-primary hover:text-primary'}`}>
              {c.label}
            </button>
          ))}
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between mb-4 gap-3">
          <div>
            <h2 className="font-bold text-gray-800 text-lg">
              {q ? `Results for "${q}"` : category || 'All Products'}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-1 text-sm border border-gray-200 rounded px-3 py-1.5 hover:border-primary text-gray-600">
              <SlidersHorizontal size={15} /> Filters
            </button>
            <select value={sort} onChange={e => setParam('sort', e.target.value)}
              className="text-sm border border-gray-200 rounded px-2 py-1.5 text-gray-600 focus:outline-none focus:border-primary">
              <option value="newest">Newest</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="name">Name A–Z</option>
            </select>
          </div>
        </div>

        {/* Filters panel */}
        {showFilters && (
          <div className="bg-white rounded-lg shadow p-4 mb-4 flex flex-wrap gap-4">
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Min Price (₹)</label>
              <input type="number" value={minPrice} onChange={e => setParam('min_price', e.target.value)}
                className="input w-32" placeholder="0" />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 block mb-1">Max Price (₹)</label>
              <input type="number" value={maxPrice} onChange={e => setParam('max_price', e.target.value)}
                className="input w-32" placeholder="99999" />
            </div>
            <div className="flex items-end">
              <button onClick={() => { setParam('min_price',''); setParam('max_price','') }}
                className="text-sm text-red-500 hover:underline">Clear</button>
            </div>
          </div>
        )}

        {/* Products grid */}
        {loading ? <Spinner /> : products.length === 0 ? (
          <Empty icon="🔍" message="No products found. Try a different search." />
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {products.map(p => <ProductCard key={p.product_id} product={p} />)}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center items-center gap-2 mt-8">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                  className="p-2 rounded border border-gray-200 hover:border-primary disabled:opacity-40">
                  <ChevronLeft size={18} />
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(n => (
                  <button key={n} onClick={() => setPage(n)}
                    className={`w-9 h-9 rounded border font-medium text-sm transition-colors
                      ${page === n ? 'bg-primary text-white border-primary' : 'border-gray-200 hover:border-primary text-gray-700'}`}>
                    {n}
                  </button>
                ))}
                <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                  className="p-2 rounded border border-gray-200 hover:border-primary disabled:opacity-40">
                  <ChevronRight size={18} />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
