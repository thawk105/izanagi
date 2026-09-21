# 依頼の逐語 (ユーザー、/dev-wave の引数、2026-09-21 07:3x JST)

受入 lease の門番 (leaders ≤ 1 ∧ load ≤ 60 + jitter) で wave が待った時間を、直近 20 wave の acceptance-*.wait-receipt.json /
  wait.log (job dir) と lease directory の記録から実測する (診断のみ、着手直前の local main から fresh worktree)。待ち時間の分布、同時に待った
  wave 数、開いた瞬間の leaders / load、飢餓 (同条件で 3 本以上が待つと開かない、2026-09-20 [T-2610]) の発生回数を出す。門番の閾値・周期・lease
  TTL の変更はユーザー裁定 (memory 正本) なので、緩和案 (閾値、jitter、周期の位相、優先順)
  を効果見積り付きの裁定パッケージにして実装しない。lease の primitive と待ち手の正本は変えない。規律 2
  を緩めない。診断だけ。gate・台帳・一般化の追加は scope 外。
