import { useState } from 'react'
import { ChevronDownIcon } from './icons.jsx'

// Placeholder for runtime generation: the intended interface, and nothing behind it.
// It never calls the backend. POST /generate exists in tools/classify_api.py but answers
// 503 until ENABLE_RUNTIME_GENERATION and ANTHROPIC_API_KEY are set, and this page does
// not send it either way. The disabled button is the point, not a stand-in for a
// working flow.

const QUALITIES = [
  { value: 'preview', label: 'Preview · 480p' },
  { value: 'full', label: 'Full · 1080p' },
]

// The stages a real run would pass through, in order. Static on purpose: the first is
// shown complete and the rest pending, to make the shape of the pipeline visible.
const STAGES = [
  'Writing brief',
  'Writing narration',
  'Synthesising audio',
  'Generating scene',
  'Running checks',
  'Rendering',
  'Muxing',
]

export function Generate({ hidden }) {
  const [topic, setTopic] = useState('')
  const [quality, setQuality] = useState('preview')
  const [brief, setBrief] = useState('')

  return (
    <main className="generate" hidden={hidden}>
      <div className="generate-body">
        <div className="generate-heading">
          <p className="eyebrow">Runtime generation</p>
          <h1 className="title">Generate a topic</h1>
          <p className="generate-lede">
            Name a topic, and the pipeline would write, voice, check and render a new narrated video.
          </p>
        </div>

        <form className="generate-form" onSubmit={(e) => e.preventDefault()}>
          <div className="field">
            <label className="field-label" htmlFor="gen-topic">
              Topic name
            </label>
            <div className="line-field">
              <input
                id="gen-topic"
                className="line-input"
                type="text"
                required
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. merge sort"
                autoComplete="off"
                spellCheck="false"
              />
              <span className="ask-line" aria-hidden="true" />
            </div>
          </div>

          <div className="field">
            <label className="field-label" htmlFor="gen-quality">
              Quality
            </label>
            <div className="line-field">
              <select
                id="gen-quality"
                className="line-input line-select"
                value={quality}
                onChange={(e) => setQuality(e.target.value)}
              >
                {QUALITIES.map((q) => (
                  <option key={q.value} value={q.value}>
                    {q.label}
                  </option>
                ))}
              </select>
              <ChevronDownIcon className="select-chevron" />
              <span className="ask-line" aria-hidden="true" />
            </div>
          </div>

          <div className="field">
            <label className="field-label" htmlFor="gen-brief">
              Visual brief <span className="field-optional">optional</span>
            </label>
            <textarea
              id="gen-brief"
              className="brief-input"
              rows={5}
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              placeholder="Leave this blank and the brief is generated from the topic name: the input values, what is drawn and how it moves, and the key teaching moment."
            />
          </div>

          <div className="generate-action">
            <button type="submit" className="generate-button" disabled aria-describedby="gen-disabled">
              Generate
            </button>
            <p id="gen-disabled" className="generate-helper">
              Runtime generation requires an API key — currently disabled. See <code>tools/generate_animation.py</code>.
            </p>
          </div>
        </form>

        <section className="pipeline" aria-labelledby="pipeline-heading">
          <h2 id="pipeline-heading" className="pipeline-heading">
            Example progress · not a live run
          </h2>
          <ol className="pipeline-steps">
            {STAGES.map((stage, i) => {
              const state = i === 0 ? 'complete' : 'pending'
              return (
                <li key={stage} className="pipeline-step" data-state={state}>
                  <span className="pipeline-mark" aria-hidden="true" />
                  <span className="pipeline-name">{stage}</span>
                  <span className="pipeline-state">{state === 'complete' ? 'Complete' : 'Pending'}</span>
                </li>
              )
            })}
          </ol>
          <p className="pipeline-note">Generation takes about 7 minutes at preview quality.</p>
        </section>
      </div>
    </main>
  )
}
