import { topicById } from './topics.js'

// What the classifier made of the last question: the query, its predicted category,
// and the topic that category retrieved.
export function Readout({ result }) {
  return (
    <div className="readout" aria-live="polite">
      {result && (
        <div className="readout-inner" key={result.seq}>
          <p className="readout-query">“{result.query}”</p>
          <p className="readout-result">
            {result.category ? (
              <>
                <span className="readout-label">Category</span>
                <span className="readout-value">{result.category}</span>
                <span className="readout-label">Topic</span>
                <span className="readout-value readout-topic">{topicById(result.topicId).title}</span>
              </>
            ) : (
              'No category matched'
            )}
          </p>
        </div>
      )}
    </div>
  )
}
