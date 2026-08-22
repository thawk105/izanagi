実装完了。commit は作成していません。

- `_validate_floor_inputs` に必須 `head` 引数を追加。
- captured HEAD の `floor_protocol.json` blob と working tree bytes を byte-exact 比較。
- 不一致時は parse・schedule・candidate 書込み前に `FreezeError`。
- 未 commit `master_seed` 変更の負例テストを追加。既存正例も確認。

変更箇所:

- `s8b_holdout_freeze.py:1348`
- `s8b_holdout_freeze.py:1362`
- `s8b_holdout_freeze.py:1723`
- `test_s8b_holdout_freeze.py:1673`
- `test_s8b_holdout_freeze.py:1762`

変更前は、HEAD blob と一致しなくても、working tree protocol 自体と関連 artifact の内部整合性を満たせば受理していました。変更後は captured HEAD blob と完全一致する場合のみ受理します。

実走結果:

- `test_v2_candidate_rejects_worktree_only_floor_protocol_master_seed_mutation`: passed
- `test_v2_candidate_build_and_generate_synthetic_g1`: passed
- ファイル全体: `121 passed, 2 skipped`

`_validate_floor_inputs` の直接 caller は `build_v2_g1_candidate` のみ。CLI は `generate_v2_g1_candidate` 経由で影響を受けます。既存の `_blob_at_head` 利用箇所と全 candidate 関連テストは確認済みです。`check_codex_agents` は成功、`check_docs` は違反なし（既存警告2件）でした。

## 総括

指定2ファイルのみ変更。未 commit。working-tree-only protocol mutation は拒否され、正当な commit 後の成功経路は維持されています。