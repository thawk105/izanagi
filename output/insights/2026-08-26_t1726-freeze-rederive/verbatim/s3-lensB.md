静的検査の結論は、段 2 プランのままでは実装不能です。`load_legacy_freeze(repository_root)` が、編集禁止の正例を確実に赤くします。加えて eager import は軽量 verifier の依存面を大幅に拡大します。

書込み、import 実行、pytest はすべて未実走です。

## 1. 既存経路の巻き添え

### [real] 編集禁止の `test_trial_registry.py` が赤くなる

`test_p5_six_complete_terminal_reports_pass_acceptance` は、

- temp repo に off descriptor と sidecar を生成・commitする: `test_trial_registry.py:285-308`
- registry acceptance 内で resolver を再実行して digest を確定する: `trial_registry.py:5320-5340`, `trial_registry.py:5643-5652`
- その正しい v3 receipt を標準 verifier へ渡す: `test_trial_registry.py:1597-1605`

という正例です。

しかし temp repo には `output/s8b-freeze/holdout_freeze.json` がありません。プランの `_require_ratified_legacy_arm_authority(root)` は、`load_legacy_freeze(root)` の `root / V1_FREEZE_PATH` 読取りで先に失敗します。`s8b_ratified_freeze.py:1409-1427`

したがって、この正例は digest 不一致ではなく `legacy-read` で赤になります。テストは編集禁止なので、設計変更が必須です。

緩めずに避ける案は、subject repository と verifier authority root を分離することです。v2/v3 を固定 V1 authority に結び付け、legacy freeze は verifier 配布物側の `s8b_ratified_freeze.ROOT` から固定 hash 付きで読む一方、off artifact だけを receipt の `repository_root` と `measurement_head` から読む形です。`s8b_ratified_freeze.py:60-65`, `s8c_arm_inputs.py:336-406`

「receipt repo 自身に legacy freeze が必須」という要件を維持するなら、編集禁止条件との両立手段はありません。

### [real] 現行 v2 fixture のままでは 10 test が赤くなる

現行 fixture は架空 descriptor と `"1" * 40` を使い、legacy freeze と off artifact を持ちません。`test_s8c_acceptance_receipt_v2.py:64-157`

authority 検査をループ前に置くと、次の既存 test は期待している既存 gate より先に freeze 不在で失敗します。

- `test_v2_producer_equivalent_full_verify_drops_only_c02`: `:246`
- `test_receipt_digest_divergence_is_attributed_to_report_descriptor`: `:289`
- `test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof`: `:308`
- `test_origin_terminal_projection_is_retained_and_reverified`: `:333`
- `test_run_start_mismatch_is_rejected_after_reference_hashes_match`: `:366`
- `test_trial_report_arm_execution_mismatch_is_rejected_after_reference_hashes_match`: `:386`
- `test_v2_never_routes_through_v1_mandatory_reason_set`: `:406`
- `test_v3_requires_cross_binding_receipt_sha256`: `:422`
- `test_v3_aggregate_is_recomputed_from_trial_leaves`: `:458`
- `test_binding_digest_is_rederived_from_self_consistent_three_way_claim`: `:474`

プランの fixture 実 resolver 化で救済可能です。ただし authority root を source 側に変更するなら、temp repo への legacy freeze 複製は不要であり、複製しても検査されない fixture にしてはいけません。

`test_pairwise_collision...` は receipt parse 中の pairwise distinct 検査で先に落ちるため、既存帰属を維持します。`s8c_acceptance_receipt.py:503-522`

### [real] 他の必須テストの判定

- `test_s8c_acceptance_receipt.py`: fixture はすべて v1です。`test_s8c_acceptance_receipt.py:75-113`。v2/v3 限定 gate なら結果は変わりません。
- `test_layer3_report.py`: 実 verifier を使う fixture は v1です。`test_layer3_report.py:261-357`。`test_m14...` 等も v1 capability を再検証してから non-certifying で拒否します。`:1620-1684`。結果は変わりません。
- `test_reflux_originless_compatibility.py`: v3 receipt は生成しますが、標準 verifier は呼ばず bytes を読み取って projection 検査します。`:41-100`, `:871-977`。serialized bytes を変えない限り結果は変わりません。
- `test_trial_registry.py`: 標準 verifier の直接正例は前述の 1 件だけです。これは赤になります。

