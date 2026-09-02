## 総括

このプランをそのまま段5へ渡すのは不可である。最も重い穴は、校正・実行環境・build receipt を hash で認証するだけで、spec の実効 field と意味的に束縛していない点である。
現存する calibration 成果物には完全な `PerfConfig`、特に `extime/reps` がなく、現案では spec 自己申告値を「校正済み」として受理してしまう。
fake `MeasurementResult` を返す高位 seam だけのテストでは、実際の `measure_point` adapter と CLI execute 経路が未検査のまま通る。
一方、`D` を直接測る既存実装はなく、新規の専用 driver 自体は必要である。材料レポート接続が scope 外なのは D1437 による正しい境界であり、穴ではない。
静的検査のみを行った。pytest、bench、build は実走しておらず、緑とは判定していない。

## 所見

1. **主張:** 校正済み `PerfConfig` の入力源が実在せず、プランは calibration と spec 内 `perf_config` を意味的に束縛していない。受理阻害級である。

   **根拠:** 事前登録は「その環境で `PerfConfig` を校正し、成果物にする」と要求する [preregistration.md:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/docs/phase3-b4-reflux-ablation-preregistration.md:889)。プランは calibration artifact の path/hash と、別の `cells[*].perf_config` を置くが [plan.md:98](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:98)、両者の field equality を要求していない。現行 `calibration/v2` の exact top-level schema は `threads/workload/saturation` 等で、`extime/reps` を持たない [schema_v2.py:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/calibrator/schema_v2.py:563)。登録済み calibration も build 時の `TRACE=0` は持つが [calibration-94a4b79fa31bba3c.json:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:10)、完全な `PerfConfig` 成果物ではない。

   **放置したときの影響:** 任意の `extime/reps`、さらに calibration と異なる workload を spec に書き、無関係な calibration bytes の正しい hash を添えた入力が受理される。測定分布、session median、最終 `D` と candidate floor が変わる。

   **提案:** driver は、全5 field を持つ人間承認済み・content-addressed な `PerfConfig` 成果物ができるまで execute を拒否すること。その成果物の producer は本 wave に追加せず、明示的な上流前提または別作業とする。既存 calibration の構造検証には `calibration_verify.load_verified_calibration` [calibration_verify.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/calibration_verify.py:81) を再利用し、最終的な5 field は成果物との exact equality を要求する。

2. **主張:** execution contract、site、source commit、build receipt は「hash が合う不透明な bytes」に留まり、実環境・binary・spec field への束縛がない。

   **根拠:** プランは `site/env_tag/clocks_per_us/numactl` と `trace` を spec field に置き [plan.md:99](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:99)、参照文書には同じ path/hash 規則だけを適用する [plan.md:125](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:125)。contract 内容と environment field、build receipt と binary SHA/trace、`source commit identity` と実行時 HEAD の equality は書かれていない。事前登録は env tag を同じ site resolver から導出するよう要求する [preregistration.md:886](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/docs/phase3-b4-reflux-ablation-preregistration.md:886)。現物には `site_policy.current_site` [site_policy.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/site_policy.py:66)、site-aware resolver [p2_2.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/p2_2.py:235)、実環境 attestation [execution_guard.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/execution_guard.py:576) がある。S8b の receipt は少なくとも `trace is False` と binary 実 hash を意味的に検証している [s8b_binary_admission.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/s8b_binary_admission.py:247)。

   また、spec の `settle_first` を各 `measure_point` に渡しても、runner は `settle()` の戻り値を捨てる [runner.py:1085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/calibrator/runner.py:1085)。これは admission gate にならない。`require_complete_metrics` もプラン上の frozen field がなく [plan.md:106](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:106)、それでも明示的に runner へ渡すとしている [plan.md:240](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:240)。

   **放置したときの影響:** login node、別 env tag、別 contract、trace-enabled binary、別 source revisionの測定が、正しい自己申告 hash を持つだけで候補集合へ入る。`require_complete_metrics=True` と `use_perf=False` の組合せなら、runner は必須 counter 欠落として全測定を落としうる。

   **提案:** execute 前に live siteから contractを解決し、spec、calibration、execution receiptと完全一致させる。build receipt は schema検証して binary SHA、trace、source identity、contract identityを再導出する。同じ floor に合成する全 window は同じ frozen source/spec/build identityを要求する。`settle_first` は admission条件から外すか、戻り値を検査する専用の window-level gateにする。`require_complete_metrics` は frozen fieldに加えるか、`use_perf` から一意に導出する規則を spec schemaへ明記する。

