## 母集合と観測区間

母集合は残存門番 log のuntil 以前の最後の門番行の時刻順の wave。landed は選択条件にしない。日付は JST、mtime 復元は (推定)。

since は log mtime の下限。直近 wave 表は since 前も含む全起動回・attempt を保持。観測期間は選択キー期間と別掲。

| 項目 | 値 |
| --- | --- |
| since (log mtime 下限) | 2026-09-21 |
| until | 2026-09-26T14:38:00+09:00 |
| exclude_wave | ["dev-wave-t2838-gate-argv-unify"] |
| 門番 file 数 | 140 |
| wave 数 | 84 |
| 直近 wave 数 | 20 |
| 選択キー期間 JST | ["2026-09-23T09:45:22+09:00", "2026-09-26T14:35:21+09:00"] |
| 直近の観測区間 JST | ["2026-09-23T08:47:50+09:00", "2026-09-26T14:35:22+09:00"] |
| 日付未解決 file 数 | 0 |
| mtime 日付復元 file 数 (推定) | 5 |
| observed-wait 数 | 139 |
| censored 数 | 5 |

## wave 表 (直近 20)

| wave | 種別 (slug、確認可能な範囲) | green-receipt | land-log | 起動回 | GO | 再投入 | 観測待ち和 秒 | 打切り | 欠測 file | 拒否 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev-wave-t2864-comsys-refs-sec7 | 実装 | no | no-file | 1 | 1 | 0 | 167.0 | 0 | 0 | 0 |
| dev-wave-t2273-shard0-local-copy | 実装 | no | yes | 2 | 2 | 1 | 328.0 | 0 | 0 | 0 |
| t2851-transfer-runner | 実装 | yes | yes | 2 | 2 | 1 | 350.0 | 0 | 0 | 0 |
| dev-wave-t2865-silo-small-compare | 実装 | yes | yes | 2 | 2 | 1 | 300.0 | 0 | 0 | 0 |
| dev-wave-t2847-sort-nonswo | 実装 | yes | yes | 1 | 1 | 0 | 141.0 | 0 | 0 | 0 |
| dev-wave-t2847-mutation-run | 実装 | yes | yes | 4 | 4 | 3 | 1785.0 | 0 | 0 | 1 |
| dev-wave-paper-story-20260923 | paper | yes | yes | 4 | 4 | 3 | 1826.0 | 0 | 0 | 0 |
| rulings-all-20260923c | rulings | no | yes | 2 | 2 | 1 | 1294.0 | 0 | 0 | 0 |
| dev-wave-t2854-unit5-v3-wiring | 実装 | yes | yes | 1 | 1 | 0 | 351.0 | 0 | 0 | 0 |
| dev-wave-t2858-mocc-xp-pin | 実装 | no | yes | 1 | 1 | 0 | 641.0 | 0 | 0 | 0 |
| dev-wave-t2853-rerun-plan | 実装 | yes | yes | 1 | 1 | 0 | 1232.0 | 0 | 0 | 0 |
| rulings-all-20260923b | rulings | no | yes | 1 | 1 | 0 | 136.0 | 0 | 0 | 0 |
| dev-wave-t2273-acceptance-bottleneck-diag | 診断 | no | yes | 2 | 3 | 2 | 1698.0 | 0 | 0 | 1 |
| dev-wave-t2854-v3-existence | 実装 | yes | yes | 1 | 1 | 0 | 3195.0 | 0 | 0 | 1 |
| dev-wave-t2850-trial-prereg | 実装 | yes | yes | 2 | 2 | 1 | 5153.0 | 0 | 0 | 1 |
| dev-wave-t2847-verifier-capacity | 実装 | yes | yes | 1 | 1 | 0 | 516.0 | 0 | 0 | 0 |
| dev-wave-t2854-mocc-v3-emitter | 実装 | yes | yes | 2 | 2 | 1 | 1614.0 | 0 | 0 | 1 |
| dev-wave-t2847-corpus-gaps | 実装 | yes | yes | 2 | 1 | 0 | 800.0 | 1 | 0 | 0 |
| dev-wave-codex-model-sol | 実装 | yes | yes | 1 | 1 | 0 | 1247.0 | 0 | 0 | 0 |
| rulings-all-20260923a | rulings | no | yes | 2 | 2 | 1 | 2540.0 | 0 | 0 | 0 |

出所: file 実在 / grep。同 dir の acceptance-receipt-green.json の実在と land*.log / land*.stdout / land-*.json の単語 landed を確認。landed の断定ではない。

## 区間分布

秒。p90 は nearest rank。打切り・日付未解決を observed-wait 分布に混ぜない。

| 母集合/条件 | n | 中央値 | p90 | 最大 | 打切り | 欠測区間 | 拒否 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| recent/all | 35 | 351.0 | 1472.0 | 3681.0 | 1 | 0 | 5 |
| recent/maxl<=1 | 30 | 296.5 | 1384.0 | 3681.0 | 1 | 0 | 5 |
| recent/other-known | 0 | unknown | unknown | unknown | 0 | 0 | 0 |
| recent/unknown | 5 | 781.0 | 1759.0 | 1759.0 | 0 | 0 | 0 |
| since/all | 139 | 174.0 | 1688.0 | 4604.0 | 5 | 0 | 17 |
| since/maxl<=1 | 125 | 176.0 | 1688.0 | 4604.0 | 4 | 0 | 17 |
| since/other-known | 0 | unknown | unknown | unknown | 0 | 0 | 0 |
| since/unknown | 14 | 152.0 | 1117.0 | 1759.0 | 1 | 0 | 0 |
| since-2026-09-19/all | 139 | 174.0 | 1688.0 | 4604.0 | 5 | 0 | 17 |
| since-2026-09-19/maxl<=1 | 125 | 176.0 | 1688.0 | 4604.0 | 4 | 0 | 17 |
| since-2026-09-19/other-known | 0 | unknown | unknown | unknown | 0 | 0 | 0 |
| since-2026-09-19/unknown | 14 | 152.0 | 1117.0 | 1759.0 | 1 | 0 | 0 |

| 母集合 | wave 観測待ち和の分布 (秒) |
| --- | --- |
| recent | {"max": 5153.0, "median": 1016.0, "min": 136.0, "n": 20, "p90": 2540.0, "sum": 25314.0} |
| since | {"max": 5393.0, "median": 443.0, "min": 105.0, "n": 84, "p90": 2824.0, "sum": 85749.0} |

| 区間種類 | 分布 (秒) |
| --- | --- |
| retry-prep | {"max": 60.0, "median": 0.5, "min": 0.0, "n": 4, "p90": 60.0, "sum": 61.0} |
| submit-prep | {"max": 581.0, "median": 1.0, "min": 0.0, "n": 138, "p90": 11.0, "sum": 1461.0} |
| run | {"max": 1957.0, "median": 739.0, "min": 9.0, "n": 137, "p90": 1508.0, "sum": 119487.0} |

## 閉門理由内訳

| recent | tick 数 | 分 (推定、直前 tick 配分、因果寄与ではない) |
| --- | --- | --- |
| open | 87 | 127.683 |
| leaders-only | 127 | 258.483 |
| load-only | 0 | 0.0 |
| both | 0 | 0.0 |
| pigz | 0 | 0.0 |
| unknown | 37 | 66.167 |

| since | tick 数 | 分 (推定、直前 tick 配分、因果寄与ではない) |
| --- | --- | --- |
| open | 341 | 480.467 |
| leaders-only | 439 | 880.067 |
| load-only | 5 | 10.633 |
| both | 6 | 11.833 |
| pigz | 0 | 0.0 |
| unknown | 68 | 111.283 |

| 母集合 | leaders-only + both の走行数 | tick 数 | 分 (推定、直前 tick 配分) |
| --- | --- | --- | --- |
| recent | 0 | 0 | 0.0 |
| recent | 1 | 29 | 58.6 |
| recent | ≥2 | 98 | 199.883 |
| since | 0 | 0 | 0.0 |
| since | 1 | 61 | 122.9 |
| since | ≥2 | 384 | 769.0 |

走行数 ≥2 は実在する走行中の受入との競合。≤1 は記録 leaders と走行数の不一致 (偽 leader・log の無い走行・started/finished の欠落のいずれか、断定しない)。走行終点の rc / 打切り補完は推定であり、競合の照合もその限界を持つ。

leaders 起因閉門 (leaders-only + both): 判定方式 × 走行数。0 件の組合せも表示。

| 母集合 | leaders_grep | 走行数 | tick 数 | 分 (推定、直前 tick 配分) |
| --- | --- | --- | --- | --- |
| recent | substring | 0 | 0 | 0.0 |
| recent | substring | 1 | 12 | 24.1 |
| recent | substring | ≥2 | 58 | 119.067 |
| recent | argv-anchored | 0 | 0 | 0.0 |
| recent | argv-anchored | 1 | 17 | 34.5 |
| recent | argv-anchored | ≥2 | 40 | 80.817 |
| recent | unknown | 0 | 0 | 0.0 |
| recent | unknown | 1 | 0 | 0.0 |
| recent | unknown | ≥2 | 0 | 0.0 |
| since | substring | 0 | 0 | 0.0 |
| since | substring | 1 | 44 | 88.4 |
| since | substring | ≥2 | 261 | 524.317 |
| since | argv-anchored | 0 | 0 | 0.0 |
| since | argv-anchored | 1 | 17 | 34.5 |
| since | argv-anchored | ≥2 | 123 | 244.683 |
| since | unknown | 0 | 0 | 0.0 |
| since | unknown | 1 | 0 | 0.0 |
| since | unknown | ≥2 | 0 | 0.0 |

同じ leaders 起因閉門 tick の記録 leaders − 走行数の内訳。

| 母集合 | leaders_grep | 走行数 | 差 ≤0 tick | 差 1 tick | 差 2 tick | 差 ≥3 tick |
| --- | --- | --- | --- | --- | --- | --- |
| recent | substring | 0 | 0 | 0 | 0 | 0 |
| recent | substring | 1 | 0 | 12 | 0 | 0 |
| recent | substring | ≥2 | 58 | 0 | 0 | 0 |
| recent | argv-anchored | 0 | 0 | 0 | 0 | 0 |
| recent | argv-anchored | 1 | 0 | 17 | 0 | 0 |
| recent | argv-anchored | ≥2 | 40 | 0 | 0 | 0 |
| recent | unknown | 0 | 0 | 0 | 0 | 0 |
| recent | unknown | 1 | 0 | 0 | 0 | 0 |
| recent | unknown | ≥2 | 0 | 0 | 0 | 0 |
| since | substring | 0 | 0 | 0 | 0 | 0 |
| since | substring | 1 | 0 | 39 | 5 | 0 |
| since | substring | ≥2 | 232 | 22 | 7 | 0 |
| since | argv-anchored | 0 | 0 | 0 | 0 | 0 |
| since | argv-anchored | 1 | 0 | 17 | 0 | 0 |
| since | argv-anchored | ≥2 | 123 | 0 | 0 | 0 |
| since | unknown | 0 | 0 | 0 | 0 | 0 |
| since | unknown | 1 | 0 | 0 | 0 | 0 |
| since | unknown | ≥2 | 0 | 0 | 0 | 0 |

