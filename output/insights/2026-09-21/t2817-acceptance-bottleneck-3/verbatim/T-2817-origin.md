# 依頼の逐語 (/dev-wave の引数、2026-09-21)

[T-2273]/[T-2444]/[T-2495]/[T-2560] + [T-2817] (P1・裁定済み D2148 項 6、D1936 項 35) 受入律速の再同定 (第 3 回) と collection
  差の分解診断。着手直前の local main から fresh worktree、診断のみで実装 0 行 (conftest / gate の改変で代用しない)。(1) pairing 既定 on (entry
  1756、[T-2766]) 後の実受入で最遅 shard の wall の内訳 (共有 base 構築・verify・copy・相方・固定費、entry 1676 の式)
  を計算ノードで取り直し、律速を再同定する。(2) 受入 pre 61 秒と温 collection 18.4 秒の差 約 43 秒を、同 job・同 checkout で「独立 48 process →
  xdist -n 48 (flaky-hold 完全性検査を壊さない全 deselect の形を先に設計) → shard plugin 有り → duration ledger 有り」と段階的に載せて分解する
  (一次資料 output/insights/2026-09-20/t2243-collection-contention/README.md §5 (d)、entry
  1767)。削減可能量は分解が閉じるまで書かず、効果量の見込みだけ記録して実装しない。計測は runbook
  の単独性確認に従い条件を複数ノードへ割って投入する。規律 2 を緩めない。本題の診断だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外。
