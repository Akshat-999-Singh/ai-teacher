import { useEffect, useState } from 'react'

// Nothing here names a topic. The list is rendered/manifest.json, which
// tools/render_topic.py writes when it publishes a video; vite.config.js serves it,
// minus entries whose files are gone, as [{ id, title, category }].
const TOPICS_URL = '/media/topics.json'

// topics is null until the list arrives; failed means it never will on this load.
export function useTopics() {
  const [state, setState] = useState({ topics: null, failed: false })

  useEffect(() => {
    const controller = new AbortController()
    fetch(TOPICS_URL, { signal: controller.signal, cache: 'no-store' })
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${TOPICS_URL}`)
        return res.json()
      })
      .then((topics) => setState({ topics, failed: false }))
      .catch((err) => {
        if (err.name === 'AbortError') return
        console.error('topic list failed to load:', err)
        setState({ topics: [], failed: true })
      })
    return () => controller.abort()
  }, [])

  return state
}

// The classifier's label, readable: 'dynamic_programming' -> 'Dynamic programming'.
export function subjectOf(category) {
  const words = category.replaceAll('_', ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

export const videoUrl = (id) => `/media/rendered/${id}.mp4`
export const scriptUrl = (id) => `/media/scripts/${id}.json`
