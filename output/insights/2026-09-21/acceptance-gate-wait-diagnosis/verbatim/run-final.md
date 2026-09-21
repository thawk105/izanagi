## 母集合と観測区間

母集合は残存門番 log のuntil 以前の最後の門番行の時刻順の wave。landed は選択条件にしない。日付は JST、mtime 復元は (推定)。

since は log mtime の下限。直近 wave 表は since 前も含む全起動回・attempt を保持。観測期間は選択キー期間と別掲。

| 項目 | 値 |
| --- | --- |
| since (log mtime 下限) | 2026-09-19 |
| until | 2026-09-21T07:37:00+09:00 |
| exclude_wave | ["dev-wave-lease-gate-wait-diagnosis"] |
| 門番 file 数 | 126 |
| wave 数 | 79 |
| 直近 wave 数 | 20 |
| 選択キー期間 JST | ["2026-09-20T21:20:32+09:00", "2026-09-21T04:57:50+09:00"] |
| 直近の観測区間 JST | ["2026-09-20T19:45:19+09:00", "2026-09-21T04:57:50+09:00"] |
| 日付未解決 file 数 | 0 |
| mtime 日付復元 file 数 (推定) | 7 |
| observed-wait 数 | 147 |
| censored 数 | 7 |

## wave 表 (直近 20)

| wave | 種別 (slug、確認可能な範囲) | green-receipt | land-log | 起動回 | GO | 再投入 | 観測待ち和 秒 | 打切り | 欠測 file | 拒否 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev-wave-t2797-b5-contrast | 実装 | yes | yes | 3 | 3 | 2 | 415.0 | 0 | 0 | 0 |
| dev-wave-branch-residue-cleanup | 実装 | yes | yes | 1 | 1 | 0 | 122.0 | 0 | 0 | 0 |
| dev-wave-t2817-acceptance-bottleneck-3 | 実装 | no | yes | 5 | 4 | 3 | 736.0 | 1 | 0 | 0 |
| dev-wave-t2810-g1-launch-validation | 実装 | no | yes | 2 | 2 | 1 | 510.0 | 0 | 0 | 0 |
| dev-wave-t2814-cleanup-command | 実装 | no | yes | 1 | 2 | 1 | 867.0 | 0 | 0 | 0 |
| dev-wave-paper-story-20260921 | paper | yes | yes | 1 | 1 | 0 | 149.0 | 0 | 0 | 0 |
| dev-wave-wall-decomp | 診断 | yes | yes | 1 | 1 | 0 | 150.0 | 0 | 0 | 0 |
| dev-wave-paper-abstract-conclusion-ja | paper | no | yes | 1 | 1 | 0 | 143.0 | 0 | 0 | 0 |
| rulings-all-20260921 | rulings | no | yes | 1 | 1 | 0 | 140.0 | 0 | 0 | 0 |
| dev-wave-t2344-closure-stage | 実装 | yes | yes | 2 | 2 | 1 | 272.0 | 0 | 0 | 0 |
| dev-wave-t2803-provenance-receipt | 実装 | yes | yes | 3 | 3 | 2 | 425.0 | 0 | 0 | 0 |
| dev-wave-t2804-provenance-timeout-contract | 実装 | no | yes | 1 | 2 | 1 | 310.0 | 0 | 0 | 0 |
| dev-wave-t2243-collection-diag | 診断 | yes | yes | 1 | 2 | 1 | 322.0 | 0 | 0 | 0 |
| dev-wave-t2807-b8-prerun | 実装 | yes | yes | 1 | 1 | 0 | 157.0 | 0 | 0 | 0 |
| dev-wave-t2813-o26-inventory | 実装 | no | yes | 1 | 1 | 0 | 384.0 | 0 | 0 | 0 |
| dev-wave-k2-loop-originals-lost-downstream | 実装 | yes | yes | 1 | 1 | 0 | 642.0 | 0 | 0 | 0 |
| dev-wave-paper-related-work-ja | paper | no | yes | 1 | 1 | 0 | 295.0 | 0 | 0 | 0 |
| dev-wave-fig13-b10-waiting-grid | 実装 | no | yes | 1 | 1 | 0 | 141.0 | 0 | 0 | 0 |
| dev-wave-paper-story-20260920b | paper | yes | yes | 2 | 2 | 1 | 5946.0 | 0 | 0 | 0 |
| dev-wave-t2153-witness-requested-us | 実装 | yes | yes | 1 | 2 | 1 | 381.0 | 0 | 0 | 0 |

出所: file 実在 / grep。同 dir の acceptance-receipt-green.json の実在と land*.log / land*.stdout / land-*.json の単語 landed を確認。landed の断定ではない。

## 区間分布

秒。p90 は nearest rank。打切り・日付未解決を observed-wait 分布に混ぜない。

| 母集合/条件 | n | 中央値 | p90 | 最大 | 打切り | 欠測区間 | 拒否 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| recent/all | 34 | 152.5 | 642.0 | 4838.0 | 1 | 0 | 0 |
| recent/maxl<=1 | 33 | 153.0 | 642.0 | 4838.0 | 1 | 0 | 0 |
| recent/other-known | 1 | 141.0 | 141.0 | 141.0 | 0 | 0 | 0 |
| recent/unknown | 0 | unknown | unknown | unknown | 0 | 0 | 0 |
| since/all | 147 | 261.0 | 3157.0 | 9317.0 | 7 | 0 | 27 |
| since/maxl<=1 | 140 | 338.5 | 3157.0 | 9317.0 | 6 | 0 | 27 |
| since/other-known | 6 | 146.0 | 276.0 | 276.0 | 1 | 0 | 0 |
| since/unknown | 1 | 126.0 | 126.0 | 126.0 | 0 | 0 | 0 |
| since-2026-09-19/all | 147 | 261.0 | 3157.0 | 9317.0 | 7 | 0 | 27 |
| since-2026-09-19/maxl<=1 | 140 | 338.5 | 3157.0 | 9317.0 | 6 | 0 | 27 |
| since-2026-09-19/other-known | 6 | 146.0 | 276.0 | 276.0 | 1 | 0 | 0 |
| since-2026-09-19/unknown | 1 | 126.0 | 126.0 | 126.0 | 0 | 0 | 0 |

| 母集合 | wave 観測待ち和の分布 (秒) |
| --- | --- |
| recent | {"max": 5946.0, "median": 316.0, "min": 122.0, "n": 20, "p90": 736.0, "sum": 12507.0} |
| since | {"max": 13639.0, "median": 757.0, "min": 62.0, "n": 79, "p90": 5946.0, "sum": 169319.0} |

| 区間種類 | 分布 (秒) |
| --- | --- |
| retry-prep | {"max": 60.0, "median": 1.0, "min": 0.0, "n": 27, "p90": 60.0, "sum": 783.0} |
| submit-prep | {"max": 349.0, "median": 0.0, "min": 0.0, "n": 143, "p90": 8.0, "sum": 603.0} |
| run | {"max": 2102.0, "median": 670.0, "min": 16.0, "n": 143, "p90": 1404.0, "sum": 101221.0} |

## 閉門理由内訳

| recent | tick 数 | 分 (推定、直前 tick 配分、因果寄与ではない) |
| --- | --- | --- |
| open | 78 | 98.783 |
| leaders-only | 50 | 101.867 |
| load-only | 2 | 4.067 |
| both | 2 | 3.733 |
| pigz | 0 | 0.0 |
| unknown | 0 | 0.0 |

| since | tick 数 | 分 (推定、直前 tick 配分、因果寄与ではない) |
| --- | --- | --- |
| open | 503 | 768.05 |
| leaders-only | 973 | 1938.4 |
| load-only | 22 | 45.0 |
| both | 55 | 110.917 |
| pigz | 0 | 0.0 |
| unknown | 87 | 154.833 |

| 母集合 | leaders-only + both の走行数 | tick 数 | 分 (推定、直前 tick 配分) |
| --- | --- | --- | --- |
| recent | 0 | 0 | 0.0 |
| recent | 1 | 14 | 28.133 |
| recent | ≥2 | 38 | 77.467 |
| since | 0 | 83 | 168.333 |
| since | 1 | 419 | 834.65 |
| since | ≥2 | 526 | 1046.333 |

走行数 ≥2 は実在する走行中の受入との競合。≤1 は記録 leaders と走行数の不一致 (偽 leader・log の無い走行・started/finished の欠落のいずれか、断定しない)。走行終点の rc / 打切り補完は推定であり、競合の照合もその限界を持つ。

leaders 起因閉門 (leaders-only + both): 判定方式 × 走行数。0 件の組合せも表示。

| 母集合 | leaders_grep | 走行数 | tick 数 | 分 (推定、直前 tick 配分) |
| --- | --- | --- | --- | --- |
| recent | substring | 0 | 0 | 0.0 |
| recent | substring | 1 | 14 | 28.133 |
| recent | substring | ≥2 | 37 | 75.633 |
| recent | argv-anchored | 0 | 0 | 0.0 |
| recent | argv-anchored | 1 | 0 | 0.0 |
| recent | argv-anchored | ≥2 | 1 | 1.833 |
| recent | unknown | 0 | 0 | 0.0 |
| recent | unknown | 1 | 0 | 0.0 |
| recent | unknown | ≥2 | 0 | 0.0 |
| since | substring | 0 | 83 | 168.333 |
| since | substring | 1 | 387 | 772.733 |
| since | substring | ≥2 | 475 | 948.267 |
| since | argv-anchored | 0 | 0 | 0.0 |
| since | argv-anchored | 1 | 32 | 61.917 |
| since | argv-anchored | ≥2 | 51 | 98.067 |
| since | unknown | 0 | 0 | 0.0 |
| since | unknown | 1 | 0 | 0.0 |
| since | unknown | ≥2 | 0 | 0.0 |

同じ leaders 起因閉門 tick の記録 leaders − 走行数の内訳。

| 母集合 | leaders_grep | 走行数 | 差 ≤0 tick | 差 1 tick | 差 2 tick | 差 ≥3 tick |
| --- | --- | --- | --- | --- | --- | --- |
| recent | substring | 0 | 0 | 0 | 0 | 0 |
| recent | substring | 1 | 0 | 14 | 0 | 0 |
| recent | substring | ≥2 | 32 | 5 | 0 | 0 |
| recent | argv-anchored | 0 | 0 | 0 | 0 | 0 |
| recent | argv-anchored | 1 | 0 | 0 | 0 | 0 |
| recent | argv-anchored | ≥2 | 1 | 0 | 0 | 0 |
| recent | unknown | 0 | 0 | 0 | 0 | 0 |
| recent | unknown | 1 | 0 | 0 | 0 | 0 |
| recent | unknown | ≥2 | 0 | 0 | 0 | 0 |
| since | substring | 0 | 0 | 0 | 83 | 0 |
| since | substring | 1 | 0 | 363 | 23 | 1 |
| since | substring | ≥2 | 366 | 103 | 6 | 0 |
| since | argv-anchored | 0 | 0 | 0 | 0 | 0 |
| since | argv-anchored | 1 | 0 | 32 | 0 | 0 |
| since | argv-anchored | ≥2 | 46 | 5 | 0 | 0 |
| since | unknown | 0 | 0 | 0 | 0 | 0 |
| since | unknown | 1 | 0 | 0 | 0 | 0 |
| since | unknown | ≥2 | 0 | 0 | 0 | 0 |

substring は他 process の argv に `dev_wave_wait.py` と ` acceptance` の両方を含むだけで数える (包み shell・codex 子の prompt 文字列を含みうる)。argv-anchored は interpreter で始まる行だけを数える。差は原因の候補であって断定ではない。

## GO 時点値

| 母集合 | GO 数 | GO 直前 leaders 値:件数 | recount leaders 値:件数 | GO 直前 load1 中央値 | p90 | 最大 |
| --- | --- | --- | --- | --- | --- | --- |
| recent | 34 | 0.0: 17; 1.0: 16; 2.0: 1 | 0.0: 19; 1.0: 14; 2.0: 1 | 4.47 | 11.7 | 38.55 |
| since | 147 | 0.0: 49; 1.0: 92; 2.0: 6 | 0.0: 47; 1.0: 87; 2.0: 6; 欠測: 7 | 6.56 | 16.91 | 39.54 |

