import { PauseIcon, PlayIcon } from './icons.jsx'

function formatTime(seconds) {
  const s = Math.max(0, Math.floor(seconds))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

export function Transport({ clock, videoRef, onToggle, segmentIndex, segmentCount }) {
  const { currentTime, duration, paused } = clock
  const progress = duration > 0 ? Math.min(currentTime / duration, 1) : 0

  return (
    <div className="transport">
      <button
        type="button"
        className="transport-toggle"
        data-paused={paused}
        aria-label={paused ? 'Play' : 'Pause'}
        onClick={onToggle}
      >
        {paused ? <PlayIcon /> : <PauseIcon />}
      </button>
      <span className="transport-time">{formatTime(currentTime)}</span>
      <div className="scrub">
        <div className="scrub-track" />
        <div className="scrub-fill" style={{ transform: `scaleX(${progress})` }} />
        <input
          type="range"
          className="scrub-input"
          min={0}
          max={duration}
          step="any"
          value={Math.min(currentTime, duration)}
          disabled={!duration}
          aria-label="Seek"
          aria-valuetext={`${formatTime(currentTime)} of ${formatTime(duration)}`}
          onChange={(e) => {
            videoRef.current.currentTime = Number(e.target.value)
          }}
        />
      </div>
      <span className="transport-time">{formatTime(duration)}</span>
      <span className="transport-segment" title="Narration segment">
        {segmentCount > 0 ? `${segmentIndex + 1} / ${segmentCount}` : ''}
      </span>
    </div>
  )
}
