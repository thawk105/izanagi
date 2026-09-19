# t1259 scan survey

Time is the testcase setup/call/teardown proxy, not an individual Git duration. n/percentiles use non-error cases with time >= 2 s; errors are reported separately as 30 s right-censored Git observations (their testcase time is not replaced).

Overlap = number of distinct other retained sessions whose shard-0..2 window union intersects this session; this is not peak simultaneous concurrency. Naive timestamps and --since use the local timezone. Sessions are filtered by directory mtime.

| regime | other sessions | scan proxies | n | p50 | p90 | p95 | p99 | max | errors | hostname |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| real-repo | 0 | 5 | 5 | 8.614 | 18.323 | 21.408 | 23.877 | 24.494 | 0 | bnode021, bnode078, bnode112, bnode113 |
| real-repo | 1 | 18 | 18 | 9.029 | 17.686 | 23.119 | 23.234 | 23.263 | 0 | bnode009, bnode014, bnode015, bnode021, bnode050, bnode055, bnode060, bnode072, bnode076, bnode078, bnode079, bnode080, bnode106, bnode108, bnode109, bnode126 |
| real-repo | 2 | 3 | 3 | 8.581 | 8.921 | 8.963 | 8.998 | 9.006 | 0 | bnode014, bnode081, bnode126 |
| ungrouped | 0 | 132 | 122 | 20.169 | 41.260 | 47.200 | 54.310 | 57.688 | 14 | bnode029, bnode059, bnode113 |
| ungrouped | 1 | 43 | 42 | 22.026 | 29.791 | 34.995 | 35.582 | 35.584 | 1 | bnode009 |
| ungrouped | 2 | 175 | 169 | 22.920 | 41.191 | 47.863 | 54.900 | 57.073 | 6 | bnode034, bnode053, bnode055, bnode113 |
| ungrouped | 3 | 89 | 89 | 18.609 | 27.340 | 30.065 | 32.105 | 33.192 | 0 | bnode006, bnode029 |
| ungrouped | 5 | 214 | 184 | 20.799 | 39.115 | 42.577 | 57.654 | 58.874 | 34 | bnode007, bnode059, bnode114, bnode127, bnode136 |
| ungrouped | 6 | 45 | 22 | 32.215 | 41.851 | 45.346 | 45.729 | 45.782 | 28 | bnode050 |
| ungrouped | 7 | 89 | 85 | 20.239 | 31.998 | 32.539 | 35.789 | 35.790 | 4 | bnode109, bnode140 |

## Session suite windows

