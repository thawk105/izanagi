## 総括

2 件とも実装済みです。変更は指定された 2 ファイルだけで、docs・`__init__.py`・他 lane のファイルは未変更、commit / add も行っていません。

- [approval_payload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-fix2e/orchestrator/preregistration/approval_payload.py:69)
  - level-2 見出し境界で先頭空白 0〜3 を認識。
  - canonical D282 見出し自体は従来どおり空白なしに限定し、受理集合を拡大していません。
  - 例外に機械可読な `ApprovalPayloadRejectionReason` と `reason` 属性を追加。
- [test_t139_approval_payload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-fix2e/orchestrator/tests/test_t139_approval_payload.py:96)
  - 指定された負例 14 node すべてで診断文ではなく enum reason を明示 assert。
  - approved role 3 node も reason assert 化。
  - 先頭空白 1〜3 の `## D999` 後に攻撃者 fence を置くレビュー C の負例を追加。
  - 空白付き D282 が引き続き拒否される負例も追加。

### 検査結果

`tools/run_tests.py orchestrator/tests/test_t139_approval_payload.py -q` は dispatch preflight 障害で `rc=16`。契約どおり素の pytest へ切り替えました。

- `python3 -m pytest orchestrator/tests/test_t139_approval_payload.py -q`
  - 対象範囲: 同ファイルの全 25 nodeid
  - 結果: `25 passed in 0.87s`
- `python3 -m pytest orchestrator/tests/test_plain_runner_coverage.py -q`
  - `test_every_test_file_is_self_runnable_or_allowlisted`
  - `test_allowlist_has_no_stale_or_self_runnable_entries`
  - `test_this_metatest_is_itself_self_runnable`
  - 結果: `3 passed in 0.31s`
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- `git diff --check`: rc=0

対象走に残る赤はありません。全 repository 受入と mutation harness は親担当のため未実走です。

### guard 削除時に赤くなる nodeid

| 検査 | nodeid |
|---|---|
| 見出し一意性 | `test_missing_d282_heading_is_rejected_without_unicode_normalization`, `test_duplicate_d282_heading_is_rejected` |
| fence 一意性 | `test_missing_target_fence_is_rejected`, `test_duplicate_target_fence_is_rejected` |
| fence 入れ子・delimiter 不一致 | `test_nested_fence_is_rejected`, `test_mismatched_fence_delimiter_length_is_rejected` |
| top-level 未知 key | `test_unknown_top_level_key_is_rejected` |
| top-level 欠落 key | `test_missing_top_level_key_is_rejected` |
| approved role 数 exact 6 | `test_approved_blob_role_count_not_six_is_rejected` |
| approved 未知 role | `test_unknown_approved_blob_role_is_rejected` |
| approved 重複 role | `test_duplicate_approved_blob_role_is_rejected` |

未知 top-level key、role 数、重複 role などは guard 削除後も後段 guard によって拒否され得ます。したがって受理集合上の単独変異は mask されますが、期待 reason が変わるため上記 node は赤くなり、`first_rejecting_node` を識別できます。これは acceptance-set KILL ではなく diagnostic sensitivity pin です。

残りの指定 14 nodeである top-level 重複、erratum 順序、旧 root の commit key、alpha key 欠落、alpha commit pin、非 UTF-8 も、それぞれ専用 reason を assert しています。

### 波及可能性

静的検索では、所有外に `approval_payload` の caller、共有 fixture、consumer test はありませんでした。将来の直接 caller には `reason` 属性が追加されますが、既存例外階層と診断文字列は維持しています。固定 `F_r` digest、`BlobRef`、`read_pinned_blob`、package export は変更していません。