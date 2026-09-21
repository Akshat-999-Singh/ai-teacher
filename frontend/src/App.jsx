import { useEffect, useRef, useState } from 'react'
import { Ask } from './Ask.jsx'
import { AvatarSlot } from './AvatarSlot.jsx'
import { classify } from './classify.js'
import { Generate } from './Generate.jsx'
import { PlayIcon } from './icons.jsx'
import { useNarration, useScript, useVideoClock } from './narration.js'
import { Readout } from './Readout.jsx'
import { subjectOf, useTopics, videoUrl } from './topics.js'
import { Transport } from './Transport.jsx'

const BLANK = ' ' // keeps the heading's height while the topic list loads

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
  const topicsRef = useRef(null)
  const { topics, failed } = useTopics()
  const [pickedId, setPickedId] = useState(null)
  const [classification, setClassification] = useState(null)
  const [view, setView] = useState('watch') // 'watch' | 'generate'; no router, just a toggle

  // The picked topic while it is listed, otherwise the first one.
  const topic = topics?.find((t) => t.id === pickedId) ?? topics?.[0] ?? null
  const topicId = topic?.id ?? null
  const isListed = (id) => topics?.some((t) => t.id === id) ?? false
  const titleOf = (id) => topics?.find((t) => t.id === id)?.title ?? id

  const clock = useVideoClock(videoRef)
  const segments = useScript(topicId)
  const { currentSegment, index, speaking } = useNarration(segments, clock.currentTime)

  // Only at the start and the end: a mid-video pause leaves the frame unobstructed. Shown
  // while the list loads too, so it is there from the first paint instead of fading in.
  const showPlayOverlay = topics?.length !== 0 && clock.paused && (clock.ended || clock.currentTime < 0.05)

  useEffect(() => {
    if (playOnLoad.current && topicId) play(videoRef.current)
  }, [topicId])

  // Keep the playing topic visible when the list scrolls (a question can pick one that is
  // scrolled out of view). Moves the list only: scrollIntoView would also scroll the page.
  useEffect(() => {
    const list = topicsRef.current
    const item = list?.querySelector('[aria-current="true"]')
    if (!item) return
    const box = list.getBoundingClientRect()
    const row = item.getBoundingClientRect()
    if (row.top < box.top) list.scrollTop -= box.top - row.top
    else if (row.bottom > box.bottom) list.scrollTop += row.bottom - box.bottom
  }, [topicId, topics])

  function showTopic(id, autoplay = true) {
    playOnLoad.current = autoplay
    if (id !== topicId) setPickedId(id)
    else if (autoplay) play(videoRef.current)
  }

  // Both views stay mounted and the other one is hidden: the video clock binds to its
  // element once, and the Generate fields keep what was typed. A hidden video still
  // plays its audio, so leaving Watch pauses it.
  function showView(next) {
    if (next !== 'watch') videoRef.current.pause()
    setView(next)
  }

  async function handleAsk(query) {
    showView('watch') // the answer is a video, so a question always lands on Watch
    const seq = ++askSeq.current
    let result
    try {
      result = await classify(query)
    } catch (err) {
      if (seq !== askSeq.current) return
      console.warn('classifier unavailable:', err)
      setClassification({ seq, query, unavailable: true })
      return
    }
    if (seq !== askSeq.current) return // superseded by a newer question or a manual pick
    setClassification({ seq, query, ...result })
    // A low-confidence match is only the closest topic: show it, but don't start narrating.
    if (result.topic && isListed(result.topic)) showTopic(result.topic, !result.low_confidence)
  }

  function pickTopic(id) {
    askSeq.current++
    setClassification(null)
    showTopic(id)
  }

  function togglePlay() {
    const video = videoRef.current
    if (!topic) return
    if (video.paused) play(video)
    else video.pause()
  }

  const emptyTitle = topics === null ? BLANK : failed ? 'Topic list unavailable' : 'No topics rendered yet'

  return (
    <div className="page">
      <header className="masthead">
        <div className="masthead-start">
          <p className="wordmark">AI Teacher</p>
          <nav className="views" aria-label="Views">
            {[
              ['watch', 'Watch'],
              ['generate', 'Generate'],
            ].map(([id, label]) => (
              <button
                key={id}
                type="button"
                className="view"
                aria-current={view === id ? 'page' : undefined}
                onClick={() => showView(id)}
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
        <Ask onAsk={handleAsk} />
      </header>

      <main className="stage" hidden={view !== 'watch'}>
        <div className="stage-heading">
          <div className="heading-text">
            <p className="eyebrow">{topic ? subjectOf(topic.category) : BLANK}</p>
            <h1 className="title">{topic ? topic.title : emptyTitle}</h1>
          </div>
          <Readout result={classification} titleOf={titleOf} onPickTopic={pickTopic} />
        </div>

        <div className="frame">
          <video
            ref={videoRef}
            className="video"
            src={topicId ? videoUrl(topicId) : undefined}
            preload="auto"
            playsInline
            onClick={togglePlay}
          />
          <button
            type="button"
            className="play-overlay"
            data-visible={showPlayOverlay}
            tabIndex={showPlayOverlay ? 0 : -1}
            aria-label={topic ? `Play ${topic.title}` : 'Play'}
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
          {/* `speaking` only means the clock sits inside a segment, so a paused video
              would leave the mouth moving with no narration. */}
          <AvatarSlot segment={currentSegment} speaking={speaking && !clock.paused} />
          <nav className="topics" aria-label="Topics" ref={topicsRef}>
            <ul>
              {topics?.map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    className="topic"
                    aria-current={t.id === topicId ? 'true' : undefined}
                    onClick={() => pickTopic(t.id)}
                  >
                    <span className="topic-subject">{subjectOf(t.category)}</span>
                    <span className="topic-title">{t.title}</span>
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </aside>
      </main>

      <Generate hidden={view !== 'generate'} />
    </div>
  )
}