substring は他 process の argv に `dev_wave_wait.py` と ` acceptance` の両方を含むだけで数える (包み shell・codex 子の prompt 文字列を含みうる)。argv-anchored は interpreter で始まる行だけを数える。差は原因の候補であって断定ではない。

## GO 時点値

| 母集合 | GO 数 | GO 直前 leaders 値:件数 | recount leaders 値:件数 | GO 直前 load1 中央値 | p90 | 最大 |
| --- | --- | --- | --- | --- | --- | --- |
| recent | 35 | 0.0: 18; 1.0: 17 | 0.0: 17; 1.0: 18 | 6.24 | 9.53 | 13.17 |
| since | 139 | 0.0: 53; 1.0: 86 | 0.0: 53; 1.0: 86 | 5.28 | 13.47 | 23.69 |

| wave | file | segment | GO | leaders | load1 | load5 | recount leaders | recount load1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cleanup-0921c-ledger-handover | acceptance-final-1.chain.log | 1 | 2026-09-21T14:14:12+09:00 | 0.0 | 13.68 | 9.19 | 0.0 | - |
| dev-wave-acceptance-resubmit-causes | acceptance-final.chain.log | 1 | 2026-09-21T09:01:11+09:00 | 1.0 | 7.75 | 5.84 | 1.0 | 8.47 |
| dev-wave-branch-residue-cleanup | acceptance-final.chain.log | 1 | 2026-09-21T04:19:14+09:00 | 0.0 | 3.28 | 3.05 | 0.0 | 2.99 |
| dev-wave-codex-model-sol | acceptance-final.chain.log | 1 | 2026-09-23T10:00:31+09:00 | 0.0 | 7.69 | 8.26 | 0.0 | 8.04 |
| dev-wave-codex-selfrun-precheck | acceptance-L1-1.chain.log | 1 | 2026-09-21T10:22:39+09:00 | 1.0 | 10.44 | 12.89 | 1.0 | 10.81 |
| dev-wave-codex-selfrun-precheck | acceptance-L2-1.chain.log | 1 | 2026-09-21T10:58:00+09:00 | 1.0 | 15.38 | 17.06 | 1.0 | 15.18 |
| dev-wave-codex-selfrun-precheck | acceptance-L2-2.chain.log | 1 | 2026-09-21T11:16:34+09:00 | 0.0 | 18.61 | 16.54 | 0.0 | 18.61 |
| dev-wave-codex-selfrun-precheck | acceptance-final.chain.log | 1 | 2026-09-21T09:01:04+09:00 | 1.0 | 7.75 | 5.84 | 1.0 | 8.17 |
| dev-wave-codex-selfrun-precheck | acceptance-final2.chain.log | 1 | 2026-09-21T09:39:20+09:00 | 1.0 | 6.93 | 8.18 | 1.0 | 7.22 |
| dev-wave-comsys2026-manuscript | acceptance-final.chain.log | 1 | 2026-09-22T12:41:42+09:00 | 0.0 | 4.16 | 4.02 | 0.0 | 4.15 |
| dev-wave-dwm08-selfrun-probe | acceptance-final.chain.log | 1 | 2026-09-21T08:13:04+09:00 | 1.0 | 4.58 | 4.8 | 1.0 | 4.37 |
| dev-wave-focus-run-count-diagnosis | acceptance-final.chain.log | 1 | 2026-09-21T09:00:18+09:00 | 0.0 | 5.9 | 5.36 | 0.0 | 5.76 |
| dev-wave-land-roundtrip-diagnosis | acceptance-final.chain.log | 1 | 2026-09-21T09:25:33+09:00 | 0.0 | 7.01 | 5.69 | 0.0 | 6.48 |
| dev-wave-lease-gate-wait-diagnosis | acceptance-final.chain.log | 1 | 2026-09-21T10:22:40+09:00 | 1.0 | 10.7 | 13.32 | 1.0 | 11.14 |
| dev-wave-login-check-wall | acceptance-final.chain.log | 1 | 2026-09-21T10:04:06+09:00 | 1.0 | 23.69 | 20.67 | 1.0 | 27.21 |
| dev-wave-login-check-wall | acceptance-final2.chain.log | 1 | 2026-09-21T11:03:05+09:00 | 1.0 | 18.27 | 17.24 | 1.0 | 17.76 |
| dev-wave-mocc-xp-pin-candidate | acceptance-final.chain.log | 1 | 2026-09-21T15:11:07+09:00 | 1.0 | 5.22 | 4.66 | 1.0 | 4.51 |
| dev-wave-mocc-xp-pin-candidate | acceptance-final.chain.log | 5 | 2026-09-21T15:14:24+09:00 | 1.0 | 3.54 | 4.19 | 1.0 | 3.92 |
| dev-wave-mocc-xp-pin-candidate | acceptance-final2.chain.log | 1 | 2026-09-21T15:42:43+09:00 | 1.0 | 3.62 | 3.05 | 1.0 | 3.72 |
| dev-wave-paper-abstract-conclusion-ja | acceptance-final.chain.log | 1 | 2026-09-21T01:43:40+09:00 | 0.0 | 3.66 | 5.25 | 0.0 | 3.33 |
| dev-wave-paper-b8-pass-ja | acceptance-final.chain.log | 1 | 2026-09-21T15:27:00+09:00 | 1.0 | 3.52 | 3.85 | 1.0 | 3.52 |
| dev-wave-paper-methods-ja-b8 | acceptance-final.chain.log | 1 | 2026-09-21T22:19:39+09:00 | 1.0 | 4.47 | 5.16 | 1.0 | 3.95 |
| dev-wave-paper-methods-ja-b8 | acceptance-final2.chain.log | 1 | 2026-09-21T22:39:54+09:00 | 1.0 | 2.42 | 3.71 | 1.0 | 2.28 |
| dev-wave-paper-methods-ja-b8 | acceptance-final4.chain.log | 1 | 2026-09-21T23:33:33+09:00 | 1.0 | 4.64 | 4.49 | 1.0 | 4.67 |
| dev-wave-paper-story-2026-09-21c | acceptance-final1.chain.log | 1 | 2026-09-21T16:54:23+09:00 | 1.0 | 2.76 | 3.53 | 1.0 | 3.04 |
| dev-wave-paper-story-20260921 | acceptance-final.chain.log | 1 | 2026-09-21T02:36:10+09:00 | 1.0 | 2.39 | 3.6 | 1.0 | 2.56 |
| dev-wave-paper-story-20260923 | acceptance-final.chain.log | 1 | 2026-09-23T20:44:13+09:00 | 1.0 | 13.17 | 10.2 | 1.0 | 17.43 |
| dev-wave-paper-story-20260923 | acceptance-final2.chain.log | 1 | 2026-09-23T21:27:19+09:00 | 1.0 | 6.24 | 7.01 | 1.0 | 4.94 |
| dev-wave-paper-story-20260923 | acceptance-final3.chain.log | 1 | 2026-09-23T21:44:56+09:00 | 1.0 | 6.1 | 6.47 | 1.0 | 7.76 |
| dev-wave-paper-story-20260923 | acceptance-final4.chain.log | 1 | 2026-09-23T22:22:10+09:00 | 1.0 | 6.18 | 7.38 | 1.0 | 6.52 |
| dev-wave-provenance-cold-diag | acceptance-final.chain.log | 1 | 2026-09-21T09:26:19+09:00 | 1.0 | 7.51 | 6.04 | 1.0 | 7.51 |
| dev-wave-r29-items4-9-diagnosis | acceptance-final.chain.log | 1 | 2026-09-21T16:24:05+09:00 | 1.0 | 2.83 | 3.36 | 1.0 | 2.53 |
| dev-wave-silo-function-synthesis-space | acceptance-final.chain.log | 1 | 2026-09-21T23:22:09+09:00 | 1.0 | 4.28 | 3.37 | 1.0 | 4.37 |
| dev-wave-t1851-leftover-audit | acceptance-final.chain.log | 1 | 2026-09-22T09:38:47+09:00 | 1.0 | 8.66 | 11.66 | 1.0 | 8.55 |
| dev-wave-t2273-acceptance-bottleneck-diag | acceptance-final.chain.log | 1 | 2026-09-23T10:25:47+09:00 | 0.0 | 5.39 | 6.21 | 1.0 | 6.4 |
| dev-wave-t2273-acceptance-bottleneck-diag | acceptance-final.chain.log | 5 | 2026-09-23T10:30:12+09:00 | 1.0 | 6.68 | 7.09 | 1.0 | 6.48 |
| dev-wave-t2273-acceptance-bottleneck-diag | acceptance-final2.chain.log | 1 | 2026-09-23T11:03:19+09:00 | 1.0 | 4.44 | 4.55 | 1.0 | 3.91 |
| dev-wave-t2273-shard0-local-copy | acceptance-final1.chain.log | 1 | 2026-09-26T13:10:37+09:00 | 0.0 | 2.5 | 2.49 | 0.0 | 2.41 |
| dev-wave-t2273-shard0-local-copy | acceptance-final2.chain.log | 1 | 2026-09-26T13:31:48+09:00 | 0.0 | 3.67 | 2.69 | 0.0 | 3.25 |
| dev-wave-t2344-closure-stage | acceptance-final2.chain.log | 1 | 2026-09-21T00:02:39+09:00 | 1.0 | 4.73 | 5.05 | 1.0 | 4.73 |
| dev-wave-t2344-source-bound-emitters | acceptance-final.chain.log | 1 | 2026-09-21T11:46:59+09:00 | 1.0 | 17.86 | 18.54 | 1.0 | 17.75 |
| dev-wave-t2344-source-bound-emitters | acceptance-final2.chain.log | 1 | 2026-09-21T12:23:28+09:00 | 1.0 | 9.22 | 12.27 | 1.0 | 9.22 |
| dev-wave-t2344-source-bound-emitters | acceptance-final3.chain.log | 1 | 2026-09-21T12:41:57+09:00 | 0.0 | 8.95 | 9.83 | 0.0 | 8.84 |
| dev-wave-t2632-b4-evidence-carrier | acceptance-final.chain.log | 1 | 2026-09-21T22:46:55+09:00 | 1.0 | 3.35 | 2.95 | 1.0 | 3.6 |
| dev-wave-t2795-k2-pair-repair | acceptance-final.chain.log | 1 | 2026-09-21T11:53:49+09:00 | 1.0 | 15.36 | 16.07 | 1.0 | 15.33 |
| dev-wave-t2795-k2-pair-repair | acceptance-final2.chain.log | 1 | 2026-09-21T12:08:27+09:00 | 1.0 | 8.72 | 41.97 | 1.0 | 8.31 |
| dev-wave-t2795-k2-pair-repair | acceptance-final3.chain.log | 1 | 2026-09-21T12:48:17+09:00 | 1.0 | 10.7 | 10.16 | 1.0 | 10.32 |
| dev-wave-t2795-k2-pair-repair | acceptance-final4.chain.log | 1 | 2026-09-21T13:08:52+09:00 | 0.0 | 10.25 | 10.99 | 0.0 | 10.87 |
| dev-wave-t2795-k2-pair-resubmit | acceptance-final.chain.log | 1 | 2026-09-22T11:51:22+09:00 | 0.0 | 2.4 | 2.58 | 0.0 | 2.16 |
| dev-wave-t2797-b5-contrast | acceptance-final.chain.log | 1 | 2026-09-21T04:21:32+09:00 | 1.0 | 3.19 | 3.28 | 1.0 | 2.93 |
| dev-wave-t2797-b5-contrast | acceptance-final2.chain.log | 1 | 2026-09-21T04:40:27+09:00 | 0.0 | 2.41 | 3.66 | 0.0 | 2.39 |
| dev-wave-t2797-b5-contrast | acceptance-final3.chain.log | 1 | 2026-09-21T04:57:50+09:00 | 0.0 | 1.48 | 1.9 | 0.0 | 1.44 |
| dev-wave-t2797-b5-effect-bundle | acceptance-final.chain.log | 1 | 2026-09-22T13:51:50+09:00 | 0.0 | 2.75 | 2.8 | 0.0 | 2.19 |
| dev-wave-t2797-tier0 | acceptance-final.chain.log | 1 | 2026-09-22T00:22:47+09:00 | 0.0 | 1.69 | 2.38 | 0.0 | 1.53 |
| dev-wave-t2797-tier0 | acceptance-final2.chain.log | 1 | 2026-09-22T00:35:26+09:00 | 0.0 | 2.1 | 2.17 | 0.0 | 2.12 |
| dev-wave-t2803-provenance-receipt | acceptance-final3.chain.log | 1 | 2026-09-20T23:45:07+09:00 | 1.0 | 3.81 | 4.61 | 1.0 | 3.53 |
| dev-wave-t2807-b8-effective | acceptance-final.chain.log | 1 | 2026-09-21T10:43:03+09:00 | 1.0 | 15.79 | 17.55 | 1.0 | 16.93 |
| dev-wave-t2807-b8-effective | acceptance-final2.chain.log | 1 | 2026-09-21T11:16:51+09:00 | 0.0 | 17.83 | 16.25 | 1.0 | 17.99 |
| dev-wave-t2810-g1-launch-validation | gate-loop-final.log | 1 | 2026-09-21T03:12:15+09:00 | 1.0 | 2.71 | 3.14 | 1.0 | - |
| dev-wave-t2810-g1-launch-validation | gate-loop-final2.log | 1 | 2026-09-21T03:29:14+09:00 | 1.0 | 2.4 | 3.09 | 1.0 | - |
| dev-wave-t2812-old-series-realignment | gate-loop-final.log | 1 | 2026-09-21T10:28:42+09:00 | 1.0 | 15.81 | 13.76 | 1.0 | - |
| dev-wave-t2814-cleanup-command | gate-loop-final.log | 1 | 2026-09-21T02:46:42+09:00 | 1.0 | 6.93 | 3.92 | 1.0 | - |
| dev-wave-t2814-cleanup-command | gate-loop-final.log | 5 | 2026-09-21T02:50:30+09:00 | 1.0 | 4.14 | 4.01 | 0.0 | - |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final.chain.log | 1 | 2026-09-21T02:59:51+09:00 | 1.0 | 2.53 | 3.66 | 1.0 | 2.42 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final3.chain.log | 1 | 2026-09-21T03:18:33+09:00 | 0.0 | 5.32 | 3.77 | 0.0 | 4.93 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final4.chain.log | 1 | 2026-09-21T03:36:03+09:00 | 1.0 | 3.54 | 4.11 | 1.0 | 3.37 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-ref.chain.log | 1 | 2026-09-21T02:12:08+09:00 | 0.0 | 2.92 | 4.16 | 0.0 | 4.24 |
| dev-wave-t2825-ledger-refresh-ab | acceptance-final.chain.log | 1 | 2026-09-21T13:58:01+09:00 | 1.0 | 3.16 | 3.81 | 1.0 | 3.21 |
| dev-wave-t2825-ledger-refresh-ab | acceptance-final2.chain.log | 1 | 2026-09-21T14:44:22+09:00 | 1.0 | 5.18 | 21.01 | 1.0 | 4.44 |
| dev-wave-t2825-ledger-refresh-ab | acceptance-final3.chain.log | 1 | 2026-09-21T16:13:33+09:00 | 1.0 | 3.91 | 3.25 | 1.0 | 3.91 |
| dev-wave-t2826-resume | acceptance-final.chain.log | 1 | 2026-09-21T21:42:40+09:00 | 0.0 | 5.94 | 5.75 | 0.0 | 6.24 |
| dev-wave-t2826-resume | acceptance-final2.chain.log | 1 | 2026-09-21T21:56:54+09:00 | 1.0 | 4.99 | 5.59 | 1.0 | 4.65 |
| dev-wave-t2826-shard-plugin-modify-timing | acceptance-final.chain.log | 1 | 2026-09-21T15:01:20+09:00 | 1.0 | 6.12 | 5.59 | 1.0 | 6.0 |
| dev-wave-t2830-b5-node-local-lock | acceptance-final.chain.log | 1 | 2026-09-21T15:48:59+09:00 | 1.0 | 4.17 | 3.9 | 1.0 | 4.08 |
| dev-wave-t2830-b5-node-local-lock | acceptance-final2.chain.log | 1 | 2026-09-21T16:24:05+09:00 | 1.0 | 2.83 | 3.36 | 1.0 | 2.53 |
| dev-wave-t2830-b5-node-local-lock | acceptance-final3.chain.log | 1 | 2026-09-21T17:05:19+09:00 | 0.0 | 4.78 | 3.45 | 0.0 | 4.22 |
| dev-wave-t2833-land-eintr-retry | acceptance-final.chain.log | 1 | 2026-09-21T15:21:41+09:00 | 1.0 | 4.03 | 4.01 | 1.0 | 3.51 |
| dev-wave-t2833-land-eintr-retry | acceptance-final2.chain.log | 1 | 2026-09-21T16:11:55+09:00 | 1.0 | 4.27 | 2.82 | 1.0 | 4.96 |
| dev-wave-t2833-land-eintr-retry | acceptance-final3.chain.log | 1 | 2026-09-21T16:54:20+09:00 | 1.0 | 2.81 | 3.56 | 1.0 | 2.7 |
| dev-wave-t2835-land-guard-base | acceptance-final-1.chain.log | 1 | 2026-09-21T14:57:48+09:00 | 1.0 | 4.13 | 5.05 | 1.0 | - |
| dev-wave-t2844-mocc-xp-hook-branch | acceptance-final.chain.log | 1 | 2026-09-21T22:32:30+09:00 | 1.0 | 5.61 | 5.01 | 1.0 | 5.73 |
| dev-wave-t2844-mocc-xp-hook-branch | acceptance-final2.chain.log | 1 | 2026-09-21T23:22:02+09:00 | 1.0 | 4.49 | 3.44 | 1.0 | 4.49 |
| dev-wave-t2844-mocc-xp-hook-branch | acceptance-final3.chain.log | 1 | 2026-09-22T07:43:08+09:00 | 0.0 | 5.28 | 4.12 | 0.0 | 4.53 |
| dev-wave-t2847-corpus-gaps | acceptance-final2.chain.log | 1 | 2026-09-23T10:14:28+09:00 | 1.0 | 5.88 | 5.6 | 1.0 | 6.2 |
| dev-wave-t2847-mutation-run | acceptance-final.chain.log | 1 | 2026-09-23T22:18:24+09:00 | 1.0 | 6.49 | 6.9 | 1.0 | 6.49 |
| dev-wave-t2847-mutation-run | acceptance-final2.chain.log | 1 | 2026-09-23T22:28:05+09:00 | 1.0 | 7.65 | 7.24 | 1.0 | 7.65 |
| dev-wave-t2847-mutation-run | acceptance-final3.chain.log | 1 | 2026-09-23T22:47:36+09:00 | 0.0 | 4.49 | 6.09 | 0.0 | 4.07 |
| dev-wave-t2847-mutation-run | acceptance-final4.chain.log | 1 | 2026-09-23T23:08:44+09:00 | 0.0 | 3.2 | 3.54 | 0.0 | 3.2 |
| dev-wave-t2847-patch-verify | acceptance-final.chain.log | 1 | 2026-09-23T09:09:49+09:00 | 1.0 | 7.93 | 8.2 | 1.0 | 7.65 |
| dev-wave-t2847-patch-verify | acceptance-final2.chain.log | 1 | 2026-09-23T09:32:09+09:00 | 1.0 | 12.04 | 9.65 | 1.0 | 12.44 |
| dev-wave-t2847-sort-nonswo | acceptance-final.chain.log | 1 | 2026-09-23T23:31:46+09:00 | 0.0 | 9.53 | 8.39 | 0.0 | 8.59 |
| dev-wave-t2847-verifier-capacity | acceptance-final.chain.log | 1 | 2026-09-23T10:41:05+09:00 | 1.0 | 5.8 | 7.68 | 1.0 | 5.77 |
| dev-wave-t2847-verifier-detection-design | acceptance-final.chain.log | 1 | 2026-09-22T10:54:03+09:00 | 0.0 | 1.51 | 2.39 | 0.0 | 1.63 |
| dev-wave-t2849-comparison-harness-design | acceptance-final.chain.log | 1 | 2026-09-22T12:22:23+09:00 | 0.0 | 4.07 | 3.83 | 0.0 | 3.37 |
| dev-wave-t2850-trial-prereg | acceptance-final.chain.log | 1 | 2026-09-23T10:25:39+09:00 | 0.0 | 5.39 | 6.21 | 0.0 | 6.26 |
| dev-wave-t2850-trial-prereg | acceptance-final2.chain.log | 1 | 2026-09-23T10:52:52+09:00 | 1.0 | 6.12 | 5.04 | 1.0 | 5.7 |
| dev-wave-t2851-tpcc-prereg | acceptance-final.chain.log | 1 | 2026-09-23T09:24:52+09:00 | 1.0 | 9.39 | 10.1 | 1.0 | 11.26 |
| dev-wave-t2851-transfer-prereg | acceptance-final.chain.log | 1 | 2026-09-22T20:24:35+09:00 | 0.0 | 4.03 | 3.66 | 0.0 | 4.31 |
| dev-wave-t2853-repro-package-estimate | acceptance-final.chain.log | 1 | 2026-09-22T11:07:23+09:00 | 0.0 | 3.92 | 3.8 | 0.0 | 3.19 |
| dev-wave-t2853-repro-package-rest | acceptance-final.chain.log | 1 | 2026-09-23T09:15:07+09:00 | 1.0 | 9.45 | 9.71 | 1.0 | 9.25 |
| dev-wave-t2853-rerun-plan | acceptance-final.chain.log | 1 | 2026-09-23T21:06:11+09:00 | 1.0 | 10.96 | 10.91 | 1.0 | 11.66 |
| dev-wave-t2854-mocc-v3-emitter | acceptance-final.chain.log | 1 | 2026-09-23T10:00:22+09:00 | 0.0 | 7.81 | 8.33 | 0.0 | 7.84 |
| dev-wave-t2854-mocc-v3-emitter | acceptance-final2.chain.log | 1 | 2026-09-23T10:25:40+09:00 | 0.0 | 6.26 | 6.32 | 0.0 | 6.26 |
| dev-wave-t2854-tpcc-ccbench-v3 | acceptance-final.chain.log | 1 | 2026-09-22T21:43:19+09:00 | 1.0 | 1.87 | 3.14 | 1.0 | 1.6 |
| dev-wave-t2854-tpcc-ccbench-v3 | acceptance-final2.chain.log | 1 | 2026-09-22T22:00:02+09:00 | 0.0 | 2.1 | 2.77 | 0.0 | 2.1 |
| dev-wave-t2854-tpcc-verifier-v3 | acceptance-final.chain.log | 1 | 2026-09-22T21:39:10+09:00 | 0.0 | 5.27 | 4.04 | 0.0 | 4.34 |
| dev-wave-t2854-unit5-v3-wiring | acceptance-final.chain.log | 1 | 2026-09-23T22:05:26+09:00 | 0.0 | 7.19 | 6.41 | 0.0 | 7.54 |
| dev-wave-t2854-v3-existence | acceptance-final.chain.log | 1 | 2026-09-23T11:01:13+09:00 | 0.0 | 4.12 | 4.35 | 0.0 | 5.45 |
| dev-wave-t2857-silo-policy-stage-c | acceptance-final.chain.log | 1 | 2026-09-23T00:08:31+09:00 | 0.0 | 1.68 | 2.25 | 0.0 | 1.62 |
| dev-wave-t2858-mocc-xp-pin | gate-loop-final.log | 1 | 2026-09-23T21:53:43+09:00 | 1.0 | 6.67 | 6.6 | 1.0 | - |
| dev-wave-t2860-k2-round4-reflux | acceptance-final.chain.log | 1 | 2026-09-23T08:31:31+09:00 | 1.0 | 10.46 | 9.04 | 0.0 | 16.99 |
| dev-wave-t2860-k2-round4-reflux | acceptance-final2.chain.log | 1 | 2026-09-23T08:49:20+09:00 | 1.0 | 9.87 | 15.1 | 1.0 | 9.23 |
| dev-wave-t2862-comsys-manuscript-revision | acceptance-final.chain.log | 1 | 2026-09-23T08:02:44+09:00 | 0.0 | 14.27 | 24.82 | 0.0 | 14.56 |
| dev-wave-t2864-comsys-refs-sec7 | acceptance-final.chain.log | 1 | 2026-09-26T14:35:22+09:00 | 0.0 | 7.77 | 7.61 | 0.0 | 9.13 |
| dev-wave-t2865-silo-small-compare | acceptance-final.chain.log | 1 | 2026-09-26T10:28:01+09:00 | 0.0 | 3.94 | 4.32 | 0.0 | 4.21 |
| dev-wave-t2865-silo-small-compare | acceptance-final2.chain.log | 1 | 2026-09-26T10:34:10+09:00 | 0.0 | 3.66 | 4.43 | 0.0 | 3.82 |
| dev-wave-tpcc-trace-design | acceptance-final.chain.log | 1 | 2026-09-21T23:01:56+09:00 | 1.0 | 4.26 | 2.85 | 1.0 | 4.83 |
| dev-wave-vldb-direction-revision | acceptance-final.chain.log | 1 | 2026-09-21T22:03:54+09:00 | 1.0 | 6.32 | 6.43 | 1.0 | 6.54 |
| dev-wave-vldb-direction-revision | acceptance-final2.chain.log | 1 | 2026-09-21T22:20:36+09:00 | 1.0 | 4.72 | 5.03 | 1.0 | 5.25 |
| dev-wave-waiter-collect-latency | acceptance-final.chain.log | 1 | 2026-09-21T08:36:12+09:00 | 1.0 | 9.07 | 12.6 | 1.0 | 8.88 |
| dev-wave-waiter-collect-latency | acceptance-final2.chain.log | 1 | 2026-09-21T08:50:46+09:00 | 1.0 | 5.92 | 6.89 | 1.0 | 5.39 |
| dev-wave-wall-decomp | acceptance-final.chain.log | 1 | 2026-09-21T02:28:10+09:00 | 0.0 | 2.44 | 3.43 | 0.0 | 2.38 |
| dev-wave-wave-startup-cost | acceptance-final.chain.log | 1 | 2026-09-21T16:49:29+09:00 | 1.0 | 4.52 | 4.05 | 1.0 | 4.12 |
| dev-wave-wave-startup-cost | acceptance-final2.chain.log | 1 | 2026-09-21T17:16:17+09:00 | 1.0 | 2.63 | 3.28 | 1.0 | 3.11 |
| next-tasks-throwable-only | acceptance-final-1.chain.log | 1 | 2026-09-21T14:33:26+09:00 | 1.0 | 7.2 | 6.75 | 1.0 | - |
| rulings-all-20260921 | acceptance-final-1.chain.log | 1 | 2026-09-21T01:07:14+09:00 | 0.0 | 4.18 | 5.26 | 0.0 | - |
| rulings-all-20260921b | acceptance-final-1.chain.log | 1 | 2026-09-21T08:34:55+09:00 | 0.0 | 15.49 | 14.52 | 0.0 | - |
| rulings-all-20260921c | acceptance-final-1.chain.log | 1 | 2026-09-21T13:46:18+09:00 | 0.0 | 3.59 | 5.37 | 0.0 | - |
| rulings-all-20260921c | acceptance-final-2.chain.log | 1 | 2026-09-21T14:15:19+09:00 | 1.0 | 13.47 | 9.85 | 1.0 | - |
| rulings-all-20260921d | acceptance-final-2.chain.log | 1 | 2026-09-21T21:54:46+09:00 | 0.0 | 5.28 | 5.97 | 0.0 | - |
| rulings-all-20260921d | acceptance-final-3.chain.log | 1 | 2026-09-21T22:05:33+09:00 | 1.0 | 6.61 | 6.53 | 1.0 | - |
| rulings-all-20260922a | acceptance-final-1.chain.log | 1 | 2026-09-22T09:15:43+09:00 | 0.0 | 20.55 | 43.76 | 0.0 | - |
| rulings-all-20260923a | acceptance-final-1.chain.log | 1 | 2026-09-23T09:00:51+09:00 | 1.0 | 6.71 | 9.12 | 1.0 | - |
| rulings-all-20260923a | acceptance-final-2.chain.log | 1 | 2026-09-23T09:45:30+09:00 | 1.0 | 7.67 | 8.2 | 1.0 | - |
| rulings-all-20260923b | acceptance-final-1.chain.log | 1 | 2026-09-23T20:12:29+09:00 | 0.0 | 10.12 | 16.96 | 0.0 | - |
| rulings-all-20260923c | acceptance-final-1.chain.log | 1 | 2026-09-23T21:20:48+09:00 | 1.0 | 6.37 | 6.88 | 1.0 | - |
| rulings-all-20260923c | acceptance-final-2.chain.log | 1 | 2026-09-23T22:06:04+09:00 | 1.0 | 7.02 | 6.46 | 1.0 | - |
| t2851-transfer-runner | acceptance-final.chain.log | 1 | 2026-09-26T11:02:25+09:00 | 0.0 | 2.99 | 2.94 | 0.0 | 2.93 |
| t2851-transfer-runner | acceptance-final2.chain.log | 1 | 2026-09-26T11:42:19+09:00 | 0.0 | 1.3 | 2.33 | 0.0 | 1.29 |

