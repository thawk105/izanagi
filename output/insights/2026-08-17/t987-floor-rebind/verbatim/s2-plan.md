## 前提 P1 の確定

**P1 は偽。束縛の実体は機械 gate である。**  
ただし、実体は単純な `protocol.ccbench_pin == HEAD gitlink` 比較ではない。再封印版 protocol を consumer へ通す際の「現行 contract につき 1 件」という resolver と、holdout admission の固定 legacy path authority が実測を止める。

現 HEAD の `external/ccbench` gitlink は `511c9538e4e8efa54b45cda62e72389ed3b706ec` で、承認定数 `orchestrator/campaign/s8b_approved.py:65-67` と一致する。一方、固定 protocol は `output/s8b-freeze/floor_protocol.json:1` の `d706650c...` であり、現 HEAD と不一致である。

この不一致自体は現在も受理される。

- protocol validator は `ccbench_pin` を空でない文字列としてしか検査しない: `orchestrator/campaign/s8b_floor_contract.py:386-400`。
- 現行 resolver の実 repo テストも、選ばれた legacy pin が承認定数と不一致であることを明示している: `orchestrator/tests/test_s8b_protocol_builder.py:1001-1024`。
- build は現在の submodule HEAD を要求せず、protocol pin の checkout を作る: `orchestrator/campaign/s8b_floor_campaign.py:2281-2296`。
- AI reseal は承認定数との一致を検査せず、固定 HEAD から実 gitlink を読んで successor に入れる: `orchestrator/campaign/s8b_floor_campaign.py:936-964`。

### held により発火しない拒否

`HELD=True` と対象 ID は `orchestrator/campaign/freeze_verification_hold.py:14-38`、`status="held"` は同 `:68-76` にある。

| check_id | 本来の拒否位置 | held 中の挙動 | 到達性 |
|---|---|---|---|
| `s8b-floor.sealed-protocol-ccbench-pin-current-head` | `orchestrator/tests/test_s8b_floor_campaign.py:1210-1219` の `assert current_head == ccbench_pin` | `held_marker()` を返し、`AssertionError` は発火しない | **テスト helper のみ**。production campaign に同じ比較はない |
| `s8b-floor.protocol-bytes-expected-pin` | `orchestrator/campaign/s8b_floor_campaign.py:3628-3635`。固定 `floor_protocol.json` の SHA-256 と実行 protocol hash が違えば `FloorCampaignError("launch refusal: floor protocol bytes sha256 が expected と不一致")` | 比較を行わず held marker を残す | official preflight のみ。production official はさらに手前で無条件拒否される |

### held ではなく残っている拒否

| 経路 | 発火条件 | 拒否位置と外向き例外 | 状態 |
|---|---|---|---|
| 標準 Pegasus pilot | 同一 current contract の legacy と新 pin 版が index に並ぶ | `resolve_current_floor_protocol()` が count=2 で `FloorCampaignError`: `orchestrator/campaign/s8b_floor_campaign.py:882-901`。`_admit_floor()` が `AdmissionRejected("floor protocol current validation failed")` へ変換: `orchestrator/campaign/certified_writer_admission.py:200-223`。preflight は rc=3: `orchestrator/campaign/certified_writer_preflight.py:169-185` | **発火する。P1 を否定する主 gate** |
| pilot に versioned protocol を直接渡す | supplied document が固定 legacy document と異なる | `_authority()` が `HoldoutAdmissionError("fixed protocol bytes do not match the supplied protocol")`: `orchestrator/campaign/s8b_holdout_admission.py:463-490`。campaign が `FloorCampaignError("holdout admission reservation failed: ...")` へ変換: `orchestrator/campaign/s8b_floor_campaign.py:6048-6067` | **発火する。第二の主 gate** |
| official の dormant test seam に versioned protocol を渡す | held 済み比較を抜けた後、固定 path の実 bytes と allowlist 上の versioned hash が異なる | `_assert_freeze_allowlist()` が `FloorCampaignError("launch certificate: freeze allowlist hash 不一致: output/s8b-freeze/floor_protocol.json")`: `orchestrator/campaign/s8b_floor_campaign.py:3700-3707,3802-3869` | **held ではない**。production では official 無条件拒否の後ろなので通常は未到達 |
| production official | protocol 内容に関係なく official | CLI は rc=2: `orchestrator/campaign/s8b_floor_campaign.py:6740-6747`。core は `_assert_official_permitted()` の `FloorCampaignError`: 同 `:368-378,5529-5533` | 発火するが、T-987 の pin/chain 束縛ではないため変更対象外 |

