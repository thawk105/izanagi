実装と pin 同期は完了しました。ただし pytest は infrastructure failure で child が起動せず、`closed` とは申告しません。

### 変更内容

- [reflux_formal_consumer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2353-author/orchestrator/campaign/reflux_formal_consumer.py:35)
  - `STAGE_COMMIT` / `STAGE_ABORT` を import。
  - FC07 の 2 判定を root `kind` から root `stage` へ変更。
  - `_wal_field()`、他の判定式・reason code・gate は未変更。
- [reflux_origin_fixture_builder.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2353-author/orchestrator/tests/reflux_origin_fixture_builder.py:362)
  - terminal を `{variant, stage, env_tag, ts, payload}` へ変更。
  - witness 系 field を payload 内へ移動。
- [test_reflux_formal_consumer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2353-author/orchestrator/tests/test_reflux_formal_consumer.py:843)
  - 旧 root `kind` を拒否する負例と、production commit が `P6Unavailable` へ到達する正例を追加。
  - 既存 terminal と witness 変更箇所を production 形状へ更新。
- [reflux_origin_fixture_baseline.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2353-author/orchestrator/tests/reflux_origin_fixture_baseline.json:15) と [test_reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2353-author/orchestrator/tests/test_reflux_result_evidence.py:24) の pin を同期。

変更前は、production の `stage` commit/abort terminal は root `kind` がないため FC07 で拒否され、旧 root `kind` 合成形状だけが terminal 分岐に一致しました。  
変更後は、production `stage` commit が commit 枝を通って `P6Unavailable` へ到達可能になり、旧 root `kind` は FC07 で拒否される一方、production abort は witness producer 不在のため引き続き FC07 で拒否されます。

### pin 再計算

repo root で `python3 - <<'PY'` を実行し、変更後の `build_ordered_wal_projection()` と `build_result_evidence_record()` を直接生成して canonical JSON bytes、production digest helper、salted commitment を計算しました。

- source WAL: `715` bytes
- source WAL SHA-256: `8f61d1aa41d1340730f96d17bbf78c39edd718dbcd85c4258f071879a2107b83`
- ordered projection: `975` bytes
- ordered projection SHA-256: `271323c60ad2af8b4034872096d5c1c5066f26c6c85689252dd5ce762ddd3bc6`
- result evidence: `1848` bytes
- result evidence SHA-256: `631a5fa04f9cc1a5442c5660410bb27b1ad03ef76f5da3fe3d4603ac5577c82c`
- ledger evidence digest: `631a5fa04f9cc1a5442c5660410bb27b1ad03ef76f5da3fe3d4603ac5577c82c`
- outer salted commitment: `5aaf3851fe1c8b55ee009a35b9f319cc1feee93d45df7a99c68a56da8bba6cf7`
- wrong-domain digest: `515e7f7ca39461903b9d3291dd010b9576732ff2674f1b29e677aba6032399c3`

段 2 / 段 3 の主張と全値一致しました。

### 検証状況

次の新規 nodeid を `tools/run_tests.py` 経由で指定しましたが、`qstat -Q preflight rc=1`、dispatch rc=16、`child_started=false` となりました。

- `test_reflux_formal_consumer.py::test_fc07_rejects_legacy_root_kind_terminal_shape`
- `test_reflux_formal_consumer.py::test_fc07_accepts_production_commit_terminal_shape`

したがって負例の実走確認は未完了です。負例自体は `_assert_reason()` により result と projection の双方が厳密に FC07 であることを要求しており、静的には `_rewrite_wal()` が attempt、source bytes、projection hash、evidence digest を同期するため、FC05B/FC05C/FC06 を越える構成ですが、実走済みとは扱いません。一時変異は使用していません。

指定された 11 test file も同じ wrapper で一括指定しましたが、同じ rc=16 で child 起動前に停止しました。11 file すべて「実装済み・未実走」です。最終観測時の local 安全予算は `201467488` bytes で最低 1 GiB 未満でした。

一方、以下は実走して成功しています。

- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- 変更 Python 4 file の AST parse
- `git diff --check`

test file 集合を exact 列挙する制約 meta-test は検索で見つかりませんでした。`test_pytest_collection_config.py` の glob 検査は file 集合を列挙するものではありません。

### 静的波及範囲

- production caller: `p3_autonomous_workload_trial.py`、`reflux_origin_client.py`、`trial_registry.py`
- consumer test: `test_reflux_formal_consumer.py`、`test_reflux_origin_client.py`、`test_trial_registry.py`
- shared fixture 利用者: origin artifacts、binding、client、topology、source closure、result evidence、P3 trial 各 test
- `test_reflux_originless_compatibility.py` は P3 trial helper 経由の間接利用者

所有外の `test_reflux_origin_binding.py` と `test_reflux_originless_compatibility.py` に差分はありません。

`git status --short` は指定した 5 file の変更だけです。commit、push、branch 操作、docs 編集は行っていません。

## 総括

- 実装済み: terminal の `stage` 判定、production 形状 fixture/test、正負 2 test、実物からの pin 同期。
- 残った赤: 判定なし。pytest child が一度も起動していないため、赤・緑とも未判定です。
- 未完了: 新規 2 nodeid と指定 11-file 範囲の実走、旧 root `kind` 負例が前段を越えて FC07 で落ちることの動的確認。