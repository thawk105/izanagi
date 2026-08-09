---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t682-provenance-known-violations
seq: 2
---

## 新規

### {{F:blacklist-only-note-gate}}. 必須 note の実質性を拒否リストだけで守ろうとし、不可視文字で名目化できた [恒真ゲート]

- 事象: [T-139] 裁定は known-violation の追加 kind に「なぜ内容が正確で綴りだけの誤りなのかを
  1 件ずつ書く」note を必須とした。これを `not note.strip()` と、Unicode category
  `Cc` / `Cf` / `Zl` / `Zp` および zero-width 4 文字の**拒否リスト**で実装したところ、
  U+034F COMBINING GRAPHEME JOINER と U+FE0F VARIATION SELECTOR-16 (ともに `Mn`)、
  U+3164 HANGUL FILLER (`Lo`) だけからなる note が registry を通った。
  視覚上ほぼ空の note で、説明のない entry を既知違反として抑止できる状態だった。
  段 6 の焦点再レビューが実測で示すまで、拒否リストを 2 度広げても閉じなかった。
- 根本原因: 「望ましくないものを列挙して除く」形で実質性を守ろうとしたこと。
  実質性は正条件 (可視の説明文字が最低 1 つある) でしか表せず、拒否リストは
  Unicode の未列挙領域が常に残るため原理的に閉じない。`Lo` (Letter) に属する filler が
  あるため「category が Letter なら可視」という素朴な正条件も不十分で、
  default-ignorable 相当の明示除外が要る。
- 恒久対応: `tools/check_ai_provenance.py` の `_contains_descriptive_note_character` —
  category が `L/N/P/S` で始まり、default-ignorable 相当の明示集合に含まれない文字を
  最低 1 つ要求する fails-closed 検査。拒否リストは縮小せず併存させる。
- 再発検知: `orchestrator/tests/test_check_ai_provenance.py` の
  `test_registry_rejects_non_descriptive_required_note_rc2` (U+034F / U+FE0F / U+3164 の負例) と
  `test_registry_accepts_visible_character_mixed_with_non_descriptive_characters`
  (過剰拒否を検出する正例)。変異 M7 / M8 で両方向の検出力を実測済み (ともに KILLED)。