| wave | file | segment | GO | leaders | load1 | load5 | recount leaders | recount load1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev-wave-a1-sized-attempt2 | acceptance-final.chain.log | 1 | 2026-09-19T22:39:18+09:00 | 0.0 | 25.49 | 46.51 | 0.0 | 28.28 |
| dev-wave-acceptance-worker-time-trim | acceptance-final.chain.log | 1 | 2026-09-20T01:26:15+09:00 | 1.0 | 12.05 | 8.49 | 1.0 | 11.76 |
| dev-wave-b10-waiting-grid-results | gate-loop-final.log | 1 | 2026-09-20T15:27:34+09:00 | 1.0 | 4.41 | 8.68 | 0.0 | - |
| dev-wave-b5-generator-contrast-prereg | acceptance-1.chain.log | 1 | 2026-09-19T23:29:17+09:00 | 0.0 | 23.29 | 19.57 | 0.0 | 23.68 |
| dev-wave-b8-longrun-verify-prereg | acceptance-1.chain.log | 1 | 2026-09-20T14:46:44+09:00 | 1.0 | 9.18 | 9.58 | 0.0 | 29.16 |
| dev-wave-branch-residue-cleanup | acceptance-final.chain.log | 1 | 2026-09-21T04:19:14+09:00 | 0.0 | 3.28 | 3.05 | 0.0 | 2.99 |
| dev-wave-claim-evidence-2026-09-20 | acceptance-final.chain.log | 1 | 2026-09-20T09:24:49+09:00 | 0.0 | 4.94 | 8.28 | 0.0 | 4.52 |
| dev-wave-cleanup-backup-loss-record | acceptance-final.chain.log | 1 | 2026-09-20T20:04:27+09:00 | 1.0 | 8.11 | 6.61 | 1.0 | 7.1 |
| dev-wave-cleanup-backup-loss-record | acceptance-final2.chain.log | 1 | 2026-09-20T21:05:25+09:00 | 1.0 | 16.65 | 16.58 | 1.0 | 15.78 |
| dev-wave-cleanup-backup-loss-record | acceptance-final3.chain.log | 1 | 2026-09-20T21:17:03+09:00 | 1.0 | 17.48 | 39.14 | 1.0 | 17.11 |
| dev-wave-dead-code-inventory | acceptance-a1.chain.log | 1 | 2026-09-20T00:51:49+09:00 | 1.0 | 4.5 | 6.76 | 1.0 | 4.5 |
| dev-wave-fig11-a6-certification | gate-loop-final.log | 1 | 2026-09-20T15:32:07+09:00 | 2.0 | 11.13 | 11.74 | 2.0 | - |
| dev-wave-fig13-b10-waiting-grid | gate-loop-final.log | 1 | 2026-09-20T21:35:45+09:00 | 2.0 | 18.35 | 14.58 | 2.0 | - |
| dev-wave-fig3b-arc-status | gate-loop-final.log | 1 | 2026-09-20T09:46:54+09:00 | 1.0 | 5.39 | 9.12 | 1.0 | - |
| dev-wave-fig3b-arc-status | gate-loop-final2.log | 1 | 2026-09-20T10:52:15+09:00 | 1.0 | 5.03 | 4.3 | 1.0 | - |
| dev-wave-fig3b-arc-status | gate-loop-final2.log | 5 | 2026-09-20T11:00:46+09:00 | 1.0 | 3.75 | 5.86 | 1.0 | - |
| dev-wave-k2-loop-fig12 | gate-loop-final.log | 1 | 2026-09-20T15:54:48+09:00 | 1.0 | 5.76 | 6.43 | 1.0 | - |
| dev-wave-k2-loop-originals-lost-downstream | acceptance-final.chain.log | 1 | 2026-09-20T22:04:33+09:00 | 1.0 | 6.98 | 8.94 | 1.0 | 7.49 |
| dev-wave-k2-loop-round3 | acceptance-final.chain.log | 1 | 2026-09-19T23:31:02+09:00 | 1.0 | 37.0 | 22.96 | 1.0 | 40.28 |
| dev-wave-k2-three-rounds-results | acceptance-final.chain.log | 1 | 2026-09-20T08:48:59+09:00 | 1.0 | 10.69 | 17.39 | 1.0 | 10.69 |
| dev-wave-k2-three-rounds-results | acceptance-final.chain.log | 5 | 2026-09-20T08:53:10+09:00 | 1.0 | 13.4 | 22.07 | 1.0 | 10.46 |
| dev-wave-k2-three-rounds-results | acceptance-final2.chain.log | 1 | 2026-09-20T09:19:02+09:00 | 1.0 | 10.44 | 7.75 | 1.0 | 11.97 |
| dev-wave-k2-three-rounds-results | acceptance-final2.chain.log | 5 | 2026-09-20T09:24:59+09:00 | 0.0 | 4.59 | 8.27 | 1.0 | 4.53 |
| dev-wave-mocc-g2-observation-results | gate-loop-final.log | 1 | 2026-09-20T08:44:19+09:00 | 1.0 | 10.64 | 17.57 | 1.0 | - |
| dev-wave-mocc-g2-observation-results | gate-loop-final.log | 5 | 2026-09-20T08:54:28+09:00 | 1.0 | 6.56 | 17.79 | 1.0 | - |
| dev-wave-mocc-g2-observation-results | gate-loop-final2.log | 1 | 2026-09-20T09:51:59+09:00 | 1.0 | 4.67 | 8.43 | 1.0 | - |
| dev-wave-mocc-witlight-arm-run | acceptance-final-1.chain.log | 1 | 2026-09-20T00:07:08+09:00 | 1.0 | 24.56 | 19.71 | 1.0 | - |
| dev-wave-mocc-witlight-results | acceptance-final-1.chain.log | 1 | 2026-09-20T07:59:32+09:00 | 1.0 | 12.63 | 12.82 | 1.0 | - |
| dev-wave-p24-static-backoff-sweep-results | acceptance-final.chain.log | 1 | 2026-09-20T14:27:41+09:00 | 1.0 | 13.84 | 11.76 | 1.0 | 12.35 |
| dev-wave-p24-static-backoff-sweep-results | acceptance-final2.chain.log | 1 | 2026-09-20T16:32:24+09:00 | 1.0 | 8.98 | 66.25 | 1.0 | 8.98 |
| dev-wave-paper-abstract-conclusion-ja | acceptance-final.chain.log | 1 | 2026-09-21T01:43:40+09:00 | 0.0 | 3.66 | 5.25 | 0.0 | 3.33 |
| dev-wave-paper-intro-ja | acceptance-final2.chain.log | 1 | 2026-09-20T19:15:55+09:00 | 0.0 | 16.29 | 18.84 | 0.0 | 12.38 |
| dev-wave-paper-intro-ja | acceptance-final3.chain.log | 1 | 2026-09-20T20:39:37+09:00 | 1.0 | 10.48 | 7.75 | 1.0 | 9.8 |
| dev-wave-paper-intro-ja | acceptance-final3.chain.log | 5 | 2026-09-20T20:44:52+09:00 | 1.0 | 39.54 | 28.0 | 1.0 | 55.05 |
| dev-wave-paper-methods-ja-2026-09-20 | acceptance-final.chain.log | 1 | 2026-09-20T19:02:15+09:00 | 1.0 | 8.6 | 7.4 | 1.0 | 8.6 |
| dev-wave-paper-related-work-ja | acceptance-final.chain.log | 1 | 2026-09-20T21:51:46+09:00 | 1.0 | 11.7 | 17.05 | 1.0 | 12.78 |
| dev-wave-paper-results-ja-2026-09-20 | acceptance-final.chain.log | 1 | 2026-09-20T19:20:53+09:00 | 1.0 | 24.13 | 22.54 | 1.0 | 17.5 |
| dev-wave-paper-story-20260919 | acceptance-final.chain.log | 1 | 2026-09-20T00:07:15+09:00 | 1.0 | 24.56 | 19.71 | 1.0 | 22.46 |
| dev-wave-paper-story-20260919 | acceptance-final.chain.log | 5 | 2026-09-20T02:03:35+09:00 | 1.0 | 5.82 | 6.19 | 1.0 | 5.51 |
| dev-wave-paper-story-20260919 | acceptance-final.chain.log | 9 | 2026-09-20T02:07:20+09:00 | 1.0 | 5.98 | 7.78 | 1.0 | 4.93 |
| dev-wave-paper-story-20260919 | acceptance-final2.chain.log | 1 | 2026-09-20T03:05:07+09:00 | 1.0 | 5.41 | 3.87 | 1.0 | 14.7 |
| dev-wave-paper-story-20260919 | acceptance-final2.chain.log | 5 | 2026-09-20T03:08:56+09:00 | 1.0 | 6.99 | 11.47 | 1.0 | 5.87 |
| dev-wave-paper-story-20260919 | acceptance-final2.chain.log | 9 | 2026-09-20T03:12:06+09:00 | 1.0 | 2.81 | 7.9 | 0.0 | 2.5 |
| dev-wave-paper-story-20260919 | acceptance-final3.chain.log | 1 | 2026-09-20T03:17:55+09:00 | 0.0 | 2.37 | 3.87 | 0.0 | 2.54 |
| dev-wave-paper-story-20260919 | acceptance-final4.chain.log | 1 | 2026-09-20T03:29:38+09:00 | 0.0 | 2.02 | 2.56 | 0.0 | 2.02 |
| dev-wave-paper-story-20260920 | acceptance-final.chain.log | 1 | 2026-09-20T08:48:35+09:00 | 0.0 | 9.98 | 17.92 | 0.0 | 9.98 |
| dev-wave-paper-story-20260920b | acceptance-final.chain.log | 1 | 2026-09-20T21:05:57+09:00 | 1.0 | 17.88 | 16.82 | 1.0 | 22.95 |
| dev-wave-paper-story-20260920b | acceptance-final2.chain.log | 1 | 2026-09-20T21:32:02+09:00 | 0.0 | 11.07 | 11.57 | 0.0 | 13.49 |
| dev-wave-paper-story-20260921 | acceptance-final.chain.log | 1 | 2026-09-21T02:36:10+09:00 | 1.0 | 2.39 | 3.6 | 1.0 | 2.56 |
| dev-wave-s1a-nine-pair-results | acceptance-final.chain.log | 1 | 2026-09-20T14:18:02+09:00 | 1.0 | 10.86 | 10.16 | 1.0 | 10.37 |
| dev-wave-t1998-b7-fixed5 | acceptance-final.chain.log | 1 | 2026-09-20T02:07:51+09:00 | 1.0 | 4.57 | 6.97 | - | - |
| dev-wave-t1998-b7-fixed5 | acceptance-final2.chain.log | 1 | 2026-09-20T02:13:40+09:00 | 1.0 | 7.5 | 10.16 | - | - |
| dev-wave-t1998-b7-fixed5 | acceptance-final3.chain.log | 1 | 2026-09-20T02:23:22+09:00 | 1.0 | 12.67 | 9.5 | - | - |
| dev-wave-t1998-b7-fixed5 | acceptance-final4.chain.log | 1 | 2026-09-20T02:44:57+09:00 | 1.0 | 4.98 | 4.53 | - | - |
| dev-wave-t1998-b7-fixed5 | acceptance-final4.chain.log | 5 | 2026-09-20T02:49:55+09:00 | 0.0 | 8.12 | 8.83 | - | - |
| dev-wave-t2153-witness-6 | acceptance-final.chain.log | 1 | 2026-09-20T01:52:38+09:00 | 1.0 | 3.49 | 4.48 | 1.0 | 3.49 |
| dev-wave-t2153-witness-6 | acceptance-final2.chain.log | 1 | 2026-09-20T02:09:00+09:00 | 0.0 | 5.11 | 6.73 | 0.0 | 4.64 |
| dev-wave-t2153-witness-6 | acceptance-final3.chain.log | 1 | 2026-09-20T02:28:19+09:00 | 1.0 | 17.99 | 15.56 | 1.0 | 16.39 |
| dev-wave-t2153-witness-bc | acceptance-final.chain.log | 1 | 2026-09-20T17:04:02+09:00 | 1.0 | 4.23 | 3.21 | 1.0 | 4.88 |
| dev-wave-t2153-witness-requested-us | acceptance-final.chain.log | 1 | 2026-09-20T21:15:42+09:00 | 0.0 | 38.55 | 49.57 | 0.0 | 26.49 |
| dev-wave-t2153-witness-requested-us | acceptance-final.chain.log | 5 | 2026-09-20T21:20:32+09:00 | 1.0 | 10.24 | 25.51 | 1.0 | 11.22 |
| dev-wave-t2243-collection-diag | acceptance-final.chain.log | 1 | 2026-09-20T22:53:53+09:00 | 0.0 | 6.78 | 7.72 | 0.0 | 6.67 |
| dev-wave-t2243-collection-diag | acceptance-final.chain.log | 5 | 2026-09-20T22:57:43+09:00 | 0.0 | 4.95 | 6.56 | 0.0 | 4.82 |
| dev-wave-t2288-floor-pair-w1 | acceptance-final-1.chain.log | 1 | 2026-09-19T23:47:11+09:00 | 0.0 | 7.14 | 10.33 | 1.0 | 10.31 |
| dev-wave-t2304-pin-advance | gate-loop-final.log | 1 | 2026-09-20T17:24:20+09:00 | 1.0 | 4.97 | 4.42 | 1.0 | - |
| dev-wave-t2304-pin-advance | gate-loop-final.log | 5 | 2026-09-20T17:28:41+09:00 | 1.0 | 3.73 | 4.49 | 1.0 | - |
| dev-wave-t2304-pin-advance | gate-loop-final.log | 9 | 2026-09-20T17:38:07+09:00 | 1.0 | 2.92 | 3.32 | 1.0 | - |
| dev-wave-t2304-pin-advance | gate-loop-final2.log | 1 | 2026-09-20T17:46:20+09:00 | 1.0 | 4.39 | 4.77 | 1.0 | - |
| dev-wave-t2304-pin-advance | gate-loop-final2.log | 5 | 2026-09-20T17:50:36+09:00 | 1.0 | 4.18 | 4.18 | 1.0 | - |
| dev-wave-t2304-pin-advance | gate-loop-final2.log | 9 | 2026-09-20T17:54:08+09:00 | 1.0 | 3.47 | 3.8 | 1.0 | - |
| dev-wave-t2304-pin-advance | gate-loop-final3.log | 1 | 2026-09-20T18:01:29+09:00 | 1.0 | 5.56 | 4.2 | 1.0 | - |
| dev-wave-t2304-pin-advance | gate-loop-final4.log | 1 | 2026-09-20T18:50:13+09:00 | 1.0 | 7.75 | 6.53 | 1.0 | - |
| dev-wave-t2304-pin-advance | gate-loop-pre.log | 1 | 2026-09-20T16:12:27+09:00 | 0.0 | 11.47 | 41.08 | 0.0 | - |
| dev-wave-t2344-closure-stage | acceptance-final.chain.log | 1 | 2026-09-20T23:35:37+09:00 | 0.0 | 4.14 | 4.87 | 0.0 | 3.92 |
| dev-wave-t2344-closure-stage | acceptance-final2.chain.log | 1 | 2026-09-21T00:02:39+09:00 | 1.0 | 4.73 | 5.05 | 1.0 | 4.73 |
| dev-wave-t2384-terminal-outer-shape | gate-loop-final.log | 1 | 2026-09-20T09:41:06+09:00 | 1.0 | 4.74 | 4.89 | 1.0 | - |
| dev-wave-t2384-terminal-outer-shape | gate-loop-final.log | 5 | 2026-09-20T10:40:34+09:00 | 1.0 | 3.6 | 7.78 | 1.0 | - |
| dev-wave-t2489-nodes5-local-lock | acceptance-final3.chain.log | 1 | 2026-09-19T21:34:08+09:00 | 1.0 | 6.09 | 10.66 | 1.0 | 5.58 |
| dev-wave-t2609-t2656-provenance-cost | gate-loop-final.log | 1 | 2026-09-20T10:08:20+09:00 | 1.0 | 4.28 | 4.86 | 1.0 | - |
| dev-wave-t2610-b7-limited | acceptance-final-1.chain.log | 1 | 2026-09-20T14:04:48+09:00 | 0.0 | 9.37 | 9.59 | 0.0 | - |
| dev-wave-t2610-fig10 | gate-loop-final.log | 2 | 2026-09-20T12:44:11+09:00 | 0.0 | 12.49 | 47.65 | 1.0 | - |
| dev-wave-t2620-zombie-residual | gate-loop-final.log | 1 | 2026-09-20T10:10:28+09:00 | 2.0 | 11.97 | 7.88 | 2.0 | - |
| dev-wave-t2620-zombie-residual | gate-loop-final.log | 5 | 2026-09-20T10:16:39+09:00 | 2.0 | 11.64 | 8.38 | 2.0 | - |
| dev-wave-t2629-legacy-compiler-reach | gate-loop-final.log | 1 | 2026-09-20T08:06:56+09:00 | 1.0 | 13.15 | 18.39 | 1.0 | - |
| dev-wave-t2629-legacy-compiler-reach | gate-loop-final.log | 5 | 2026-09-20T08:13:09+09:00 | 1.0 | 8.67 | 13.71 | 1.0 | - |
| dev-wave-t2632-evidence-provenance | acceptance-final.chain.log | 1 | 2026-09-20T19:51:05+09:00 | 1.0 | 12.63 | 11.1 | 1.0 | 12.63 |
| dev-wave-t2700-prewarm-ab | gate-loop-final.log | 1 | 2026-09-20T18:18:35+09:00 | 0.0 | 2.69 | 3.73 | 0.0 | - |
| dev-wave-t2709-blob-transfer-cost | gate-loop-final.log | 1 | 2026-09-20T08:58:52+09:00 | 1.0 | 7.1 | 14.32 | 1.0 | - |
| dev-wave-t2711-ancestry-check | gate-loop-final.log | 1 | 2026-09-20T08:37:46+09:00 | 1.0 | 21.22 | 16.63 | 1.0 | - |
| dev-wave-t2711-ancestry-check | gate-loop-final2.log | 1 | 2026-09-20T10:15:08+09:00 | 1.0 | 4.25 | 7.11 | 1.0 | - |
| dev-wave-t2737-noninert-codex | acceptance-final.chain.log | 1 | 2026-09-19T21:29:48+09:00 | 0.0 | 10.43 | 11.62 | 0.0 | 9.83 |
| dev-wave-t2737-noninert-codex | acceptance-final2.chain.log | 1 | 2026-09-19T23:47:00+09:00 | 0.0 | 7.53 | 10.51 | 0.0 | 10.48 |
| dev-wave-t2766-pairing-ab | gate-loop-final.log | 1 | 2026-09-20T05:28:01+09:00 | 1.0 | 1.68 | 2.05 | 1.0 | - |
| dev-wave-t2773-mocc-template-wave2 | acceptance-final-1.chain.log | 1 | 2026-09-20T01:22:16+09:00 | 1.0 | 5.4 | 8.05 | - | - |
| dev-wave-t2773-mocc-template-wave2 | acceptance-final-2.chain.log | 1 | 2026-09-20T01:38:57+09:00 | 1.0 | 8.14 | 9.2 | - | - |
| dev-wave-t2778-child-worktree-cleanup | acceptance-final.chain.log | 1 | 2026-09-20T02:02:08+09:00 | 1.0 | 5.46 | 6.29 | 1.0 | 6.24 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-final2.chain.log | 1 | 2026-09-20T03:04:20+09:00 | 0.0 | 2.25 | 3.33 | 0.0 | 2.51 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-final3.chain.log | 1 | 2026-09-20T03:19:03+09:00 | 1.0 | 7.01 | 4.85 | 1.0 | 7.01 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w2final.chain.log | 1 | 2026-09-20T04:00:03+09:00 | 0.0 | 2.41 | 3.24 | 0.0 | 2.35 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w3final.chain.log | 1 | 2026-09-20T04:31:44+09:00 | 0.0 | 3.1 | 3.12 | 0.0 | 3.17 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w4final.chain.log | 1 | 2026-09-20T05:01:37+09:00 | 0.0 | 2.08 | 2.25 | 0.0 | 2.08 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w4final2.chain.log | 1 | 2026-09-20T05:16:05+09:00 | 0.0 | 2.01 | 1.87 | 0.0 | 2.25 |
| dev-wave-t2786-base-decomposition | acceptance-final.chain.log | 1 | 2026-09-20T01:26:26+09:00 | 1.0 | 11.76 | 8.62 | 1.0 | 11.48 |
| dev-wave-t2786-base-decomposition | acceptance-final2.chain.log | 1 | 2026-09-20T02:22:28+09:00 | 1.0 | 7.48 | 8.39 | 1.0 | 7.64 |
| dev-wave-t2786-base-decomposition | acceptance-final2.chain.log | 5 | 2026-09-20T02:27:28+09:00 | 0.0 | 11.19 | 14.28 | 0.0 | 11.9 |
| dev-wave-t2789-acceptance-ops-docs | acceptance-final.chain.log | 1 | 2026-09-20T07:48:40+09:00 | 0.0 | 11.16 | 11.15 | 0.0 | 11.07 |
| dev-wave-t2790-t1259-scan-timeout | acceptance-final.chain.log | 1 | 2026-09-20T01:07:30+09:00 | 2.0 | 3.53 | 8.14 | 2.0 | 3.41 |
| dev-wave-t2790-t1259-scan-timeout | acceptance-meas.chain.log | 1 | 2026-09-20T00:38:37+09:00 | 2.0 | 6.35 | 7.56 | 2.0 | 5.58 |
| dev-wave-t2791-mocc-upstream-report | gate-loop-final.log | 1 | 2026-09-20T15:27:36+09:00 | 1.0 | 5.01 | 9.01 | 1.0 | - |
| dev-wave-t2792-a1-sized-attempt2 | acceptance-final.chain.log | 1 | 2026-09-20T19:35:56+09:00 | 1.0 | 8.61 | 9.91 | 1.0 | 10.81 |
| dev-wave-t2792-a1-sized-attempt2 | acceptance-final3.chain.log | 1 | 2026-09-20T20:27:29+09:00 | 1.0 | 9.5 | 7.39 | 1.0 | 8.38 |
| dev-wave-t2792-a1-sized-rerun-auth | gate-loop-final.log | 1 | 2026-09-20T15:14:37+09:00 | 0.0 | 10.11 | 10.05 | 1.0 | - |
| dev-wave-t2793-fig8b-cohort2 | gate-loop-final.log | 1 | 2026-09-20T10:35:18+09:00 | 1.0 | 6.62 | 5.45 | 1.0 | - |
| dev-wave-t2793-fig8b-cohort2 | gate-loop-final.log | 5 | 2026-09-20T10:56:57+09:00 | 1.0 | 8.6 | 6.98 | 1.0 | - |
| dev-wave-t2793-fig8b-cohort2 | gate-loop-final.log | 9 | 2026-09-20T11:19:52+09:00 | 1.0 | 3.0 | 2.52 | 1.0 | - |
| dev-wave-t2795-k2-pair | acceptance-final.chain.log | 1 | 2026-09-20T20:26:19+09:00 | 0.0 | 7.87 | 6.81 | 0.0 | 7.87 |
| dev-wave-t2795-pair-launcher | gate-loop-final.log | 1 | 2026-09-20T16:40:22+09:00 | 1.0 | 7.48 | 19.66 | 1.0 | - |
| dev-wave-t2795-pair-launcher | gate-loop-final2.log | 1 | 2026-09-20T17:29:42+09:00 | 1.0 | 3.28 | 4.25 | 1.0 | - |
| dev-wave-t2796-docs4 | acceptance-final.chain.log | 1 | 2026-09-20T13:37:56+09:00 | 0.0 | 8.55 | 15.51 | 0.0 | - |
| dev-wave-t2796-docs4 | acceptance-final2.chain.log | 1 | 2026-09-20T14:06:15+09:00 | 1.0 | 6.85 | 8.65 | 1.0 | - |
| dev-wave-t2796-docs4 | acceptance-final3.chain.log | 1 | 2026-09-20T15:00:43+09:00 | 1.0 | 14.99 | 12.8 | 1.0 | - |
| dev-wave-t2797-b5-contrast | acceptance-final.chain.log | 1 | 2026-09-21T04:21:32+09:00 | 1.0 | 3.19 | 3.28 | 1.0 | 2.93 |
| dev-wave-t2797-b5-contrast | acceptance-final2.chain.log | 1 | 2026-09-21T04:40:27+09:00 | 0.0 | 2.41 | 3.66 | 0.0 | 2.39 |
| dev-wave-t2797-b5-contrast | acceptance-final3.chain.log | 1 | 2026-09-21T04:57:50+09:00 | 0.0 | 1.48 | 1.9 | 0.0 | 1.44 |
| dev-wave-t2800-dead-code-delete | gate-loop-final.log | 1 | 2026-09-20T16:12:40+09:00 | 0.0 | 16.91 | 40.94 | 1.0 | - |
| dev-wave-t2803-provenance-receipt | acceptance-final.chain.log | 1 | 2026-09-20T23:16:31+09:00 | 0.0 | 4.43 | 4.88 | 0.0 | 4.48 |
| dev-wave-t2803-provenance-receipt | acceptance-final2.chain.log | 1 | 2026-09-20T23:34:29+09:00 | 0.0 | 4.83 | 5.09 | 0.0 | 4.58 |
| dev-wave-t2803-provenance-receipt | acceptance-final3.chain.log | 1 | 2026-09-20T23:45:07+09:00 | 1.0 | 3.81 | 4.61 | 1.0 | 3.53 |
| dev-wave-t2804-provenance-timeout-contract | gate-loop-final.log | 1 | 2026-09-20T23:11:55+09:00 | 0.0 | 4.9 | 5.57 | 0.0 | - |
| dev-wave-t2804-provenance-timeout-contract | gate-loop-final.log | 5 | 2026-09-20T23:16:38+09:00 | 0.0 | 4.51 | 4.91 | 0.0 | - |
| dev-wave-t2807-b8-prerun | acceptance-final.chain.log | 1 | 2026-09-20T22:32:31+09:00 | 1.0 | 7.6 | 7.77 | 0.0 | 8.05 |
| dev-wave-t2810-g1-launch-validation | gate-loop-final.log | 1 | 2026-09-21T03:12:15+09:00 | 1.0 | 2.71 | 3.14 | 1.0 | - |
| dev-wave-t2810-g1-launch-validation | gate-loop-final2.log | 1 | 2026-09-21T03:29:14+09:00 | 1.0 | 2.4 | 3.09 | 1.0 | - |
| dev-wave-t2813-o26-inventory | gate-loop-final.log | 1 | 2026-09-20T22:13:30+09:00 | 1.0 | 4.92 | 8.04 | 1.0 | - |
| dev-wave-t2814-cleanup-command | gate-loop-final.log | 1 | 2026-09-21T02:46:42+09:00 | 1.0 | 6.93 | 3.92 | 1.0 | - |
| dev-wave-t2814-cleanup-command | gate-loop-final.log | 5 | 2026-09-21T02:50:30+09:00 | 1.0 | 4.14 | 4.01 | 0.0 | - |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final.chain.log | 1 | 2026-09-21T02:59:51+09:00 | 1.0 | 2.53 | 3.66 | 1.0 | 2.42 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final3.chain.log | 1 | 2026-09-21T03:18:33+09:00 | 0.0 | 5.32 | 3.77 | 0.0 | 4.93 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final4.chain.log | 1 | 2026-09-21T03:36:03+09:00 | 1.0 | 3.54 | 4.11 | 1.0 | 3.37 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-ref.chain.log | 1 | 2026-09-21T02:12:08+09:00 | 0.0 | 2.92 | 4.16 | 0.0 | 4.24 |
| dev-wave-verifier-capacity | acceptance-final.chain.log | 1 | 2026-09-20T16:45:18+09:00 | 1.0 | 4.2 | 11.33 | 1.0 | 4.64 |
| dev-wave-verify-phase-adopted-backoff | acceptance-final.chain.log | 1 | 2026-09-20T02:09:07+09:00 | 0.0 | 4.75 | 6.75 | 0.0 | 4.68 |
| dev-wave-wall-decomp | acceptance-final.chain.log | 1 | 2026-09-21T02:28:10+09:00 | 0.0 | 2.44 | 3.43 | 0.0 | 2.38 |
| rulings-all-20260920 | acceptance-final-1.chain.log | 1 | 2026-09-20T10:56:14+09:00 | 0.0 | 6.04 | 6.45 | 0.0 | - |
| rulings-all-20260920b | acceptance-final-1.chain.log | 1 | 2026-09-20T12:43:56+09:00 | 0.0 | 17.35 | 51.54 | 0.0 | - |
| rulings-all-20260920c | acceptance-final-1.chain.log | 1 | 2026-09-20T19:15:58+09:00 | 0.0 | 13.17 | 17.89 | 1.0 | - |
| rulings-all-20260921 | acceptance-final-1.chain.log | 1 | 2026-09-21T01:07:14+09:00 | 0.0 | 4.18 | 5.26 | 0.0 | - |

