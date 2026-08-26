---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1805-predicate-exec-proof
seq: 1
title: [T-1805] 宣言した述語が build と実走へ届いたことを証明する (コード、branch worktree-dev-wave-t1805-predicate-exec-proof)
---

## 本文

- **欠けていたのは意味解析ではなく照合先だった。** 既存の証拠は source の digest・tracked diff・
  tracked path を**観測して記録する**だけで、宣言から導いた期待値と突き合わせる経路がどこにも
  無かった。prologue に `return;` を挿しても、`izanagi_gate_pass` を別の実体で shadow しても、
  変わった値がそのまま正直に記録され、誰も拒否しない。実体化は宣言 (pinned commit +
  template patch + 正準述語) の決定的関数なので期待値は導ける。**非到達化と別変数分岐は
  意味解析なしで閉じられる**というのが本 wave の中核である。段 3 レンズ A と親が独立に同じ結論へ達した。
- **段 2 プランの結論を裁定で覆した。** プランは非到達化と別変数分岐を「狭めるが閉じない」と
  結論したが、これは規範的照合を検討していない過小評価だった。
- **関門の設置場所を 4 度変えた。** 共有 `prepare_cell` (S1 の 57 件が落ちる) →
  `prepared_binding` (下流 117 件が落ちる) → floor build 経路 (同) →
  `buildcache.build_v2` の内側 (テストが差し替える境界の内側)。
  **単体テストは実 build を注入で差し替えるので、実 I/O を要する関門を campaign コードへ置くと
  必ず落ちる。**関門はテストが差し替える境界の内側に置き、証拠の要求は receipt 境界へ一本化する。
- **親が 2 度、切り詰められた failure digest を根拠に主因を誤診した。** 焦点走の digest は
  117 件中 10 件しか描画しない (budget 49152 bytes)。`--tb=line` へ切り替えると描画が 44 件へ増え、
  1 nodeid の単独走で全文を採って初めて真因が判明した。焦点走の赤は 118 → 117 → 161 → 222 → 3 → 0 と推移した。
- **実装子が 2 度、S8b 固有の証拠要求を共有部品の必須引数にした。** 単位 A は共有実体化器へ、
  単位 B は `build_v2` の既定値なし必須引数へ。後者は `pipeline` 4 箇所と
  `b10_backoff_shape_sweep` 1 箇所を TypeError にする。いずれも受理集合の縮小ではなく
  他 campaign の**可用性の喪失**である。任意引数化し、未指定時は変更前と同一 digest になることを
  機械で固定した。
- **段 6 の敵対レビューが実在する欠陥 4 件を出した。** うち最重要は
  A→B→A が閉じていないこと — 関門は build 前に tree を照合し、compiler input manifest は
  build 後に pathname の bytes を hash するため、build 中だけ差し替えて戻せば両方を通る。
  **親が段 4 で sandbox 級の不変性を「脅威モデルに対して過剰」として落としたのは誤りだった。**
  D966 は A→B→A を閉じるべき経路として明示しており、脅威モデルに含まれていた。
  親 directory の書込禁止と root の dev/ino 前後照合で閉じ直し、残余は閉じないと明記した。
- **compiler input の検査が実 build を過剰拒否していた。** 実 depfile には system header と
  外部 dependency header が含まれ、いずれも snapshot の外にある。全 input を snapshot 内へ
  要求する形では正当な全 cell が拒否され、成果物が 1 件も作れない。実 build でしか出ない型で、
  段 6 レビュー B が静的に捕まえた。
- **oracle の `evaluate_fn` seam は build を 1 度も呼ばない評価を受理できる。**
  既存 oracle テストがその完走を契約として固定しているため実装を見送り、この seam を通る
  呼び手には関門を保証しないと docstring へ明記した。裁定へ返す。
- **依頼が示した編集面の重複前提を実測で訂正した。** `next_tasks_overlap.sh` の
  `git diff --name-only main` は worktree が main から遅れている分も拾うため、
  無関係な 14 worktree が `s8b_floor_campaign.py` を編集中に見えた。未 commit 差分だけで測ると
  生きた編集は 2 test file だけで、しかも相手の hunk (17〜97、559〜786) と本 wave の編集面
  (134〜152、440〜495、2040、10575 付近) は素集合だった。段 5 投入直前と受入直前に再測した。
- 親の実測: CCBench の compile 行は翻訳単位ごとに `-MD -MF <obj>.o.d` を出すので compiler が
  読んだ入力の完全一覧は取れるが、build dir 破棄後には残らない。実測に使った build dir は
  CMake 3.25 + g++-11 で、login node の cmake 3.22 とは別環境である (計算ノードとは未確認)。
- 設計判断は {{D:predicate-execution-proof-placement}}、失敗は
  {{F:truncated-failure-digest-misdiagnosis}} と {{F:shared-component-mandatory-evidence}} を参照。

## 次の一手差分

### 完了

- [T-1805] 宣言した述語が build と実走へ届いたことを正式受入が証明できるようにした。
  remaining: none
  base: 5f451e1bb3758e279140ca01fde658f5e7c0c784988c052dcbe4abef1bbc3791

### 新規

- {{T:abamba-residual-closure}} **P2・新規**: A→B→A の残余 (所有者自身による権限変更) を閉じるか、
  閉じないことを正式に受理するかを決める。read-only bind mount 等の手段と、計算ノードでの
  capability 実測が要る。
- {{T:oracle-evaluate-fn-seam}} **P2・ユーザー裁定待ち**: oracle の `evaluate_fn` seam が
  build 0 回の評価を `committed` にできる。既存テストがその完走を契約として固定しているため、
  seam を塞ぐには当該テストの所有と契約変更の裁定が要る。
- {{T:root-neutral-cache-identity}} **P3・ユーザー裁定待ち**: 正式 S8b では cache 同一性に
  絶対 source root が入り materializer が毎回一意 worktree を作るため、cache hit が起きない。
  root-neutral 化すると hit が起きるようになり再利用の受理集合が広がる。独立裁定が要る。
- {{T:compiler-input-real-build-control}} **P1・新規**: 計算ノードでの実 build 正例を 1 回取り、
  実 CMake が出す `DependInfo.cmake` と `.o.d` の形状で manifest 採取が通ることを実測する。
  本 wave では取れていない。
