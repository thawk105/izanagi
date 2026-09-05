## must-fix

なし。静的検査では、成果物の値・受理集合・参照を変える回帰や、受入全走を赤にする漏れを確認しなかった。

## 旧 3 名の残存参照

実行可能な caller、import、re-export、`__all__`、doctest、動的 import 経由の残存は 0 件。走査範囲は worktree 全体、特に `orchestrator/`、`tools/`、ignored を含む `output/`、`docs/`。

25 箇所の test caller は報告どおりだった。

- `_build_manifest` 12 件、`_write_manifest` 13 件: `test_s8b_oracle_manifest.py:196,402,410,424,443,469,489,528,551,571,607,630,657,780,801,858,1591,1607,1807,1848`、`test_s8b_oracle_report.py:268,391,402`、`test_s8b_oracle_driver.py:2336,2347`
- `_build_manifest_from_ratified` の test caller は 0 件。production 内部 caller 1 件は [s8b_oracle_manifest.py:1245](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_oracle_manifest.py:1245)。

旧名の字面は次に残るが、caller ではない。

- 公開属性拒否用の意図的な 3 文字列: [test_s8b_oracle_manifest.py:1250](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_oracle_manifest.py:1250)
- 本体不変条件で維持された例外文言: [s8b_oracle_manifest.py:906](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_oracle_manifest.py:906)
- 現行 runbook の陳腐化した参照: [phase3-8b-restart-runbook.md:276](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/docs/phase3-8b-restart-runbook.md:276)
- archive、decisions、過去の `output/insights/` にある履歴記録は実行参照ではない。

同名の別物は未変更。例は [related_work_search.py:4972](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/related_work_search.py:4972)、[p3_b4_analysis_ledgers.py:1016](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/p3_b4_analysis_ledgers.py:1016)、[prepare_inputs.py:671](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/output/insights/2026-08-24_t1618-xdist-controller-cost/prepare_inputs.py:671)。

## 赤になりうる meta-test / 構造検査

なし。

- growth hold は registry 自体だけを件数・digest 固定し、ratified-verify 全 node を対象外と明記する: [test_growth_test_holds_contract.py:398](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_growth_test_holds_contract.py:398)、[同:445](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_growth_test_holds_contract.py:445)
- flaky registry は別の 1 node のみ: [flaky_test_holds.py:200](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/flaky_test_holds.py:200)
- duration ledger にない新 node は unknown duration として受理される: [conftest.py:1524](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/conftest.py:1524)
- 新規ファイルはなく、既存 2 test file は既に pytest-only allowlist 内: [README.md:169](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/README.md:169)、[同:174](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/README.md:174)
- 新 helper は import 時に実行されず、4 新 test からだけ呼ばれる: [test_s8b_ratified_verify.py:854](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:854)、[同:1027](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:1027)。各 test は自身の `tmp_path` から repo を構築するため、同 file の他 test へ状態は漏れない: [同:677](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8b_ratified_verify.py:677)
- process scanner は production AST の process call だけを数えるため、関数改名は無影響: [test_ccbench_spawn_sites.py:332](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_ccbench_spawn_sites.py:332)
- perf scanner の token、call、guard は変化していない: [test_official_perf_closure.py:479](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_official_perf_closure.py:479)
- holdout 全 repository scan に新しい三軸 conjunction は加わっていない: [test_s8c_preregistration_invariant.py:623](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8c_preregistration_invariant.py:623)
- s8c predicate の evaluator ID と負例集合にも対象名は含まれない: [test_s8c_preregistration_predicates.py:2910](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/test_s8c_preregistration_predicates.py:2910)

## nit

- 現行 runbook の旧 API 記述は親の修正が必要: [phase3-8b-restart-runbook.md:276](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/docs/phase3-8b-restart-runbook.md:276)
- 「13 file」は `test_*.py` の lexical 集合としては過不足なし。ただし全 Python consumer と呼ぶなら、直接 import する非 test helper が別にある: [s8b_oracle_spec_fixture.py:12](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/tests/s8b_oracle_spec_fixture.py:12)。この helper は 13 file 中の manifest・report・driver から import されるため焦点走の実行漏れにはならない。
- 差分は許可された 5 file のみ。保存された `s5-diff.patch` と live `git diff` の SHA-256 も一致し、整形・import 順・無関係な既存行の変更はなかった。

## scope 外の所見

既知境界のみ。private 化は Python の命名規約なので、underscore 名を知る in-process caller は [s8b_oracle_manifest.py:818](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_oracle_manifest.py:818)、[同:842](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_oracle_manifest.py:842)、[同:902](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2067-bcd-selection-closure/orchestrator/campaign/s8b_oracle_manifest.py:902)へ明示到達できる。seal token 化は指定どおり scope 外。

## 総括

must-fix は 0 件。  
25 test caller と production 内部 caller 1 件は過不足なく追随している。  
旧名の実行参照は 0 件だが、負例文字列・例外文言・履歴資料・親修正待ち runbook には字面が残る。  
新 helper は各 `tmp_path` 内だけで作用し、既存 sibling test への共有状態変更はない。  
meta-test と 4 構造検査に静的な更新漏れは見つからなかった。  
pytest は指示どおり実行しておらず、実測結果は親の焦点走に委ねる。