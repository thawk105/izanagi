---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1777-interleaved-impl
seq: 1
title: [T-1777] A-1 交互配置の coordinator は着地済みだった — 依頼の前提を覆し、pilot を止めている本当の関門を特定した (docs のみ、branch worktree-dev-wave-t1777-interleaved-impl、実装面 0・変異 matrix 免除)
---

## 本文

- **依頼は「境界の棚卸しと配置の確定は完了済みで、残るのは実装」として起票されたが、
  着手直前の local main `08a17b3b3` では coordinator が既に全着地していた。** 段 1 の前提実測で
  判明し、段 4 で「実装面の純増ゼロ = 実装しない」と裁定して `4→7→8→9` を採った。
- 着地させたのは T-2074 の wave である。同 wave は estimand の揃え直し (D1262) と
  均衡配置 (D1295) を同じ変更単位で実装していた
  (`ed61448f6` / `73c6473fa` / `a1f91bdbe`、いずれも main の祖先)。
- **着地と記録がずれたまま carry され続けたのが原因である。** worklog 1142 (T-2074) の本文は
  均衡配置の着地を書かず、次の一手の T-1777 も 1091 以来 carry stub のままだった。
  結果として、完了済みの作業を実装依頼として再提示しうる状態が続いていた。
- **「実装は着地済み」という判定は誤ると重い** — 実在する実装の穴を docs の書き換えだけで
  閉じたことにしてしまう。そこで段 3 相当の独立レンズ 1 本 (read-only codex、reasoning=xhigh) に
  親の判定そのものを検査させた。**この検証が親の「純増ゼロ」を支持せず、real 所見を 2 件出した。**
  子を省いていれば、どちらも見落としたまま「完了」と記録していた。
  1. **pilot の事前登録が未凍結で、pilot study を起動できない。** policy の `preregistration` が
     `{path: null, sha256: null}` のままで、readiness gate が submit も measure も必ず拒否する。
     これは事故ではなく意図された未完成で、拒否を固定する正例テストまである。
     **T-1777 の手順 (1)〜(5) はこの作業を誰にも割り当てていなかった** — (4) は pilot と sizing の
     後に作る「別 study」の事前登録である。次の一手へ (1.5) として明示的に足した。
  2. **中断の terminal-invalid recovery が `build_done` 前の窓でしか発火しない。**
     D1295 項目 7 の文言に対して実装が狭い。ただし correctness の穴ではない — 例外は
     fail-closed で、campaign loop 側も独立に再評価を拒否するため、不正な結果は admit されない。
- どちらも本 wave の scope 外として実装せず、裁定パッケージでユーザーへ返した。1 は凍結成果物の
  新規発行を伴い `DW-O09` の読了期限 (段 1 前) を過ぎているため、取り込むなら段 1 からの
  別 wave になる。
- **land 競合の最中に着地したユーザー裁定 3 件を読んで、裁定パッケージの推奨を書き直した。**
  段 4 は 3 件より前だったので、`DW-S04` の「段 4 直前に裁定 inbox を再走査する」に従って
  主題で照合した。所見が real であること自体は変わっていない。
  - D1383 (B-4 事前登録の床値欄) と D1391 (承認 record) が「AI は準備・手続き案・測定計画を
    人間承認の直前まで用意し、発効だけ人間の手番」という工程分割を確定していた。当初は
    「事前登録は研究上の約束なので丸ごと返す」と書いていたが、既裁定と整合しないので改めた。
    AI が本文と差し込み手続きを用意し、発効だけユーザーが行う形にする。
  - D1388 が「enforcement source closure の束縛を live resume の互換のために緩めない。実害が
    再走時間だけなら受理集合を広げる代償に見合わない」と裁定していた。所見 2 は同じ天秤に
    かかるので、実装方針を先に決め打ちせず「直す価値があるか」から問う形へ改めた。
- **D1295 項目 4 の contrast と現行実装の食い違いは、決定間の矛盾ではない**と親が裁定した。
  後発の D1262 が対の中身を `static10 − adaptive` から `variant − baseline` へ更新したもので、
  D1295 が守ろうとした「contrast を物理順によらず役割で決める」不変条件は保たれている。
  子はここを「決定間の優先関係なしには確定できない」として不明に置いた。記録しておかないと
  次の wave がコード欠陥として再提起する。
- 実装面の差分が 0 なので変異 matrix は免除した (DW-S04)。受入全走は免除せず実走した。

## 次の一手差分

### 更新

- [T-1777] **P2・計測待ち**: A-1 の対の配置。**(1) の coordinator 実装は着地済みである**
  (2026-09-01、`08a17b3b3` で実測。閉包 4 member・driver profile・スケジュール・collector・
  投入 selector・job script。根拠と D1295 7 項目の対応表は insight
  `2026-09-01_t1777-implementation-landed`)。残る手順は次のとおり。
  **(1.5) pilot の事前登録を用意し、発効させる** — `v3-pilot.json` の `preregistration` が
  未束縛のため readiness gate が submit / measure を必ず拒否する。**ここが pilot を止めている
  関門であり、旧 (1)〜(5) はこの段を割り当てていなかった。** D1383 / D1391 の工程分割に従い、
  AI が本文 (D1296 の 60 対/workload・対 SD とブロック実効 sigma・判定式・再標本化、および
  D1295 項目 5 の「5-rep 均衡スケジュール下での差」という限定文言) と、path / sha256 を
  `preregistration` 欄へ差し込む手続きの案を人間承認の直前まで用意し、**発効はユーザーが行う**。
  凍結成果物の新規発行なので `DW-O08`/`DW-O09`/`DW-O10` を段 1 前に読む wave が要る。
  (2) その機構で pilot を 60 対/workload 測る (未走)。(3) pilot から対 SD とブロック実効 sigma を
  出し、独立 seed の simulation で反復数を認証する。(4) `paper_story_a1_paired.v3-sized.json` と
  その事前登録を凍結する (未作成)。(5) 本走を投入する。
  凍結済みの現行 study は据え置き、bytes を変えない。
  base: 64503f586e5b9937fafd34d8e9636d7c505fd872692a9e8aeca3b3504641b687

### 新規

- {{T:a1-balanced5-interrupt-recovery-scope}} **P3・新規**: balanced5 の中断 recovery の射程を
  D1295 項目 7 まで広げる。現行は active attempt の開始後に `build_done` / `verify_done` /
  `bench_done` があると例外になり、terminal-invalid abort の生成へ到達しない
  (`orchestrator/campaign/wal.py:1896-1983`)。正例テストの fixture も `build_start` しか
  記録しておらず、bench 中断・片側 commit が被覆されていない。
  **correctness の穴ではない** — 例外は fail-closed で、`loop.py:381-399` も独立に再評価を
  拒否するため不正な結果は admit されない。失われるのは「invalid であった」という WAL 上の
  耐久記録の形だけである。
  **まず「直す価値があるか」から問う。** D1388 が「実害が再走時間だけなら受理集合を広げる
  代償に見合わない」と裁定しており、本項は同じ天秤にかかる (現行の実害も中断した pilot を
  測り直す時間だけである)。直すと決めた場合だけ、受理集合の変更として変異事前登録を伴う
  独立 wave にする。pilot の起動を妨げないので [T-1777] の (1.5) より後でよい。
  一次資料は insight `2026-09-01_t1777-implementation-landed` の §6.2 と §7.2。
