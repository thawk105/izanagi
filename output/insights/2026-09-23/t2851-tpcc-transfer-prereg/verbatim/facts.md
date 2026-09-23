# 親が集めた事実 (2026-09-23、worktree HEAD = local main cadaf3805、CCBench pin e9e477ca)

凡例: [子] = 調査子 (read-only、sonnet) の報告を写したもの、[子→親] = 子の報告を親が現物で検算したもの、[親] = 親が直接確認。

1. [子→親] TPC-C 固有の実行時引数 (`external/ccbench/include/tpcc/tpcc_common.hh:6-14`): `tpcc_num_wh` 既定 1、`tpcc_perc_payment` 43、
   `tpcc_perc_order_status` 4、`tpcc_perc_delivery` 4、`tpcc_perc_stock_level` 4、`tpcc_interactive_ms` 0 (SQL 相当 1 単位ごとの sleep ms)。
   表の大きさは定数 (DIST_PER_WARE 10、MAX_ITEMS 100000、CUST_PER_DIST 3000、`:24-27`)。
2. [子] 共通の引数 (`cc/silo/include/common.hh:32-36`、`cc/mocc/include/common.hh:34-47`): clocks_per_us 2100、epoch_time 40 ms、extime 3 s、thread_num 10。
   binary は `build/cc/{silo,mocc}/tpcc_{silo,mocc}.exe` (`cc/<p>/CMakeLists.txt:1-3`)。
3. [子→親] NewOrder の比率は flag でなく残差 100 − (Payment + OrderStatus + Delivery + StockLevel) (`tpcc_query.hh:57-64` の閾値、`:289-296` の decideQueryType)。
4. [子→親] home warehouse = `(thread_id mod tpcc_num_wh) + 1` で thread ごとに固定 (`include/tpcc.hh:40`)。倉庫数と thread 数の整合を強制する検査は無い。
5. [子→親] NewOrder の明細数 5〜15 の一様 (`tpcc_query.hh:98`)、remote 品目 1% (倉庫 > 1 のとき、`:111`)、Payment の remote 顧客 15% (`:163-178`、倉庫 1 なら home)。
   いずれもコンパイル時の定数で flag ではない。
6. [親] 段 1 は既存 flag で OrderStatus / Delivery / StockLevel を 0 にでき、比率は NewOrder 57 : Payment 43 (設計 README §3.5、所見 B7)。
7. [子] repo に TPC-C の性能 (throughput) 測定は 0 件 (`git grep -niE "tpcc.{0,80}(tps|throughput|txn/s|commits?/s)" -- output docs` 0 件)。
   唯一の実行記録は T-2854 の構造検査 (`output/insights/2026-09-22/t2854-tpcc-ccbench-v3/`、thread 2・extime 1・倉庫 1・段 1 構成、計算ノード 1 走)。
   v1 起草時の棚卸し (`output/insights/2026-09-22/t2851-transfer-prereg/verbatim/facts.md`) も「TPC-C: 実行記録 0 件」。
8. [子→親] orchestrator に TPC-C の学習条件・campaign 定義は無い (`grep -rniE "num_wh|perc_payment" orchestrator tools` 0 件、tpcc の hit は test fixture と probe の列挙だけ)。
   trace witness 経路は `ycsb_` 以外の binary を拒否 (`orchestrator/campaign/pipeline.py:432-434`)。
9. [子] T 状態: T-2854 (段 1 認定) は単位 1・2・4 済、残り = 存在履歴の verifier 実装 (印 `Integrity.v3_existence_unverified` の撤去)・単位 5 (pipeline 配線・allowlist)・
   単位 3 (mocc emitter)・単位 11。T-2855 (段 2) は未着手。T-2850 (探索の独立反復、YCSB) は未着手。TPC-C の生成・探索・選択の証跡なし。
10. [子] Pegasus = Xeon Platinum 8468 × 1 socket、48 物理コア、HT 無効、DRAM 128 GiB (`docs/pegasus-runbook.md:33-45`)。
11. [親] 設計 README §7.3: 「既定 1 倉庫・48 スレッドでは Payment の Warehouse 更新と 10 District に競合が集中し、abort 率と取引別の commit 比率が変わる」。
    NewOrder は 1% の意図的な無効品目で abort し query を作り直す (`tpcc_query.hh:122`、`tpcc.hh:48`)。
12. [親] v1 (`docs/unseen-condition-transfer-preregistration.md`) §13.2: 着地から発効まで本文の既存 bytes を書き換えない。追補は誤記訂正と発効束の補足だけ。
    §14: TPC-C の留保は TPC-C の生成・探索・選択が始まる前に別の登録で固定する。
