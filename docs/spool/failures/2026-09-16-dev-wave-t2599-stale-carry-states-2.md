---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2599-stale-carry-states
seq: 2
---

## 再発

### F300

- **再発: 2026-09-16 (2 本目の wave、[T-2599])** — 同日の [T-2638] が記録した「churn の出所が
  同じ走行の内側」の変種を、**別の wave が独立に踏んだ**。docs のみ (`docs/spool/**` だけ) の wave で
  受入全走が 4 回続けて赤になり、赤の集合は走行ごとに変わった (2 件 → 17 件 → 4 件 → 4 件)。
  出た test はすべて F300 の既存追記が名指す 4 件の部分集合で、単独走はいずれも緑
  (2 件 → 2 passed、4 file → 543 passed、3 file → 267 passed)。
  **他 session の同時走行は原因ではないと実測で分かった** — 受入 leader が他に 1 本だけで
  1 分平均負荷 1.95 の最も静かな窓でも同じ 4 件が赤になった。投入直前の leader 本数と負荷は
  赤の有無を予測しない。
  **2 例目が別 producer で揃ったので、族としての恒久対応を検討できる状態になった** (DW-G03)。
  ただし本 wave は docs のみで実装面の差分を持たないため、`orchestrator/tests/flaky_test_holds.py`
  への登録も走査側の設計変更も行っていない。恒久対応は依然として未定であり、
  次に必要なのは「repo root 全走査の検査と repo root 配下に scratch を作る検査を同一走行内で
  同居させない」設計の裁定である。
