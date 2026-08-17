---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t987-floor-rebind
seq: 2
---

## 再発

### F370

- **再発: 2026-08-17 ([T-987] wave の段 1)** — 親が「`reseal_protocol()` の production caller は
  ゼロ、呼び手はテストのみ」と brief と実測記録へ書いた。実際は同一 file の `main()` に
  `reseal-protocol` CLI サブコマンドが実在した
  (`orchestrator/campaign/s8b_floor_campaign.py` の dispatcher、parser は同 file)。
  原因は呼び手検索を `grep -v "^orchestrator/campaign/s8b_floor_campaign.py"` で走らせ、
  **答えを含む file を自分の除外条件で消していた**こと。F370 が「検索した空間そのものが違った」
  と書いた型の同型再発で、今回は空間の欠落が他 module でなく自 module だった。
  恒久対応は同じ memory `authoritative-closure-before-counting` を、
  **除外条件付き検索で「不在」を断定する前に除外集合を読み上げる**方向へ適用する。
  検出は F370 と同じ経路 — 段 3 の敵対レンズ (luna) が refuted を返し、親が再確認して確定した。