## 同時待ち・同時 GO

全 since 対象の観測区間で他 wave を重複排除。leaders は走行側観測であり同時待ち数を補正しない。log の無い待ち手は欠測。

走行区間の数: 門番 log のある dir 142 / 無い dir 1

走行数は全走査対象 dir の since 日付以降に始まった started→finished を照合し、started ≤ tick < end の他 wave 数。finished 欠落時は対応 GO 後の rc、それも無ければ until、until 無指定なら同 dir の最終観測時刻 / log mtime (門番 log も無ければ started) で打切り (推定)。until より後の finished は until で打切り。GO の無い censored の GO 直前値は欠測。leaders_minus_runs_pre_go は記録 leaders − 走行数で、偽 leader 疑いの上限であり断定ではない。

| 母集合 | GO 直前同時待ち 値:件数 | 区間最大同時待ち 値:件数 (打切り含む) | 同時 GO ±120秒 値:件数 | 走行数 (GO 直前) 値:件数 |
| --- | --- | --- | --- | --- |
| recent | 0: 28; 1: 5; 2: 1 | 0: 24; 1: 8; 2: 2; 3: 1 | 0: 28; 1: 6 | 0: 18; 1: 16 |
| since | 0: 59; 1: 20; 2: 17; 3: 17; 4: 13; 5: 12; 6: 4; 7: 2; 8: 1; 9: 2 | 0: 49; 1: 20; 2: 11; 3: 21; 4: 10; 5: 20; 6: 11; 7: 1; 8: 1; 9: 10 | 0: 93; 1: 50; 3: 4 | 0: 75; 1: 69; 2: 3 |

