---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: soft-plotting-starlight
seq: 2
---

## 再発

### F35

- **再発: 2026-08-18** — [T-715] の実装記録 commit (2026-08-18 15:15 JST、archive worklog
  エントリ (655)) が次の一手 delta で自 task ID を `完了` 節へ明示しなかったため、
  `docs/spool/README.md` の暗黙 carry (「触れなかった active な T は自動的に carry される」) が
  [T-715] を未着手のまま (656)〜(666) へ再送出し続けた。実装完了 (17:10 land 完了) から
  着手 (今回の /dev-wave 起票) までの時間差は無く、記録 commit そのものが「済んだのに
  未消化の carry を残す」唯一の発生源だった点が、2026-07-24 (承認記録側の照合漏れ) /
  2026-08-13 (起票から投入までの約 12 時間差) の既知 2 形態と異なる新しい面である。
  恒久対応 1 (`DW-S01` の照合義務) は今回も投入前に機能し実装は行われなかった。
  恒久対応候補 (段 7 記録テンプレートへ「自 task ID を完了節へ明示する」チェックを追加) は
  dev-wave docs 予算満杯のため未実装 — ユーザー裁定へ返す。
