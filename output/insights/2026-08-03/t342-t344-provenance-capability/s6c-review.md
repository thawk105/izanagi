静的読解のみで再レビューした。pytest・build は実行しておらず、実測上の成否は判定していない。16 件中、`closed` 11 件、`partial` 5 件、`regressed` 0 件と判定する。

## 対応表

| 元所見 | 判定 | 根拠 |
|---|---|---|
| レビュー1 #1 DTO の可変性 | `closed` | DTO と payload の深い不変化が実装され、呼び出し側からの書換え面は残っていない（[artifact_admission.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:68)、[artifact_admission.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:180)）。 |
| レビュー1 #2 ledger の exactness | `closed` | key・型・順序・重複・digest の exact 検査が集約されている（[artifact_admission.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:244)）。 |
| レビュー1 #3 receipt と variant の再導出 | `partial` | receiptful `BUILD_START` の束縛は閉じたが、`VERIFY_DONE`・`BENCH_DONE`・`ABORT` は START なしで残せる。validator が START 以外をスキップする構文クラスが残存（[artifact_admission.py:545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:545)、[wal.py:606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/wal.py:606)）。 |
| レビュー1 #4 historicity | `closed` | trusted git snapshot の byte hash と exact overlay 双方を要求し、単なる bytes 移設では歴史性を得られない（[artifact_admission.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:355)、[artifact_admission.py:440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:440)）。 |
| レビュー1 #5 critic view | `closed` | issue・sort・red paths が exact `AdmittedCampaign` view を共有し、raw 再読込面は閉じている（[digest.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/critic/digest.py:194)、[digest.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/critic/digest.py:456)）。 |
| レビュー1 #6 producer の valid WAL | `partial` | S6/S8 は閉じたが guided producer が receiptless・attemptless START/DONE/COMMIT を生成し続ける（[guided.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:127)）。 |
| レビュー1 #7 autonomous identity | `closed` | parser authority より前に共通 identity context を確定し、artifact 発行と run が同じ context を使う（[p3_autonomous_workload_trial.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tools/p3_autonomous_workload_trial.py:501)、[p3_autonomous_workload_trial.py:1518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tools/p3_autonomous_workload_trial.py:1518)）。 |
| レビュー1 #8 S8a/registry consumer | `closed` | S8a は receipt と policy/identity を exact 検証し、materializer mapping は canonical registry に一本化された（[s8a_trigger_sweep.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s8a_trigger_sweep.py:132)、[materializer_admission.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/materializer_admission.py:31)）。 |
| レビュー2 #1 producer/guided | `partial` | production `_log_eval` は共有 admission gate が拒否する形を発行し、テストも gate を踏まない（[guided.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:127)、[test_guided.py:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_guided.py:270)）。 |
| レビュー2 #2 diff-reject topology | `closed` | START と ABORT が同一 attempt に束縛され、spy も real validator を side effect で実行している（[p3_s4_loop.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_s4_loop.py:232)、[test_p3_s4_loop.py:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_p3_s4_loop.py:487)）。 |
| レビュー2 #3 S6/S8 public-path proof | `closed` | public sweep と実 capability resolver を経由し、独立 literal pin で identity class を検証している（[test_s6_sort_sweep.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_s6_sort_sweep.py:321)、[test_s8a_trigger_sweep.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_s8a_trigger_sweep.py:365)）。 |
| レビュー2 #4 campaign-ID goldens | `closed` | pre/current の固定 literal と歴史 derivation が分離されている（[test_campaign.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_campaign.py:236)）。 |
| レビュー2 #5 semantic negatives | `closed` | T126 と trigger public path の双方で dirty/authorityless rejection が build 前に検証され、missing-context とも分離された（[test_t126_qualification_driver.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_t126_qualification_driver.py:58)、[test_p3_build_authority_cli.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_p3_build_authority_cli.py:254)）。 |
| レビュー2 #6 autonomous completeness | `closed` | completeness consumer 自身が admission gate を呼び、その後 exact decisions を検査する。期待 identity も独立 literal（[autonomous_trial_completeness.py:1058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/autonomous_trial_completeness.py:1058)、[test_autonomous_trial_completeness.py:1329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_autonomous_trial_completeness.py:1329)）。 |
| レビュー2 #7 silo registry closure | `closed` | 親裁定どおり registry が閉包を担い、silo docstring も実態に訂正済み。`build_admission` 非埋込みは再所見化しない（[materializer_admission.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/materializer_admission.py:2)）。 |
| レビュー2 #8 mutation evidence | `partial` | 現在の HEAD に再照準済み mutation spec がなく、M3/M7/M9/M10/M11 の元 mutation は引き続き広い例外等で mask される（例: [buildcache.py:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/buildcache.py:377)、[artifact_admission.py:592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:592)）。別 worktree の未追跡 spec は committed fix の証拠には数えなかった。 |

## 残存・新規所見