3. **主張:** テスト seam が production adapter を迂回するため、bench 非実走でも必要な本番経路検査になっていない。

   **根拠:** `run_window` は高位の `MeasurementRequest -> MeasurementResult` 関数を受ける [plan.md:58](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:58)。テストはすべて fake measure を使い、`measure_point` 自体を起動しない [plan.md:254](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:254)。テスト一覧には `_measure_with_runner` の引数変換、ScalePoint 投影、または `--execute-window` が production adapter を選ぶ命題がない。runner の raw 証跡は初期化だけでなく、return code・時刻・throughput を別箇所で埋める [runner.py:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/calibrator/runner.py:1189)。

   **放置したときの影響:** workload、extime、reps、numactl、sink の一つを adapter が落としても、全 `run_window` テストが通る。CLI の validate-only は動くが executeだけ壊れる成果物になりうる。

   **提案:** fake `measure_point` を `_measure_with_runner` の直下へ注入し、全 positional/keyword 引数、sink、ScalePointから `MeasurementResult` への変換を検査する。さらに CLI execute 分岐がその adapter を選ぶ統合テストを追加する。実 subprocess は一切不要である。

4. **主張:** `cells` と `pairs` が candidate/reference artifact参照を二重所有している。

   **根拠:** cellにも candidate/reference参照を持たせる一方 [plan.md:101](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:101)、pairも `reference_artifact_id` と candidate IDを持つ [plan.md:133](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:133)。両者の一致規則は記されていない。

   **放置したときの影響:** plannerがcell側、runnerがpair側を読むなどの実装差で、計画に記録したbinaryと実測binaryが分かれる。対照対と共通参照点の受理集合が実装順序依存になる。

   **提案:** artifact参照の所有をpairだけに寄せる。cellに残すなら、pairから参照される全IDとのexact equalityをloaderで要求し、その不一致テストを追加する。

5. **主張:** 上限統計はまだ実装可能な確定状態ではなく、親P2とプランが矛盾している。

   **根拠:** 親P2はdriver内に上限統計実装を持たせないとしている [BRIEF.md:46](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/BRIEF.md:46)。一方、プランは適切な既存関数がないため組込み `max` registryを新設する [plan.md:7](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:7)。プラン自身もfunction IDが未裁定だと認めている [plan.md:306](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:306)。

   **放置したときの影響:** 採用する関数によってcandidate floorそのものが変わる。59/299等の許容限界の説明を同一window内の連続標本へ一般化すると、値は同じ最大でも、そのcoverage主張が失われる。

   **提案:** 段5前にfunction ID、入力単位、window内標本と独立campaignの扱い、実装identityを人間が凍結する。P2は「専用driver内のclosed exact実装を、裁定済みIDにだけ束縛する」へ修正する。裁定前はloader/planまでは実装できても、authoritativeなfinalizerを完成扱いにしない。

6. **主張:** file:lineの大半は妥当だが、一部は実在しない予告行または不正確なアンカーである。これは nit であり、床値自体への直接影響はない。

   **根拠:** 現時点で `floor_pair_driver.py` と `test_floor_pair_driver.py` は存在しないため、プラン内の全 `floor_pair_driver.py:*`、`test_floor_pair_driver.py:*` は実在アンカーではなく予定行である。既存箇所では `runner.py:1104-1117` は raw rep の「収集」ではなく初期 carrier の作成であり、実値設定は `:1189-1218` と `:1236-1275` にある。`s8b_floor_campaign.py:6077-6103` も、pre競合時はpost probeをせず `probe_after=None` で戻る [s8b_floor_campaign.py:6077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/s8b_floor_campaign.py:6077)。

   **提案:** 新規fileの行番号を「予定範囲」と明記する。runner anchorを複数箇所へ直し、S8b参照は「pre clear後の経路」と限定する。

7. **主張:** 規模はプラン記載だけで約1,280行、実効性の穴を閉じると約1,500〜1,700行になる見込みである。

   **根拠:** module 760行 [plan.md:14](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:14)、test 520行 [plan.md:254](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2166-floor-pair-driver/codex/t2166-floor-pair-driver/plan.md:254) に worklog が加わる。semantic binding、adapter test、live admissionの追加分が未計上である。

   **放置したときの影響:** 760行へ収めるため意味検証を削ると受理集合が広がる。逆にcalibration producerまで本waveへ入れるとD1453の専用adapter境界を越える。

   **提案:** calibration producerとconsumer接続は別作業のままにし、既存leafを再利用する。専用schema、closed statistic、B4固有の3-session sampleに限定する限り、規模は大きいが「汎用測定基盤」にはまだ当たらない。

## 層の表