| wave | file | segment | 最大 他 wave | GO 直前 tick | GO 時点 | GO ±120秒 | 走行 (GO 直前) | leaders − 走行 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev-wave-a1-sized-attempt2 | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-acceptance-worker-time-trim | acceptance-final.chain.log | 1 | 6 | 5 | 5 | 1 | 0 | 1.0 |
| dev-wave-b10-waiting-grid-results | gate-loop-final.log | 1 | 5 | 3 | 3 | 1 | 1 | 0.0 |
| dev-wave-b5-generator-contrast-prereg | acceptance-1.chain.log | 1 | 2 | 2 | 2 | 1 | 0 | 0.0 |
| dev-wave-b8-longrun-verify-prereg | acceptance-1.chain.log | 1 | 4 | 4 | 5 | 0 | 1 | 0.0 |
| dev-wave-branch-residue-cleanup | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-claim-evidence-2026-09-20 | acceptance-final.chain.log | 1 | 9 | 9 | 9 | 1 | 0 | 0.0 |
| dev-wave-cleanup-backup-loss-record | acceptance-final.chain.log | 1 | 3 | 3 | 3 | 0 | 1 | 0.0 |
| dev-wave-cleanup-backup-loss-record | acceptance-final2.chain.log | 1 | 3 | 1 | 1 | 1 | 1 | 0.0 |
| dev-wave-cleanup-backup-loss-record | acceptance-final3.chain.log | 1 | 2 | 1 | 1 | 1 | 1 | 0.0 |
| dev-wave-dead-code-inventory | acceptance-a1.chain.log | 1 | 6 | 5 | 5 | 0 | 0 | 1.0 |
| dev-wave-fig11-a6-certification | gate-loop-final.log | 1 | 2 | 2 | 3 | 0 | 2 | 0.0 |
| dev-wave-fig13-b10-waiting-grid | gate-loop-final.log | 1 | 0 | 0 | 0 | 0 | 1 | 1.0 |
| dev-wave-fig3b-arc-status | gate-loop-final.log | 1 | 9 | 7 | 7 | 0 | 1 | 0.0 |
| dev-wave-fig3b-arc-status | gate-loop-final2.log | 1 | 3 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-fig3b-arc-status | gate-loop-final2.log | 5 | 2 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-k2-loop-fig12 | gate-loop-final.log | 1 | 4 | 4 | 4 | 0 | 0 | 1.0 |
| dev-wave-k2-loop-originals-lost-downstream | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-k2-loop-round3 | acceptance-final.chain.log | 1 | 2 | 1 | 1 | 1 | 1 | 0.0 |
| dev-wave-k2-three-rounds-results | acceptance-final.chain.log | 1 | 4 | 4 | 4 | 1 | 1 | 0.0 |
| dev-wave-k2-three-rounds-results | acceptance-final.chain.log | 5 | 5 | 5 | 5 | 1 | 1 | 0.0 |
| dev-wave-k2-three-rounds-results | acceptance-final.chain.log | 9 | 5 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-k2-three-rounds-results | acceptance-final2.chain.log | 1 | 8 | 8 | 8 | 0 | 1 | 0.0 |
| dev-wave-k2-three-rounds-results | acceptance-final2.chain.log | 5 | 9 | 9 | 8 | 1 | 0 | 0.0 |
| dev-wave-mocc-g2-observation-results | gate-loop-final.log | 1 | 5 | 5 | 5 | 0 | 1 | 0.0 |
| dev-wave-mocc-g2-observation-results | gate-loop-final.log | 5 | 5 | 5 | 5 | 1 | 1 | 0.0 |
| dev-wave-mocc-g2-observation-results | gate-loop-final2.log | 1 | 9 | 6 | 6 | 0 | 1 | 0.0 |
| dev-wave-mocc-witlight-arm-run | acceptance-final-1.chain.log | 1 | 4 | 4 | 4 | 1 | 0 | 1.0 |
| dev-wave-mocc-witlight-results | acceptance-final-1.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-p24-static-backoff-sweep-results | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-p24-static-backoff-sweep-results | acceptance-final.chain.log | 5 | 5 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-p24-static-backoff-sweep-results | acceptance-final2.chain.log | 1 | 5 | 3 | 3 | 0 | 0 | 1.0 |
| dev-wave-paper-abstract-conclusion-ja | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-paper-intro-ja | acceptance-final.chain.log | 1 | 1 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-paper-intro-ja | acceptance-final2.chain.log | 1 | 3 | 3 | 3 | 1 | 0 | 0.0 |
| dev-wave-paper-intro-ja | acceptance-final2.chain.log | 5 | 2 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-paper-intro-ja | acceptance-final3.chain.log | 1 | 3 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-paper-intro-ja | acceptance-final3.chain.log | 5 | 2 | 2 | 2 | 0 | 0 | 1.0 |
| dev-wave-paper-methods-ja-2026-09-20 | acceptance-final.chain.log | 1 | 1 | 1 | 1 | 0 | 0 | 1.0 |
| dev-wave-paper-related-work-ja | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-paper-results-ja-2026-09-20 | acceptance-final.chain.log | 1 | 3 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-paper-story-20260919 | acceptance-final.chain.log | 1 | 4 | 4 | 3 | 1 | 0 | 1.0 |
| dev-wave-paper-story-20260919 | acceptance-final.chain.log | 5 | 6 | 4 | 4 | 1 | 0 | 1.0 |
| dev-wave-paper-story-20260919 | acceptance-final.chain.log | 9 | 4 | 4 | 4 | 3 | 0 | 1.0 |
| dev-wave-paper-story-20260919 | acceptance-final2.chain.log | 1 | 3 | 0 | 0 | 1 | 1 | 0.0 |
| dev-wave-paper-story-20260919 | acceptance-final2.chain.log | 5 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-paper-story-20260919 | acceptance-final2.chain.log | 9 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-paper-story-20260919 | acceptance-final3.chain.log | 1 | 1 | 1 | 1 | 1 | 0 | 0.0 |
| dev-wave-paper-story-20260919 | acceptance-final4.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-paper-story-20260920 | acceptance-final.chain.log | 1 | 5 | 5 | 5 | 1 | 0 | 0.0 |
| dev-wave-paper-story-20260920b | acceptance-final.chain.log | 1 | 3 | 0 | 0 | 1 | 1 | 0.0 |
| dev-wave-paper-story-20260920b | acceptance-final2.chain.log | 1 | 2 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-paper-story-20260921 | acceptance-final.chain.log | 1 | 1 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-s1a-nine-pair-results | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t1998-b7-fixed5 | acceptance-final.chain.log | 1 | 6 | 3 | 3 | 3 | 0 | 1.0 |
| dev-wave-t1998-b7-fixed5 | acceptance-final2.chain.log | 1 | 2 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-t1998-b7-fixed5 | acceptance-final3.chain.log | 1 | 3 | 2 | 2 | 1 | 1 | 0.0 |
| dev-wave-t1998-b7-fixed5 | acceptance-final4.chain.log | 1 | 3 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-t1998-b7-fixed5 | acceptance-final4.chain.log | 5 | 2 | 2 | 2 | 0 | 0 | 0.0 |
| dev-wave-t2153-witness-6 | acceptance-final.chain.log | 1 | 6 | 5 | 5 | 0 | 0 | 1.0 |
| dev-wave-t2153-witness-6 | acceptance-final2.chain.log | 1 | 4 | 2 | 2 | 3 | 0 | 0.0 |
| dev-wave-t2153-witness-6 | acceptance-final3.chain.log | 1 | 3 | 2 | 3 | 1 | 1 | 0.0 |
| dev-wave-t2153-witness-bc | acceptance-final.chain.log | 1 | 5 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2153-witness-requested-us | acceptance-final.chain.log | 1 | 2 | 2 | 2 | 1 | 0 | 0.0 |
| dev-wave-t2153-witness-requested-us | acceptance-final.chain.log | 5 | 1 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-t2243-collection-diag | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2243-collection-diag | acceptance-final.chain.log | 5 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2288-floor-pair-w1 | acceptance-final-1.chain.log | 1 | 3 | 3 | 2 | 1 | 0 | 0.0 |
| dev-wave-t2304-pin-advance | gate-loop-final.log | 1 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-t2304-pin-advance | gate-loop-final.log | 5 | 1 | 1 | 1 | 1 | 0 | 1.0 |
| dev-wave-t2304-pin-advance | gate-loop-final.log | 9 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2304-pin-advance | gate-loop-final2.log | 1 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-t2304-pin-advance | gate-loop-final2.log | 5 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-t2304-pin-advance | gate-loop-final2.log | 9 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-t2304-pin-advance | gate-loop-final3.log | 1 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-t2304-pin-advance | gate-loop-final4.log | 1 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-t2304-pin-advance | gate-loop-pre.log | 1 | 5 | 5 | 5 | 1 | 0 | 0.0 |
| dev-wave-t2344-closure-stage | acceptance-final.chain.log | 1 | 1 | 0 | 0 | 1 | 0 | 0.0 |
| dev-wave-t2344-closure-stage | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2384-terminal-outer-shape | gate-loop-final.log | 1 | 9 | 7 | 7 | 0 | 1 | 0.0 |
| dev-wave-t2384-terminal-outer-shape | gate-loop-final.log | 5 | 6 | 3 | 3 | 0 | 1 | 0.0 |
| dev-wave-t2489-nodes5-local-lock | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2609-t2656-provenance-cost | gate-loop-final.log | 1 | 7 | 5 | 5 | 0 | 1 | 0.0 |
| dev-wave-t2610-b7-limited | acceptance-final-1.chain.log | 1 | 1 | 1 | 1 | 1 | 0 | 0.0 |
| dev-wave-t2610-fig10 | gate-loop-final.log | 1 | 9 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-t2610-fig10 | gate-loop-final.log | 2 | 1 | 1 | 0 | 1 | 0 | 0.0 |
| dev-wave-t2620-zombie-residual | gate-loop-final-le1.log | 1 | 9 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-t2620-zombie-residual | gate-loop-final.log | 1 | 5 | 4 | 4 | 0 | 2 | 0.0 |
| dev-wave-t2620-zombie-residual | gate-loop-final.log | 5 | 4 | 3 | 3 | 1 | 2 | 0.0 |
| dev-wave-t2629-legacy-compiler-reach | gate-loop-final.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2629-legacy-compiler-reach | gate-loop-final.log | 5 | 1 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-t2632-evidence-provenance | acceptance-final.chain.log | 1 | 3 | 3 | 3 | 0 | 1 | 0.0 |
| dev-wave-t2700-prewarm-ab | gate-loop-final.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2709-blob-transfer-cost | gate-loop-final.log | 1 | 4 | 3 | 3 | 0 | 1 | 0.0 |
| dev-wave-t2711-ancestry-check | gate-loop-final.log | 1 | 5 | 5 | 5 | 0 | 1 | 0.0 |
| dev-wave-t2711-ancestry-check | gate-loop-final2.log | 1 | 9 | 4 | 4 | 1 | 1 | 0.0 |
| dev-wave-t2737-noninert-codex | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2737-noninert-codex | acceptance-final2.chain.log | 1 | 3 | 3 | 3 | 1 | 0 | 0.0 |
| dev-wave-t2766-pairing-ab | gate-loop-final.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2773-mocc-template-wave2 | acceptance-final-1.chain.log | 1 | 6 | 6 | 6 | 0 | 1 | 0.0 |
| dev-wave-t2773-mocc-template-wave2 | acceptance-final-2.chain.log | 1 | 4 | 4 | 4 | 0 | 1 | 0.0 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-final.chain.log | 1 | 6 | 4 | 4 | 1 | 0 | 1.0 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-final2.chain.log | 1 | 3 | 1 | 1 | 1 | 0 | 0.0 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-final3.chain.log | 1 | 1 | 0 | 0 | 1 | 1 | 0.0 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w2final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w3final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w4final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w4final2.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2786-base-decomposition | acceptance-final.chain.log | 1 | 6 | 4 | 4 | 1 | 0 | 1.0 |
| dev-wave-t2786-base-decomposition | acceptance-final2.chain.log | 1 | 5 | 3 | 3 | 1 | 0 | 1.0 |
| dev-wave-t2786-base-decomposition | acceptance-final2.chain.log | 5 | 3 | 3 | 3 | 1 | 0 | 0.0 |
| dev-wave-t2789-acceptance-ops-docs | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2790-t1259-scan-timeout | acceptance-final.chain.log | 1 | 6 | 6 | 6 | 0 | 1 | 1.0 |
| dev-wave-t2790-t1259-scan-timeout | acceptance-meas.chain.log | 1 | 6 | 6 | 6 | 0 | 0 | 2.0 |
| dev-wave-t2791-mocc-upstream-report | gate-loop-final.log | 1 | 5 | 3 | 2 | 1 | 1 | 0.0 |
| dev-wave-t2792-a1-sized-attempt2 | acceptance-final.chain.log | 1 | 3 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-t2792-a1-sized-attempt2 | acceptance-final3.chain.log | 1 | 3 | 3 | 3 | 1 | 1 | 0.0 |
| dev-wave-t2792-a1-sized-rerun-auth | gate-loop-final.log | 1 | 5 | 4 | 4 | 0 | 0 | 0.0 |
| dev-wave-t2793-fig8b-cohort2 | gate-loop-final.log | 1 | 9 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-t2793-fig8b-cohort2 | gate-loop-final.log | 5 | 3 | 1 | 1 | 1 | 1 | 0.0 |
| dev-wave-t2793-fig8b-cohort2 | gate-loop-final.log | 9 | 1 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2795-k2-pair | acceptance-final.chain.log | 1 | 3 | 3 | 3 | 1 | 0 | 0.0 |
| dev-wave-t2795-pair-launcher | gate-loop-final.log | 1 | 5 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-t2795-pair-launcher | gate-loop-final2.log | 1 | 1 | 0 | 0 | 1 | 0 | 1.0 |
| dev-wave-t2796-docs4 | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2796-docs4 | acceptance-final2.chain.log | 1 | 1 | 0 | 0 | 1 | 1 | 0.0 |
| dev-wave-t2796-docs4 | acceptance-final3.chain.log | 1 | 5 | 5 | 5 | 0 | 0 | 1.0 |
| dev-wave-t2797-b5-contrast | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2797-b5-contrast | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2797-b5-contrast | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2800-dead-code-delete | gate-loop-final.log | 1 | 5 | 5 | 4 | 1 | 0 | 0.0 |
| dev-wave-t2803-provenance-receipt | acceptance-final.chain.log | 1 | 1 | 1 | 1 | 1 | 0 | 0.0 |
| dev-wave-t2803-provenance-receipt | acceptance-final2.chain.log | 1 | 1 | 1 | 1 | 1 | 0 | 0.0 |
| dev-wave-t2803-provenance-receipt | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2804-provenance-timeout-contract | gate-loop-final.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2804-provenance-timeout-contract | gate-loop-final.log | 5 | 1 | 1 | 0 | 1 | 0 | 0.0 |
| dev-wave-t2807-b8-prerun | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-t2810-g1-launch-validation | gate-loop-final.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2810-g1-launch-validation | gate-loop-final2.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2813-o26-inventory | gate-loop-final.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2814-cleanup-command | gate-loop-final.log | 1 | 1 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2814-cleanup-command | gate-loop-final.log | 5 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final2.chain.aborted-before-submit.log | 1 | 1 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final4.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-ref.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-verifier-capacity | acceptance-final.chain.log | 1 | 5 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-verify-phase-adopted-backoff | acceptance-final.chain.log | 1 | 5 | 2 | 1 | 3 | 0 | 0.0 |
| dev-wave-wall-decomp | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| rulings-all-20260920 | acceptance-final-1.chain.log | 1 | 9 | 2 | 2 | 1 | 0 | 0.0 |
| rulings-all-20260920b | acceptance-final-1.chain.log | 1 | 1 | 1 | 1 | 1 | 0 | 0.0 |
| rulings-all-20260920c | acceptance-final-1.chain.log | 1 | 3 | 3 | 2 | 1 | 0 | 0.0 |
| rulings-all-20260921 | acceptance-final-1.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |

