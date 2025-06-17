// a live‐binding export of your current word pool
export let words = [];

// called by the main script whenever `words` changes
export function updateWords(newWords) {
  words = newWords;
}
