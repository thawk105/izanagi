所見は 1 件です。pytest は実行しておらず、以下はコード逐語による静的判定です。

## 所見 1 — M1 は比較偽装へ到達する前に `str` subclass で赤くなる

- 種別: 偽 kill
- 根拠: [test_s1_known_axes_freeze.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:172) では、単一 node の走査順が逐語で次の通りです。

  ```python
  NameSubclass("g_none"),
  EqualToCanonicalName(),
  ```

  同じ node 内で順番に `pytest.raises` しているため、[同ファイル:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:180) のループは最初の未拒否ケースで停止します。

  M1 で [s1_known_axes_freeze.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:142) の

  ```python
  if type(name) is not str:
      reject()
  ```

  を削除すると、`NameSubclass("g_none")` は membership と mask 0 比較を通過します。したがって node はここで赤くなり、行 178 の `EqualToCanonicalName()` は実行されません。
- 発火シナリオ: M1 を投入 → `test_trigger_name_mask_binding_rejects_invalid_names` は赤くなるが、事前登録した「`__eq__` / `__hash__` 比較偽装による kill」ではなく、先行する `str` subclass の受理が理由。比較偽装 kill の実在を証明していない。
- 重大度: must-fix
- 提案: `EqualToCanonicalName` を専用 test node に分離する。残る無効名も `pytest.mark.parametrize(..., ids=...)` で各ケースを独立 node にする。

## M1〜M7 の静的 kill 対応

| 変異 | 静的に赤となる test node | 判定 |
|---|---|---|
| M1 | `test_trigger_name_mask_binding_rejects_invalid_names` | 変異は死ぬが、比較偽装より前の subclass で停止する偽 kill |
| M2 | `test_trigger_entries_rejects_coordinated_canonical_name_mask_tamper`、`test_validate_schema_rejects_coordinated_canonical_name_mask_tamper` | genuine。helper の先頭 `return` により両 node の `pytest.raises` が成立しない |
| M3 | `test_validate_schema_rejects_coordinated_canonical_name_mask_tamper` | genuine。正準 mask 0 への改竄なので前段 membership は拒否理由にならない |
| M4 | `test_trigger_entries_rejects_coordinated_canonical_name_mask_tamper` | genuine。main/remeasure は同じ mock provenance から取得され、equality では落ちない |
| M5 | `test_current_six_frozen_trigger_predicates_pass_semantic_membership` | genuine。alias 登録を消すと最初の `ident_all` record が過剰拒否される |
| M6 | `test_trigger_name_mask_binding_accepts_all_32_masks` | genuine。mask 0 の `g_none` が最初に過剰拒否される |
| M7 | `test_mask_for_canonical_predicate_recovers_all_32_masks[space/tab/crlf/vertical-tab/form-feed/nbsp/ideographic-space]` | genuine。逆順化すると最初の mask 0 が 31 と復元される |

M2〜M4 の負例は完全診断ではなく安定断片だけを検査しています（[生成層:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:263)、[schema 層:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:302)）。完全診断は専用 test に分離されています。

実装本体については、`reject()` が必ず `raise FreezeError` し、exact-type → membership → mask 比較の制御継続穴は見つかりませんでした。mask 0、全 32 mask、mask 31 の両名、外側 whitespace、欠落・`None`・bytes・subclass・比較偽装もコード上は拒否／受理契約どおりです。テスト差分は追加のみで、既存期待値の反転・緩和・skip・削除や fixture/hash の変更もありません。

## 総括

**NO-GO**。  
M2〜M7 に変異生存は見つからない。  
ただし M1 は登録した比較偽装ではなく先行 subclass で赤くなる偽 kill である。  
比較偽装を独立 node に分離してから land 判定すべき。