## 飢餓候補と長時間待ち

長時間待ち ≥1800秒、飢餓候補 = 長時間待ちかつ同一区間の拒否 ≥2。事例探索条件であり一般定義ではない。

| 母集合 | wave | file | segment | kind | 秒 | 拒否 | 飢餓候補 | 同時待ち最大 | 走行最大 | leaders_grep | 閉門 leaders 起因 tick / 全 tick |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent | dev-wave-paper-story-20260920b | acceptance-final.chain.log | 1 | observed-wait | 4838.0 | 0 | False | 3 | 2 | substring | 33 / 41 |
| since | dev-wave-acceptance-worker-time-trim | acceptance-final.chain.log | 1 | observed-wait | 2033.0 | 0 | False | 6 | 2 | substring | 16 / 18 |
| since | dev-wave-b10-waiting-grid-results | gate-loop-final.log | 1 | observed-wait | 3084.0 | 0 | False | 5 | 2 | substring | 22 / 27 |
| since | dev-wave-claim-evidence-2026-09-20 | acceptance-final.chain.log | 1 | observed-wait | 2478.0 | 0 | False | 9 | 2 | substring | 13 / 21 |
| since | dev-wave-cleanup-backup-loss-record | acceptance-final2.chain.log | 1 | observed-wait | 2336.0 | 1 | False | 3 | 2 | substring | 14 / 20 |
| since | dev-wave-dead-code-inventory | acceptance-a1.chain.log | 1 | observed-wait | 2391.0 | 0 | False | 6 | 1 | substring | 19 / 21 |
| since | dev-wave-fig3b-arc-status | gate-loop-final.log | 1 | observed-wait | 2134.0 | 1 | False | 9 | 2 | substring | 13 / 19 |
| since | dev-wave-k2-loop-round3 | acceptance-final.chain.log | 1 | observed-wait | 2804.0 | 1 | False | 2 | 1 | substring | 18 / 24 |
| since | dev-wave-mocc-g2-observation-results | gate-loop-final.log | 1 | observed-wait | 2006.0 | 1 | False | 5 | 2 | substring | 13 / 18 |
| since | dev-wave-mocc-g2-observation-results | gate-loop-final2.log | 1 | observed-wait | 3157.0 | 1 | False | 9 | 2 | substring | 19 / 27 |
| since | dev-wave-mocc-witlight-arm-run | acceptance-final-1.chain.log | 1 | observed-wait | 2027.0 | 0 | False | 4 | 2 | substring | 15 / 18 |
| since | dev-wave-p24-static-backoff-sweep-results | acceptance-final.chain.log | 5 | censored | 3500.0 | 2 | True | 5 | 3 | substring | 22 / 29 |
| since | dev-wave-p24-static-backoff-sweep-results | acceptance-final2.chain.log | 1 | observed-wait | 2539.0 | 0 | False | 5 | 2 | substring | 17 / 22 |
| since | dev-wave-paper-intro-ja | acceptance-final3.chain.log | 1 | observed-wait | 3149.0 | 0 | False | 3 | 2 | argv-anchored | 23 / 28 |
| since | dev-wave-paper-story-20260919 | acceptance-final.chain.log | 1 | observed-wait | 3257.0 | 1 | False | 4 | 2 | substring | 23 / 28 |
| since | dev-wave-paper-story-20260919 | acceptance-final.chain.log | 5 | observed-wait | 6847.0 | 1 | False | 6 | 2 | substring | 51 / 57 |
| since | dev-wave-paper-story-20260919 | acceptance-final2.chain.log | 1 | observed-wait | 2822.0 | 1 | False | 3 | 2 | substring | 19 / 24 |
| since | dev-wave-paper-story-20260920b | acceptance-final.chain.log | 1 | observed-wait | 4838.0 | 0 | False | 3 | 2 | substring | 33 / 41 |
| since | dev-wave-t1998-b7-fixed5 | acceptance-final.chain.log | 1 | observed-wait | 7771.0 | 0 | False | 6 | 2 | substring | 0 / 66 |
| since | dev-wave-t2153-witness-6 | acceptance-final.chain.log | 1 | observed-wait | 6743.0 | 0 | False | 6 | 2 | substring | 52 / 57 |
| since | dev-wave-t2153-witness-bc | acceptance-final.chain.log | 1 | observed-wait | 4159.0 | 0 | False | 5 | 2 | substring | 26 / 35 |
| since | dev-wave-t2304-pin-advance | gate-loop-pre.log | 1 | observed-wait | 2455.0 | 0 | False | 5 | 3 | substring | 16 / 22 |
| since | dev-wave-t2384-terminal-outer-shape | gate-loop-final.log | 1 | observed-wait | 2429.0 | 0 | False | 9 | 2 | substring | 16 / 20 |
| since | dev-wave-t2384-terminal-outer-shape | gate-loop-final.log | 5 | observed-wait | 3323.0 | 0 | False | 6 | 3 | substring | 22 / 29 |
| since | dev-wave-t2610-fig10 | gate-loop-final.log | 1 | censored | 3021.0 | 2 | True | 9 | 2 | substring | 19 / 26 |
| since | dev-wave-t2620-zombie-residual | gate-loop-final-le1.log | 1 | censored | 3383.0 | 0 | False | 9 | 2 | substring | 0 / 29 |
| since | dev-wave-t2709-blob-transfer-cost | gate-loop-final.log | 1 | observed-wait | 1861.0 | 0 | False | 4 | 2 | substring | 9 / 16 |
| since | dev-wave-t2711-ancestry-check | gate-loop-final2.log | 1 | observed-wait | 4151.0 | 2 | True | 9 | 2 | substring | 26 / 36 |
| since | dev-wave-t2778-child-worktree-cleanup | acceptance-final.chain.log | 1 | observed-wait | 6030.0 | 0 | False | 6 | 2 | substring | 46 / 51 |
| since | dev-wave-t2778-child-worktree-cleanup | acceptance-final2.chain.log | 1 | observed-wait | 3104.0 | 0 | False | 3 | 2 | substring | 22 / 26 |
| since | dev-wave-t2786-base-decomposition | acceptance-final.chain.log | 1 | observed-wait | 5515.0 | 0 | False | 6 | 2 | substring | 42 / 46 |
| since | dev-wave-t2786-base-decomposition | acceptance-final2.chain.log | 1 | observed-wait | 2394.0 | 2 | True | 5 | 2 | substring | 12 / 20 |
| since | dev-wave-t2791-mocc-upstream-report | gate-loop-final.log | 1 | observed-wait | 3525.0 | 0 | False | 5 | 3 | substring | 25 / 30 |
| since | dev-wave-t2792-a1-sized-rerun-auth | gate-loop-final.log | 1 | observed-wait | 2077.0 | 0 | False | 5 | 2 | substring | 14 / 18 |
| since | dev-wave-t2793-fig8b-cohort2 | gate-loop-final.log | 1 | observed-wait | 4473.0 | 1 | False | 9 | 3 | substring | 28 / 37 |
| since | dev-wave-t2795-k2-pair | acceptance-final.chain.log | 1 | observed-wait | 2377.0 | 0 | False | 3 | 2 | substring | 16 / 20 |
| since | dev-wave-t2795-pair-launcher | gate-loop-final.log | 1 | observed-wait | 2150.0 | 0 | False | 5 | 2 | substring | 13 / 19 |
| since | dev-wave-t2800-dead-code-delete | gate-loop-final.log | 1 | observed-wait | 4407.0 | 1 | False | 5 | 3 | argv-anchored | 28 / 37 |
| since | dev-wave-verifier-capacity | acceptance-final.chain.log | 1 | observed-wait | 2991.0 | 0 | False | 5 | 2 | substring | 19 / 26 |
| since | rulings-all-20260920 | acceptance-final-1.chain.log | 1 | observed-wait | 9317.0 | 2 | True | 9 | 3 | substring | 61 / 80 |
| since-2026-09-19 | dev-wave-acceptance-worker-time-trim | acceptance-final.chain.log | 1 | observed-wait | 2033.0 | 0 | False | 6 | 2 | substring | 16 / 18 |
| since-2026-09-19 | dev-wave-b10-waiting-grid-results | gate-loop-final.log | 1 | observed-wait | 3084.0 | 0 | False | 5 | 2 | substring | 22 / 27 |
| since-2026-09-19 | dev-wave-claim-evidence-2026-09-20 | acceptance-final.chain.log | 1 | observed-wait | 2478.0 | 0 | False | 9 | 2 | substring | 13 / 21 |
| since-2026-09-19 | dev-wave-cleanup-backup-loss-record | acceptance-final2.chain.log | 1 | observed-wait | 2336.0 | 1 | False | 3 | 2 | substring | 14 / 20 |
| since-2026-09-19 | dev-wave-dead-code-inventory | acceptance-a1.chain.log | 1 | observed-wait | 2391.0 | 0 | False | 6 | 1 | substring | 19 / 21 |
| since-2026-09-19 | dev-wave-fig3b-arc-status | gate-loop-final.log | 1 | observed-wait | 2134.0 | 1 | False | 9 | 2 | substring | 13 / 19 |
| since-2026-09-19 | dev-wave-k2-loop-round3 | acceptance-final.chain.log | 1 | observed-wait | 2804.0 | 1 | False | 2 | 1 | substring | 18 / 24 |
| since-2026-09-19 | dev-wave-mocc-g2-observation-results | gate-loop-final.log | 1 | observed-wait | 2006.0 | 1 | False | 5 | 2 | substring | 13 / 18 |
| since-2026-09-19 | dev-wave-mocc-g2-observation-results | gate-loop-final2.log | 1 | observed-wait | 3157.0 | 1 | False | 9 | 2 | substring | 19 / 27 |
| since-2026-09-19 | dev-wave-mocc-witlight-arm-run | acceptance-final-1.chain.log | 1 | observed-wait | 2027.0 | 0 | False | 4 | 2 | substring | 15 / 18 |
| since-2026-09-19 | dev-wave-p24-static-backoff-sweep-results | acceptance-final.chain.log | 5 | censored | 3500.0 | 2 | True | 5 | 3 | substring | 22 / 29 |
| since-2026-09-19 | dev-wave-p24-static-backoff-sweep-results | acceptance-final2.chain.log | 1 | observed-wait | 2539.0 | 0 | False | 5 | 2 | substring | 17 / 22 |
| since-2026-09-19 | dev-wave-paper-intro-ja | acceptance-final3.chain.log | 1 | observed-wait | 3149.0 | 0 | False | 3 | 2 | argv-anchored | 23 / 28 |
| since-2026-09-19 | dev-wave-paper-story-20260919 | acceptance-final.chain.log | 1 | observed-wait | 3257.0 | 1 | False | 4 | 2 | substring | 23 / 28 |
| since-2026-09-19 | dev-wave-paper-story-20260919 | acceptance-final.chain.log | 5 | observed-wait | 6847.0 | 1 | False | 6 | 2 | substring | 51 / 57 |
| since-2026-09-19 | dev-wave-paper-story-20260919 | acceptance-final2.chain.log | 1 | observed-wait | 2822.0 | 1 | False | 3 | 2 | substring | 19 / 24 |
| since-2026-09-19 | dev-wave-paper-story-20260920b | acceptance-final.chain.log | 1 | observed-wait | 4838.0 | 0 | False | 3 | 2 | substring | 33 / 41 |
| since-2026-09-19 | dev-wave-t1998-b7-fixed5 | acceptance-final.chain.log | 1 | observed-wait | 7771.0 | 0 | False | 6 | 2 | substring | 0 / 66 |
| since-2026-09-19 | dev-wave-t2153-witness-6 | acceptance-final.chain.log | 1 | observed-wait | 6743.0 | 0 | False | 6 | 2 | substring | 52 / 57 |
| since-2026-09-19 | dev-wave-t2153-witness-bc | acceptance-final.chain.log | 1 | observed-wait | 4159.0 | 0 | False | 5 | 2 | substring | 26 / 35 |
| since-2026-09-19 | dev-wave-t2304-pin-advance | gate-loop-pre.log | 1 | observed-wait | 2455.0 | 0 | False | 5 | 3 | substring | 16 / 22 |
| since-2026-09-19 | dev-wave-t2384-terminal-outer-shape | gate-loop-final.log | 1 | observed-wait | 2429.0 | 0 | False | 9 | 2 | substring | 16 / 20 |
| since-2026-09-19 | dev-wave-t2384-terminal-outer-shape | gate-loop-final.log | 5 | observed-wait | 3323.0 | 0 | False | 6 | 3 | substring | 22 / 29 |
| since-2026-09-19 | dev-wave-t2610-fig10 | gate-loop-final.log | 1 | censored | 3021.0 | 2 | True | 9 | 2 | substring | 19 / 26 |
| since-2026-09-19 | dev-wave-t2620-zombie-residual | gate-loop-final-le1.log | 1 | censored | 3383.0 | 0 | False | 9 | 2 | substring | 0 / 29 |
| since-2026-09-19 | dev-wave-t2709-blob-transfer-cost | gate-loop-final.log | 1 | observed-wait | 1861.0 | 0 | False | 4 | 2 | substring | 9 / 16 |
| since-2026-09-19 | dev-wave-t2711-ancestry-check | gate-loop-final2.log | 1 | observed-wait | 4151.0 | 2 | True | 9 | 2 | substring | 26 / 36 |
| since-2026-09-19 | dev-wave-t2778-child-worktree-cleanup | acceptance-final.chain.log | 1 | observed-wait | 6030.0 | 0 | False | 6 | 2 | substring | 46 / 51 |
| since-2026-09-19 | dev-wave-t2778-child-worktree-cleanup | acceptance-final2.chain.log | 1 | observed-wait | 3104.0 | 0 | False | 3 | 2 | substring | 22 / 26 |
| since-2026-09-19 | dev-wave-t2786-base-decomposition | acceptance-final.chain.log | 1 | observed-wait | 5515.0 | 0 | False | 6 | 2 | substring | 42 / 46 |
| since-2026-09-19 | dev-wave-t2786-base-decomposition | acceptance-final2.chain.log | 1 | observed-wait | 2394.0 | 2 | True | 5 | 2 | substring | 12 / 20 |
| since-2026-09-19 | dev-wave-t2791-mocc-upstream-report | gate-loop-final.log | 1 | observed-wait | 3525.0 | 0 | False | 5 | 3 | substring | 25 / 30 |
| since-2026-09-19 | dev-wave-t2792-a1-sized-rerun-auth | gate-loop-final.log | 1 | observed-wait | 2077.0 | 0 | False | 5 | 2 | substring | 14 / 18 |
| since-2026-09-19 | dev-wave-t2793-fig8b-cohort2 | gate-loop-final.log | 1 | observed-wait | 4473.0 | 1 | False | 9 | 3 | substring | 28 / 37 |
| since-2026-09-19 | dev-wave-t2795-k2-pair | acceptance-final.chain.log | 1 | observed-wait | 2377.0 | 0 | False | 3 | 2 | substring | 16 / 20 |
| since-2026-09-19 | dev-wave-t2795-pair-launcher | gate-loop-final.log | 1 | observed-wait | 2150.0 | 0 | False | 5 | 2 | substring | 13 / 19 |
| since-2026-09-19 | dev-wave-t2800-dead-code-delete | gate-loop-final.log | 1 | observed-wait | 4407.0 | 1 | False | 5 | 3 | argv-anchored | 28 / 37 |
| since-2026-09-19 | dev-wave-verifier-capacity | acceptance-final.chain.log | 1 | observed-wait | 2991.0 | 0 | False | 5 | 2 | substring | 19 / 26 |
| since-2026-09-19 | rulings-all-20260920 | acceptance-final-1.chain.log | 1 | observed-wait | 9317.0 | 2 | True | 9 | 3 | substring | 61 / 80 |

