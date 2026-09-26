# T-2797 B-5 v2 mutation probe

`spec-probe.json` は `izanagi-dev-wave-mutation-spec/v1` の観測用 spec。全件 `SURVIVED` / 空の `expected_nodes` とし、実走で kill node を採集する。`estimated_run_seconds=450` は焦点 file 集合の計算ノード 1 run の見積り (300〜600 秒)。timeout 10800 秒、hang timeout 3000 秒は先例に合わせた。下表の nodeid は kill を期待する箇所であり、実走結果ではない。

| ID | 意図: 壊す条件と変わる挙動 | kill 予定の test nodeid |
|---|---|---|
| M0-loop | `p3_s4_loop.py` のコメント 1 文字を替える。意味は等価で、contract-loader の drift 層だけを観測する。 | contract-loader drift node (probe で採集) |
| M0-b5 | `b5_generator_contrast.py` のコメント 1 文字を替える。同じく意味は等価。 | contract-loader drift node (probe で採集) |
| M-A1 | v2 critic の診断節を出さず、critic prompt の bytes から節を消す。 | `orchestrator/tests/test_b5_llm_round.py::test_v2_critic_diagnosis_request_and_job_disclosures` |
| M-A2 | v2 の job 開示を v1 の系列全体 1 job 文面に戻す。 | `orchestrator/tests/test_b5_llm_round.py::test_v2_critic_diagnosis_request_and_job_disclosures` |
| M-B1 | 429 を failure retry に計上し、3 回の outage で同じ a を継続できなくする。 | `orchestrator/tests/test_b5_contrast_launch.py::test_v2_three_429s_restart_stock_then_accept_same_a_and_evaluate` |
| M-B2 | 構造化 status でなく result 文言の 429 で outage を判定し、成功文言も誤分類する。 | `orchestrator/tests/test_b5_llm_parent.py::test_429_requires_structured_status_and_valid_json` |
| M-B3 | handshake の前に proposal-opportunity を記帳し、outage 中にも A を増やす。 | `orchestrator/tests/test_b5_contrast_launch.py::test_v2_three_429s_restart_stock_then_accept_same_a_and_evaluate` |
| M-B4 | 正常な空出力を rejected として記帳せず、A を消費しない。 | `orchestrator/tests/test_b5_contrast_launch.py::test_v2_login_429_does_not_count_a_and_empty_output_does[success-ready]` |
| M-B5 | stock の直後に job 1 を返し、同 job の評価 1 を飛ばす。 | `orchestrator/tests/test_b5_generator_contrast.py::test_v2_first_job_has_stock_and_one_evaluation_and_later_job_one[random]` |
| M-B6 | 評価 job の search slot を 2 度実行し、1 step の物理評価回数を 2 回にする。 | `orchestrator/tests/test_b5_generator_contrast.py::test_v2_first_job_has_stock_and_one_evaluation_and_later_job_one[random]` |
| M-B7 | 計算 job の次 step 照合を無効にし、台帳と違う step を進める。 | `orchestrator/tests/test_b5_generator_contrast.py::test_v2_step_mismatch_refuses_before_session` |
| M-B8 | balanced slot から同時検査 flag を外す。 | `orchestrator/tests/test_b5_generator_contrast.py::test_v2_concurrent_verify_write_heavy_and_balanced` |
| M-B9 | model-mismatch file の検査を無効にし、空出力として A を消費する。 | `orchestrator/tests/test_b5_contrast_launch.py::test_v2_model_mismatch_ends_without_consuming_a[round-False]`; 同 `[critic-False]` |
| M-C1 | concurrent verify の許可を write-heavy のみに戻し、balanced を拒否する。 | `orchestrator/tests/test_p3_s4_loop.py::test_balanced_concurrent_flag_reaches_evaluate` |
| M-C2 | 許可に read-heavy を加え、拒否すべき workload を受理する。 | `orchestrator/tests/test_p3_s4_loop.py::test_concurrent_verify_cli_rejects_missing_requirements` |
| M-D1 | v2 Holm を 4 件でなく 6 件の係数で補正する。 | `orchestrator/tests/test_b5_generator_contrast_report.py::test_v2_four_comparison_holm_family` |
| M-D2 | v2 に batch ごとの正の median 条件を戻し、優越を余分に拒否する。 | `orchestrator/tests/test_b5_generator_contrast_report.py::test_v2_batch_median_is_descriptive_only` |
| M-D3 | v2 stock CV を pooled と batch 内 CV の最大に戻す。 | `orchestrator/tests/test_b5_generator_contrast_report.py::test_v2_pooled_stock_cv_not_batch_maximum` |
| M-D4 | v2 fallback を workload 全 15 session から batch 5 session に戻す。 | `orchestrator/tests/test_b5_generator_contrast_report.py::test_v2_fallback_uses_pooled_fifteen_session_median` |
| M-D5 | 測り直し stock が複数ある v2 系列を拒否する。 | `orchestrator/tests/test_b5_generator_contrast_report.py::test_v2_restarted_stock_keeps_score_and_comparison` |
