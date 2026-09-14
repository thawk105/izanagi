---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t2374-a1-pilot-next-attempt
seq: 2
---

## {{D:a1-pilot-additional-attempt-not-submitted}}. A-1 pilot の追加 attempt は投入せず、完了済みの重複項目として閉じる

**決定:** A-1 balanced5 pilot (study `paper-story-a1-20260901-balanced5-pilot-v1`) の追加 attempt を
投入しない。持ち越し項目としての「次の attempt を投入する」は、同じ作業が 2026-09-11 に
attempt-0004 として実施済みであることを理由に完了として閉じる。後続の本走には本決定で触れず、
認可 (人間手番) と実行面の整備を持つ既存の 2 項目にそのまま残す。

**理由:**

- pilot は 2026-09-11 の attempt-0004 で 3 workload とも valid で完走した。成果物
  `output/insights/2026-09-01_paper-story-a1-balanced5-pilot/` が実在し、その README は
  `All workloads terminal: true` / `All workloads valid: true`、各 workload reps=60 を逐語で記す。
  request は 991875 / 991876 / 991877 (.nqsv)、source commit は `a9d20d701`。
- 事前登録は pilot の観測値を最終推定へ入れることを禁じ、用途を sizing 入力に限定している。
  同じ pilot をもう一度走らせても、新しく主張できる量は増えない。計算ノードの資源だけを消費する。
- pilot の sizing 入力は既に消費済みである。2026-09-14 に sizing 証明書と本走 policy
  `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` が凍結された (D1973)。
  pilot を再走させると、凍結済みの証明書が参照する材料と別の材料が生まれる。
- 持ち越し項目が閉じられずに残っていたのは記録漏れであって、未実施の作業が残っていたからではない。
  実体を消化した項目は完了として閉じられたが、同内容の重複項目は bare な参照のまま carry され続け、
  依頼のたびに済んだ作業を再提案する原因になっていた。

**却下した選択肢:**

- **pilot を再投入して念のため追試する** — 事前登録が pilot 観測値の用途を sizing 入力に限定して
  いるため、追試から新しい主張は作れない。凍結済み証明書の材料と食い違う材料を作る害だけが残る。
- **この機会に本走を投入する** — 事前登録の拒否リストが「この走行を認可なしに投入すること」を
  明示的に禁じており、認可は人間手番である。加えて事前登録は、計測経路に source 契約・hydrate 入力・
  依存 source の staging・source binding の生成・amended build の受理形が pilot 専用のまま残ると
  書いている。認可が出ても現状では実行できない。
- **重複項目を閉じずに残し、本文だけ現況へ書き替える** — 残件が無い項目を active に置き続けると、
  次の提案が同じ済み作業をまた選ぶ。終端は構造の宣言で示す。
- **本走の実行面の整備を本 wave で始める** — 依頼が scope を本題の投入だけに限定した。
  実行面は 1 箇所の限定解除では足りないと段 3 が数え上げており、別の作業単位が所有している。
