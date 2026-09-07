# 親が段 1 で実測した事実 (段 3 の検査対象)

これらは親が現物で確かめたと主張している事実である。**一般化しすぎていないか、
別の読み方があるかを検査せよ。** 誤りを見つけたら real 所見として報告せよ。

1. runner.measure_point (orchestrator/calibrator/runner.py:1057) と
   runner.capture_measure_point (同 :803) は、いずれも第 1 引数に binary を 1 個だけ取る。
   親はここから「1 回の呼び出しで 2 binary を測ることはできない」と結論した。
2. driver の subprocess 起動点は orchestrator/tests/test_ccbench_spawn_sites.py:115-117 で
   3 つの helper 関数 (HEAD 読取、blob 読取、競合 probe) の各 1 に固定されている。
   親はここから「起動点を増やさなければこの台帳は編集不要」と結論した。
3. orchestrator/tests/test_official_perf_closure.py:53 に driver が reviewed perf file として
   既に登録されている。親はここから「この台帳も編集不要」と結論した。
4. driver を参照するテストは 3 file だけである
   (test_floor_pair_driver.py / test_ccbench_spawn_sites.py / test_official_perf_closure.py)。
   参照関係で orchestrator/tests/ を検索して得た。この 3 file の baseline は
   2026-09-07 19:16 JST に 226 passed で緑だった (rc=0)。
5. main 全体で driver または其の schema 識別子を pin している file は上記 2 台帳だけであり、
   docs からの pin は無い。親はここから「schema 版を上げても壊れる pin は無い」と結論した。
6. summary 成果物の consumer は p3_b4_material_report 系のみで、依存は
   schema 識別子 / status=="generated" / candidate_floor の 3 点である
   (別 session からの申告を親が現物で確認した)。
7. 親は docs/phase3-b4-reflux-ablation-preregistration.md を編集しないと決めた。
   根拠は D1699 の「§5 の値セルは sentinel のままで本書はまだ発効していない」である。