| session | overlap | shard | timestamp | time | hostname |
|---|---:|---|---|---:|---|
| 028bb4029aa1e24bf0d1f37b67efedbe | 2 | shard-0 | 2026-09-19T23:10:24.066895+09:00 | 480.413 | bnode126 |
| 028bb4029aa1e24bf0d1f37b67efedbe | 2 | shard-1 | 2026-09-19T23:11:54.717850+09:00 | 285.491 | bnode130 |
| 028bb4029aa1e24bf0d1f37b67efedbe | 2 | shard-2 | 2026-09-19T23:22:20.089084+09:00 | 228.093 | bnode122 |
| 0345e47cd270926ed7de0395addf1036 | 1 | shard-0 | 2026-09-19T06:40:04.034622+09:00 | 322.583 | bnode076 |
| 0345e47cd270926ed7de0395addf1036 | 1 | shard-1 | 2026-09-19T06:40:03.296556+09:00 | 262.102 | bnode074 |
| 0345e47cd270926ed7de0395addf1036 | 1 | shard-2 | 2026-09-19T06:40:04.449332+09:00 | 227.582 | bnode078 |
| 08f548a2ef1537c63bc665bc15da496c | 1 | shard-0 | 2026-09-19T23:02:40.436474+09:00 | 528.451 | bnode109 |
| 08f548a2ef1537c63bc665bc15da496c | 1 | shard-1 | 2026-09-19T23:04:17.229457+09:00 | 229.889 | bnode128 |
| 08f548a2ef1537c63bc665bc15da496c | 1 | shard-2 | 2026-09-19T23:06:18.730111+09:00 | 175.563 | bnode121 |
| 0ef1c769f245ec9a3009b1c19eb98266 | 5 | shard-0 | 2026-09-18T22:39:40.005337+09:00 | 356.449 | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | 5 | shard-1 | 2026-09-18T22:35:29.169679+09:00 | 238.711 | bnode034 |
| 15a50431fccc3328530807ce25a2ad48 | 2 | shard-0 | 2026-09-18T23:17:35.090792+09:00 | 396.594 | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | 2 | shard-1 | 2026-09-18T23:16:23.017589+09:00 | 236.893 | bnode063 |
| 15a50431fccc3328530807ce25a2ad48 | 2 | shard-2 | 2026-09-18T23:19:36.984313+09:00 | 223.298 | bnode114 |
| 176eac4a5b5d8be4fa250c547b2fd246 | 0 | shard-0 | 2026-09-19T00:36:21.937705+09:00 | 446.745 | bnode113 |
| 176eac4a5b5d8be4fa250c547b2fd246 | 0 | shard-1 | 2026-09-19T00:36:21.950611+09:00 | 303.659 | bnode073 |
| 176eac4a5b5d8be4fa250c547b2fd246 | 0 | shard-2 | 2026-09-19T00:36:21.942379+09:00 | 207.635 | bnode091 |
| 26146125d402f3e5e57a8f56ea02b596 | 1 | shard-0 | 2026-09-19T07:02:06.142783+09:00 | 480.35 | bnode078 |
| 26146125d402f3e5e57a8f56ea02b596 | 1 | shard-1 | 2026-09-19T07:07:25.755749+09:00 | 234.428 | bnode076 |
| 26146125d402f3e5e57a8f56ea02b596 | 1 | shard-2 | 2026-09-19T07:02:05.408853+09:00 | 214.841 | bnode074 |
| 27398d75ff0f382cfb1557af26f3f422 | 2 | shard-0 | 2026-09-18T21:52:29.439206+09:00 | 393.443 | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | 2 | shard-1 | 2026-09-18T21:47:57.053797+09:00 | 233.556 | bnode127 |
| 27398d75ff0f382cfb1557af26f3f422 | 2 | shard-2 | 2026-09-18T21:43:54.553202+09:00 | 207.668 | bnode109 |
| 2944a7d5c1404704281a5a5863261ebe | 5 | shard-0 | 2026-09-18T22:07:18.393762+09:00 | 348.869 | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | 5 | shard-1 | 2026-09-18T22:50:44.957181+09:00 | 236.677 | bnode009 |
| 2944a7d5c1404704281a5a5863261ebe | 5 | shard-2 | 2026-09-18T22:12:59.446882+09:00 | 216.924 | bnode034 |
| 294df845f44f782c0def2cf4878bc313 | 5 | shard-0 | 2026-09-18T22:33:58.232855+09:00 | 698.339 | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | 5 | shard-1 | 2026-09-18T22:34:38.295767+09:00 | 286.444 | bnode012 |
| 294df845f44f782c0def2cf4878bc313 | 5 | shard-2 | 2026-09-18T22:33:54.942419+09:00 | 172.813 | bnode025 |
| 401375e3eb302f10121e6412bb4dfbef | 2 | shard-1 | 2026-09-18T21:52:40.270908+09:00 | 230.266 | bnode063 |
| 401375e3eb302f10121e6412bb4dfbef | 2 | shard-2 | 2026-09-18T21:42:38.960501+09:00 | 206.174 | bnode063 |
| 4e8c9aaaeb6ae7f1a6f105d203741bd6 | 1 | shard-0 | 2026-09-19T23:35:34.160098+09:00 | 483.117 | bnode126 |
| 4e8c9aaaeb6ae7f1a6f105d203741bd6 | 1 | shard-1 | 2026-09-19T23:36:49.389484+09:00 | 230.569 | bnode128 |
| 4e8c9aaaeb6ae7f1a6f105d203741bd6 | 1 | shard-2 | 2026-09-19T23:36:49.375787+09:00 | 175.444 | bnode119 |
| 50679c150b0e76aafa1983c20294bf27 | 1 | shard-0 | 2026-09-19T22:54:51.156631+09:00 | 425.705 | bnode106 |
| 50679c150b0e76aafa1983c20294bf27 | 1 | shard-1 | 2026-09-19T22:52:16.527852+09:00 | 233.247 | bnode055 |
| 50679c150b0e76aafa1983c20294bf27 | 1 | shard-2 | 2026-09-19T22:50:20.181525+09:00 | 166.199 | bnode128 |
| 5b3249c0448668ecc8b745ce226e1037 | 1 | shard-0 | 2026-09-19T22:42:00.564688+09:00 | 523.831 | bnode080 |
| 5b3249c0448668ecc8b745ce226e1037 | 1 | shard-1 | 2026-09-19T22:42:05.794126+09:00 | 319.967 | bnode106 |
| 5b3249c0448668ecc8b745ce226e1037 | 1 | shard-2 | 2026-09-19T22:42:03.735803+09:00 | 191.495 | bnode055 |
| 5e38eddf96f8aeef589e1346eea32e4d | 1 | shard-0 | 2026-09-19T08:04:30.748277+09:00 | 285.542 | bnode060 |
| 5e38eddf96f8aeef589e1346eea32e4d | 1 | shard-1 | 2026-09-19T08:10:42.235226+09:00 | 241.526 | bnode076 |
| 5e38eddf96f8aeef589e1346eea32e4d | 1 | shard-2 | 2026-09-19T08:04:32.723766+09:00 | 208.615 | bnode111 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | 2 | shard-0 | 2026-09-18T23:06:20.666545+09:00 | 355.662 | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | 2 | shard-1 | 2026-09-18T23:06:16.932407+09:00 | 237.281 | bnode063 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | 2 | shard-2 | 2026-09-18T23:06:20.673008+09:00 | 233.429 | bnode055 |
| 6d44cbdefcb2ac00d7641f29f630a597 | 7 | shard-0 | 2026-09-18T22:12:06.196044+09:00 | 351.808 | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | 7 | shard-1 | 2026-09-18T22:34:48.467020+09:00 | 306.707 | bnode127 |
| 6d44cbdefcb2ac00d7641f29f630a597 | 7 | shard-2 | 2026-09-18T22:25:03.239330+09:00 | 208.965 | bnode113 |
| 6e3a28d9916306d0582b387b8a3acc26 | 0 | shard-0 | 2026-09-19T08:15:24.136915+09:00 | 293.398 | bnode078 |
| 6e3a28d9916306d0582b387b8a3acc26 | 0 | shard-1 | 2026-09-19T07:59:51.504651+09:00 | 264.017 | bnode050 |
| 6e3a28d9916306d0582b387b8a3acc26 | 0 | shard-2 | 2026-09-19T07:59:49.046668+09:00 | 230.2 | bnode076 |
| 702141446c72b740527e223f1fedd1f2 | 0 | shard-0 | 2026-09-18T21:31:48.148255+09:00 | 533.61 | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | 0 | shard-1 | 2026-09-18T21:31:38.324254+09:00 | 366.764 | bnode009 |
| 702141446c72b740527e223f1fedd1f2 | 0 | shard-2 | 2026-09-18T21:31:59.324918+09:00 | 226.11 | bnode063 |
| 772d45201515c46abc25d6a038e45966 | 0 | shard-0 | 2026-09-18T23:41:50.201803+09:00 | 390.03 | bnode059 |
| 772d45201515c46abc25d6a038e45966 | 0 | shard-1 | 2026-09-18T23:34:50.055156+09:00 | 232.034 | bnode067 |
| 772d45201515c46abc25d6a038e45966 | 0 | shard-2 | 2026-09-18T23:44:20.854998+09:00 | 217.463 | bnode067 |
| 792a5f0db0c597e80e0d09ebe66c05b2 | 1 | shard-0 | 2026-09-19T23:49:59.439966+09:00 | 617.635 | bnode015 |
| 792a5f0db0c597e80e0d09ebe66c05b2 | 1 | shard-1 | 2026-09-19T23:50:00.739916+09:00 | 232.389 | bnode013 |
| 792a5f0db0c597e80e0d09ebe66c05b2 | 1 | shard-2 | 2026-09-19T23:50:02.687864+09:00 | 171.829 | bnode012 |
| 7b08b2f79360f16b6570f2583be76007 | 1 | shard-0 | 2026-09-19T23:50:02.581211+09:00 | 612.243 | bnode055 |
| 7b08b2f79360f16b6570f2583be76007 | 1 | shard-1 | 2026-09-19T23:50:05.577155+09:00 | 306.682 | bnode122 |
| 7b08b2f79360f16b6570f2583be76007 | 1 | shard-2 | 2026-09-19T23:50:06.117375+09:00 | 172.153 | bnode011 |
| 8212f02c4c4d72b9b81939b989c81ed2 | 5 | shard-0 | 2026-09-18T22:48:23.663035+09:00 | 580.677 | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | 5 | shard-1 | 2026-09-18T22:15:33.130619+09:00 | 240.153 | bnode113 |
| 8212f02c4c4d72b9b81939b989c81ed2 | 5 | shard-2 | 2026-09-18T22:24:40.090370+09:00 | 210.382 | bnode127 |
| 86438c4d22aaa4b3512231ddb6b1c81a | 1 | shard-0 | 2026-09-19T07:16:51.231007+09:00 | 305.096 | bnode072 |
| 86438c4d22aaa4b3512231ddb6b1c81a | 1 | shard-1 | 2026-09-19T07:23:53.463036+09:00 | 243.996 | bnode076 |
| 86438c4d22aaa4b3512231ddb6b1c81a | 1 | shard-2 | 2026-09-19T07:21:17.174993+09:00 | 234.804 | bnode074 |
| 8b0890b98436fb8be10f39b671b024be | 1 | shard-0 | 2026-09-19T08:21:36.424116+09:00 | 485.536 | bnode060 |
| 8b0890b98436fb8be10f39b671b024be | 1 | shard-1 | 2026-09-19T08:10:47.779795+09:00 | 241.086 | bnode081 |
| 8b0890b98436fb8be10f39b671b024be | 1 | shard-2 | 2026-09-19T08:10:47.771530+09:00 | 178.927 | bnode079 |
| 8d5a2f361e24ee3b80e0e7b4ed86fa71 | 0 | shard-0 | 2026-09-19T22:29:49.935431+09:00 | 484.972 | bnode112 |
| 8d5a2f361e24ee3b80e0e7b4ed86fa71 | 0 | shard-1 | 2026-09-19T22:28:22.526711+09:00 | 265.33 | bnode130 |
| 8d5a2f361e24ee3b80e0e7b4ed86fa71 | 0 | shard-2 | 2026-09-19T22:27:09.202779+09:00 | 198.976 | bnode126 |
| 8e94b125ef46a86c899fdcb9e775059b | 2 | shard-0 | 2026-09-20T00:36:11.879995+09:00 | 389.646 | bnode014 |
| 8e94b125ef46a86c899fdcb9e775059b | 2 | shard-1 | 2026-09-20T00:35:45.589433+09:00 | 236.52 | bnode015 |
| 8e94b125ef46a86c899fdcb9e775059b | 2 | shard-2 | 2026-09-20T00:19:20.598038+09:00 | 256.732 | bnode010 |
| 8f7aa362bbbb6b447ff913c2be94d9d5 | 2 | shard-2 | 2026-09-18T22:23:01.731895+09:00 | 219.564 | bnode034 |
| 916c1cd50105b81544ad1b18e00a9675 | 1 | shard-0 | 2026-09-19T21:32:01.594027+09:00 | 392.461 | bnode021 |
| 916c1cd50105b81544ad1b18e00a9675 | 1 | shard-1 | 2026-09-19T21:32:01.601630+09:00 | 257.821 | bnode020 |
| 916c1cd50105b81544ad1b18e00a9675 | 1 | shard-2 | 2026-09-19T21:32:01.592394+09:00 | 194.787 | bnode019 |
| a4ded6951baf937c43d94745f399ce38 | 6 | shard-0 | 2026-09-18T22:48:20.797066+09:00 | 665.239 | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | 6 | shard-1 | 2026-09-18T22:47:26.685643+09:00 | 235.732 | bnode029 |
| a4ded6951baf937c43d94745f399ce38 | 6 | shard-2 | 2026-09-18T22:40:30.562739+09:00 | 208.478 | bnode009 |
| a6f7c71c1fbf910b85a1f0419134b523 | 1 | shard-0 | 2026-09-19T21:37:04.333020+09:00 | 457.946 | bnode108 |
| a6f7c71c1fbf910b85a1f0419134b523 | 1 | shard-1 | 2026-09-19T21:37:04.326224+09:00 | 232.594 | bnode107 |
| a6f7c71c1fbf910b85a1f0419134b523 | 1 | shard-2 | 2026-09-19T21:40:41.910512+09:00 | 168.487 | bnode019 |
| ad7a2a5489be9c511045d777a7828fa0 | 3 | shard-0 | 2026-09-18T23:00:55.375476+09:00 | 358.83 | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | 3 | shard-1 | 2026-09-18T23:12:02.682621+09:00 | 263.306 | bnode050 |
| ad7a2a5489be9c511045d777a7828fa0 | 3 | shard-2 | 2026-09-18T23:00:57.570790+09:00 | 220.519 | bnode113 |
| af35189c8facc2eb00eebc87bc1c5958 | 0 | shard-0 | 2026-09-19T07:44:50.635346+09:00 | 534.873 | bnode078 |
| af35189c8facc2eb00eebc87bc1c5958 | 0 | shard-1 | 2026-09-19T07:34:29.547706+09:00 | 231.99 | bnode079 |
| af35189c8facc2eb00eebc87bc1c5958 | 0 | shard-2 | 2026-09-19T07:34:14.626353+09:00 | 282.94 | bnode076 |
| b24821a39b6bb7041851237003b786e3 | 2 | shard-0 | 2026-09-18T21:52:24.879267+09:00 | 532.944 | bnode034 |
| b24821a39b6bb7041851237003b786e3 | 2 | shard-2 | 2026-09-18T21:57:28.557862+09:00 | 208.155 | bnode127 |
| b37b3251dfc8435ef330b20a738c2df5 | 7 | shard-0 | 2026-09-18T22:54:36.655904+09:00 | 367.089 | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | 7 | shard-1 | 2026-09-18T22:34:41.644487+09:00 | 265.603 | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | 7 | shard-2 | 2026-09-18T22:44:44.877892+09:00 | 205.7 | bnode140 |
| b6162dafa84bc674704a2a13f342d40c | 0 | shard-0 | 2026-09-19T00:07:11.941664+09:00 | 345.029 | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | 0 | shard-1 | 2026-09-18T23:54:54.075908+09:00 | 240.095 | bnode067 |
| b6162dafa84bc674704a2a13f342d40c | 0 | shard-2 | 2026-09-18T23:49:23.088132+09:00 | 207.47 | bnode012 |
| bafb8fd26979e25cf366dd349d2d0335 | 3 | shard-0 | 2026-09-18T23:10:05.507044+09:00 | 354.397 | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | 3 | shard-1 | 2026-09-18T23:21:11.108886+09:00 | 233.715 | bnode029 |
| bafb8fd26979e25cf366dd349d2d0335 | 3 | shard-2 | 2026-09-18T23:16:03.661256+09:00 | 209.79 | bnode113 |
| c85e84993335fc80c0f57d1b677a20f8 | 1 | shard-0 | 2026-09-18T22:02:29.396142+09:00 | 370.559 | bnode009 |
| d32ec36aa639ef3ec60ec0964db23a25 | 1 | shard-0 | 2026-09-20T00:10:51.028321+09:00 | 490.664 | bnode014 |
| d32ec36aa639ef3ec60ec0964db23a25 | 1 | shard-1 | 2026-09-20T00:16:43.136327+09:00 | 231.517 | bnode013 |
| d32ec36aa639ef3ec60ec0964db23a25 | 1 | shard-2 | 2026-09-20T00:10:47.692138+09:00 | 171.607 | bnode011 |
| da379915ed116c8b5c6937cbe325b601 | 1 | shard-0 | 2026-09-20T00:40:50.018683+09:00 | 507.835 | bnode009 |
| da379915ed116c8b5c6937cbe325b601 | 1 | shard-1 | 2026-09-20T00:40:50.045291+09:00 | 247.385 | bnode008 |
| da379915ed116c8b5c6937cbe325b601 | 1 | shard-2 | 2026-09-20T00:40:50.012309+09:00 | 182.513 | bnode013 |
| de52a7377fc52d012079f743efb601c4 | 1 | shard-0 | 2026-09-19T06:40:53.573564+09:00 | 373.46 | bnode079 |
| de52a7377fc52d012079f743efb601c4 | 1 | shard-1 | 2026-09-19T06:40:54.759897+09:00 | 401.793 | bnode081 |
| e818446e399fe09320c86bccd7f27afb | 0 | shard-0 | 2026-09-19T22:10:20.582698+09:00 | 503.001 | bnode021 |
| e818446e399fe09320c86bccd7f27afb | 0 | shard-1 | 2026-09-19T22:00:58.546031+09:00 | 233.73 | bnode020 |
| e818446e399fe09320c86bccd7f27afb | 0 | shard-2 | 2026-09-19T21:59:33.677729+09:00 | 173.584 | bnode019 |
| f4b4518824c4f2497f80aa8f6f03e8ac | 2 | shard-0 | 2026-09-19T07:12:12.134747+09:00 | 285.021 | bnode081 |
| f4b4518824c4f2497f80aa8f6f03e8ac | 2 | shard-1 | 2026-09-19T07:15:51.872375+09:00 | 240.725 | bnode079 |
| f4b4518824c4f2497f80aa8f6f03e8ac | 2 | shard-2 | 2026-09-19T07:02:48.729532+09:00 | 242.417 | bnode082 |
| faf48e0e8f80aea69abd7fe155053925 | 1 | shard-0 | 2026-09-19T23:37:17.499662+09:00 | 390.618 | bnode009 |
| faf48e0e8f80aea69abd7fe155053925 | 1 | shard-1 | 2026-09-19T23:38:17.006036+09:00 | 239.55 | bnode055 |
| faf48e0e8f80aea69abd7fe155053925 | 1 | shard-2 | 2026-09-19T23:38:56.345568+09:00 | 225.739 | bnode130 |
| fbc809ecc5b11c8aff6e13260f48554c | 5 | shard-0 | 2026-09-18T22:34:38.313465+09:00 | 376.53 | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | 5 | shard-1 | 2026-09-18T22:30:04.193784+09:00 | 232.704 | bnode136 |
| fbc809ecc5b11c8aff6e13260f48554c | 5 | shard-2 | 2026-09-18T22:33:02.197175+09:00 | 208.875 | bnode008 |
| fcc43198a07a3e3e624b30c0a347e96d | 1 | shard-0 | 2026-09-19T23:17:49.922317+09:00 | 582.82 | bnode050 |
| fcc43198a07a3e3e624b30c0a347e96d | 1 | shard-1 | 2026-09-19T23:19:55.691319+09:00 | 230.156 | bnode128 |
| fcc43198a07a3e3e624b30c0a347e96d | 1 | shard-2 | 2026-09-19T23:17:00.001805+09:00 | 166.897 | bnode121 |