| 母集合 | 長時間待ち n | 飢餓候補 n | うち censored n (飢餓候補) | censored n (長時間待ち) |
| --- | --- | --- | --- | --- |
| recent | 1 | 0 | 0 | 0 |
| since | 39 | 5 | 2 | 3 |
| since-2026-09-19 | 39 | 5 | 2 | 3 |

## 時間帯

| 母集合 | 開始 JST 時 | observed 分布 秒 | 打切り |
| --- | --- | --- | --- |
| recent | 0 | {"max": 108.0, "median": 108.0, "min": 108.0, "n": 1, "p90": 108.0, "sum": 108.0} | 0 |
| recent | 1 | {"max": 143.0, "median": 141.5, "min": 140.0, "n": 2, "p90": 143.0, "sum": 283.0} | 0 |
| recent | 2 | {"max": 745.0, "median": 154.0, "min": 122.0, "n": 6, "p90": 745.0, "sum": 1497.0} | 0 |
| recent | 3 | {"max": 353.0, "median": 204.5, "min": 153.0, "n": 4, "p90": 353.0, "sum": 915.0} | 1 |
| recent | 4 | {"max": 141.0, "median": 137.0, "min": 122.0, "n": 4, "p90": 141.0, "sum": 537.0} | 0 |
| recent | 19 | {"max": 4838.0, "median": 4838.0, "min": 4838.0, "n": 1, "p90": 4838.0, "sum": 4838.0} | 0 |
| recent | 21 | {"max": 1108.0, "median": 270.5, "min": 135.0, "n": 6, "p90": 1108.0, "sum": 2567.0} | 0 |
| recent | 22 | {"max": 384.0, "median": 164.0, "min": 151.0, "n": 4, "p90": 384.0, "sum": 863.0} | 0 |
| recent | 23 | {"max": 164.0, "median": 148.5, "min": 137.0, "n": 6, "p90": 164.0, "sum": 899.0} | 0 |
| since | 0 | {"max": 6847.0, "median": 2391.0, "min": 108.0, "n": 7, "p90": 6847.0, "sum": 24289.0} | 0 |
| since | 1 | {"max": 2394.0, "median": 143.0, "min": 132.0, "n": 7, "p90": 2394.0, "sum": 4722.0} | 0 |
| since | 2 | {"max": 3104.0, "median": 149.5, "min": 109.0, "n": 16, "p90": 2822.0, "sum": 9588.0} | 0 |
| since | 3 | {"max": 353.0, "median": 145.5, "min": 125.0, "n": 10, "p90": 252.0, "sum": 1743.0} | 1 |
| since | 4 | {"max": 141.0, "median": 129.0, "min": 106.0, "n": 6, "p90": 141.0, "sum": 751.0} | 0 |
| since | 5 | {"max": 150.0, "median": 146.0, "min": 142.0, "n": 2, "p90": 150.0, "sum": 292.0} | 0 |
| since | 7 | {"max": 149.0, "median": 134.5, "min": 120.0, "n": 2, "p90": 149.0, "sum": 269.0} | 0 |
| since | 8 | {"max": 9317.0, "median": 1040.5, "min": 137.0, "n": 12, "p90": 3157.0, "sum": 22434.0} | 2 |
| since | 9 | {"max": 4473.0, "median": 2281.5, "min": 176.0, "n": 8, "p90": 4473.0, "sum": 19019.0} | 1 |
| since | 10 | {"max": 1234.0, "median": 630.5, "min": 149.0, "n": 6, "p90": 1234.0, "sum": 3889.0} | 0 |
| since | 12 | {"max": 853.0, "median": 509.5, "min": 166.0, "n": 2, "p90": 853.0, "sum": 1019.0} | 0 |
| since | 13 | {"max": 149.0, "median": 149.0, "min": 149.0, "n": 1, "p90": 149.0, "sum": 149.0} | 0 |
| since | 14 | {"max": 4407.0, "median": 1274.5, "min": 128.0, "n": 10, "p90": 3525.0, "sum": 16493.0} | 1 |
| since | 15 | {"max": 4159.0, "median": 2497.0, "min": 126.0, "n": 6, "p90": 4159.0, "sum": 12413.0} | 0 |
| since | 16 | {"max": 2150.0, "median": 2150.0, "min": 2150.0, "n": 1, "p90": 2150.0, "sum": 2150.0} | 0 |
| since | 17 | {"max": 847.0, "median": 150.5, "min": 131.0, "n": 8, "p90": 847.0, "sum": 2222.0} | 0 |
| since | 18 | {"max": 261.0, "median": 157.0, "min": 124.0, "n": 3, "p90": 261.0, "sum": 542.0} | 0 |
| since | 19 | {"max": 4838.0, "median": 689.0, "min": 211.0, "n": 9, "p90": 4838.0, "sum": 14161.0} | 2 |
| since | 20 | {"max": 2336.0, "median": 1192.0, "min": 164.0, "n": 3, "p90": 2336.0, "sum": 3692.0} | 0 |
| since | 21 | {"max": 1108.0, "median": 246.0, "min": 62.0, "n": 9, "p90": 1108.0, "sum": 3160.0} | 0 |
| since | 22 | {"max": 2804.0, "median": 277.5, "min": 151.0, "n": 6, "p90": 2804.0, "sum": 4560.0} | 0 |
| since | 23 | {"max": 7771.0, "median": 513.0, "min": 137.0, "n": 13, "p90": 5515.0, "sum": 21762.0} | 0 |

