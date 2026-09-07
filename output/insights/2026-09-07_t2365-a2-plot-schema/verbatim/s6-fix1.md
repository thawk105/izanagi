## 総括

敵対レビュー A の must-fix 1〜4 をすべて閉じました。  
[対象テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-a/orchestrator/tests/test_plot_a2_certification.py) のみを実変更しています。  
自走 harness は全 60 case が pass、対象の最小変異 10 件はすべて対応 node の赤を実測しました。  
production 実装への一時変異はすべて復元済みです。

## 所見ごとの対応

1. current CLI の pin 表

   - nodeid: `::test_current_cli_reads_repository_owned_pin_table`
   - `main()` を kwargs なしで通し、監視可能な pin 表が実際に参照されること、正しい pin で成功し poisoned pin で拒否されることを検査。
   - current の実 hash を `expected_hashes` に自己設定する変異で、pin 表参照 assertion が実際に赤。

2. WAL の二つの token authority

   - nodeid: `::test_current_rejects_wal_build_start_payload_src_token_mismatch`
   - nodeid: `::test_current_rejects_wal_build_admission_source_src_token_mismatch`
   - helper を分離し、各 authority だけを変更。
   - 対応する tuple 要素を一つずつ削除する二変異で、それぞれ `DID NOT RAISE` の赤を確認。

3. current の拒否枝

   - `::test_current_rejects_legacy_raw_cell_schema` — current で raw v2 を許す変異を殺害。
   - `::test_current_rejects_embedded_policy_protocol_identity_mismatch` — policy protocol equality 削除を殺害。
   - `::test_current_rejects_duplicate_wal_build_start_mapping` — build-start 一意性削除を殺害。
   - `::test_current_rejects_policy_mismatched_workload_condition` — policy workload 条件比較削除を殺害。
   - `::test_current_rejects_noncanonical_campaign_claim_path` — canonical claim path 比較削除を殺害。
   - `::test_current_rejects_symlinked_campaign_claim_path` — symlink 拒否削除を殺害。
   - 全六変異で対応 node の実際の赤を確認。

4. caption の過剰主張

   - nodeid: `::test_current_gate_copy_is_receipt_observation_not_legacy_fixed_copy`
   - 禁止語列挙ではなく、受領証から導ける gate 文との完全一致と caption 内の完全な埋め込みを検査。
   - `D1198 was executed successfully.` を追加する変異で完全一致 assertion の赤を確認。

## 実走した検査

- `PYTHONPATH=. MPLCONFIGDIR=/tmp python3` の自走 harness:
  - 対象 10 node: `10 passed`
  - test file 全体: `60 passed, 0 skipped, 0 failed`
- 最小変異: `10/10` で対応 node の赤を確認。
- `git diff --check`: pass。
- 通常の pytest 経路は指示どおり使用していません。

## 所有外への波及

- `tools/plotting/plot_a2_certification.py` は変異確認中のみ一時編集し、すべて復元しました。
- producer、policy、別所有 test、docs は編集していません。
- 指定された凍結 output・figures・results への差分はありません。
- `git add`、commit は実施していません。

## 未了・申し送り

未了なし。親側でそのまま統合・正式検査へ進められます。