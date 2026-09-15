---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-15
wave: dev-wave-cc-diagnostic-skill
seq: 1
---

## 新規

### {{F:layer-budget-omits-leaf-preamble}}. 層予算を節の和だけで見積もり、leaf の preamble 304 bytes を落とした [手順漏れ]

- 事象: 段 1 brief で dev-wave 読み込み契約の L1 層を「10,320 / 10,625、残 305 bytes」と実測として
  報告し、その余地に発見経路 1 行を足す設計を立てた。段 3 の 2 レンズが独立に
  「現物は 10,624 / 10,625、残 1 byte」と反証し、親が検査器自身の関数で再測して子が正しいと確定した。
  提案どおり足していれば文書検査が 95 bytes 超過で赤になった。
- 根本原因: 親が `## ` 見出しで節を切り出して和を取り、**leaf file の preamble を数えなかった。**
  `docs/dev-wave/core.md` の preamble は L1 に入るので数えたが、`mutation.md` (109 bytes) と
  `operations.md` (195 bytes) の preamble も、その file に L1 節がある限り L1 へ計上される。
  検査器は「分類済み節 + preamble = 実 bytes」の被覆不変条件を持つため、preamble はどこかの層に
  必ず入る。自前の節切り出しはこの規則を再現していなかった。
- 恒久対応: 層予算を見積もるときは `tools/check_docs.py` の `_visible_reference_slices` と
  `STAGE_UNCONDITIONAL_DISPATCH_CONTRACT` を通して測る。自前の見出し切り出しで代用しない。
- 再発検知: `orchestrator/tests/test_check_docs.py::test_dev_wave_layer_budget_rejects_plus_one` が
  境界 +1 byte を固定しているので、誤った見積もりで足せば検査が赤で止まる。親側の見積もり誤りは
  止められないので、追記を提案する段で必ず検査器経由の実測値を添える。

### {{F:summary-fabricated-section-titles}}. 要約経路が一次資料の節構成を捏造した [捏造/幻覚]

- 事象: ユーザーが参照論文の §3.5〜3.6 と §5.5 を読むよう指示した。Web 取得の要約は
  §3.5 を "Self-Improvement Through Architectural Modifications"、§3.6 を "Knowledge Integration
  and Expansion"、§5.5 を "Safety Considerations in Autonomous Research Loops" と報告した。
  親が PDF 本文を自分で text 化すると、実体は §3.5 "Harness and agent self-evolution"、
  §3.6 "Skill libraries and persistent accumulation"、§5.5 "Result-level versus process-level
  improvement" だった。**節の題・内容・引用文献のすべてが別物**で、要約は一般論で埋められていた。
  引用文献の節も「機械学習の自己最適化、AI 安全性文献、メタ学習研究を参照している」という
  出典を辿れない記述だった。
- 観測: 要約の側には「その節が取れなかった」という信号が出ず、一般論で埋まった題と内容が返った。
  引用文献の節も「機械学習の自己最適化、AI 安全性文献、メタ学習研究を参照している」という
  出典を辿れない記述だった。
- 根本原因: **未確定。** 節番号で特定の節を要求したとき、取得できなかった部分をもっともらしい題で
  埋めている、という推測までである。要約を生成する構成も、その入力が本文のどこまでを含んでいたかも
  本 wave では確かめていない。下の恒久対応は原因の確定に依存しない。
- 恒久対応: 一次資料の節を根拠にする前に、**自分で本文を取り出して節見出しを照合する**。
  PDF なら `pdftotext -layout` で text 化し、見出し行を検索してから該当範囲を読む。
  要約だけを根拠に節名・節番号・引用文献を書かない。
- 再発検知: 論文・仕様の節番号を引く記述には、本文から取った見出し文字列を併記する。
  併記が無い節参照は裏取り未実施として扱う。
