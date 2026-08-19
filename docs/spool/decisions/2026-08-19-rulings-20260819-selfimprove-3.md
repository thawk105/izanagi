---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: rulings-20260819-selfimprove
seq: 3
---

## {{D:loop-py-conditional-single-process-enforcement}}. `loop.py` の postclaim 強制は D419 決定 (4) の「(c)→(a)」順を継続し、(a) (sink-local な `single_process` 強制) を今回採用する

**決定:** `orchestrator/campaign/loop.py` の `_authorize_measurement` (`loop.py:61-89`) へ、`contract.isolation_policy.single_process is True` のときだけ発火する sink-local な claim 取得・reservation 検査を追加する。caller は当面 repo 外の 8c job script のままとし、tracked wrapper 化 ([T-1097] / [T-276] の所有範囲) は本決定の対象外とする。2026-08-03 の裁定 (D419 決定 1 が引用) が明示した「発火 caller を持たない wave では部分実装を採らない」という禁止は、**単独性が未検査のまま既に実在する呼び手を持つ本件に限り解除する。**

**理由:**
- D419 決定 (4) は「発火 caller が既に実在する穴を先に直す方を推奨する」として (c) を先に選び、
  (a) は「再訪する」前提で保留された (D419 決定 3:「本決定は現状維持を推奨するものではない」)。
  (c) の実装 (claim identity の生存プロセス単位化・submitter receipt authority) は
  2026-08-16 に完了している (D464/D465)。保留の前提だった作業は終わっている。
- 2026-08-03 の禁止が守ろうとしていたのは「発火 caller が存在しない gate を作らない」ことであり、
  その趣旨は「caller が tracked なテストで固定できない」こととは別である。本件の caller
  (8c live pilot job script、`/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1097-s8c-live-abc/live/live.pbs`)
  は実在し、実際にこの経路を通っている — untracked なだけで、死んだコードではない。
- 契約 (`single_process=True`) は既に宣言されている一方、宣言を検査する強制は一度も無い。
  [T-1097] の transport 欠陥が直った瞬間、単独性を一度も検査しないまま exploratory の
  WAL・report・binary SHA・throughput を受理し始める (F322)。規律 3 (正しさシグナルを
  後付けにしない) に照らし、宣言だけで強制がない期間を漫然と延ばす理由はない。

**却下した選択肢:**
- 現状維持 ([T-1097] / [T-276] 完了まで待つ) — 完了時期が不明であり、その間 `single_process`
  契約は無検査のまま通り続ける。
- 本決定で tracked wrapper を新設する — D125 決定 (6)・D108 決定 (2)〜(5) の campaign task
  凍結境界を割る。[T-1097] / [T-276] の所有範囲であり、本決定はその境界を開かない。
