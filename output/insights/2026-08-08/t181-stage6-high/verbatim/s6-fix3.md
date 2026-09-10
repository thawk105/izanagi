F9 の限定修正とテスト追加を完了しました。docs 編集・commit はしていません。

## 変更

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-fix3/tools/check_docs.py:3448)
  - CRLF を LF に正規化後、`"\n"` だけで独立行を分割。
  - CR-only と Unicode separator は行境界にしていません。
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-fix3/orchestrator/tests/test_check_docs.py:5345)
  - U+2028 / U+2029 / VT / FF / NEL × S06-A/C の10 production-path 負例。
  - 各ケースで finding 集合を exact 比較。
  - CRLF 全文の production-path 正例を追加。
  - 既存テストの期待値は変更していません。

## Finding 集合と probe

事前期待は、S06-A の5ケースが A finding singleton、S06-C の5ケースが C finding singleton、それ以外は回帰です。

実測結果：

- Unicode separator 10/10: 対応する singleton と完全一致。余分な finding なし。
- CRLF 全文: `findings=[]`。
- CR-only 全文: 従来どおり12 findings。
  - S02/S03/S06-A/S06-C pin finding ×4
  - S02/S03/S05-A/B/C/S06-A/B/C H2 finding ×8
- 現行 `workers.md`: S06-A は物理行48、S06-C は物理行67に各 exact-one。
- 現行 docs: `python3 tools/check_docs.py` → `check_docs: 違反なし`。

## 検査

成功：

- `python3 tools/check_docs.py`
- `python3 tools/check_codex_agents.py`
- `python3 -m py_compile tools/check_docs.py orchestrator/tests/test_check_docs.py`
- `git diff --check`

pytest nodeid：

- `test_dev_wave_reasoning_effort_pin_production_path_rejects_unicode_line_separators_exact`
- `test_dev_wave_reasoning_effort_pin_production_path_accepts_crlf_document_exact`

`tools/run_tests.py` 経由で3回投入しましたが、予約台帳をsandboxから更新できず、compute側も `qstat -Q preflight rc=1` で全回 rc=16。テスト本体は未実走なので、pytest の緑は主張しません。

## 静的波及

- caller: `_check_command_docs_guard()`
- 共有処理: `_visible_dispatch_inventory_text()`、`_reference_id_sections()`
- fixture/helper: `_write_command_guard_docs()`、`_build_min_repo()`、`_run_check()`、`_finding_set()`
- consumer: S02/S03/S06/O16 pin tests、H2 inventory tests、`test_real_repo_clean`
- production変更は S06-A/C の独立行 count 分岐だけ。S02/S03 の substring pin、finding逐語、共有節抽出、H2 inventory は不変です。
- F1/F3/F4/F5/F7/F8/CF-07 の経路には変更なし。観測された regression は0です。

## 総括

- F9: **partial（実装・production probe 完了、pytest未実走）**
- Unicode separator 迂回: 10/10 拒否
- CRLF: 引き続き受理
- CR-only: 12 findings のまま
- 現行規範2行: exact-one、実 repo checker通過
- regressed: 観測上0
- 残る懸念: runner rc=16 解消後のpytest実走のみ