|層|実在する面・成果物|プランの被覆|判定|
|---|---|---|---|
|1. 対象driver/site/cell/statisticの人間裁定|D1437、D1383、事前登録§11|実装しない|正しい人間境界|
|2. 校正済み完全`PerfConfig`の生成|現calibratorはrecords/threads/workload等まで。extime/reps成果物なし|path/hashを要求するだけ|上流前提は未成立。自己申告を通すのは穴|
|3. trace-disabled binaryとbuild receiptの生成|buildcache、build admission、S8b専用receiptは存在|buildはしない|生成をscope外にするのは正しい。意味検証欠落は穴|
|4. 測定手順specの作成・承認・commit|まだspec実体なし|loaderだけ実装|人間・上流境界|
|5. spec/path/hash/checkout検証|新規loader予定|被覆あり|構文・hashは被覆。semantic bindingは不足|
|6. 決定的plan生成|新規HMAC planner予定|被覆あり|被覆|
|7. 非測定preview|`--validate-only`予定|被覆あり|被覆。ただし凍結・認可の証明ではない|
|8. live site/env/build admission|既存site resolver、env contract、attestationあり|時刻、probe、binary hashのみ|不足|
|9. pre→measure→post→append journal|S8bに既存形あり、新driverで専用再実装|被覆あり|被覆。production adapter test要|
|10. rawからmedian、gain、D再計算|新規pure function/finalizer予定|被覆あり|被覆|
|11. stratum upperと最終candidate floor|新規closed registry予定|式が未裁定|未着手条件。裁定前は完成不可|
|12. 証拠確認、採用裁定、§5記入|人間手番|実装しない|D1383による正しい境界|
|13. 材料reportへのauthoritative floor接続|現状は常に`floor=None` [p3_b4_material_report.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/p3_b4_material_report.py:224)|実装しない|D1437で明示的に切られた別作業。穴ではない|
|14. 4分類analysis|既存evaluatorは`0 <= floor < 1`を要求 [p3_b4_analysis_path.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/p3_b4_analysis_path.py:349)|変更しない|consumer接続後の既存層|

## 親 brief への反証

- **P1は規範ではなく実装選択である。** 事前登録が要求するのは「測定前にcommitされた測定手順の凍結」であり [preregistration.md:871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/docs/phase3-b4-reflux-ablation-preregistration.md:871)、JSON、実行時HEADとのbyte一致までは裁定していない。tracked JSON案は安全な提案だが「正しい形」と断定しない方がよい。

- **P2は現物と両立しない。** 適切な既存upper関数がない以上、「driverに実装を持たせない」と「specが名指しした関数を適用する」を同時には満たせない。プランも実際にはclosed registryの新設へ変更している。

- **P3は概ね正しい。** `between_run_floor.measure_point_floor` は固定点のsession-median CVで [between_run_floor.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/between_run_floor.py:202)、`D`ではない。ただしproduction receiptやenvironment admissionまで低水準runnerだけで代替できるわけではない。

- **P4は必要性を過大に述べている。** validate-onlyは有用だが、結果を見る前の凍結を成立させるものは人間裁定とcommitである。validate-only成功を凍結または測定認可の証拠として扱ってはならない。

- **trace-disabled不変条件は現プランでは自己申告である。** `trace=false` fieldとbuild receiptのhashだけでは、receipt内容とbinaryの関係を証明しない。

- **DW-G05の因果は必要条件と十分条件を混ぜている。** driverがなければ床値を測れないのは正しいが、driver完成だけでは§5は埋まらず、埋まっても現material reportは変わらない。D1437のconsumer接続と人間の採用裁定が別に必要である。

- **アンカー表は概ね実在する。** `PerfConfig:168`、`default_perf:1012`、`measure_point:1057`、`strict_probe:1693`、preregistration `§11.2:918` は指した意味を持つ。`_write_out:255` は関数定義位置で、実際の衝突拒否は269〜271行、exclusive createは301行であるため、より正確な行へ直せるが nit である。

- **標本数の実測値の一般化:** 59/299、8標本時の約33.7%/7.7%は独立標本という条件下では算術的に妥当である。ただし同一window内の連続標本へcoverageを一般化してはならない。親brief自身はこの限定を不変条件に書いており、プランのsummaryも独立campaign数とsession数を別fieldで保持すべきである。

## 検査したが問題なしと判断した点

- repository内に、共通referenceを使う `D = |gain_1-gain_2|` を測ってupperを出す既存driverはない。新設自体は必要である。
- `s8b_floor_stats.py` は絶対throughput dispersionの別formulaで、S8b binary admission/contractも引く。今回の`D`統計への直接再利用は不適切である。
- `s8b_floor_contract.py` は軽量寄りだが、S8b固有の8 session、retry、freeze cell shape、scheduleをpinしており、今回のspec validatorとしては使えない。
- `pegasus_floor_scoping.py` と `calibrator/stability.py` は固定動作点のwithin/between CVを測る別量であり、今回のupper関数を提供しない。
- `s8b_floor_campaign.strict_probe` の直接importを避け、runnerの共有classifierだけを使う判断は、巨大なcampaign依存を避ける点で妥当である。
- 共通referenceを1標本内で共有する式、欠測1件で全体未生成、retry/補充禁止、rawからの再計算、`upper >= 1`を切り詰めない設計は要件と整合する。
- 最終pathを最初からexclusive-createし、失敗時にも削除・renameしない方針は、既存`between_run_floor._write_out`より強いcreate-only証拠になる。
- 材料レポートconsumer、§5値セル、採用裁定を変更しないことは、D1437・D1383による正しいscope境界である。