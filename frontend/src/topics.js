// `category` is the classifier's label; each category has exactly one rendered topic.
export const TOPICS = [
  { id: 'bubble_sort', category: 'sorting', title: 'Bubble sort', subject: 'Sorting' },
  { id: 'binary_search', category: 'searching', title: 'Binary search', subject: 'Searching' },
  { id: 'kadane', category: 'dynamic_programming', title: 'Kadane’s algorithm', subject: 'Dynamic programming' },
  { id: 'valid_parentheses', category: 'stack', title: 'Valid parentheses', subject: 'Stack' },
  { id: 'euclidean_gcd', category: 'math', title: 'Euclidean GCD', subject: 'Math' },
  { id: 'projectile_motion', category: 'physics', title: 'Projectile motion', subject: 'Physics' },
]

export const topicById = (id) => TOPICS.find((t) => t.id === id)
export const topicByCategory = (category) => TOPICS.find((t) => t.category === category)
export const videoUrl = (id) => `/media/rendered/${id}.mp4`
export const scriptUrl = (id) => `/media/scripts/${id}.json`
