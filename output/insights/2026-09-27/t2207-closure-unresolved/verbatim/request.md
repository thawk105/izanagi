# 依頼逐語 (/dev-wave 引数、2026-09-27 14:28 JST 起動)

source 閉包の系統を 1 wave で進める。(1) [T-2207] D1539: 設定式が動的入力に依存するとき、部分 inventory に無いことを
  proven-unreachable の根拠にせず unresolved へ倒す (現状は 18 セルが誤って到達不能に数えられている。受理集合を狭める向き)。(2) [T-2344] 次段 =
  tuple 起点の 2 段目 23 本と exact-85 の再走査。exact-85 の記録済み lock を再走査し、未検出なら同じ wave で exact-85
  の歴史収載を撤去し、検出されれば D1653 の充足として残す。exact-96 も同じ条件で扱う (D1884・D2193・D2194 項 4・D2211 項 5、一次資料
  output/insights/2026-09-21/t2344-closure-emitters/README.md §8)。(3) [T-734] 全 certified sink に source gate を課す (2026-08-16 /rulings 第
  3 回)。3 件の編集 file の重なりは段 1 で閉包を取って確かめる。[T-733] の未収載 69 module は [T-2344] と重複するので、この wave
  の範囲で整理する。実装は Codex author (D95)。規律 2 を緩めない。本題の実装だけ。これ以外の gate・検査・台帳・一般化の追加は scope
  外。着手直前の local main から fresh worktree を作る。
