## Timings (seconds)
| Kind | Side | n (rc=0) | rc≠0 | Median | Min | Max |
|---|---|---:|---:|---:|---:|---:|
| worktree-add | A | 6 | 0 | 199.044 | 188.061 | 219.905 |
| worktree-add | B | 6 | 0 | 187.136 | 160.527 | 219.958 |
| status | A | 18 | 0 | 17.998 | 12.422 | 29.426 |
| status | B | 18 | 0 | 20.518 | 12.718 | 50.189 |

## Per-pair B/A (median successful seconds per side)
| Pair | Kind | A | B | B/A |
|---|---|---:|---:|---:|
| 1 | worktree-add | 188.124 | 160.527 | 0.853 |
| 1 | status | 26.918 | 37.557 | 1.395 |
| 2 | worktree-add | 219.905 | 186.203 | 0.847 |
| 2 | status | 16.888 | 13.226 | 0.783 |
| 3 | worktree-add | 199.044 | 168.382 | 0.846 |
| 3 | status | 16.937 | 18.465 | 1.090 |
| 11 | worktree-add | 188.061 | 188.068 | 1.000 |
| 11 | status | 27.299 | 39.948 | 1.463 |
| 12 | worktree-add | 219.898 | 219.958 | 1.000 |
| 12 | status | 15.212 | 15.278 | 1.004 |
| 13 | worktree-add | 199.043 | 199.043 | 1.000 |
| 13 | status | 15.808 | 20.309 | 1.285 |
| Median across pairs | worktree-add | — | — | 0.927 |
| Median across pairs | status | — | — | 1.187 |

## Per-pair concurrent load (all rows)
| Pair | load1 range | concurrent_worktree_add range |
|---|---:|---:|
| 1 | 4.75–9.99 | 0–3 |
| 2 | 4.44–7.18 | 0–3 |
| 3 | 7.27–9.55 | 0–0 |
| 11 | 4.75–9.99 | 0–3 |
| 12 | 4.44–7.48 | 0–3 |
| 13 | 7.27–9.55 | 0–0 |
