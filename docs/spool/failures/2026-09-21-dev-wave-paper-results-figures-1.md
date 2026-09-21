---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-paper-results-figures
seq: 1
---

## 新規

### {{F:selfrun-green-pytest-red-exact-exception-text}}. 実装子の自走 harness で緑の新 test が、受入と同じ pytest では赤になった — 捕まえた AssertionError の文言を完全一致で比べた [テスト代表性] [手順漏れ]

- 事象: 2026-09-21 の論文図 wave (`dev-wave-paper-results-figures`) で、Codex 実装子 2 本が独立に、`assert cond, msg` の `AssertionError` を捕まえて
  `str(exc) == msg` と完全一致で比べる test を計 4 箇所書いた (fig14 / fig15 の bundle 欠落の拒否、可視 Text の禁止句の負例)。子は prompt の指示どおり sandbox で pytest を使わず
  plain runner だけで全件緑を報告したが、親の焦点走 (計算ノード `15694.nqsv`、`tools/run_tests.py`) で 4 件とも赤になった。pytest の assert 書き換えが例外文に説明行を足すため。
  近接 miss であり、受入の前に検出した。既存の fig9 test は `startswith` で比べていて無事だった。
- 根本原因: 子の自走と受入の pytest は同じ test を別の assert 意味論で走らせる。自走の緑を pytest の緑と同一視した (子の報告の緑は plain runner の緑だけだった)。
- 恒久対応: (1) 先頭行の完全一致に直した (fix commit `fc6c4f836`)。(2) memory `selfrun-green-pytest-red-exact-exception-text` — author / fix prompt に先頭行比較を指定し、
  親は段 6 のレビュー投入前に pytest の焦点走を回す。(3) 検出した経路は既存の `docs/dev-wave/operations.md` の `DW-O26` (焦点走の file 集合) と段 6 の consumer 回帰の順序であり、新しい検査は足していない。
- 再発検知: 親の焦点走 (pytest) の赤。機械的な lint (`str(exc) ==` の禁止) は作っていない (依頼の scope 外、単発の型)。
