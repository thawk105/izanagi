---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t1281-qsub-waiter
seq: 1
title: [T-1281] 計算ノード job の完了を待つ待ち手を正本へ載せた — 敵対レビューが会計判定の誤完了 2 経路を暴いた (コード + テスト + 手順書 + insight、branch worktree-dev-wave-t1281-qsub-waiter、変異 11/12 KILLED)
---

## 本文

- D1290 が判定材料まで確定させていた待ち手を実装した。`tools/dev_wave_wait.py` の subcommand
  `compute` で、done-marker の実在と scheduler 会計 `Ended Request Time:` の論理和だけを見る。
  `qstat` は rc も状態も呼ばない。手順書は `docs/pegasus-runbook.md` §7.3 が正本。
- **敵対レビューが誤完了を 2 経路見つけた。** 会計本文の `Ended Request Time:` が対象 record へ
  束縛されておらず、(i) 他 job の終了行が CRLF で混ざると実行中の job を完了と判定し、
  (ii) 終了行が対象 ID 行より前にあっても完了と判定していた。CRLF の扱いが ID 側 (拒否) と
  Ended 側 (受理) で非対称だったことが (i) を踏ませ、同じ非対称が全行 CRLF の会計を見落とす
  逆向きの欠陥も生んでいた。親が現物で 3 入力とも再現し、修正後の値も現物で確認した。
  逐語は `output/insights/2026-09-08_t1281-compute-waiter/RESULT.md`。
- レビュー所見のうち 4 件を採用し 4 件を不採用にした。不採用の理由は {{D:compute-waiter-scope}}。
  空白だけの done-marker を証拠にしない現行挙動は「非空」より厳しい側であり、緩めるのは完了判定の
  受理集合を広げる方向なので規律 2 に従って据え置き、手順書へ明記して閉じた。
- 変異は 13 件を事前登録し、12 件を計算ノード dispatch で走らせて **11 KILLED / 1 SURVIVED**
  (期待と完全一致、`MISMATCH` 0)。生存した 1 件は等価変異で、両層同時変異を追加で走らせて
  実効 gate が前置検査であることを裏取りした。
- 残る 1 件 (request ID の引数検査を外す変異) は本走から外した。外すと待ち手が既定 6 時間だけ
  実際に待つため、テストが赤ではなく停止し、dispatch では job が walltime まで居座って
  orphan-hold になる。DW-M06 に従い timeout は fail-open の証拠として扱い、login 自走 probe で
  観測したハングを erratum に残した。詳細と復旧手順は {{F:hang-mutation-orphan-hold}}。
- 非帰属の赤 2 件を実測で切り分けた。実装子が見た `test_pegasus_dispatch_compute.py` の 14 件は
  codex sandbox の隔離失敗で、親の login 環境では素の base でも patch 適用後でも 334 全緑。
  fix 子が見た `test_mutation_worktree.py` の 3 件は fix 前の同じ木でも同数・同テストで再現した。
- **新規 test file を足したことで受入所要時間台帳の被覆 gate に掛かった。** attempt 1 が
  `coverage too low: 89.849780%` の 1 件だけで赤。37 node を除くと 90.0037% で緑になるため
  本 wave 起因と実測で確定し、正本 producer の `--add-only` で 37 node を登録した。さらに
  main 側 wave も同台帳へ追記していたため、main 取り込みで 2 回連続して content conflict になり、
  その都度 main を固定 SHA で取り込んで和集合に合成した (最終 19694 entry = 共通 19592 +
  main のみ 65 + 本 wave のみ 37、両親の全 entry で欠落 0・値不一致 0・和集合外 0)。
  詳細は {{F:new-test-file-hits-duration-ledger-gate}}。
- 台帳を和集合に合成した後の受入全走 (attempt 3) は `child-green`、21,644 passed / 68 skipped / 0 failed、`tested_main` = `a916458d8`、`tested_tip` = `41888b526`。本記録は DW-O16 に従いこの後の最終受入より前に commit する。

## 次の一手差分

### 完了

- [T-1281] 計算ノード job の待ち手を実装し、手順書 §7.3 の正本へ載せた。変異 11/12 KILLED
  (1 件は等価変異、1 件は hang として本走から除外)。
  remaining: none
  base: 86e58e8398fcfe677baa2cb59ac2d6fb1098714f209cef0318771ea9aa4d9fd2
