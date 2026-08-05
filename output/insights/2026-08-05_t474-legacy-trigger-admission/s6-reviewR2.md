# R2 防御レビュー

## 所見

### R2-1 / validator SHA drift の裁定済み限界が新 D から欠落している / severity: must-fix

- 根拠: 親裁定は SHA drift を real とし、他 filesystem の run-root を未証明の限界として記録するよう要求している（[s4-adjudication.md:30](/work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/s4-adjudication.md:30)、[s4-adjudication.md:42](/work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/s4-adjudication.md:42)）。一方、新 D の非主張は WAL ABA などで終わり、この項目がない（[decision fragment:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/spool/decisions/2026-08-05-dev-wave-t474-legacy-trigger-admission-1.md:46)）。validator SHA はファイル全体から算出され（[artifact_admission.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:542)）、receipt に入る（[artifact_admission.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:112)）。実際、HEAD の `59de7c9d…` から変更後の `37850bb0…` へ変わる。実装報告の「挙動が変わるのは旧6件だけ」も receipt 値については誤り（[s5-impl.md:28](/work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/out/s5-impl.md:28)）。
- 失敗シナリオ: 未探索の外部 run-root に旧 validator SHA を持つ v3 Layer3 report があると、campaign bytes が不変でも、現行 validator から再生成した receipt との完全一致検査（[autonomous_trial_completeness.py:1010](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/autonomous_trial_completeness.py:1010)、[autonomous_trial_completeness.py:1085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/autonomous_trial_completeness.py:1085)）で拒否される。
- 成果物影響: 材料レポートの `admission_decision.validator.sha256` 参照が stale になり、report bytes は残っても campaign-chain の受理集合から落ちる。試行台帳の `cells[i].admission_decision` も不一致となり、その chain を前提とする certified 選択候補を認証できない。親実測範囲 `/work/1/SFC/tanab` では該当 0 件だが、他 filesystem は未証明。
- 提案: コードは裁定どおり維持し、新 D の非主張へ「validator 実装 SHA は全 decision receipt で変わる」「指定範囲の persisted artifact は 0 件」「他 filesystem の run-root は未探索」を追記する。実装報告も「分類・status の変化は旧6件のみ」と限定する。

### R2-2 / 新 D は既存の分類値と decision consumer を過小に記述している / severity: nit

- 根拠: 新 D は「binding 証明済みと歴史的無証明を型でも値でも区別できなかった」とする（[decision fragment:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/spool/decisions/2026-08-05-dev-wave-t474-legacy-trigger-admission-1.md:38)）が、decision には従来から `classification` があり（[artifact_admission.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:81)）、`AdmittedCampaign` も decision を保持する（[artifact_admission.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:123)）。また「既存 consumer は decision を読まない」とする箇所（[decision fragment:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/spool/decisions/2026-08-05-dev-wave-t474-legacy-trigger-admission-1.md:58)）に対し、Layer3 は receipt を埋め込み（[layer3_report.py:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/layer3_report.py:468)）、completeness checker は完全一致を読む。
- 失敗シナリオ: 後続設計が「既存の区別値・consumer は存在しない」という誤った履歴を前提に、不要な schema 変更や consumer 移行を起こす。
- 成果物影響: この prose 単独では certified 選択・材料レポート・台帳の現行値や受理集合は変わらないため nit。
- 提案: 「分類値による識別は可能だったが、`admitted` capability は `admission_status != legacy-unclassified` だけで発行され、raw consumer に分類分岐を強制していなかった」と修正する。証拠 field 案の却下理由も「field が admission gate に結線されない」と限定する。

### R2-3 / supersede 条項が D160 の却下案まで置換するように読める / severity: nit

- 根拠: fragment は「却下選択肢のうち当該6件を拒否へ反転させない判断」を置換するとする（[decision fragment:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/spool/decisions/2026-08-05-dev-wave-t474-legacy-trigger-admission-1.md:29)）。しかし D160 が却下したのは「全 trigger campaign への binding 遡及要求」そのもの（[decisions.md:7961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/decisions.md:7961)）であり、今回も binding を遡及要求せず status で拒否している。
- 失敗シナリオ: 後続の読者が、旧6件にも binding/v1 の retroactive 証拠を要求する判断が復活したと解釈する。
- 成果物影響: 現行実装では raw 受理集合・凍結参照・台帳値に追加変化はないため nit。誤解に従う将来変更では旧 freeze の proof-chain 参照まで拒否されうる。
- 提案: supersede 対象を D160 決定5の「機械 sweep 6件について遡及被害ゼロを実測した」という raw-admission 結果だけに限定し、「全 trigger campaign への binding 遡及要求」の却下は維持すると明記する。

### R2-4 / literal corpus は削除には安全側だが trusted snapshot 拡張には追随しない / severity: nit