n=0 の時間帯は省略。n は observed-wait 数。打切りのみの時間帯も省略し、打切り総数は区間分布に保持。

## 条件変種

script は現存版からの読取りであり過去版の証明ではない。grep 差だけでは偽陽性と断定しない。

| wave | file | maxl (出所) | maxload (出所) | maxpigz (出所) | leaders_grep | recount_scope | streak | gate.conf | 照合可否 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev-wave-a1-sized-attempt2 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | True (filesystem) | available |
| dev-wave-acceptance-worker-time-trim | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-b10-waiting-grid-results | gate-loop-final.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-b5-generator-contrast-prereg | acceptance-1.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-b8-longrun-verify-prereg | acceptance-1.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-branch-residue-cleanup | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-claim-evidence-2026-09-20 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-cleanup-backup-loss-record | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-cleanup-backup-loss-record | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-cleanup-backup-loss-record | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-dead-code-inventory | acceptance-a1.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-fig11-a6-certification | gate-loop-final.log | 2.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-fig13-b10-waiting-grid | gate-loop-final.log | 2.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-fig3b-arc-status | gate-loop-final.log | 1.0 (script) | 30.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-fig3b-arc-status | gate-loop-final2.log | 1.0 (script) | 30.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-k2-loop-fig12 | gate-loop-final.log | unknown (unknown) | unknown (unknown) | unknown (unknown) | unknown (unknown) | unknown (unknown) | unknown (unknown) | False (filesystem) | available |
| dev-wave-k2-loop-originals-lost-downstream | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-k2-loop-round3 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-k2-three-rounds-results | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-k2-three-rounds-results | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-mocc-g2-observation-results | gate-loop-final.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-mocc-g2-observation-results | gate-loop-final2.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-mocc-witlight-arm-run | acceptance-final-1.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-mocc-witlight-results | acceptance-final-1.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-p24-static-backoff-sweep-results | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-p24-static-backoff-sweep-results | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-abstract-conclusion-ja | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-intro-ja | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-paper-intro-ja | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-intro-ja | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-methods-ja-2026-09-20 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-related-work-ja | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-results-ja-2026-09-20 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260919 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260919 | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260919 | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260919 | acceptance-final4.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260920 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260920b | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260920b | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260921 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-s1a-nine-pair-results | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t1998-b7-fixed5 | acceptance-final.chain.log | 1.0 (script) | unknown (unknown) | unknown (unknown) | substring (script) | unknown (unknown) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t1998-b7-fixed5 | acceptance-final2.chain.log | 1.0 (script) | unknown (unknown) | unknown (unknown) | substring (script) | unknown (unknown) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t1998-b7-fixed5 | acceptance-final3.chain.log | 1.0 (script) | unknown (unknown) | unknown (unknown) | substring (script) | unknown (unknown) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t1998-b7-fixed5 | acceptance-final4.chain.log | 1.0 (script) | unknown (unknown) | unknown (unknown) | substring (script) | unknown (unknown) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2153-witness-6 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2153-witness-6 | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-t2153-witness-6 | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2153-witness-bc | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2153-witness-requested-us | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2243-collection-diag | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2288-floor-pair-w1 | acceptance-final-1.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2304-pin-advance | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2304-pin-advance | gate-loop-final2.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2304-pin-advance | gate-loop-final3.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2304-pin-advance | gate-loop-final4.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2304-pin-advance | gate-loop-pre.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2344-closure-stage | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2344-closure-stage | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2384-terminal-outer-shape | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2489-nodes5-local-lock | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | unknown (unknown) | unknown (unknown) | unknown (unknown) | False (filesystem) | available |
| dev-wave-t2609-t2656-provenance-cost | gate-loop-final.log | 1.0 (script) | 30.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2610-b7-limited | acceptance-final-1.chain.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2610-fig10 | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2620-zombie-residual | gate-loop-final-le1.log | 2.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-t2620-zombie-residual | gate-loop-final.log | 2.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2629-legacy-compiler-reach | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2632-evidence-provenance | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2700-prewarm-ab | gate-loop-final.log | 1.0 (script) | 30.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2709-blob-transfer-cost | gate-loop-final.log | 1.0 (script) | 30.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2711-ancestry-check | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2711-ancestry-check | gate-loop-final2.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2737-noninert-codex | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | True (filesystem) | available |
| dev-wave-t2737-noninert-codex | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | True (filesystem) | available |
| dev-wave-t2766-pairing-ab | gate-loop-final.log | 1.0 (script) | 30.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2773-mocc-template-wave2 | acceptance-final-1.chain.log | 1.0 (script) | 60.0 (script) | 1.0 (script) | argv-anchored (script) | unknown (unknown) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2773-mocc-template-wave2 | acceptance-final-2.chain.log | 1.0 (script) | 60.0 (script) | 1.0 (script) | argv-anchored (script) | unknown (unknown) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2778-child-worktree-cleanup | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-t2778-child-worktree-cleanup | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2778-child-worktree-cleanup | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w2final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w3final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w4final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2778-child-worktree-cleanup | acceptance-w4final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2786-base-decomposition | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2786-base-decomposition | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2789-acceptance-ops-docs | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | True (filesystem) | available |
| dev-wave-t2790-t1259-scan-timeout | acceptance-final.chain.log | 1.0 (log); 2.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | True (filesystem) | available |
| dev-wave-t2790-t1259-scan-timeout | acceptance-meas.chain.log | 2.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | True (filesystem) | available |
| dev-wave-t2791-mocc-upstream-report | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2792-a1-sized-attempt2 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2792-a1-sized-attempt2 | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2792-a1-sized-rerun-auth | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2793-fig8b-cohort2 | gate-loop-final.log | 1.0 (script) | 30.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2795-k2-pair | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2795-pair-launcher | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2795-pair-launcher | gate-loop-final2.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2796-docs4 | acceptance-final.chain.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2796-docs4 | acceptance-final2.chain.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2796-docs4 | acceptance-final3.chain.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2797-b5-contrast | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2797-b5-contrast | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2797-b5-contrast | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2800-dead-code-delete | gate-loop-final.log | 1.0 (script) | 60.0 (script) | 3.0 (script) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | True (filesystem) | available |
| dev-wave-t2803-provenance-receipt | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2803-provenance-receipt | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-t2803-provenance-receipt | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2804-provenance-timeout-contract | gate-loop-final.log | 1.0 (log) | 60.0 (log) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2807-b8-prerun | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2810-g1-launch-validation | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2810-g1-launch-validation | gate-loop-final2.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2813-o26-inventory | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2814-cleanup-command | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final2.chain.aborted-before-submit.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final4.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-ref.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-verifier-capacity | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-verify-phase-adopted-backoff | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-wall-decomp | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260920 | acceptance-final-1.chain.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260920b | acceptance-final-1.chain.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260920c | acceptance-final-1.chain.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260921 | acceptance-final-1.chain.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |

## sensitivity (仮定付き参考模型、効果見積りではない)

連続2 tickと直後の記録 recount (無ければ直前 tick の leaders (推定))。b0 は各 tick の実条件 (log/script の maxl・maxload) を同じ模型へ適用した候補 tick。差は代替候補 tick − b0 秒、負なら早く開いたであろう。

実 GO − b0 は jitter + recount の実費等を含む模型と実の差として別掲。pigz、他 wave の応答、jitter・位相・FIFO の効果は模型に含めない。基準不明・成立機会なしは差の分布から除外。

