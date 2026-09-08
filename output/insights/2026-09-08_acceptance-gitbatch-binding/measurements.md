# 計算ノード実測 — 受入形でない全 suite 走行 (dispatch、1 node × 48 worker、n=1)

- 走行: `python3 tools/run_tests.py --force-dispatch --junitxml=...` を wave tip `b06e9b18f` (main `c12e25078` 取り込み済み) で 1 回。
  受入形 (K=3 shard) ではない。wall は shard 構成が違うので比較しない。**比較するのは W (testcase duration 総和) と module 別 W。**
- 結果: 21,766 passed / 3 failed / 1 error / 68 skipped、wall 474.9 秒 (単一 node、全 21,838 node)。
  赤 4 件は `test_t1259_qsub_env_delivery_probe` (setup error、qsub 環境)、`test_run_tests_preflight` と `test_check_ai_provenance` の
  headroom / queue 判定 message、`test_codex_worker_launch::test_limit_stop_is_never_accepted` で、いずれも本 wave の差分に帰属しない
  (契約 loader・admission・wiring probe を通らない)。
- 改修前の分布: 2026-09-08 の受入走 47 走 (K=3、shard 合算)。

| 対象 | 改修前 中央値 (最小) | 改修後 (n=1) | 比 |
|---|---:|---:|---:|
| W 全体 | 28,734 秒 (p25 24,691 / p75 35,645) | 17,236 秒 | 0.60 |
| `test_autonomous_trial_completeness` | 1,879 (1,232) | 229 | 0.12 |
| `test_p3_b4_raw_record_producer` | 1,399 (682) | 311 | 0.22 |
| `test_p3_b4_closed_critic` | 1,264 (825) | 93 | 0.07 |
| `test_trial_registry` | 2,092 (1,434) | 347 | 0.17 |
| `test_layer3_report` | 850 (594) | 29 | 0.03 |
| `test_campaign` | 714 (532) | 288 | 0.40 |
| `test_p3_s4_loop` | 785 (597) | 89 | 0.11 |
| `test_critic` | 847 (528) | 60 | 0.07 |
| 対照 `test_s8b_oracle_driver` (binding を通らない) | 2,489 (2,048) | 2,665 | 1.07 |
| 対照 `test_s8b_floor_campaign` (同上) | 2,042 (1,676) | 1,932 | 0.95 |
| profile した node (`test_m10_empty_red_section_...`) | 56.0 秒 (9.5) | 5.7 秒 | 0.10 |

読み方: 対照 2 module が ≈ 1.0 なので、対象 module の低下は node 負荷の差ではなく本変更に帰属できる。
ただし n=1 かつ受入形でないので、最遅 shard wall (D1620 の測定面) の改善は主張しない。
受入走が投入できるようになったら (裁定 inbox `2026-09-08-main-codex-worktrees-gitlinks-block-acceptance-and-land.md`)、
同じ表を受入 junit で取り直す。junit の原本: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-gitbatch-20260908/fullsuite-junit.xml` (3.5 MB、repo 外)。
