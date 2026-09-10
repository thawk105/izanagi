# [T-1851] B2 / D1 (非 terminal 部分) — 親の実測

すべて親が実走した。login node は `pegasus` の login node、計算ノードは `tools/run_tests.py` の自動 dispatch
(`| ` 前置の行は計算ノード側の出力)。時刻は JST。codex 子はいずれも sandbox で pytest を走らせられなかった
(runner rc=16、`child_started=false`)。子の未実走を緑と数えていない。

## 起動と main 取り込み (checkout: `fd814b2f0` → `50dbf9158`)

| 検査 | 結果 |
|---|---|
| `check_wave_startup.py --mode resume --external-handoff` (取り込み前) | rc=1 (`HEAD does not contain local main (75 commit behind)`、想定どおり) |
| `git merge --no-ff --no-commit 61bc6ac69` 1 回目 | `error: Unable to write index` (Lustre の一過性)。`--abort` 後の 2 回目で `Automatic merge went well` |
| 両親が共に変更した file (merge-base `1b7822110`) | 0 件 (`comm -12`) |
| `external/ccbench` gitlink | 両親とも `511c9538e` |
| provenance `--message-file` 事前検査 | rc=0 |
| merge commit | `50dbf9158` (integrator) |
| `check_wave_startup.py --mode resume --external-handoff` (取り込み後) | rc=0 |
| `check_docs.py` | rc=0 |
| 全史 provenance (`check_ai_provenance.py`、計算ノード) | rc=0、**8,245 件、新規違反なし** |

## focus 走 (DW-O26、消費側 20 file = 編集面 4 module の consumer 19 file + `test_plain_runner_coverage`)

| 走 | checkout | 結果 |
|---|---|---|
| baseline (実装前、21 file) | `50dbf9158` | 2,210 passed / 8 skipped / **collect error 1** (`test_s8b_approved.py:31` の `from tests.skiputil import` が file 選択走で `No module named 'tests'`。DW-O18 の偽赤型、以後 20 file) 計算ノード 977879.nqsv、76.2 s |
| focus 1 (段 5 統合後、未 commit) | `50dbf9158` + s5 | **2,264 passed / 8 skipped / rc=0**、60.4 s |
| focus 2 (fix1 統合後、未 commit) | `50dbf9158` + s5 + fix1 | **1 failed** / 2,266 passed / 8 skipped、65.3 s。赤 = fix1 新設 `test_live_v5_real_registry_rejects_reported_other_generation` (fixture が世代 B の admission を A と同じ campaign identity で予約し `measurement generation claim identity was unexpectedly reused`)。production 無関係 |
| focus 3 (fix2 統合後、未 commit) | `50dbf9158` + s5 + fix1 + fix2 | **2,267 passed / 8 skipped / rc=0**、71.4 s |

実装 commit `a0ac63690` は focus 3 と同じ bytes (8 file、+1,749 / −11)。

## 変異 matrix (checkout: `a0ac63690`、harness `tools/mutation_harness.py`、dispatch、runner = 所有 test 4 file `-q -rf`)

- probe 第 1 走 (全件 SURVIVED 登録、観測 node 収集目的): baseline PASSED (354 passed、27.0 s)。M1〜M8 は MISMATCH (赤、観測 node は `mutation-probe-summary.txt`)。M9 は dispatch の queue 待ち 900 s で rc=16 → harness が `PARSE_ERROR` で停止 (test 本体は未走行、変異は復元済み、`git status` clean)。
- probe resume (M9〜M18、D612 上書き 3600/600、`--resume`、sidecar を attempt-2 へ複写、wrapper-attempt 2): 10 件すべて MISMATCH (赤)。17/17 に観測 node 集合が付き (計 93 node、M15 は v4 key set 変異なので 52 node)、各集合は段 4 で事前登録した観測 node を含む。M9 の再走は 69 s。
- 本走 (`mutation-spec-final.json`、KILLED 期待 = 観測完全集合、D612 上書き、09:55〜10:07 JST): baseline PASSED (354 passed、27.4 s)、**17/17 KILLED、`matching=17`**、harness rc=0。各変異 32〜37 s (dispatch 込み)。

## 受入全走 (checkout: `b54836171` = 記録 commit `b6c5b568d` + local main `8c07ded74`)

- 受入全走 attempt 1 (`tools/dev_wave_wait.py acceptance`、post-claim merge で local main `8c07ded74` を `b54836171` (merge main、integrator trailer は tool 生成) として取り込み、D612 上書き 3600/600、10:12〜10:19 JST): `classification=child-green`、`reason=child-verdict`、raw / normalized child rc=0、**20,699 passed / 68 skipped**、3 shard、tested_main `8c07ded74`、tested_tip `b54836171`、pre / post fingerprint 一致 (`diff_bytes=0`、`status_bytes=0`)、lease_holder `a089fc930b73`。走行後に `wave_land_window.py release` で release (`state=released`、`holder_self=true`)。
- 全史 provenance (受入後、`b54836171` まで): rc=0、8,259 件、新規違反なし。
