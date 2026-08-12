---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t139-q1-canonical-decision
seq: 1
---

## 再発

### F282

- **再発: 2026-08-13** — 段 3 の敵対レンズ A を待つ待ち手が exit 0 を返したが、`.done` も成果物も
  無く producer は生存していた (3 点照合で捕捉、子は約 3 分後に正常完了)。恒久対応どおり
  3 点照合が効いた。**別 wave での独立 2 例目**であり、待ち手の 0 復帰を完了の十分条件に
  しない規律は維持する。本 wave は親側で 3 点照合する待ち手を自作して回避した。