さらに標準 job wrapper は `output/s8b-freeze/floor_protocol.json` を固定で渡す: `tools/pegasus/floor_campaign.sh:954-978`。これは例外を投げないが、新 protocol を選べず旧 pin を測るため、resolver を単独で直しても authority が分裂する。D471 もこの残留を明記している: `docs/decisions.md:19610-19616,19624-19633`。

起動外にも次の active gate があるが、今回置換してはならない。

- 人間向け旧 builder は gitlink と `CCBENCH_FULL_SHA` の不一致を `FloorCampaignError` で拒否する: `orchestrator/campaign/s8b_floor_campaign.py:1112-1118`。`freeze_protocol()` からの呼出しは同 `:1276-1285`。
- selector seal も同 builder の失敗を `PredictionRunnerError` に包む: `orchestrator/campaign/s8b_prediction_runner.py:1438-1451,1542-1549`。
- CI の実 gitlink 検査は通常の `AssertionError`: `orchestrator/tests/test_s8b_approved.py:58-64`。

したがって、緩める対象は台帳条件だけではない。**既存 generic resolver や correctness gate を弱めず、明示的な「記録付き再測定 lane」を追加して、上記二つの pilot gate をその lane だけで置換する必要がある。**

## 変更面

推奨する記録先は次である。

`output/env/<env_tag>/floor/attempts/submissions/<submission_nonce>/floor-remeasurement-attempt.json`

記録は exact schema とし、最低限次を持たせる。

| field | 値 |
|---|---|
| `schema` | `s8b-floor-remeasurement-attempt/v1` |
| `event` | `floor-remeasurement-attempt` |
| `status` | `record-only` |
| `relaxed_binding` | `floor-v2-remeasurement-same-generation-chain` |
| `ruling_id` | `T-987` |
| `contract_sha256` | current contract から独立導出 |
| `ccbench_pin` | 固定 HEAD の実 gitlink |
| `floor_protocol` | exact `{path, sha256}` |
| `held_check_ids` | `HELD` が真なら、その時点の `HELD_CHECK_IDS` 全件をソート。偽なら空 |
| 補助 identity | `source_commit`, `submission_nonce`, `pbs_job_id`, `mode="pilot"`, `recorded_utc` |

`status` と `relaxed_binding` により、検査通過証明ではなく「この束縛を記録基準へ置換して開始した事実」であることを明示する。

