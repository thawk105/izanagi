## 総括

**NO-GO。blocker は2件です。**

実装上の8 root causeは概ね閉じていますが、process rc と compiler phase drift のテストに後段 mask が残っています。mutation evidenceを behavioral kill として確定できません。

- `s6-pre-fix.patch` は staged diff と SHA-256 一致。
- `s6-fix.patch` は unstaged diff と SHA-256 一致。
- fix規模は申告どおり `+453/-71`。
- `git diff --check`、`git diff --cached --check` は異常なし。
- pytest/buildは指示どおり未実走。緑は申告しません。
- code-level blocker 0、test/mutation-evidence blocker 2、regression確認 0。

## Closed-Partial-Regressed表

| pre-fix root cause | 判定 | post-fix判定 |
|---|---|---|
| `uint64_t` bits注入false-green | **partial** | [condition_meaning_gate.py:545](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:545) のexact `double` assertにより静的には閉じた。`uint64_t`ではこのassertがcompile失敗する。compiler test未実走のためDW-O16上はpartial。 |
| parent symlink/root containment | **partial** | 全中間componentが`O_DIRECTORY | O_NOFOLLOW`、最終componentも`O_NOFOLLOW`。[condition_meaning_gate.py:248](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:248) persistent parent symlink bypassは閉じた。 |
| cross-file/path swap | **partial** | 3 fdを全て先に開き、fd before/afterとpath reopen identityを照合する。[condition_meaning_gate.py:330](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:330) 同一UIDがsnapshot間で交換・復元する完全attestationは残るが、atomic snapshotは主張しておらず過大主張ではない。deterministic swap nodeは未追加。 |
| compiler identity未固定 | **partial** | dev/inode/size/mtime/ctime/hashをbefore-version、after-version、after-compileで取得し、baseline照合してevidenceへ格納。[condition_meaning_gate.py:581](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:581)、[condition_meaning_gate.py:733](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:733) claimもsnapshot間復元、delegation、version self-reportを除外して一致。ただしFinding 2のtest maskが残る。 |
| F707 compiler-before-rejection | **closed static** | `_resolve_compiler`と`_run_process`を即失敗化し、0 callを固定。[test_condition_meaning_gate.py:117](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:117) |
| duplicate marker二重負例 | **closed static** | `text + text`で正しいdecoder 2blockだけになった。[test_condition_meaning_gate.py:235](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:235) uniqueness bypassでfirst/lastのどちらを選んでもmeaningはPASSするため、単一理由負例。 |
| bare supply reason | **closed static** | bareはsupplied集合に残り、`cache_name=None`を`supply-value-mismatch`へ分類。[condition_meaning_gate.py:484](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:484) |
| adapter provenance claim | **closed static** | caller-supplied textでありowner pathをattestしないと明記。[source_digest.py:1899](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:1899) |
| M01/M02 supply mutation | **partial** | production predicateはfail-closedだが、旧mutationは引き続きmask/equivalent。独立resolution seam nodeへの再登録が必要。 |
| M07 finite mutation | **partial/reclassify** | safetyはpointwise比較でも維持される。behavioral killではなくdiagnostic sensitivityとして再登録すべき。 |
| M08 process mutation | **partial** | timeout/rc/stderrとcompile/runのnodeは分割されたが、rc fixtureにstderrが残りFinding 1のmaskがある。 |
| sort/source_digest既存経路 | **partial** | fix限定patchではsource_digest docstring以外の既存経路とsortを変更していない。pre-fix refactorも旧wrapperと同一extractorを共有。静的な期待反転・削除・skipは0だが未実走。 |
| supply/meaning独立、scope境界 | **closed static** | 別公開関数・別evidenceで、meaningはsupply result/adapterを参照しない。production caller 0、driver integration none、現1000未保護、残り7 macro未対応のまま。 |
| regressed | **0** | 新しいproduction false-green、fd leak、既存期待値反転は現物上確認せず。 |

## 新規Findings

1. **real / severity=high / scope内 / blocker**

   - file:line: [test_condition_meaning_gate.py:387](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:387)、[condition_meaning_gate.py:654](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:654)
   - 反例: compile/run return-code fixtureは`rc=4`に加えて`stderr=b"failed"`を持つ。rc guardだけを除去しても、直後のstderr guardが同じfailure reasonで拒否するため、両rc testはそのまま通る。
   - 成果物影響: M08のcompile-rc/run-rc mutationがSURVIVEDしてもKILLEDと誤記され得る。process-failure mutation台帳を確定できない。
   - 最小fix: 2つのreturn-code fixtureを`stderr=b""`にする。stderr負例は既存のrc=0専用nodeだけに残す。

2. **real / severity=high / scope内 / blocker**

   - file:line: [test_condition_meaning_gate.py:488](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:488)、[condition_meaning_gate.py:742](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:742)、[condition_meaning_gate.py:767](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:767)
   - 反例:
     - after-version照合だけを除去すると、fixtureの永続的な交換はafter-compile照合が同じ`compiler-identity-drift`で拒否する。現testは通る。
     - after-compile照合だけを除去しても、現testはafter-versionで停止し、そのanchorへ到達しない。
     - 両照合を無効化しても、交換後scriptがbinaryを作らず、後段`decoder-run-failed`になる。赤になってもacceptance killではない。
   - 成果物影響: compiler phase mutationを有効なkillとして数えられず、照合が失われたgateが有効binaryを残す交換compilerを受理するfalse-greenを見逃す。
   - 最小fix: after-versionだけidentityを不一致にし、その後baselineへ戻すnodeと、after-compileだけ不一致にするnodeを分ける。process seamで有効version/compile/run結果を返し、対象照合を外した場合だけMeaningEvidenceが返るfixtureにする。

