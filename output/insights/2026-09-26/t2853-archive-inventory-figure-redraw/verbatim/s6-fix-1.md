## 変更

- [pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2633): 保全用 Git 起動を `_archive_git` の 1 箇所に集約しました。source の HEAD と patch hash を evidence に照合し、不一致なら理由を記録して inventory を `failed` にします。
- [test_t2853_trace_preservation.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:32): Silo proof source を commit した fixture に直し、実際の HEAD・diff に evidence を揃えました。pin と patch からの復元確認、source drift・pin drift のテストも追加しました。
- [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py:99): 新 helper の起動箇所を理由付きで登録しました。両登録簿の検査が参照する共通の登録です。

基準 `74e6d2f23` からの追加は **production 63 行／test 177 行**で、上限の 120／280 行以内です。変更した tracked file は指定の 3 件だけです。

## 裁定との対応

| 段 6 の所見・焦点走の赤 | 修正箇所 |
|---|---|
| A-M1／B-M1：保全 source のずれ | [HEAD・hash 照合](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2724)、[失敗記録](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2744) |
| A-S2：proof source 欠落 | [fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:64) |
| A-S3：diff hash の期待値 | [実 diff の evidence](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:85)、[照合 assert](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:124) |
| B-S2：pin と patch からの復元 | [clone・checkout・apply](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:126) |
| B-N3：test double の広い差し替え | 裁定どおり変更なし |
| `test_archive_before_cleanup` | [proof source 付き fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:70) |
| `test_unset_env_unchanged` | [計測開始前の metadata 取得](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:292) |
| `test_failure_retains_original` の 4 パラメータ | [共通 fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:64) |
| `test_preservation_error_does_not_replace_result` | [共通 fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:64) |
| `test_inventory_records_r1_inputs` | [実 HEAD・diff と復元の検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:99) |
| 起動箇所検査の赤 2 件 | [単一起動 helper](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2633)、[共通登録](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py:99) |

裁定から違えた箇所はありません。赤 10 件の解消は**静的な対応付けであり、未実走**です。

## 変異の位置

以下は現在の file 内で一意の置換アンカーです。赤になる箇所は未実走の予測です。M1〜M11 は `pipeline.py`、assert は `test_t2853_trace_preservation.py` にあります。

| ID | 置換アンカー → 置換後 | 予測する赤の assert |
|---|---|---|
| M1 | `tdir, "--json", "--expected-commits", str(commit_count_witness),` → `tdir, "--json",` | `test_inventory_records_r1_inputs` の argv 全体、117 行 |
| M2 | `"--protocol", genome.protocol, "--ccbench-root", evidence.source_root,` → 末尾の `evidence.source_root` を `tdir` に | 同 argv assert、117 行 |
| M3 | `if commit_count_witness is not None:` → `if True:` | `test_r1_argv_null_without_witness` の null assert、145 行 |
| M4 | `inventory["repo_head"] = _archive_git(repo_root, "head").decode().strip()` → `repo_root` を `evidence.source_root` に | inventory test の repo HEAD assert、118 行 |
| M5 | `inventory["ccbench_pin"] = evidence.ccbench_commit` → 右辺を `None` に | inventory test の pin assert、119 行 |
| M6 | `inventory["patch_sha256"] = hashlib.sha256(patch).hexdigest()` → 直前に `patch = b""` を挿入 | inventory test の復元 bytes・hash の組 assert、122 行 |
| M7 | `for path in sorted(verifier_root.glob("*.py"))` → `for path in sorted(verifier_root.glob("*.py"))[1:]` | inventory test の module hash 辞書 assert、134 行 |
| M8 | `archive_root = os.environ.get("IZANAGI_TRACE_ARCHIVE_ROOT")` → 直後に verifier module の `read_bytes()` と hash を挿入 | `test_unset_env_unchanged` の `r1_reads` assert、328 行 |
| M9 | `except Exception as exc:` と直後の `preserved = False` → `except OSError as exc:` | `test_r1_input_failure_retains_original` の結果比較 assert、168 行 |
| M10 | `if inventory["patch_sha256"] != evidence.tracked_diff_sha256:` → `if False and inventory["patch_sha256"] != evidence.tracked_diff_sha256:` | `test_r1_source_drift_marks_failed` が呼ぶ組 assert、193 行 |
| M11 | `if source_head != evidence.ccbench_commit:` → `if False and source_head != evidence.ccbench_commit:` | `test_r1_pin_drift_marks_failed` が呼ぶ組 assert、193 行 |
| C0 | `Archive one local repetition; failures propagate to the cleanup boundary.` → `Archive one local repetition; archival failures reach the cleanup boundary.` | 赤なし |

M10・M11 の入力はそれぞれ evidence の **1 field だけ**を変えます。M4 は repo と source の HEAD が異なる fixture、M9 は非 Git root の入力です。単一 assert での kill は変異 probe 未実走のため、まだ確定していません。

## 現行の受理・拒否挙動

照合は opt-in 保全処理内にあり、不一致は既存の `failed` inventory と原本保持の経路に入ります。[caller の例外境界](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2203)は変更していません。判定、`EvalResult` への投影、元の例外、WAL の処理も変更していません。env 未設定時は production の追加 Git 起動・hash・保全 I/O に入りません。この同一性の実走確認は残っています。

## 波及

所有外 caller では `_preserve_trace_directory` の呼出しは反復の `finally` に限られ、追加の既定値付き引数は段 5 のままです。`_execute_verification_repetition` の戻り値を参照する `test_campaign.py`、`test_verify_fanout.py`、`test_layer3_report.py`、共有 fixture、consumer test は編集していません。Git 起動 inventory の 2 テストは同じ登録を参照します。

## 実走

`python3 -m py_compile` は 3 ファイルで成功し、`git diff --check` も成功しました。pytest、焦点走、変異 probe、C0 は**実装済み・未実走**です。小さな手動 Git 確認は PreToolUse hook がコマンドを起動前に拒否したため、実走していません。

## 総括

指定の 3 ファイルに fix を反映し、行数上限内です。構文と差分形式は確認済みです。認証の回復と単一理由の変異 kill は、親の計算ノード実走による確認が必要です。