## 同時待ち・同時 GO

全 since 対象の観測区間で他 wave を重複排除。leaders は走行側観測であり同時待ち数を補正しない。log の無い待ち手は欠測。

走行区間の数: 門番 log のある dir 135 / 無い dir 3

走行数は全走査対象 dir の since 日付以降に始まった started→finished を照合し、started ≤ tick < end の他 wave 数。finished 欠落時は対応 GO 後の rc、それも無ければ until、until 無指定なら同 dir の最終観測時刻 / log mtime (門番 log も無ければ started) で打切り (推定)。until より後の finished は until で打切り。GO の無い censored の GO 直前値は欠測。leaders_minus_runs_pre_go は記録 leaders − 走行数で、偽 leader 疑いの上限であり断定ではない。

| 母集合 | GO 直前同時待ち 値:件数 | 区間最大同時待ち 値:件数 (打切り含む) | 同時 GO ±120秒 値:件数 | 走行数 (GO 直前) 値:件数 |
| --- | --- | --- | --- | --- |
| recent | 0: 19; 1: 7; 2: 4; 3: 4; 4: 1 | 0: 15; 1: 6; 2: 6; 3: 4; 4: 5 | 0: 28; 1: 4; 2: 3 | 0: 20; 1: 15 |
| since | 0: 76; 1: 26; 2: 24; 3: 11; 4: 2 | 0: 65; 1: 23; 2: 31; 3: 15; 4: 10 | 0: 107; 1: 26; 2: 6 | 0: 63; 1: 76 |

