# B-10 backoff shape report

- official certification: `false`
- preregistration binding: `24d80d9a35122de1d6ecd8a7d0244c439434452e94418fa35d34a48169b9f483`
- preregistration spec SHA-256: `9c59411476018d510c8fc5d57f203920ccd3b216e6c5f341ce6b97e45041a7c2`
- analysis code: `2a338449bb2798b729c5bc2f9bfe76463a7fe347` / `b15c35480f50e73a440be0a734e7247f9ca56f17df58d86a4cdb1752fb214dd9`
- submission request: `978195.nqsv` (`93a1cd74ce279c6c8c876a7ab60fb772b216f25cf59f4eff70d0b0e2b8b429b4`)
- records: `1000000` (calibration artifact)
- exposure minimum: `10000` abort/backoff calls per cell

## Performance cell completeness

- expected / observed: `135` / `135`
- the exact 135-cell gate does not prove that all three workload jobs terminated
- job termination is guaranteed by submission sequencing after all three workload jobs terminate; there is no mechanical termination gate
- write-heavy: `b10-backoff-shape-silo-write-heavy-formal-e3de15eb` (45 cells)
- balanced: `b10-backoff-shape-silo-balanced-formal-143a3f74` (45 cells)
- read-heavy: `b10-backoff-shape-silo-read-heavy-formal-acf840c8` (45 cells)

## Verification slot completeness

- expected / completed / incomplete: `270` / `270` / `0`
- counting rule: count verify_done by (workload, variant, verify_tag), capped only for slot projection
- known limitation: duplicate WAL frames and distinct repetitions cannot be distinguished because verify_done has no repetition identity
- write-heavy: `b10-backoff-shape-silo-write-heavy-formal-e3de15eb`; verify_done=90; completed_logical_slots=90; tags={'legacy': 15, 'performance': 75}; truncated_tail=False; unknown_tags={}; unknown_tag_values=[]; overruns=[]; wal_error=None
- balanced: `b10-backoff-shape-silo-balanced-formal-143a3f74`; verify_done=90; completed_logical_slots=90; tags={'legacy': 15, 'performance': 75}; truncated_tail=False; unknown_tags={}; unknown_tag_values=[]; overruns=[]; wal_error=None
- read-heavy: `b10-backoff-shape-silo-read-heavy-formal-acf840c8`; verify_done=90; completed_logical_slots=90; tags={'legacy': 15, 'performance': 75}; truncated_tail=False; unknown_tags={}; unknown_tag_values=[]; overruns=[]; wal_error=None

Formal driver 経路について、登録前に性能を見ていないという限定主張だけを行う。

