## 所見対応表 (H1〜H3: closed / partial / regressed と根拠)

| 所見 | 状態 | 根拠 |
| --- | --- | --- |
| H1 | closed | recent / since の判定方式×走行数の交差表と、同じ分類による leaders差の内訳表・指定脚注を追加。 |
| H2 | closed | 指定2条件の負の差を昇順で表示。recentは8行・1行、sinceは15行・9行。 |
| H3 | closed | 長時間待ち表に同時待ち最大・走行最大・leaders_grep・leaders起因閉門tick比を追加。 |

## 実装した内容

変更は `tools/gate_wait_probe.py` のMarkdown生成部のみです。既存の区間分割・閉門分類・走行照合・感度模型・self-check期待値は変更していません。

判定方式は起動回の既存データから取得。交差表は0件の組合せも表示し、感度差の同値はwave・file・segment順に並べます。git command・commitは実行していません。

## 実走した検査 (command と出力の逐語)

構文検査：終了コード0、出力なし。

```bash
PYTHONPYCACHEPREFIX=/tmp/gate-wait-probe-fix4/pycache python3 -m py_compile tools/gate_wait_probe.py
```

指定本走1本：終了コード0。

```bash
python3 tools/gate_wait_probe.py --jobs-root /work/1/SFC/tanab/dev-wave-jobs --since 2026-09-19 --recent-n 20 --until 2026-09-21T07:37:00+09:00 --exclude-wave dev-wave-lease-gate-wait-diagnosis --self-check --out-json /tmp/gate-wait-probe-fix4/until.json --out-md /tmp/gate-wait-probe-fix4/until.md
```

```text
scan directories=100 gate_logs=0
scan directories=200 gate_logs=11
scan directories=300 gate_logs=42
scan directories=400 gate_logs=42
scan directories=500 gate_logs=42
scan directories=600 gate_logs=49
scan directories=700 gate_logs=66
scan directories=800 gate_logs=102
scan directories=900 gate_logs=177
scan directories=1000 gate_logs=177
scan directories=1100 gate_logs=181
scan directories=1200 gate_logs=192
scan directories=1300 gate_logs=192
scan directories=1400 gate_logs=192
gate logs=126 waves=79 segments=467
self-check dev-wave-t2610-fig10: passed [('censored', 3021.0, 2, True, 1), ('observed-wait', 853.0, 0, False, 1)]
self-check dev-wave-t2814-cleanup-command: passed [('observed-wait', 745.0, 0, False, 1), ('observed-wait', 122.0, 0, False, 2)]
self-check dev-wave-paper-story-20260921: passed [('observed-wait', 149.0, 0, False, 1)]
self-check dev-wave-t2243-collection-diag: passed [('observed-wait', 171.0, 0, False, 1), ('observed-wait', 151.0, 0, False, 2)]
JSON: /tmp/gate-wait-probe-fix4/until.json
MD: /tmp/gate-wait-probe-fix4/until.md
```

fix3とのJSON全体比較：終了コード0、出力なし。全生record・集計がバイト単位で一致しました。

```bash
cmp /tmp/gate-wait-probe-fix3/until.json /tmp/gate-wait-probe-fix4/until.json
```

## 本走の要点 (上記の表を逐語)

母集合と観測区間：

```markdown
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
```

F2小表はfix3報告と全数値が一致。sinceの走行数≤1は83＋419＝502 tickです。

```markdown
| 母集合 | leaders-only + both の走行数 | tick 数 | 分 (推定、直前 tick 配分) |
| --- | --- | --- | --- |
| recent | 0 | 0 | 0.0 |
| recent | 1 | 14 | 28.133 |
| recent | ≥2 | 38 | 77.467 |
| since | 0 | 83 | 168.333 |
| since | 1 | 419 | 834.65 |
| since | ≥2 | 526 | 1046.333 |
```

H1の2表と脚注：

```markdown
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
```

H2の表：

```markdown
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
```

H3の表（ヘッダとsince側39行を逐語抜粋）：

```markdown
| 母集合 | wave | file | segment | kind | 秒 | 拒否 | 飢餓候補 | 同時待ち最大 | 走行最大 | leaders_grep | 閉門 leaders 起因 tick / 全 tick |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
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
```

self-check節：

```markdown
## self-check

実 log の照合。tuple = (kind, 秒, 再カウント拒否, 飢餓候補, attempt)。

| wave | 結果 | 実測 | 期待 |
| --- | --- | --- | --- |
| dev-wave-t2610-fig10 | passed | [["censored", 3021.0, 2, true, 1], ["observed-wait", 853.0, 0, false, 1]] | [["censored", 3021, 2, true, 1], ["observed-wait", 853, 0, false, 1]] |
| dev-wave-t2814-cleanup-command | passed | [["observed-wait", 745.0, 0, false, 1], ["observed-wait", 122.0, 0, false, 2]] | [["observed-wait", 745, 0, false, 1], ["observed-wait", 122, 0, false, 2]] |
| dev-wave-paper-story-20260921 | passed | [["observed-wait", 149.0, 0, false, 1]] | [["observed-wait", 149, 0, false, 1]] |
| dev-wave-t2243-collection-diag | passed | [["observed-wait", 171.0, 0, false, 1], ["observed-wait", 151.0, 0, false, 2]] | [["observed-wait", 171, 0, false, 1], ["observed-wait", 151, 0, false, 2]] |
```

## 波及・未実走・既知の限界

- 所有外caller・共有fixture・consumer testへの変更は無し。追加依存も無し。
- 実走範囲は構文検査と指定本走1本。子の検査は親の全走を代替しません。
- leaders_grepは現存scriptからの判定で、過去版の証明ではありません。走行記録の欠落・終点推定による照合限界も維持しています。
- H3の分母は区間の全tick。leaders起因0件でも、条件不明などを含むため「閉門なし」とは断定できません。
- 感度差は仮定付き参考模型であり、実際の短縮効果ではありません。
- 検査成果物とキャッシュは指定の`/tmp`配下。報告書fileは作成していません。

## 総括

H1〜H3はclosed。self-check4件passed、F2小表はfix3と一致し、JSON全体もバイト単位で一致しました。