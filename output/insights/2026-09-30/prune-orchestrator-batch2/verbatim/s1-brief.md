# 段 1 brief — prune-orchestrator-batch2 (md_4)

- 依頼: /work/1/SFC/tanab/tmp/speedup-2026-09-29/md_4.txt (+ common.txt §3)。worktree = /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2、基準 = local main 4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037。
- 研究前進: 論文主張・図表は進めない。土台 = 2026-09-29 のユーザー依頼「不要なテスト、ツール、ファイルは削除して記録しておき、後でgit参照しやすいように」。完了判定 = 候補 12 module ごとに削除/残すを D1989・D2179 で判定し、削除は prune(orchestrator) commit、残すは理由を一次資料に書く。
- 確定済み裁定: D1989 (参照 4 分類、現役の拘束的 consumer が無いこと)、D2179 (一回限り・結果凍結済み・現行機構の実装でない の 3 連言 + 専用 test の専用性; 被覆を残す test 分割は削除 wave の scope 外)、D2172 項 5・6 (派生値 pin の test は維持)、D2257 (持ち越しの取り下げは各 D を取り消さない; T-139 は test が active 項として固定)、common.txt §2 (8b/8c module の切り離し・8c 系削除はしない)。
- 不変条件: 凍結 bytes・hash・path に束縛された文書・成果物を動かさない (規律 7)。既存 test の期待値を変えない (削除 test の丸ごと削除を除く)。所要台帳 acceptance_duration_ledger.json は編集しない。tools/check_docs.py・hooks/・test_hooks.py・test_check_docs.py に触れない。
- 成果物: 削除があれば prune(orchestrator) commit (本文に path・理由・D を 1 行ずつ)、test_ccbench_spawn_sites・nodeid 台帳・allowlist の該当行更新、一次資料 output/insights/2026-09-30/prune-orchestrator-batch2/README.md、spool fragment。
- 分割: 実装面の削除は Codex author 1 本 (所有を分けるほどの量でない)。

## 親の事前実測 (P = 親の provisional 裁定・攻撃対象)

| 候補 | 親の観測 (main 4f412c67b) | 見立て |
|---|---|---|
| orchestrator/submission_gate/ (11 file) + test_t338_submission_gate_unit1..5 + test_t139_submission_path + fixtures/t338_submission_gate/ | 非 test の import は package 内だけ。D749 (ユーザー裁定 2026-08-24)「private receipt gate の実装と検証は完了…残る実装 wave は pilot 禁止を維持したまま進められる」。D574 決定(1) が conformance vector index の (path, commit, sha256) 三つ組を上書き対象に指定し、orchestrator/preregistration/t139-approval-manifest-v1.json・t139-vector-approval-v1.json が fixtures/t338_submission_gate/conformance/index-v2.json を path@commit 6d431a60a で束縛。approval_payload.py (候補外) が両 manifest を読む。worklog 持ち越しに [T-139] が active のまま (D2257 項 7)。phase3.md の T-338「active から除外」は持ち越し走査対象外の意味で、D を取り消さない (D2257「取り下げの意味と射程」) | (P1) 残す: 現行機構 (有効なユーザー裁定が名指す投入 gate) の実装 |
| campaign/backoff_counterfactual_analysis.py | D2179 wave (T-2800, output/insights/2026-09-20/t2800-dead-code-delete/README.md §3) が凍結事前登録 docs/backoff-counterfactual-preregistration.md の解析器契約で残す | (P2) 残す (09-20 の判定以後に拘束が外れた事実を探す) |
| campaign/backoff_counterfactual_cohort2_analysis.py | 同上 + test_t2187_adaptive_const_probe.py が PREREGISTERED_SEEDS を照合先 | (P2) 残す |
| campaign/backoff_nonmonotonicity_analysis.py | T-2583/T-2635 の probe が library 再利用 (一回限り不成立は恒久) | (P2) 残す |
| campaign/backoff_policy_performance_analysis.py | 凍結事前登録 docs/backoff-policy-performance-preregistration.md:330「解析は …backoff_policy_performance_analysis.py の公開関数 1 本で行い」。test_t2187_adaptive_const_probe.py:23 が import | (P3) 残す: 事前登録が解析器に契約を課す + live test の照合先か要確認 |
| campaign/backoff_sweep_report.py | T-2800 が D12 材料レポート射影器として残す | (P2) 残す |
| campaign/s8b_floor_evacuation.py | docs/phase3-8b-restart-runbook.md:279 が `python3 -m orchestrator.campaign.s8b_floor_evacuation evacuate` を手順として指定。test_s8b_holdout_freeze.py:3324 (非専用 test) が import。test_ccbench_spawn_sites.py:297 に spawn 表 1 行 | (P4) 残す: 現行 runbook の手順 |
| campaign/s8b_oracle_exploration.py | decisions.md:21801 が artifact_role の所在として名指し。test_s8b_oracle_artifacts.py:22,344 が import・script 実行 | (P5) 残す見込み、D と test の中身を要確認 |
| campaign/s8b_verdict.py | test_official_perf_closure.py:85,187-189,439 (T967 predicate)、test_s8b_oracle_manifest_contract.py:25-35、docs/freeze-permanent-design.md:366・-s2.md:2525 が閉包・凍結対象に列挙、D(22607 行付近) が judge_combined を改訂 | (P6) 残す見込み: 凍結/oracle manifest 閉包の member |

親の見立て: 12 module とも削除条件を満たさず、削除 0。段 2 の役割は「消せるものを見落としていないか」「親の拘束認定が名前だけの非拘束・歴史的言及ではないか」の独立検証。

## 変更面 (削除があった場合の実アンカー)

- orchestrator/tests/test_ccbench_spawn_sites.py:297 (s8b_floor_evacuation の spawn 表行)
- orchestrator/tests/README.md:181 (`- test_s8b_verdict.py` allowlist 行) 他、nodeid 台帳 (test_plain_runner_coverage、REAL_REPO_SERIAL_NODES、growth_test_holds、FLAKY_TEST_HOLDS)
- docs/README.md の地図の該当行
