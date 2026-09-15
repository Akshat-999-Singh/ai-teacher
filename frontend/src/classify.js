// The classifier service (tools/classify_api.py), proxied by Vite at /api. Resolves to
// { category, confidence, topic, low_confidence, candidates: [{ category, score, topic }] }.
export async function classify(text) {
  const res = await fetch('/api/classify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
    signal: AbortSignal.timeout(10000),
  })
  if (!res.ok) throw new Error(`classifier responded ${res.status}`)
  return res.json()
}
