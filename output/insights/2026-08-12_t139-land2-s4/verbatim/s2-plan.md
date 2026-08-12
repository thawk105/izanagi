NO-GO

## 総括

現行 brief のまま解除 decision を land してはならない。独立した blocker が三つある。

1. `a12` は実装も実成果物も 0 件なのに、P6 は本 wave で実装しない。これは「未実装 gate の条件を先に凍結しない」とする [D292:13586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/docs/decisions.md:13586)・[D292:13594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/docs/decisions.md:13594) に正面から反する。現在は通る正例を構成できず、`submit_pilot` は常時拒否する休眠 gate になる。

2. `a09` schedule の generator も 0 件である。driver が caller 提供の seed/table を信用すれば producer 自己申告になる一方、独立再導出を新設すると Q1/Q2 が禁じた fixed semantic validator との境界が未裁定になる。

3. P5 の根拠が自己矛盾している。brief は `{{D:coarse-provenance-standard}}` を作らず canonical に存在しないと明記する一方、P5 は同 decision が粗い proof chain を「既に認めた」としている（[brief:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2-s4/s1-brief.md:12)、[brief:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2-s4/s1-brief.md:39)、[brief:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2-s4/s1-brief.md:81)）。粗い record は非権威の運用証拠にはできるが、材料 report・試行台帳・certified 選択の proof chain には使えない。

P1 の「本 wave では投入しない」自体は妥当である。CLI → `submit_pilot` → gate → intent/binding → driver という production consumer chainを作れば孤児 gate ではない。ただし現状は `a12` 不在で受理集合が空なので、P6 を直さない限り実質的には休眠 gate のままである。

P3 は現時点で二重権威を生んでいない。deny-only report の production consumer は 0 件で、出力にも D291 とその trust-root が入っている。ただし [report.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/publication/report.py:235) の公開関数と [report.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/publication/report.py:254) の CLI は将来誤読され得るため、履歴スコープを機械可読に追加すべきである。`pilot_submission = "forbidden"` 自体は変更しない。

## 実装プラン (file:line)

以下は blocker 解消後の条件付きプランである。

1. `orchestrator/campaign/t139_pilot.py`（新規、予定 1〜460 行）

   - `submit_pilot` は source-side admission なので `preregistration` でも、qualification-only を掲げる [qualification/__init__.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/__init__.py:2) でもなく `campaign` に置く。
   - 公開 API は次だけにする。

     ```python
     def submit_pilot(
         *,
         repository_root: Path,
         evidence_root: Path,
     ) -> PilotSubmissionBatch
     ```

   - `cluster_slot`、`decision_id`、`released: bool`、`a09_passed`、`a12_passed`、caller 作成 binding、qsub stdout、command runner は受け取らない。HEAD・実成果物・qsub stdout から内部導出する。
   - 予定 45〜125 行: sanitized `git show HEAD:docs/decisions.md` と fence-aware heading scan。D292 後の release marker を動的に探し、一意性と後続参照を検査する。D 番号や後続 decision 集合を literal 固定しない。
   - 予定 126〜195 行: `a09` と `a12` の実成果物 gate。両者の権威 API が実在するまで実装開始不可。
   - 予定 196〜285 行: pilot 全体の immutable intent。exact slot `[1..8]` と各 slot の nonce、schedule digest、release decision/HEAD、driver/collector digestを、最初の qsub より前に durable 化する。
   - 予定 286〜410 行: slot ごとの create-only invocation claim → qsub → stdout-derived job ID → binding。qsub 後・binding 前 crash では自動再投入を拒否する。
   - 予定 411〜460 行: compute driver 用の `verify_pilot_submission_binding(...)`。raw qsub で起動された job は benchmark 前に拒否する。
   - `orchestrator/campaign/__init__.py` は編集せず、公開名は `orchestrator.campaign.t139_pilot.submit_pilot` に限定する。

2. [submission.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/submission.py:143)〜158、161〜173

   - `_durable_json` の O_EXCL・file fsync・parent-dir fsync を共通 helper として再利用可能にする。
   - [submission.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/submission.py:150) の単発 `os.write` は short-write loop に直す。
   - T-126 固有の `prepare()`、toolchain、series identity は T-139 へ流用しない。写すのは durable create protocol だけとする。

3. [qsub_binding.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/qsub_binding.py:19)〜23、44〜93

   - exact 8 key、厳密 stdout grammar、stdout-derived job ID、nonce/intent/invocation/retry binding はそのまま再利用する。
   - `validate_qsub_binding(..., expected_schema_version="t126-qsub-binding/v2")` を追加し、既存 caller は既定値で不変、T-139 は `t139-pilot-qsub-binding/v1` を明示する。
   - schema literal 以外の独自 binding family は作らない。

4. `orchestrator/campaign/t139_pilot_schedule.py`（新規、予定 1〜220 行、blocker 解消後）

   - authoritative `a09` から canonical 157 行 TSV を再導出する。
   - driver は intent 内の schedule file record を読むだけでなく、この module で独立再導出して bytes/hash を照合する。
   - pilot は full schedule の slot 1〜8だけを消費し、各 slot の12 blockを3 armへ展開して36 run、全体288 runとする（[record-items-v2.md:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:306)、[record-items-v2.md:632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:632)）。
   - caller 提供 schedule を「検証済み」として受け取る APIは作らない。

