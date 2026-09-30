# 段 6 裁定 2 (焦点再レビュー focus-1 の新規所見) — 2026-10-01 00:50 JST

入力: focus-1.md (NO-GO)。焦点走 f3 (`8631dee79`、41 file): 4,055 passed / 0 failed / 11 skipped (40135.nqsv)。
対応表: A1・A2・A4・B2・B5・f1 の 10 件・f2 の 1 件 = closed。A3・B3 = partial (下の N2・N3)。

| 所見 | 裁定 | 理由と処置 |
|---|---|---|
| N1 local 並列検証の受信側 (pipeline.py:1029-1045 `validate_verify_payload`) が `gate_witness` 入りの payload を拒否する | real。本 wave では直さない (backlog) | 親の実測: 新 driver (`p3_s4_loop_lock_order.default_cfg`) は `verify_performance_concurrent` を設定しない。方策 driver でも設定するのは生成器対照 (`contrast is not None`) だけ (p3_s4_loop_policy.py:188-190)。到達しても拒否 (fail-closed) で、誤って certified にはならない。成果物影響は「この構成の gen-opt 候補が検証を確定できない」で、今の driver 経路では 0。段 A の軸で並列検証を使うとき (生成器対照を作るとき) の前提として [T-2896] に書き、直すときは受信側の key 集合を task に束縛した要求で切り替える (要求なしの集合は維持) |
| N2 driver が WAL の verify_done 記録数を期待反復数と照合しない (A3 partial) | real。本 wave では直さない (backlog) | pipeline は全反復の検証が合格しないと certified を返さず、各反復は certified 判定の前に verify_done を WAL に書く。記録が欠けて `result.certified` が真になるのは WAL の破損・切り詰めのときだけで、そのとき campaign 自身の再開・receipt の照合も壊れる。今の成果物で certified 行が誤る実例は無い。一次資料の限界と [T-2896] の前提 (本評価の前に期待反復数の照合を足す) に書く |
| N3 層 3 schema の counts は追加 key を拒む | nit | 現行の意味の版 2 では `result_to_dict` の 8 key と一致。版を上げるときに schema も D828 の型で足す |

変異 matrix (M0〜M15) は `8631dee79` の独立 clone で probe → final の順に進める (probe は 00:44 投入)。
