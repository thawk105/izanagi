# [T-1942] 段 1 brief — 床値 official 実測の投入前ゲートと D926 実装

基準: local main `08a17b3b3`、worktree `.claude/worktrees/dev-wave-t1942-floor-gate-recheck`、
branch `worktree-dev-wave-t1942-floor-gate-recheck`。

## 主目的

現行 Pegasus で workload 別 (holdout `rr20` / `rr80`) の床値を **official 経路**で実測し、
`output/s8b-freeze/holdout_freeze.json` の `floor` (現在 `null`) を埋める材料を得る。
論文側要求は `docs/paper-story/2026-08-26.md` §8 A-4。

## 確定済みユーザー裁定 (この wave の拘束)

- D811: pilot 値 (rr20=3.555e+04 / rr80=4.551e+04) を発効させない。official で採る。
  **着手条件** — pilot が消費した使い捨て入場鍵の状態を実測し、official が同じ cell を
  claim できることを確かめる。できなければ着手せずユーザーへ返す。
- D323: `floor_campaign.sh` に mode の受け口を作らない。official 解禁は別の source commit と
  script blob hash での再投入で行う。
- D926: official 専用 zero-arity 引数と nonce env を pilot とは**別系統**で追加。
  `floor_campaign.sh` は固定 official argv へ。job-result・失敗文言・guard・無条件拒否テスト・
  手順書を同じ変更単位で直す。**submission receipt schema / admission claim key 6 項目 /
  refreeze 不適格 seam 18 名集合 / `_derive_refreeze_eligibility` の判定式は変更しない。**
- 今回の依頼: 投入前ゲートを実測し直し、通ることを確認してから投入する。通らなければ
  実測結果を記録して停止し、迂回しない。計測は trace-disabled build、環境タグ付き。

## 投入前ゲート (両方緑でなければ投入しない)

- **G-A (compiler input)**: 2026-08-29 に無条件赤と実測した s8b compiler input manifest の赤
  (`output/insights/2026-08-29_t1942-floor-gate-compiler-input/README.md`) が解けているか。
- **G-B (D811 着手条件)**: official 走行が 12 cell を claim できるか。

## 親の provisional 裁定 (割れうる前提・攻撃対象)

- **(P1-a)** G-A は「落ちた job 952631 の旧 manifest を現行 validator へ再走」では測れない。
  旧 manifest は v1/v2 schema で絶対 path を持ち、現行 collector が作る v3 manifest とは別物である。
  測るべきは「現行 collector が同じ消える絶対 path 群を再束縛可能な根へ分類し、受領書発行が通ること」。
- **(P1-b)** 第 1 クラス (build cache staging `.staging-<PID>-<nonce>/_deps/masstree-src/*.hh` 31 件) は
  `fetchcontent-masstree` 根で、第 2 クラス (`/scr/0_<jobid>/...` 7 件) は T-2027 の `dependency-prefix`
  根で覆われている。受領書発行側の配線は `s8b_floor_campaign.py:4392-4398` に実在する。
  **これはコード読解であって実測ではない。** 実測手段は段 2 が決める。
- **(P1-c)** G-B は consumed marker 228 件 (`.git/izanagi/s8b-holdout-admission-v1/consumed`、
  D811 当時は 118 件) と claim key 6 項目を実測して判定する。
- **(P1-d)** 実装 scope は D926 が列挙した面に限る。official 承認 gate 以外の新規 gate・検査・
  台帳・一般化は作らない (依頼の scope 指定)。
- **(P1-e)** 実装は submit 側・job script 側・driver 側が 1 つの承認契約を跨ぐので、段 5 は
  分割せず 1 単位にする。

## 覆った前提 (段 4 で再裁定する)

- T-1942 の記述「判定床 0.030 は read-heavy を含まない」は、`s8a_trigger_sweep.py:111-113` の
  「read-heavy の 0.030 は rr95 実測 (within 0.19% / between 0.11%) で保守性を裏付けた」と
  食い違う。read-heavy が**一度も測られていない**のではなく、**旧環境で測って 0.030 が保守側だと
  確認済み**である可能性がある。主目的 (現行環境の official 実測) は変わらないが、
  「read-heavy を含まない」を成果物の主張に書いてはならない。

## 不変条件

- 規律 2 を緩めない。correctness gate・受理集合を広げる変更をしない。
- D926 が「変更しない」と名指しした 4 項目に触れない。
- mode の受け口 (env / argv / eval) を作らない。
- ゲートが赤なら投入せず、実測結果を記録して停止する。

## 成果物

- 実装: official 承認束縛 (投入器 + job script + driver) と、その正例・負例テスト。
- 実測: G-A / G-B のゲート実測記録 (insight)。緑なら official campaign 投入と床値。
- 記録: worklog / decisions / failures fragment、runbook 更新。

## 分割方針

段 5 は 1 単位。段 2 plan 1 本、段 3 敵対相談 2 本 (レンズ: 承認 gate の恒真化・bypass 面 /
ゲート実測の妥当性と親の一般化)、段 6 レビュー 2 本 + fix。

## 段 3 を受けた brief の訂正 (親、2026-09-01 18:55 JST)

- **(P1-c) は誤り。** 旧 `claims/` 36 件と `consumed/` 228 件は fresh reservation の衝突述語から
  除外されている (`s8b_holdout_admission.py:1618-1620`)。実際の衝突は
  `measurement-generation-claims/<generation_claim_digest>-<sha256(attempt_id)>.json` の
  `O_EXCL` 失敗だけで決まる (`同:1636-1647`)。G-B はそちらを測る。
  read-only 判定に残る TOCTOU は残余として明記する。
- **(P1-d) の scope は現行 staged transport と両立していない。** G-D (gates.md) を参照。
  段 4 で transport 方針を先に裁定するまで段 5 を開始しない。
- 段 2 の実測 snapshot: `measurement-generation-claims` 24 件、
  `measurement-generation-consumed` 192 件。
