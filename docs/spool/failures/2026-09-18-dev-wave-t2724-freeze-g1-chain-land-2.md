---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2724-freeze-g1-chain-land
seq: 2
---

## 再発

### F370

- **再発: 2026-09-18 ([T-2724] chain land wave の段 1)** — 親は chain が足す 3 path で `orchestrator/tests/` を逆引きし
  12 file の hit を得たが、**hit した test の中身を読まずに** brief へ「実 repo を読んで赤になるのは growth hold 下の 2 node
  だけ」と書いた。実際は `test_s8b_floor_campaign.py` の実 HEAD clone fixture (:2291 / :15625) を使う非 hold 5 node が
  production `clean_scan_digest` の正しい拒否で赤になり、land すると main の受入が恒久赤になる状態だった。検出は
  F370 と同じ経路 — 段 3 の敵対レンズ (A-4) が静的に指摘し、親が焦点走 (計算ノード、5 failed) で確定して land を止めた。
  前 wave (entry 1591) も chain 木で三軸走査だけを実走し受入を走らせていなかったため、裁定パッケージ (D2120 (d)) に
  この波及が載らなかった。恒久対応は F370 の 2026-09-16 再発が定めた「hit した test の中身で pin の形を読む」を、
  **実 ROOT を clone / 走査する fixture の有無**まで読む方向へ適用する (一次資料
  `output/insights/2026-09-18/t2724-freeze-g1-chain-land/README.md` §3)。