## 2. fixture 実 resolver 化の依存と時間

### [real] 必要な外部条件

- `git`: 必須。現 verifier 自体も既に Git を要求します。`s8c_acceptance_receipt.py:543-582`
- 書込可能 tmp、通常ファイル、`.git` object store: 必須。現 fixture も必要ですが、新 fixture は authority commitを先に作るため commit が最低 1 個増えます。`test_s8c_acceptance_receipt_v2.py:31-46`
- `jsonschema`: 新規の必須 Python 依存です。`s8c_arm_inputs` から `s8b_descriptor` を経由します。`s8c_arm_inputs.py:21-22`, `s8b_descriptor.py:16`
- descriptor schema data file: resolver ごとに読みます。`s8b_descriptor.py:46-54`, `:180-197`
- source checkout 内の legacy freeze bytes: temp repoへ複製する設計の場合に必須です。`s8b_ratified_freeze.py:64-65`, `:1415-1427`

不要なものは次のとおりです。

- network: 不要
- submodule checkout: 不要
- `perf`、`/bin/true`: import 連鎖には現れますが、この call pathでは実行されません。`perf_preflight.py:17-26`
- ccbench submodule検査: `load_legacy_freeze` は行いません。`verify_document` を避ける判断は正しいです。

### [疑い] 小さい test file に対して resolver 呼出しが過剰

`resolve_arm_input` は on/swapped の場合でも必ず off artifact を検査します。`s8c_arm_inputs.py:434-459`。1 回の resolve で 2 pathについて `ls-tree` と `show` を行うため、6セルで24 Git subprocessです。`s8c_arm_inputs.py:336-365`

v2 test fileでは各 testが fixtureを作り直すため、fixture生成と verifier側を合わせて概算約500 Git subprocess、同程度の schema再読込みが発生します。未実走の見積りですが、現在約1.63秒の fileが3.5から5秒程度になる可能性があります。現行の代表値は `acceptance_duration_ledger.json:11999-12008` です。

- `test_s8c_acceptance_receipt_v2.py`: 推定 +1.5から3秒
- `test_trial_registry.py::test_p5...`: 設計修正後でも推定 +0.1から0.3秒。現行9.8秒。`acceptance_duration_ledger.json:15625`
- v1だけの `test_s8c_acceptance_receipt.py` と `test_layer3_report.py`: gate実行時間の増加なし
- `test_reflux_originless_compatibility.py`: gate実行時間の増加なし

全走の RUN 上限は3600秒です。`tools/check_acceptance_reds.py:28-31`。数秒の純増だけで直ちに上限超過とは判断しませんが、軽量 test fileへ数百 subprocessを足す設計は所見対象です。全走影響は未確定、未実走です。

## 3. import の芋づる

### [real] eager import は軽量 verifier の契約を壊す

現在の `s8c_acceptance_receipt` は stdlibだけです。`s8c_acceptance_receipt.py:11-20`

プランの3 importを module top-levelへ置くと、静的な import-time closureは35ローカル moduleになります。主な全連鎖は次です。

- `s8c_arm_inputs`
  - `s8b_descriptor`
  - `jsonschema`
  - `s8b_holdout_freeze`
  - `t080_freeze_migration`
  - `freeze_verification_hold`
- `s8b_ratified_freeze`
  - `calibrator.perf_preflight`
  - `calibrator.runner`
  - `benchparse`, `calibrator.model`, `perfparse`, `holdout_observation`
  - `env_contract`, `env_contract_activation`
  - `env_attestation`, `calibration_verify`
  - `schema_v2`, `effective_clock_policy`, `tsc`
  - `execution_guard`, `site_policy`
  - `s8b_floor_contract`, `s8b_experiment_numbers`, `s8b_floor_stats`
  - `s8b_binary_admission`
  - `build_admission`, `axis_trigger_gating`, `materializer_admission`, `pin`, `reflux_ir`, `source_digest`, campaign `model`
  - `s8b_sort_swo_receipt`, `sort_swo_oracle`
  - `s8b_holdout_freeze`, `t080_freeze_migration`, `freeze_verification_hold`
  - `s8b_launch_cert`

