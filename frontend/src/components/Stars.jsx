export function Stars({ value, size = 18 }) {
  return (
    <span className="stars" role="img" aria-label={`Оценка ${value.toFixed(1)} от 5`} style={{ fontSize: size }}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={n <= Math.round(value) ? 'on' : ''}>★</span>
      ))}
    </span>
  )
}

export function StarInput({ value, onChange }) {
  return (
    <fieldset className="star-input">
      <legend>Вашата оценка</legend>
      {[1, 2, 3, 4, 5].map((n) => (
        <label key={n} className={n <= value ? 'on' : ''}>
          <input type="radio" name="rating" value={n} checked={value === n} onChange={() => onChange(n)} />
          <span aria-hidden="true">★</span>
          <span className="sr">{n} от 5</span>
        </label>
      ))}
    </fieldset>
  )
}
