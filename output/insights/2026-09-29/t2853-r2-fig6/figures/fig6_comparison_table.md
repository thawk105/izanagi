# A-2 attempt comparison

## Attempts

| Attempt | ID | Outer status | current_pin | Izanagi source commit | protocol_sha256[:12] | Workload: request / host / recorded UTC | Toolchain | Correctness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Original | t2364-20260907b | observed-positive | 511c953 | 31ec382a7841e188e46f93e8de4261c964facfb2 | 136b823e60a4 | rr5: 981476.nqsv / bnode077 / 2026-09-07T12:12:55.607184+00:00<br>rr50: 981477.nqsv / bnode085 / 2026-09-07T12:12:55.388302+00:00 | cc: x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0; cxx: x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0; cmake: cmake version 3.22.1 | 4/4 certified; legacy 1, performance 5 repetitions |
| R2 | t2853r2-20260929a | observed-positive | 6810666 | 035fc11fa601547f5d68e54f5661c5daa70b93a5 | d99f08bcc50c | rr5: 35310.nqsv / bnode104 / 2026-09-29T06:00:17.909493+00:00<br>rr50: 35327.nqsv / bnode084 / 2026-09-29T06:01:00.688611+00:00 | cc: x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0; cxx: x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0; cmake: cmake version 3.22.1 | 4/4 certified; legacy 1, performance 5 repetitions |

## Cells

Throughput and t 95% CI half width are in transactions per second; CV and abort rate are fractions.

| Workload | Cell ID | Role | Genome | Original: median; mean; CI; CV; abort | R2: median; mean; CI; CV; abort |
| --- | --- | --- | --- | --- | --- |
| rr5 | rr5-stock | stock / stock | original {"BACKOFF_FIXED": -1, "BACK_OFF": 0}; R2 {"BACKOFF_FIXED": -1, "BACK_OFF": 0} | median 2438295; mean 2462838.6; CI ±99765.5912601; CV 0.0326242652952; abort 0.7845 | median 2405931; mean 2436289.4; CI ±113267.502074; CV 0.0374431483252; abort 0.788 |
| rr5 | rr5-fixed10 | adopted / adopted | original {"BACKOFF_FIXED": 10, "BACK_OFF": 1}; R2 {"BACKOFF_FIXED": 10, "BACK_OFF": 1} | median 3987794; mean 4004505; CI ±45583.8315969; CV 0.00916764733208; abort 0.3833 | median 3979720; mean 3981584.2; CI ±46261.27445; CV 0.0093574518182; abort 0.3837 |
| rr50 | rr50-stock | stock / stock | original {"BACKOFF_FIXED": -1, "BACK_OFF": 0}; R2 {"BACKOFF_FIXED": -1, "BACK_OFF": 0} | median 3756230; mean 3808422; CI ±138475.240134; CV 0.029283499309; abort 0.685 | median 3813280; mean 3881173.4; CI ±187725.84642; CV 0.0389544373523; abort 0.684 |
| rr50 | rr50-fixed5 | adopted / adopted | original {"BACKOFF_FIXED": 5, "BACK_OFF": 1}; R2 {"BACKOFF_FIXED": 5, "BACK_OFF": 1} | median 4297929; mean 4302525; CI ±58456.6958578; CV 0.0109422535182; abort 0.4615 | median 4305015; mean 4329303.6; CI ±59543.4967257; CV 0.0110767461692; abort 0.4623 |

## Median-ratio effects

| Workload | Original certification effect | Original computed crosscheck | R2 certification effect | R2 computed crosscheck |
| --- | --- | --- | --- | --- |
| rr5 | 0.635484631679 | 0.635484631679 | 0.654128900621 | 0.654128900621 |
| rr50 | 0.144213480005 | 0.144213480005 | 0.128953289556 | 0.128953289556 |

2 attempt の値は別々に読んだもので合成していない。数値の近さを再現精度として評価しない。