| wave | file | segment | 最大 他 wave | GO 直前 tick | GO 時点 | GO ±120秒 | 走行 (GO 直前) | leaders − 走行 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cleanup-0921c-ledger-handover | acceptance-final-1.chain.log | 1 | 1 | 1 | 1 | 1 | 0 | 0.0 |
| dev-wave-acceptance-resubmit-causes | acceptance-final.chain.log | 1 | 4 | 2 | 1 | 2 | 1 | 0.0 |
| dev-wave-branch-residue-cleanup | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-codex-model-sol | acceptance-final.chain.log | 1 | 4 | 1 | 1 | 1 | 0 | 0.0 |
| dev-wave-codex-selfrun-precheck | acceptance-L1-1.chain.log | 1 | 2 | 2 | 2 | 1 | 1 | 0.0 |
| dev-wave-codex-selfrun-precheck | acceptance-L1-1.chain.log | 5 | 2 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-codex-selfrun-precheck | acceptance-L2-1.chain.log | 1 | 2 | 1 | 1 | 0 | 0 | 1.0 |
| dev-wave-codex-selfrun-precheck | acceptance-L2-2.chain.log | 1 | 2 | 2 | 2 | 1 | 0 | 0.0 |
| dev-wave-codex-selfrun-precheck | acceptance-final.chain.log | 1 | 4 | 2 | 2 | 2 | 1 | 0.0 |
| dev-wave-codex-selfrun-precheck | acceptance-final2.chain.log | 1 | 3 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-comsys2026-manuscript | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-dwm08-selfrun-probe | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-focus-run-count-diagnosis | acceptance-final.chain.log | 1 | 4 | 3 | 3 | 2 | 0 | 0.0 |
| dev-wave-land-roundtrip-diagnosis | acceptance-final.chain.log | 1 | 4 | 3 | 3 | 1 | 0 | 0.0 |
| dev-wave-lease-gate-wait-diagnosis | acceptance-final.chain.log | 1 | 2 | 2 | 1 | 1 | 1 | 0.0 |
| dev-wave-login-check-wall | acceptance-final.chain.log | 1 | 2 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-login-check-wall | acceptance-final2.chain.log | 1 | 2 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-mocc-xp-pin-candidate | acceptance-final.chain.log | 1 | 2 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-mocc-xp-pin-candidate | acceptance-final.chain.log | 5 | 3 | 3 | 3 | 0 | 1 | 0.0 |
| dev-wave-mocc-xp-pin-candidate | acceptance-final2.chain.log | 1 | 2 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-paper-abstract-conclusion-ja | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-paper-b8-pass-ja | acceptance-final.chain.log | 1 | 3 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-paper-methods-ja-b8 | acceptance-final.chain.log | 1 | 1 | 1 | 1 | 1 | 1 | 0.0 |
| dev-wave-paper-methods-ja-b8 | acceptance-final2.chain.log | 1 | 2 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-paper-methods-ja-b8 | acceptance-final3.chain.log | 1 | 2 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-paper-methods-ja-b8 | acceptance-final4.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-paper-story-2026-09-21c | acceptance-final1.chain.log | 1 | 2 | 1 | 0 | 1 | 1 | 0.0 |
| dev-wave-paper-story-20260921 | acceptance-final.chain.log | 1 | 1 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-paper-story-20260923 | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-paper-story-20260923 | acceptance-final2.chain.log | 1 | 1 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-paper-story-20260923 | acceptance-final3.chain.log | 1 | 1 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-paper-story-20260923 | acceptance-final4.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-provenance-cold-diag | acceptance-final.chain.log | 1 | 3 | 2 | 2 | 1 | 1 | 0.0 |
| dev-wave-r29-items4-9-diagnosis | acceptance-final.chain.log | 1 | 2 | 1 | 1 | 1 | 1 | 0.0 |
| dev-wave-silo-function-synthesis-space | acceptance-final.chain.log | 1 | 2 | 2 | 1 | 1 | 1 | 0.0 |
| dev-wave-t1851-leftover-audit | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2273-acceptance-bottleneck-diag | acceptance-final.chain.log | 1 | 3 | 3 | 1 | 2 | 0 | 0.0 |
| dev-wave-t2273-acceptance-bottleneck-diag | acceptance-final.chain.log | 5 | 2 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-t2273-acceptance-bottleneck-diag | acceptance-final2.chain.log | 1 | 1 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2273-shard0-local-copy | acceptance-final1.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2273-shard0-local-copy | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2344-closure-stage | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-t2344-source-bound-emitters | acceptance-final.chain.log | 1 | 2 | 1 | 1 | 0 | 0 | 1.0 |
| dev-wave-t2344-source-bound-emitters | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2344-source-bound-emitters | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2632-b4-evidence-carrier | acceptance-final.chain.log | 1 | 2 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-t2795-k2-pair-repair | acceptance-final.chain.log | 1 | 1 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2795-k2-pair-repair | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2795-k2-pair-repair | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2795-k2-pair-repair | acceptance-final4.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2795-k2-pair-resubmit | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2797-b5-contrast | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2797-b5-contrast | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2797-b5-contrast | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2797-b5-effect-bundle | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2797-tier0 | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2797-tier0 | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2803-provenance-receipt | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-t2807-b8-effective | acceptance-final.chain.log | 1 | 2 | 2 | 2 | 0 | 0 | 1.0 |
| dev-wave-t2807-b8-effective | acceptance-final2.chain.log | 1 | 2 | 2 | 1 | 1 | 0 | 0.0 |
| dev-wave-t2810-g1-launch-validation | gate-loop-final.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2810-g1-launch-validation | gate-loop-final2.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2812-old-series-realignment | gate-loop-final.log | 1 | 2 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-t2814-cleanup-command | gate-loop-final.log | 1 | 1 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2814-cleanup-command | gate-loop-final.log | 5 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final2.chain.aborted-before-submit.log | 1 | 1 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final4.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-ref.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2825-ledger-refresh-ab | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2825-ledger-refresh-ab | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2825-ledger-refresh-ab | acceptance-final3.chain.log | 1 | 3 | 1 | 1 | 1 | 1 | 0.0 |
| dev-wave-t2826-resume | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2826-resume | acceptance-final2.chain.log | 1 | 1 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2826-shard-plugin-modify-timing | acceptance-final.chain.log | 1 | 2 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-t2830-b5-node-local-lock | acceptance-final.chain.log | 1 | 3 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-t2830-b5-node-local-lock | acceptance-final2.chain.log | 1 | 1 | 1 | 1 | 1 | 1 | 0.0 |
| dev-wave-t2830-b5-node-local-lock | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2833-land-eintr-retry | acceptance-final.chain.log | 1 | 3 | 3 | 3 | 0 | 1 | 0.0 |
| dev-wave-t2833-land-eintr-retry | acceptance-final2.chain.log | 1 | 2 | 2 | 2 | 1 | 1 | 0.0 |
| dev-wave-t2833-land-eintr-retry | acceptance-final3.chain.log | 1 | 2 | 1 | 1 | 1 | 1 | 0.0 |
| dev-wave-t2835-land-guard-base | acceptance-final-1.chain.log | 1 | 1 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-t2844-mocc-xp-hook-branch | acceptance-final.chain.log | 1 | 2 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-t2844-mocc-xp-hook-branch | acceptance-final2.chain.log | 1 | 2 | 2 | 2 | 1 | 1 | 0.0 |
| dev-wave-t2844-mocc-xp-hook-branch | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2847-corpus-gaps | acceptance-final.chain.log | 1 | 4 | unknown | unknown | unknown | unknown | unknown |
| dev-wave-t2847-corpus-gaps | acceptance-final2.chain.log | 1 | 3 | 3 | 3 | 0 | 1 | 0.0 |
| dev-wave-t2847-mutation-run | acceptance-final.chain.log | 1 | 2 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2847-mutation-run | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2847-mutation-run | acceptance-final3.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2847-mutation-run | acceptance-final4.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2847-patch-verify | acceptance-final.chain.log | 1 | 1 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2847-patch-verify | acceptance-final2.chain.log | 1 | 3 | 3 | 3 | 0 | 1 | 0.0 |
| dev-wave-t2847-sort-nonswo | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2847-verifier-capacity | acceptance-final.chain.log | 1 | 2 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-t2847-verifier-detection-design | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2849-comparison-harness-design | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2850-trial-prereg | acceptance-final.chain.log | 1 | 4 | 3 | 3 | 2 | 0 | 0.0 |
| dev-wave-t2850-trial-prereg | acceptance-final2.chain.log | 1 | 2 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-t2851-tpcc-prereg | acceptance-final.chain.log | 1 | 3 | 3 | 3 | 0 | 1 | 0.0 |
| dev-wave-t2851-transfer-prereg | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2853-repro-package-estimate | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2853-repro-package-rest | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2853-rerun-plan | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2854-mocc-v3-emitter | acceptance-final.chain.log | 1 | 4 | 2 | 2 | 1 | 0 | 0.0 |
| dev-wave-t2854-mocc-v3-emitter | acceptance-final2.chain.log | 1 | 3 | 3 | 2 | 2 | 0 | 0.0 |
| dev-wave-t2854-tpcc-ccbench-v3 | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| dev-wave-t2854-tpcc-ccbench-v3 | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2854-tpcc-verifier-v3 | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2854-unit5-v3-wiring | acceptance-final.chain.log | 1 | 2 | 2 | 2 | 1 | 0 | 0.0 |
| dev-wave-t2854-v3-existence | acceptance-final.chain.log | 1 | 3 | 0 | 1 | 0 | 0 | 0.0 |
| dev-wave-t2857-silo-policy-stage-c | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2858-mocc-xp-pin | gate-loop-final.log | 1 | 1 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-t2860-k2-round4-reflux | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| dev-wave-t2860-k2-round4-reflux | acceptance-final2.chain.log | 1 | 1 | 1 | 1 | 0 | 0 | 1.0 |
| dev-wave-t2862-comsys-manuscript-revision | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2864-comsys-refs-sec7 | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2865-silo-small-compare | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-t2865-silo-small-compare | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-tpcc-trace-design | acceptance-final.chain.log | 1 | 1 | 1 | 1 | 0 | 1 | 0.0 |
| dev-wave-vldb-direction-revision | acceptance-final.chain.log | 1 | 1 | 1 | 1 | 1 | 1 | 0.0 |
| dev-wave-vldb-direction-revision | acceptance-final2.chain.log | 1 | 1 | 0 | 0 | 1 | 1 | 0.0 |
| dev-wave-waiter-collect-latency | acceptance-final.chain.log | 1 | 3 | 2 | 2 | 1 | 1 | 0.0 |
| dev-wave-waiter-collect-latency | acceptance-final2.chain.log | 1 | 4 | 4 | 4 | 0 | 1 | 0.0 |
| dev-wave-wall-decomp | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| dev-wave-wave-startup-cost | acceptance-final.chain.log | 1 | 2 | 2 | 2 | 0 | 1 | 0.0 |
| dev-wave-wave-startup-cost | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 |
| next-tasks-throwable-only | acceptance-final-1.chain.log | 1 | 1 | 0 | 0 | 0 | 1 | 0.0 |
| rulings-all-20260921 | acceptance-final-1.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| rulings-all-20260921b | acceptance-final-1.chain.log | 1 | 3 | 3 | 3 | 1 | 0 | 0.0 |
| rulings-all-20260921c | acceptance-final-1.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| rulings-all-20260921c | acceptance-final-2.chain.log | 1 | 1 | 1 | 1 | 1 | 1 | 0.0 |
| rulings-all-20260921d | acceptance-final-1.chain.log | 1 | 0 | unknown | unknown | unknown | unknown | unknown |
| rulings-all-20260921d | acceptance-final-2.chain.log | 1 | 0 | 0 | 1 | 0 | 0 | 0.0 |
| rulings-all-20260921d | acceptance-final-3.chain.log | 1 | 1 | 0 | 0 | 1 | 1 | 0.0 |
| rulings-all-20260922a | acceptance-final-1.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| rulings-all-20260923a | acceptance-final-1.chain.log | 1 | 1 | 1 | 1 | 0 | 1 | 0.0 |
| rulings-all-20260923a | acceptance-final-2.chain.log | 1 | 4 | 4 | 4 | 0 | 1 | 0.0 |
| rulings-all-20260923b | acceptance-final-1.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| rulings-all-20260923c | acceptance-final-1.chain.log | 1 | 1 | 1 | 1 | 0 | 0 | 1.0 |
| rulings-all-20260923c | acceptance-final-2.chain.log | 1 | 2 | 1 | 1 | 1 | 1 | 0.0 |
| t2851-transfer-runner | acceptance-final.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| t2851-transfer-runner | acceptance-final2.chain.log | 1 | 0 | 0 | 0 | 0 | 0 | 0.0 |

