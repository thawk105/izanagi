---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t657-t660-g2-activation
seq: 1
---

## 新規

### {{F:provenance-model-after-model-switch}}. セッション途中の `/model` 切替後も開始時の model slug を trailer へ書き続けた [捏造/幻覚] [ドリフト]

- 事象: 本 wave のセッションは開始時 system prompt が `Fable 5 / claude-fable-5` を告げていたが、
  作業途中でユーザーが `/model` を実行し、出力は
  `Set model to Opus 5 (1M context) and saved as your default for new sessions` だった。
  親はその後も `AI-Agent:` trailer へ `model=claude-fable-5` を書き続け、**8 commit** を作った
  (未 land)。ユーザーの指摘で判明した。
- 根本原因: system prompt は会話開始時に固定され途中で更新されないため、切替後の実行面を
  親は観測できない。にもかかわらず「開始時の記述が今も真」と暗黙に仮定した。
  `docs/ai-provenance.md` の共通則は「本来確認できるが記録時に確定できない場合は `unknown` とし、
  世代や内部モデルを推測しない」と定めており、**確定不能を確定として書いた時点で違反**である。
  切替後の書き方を定めた条項が入口にも reference にも無く、規約の穴でもある。
- 恒久対応: memory [[provenance-model-unknown-after-model-switch]] に
  「セッション途中で `/model` が実行されたら、以降の `AI-Agent:` は `model=unknown` を使い、
  開始時 slug を書き続けない」を記録した。規約本体への条項追加は
  {{T:provenance-model-switch-rule}} で裁定へ返す (本 wave では既成事実にしない)。
- 再発検知: 同型は同日の [T-139] R4 probe wave が独立に踏んでいる — 同 wave の 22 commit が
  `model=claude-opus-5[1m]` を書き、`[a-z0-9][a-z0-9._-]*` に反して
  `check_ai_provenance.py` の形式検査で赤になった (親が incoming 監査で実測、
  既知違反リスト未登録)。**あちらは形式違反として機械検出されたが、本 wave の
  `claude-fable-5` は形式として妥当なため機械検出されない**。値の真偽を機械で照合する層は
  現状存在せず、`unknown` 規律と人間の指摘だけが防壁である。
