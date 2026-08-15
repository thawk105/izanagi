---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-15
wave: dev-wave-t324-8c-prereg
seq: 1
---

## 新規

### {{F:worktree-nested-submodule-blocks-acceptance}}. 新規 worktree の入れ子 submodule 未初期化が受入を走行ゼロで止める [手順漏れ]

- 事象: 受入全走が `stage=preflight-submodule-ready rc=2` で、テストを 1 件も走らせずに落ちた。
  wave 開始時に worktree 内で submodule を初期化していたにもかかわらず発生した。
- 根本原因: 初期化が非再帰だった。CCBench 配下の入れ子 submodule
  (`third_party/shirakami` とその配下の googletest) が未初期化のまま残り、受入の前検査が拒否した。
  現行の運用節は worktree 作成時に非再帰の初期化を指示し、受入直前には
  `--recursive` だけを指示している。**`--recursive` は未初期化の submodule を clone しない**ため、
  新規 worktree ではどちらの指示でも入れ子まで届かない。
  加えて、この環境では素の submodule 初期化が transport 制限で必ず失敗するが、
  その回避設定はどちらの指示にも書かれていない。
- 影響: 受入 lease を 1 回取得したうえで走行ゼロで失敗した。lease は競合する複数 wave が
  争う資源であり、走行ゼロの取得はその窓を捨てることになる。
- 恒久対応: **未実施 (ユーザー裁定へ返す)。** 該当運用節は 996 bytes で単節予算 1,000 bytes に対し
  残り 4 bytes しかなく、初期化を再帰化する記述と transport 設定を追記できない。
  意味等価な圧縮は同族の docs で exact pin を壊した実績があり、
  本 wave では計算ノードが停止していて検査を走らせられないため実施しない。
  裁定と実施は {{T:devwave-o20-recursive-submodule}} が持つ。
- 再発検知: 受入の前検査そのものが fails-closed で検出する
  (本事象はその検査が実際に発火して判明した)。検査の存在は確認済みで、
  欠けているのは検査を踏まないための手順記述である。
