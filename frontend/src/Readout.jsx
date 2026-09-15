const percent = (score) => `${Math.round(score * 100)}%`

// What the classifier made of the last question. At most three single lines, so the
// video below never moves when a result arrives.
export function Readout({ result, titleOf, onPickTopic }) {
  return (
    <div className="readout" aria-live="polite">
      {result && (
        <div className="readout-inner" key={result.seq}>
          {result.unavailable ? (
            <>
              <p className="readout-query">“{result.query}”</p>
              <p className="readout-main">The classifier isn’t reachable. Choose a topic from the list.</p>
            </>
          ) : (
            <Classified result={result} titleOf={titleOf} onPickTopic={onPickTopic} />
          )}
        </div>
      )}
    </div>
  )
}

function Classified({ result, titleOf, onPickTopic }) {
  const [best, runnerUp] = result.candidates
  const named = (id) => (id ? titleOf(id) : 'none rendered yet')
  return (
    <>
      {result.low_confidence ? (
        <p className="readout-note">
          There’s no explanation for “<span className="readout-q">{result.query}</span>” yet.
        </p>
      ) : (
        <p className="readout-query">“{result.query}”</p>
      )}

      <p className="readout-main">
        {result.low_confidence ? (
          <>
            <span className="readout-label">Closest available topic</span>
            <span className="readout-topic">{named(result.topic)}</span>
          </>
        ) : (
          <>
            <span className="readout-label">Category</span>
            <span className="readout-value">
              {best.category} <span className="readout-score">{percent(best.score)}</span>
            </span>
            <span className="readout-label">Topic</span>
            <span className="readout-topic">{named(result.topic)}</span>
          </>
        )}
      </p>

      <p className="readout-alt">
        {result.low_confidence && `best guess ${best.category} ${percent(best.score)} · `}
        {runnerUp && (
          <>
            runner-up {runnerUp.category} {percent(runnerUp.score)}
            {runnerUp.topic && (
              <>
                {', '}
                <button type="button" className="readout-link" onClick={() => onPickTopic(runnerUp.topic)}>
                  {named(runnerUp.topic)}
                </button>
              </>
            )}
          </>
        )}
      </p>
    </>
  )
}