| file:line | 今どうなっているか | どう変えるか |
|---|---|---|
| `orchestrator/campaign/s8b_floor_campaign.py:882-922` | generic resolver は current contract の候補を exact 1 件要求し、gitlink helper は形式だけを検査する | generic resolver は不変のまま、root だけを引数にする `resolve_remeasurement_floor_protocol()` を追加し、`(current contract, HEAD gitlink)` の exact pair、versioned 導出 path、HEAD/worktree bytes、SHA-256 を検証する |
| `orchestrator/campaign/s8b_floor_campaign.py:2372-2402,6550-6780` | create-only private JSON writer はあるが再測定 record producer はない | zero-arity の `record-remeasurement-attempt` subcommand を追加し、呼び手から各入力を受けずに resolver、PBS identity、hold 状態から record を導出して canonical path へ create-only 保存・read-back 検証する |
| `orchestrator/campaign/floor_submit_receipt.py:13-24,39-98` | submit receipt の exact schema/path/loader だけを持つ | `_FLOOR_KEYS` は一切変えず、sibling attempt record の path、独立 exact schema、strict loader、expected-value binding helper を追加する |
| `orchestrator/campaign/certified_writer_admission.py:65-72,178-224` | 常に generic current resolver を使う | nonce と exact 一致する専用環境 marker がある場合だけ新 resolver を使用し、marker 無しは現行 resolver のままにする。record 自体は後段で作るため、この admission は引き続き read-only |
| `tools/pegasus/submit_floor.sh:7-75,416-432` | pilot holdout 確認 flag と nonce だけを qsub へ渡す | zero-arity `--record-floor-remeasurement` を追加し、選択時だけ `IZANAGI_FLOOR_REMEASUREMENT_NONCE=$NONCE` を export。protocol path/pin/hash は引数にしない |
| `tools/pegasus/floor_campaign.sh:29-95,346-410,954-978` | static admission 後も legacy protocol path を固定して driver を起動する | marker を nonce に束縛し、receipt/source identity 確認後かつ driver より前に record subcommand を実行する。失敗時は driver を起動せず、成功時だけ record 内の検証済み protocol path を渡す |
| `orchestrator/campaign/s8b_floor_campaign.py:5409-5560,5633-5671,5820-5825,6036-6067` | core は record を要求せず、holdout admission には protocol document だけを渡す | marker lane では canonical record を再読し、receipt、current pair、protocol path/hash、hold 一覧を再導出照合する。欠落・改変時は build と測定より前に `FloorCampaignError`。検証済み record を専用 holdout entrypoint へ渡す |
| `orchestrator/campaign/s8b_holdout_admission.py:413-490,735-786,868-897` | authority は常に HEAD の固定 legacy protocol を読み、supplied document との一致を要求する | 既存 entrypoint は完全に維持し、recorded-remeasurement 専用 entrypoint を追加する。versioned path を document の pair から再導出し、100644 HEAD blob、worktree bytes、record hash、supplied document を全照合してから既存 schedule・claim・one-shot gate へ合流する |
| `orchestrator/campaign/freeze_verification_hold.py:14-48` | held ID 集合は count/hash で自己 pin されている | **変更しない**。record producer は read-only snapshot だけを取る |
| `orchestrator/campaign/s8b_floor_contract.py:352-400` | protocol correctness と contract cross-field を検査する | **変更しない**。`ccbench_pin` の意味を validator 側で緩めない |
| `orchestrator/campaign/s8b_floor_campaign.py:265-272,3588-3921` | chain record は freeze namespace と official clean digest の機構 | **変更しない**。新 pattern も新 freeze artifact も追加しない |
| `orchestrator/campaign/floor_liveness.py:55-83` | submission receipt と scheduler/job marker だけで状態を分類する | **変更不要**。sibling attempt record の有無を成功判定へ流用しない |
| `docs/spool/README.md:3-5,28-49` | wave は canonical 台帳を直接編集できない | 新 worklog/decisions fragment に P1 が偽だったこと、専用 lane、chain pattern 不採用、official/default resolver/規律 2 不変を記録する |

### chain record を採らない理由と digest 波及

- submitter の安全境界は `output/s8b-freeze/` への書込みを明示拒否する: `tools/pegasus/submit_floor.sh:105-130`。実測開始時の事実を標準経路から chain namespace へ作れない。
- pilot は official freeze scan を通らない: `orchestrator/campaign/s8b_floor_campaign.py:5722-5748`。既存 characterization は `orchestrator/tests/test_s8b_floor_campaign.py:6884-6904`。したがって pattern 追加だけでは R2 の実効 gate にならない。
- `_CHAIN_RECORD_PATTERNS` に regex を追加しただけでは digest は変わらない。対応する file が存在した場合、`_assert_freeze_allowlist()` が path と bytes hash を `chain_records` へ入れ: `orchestrator/campaign/s8b_floor_campaign.py:3842-3849`、`clean_scan_digest()` が allowlist と結合して path+hash を preimage に入れる: 同 `:3893-3921`。
- その結果 `clean_scan_digest` が変わり、`build_launch_certificate()` の field に波及する: 同 `:3924-3940`。二回 scan と strict 検証は同 `:3975-4000`、発行 certificate の hash と `launch-start` journal への波及は同 `:5770-5798`。
- attempt record も将来 official scan が走れば repository file path 集合には現れる: `orchestrator/campaign/s8b_holdout_freeze.py:367-382`。ただし今回の lane は pilot 限定であり、record bytes の authority は専用 loader と campaign/holdout の再照合に置く。

## 新規/変更するテスト

