## 変更差分

指定の 2 file・3 literal のみ更新しました。算法・完全一致比較・対象 dir・`fail 2`・completion 記録は不変です。

`git diff --stat`（逐語）:

```text
 orchestrator/tests/test_backoff_extended_sweep.py | 4 ++--
 tools/pegasus/b10_backoff_grid.sh                 | 2 +-
 2 files changed, 3 insertions(+), 3 deletions(-)
```

`git diff`（逐語）:

```diff
diff --git a/orchestrator/tests/test_backoff_extended_sweep.py b/orchestrator/tests/test_backoff_extended_sweep.py
index d708f55d0..f51b1c823 100644
--- a/orchestrator/tests/test_backoff_extended_sweep.py
+++ b/orchestrator/tests/test_backoff_extended_sweep.py
@@ -1668,7 +1668,7 @@ def test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs():
     assert budget["EXPECTED_WALLTIME_S"] == 18000
     assert (
         "EXPECTED_FREEZE_TREES_SHA256="
-        "c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3"
+        "6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415"
     ) in job
     assert "WORKLOADS=(write-heavy balanced read-heavy)" in submit
     assert (
@@ -2022,7 +2022,7 @@ def test_b10_freeze_tree_bytes_match_the_wave_local_gate():
         digest.update(b"\0")
         digest.update(path.read_bytes())
     assert digest.hexdigest() == (
-        "c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3"
+        "6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415"
     )


diff --git a/tools/pegasus/b10_backoff_grid.sh b/tools/pegasus/b10_backoff_grid.sh
index 0f7864bea..7736c0afc 100644
--- a/tools/pegasus/b10_backoff_grid.sh
+++ b/tools/pegasus/b10_backoff_grid.sh
@@ -19,7 +19,7 @@ WORKTREE_CLEANUP_CAP_S=120
 FINALIZE_CAP_S=300
 EXPECTED_WALLTIME_S=18000
 EXPECTED_RESERVE_S=1380
-EXPECTED_FREEZE_TREES_SHA256=c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3
+EXPECTED_FREEZE_TREES_SHA256=6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415
 BUILD_NETWORK_PROXY_URL=http://10.120.96.1:8080
 CURRENT_STAGE=bootstrap
 PY=""
```

`git status --porcelain --untracked-files=all`（逐語）:

```text
 M orchestrator/tests/test_backoff_extended_sweep.py
 M tools/pegasus/b10_backoff_grid.sh
```

HEAD は `9fa49b0a1`。禁止された Git 操作は実行していません。

## 検算結果

`python3 -I -B -c` で指定算法を直接実行し、両期待値への assert が成功しました。ファイルは生成していません。

```text
20 6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415
19 c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3
```

19 file は G のみを検算対象から除いた値です。実 tree は変更していません。

| 検査 | 結果 |
|---|---|
| test module の `ast.parse` | 成功 |
| `bash -n < tools/pegasus/b10_backoff_grid.sh` | rc=0 |
| `test_b10_freeze_tree_bytes_match_the_wave_local_gate()` | module import 後の直接呼び出し成功 |
| `test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs()` | module import 後の直接呼び出し成功、fixture 不要 |

対象 2 file の `grep -n c405c742 …` は出力なし、rc=1（0 件）。`grep -n 6a4ee1ef …` は rc=0、ちょうど次の 3 件です。

```text
orchestrator/tests/test_backoff_extended_sweep.py:1671:        "6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415"
orchestrator/tests/test_backoff_extended_sweep.py:2025:        "6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415"
tools/pegasus/b10_backoff_grid.sh:22:EXPECTED_FREEZE_TREES_SHA256=6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415
```

## 静的列挙

編集前の `git grep -n c405c742` で、更新すべき起動契約は今回の test 1671・2025 行と job script 22 行の 3 か所でした。

それ以外の全出現先を以下に列挙します。すべて測定・作業時点の記録であり、更新していません。表中の `I/` は `output/insights/` です。

