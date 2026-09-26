# 依頼の逐語 (/dev-wave 引数、2026-09-26 22:02 JST 受領)

[T-2854] D297 の header 差分受理規則の設計審査だけを行う (D2249 項 2、択 1。裁定の控え
  /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-26-rulings-full36-verdicts.md)。材料は
  output/insights/2026-09-26/t2854-unit11-combined/README.md §5.2 と canonical worklog の [T-2854] 項。変更 header を読む consumer TU
  を列挙し、TU ごとの文脈で header 差分を条件つきで受け付ける規則を D297 の検査器に足す設計を審査し、insight と decisions fragment
  に記録する。成果は審査結果と、裁定に出す承認事項 (実装の委任、C2' 40a7f4ac の pin 前進) の案まで。検査器の実装・pin 前進・branch push
  はしない (別裁定・人間手番)。D780 項 2 は維持し、その比較を trace 完全除去の防壁と呼ばない。規律 1・2 は緩めない。稼働中の [T-2847] si v2
  wave が [T-2854] 単位 (12) に相乗りしているので、[T-2854] 項の fragment は land 前に main を取り込んで合わせる。着手直前の local main から
  fresh worktree を作る。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