| test file:line | 追加・変更内容と殺す変異 |
|---|---|
| `orchestrator/tests/test_s8b_protocol_builder.py:636-659,1001-1087` | 新 resolver が same-contract/new-pin の exact versioned pair を選ぶ正例、missing/uncommitted/hash drift/legacy fallback を拒否する負例、引数が root だけである検査を追加。generic resolver を HEAD pin selector に変える変異を殺す |
| `orchestrator/tests/test_campaign.py:4944-5062` | marker 無しは既存 resolver、exact nonce marker だけが新 resolver、壊れた marker・disk bytes 差替えは `AdmissionRejected` を確認。既存 admission を一律 remeasurement 化する変異を殺す |
| `orchestrator/tests/test_floor_submit_receipt.py:43-70,132-244,309-326` | sibling record path、exact key/type、`status="record-only"`、`ruling_id="T-987"`、relaxed binding、protocol path/hash、sorted held IDs、欠落・extra・duplicate・tamper を検査。既存 receipt `_FLOOR_KEYS` の変更も拒否する |
| `orchestrator/tests/test_pegasus_floor_tools.py:420-469,1094-1171` | preflight/record writer 失敗時に driver と launch marker が作られないこと、default は legacy、marker lane は record-bound path、qsub marker は nonce exact、record 作成が driver より前で create-only であることを検査 |
| `orchestrator/tests/test_s8b_floor_campaign.py:3705-3724,3866-3885,6036-6118` | record 無し・status/ruling/binding/held list/path/hash の各変異が build/measure callback より前に落ちること、正例だけが versioned protocol へ進むこと、official は record があっても従来どおり拒否されることを検査 |
| `orchestrator/tests/test_s8b_holdout_admission.py:201-235,359-412,521-530,656-700` | legacy entrypoint の固定 authority を維持しつつ、専用 entrypoint が record-bound versioned HEAD blob だけを受理する正例と、caller path・uncommitted bytes・hash・document・record 改変を claim 作成前に拒否する負例を追加 |
| `orchestrator/tests/test_freeze_verification_hold.py:16-28,81-89` | 既存 hold count/hash/status をそのまま回し、T-987 が ID 追加や `pass` 相当 status を持ち込まないことを固定 |
| `orchestrator/tests/test_s8b_floor_campaign.py:6500-6527,6749-6779,8078-8115` | chain digest、held positive control、official 二回 scan の既存テストを変更せず回し、freeze allowlist の受理集合に変化がないことを検出 |

新規 test file は作らない。したがって新しい自走 harness は不要である。追加先のうち `test_s8b_protocol_builder.py:1621-1625`、`test_floor_submit_receipt.py:329-330`、`test_s8b_holdout_admission.py:1147-1152`、`test_pegasus_floor_tools.py:2559-2564` には既存 harness がある。`test_campaign.py` へ足す関数は既存慣例どおり `tmp_path=None` 形にして同 file の自走 runner を壊さない。

この段ではテスト結果はない。静的調査中の `python3 tools/run_tests.py --help` は pytest 側へ渡り、書込可能 tmp 不在で collection 前に停止したため、テスト実行・緑判定には数えていない。

## 実装順序

