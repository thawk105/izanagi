# Izanagi

**ワークロード特化の並行性制御 (Concurrency Control) を AI が自動合成するシステム。**

CCBench を素材コーパスとして、入力ワークロードに最適な CC を選定し、他の CC 実装から有用な最適化を移植して variant を進化させ、最終的に「新しい CC + なぜそれが速いのかの説明 + 試行錯誤の記録」を生成することを目指す。

## 名前の由来

イザナギは日本神話の創造神。天の沼矛で混沌をかき混ぜ、滴り落ちたものから島々を生成した。「既存のものを素材に、新しいものを引き出す」という神話的含意が、本システムの本質 — 既存 CC の集合をかき混ぜて新しい variant を析出させる — と重なる。

命名は作者の研究系譜 (Tsurugi / Shirakami / Yakushima) に連なる「日本のルーツ」シリーズの一環。

## 現在の状態

**Phase 1 (評価器の構築) に着手する段階。** まだコードは無い。設計はすべて `docs/` に文書化済み。

実装を始める前に、必ず以下を順に読むこと:

1. `CLAUDE.md` — 作業の出発点。現在地と絶対規律
2. `docs/roadmap.md` — 全体設計とその理由 (議論の蓄積)
3. `docs/phase1.md` — 今やるべきタスクの分解

## アーキテクチャ概要 (三層)

```
ワークロード入力 (spec cards: 環境/ワークロード/要求)
   ↓
層1: ベースCC選定      … CCBench解析 → workload照合 → 軽量ベンチで確定
   ↓
層2: 最適化移植ループ   … 他CCから最適化を抽出 → variant生成 → 評価 → 取捨選択
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
