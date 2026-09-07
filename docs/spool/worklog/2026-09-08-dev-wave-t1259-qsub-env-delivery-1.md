---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t1259-qsub-env-delivery
seq: 1
title: [T-1259] qsub -v の 2 本目以降は届き、NQSV は -v 外の ambient env を継承しないと実測した (probe + テスト + insight、branch worktree-dev-wave-t1259-qsub-env-delivery、変異 matrix = baseline PASSED・KILLED 9・SURVIVED 1 (等価変異として事前登録)・MISMATCH 0・期待 node 完全一致 10/10)
---

## 本文

- **実測は 3 request すべて完走した** (`982468` / `982469` / `982470`、`bnode011` / `bnode001` /
  `bnode011`、いずれも `ok=true`)。official 床値走行は投入していない。
  値と証拠は `output/insights/2026-09-07_t1259-qsub-env-delivery/`。
- **依頼の前提を 1 件反証した。** 原文と親 brief は「先行 probe の 2 本渡し実績が
  『2 本目は届く』を被覆している」と書いたが循環していた。先行 probe が示すのは
  「2 本目の値が job 側に存在した」ことだけで、`-v` の 2 番目 field で運ばれたのか
  ambient 継承で届いたのかを識別できない。ambient 継承の有無が未確定な間は前者の証拠に
  ならない。段 3 の 2 レンズが独立に反証した。本 wave の実測 (ambient 継承なし) が
  確定した後で初めて遡って言える。
- **親 brief のもう 1 件の誤りも段 3 が反証した。** 「ambient 継承するなら承認束縛の前提
  そのものに関わる」は過大だった。投入器の実投入 guard は shell 内部変数を見ており、
  それを立てるのは CLI 引数だけである。ambient の同名 env は guard 判定に使われない。
  影響が及ぶのは raw `qsub` の非標準経路だけで、そこは既に保証外と明記されている。
- **敵対レビュー 2 本が must-fix 計 14 件、焦点再レビューがさらに 4 件を出した。**
  重なりを除く 9 系統を全件採用した。最も重いのは PBS shell の `ERR` trap が
  `set +e` の下でも発火する欠陥で、**observer が「env が届かなかった」という正規の負結果で
  rc=1 を返すと結果行が 2 本出る**。まさに本 wave が測ろうとしていた経路の一次証拠が壊れていた。
- **2 レンズが逆の判断を出した 1 件は、親が runbook の実文で決めた。** 投入 script の
  admission 分類である。判断は {{D:probe-submitter-not-a-repo-executable}}。
- **変異 matrix が、静的レビュー 3 本が見逃した穴を暴いた。** 事前登録 10 件の probe 走で
  5 件が生き残り、うち 3 件は正しさゲートの中心 (未承認 driver argv への承認 flag 混入、
  argv 完全一致の緩和、承認値と nonce の一致検査の骨抜き) だった。直前の fix は
  「負例を追加した」と報告していたが、その負例は対象の述語を通っていなかった。
  判断は {{D:mutation-over-static-review-for-negative-examples}}、事象は
  {{F:review-blind-to-uncovered-predicate}}。
- **実機だけが暴いた欠陥も 1 件ある。** 投入 script が `qstat` 本文の状態列でなく Pri 列を
  読んでいた。合成 fixture が実装と同じ誤った列配置を共有していたため緑だった。
  事象は {{F:synthetic-fixture-hides-column-layout}}、判断は
  {{D:external-command-parsers-need-measured-fixtures}}。
- **親が段 6 に書いた受理述語も 1 件誤っていた。** `accepted_states = ("QUE", "RUN")` は
  投入直後の実測値 `STG` に到達しない。実測値へ合わせて広げた。実測できたのは `STG` の
  1 値だけで、残りは `qstat -Q` header 由来の未実測候補である。
- **fix は 6 巡した。** 1 巡目は `.txt` 案が execution inventory を外れないとして停止条件で
  正しく止まり、親が判定器を実測して解き方を渡した。3 巡目は HEAD blob 束縛 file の
  未 commit で rc=2、同じ job-id の receipt 残留で rc=2 と 2 度躓いた。
- **実装子は 1 度もテストを走らせられていない。** codex の sandbox が `qstat` の socket を
  作れず dispatch preflight が rc=1 になり `rc=16` で落ちる。親が全て代走した。
- 背景の待ち手として張った until ループが、条件未達のまま完了通知を出す事象を 2 度実測した。
  毎回 `.done` と成果物で検算していたので誤判定には至っていない。正本の
  `tools/dev_wave_wait.py producer` へ切り替えて回復した。既存の正本が既に
  「待ち手は `tools/dev_wave_wait.py` を使う」と定めているので、文書は変えない。
- **段 8 の改善候補 1 件は実施しないへ落とした。** 段 2 の plan 子が投入元を wave worktree に
  置いた件で、submit-tree の既裁定が dev-wave の reference から引けないのが原因である。
  `DW-C01` へ 1 行足すと節全体の exact 契約と単節予算 1000 bytes を破る (1114 bytes)。
  D730 / D782 の手順に従い、既存記述の削減は安全義務の圧縮になるため採らず、
  独立 3 例にも達していないので収容しない。上限引き上げには至っていない。

## 次の一手差分

### 完了

- [T-1259] `qsub -v` の 2 本目・3 本目の到達と NQSV の ambient 継承を、承認あり / なしの
  双方で実測した。2 本目も 3 本目も byte 単位で届き、`-v` 指定外の ambient env は継承されない。
  承認変数名そのものも継承されない。同名が双方にあるときは `-v` が勝つ。
  承認なしの実 driver は argv 完全一致のまま rc=2 で拒否され protocol loader へ到達しない。
  remaining: none
  base: 8d108c3ac8a8577d3878a63f0fdbf2a36ac44b49028856b9b9aefd0e8e5e12b6
