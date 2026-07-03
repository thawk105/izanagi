# Izanagi

**ワークロード特化の並行性制御 (Concurrency Control) を AI が自動合成するシステム。**

CCBench を素材コーパスとして、入力ワークロードに最適な CC を選定し、他の CC 実装から有用な最適化を移植して variant を進化させ、最終的に「新しい CC + なぜそれが速いのかの説明 + 試行錯誤の記録」を生成することを目指す。

## 名前の由来

イザナギは日本神話の創造神。天の沼矛で混沌をかき混ぜ、滴り落ちたものから島々を生成した。「既存のものを素材に、新しいものを引き出す」という神話的含意が、本システムの本質 — 既存 CC の集合をかき混ぜて新しい variant を析出させる — と重なる。

命名は作者の研究系譜 (Tsurugi / Shirakami / Yakushima) に連なる「日本のルーツ」シリーズの一環。

## 現在の状態

**Phase 2 (パラメータ探索) 完了。次は Phase 3 (合成) 着手。** Phase 1 (評価器の構築) は完了済み — trace verifier・calibrator が `orchestrator/` に実装され、評価パイプライン (正しさ + 性能) が信頼できる状態。Phase 2 は P2-0〜P2-5 + A2 完了 (silo 全探索、critic/profiler 実体化、backoff ケーススタディで stock 最良を contention 域で +38%/+11% 上回る合成を certified で達成)。主実験 P2-5 は negative result (LLM 誘導は機械的勾配で達成できる水準を超えず、deceptive 構造では有意に有害 → 価値は空間外の合成にある、D21/D29)。S4 (規律3 配線) 完了済み。次は Phase 3 (LLM が CC コードを合成: planner/coder/auditor)。詳細な現在地は `CLAUDE.md` と `docs/worklog.md` 末尾。

実装を読む/進める前に、必ず以下を順に読むこと:

1. `CLAUDE.md` — 作業の出発点。現在地と絶対規律
2. `docs/roadmap.md` — 全体設計とその理由 (議論の蓄積)
3. `docs/phase3.md` — 今やるべきタスクの分解 (Phase 1/2 は `docs/phase1.md` / `docs/phase2.md` に完了記録)

## アーキテクチャ概要 (三層)

```
ワークロード入力 (spec cards: 環境/ワークロード/要求)
   ↓
層1: ベースCC選定      … CCBench解析 → workload照合 → 軽量ベンチで確定
   ↓
層2: 最適化合成ループ   … 変異軸を合成 (フラグ空間外の新軸が主軸。他CCからの移植は拡張予約 D32)
                          → variant生成 → 評価 → 取捨選択
   │                      (据え置きの正しさゲートを壊す変異はreject)
   ↓
層3: variant比較・選択  … Pareto front上で最終CCを決定
   ↓
最終成果物: 新CC + なぜ速いかの理由 + 試行ログ
```

## 関連研究 (本システムの土台)

- **Polyjuice** (OSDI 2021) — CC をアクション列に分解して進化的に学習。本システムの層2の思想的祖先
- **CCaaLF / NeurCC** (2025) — CC を学習可能関数としてモデル化、ベイズ最適化で高速化
- **Jitskit** (arXiv 2605.24096) — KVストアをワークロード仕様から丸ごと合成。spec cards / adversarial auditor / leading indicators / reward hack 対策の源泉
- **IDS** (arXiv 2605.23109) — コードと証明を同時に育てる。「正しさを後付けにしない」思想の源泉
- **ECC** (github.com/affaan-m/ECC) — Claude Code の運用パターン (agent定義のtools/model指定、hookによる規律執行) の参考

詳細は `docs/roadmap.md` の「関連研究からの借用」を参照。

## ライセンス

未定 (Phase 進行中は private 想定)。