1. `test_s8b_protocol_builder.py` に新 resolver の正負テストを置き、generic resolver を変更しない契約を先に固定する。
2. `s8b_floor_campaign.py` に root-only の再測定 resolver を追加する。target pair、versioned path、HEAD blob、worktree bytes をここで確定する。
3. `floor_submit_receipt.py` に独立 record schema/path/strict loader を追加し、既存 receipt schema と分離する。
4. `s8b_floor_campaign.py` に zero-arity record producer と create-only/read-back 検査を追加する。record field はすべて repo・PBS・hold 正本から導出し、caller 値を受けない。
5. `s8b_holdout_admission.py` に専用 recorded-remeasurement entrypoint を追加する。既存固定 legacy entrypoint と `_key_fields()` 以下は変えない。
6. `s8b_floor_campaign._run_campaign_core()` で marker、receipt、record、resolved protocol を照合し、専用 holdout entrypoint へ渡す。record 欠落時の拒否を build/runner より前へ置く。
7. `certified_writer_admission.py` に nonce-bound marker 分岐を追加する。marker 無しのコードパスは byte-level で可能な限り維持する。
8. `submit_floor.sh` と `floor_campaign.sh` を最後に配線し、record 作成成功前には driver を組み立てない。既存 pilot confirmation は独立したまま保つ。
9. targeted tests を必ず `python3 tools/run_tests.py` 経由で実行し、その後 acceptance 全走、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py` を実行する。床値本走や benchmark はこの wave で行わない。
10. spool の worklog/decisions fragment を追加して同じ commit に含める。commit 後に `python3 tools/check_ai_provenance.py` を実行する。

## 危険と反証

| 危険 | 防壁 | 検出する既存/変更後 nodeid |
|---|---|---|
| generic resolver を HEAD pin 優先へ変え、通常の受理集合を広げる | generic resolver は不変、新 resolver は別名・root-only | `orchestrator/tests/test_s8b_protocol_builder.py::test_current_floor_protocol_resolver_selects_exact_index_record`、`::test_current_floor_protocol_resolver_has_only_root_selection_argument`、`::test_current_floor_protocol_resolver_rejects_two_current_contract_matches` |
| marker を付けるだけで record 無しでも進む | wrapper と campaign の二箇所で record 必須。campaign は build/measure callback より前に拒否 | `orchestrator/tests/test_pegasus_floor_tools.py::test_floor_wrapper_preflight_rejection_is_nonmutating_and_starts_no_driver` と新しい missing-record test |
| record が検査通過証明に見える | exact `status="record-only"` と `relaxed_binding` を要求し、`pass`/`verified` を schema に持たせない | `orchestrator/tests/test_freeze_verification_hold.py::test_hold_reason_is_machine_readable_and_release_is_literal` と新 record schema mutation tests |
| holdout correctness authority を caller-selected path へ弱める | path は `(contract_sha256, ccbench_pin)` から再導出し、HEAD 100644 blob、worktree bytes、SHA-256、record を独立照合 | `orchestrator/tests/test_s8b_holdout_admission.py::test_worktree_byte_drift_is_rejected_before_any_cell_claim`、`::test_canonical_authority_to_run_once_proof_chain_e2e` |
| 新 pin が one-shot holdout key に入らず、旧測定と衝突する | `_key_fields()` と claim 生成は変更せず、選択済み versioned document の pin を使う: `orchestrator/campaign/s8b_holdout_admission.py:868-897` | `orchestrator/tests/test_s8b_holdout_admission.py::test_n_pilot_ledger_and_attempt_allowance_are_durable_and_protocol_bound` |
| shell が admission した versioned protocol と別の legacy protocol を実行する | driver path は create-only record からのみ取得し、campaign が再照合 | `orchestrator/tests/test_pegasus_floor_tools.py::test_floor_job_invokes_fixed_pilot_cli_without_bypass` を default/recorded の二ケースへ改訂 |
| official gate や clean digest を意図せず緩める | official 無条件拒否、`_CHAIN_RECORD_PATTERNS`、freeze allowlist を変更しない | `orchestrator/tests/test_s8b_floor_campaign.py::test_main_official_mode_always_refused`、`::test_run_campaign_core_rejects_official_with_zero_side_effects`、`::test_clean_scan_digest_binds_recognized_chain_record_path_and_bytes`、`::test_official_preflight_rejects_digest_shift_between_independent_scans` |
| held 集合や凍結 bytes を変更する | 対象ファイルを編集面から除外 | `orchestrator/tests/test_freeze_verification_hold.py::test_held_check_id_registry_count_digest_and_unknown_rejection`、`orchestrator/tests/test_frozen_artifacts.py::test_frozen_artifacts_match_manifest` |
| 規律 2 を侵食する | anomaly、portable binary、session/result、verdict の各判定には触れず、変更は protocol authority 選択と記録必須化だけに限定 | `orchestrator/tests/test_s8b_floor_campaign.py::test_end_to_end_golden_floor_values_and_tamper_detection`、`::test_portable_built_rejects_missing_admission_receipt` |

最も危険なのは `s8b_holdout_admission._authority()` を単に「任意 path 可」へする実装である。それは規律 2 侵食なので不可。専用 entrypoint、機械導出 path、record 必須、HEAD/worktree/hash の四重束縛が崩れる案は採用しない。

## 総括

P1 は偽であり、標準 pilot の count=2 admission と固定 legacy holdout authority が実在する機械 gate である。  
直接の pin/current HEAD 比較は held または不在だが、それだけでは再封印版を実走できない。  
推奨は freeze chain 追加ではなく、Pegasus submission 配下の create-only attempt record と専用 remeasurement lane である。  
generic resolver、official 拒否、`HELD_CHECK_IDS`、凍結 bytes、correctness/verdict の受理集合は変更しない。  
本回答は静的調査のみで、編集・commit・有効なテスト実行は行っていない。