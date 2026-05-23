export function Spinner({ size = 8 }) {
  return (
    <div className="flex justify-center items-center py-12">
      <div className={`w-${size} h-${size} border-4 border-primary border-t-transparent rounded-full animate-spin`} />
    </div>
  )
}

export function Empty({ icon = '📭', message = 'Nothing here yet' }) {
  return (
    <div className="text-center py-16 text-gray-400">
      <div className="text-5xl mb-3">{icon}</div>
      <p className="text-lg">{message}</p>
    </div>
  )
}

export function StockBadge({ badge }) {
  if (!badge) return null
  const cls = badge.color === 'danger' ? 'badge-danger' :
              badge.color === 'warning' ? 'badge-warning' : 'badge-success'
  return <span className={cls}>{badge.label}</span>
}

export function StarRating({ rating, count }) {
  return (
    <div className="flex items-center gap-1">
      <div className="flex">
        {[1,2,3,4,5].map(s => (
          <span key={s} className={s <= Math.round(rating) ? 'text-yellow-400' : 'text-gray-200'}>★</span>
        ))}
      </div>
      {count !== undefined && <span className="text-sm text-gray-500">({count})</span>}
    </div>
  )
}

export function TrackingBar({ steps }) {
  return (
    <div className="flex items-center gap-0 w-full">
      {steps.map(({ step, done }, i) => (
        <div key={step} className="flex items-center flex-1">
          <div className="flex flex-col items-center flex-1">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2
              ${done ? 'bg-green-500 border-green-500 text-white' : 'bg-white border-gray-300 text-gray-400'}`}>
              {done ? '✓' : i + 1}
            </div>
            <span className={`text-xs mt-1 text-center leading-tight ${done ? 'text-green-600 font-medium' : 'text-gray-400'}`}>
              {step}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div className={`h-1 flex-1 -mt-5 ${done && steps[i+1]?.done ? 'bg-green-500' : 'bg-gray-200'}`} />
          )}
        </div>
      ))}
    </div>
  )
}
