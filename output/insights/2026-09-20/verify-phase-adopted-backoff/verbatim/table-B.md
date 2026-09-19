
### fixed-5 — job 表
| workload | job-index | reps | request | node | Started (JST) | Ended (JST) | Elapse S | runner job wall s | setup+hydrate+build s |
|---|---|---|---|---|---|---|---|---|---|
| write-heavy | 1 | 1-4 | 11275.nqsv | bnode001 | Sun Sep 20 00:04:36 2026 | Sun Sep 20 00:13:31 2026 | 539 | 534.0 | 30.5 |
| write-heavy | 2 | 5-8 | 11276.nqsv | bnode017 | Sun Sep 20 00:06:08 2026 | Sun Sep 20 00:15:04 2026 | 540 | 535.1 | 30.2 |
| balanced | 1 | 1-4 | 11268.nqsv | bnode055 | Sun Sep 20 00:20:40 2026 | Sun Sep 20 00:33:02 2026 | 746 | 741.6 | 30.6 |
| balanced | 2 | 5-8 | 11272.nqsv | bnode128 | Sun Sep 20 00:10:12 2026 | Sun Sep 20 00:22:46 2026 | 758 | 753.7 | 30.6 |
| read-heavy | 1 | 1-4 | 11270.nqsv | bnode125 | Sun Sep 20 00:04:23 2026 | Sun Sep 20 00:35:13 2026 | 1855 | 1849.6 | 31.1 |
| read-heavy | 2 | 5-8 | 11274.nqsv | bnode130 | Sun Sep 20 00:09:56 2026 | Sun Sep 20 00:41:10 2026 | 1878 | 1874.1 | 31.3 |
| **合計** | | | | | | | **6316** | **6288.1** | |

### fixed-5 — 24 枠
| workload | rep | attempt | commit | abort | bench s | count s | 保全 s | verifier wall s | maxrss GiB | rc | verdict | certified | anomaly | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| write-heavy | 1 | 1/1 | 2499737 | 11877931 | 3.344 | 2.517 | 5.197 | 114.301 | 9.6 | 0 | serializable | True | 0 | completed |
| write-heavy | 2 | 1/1 | 2507569 | 11860993 | 3.349 | 2.480 | 5.324 | 113.480 | 9.6 | 0 | serializable | True | 0 | completed |
| write-heavy | 3 | 1/1 | 2513316 | 11924579 | 3.339 | 2.481 | 5.155 | 117.273 | 9.6 | 0 | serializable | True | 0 | completed |
| write-heavy | 4 | 1/1 | 2514518 | 11911922 | 3.341 | 2.477 | 5.148 | 113.499 | 9.6 | 0 | serializable | True | 0 | completed |
| write-heavy | 5 | 1/1 | 2507367 | 11828931 | 3.347 | 2.474 | 5.168 | 115.464 | 9.6 | 0 | serializable | True | 0 | completed |
| write-heavy | 6 | 1/1 | 2471532 | 11819001 | 3.389 | 2.444 | 5.206 | 114.446 | 9.5 | 0 | serializable | True | 0 | completed |
| write-heavy | 7 | 1/1 | 2493601 | 11587522 | 3.346 | 2.459 | 5.158 | 115.389 | 9.5 | 0 | serializable | True | 0 | completed |
| write-heavy | 8 | 1/1 | 2517433 | 11924391 | 3.342 | 2.510 | 5.168 | 114.656 | 9.6 | 0 | serializable | True | 0 | completed |
| balanced | 1 | 1/1 | 4403500 | 10500591 | 3.350 | 4.357 | 8.193 | 161.734 | 13.8 | 0 | serializable | True | 0 | completed |
| balanced | 2 | 1/1 | 4393814 | 10539470 | 3.351 | 4.350 | 8.248 | 162.227 | 13.8 | 0 | serializable | True | 0 | completed |
| balanced | 3 | 1/1 | 4380681 | 10480502 | 3.347 | 4.313 | 8.018 | 162.121 | 13.7 | 0 | serializable | True | 0 | completed |
| balanced | 4 | 1/1 | 4365454 | 10513749 | 3.350 | 4.293 | 8.166 | 160.678 | 13.7 | 0 | serializable | True | 0 | completed |
| balanced | 5 | 1/1 | 4451755 | 10629986 | 3.348 | 4.422 | 8.360 | 164.213 | 14.0 | 0 | serializable | True | 0 | completed |
| balanced | 6 | 1/1 | 4451186 | 10655728 | 3.337 | 4.393 | 8.395 | 163.522 | 14.0 | 0 | serializable | True | 0 | completed |
| balanced | 7 | 1/1 | 4452685 | 10611043 | 3.332 | 4.421 | 8.273 | 164.838 | 14.0 | 0 | serializable | True | 0 | completed |
| balanced | 8 | 1/1 | 4464643 | 10627652 | 3.322 | 4.380 | 8.179 | 165.327 | 14.0 | 0 | serializable | True | 0 | completed |
| read-heavy | 1 | 1/1 | 16644814 | 2448431 | 3.346 | 16.453 | 24.390 | 412.097 | 42.7 | 0 | serializable | True | 0 | completed |
| read-heavy | 2 | 1/1 | 16562907 | 2417312 | 3.341 | 16.515 | 24.477 | 410.436 | 42.5 | 0 | serializable | True | 0 | completed |
| read-heavy | 3 | 1/1 | 16487409 | 2417826 | 3.340 | 16.273 | 24.549 | 411.495 | 42.3 | 0 | serializable | True | 0 | completed |
| read-heavy | 4 | 1/1 | 16456248 | 2423188 | 3.344 | 16.239 | 24.528 | 405.617 | 42.2 | 0 | serializable | True | 0 | completed |
| read-heavy | 5 | 1/1 | 16860602 | 2467616 | 3.389 | 16.839 | 25.044 | 416.313 | 43.3 | 0 | serializable | True | 0 | completed |
| read-heavy | 6 | 1/1 | 16802762 | 2454114 | 3.382 | 16.803 | 25.167 | 414.564 | 43.1 | 0 | serializable | True | 0 | completed |
| read-heavy | 7 | 1/1 | 16802628 | 2466982 | 3.338 | 16.738 | 25.138 | 412.401 | 43.1 | 0 | serializable | True | 0 | completed |
| read-heavy | 8 | 1/1 | 16820673 | 2454210 | 3.346 | 16.686 | 25.165 | 416.344 | 43.2 | 0 | serializable | True | 0 | completed |