3. **nit / severity=low / scope内 / non-blocker**

   - file:line: [test_condition_meaning_gate.py:305](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:305)、[condition_meaning_gate.py:688](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:688)
   - 反例: early unknown-row predicateだけを除去しても、final exact set照合がextra/missing集合を拒否する。現fixtureは0:1欠落も同時に持つ。
   - 成果物影響: production受理集合への影響はない。early unknown guardをbehavioral killとして登録した場合だけmutation分類が誤る。
   - 最小fix: codeは変えない。early guardはdiagnostic pinとし、必要ならtestで`detail`のunknown-row文言まで固定する。

## Refuted

- **refuted / scope内**: `uint64_t` bits注入はexact `decltype` assertでcompile拒否される。sizeof assertだけの旧false-greenは残っていない。
- **refuted / scope内**: persistent parent symlinkは各componentの`O_NOFOLLOW`で辿れず、最終fileもregular-file限定。開いたfdは成功・失敗経路とも閉じられており、静的fd leakは確認しない。
- **refuted / scope内**: compiler evidenceとclaimの不一致。必要な5 stat fieldとhash、3 phaseがevidenceに入り、同一UID完全attestationやdelegated processを明示的に主張外としている。
- **refuted / scope内**: source_digest/sort既存経路の受理緩和。fix patchはsource_digestのdocstringだけで、sort側変更は0。pre-fixのsort wrapperは旧hole bytesと例外文言を共有extractorへ移しただけ。
- **refuted / scope内**: supply/meaning結合。公開arm、evidence、入力導線は独立し、production callerは0。F718はテストに存在しても現行1000点をproduction上保護しない。

## Mutation再登録案

旧M01からM08はそのまま使わず、次へerratum再登録するべきです。

| mutation | exact anchor | expected node |
|---|---|---|
| M01 supply membership | [condition_meaning_gate.py:485](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:485) のmembership guard | 新規`test_supply_membership_is_independent_of_route_and_value`。adapter seamでsupplied集合だけ欠落、cache nameとeffective valueは正しくする。F707 nodeはpolicy pinでありM01 killに数えない。 |
| M02 effective value | [condition_meaning_gate.py:491](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:491) の`effective != str(value)` | 新規`test_supply_effective_value_mismatch_with_correct_route_is_rejected`。cache nameは正しく、effectiveだけ誤らせる。 |
| M03 marker authority | [evolve_block.py:38](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/evolve_block.py:38) のunique pair判定 | `test_duplicate_correct_marker_blocks_are_rejected`とsort shared-parser duplicate case。後者には安定した`id="duplicate"`を付けてexact node化する。 |
| M04 captured-hole authority | [condition_meaning_gate.py:731](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:731) の`block.hole` dataflowをknown-good holeへ差替える一時mutation | formula-comment、uniform-shift、result-kind、nonfiniteの4 node。productionへbaseline constantを追加しない。 |
| M05 pointwise comparison | [condition_meaning_gate.py:781](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:781) のcomparison bypass | F718、formula-comment、uniform-shiftの3 node。invertは別mutation。 |
| M06 duplicate row | [condition_meaning_gate.py:688](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:688) の`identity in observed`だけを除去 | `test_duplicate_rows_fail_closed` |
| M06 missing row | [condition_meaning_gate.py:702](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:702) のfinal set check bypass | `test_missing_rows_fail_closed` |
| M07 finite output | [condition_meaning_gate.py:693](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:693) | `test_nonfinite_decoder_output_fails_closed`をdiagnostic sensitivityとして登録。behavioral KILLEDに数えない。 |
| M08 timeout | [condition_meaning_gate.py:650](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:650) | compile-timeoutとrun-timeoutの2 node |
| M08 return code | [condition_meaning_gate.py:654](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:654) | compile-rcとrun-rcの2 node。Finding 1修正後に登録。 |
| M08 stderr | [condition_meaning_gate.py:659](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:659) | compile-stderrとrun-stderrの2 node |

追加の事前登録:

- result kind: [condition_meaning_gate.py:545](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:545) のexact-type assert削除 → `test_result_identifier_must_be_exact_double`。
- parent nofollow: [condition_meaning_gate.py:250](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:250) の中間component `nofollow`削除 → `test_parent_component_symlink_outside_root_is_rejected`。
- all-fd-first: [condition_meaning_gate.py:333](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:333) のopen/read二段を逐次open-readへ戻すmutation → 新規cross-file swap seam node。
- path-after reconciliation: [condition_meaning_gate.py:347](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:347) のidentity比較削除 → 新規`test_captured_input_path_swap_after_open_is_rejected`。
- compiler after-version: [condition_meaning_gate.py:742](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:742) の照合削除 → Finding 2のphase専用node。
- compiler after-compile: [condition_meaning_gate.py:767](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:767) の照合削除 → Finding 2のphase専用node。

## GO-NO-GO

**NO-GO**

- blocker: **2**
- non-blocking nit: **1**
- code-level false-green blocker: **0**
- test/mutation-evidence blocker: **2**
- regressed: **0**
- pytest/build: **未実走**