入口は `s8b_ratified_freeze.py:40-53` と `s8c_arm_inputs.py:21-22` です。

具体的な import 時作用は以下です。

- `env_contract` が registry を構築・検証し、fork callbackを2本登録します。`env_contract.py:373-400`, `:732-745`
- `freeze_verification_hold` が pin hashを再計算して不一致なら importを失敗させ、Lockを作ります。`freeze_verification_hold.py:43-65`
- `sort_swo_oracle` が corpus、C++ source、複数 digestを import時に生成し、`inspect.getsource` で実装 sourceを読みます。`sort_swo_oracle.py:669-772`, `:2525-2582`
- `sort_swo_oracle` は Unix固有の `resource` も importします。`:20-39`
- `s8b_descriptor` は第三者 package `jsonschema` を importします。`s8b_descriptor.py:16`

subprocess、network、hardware probe、activation artifact読取りは import時には発火しません。`env_contract` の activation I/O は Mapping 初回操作まで遅延されています。`env_contract.py:748-802`

ただし、最小環境で verifierを importまたはv1 parseするだけの consumerまで、`jsonschema`、Unix `resource`、source file配置へ依存します。これは破壊的です。既存 independence testは `trial_registry` と `layer3_report` の名前しか禁止しておらず、この問題を検出しません。`test_s8c_acceptance_receipt_v2.py:227-243`

少なくとも新依存は v2/v3 gate 内で lazy importすべきです。それでもv2/v3検証時の巨大 closureは残るため、本来は固定 V1 loaderを軽い leafへ分離する裁定候補です。

import循環は静的には見つかりませんでした。

## 4. T-1727 と v4

### [real] 現行 receipt は freeze identityを持たない

v2/v3の trialが持つ authority 関連値は `arm_execution` の3 fieldだけです。`s8c_acceptance_receipt.py:62-84`。binding digestの原像にも freeze hashはありません。`:684-692`。v3 aggregateも `trial_id` と leaf digestだけです。`:179-203`

したがって将来の挙動は次の二択になります。

- `V1_FREEZE_SHA256` を同じ holdout projectionの別 bytesへ差し替える:
  old receiptのdigestは変わらず、将来 verifierで黙って緑になります。どのfreezeで実行したかは誤帰属されます。
- freezeまたは `HOLDOUTS` が descriptorを変える:
  old receiptは将来の再検証で黙って赤になります。発火点は `verify_acceptance_receipt` と、それを再実行する `require_current_verified_receipt` です。`s8c_acceptance_receipt.py:918-1009`, `:1012-1026`
- source `HOLDOUTS` だけを改訂:
  プランの freeze対source exact比較ですべて赤になります。
- 複数 freeze世代を併存:
  receipt内に選択子がないため、一つの current定数以外を選べません。同じ意味なら誤った世代として緑、意味が異なれば赤です。

### [疑い] 「v4 は provenanceだけ」は将来条件では誤り

単一かつ永久不変の V1 authorityという前提下では、v2/v3 schema自体を「必ずV1」と規定できるため、今回直ちにv4を上げなくてもT-1726は成立します。

しかし複数世代、`V1_FREEZE_SHA256` の置換、`HOLDOUTS` または `DERANGEMENT` の改訂が起きた時点で、freeze identityは受理判定そのものになります。provenanceだけではありません。`s8c_arm_inputs.py:186-195`, `:445-459`

正しい運用は「旧v2/v3 artifactを固定V1のlegacyとして読み続ける」です。そのためには、

- `V1_FREEZE_SHA256` を差し替えない
- v2/v3を常に旧V1 bytesと旧V1 resolver semanticsへ結び付ける
- 次世代導入前にv4へ authority path/hash/generationをserialized bindingとして載せる

ことが必要です。

明示的失効を選ぶなら、偶発的な digest不一致ではなく、versioned policyと明示 reasonで失効させるべきです。監査artifactである以上、既定としてはlegacy継続が妥当です。

したがってP2は「今回は上げない」までは成立し得ますが、「旧artifactを読み続けられる」という一般化は、現在の `HOLDOUTS` 依存 resolverのままでは成立しません。

## 5. 層の網羅

### [real] 同じ authority 断絶が receipt issuer層に残る

