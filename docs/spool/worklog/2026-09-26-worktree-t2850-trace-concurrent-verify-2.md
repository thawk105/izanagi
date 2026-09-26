---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: worktree-t2850-trace-concurrent-verify
seq: 2
title: [T-2850] 試走 v2 (cohort t2850-trial-v2、S1-wh の 3 block・18 job) をユーザーの計算確認で発効させ、同時検査の実装に固定して 18 job をまとめて投入した。LLM 3 系列の親は再開型の起動器で動かしている (docs、branch worktree-t2850-trace-concurrent-verify)
---

## 本文

- ユーザー裁定 (2026-09-26、前 entry の最終報告への回答): 試走 3 block (見積り 22.2〜40.5 node 時間、LLM の待ち 1.9〜19.5 時間) の投入を「いいよ」で認めた。発効の決定は {{D:trial-v2-effect}}。
- 固定 commit は本実装を取り込んだ main の fold commit `299aa022e`。その後 main に入った別 wave の変更 (条件の意味検査など) は試走に混ぜない。
- job ごとに repo 外の checkout を 1 本 (block 1 は 6 job で 1 本を共有していた)。作成は lustre 上で 1 本約 6 分かかり、直列 1 本 + 並行 3 本で 19 本を 22:04〜22:31 JST (27 分) で揃えた。
- 18 job は 22:34 JST にまとめて投入 (request 30122〜30139、insight §6 の表)。block の間隔は置いていない (D2249)。LLM 3 系列 (30124・30128・30134) の親は login の起動器が request ごとに起こす。
- 並走 session との調整: B-5 v2 の準備 wave から同時検査の箇所 (p3_s4_loop.py の write-heavy 限定・pipeline.py の静定上限) を balanced へ広げる可能性の照会があり、本 wave は編集しないこと、balanced の静定上限は未測定であることを返した。

## 次の一手差分

### 更新

- [T-2850] **P1 (VLDB 差分分析 P3: 探索の独立反復と費用・成果の曲線)**: 事前登録 v1 `docs/search-repetition-trial-preregistration.md` (D2231)・追補 1・追補 2 で、
  試走 v2 (cohort `t2850-trial-v2`、S1-wh × 5 手法 × 3 系列 + block job 3 = 18 job) を {{D:trial-v2-effect}} で発効させ、2026-09-26 22:34 JST に投入した
  (request 30122〜30139、固定 commit `299aa022e`、repo 外の job dir `dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2/`、LLM 親の起動器は login で稼働)。
  見積り 22.2〜40.5 node 時間、費用上限 200。旧 block 1 (cohort `t2850-trial-v1`) は予備走。残りは 4 つ。
  (1) 試走の終了を待ち、欠測 (品質欠測・LLM の週次上限・`verify-local-unavailable`) と job Elapse の総和を確かめる。総和が見積りの上側を超えそうなら新しい投入を止めて再確認する。
  (2) 試走の後: 事前登録 §8 の規則で T_c・対差 SD・課題の集合・系列数を計算して追補に書き、本比較の上限をユーザー確認してから投入する。
  (3) 案 (a) (LLM の待ちを node の外へ) は、試走の LLM 待ちの実測を見てから、残る待ちの node 時間が導入費を上回るときだけ設計する。
  (4) MOCC (S2)・policy IR (S3) は、その空間の最初の生成より前の追補で足す。read-heavy・balanced へ同時検査を広げるときは記憶量と静定の上限を別に測る (B-5 v2 も同じ部品を使いうる、D2249 項 1)。
  **生成・選択には [T-2851] の留保条件を使わない** (`docs/unseen-condition-transfer-preregistration.md` §2.3・§3、D2223)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P3。
  base: 60d864fbaaf1af17b4617c7de49353e6315b57d714f1da4d057ffd5df2c800fe
