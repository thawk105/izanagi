---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: rulings-20260821-ai-performance-measurement
seq: 1
---

## {{D:ai-performance-measurement-authority}}. AI セッションによる性能実測を許可する

**決定:** このプロジェクトでは、ユーザーが明示的に依頼した場合、AI セッションが性能実測の投入・回収・解析を行ってよい。実測は sanctioned な controller / dispatch 経路を通し、計算ノード上で行う。計算ノード専用、投入前 preflight、job/source/receipt の束縛、キュー状態確認、CCBench の TRACE=0 分離、verifier と正しさゲートは維持する。ログインノードでのベンチ直接実行、controller を迂回した未記録の raw 実測、qsub receipt や結果の捏造は許可しない。D86/D87 に残る「AI は qsub しない」という旧来の制約は、ユーザーの今回の明示指示によりこの性能実測スコープでは supersede する。

**理由:** ユーザーは 2026-08-21 に「このプロジェクトは AI が性能実測する」と明示した。AI による CC の自動合成・進化探索が目的であり、性能実測を常に人間の手番へ戻すと主経路を停止させる。必要なのは実行主体の人間性ではなく、sanctioned 経路・計算ノード・receipt・正しさ証拠の完全性である。

**却下した選択肢:**

- 全性能実測を人間の明示 qsub に限定する — AI 自動合成の実験ループを不必要に停止させるため採らない。
- qsub を直接打つだけで preflight・receipt・source pin・verifier を省略する — 性能値の権威性と再現性を失うため採らない。
