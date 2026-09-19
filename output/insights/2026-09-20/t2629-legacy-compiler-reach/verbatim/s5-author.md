## 検査

- login 実走：`pegasus02`、Python 3.10.12、rc=0。
- `py_compile`：rc=0。
- [実走 JSON](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2629-unit-probe/probe-t2629-selfrun/probe.json) を保存しました。
- meta-test は静的確認のみ。`tools/` 直下の新規ファイル全般に一覧・命名・shebang・provenance を要求する検査は見つかりませんでした。`test_hooks.py::test_bash_pegasus_execution_inventory_is_synchronized` は `tools/pegasus/` 限定なので対象外です。確認範囲で、この追加による失敗は特定していません。

## 総括

作成：[tools/t2629_legacy_compiler_reach_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2629-unit-probe/tools/t2629_legacy_compiler_reach_probe.py)、**147 行**。関数は `record`、`command_line`、`environment`、`main`。add・commit は行っていません。

| 項目 | observed / exception |
|---|---|
| `env` | dict：`PEGASUS_LOGIN`、site・既定とも `gcc-13/g++-13`、両 compiler 不在 |
| `authorization_linux_baremetal` | dict：guard 通過、mode=`none` |
| `authorization_pegasus` | dict：guard 通過、mode=`required` |
| `evidence_site_cxx` | `RuntimeError`：`g++-13` のマクロ照会を起動できない |
| `evidence_default_cxx` | `"same-as-site"` |
| `legacy_build_trace` | `SkippedNoEvidence` |
| `limitations` | list：限界を記録 |

`STOCK_G` は `p3_kickoff.py:54` の `_BASE` を逐語複製し、`Genome("silo", {**_BASE, "BACK_OFF": 1})` で構築しました。同モジュールは import せず、commit は `pin.CURRENT_PIN` を使用しています。

未実走は admission 導出・build 本体と compute 実走です。今回、cmake configure や heavy-work gate の拒否は観測していません。WAL abort 変換、cache-hit、compiler 間 evidence 不一致も未測定です。認可通過は full attestation 成功を意味せず、compiler 不在の観測は当該 node・日時・PATH に限定されます。