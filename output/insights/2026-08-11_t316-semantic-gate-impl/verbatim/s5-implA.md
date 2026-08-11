変更前はこの層に効果 scanner がなく、対象 token・loop・malformed input を拒否する挙動はありませんでした。変更後は指定 deny category、明示的な無条件 loop、malformed input のみ fail-closed で拒否し、必須正例は受理する設計です。

編集は所有範囲の新規 2 ファイルだけです。docs 編集・commit はしていません。

## 総括

- 実装:
  - [coder_effect_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py): 公開 deny table、重複 assert、C++ lexer、無条件 loop 検出、bytes 非反射 finding、malformed fail-closed。
  - [test_coder_effect_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py): 攻撃 4 種、category 別 mutation-killing probe、偽陽性、全必須正例、malformed、rule ID、保守的拒否を網羅。
- 検査:
  - Python 構文検査と whitespace 検査は成功。
  - `test_coder_effect_gate.py` 単体、および同ファイル＋`test_plain_runner_coverage.py`＋`test_pytest_collection_config.py` を `tools/run_tests.py` 経由で投入したが、いずれも開始前に `qstat -Q preflight rc=1`、最終確認では `NQSconnect ... Can't create socket`。実行 nodeid は 0 件。**実装済み・未実走であり、緑は主張しない。**
- 波及可能性:
  - 単位 B の `p3_s4_loop.quarantine()` caller、sort/trigger driver、S6/S8a sweep、direct comparison、calibration。
  - 共有正例 `CANDIDATES`、`_NOSORT_IMPL`、`emit_predicate()` の変更時。
  - 将来の WAL・critic・provenance consumer は disclosure-free finding schemaへの対応が必要。
- 残余・未実装:
  - 単位 B の配線、WAL/critic 統合、consumer tests は未実装。
  - `close`/`fsync`、`File(...)` 間接効果、`2 - 1`、token-pasting、事前取得済み function pointer、deny table 外 extension は残余。
  - host-security boundary ではなく、測定済み 4 注入への defense-in-depth。`while (true) { break; }` は意図的に保守的拒否。