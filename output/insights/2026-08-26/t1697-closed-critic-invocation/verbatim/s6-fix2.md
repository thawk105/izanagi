実装済みです。pytest は指示どおり実行していないため、緑とは報告しません。

## 総括

- [_CERTIFIED_RUNNER](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/campaign/p3_b4_closed_critic.py:84) を追加し、certified 判定と実際の runner の両方が呼出し時の module 属性を参照するよう修正。
- 固定名 `claude` の PATH 解決は維持し、狭い `_CERTIFIED_WHICH` seam に変更。
- [共有 fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/tests/test_p3_b4_closed_critic.py:227) は同じ fake を `_CERTIFIED_RUNNER` と `runner=` に設定。大域 `subprocess.run` が無傷であることも検査。
- [M5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/tests/test_p3_b4_closed_critic.py:460) は seam が fake A、引数が fake B の負例へ変更。旧エラー文言には依存しません。

置き換えた大域 patch は全 5 箇所です。

| 元の箇所 | 件数 | 置換後 |
|---|---:|---|
| 共有 fixture の `C.subprocess.run` | 1 | `C._CERTIFIED_RUNNER` |
| M5 の `C.subprocess.run` | 1 | `C._CERTIFIED_RUNNER` |
| 共有 fixture の `C.shutil.which` | 1 | `C._CERTIFIED_WHICH` |
| M5 正例の `C.shutil.which` | 1 | `C._CERTIFIED_WHICH` |
| M5 負例の `C.shutil.which` | 1 | 同じ M5 seam context に統合 |

残った `patch.object` は 7 箇所です。

- `C.exploration_campaign_layout`
- `C._CERTIFIED_WHICH` 2 箇所
- `C._CERTIFIED_RUNNER` 2 箇所
- `C._write_exclusive_json`
- `C.assert_b4_arm_pair`

共有モジュール `C.subprocess` または `C.shutil` を対象にした patch は 0 箇所です。

| 赤だった test | 対応 |
|---|---|
| `test_m17_pair_id_accepts_one_factory_and_rejects_mixed_factories_only` | closed |
| `test_unregistered_pair_control_rejects_reused_provider_identity` | closed |
| `test_unregistered_pair_control_rejects_reused_session_after_byte_recheck` | closed |
| `test_r1_terminal_pair_revalidation_rejects_status_and_payload_byte_tamper` | closed |
| `test_p4_certified_pair_reports_precursor_differences_without_rejecting_them` | closed |
| `test_m19_pair_gate_accepts_terminal_paths_and_rejects_promoted_dataclasses` | closed |
| `test_m16_sent_on_off_payload_bytes_match_independent_admitted_view_digests` | closed |
| `test_m18_certified_fixed_claude_resolution_ignores_caller_executable_decoy` | closed |

partial は 0 件、regressed は 0 件です。2 ファイルの構文解析は成功しました。pytest は計算ノード未 dispatch のため未実走です。変更禁止の `contract_loader_binding.py` には触れていません。作業ツリーにある `test_p3_s4_loop.py` の既存変更にも触れておらず、commit、add、stash、branch 操作は行っていません。