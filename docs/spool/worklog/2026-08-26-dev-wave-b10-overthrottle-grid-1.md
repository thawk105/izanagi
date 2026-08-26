---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-b10-overthrottle-grid
seq: 1
title: 静的 backoff の計測格子を適応機構の全離散状態へ広げ、過抑制の開始点とピーク位置を機械判定する経路を作った (コード + テスト、branch worktree-dev-wave-b10-overthrottle-grid、変異 matrix = baseline PASSED・17/17 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

**この wave は計測機構と判定規則までで、実測はまだ 1 度も取っていない。** 投入 script が
本チェックアウト側の Pegasus 登録簿を読む hook に拒否されるため、登録が main へ着地するまで
実走できない。実測は次の一手として登録する。

**ユーザー依頼の前提を 4 点訂正した。いずれも実測で確定したもので、目的は変えていない。**

1. 「格子を 10µs より上へ延ばす」— 格子は既に 100µs まで在り、tracked な 3 campaign が
   2/5/10/25/50/100µs を全点測っていた。欠けていたのは分解能・100µs 超・現行環境である。
2. 「`backoff_overthrottle.py` は perf 非依存」— **指標は** perf 非依存だが**現行 driver は
   perf 依存**だった。`run_once` の既定 `use_perf=True` を override していない。
3. 「レコード数は calibrator の飽和判定に従う」— 登録済み calibration は **飽和していない**
   (`saturated:false`)。ミス率が閾値 1% まで下がりきらず (実測 2.71%)、calibrator は
   L3 の 4 倍という下限規則で 100 万レコードを選んでいた。動作点が calibrator 由来である点は
   変わらないのでレコード数は増やさなかったが、「飽和値」とは書けない。
4. 「D496 下の対測定ではない」— D496 の第 1 項 (比べる構成をすべて同じ campaign の中で測る) は
   満たす。満たさないのは第 2 項 (比較規則・構成集合の事前登録) である。**依頼の指示
   (論文の利得率の出所として使えると書かない) はそのまま守った**が、理由を
   「D496 非該当」ではなく「比較規則の事前登録が無い」「estimand が論文 headline と一致しない」
   と正確に書き、判定 JSON の field 名も実態に合わせた ({{D:b10-claim-boundary-fields}})。

**目的の言い方も実装に合わせて変えた。** D20 の「stock 適応は約 560µs に駐車」は
機構の状態ではありえない — CCBench の適応 backoff は 0〜1000µs を 100µs 刻みで動く。
560 は spin 占有率から逆算した相当値で、D20 自身が外挿と書いている。
**格子が 100µs で止まっていたということは、適応機構の可動域のうち下から 10% しか
静的点で覆えていなかった、ということである。** 上限を 1000µs にする根拠も恣意的な数ではなく
実装上の上限そのものである ({{D:b10-adaptive-state-coverage}})。

**段 1 を 1 度巻き戻した。** 初回 brief を確定して段 2 を投入した直後、`SWEEP_US` の pin 閉包検索で
凍結 golden と oracle gate に触れることが判明した。`DW-O08` / `DW-O09` / `DW-O10` は
最遅読了段が段 1 brief 前なので、入口の巻き戻し規則に従って brief を invalidate し、
段 2 の子を停止して段 1 から再実行した。停止した子は成果物ゼロで、旧 brief と旧 prompt は流用していない。

**段 3 は 2 レンズとも NO-GO、段 6 も 2 レンズとも NO-GO だった。** 段 6 の指摘のうち
最も重かったのは、PBS payload が計算ノードの割当て照合と reservation の環境変数を作っておらず、
**正常に投入しても計測が開始前に停止する**というものだった。この wave の目的である実測が
まったく取れないところだった。レビュー子は入力変異も実際に当て、
別 workload / 別 campaign の診断行が受理されることを実証した。

**変異 matrix が恒真な保証を 1 件暴いた ({{F:tautological-onset-guard}})。**
過抑制開始点の「床超え低下が 2 点連続」という条件を「1 点でも可」に緩めても 1 件も赤にならなかった。
追うと、候補点はノイズ同値なピーク台地の右端より右の点だけなので定義上すべて床を超えて低下しており、
この条件は 1 件も拒否していなかった。単発の落ち込みを開始点にしない働きを実際に担っていたのは
同値集合の連続性検査で、そちらにはテストが 1 本も無かった。恒真な条件を挙動保存で撤去し、
連続性検査にテストを足して再変異で KILLED を確認した。

**親の登録ミスも 1 件あった。** MU-14 は「診断値がピーク判定を動かせない」を試すつもりで
別のテストが守っている定数を書き換える変異になっていた。狙い直して KILLED。
MU-02 は上端を落とすと適応状態も必ず 1 つ落ちるため冗長 gate であり、期待ノードを完全集合へ登録し直した。

**未 commit 差分が検査を止める型を 2 つ踏んだ ({{F:uncommitted-registry-blocks-children}})。**
(a) `tools/pegasus/admission_registry.json` は codex 子の起動前検査で HEAD と一致を要求されるため、
実装子がここへ新 job を登録した直後から段 6 のレビュー子が全部起動できなくなった。
(b) `orchestrator/campaign/loop.py` は contract loader の閉包に入っており、未 commit の間
19 件の setup error が出る。どちらも親の統合 commit で解ける偽赤である。

**焦点走の consumer を名前で引くと漏れる型も踏んだ ({{F:content-scanning-inventory-missed}})。**
`test_official_perf_closure.py` は production を内容で走査して perf 言及 file を集めるので、
新設 module 名を grep しても hit しない。段 6 の fix 後に初めて赤が出た。

**scope 外として裁定パッケージへ返す項目**は {{D:b10-diagnostic-binding}} の末尾に列挙した。

## 次の一手差分

### 新規

- {{T:b10-grid-measurement-run}} **P1・新規**: B-10 拡張格子の実測を 3 workload 分投入して回収する。
  `tools/pegasus/submit_b10_backoff_grid.sh --output-parent <repo 外の絶対パス>` で
  workload ごとに独立 job を並行投入し、完了 receipt の campaign id と hash を照合してから
  新 slug の 3 campaign directory だけを取り込む。**登録簿が main へ着地して初めて起動できる。**
- {{T:b10-adaptive-requested-us-instrument}} **P2・新規**: 適応 backoff が要求する µs を直接計装する
  診断 patch (D16 第 5 類) を検討する。現在は spin 占有率からの推定しかできず、
  spin 占有率は呼び出し回数と待ち量の積なので逆写像を持たない。
- {{T:b10-between-block-floor}} **P2・新規**: 現行 Pegasus・workload 別の between-block 床値を実測する。
  判定床に使っている 0.030 は旧環境の write-heavy / balanced 由来で read-heavy を含まない。