| workload | host | block | point | shape | mean us | median tps | CV | abort rate | abort count | backoff calls | calls/s | nominal total wait us | correctness certified | unstable | exposure |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| balanced | bnode015 | block-1 | none | — | — | 3652963 | 0.0231 | 0.6874 | 121545410 | 0 | 0.00 | — | yes | no | indeterminate |
| balanced | bnode015 | block-1 | adaptive | — | — | 1253516 | 0.0336 | 0.2115 | 5012955 | 5012955 | 334197.00 | — | yes | no | met |
| balanced | bnode015 | block-1 | zero-loop | constant | 0 | 3676625 | 0.0097 | 0.6833 | 118701222 | 118701222 | 7913414.80 | 0 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu2 | constant | 2 | 4187219 | 0.0106 | 0.5634 | 81244885 | 81244885 | 5416325.67 | 162489770 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 4221855 | 0.0047 | 0.5633 | 81484350 | 81484350 | 5432290.00 | 162968700 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 4172133 | 0.0064 | 0.4672 | 54809545 | 54809545 | 3653969.67 | 274047725 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu5 | constant | 5 | 4167860 | 0.0058 | 0.4687 | 55072049 | 55072049 | 3671469.93 | 275360245 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu10 | constant | 10 | 3813996 | 0.0040 | 0.3893 | 36475711 | 36475711 | 2431714.07 | 364757110 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3847706 | 0.0020 | 0.3863 | 36369003 | 36369003 | 2424600.20 | 363690030 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3084737 | 0.0041 | 0.2891 | 18817078 | 18817078 | 1254471.87 | 470426950 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu25 | constant | 25 | 3004729 | 0.0238 | 0.2923 | 18538341 | 18538341 | 1235889.40 | 463458525 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu50 | constant | 50 | 2428183 | 0.0024 | 0.2272 | 10705046 | 10705046 | 713669.73 | 535252300 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2448502 | 0.0023 | 0.2250 | 10669776 | 10669776 | 711318.40 | 533488800 | yes | no | met |
| balanced | bnode015 | block-1 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 1879789 | 0.0026 | 0.1714 | 5834649 | 5834649 | 388976.60 | 583464900 | yes | no | met |
| balanced | bnode015 | block-1 | constant-mu100 | constant | 100 | 1860266 | 0.0032 | 0.1732 | 5844335 | 5844335 | 389622.33 | 584433500 | yes | no | met |
| balanced | bnode015 | block-2 | adaptive | — | — | 1232300 | 0.0255 | 0.2117 | 5025250 | 5025250 | 335016.67 | — | yes | no | met |
| balanced | bnode015 | block-2 | zero-loop | constant | 0 | 3656568 | 0.0121 | 0.6843 | 118760199 | 118760199 | 7917346.60 | 0 | yes | no | met |
| balanced | bnode015 | block-2 | none | — | — | 3586501 | 0.0095 | 0.6900 | 120199576 | 0 | 0.00 | — | yes | no | indeterminate |
| balanced | bnode015 | block-2 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 4198348 | 0.0081 | 0.5620 | 81082198 | 81082198 | 5405479.87 | 162164396 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu2 | constant | 2 | 4228433 | 0.0075 | 0.5622 | 81410765 | 81410765 | 5427384.33 | 162821530 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu5 | constant | 5 | 4180192 | 0.0030 | 0.4673 | 55026253 | 55026253 | 3668416.87 | 275131265 | yes | no | met |
| balanced | bnode015 | block-2 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 4199083 | 0.0070 | 0.4653 | 54900500 | 54900500 | 3660033.33 | 274502500 | yes | no | met |
| balanced | bnode015 | block-2 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3862252 | 0.0038 | 0.3864 | 36401759 | 36401759 | 2426783.93 | 364017590 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu10 | constant | 10 | 3814226 | 0.0038 | 0.3901 | 36545715 | 36545715 | 2436381.00 | 365457150 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu25 | constant | 25 | 3056567 | 0.0033 | 0.2919 | 18860673 | 18860673 | 1257378.20 | 471516825 | yes | no | met |
| balanced | bnode015 | block-2 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3079650 | 0.0039 | 0.2895 | 18813525 | 18813525 | 1254235.00 | 470338125 | yes | no | met |
| balanced | bnode015 | block-2 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2441075 | 0.0033 | 0.2256 | 10668446 | 10668446 | 711229.73 | 533422300 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu50 | constant | 50 | 2429818 | 0.0016 | 0.2270 | 10700591 | 10700591 | 713372.73 | 535029550 | yes | no | met |
| balanced | bnode015 | block-2 | constant-mu100 | constant | 100 | 1862902 | 0.0051 | 0.1730 | 5837823 | 5837823 | 389188.20 | 583782300 | yes | no | met |
| balanced | bnode015 | block-2 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 1880074 | 0.0017 | 0.1712 | 5828019 | 5828019 | 388534.60 | 582801900 | yes | no | met |
| balanced | bnode015 | block-3 | zero-loop | constant | 0 | 3618263 | 0.0050 | 0.6834 | 116995409 | 116995409 | 7799693.93 | 0 | yes | no | met |
| balanced | bnode015 | block-3 | none | — | — | 3572391 | 0.0107 | 0.6911 | 120029097 | 0 | 0.00 | — | yes | no | indeterminate |
| balanced | bnode015 | block-3 | adaptive | — | — | 1229420 | 0.0286 | 0.2089 | 4918601 | 4918601 | 327906.73 | — | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu2 | constant | 2 | 4180079 | 0.0055 | 0.5638 | 81150807 | 81150807 | 5410053.80 | 162301614 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 4234369 | 0.0071 | 0.5613 | 80992548 | 80992548 | 5399503.20 | 161985096 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 4192970 | 0.0279 | 0.4676 | 54594151 | 54594151 | 3639610.07 | 272970755 | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu5 | constant | 5 | 4200819 | 0.0102 | 0.4672 | 54975846 | 54975846 | 3665056.40 | 274879230 | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu10 | constant | 10 | 3809797 | 0.0058 | 0.3890 | 36512992 | 36512992 | 2434199.47 | 365129920 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3836308 | 0.0018 | 0.3871 | 36378287 | 36378287 | 2425219.13 | 363782870 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3083873 | 0.0019 | 0.2891 | 18807661 | 18807661 | 1253844.07 | 470191525 | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu25 | constant | 25 | 3062565 | 0.0047 | 0.2916 | 18856718 | 18856718 | 1257114.53 | 471417950 | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu50 | constant | 50 | 2424905 | 0.0023 | 0.2275 | 10702404 | 10702404 | 713493.60 | 535120200 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2445236 | 0.0030 | 0.2253 | 10661626 | 10661626 | 710775.07 | 533081300 | yes | no | met |
| balanced | bnode015 | block-3 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 1869508 | 0.0054 | 0.1718 | 5831209 | 5831209 | 388747.27 | 583120900 | yes | no | met |
| balanced | bnode015 | block-3 | constant-mu100 | constant | 100 | 1863479 | 0.0016 | 0.1729 | 5843456 | 5843456 | 389563.73 | 584345600 | yes | no | met |
| read-heavy | bnode088 | block-1 | none | — | — | 10311699 | 0.0095 | 0.1549 | 28470693 | 0 | 0.00 | — | yes | no | indeterminate |
| read-heavy | bnode088 | block-1 | adaptive | — | — | 2323131 | 0.0085 | 0.0402 | 1460201 | 1460201 | 97346.73 | — | yes | no | met |
| read-heavy | bnode088 | block-1 | zero-loop | constant | 0 | 10198102 | 0.0047 | 0.1539 | 27795829 | 27795829 | 1853055.27 | 0 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu2 | constant | 2 | 9630186 | 0.0028 | 0.1447 | 24423602 | 24423602 | 1628240.13 | 48847204 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 9718203 | 0.0031 | 0.1446 | 24639061 | 24639061 | 1642604.07 | 49278122 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 9102850 | 0.0027 | 0.1339 | 21087198 | 21087198 | 1405813.20 | 105435990 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu5 | constant | 5 | 9017765 | 0.0012 | 0.1349 | 21081311 | 21081311 | 1405420.73 | 105406555 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu10 | constant | 10 | 8232900 | 0.0048 | 0.1227 | 17250734 | 17250734 | 1150048.93 | 172507340 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 8255918 | 0.0033 | 0.1216 | 17122746 | 17122746 | 1141516.40 | 171227460 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 6899590 | 0.0017 | 0.0994 | 11430533 | 11430533 | 762035.53 | 285763325 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu25 | constant | 25 | 6867054 | 0.0023 | 0.1002 | 11469100 | 11469100 | 764606.67 | 286727500 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu50 | constant | 50 | 5651380 | 0.0014 | 0.0815 | 7520706 | 7520706 | 501380.40 | 376035300 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 5669177 | 0.0019 | 0.0810 | 7486903 | 7486903 | 499126.87 | 374345150 | yes | no | met |
| read-heavy | bnode088 | block-1 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 4473432 | 0.0022 | 0.0633 | 4535535 | 4535535 | 302369.00 | 453553500 | yes | no | met |
| read-heavy | bnode088 | block-1 | constant-mu100 | constant | 100 | 4459835 | 0.0019 | 0.0638 | 4554715 | 4554715 | 303647.67 | 455471500 | yes | no | met |
| read-heavy | bnode088 | block-2 | adaptive | — | — | 2327468 | 0.0064 | 0.0400 | 1451693 | 1451693 | 96779.53 | — | yes | no | met |
| read-heavy | bnode088 | block-2 | zero-loop | constant | 0 | 10132409 | 0.0041 | 0.1539 | 27600091 | 27600091 | 1840006.07 | 0 | yes | no | met |
| read-heavy | bnode088 | block-2 | none | — | — | 10179288 | 0.0033 | 0.1549 | 27960631 | 0 | 0.00 | — | yes | no | indeterminate |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 9674282 | 0.0031 | 0.1444 | 24483970 | 24483970 | 1632264.67 | 48967940 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu2 | constant | 2 | 9631925 | 0.0023 | 0.1447 | 24440757 | 24440757 | 1629383.80 | 48881514 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu5 | constant | 5 | 9005092 | 0.0022 | 0.1350 | 21075893 | 21075893 | 1405059.53 | 105379465 | yes | no | met |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 9048083 | 0.0032 | 0.1339 | 20991815 | 20991815 | 1399454.33 | 104959075 | yes | no | met |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 8220868 | 0.0073 | 0.1218 | 17070086 | 17070086 | 1138005.73 | 170700860 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu10 | constant | 10 | 8215784 | 0.0050 | 0.1226 | 17206917 | 17206917 | 1147127.80 | 172069170 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu25 | constant | 25 | 6844838 | 0.0017 | 0.1004 | 11452259 | 11452259 | 763483.93 | 286306475 | yes | no | met |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 6898605 | 0.0026 | 0.0995 | 11446665 | 11446665 | 763111.00 | 286166625 | yes | no | met |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 5670159 | 0.0018 | 0.0809 | 7484550 | 7484550 | 498970.00 | 374227500 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu50 | constant | 50 | 5651461 | 0.0024 | 0.0814 | 7508840 | 7508840 | 500589.33 | 375442000 | yes | no | met |
| read-heavy | bnode088 | block-2 | constant-mu100 | constant | 100 | 4452598 | 0.0029 | 0.0639 | 4557727 | 4557727 | 303848.47 | 455772700 | yes | no | met |
| read-heavy | bnode088 | block-2 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 4477590 | 0.0011 | 0.0633 | 4537706 | 4537706 | 302513.73 | 453770600 | yes | no | met |
| read-heavy | bnode088 | block-3 | zero-loop | constant | 0 | 10133586 | 0.0057 | 0.1539 | 27573535 | 27573535 | 1838235.67 | 0 | yes | no | met |
| read-heavy | bnode088 | block-3 | none | — | — | 10158776 | 0.0034 | 0.1547 | 27898034 | 0 | 0.00 | — | yes | no | indeterminate |
| read-heavy | bnode088 | block-3 | adaptive | — | — | 2326305 | 0.0075 | 0.0405 | 1479465 | 1479465 | 98631.00 | — | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu2 | constant | 2 | 9618673 | 0.0018 | 0.1450 | 24479065 | 24479065 | 1631937.67 | 48958130 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 9674916 | 0.0026 | 0.1445 | 24524138 | 24524138 | 1634942.53 | 49048276 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 9040824 | 0.0029 | 0.1341 | 20995570 | 20995570 | 1399704.67 | 104977850 | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu5 | constant | 5 | 9020648 | 0.0030 | 0.1348 | 21103528 | 21103528 | 1406901.87 | 105517640 | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu10 | constant | 10 | 8204568 | 0.0060 | 0.1227 | 17193604 | 17193604 | 1146240.27 | 171936040 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 8226320 | 0.0050 | 0.1216 | 17091221 | 17091221 | 1139414.73 | 170912210 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 6910847 | 0.0014 | 0.0995 | 11452746 | 11452746 | 763516.40 | 286318650 | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu25 | constant | 25 | 6852143 | 0.0028 | 0.1002 | 11451239 | 11451239 | 763415.93 | 286280975 | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu50 | constant | 50 | 5642522 | 0.0030 | 0.0815 | 7509987 | 7509987 | 500665.80 | 375499350 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 5672363 | 0.0009 | 0.0809 | 7488458 | 7488458 | 499230.53 | 374422900 | yes | no | met |
| read-heavy | bnode088 | block-3 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 4477951 | 0.0009 | 0.0633 | 4540249 | 4540249 | 302683.27 | 454024900 | yes | no | met |
| read-heavy | bnode088 | block-3 | constant-mu100 | constant | 100 | 4458944 | 0.0008 | 0.0638 | 4557110 | 4557110 | 303807.33 | 455711000 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | none | — | — | 2422011 | 0.0322 | 0.7849 | 134719086 | 0 | 0.00 | — | yes | no | indeterminate |
| write-heavy | not-recorded-legacy-v2 | block-1 | adaptive | — | — | 1354088 | 0.0179 | 0.1221 | 2830938 | 2830938 | 188729.20 | — | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | zero-loop | constant | 0 | 2439674 | 0.0083 | 0.7818 | 130595054 | 130595054 | 8706336.93 | 0 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu2 | constant | 2 | 3454217 | 0.0074 | 0.6364 | 90469377 | 90469377 | 6031291.80 | 180938754 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 3415244 | 0.0092 | 0.6350 | 89221334 | 89221334 | 5948088.93 | 178442668 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 3923154 | 0.0056 | 0.5006 | 58974695 | 58974695 | 3931646.33 | 294873475 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu5 | constant | 5 | 3982673 | 0.0200 | 0.4990 | 58789077 | 58789077 | 3919271.80 | 293945385 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu10 | constant | 10 | 3924247 | 0.0044 | 0.3873 | 37256513 | 37256513 | 2483767.53 | 372565130 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3932174 | 0.0034 | 0.3862 | 37156234 | 37156234 | 2477082.27 | 371562340 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3505891 | 0.0068 | 0.2586 | 18271151 | 18271151 | 1218076.73 | 456778775 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu25 | constant | 25 | 3430191 | 0.0046 | 0.2631 | 18381750 | 18381750 | 1225450.00 | 459543750 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu50 | constant | 50 | 2904761 | 0.0041 | 0.1915 | 10318030 | 10318030 | 687868.67 | 515901500 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2952224 | 0.0036 | 0.1882 | 10250505 | 10250505 | 683367.00 | 512525250 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 2375988 | 0.0029 | 0.1357 | 5599704 | 5599704 | 373313.60 | 559970400 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-1 | constant-mu100 | constant | 100 | 2346648 | 0.0044 | 0.1376 | 5623103 | 5623103 | 374873.53 | 562310300 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | adaptive | — | — | 1356456 | 0.0098 | 0.1247 | 2918754 | 2918754 | 194583.60 | — | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | zero-loop | constant | 0 | 2428482 | 0.0166 | 0.7834 | 130553071 | 130553071 | 8703538.07 | 0 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | none | — | — | 2386915 | 0.0097 | 0.7906 | 135235525 | 0 | 0.00 | — | yes | no | indeterminate |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 3434411 | 0.0152 | 0.6353 | 89880322 | 89880322 | 5992021.47 | 179760644 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu2 | constant | 2 | 3375498 | 0.0144 | 0.6388 | 90148296 | 90148296 | 6009886.40 | 180296592 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu5 | constant | 5 | 3951087 | 0.0044 | 0.5000 | 59341088 | 59341088 | 3956072.53 | 296705440 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 3924361 | 0.0075 | 0.5001 | 58827499 | 58827499 | 3921833.27 | 294137495 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3950786 | 0.0038 | 0.3852 | 37084422 | 37084422 | 2472294.80 | 370844220 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu10 | constant | 10 | 3955909 | 0.0028 | 0.3849 | 37129418 | 37129418 | 2475294.53 | 371294180 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu25 | constant | 25 | 3444681 | 0.0024 | 0.2622 | 18345577 | 18345577 | 1223038.47 | 458639425 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3467458 | 0.0056 | 0.2601 | 18319305 | 18319305 | 1221287.00 | 457982625 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2948141 | 0.0043 | 0.1883 | 10246320 | 10246320 | 683088.00 | 512316000 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu50 | constant | 50 | 2916249 | 0.0031 | 0.1907 | 10302119 | 10302119 | 686807.93 | 515105950 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | constant-mu100 | constant | 100 | 2353744 | 0.0019 | 0.1373 | 5620589 | 5620589 | 374705.93 | 562058900 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-2 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 2378941 | 0.0014 | 0.1356 | 5600801 | 5600801 | 373386.73 | 560080100 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | zero-loop | constant | 0 | 2355992 | 0.0262 | 0.7872 | 132217987 | 132217987 | 8814532.47 | 0 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | none | — | — | 2380088 | 0.0122 | 0.7896 | 133974270 | 0 | 0.00 | — | yes | no | indeterminate |
| write-heavy | not-recorded-legacy-v2 | block-3 | adaptive | — | — | 1375023 | 0.0119 | 0.1255 | 2967792 | 2967792 | 197852.80 | — | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu2 | constant | 2 | 3373450 | 0.0078 | 0.6407 | 90258398 | 90258398 | 6017226.53 | 180516796 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu2 | symmetric-modulo | 2 | 3427953 | 0.0079 | 0.6361 | 89686236 | 89686236 | 5979082.40 | 179372472 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu5 | symmetric-modulo | 5 | 3918943 | 0.0099 | 0.5007 | 58883537 | 58883537 | 3925569.13 | 294417685 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu5 | constant | 5 | 3948581 | 0.0049 | 0.4999 | 59291149 | 59291149 | 3952743.27 | 296455745 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu10 | constant | 10 | 3916268 | 0.0082 | 0.3868 | 37203056 | 37203056 | 2480203.73 | 372030560 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu10 | symmetric-modulo | 10 | 3959094 | 0.0067 | 0.3849 | 37048838 | 37048838 | 2469922.53 | 370488380 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu25 | symmetric-modulo | 25 | 3484569 | 0.0040 | 0.2595 | 18303393 | 18303393 | 1220226.20 | 457584825 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu25 | constant | 25 | 3451158 | 0.0049 | 0.2619 | 18360901 | 18360901 | 1224060.07 | 459022525 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu50 | constant | 50 | 2919663 | 0.0033 | 0.1905 | 10301616 | 10301616 | 686774.40 | 515080800 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu50 | symmetric-modulo | 50 | 2940961 | 0.0047 | 0.1883 | 10246544 | 10246544 | 683102.93 | 512327200 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | symmetric-modulo-mu100 | symmetric-modulo | 100 | 2381736 | 0.0010 | 0.1355 | 5598223 | 5598223 | 373214.87 | 559822300 | yes | no | met |
| write-heavy | not-recorded-legacy-v2 | block-3 | constant-mu100 | constant | 100 | 2355560 | 0.0035 | 0.1373 | 5624052 | 5624052 | 374936.80 | 562405200 | yes | no | met |