## 飢餓候補と長時間待ち

長時間待ち ≥1800秒、飢餓候補 = 長時間待ちかつ同一区間の拒否 ≥2。事例探索条件であり一般定義ではない。

| 母集合 | wave | file | segment | kind | 秒 | 拒否 | 飢餓候補 | 同時待ち最大 | 走行最大 | leaders_grep | 閉門 leaders 起因 tick / 全 tick |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent | dev-wave-t2847-corpus-gaps | acceptance-final.chain.log | 1 | censored | 1826.0 | 0 | False | 4 | 2 | substring | 13 / 16 |
| recent | dev-wave-t2850-trial-prereg | acceptance-final.chain.log | 1 | observed-wait | 3681.0 | 1 | False | 4 | 2 | argv-anchored | 23 / 31 |
| recent | dev-wave-t2854-v3-existence | acceptance-final.chain.log | 1 | observed-wait | 3195.0 | 1 | False | 3 | 2 | substring | 19 / 27 |
| since | dev-wave-land-roundtrip-diagnosis | acceptance-final.chain.log | 1 | observed-wait | 3145.0 | 1 | False | 4 | 3 | substring | 22 / 27 |
| since | dev-wave-lease-gate-wait-diagnosis | acceptance-final.chain.log | 1 | observed-wait | 3874.0 | 1 | False | 2 | 3 | argv-anchored | 27 / 33 |
| since | dev-wave-silo-function-synthesis-space | acceptance-final.chain.log | 1 | observed-wait | 2057.0 | 1 | False | 2 | 2 | substring | 13 / 18 |
| since | dev-wave-t2344-source-bound-emitters | acceptance-final.chain.log | 1 | observed-wait | 1875.0 | 0 | False | 2 | 2 | substring | 12 / 16 |
| since | dev-wave-t2812-old-series-realignment | gate-loop-final.log | 1 | observed-wait | 2902.0 | 1 | False | 2 | 3 | substring | 20 / 25 |
| since | dev-wave-t2825-ledger-refresh-ab | acceptance-final3.chain.log | 1 | observed-wait | 4604.0 | 1 | False | 3 | 2 | argv-anchored | 29 / 39 |
| since | dev-wave-t2830-b5-node-local-lock | acceptance-final.chain.log | 1 | observed-wait | 2874.0 | 2 | True | 3 | 2 | substring | 14 / 24 |
| since | dev-wave-t2847-corpus-gaps | acceptance-final.chain.log | 1 | censored | 1826.0 | 0 | False | 4 | 2 | substring | 13 / 16 |
| since | dev-wave-t2850-trial-prereg | acceptance-final.chain.log | 1 | observed-wait | 3681.0 | 1 | False | 4 | 2 | argv-anchored | 23 / 31 |
| since | dev-wave-t2854-v3-existence | acceptance-final.chain.log | 1 | observed-wait | 3195.0 | 1 | False | 3 | 2 | substring | 19 / 27 |
| since | dev-wave-tpcc-trace-design | acceptance-final.chain.log | 1 | observed-wait | 1840.0 | 0 | False | 1 | 2 | argv-anchored | 11 / 16 |
| since-2026-09-19 | dev-wave-land-roundtrip-diagnosis | acceptance-final.chain.log | 1 | observed-wait | 3145.0 | 1 | False | 4 | 3 | substring | 22 / 27 |
| since-2026-09-19 | dev-wave-lease-gate-wait-diagnosis | acceptance-final.chain.log | 1 | observed-wait | 3874.0 | 1 | False | 2 | 3 | argv-anchored | 27 / 33 |
| since-2026-09-19 | dev-wave-silo-function-synthesis-space | acceptance-final.chain.log | 1 | observed-wait | 2057.0 | 1 | False | 2 | 2 | substring | 13 / 18 |
| since-2026-09-19 | dev-wave-t2344-source-bound-emitters | acceptance-final.chain.log | 1 | observed-wait | 1875.0 | 0 | False | 2 | 2 | substring | 12 / 16 |
| since-2026-09-19 | dev-wave-t2812-old-series-realignment | gate-loop-final.log | 1 | observed-wait | 2902.0 | 1 | False | 2 | 3 | substring | 20 / 25 |
| since-2026-09-19 | dev-wave-t2825-ledger-refresh-ab | acceptance-final3.chain.log | 1 | observed-wait | 4604.0 | 1 | False | 3 | 2 | argv-anchored | 29 / 39 |
| since-2026-09-19 | dev-wave-t2830-b5-node-local-lock | acceptance-final.chain.log | 1 | observed-wait | 2874.0 | 2 | True | 3 | 2 | substring | 14 / 24 |
| since-2026-09-19 | dev-wave-t2847-corpus-gaps | acceptance-final.chain.log | 1 | censored | 1826.0 | 0 | False | 4 | 2 | substring | 13 / 16 |
| since-2026-09-19 | dev-wave-t2850-trial-prereg | acceptance-final.chain.log | 1 | observed-wait | 3681.0 | 1 | False | 4 | 2 | argv-anchored | 23 / 31 |
| since-2026-09-19 | dev-wave-t2854-v3-existence | acceptance-final.chain.log | 1 | observed-wait | 3195.0 | 1 | False | 3 | 2 | substring | 19 / 27 |
| since-2026-09-19 | dev-wave-tpcc-trace-design | acceptance-final.chain.log | 1 | observed-wait | 1840.0 | 0 | False | 1 | 2 | argv-anchored | 11 / 16 |

