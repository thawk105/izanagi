---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-19
wave: codex-dev-wave-t2783-critic-input
seq: 1
---

## {{D:k2-explicit-critic-input}}. K2手動loopのcritic診断は明示逐語から兄弟keyへ射影し、同一診断を次planner/coderへ渡す

**決定:** D2148項3の局所実装として `k2_critic_diagnosis` を追加する。親が指定したcritic逐語bytesから
既存抽出器で4節を取り、data boundary・source SHA-256と合わせたexact6fieldを両role入力へ組み込む。
K2・非B-4・reflux onに限定し、直接builderにも適用条件を置く。未指定はkey自体なし。
whiteboardの5field・delta_pct=None・AO非読取と、評価・停止判定は不変。実consumerは登録Claude roleへの
親のinline送付であり、新しい自動launcherや送達receiptは作らない。実受領・採用・改善効果は別の実走で確認する。

**理由:** 診断未送達と既知値再提案は実走で観測されたが、因果は未検証。4節は留保を落とさず既存抽出器を
再利用する局所案であり、候補値の採用強制ではない。診断中の権限・検証上書き命令は既存境界報告へ返し、
knowledge source indexを捏造しない。static adapterは本文とsource pinのみ同期し、既存schemaとruntime blockedを維持する。

**却下:** whiteboard拡張、報告用AOからの自動還流、8c数値射影への置換、static schemaのついで修復、
新launcher・汎用台帳・候補再抽選。次の実走計画には同機体・同jobのstock適応backoff対照を含め、
予算は別途確定する。本変更では3巡目を投入しない。検証記録は `output/insights/2026-09-19/t2783-critic-input/README.md`。
