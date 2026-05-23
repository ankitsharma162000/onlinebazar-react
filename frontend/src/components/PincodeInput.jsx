import { useState, useRef } from 'react'
import { MapPin } from 'lucide-react'

export default function PincodeInput({ value, onChange, onAreaFound, className = '' }) {
  const [info, setInfo] = useState(null)
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(false)
  const timer = useRef(null)

  const handleChange = (e) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 6)
    onChange(val)
    setInfo(null); setError(false)
    clearTimeout(timer.current)
    if (val.length === 6) {
      timer.current = setTimeout(() => lookup(val), 600)
    }
  }

  const lookup = async (pin) => {
    setLoading(true)
    try {
      const r = await fetch(`https://api.postalpincode.in/pincode/${pin}`)
      const data = await r.json()
      if (data?.[0]?.Status === 'Success') {
        const post = data[0].PostOffice[0]
        setInfo(`${post.Name}, ${post.District}, ${post.State}`)
        setError(false)
        onAreaFound?.({ district: post.District, state: post.State, area: post.Name })
      } else {
        setError(true)
        onAreaFound?.({ district: '', state: '', area: '' })
      }
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <input
        type="text"
        value={value}
        onChange={handleChange}
        maxLength={6}
        placeholder="6-digit pincode"
        className={`input ${className}`}
        autoComplete="off"
      />
      {loading && <p className="text-xs text-gray-400 mt-1">Looking up pincode...</p>}
      {info && !loading && (
        <p className="text-xs text-green-600 mt-1 flex items-center gap-1">
          <MapPin size={12} /> {info}
        </p>
      )}
      {error && !loading && (
        <p className="text-xs text-red-500 mt-1">⚠ Pincode not found. Please check.</p>
      )}
    </div>
  )
}