## Individual scan proxies and errors

| session | regime | overlap | nodeid | time | error (30 s censored) | hostname |
|---|---|---:|---|---:|---|---|
| 028bb4029aa1e24bf0d1f37b67efedbe | real-repo | 2 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.581 | False | bnode126 |
| 0345e47cd270926ed7de0395addf1036 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 9.014 | False | bnode076 |
| 08f548a2ef1537c63bc665bc15da496c | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 10.241 | False | bnode109 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_swapped_r2_hex_values_fail_exact_binding | 14.413 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 13.084 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 20.818 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_repo_unchanged_claim_compares_target_content_digests | 22.4 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[unparseable-json] | 22.293 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 23.644 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 19.54 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 19.159 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 20.424 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_request_receipt_accepts_measured_qstat_layout | 14.808 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 20.545 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 17.019 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_repository_local_evidence_directory_is_rejected | 13.611 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 16.541 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 15.961 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_atomic_result_publish_is_create_only | 22.018 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 22.835 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 19.746 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 28.576 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 30.021 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 30.021 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r2_timeout_is_not_accepted_as_refusal | 29.857 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_group_intent_is_create_only_and_has_no_completion_fields | 29.952 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 26.095 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 29.856 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 29.86 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 28.742 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 20.92 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r3_manifest_rejects_nonliteral_ambient_approval | 20.519 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 26.735 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 21.087 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 21.01 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 23.573 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 15.725 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_submitter_text_is_outside_execution_inventory | 13.261 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 18.034 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 13.783 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 6.854 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 3.982 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 7.021 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 5.863 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.73 | False | bnode136 |
| 0ef1c769f245ec9a3009b1c19eb98266 | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.138 | False | bnode136 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_swapped_r2_hex_values_fail_exact_binding | 23.77 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 22.92 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_submission_source_digests_are_bound_to_runtime_bytes[campaign-bytes] | 23.642 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[unparseable-json] | 35.653 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 26.64 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_repo_unchanged_claim_compares_target_content_digests | 35.833 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 32.027 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 29.695 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 43.453 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 41.809 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 24.867 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 27.463 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_request_receipt_accepts_measured_qstat_layout | 14.928 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_repository_local_evidence_directory_is_rejected | 14.15 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 14.864 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 16.991 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_atomic_result_publish_is_create_only | 14.427 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 14.32 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 18.078 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 38.076 | True | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 36.134 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 35.039 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 33.015 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 32.667 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 28.031 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 22.841 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 29.151 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 21.556 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 28.934 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 26.339 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r3_manifest_rejects_nonliteral_ambient_approval | 22.823 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_group_intent_is_create_only_and_has_no_completion_fields | 11.706 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 18.166 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 14.047 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_submitter_text_is_outside_execution_inventory | 17.256 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 18.177 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r2_timeout_is_not_accepted_as_refusal | 11.583 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 4.565 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.082 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 7.242 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 5.973 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.773 | False | bnode055 |
| 15a50431fccc3328530807ce25a2ad48 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.121 | False | bnode055 |
| 176eac4a5b5d8be4fa250c547b2fd246 | real-repo | 0 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 24.494 | False | bnode113 |
| 26146125d402f3e5e57a8f56ea02b596 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.007 | False | bnode078 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 10.863 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_swapped_r2_hex_values_fail_exact_binding | 11.902 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 31.197 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_submitter_preflight_parses_gen_s_semantic_state[disabled] | 33.685 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_repo_unchanged_claim_compares_target_content_digests | 34.514 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 34.042 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 30.861 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 30.641 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 28.715 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 26.757 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_request_receipt_rejects_wrong_owner_or_non_active_state[different-owner] | 20.097 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 27.629 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_repository_local_evidence_directory_is_rejected | 19.711 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 17.767 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_atomic_result_publish_is_create_only | 26.715 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 28.306 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 26.329 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 24.197 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 21.688 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 36.502 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 34.846 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 35.187 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 22.508 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 29.994 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 30.842 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_submitter_text_is_outside_execution_inventory | 20.311 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 21.751 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 23.876 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_group_intent_is_create_only_and_has_no_completion_fields | 23.579 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 30.962 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r3_manifest_rejects_nonliteral_ambient_approval | 25.862 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 30.163 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 7.6 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 10.49 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 7.612 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r2_timeout_is_not_accepted_as_refusal | 7.607 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 7.613 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 4.938 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.288 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 7.225 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 6.318 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.869 | False | bnode113 |
| 27398d75ff0f382cfb1557af26f3f422 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.343 | False | bnode113 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_swapped_r2_hex_values_fail_exact_binding | 10.278 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 9.231 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 14.383 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[unparseable-json] | 21.179 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_repo_unchanged_claim_compares_target_content_digests | 21.252 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 21.227 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 16.145 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 14.11 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 18.73 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 19.241 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 17.871 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_repository_local_evidence_directory_is_rejected | 12.392 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_request_receipt_accepts_measured_qstat_layout | 15.315 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 12.023 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 10.619 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 23.117 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 20.567 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 23.868 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_atomic_result_publish_is_create_only | 25.661 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 16.934 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 24.245 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 27.761 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_group_intent_is_create_only_and_has_no_completion_fields | 27.861 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r2_timeout_is_not_accepted_as_refusal | 27.781 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 27.8 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 30.304 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r3_manifest_rejects_nonliteral_ambient_approval | 18.063 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 18.3 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 21.091 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 18.312 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_submitter_text_is_outside_execution_inventory | 11.96 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 25.083 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 15.687 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 12.736 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 23.994 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[body-present-rc-failed] | 18.092 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[rc-zero-but-absent] | 18.311 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 26.747 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 24.728 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 8.18 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.94 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 5.967 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 5.685 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.741 | False | bnode127 |
| 2944a7d5c1404704281a5a5863261ebe | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.073 | False | bnode127 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_swapped_r2_hex_values_fail_exact_binding | 17.253 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 16.223 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 33.801 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 34.442 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 46.848 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 44.388 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 45.241 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 47.791 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 45.507 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_repo_unchanged_claim_compares_target_content_digests | 42.421 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_pbs_preserves_one_valid_negative_observer_result | 0.001 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_submitter_preflight_parses_gen_s_semantic_state[disabled] | 43.673 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_submitter_preflight_parses_gen_s_semantic_state[missing-gen-s] | 0.001 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_request_receipt_rejects_wrong_owner_or_non_active_state[different-owner] | 41.508 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_repository_local_evidence_directory_is_rejected | 42.191 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_request_receipt_accepts_measured_qstat_layout | 42.604 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[unparseable-json] | 40.005 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 46.33 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 45.544 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_atomic_result_publish_is_create_only | 46.389 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 39.942 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 43.261 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 42.633 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 40.466 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 47.315 | True | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 39.581 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 38.067 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r3_manifest_rejects_nonliteral_ambient_approval | 31.944 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 33.616 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 30.538 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 24.275 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 21.699 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_submitter_text_is_outside_execution_inventory | 17.58 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 20.779 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 21.71 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 18.361 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r2_timeout_is_not_accepted_as_refusal | 12.741 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 12.703 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_group_intent_is_create_only_and_has_no_completion_fields | 12.829 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 12.703 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 12.686 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.532 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 5.644 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 6.04 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.831 | False | bnode007 |
| 294df845f44f782c0def2cf4878bc313 | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.238 | False | bnode007 |
| 4e8c9aaaeb6ae7f1a6f105d203741bd6 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.511 | False | bnode126 |
| 50679c150b0e76aafa1983c20294bf27 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 13.839 | False | bnode106 |
| 5b3249c0448668ecc8b745ce226e1037 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.828 | False | bnode080 |
| 5e38eddf96f8aeef589e1346eea32e4d | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.341 | False | bnode060 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_swapped_r2_hex_values_fail_exact_binding | 11.28 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 9.892 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 25.86 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_repo_unchanged_claim_compares_target_content_digests | 26.431 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[unparseable-json] | 25.845 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 24.109 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 17.934 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 20.077 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 15.843 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 19.147 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 19.22 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_repository_local_evidence_directory_is_rejected | 14.703 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 11.417 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 21.829 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_atomic_result_publish_is_create_only | 17.232 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 22.513 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 18.791 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 19.421 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 16.266 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 16.296 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 16.313 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 31.769 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_group_intent_is_create_only_and_has_no_completion_fields | 31.88 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r2_timeout_is_not_accepted_as_refusal | 31.776 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 30.739 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 27.839 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 28.373 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r3_manifest_rejects_nonliteral_ambient_approval | 24.942 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 25.356 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 26.203 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_submitter_text_is_outside_execution_inventory | 13.609 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 25.557 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 23.588 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 18.684 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 19.989 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 14.317 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[rc-zero-but-absent] | 25.566 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 7.868 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.057 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 8.014 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 6.248 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_pbs_contract_runs_observer_through_single_result_call_block | 4.026 | False | bnode053 |
| 6b5ba425d1a6ecbab7967cb7be12ced7 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 6.417 | False | bnode053 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 9.756 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_submission_source_digests_are_bound_to_runtime_bytes[campaign-bytes] | 10.834 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_swapped_r2_hex_values_fail_exact_binding | 11.483 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 18.378 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_submitter_preflight_parses_gen_s_semantic_state[disabled] | 20.239 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_repo_unchanged_claim_compares_target_content_digests | 20.414 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 18.256 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 16.194 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 17.166 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 14.1 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 16.323 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 18.482 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_repository_local_evidence_directory_is_rejected | 15.39 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 16.451 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 20.69 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 15.653 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_atomic_result_publish_is_create_only | 15.494 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 17.919 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 19.376 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 19.325 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 19.389 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r2_timeout_is_not_accepted_as_refusal | 32.46 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 32.452 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_group_intent_is_create_only_and_has_no_completion_fields | 32.559 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 32.456 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 28.992 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 23.194 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 25.824 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 25.045 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_submitter_text_is_outside_execution_inventory | 15.832 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 16.605 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 23.385 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 21.138 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 32.287 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r3_manifest_rejects_nonliteral_ambient_approval | 22.756 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 25.739 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 29.614 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 12.703 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 7.295 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 3.908 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 5.494 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 5.937 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.604 | False | bnode109 |
| 6d44cbdefcb2ac00d7641f29f630a597 | ungrouped | 7 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.321 | False | bnode109 |
| 6e3a28d9916306d0582b387b8a3acc26 | real-repo | 0 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.614 | False | bnode078 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_swapped_r2_hex_values_fail_exact_binding | 23.514 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 22.786 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 30.119 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 30.218 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_repo_unchanged_claim_compares_target_content_digests | 30.229 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[unparseable-json] | 30.245 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_pbs_preserves_one_valid_negative_observer_result | 0.0 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_submitter_preflight_parses_gen_s_semantic_state[disabled] | 0.0 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_submitter_preflight_parses_gen_s_semantic_state[missing-gen-s] | 0.0 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 57.688 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 55.126 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_request_receipt_rejects_wrong_owner_or_non_active_state[different-owner] | 39.739 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 51.241 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 41.915 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 43.603 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 40.363 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_request_receipt_accepts_measured_qstat_layout | 43.611 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_repository_local_evidence_directory_is_rejected | 40.075 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 43.708 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_atomic_result_publish_is_create_only | 39.525 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 0.001 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 40.006 | True | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 36.66 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 37.21 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 41.36 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 34.161 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 33.749 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 29.726 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[rc-zero-but-absent] | 29.71 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r3_manifest_rejects_nonliteral_ambient_approval | 29.251 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 25.305 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 21.863 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 16.843 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_submitter_text_is_outside_execution_inventory | 13.135 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 14.946 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_group_intent_is_create_only_and_has_no_completion_fields | 17.138 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 17.052 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 12.517 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 14.095 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 12.522 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 12.52 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 12.522 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r2_timeout_is_not_accepted_as_refusal | 7.667 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.413 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 7.239 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 6.552 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_pbs_contract_runs_observer_through_single_result_call_block | 4.063 | False | bnode113 |
| 702141446c72b740527e223f1fedd1f2 | ungrouped | 0 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.114 | False | bnode113 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_swapped_r2_hex_values_fail_exact_binding | 11.196 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 9.802 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_submission_source_digests_are_bound_to_runtime_bytes[campaign-bytes] | 10.95 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 23.298 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_submitter_preflight_parses_gen_s_semantic_state[disabled] | 25.94 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_repo_unchanged_claim_compares_target_content_digests | 26.289 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 24.21 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 22.661 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 21.761 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 21.765 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 19.763 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 17.546 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_request_receipt_accepts_measured_qstat_layout | 19.856 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_repository_local_evidence_directory_is_rejected | 17.086 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 18.335 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 29.737 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_atomic_result_publish_is_create_only | 26.951 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 22.418 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 18.038 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 26.642 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 47.62 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 45.391 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 47.638 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 43.432 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 44.426 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 47.369 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 43.973 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_group_intent_is_create_only_and_has_no_completion_fields | 47.295 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[body-present-rc-failed] | 31.516 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 39.593 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 32.37 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 26.338 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r3_manifest_rejects_nonliteral_ambient_approval | 32.117 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_submitter_text_is_outside_execution_inventory | 24.147 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 30.709 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r2_timeout_is_not_accepted_as_refusal | 18.874 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 18.828 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 18.865 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 8.199 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 5.278 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 5.576 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 5.882 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.498 | False | bnode059 |
| 772d45201515c46abc25d6a038e45966 | ungrouped | 0 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.007 | False | bnode059 |
| 792a5f0db0c597e80e0d09ebe66c05b2 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 23.093 | False | bnode015 |
| 7b08b2f79360f16b6570f2583be76007 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 23.263 | False | bnode055 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 38.04 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_swapped_r2_hex_values_fail_exact_binding | 41.28 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 30.12 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 30.073 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 30.127 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 51.767 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_repo_unchanged_claim_compares_target_content_digests | 58.874 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 57.867 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 46.659 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 57.61 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_request_receipt_accepts_measured_qstat_layout | 41.129 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_request_receipt_rejects_wrong_owner_or_non_active_state[different-owner] | 30.212 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 40.847 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_atomic_result_publish_is_create_only | 50.441 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 53.742 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 50.085 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_repository_local_evidence_directory_is_rejected | 49.577 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 45.535 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 59.72 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 30.173 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 30.215 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[rc-zero-but-absent] | 30.22 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 0.0 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 59.075 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 58.023 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 56.931 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r3_manifest_rejects_nonliteral_ambient_approval | 58.134 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[body-present-rc-failed] | 0.0 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 44.593 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 49.212 | True | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_submitter_text_is_outside_execution_inventory | 39.564 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 40.966 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 42.423 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 37.999 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 38.027 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_group_intent_is_create_only_and_has_no_completion_fields | 16.58 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 28.727 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 28.722 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 16.451 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 28.727 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r2_timeout_is_not_accepted_as_refusal | 28.726 | False | bnode114 |
| 8212f02c4c4d72b9b81939b989c81ed2 | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 7.093 | False | bnode114 |
| 86438c4d22aaa4b3512231ddb6b1c81a | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.812 | False | bnode072 |
| 8b0890b98436fb8be10f39b671b024be | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.365 | False | bnode060 |
| 8d5a2f361e24ee3b80e0e7b4ed86fa71 | real-repo | 0 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 9.066 | False | bnode112 |
| 8e94b125ef46a86c899fdcb9e775059b | real-repo | 2 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 9.006 | False | bnode014 |
| 916c1cd50105b81544ad1b18e00a9675 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.817 | False | bnode021 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 40.035 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_swapped_r2_hex_values_fail_exact_binding | 41.885 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 30.086 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 30.138 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 30.155 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_repo_unchanged_claim_compares_target_content_digests | 30.2 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_pbs_preserves_one_valid_negative_observer_result | 0.0 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 49.796 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[unparseable-json] | 30.265 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_submitter_preflight_parses_gen_s_semantic_state[disabled] | 0.001 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_submitter_preflight_parses_gen_s_semantic_state[missing-gen-s] | 0.0 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 30.28 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 30.383 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_request_receipt_accepts_measured_qstat_layout | 35.637 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_request_receipt_rejects_wrong_owner_or_non_active_state[different-owner] | 35.692 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 45.528 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 42.586 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_atomic_result_publish_is_create_only | 48.891 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 0.0 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 46.181 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_repository_local_evidence_directory_is_rejected | 49.677 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 58.419 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 55.925 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 56.846 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 51.392 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 43.139 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_request_receipt_binds_qstat_body_visibility[rc-zero-but-absent] | 43.363 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 51.917 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 43.014 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r3_manifest_rejects_nonliteral_ambient_approval | 44.342 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_request_receipt_binds_qstat_body_visibility[body-present-rc-failed] | 0.0 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 44.174 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 45.782 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_submitter_text_is_outside_execution_inventory | 36.555 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 41.55 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 42.722 | True | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 28.952 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 28.954 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 32.22 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 32.211 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 32.228 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 32.24 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 20.55 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_group_intent_is_create_only_and_has_no_completion_fields | 19.651 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r2_timeout_is_not_accepted_as_refusal | 9.912 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 7.417 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 15.256 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_pbs_contract_runs_observer_through_single_result_call_block | 9.746 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 12.455 | False | bnode050 |
| a4ded6951baf937c43d94745f399ce38 | ungrouped | 6 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 7.085 | False | bnode050 |
| a6f7c71c1fbf910b85a1f0419134b523 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 9.045 | False | bnode108 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_submission_source_digests_are_bound_to_runtime_bytes[campaign-bytes] | 10.949 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 10.298 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_swapped_r2_hex_values_fail_exact_binding | 11.856 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 25.076 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_repo_unchanged_claim_compares_target_content_digests | 25.24 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 22.848 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[unparseable-json] | 23.639 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 19.353 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 18.998 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 20.202 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 17.106 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 21.889 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_request_receipt_accepts_measured_qstat_layout | 16.128 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_repository_local_evidence_directory_is_rejected | 14.056 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 21.083 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 15.659 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 19.516 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_atomic_result_publish_is_create_only | 15.427 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 20.379 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 14.267 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 14.274 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 14.273 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 14.28 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_group_intent_is_create_only_and_has_no_completion_fields | 14.372 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r2_timeout_is_not_accepted_as_refusal | 30.054 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 30.05 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 17.071 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 21.765 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_submitter_text_is_outside_execution_inventory | 12.457 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 22.323 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 21.772 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 20.89 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 16.147 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 25.44 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 19.874 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_request_receipt_binds_qstat_body_visibility[rc-zero-but-absent] | 21.767 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 14.84 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 24.914 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 27.321 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r3_manifest_rejects_nonliteral_ambient_approval | 21.337 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.022 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 4.151 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 6.2 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 6.297 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.878 | False | bnode029 |
| ad7a2a5489be9c511045d777a7828fa0 | ungrouped | 3 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.882 | False | bnode029 |
| af35189c8facc2eb00eebc87bc1c5958 | real-repo | 0 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 5.137 | False | bnode078 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_submission_source_digests_are_bound_to_runtime_bytes[campaign-bytes] | 20.509 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 20.653 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_swapped_r2_hex_values_fail_exact_binding | 21.382 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 51.45 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 50.931 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_submitter_preflight_parses_gen_s_semantic_state[missing-gen-s] | 52.816 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 49.329 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 56.267 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 54.256 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_repo_unchanged_claim_compares_target_content_digests | 57.073 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_request_receipt_rejects_wrong_owner_or_non_active_state[different-owner] | 43.438 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_request_receipt_accepts_measured_qstat_layout | 41.037 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 38.167 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 38.22 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 34.011 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_repository_local_evidence_directory_is_rejected | 39.194 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 44.214 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 39.014 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_atomic_result_publish_is_create_only | 39.996 | True | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 39.474 | True | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 43.94 | True | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 44.206 | True | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 43.677 | True | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 47.118 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 38.239 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r3_manifest_rejects_nonliteral_ambient_approval | 44.37 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[body-present-rc-failed] | 44.372 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 48.36 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 50.076 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_request_receipt_binds_qstat_body_visibility[rc-zero-but-absent] | 47.112 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 31.376 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 37.341 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_submitter_text_is_outside_execution_inventory | 29.595 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 25.025 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 20.043 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 20.044 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r2_timeout_is_not_accepted_as_refusal | 20.037 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 20.042 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_group_intent_is_create_only_and_has_no_completion_fields | 20.131 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 14.383 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 7.233 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 6.996 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 14.85 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 12.892 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_pbs_contract_runs_observer_through_single_result_call_block | 10.397 | False | bnode034 |
| b24821a39b6bb7041851237003b786e3 | ungrouped | 2 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 6.163 | False | bnode034 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 10.166 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_swapped_r2_hex_values_fail_exact_binding | 12.111 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 26.59 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_submitter_preflight_parses_gen_s_semantic_state[missing-gen-s] | 25.899 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 27.179 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_repo_unchanged_claim_compares_target_content_digests | 27.566 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 22.628 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 18.404 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 20.695 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_request_receipt_accepts_measured_qstat_layout | 14.647 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 21.325 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 22.696 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_repository_local_evidence_directory_is_rejected | 16.138 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 15.342 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 24.208 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 25.732 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_atomic_result_publish_is_create_only | 23.52 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 23.187 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 20.758 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 38.559 | True | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 36.271 | True | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 36.277 | True | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 36.267 | True | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 35.776 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 35.79 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 31.139 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r2_timeout_is_not_accepted_as_refusal | 35.789 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 34.529 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 31.564 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 30.484 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 19.664 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 22.153 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 26.57 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 22.263 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 22.01 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_request_receipt_binds_qstat_body_visibility[body-present-rc-failed] | 22.03 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r3_manifest_rejects_nonliteral_ambient_approval | 21.777 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_submitter_text_is_outside_execution_inventory | 11.976 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 13.502 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_group_intent_is_create_only_and_has_no_completion_fields | 11.254 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.151 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 5.733 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 6.087 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_pbs_contract_runs_observer_through_single_result_call_block | 4.065 | False | bnode140 |
| b37b3251dfc8435ef330b20a738c2df5 | ungrouped | 7 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.287 | False | bnode140 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 9.55 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_swapped_r2_hex_values_fail_exact_binding | 10.966 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_submission_source_digests_are_bound_to_runtime_bytes[campaign-bytes] | 10.791 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 23.341 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 20.377 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_repo_unchanged_claim_compares_target_content_digests | 23.894 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[unparseable-json] | 21.91 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 18.53 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 19.012 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 17.708 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 15.657 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 19.962 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_repository_local_evidence_directory_is_rejected | 13.342 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 14.104 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 18.011 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 18.938 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_atomic_result_publish_is_create_only | 19.471 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 19.285 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 17.032 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 17.033 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 13.264 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 11.842 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 27.794 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 27.82 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r2_timeout_is_not_accepted_as_refusal | 27.817 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 24.994 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 25.293 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 23.447 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[rc-zero-but-absent] | 23.507 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r3_manifest_rejects_nonliteral_ambient_approval | 22.966 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_submitter_text_is_outside_execution_inventory | 14.387 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 16.63 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 15.246 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 20.595 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[body-present-rc-failed] | 22.892 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 23.476 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 23.828 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 25.738 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_group_intent_is_create_only_and_has_no_completion_fields | 5.935 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.004 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 5.415 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 5.841 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.746 | False | bnode029 |
| b6162dafa84bc674704a2a13f342d40c | ungrouped | 0 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.076 | False | bnode029 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_swapped_r2_hex_values_fail_exact_binding | 12.222 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 10.779 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 18.601 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 20.299 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_submitter_preflight_parses_gen_s_semantic_state[disabled] | 22.416 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_repo_unchanged_claim_compares_target_content_digests | 22.426 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 13.616 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 15.747 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 17.954 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 17.35 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 18.346 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_repository_local_evidence_directory_is_rejected | 13.219 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 13.326 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 12.643 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 24.897 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 25.029 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_atomic_result_publish_is_create_only | 20.807 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 20.861 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 21.819 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 33.192 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 30.073 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_group_intent_is_create_only_and_has_no_completion_fields | 30.163 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 31.017 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 26.906 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 27.416 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r2_timeout_is_not_accepted_as_refusal | 31.957 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 29.746 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 26.218 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_submitter_text_is_outside_execution_inventory | 12.544 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 22.78 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_request_receipt_rejects_wrong_owner_or_non_active_state[terminal-state] | 20.88 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 20.919 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 18.609 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r3_manifest_rejects_nonliteral_ambient_approval | 18.653 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 12.763 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 12.904 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 16.39 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 6.292 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.175 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 5.639 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 5.933 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.909 | False | bnode006 |
| bafb8fd26979e25cf366dd349d2d0335 | ungrouped | 3 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.19 | False | bnode006 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_swapped_r2_hex_values_fail_exact_binding | 12.352 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 10.869 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 23.533 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_submitter_preflight_parses_gen_s_semantic_state[missing-gen-s] | 23.464 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 26.538 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_repo_unchanged_claim_compares_target_content_digests | 24.708 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 20.381 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 18.411 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 18.581 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 20.588 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 16.219 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_repository_local_evidence_directory_is_rejected | 14.153 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 26.547 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name-queued] | 27.018 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_atomic_result_publish_is_create_only | 26.021 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 28.589 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 26.041 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 23.955 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 38.983 | True | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 35.584 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 35.578 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 35.16 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 29.297 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 29.846 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 31.866 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 25.409 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_request_receipt_binds_qstat_body_visibility[rc-zero-but-absent] | 25.349 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 26.353 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 25.558 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r3_manifest_rejects_nonliteral_ambient_approval | 24.887 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_request_receipt_rejects_wrong_owner_or_non_active_state[non-active-state] | 18.466 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_submitter_text_is_outside_execution_inventory | 15.622 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 19.808 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 16.761 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 11.334 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r2_timeout_is_not_accepted_as_refusal | 11.333 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_group_intent_is_create_only_and_has_no_completion_fields | 11.424 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 4.883 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.132 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 7.811 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 6.317 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_pbs_contract_runs_observer_through_single_result_call_block | 3.967 | False | bnode009 |
| c85e84993335fc80c0f57d1b677a20f8 | ungrouped | 1 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 4.399 | False | bnode009 |
| d32ec36aa639ef3ec60ec0964db23a25 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 10.735 | False | bnode014 |
| da379915ed116c8b5c6937cbe325b601 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 9.195 | False | bnode009 |
| de52a7377fc52d012079f743efb601c4 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 4.624 | False | bnode079 |
| e818446e399fe09320c86bccd7f27afb | real-repo | 0 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.277 | False | bnode021 |
| f4b4518824c4f2497f80aa8f6f03e8ac | real-repo | 2 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 8.009 | False | bnode081 |
| faf48e0e8f80aea69abd7fe155053925 | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 11.321 | False | bnode009 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_SUBMISSION_NONCE] | 16.048 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_swapped_r2_hex_values_fail_exact_binding | 17.766 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[detached-False] | 24.416 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_repo_unchanged_claim_compares_target_content_digests | 21.333 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_FLOOR_JOB_EVIDENCE_ROOT] | 20.555 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_submitter_preflight_parses_gen_s_semantic_state[disabled] | 20.103 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal | 18.951 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r1_binds_all_three_explicit_values_and_skips_real_driver | 17.467 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r3_records_only_the_observed_ambient_approval_condition[not-delivered] | 17.128 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r1_projection_follows_observed_approval_not_request_identity[approval-mismatch] | 19.29 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r3_records_only_the_observed_ambient_approval_condition[delivered-mismatching-literal] | 19.259 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_repository_local_evidence_directory_is_rejected | 14.812 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_submitter_has_exact_three_request_design_and_create_only_witnesses | 15.766 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_atomic_result_publish_is_create_only | 24.956 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r2_unexpected_approval_presence_is_unbound_and_not_green | 28.452 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_main_emits_one_prefixed_stdout_line_and_auxiliary_result | 24.424 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r1_manifest_rejects_approval_that_does_not_equal_nonce | 29.441 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[tracked_status- M orchestrator/campaign/s8b_floor_campaign.py\n] | 37.076 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-bad_value3] | 31.132 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_submission_source_digests_are_bound_to_runtime_bytes[repo-pbs-bytes] | 31.546 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-immediate-staging] | 31.907 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_submitter_preflight_parses_gen_s_semantic_state[enabled] | 34.494 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_pbs_early_ulimit_failure_emits_one_prefixed_result | 25.029 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[no-output-nonzero] | 27.023 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_missing_r1_explicit_value_cannot_be_green[IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN] | 25.081 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[rc-zero-but-absent] | 27.053 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r3_manifest_rejects_nonliteral_ambient_approval | 21.851 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_pbs_replaces_invalid_observer_stdout_with_one_fallback[two-prefixed-lines] | 28.413 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[body-present-rc-failed] | 21.956 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_submitter_text_is_outside_execution_inventory | 13.096 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_request_receipt_binds_qstat_body_visibility[visible-eight-char-name] | 21.074 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[wrong-mode] | 15.015 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r2_timeout_is_not_accepted_as_refusal | 10.329 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r1_projection_follows_observed_approval_not_request_identity[approval-missing] | 10.333 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match | 10.317 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_job_start_requires_manifest_head_detached_and_clean_repository[head-0000000000000000000000000000000000000000] | 10.331 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_group_intent_is_create_only_and_has_no_completion_fields | 4.709 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[extra-argv] | 4.121 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract | 9.494 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_submission_source_digests_are_bound_to_runtime_bytes[executing-pbs-bytes] | 6.828 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_pbs_contract_runs_observer_through_single_result_call_block | 4.178 | False | bnode059 |
| fbc809ecc5b11c8aff6e13260f48554c | ungrouped | 5 | test_r2_refusal_rejects_any_driver_argv_mutation[approval-flag] | 3.627 | False | bnode059 |
| fcc43198a07a3e3e624b30c0a347e96d | real-repo | 1 | test_r1_binds_all_three_explicit_values_and_skips_real_driver@real-repo | 15.368 | False | bnode050 |
