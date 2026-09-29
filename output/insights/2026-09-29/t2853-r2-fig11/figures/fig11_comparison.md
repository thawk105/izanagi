# Figure 11: separate attempt comparison

Each attempt is evaluated separately. No samples are pooled and no between-attempt effect is computed.

| attempt | request | host | source commit | CCBench pin | nodes (policy / receipt) | effects.rr95 | outer_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| original: a6-20260908b | 982234.nqsv | bnode031 | ae8a767eb60118c3f9791141603fa01ad4f28406 | 511c953 | policy 1; receipt 1 | -0.057841193339621455 | reject |
| R2: a6-r2-20260929a | 35349.nqsv | bnode087 | 035fc11fa601547f5d68e54f5661c5daa70b93a5 | 6810666 | policy 5; receipt 5 | -0.05214379860989382 | reject |

| attempt | cell | role | 5 trace-disabled TPS samples | median TPS | mean TPS ± t95 CI half-width (df=4) | representative abort rate | correctness status | anomalies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original: a6-20260908b | rr95-stock | stock | 10365808.0, 10103030.0, 10029940.0, 10088796.0, 10073679.0 | 10088796.0 | 10132250.6 ± 165646.18668188356 | 0.1547 | certified | 0 |
| original: a6-20260908b | rr95-fixed2 | adopted | 9753031.0, 9587735.0, 9488225.0, 9494008.0, 9505248.0 | 9505248.0 | 9565649.4 ± 139341.85904304445 | 0.145 | certified | 0 |
| R2: a6-r2-20260929a | rr95-stock | stock | 10632564.0, 10325830.0, 10361900.0, 10281088.0, 10315111.0 | 10325830.0 | 10383298.6 ± 176681.34296741674 | 0.1554 | certified | 0 |
| R2: a6-r2-20260929a | rr95-fixed2 | adopted | 9961007.0, 9787402.0, 9778168.0, 9790839.0, 9739453.0 | 9787402.0 | 9811373.8 ± 106923.14386151911 | 0.1445 | certified | 0 |
