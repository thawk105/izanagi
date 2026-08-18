[severity: must-fix] [攻撃シナリオ] C07 は `floor_protocol` と `floor_source` の両方を要求するが、実装は 1 件しか受け付けず、`floor_source` しか検証しない。また実 producer の v4 result にない `measurement_head` を要求する。 [根拠 orchestrator/campaign/s8c_result_judge.py:949-1053; orchestrator/campaign/s8b_ratified_freeze.py:917-924; orchestrator/campaign/s8b_floor_contract.py:80-86; orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:271-297] [提案] ratified の 2 artifact を各 path/hash で検証し、現行 result schema と整合する measurement head の権威を固定する。  
成果物影響: 現 wave の certified 選択・レポート・台帳は変わらないが、活性化後は正規 v4 floor source が拒否され、result table と certified 受理集合が空になる。

[severity: should-fix] [攻撃シナリオ] 親が確認した 1 赤は、`same=True` が prediction だけを同一化し、manifest の off cell は `cfg-*-off` のままなので、C3 は `UNSATISFIED` ではなく prediction-cell binding invalid により `INDETERMINATE` になる。 [根拠 orchestrator/tests/test_s8c_result_judge.py:117-125,438-445,448-455; orchestrator/campaign/s8c_result_judge.py:659-684] [提案] 既存の同一 prediction テストと同じく off cell の configuration を合わせるか、期待値を `INDETERMINATE` にする。judge の優先順位を緩和しない。  
成果物影響: certified 選択・レポート・台帳の値は変わらないが、現状は wave の受入テスト集合が 69/70 で赤のままになる。

[severity: should-fix] [攻撃シナリオ] 文書化された `python3 orchestrator/tests/test_*.py` 単独実行では、新 test が root path を挿入する前に `orchestrator` を import し、さらに `_run()` が pytest に依存するため、環境によって単独検証が起動不能になる。 [根拠 orchestrator/tests/README.md:105-112; orchestrator/tests/test_s8c_result_judge.py:20-22,660-668; orchestrator/tests/test_plain_runner_coverage.py:25-41] [提案] 既存の root path bootstrap を import 前に置き、真の plain runner にするか、pytest 専用 allowlist として正直に登録する。  
成果物影響: certified 選択・レポート・台帳の値は変わらないが、単独実行による受入証拠を得られず、テスト受理集合の再現性が落ちる。

[severity: should-fix] [攻撃シナリオ] `_evaluate_c07` は実装されても production `evaluate_all` から到達せず、C07 は `_evaluate_undefined` の `floor-judge-contract-undefined` に固定される。完了報告を「C07 が有効化された」と読むと、未配線を隠せる。 [根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2152-2164,2167-2204; orchestrator/tests/test_s8c_preregistration_predicates.py:961-979; /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/s4-adjudication.md:31-42] [提案] worklog に「static readiness checker と direct test のみ。registry 非登録、`evaluate_all` は undefined、certified output/ledger row は未生成」と明記する。登録や staged registry は提案しない。  
成果物影響: certified 選択・レポート・台帳の値と受理集合は現状のまま増えず、参照 reason は `floor-judge-contract-undefined` のままである。

## 総括

必読 path は全て読了し、実装変更はしていない。pytest も起動していない。  
最大の問題は floor verifier と ratified の 2 artifact、現行 result schema の不整合である。  
既知の 1 赤は judge ではなく新 test fixture の不整合である。  
凍結 JSON、freeze dir、phase doc、FROZEN_MANIFEST は変更されていない。  
既存 evaluator 集合、negative control、gap snapshot、`evaluate_all` の既存 reason は不変である。  
evidence module の judge import、import 時の top-level call、命名衝突は確認されない。  
新規 file は禁止 token を含まず、full holdout scan の列挙対象には入る。  
ただし単独 runner の import path と pytest 依存は修正または明記が必要である。