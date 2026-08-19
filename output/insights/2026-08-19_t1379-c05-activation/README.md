# 8c 条件 5 (C05) の activation — insight package

wave: `dev-wave-t1379-c05-activation` / branch `worktree-dev-wave-t1379-c05-activation`
base main `a31832d9` (着手) → `c31c8fea` (段5 着手前に取り込み) / 2026-08-19 JST

## この wave が作ったもの

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`:
  C05 の `machine_checkable` を `false` → `true`。
- `orchestrator/campaign/s8c_preregistration_evidence.py`:
  `_MACHINE_EVALUATORS` へ `5: _evaluate_c05,` を登録。
- `orchestrator/campaign/s8c_preregistration.py`: `DECIDER_VERSION` を
  `s8c-decider/v4` → `s8c-decider/v5`。
- `orchestrator/tests/test_s8c_preregistration_predicates.py`: C05 の負対照 fixture
  (token-only / mutated ペア) を新規実装、`NEGATIVE_CONTROL_CASES` 移動、
  `test_satisfiable_predicate_requires_negative_control` 等の既存 tripwire 更新。
- `orchestrator/tests/test_s8c_preregistration_invariant.py`: `parse_module` の
  `.py` 限定 assertion を緩和 (C05 の `required_evidence` に非 `.py` path
  `schedule.v1.json` が含まれるため)、`MACHINE_CONTRACT_FUNCTION_CHECKS`/
  `MACHINE_CONTRACT_FUNCTION_EXCLUSIONS` へ C05 の 6 entry を追加。
- `orchestrator/tests/test_s8c_preregistration_core.py`: 契約意味 hash・
  DECIDER_VERSION のハードコード期待値を新しい値へ更新。
- `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g9.json` (新規発行)。

## この wave が主張しないこと (重要)

**C05 は発効していない。** `_evaluate_c05` を production HEAD に対して評価すると
`UNSATISFIED / schedule-consumer-unreachable` になる
(`test_c05_direct_evaluator_reports_current_head_unreachable` が固定)。理由は
`p3_autonomous_workload_trial.py` の `run_trial` が `load_schedule`/`verify_schedule`/
`consume_schedule` を一切呼んでいないため (T-1380 が扱う配線が未実装)。
拒否理由の意味だけが「証拠不足」から「到達不能」へ変わる。entry (667) の C07 と同型。

**§5 `master_seed` の記入と `schedule.v1.json` の commit は本 wave のscope外。**
段3 の敵対相談 2 本 (レンズA/B) が独立に「意味の定義された本物の authority
(`WORKLOADS`/`ROLE_FILES` 等) はこの scope 内では構築不可能」と指摘し、ユーザー裁定
(AskUserQuestion) で「4 項目のみ実装し§5/artifact は T-1380 待ちとして保留」を確定した。
詳細は `verbatim/s4-adjudication.md`。

## 実測 (すべて親が実行)

| 対象 | 結果 |
|---|---|
| 焦点走 (実装+fix 後、g9 発行込み) | rc=0 / **574 passed** (bounded local、受入形ではない) |
| s8b 関連 4 file (契約変更の波及確認) | rc=0 / 548 passed, 17 skipped (既知 freeze-hold) |
| `check_docs.py` | rc=0 |
| 変異 matrix (dispatch 本走) | baseline **PASSED** / **4/4 KILLED** / SURVIVED 0 / MISMATCH 0 |

## 段6 レビューAが指摘した変異事前登録の修正 (DW-M02)

当初の変異#2 (`_evaluate_c05` の到達性検査を弱める) は `required_calls` と
`required_targets` の両方を対象にしていたが、レビューAが「新設 fixture は
`required_targets` 層だけを検証しており、`required_calls` 層を弱める変異は fixture
側の到達不能で先にマスクされ SURVIVED になる」と実測で指摘した。**登録対象を
`required_targets` の弱体化変異 1 件 (`c05act.m03`) に限定して解決した**
(`required_calls` 層の検出力は本 wave の fixture では検証しない既知のギャップ、
entry (662) の scope)。

## 変異 spec 組成時の erratum (F408 の再発、DW-M02)

- **c05act.m01 (契約反転) は過剰決定だった。** 期待していた 2 test (`bijective`,
  `satisfiable_predicate`) だけでなく、実測では 13 test が同時に赤くなった。契約だけを
  `false` へ戻すとコード側 (`_MACHINE_EVALUATORS`) は登録済みのままになり、
  `current_commit_snapshot` fixture の「契約は作業ツリー、コードは HEAD」という
  混合ロジックが不整合を全域へ波及させるため。単一理由性を諦め、expected_nodes を
  実測 13 件へ差し替えて登録した (DW-M03)。
- **`@pytest.mark.xdist_group` 付き 2 test の node ID 表現問題が再発した。**
  `test_candidate_freeze_matches_contract_and_generation_chain` と
  `test_repository_tip_binds_current_decider_version_without_activation` は、
  harness の collection-preflight には suffix なしの node ID が必要で、実行結果の
  照合には suffix (`@s8c-preregistration-candidate`) 付きの node ID が必要という、
  同時に満たせない矛盾があった。**T-1355 (`dev-wave-t1355-c04-c07-decider-bump`)
  が同一の 2 test で同じ問題を独立に発見し `F408` として新規記録済み**
  (SendMessage でのやり取り中に判明)。本 wave はこれを F408 の**再発**として記録し、
  同じ workaround (`--deselect` でこの 2 test を変異 harness の実行対象から除外) を
  適用した (この 2 test は焦点走 574 passed に含まれ、wave 全体のカバレッジからは
  除外していない)。2 回の独立再現により DW-G03 の族一般化条件 (異なる producer/consumer
  で 2 件) を満たしたため、harness 本体の恒久対応 (次の一手) を提案する。

## 並行 wave との資源調整

別セッション T-1355 (条件4/7 evaluator 改訂、同じく DECIDER_VERSION/凍結世代を要求) と
SendMessage で資源調整した。詳細経緯は `verbatim/s1-brief.md` と worklog 本文を参照。
要約: main の DECIDER_VERSION は着手時点で既に v3→v4 (別 wave が消費済み)、その後
T-1355 が先に v4/g8 を着地させたため、本 wave は次の未使用版 v5/g9 を使った。

## 段別成果物 (verbatim/)

- `s1-brief.md` — 段1 brief (生死実験の実測結果を含む)
- `s2-plan-output.md` — 段2 プラン起草 (codex)
- `s3-lensA-output.md` / `s3-lensB-output.md` — 段3 敵対相談 (正しさ境界 / 整合・実効性)
- `s4-adjudication.md` — 段4 の確定裁定 (仕様の正本、レビューA所見反映後の最終版)
- `s5-author-output.md` — 段5 実装子の完了報告
- `s6-reviewA-output.md` / `s6-reviewB-output.md` — 段6 敵対レビュー
- `s6-fix-output.md` — 段6 fix (既存メタテスト追随6項目)
- `mutation/mutation-spec.json` / `mutation/mutation-out.json` — 変異 spec と最終結果

## 未実施

- 受入全走は本 README 作成時点では未実施 (このあと段6 の続きとして投入する)。
- T-1380 (`run_trial -> load_schedule -> verify_schedule -> consume_schedule -> launch` の
  配線、権威の実体供給) は次の一手として持ち越し。完了するまで C05 は発効しない。
