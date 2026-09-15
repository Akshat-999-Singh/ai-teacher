// The topic -> category map lives in the classifier service (tools/classify_api.py).
export const TOPICS = [
  { id: 'bubble_sort', title: 'Bubble sort', subject: 'Sorting' },
  { id: 'binary_search', title: 'Binary search', subject: 'Searching' },
  { id: 'kadane', title: 'Kadane’s algorithm', subject: 'Dynamic programming' },
  { id: 'valid_parentheses', title: 'Valid parentheses', subject: 'Stack' },
  { id: 'euclidean_gcd', title: 'Euclidean GCD', subject: 'Math' },
  { id: 'projectile_motion', title: 'Projectile motion', subject: 'Physics' },
]

export const topicById = (id) => TOPICS.find((t) => t.id === id)
export const videoUrl = (id) => `/media/rendered/${id}.mp4`
export const scriptUrl = (id) => `/media/scripts/${id}.json`
