---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t685-scorer-erratum
seq: 2
---

## 新規

### {{F:scorer-conflict-guard-inert}}. 曖昧さ検出が同じ lookahead で無力化され、相反する総括を 13/18 受理していた [恒真ゲート] [テスト代表性]

- 事象: `tools/codex_reasoning_ab.py` の `score_text` は「総括に GO と NO-GO が併記されていたら
  拒否する」二段目を持つが、抽出正規表現の lookahead
  `(?![A-Za-z一-龯ぁ-んァ-ヶ-])` が決定語の直後のひらがなを除外するため、
  2 つ目の決定が `NO-GOです。` `NO-GOでもある。` のように日本語で続く限り数えられない。
  親が [T-685] wave で実測したところ、相反・否定を含む 18 種のうち **13 種を valid として受理**していた
  (`GO。しかしNO-GOでもある。` が `valid=True / decision=GO` になる等)。
  F176 は同じ lookahead の**取りこぼし側 (false reject)** だけを記録しており、
  この**受理側 (false accept)** は 1 年分の運用で一度も顕在化していなかった。
- 根本原因: 同一の lookahead が「決定語の言及を数えない」ためにあり、
  false reject と false accept の両方を同時に生んでいた。二段目は存在するが**発火しない恒真ゲート**
  だった。事前登録された采点器 control が歴史 `focus1.md` / `focus2.md` の 2 本だけで、
  どちらも単一決定の総括だったため、併記を突く負例が control に一件も無かった。
- 恒久対応: `tools/codex_reasoning_ab.py` の `_DECISION_ASSERTION_RE` と
  `score_text` の `claimed_decisions = extracted_decisions | asserted_decisions` —
  抽出は据え置いたまま、「文末の断定」「〜と判断/結論/裁定」「〜の結論」の 3 枝からなる
  閉じた断定形を和集合に足し、冒頭決定との完全一致を要求する fails-closed 判定。
  同 commit で F176 の恒久対応 (`decision` 抽出 0 件を曖昧と誤判定しない) も実装した。
- 再発検知: `orchestrator/tests/test_codex_reasoning_ab.py` の
  `test_f176_rejects_conflicting_decision_claims` (相反 14 種) と
  `test_f176_preserves_legitimate_opposite_mentions` (過剰拒否を検出する正例 10 文)。
  変異 11 件を実装前に事前登録して本走し、11/11 検出・SURVIVED 0 を
  `output/insights/2026-08-09_t685-scorer-erratum-mutation-ledger.json` へ凍結した。

### {{F:mutation-spec-diverged-from-preregistration}}. 変異 spec を裁定表と同期させずに書き換え、実走前検査で初めて気づいた [手順漏れ]

- 事象: [T-685] wave の親が、段 6 裁定に載せた変異表 v2 を更新しないまま
  `mutation-spec.json` だけを書き換えた (1 件を落として番号を詰め、裁定に無い変異を 1 件足した)。
  焦点再レビューが「spec は裁定表と一致しない」と指摘し、続く親の実走前検査で
  さらに 2 件の欠陥 (削除済み行を anchor にした M05、期待 node を反転させず生存する M12) が出た。
  harness は M05 で `anchor count=0` を検出して fail-closed に中断した (実装は無傷)。
- 根本原因: 事前登録 (`DW-M01`) は「集合と意図」を実装前に固定するものだが、
  逐語の置換文字列は実装後にしか書けない。この**二段階性**を手順として明示していないため、
  spec 作成時に裁定表へ書き戻す手が抜けた。加えて、fix 2 巡目が anchor 行を削除したのに
  spec を追随させなかった。
- 恒久対応: 実走前に spec を機械検査する手順を親の義務に加えた —
  各 `old` が source 中にちょうど 1 回現れることと、**memory 上で変異させて期待入力の判定が
  実際に反転すること**を全数で確かめてから本走する。[T-685] wave はこれで 2 件を実走前に潰した。
  手順の逐語は `docs/dev-wave/mutation.md` の `DW-M01` / `DW-M04` が既に要求している
  「単一理由性をコードで確認する」の実施形である。
- 再発検知: harness 自身の anchor 一意性検査 (`anchor count` の fail-closed 中断) が
  第 1 層で、実走前の反転検査が第 2 層。生存する変異は本走の `summary.SURVIVED` に出る。
