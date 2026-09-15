import { useState } from 'react'

export function Ask({ onAsk }) {
  const [query, setQuery] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    const text = query.trim()
    if (text) onAsk(text)
  }

  return (
    <form className="ask" role="search" onSubmit={handleSubmit}>
      <label className="visually-hidden" htmlFor="ask-input">
        Ask about a problem
      </label>
      <div className="ask-field">
        <input
          id="ask-input"
          className="ask-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about a problem…"
          autoComplete="off"
          spellCheck="false"
          enterKeyHint="search"
        />
        <span className="ask-line" aria-hidden="true" />
      </div>
    </form>
  )
}
