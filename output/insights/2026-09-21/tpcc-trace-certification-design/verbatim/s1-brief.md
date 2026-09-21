# 段 1 brief — TPC-C の trace 直列化可能性認定: 設計と工数見積り (precheck、実装差分ゼロ)

基準: worktree `.claude/worktrees/dev-wave-tpcc-trace-design` HEAD = local main 36fb14a3d131d516dc57b02ec69f56c711927c2e。submodule external/ccbench = e9e477ca1b55348ab4530de0b1cf663ce4555290。

- **研究前進:** VLDB 裁定控え (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-vldb-direction-verdicts.md` 項 2) が TPC-C を必須にした。論文の「合成候補を TPC-C でも trace で直列化可能と認定した」主張の前提工事を、実装 wave をそのまま起票できる粒度 (file:line) で設計し工数を出す。完了判定 = 依頼の 5 項目 (段 1 trace 形式と意味 / 段 2 述語読みと phantom / CC 別改修点 / 正例・負例 / 工数と trace 容量) がアンカー付きで揃うこと。
- **scope:** 設計と見積りだけ。コード・テスト・CCBench・patches の差分ゼロ。計算ノードへ投入しない。login では静的確認と小規模 build (tpcc_{silo,si,mocc} の TRACE=1 build を repo 外 scratch で) だけ。binary の実行はしない。仮想リスク向けの gate・検査・台帳・一般化は足さない。
- **確定裁定:** 裁定控え項 2 (段 1 = NewOrder/Payment、段 2 = 全 5 取引) と項 4 (2 node 時間以上は投入前確認)。D14 (`#if TRACE`)、D16 (trace-hook の行き先)、D295 (witness は trace 外 counter、YCSB だけ allowlist)、D296 (silo v2 frame: C 行に R/W 件数 + E 終端)、D48 (tpcc.hh の app 層 abort)。
- **不変条件:** 規律 1 (trace は `#if TRACE` のみ、perf build に何も残さない)。規律 2 (受理集合を緩めない — witness に許容幅を作らない、表識別子の欠落や未知 tag は indeterminate へ倒す)。規律 3 (anomaly は取引種別・表・key まで構造化して返す)。
- **成果物:** `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` (設計 + 工数 + 容量試算 + 正例・負例表) と worklog fragment (docs/spool)。decisions は作らない (未採用の設計提案であり、採否は実装 wave で裁定)。
- **分割:** 段 2 = read-only codex 1 本が file:line 粒度で設計草案を起草。段 3 = read-only codex 2 本 (レンズ A: 意味論の健全性 = 偽認定 (cycle を隠す) 経路と偽警報、レンズ B: CC 実装・工数・容量の実在性)。段 4 で「コードは実装しない」と裁定し、docs は親が書く。docs は一次資料から事実を再抽出するので段 6 の read-only review 1 本は残す。
- **成果物影響 (DW-G05):** 本設計が無いと TPC-C の走行は pipeline で検証前に拒否され続け、TPC-C の certified 選択が 1 件も作れない (論文の TPC-C 表が空)。

## 親の provisional 裁定 (攻撃対象)

- (P1) 表識別子は 3 CC の read/write set 要素が既に持つ `storage_` (Storage 列挙の整数) を R/W 行に足せば足りる。verifier の key は `(表, key_hex)` の組にする。実例で要る: NewOrder 表と Order 表の key は同じ 8 byte `(w_id, 0, d_id, o_id)` (tpcc_tables.hh:257-262 と :284-289)、Warehouse (w_id) と Item (i_id) も 8 byte で一致しうる (:44-47 と :356-359)。
- (P2) tpcc.hh は commit 成功後に `quit_` を見て counter 加算の前に return する (tpcc.hh:102-110)。この差は counter 側を直して閉じ、verifier に許容幅を作らない。
- (P3) Payment の姓検索は CC を通らず `CustomerSecondary` を直接読む (tpcc_tx_payment.hh:114-115)。同表の書き手は初期ロードだけ (tpcc_initializer.hh:365,380) なので実行中は不変で、依存辺を生まない。trace の追加は不要で、その根拠を静的に記録すれば足りる。
- (P4) 範囲読みは scan 1 回ごとに S 行 (表・下限・上限・両端の排他・件数上限・返却件数) を出す。件数上限に達した scan の実効範囲は [下限, 最後に返した key] に縮める。verifier は述語読みに対して、範囲内の key に「読んだ時点より後の版」(insert / delete / update) を最初に産んだ trx への rw 辺と、範囲内の見えた版の producer からの wr 辺を足す。
  - **(P4) の既知の穴 (親の実測):** 範囲内で「見えなかった key」が挿入前 (unborn) だったのか削除後 (dead) だったのかは、現行 trace からは決まらない。CCBench の TPC-C で挿入と削除の両方を受けるのは NewOrder 表だけ (Delivery の delete_record、tpcc_tx_delivery.hh:69)。OrderLine・OrderSecondary・Order は挿入のみ。挿入のみの key は「見えなかった = 挿入前」で一意に決まり、読み手 → 挿入者の rw 辺だけで足りる。挿入 + 削除の key は「読み手 → 挿入者」か「削除者 → 読み手」の選言になる。親の暫定案 = 既存辺の到達可能性で片方に決め (挿入者から読み手へ既に道があれば削除者 → 読み手)、決まらなければ indeterminate へ倒して件数を返す。代案 = trace build だけで物理順の通し番号 (木への挿入・除去・scan の開始/終了) を刻む。どちらが健全かを攻撃対象にする。
  - **件数上限付き scan:** Masstree は absent (未 commit の挿入・削除済み) の tuple も件数に数えて止まる可能性がある。返却件数 < 上限でも走査範囲が [下限, 上限) 全体とは限らないので、S 行には Masstree が返した件数と最後に触れた key も要る。
- (P5) 3 CC とも Masstree node version による phantom 防止 (node_map_ の検証) を既に持つので、CC 側の改修は trace 出力だけで制御は変えない。
- (P7) CCBench の TPC-C で commit する取引は「見つからない」点読みで進まない (NewOrder/Payment/Delivery/OrderStatus/StockLevel とも、点読みの NOT_FOUND は return false = app 層 abort)。例外は Delivery の delete_record の NOT_FOUND 無視 (tpcc_tx_delivery.hh:69) で、同じ key を scan で読んだ R 行が rw 辺を張るので追加の trace は要らない。
- (P8) CCBench の編集面は hook で `include/backoff.hh`・`cc/silo/transaction.cc`・`cc/mocc/transaction.cc` の 3 file (hooks/guard_write.py:44-45)。`include/trace.hh`・`include/tpcc.hh`・`cc/si/transaction.cc` の改修は D16 の `izanagi-trace` 枝 + submodule の pin 前進 (承認定数 `CCBENCH_FULL_SHA`、orchestrator/campaign/s8b_approved.py:67) を伴い、工数の主要項に入る。
- (P6) mocc の G2 witness (値の先頭 8 byte に producer txid を刻む) は TPC-C の行を壊すので TPC-C では使わない。si の trace は v1 (C 行 5 token、E 無し) のまま。

## 変更面の実アンカー表 (設計対象。本 wave では編集しない)

| 面 | 位置 |
|---|---|
| trace 形式の定義 | external/ccbench/include/trace.hh:17-24, 70-97 |
| silo の trace 出力 | external/ccbench/cc/silo/transaction.cc:584-620, 694-699; scan :291-340; insert :70-115 |
| si の trace 出力 | external/ccbench/cc/si/transaction.cc:526-555; scan :411-460 |
| mocc の trace 出力 | external/ccbench/cc/mocc/transaction.cc:23-120, 1134-1205; scan :375-418 |
| TPC-C の取引 dispatch・計数 | external/ccbench/include/tpcc.hh:44-115 |
| 検証前拒否 | orchestrator/campaign/pipeline.py:434-437 (依頼文の `orchestrator/pipeline.py` は実在しない) |
| verifier の parse / 辺 | orchestrator/verifier/parse.py (C/R/W の token 解析), dsg.py:344-679, model.py:315-352 |

## 受入・実測環境

login node の静的確認と小規模 build のみ (受入走・計算ノードなし)。docs 変更の検査は `python3 tools/check_docs.py` と関連 test。
