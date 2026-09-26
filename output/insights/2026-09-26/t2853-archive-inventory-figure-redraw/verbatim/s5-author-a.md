## 変更

- [pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:490): **51 行追加**。反復の commit witness と `SourceEvidence` を保全処理へ渡し、inventory に R1 入力を記録します。patch は `patch/ccbench.diff.zst` に保全します。
- [test_t2853_trace_preservation.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:30): **106 行追加**。独立した一時 Git repo を使う fixture と指定の test を追加しました。

追加行数は裁定の上限（production 120 行、test 200 行）内です。

## 裁定との対応

| 裁定 | 実装箇所 |
|---|---|
| §2.1 witness・evidence の受け渡し | [pipeline.py:490](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:490)、[pipeline.py:2183](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2183) |
| §2.2 argv・repo HEAD・pin・patch・各 hash | [pipeline.py:2649](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2649)、[pipeline.py:2694](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2694) |
| §2.3 opt-in と保全失敗の扱い | [pipeline.py:2203](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2203)、[pipeline.py:2729](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2729) |
| §2.4 evidence が None のときの null | [pipeline.py:2653](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2653)、[pipeline.py:2705](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2705) |
| §2.5 判定・fan-out 等の維持 | outcome の保全専用 field と finally の変更に限定：[pipeline.py:490](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:490)、[pipeline.py:2201](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/campaign/pipeline.py:2201) |
| §3 `test_inventory_records_r1_inputs` | [test file:75](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:75) |
| §3 `test_r1_argv_null_without_witness` | [test file:106](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:106) |
| §3 `test_unset_env_unchanged` 拡張 | [test file:225](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:225) |
| §3 `test_r1_input_failure_retains_original` | [test file:117](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-unit-a/orchestrator/tests/test_t2853_trace_preservation.py:117) |

裁定との差異はありません。

## 変異の位置

以下のアンカーは、現行 `pipeline.py` 内でそれぞれ **1 回**現れることを静的に確認しました。「赤」は未実走の予測です。

| ID | 置換アンカー → 置換後 | 赤を期待する test・assert |
|---|---|---|
| M1 | `tdir, "--json", "--expected-commits", str(commit_count_witness),` → `tdir, "--json",` | `test_inventory_records_r1_inputs`、argv 全体の assert（93 行） |
| M2 | `"--protocol", genome.protocol, "--ccbench-root", evidence.source_root,` → `"--protocol", genome.protocol, "--ccbench-root", tdir,` | 同 test、argv 全体の assert（93 行） |
| M3 | `if commit_count_witness is not None:` → `if True:` | `test_r1_argv_null_without_witness`、null の assert（110 行） |
| M4 | `["git", "-C", repo_root, "rev-parse", "HEAD"],` → `["git", "-C", evidence.source_root, "rev-parse", "HEAD"],` | `test_inventory_records_r1_inputs`、repo HEAD の assert（94 行）。両 HEAD の相違も fixture で確認 |
| M5 | `inventory["ccbench_pin"] = evidence.ccbench_commit` → `inventory["ccbench_pin"] = None` | `test_inventory_records_r1_inputs`、pin の assert（95 行）。null-witness test の他項目 assert も赤になり得る |
| M6 | `).stdout` の直後の `inventory["patch_sha256"] = hashlib.sha256(patch).hexdigest()` → 間に `patch = b""` を挿入 | `test_inventory_records_r1_inputs`、復元 bytes・sha・長さの単一 assert（98 行） |
| M7 | `for path in sorted(verifier_root.glob("*.py"))` → `for path in sorted(verifier_root.glob("*.py"))[1:]` | 同 test、module hash 辞書の assert（101 行） |
| M8 | `archive_root = os.environ.get("IZANAGI_TRACE_ARCHIVE_ROOT")` → 同行の直後に `hashlib.sha256((Path(__file__).resolve().parents[1] / "verifier" / "__init__.py").read_bytes())` を挿入 | `test_unset_env_unchanged`、`r1_reads` の assert（259 行） |
| M9 | `except Exception as exc:` に続く `preserved = False` → `except OSError as exc:` に続く `preserved = False` | `test_r1_input_failure_retains_original`、結果比較の assert（131 行） |
| C0 | `Archive one local repetition; failures propagate to the cleanup boundary.` → `Archive one local repetition; archival failures reach the cleanup boundary.` | 緑を期待 |

## 現行の受理・拒否挙動

検証関数の判定条件、verifier の呼び方、`EvalResult` への投影は変更していません。追加した witness field は inventory 作成時だけ参照します。保全時の例外は従来の finally の境界で捕捉され、原本を残します。このため、評価結果・元の例外・WAL を変えない設計です。**同一性の実走確認は親の test 待ち**です。

## 波及

静的検索では `_preserve_trace_directory` の caller は本体の finally と同 test file の直接呼出しだけでした。追加引数は既定値付きです。`_execute_verification_repetition` の戻り値を使う所有外箇所は `test_campaign.py`、`test_verify_fanout.py`、`test_layer3_report.py` にあり、既存 field は維持しています。共有 fixture と consumer test は編集していません。

## 実走

`python3 -m py_compile` は両 file で成功しました。置換アンカーの出現回数と、変更 file が所有 path の 2 件だけであることも静的確認済みです。pytest、変異 probe、C0 対照は**実装済み・未実走**です。

## 総括

R1 入力の記録と指定 test を追加しました。追加行数は裁定の上限内です。実行による受入判定は親の計算ノード実走に残ります。