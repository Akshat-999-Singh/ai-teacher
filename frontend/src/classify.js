// Stand-in for the trained classifier (models/classifier.pkl), with the contract the
// real one will keep: free text in, one of its six category labels or null out, async.
const KEYWORDS = {
  sorting: ['sort', 'swap', 'bubble', 'ascending', 'descending'],
  searching: ['search', 'binary', 'target', 'sorted array', 'log n'],
  dynamic_programming: ['kadane', 'subarray', 'contiguous', 'maximum sum', 'subsequence'],
  stack: ['parenthes', 'bracket', 'balanced', 'stack'],
  math: ['gcd', 'divisor', 'euclid', 'common factor', 'prime'],
  physics: ['projectile', 'velocity', 'thrown', 'launch', 'trajectory', 'gravity'],
}

export async function classify(query) {
  const q = query.toLowerCase()
  let best = null
  let bestHits = 0
  for (const [category, words] of Object.entries(KEYWORDS)) {
    const hits = words.filter((w) => q.includes(w)).length
    if (hits > bestHits) {
      best = category
      bestHits = hits
    }
  }
  return best
}
