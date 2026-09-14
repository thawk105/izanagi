## 変更した内容

- [probe](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl/tools/pegasus/probes/t316_sandbox_backend_probe.py:1968) の1968–1974行：拒否直前に supply／meaning の `.get("detail")` を stderr へ出力。欠落・None・空は `<no detail>` と表示します。
- [test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2519-impl/orchestrator/tests/test_t316_sandbox_probe.py:43) の43–85行：実 CMake と `_require_condition_gate` を通し、rc・stderr・argv、detail 欠落表示、stdout 無出力、従来の `RuntimeError` を検査する正例を追加しました。

既存期待値、共有 fixture、gate 本体、docs は変更していません。commit もしていません。

## 受理・拒否挙動の変化

変更ありません。変更前後とも admission が偽なら同じ `RuntimeError` で拒否し、真なら従来の tuple を返します。inert の2契約 exact 一致、receipt summary、`SCHEMA_VERSION` は維持しています。

## 実走結果

試行：

```bash
PYTHONPATH=. python3 tools/run_tests.py orchestrator/tests/test_t316_sandbox_probe.py -n 0
```

**rc=16、テスト未開始**。runner 内部が禁止対象の `qstat -Q` preflight を試み、rc=1 で失敗しました。この点は指示からの逸脱です。再試行していません。

構造メタテストは自走 harness で実走しました：

```bash
PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py
```

**rc=0、次の3 node が成功**（接頭辞 `orchestrator/tests/test_plain_runner_coverage.py::`）：

- `test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_every_test_file_is_self_runnable_or_allowlisted`
- `test_this_metatest_is_itself_self_runnable`

`git diff --check` は rc=0 です。

## 波及可能性の静的列挙

- caller：`observe_s6` → `_execute_ccbench_build` → `_require_condition_gate`。拒否時の job stderr が増えます。
- import test：検索で確認した直接 import は `test_t316_sandbox_probe.py`。既存の S6、receipt、execution binding テストが関連します。
- 共有 fixture：`fixtures/condition_meaning_gate/supplied`。追加テストは一時コピーだけを変更します。
- BOUND_PATHS：PBS の dirty 検査・live／commit blob の SHA-256 比較、および Python の `_execution_binding` が関連します。probe の bytes が変わるため、再計測には親による新 commit の束縛が必要です。
- その他の検査経路：`test_hooks.py`、`test_official_perf_closure.py` の probe 登録・静的検査、`test_pytest_collection_config.py` の収集契約。これらは未実走です。

## 総括

**実装済み・機能テスト未実走**です。構造メタテスト3件のみ成功しており、closed とは申告しません。追加正例と既存 consumer テストの実走は親へ引き継ぎます。