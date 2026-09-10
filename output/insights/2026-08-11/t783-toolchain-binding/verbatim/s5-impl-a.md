単位 A を実装しました。docs・所有外ファイルは変更せず、commit も作成していません。

- [toolchain_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/toolchain_binding.py) を新設。floor の一意抽出、silo の first-wins 抽出、双方の pure 照合述語を実装しました。version は全文比較です。
- [silo_ladder_rung1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/silo_ladder_rung1.py:38) は `tool_version_body` を re-exportし、既存5条件を silo 用述語へ移しました。
- [test_toolchain_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_toolchain_binding.py) に M01〜M07、M10〜M12相当を追加。silo は独立した旧実装との32通り真偽表比較です。
- `git diff --check` は成功し、変更は所有3ファイルだけです。

テストは指定 runner で新規全node、既存re-export node、`test_plain_runner_coverage.py` meta-testを要求しましたが、実行前に rc=16 で停止しました。原因は sandbox から admission ledgerを更新できず、compute dispatchも `qstat -Q` rc=1だったためです。緑は主張しません。

単位 B 未 land により期待する赤い finding 集合は `{floor gate caller未結線（M01〜M07のE2E未発火）, M08 site compiler解決未結線, M09 buildcache TOCTOU照合未結線}` です。

所有外の直接 import consumer は `tools/pegasus/fetch_third_party.py`、`test_silo_ladder_rung1_driver.py`、`test_silo_ladder_rung1_evidence.py`。将来 caller は単位 B の `s8b_floor_campaign.py` です。

## 総括

- API: `tool_version_body`, `extract_floor_compiler_paths`, `extract_silo_compiler_paths`, `floor_toolchain_matches`, `silo_toolchain_matches`
- 実走: 未実走 — 新規全node・既存re-export node・meta-testはいずれもrunner preflight rc=16
- silo受理集合: `test_silo_predicate_matches_legacy_five_condition_truth_table` の独立32組合せ比較で保証する実装（未実走）
- 期待赤: floor caller未結線、M08、M09
- 波及: `fetch_third_party.py`、silo driver/evidence tests、単位Bのfloor caller