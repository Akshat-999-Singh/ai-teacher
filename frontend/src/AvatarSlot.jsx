// Reserved for the avatar. It receives the active narration segment
// ({ id, text, start, end, beat }) and whether that segment is being spoken right now.
export function AvatarSlot({ segment, speaking }) {
  return (
    <div
      className="avatar-slot"
      aria-hidden="true"
      data-segment-id={segment?.id ?? ''}
      data-beat={segment?.beat ?? ''}
      data-speaking={speaking}
    />
  )
}
