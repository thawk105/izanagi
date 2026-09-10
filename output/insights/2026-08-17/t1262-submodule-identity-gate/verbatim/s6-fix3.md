## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| H1 | partial | relocation fixture の全 submodule を detached HEAD 化してから seal。strict preflight は維持。未実走 |
| H2 | partial | end-to-end 2 node のみ containment に戻し、helper 直呼びの exact equality は維持。未実走 |
| H3 | partial | HEAD 解決失敗を構造化拒否理由へ変換。rank 1 は封緘済み fixture と exact equality を使用。未実走 |

regressed と判断した所見はありません。ただし実走不能のため closed とは申告しません。

## 変更内容

- [tools/codex_reasoning_ab.py:1004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1004)
  - `rev-parse HEAD` を非例外 probe にし、失敗時は `initialized submodule HEAD cannot be resolved: <path>` で拒否。
  - production を緩めていない根拠: 従来の例外終了を同じ拒否方向の構造化理由へ変えただけで、受理経路は追加していない。

- [test_codex_reasoning_ab.py:1647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:1647)
  - relocation fixture の submodule を detached HEAD 化し、全 repository を seal。
  - production を緩めていない根拠: builder transport 許可は fixture の封緘前列挙だけで、production の relocation preflight は strict のまま。

- [test_codex_reasoning_ab.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:1932)
  - nested fixture に opt-in の `seal=True` を追加。
  - production を緩めていない根拠: test-only 変更であり、既存 pre-seal 正例の既定挙動も維持。

- [test_codex_reasoning_ab.py:2224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:2224)
  - end-to-end 用 containment helper を追加。
  - production を緩めていない根拠: helper 直呼びの exact equality は変更せず、production 検査にも変更なし。

- [test_codex_reasoning_ab.py:2275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:2275)
  - 空 index の end-to-end node を containment 化し、`git fsck` と unreachable object の併記をコメント化。

- [test_codex_reasoning_ab.py:3006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:3006)
  - 中間 symlink の end-to-end node を containment 化し、filesystem allowlist の extra files 併記をコメント化。

- [test_codex_reasoning_ab.py:3818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:3818)
  - rank 1 を封緘済み fixture に変更し、helper 直呼びとして exact reasons equality を固定。
  - production を緩めていない根拠: test fixture と期待診断を厳格化しただけ。

## 追加・変更したテスト

- `test_uninitialized_nested_submodule_gitlink_pin_rejects_change`
- `test_submodule_inventory_rejects_initialized_submodule_with_unresolvable_head`（追加）
- `test_shared_base_copy_preserves_metadata_and_relocates_submodules`
- `test_snapshot_relocation_preflight_rejects_absolute_gitdir[deps/child]`
- `test_snapshot_relocation_preflight_rejects_absolute_gitdir[deps/child/third_party/grandchild]`
- `test_snapshot_relocation_preflight_rejects_absolute_core_worktree[deps/child]`
- `test_snapshot_relocation_preflight_rejects_absolute_core_worktree[deps/child/third_party/grandchild]`
- `test_derived_preflight_rejects_path_dependent_absolute_core_worktree`
- `test_verify_snapshot_submodule_content_gate_rejects_empty_index_and_worktree`
- `test_verify_snapshot_submodule_content_gate_rejects_intermediate_directory_symlink`

単一理由性を維持した helper node:

- `test_submodule_content_identity_reasons_rejects_empty_index_and_worktree`
- `test_submodule_content_identity_reasons_rejects_intermediate_directory_symlink`

## 実走結果

実装済み・未実走です。

- 焦点 12 selector: `tools/run_tests.py` が dispatch 前の `qstat -Q` で基盤失敗、`rc=16`
- collect-only: 同じ基盤失敗、`rc=16`
- queue state: ENA/STS とも観測不能
- Python AST 構文検査: 成功
- `git diff --check`: 成功
- 変更ファイル: 指定された 2 file のみ

## 波及と残件

- 親の計算ノード走で、残り 9 node、新設 HEAD 不在 node、焦点集合全体の確認が必要です。
- `includeif.*` は引き続き禁止で、絶対 `core.worktree` と分離した単独 node を維持しています。
- G1 の transport 許可は封緘前だけで、封緘後・relocation・内容同一性経路は strict のままです。
- RA3、oracle schema、docs、commit には触れていません。
- F1〜F10、G1〜G4について静的な後退は見つかりませんでしたが、実測による確定は親に残ります。

## 総括

H1〜H3 の実装修正は完了しました。  
production の拒否条件は緩めず、HEAD 不在の診断だけを構造化しました。  
end-to-end と helper 直呼びの理由契約を裁定どおり分離しました。  
Pegasus 基盤が `rc=16` のため、状態は partial・実装済み未実走です。