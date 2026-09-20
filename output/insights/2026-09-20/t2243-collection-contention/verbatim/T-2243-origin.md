# [T-2243] の依頼逐語 (dev-wave 引数、2026-09-20)

[T-2243] (P2・新規、entry 1218) 受入 collection の計算ノード約 51.7 秒とログインノード単一 process 12〜14 秒の約 3.6
  倍差を分解する診断 wave。48 並列の contention が CPU か Lustre metadata か memory 帯域かを、計算ノード (単独性を pgrep で確認、login
  では測らない) で条件を割って測り、collection 短縮策の効果量の見込みだけを記録する。改善実装は行わない (効果を先に測る、D1936 項 35)。[T-2786]
  の共有 base 構築 3 ブロック分解 (main 着地済み) と重ねて読み、同じ量を二重に数えない。着手直前の local main から fresh worktree。一次資料
  `docs/archive/worklog-phase3-0903-1218.md` (entry 1218)。規律 2 を緩めない。診断だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope
  外。
