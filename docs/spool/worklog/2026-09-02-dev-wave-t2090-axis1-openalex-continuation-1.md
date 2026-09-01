---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2090-axis1-openalex-continuation
seq: 1
title: [T-2090] 軸 1 OpenAlex の継続取得は無償枠ではなく条件 1 に塞がれていた — 取得も実装もせず裁定へ返す (docs のみ、branch worktree-dev-wave-t2090-axis1-openalex-continuation、実装差分ゼロ・変異 matrix 免除)
---

## 本文

- 依頼は「発行済みの再開点から無償枠の窓ごとに OpenAlex 78 leaf を継いで取り切る」だった。
  **前提が現物と食い違っており、取得を 1 request も行わずに裁定へ返す。**
- **実行環境はコード変更なしに再構成できた。** 実行器は `HEAD == d0ba65c01` を要求し
  (`validator.py` の登録検査)、再開点は `bundle_root` を絶対 path で束縛する
  (`run_axis1_search.py` の checkpoint 検査)。その worktree は消えていたので、登録 commit を
  detach した worktree を同じ絶対 path へ作り直し、bundle を復元した。登録検査が
  `passed: true` を返し、復元した `manifest.json` の SHA-256 は凍結記録の値と byte 単位で一致した。
  検査器は main 側 (D1317 の修正入り) を使う必要があり、**実行器は登録 commit の木・
  検査器は main の木・bundle は記録された絶対 path** の 3 点セットで実行も検査も成立する。
- **無償枠のゲートが窓をまたいで自己施錠していた。** 持続化された最後の観測
  (`remaining: 10`、2026-08-29 観測) が失効せず、`x-ratelimit-reset` は記録されるだけで
  判定に使われない。登録済み leaf を起動しても `request_count: 0` で `quota_reserve` 停止した (実測)。
- **しかし本当の blocker はその先にあった。** 頁の完走条件が 1 つでも落ちると
  `blocked_on_ruling` を返して leaf を終え、次 cursor へ進まず**後継 checkpoint も書かない**。
  OpenAlex の条件 1 は全枝で落ちる (前走行の診断が 92 頁すべてで順序のみの差を実測済み)。
  つまり枠を直しても、**各枝は最初の 1 頁で止まり、継続不能な証拠が積まれるだけ**である。
  T-2091 の裁定なしに T-2090 は着手できない。
- 段 3 の 2 レンズが独立にこの停止を指摘し、親が `runner.py` の当該分岐と
  `failure_result` の生成箇所を現物で追認した。
- 段 2 が採った案 (登録 commit を張り替え、bundle 内の checkpoint 束縛を artifact 単位へ緩める)
  には、段 3 が反例を出した — **manifest の commit だけを新しくすれば 3 束縛はすべて成立し、
  新しい成果物がゼロでも通る。** 内部の自己整合であって外部の登録事実への束縛ではない。
  規律 2 によりこの形では採らない。
- 予算の見積りも訂正した。1 窓の上限は 96 でなく **97 request**
  (`remaining=40` でも `40-30>=10` が真)。また OpenAlex 78 枝のうち **74 枝が独立 2 走必須**
  なので最低 154 request、2 窓以上を要する。契約が言う「5 日以上」は、現存する 92 頁の実測と
  74 本の 2 走義務からは支持されない (親が catalog で検算)。
- codex 子 3 本 (plan 1・consult 2、いずれも read-only、reasoning=xhigh)。
  rc はすべて 0、`check_codex_output.py` も 3 本とも rc=0。
  逐語は `output/insights/2026-09-02_t2090-axis1-continuation-blocked/`。
- 実装面の差分はゼロ。機械受理集合・凍結 bytes・proof chain・certified 選択はいずれも不変。
  既存 bundle の bytes も不変 (実測 probe が書いた checkpoint は破棄し、manifest SHA の再一致を確認)。
  変異 matrix は免除、受入全走は免除しない。

## 次の一手差分

### 更新

- [T-2090] **P2・T-2091 の裁定待ちで着手不能**: 軸 1 の OpenAlex 78 leaf を、
  発行済みの再開点から無償枠の窓ごとに継いで取り切る。**2026-09-02 に、無償枠ではなく
  完走条件 1 が継続を塞いでいることが判明した。** 実行器は条件が落ちた頁で
  `blocked_on_ruling` を返して leaf を終え、後継 checkpoint を書かないため、
  枠を直しても各枝は最初の 1 頁で止まる。T-2091 が決まるまで着手しない。
  無償枠の窓をまたぐ自己施錠 (持続化した観測が失効せず次窓で 1 request も出せない) も
  併せて直す必要がある。最低 154 request・2 窓以上 (74 枝が独立 2 走必須)。
  base: 9c69e8f7861b6915baf793d09b86c12580c7838a7118b127075733c453a15d90
- [T-2091] **P1・ユーザー裁定待ち・T-2090 を塞いでいる**: OpenAlex の条件 1 を
  `oqo` の順序非依存な比較へ改めるか。索引が順序を正規化する以上、順序つきの比較は構造的に
  充足不能である。改めるなら新しい amendment・新しい epoch・新しい query ID を要する。
  **2026-09-02 に、この裁定が T-2090 の前提であることが判明した** — 現行のままでは
  OpenAlex の全枝が最初の 1 頁で停止し、継続取得の経路が存在しない。
  base: 30a5cf20c909b7eec9219f32d5a506a397a72f58b5ff7d34ba17c90088591bb1
