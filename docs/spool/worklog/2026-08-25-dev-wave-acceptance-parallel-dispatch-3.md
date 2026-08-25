---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-acceptance-parallel-dispatch
seq: 3
title: 受入全走の律速を 4 相へ分解し、並列化・分散ジョブ化・bytecode cache の 3 案をすべて実測で反証した (docs のみ、実装差分ゼロ、branch worktree-dev-wave-acceptance-parallel-dispatch)
---

## 本文

- ユーザー依頼は「受入全走のボトルネックを確認し、並列化・分散ジョブ化で改善できそうなら
  改善する。リワードハック禁止」だった。**改善できる並列化は無いという結論を実測で返した。**
  実装差分はゼロである。
- 相分解と 3 つの反証は {{D:acceptance-wall-decomposition}} と
  {{D:pytest-rewrite-cache-already-warm}} に凍結した。
- **親の当初仮説は親自身が反証した。** 親は「48 worker が同じ source を独立に compile している。
  repo 外の共有 cache を read 専用で与えれば 34 秒縮む」と裁定しかけたが、段 5 の直前に
  実在 worktree 49 個の cache 状態を全数調査し、**実受入は最初から warm で走っている**ことを
  確定して撤回した。probe を新品 worktree で測ったことによる artifact だった
  ({{F:fresh-worktree-probe-misrepresents-production}})。
- **段 3 の 2 レンズは独立に NO-GO で一致し、親が気づいていない正しさの穴を 3 件出した。**
  (a) rewrite 結果は source だけでなく `Config` の `enable_assertion_pass_hook` にも依存するため、
  pytest version だけを identity にした generation は別設定の bytecode を共有しうる。
  (b) 走行前の sidecar 検証では F52 型 TOCTOU が閉じない。受入の tree fingerprint は走行前後の
  境界しか見ないので、走行中の同一長・同一秒の往復を観測できない。
  (c) rewrite cache を作るには `sys.dont_write_bytecode` を解除する writer が要り、
  「子に bytecode を書かせない」現行の防壁と両立しない。
- **レンズ B は親の実測値の帰属誤りも見つけた。** 8 worker と 24 worker の値が逆で、
  正しくは 8=36.57 秒 / 24=41.00 秒 / 48=49.32 秒である。親は「固定 overhead は worker 数に
  ほぼ依らない」と一般化していたが、実際は 8→48 で 12.75 秒 (+34.9%) 増える競合だった。
  親が dispatch receipt の `request.json` と job stdout を join して訂正した
  ({{F:parallel-probe-output-mislabelled}})。
- **レンズ B は hit 率も実データで測った。** 全 `.py` の内容 digest で cache generation を
  鍵付ける設計の実 hit 率は 8.0% (直近 3 日の受入受領証 112 件を tested tip の Python tree で比較)。
  損益分岐は 24〜33% なので、採用すれば 1 走あたり平均で悪化する。
- **新しい未帰属ブロックが露出した。** warm な固定 overhead は 48 worker で 15.40 秒なのに、
  実受入の残余 (pytest wall − pole) は shard-0 で 62 秒、shard-1 で 47 秒ある。差の
  約 32〜47 秒は compile でも pole でもない。候補は受入 plugin の処理、report.json (5MB) と
  junit の書き出し、`observed_universe` 16033 件の記録、per-item の xdist 往復、worker 終端。
  本 wave では帰属していない。
- **ユーザー裁定へ返す件**: login preflight は中央値 96 秒で全体の約 20% を占め、その主部は
  全史 provenance 監査 (単体実測 39 秒 / 48 秒、5782 commit) が 1 走で 1〜2 本走ることである。
  冗長を削る案は 2 つあるが、どちらも親が単独で決めるべきでない。
  (A1)「main より遅れているときは claim 前の監査を省く」は監査の被覆を落とさず、
  merge 後の監査が同じ commit 範囲を dispatch より前に歩くので計算資源も無駄にしないが、
  `test_preclaim_history_provenance_failure_never_claims_and_returns_reason` が pin する
  「壊れた履歴では lease を claim しない」という明示の性質を壊す。
  (A2)「merge 後の監査を入力不変なら省く」は性質を保つが、checker の入力閉包
  (known_violations 木・`docs/ai-provenance.md`・checker 自身・grafts) の列挙が要る。
  閉包を 1 つ落とせば gate が黙って走らなくなるため、リワードハック禁止の依頼下で
  親が単独採用してよい形ではない。
- 工数: codex 子 3 本 (plan 1、consult 2)。実装子と fix 子は不要 (実装しない裁定)。
  変異 matrix は実装差分ゼロのため免除。受入全走は免除せず実走した。
- 親が待ち手の argv を 1 度誤った (`--artifact-file` 欠落で rc=2)。子は生存しており、
  張り直して実害なし。**段 8 はこの明確化を `DW-O01` へ足す案を不採用にした。**
  同節の waiter 行は可視 top-level exact 1 件として pin されており、48 bytes の追記で
  `docs/dev-wave/**` の L1.5 footprint 予算 9566 bytes を 47 bytes 超過する (実測)。
  予算値の引き上げは通常の自己改善の対象外であり、fail-closed で実害が再投入のみに
  留まったことも不採用の根拠にした。候補は他に無く、command と reference の編集はゼロである。

## 次の一手差分

### 新規

- {{T:acceptance-post-collection-residual}} **P2・新規**: 受入 shard の残余
  (pytest wall − pole、shard-0 で 62 秒 / shard-1 で 47 秒) のうち、warm な固定 overhead
  15.40 秒を超える約 32〜47 秒を帰属する。候補は受入 plugin、report.json と junit の書き出し、
  `observed_universe` 16033 件の記録、per-item の xdist 往復、worker 終端。
  内部 shard 形式は追加 argv を rc=16 で拒むため、切り分けには計装が要る。
- {{T:acceptance-preflight-provenance-redundancy}} **P1・ユーザー裁定待ち**: login preflight の
  全史 provenance 監査 2 本の冗長 (各 39〜48 秒、preflight 中央値 96 秒 = 全体の約 20%) を
  削るかどうか。A1 は tested property を壊し、A2 は gate の入力閉包の列挙を要する。
  {{D:acceptance-wall-decomposition}} の相分解を根拠に、どちらを採るか / 現状維持かを決める。
