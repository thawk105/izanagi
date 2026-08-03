---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: wave-t367-qdel-guard
seq: 2
---

## {{D:fresh-qstat-gate-scope}}. 自動 qdel の受理集合を fresh snapshot の QUE/HLD へ縮小し、保証の射程を snapshot に限定する

**決定:** `dispatch_compute` の自動 qdel は、qdel 直前に取り直した qstat が次をすべて満たすときだけ
発行する。(1) rc=0、(2) 対象 request ID が出力中にちょうど一つ可視、(3) その block の state field が
種別ごとに高々一つで相互に矛盾しない、(4) 既存 parser と同じ field 別語彙で正規化した結果が
QUE または HLD (STG は QUE へ正規化)、(5) 監視ループが terminal END を観測していない、
(6) cleanup 絶対予算内。判定不能・rc≠0・request 不在・RUN・END・UNKNOWN では発行しない。
qstat の分類が transient のときだけ上限付きで再試行し、permission と rc=0 の不在は即拒否する。

**保証の射程:** 保証するのは「**直前 snapshot が取消可能だったときだけ qdel を発行する**」までである。
qstat と qdel は別 scheduler command で atomic ではないため、「qdel 時点で対象が RUN でない」ことは
保証しない。gate が見送った job は孤児として残る。これらは謳わず、実装の docstring・テスト名・
receipt (`qdel.cleanup_policy`、`qdel.gate`、`qdel.job_may_remain`) で射程を明示する。

**理由:**
- 従来の `active` フラグは qsub 成功で立つだけで scheduler 上の QUE/RUN を表さず、
  infra error・timeout・signal・compute marker 不在の 4 経路が走行中の job を殺しえた。
- 走行中を殺すと、その試行の receipt・stdout・会計の対応が失われ、受入証拠が欠測する。
  「殺さない」側へ倒すと孤児が残るが、孤児は人間が qstat で確認して処理できる一方、
  失われた実行は取り戻せない。非対称なので fail-closed の向きは「殺さない」である。
- 状態語彙を新設せず既存 parser の受理形へ束縛するのは、gate だけが認識する形や
  gate だけが見落とす形を作らないためである。**既存 parser が state と認識する行は gate も必ず数え、
  既存 parser が認識しない値は gate も受理しない**という双方向の一致を不変条件にする。

**却下した選択肢:**
- RUN 観測後の自動 qdel を全面禁止する案 — 孤児 job を無条件に増やす。
- 任意の UNKNOWN を RUN 相当として保護する案 — scheduler の schema drift と malformed 出力を
  長時間受理することになる。UNKNOWN は「殺さない」だけに使い、RUN の権威ある確認は別項目とする。
- gate の判定に監視ループの permissive な状態解析をそのまま流用する案 — 出力全体から最初の
  state を拾うため、複数 block や矛盾した state を含む応答で対象と無関係な状態を根拠に
  destructive command を発行しうる。
- receipt schema を上げて既存 field 意味を変える案 — consumer の実在を確認したうえで
  additive 拡張に留め、既存 `qdel.reason` の語彙も維持した。