### fixed-10 — job 表
| workload | job-index | reps | request | node | Started (JST) | Ended (JST) | Elapse S | runner job wall s | setup+hydrate+build s |
|---|---|---|---|---|---|---|---|---|---|
| write-heavy | 1 | 1-4 | 11273.nqsv | bnode129 | Sun Sep 20 00:04:24 2026 | Sun Sep 20 00:13:24 2026 | 545 | 540.3 | 30.9 |
| write-heavy | 2 | 5-8 | 11277.nqsv | bnode132 | Sun Sep 20 00:11:37 2026 | Sun Sep 20 00:20:38 2026 | 545 | 540.2 | 30.5 |
| balanced | 1 | 1-4 | 11271.nqsv | bnode126 | Sun Sep 20 00:20:33 2026 | Sun Sep 20 00:32:48 2026 | 739 | 734.3 | 30.4 |
| balanced | 2 | 5-8 | 11278.nqsv | bnode113 | Sun Sep 20 00:12:37 2026 | Sun Sep 20 00:24:47 2026 | 734 | 729.3 | 30.5 |
| read-heavy | 1 | 1-4 | 11269.nqsv | bnode122 | Sun Sep 20 00:10:10 2026 | Sun Sep 20 00:40:05 2026 | 1799 | 1794.5 | 30.9 |
| read-heavy | 2 | 5-8 | 11279.nqsv | bnode115 | Sun Sep 20 00:13:36 2026 | Sun Sep 20 00:43:04 2026 | 1772 | 1767.0 | 30.6 |
| **合計** | | | | | | | **6134** | **6105.7** | |

