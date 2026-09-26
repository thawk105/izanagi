## 変更

- [pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2668): 宣言 pin が空でなく、source HEAD がその宣言値で始まる場合に一致とします。`ccbench_pin` に完全 HEAD、`ccbench_pin_declared` に宣言値を記録します。evidence がない場合は両方 `null` です。
- [test_t2853_trace_preservation.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:155): 7 桁 pin のテストを追加し、既存の本 wave テスト 2 件で宣言値も確認します。M11 の入力は実 HEAD の先頭 1 桁を変えた、異なる 40 桁のままです。

基準 `74e6d2f23` からの追加行は **production 64／test 191**（今回編集していない起動箇所テストの既存追加 2 行を含む）で、上限 120／280 行以内です。今回の変更ファイルは指定の 2 件だけです。

## 裁定との対応

| 対象 | 修正箇所 |
|---|---|
| 段 6 裁定 2 §1：短縮 pin の受理 | [前方一致と空宣言の拒否](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2738) |
| 同 §1：完全 SHA と宣言値の記録 | [inventory の初期値と代入](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2668)、[source HEAD の代入](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2724) |
| 同 §2：M12 の kill 点 | [短縮 pin の単一 assert](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:163) |
| 同 §2：M11 の維持 | [異なる 40 桁を作る入力](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:198) |

焦点走 2 回目は **3,945 passed／0 failed／14 skipped** で、対応する赤はありません。裁定から違えた箇所はありません。

## 変異の位置

以下の置換アンカーは、いずれも現在の `pipeline.py` 内で **1 回だけ**現れます。赤は未実走の予測です。

| ID | 置換アンカー → 置換後 | 赤になる test・assert |
|---|---|---|
| M1 | `tdir, "--json", "--expected-commits", str(commit_count_witness),` → `tdir, "--json",` | `test_inventory_records_r1_inputs`、117 行の argv assert |
| M2 | `"--protocol", genome.protocol, "--ccbench-root", evidence.source_root,` → 末尾を `tdir` に変更 | 同 117 行 |
| M3 | `if commit_count_witness is not None:` → `if True:` | `test_r1_argv_null_without_witness`、146 行 |
| M4 | `inventory["repo_head"] = _archive_git(repo_root, "head").decode().strip()` → `repo_root` を `evidence.source_root` に変更 | inventory test、118 行 |
| M5 | `inventory["ccbench_pin"] = source_head` → 右辺を `None` に変更 | inventory test、120 行 |
| M6 | `patch = _archive_git(evidence.source_root, "diff")` → `patch = b""` | inventory test、123 行の復元 bytes・hash の組 assert |
| M7 | `for path in sorted(verifier_root.glob("*.py"))` → 反復対象に `[1:]` を追加 | inventory test、135 行 |
| M8 | `archive_root = os.environ.get("IZANAGI_TRACE_ARCHIVE_ROOT")` → 直後に verifier module の読取・hash を挿入 | `test_unset_env_unchanged` の `r1_reads` assert |
| M9 | `except Exception as exc:` と直後の `inventory.update(status="failed", error=str(exc))` → `Exception` を `OSError` に変更 | `test_r1_input_failure_retains_original`、182 行の結果比較 |
| M10 | `if inventory["patch_sha256"] != evidence.tracked_diff_sha256:` → 条件の先頭に `False and` を追加 | `test_r1_source_drift_marks_failed`、207 行の組 assert |
| M11 | `if not evidence.ccbench_commit or not source_head.startswith(evidence.ccbench_commit):` → `if False:` | `test_r1_pin_drift_marks_failed`、207 行の組 assert |
| M12 | 同じ前方一致条件 → `if not evidence.ccbench_commit or source_head != evidence.ccbench_commit:` | `test_r1_short_pin_records_full_head`、163 行の **1 assert** |
| C0 | `Archive one local repetition; failures propagate to the cleanup boundary.` → `Archive one local repetition; archival failures reach the cleanup boundary.` | 赤なし |

## 現行の受理・拒否挙動

短縮 pin は source HEAD の前方一致で受理し、空宣言と不一致は従来の `failed` inventory に入ります。変更は保全処理内に限られ、[caller の例外境界](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2203)は変更していません。したがって保全の成否は評価結果・元の例外・WAL を置き換えず、env 未設定時の追加 I/O・subprocess・hash もありません。この同一性のテスト実走は親の確認待ちです。

## 波及

所有外の caller は反復処理からの `_preserve_trace_directory` 呼出し、直接利用する consumer test は `test_multiple_archives_and_streaming_counts` です。共有 `test_campaign` fixture、起動箇所登録、他の consumer test は編集していません。Git 起動箇所も増えていません。

## 実走

2 ファイルの `python3 -m py_compile` と `git diff --check` は成功しました。pytest、焦点走、M1〜M12・C0 の変異 probe は今回未実走です。

## 総括

短縮 pin の通常経路を受理し、inventory に完全 SHA と宣言値を残す修正を反映しました。変更は指定の 2 ファイルに収まり、構文と差分形式を確認済みです。