### 1. START に係留されない post-build stage が admission を通る

- **Claim:** variant 再導出の narrow が過大で、START 以外の record 全体を検査対象外にした。任意 variant の `VERIFY_DONE`・`BENCH_DONE`・一定の `ABORT` を START/attempt なしで注入できる。
- **Evidence:** [artifact_admission.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:543)、[wal.py:606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/wal.py:606)、穴を正例として固定した [test_artifact_admission.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_artifact_admission.py:232)。
- **Impact:** admission が「全 later record を START/receipt に束縛する」という契約を満たさない。
- **Suggested fix:** receiptless START→pre-build ABORT の既知例外だけを狭く残し、VERIFY/BENCH と post-build ABORT は既知 START/attempt への係留を必須にする。receiptful START の canonical variant 再導出とは別 invariant にする。
- **重大度:** High。
- **成果物への波及:** この構文だけでは orphan COMMIT は通らないため certified 選択集合は直接増えないが、Layer3 の variants/verifications/runs/aborts と参照 source が追加・再keyされ、材料レポートおよびそれを指す試行台帳の参照・値が変わる（[layer3_report.py:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/layer3_report.py:438)）。

### 2. Guided trial が inadmissible WAL を成功値として消費する

- **Claim:** guided production path は attempt/receipt のない START→VERIFY→BENCH→COMMIT を書き、共有 admission を一度も通さず trajectory と reached cost を返す。
- **Evidence:** [guided.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:127)、raw COMMIT を集計する [guided.py:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:122) と [guided.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:224)、非 gate テスト [test_guided.py:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_guided.py:270)。
- **Impact:** producer の成功判定と共有 consumer の受理判定が分裂する。
- **Suggested fix:** no-build/replay 用にも契約上有効な attempt・policy/receipt topology を定義して発行し、production `_log_eval` から得た実 WAL を `require_admitted_campaign` に渡す E2E を追加する。
- **重大度:** High。
- **成果物への波及:** raw COMMIT の cost/trajectory が guided trial 台帳へ成功値として残る一方、材料レポート側では campaign が拒否され参照が生成されないため、試行台帳の選択値と certified/material 受理集合が不整合になる。

### 3. テスト契約の列挙外変更と self-oracle が残る

- **Claim:** skip/xfail 化・assert 削除・validator monkeypatch は見つからなかったが、段4 §1-E の許可列挙外の期待値変更と production-derived oracle が残る。
- **Evidence:** diff-reject payload expectation [test_p3_s4_loop.py:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_p3_s4_loop.py:69)、critic の production `variant_id` 由来期待値 [test_critic.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_critic.py:84) と [test_critic.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_critic.py:298)、gate を踏まない post-policy 形の screening fixture [test_screening_driver.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/tests/test_screening_driver.py:55)。
- **Impact:** 実質的な強化を含む変更ではあるが、§1-E の唯一契約としては追補裁定なしの変更であり、variant/reference drift を production と同時に追従して見逃すテストがある。
- **Suggested fix:** 親裁定で列挙を明示的に追補するか列挙外期待値を戻す。identity 期待値は独立 literal にし、post-policy fixture は shared gate を通す。
- **重大度:** Nit。
- **成果物への波及:** 現行成果物の値・受理集合・参照を直接変える所見ではないため nit。ただし将来の variant/reference 退行を検知できず、誤った certified/material 参照を固定する可能性がある。

なお、historicity fixture について `require_admitted_campaign`、historicity 判定、view、lock、topology validator の monkeypatch・置換は確認できなかった。real gate を spy する箇所も `side_effect` で実 validator を実行している。

## 凍結・pin 面

pre-wave の `ea6ca43` と現在の `73f3dce` を git object 単位で比較した。

- `FROZEN_MANIFEST`: 23 件、missing 0、hash mismatch 0。全 target が `output/` 配下。
- `output/` tree object: 両方とも `9402a05b0e73166431d6ee68920bbdaccd633480`。
- `s1_known_axes_freeze.py` blob: 両方とも `971fce8caa94adc4183f1c0310912a5d4ee7103b`。
- `test_frozen_artifacts.py` blob: 両方とも `ff601b8e78e1f08554d55c14710de59ee10b8992`。
- 上記三面はいずれも追加・削除・byte 差分なし。

## 総括

最大の残存リスクは、START に係留されない post-build evidence の admission と、guided が inadmissible WAL から成功値を算出する producer/consumer 分裂である。

撤回すべき主張は、G1 の「全 later record が制約・束縛された」と、H1 の「BUILD_START のない任意 variant は正当で過剰拒否が閉じた」という記述である（[g1-report.md:9](/work/1/SFC/tanab/dev-wave-jobs/70fa1240/wave-t342-344/g1-report.md:9)、[h1-report.md:16](/work/1/SFC/tanab/dev-wave-jobs/70fa1240/wave-t342-344/h1-report.md:16)）。