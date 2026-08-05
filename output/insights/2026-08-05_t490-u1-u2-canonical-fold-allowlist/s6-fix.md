実装済み・未実走です。計算ノードへの dispatch が失敗したため、両所見とも `partial` とします。

| 所見 | 状態 | 対応 |
|---|---|---|
| FIX-1 | `partial` | `_require_g13()` の toolchain 不在を `pytest.fail` から `pytest.skip` に変更 |
| FIX-2 | `partial` | producer 変更後に consumer を別名で fresh importし、7 個目が checkout 前に `DriverError` となる独立 node を追加 |

変更箇所は [test_s1_direct_comparison.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:193) のみです。

追加・変更した node id:

- `orchestrator/tests/test_s1_direct_comparison.py::test_real_source_digest_unifies_all_outer_whitespace_tokens`
- `orchestrator/tests/test_s1_direct_comparison.py::test_fresh_prepare_rejects_configuration_added_only_to_producer_domain`

検査結果:

- `python3 -m py_compile orchestrator/tests/test_s1_direct_comparison.py`: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 違反なし
- 対象ファイル全体の pytest dispatch: rc=16、`qstat -Q preflight rc=1`。実行 node は 0 件
- `--collect-only` は Pegasus ログインノードで pytest を走らせない規律のため未実施

波及可能性の静的確認:

- production caller は S1 本体、`s8b_materialization`、`s8b_floor_campaign`、`s8b_oracle_driver`。production は今回変更していません。
- consumer test は主に `test_s8b_materialization.py`、`test_s8b_floor_campaign.py`、`test_s8b_oracle_driver.py`。production 無変更のため直接的な挙動変更はありません。
- fresh import node は共有 `s1_measurement_freeze.CONFIGURATIONS` と `patchharness.checkout` を monkeypatch しますが、pytest が復元し、別名 module も `finally` で `sys.modules` から除去します。
- 既存 wave 差分にある `orchestrator/campaign/` の 3 ファイル、docs、output、凍結成果物は今回編集していません。commit・add 等も行っていません。

## 総括

- FIX-1: `partial`（実装済み・未実走）
- FIX-2: `partial`（実装済み・未実走）
- `regressed` は 0 件です。
- production コードと既存の pre-wave テスト期待値は変更していません。
- 計算ノードで上記 2 node、続いて対象ファイル全体を再走すれば close 判定できます。