`trial_registry` は receipt値を resolverから独立再導出しますが、resolverは現在の `HOLDOUTS` と historical off artifactしか読みません。`trial_registry.py:5320-5340`, `s8c_arm_inputs.py:434-493`

legacy freezeとsourceの一致は確認しないため、「registry acceptanceに検査済み」という親 brief の表現は、receiptから独立という意味では正しい一方、legacy freezeから独立再導出という意味では誤りです。

receipt issuer層は編集禁止なので、本waveで実装したふりにはできません。次の裁定パッケージ候補として返すべきです。

- trial registry acceptance issuerへ同じ固定V1 authority bindingを置く
- producer、issuer、receipt verifierが共有する軽量 authority leafを新設する
- T-1727のv4導入時に origin/reflux のserialized arm bindingにも同じ freeze generationを通す

formal producerとcompletenessにはlegacy freezeを読む実装があります。`p3_autonomous_workload_trial.py:854-885`, `autonomous_trial_completeness.py:3801-3845`。ただしtrial registry acceptanceはこのsource検査を呼んでいません。

`layer3_report` は標準 verifierを経由するため、今回のgateが入れば追加の穴は残りません。`layer3_report.py:604-624`

## 6. 親 brief の主張

### [real] 「編集面の競合ゼロ」は意味を広げると誤り

`s8c_acceptance_receipt.py` 自体のテキスト競合ゼロは否定できません。しかし `trial_registry.py` は同moduleを importし、生成したreceiptを標準 verifierへ渡す正例があります。`trial_registry.py:44`, `test_trial_registry.py:1597-1605`

したがって意味的な巻き添えはゼロではありません。

### [real] 「純増検出力」は関数単体では正しいが、システム一般化は誤り

自己整合した誤値を標準 verifier単独で赤くする能力は純増です。しかし同時に、

- authority artifactの配置
- third-party import可能性
- current sourceの世代
- historical off artifactの存在

を新たな受理条件にします。正しい registry生成receiptまで赤くなるため、「誤値だけを追加検出する」という意味の純増ではありません。

### [real] 「受理集合は狭くする方向だけ」は論理的には正しいが、安全な正例維持を証明しない

新述語を論理積に足すため形式上は狭くなります。ただし狭くなる集合に `test_trial_registry.py` の正例が含まれます。よって親の不変条件「既存の緑を通す正例」とは両立していません。

### [real] Layer3への現時点の影響は親 briefが過大評価している

全current schemaは parserで `certifying=false` を強制されます。`s8c_acceptance_receipt.py:393-401`, `:524-539`。Layer3も再検証直後に `certifying is not True` を拒否し、「certified consumerは存在しない」と明記しています。`layer3_report.py:611-624`

したがって現checkoutで誤receiptがcertified選択や論文数値を決める到達可能経路はありません。標準 verifierの穴と将来リスクは実在しますが、現在の成果物影響としての一般化は誤りです。

## 総括

1. **[real] 最重件:** `load_legacy_freeze(repository_root)` は編集禁止の `test_trial_registry.py::test_p5...` を確実に赤くする。subject rootと固定V1 authority rootを分離しない限り、プランは実装不能。
2. **[real]** eager importは軽量 verifierを35ローカルmodule、`jsonschema`、Unix `resource`、source配置へ依存させる。新依存は最低でもlazy import化が必要。
3. **[real]** receipt issuerである `trial_registry` にlegacy freezeとの断絶が残る。本waveのscope外なので、共有authority leafを含む裁定パッケージとして返すべき。
4. **[疑い]** v4見送りは固定V1が永久不変なら可能。ただし複数世代や`HOLDOUTS`改訂後はold receiptが黙って赤または誤ったauthorityで緑になる。v4は最初のauthority改訂前に必須。
5. **[疑い]** 実 resolver fixtureはv2 test fileへ約500 Git subprocess相当を追加し、約1.63秒から3.5から5秒程度へ伸ばす可能性がある。全走上限超過は未確定だが、遅い設計である。
6. **[real]** 親 briefの「競合ゼロ」「純増」「正しい集合を保ったまま狭める」はシステム全体では成立しない。また現在のLayer3 certified経路は構造的に到達不能であり、成果物影響は将来リスクとして書き直す必要がある。

全項目、静的検査のみで未実走です。