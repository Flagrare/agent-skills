---
type: regex
pattern: 'setup\.py[^\n]*install|installed|reinstalled|is in now|live now|works now|from your next message'
flags: i
match: contains
target: last_message
---
