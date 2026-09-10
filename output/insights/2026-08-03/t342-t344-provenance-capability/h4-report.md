## 総括

残り4件はすべて closed です。production gate・completeness 判定は変更せず、テスト fixture／期待定数のみ修正しました。

| 対象 | 状態 | 根本原因 |
|---|---|---|
| `test_comment_reject...` | closed | `STAGE_BUILD_START` の参照に対し、正本 `campaign.model` からの import が漏れていた。 |
| `test_screening_none...` | closed | admission policy 追加後の current campaign ID 定数が古い preimage の値だった。歴史値は維持。 |
| `test_success_consumer...` | closed | fixture が別 module namespace の `BuildRunContext` を生成し、厳密型検査で拒否され `partial` になった。 |
| `test_terminal_events...` | closed | 同じ namespace 二重 import により、fixture context が shared context と認識されなかった。 |

歴史定数と現行定数の対は [test_campaign.py:236–255](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h4/orchestrator/tests/test_campaign.py:236) にあります。旧値は [明示的な旧 preimage 導出](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-h4/orchestrator/tests/test_campaign.py:407) で検証し、current config から導出していません。

実行結果:

- `test_p3_s4_loop.py::test_comment_reject_wal_to_critic_digest_does_not_repeat_payload`: `1 passed`
- `test_campaign.py -k 'campaign_id_binds_admission_policy or screening_search_config_omits_none_and_binds_current_admission_policy or screening_none_keeps_representative_legacy_campaign_ids_unchanged'`: `3 passed, 198 deselected`
- `test_claude_transport.py::test_success_consumer_keeps_valid_receipt_in_journal_and_report`: `1 passed`
- `test_claude_transport.py::test_terminal_events_keep_transport_receipt`: `1 passed`
- `test_p3_s4_loop.py` 全ファイル: `64 passed`
- `test_claude_transport.py` 全ファイル: `43 passed`

未修正・partial の項目はありません。docs、production module、禁止対象、git index/commit/branch は変更していません。編集は3つの test file に未コミットで残しています。