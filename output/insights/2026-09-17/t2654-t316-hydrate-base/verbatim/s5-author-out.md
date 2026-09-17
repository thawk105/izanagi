## 実装した変更 (file:line と要旨)

所有 3 ファイルのみ変更しました。commit・docs 編集・PBS 操作はしていません。

- [probe.py:1826](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2654-impl/tools/pegasus/probes/t316_sandbox_backend_probe.py:1826)：source override を staging に変更。outside の依存 install 後に実 prepare を接続し、失敗記録と関門前の再判定を追加。
- 同ファイル :2048／:2101：scratch の兄弟 staging、実 hydrate CLI、失敗時の停止、staging 側 identity、readonly bind、観測 2 key を追加。
- [probe.pbs:54](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2654-impl/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54) と Python :2474：束縛を同じ 9 path に拡張。
- [test.py:1738](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2654-impl/orchestrator/tests/test_t316_sandbox_probe.py:1738)：独立 literal 同期検査、追加入力の dirty 拒否。
- 同ファイル :1805／:1989／:2160：5 Git repo・実 hydrate・実 FetchContent・package config・masstree OUTPUT 2 本の fixture、inline assert、指定の正常／失敗系テストを追加。

## 現行の受理・拒否挙動 (scope 前) と変更後の差

変更前は永続 cache を identity／configure が直接参照し、masstree 生成物の残留に依存し得ました。変更後は hydrate した S を prepare して供給します。したがって、元の cache 状態から見た到達集合は変わります。

関門の判定規則は維持しています。`verdict_s6`、`_require_condition_gate`、`_condition_gate_family_valid`、`_INERT_CONDITION_GATE_PAIRS` は変更前との AST 一致を確認しました。hydrate 失敗は `S6_SOURCE_IDENTITY_INVALID`、prepare 失敗は `S6_CONDITION_GATE_UNPROVEN` を期待するテストを追加しています。

## 実走した test (nodeid・範囲・結果) と実走不能の node

**pytest 実走は 0 件です。実装済み・未実走です。**

- 指定ファイル全体の `pytest -q -x -p no:cacheprovider`：PreToolUse hook が起動前に拒否。
- 既存 runner：local 実行へ進まず dispatch に分岐。投入を拒否する callback で rc=16 に停止しました。
- `bash -n`：同 hook が拒否。
- 実施できた静的検査：Python 3.10 AST 構文、保護対象 AST 一致、束縛 9 件一致、既存関門順序 assertion の静的照合、`git diff --check`。すべて通過。

未実走範囲は `orchestrator/tests/test_t316_sandbox_probe.py::*` 全体です。特に次を親で再走してください。

- `test_s6_live_offline_source_paths_and_prepare_order`
- `test_s6_live_staging_is_readonly_outside_scratch`
- `test_s6_hydrate_failure_stops_before_identity_and_gate`
- `test_s6_prepare_failure_stops_before_gate[configure|target]`
- `test_execution_binding_*`
- `test_condition_gate_dominates_ccbench_configure`
- 既存 S6 live／identity／cleanup／TMPDIR 各 test

node 起動前に停止したため、今回確認した `NETLINK_ROUTE` 由来の失敗 node はありません。

## 所有外 caller・共有 fixture・consumer test への波及 (静的列挙)

- `_execute_ccbench_build` の所有外 caller は検索で検出しませんでした。
- `buildcache.py`、hydrate CLI、policy、共有 fixture、`conftest.py` は変更していません。
- `bound_bytes` は 9 件、shell dirty gate は 22 parameter node、新規 Python dirty 拒否は 4 node。
- consumer 再確認対象：`test_official_perf_closure.py`、`test_hooks.py`、`test_acceptance_schedule_order.py`、`test_real_repo_serialization.py`、`test_ccbench_spawn_sites.py`、`test_plain_runner_coverage.py`。いずれも未実走。
- 新しい spawn 台帳登録は追加していません。旧受領証への変更もありません。

## 変異 M0〜M12 の anchor 候補 (old 行の逐語)

以下は**変異前の現実装**にある anchor です。KILL／SURVIVED は未実測です。

| ID | old 行 |
|---|---|
| M0 | `# A later writable scratch bind must never cover the requested source.` |
| M1 | `f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={staging_root / 'masstree'}",` |
| M2 | `if not inside and failure_stage is None:` |
| M3 | `("ccbench-configure", configure, 300),` |
| M4 | `prefix="t316-s6-thirdparty-", dir=scratch.resolve(strict=True).parent,` |
| M5 | `(*profile.readonly_roots, requested_root, staging_root), runner=profile.runner,` |
| M6 | `"tools/pegasus/fetch_third_party.py",` |
| M6b | `  orchestrator/campaign/buildcache.py`（PBS） |
| M7 | `if command.get("rc") != 0 or command.get("timed_out"):` と `failure_stage = "third-party-hydrate"` |
| M7b | `if command.get("rc") != 0 or command.get("timed_out"):` |
| M8 | `if not inside and failure_stage is None:` |
| M9 | `f"-DCMAKE_PREFIX_PATH={prefix}",` |
| M10 | `if failure_stage is None:`（:1945、直後が関門呼出し） |
| M11 | `dependency_prefix=str(prefix),` |
| M12 | `else (source if name == "ccbench" else staging_root / name),` |

M2 は prepare block をスキップする置換、M7 は rc 拒否と JSON 例外時の failure 設定の両方を外す置換を想定しています。M1／M3／M12 の cache 参照は、改名で消えた `cache_root` を使わず環境変数から構成し、`NameError` による別理由の赤を避けてください。

## 未完・限界

実 hydrate・prepare・bwrap、変異 matrix、計算ノード受入は未確認です。最初の赤理由への帰属も親での実測が必要です。

prepare 固有の configure 抑制条件の差、manifest の timeout 不在、prepare の子孫停止、強制終了時の staging 撤去は保証しません。S6 全体の厳密な deadline 保証も追加していません。

## 総括

親の段 6 では、焦点全件と consumer、変異の最初の赤理由を確認してください。
確定 commit 後、束縛 9 path の HEAD blob 一致と計算ノード実経路の S6 到達・新観測を確認してください。
実装差分は所有 3 ファイルに限定済みですが、実走の緑はまだありません。