# 段 6 裁定 1 — [T-2853] (1') 敵対レビュー 2 本の所見と fix 1 の範囲

- 対象: 統合 commit 3962394dd6d43fe5f799644e63958c281a6c3b00 (基準 74e6d2f23)。
- レビュー A (正しさ境界・整合) `codex/s6-review-A.md` NO-GO: must-fix 1・should 2。レビュー B (実効性・過剰・削除) `codex/s6-review-B.md` NO-GO: must-fix 1・should 1・nit 1。両方 check_codex_output rc=0。
- 焦点走 1 回目 (`focus-1.log`) の赤は本裁定の後に追記する (§4)。

## 1. 所見の裁定

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| A-M1 / B-M1 (同一) | patch と HEAD を検証の後に生きた checkout から取るので、build 時の source (evidence) とずれても inventory が `complete` になる | **real・scope 内** (2 レンズが独立に同じ反例。放置時: inventory から組む R1 の source が元の判定の source と違い、R1 の判定が変わりうるのに inventory は正常を名乗る) | 保全時に `sha256(patch) == evidence.tracked_diff_sha256` と `source root の rev-parse HEAD == evidence.ccbench_commit` を照合し、どちらか不一致なら inventory を `failed` (error に理由) にする。**段 4 裁定 §2 項 2 の「一致を gate にしない (記録だけ)」を撤回**する — 照合は保全の成否 (archival index の status) だけに効き、評価結果・verdict・例外には効かない (D2233 項 4 の境界の内側) |
| A-S2 | test の source root (`git_source`) に Silo の proof source が無く `result.certified` が先に落ちる。M1・M2・M4〜M8 の kill 点が単一理由にならない | real・scope 内 | fixture の tmp git repo に `test_campaign._install_complete_silo_proof_source` で proof source を入れて commit し、その後 proof に関係しない tracked file を 1 つ変えて dirty にする。無変異で緑になることを焦点走で確かめる |
| A-S3 | `tracked_diff_sha256` の期待値が空 bytes の hash で、記録値と保存 patch の対応を検査していない | real・scope 内 | evidence の `tracked_diff_sha256` を fixture の実 diff の sha256 にし (`tracked_clean=False`、`tracked_paths` も実 diff の path)、記録値 == 実 diff の hash == `patch_sha256` を assert |
| B-S2 | `ccbench_pin` が実在しない `deadbeef` で、pin + patch から source を組めることを試験していない | real・scope 内 (brief の完了判定そのもの) | evidence の `ccbench_commit` を fixture repo の実 HEAD にし、test で「inventory の `ccbench_pin` を別 dir に checkout (clone でよい) → 復元した patch を `git apply` → tracked file の内容が source root と一致」を確かめる |
| B-N3 | `subprocess.run`・`Path.read_bytes` の全体差し替えは将来の偽赤の余地 | nit (成果物の値を変えない) | 採用しない。insight に記録 |
| 親 (焦点走前の静的確認) | `_preserve_trace_directory` の `subprocess.run` 2 か所が `orchestrator/tests/test_ccbench_spawn_sites.py` の起動箇所棚卸しに未登録 (照合の追加で 3 か所目) | real・scope 内 (受入全走が赤になる) | git の起動を `_preserve_trace_directory` 専用の 1 helper (sanitized env、固定 argv 形 `git -C <root> …`、CCBench を実行しない) に寄せて起動箇所を 1 つにし、`test_ccbench_spawn_sites.py` の review 済み inventory に理由の comment つきで 1 行登録する。既存の登録の件数・意味は変えない |

削除・縮小の候補 (B §削除) はいずれも「削らない」と同意見 (B 自身の結論)。`_current_repo_head` への寄せは sanitized env を保つための引数追加が要り起動箇所が減らないので採らず、上の 1 helper に寄せる。

## 2. fix 1 の範囲 (Codex fix 子 1 本、同じ unit worktree・同じ branch に積む)

所有 path: `orchestrator/campaign/pipeline.py`、`orchestrator/tests/test_t2853_trace_preservation.py`、`orchestrator/tests/test_ccbench_spawn_sites.py` (登録 1 行と comment だけ)。
規模上限: production 120 行・test 280 行 (基準 74e6d2f23 からの追加行の合計)。test は段 4 の 200 行から 280 行へ上げる — 段 6 の real 所見で新 test 2 本 (M10・M11) と pin + patch からの復元確認・起動箇所の登録が加わるため。production は段 4 のまま。

## 3. 変異の追加登録 (DW-M01、fix 前)

| ID | 変異 | 期待 | kill 点 |
|---|---|---|---|
| M10 | patch の hash と evidence.tracked_diff_sha256 の照合を外す (不一致でも complete) | KILLED | 新 test `test_r1_source_drift_marks_failed` (evidence の tracked_diff_sha256 を実 diff と違う値にした入力で inventory が failed・原本保持・評価結果は env 未設定時と同じ) |
| M11 | source root の HEAD と evidence.ccbench_commit の照合を外す | KILLED | 新 test `test_r1_pin_drift_marks_failed` (evidence の ccbench_commit を実 HEAD と違う 40 hex にした入力で failed) |

M1〜M9 は段 4 のまま。fix 後に全件の単一理由を probe で確かめてから本走する。

## 4. 焦点走 1 回目 (統合 commit 3962394dd、job 29396.nqsv、Elapse 353 s): 10 failed / 3,933 passed / 14 skipped

- `test_t2853_trace_preservation.py` の 8 件 (既存 6 件 = test_archive_before_cleanup・test_unset_env_unchanged・test_failure_retains_original の 4 param・test_preservation_error_does_not_replace_result、新 test_inventory_records_r1_inputs ほか):
  すべて `assert result.certified` が偽。原因は fix 前の test wrapper `evaluate` が既定で proof source の無い tmp git repo を source root にしたこと (A-S2 と同じ)。実装の判定の回帰ではない (pipeline の verdict 経路は変えていない)。
  → fix 1: fixture の source root に Silo proof source を入れる。既存 6 test は元の挙動 (fix 前の base と同じ certified) に戻ること。既存 test の期待値は変えない。
- `test_ccbench_spawn_sites.py` の 2 件 (`test_reviewed_ccbench_measurement_launches_use_bounded_sites`・`test_reviewed_process_launch_inventory_is_recursive_and_exact`): 両方の登録簿で `('campaign/pipeline.py', '<module>._preserve_trace_directory'): 2` が未登録。
  → fix 1: §1 の最終行のとおり git 起動を 1 helper に寄せ、その 1 箇所を両方の登録簿へ理由の comment つきで登録する (zstd の既存登録 `_compress_trace_archive` と同じ流儀)。
- 他 21 file は緑。