- 根拠: 負例6件と正例21件は literal 列挙されている（[test_artifact_admission.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:56)、[test_artifact_admission.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:88)）が、trusted snapshot 全体との集合一致検査はない。現 snapshot は固定 commit（[legacy_admission_overlay_v1.json:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/legacy_admission_overlay_v1.json:7)）で、現在は 30 campaign = overlay 3 + 負例6 + 正例21 と一致している。
- 失敗シナリオ: listed campaign の削除・改変はファイル読取または snapshot 照合で赤になり安全側。通常の新 campaign は固定 snapshot に存在せず historicity gate で拒否されるため安全側。一方、将来 `created_from_commit` または grandfather 集合を拡張しても literal を更新し忘れると、その追加分だけ正例 coverage に入らず、対象限定の過剰拒否が検出されない。
- 成果物影響: 現在の値・受理集合への影響はない。将来追加された正当な歴史 campaign が raw view／新規材料レポートの受理集合から誤って落ち、その campaign を参照する試行台帳が不成立になりうるため nit。
- 提案: explicit literals は維持しつつ、snapshot 内の paired `campaign.lock`/WAL 集合が「overlay + 負例 + 正例」の和集合と完全一致する census test を追加する。

## `require_admitted_campaign` caller 棚卸し

| caller | 旧6件の到達性 | 判定 |
|---|---|---|
| `critic/digest.py:459,706` | 任意 layout／`--campaign-dir` で到達可能 | 今回の意図した拒否。引数なしは P2-2 で非 trigger |
| `campaign/replay.py:107` | generic discovery と custom root なら到達可能 | 標準 `discover_p2_2_dir` は非 trigger で維持 |
| `campaign/layer3_report.py:375` | 任意 campaign path で到達可能 | 新規 Layer3 拒否の本対象 |
| `campaign/p3_s4_loop.py:281,960` | `make_critic_digest` の型上は任意 layout、通常配線は policy-bound S4 | 通常 resume は旧6件を渡さない |
| `campaign/s8a_trigger_sweep.py:525` | `_load_rows` の型上は任意 layout | public `report()` は現行 policy-bound ID を再導出するため旧6件を渡さない |
| `campaign/s6_sort_sweep.py:421` | `_load_rows` の型上は任意 layout | 通常配線は非 trigger sort campaign |
| `campaign/p3_s4_red.py:170` | 固定の policy-bound red campaign | 渡さない |
| `campaign/p3_s4_loop_sort.py:484` | 固定の policy-bound sort-loop campaign | 渡さない |
| `campaign/autonomous_trial_completeness.py:1085` | producer 導出 ID と root を先に照合 | 旧 sweep 6件は渡せない |

テスト側の直接 caller は `test_artifact_admission.py:355,380,389,421,444,717,739,748,761,775,783`、`test_critic.py:69,171`、`test_bench_first_real_wal.py:144`、`test_p3_s4_loop.py:85`、`test_p3_s4_loop_sort.py:83`、`test_p3_s4_loop_trigger_gating.py:118`。旧6件を実際に渡す追加検査は `test_artifact_admission.py:380` と、`render()` 経由の `test_layer3_report.py:262` だけである。既存 fixture は post-policy、非 trigger 歴史、または既存 overlay 拒否で、従来期待値の削除・変更はない。

現行 s8a resume は pre-T343 ID と policy-bound ID が分離済み（[test_s8a_trigger_sweep.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_s8a_trigger_sweep.py:262)）であり、旧6件を再開対象にしない。

## 凍結・所有境界

二層状態は実装と一致している。raw admission は旧6件を拒否する一方、`s1_known_axes_freeze` は旧 campaign の provenance を直接読む（[s1_known_axes_freeze.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s1_known_axes_freeze.py:471)）。s8b は exact-hash の known-axes freeze を読み、binding を再構成する（[s8b_holdout_freeze.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s8b_holdout_freeze.py:524)、[s8b_holdout_freeze.py:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s8b_holdout_freeze.py:809)）。fragment の grandfather 記述自体はこの境界を記録している。

`git diff HEAD` 上、変更は実装1ファイル、テスト2ファイル、新 D fragment のみ。`s8a_trigger_sweep.py`、`output/`、`layer3_schema.json`、`autonomous_trial_completeness.py`、`s1_direct_comparison.py`、`s1_verify_extime_calibration.py` に tracked difference はない。

このレビューではテストを実走していない。提示された request 889258 の対象2ファイル 100 passed を前提情報として扱った。全受入は未走のままである。

## 総括

**NO-GO — must-fix 1件、nit 3件。**

production gate、既存 caller、resume、freeze grandfather、所有境界には must-fix の不整合を認めない。land 前の blocker は、親裁定が明記を要求した validator SHA drift／外部 receipt 失効限界を新 D に復元すること。