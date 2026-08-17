---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t822-tautology-guards
seq: 1
title: 8c 正式受入の恒真保証 3 件のうち measurement_head 一致だけを閉じ、残る 2 件は前提欠落で裁定へ返す (コード + docs、branch worktree-dev-wave-t822-tautology-guards)
---

## 本文

**[T-822] の 3 件のうち閉じたのは (iii) だけである。** 6 report 間の `measurement_head` 一致検査を
acceptance (`trial_registry.assert_trial_registry_acceptance`) と standalone receipt verifier
(`s8c_acceptance_receipt.parse_acceptance_receipt_bytes`) の 2 層へ入れた。変更前は各 head を個別に
検証するだけで、6 trial が別 commit で測られた束をそのまま受理し、receipt の `trials[*]` が比較不能な
測定を 1 束として記録できた。現在 HEAD との一致は要求しない — 計測は main の進行より前でよく、
要求すれば正当な束を過剰に拒否する。差分は 97 行の純増で、既存テストの期待値は 1 件も変えていない。

**(i) Layer-3 chain の必須化と (ii) 宣言 arm の実走認証は実装しなかった。** 2026-08-11 の裁定
「閉じる」が未見だった前提欠落を段 2・段 3 が実コードで見つけた。どちらも今実装すると、恒真な assert か
正式 scale を偽る偽 positive になる。本タスク自身が恒真禁止を要求している以上、実装しないことが
その要求への忠実な帰結である。**[T-822] は完了にしない。**

- (i) の閂: 正式 holdout は `rr80` / `rr20` だが producer の `WORKLOADS` は `ycsb-a/b/c` だけで、
  `assert_campaign_layer3_chain` は cell workload が producer 閉集合にあることを要求する。必須化すると
  正式 6 report の受理集合が空になる。workload 名だけを足す案は、正式 freeze が両 holdout を
  1,000,000 records / 48 threads と定める一方 producer の campaign / perf / descriptor の 3 sink が
  100,000 / 4 を固定しているため、正式 scale で測ったと読める成果物を作る (規律 2)。さらに originless
  compatibility の 2 node が「no-build report が正式 acceptance を通る」を既存契約として pin しており、
  fixture 育成では両立しない。
- (ii) の閂: 実走 arm を示す field が現行 artifact に存在しない。manifest / registration /
  `launch_admission.binding.arm` / receipt の arm はすべて同一宣言のコピーで、`_campaign_for` も
  proposal path も invocation ID も arm を受け取らない。`OriginProducerInputs.enforcement_arm` は
  caller が渡す非空文字列で manifest arm と照合されない。閉じるには arm が実行を変える authority、
  とくに `off` の「凍結済み中立入力」の canonical bytes が要るが、設計文書に要求だけがあり実体がない。

**親 brief の前提 1 件が段 3 で反証された。** 親は「既存 acceptance fixture は全て `cells: []` なので
cells 非空条件は発火しない」と書いたが、`_complete_report` が直後に 1 cell へ上書きしており誤りだった。
`cells` 空と no-build は別概念である。段 4 で前提を撤回し、(i) の裁定根拠から外した。

**変異は probe → 本走の 2 段で行った。** 全件 SURVIVED 期待の probe で観測 node を集め、3 変異それぞれが
ちょうど 1 node を落とすことを確認してから完全集合として再登録し、本走で 3/3 KILLED を得た。M-3 は
「現在 HEAD と一致」への過剰強化変異であり、新設した過剰拒否防止の正例だけが検出する。既存正例は過去
head を使っていないため、この方向の防壁は新設 node が単独で担う。

**段 6 の敵対レビュー 2 本は must-fix ゼロだった。** nit 2 件 (段 5 報告の呼び手列挙漏れ、receipt 負例の
余分な commit 1 回) は成果物影響を書けないため nit のまま据え置いた。tracked な acceptance receipt は
既定 directory に 0 件で、既存 fixture・golden に mixed head が無いことをレビューが実データで確認した。

**親の argv 誤りで段 6 を 1 度捨てた。** review 段へ `--lane` を渡し、`--lane は --stage consult でだけ
指定できる` で 2 本とも即死した。`--lane` は consult 専用である。別名で再投入して回復した。

**親が待機中の経過時刻を推定で報告し、訂正した。** 実測せずに「10:00 / 11:00 / 12:00 JST」と書いたが、
実際には 09:41 JST で 6 分しか経っていなかった。以後は毎回 `date` で実測した。

## 次の一手差分

### 更新

- [T-822] **P2・一部完了 (2026-08-17) → 残る 2 件はユーザー裁定待ち**: 8c 正式受入の恒真保証 3 件のうち
  (iii) 6 report 間の `measurement_head` 一致検査は acceptance と standalone receipt の 2 層で閉じた
  (変異 3/3 KILLED)。(i) Layer-3 chain の必須化と (ii) 宣言 arm の実走認証は、2026-08-11 の裁定時に
  未見だった前提欠落のため実装できない。**恒真な assert を作るなという同タスクの要求ゆえに実装を
  見送っている。**(i) は正式 holdout `rr80` / `rr20` が producer の workload 閉集合に無く、名前だけ
  足すと正式 scale (1,000,000 records / 48 threads) を偽るため、{{T:s8c-formal-workload-profile}} が先に要る。
  (ii) は実走 arm を示す field が存在せず、`off` の中立入力の canonical bytes も無いため、
  {{T:s8c-arm-execution-authority}} が先に要る。**諮る点 = この 2 件を前提タスクの後へ送るか、
  別の閉じ方を採るか。**正本 =
  `output/insights/2026-08-17_t822-measurement-head-coherence/package.md`
  base: 048203ea77db56a980cc4bfb6d24815b1161936ec5ba2d7791cd963882ef0ef9

### 新規

- {{T:s8c-formal-workload-profile}} **P2・新規 ([T-822] (i) の前提)**: 正式 holdout `rr80` / `rr20` を
  producer の production profile として実装し、ratified freeze の正式 scale (1,000,000 records /
  48 threads) を campaign / perf / descriptor の 3 sink へ束縛する。探索 CLI の既定は `ycsb-a/b/c` の
  まま別定数で保つ。これが無いと [T-822] (i) の Layer-3 必須化は正式受理集合を空にするか、
  正式 scale を偽る偽 positive になる。C01 evaluator の `workload-projection-mismatch` snapshot と
  repo scan invariant の既知 hit 0 件契約に波及する。
- {{T:s8c-arm-execution-authority}} **P2・新規 ([T-822] (ii) の前提)**: arm (`on` / `off` / `swapped`) が
  実行を変える authority を定義・実装する。とくに `off` の「凍結済み中立入力」の canonical bytes は
  設計文書に要求だけがあり実体が無い。arm が選ぶ入力から sealed execution digest を導出し、descriptor・
  campaign identity・proposal bytes/path・invocation namespace・run-start・terminal report の各 sink で
  同じ digest を消費させる。これが無い限り acceptance 側の arm 検査は宣言値の往復照合にしかならず恒真である。