| 出現先 | 行 | 分類 |
|---|---|---|
| `docs/archive/worklog-phase3-0919-1688.md` | 8 | 受入失敗の記録 |
| `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` | 120 | 測定記録 |
| `docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md` | 129 | 測定記録 |
| `I/2026-09-07/t2266-tail-measurement/README.md` | 255 | 測定記録 |
| `I/2026-09-07_t2320-backoff-sweep-gate-layer2/t2266-tail/completion-balanced.json` | 13 | 完了記録 |
| 同 directory の `completion-read-heavy.json` | 13 | 完了記録 |
| 同 directory の `completion-write-heavy.json` | 13 | 完了記録 |
| `I/2026-09-09_t2418-backoff-static-explore/README.md` | 197 | 測定記録 |
| `I/2026-09-10/t2266-formal-1000us/README.md` | 296 | 測定記録 |
| `I/2026-09-10/t2266-formal-1000us/t2266-tail-v2/completion-balanced.json` | 13 | 完了記録 |
| 同 directory の `completion-read-heavy.json` | 13 | 完了記録 |
| 同 directory の `completion-write-heavy.json` | 13 | 完了記録 |
| `I/2026-09-15/t2266-tail-band/README.md` | 167 | 測定記録 |
| `I/2026-09-19/b10-tail-cohort2/README.md` | 74 | 測定記録 |
| `I/2026-09-19/b10-tail-cohort2/verbatim/extract-cohort1-crosscheck.md` | 27・40・53 | 測定照合記録 |
| `I/2026-09-19/b10-tail-cohort2/verbatim/extract-cohort2.md` | 27・40・53 | 測定照合記録 |
| `I/2026-09-19/t2724-chain-land-2/README.md` | 72・73・74・110 | 受入失敗・検算記録 |
| `I/2026-09-19/t2724-chain-land-2/evidence/acceptance-1-failure-excerpt.txt` | 2・4・21・23・25 | 失敗ログ |

親 brief の分類と一致します。ただし `docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json` は、この HEAD では旧値 literal と `freeze_trees_sha256` キーの双方が検索 0 件でした。completion の path・sha256 等を保持する過去の記録であり、不変とする扱いは同じです。

`test_b10_backoff_grid_job.py:420–425` は厳密には旧 literal の置換ではなく、固定 pin 行より後の `source[start:]` に次を前置します。

```bash
remove_ccbench_worktree() { :; }
freeze_digest() { echo fixture-freeze; }
EXPECTED_FREEZE_TREES_SHA256=fixture-freeze
```

したがって今回の定数変更による影響はありません。

## 変異期待の確認

対象 test file の他の assert と、関連 job・submit test の参照を静的に確認しました。確認範囲では追加の赤 node は見つかりませんでした。

| 変異 | 期待 node（`test_backoff_extended_sweep.py::` 以下） | 拒否理由 |
|---|---|---|
| m1 | `test_b10_freeze_tree_bytes_match_the_wave_local_gate` | 実 tree digest と旧 test literal の不一致 |
| m2 | `test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs` | job 内に新 pin 文字列が存在しない |
| n2 | `test_b10_freeze_tree_bytes_match_the_wave_local_gate` | `measurement_freeze.json` の byte 変更による digest 不一致 |

他の job 関連 assert は予算・routing・script の構造などを検査しており、この literal や実 freeze bytes を別途照合しません。script identity の test も固定 script hash の比較ではなく、照合処理の文字列検査です。

以上は期待集合の静的確認です。変異を実行して完全集合を実証したものではありません。

## 未実走・限界

pytest、変異 m1/m2、負例 n1/n2/n3、焦点走・受入全走は未実走です。

隔離 Python (`-I`) での module import は user-site の pytest が見えず失敗しました。その後 `python3 -B` で既存 pytest を import し、指定の 2 関数を直接呼び出して成功しました。pytest runner は起動していません。

hook は編集用 Python、digest の heredoc、script 名を引数にした `bash -n` を拒否しました。編集は差分適用ツール、digest は `-c`、構文検査は標準入力経由で完了しています。

## 総括

指定の 3 literal の更新と検算を完了しました。変更は 2 file のみです。親による独立レビュー・変異実測・受入・commit に引き渡せる状態です。