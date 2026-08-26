---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-b10-balanced-profile
seq: 3
title: B-10 の balanced 機序 profile を Pegasus で取得し、要求 define が黙って無視される欠陥を独立 2 例まで確定した (コード + 計測 + docs、branch worktree-dev-wave-b10-balanced-profile、変異 matrix = baseline PASSED・KILLED 13・SURVIVED 1 (登録どおりの等価変異)・MISMATCH 0)
---

## 本文

- ユーザー起票。paper-story §8 B-10 の未取得 4 項目のうち「balanced workload の profile」を
  取得した。一次資料は `output/insights/2026-08-26_b10-balanced-profile/README.md`、
  成果物は `output/env/pegasus/profile/backoff_profile_t48_skew0p9_rr50.{json,md}`。
  判定は事前登録どおり condition-met (評価帯 0-10us で total_ipc 散布 57.0% に対し
  useful_ipc 散布 4.3%、bar 4.4%)。**balanced の headline 利得そのものを説明したとは
  主張しない** ({{D:balanced-profile-preregistered-band}} の理由 3 点)。
- **この wave の最大の成果は profile ではなく、要求した build define が黙って無視されうる
  という発見である** ({{F:silent-ignored-build-define}})。段 6 レビューが追加させた
  「perf report に対象 symbol が出ること」の gate が、まったく別の原因で発火して止めた。
  gate が無ければ 6 点とも実質同条件の値が機序 profile になっていた。
- **並行 wave `dev-wave-b10-overthrottle-grid` と相互照会し、独立 2 例まで確定した。**
  向こうは同型を自分の 3 driver で再現し (`backoff_sweep.py` を含む)、投入直前に止めた。
  さらに既存 3 系列の WAL 全点集計で、歴史的成果物は無事だがそれを保証していたのは driver では
  なく起動時の作業ツリーの状態だったことを示した。**族一般化 (要求 define の正例検査を全 driver へ
  義務化するか) はユーザー裁定へ送る。「当てる」の義務化と「効いたことを確かめる」の義務化は
  別物で、後者が本体・前者はその手段。**
- **相互照会で双方の無駄走行を防いだ。** こちらから渡したのは (1) 計算ノードで perf が動く
  実測 (環境 runbook が「未確認」と記していた点)、(2) proxy 経由なら取得できること、
  (3) define が黙って無視される欠陥。向こうから受けたのは (1) 計測前に関門を通せ、
  (2) 在庫を閉じる変更は稼働 wave と衝突する (受入全走でしか出ない)、
  (3) 着地済み spool fragment を編集すると受入が terminal 停止する、
  (4) 所要台帳の網羅率が閾値割れしていた件。**(4) はこちらの「凍結は 8 suite 限定」という
  読みが向こうの `--add-only` 実装につながり、main で解消された。**
- **親の見積りが実測と桁で外れた事例が 1 件。** 計測所要を「1〜2 時間」と報告したが、実測は
  ビルド一式で 236 秒だった。build cap (900 秒 × 7 点) からの机上計算で、既に手元にあった
  dispatch 受領証の Elapse を見ていなかった。ユーザーの指摘で訂正した。あわせて
  「測定は分散できない」も言い過ぎで、同一環境である以上、設計として分ける場合は成立する。
- 本走は 6 回投入し 5 回は値が出る前に検査が止めたが、**5 時間枠は 1 度も浪費していない**
  (最長 241 秒)。うち 1 回は親の指示誤り (無参照の関数は emit されないのに、無 backoff 点にも
  symbol の実在を要求した)。
- 段 6 の fix は 7 巡。うち 5 巡は親の実機 blocker (DW-O16 の 3 巡上限とは別枠)。
- 子の工数: codex 子 11 本 (plan 1 / consult 2 / author 1 / review 2 / fix 5)。
  いずれも `gpt-5.6-sol` / `reasoning=xhigh`。

## 次の一手差分

### 新規

- {{T:balanced-stock-inline-control}} **P2・新規**: balanced の headline 利得を説明するには、
  同一 env / 同一 source の stock-inline 対照が要る。診断 build の値は D20 で headline 非適格
  なので、対照は別走で取る。
- {{T:build-define-positive-control-family}} **P1・ユーザー裁定待ち**: patch 供給の define を
  build へ渡す driver 全体へ、効いたことの正例検査を義務化するか
  ({{F:silent-ignored-build-define}} の族一般化)。独立 2 例は揃っている。
- {{T:legacy-build-offline-source-dirs}} **P2・新規**: legacy build 経路は
  `FETCHCONTENT_SOURCE_DIR_*` を渡せず、計算ノードでは proxy 経由の取得が事実上の前提になる。
  `build_v2` へ寄せるかは境界を跨ぐ設計判断なので裁定が要る。
