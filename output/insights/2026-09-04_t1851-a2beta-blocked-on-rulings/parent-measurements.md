# [T-1851] A2β — 親の実測

すべて親が実走した。login node は `pegasus` の login node、計算ノードは `run_tests.py` /
`check_ai_provenance.py` の自動 dispatch (gen_S) による。測定した checkout を併記する。

## 継承時の実測 (checkout: primary main `1b7822110`、branch tip `520b1ddba`)

| 項目 | 値 |
|---|---|
| `git log --oneline main..worktree-dev-wave-t1851-unit-a` | 21 commit (B1 2、A1' 4、A2α 9、merge 4、記録・自己改善 2) |
| merge-base | `36406d376` |
| `git rev-list --count branch..main` | 146 |
| main が merge-base 以後に変えた file のうち branch の実装面 4 file との交差 | 0 (交差は `docs/dev-wave/operations.md` のみ) |
| `pgrep -af dev-wave-t1851-unit-a` | 0 件 |
| `ListAgents` の同名 wave | 無し (peer 70 session 中) |
| `docs/decisions.md` の A2α 裁定 3 件 | 無し (D1622 まで) |
| worklog 1260 (/rulings 第 7 回) の索引 | T-1851 を含まず |

## main 取り込み (checkout: worktree `dev-wave-t1851-unit-a`)

| 項目 | 値 |
|---|---|
| `git merge --no-ff --no-commit main` | 競合なし (`Automatic merge went well`) |
| `git ls-tree main external/ccbench` と staged gitlink | 一致 `511c9538e` |
| `check_ai_provenance.py --message-file merge-msg-1.txt` | rc=0 (`1 件、違反なし`) |
| merge commit | `7771c9e65` (integrator) |
| `check_ai_provenance.py` 全史 (計算ノード 977068.nqsv、Elapse 52S) | rc=0、8,167 件、新規違反なし、known-violations 55 |
| `git submodule update --recursive` | 無出力 (揃っていた) |
| `check_docs.py` | rc=0 |
| `check_wave_startup.py --mode resume --external-handoff <job dir handoff>` | rc=0 (`乖離なし 0 commit`) |
| `spool_fold.py --dry-run` (fragment 編集前) | rc=0 |

## 焦点走 (DW-O26、checkout: `7771c9e65`)

対象は編集面 4 module 名で `orchestrator/tests/` を grep した consumer 14 file と
`test_plain_runner_coverage.py`。login node の guard が素の pytest を拒否するため
`tools/run_tests.py` 経由 (自動 dispatch)。

| 対象 | 結果 |
|---|---|
| 15 file | **1,720 passed / 5 skipped / rc=0**、141.37 s |

## 受入全走 (checkout: `7771c9e65`)

- 投入: `tools/dev_wave_wait.py acceptance --wave dev-wave-t1851-unit-a`
  `--lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease --receipt-file <job dir>/acceptance-3.receipt.json`
  `--log-file <job dir>/acceptance-3.child.log -- python3 tools/run_tests.py`
- attempt 1 / 2 はテストが 1 件も走る前に投入 argv の誤りで終わった (attempt 1: Write で作った
  run script に実行権限が無く `許可がありません`。attempt 2: `--receipt-file` / `--log-file` 欠落で
  `stage=cli-usage rc=2`)。
- attempt 3: gen_S 混雑 (QUE 243 / RUN 69) で 3 shard の dispatch が既定 900 秒の queue 待ち後に signal-abort (`child_started=true`、`child_rc=null`、`kind=infra`)。`stage=acceptance-command rc=70 source_rc=16 reason=dispatch-attestation-missing`、テスト本体は 1 件も走らず、赤ではない。job 977095 / 977097 は qstat に不在で、orphan hold 3 file (`orphan-hold.json` と `orphan-holds/<id>.json` 2 本) を作業木 clean を確認して消した。
- attempt 4 (D612 の上書き `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` / `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600`): `classification=child-green`、`reason=child-verdict`、`retry=false`、raw / normalized child rc=0。**20,469 passed / 68 skipped**。`verdict=child-green`、`tested_main=1b7822110c54536f82ecab8d058d7a9253bfd3ce`、`tested_tip=7771c9e65d8507c4c1af984a844b0680345d420d`、`lease_holder=a089fc930b73`、pre/post fingerprint 一致 (digest `1f5d90743fe8…`、status_bytes 0)。lease は走行後に `tools/wave_land_window.py release` で解放した (`state=released`、`holder_self=true`)。
- **受入は記録 commit より前の tip `7771c9e65` に対するものである。** 記録 commit は docs のみで、
  D1341 により本 wave は land しない。6 段が揃った時点で受入を取り直す。

## 記録後の検査 (checkout: 記録 commit)

記録 commit 前の作業木で実走 (checkout: `7771c9e65` + 未 commit の docs)。

| 検査 | 結果 |
|---|---|
| `check_docs.py` | rc=0 (`違反なし`) |
| `spool_fold.py --dry-run` | rc=0、`status=planned` |
| 三軸語走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search` | rc=0、conjunction_hits 0、positive_control hit_count 145 |
| `git diff --check` | rc=0 |

記録 commit 後の再走 (F34) は本 file の末尾に amend で追記する。

### 記録 commit `93530d779` 後の再走 (F34、amend で追記)

| 検査 | 結果 |
|---|---|
| `check_ai_provenance.py` 全史 (計算ノード 977182.nqsv、Elapse 47S) | rc=0、8,168 件、新規違反なし |
| `check_docs.py` | rc=0 |
| 三軸語走査 | rc=0、conjunction_hits 0、positive_control hit_count 145 |
| `spool_fold.py --dry-run` | rc=0 |
| `git status --short` | 空 |
