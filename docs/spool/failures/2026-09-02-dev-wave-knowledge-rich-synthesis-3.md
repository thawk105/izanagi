---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-knowledge-rich-synthesis
seq: 3
---

## 再発

### F511

- **再発: 2026-09-02** — 親が段 6 レビュー子へ渡す「確定差分の全文」を `git diff` で作った。
  この wave の成果物 3 点のうち 2 点は新規 untracked file (spool fragment) なので、
  `git diff` の出力には現れない。decisions fragment は別途逐語で射影していたため助かったが、
  **worklog fragment は検査束から丸ごと欠落**し、1 巡目のレビューは一度も見ていない状態で
  「差し戻し」を返した。レビュー自身が must-fix として欠落を指摘したので発覚し、親は
  worklog を射影に加えて焦点再レビューを回した。射影の完全性を検査する経路が無い点は
  F511 本体と同じで、機構が違う (行範囲の切り出し漏れではなく、`git diff` が untracked を
  黙って落とす)。恒久対応は「レビューへ渡す成果物側の射影は `git status --porcelain` で
  変更集合を先に列挙し、tracked 差分と untracked file の両方を数え合わせてから作る」。
