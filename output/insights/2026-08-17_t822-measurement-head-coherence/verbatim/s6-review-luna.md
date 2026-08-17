## must-fix

ゼロ。

## nit

### N1: 段 5 の caller 列挙は網羅的ではない

- 所見: 推奨回帰ファイルは妥当だが、「波及可能性」の caller 列挙から receipt verifier 内部の再検証、trial registry 側の parser consumer、accept CLI の subprocess test が漏れている。
- 根拠: `parse_acceptance_receipt_bytes` の caller は [s8c_acceptance_receipt.py:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:597)、[test_trial_registry.py:2164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:2164)、`test_s8c_acceptance_receipt.py:126,158,279,337`。`verify_acceptance_receipt` は [s8c_acceptance_receipt.py:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:647)、[test_layer3_report.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_layer3_report.py:329)、receipt test 内 8 箇所から呼ばれる。accept CLI 自体の consumer test は [test_trial_registry.py:2220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:2220)。
- 影響: 成果物の値・受理集合は変わらない。段 5 報告だけから焦点 node を組むと回帰対象を取りこぼしうる。
- 提案: 段 5 の波及一覧へ上記 caller chain を追記する。既存の四 test file 全走という推奨範囲自体は維持してよい。
- 自己判定: **real / nit**。

### N2: receipt 負例に不要な commit が 1 回ある

- 所見: 新設 3 node は合計 12 commit を作る。receipt 負例の 4 commit のうち、最初の dummy receipt commit は省ける。
- 根拠: acceptance 2 node は `_registered_repo` の seed・manifest・registry 3 commitに各 1 commitを追加する。[test_trial_registry.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:62)、[test_trial_registry.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:130)、[test_trial_registry.py:844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:844)、[test_trial_registry.py:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:868)。receipt node は fixture の 2 commitに coherent・mixed の 2 commitを追加する。[test_s8c_acceptance_receipt.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_acceptance_receipt.py:96)、[test_s8c_acceptance_receipt.py:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_acceptance_receipt.py:120)、[test_s8c_acceptance_receipt.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_acceptance_receipt.py:180)、[test_s8c_acceptance_receipt.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_acceptance_receipt.py:186)。fixture-levelだけで最低 46 Git subprocess、加えて acceptance/verifier 内の履歴 walkが走る。
- 影響: 成果物には影響せず、test wall timeだけが増える。blocker とする規模ではない。
- 提案: receipt 負例を `commit_receipt=False` で作り、coherent receipt の `_commit_all` 戻り値を distinct head に使う。3 commit、Git subprocess 4 回分を削減できる。
- 自己判定: **real / nit**。

## refuted

### R1: 既存 caller・fixture・golden が mixed head で赤になる

- 所見: refuted。列挙した既存 consumer の正例に mixed head はない。
- 根拠: `_receipt_fixture` は全 6 行を同じ値にする。[test_s8c_acceptance_receipt.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_s8c_acceptance_receipt.py:75)。Layer 3 fixture も同一値である。[test_layer3_report.py:265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_layer3_report.py:265)。originless baseline は `acceptance/trials/*/measurement_head` を一値 6 回として凍結している。[test_reflux_originless_compatibility.py:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_reflux_originless_compatibility.py:234)。registry test の `_reports` も一つの引数を全 trialへ渡す。[test_trial_registry.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_trial_registry.py:663)。
- 影響: 既存 fixture・golden の受理集合、レポート値、参照は変わらない。
- 提案: 親の実測で四 test file を確認する。
- 自己判定: **refuted**。

### R2: tracked な凍結 acceptance receipt が検証不能になる

- 所見: refuted。既定 receipt directory に tracked receipt はない。
- 根拠: 正規 directory は [s8c_acceptance_receipt.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/s8c_acceptance_receipt.py:24)。`git ls-files 'output/s8c-trial-registry/receipts/**'` は 0 件で、`output/` の schema version hit も実 receipt ではなく過去 plan の文面 1 件だけだった。
- 影響: 既存凍結成果物の bytes・参照・検証可能集合は変わらない。
- 提案: なし。
- 自己判定: **refuted**。

### R3: acceptance caller が意図せず mixed head を作る

- 所見: 自動 harness については refuted。手動 CLI は任意の 6 report を受け取れるため mixed 経路を持つが、それを拒否することが今回の裁定そのものである。
- 根拠: originless harness は同じ fixture repo上で commitを挟まず 6 trialを生成してから acceptanceへ渡す。[test_reflux_originless_compatibility.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_reflux_originless_compatibility.py:38)、[test_reflux_originless_compatibility.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_reflux_originless_compatibility.py:65)。一方、launch binding は各起動時の HEAD を個別に解決する。[trial_registry.py:1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:1178)。accept CLI は report path 群をそのまま渡す。[trial_registry.py:2748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/campaign/trial_registry.py:2748)。
- 影響: HEADを途中で進めた手動実行では receipt が発行されなくなるが、これは承認済みの受理集合縮小であり、誤った certified 材料を残さない。
- 提案: 運用時は 6 trial を同一 checkoutで実行する。gate は緩めない。
- 自己判定: **refuted**。

### R4: 新設 node が collection pin を壊す

- 所見: refuted。full suite の全 node集合を逐語 pin する検査はなく、real-repo golden は対象 nodeだけの閉集合である。
- 根拠: real-repo marker は明示集合に含まれる nodeだけへ付く。[conftest.py:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/conftest.py:397)。meta-testもその集合と marker の一致だけを検査する。[test_real_repo_serialization.py:724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_real_repo_serialization.py:724)。plain-runner検査は file集合だけを扱い、新規 file はない。[test_plain_runner_coverage.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-tautology-guards/orchestrator/tests/test_plain_runner_coverage.py:44)。
- 影響: real-repo marker集合、collection順、test file allowlist は変わらない。
- 提案: 親の collection meta-test 実測で最終確認する。
- 自己判定: **refuted**。

## 総括

must-fix はゼロ。既存 caller、指定 fixture、originless golden に mixed head はなく、tracked acceptance receipt も存在しない。  
real-repo collection pin と test file列挙にも新設 3 nodeの影響はない。  
nit は段 5 の caller列挙漏れと、receipt負例の不要な 1 commit。  
確認時には作業木が cleanで対象差分は `HEAD` の `06396d0c` に commit済みだったため、同 commitの `HEAD^..HEAD` を静的レビューした。pytest は実行していない。