| 母集合 | 条件 | n | min | 中央値 | p90 | 最大 | 合計 (秒) | 基準不明・成立機会なし |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent | 実条件 = 模型基準 | 34 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| recent | maxl=1,maxload=60 | 33 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 |
| recent | maxl=1,maxload=80 | 33 | -932.0 | 0.0 | 0.0 | 0.0 | -932.0 | 1 |
| recent | maxl=2,maxload=60 | 34 | -4685.0 | 0.0 | 0.0 | 0.0 | -7375.0 | 0 |
| recent | maxl=2,maxload=80 | 34 | -4685.0 | 0.0 | 0.0 | 0.0 | -7491.0 | 0 |
| recent | maxl=3,maxload=60 | 34 | -4685.0 | 0.0 | 0.0 | 0.0 | -7375.0 | 0 |
| recent | maxl=3,maxload=80 | 34 | -4685.0 | 0.0 | 0.0 | 0.0 | -7491.0 | 0 |
| recent | 実 GO − b0 | 34 | 2.0 | 20.0 | 39.0 | 44.0 | 719.0 | 0 |
| since | 実条件 = 模型基準 | 141 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 6 |
| since | maxl=1,maxload=60 | 135 | -602.0 | 0.0 | 0.0 | 0.0 | -602.0 | 12 |
| since | maxl=1,maxload=80 | 135 | -1881.0 | 0.0 | 0.0 | 0.0 | -5728.0 | 12 |
| since | maxl=2,maxload=60 | 141 | -9181.0 | 0.0 | 0.0 | 0.0 | -132794.0 | 6 |
| since | maxl=2,maxload=80 | 141 | -9181.0 | -119.0 | 0.0 | 0.0 | -133804.0 | 6 |
| since | maxl=3,maxload=60 | 141 | -9181.0 | -110.0 | 0.0 | 0.0 | -135276.0 | 6 |
| since | maxl=3,maxload=80 | 141 | -9181.0 | -120.0 | 0.0 | 0.0 | -136286.0 | 6 |
| since | 実 GO − b0 | 141 | 0.0 | 20.0 | 41.0 | 1046.0 | 5103.0 | 6 |

感度分析の寄与上位: 差 (代替 − b0) が負の区間を差の小さい順。同差は wave・file・segment 順。maxl=2,maxload=60 は各母集合で最大15行、maxl=1,maxload=80 は最大10行。

| 母集合 | 条件 | wave | file | segment | observed 秒 | 差 (代替 − b0) 秒 | GO 直前 leaders | GO 直前走行数 | leaders_grep |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent | maxl=2,maxload=60 | dev-wave-paper-story-20260920b | acceptance-final.chain.log | 1 | 4838.0 | -4685.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-paper-story-20260920b | acceptance-final2.chain.log | 1 | 1108.0 | -816.0 | 0.0 | 0 | substring |
| recent | maxl=2,maxload=60 | dev-wave-t2814-cleanup-command | gate-loop-final.log | 1 | 745.0 | -613.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-k2-loop-originals-lost-downstream | acceptance-final.chain.log | 1 | 642.0 | -513.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-t2813-o26-inventory | gate-loop-final.log | 1 | 384.0 | -257.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-t2810-g1-launch-validation | gate-loop-final.log | 1 | 353.0 | -240.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-paper-related-work-ja | acceptance-final.chain.log | 1 | 295.0 | -132.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final3.chain.log | 1 | 252.0 | -119.0 | 0.0 | 0 | argv-anchored |
| recent | maxl=1,maxload=80 | dev-wave-paper-story-20260920b | acceptance-final2.chain.log | 1 | 1108.0 | -932.0 | 0.0 | 0 | substring |
| since | maxl=2,maxload=60 | rulings-all-20260920 | acceptance-final-1.chain.log | 1 | 9317.0 | -9181.0 | 0.0 | 0 | substring |
| since | maxl=2,maxload=60 | dev-wave-paper-story-20260919 | acceptance-final.chain.log | 5 | 6847.0 | -6688.0 | 1.0 | 0 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2153-witness-6 | acceptance-final.chain.log | 1 | 6743.0 | -6517.0 | 1.0 | 0 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2778-child-worktree-cleanup | acceptance-final.chain.log | 1 | 6030.0 | -5914.0 | 1.0 | 0 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2786-base-decomposition | acceptance-final.chain.log | 1 | 5515.0 | -5394.0 | 1.0 | 0 | substring |
| since | maxl=2,maxload=60 | dev-wave-paper-story-20260920b | acceptance-final.chain.log | 1 | 4838.0 | -4685.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2793-fig8b-cohort2 | gate-loop-final.log | 1 | 4473.0 | -4346.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2800-dead-code-delete | gate-loop-final.log | 1 | 4407.0 | -4240.0 | 0.0 | 0 | argv-anchored |
| since | maxl=2,maxload=60 | dev-wave-t2711-ancestry-check | gate-loop-final2.log | 1 | 4151.0 | -4029.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2153-witness-bc | acceptance-final.chain.log | 1 | 4159.0 | -4005.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2791-mocc-upstream-report | gate-loop-final.log | 1 | 3525.0 | -3271.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2384-terminal-outer-shape | gate-loop-final.log | 5 | 3323.0 | -3203.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-paper-story-20260919 | acceptance-final.chain.log | 1 | 3257.0 | -3138.0 | 1.0 | 0 | substring |
| since | maxl=2,maxload=60 | dev-wave-mocc-g2-observation-results | gate-loop-final2.log | 1 | 3157.0 | -3009.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-paper-intro-ja | acceptance-final3.chain.log | 1 | 3149.0 | -2980.0 | 1.0 | 1 | argv-anchored |
| since | maxl=1,maxload=80 | dev-wave-t2795-pair-launcher | gate-loop-final.log | 1 | 2150.0 | -1881.0 | 1.0 | 1 | substring |
| since | maxl=1,maxload=80 | dev-wave-p24-static-backoff-sweep-results | acceptance-final2.chain.log | 1 | 2539.0 | -1366.0 | 1.0 | 0 | substring |
| since | maxl=1,maxload=80 | dev-wave-paper-story-20260920b | acceptance-final2.chain.log | 1 | 1108.0 | -932.0 | 0.0 | 0 | substring |
| since | maxl=1,maxload=80 | dev-wave-t2709-blob-transfer-cost | gate-loop-final.log | 1 | 1861.0 | -602.0 | 1.0 | 1 | substring |
| since | maxl=1,maxload=80 | dev-wave-cleanup-backup-loss-record | acceptance-final3.chain.log | 1 | 398.0 | -269.0 | 1.0 | 1 | substring |
| since | maxl=1,maxload=80 | dev-wave-t2800-dead-code-delete | gate-loop-final.log | 1 | 4407.0 | -241.0 | 0.0 | 0 | argv-anchored |
| since | maxl=1,maxload=80 | dev-wave-t2304-pin-advance | gate-loop-pre.log | 1 | 2455.0 | -206.0 | 0.0 | 0 | substring |
| since | maxl=1,maxload=80 | dev-wave-a1-sized-attempt2 | acceptance-final.chain.log | 1 | 893.0 | -123.0 | 0.0 | 0 | substring |
| since | maxl=1,maxload=80 | dev-wave-t2610-fig10 | gate-loop-final.log | 2 | 853.0 | -108.0 | 0.0 | 0 | substring |

## 欠測・打切り・未知行

24時間以上の無記録空白は時刻文字列のみから識別できない。複数逆行または錨と mtime の日付矛盾は未解決。未知行は JSON に逐語を保持。

| 分類 | 行数 |
| --- | --- |
| info | 214 |
| other | 0 |

| file | date_status | 理由 | info 数 | other 数 | 打切り数 | GO に started 無し |
| --- | --- | --- | --- | --- | --- | --- |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-worker-time-trim/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b10-waiting-grid-results/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/acceptance-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b8-longrun-verify-prereg/acceptance-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-branch-residue-cleanup/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-claim-evidence-2026-09-20/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-backup-loss-record/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-backup-loss-record/acceptance-final2.chain.log | mtime-estimated (推定) | [] | 4 | 0 | 0 | 1 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-backup-loss-record/acceptance-final3.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-dead-code-inventory/acceptance-a1.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig3b-arc-status/gate-loop-final.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig3b-arc-status/gate-loop-final2.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-originals-lost-downstream/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-round3/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-three-rounds-results/acceptance-final.chain.log | anchored | [] | 2 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-three-rounds-results/acceptance-final2.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-g2-observation-results/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-g2-observation-results/gate-loop-final2.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/acceptance-final-1.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-results/acceptance-final-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-p24-static-backoff-sweep-results/acceptance-final.chain.log | anchored | [] | 1 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-p24-static-backoff-sweep-results/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-abstract-conclusion-ja/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-intro-ja/acceptance-final.chain.log | mtime-estimated (推定) | [] | 0 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-intro-ja/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-intro-ja/acceptance-final3.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-2026-09-20/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-related-work-ja/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-ja-2026-09-20/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260919/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260919/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260919/acceptance-final3.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260919/acceptance-final4.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260920/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260920b/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260920b/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260921/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1a-nine-pair-results/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1998-b7-fixed5/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1998-b7-fixed5/acceptance-final2.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1998-b7-fixed5/acceptance-final3.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1998-b7-fixed5/acceptance-final4.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/acceptance-final2.chain.log | mtime-estimated (推定) | [] | 7 | 0 | 0 | 1 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/acceptance-final3.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-bc/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/acceptance-final.chain.log | anchored | [] | 6 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2243-collection-diag/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w1/acceptance-final-1.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2304-pin-advance/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2304-pin-advance/gate-loop-final2.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2304-pin-advance/gate-loop-final3.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2304-pin-advance/gate-loop-final4.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2304-pin-advance/gate-loop-pre.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-nodes5-local-lock/acceptance-final3.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2609-t2656-provenance-cost/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-b7-limited/acceptance-final-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/gate-loop-final.log | anchored | [] | 0 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2620-zombie-residual/gate-loop-final-le1.log | mtime-estimated (推定) | [] | 0 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2620-zombie-residual/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2629-legacy-compiler-reach/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-evidence-provenance/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2709-blob-transfer-cost/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2711-ancestry-check/gate-loop-final.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2711-ancestry-check/gate-loop-final2.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/acceptance-final-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/acceptance-final-2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/acceptance-final.chain.log | mtime-estimated (推定) | [] | 5 | 0 | 0 | 1 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/acceptance-final2.chain.log | anchored | [] | 5 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/acceptance-final3.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/acceptance-w2final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/acceptance-w3final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/acceptance-w4final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/acceptance-w4final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2786-base-decomposition/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2786-base-decomposition/acceptance-final2.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2789-acceptance-ops-docs/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2790-t1259-scan-timeout/acceptance-final.chain.log | anchored | [] | 6 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2790-t1259-scan-timeout/acceptance-meas.chain.log | anchored | [] | 6 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2791-mocc-upstream-report/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/acceptance-final3.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-rerun-auth/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2793-fig8b-cohort2/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-pair-launcher/gate-loop-final.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-pair-launcher/gate-loop-final2.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2796-docs4/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2796-docs4/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2796-docs4/acceptance-final3.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/acceptance-final3.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2800-dead-code-delete/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/acceptance-final2.chain.log | mtime-estimated (推定) | [] | 6 | 0 | 0 | 1 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/acceptance-final3.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2804-provenance-timeout-contract/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2810-g1-launch-validation/gate-loop-final.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2810-g1-launch-validation/gate-loop-final2.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/acceptance-final2.chain.aborted-before-submit.log | mtime-estimated (推定) | [] | 0 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/acceptance-final3.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/acceptance-final4.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/acceptance-ref.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-capacity/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wall-decomp/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260920/acceptance-final-1.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260920b/acceptance-final-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260920c/acceptance-final-1.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921/acceptance-final-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |

| 警告 |
| --- |

## self-check

実 log の照合。tuple = (kind, 秒, 再カウント拒否, 飢餓候補, attempt)。

| wave | 結果 | 実測 | 期待 |
| --- | --- | --- | --- |
| dev-wave-t2610-fig10 | passed | [["censored", 3021.0, 2, true, 1], ["observed-wait", 853.0, 0, false, 1]] | [["censored", 3021, 2, true, 1], ["observed-wait", 853, 0, false, 1]] |
| dev-wave-t2814-cleanup-command | passed | [["observed-wait", 745.0, 0, false, 1], ["observed-wait", 122.0, 0, false, 2]] | [["observed-wait", 745, 0, false, 1], ["observed-wait", 122, 0, false, 2]] |
| dev-wave-paper-story-20260921 | passed | [["observed-wait", 149.0, 0, false, 1]] | [["observed-wait", 149, 0, false, 1]] |
| dev-wave-t2243-collection-diag | passed | [["observed-wait", 171.0, 0, false, 1], ["observed-wait", 151.0, 0, false, 2]] | [["observed-wait", 171, 0, false, 1], ["observed-wait", 151, 0, false, 2]] |

