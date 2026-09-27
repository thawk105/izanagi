---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-27
wave: dev-wave-t2866-tpcc-campaign
seq: 1
---

## {{D:tpcc-campaign-evaluate-wiring}}. campaign の評価単位 (pipeline.evaluate) と buildcache は workload (ycsb / tpcc) を既定値付き引数で受け、ycsb の cache identity と argv は bytes を変えない。転移実行器の TPC-C 検証は段 1 の 57:43 cell だけを D2238 の経路へ通し、v2 は未確定にする

**決定:** TPC-C 段 1 の候補を production の経路で build・評価できるようにする (依頼は [T-2854] の残り (2) と、転移の実行器の TPC-C 検証の接続)。
実装と試験・計算ノードの生死確認は `output/insights/2026-09-27/t2866-tpcc-campaign-wiring/README.md`。

1. **build:** `buildcache.build()` / `build_v2()` は keyword `workload` (`ycsb` / `tpcc`、既定 `ycsb`) を受け、target・binary path・compiler input の target を `<workload>_<protocol>.exe` の 1 箇所から作る。
   legacy の cache key と v2 の identity preimage は tpcc のときだけ workload を足す。ycsb の key・bdir 名・digest は変えない (既発行の cache・受領証の束縛を保つ)。
2. **評価:** `pipeline.evaluate(..., workload=)` は build と、保持した準備状態経由で bench へ workload を通す。`measure_point` / `capture_measure_point` の `workload_name` は件数 flag を
   `-ycsb_tuple_num` / `-tpcc_num_wh` に切り替える (`PerfConfig.records` は TPC-C では倉庫数)。TPC-C の `perf.workload` に `tpcc_num_wh` があれば既存の `ycsb_tuple_num` 拒否と同形で拒否する。
   TPC-C の correctness は caller が渡す。入口に新しい拒否は足さない (未指定なら YCSB の既定 flag になり、既存 `_run_trace` が tpcc binary を既存 reason で拒否する)。bench / commit payload に `workload` key は足さない
   (bench は既存の `run_cmd` の binary 名と `-tpcc_num_wh`、commit は同じ variant の build 記録で識別できる。bench payload の key 集合は layer3 レポートの閉包 pin に束縛され、
   WAL の `workload` key は検証記録で `{"tag": ...}` の意味に既に使われている)。
3. **受理は変えない:** `_run_trace` の 57:43 文字列一致と verifier 後の v3 要求 (D2238 項 2・3) はそのまま。critic の `trace-witness-unsupported-workload` は説明文だけを TPC-C の v2 reject と 57:43 以外に合わせる。
4. **転移実行器:** TPC-C は段 s1 で 4 比率 flag が 43/0/0/0 の cell だけを trace → witness → 実 verifier (凍結した source root) へ通し、verifier 後に v3 (`existence_violation_details` が list) を要求する。
   v2 は `verification_status(certified=False)` で未確定 (anomaly・非直列化は失格が優先)、reason は D2238 項 3 と同じ語。s2 と s1 の非 57:43 は「認定経路なし」の未確定のまま。
5. **範囲:** 「campaign で評価できる」は campaign の評価単位 `pipeline.evaluate` までとする。探索 loop (`loop.run_campaign` の workload・verify mode、TPC-C の calibration、`calibrator/cli.py` の ycsb target 固定) は TPC-C の探索設計と一緒に行う。

**理由:**
- 計算ノードの生死確認 (錨 s1-H-base だけ) で、production の `build_v2(workload="tpcc")` が `tpcc_silo.exe` を作り、実行器の 1 job・検証 1 本、bench の直接 1 回、evaluate 1 件が期待どおりに走った。
  現 pin の v2 trace は実行器で未確定、evaluate で既存 reason の abort (bench 未起動・COMMIT なし) と記録された。
- workload を dataclass の field や `PerfConfig` に足すと、ycsb の同一性 hash・WAL・受領証の形が変わりうる。既定値付き引数と tpcc だけの条件付き追加なら ycsb の bytes は変わらない (golden test と変異で固定)。
- 焦点走の新 test が、`_prepare_evaluation_core` の反復変数が引数 `workload` を上書きして v3 通過後の TPC-C bench が落ちる欠陥を見つけた (fix 済み)。

**却下した選択肢:**
- `PerfConfig` に workload field を足す — ycsb の値にも field が増え、同一性や記録の形に波及しうる。
- TPC-C 用の測定関数を `run_once` で新設する — 反復・安定性・rc の扱いを作り直し、fitness の意味が変わりうる。
- TPC-C で correctness 未指定を入口で拒否する — 既存 `_run_trace` の拒否で fail-closed が成立しており、新しい gate になる。
- bench / commit payload に TPC-C のときだけ `workload` を載せる — 当初は実装したが、受入で layer3 レポートの payload key 閉包 pin が赤になり取り下げた。
  既存の記録で識別でき、WAL の `workload` key の意味 (検証記録の `{"tag": ...}`) と二義になる。
- search config へ workload を記録して campaign lock を分ける — `run_campaign` が evaluate へ渡さない現状では実行引数と結び付かない。探索設計の段で決める。
- 57:43 以外の s1 cell (pay20 / pay70) や s2 を検証経路へ通す — D2238 の受理外で、受理を広げるのは認定の設計変更である。
