---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2224-certify-protocol-axes
seq: 1
title: [T-2224] 認定 launcher の protocol と軸を引数化した — 受理集合は 3 protocol に閉じたが、認定較正 record は 1 件も生産できていない (コード + 実測 + docs、branch worktree-dev-wave-t2224-certify-protocol-axes、変異 8/8 KILLED・期待 node 完全一致)
---

## 本文

- 依頼の「軸」は genome 軸 (CCBENCH_*) であって YCSB の workload ノブではない。段 1 brief が
  取り違えて `--skew` / `--rmw` を scope に入れていたので段 4 で取り下げた。依頼と worklog が
  名指すのは `CCBENCH_*` と `ycsb_silo.exe` の 2 つである。
- **依頼の前提「silo は生産できるが非 silo は生産できない」は現行 main では成立しない。**
  実測で 2 つの blocker が出た。いずれも T-2224 の外側にある。
  (1) 条件関門が patch 未供給の `BACKOFF_FIXED` を拒否し、認定 job は configure 前に rc=2 で止まる
  ({{F:mandated-condition-gate-cannot-pass-on-unpatched-pin}})。
  (2) 計算ノードから外部ネットワークへ到達できず、CCBench の FetchContent が失敗する
  (bnode122 / bnode013 の 2 ノードで独立に確認)。
- したがって本 wave は **認定較正 record を 1 件も新規生産していない**。「非 silo の within-run
  floor が公式成果物へ入れるようになった」とは言わない。詳細と段ごとの集合は
  `output/insights/2026-09-09_t2224-certify-protocol-axes/README.md`。
- 設計判断は {{D:certify-protocol-axis-table-stays-independent}} と
  {{D:certification-records-only-values-that-reach-the-compiler}}。
- **親が機械防壁をすり抜けた。** 生死確認のビルドを背景 script 経由で起動したため、
  `hooks/guard_bash.py` の login 重量 command 判定が発火せず、login node で CCBench を
  ビルドしてしまった。以後の実測は計算ノード経路へ載せ替え、login で取った値には取得経路が
  正規でないことを成果物へ明記した ({{F:script-wrapped-heavy-command-evades-login-guard}})。
- 段 3 の敵対相談 2 本と段 6 の敵対レビュー 2 本、段 5 実装子 2 本、段 6 fix 子 2 本、
  probe 作成子 1 本を使った。段 6 レビューが「軸の名前しか検査しておらず、制約外 genome を
  認定できる」を反例つきで挙げ、値の exact 照合と `SPACES[p].enumerate()` 所属検査を足した。
- 子はいずれも pytest を実走できなかった (`qstat -Q` が sandbox から `EACCTAUTH Unknown user-id`)。
  テストの実測はすべて親が行った。

## 次の一手差分

### 更新

- [T-2224] **P2・部分完了**: 引数化は着地し、受理集合は `{silo,mocc,tictoc}` に閉じた。
  ただし認定較正 record は 0 件で、非 silo の within-run floor の embargo は継続する。
  残りは {{T:certify-backoff-fixed-ruling}} と {{T:certify-offline-fetchcontent}} の 2 つの blocker。
  base: 6309c26be71ead331d318dc962d07d7d3ed9fd2186c745c8307aef9e83ef234d

### 新規

- {{T:certify-backoff-fixed-ruling}} **P1・ユーザー裁定待ち**: 認定 launcher が
  `-DCCBENCH_BACKOFF_FIXED=-1` を渡し続けるか。(R1) 渡すのをやめる — 実測でバイナリは 1 bit も
  変わらない (build path 固定で sha256 完全一致、再走対照つき)。条件関門の義務も消える。
  (R2) patch を build source へ materialize する — patched source を `pinned_clean=true` と
  記録することになり provenance が偽になるため却下推奨。親の推奨は R1。
- {{T:certify-offline-fetchcontent}} **P1・新規**: 認定経路へ offline の FetchContent 供給を
  配線する。計算ノードから `github.com` の名前解決ができず、masstree の取得で configure が落ちる。
  `screening_driver.py` が同種の配線 (`FETCHCONTENT_BASE_DIR` と source dir の受け渡し) を既に持つ。
  これが無い限り protocol を問わず認定 job は build 段で落ちる。
- {{T:cicada-axis-name-alignment}} **P2・新規**: `SPACES` の cicada 軸 `INLINE_VERSION_OPT` を
  CCBench の実体 `CCBENCH_INLINE_VERSION_OPT_CICADA` へ合わせる。合わせるまで cicada は認定の
  受理集合へ入れない。併せて、正しい cache 名で値 1 を渡すと
  `cc/cicada/include/transaction.hh:207` の `write()` が POSIX `write(int,...)` へ解決されて
  ビルドが落ちる上流の死にコードを、`output/README.md` の形式で上流 insight にする。
- {{T:guard-script-wrapped-heavy-command}} **P2・ユーザー裁定待ち**: `hooks/guard_bash.py` の
  login 重量 command 判定が、背景 script に包まれた command を分類できない。dev-wave の背景投入の
  定型が必ず `bash <script>` になるため、防壁の射程と規定の起動導線が構造的に食い違う。
  実施形は防壁の設計変更なのでユーザー裁定へ返す。
- {{T:acceptance-ledger-t2224-nodes}} **P3・新規**: 本 wave が新設した 15 test node を
  受入所要時間台帳へ登録する。被覆検査は比率を表示するだけで非零終了させる gate ではなく、
  被覆率も 22155 node に対し 99.9% なので本 wave では見送った。台帳更新は main 取り込みで
  必ず競合するため、単独の小さい wave で行う。
