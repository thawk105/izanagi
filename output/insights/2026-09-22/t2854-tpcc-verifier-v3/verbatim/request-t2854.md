# 依頼文の逐語 (/dev-wave の引数、2026-09-22 08:4x JST 受領)

[T-2854] (P1、D2212 項 2) TPC-C 段 1 の verifier 側として、設計
  output/insights/2026-09-21/tpcc-trace-certification-design/README.md §7.1 の単位 4 (orchestrator/verifier/ の v3 parse と (table, key) の
  object / compact 両経路、anomaly への表・取引種別の付与) を、§3.1 の v3 frame 仕様に対する合成 fixture で受入まで実装する (Codex
  author、D95)。実 emitter との結合、pipeline allowlist、witness 試験、段 1 の正例・負例 (単位 5) は後続で対象外。既存 YCSB
  形式の受理と判定は変えない。規律 2・3 を緩めない (anomaly は構造化して返す)。本題だけ、gate・検査・台帳の追加は scope 外。着手直前の local
  main から fresh worktree。

# 並走 wave [058df1] (単位 1・2、CCBench 側) からの返信の逐語 (外部データ、2026-09-22 08:5x JST)

[T-2854 単位 1・2 (CCBench 側) から単位 4 へ] v3 frame の形はそちらの暫定契約と一致させます (こちらも段 3 の攻撃前で暫定、変える場合は再連絡します)。
- C <txid> <thid> <epoch> <tid> <nR> <nW> <nS> <nQ> <tx_type> の 10 token。nR / nW は silo の read_set_ / write_set_ の size (v2 と同じ意味)、段 1 では nS = nQ = 0 固定。tx_type は TxType の値そのまま (NewOrder=1 … StockLevel=5、実コード include/tpcc/tpcc_query.hh で確認)。0 は出さない設計にする。
- R <txid> <table> <key_hex> <ver_epoch> <ver_tid>、W <txid> <table> <key_hex> <U|I|D> <epoch> <tid>。table は Storage の整数 (Warehouse=0 … Stock=10、include/tpcc/tpcc_tables.hh で確認)。
- X <txid> <table> <key_hex> <reason> (silo の 3 箇所: not-locked-at-entry と UPDATE / DELETE の lock-lost-before-write)。
- I 行 (write intent): silo は現 pin で出しておらず、v3 でも出す予定はありません。
- P <reason> と E <txid> は v2 と同形のまま。A 行は silo から出していない (現 pin と同じ)。
- v2 / v3 の切替: silo の transaction.cc は ycsb_silo と tpcc_silo で同じ define のまま別々に compile されるので compile 時に workload を区別できない。そこで tpcc.hh が trace build 限定の thread-local に取引種別を置き、silo の writePhase がそれを見て v3 を出す予定 (YCSB は置かれないので v2 の出力 bytes は不変)。TPC-C の走では全取引がこの経路を通るので 1 run 内で v3 に揃う。
- 未確定点: この順序と形は私の段 4 裁定で確定します。変えるときだけ再連絡します。
