## D-01

- **重大度:** must-fix
- **主張:** value 検査テストの期待文言だけが production の実文言と不一致である。
- **証拠:** production は [`tools/check_ai_provenance.py:567-570`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:567) で `"prohibited character in finding value"`、テストは [`orchestrator/tests/test_check_ai_provenance.py:1776`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1776) で `"prohibited character in value"` を期待する。親の実測 6 件はこの不一致のみ。
- **どの production 変異が検出されないか:** M1〜M6 に未検出はない。ただし M6 の変異結果が、現行ベースの診断不一致による赤と同じ nodeid へ重なる。
- **成果物影響:** 受入テストが 6 件赤のままで、M6 の変異結果を診断上分離できない。
- **推奨対応:** (a) テスト期待値を `"prohibited character in finding value"` へ合わせる。note/value の field 識別要件を満たしており、production 検査は弱めない。

## D-02

- **重大度:** nit
- **主張:** M1〜M6 はすべて、実装後コード上で少なくとも 1 つの実 nodeid に静的到達し、恒真な新設・更新テストは確認できない。
- **証拠:**  
  - M1: `test_malformed_kind_requires_nonblank_note_rc2[empty]`, `[blank]` — [`orchestrator/tests/test_check_ai_provenance.py:1674-1705`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1674)
  - M2: `test_base_finding_kind_is_anchored_after_full_label[duplicate]`, `[none-mixed]`, `[reserved]`, `[model-none]` — [`...:1878-1909`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1878)
  - M3: `test_malformed_known_violation_missing_finding_is_stale_rc2` — [`...:1971-2005`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1971)
  - M4: `test_expected_finding_value_registry_contract_is_rc2[non-malformed-nonempty]` — [`...:1780-1875`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1780)
  - M5: `test_ai_agent_acceptance_language_is_unchanged` — [`...:2008-2040`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:2008)
  - M6: `test_registry_rejects_control_and_zero_width_characters[note-\x00]`、`[note-\x1f]`、`[note-\u200b]`、`[note-\u200c]`、`[note-\u200d]`、`[note-\ufeff]`、および同じ 6 件の `value-*` — [`...:1726-1777`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1726)
- **どの production 変異が検出されないか:** なし（静的追跡。pytest の変異実走結果ではない）。
- **成果物影響:** 変異の単一理由は保たれている。複数 nodeid が赤くなる場合も、各々同一防壁の同一理由である。
- **推奨対応:** D-01 の文言修正後、登録済み M1〜M6 を指定 nodeid 単位で再走する。

## 恒真性・oracle 監査

- 受理集合テストは `ROLES` / `IDENT` の literal pin に加え、`AGENT_VALUE.fullmatch()` と `validate_message()` の双方を実行し、`; extra=x` を reject matrix に含む。[`...:2008-2040`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:2008)
- 登録済み malformed テストは `_normal_commit_audit()` を mock していない。[`...:1912-1946`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1912)
- 未登録 malformed は production の registry を差し替えず、synthetic SHA を集合外で確認する。[`...:1949-1968`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1949)
- stale spec は非空 note と非空 value を持つ。[`...:1971-1992`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1971)
- 30 件 literal は SHA・kind・ruling・note・value・順序を固定し、registry kind 集合も exact pin する。[`...:1328-1403`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1328)
- empty-registry oracle は exact 30 本文を固定している。[`...:2361-2458`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:2361)
- `_known_spec` の既存既定値は `note=""`, `expected_finding_value=""` で、既存呼び出しの意味を変更していない。[`...:266-280`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:266)
- テスト期待値に working tree の hash・現在 path・行番号・日時は焼き込まれていない。probe `.md` の外部 path と元 `.py` digest は履歴 artifact の固定メタデータであり、テスト oracle ではない。

## 総括

- D-01 の診断文字列不一致を必ず修正する。
- production の field-specific な診断は維持する。
- 修正後、M1〜M6 を登録 nodeid で再実走する。
- 現在の 6 件赤を解消するまで受入完了とは扱わない。

**NO-GO**