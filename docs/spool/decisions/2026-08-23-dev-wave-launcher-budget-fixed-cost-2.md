---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-launcher-budget-fixed-cost
seq: 2
---

## {{D:launcher-three-interval-budget}}. launcher の受理締切を 3 区間の独立予算へ分ける

**決定:** `codex_worker_launch.py` の受理締切を 1 本から 3 本へ分け、境界を
`L`=launcher 起点、`P`=初回 `Popen` 直前、`S`=最終 attempt wall 標本、
`R`=receipt atomic 公開完了、`V`=`codex --version` 所要として次のとおり束縛する。

- 準備 `(P-L)-V` を `preparation_admission_bound_s` (既定 60) で縛る
- 監督実行 `(S-P)+V` を従来の `wall_clock_admission_bound_s` (既定 3600、変更しない) で縛る
- 最終化 `R-S` を `finalization_admission_bound_s` (既定 60) で縛る

3 区間の和は `R-L` であり、**無予算の区間を作らない**。runtime の gate と receipt validator の
残差計算は同じ境界を使う。receipt は schema V4 を新設し
`actuals.preparation_wall_clock_s` / `actuals.finalization_wall_clock_s` で内訳を可視化する。
`actuals.wall_clock_s` と `wall_clock_scope` の意味、V1〜V3 の field 集合と truth table、
「完全な既存 receipt は上書きできない」防壁は変更しない。
準備超過・最終化超過は attempt の `limit_trigger` ではなく job 単位の stop reason とし、
attempt 側の 3 理由集合は据え置く。控除後 attempt wall の検査は全 outcome へ適用し、
job-stop が attempt 超過を覆い隠せないようにする。

**理由:**
- 従来の 1 本の予算は launcher の module import 時点から receipt 構築までの全経過を縛っており、
  被験体である codex attempt でない準備 (project import、実行ファイル hash、manifest / receipt 検証)
  と最終化 (seal、audit、receipt staging、atomic 公開) を同じ予算で食っていた。
  被験体が正常でも機体が混むと締切に達し、launcher の受理集合検査の rc が
  テストの中身でなくノード負荷で決まっていた。
- 予算の一律引き上げは採らない。本当に暴走した被験体を捕まえられなくなるため、
  受理集合を緩める方向になる。
- `codex --version` は caller 指定の codex を実行するので**被験体**である。その所要を準備側へ
  置くと、暴走した被験体が準備予算へ逃げられる。attempt 予算へ算入し、さらに
  新規 session / process group で起動して残留子孫の観測と終了確認を行う。
  これにより被験体の実行時間の縛りは変更前より緩まない。
- 実走 launcher の診断成果物 1281 件で、準備は p50 0.678 s / max 3.792 s、
  最終化は p50 0.986 s / max 4.940 s、seal は p50 0.0058 s。最終化は成果物サイズ依存が弱く
  約 0.8 秒の床を持つため、**準備だけを控除する設計では症状が消えない**ことが実測で示された。

**却下した選択肢:**
- 予算の一律引き上げ — 暴走した被験体を捕まえられなくなる。
- 準備だけを attempt 予算から外す — 最終化費が予算に残り、負荷下で同じ赤が残る。
  段 3 の敵対レンズ 2 本が独立にこの穴を指摘し、その後の実測が裏づけた。
- `_RECEIPT_FIELDS_V3` を其の場で拡張して V4 を作らない — 既存 V3 受領証が検証に落ち、
  「完全な既存 receipt は上書きできない」防壁が逆に無効化される。
- 準備超過を attempt の `limit_trigger` として記録する — 存在しない attempt が準備超過した、
  という不正な受領証になる。
- 準備区間に物理 hard cap を与える — 既存 wall 上限も polled admission 検査であり、
  同じ強度に揃えるのが本決定の射程である。hard cap は launcher の import より外側の
  watchdog を要し、呼び出し形と背景 job の detach 契約に触れるため別途審査とする。
