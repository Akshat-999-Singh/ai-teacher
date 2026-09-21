import { useEffect, useRef, useState } from 'react'

// The avatar. It receives the active narration segment ({ id, text, start, end, beat })
// and whether that segment is being spoken right now. It makes no sound: the narration
// is already in the video.
//
// The 3D model (public/avatar.glb, driven by avatar3d.js) is the avatar. The 2D portrait
// is the fallback when WebGL2 is unavailable or the model fails to load. three.js is
// imported on demand, so it never delays the page.

const MODEL = '/avatar.glb'

function hasWebGL2() {
  try {
    return Boolean(document.createElement('canvas').getContext('webgl2'))
  } catch {
    return false
  }
}

export function AvatarSlot({ segment, speaking }) {
  // 'loading' -> '3d', or '2d' when WebGL2 is missing or the model fails.
  const [mode, setMode] = useState(() => (hasWebGL2() ? 'loading' : '2d'))

  return (
    <div
      className="avatar-slot"
      aria-hidden="true"
      data-segment-id={segment?.id ?? ''}
      data-beat={segment?.beat ?? ''}
      data-speaking={speaking}
      data-avatar={mode}
    >
      {mode === '2d' ? (
        <Portrait speaking={speaking} />
      ) : (
        <Model speaking={speaking} onReady={() => setMode('3d')} onFail={() => setMode('2d')} />
      )}
    </div>
  )
}

function Model({ speaking, onReady, onFail }) {
  const hostRef = useRef(null)
  const avatarRef = useRef(null)
  const speakingRef = useRef(speaking)

  useEffect(() => {
    speakingRef.current = speaking
    avatarRef.current?.setSpeaking(speaking)
  }, [speaking])

  // Mount once. A fresh canvas per mount: StrictMode mounts twice in development, and a
  // canvas whose renderer was disposed must not be handed to a new one.
  useEffect(() => {
    const host = hostRef.current
    const canvas = document.createElement('canvas')
    canvas.className = 'avatar-canvas'
    host.appendChild(canvas)
    let cancelled = false

    const fail = (err) => {
      if (cancelled) return
      console.warn('3D avatar unavailable, showing the 2D portrait:', err)
      onFail()
    }

    import('./avatar3d.js')
      .then(({ createAvatar }) => {
        if (cancelled) return
        const avatar = createAvatar(canvas, MODEL, {
          onReady: () => {
            if (cancelled) return
            canvas.dataset.ready = 'true'
            onReady()
          },
          onError: fail,
        })
        avatar.setSpeaking(speakingRef.current)
        avatarRef.current = avatar
        if (import.meta.env.DEV) host.__avatar = avatar.debug
      })
      .catch(fail)

    return () => {
      cancelled = true
      avatarRef.current?.dispose()
      avatarRef.current = null
      canvas.remove()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps -- mount once; the callbacks only set state

  return <div className="avatar-host" ref={hostRef} />
}

// The 2D fallback: both frames in the DOM from the start, one hidden, so a swap never
// waits on a download and never flashes. Only the mouth differs between them.
const CLOSED = '/avatar-closed.svg'
const OPEN = '/avatar-open.svg'

// 6-8 swaps a second, redrawn each time so the mouth does not tick like a metronome.
const SWAP_MIN_MS = 125
const SWAP_MAX_MS = 166

function Portrait({ speaking }) {
  const [mouthOpen, setMouthOpen] = useState(false)

  useEffect(() => {
    if (!speaking) {
      setMouthOpen(false) // hold the closed frame between sentences
      return
    }
    let timer
    const swap = () => {
      setMouthOpen((open) => !open)
      timer = setTimeout(swap, SWAP_MIN_MS + Math.random() * (SWAP_MAX_MS - SWAP_MIN_MS))
    }
    swap()
    return () => clearTimeout(timer)
  }, [speaking])

  return (
    <div className="avatar-figure" data-mouth={mouthOpen ? 'open' : 'closed'}>
      <img className="avatar-frame" src={CLOSED} alt="" hidden={mouthOpen} />
      <img className="avatar-frame" src={OPEN} alt="" hidden={!mouthOpen} />
    </div>
  )
}