### fixed-10 — 24 枠
| workload | rep | attempt | commit | abort | bench s | count s | 保全 s | verifier wall s | maxrss GiB | rc | verdict | certified | anomaly | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| write-heavy | 1 | 1/1 | 2533193 | 8347013 | 3.348 | 2.506 | 5.275 | 114.032 | 9.7 | 0 | serializable | True | 0 | completed |
| write-heavy | 2 | 1/1 | 2520668 | 8327029 | 3.355 | 2.489 | 5.408 | 117.619 | 9.6 | 0 | serializable | True | 0 | completed |
| write-heavy | 3 | 1/1 | 2525597 | 8340096 | 3.345 | 2.478 | 5.305 | 113.754 | 9.6 | 0 | serializable | True | 0 | completed |
| write-heavy | 4 | 1/1 | 2528572 | 8358743 | 3.333 | 2.489 | 5.173 | 118.387 | 9.7 | 0 | serializable | True | 0 | completed |
| write-heavy | 5 | 1/1 | 2532454 | 8362454 | 3.344 | 2.522 | 5.447 | 115.935 | 9.7 | 0 | serializable | True | 0 | completed |
| write-heavy | 6 | 1/1 | 2516870 | 8339854 | 3.383 | 2.491 | 5.287 | 114.981 | 9.6 | 0 | serializable | True | 0 | completed |
| write-heavy | 7 | 1/1 | 2522069 | 8351604 | 3.339 | 2.536 | 5.299 | 115.413 | 9.7 | 0 | serializable | True | 0 | completed |
| write-heavy | 8 | 1/1 | 2520654 | 8362735 | 3.350 | 2.505 | 5.217 | 117.586 | 9.6 | 0 | serializable | True | 0 | completed |
| balanced | 1 | 1/1 | 4332864 | 7267660 | 3.349 | 4.285 | 8.039 | 161.706 | 13.6 | 0 | serializable | True | 0 | completed |
| balanced | 2 | 1/1 | 4300911 | 7242780 | 3.337 | 4.238 | 8.012 | 160.113 | 13.5 | 0 | serializable | True | 0 | completed |
| balanced | 3 | 1/1 | 4328676 | 7270588 | 3.335 | 4.245 | 7.947 | 158.882 | 13.6 | 0 | serializable | True | 0 | completed |
| balanced | 4 | 1/1 | 4323695 | 7276003 | 3.327 | 4.248 | 8.185 | 159.724 | 13.6 | 0 | serializable | True | 0 | completed |
| balanced | 5 | 1/1 | 4345781 | 7298418 | 3.353 | 4.282 | 8.312 | 159.801 | 13.6 | 0 | serializable | True | 0 | completed |
| balanced | 6 | 1/1 | 4323379 | 7284358 | 3.345 | 4.247 | 8.077 | 157.808 | 13.6 | 0 | serializable | True | 0 | completed |
| balanced | 7 | 1/1 | 4309099 | 7267055 | 3.359 | 4.223 | 8.347 | 158.280 | 13.5 | 0 | serializable | True | 0 | completed |
| balanced | 8 | 1/1 | 4317436 | 7269138 | 3.337 | 4.257 | 8.118 | 158.435 | 13.6 | 0 | serializable | True | 0 | completed |
| read-heavy | 1 | 1/1 | 16078316 | 2163428 | 3.356 | 15.911 | 24.247 | 397.910 | 41.3 | 0 | serializable | True | 0 | completed |
| read-heavy | 2 | 1/1 | 15992328 | 2154830 | 3.341 | 15.822 | 24.079 | 396.178 | 41.0 | 0 | serializable | True | 0 | completed |
| read-heavy | 3 | 1/1 | 16030619 | 2155333 | 3.348 | 15.798 | 23.879 | 398.298 | 41.1 | 0 | serializable | True | 0 | completed |
| read-heavy | 4 | 1/1 | 15991074 | 2159130 | 3.370 | 15.742 | 23.659 | 396.549 | 41.1 | 0 | serializable | True | 0 | completed |
| read-heavy | 5 | 1/1 | 15837259 | 2140134 | 3.349 | 15.684 | 23.167 | 395.982 | 40.7 | 0 | serializable | True | 0 | completed |
| read-heavy | 6 | 1/1 | 15779466 | 2136346 | 3.350 | 15.536 | 23.475 | 393.653 | 40.5 | 0 | serializable | True | 0 | completed |
| read-heavy | 7 | 1/1 | 15688765 | 2133037 | 3.343 | 15.505 | 22.973 | 386.490 | 40.3 | 0 | serializable | True | 0 | completed |
| read-heavy | 8 | 1/1 | 15772835 | 2126265 | 3.355 | 15.646 | 23.757 | 389.182 | 40.5 | 0 | serializable | True | 0 | completed |
