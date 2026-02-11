# Prompts

## 2026-02-11
Fix State Management, Routing, and Encoding Bugs - Fix intermittent "Note Not Found" errors for notes that exist, and sidebar showing wrong vault after page refresh. Three root causes: (1) loadedPath guard prevents retry after vault changes, (2) vault selection not persisted (lost on refresh), (3) note paths in generated HTML not URL-encoded.
