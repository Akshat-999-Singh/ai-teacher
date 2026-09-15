import { useEffect, useRef, useState } from 'react'
import { Ask } from './Ask.jsx'
import { AvatarSlot } from './AvatarSlot.jsx'
import { classify } from './classify.js'
import { PlayIcon } from './icons.jsx'
import { useNarration, useScript, useVideoClock } from './narration.js'
import { Readout } from './Readout.jsx'
import { TOPICS, topicByCategory, topicById, videoUrl } from './topics.js'
import { Transport } from './Transport.jsx'

function play(video) {
  // A newer src or a pause interrupting play() rejects with AbortError; that's expected.
  video.play().catch((err) => {
    if (err.name !== 'AbortError') console.error('video playback failed:', err)
  })
}

export default function App() {
  const videoRef = useRef(null)
  const playOnLoad = useRef(false)
  const askSeq = useRef(0)
  const [topicId, setTopicId] = useState(TOPICS[0].id)
  const [classification, setClassification] = useState(null)

  const clock = useVideoClock(videoRef)
  const segments = useScript(topicId)
  const { currentSegment, index, speaking } = useNarration(segments, clock.currentTime)
  const topic = topicById(topicId)

  // Only at the start and the end: a mid-video pause leaves the frame unobstructed.
  const showPlayOverlay = clock.paused && (clock.ended || clock.currentTime < 0.05)

  useEffect(() => {
    if (playOnLoad.current) play(videoRef.current)
  }, [topicId])

  function showTopic(id) {
    playOnLoad.current = true
    if (id === topicId) play(videoRef.current)
    else setTopicId(id)
  }

  async function handleAsk(query) {
    const seq = ++askSeq.current
    const category = await classify(query)
    if (seq !== askSeq.current) return // superseded by a newer question or a manual pick
    const matched = category ? topicByCategory(category) : null
    setClassification({ seq, query, category, topicId: matched?.id ?? null })
    if (matched) showTopic(matched.id)
  }

  function pickTopic(id) {
    askSeq.current++
    setClassification(null)
    showTopic(id)
  }

  function togglePlay() {
    const video = videoRef.current
    if (video.paused) play(video)
    else video.pause()
  }

  return (
    <div className="page">
      <header className="masthead">
        <p className="wordmark">AI Teacher</p>
        <Ask onAsk={handleAsk} />
      </header>

      <main className="stage">
        <div className="stage-heading">
          <div className="heading-text">
            <p className="eyebrow">{topic.subject}</p>
            <h1 className="title">{topic.title}</h1>
          </div>
          <Readout result={classification} />
        </div>

        <div className="frame">
          <video
            ref={videoRef}
            className="video"
            src={videoUrl(topicId)}
            preload="auto"
            playsInline
            onClick={togglePlay}
          />
          <button
            type="button"
            className="play-overlay"
            data-visible={showPlayOverlay}
            tabIndex={showPlayOverlay ? 0 : -1}
            aria-label={`Play ${topic.title}`}
            onClick={togglePlay}
          >
            <PlayIcon />
          </button>
        </div>

        <Transport
          clock={clock}
          videoRef={videoRef}
          onToggle={togglePlay}
          segmentIndex={index}
          segmentCount={segments.length}
        />

        <aside className="sidebar">
          <AvatarSlot segment={currentSegment} speaking={speaking} />
          <nav className="topics" aria-label="Topics">
            <ul>
              {TOPICS.map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    className="topic"
                    aria-current={t.id === topicId ? 'true' : undefined}
                    onClick={() => pickTopic(t.id)}
                  >
                    <span className="topic-subject">{t.subject}</span>
                    <span className="topic-title">{t.title}</span>
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </aside>
      </main>
    </div>
  )
}
