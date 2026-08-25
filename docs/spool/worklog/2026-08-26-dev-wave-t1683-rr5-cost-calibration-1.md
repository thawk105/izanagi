---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1683-rr5-cost-calibration
seq: 1
title: [T-1683] A-2 4 cell の実コストを Pegasus で実測し、6 時間に収まることを確定した。最も重いのは rr5 でなく rr50-stock だった (コード + 計測 + docs、branch worktree-dev-wave-t1683-rr5-cost-calibration)
---

## 本文

- 依頼は rr5 の全規模 trace 量・verifier 時間・RSS の実測だった。段 1 で「批准が閂なら
  実装差分ゼロの precheck で終端する」条件が付いていたが、**批准はこの計測の閂ではなかった。**
  批准 gate の生きた呼び手は `ident.py` の 1 箇所だけで、certified な走行の identity を
  確定する枝からしか通らない。計測経路は通らないので実走した。
- **批准 gate は別の理由で今 main で赤であり、人間が批准行を 1 行足しても開かない。**
  gate は台帳 file の commit 履歴を検査し、各版が直前の版の byte 前置拡張かつ 1 行増で
  あることを要求する。台帳の中身は開設以来 1 行のまま byte 不変だが、
  `git log --full-history` が拾う版数は main が進むたびに増える (実測で d8f777a4 のとき 13、
  9a6adfd9 のとき 14)。2 件目以降は「増えていない」ため必ず赤になる。merge commit を
  台帳の改版と数えてしまうのが原因である。T-1647 と T-1722 の前提を覆すので両方へ差し戻す。
  詳細は {{F:ratification-history-counts-merges}}。
- **既存の参照値 (539MB / 16.9M 行 / verifier 141 秒) を産んだ器具は使えなかった。**
  `s2_verify_calibration.py` は ccbench pin を `dff0f1e` に固定しており、現行 pin `511c953` と
  別物である。さらに env tag が `linux-baremetal` で、A-2 が走る `pegasus` とは
  clocks_per_us も numactl の有無も違う。親の段 1 brief 自身がこの取り違えをしており、
  linux-baremetal の値 (1800 / numactl 前置) を実装子へ指示していた。待機中の裏取りで気づき、
  段 6 で訂正した。{{D:measurement-instrument-must-match-target-env}}。
- **判定: 4 cell は 6 時間に収まる。** 1 反復あたり 4 cell 合計 695.95 秒、
  正式系列が要求する 5 反復で 3479.75 秒 = 約 58 分。ビルドと性能測定を足しても約 1 時間で、
  6 時間に対し 5 倍以上の余裕がある。
- **想定が外れた。最も重い cell は rr5 ではなく rr50-stock だった。** balanced のほうが
  commit が多く残るため trace 行数が増え、trace 1536MB・verifier 332 秒・RSS 20.3GB と
  4 cell 中の最大になる。**余裕が薄いのは walltime でなく RSS 側**で、
  既存閾値 32GB に対し 63% を使う。逐語と限界は
  `output/insights/2026-08-26_a2-4cell-walltime-cost.md`。
- 計算ノードでの実走は 4 回投入した。うち 2 回は probe の欠陥で 22〜23 秒で落ちた。
  1 件目は build の compiler が既定の `g++-13` に解決され、計算ノードに無かった
  (正規の入口 `buildcache.compilers_for_current_site()` を使っていなかった)。
  2 件目は build 受理判定が ccbench commit を完全一致で見るのに、probe が submodule の
  40 桁 HEAD を渡していた (正本 `CURRENT_PIN` は短縮 7 桁)。
  `assert_pinned_clean` は前方一致で照合するため、この取り違えを素通りさせていた。
  {{F:prefix-match-hides-exact-match-mismatch}}。
  **どちらも 6 時間の枠をほとんど消費せずに判明した** (2 回合計 45 秒)。
- 段 2・3 と段 6 の敵対レビュー子は軽量版として省いた。正しさ防壁にも受理集合にも触れず、
  設計択一も割れなかったためである。実装子は段 5 に 1 本、段 6 の fix に 3 本を出した。

## 次の一手差分

### 完了

- [T-1683] rr5 と rr50 の全規模コストを Pegasus で実測し、4 cell が 6 時間に収まることを
  確定した。最も重い cell は rr50-stock で、余裕が薄いのは walltime でなく RSS である。
  remaining: none
  base: 17e581eaefaff8eaf8dee53e16a27c01fc4263f34db7a7ff8d980a7446b9c691

### 更新

- [T-1647] **P1・ユーザー裁定待ち**: A-2 の 4-cell certification 実走。
  コスト面の不明は解消し、4 cell が 6 時間に収まることを実測で確定した
  (1 反復 695.95 秒、5 反復で約 58 分)。残る障壁は enforcement-source closure の批准だが、
  **人間が批准行を 1 行足しても gate は開かない**ことが本 wave の実測で判明した。
  台帳の履歴検査が merge commit を台帳の改版と数えるため、台帳が byte 不変のままでも
  main が進むたびに必ず赤になる。批准の前に検査側の修理が要る。
  base: 235518ad68ceb8bb3503d5fdf8824879ef8b4d27f4592281311c7ba60e185fca

- [T-1722] **P2・更新**: enforcement-source closure の批准を運用手順として整える。
  前提が変わった。**批准の導線を用意しても現状では gate が開かない。**
  履歴検査が「各版は直前の版の byte 前置拡張かつ 1 行増」を要求する一方、
  `git log --full-history` は台帳を byte 不変のまま何度も拾うため、
  2 件目以降が必ず落ちる。運用手順より先に検査側の修理が要る。
  base: 3efe830ee999602adb93f7c6fdd1a039495f61b9a3fba0a2631b5bd7f30e229f

### 新規

- {{T:ratification-history-check-repair}} **P1・新規**: enforcement-source closure の
  批准台帳の履歴検査を直す。現状は `git log --full-history` が拾う版を「台帳の改版」と数え、
  台帳が byte 不変でも main が進むたびに版数が増えて
  `ratification history is not a strict prefix extension` で必ず赤になる
  (実測: d8f777a4 で 13 版、9a6adfd9 で 14 版、blob は全て `42885e36`)。
  merge commit を改版と数えない形へ直す。**この修理が入るまで A-2 の certification は
  批准行を足しても実走できない。** 検査を緩める方向の変更にしないこと。

- {{T:a2-rss-headroom}} **P2・新規**: A-2 の RSS 余裕を確かめる。
  rr50-stock の verifier ピーク RSS は 20.29GB で、既存の判定閾値 32GB の 63% を使う。
  walltime の余裕が 5 倍あるのに対し RSS は 1.6 倍しかない。
  記録数・extime・反復の同時実行を増やす変更は walltime より先に RSS の天井へ当たる。
  5 反復を並行させる設計を採るなら事前に測る。