| 母集合 | 長時間待ち n | 飢餓候補 n | うち censored n (飢餓候補) | censored n (長時間待ち) |
| --- | --- | --- | --- | --- |
| recent | 3 | 0 | 0 | 1 |
| since | 11 | 1 | 0 | 1 |
| since-2026-09-19 | 11 | 1 | 0 | 1 |

## 時間帯

| 母集合 | 開始 JST 時 | observed 分布 秒 | 打切り |
| --- | --- | --- | --- |
| recent | 8 | {"max": 781.0, "median": 781.0, "min": 781.0, "n": 1, "p90": 781.0, "sum": 781.0} | 0 |
| recent | 9 | {"max": 3681.0, "median": 1520.5, "min": 1247.0, "n": 4, "p90": 3681.0, "sum": 7969.0} | 1 |
| recent | 10 | {"max": 3195.0, "median": 424.0, "min": 147.0, "n": 10, "p90": 1472.0, "sum": 8329.0} | 0 |
| recent | 11 | {"max": 184.0, "median": 167.0, "min": 150.0, "n": 2, "p90": 184.0, "sum": 334.0} | 0 |
| recent | 13 | {"max": 172.0, "median": 164.0, "min": 156.0, "n": 2, "p90": 172.0, "sum": 328.0} | 0 |
| recent | 14 | {"max": 167.0, "median": 167.0, "min": 167.0, "n": 1, "p90": 167.0, "sum": 167.0} | 0 |
| recent | 20 | {"max": 1232.0, "median": 136.0, "min": 131.0, "n": 3, "p90": 1232.0, "sum": 1499.0} | 0 |
| recent | 21 | {"max": 1247.0, "median": 750.0, "min": 351.0, "n": 7, "p90": 1247.0, "sum": 5060.0} | 0 |
| recent | 22 | {"max": 261.0, "median": 168.0, "min": 149.0, "n": 3, "p90": 261.0, "sum": 578.0} | 0 |
| recent | 23 | {"max": 141.0, "median": 134.5, "min": 128.0, "n": 2, "p90": 141.0, "sum": 269.0} | 0 |
| since | 0 | {"max": 173.0, "median": 148.5, "min": 108.0, "n": 4, "p90": 173.0, "sum": 578.0} | 0 |
| since | 1 | {"max": 143.0, "median": 141.5, "min": 140.0, "n": 2, "p90": 143.0, "sum": 283.0} | 0 |
| since | 2 | {"max": 745.0, "median": 154.0, "min": 122.0, "n": 6, "p90": 745.0, "sum": 1497.0} | 0 |
| since | 3 | {"max": 353.0, "median": 204.5, "min": 153.0, "n": 4, "p90": 353.0, "sum": 915.0} | 1 |
| since | 4 | {"max": 141.0, "median": 137.0, "min": 122.0, "n": 4, "p90": 141.0, "sum": 537.0} | 0 |
| since | 7 | {"max": 174.0, "median": 164.0, "min": 154.0, "n": 2, "p90": 174.0, "sum": 328.0} | 0 |
| since | 8 | {"max": 3145.0, "median": 396.0, "min": 117.0, "n": 12, "p90": 1688.0, "sum": 9922.0} | 0 |
| since | 9 | {"max": 3874.0, "median": 802.0, "min": 152.0, "n": 14, "p90": 3681.0, "sum": 17965.0} | 1 |
| since | 10 | {"max": 3195.0, "median": 591.0, "min": 142.0, "n": 15, "p90": 1732.0, "sum": 12399.0} | 1 |
| since | 11 | {"max": 1875.0, "median": 184.0, "min": 119.0, "n": 9, "p90": 1875.0, "sum": 5633.0} | 0 |
| since | 12 | {"max": 156.0, "median": 138.0, "min": 105.0, "n": 5, "p90": 156.0, "sum": 658.0} | 0 |
| since | 13 | {"max": 172.0, "median": 146.0, "min": 110.0, "n": 6, "p90": 172.0, "sum": 866.0} | 0 |
| since | 14 | {"max": 4604.0, "median": 407.5, "min": 120.0, "n": 8, "p90": 4604.0, "sum": 7561.0} | 0 |
| since | 15 | {"max": 2874.0, "median": 608.0, "min": 142.0, "n": 7, "p90": 2874.0, "sum": 6490.0} | 0 |
| since | 16 | {"max": 1344.0, "median": 923.0, "min": 264.0, "n": 5, "p90": 1344.0, "sum": 3823.0} | 0 |
| since | 17 | {"max": 230.0, "median": 187.5, "min": 145.0, "n": 2, "p90": 230.0, "sum": 375.0} | 0 |
| since | 20 | {"max": 1232.0, "median": 142.5, "min": 131.0, "n": 4, "p90": 1232.0, "sum": 1648.0} | 0 |
| since | 21 | {"max": 1247.0, "median": 351.0, "min": 119.0, "n": 13, "p90": 813.0, "sum": 5902.0} | 1 |
| since | 22 | {"max": 2057.0, "median": 276.0, "min": 137.0, "n": 12, "p90": 1840.0, "sum": 6728.0} | 0 |
| since | 23 | {"max": 837.0, "median": 141.0, "min": 128.0, "n": 5, "p90": 837.0, "sum": 1641.0} | 1 |

