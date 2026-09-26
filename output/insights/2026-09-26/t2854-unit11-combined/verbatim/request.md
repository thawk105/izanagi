/dev-wave [T-2854] 残り (1) 単位 11 を行う。CCBench の C1' 6aa7a58f・C2 a6f2c741・C3 53f6b097 を、pin C 68106660 の上へ 1 系列に並べた別名の
  local branch にする。既存の公開 branch izanagi-tpcc-v3-trace は残し、同名への force push はしない (D2235 項
  1)。そのうえで結合確認を計算ノードで取る (v3 の構造・witness・内容、YCSB v2 の certified、TRACE=0 の前処理と逆アセンブルの一致、変異)。D297
  の検査器が拒否する header 差分については受理方式の案を作る。検査器の拡張と代替証拠での受理は委任されていないので、D297 / D2207 / D2225 決定 6
  の変更を要する案になったら、不足する保証と必要性を示して諮る。push と pin 前進の承認は人間。正本は worklog の [T-2854]
  carry、output/insights/2026-09-21/tpcc-trace-certification-design/README.md
  §7.1・§8、output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md §8。計算は 2 node 時間以上なら見積りとユーザー確認 (D2212 項
  4)。着手直前の local main から fresh worktree を作る。Codex author (D95)。規律 1・2 は緩めない。本題だけで、仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。
