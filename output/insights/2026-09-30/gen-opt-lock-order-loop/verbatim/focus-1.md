## 総括

**NO-GO。** fix は段 6 の主な所見を静的には解消したが、WAL の記録件数を確認せず certified 行を作れる。要求付き検証をローカル並列で走らせる経路にも、追加した payload を受理できない欠陥がある。f3 は本レビュー時点で走行中であり、修正後の試験成功は未確認。

## 所見ごとの対応表

- **A1 — closed（静的）**：build の新規・cache hit とも出口再照合へ要求を渡し、同じ証拠束を再取得する。`orchestrator/campaign/buildcache.py:2776,3062,3530,3597,3689-3705`。両経路の試験は `orchestrator/tests/test_pipeline_gate_witness.py:89`。
- **A2 — closed（通常の逐次経路）**：要求付き `verify_payload` に gate 節を載せ、driver は成功結果の `verify_result` に依存せず WAL を読む。`orchestrator/campaign/pipeline.py:714-726`、`orchestrator/campaign/p3_s4_loop_lock_order.py:357-364`。
- **A3 — partial**：一致する `verify_done` は全件判定するが、期待反復件数を照合しない。記録が一部欠けても残りが合格し `result.certified=True` なら certified になる。`orchestrator/campaign/p3_s4_loop_lock_order.py:198-229`。
- **A4 — closed**：driver は経路から `registered`／`unregistered` を指定し、単体の投影経路は `fixture` を指定する。`orchestrator/campaign/p3_s4_loop_lock_order.py:146-152,194-196,314-331`。
- **B2 — closed**：強制式は純粋関数へ集約され、loop の capture、pipeline の評価、build 出口で使われる。`orchestrator/campaign/source_digest.py:77-82`、`orchestrator/campaign/loop.py:830-832`、`orchestrator/campaign/pipeline.py:1750-1753`、`orchestrator/campaign/buildcache.py:3689-3694`。loop が flag のみの場合に evaluate へ keyword を送らない点は、pipeline 側で実効値を再計算するため整合する（`loop.py:967-985`）。
- **B3 — partial**：driver は現行 8 計数だけを検査・投影し、追加 key を許す（`orchestrator/campaign/p3_s4_loop_lock_order.py:156-164`）。一方、層 3 schema の counts は追加 key を拒む（`orchestrator/campaign/layer3_schema.json:381-394`）。現行 `result_to_dict` の出力は 8 key で一致する（`orchestrator/verifier/report.py:141-157`）。
- **B5 — closed（静的）**：要求なし snapshot の期待 bytes は固定の source literal から作り、現行出力の `normalized_sources` を再利用しない。`orchestrator/tests/test_verifier_capability_gate_witness.py:69-83`。
- **f1 の 10 件 — closed（修正箇所の静的確認）**：perf 閉包は余分な driver 登録を撤去（`orchestrator/tests/test_official_perf_closure.py:65-69`）。署名は末尾を既存の 2 引数へ戻した（`orchestrator/campaign/loop.py:553-562`）。新 test 8 件は、反例の閉路を与える修正（`test_p3_s4_loop_lock_order.py:142-153`、`test_silo_lock_order_model_gate.py:33-43`）、M1 の実行引数・build spy の修正（`test_pipeline_gate_witness.py:23-63`）、capability fixture の pin 修正（`test_verifier_capability_gate_witness.py:46-61`）で赤の原因に対応する。後者は同 fixture を使う 4 件にも及ぶ。残る反復 test は `test_pipeline_gate_witness.py:67-88` で payload を直接確認する。**f3 の結果による実走判定は保留**。
- **f2 の層 3 閉包 1 件 — closed（静的）**：optional `gate_witness` を閉じた schema に追加し、条件付き producer key とレポート正例を試験に追加した。`orchestrator/campaign/layer3_schema.json:374-409`、`orchestrator/tests/test_layer3_report.py:5575-5584,5628-5654`。現行 `result_to_dict` の key・型とは一致する（`orchestrator/verifier/report.py:138-158`）。**f3 の実走結果は未確認**。

## 新規所見

- **must-fix — ローカル並列検証が要求付き payload を拒否する。** 生成側は `gate_witness` を追加する（`orchestrator/campaign/pipeline.py:725-726`）が、同じ pipeline の並列結果受信側は旧 key 集合との完全一致を要求する（`:1029-1045`）。`verify_performance_concurrent=True` の performance 反復はこの受信側を通る（`:2785-2790`）。**成果物影響：** この構成の適格候補は検証結果を確定できない。**直し方：** task に束縛された要求値に応じて受信 key 集合を切り替え、要求なしの集合は維持する。
- **must-fix — WAL の欠落反復を検出できない。** driver は存在する一致記録をすべて見るが、1 件以上という条件しかない（`orchestrator/campaign/p3_s4_loop_lock_order.py:198-205,222-229`）。pipeline は workload ごとの `reps` 回を実行する（`orchestrator/campaign/pipeline.py:2320-2326`）。**成果物影響：** WAL の一部が欠けても certified 履歴が成立しうる。**直し方：** 期待 tag・反復数と WAL の一致記録を照合し、欠落・重複を閉じた拒否コードにする。
- **should-fix — 将来版の追加計数で層 3 レポートが拒否される。** driver は追加計数を許す（`orchestrator/campaign/p3_s4_loop_lock_order.py:158-164`）が schema は拒む（`orchestrator/campaign/layer3_schema.json:381-394`）。**成果物影響：** 版 ≥3 が追加計数を出すと、certified 履歴と材料レポートの受理が食い違う。**直し方：** 版を含めた schema 方針を定め、追加計数を保存するか producer 側で明示的に現行形へ投影する。現行版 2 の出力には食い違いはない。

要求なしの snapshot・receipt・verify payload の新たな bytes 変更は差分上見当たらない。buildcache の key は要求値を直接含まない（`orchestrator/campaign/buildcache.py:636-659`）が、証拠束は非 wire であり（`orchestrator/campaign/source_digest.py:224-229,274-285`）、hit 時に要求付き snapshot を再取得して比較する。要求の有無だけで同一バイナリを使う現設計では、これ自体を欠陥とは判定しない。

## 親の実測の読み

`live-2-result.json` は起動器の木が **`c33afae78`** で、outcome も `fixture-liveness` と記す（同 file `:902,911`）。M は build 0、`model-unregistered` 拒否（`:3-15`）。X の 2 workload は D1・D2 計数 0、D5 pass、serializable／certified の **fixture** 履歴（`:627-671,761-805`）。S は D2b 計数が立ち、indeterminate／`verifier-not-certified` の **fixture** 履歴（`:184-228,331-375`）。したがって親の X・S の読みは JSON と整合する。これは fixture と直 build による要求付き判定・history 投影の**配線確認**であり、production 登録簿を通った campaign の certified 主張ではない。