5. `orchestrator/campaign/t139_pilot_driver.py`（新規、予定 1〜620 行）と `tools/pegasus/t139_pilot.pbs`（新規、予定 1〜110 行）

   - PBS wrapper は nonce だけを受け、qsub は呼ばない。
   - driver は bounded wait 後、intent・invocation・binding・実 `PBS_JOBID` を照合する。T-126 の [t126_driver.py:969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/t126_driver.py:969)〜996 の durable binding と、1066〜1111 の snapshot patternを写す。
   - gate と schedule 検証が終わるまで output namespaceも benchmark processも作らない。
   - 1 allocation は割り当てられた1 slotの36 runだけを schedule 順で実行し、phase capは2400秒契約に従う。
   - raw stdout/stderr、run event、終了状態を create-only で残す。receipt は生成しない。

6. `orchestrator/campaign/t139_pilot_collector.py`（新規、予定 1〜380 行）と `tools/pegasus/collect_t139_pilot.py`（新規、予定 1〜80 行）

   - login-side のみ。binding、PBS job ID、schedule digest、driver terminal record、raw file identityを再照合する。
   - 出力は `t139-pilot-collection-evidence/v1` の非権威 recordと raw file recordsに限定する。
   - `qualification_status`、`certified`、材料 report entry、試行台帳 entry、`t139-receipt/v1` は書かない。
   - [collector.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/qualification/collector.py:15)〜44 の安全な file reader、strict JSON、file record、binding validation patternを再利用する。

7. [report.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/publication/report.py:216)〜232

   - 既存の `pilot_submission` / `main_submission` は不変。
   - 次のような additive fieldを追加する。

     ```text
     report_scope.kind = historical_snapshot
     report_scope.as_of_decision = D291
     report_scope.current_submission_authority = not_evaluated
     ```

   - `submit_pilot` は `publication.report` / `approval_d291` を importしない。生きた gate と履歴 report の権威を分離する。
   - [approval_d291.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/publication/approval_d291.py:182)〜183、478〜479 は編集しない。

8. 解除 decision fragment（親所有、blocker 解消前は作成・fold禁止）

   `docs/spool/decisions/2026-08-12-t139-pilot-submission-release-1.md` の本文骨子は次とする。

   - D292 を supersede するのは pilot だけ。main は引き続き forbidden。
   - 解禁対象は `orchestrator.campaign.t139_pilot.submit_pilot` が作り、driver が再検査した「valid pilot run」に限定する。
   - canonical HEAD decision、authoritative a09 schedule、実走済みかつ検証済み a12、durable intent/invocation/qsub bindingを必要条件とする。
   - raw collection evidence は operational-only で、receipt・certification・publication・試行台帳 authorityを与えない。
   - D291 report は fold 時点の履歴であり current authorityではない。
   - fragment、実装、束縛検査を同一 land に含める。fragmentだけを先行 landしない。
   - allocator 後の D 番号はコード・テストへ pinせず、安定した release markerから動的に同定する。

9. テスト nodeid 案

   - `test_t139_pilot_submission.py::test_release_is_read_from_head_not_worktree_or_spool`  
     working tree・fragment・handoffを authorityにする変異を殺す。
   - `::test_release_accepts_unrelated_later_decisions_without_literal_id_set`  
     D番号または後続 decision集合の固定を殺す。
   - `::test_release_rejects_duplicate_marker_and_later_reference`  
     二重 release・後続 supersession無視を殺す。
   - `::test_missing_a09_rejects_before_intent_and_qsub` / `::test_missing_a12_rejects_before_intent_and_qsub`  
     gate削除、producer boolによる穴埋め、qsub先行を殺す。
   - `::test_all_eight_intents_are_durable_before_first_qsub`  
     一部slotだけの事後選択と intent後書きを殺す。
   - `::test_unbound_invocation_is_never_automatically_resubmitted`  
     qsub後 crash の二重投入を殺す。
   - `::test_t139_binding_has_exact_keys_schema_and_stdout_job_id`  
     extra key、caller job ID、schema混同を殺す。
   - `::test_all_t139_qsub_sites_are_discovered_and_only_submit_pilot_is_authorized`  
     glob/ASTで増える T-139 production filesを走査し、直接qsub追加を殺す。
   - `test_t139_pilot_driver.py::test_direct_qsub_without_bound_intent_stops_before_run`  
     [dispatch_compute.py:1475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/tools/pegasus/dispatch_compute.py:1475) 等からの raw qsub bypassを殺す。
   - `::test_bound_positive_executes_36_runs_per_slot_and_288_total`  
     slot/run欠落、重複、順序変更を殺す。
   - `::test_schedule_hash_and_independent_rederivation_are_both_required`  
     申告 hashだけを信用する変異を殺す。
   - `test_t139_pilot_collector.py::test_collection_is_operational_only_and_preserves_raw_bytes`  
     raw欠落と権威昇格を殺す。
   - `::test_collection_never_emits_receipt_or_certified_entry`  
     P5を receipt別名で迂回する変異を殺す。
   - [test_t793_report.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4/orchestrator/tests/test_t793_report.py:33) と132〜142を編集し、deny literalを維持しつつ historical scopeを pinする。
   - T-126 回帰として既存 qsub binding testsへ default schema不変と short-write拒否を追加する。