n=0 の時間帯は省略。n は observed-wait 数。打切りのみの時間帯も省略し、打切り総数は区間分布に保持。

## 条件変種

script は現存版からの読取りであり過去版の証明ではない。grep 差だけでは偽陽性と断定しない。

| wave | file | maxl (出所) | maxload (出所) | maxpigz (出所) | leaders_grep | recount_scope | streak | gate.conf | 照合可否 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cleanup-0921c-ledger-handover | acceptance-final-1.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-acceptance-resubmit-causes | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-branch-residue-cleanup | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-codex-model-sol | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-codex-selfrun-precheck | acceptance-L1-1.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-codex-selfrun-precheck | acceptance-L2-1.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-codex-selfrun-precheck | acceptance-L2-2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-codex-selfrun-precheck | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-codex-selfrun-precheck | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-comsys2026-manuscript | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-dwm08-selfrun-probe | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-focus-run-count-diagnosis | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-land-roundtrip-diagnosis | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-lease-gate-wait-diagnosis | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-login-check-wall | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-login-check-wall | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-mocc-xp-pin-candidate | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-mocc-xp-pin-candidate | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-abstract-conclusion-ja | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-b8-pass-ja | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-methods-ja-b8 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-methods-ja-b8 | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-methods-ja-b8 | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-paper-methods-ja-b8 | acceptance-final4.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-2026-09-21c | acceptance-final1.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260921 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260923 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260923 | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260923 | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-paper-story-20260923 | acceptance-final4.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-provenance-cold-diag | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-r29-items4-9-diagnosis | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-silo-function-synthesis-space | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t1851-leftover-audit | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2273-acceptance-bottleneck-diag | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2273-acceptance-bottleneck-diag | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2273-shard0-local-copy | acceptance-final1.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2273-shard0-local-copy | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2344-closure-stage | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2344-source-bound-emitters | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2344-source-bound-emitters | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2344-source-bound-emitters | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2632-b4-evidence-carrier | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2795-k2-pair-repair | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2795-k2-pair-repair | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2795-k2-pair-repair | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2795-k2-pair-repair | acceptance-final4.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2795-k2-pair-resubmit | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2797-b5-contrast | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2797-b5-contrast | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2797-b5-contrast | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2797-b5-effect-bundle | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2797-tier0 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2797-tier0 | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2803-provenance-receipt | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-t2807-b8-effective | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2807-b8-effective | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2810-g1-launch-validation | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2810-g1-launch-validation | gate-loop-final2.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2812-old-series-realignment | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2814-cleanup-command | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final2.chain.aborted-before-submit.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-final4.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2817-acceptance-bottleneck-3 | acceptance-ref.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2825-ledger-refresh-ab | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2825-ledger-refresh-ab | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2825-ledger-refresh-ab | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2826-resume | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2826-resume | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2826-shard-plugin-modify-timing | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | 2.0 (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2830-b5-node-local-lock | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2830-b5-node-local-lock | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2830-b5-node-local-lock | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2833-land-eintr-retry | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2833-land-eintr-retry | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2833-land-eintr-retry | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2835-land-guard-base | acceptance-final-1.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2844-mocc-xp-hook-branch | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2844-mocc-xp-hook-branch | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2844-mocc-xp-hook-branch | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2847-corpus-gaps | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-t2847-corpus-gaps | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2847-mutation-run | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2847-mutation-run | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2847-mutation-run | acceptance-final3.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2847-mutation-run | acceptance-final4.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2847-patch-verify | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2847-patch-verify | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2847-sort-nonswo | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2847-verifier-capacity | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2847-verifier-detection-design | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2849-comparison-harness-design | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2850-trial-prereg | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | unavailable |
| dev-wave-t2850-trial-prereg | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2851-tpcc-prereg | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2851-transfer-prereg | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2853-repro-package-estimate | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2853-repro-package-rest | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2853-rerun-plan | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2854-mocc-v3-emitter | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2854-mocc-v3-emitter | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2854-tpcc-ccbench-v3 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2854-tpcc-ccbench-v3 | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2854-tpcc-verifier-v3 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2854-unit5-v3-wiring | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2854-v3-existence | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2857-silo-policy-stage-c | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2858-mocc-xp-pin | gate-loop-final.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2860-k2-round4-reflux | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2860-k2-round4-reflux | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2862-comsys-manuscript-revision | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2864-comsys-refs-sec7 | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | partial (started 欠測 / 終点推定) |
| dev-wave-t2865-silo-small-compare | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-t2865-silo-small-compare | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-tpcc-trace-design | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-vldb-direction-revision | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-vldb-direction-revision | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-waiter-collect-latency | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-waiter-collect-latency | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | argv-anchored (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-wall-decomp | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-wave-startup-cost | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| dev-wave-wave-startup-cost | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| next-tasks-throwable-only | acceptance-final-1.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260921 | acceptance-final-1.chain.log | 1.0 (script) | 60.0 (script) | unknown (unknown) | substring (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260921b | acceptance-final-1.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260921c | acceptance-final-1.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260921c | acceptance-final-2.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260921d | acceptance-final-1.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | unavailable |
| rulings-all-20260921d | acceptance-final-2.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260921d | acceptance-final-3.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260922a | acceptance-final-1.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260923a | acceptance-final-1.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260923a | acceptance-final-2.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260923b | acceptance-final-1.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260923c | acceptance-final-1.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| rulings-all-20260923c | acceptance-final-2.chain.log | unknown (unknown) | 60.0 (script) | unknown (unknown) | argv-anchored (script) | leaders-only (script) | 2.0 (script) | False (filesystem) | available |
| t2851-transfer-runner | acceptance-final.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |
| t2851-transfer-runner | acceptance-final2.chain.log | 1.0 (log) | 60.0 (log) | no pigz condition (log) | substring (script) | leaders+load (script) | 2.0 (script) | False (filesystem) | available |

## sensitivity (仮定付き参考模型、効果見積りではない)

連続2 tickと直後の記録 recount (無ければ直前 tick の leaders (推定))。b0 は各 tick の実条件 (log/script の maxl・maxload) を同じ模型へ適用した候補 tick。差は代替候補 tick − b0 秒、負なら早く開いたであろう。

実 GO − b0 は jitter + recount の実費等を含む模型と実の差として別掲。pigz、他 wave の応答、jitter・位相・FIFO の効果は模型に含めない。基準不明・成立機会なしは差の分布から除外。

| 母集合 | 条件 | n | min | 中央値 | p90 | 最大 | 合計 (秒) | 基準不明・成立機会なし |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent | 実条件 = 模型基準 | 30 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 5 |
| recent | maxl=1,maxload=60 | 30 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 5 |
| recent | maxl=1,maxload=80 | 30 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 5 |
| recent | maxl=2,maxload=60 | 30 | -3552.0 | -175.0 | 0.0 | 0.0 | -16908.0 | 5 |
| recent | maxl=2,maxload=80 | 30 | -3552.0 | -175.0 | 0.0 | 0.0 | -16908.0 | 5 |
| recent | maxl=3,maxload=60 | 30 | -3552.0 | -175.0 | 0.0 | 0.0 | -16908.0 | 5 |
| recent | maxl=3,maxload=80 | 30 | -3552.0 | -175.0 | 0.0 | 0.0 | -16908.0 | 5 |
| recent | 実 GO − b0 | 30 | 0.0 | 30.5 | 42.0 | 45.0 | 780.0 | 5 |
| since | 実条件 = 模型基準 | 125 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 14 |
| since | maxl=1,maxload=60 | 125 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 14 |
| since | maxl=1,maxload=80 | 125 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 14 |
| since | maxl=2,maxload=60 | 125 | -4461.0 | 0.0 | 0.0 | 0.0 | -56092.0 | 14 |
| since | maxl=2,maxload=80 | 125 | -4461.0 | 0.0 | 0.0 | 0.0 | -56092.0 | 14 |
| since | maxl=3,maxload=60 | 125 | -4461.0 | 0.0 | 0.0 | 0.0 | -57442.0 | 14 |
| since | maxl=3,maxload=80 | 125 | -4461.0 | 0.0 | 0.0 | 0.0 | -57442.0 | 14 |
| since | 実 GO − b0 | 125 | 0.0 | 23.0 | 43.0 | 2143.0 | 6079.0 | 14 |

感度分析の寄与上位: 差 (代替 − b0) が負の区間を差の小さい順。同差は wave・file・segment 順。maxl=2,maxload=60 は各母集合で最大15行、maxl=1,maxload=80 は最大10行。

| 母集合 | 条件 | wave | file | segment | observed 秒 | 差 (代替 − b0) 秒 | GO 直前 leaders | GO 直前走行数 | leaders_grep |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent | maxl=2,maxload=60 | dev-wave-t2850-trial-prereg | acceptance-final.chain.log | 1 | 3681.0 | -3552.0 | 0.0 | 0 | argv-anchored |
| recent | maxl=2,maxload=60 | dev-wave-t2854-v3-existence | acceptance-final.chain.log | 1 | 3195.0 | -3061.0 | 0.0 | 0 | substring |
| recent | maxl=2,maxload=60 | dev-wave-t2850-trial-prereg | acceptance-final2.chain.log | 1 | 1472.0 | -1326.0 | 1.0 | 1 | argv-anchored |
| recent | maxl=2,maxload=60 | dev-wave-t2273-acceptance-bottleneck-diag | acceptance-final.chain.log | 1 | 1384.0 | -1246.0 | 0.0 | 0 | argv-anchored |
| recent | maxl=2,maxload=60 | dev-wave-t2847-mutation-run | acceptance-final.chain.log | 1 | 1247.0 | -1129.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-codex-model-sol | acceptance-final.chain.log | 1 | 1247.0 | -1122.0 | 0.0 | 0 | substring |
| recent | maxl=2,maxload=60 | dev-wave-t2854-mocc-v3-emitter | acceptance-final.chain.log | 1 | 1282.0 | -1121.0 | 0.0 | 0 | argv-anchored |
| recent | maxl=2,maxload=60 | dev-wave-t2853-rerun-plan | acceptance-final.chain.log | 1 | 1232.0 | -1056.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-t2847-corpus-gaps | acceptance-final2.chain.log | 1 | 800.0 | -643.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-paper-story-20260923 | acceptance-final2.chain.log | 1 | 777.0 | -620.0 | 1.0 | 1 | argv-anchored |
| recent | maxl=2,maxload=60 | dev-wave-paper-story-20260923 | acceptance-final3.chain.log | 1 | 750.0 | -615.0 | 1.0 | 1 | argv-anchored |
| recent | maxl=2,maxload=60 | dev-wave-t2858-mocc-xp-pin | gate-loop-final.log | 1 | 641.0 | -484.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-t2847-verifier-capacity | acceptance-final.chain.log | 1 | 516.0 | -348.0 | 1.0 | 1 | substring |
| recent | maxl=2,maxload=60 | dev-wave-t2854-unit5-v3-wiring | acceptance-final.chain.log | 1 | 351.0 | -235.0 | 0.0 | 0 | substring |
| recent | maxl=2,maxload=60 | dev-wave-t2854-mocc-v3-emitter | acceptance-final2.chain.log | 1 | 332.0 | -225.0 | 0.0 | 0 | argv-anchored |
| since | maxl=2,maxload=60 | dev-wave-t2825-ledger-refresh-ab | acceptance-final3.chain.log | 1 | 4604.0 | -4461.0 | 1.0 | 1 | argv-anchored |
| since | maxl=2,maxload=60 | dev-wave-lease-gate-wait-diagnosis | acceptance-final.chain.log | 1 | 3874.0 | -3713.0 | 1.0 | 1 | argv-anchored |
| since | maxl=2,maxload=60 | dev-wave-t2850-trial-prereg | acceptance-final.chain.log | 1 | 3681.0 | -3552.0 | 0.0 | 0 | argv-anchored |
| since | maxl=2,maxload=60 | dev-wave-t2854-v3-existence | acceptance-final.chain.log | 1 | 3195.0 | -3061.0 | 0.0 | 0 | substring |
| since | maxl=2,maxload=60 | dev-wave-land-roundtrip-diagnosis | acceptance-final.chain.log | 1 | 3145.0 | -3016.0 | 0.0 | 0 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2812-old-series-realignment | gate-loop-final.log | 1 | 2902.0 | -2767.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2344-source-bound-emitters | acceptance-final.chain.log | 1 | 1875.0 | -1746.0 | 1.0 | 0 | substring |
| since | maxl=2,maxload=60 | dev-wave-tpcc-trace-design | acceptance-final.chain.log | 1 | 1840.0 | -1699.0 | 1.0 | 1 | argv-anchored |
| since | maxl=2,maxload=60 | dev-wave-t2795-k2-pair-repair | acceptance-final.chain.log | 1 | 1745.0 | -1620.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-login-check-wall | acceptance-final2.chain.log | 1 | 1732.0 | -1569.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-acceptance-resubmit-causes | acceptance-final.chain.log | 1 | 1688.0 | -1554.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-t2850-trial-prereg | acceptance-final2.chain.log | 1 | 1472.0 | -1326.0 | 1.0 | 1 | argv-anchored |
| since | maxl=2,maxload=60 | dev-wave-t2273-acceptance-bottleneck-diag | acceptance-final.chain.log | 1 | 1384.0 | -1246.0 | 0.0 | 0 | argv-anchored |
| since | maxl=2,maxload=60 | dev-wave-t2847-mutation-run | acceptance-final.chain.log | 1 | 1247.0 | -1129.0 | 1.0 | 1 | substring |
| since | maxl=2,maxload=60 | dev-wave-codex-model-sol | acceptance-final.chain.log | 1 | 1247.0 | -1122.0 | 0.0 | 0 | substring |

## 欠測・打切り・未知行

24時間以上の無記録空白は時刻文字列のみから識別できない。複数逆行または錨と mtime の日付矛盾は未解決。未知行は JSON に逐語を保持。

| 分類 | 行数 |
| --- | --- |
| info | 285 |
| other | 17 |

| file | date_status | 理由 | info 数 | other 数 | 打切り数 | GO に started 無し |
| --- | --- | --- | --- | --- | --- | --- |
| /work/1/SFC/tanab/dev-wave-jobs/cleanup-0921c-ledger-handover/acceptance-final-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-branch-residue-cleanup/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-codex-model-sol/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-codex-selfrun-precheck/acceptance-L1-1.chain.log | anchored | [] | 3 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-codex-selfrun-precheck/acceptance-L2-1.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-codex-selfrun-precheck/acceptance-L2-2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-codex-selfrun-precheck/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-codex-selfrun-precheck/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-comsys2026-manuscript/acceptance-final.chain.log | anchored | [] | 3 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-dwm08-selfrun-probe/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-focus-run-count-diagnosis/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-land-roundtrip-diagnosis/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-lease-gate-wait-diagnosis/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-login-check-wall/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-login-check-wall/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/acceptance-final.chain.log | anchored | [] | 7 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-abstract-conclusion-ja/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-b8-pass-ja/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-b8/acceptance-final.chain.log | anchored | [] | 0 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-b8/acceptance-final2.chain.log | anchored | [] | 0 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-b8/acceptance-final3.chain.log | mtime-estimated (推定) | [] | 0 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-b8/acceptance-final4.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/acceptance-final1.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260921/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260923/acceptance-final.chain.log | anchored | [] | 2 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260923/acceptance-final2.chain.log | anchored | [] | 0 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260923/acceptance-final3.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260923/acceptance-final4.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-provenance-cold-diag/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-silo-function-synthesis-space/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1851-leftover-audit/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/acceptance-final1.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/acceptance-final3.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-repair/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-repair/acceptance-final2.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-repair/acceptance-final3.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-repair/acceptance-final4.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/acceptance-final3.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/acceptance-final3.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-effective/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-effective/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2810-g1-launch-validation/gate-loop-final.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2810-g1-launch-validation/gate-loop-final2.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2812-old-series-realignment/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/acceptance-final2.chain.aborted-before-submit.log | mtime-estimated (推定) | [] | 0 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/acceptance-final3.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/acceptance-final4.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2817-acceptance-bottleneck-3/acceptance-ref.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/acceptance-final3.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-resume/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-resume/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-shard-plugin-modify-timing/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/acceptance-final2.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/acceptance-final3.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2833-land-eintr-retry/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2833-land-eintr-retry/acceptance-final2.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2833-land-eintr-retry/acceptance-final3.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2835-land-guard-base/acceptance-final-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch/acceptance-final.chain.log | anchored | [] | 4 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch/acceptance-final2.chain.log | anchored | [] | 4 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch/acceptance-final3.chain.log | anchored | [] | 3 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-corpus-gaps/acceptance-final.chain.log | mtime-estimated (推定) | [] | 0 | 0 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-corpus-gaps/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/acceptance-final.chain.log | anchored | [] | 6 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/acceptance-final2.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/acceptance-final3.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/acceptance-final4.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/acceptance-final.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-verifier-capacity/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-verifier-detection-design/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2849-comparison-harness-design/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-prereg/acceptance-final.chain.log | mtime-estimated (推定) | [] | 4 | 0 | 0 | 1 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-prereg/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2851-tpcc-prereg/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2851-transfer-prereg/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-repro-package-estimate/acceptance-final.chain.log | anchored | [] | 3 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-repro-package-rest/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-rerun-plan/acceptance-final.chain.log | anchored | [] | 3 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/acceptance-final.chain.log | anchored | [] | 3 | 2 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/acceptance-final.chain.log | anchored | [] | 2 | 3 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-v3-existence/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2857-silo-policy-stage-c/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2858-mocc-xp-pin/gate-loop-final.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2860-k2-round4-reflux/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2860-k2-round4-reflux/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2862-comsys-manuscript-revision/acceptance-final.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2864-comsys-refs-sec7/acceptance-final.chain.log | anchored | [] | 0 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-small-compare/acceptance-final.chain.log | anchored | [] | 5 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-small-compare/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-tpcc-trace-design/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-vldb-direction-revision/acceptance-final.chain.log | anchored | [] | 0 | 1 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-vldb-direction-revision/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-waiter-collect-latency/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-waiter-collect-latency/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wall-decomp/acceptance-final.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/acceptance-final2.chain.log | anchored | [] | 3 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/next-tasks-throwable-only/acceptance-final-1.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921/acceptance-final-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921b/acceptance-final-1.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921c/acceptance-final-1.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921c/acceptance-final-2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921d/acceptance-final-1.chain.log | mtime-estimated (推定) | [] | 0 | 1 | 1 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921d/acceptance-final-2.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921d/acceptance-final-3.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260922a/acceptance-final-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260923a/acceptance-final-1.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260923a/acceptance-final-2.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260923b/acceptance-final-1.chain.log | anchored | [] | 1 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260923c/acceptance-final-1.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260923c/acceptance-final-2.chain.log | anchored | [] | 2 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/t2851-transfer-runner/acceptance-final.chain.log | anchored | [] | 4 | 0 | 0 | 0 |
| /work/1/SFC/tanab/dev-wave-jobs/t2851-transfer-runner/acceptance-final2.chain.log | anchored | [] | 1 | 0 | 0 | 0 |

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
