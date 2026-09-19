---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2790-t1259-scan-timeout
seq: 1
title: [T-2790] t1259 受入 fixture の git 走査 timeout を fixture 局所の候補値 120 秒にし、受入並列下の走査所要分布で採用値を決めた (コード + docs、branch worktree-dev-wave-t2790-t1259-scan-timeout)
---

## 本文

- 裁定 D2148 項 12 (D1877 → D1936 項 43 の鎖) に従い、production の 30 秒を変えずに受入 fixture (t1259 の module snapshot) の git 4 呼び出しの
  待機上限だけを候補値 120 秒にした。実装は Codex author (gpt-6-astra、medium、11 call、414 秒)、commit 4208bf332。
- 段 1 前の前提実測で裁定時に未見の事実が出た: 252e24b4f (2026-09-18 23:47 JST、T-2780 wave) 以前は t1259 が xdist worker へ個別分散し
  1 shard で module fixture の実走査が走ごと 42〜46 回実行されていた。以後は 1 回で、受入 24 走の setup error は 0。裁定 (fixture 局所の上限
  + 実測) はそのまま有効なので wave を続けた。因果の分離ではなく grouping 後の改善の観測として記録した (段 6 レビュー B の must-fix)。
- 段構成は軽量版 (段 2・3 省略、段 6 レビュー 2 本 medium、fix 子なし)。レビュー A/B の must-fix は 6 件すべて登録・記録の訂正
  (変異 M2 の期待集合、P1 の断定縮小、母集団の権威、error 件数≠打ち切り走査数、呼び出し単位/合計/lock deadline の区別、P3 の根拠表) で
  実装面の must-fix は 0。過剰との指摘は棄却。
- 変異 matrix (独立 clone、dispatch): M0 等価 SURVIVED / M1 上限 0 KILLED / M2 走査省略 KILLED、MISMATCH 0。補助 (DW-O19) で t1259 module
  は M2 形で 16 failed。fixture の実走査の検査力は `head` と `source_sha256` だけ (他 3 field は上書き) と明記。
- 分布・採用値・限界は insight `output/insights/2026-09-20/t2790-t1259-scan-timeout/README.md` §2・§6・§7、F945 追補は同 wave の
  failures fragment。焦点走で出た p3_s4_loop identity 赤 1 件は差分到達不能・単独再走緑 = 非帰属。
- 採用値 120 秒 (git 呼び出しごと)。根拠: 接尾あり regime の受入 26 走の in-situ max 24.5 秒 (本 wave の計測走 9.2 秒、25,327 passed /
  赤 0、child-green)、login sampler 11 sample の呼び出し別 max 6.3 秒 (合計 max 11.8 秒、他 leader 1〜2 本並走)。120 秒は in-situ max の
  4.9 倍、除去済み前 regime の非打ち切り max 58.9 秒の 2 倍。他 session ≥ 3 本並走・load1 > 60 は未観測条件で、超過が出たら値を上げず
  F945 へ再発追記して再検討する。
- 工数: author 1、review 2 (read-only medium)、計算ノード job = 焦点走 4 + 変異 4 走 + 受入計測走 1。最終受入の成否はこの記録後の
  共通受領証で確定する。

## 次の一手差分

### 完了

- [T-2790] fixture 局所の待機上限 (候補 120 秒) を実装し、受入並列下の走査所要分布 (前後 regime、in-situ、login sampler) と採用値・
  限界を insight と F945 追補に記録した。production timeout・走査対象・拒否論理は不変。
  remaining: none
  base: 434164d3419987ac77dbbf8dc95da44142085c500ef93ffabf1a86a1d5df9a5d

### 新規

- {{T:t1259-fixture-scan-duration-record}} **P3・新規**: t1259 受入 fixture の呼び出し別走査所要と実行識別 (worker・host) を junit に残す
  記録を設計する (現状は testcase time の代理に依存。T-2790 insight §9)。
