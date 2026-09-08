---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2423-floor-protocol-identity
seq: 1
title: [T-2423] 権威 floor の identity 要素 protocol を build receipt の canonical genome から導出した — 依頼の択一 (a)/(b) は「receipt から導出できない」という偽の前提に立っていた (コード + テスト、branch worktree-dev-wave-t2423-floor-protocol-identity、変異 baseline PASSED・KILLED 7・SURVIVED 0・MISMATCH 0・期待 node 完全一致 7/7)
---

## 本文

依頼は「protocol が凍結 spec に無く build receipt からも導出できない」を前提に (a) spec へ足す / (b) D1641 を
4 要素へ訂正 の択一を段 4 で裁定せよと求めた。段 3 の敵対相談 (レンズ A) が前提を反証し、親が現物で確認した:
receipt の `binding.genome_canonical` は `protocol|flags` 形で binary に束縛され、共有 helper
`protocol_from_floor_genome()` も既存だった。issuer が失敗していたのは record の top-level に `protocol` key を
探していたからで、テストは validator の monkeypatch で偽 key を通していた。段 4 は択一の外の (c)
「receipt 由来の protocol 導出」を採り ({{D:b4-floor-protocol-from-receipt-genome}})、凍結 spec・driver・
D1641 を変えなかった。**ユーザーが (a) を望むなら再裁定で戻せる。** 一次資料は
`output/insights/2026-09-08_t2423-floor-protocol-identity/`。

- 段 6 レンズ C の must-fix 主張「`mocc|A|B=1` が helper を通る」は親の実測で refuted (それは `Genome.canonical()` の
  正準形そのもの)。Genome の flag 名文法を model 側で締めるかは裁定パッケージ候補。
- 段 6 レンズ C / D が「`missing.append` 削除型の M8 は StopIteration で帰属が壊れる」を指摘 → M8 を
  「`protocol_failed` を見ない」型へ直し、それを殺す部分失敗の負例を fix1 で追加した。
- 段 5 実装子は sandbox の PBS 認証失敗 (`EACCTAUTH`) で test を実走できず、親が計算ノードで焦点走
  (5 file、fix1 後 321 passed)。
- 受入 attempt 1 は `stage=preflight-index-flags rc=70 source_rc=128` で停止した。原因は本 wave の差分ではなく
  main `c12e25078` の `.codex/worktrees/*` gitlink 混入で、`git submodule foreach --recursive` が
  `No url found for submodule path` を返す。同じ根本原因を `dev-wave-research-gate` が
  `prerun-fingerprint` 段で先に観測し、failures fragment へ登録のうえ `48837186c` (index からの除去 +
  既知違反登録) と `cf837838a` (母集団 pin の追従) で是正した。本 wave は二重登録を避け、
  観測した段名の違いだけをここに残す。取り込み前に別セッションの是正を敵対監査した (規律 6)。
- 受入所要台帳は編集していない (F903 の衝突点を避ける。改名・追加した issuer test 6 nodeid は未登録で既定 cost、
  被覆は 99.97% で 90% gate は割らない)。
- 工数: codex 子 = plan 1、consult 3、author 1、review 2、fix 1 (全て gpt-5.6-sol / xhigh、全件 accepted)。

## 次の一手差分

### 完了

- [T-2423] 権威 floor の identity 要素 protocol を build receipt の canonical genome から導出する形で閉じた
  (依頼の (a)/(b) は前提が偽で、択一の外の (c) を採用)。凍結 spec・D1641 は不変。
  remaining: none
  base: 98ef45ca47714e2e68b9884f8224f20c8d7a2f58f0cd29fe244189f8768e16c6

### 新規

- {{T:genome-flag-name-grammar}} **P3・新規**: `Genome.canonical()` は flag 名に `|` `,` `=` を含む値を拒否せず、
  `mocc|A|B=1` のような文字列も正準形になる。issuer は共有 helper の解釈に従うので単独では締めない。
  model 側で flag 名文法を定めるか、protocol の許可リスト / CCBench source 束縛 (D1696 再訪条件未成立) と
  併せて裁定パッケージにする。