## Paired sign-flip permutation + Holm

- balanced / symmetric-modulo: outcome=different, pairs=18, raw_p=0.00026702881, holm_p=0.00053405762
- read-heavy / symmetric-modulo: outcome=different, pairs=18, raw_p=7.6293945e-06, holm_p=2.2888184e-05
- write-heavy / symmetric-modulo: outcome=different, pairs=18, raw_p=0.025566101, holm_p=0.025566101

## Cell effects and 95% paired-block intervals

- write-heavy / constant / mu=2: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / constant / mu=5: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / constant / mu=10: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / constant / mu=25: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / constant / mu=50: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / constant / mu=100: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- write-heavy / symmetric-modulo / mu=2: effect=0.007442284930762007, CI=[-0.03287351722250576, 0.04775808708402978], status=estimable, equivalence=overlaps-equivalence-boundary
- write-heavy / symmetric-modulo / mu=5: effect=-0.009738229292106326, CI=[-0.020976416345050222, 0.0014999577608375714], status=estimable, equivalence=inside-equivalence-range
- write-heavy / symmetric-modulo / mu=10: effect=0.0038867971967747237, CI=[-0.011826149118458707, 0.019599743512008154], status=estimable, equivalence=inside-equivalence-range
- write-heavy / symmetric-modulo / mu=25: effect=0.012787354532664738, CI=[-0.007540514927378788, 0.03311522399270826], status=estimable, equivalence=overlaps-equivalence-boundary
- write-heavy / symmetric-modulo / mu=50: effect=0.011523456644465968, CI=[0.00021801346639591275, 0.022828899822536025], status=estimable, equivalence=inside-equivalence-range
- write-heavy / symmetric-modulo / mu=100: effect=0.011440148218973952, CI=[0.009098420777480324, 0.01378187566046758], status=estimable, equivalence=inside-equivalence-range
- balanced / constant / mu=2: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- balanced / constant / mu=5: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- balanced / constant / mu=10: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- balanced / constant / mu=25: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- balanced / constant / mu=50: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- balanced / constant / mu=100: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- balanced / symmetric-modulo / mu=2: effect=0.004714900870075052, CI=[-0.021400312022563796, 0.030830113762713898], status=estimable, equivalence=overlaps-equivalence-boundary
- balanced / symmetric-modulo / mu=5: effect=0.0012253172031591413, CI=[-0.006720210172551036, 0.009170844578869318], status=estimable, equivalence=inside-equivalence-range
- balanced / symmetric-modulo / mu=10: effect=0.009462806928990078, CI=[0.0023389201356250056, 0.01658669372235515], status=estimable, equivalence=inside-equivalence-range
- balanced / symmetric-modulo / mu=25: effect=0.01371228762961548, CI=[-0.0140820535791324, 0.04150662883836336], status=estimable, equivalence=overlaps-equivalence-boundary
- balanced / symmetric-modulo / mu=50: effect=0.007128362900253575, CI=[0.0017596778667229498, 0.0124970479337842], status=estimable, equivalence=inside-equivalence-range
- balanced / symmetric-modulo / mu=100: effect=0.00764931941820753, CI=[-0.0019781040029110434, 0.017276742839326103], status=estimable, equivalence=inside-equivalence-range
- read-heavy / constant / mu=2: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- read-heavy / constant / mu=5: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- read-heavy / constant / mu=10: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- read-heavy / constant / mu=25: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- read-heavy / constant / mu=50: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- read-heavy / constant / mu=100: effect=0.0, CI=[0.0, 0.0], status=estimable, equivalence=inside-equivalence-range
- read-heavy / symmetric-modulo / mu=2: effect=0.006461511483549638, CI=[0.00042504164345056033, 0.012497981323648717], status=estimable, equivalence=inside-equivalence-range
- read-heavy / symmetric-modulo / mu=5: effect=0.005481995949940736, CI=[-0.003587960840649656, 0.01455195274053113], status=estimable, equivalence=inside-equivalence-range
- read-heavy / symmetric-modulo / mu=10: effect=0.0020219568439350244, CI=[-0.0010020143689218313, 0.00504592805679188], status=estimable, equivalence=inside-equivalence-range
- read-heavy / symmetric-modulo / mu=25: effect=0.0070534494843090085, CI=[0.0019942094492431534, 0.012112689519374864], status=estimable, equivalence=inside-equivalence-range
- read-heavy / symmetric-modulo / mu=50: effect=0.003915419971911138, CI=[0.0009546519275700489, 0.006876188016252227], status=estimable, equivalence=inside-equivalence-range
- read-heavy / symmetric-modulo / mu=100: effect=0.004308112939568787, CI=[0.001121780056311224, 0.007494445822826349], status=estimable, equivalence=inside-equivalence-range

## External-floor-derived reference widths

- write-heavy: reference width=1.9% (between-run CV=0.67%, source=linux-baremetal); this is not a power guarantee.
- balanced: reference width=3% (between-run CV=1.07%, source=linux-baremetal); this is not a power guarantee.
- read-heavy: reference width=0.62% (between-run CV=0.22%, source=pegasus); this is not a power guarantee.

Non-significance means only that this registered design did not detect a difference; it is not a claim of guaranteed detection power.
