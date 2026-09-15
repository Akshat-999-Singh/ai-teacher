import { useEffect, useState } from 'react'
import { scriptUrl } from './topics.js'

const NO_SEGMENTS = []

// Index of the last segment that has started by time t; -1 before the first.
// Segments are sorted by start, so this is a binary search.
export function segmentIndexAt(segments, t) {
  let lo = 0
  let hi = segments.length - 1
  let found = -1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    if (segments[mid].start <= t) {
      found = mid
      lo = mid + 1
    } else {
      hi = mid - 1
    }
  }
  return found
}

// The <video> element is the only clock. Everything time-dependent derives from this.
export function useVideoClock(videoRef) {
  const [clock, setClock] = useState({ currentTime: 0, duration: 0, paused: true, ended: false })

  useEffect(() => {
    const video = videoRef.current
    const sync = () =>
      setClock({
        currentTime: video.currentTime,
        duration: Number.isFinite(video.duration) ? video.duration : 0,
        paused: video.paused,
        ended: video.ended,
      })
    // 'seeking' updates the scrub position immediately rather than on the next timeupdate.
    const events = ['timeupdate', 'seeking', 'seeked', 'play', 'pause', 'ended', 'durationchange', 'emptied']
    events.forEach((e) => video.addEventListener(e, sync))
    sync()
    return () => events.forEach((e) => video.removeEventListener(e, sync))
  }, [videoRef])

  return clock
}

export function useScript(topic) {
  const [loaded, setLoaded] = useState({ topic: null, segments: NO_SEGMENTS })

  useEffect(() => {
    if (!topic) return // the topic list has not arrived, or is empty
    const controller = new AbortController()
    fetch(scriptUrl(topic), { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${scriptUrl(topic)}`)
        return res.json()
      })
      .then((segments) => setLoaded({ topic, segments }))
      .catch((err) => {
        if (err.name === 'AbortError') return
        console.error('narration script failed to load:', err)
        setLoaded({ topic, segments: NO_SEGMENTS })
      })
    return () => controller.abort()
  }, [topic])

  // Never map the new video's clock against the previous topic's segments.
  return loaded.topic === topic ? loaded.segments : NO_SEGMENTS
}

// currentSegment stays on the last-started segment through the short silences
// between segments; `speaking` is true only inside [start, end].
export function useNarration(segments, currentTime) {
  const index = segmentIndexAt(segments, currentTime)
  const currentSegment = index >= 0 ? segments[index] : null
  return {
    currentSegment,
    index,
    speaking: currentSegment !== null && currentTime <= currentSegment.end,
  }
}