## 束縛検査

| 束縛 | 予定署名・位置 | fail-closed 条件 |
|---|---|---|
| canonical解除 | `require_canonical_pilot_release(repository_root: Path) -> CanonicalPilotRelease`、`t139_pilot.py` 新規45〜125行 | HEADにrelease markerなし・重複・D292以前・後続decisionから参照・Git/UTF-8/heading不正 |
| 前提充足 | `require_pilot_prerequisites(*, repository_root: Path, evidence_root: Path) -> PilotPrerequisites`、新規126〜195行 | a09 generator/bytes/hash不在または不一致、a12 verifier/実成果物不在・失敗・曖昧 |
| submit経路 | `verify_pilot_submission_binding(*, repository_root: Path, submission_dir: Path, pbs_job_id: str) -> PilotSubmissionBinding`、新規411〜460行 | intent/invocation/binding欠落、job ID不一致、digest/schema/key不一致、batch外slot、直接qsub |

禁止は署名でも固定する。`submit_pilot` に `released`、`decision_id`、`schedule_seed`、`cluster_slot`、`a12_passed`、`job_id`、`binding`、`qsub_stdout`、`run_command` を渡せる余地を作らない。

通る正例は「HEADに一意な release decisionがあり、後続の無関係 decisionが増えても releaseが維持され、authoritative a09から再導出した scheduleが exact `[1..8]`、実 a12 verifierが passし、8件のintentが全てdurableになった後に得たqsub stdoutと実PBS job IDが一致する」ケースである。ただし現 repoにはa12側が存在しないため、この正例は現在は構成不能である。mockでだけ通すことは正例に数えない。

## blocker

- B1 — `a12` 不在: P6を維持すると acceptance setが空で、D292が禁じる未実装条件の先行凍結になる。a12 producer・schema・verifier・実成果物を先行実装するか、本 wave scopeへ入れる必要がある。
- B2 — `a09` authority不明: driverが消費する scheduleを誰がどの canonical inputから生成するか未定。caller入力を信用せず再導出する実APIを指定し、Q1/Q2の禁止との境界を親が裁定する必要がある。
- B3 — P5の権威偽装: coarse provenanceを認めた canonical decisionは存在しない。collector出力を「非権威・将来の proof chainにも未採用」と明記するなら運用経路としては残せるが、材料report・試行台帳・certified選択には何も入らない。
- B4 — P4(iii)の意味: repoから人間の直接qsub自体を禁止することはできない。機械的に保証できるのは「直接qsubでscheduler requestが作られても、valid T-139 runはdriver preflightを越えない」までである。decision本文もこの保証境界で書く必要がある。

## 未読・未確認

必読ファイルの未読はない。ただし指定どおり、次は部分読みに留めた。

- `t126_driver.py`: 960〜1120行のみ。
- `collector.py`: 1〜120行のみ。
- `dispatch_compute.py`: `qsub` hitの前後40行のみ。
- `approval_d291.py`: 170〜200行、470〜490行のみ。
- `docs/decisions.md`: D292本文のみ。D308/D316は親briefの要約を根拠にし、本文は未読。
- `record-items-v2.md`: 指定された三範囲のみ。

指定行数と実ファイルには1行程度の差があり、`submission.py` は194行、`qsub_binding.py` は93行、`report.py` は266行、`test_t793_report.py` は146行だったため、それぞれ実EOFまで読んだ。

a09の逐語アルゴリズム、a12の成果物schema/producer、実PBS上での8 allocation投入順は未確認である。pytest・build・qsubは実行しておらず、緑は確認していない。

## 規模と lane 分割

blocker解消後、a12 producer/verifierを除いた見積りは production約1,500〜2,100行、test約1,600〜2,300行。a12を本 waveへ追加するなら、この見積りとlane契約は再作成が必要になる。

| 所有 | production | tests | 見積り |
|---|---|---|---|
| lane A — 投入経路 | `submission.py`、`qsub_binding.py`、`report.py`、新規 `t139_pilot.py`、新規 submit CLI | 新規 `test_t139_pilot_submission.py`、`test_t793_report.py`、T-126 binding/durability回帰 | production 500〜700、test 650〜900 |
| lane B — driver + collector | 新規 `t139_pilot_schedule.py`、`t139_pilot_driver.py`、`t139_pilot_collector.py`、PBS wrapper、collector CLI | 新規 driver test、collector test | production 1,000〜1,400、test 950〜1,400 |
| 親 | decision/worklog/failures fragments、insights、統合検査 | lane test fileは編集しない | docsのみ |

`A ∩ B = ∅`。共有 contractはlane Aの `t139_pilot.py` が所有し、lane Bはimportする。decision fragmentを含むdocsは親だけが編集する。現状はB1〜B4が閉じるまで段5へ進めない。