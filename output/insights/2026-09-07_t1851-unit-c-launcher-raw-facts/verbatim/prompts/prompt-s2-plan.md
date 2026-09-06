単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s1-brief.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s1-brief.md` — 親 brief (scope、**terminal 証拠の契約 (親案)**、不変条件、provisional 裁定 (P1)〜(P6)、実アンカー表)
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/a2beta-decisions-fragment-9.md` — 継承元の裁定 3 件の逐語 (E1 / E2 は単位 C、証拠の意味規則 3 点、分類 claim / 回復行は囲まない)
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/decisions-verbatim.md` — 確定裁定 11 件の逐語 (D1113 / D1114 / D1194 / D1336 / D1337 / D1340 / D1341 / D1342 / D1522 / D1530 / D1533)
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/b2d1-README.md` と `refs/b2d1-s4-adjudication.md`、`refs/b2d1-decisions-fragment-10.md` — 直前の実装 wave (B2 / D1)。prefix inspector、result v5 契約、proof 型、verifier の v4 / v5 分岐の現状と、閉じていない窓・次 wave の出発点
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/a2alpha-README.md` と `refs/a2alpha-s4-adjudication.md` — v2 世代・claim v3・capability 消費・v2 terminal の二層拒否 (S5 / S6) を置いた wave。**13 節の裁定パッケージ 1 / 2 と 14 節 (E2 の 4 語候補、supersede すべき pin 2 箇所)** が本 wave の直接の前提
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/a2beta-README.md` — A2β (段 1 で止めた wave)。1 節 (引数の前提が現物と食い違った経路) と 7 節
7. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/a1-README.md`、`refs/a1-s4-adjudication.md`、`refs/b1-README.md` — A1' / B1 の成果と閉じていない窓 (A1' 段 4 が固定した 2 つの封印 terminal API の signature はここにある)
8. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/s2-plan-v2.md`、`refs/s4-adjudication-r2.md`、`refs/t1946-proof-chain-s4-adjudication.md`、`refs/brief-v2.md` — 設計 wave の plan v2 / 終端裁定 / proof chain の設計凍結。「単位 C: 起動層」節が本 plan の土台

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` である。コードはすべてこの worktree の中を読む。base commit は本 branch の HEAD `04f06d032` であり、B1 / A1' / A2α / B2 / D1 の実装と local main `97ee3cd3a` の両方を含む。

## 依頼

6 段分割 `B1 → A → B2 → D1 → C → D2` のうち **C の第 1 checkpoint C1** (terminal 証拠の契約、起動層の証拠封印、台帳層の封印 terminal API = E1、台帳専用理由語彙 4 語 = E2、証拠文書の durable 化と terminal 行への digest 束縛) の実装プランを file:line 粒度で起草せよ。C2 (campaign `_Runner._run_session` の launcher 配線、producer capture、`RESULT_SCHEMA` v5 切替、pending 再読、resume) と B2 / D1 の terminal 依存部分は**実装しない**。それらは境界 (symbol・引数・戻り型) だけを固定する。

出力は 4 部構成にする。**契約の検証 (依頼 1) と規模の実測 (依頼 2) を先に出せ。**

## 依頼 1 — terminal 証拠の契約の検証

親 brief の「terminal 証拠の契約」節は親案である。field ごとに次を現物で確かめて表にせよ。

- その field の値は、起動層 (`s8b_floor_attempt_launcher.py`) が **campaign の自己申告を経由せずに**取れるか。取れる場合は取り口の file:line (例: `OpenedFloorAttempt.measurement` から throughputs をどう読むか — `calibrator/runner.py` の opened measurement の型と attribute 名を実名で書け)。取れない場合は、どの層の引数として受けるしかないか、そのとき D1113 (呼び手が値を選べない) をどう守るか。
- `expected_use_perf`: `use_perf_from_receipt` (`orchestrator/calibrator/perf_preflight.py:261`) を launcher から直接呼べるか (import 関係、循環の有無)。`mode` と receipt を reservation 時の不変入力として受ける形で D1113 に反しないか (親案: mode と receipt は識別入力であり、そこから bool を導出するのは機械導出)。
- `probe_before` / `probe_after`: launcher が pre-probe を所有する形 ((P2)) を、`_run_session` :6242-6255 の現行挙動 (pre-probe 競合なら capture しない) と、`test_ccbench_spawn_sites.py:212` の在庫 pin から検証せよ。
- `repetition_evidence`: launcher 私有の list を `capture_measure_point(..., rep_observations=<private list>)` へ渡し、`token.open()` 後に snapshot する経路が現物で成立するか (`calibrator/runner.py:803-` の `rep_observations` と `token.open()` の関係、`_CERTIFIED_MEASUREMENT_KEYWORDS` :32 との関係)。
- `raw_output_sha256` と `self_report`: terminal builder (`FloorAttemptTerminal` :123) の戻りから何を証拠へ写し、何を比較にだけ使うか。
- **再導出 policy (E1) と `TransitionPolicy.require_terminal_reason_equals_classification=True` (`s8b_attempt_profile.py:639-`、`attempt_registry_core.py` の該当検査) の両立**: classification の `pre_observation_failure_reason` (凍結語 `competing_process` / `launch_failure`) と terminal の `failure_reason` (E2 の語) は文字列として一致しない。core の等値要求を現物で読み、(a) 等値要求の意味を「同じ生の事実からの再導出が一致」へ定義し直す、(b) v2 の policy で等値要求を外し封印 API 側で検査する、(c) 別案、のどれを採るか根拠付きで決めろ。**D1113 の「辞書を権威にしない」との両立を必答とする。**
- 状態語の対応 ((P4)): `retryable-failure` を理由ありの唯一の terminal_status にしてよいか。`retryable_terminal_opens_next_attempt=False`、`max_series_attempts=None`、budget (`_s8b_v2_budget_key`) との整合を現物で確かめよ。
- 証拠文書の durable 化 ((P6)): receipts dir への create-only 公開と、replay 時の `_assert_classification_artifacts` :2059 同型の検査が、既存の `_atomic_update(prepare=...)` :1739 の形に載るか。crash 後に権威として読み直す bytes の規則を 3 行以内で確定せよ。

契約の field に過不足があれば、追加 / 削除の理由を D1113 / fragment 9 / 現物の到達可能性で示せ。

## 依頼 2 — 規模の実測と分割判定

各群 (launcher の pre-probe と sink / 証拠の封印 handle / core の v2 terminal 新 field と再導出 validator / adapter の封印 API と artifact 検査 / profile の E2 と validator 差替え / test) について次を実測して表にせよ。

- 変更する production file と、その file 内で変更・新設する関数・定数の実名と現行行番号。
- 追加・変更・削除される production 行数の見積もり。推測なら推測と書き、根拠にした現物の行数を添えろ。
- 更新・新設が必要な test node 数。**名前の推測でなく現物を数えろ。** 変更する production symbol を参照している既存 node を実際に列挙せよ (特に `record_attempt_terminal` の呼出し、`_reject_unsealed_s8b_v2_terminal` / `[s8b-v2-terminal]` の pin、v2 terminal の event_keys pin、launcher の `_RecorderRegistry` :158)。
- その群を単独で実装したとき、他の群を実装しないままでも production が壊れず既存 test が緑を保てるか。保てないなら、どの群と束ねる必要があるかを名指しせよ。

そのうえで判定せよ。**1 wave (実装子 2 本 + fix 3 巡以内) で安全に実装し 1 commit へ統合できるか。** できないなら分割案を 1 つに絞れ。分割の必須条件は「前半だけを積んだ状態で production が整合し、既存 test が緑を保ち、後半との境界の symbol・引数・戻り型を今この plan で固定できること」である。逆に余裕があるなら、C2 のうち C1 に足せる最小の部分 (例: producer capture の thin wrapper、v2 profile / genesis を protocol + schedule から組む純関数) を名指しせよ。

## 依頼 3 — 実装プラン (file:line 粒度)

実装子へそのまま渡せる粒度で書け。各項目に現行の file:line を付けろ。次を必ず含めること。

1. **`SealedTerminalEvidence` の型と seal。** exact field、frozen、process-local seal、campaign へ返さない構造 (`FloorPostProbeCapability` :96 と同じ型検査の形)。launcher のどこで作るか (`_launch_floor_attempt` :527 の `terminal_builder` 呼出し :619 の後、`output.seal` :624 の前後)。
2. **launcher の流れの変更。** pre-probe の挿入位置、競合時に capture を走らせない分岐、`_pre_observation_failure_reason` :366 と `_external_evidence_sha256` :350 の入力の変更 (probe_before を含めるか)、私有 sink の生成と snapshot、`record_attempt_terminal` 呼出し :628 の封印 API への置換。`_launch_floor_attempt_for_test` :671 の注入面が変わるなら明記。
3. **封印 API の signature と置き場所。** `s8b_attempt_registry.record_sealed_attempt_terminal(observation, evidence)` (親案)。`_require_handle` :280、`_assert_observation_row` :2510、`_reject_legacy_v2_terminal` :2536 の扱い (v1 経路は不変、v2 は封印 API だけ)。core 側 `record_attempt_terminal` :1971 に足す引数 / 新関数と、`failure_reason` の導出。
4. **v2 terminal 行の新 field と validator。** `_S8B_V2_EVENT_KEYS` :490 の terminal に `terminal_evidence_sha256` を足す方法 (v1 の key 集合は不変)、`terminal_row_validator` :683 を「封印 API 以外を拒否」から「証拠 digest と再導出の一致を要求」へ差し替える形、replay (`load_attempt_registry`) がこの validator を行だけで呼ぶ現状 (fragment 9 の理由 4) と、artifact を読む検査を adapter 側に置く分担。
5. **E2。** `S8B_V2_RETRYABLE_FAILURE_REASONS` :532 へ 4 語を入れる。genesis の `retryable_failure_reasons` field (`_S8B_GENESIS_KEYS` :395) が既存 v2 世代の bytes に影響するか (test fixture の genesis が空集合を pin していれば赤になる) を現物で数えろ。
6. **境界の固定 (実装しない部分)。** C2 が呼ぶ `launch_floor_attempt` の引数に本 wave で足すもの (mode / receipt / protocol 由来値の受け口) と、C2 側が用意する terminal builder の契約 (`FloorAttemptTerminal.campaign_record` に何を入れるか)。producer capture の呼び口。
7. **赤になる既存 test の列挙** (直接赤と fixture 経由の transitive 赤を分ける) と、supersede してよい pin (A2α 14 節の 2 箇所、spawn-site 在庫) / してはならない pin (v1 の全 pin、B2 / D1 の proof 型 pin)。
8. **テスト計画。** 正例 (launcher 経由で v2 世代に terminal 行が入り、証拠 file が実在し、replay が通る; 理由なし / 4 語それぞれ)、負例 (self_report と再導出の不一致、証拠 file 欠落 / 改竄、digest 不一致、v2 で旧 `record_attempt_terminal` を呼ぶ、封印されていない evidence、campaign 由来の callable、`rep_observations` の外部指定、probe_after 無しで throughputs あり、E2 外の語)。負例は「他の gate が同じ入力を拒否しない」ことを 1 行で示せ (変異 matrix の観測 node にする)。D1522 に従い、上流が拒否する形でも下層の実体を名指しする直接検査を置け。新規 test file は作らず既存 file へ足せ。
9. **所有分割。** unit1 (launcher + launcher test) / unit2 (core / profile / adapter + その test) を file 所有で割れるか、境界の signature を先に固定すれば並列に書けるか。

## 依頼 4 — 変異事前登録の候補

各候補に (変異位置 file:line、変異内容、KILLED を期待する test node、その test が他 gate に遮られない理由) を書け。10〜16 件。特に「再導出を self_report のコピーに置き換える」「4 語のうち 1 語を落とす」「pre-probe 競合でも capture を走らせる」「証拠 file を読まずに digest だけ比較する」「sink の snapshot を open 前に取る」を含めよ。

## 制約

- 読取専用である。書込可能 tmp が無いので pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 各主張に [実測] (現物を読んだ) か [推測] を付けろ。
- 出力の最後に `## 総括` 節を置き、契約の採否 (field の過不足)、(P1)〜(P6) の採否、分割判定、実装子の本数、規模を 12 行以内で書け。
