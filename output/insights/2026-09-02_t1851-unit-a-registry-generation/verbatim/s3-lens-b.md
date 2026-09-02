## 規模の再計数

- [実測] `wc -l` の再実行結果は `attempt_registry_core.py=1,974`、`s8b_attempt_profile.py=467`、`s8b_attempt_registry.py=2,071`、合計 `4,512` 行で、プランのファイル総行数は正しい。一方、プラン表 `s2-plan.md:9-14` の変更対象区間を重複排除すると core 406、profile 313、adapter 1,433、合計 `2,152` 行であり、`:16` の「変更対象 block 約1,900行」より252行多い。実装差分が無い現段階で `1,250〜1,500 changed LOC` は実測不能なのに、`:483` はこれを `[実測]` と再掲している。判定: real。成果物影響: review 面を約13%過小に見せ、wave 容量判断を楽観化する。

- [実測] `ast.parse` で全 `test_*` と `pytest.mark.parametrize` の値列を展開した結果は profile `50関数/78 node`、adapter `35/59`、equivalence `9/16`、計 `94関数/153 node` で、`s2-plan.md:5` の再計数は正しい。親 brief `:95-96` の `35/50/9 node` は node でなく関数数である。判定: refuted。成果物影響: プランの153 node自体には数え落としがない。

- [実測] ただし153は「3ファイルを全選択した数」で、変更 symbol 参照数ではない。AST の局所 helper 参照閉包では、profile は78 node中75 node、adapter は59中57 node、equivalence は16中2 nodeが `make_s8b_domain_profile`、`load_attempt_registry`、`record_attempt_terminal`、`DomainProfile`、`TransitionPolicy`、layout等を直接参照する。残る19 nodeは source/API/transitive検査である。除外名で列挙すると、profile の直接参照外は `test_genesis_rejects_binding_codec_overlap_with_manifest_keys`、`test_trial_registry_six_facades_have_no_top_level_rebinding`、`test_facade_rebinding_guard_rejects_c03_blind_synthetic_source`、adapter は `test_floor_campaign_does_not_import_adapter_and_guard_has_positive_control`、`test_repetition_derivation_guard_rejects_all_known_mapping_forms`、equivalence の直接参照は `test_reference_core_and_facade_event_and_receipt_bytes_are_identical` と `test_unknown_event_rejection_reason_is_identical` の2 nodeである。判定: real。成果物影響: node数は正しいが「変更 symbol の直接回帰」という帰属は成立しない。

- [実測] consumer の参照閉包はさらに19 nodeある。内訳は launcher `test_real_adapter_creates_and_exactly_reuses_complete_genesis`、campaign `test_resume_runner_produces_one_retry_from_admission_selected_recovery`、scheduler `test_registry_binding_is_honestly_inert_without_a_start_schema_field`、reflux meta `test_consumer_source_has_no_nonaborted_construction_or_success_variant`、holdout の15 nodeである。holdout の実名は `test_verified_registry_recovery_authorizes_exactly_one_retry_ordinal`、`test_registry_recovery_of_retry_attempt_selects_that_attempt_as_trigger`、`test_registry_recovery_authority_is_empty_and_fail_closed`、`test_registry_recovery_requires_standalone_receipt`、`test_registry_recovery_requires_identical_standalone_receipt_bytes`、`test_registry_recovery_counts_corrupt_extra_candidate_before_replay`、`test_verified_registry_recovery_rejects_non_next_or_multiple_retry_ordinals[2]`、`test_verified_registry_recovery_rejects_nonlatest_retry_start`、`test_inspection_rejects_registry_recovery_nonprefix_or_reused_trigger[2]`、`test_registry_recovery_without_consumed_trigger_marker_is_rejected`、`test_unverified_registry_recovery_row_is_rejected`、`test_failed_session_and_registry_recovery_evidence_are_mutually_exclusive`、`test_registry_recovery_from_other_round_cannot_open_retry` (`test_s8b_holdout_admission.py:2943-3436`)。従って静的回帰閉包は153ではなく `153+19=172 node` である。判定: real。成果物影響: consumer焦点走の選択と所要見積りが19 node不足する。

- [実測] 全Aについてはプラン自身が1 wave案を反証したが、分割後のA1'には production LOCもtest node数も再見積りがない (`s2-plan.md:32-45,262`)。さらに拒否表 `:395-413` は、bool/負数/非int、2 ordinal×2不正、projection各field、非JSON3種、generation3種など、単一理由 nodeへ分けるだけで少なくとも25負例を要する。判定: real / blocker。成果物影響: A全体は1 waveに収まらず、A1'も「実装子1〜2本、fix 3巡以内」に収まる根拠が未成立である。

## 変異の帰属

- [実測] `rg -n '変異|DW-M|M[0-9]' s2-plan.md` は0件だった。親 brief `:53-55` が必須とする事前登録 matrix は、A1'へ分割した後のプランに存在しない。前waveのM1〜M9はB2/C/D2を含む旧scope用であり代用できない。判定: real / blocker。成果物影響: 実装後のKILLED/SURVIVEDをどの防壁の証拠に数えるか決められない。

- [実測] sealed projection の「1 field mismatch」負例は、そのままでは単一理由にならない。現coreは status閉集合とdigest形を `attempt_registry_core.py:891-930`、null matrixを `:933-983`、classification reason等値を `:1264-1289` で先に検査する。terminalのstatus/reasonを直接変える入力は、新しい `terminal_row_validator` より先に既存gateで落ちうる。判定: real。成果物影響: projection testが新しいsealed再導出防壁を測らず、既存防壁の再試験になる。

- [実測] generation symlinkにもmaskがある。新enumeratorのsymlink拒否を片側だけ消しても、既存 `_read_regular_bytes()` が親componentのsymlinkとno-follow regular fileを再検査する (`s8b_attempt_registry.py:509-561`)。またlive lock検査は `s8b_holdout_admission.py:5172` と、その先の `_current_floor_attempt_consumption_identity_locked()` 内 `:5009` の二重呼出しで、B1のM9/M10と同型である。判定: real。成果物影響: 片側SURVIVEDを「防壁が効かない」と解釈すると誤るため、direct helper変異か両層同時変異が必要になる。

- [実測] 到達不能として事前登録すべき確定箇所は `_current_floor_attempt_consumption_identity_locked()` の schema再確認 `s8b_holdout_admission.py:5030-5033` である。入力は直前の `_floor_attempt_document_for_state()` がcurrent schemaで生成し、legacy tokenはさらに前の `_cell_state()` で拒否される。A1'新設guardには現物上の到達不能はまだない。一方、A2'の「registry attempt_ordinal=0だけcapability使用」guardを、attempt_ordinal=1のslotがgenesisに存在しない状態でslot lookup後へ置けば同様に到達不能になる。判定: real。成果物影響: 前者はSURVIVED期待、後者は配置確定後にSURVIVEDか通常負例かを決める必要があり、不到達を偽装するtestは作らない。

- [推測] A1'用の最小事前登録案は、(M01) core helper直接でseed不正と10/11境界、(M02) 第2世代local count=0のままseed渡しだけを消して第11 startをKILL、(M03) `serialize_session_line` の空白/newlineをexact bytesでKILL、(M04) `derive_s8b_terminal_projection` を生のsealed事実ごとにcomponent KILL、(M05) chainを正しく再計算しsealed objectだけを変えてterminal validatorをKILL、(M06) enumerator直接testでhex symlink/非directory/欠落をKILL、(M07) core-validなgenesisと物理directory名だけを違えてprofile resolverをKILL、とする。A2'ではB1の「lock片側2件はSURVIVED、両層同時はKILLED」とcurrent-schema guardのSURVIVEDをそのまま再登録する。判定: real。成果物影響: 各結果を予算、serializer、projection、storage、profile dispatch、lockの単独防壁へ帰属できる。

## 効く層の閉包

- [実測] 効く順序は `A1' core/profile/read-only基盤 → A2' v2 writer/claim → B2 inspector/coverage → D1 v5 proof型 → C launcher配線・材料result発行 → D2 verifier/candidate/ratified/earlier選択` である。現在 `launch_floor_attempt()` のproduction callerは0件で、`rg '\\blaunch_floor_attempt\\s*\\('` は定義とtest 1件だけだった。resultはまだv4 (`s8b_floor_contract.py:34`) で、campaignは台帳proofなしに `assemble_result()` を呼ぶ (`s8b_floor_campaign.py:7789-7795`)。判定: real。成果物影響: A単体ではcertified選択、材料レポート、proof chainのどれにも台帳束縛は発火しない。

- [実測] A1'は既存v1 APIを維持しv2 mutationを開かないと明記され (`s2-plan.md:38-45`)、A2'でもlauncherのproduction dependencyがadapterを指すだけで (`s8b_floor_attempt_launcher.py:158-160`)、Cがcampaignからlauncherを呼ぶまで台帳行は生えない。B2/D1/C/D2がscope外なのにA単体で「効く」とする記述は見つからない。判定: refuted。成果物影響: プランはcheckpointの非実効性を正直に記述している。

- [実測] certified選択への実効点はD2のcandidate、ratified reverify、`_official_earlier_floor_results()` (`s8b_holdout_freeze.py:1813-1950`) である。材料レポートへの実効点はCのresult/result.md生成 (`s8b_floor_campaign.py:7789-7844`) とD1のv5契約、proof chainはB2 captureとD2 live/prefix verificationである。最終8c公式選択表はD1342により台帳の生存再確認をしないため、意図どおりこの閉包外である。判定: real。成果物影響: featureとして必要な全層はA外だが、6段全体のscopeには入っている。

- [実測] D1341はこの答えを変えない。A1'/A2'/B2/D1/C/D2をlandしないcheckpointとして保持するため部分成果は利用者へ発効しないが、最終landに必要な層を減らす裁定ではない (`decisions-verbatim.md:76-95`, `s2-plan.md:479`)。判定: refuted。成果物影響: partial checkpointを「実効済み」と数えない限り、writer-onlyまたはverifier-only保証は公開されない。

- [実測] `attempt_registry_core.py` は8cと共有され、`trial_registry.py:3363` が変更対象の `record_attempt_terminal` を使うため、scope外8cへの回帰blast radiusは存在する。一方、親がproduction consumerとした3つのB4 moduleは `canonical_json_bytes` または `chained_event_row` しか参照せず (`p3_b4_analysis_ledgers.py:26`, `p3_b4_prerun_issuer.py:36`, `p3_b4_raw_record_producer.py:36`)、今回変更する防壁のconsumerではない。判定: nit。成果物影響: 8c equivalence検査は必要だが、B4を防壁帰属の根拠に数えると回帰集合を水増しする。

## 親 brief 自体の所見

- [実測] 「実測した前提」1のDW-O09は、`FROZEN_MANIFEST`にliteralが無いこととtracked `registry.jsonl` 0件までは `rg` / `git ls-files` で再現した。しかしそこから「pinはpath側にもkey側にも無い」とする意味上の閉包は検索語だけでは測れていない。判定: nit。成果物影響: 現物反例は無いが、path生成や別名digest pinを除外した証拠にはならない。

- [実測] 前提2のDW-O10は「対象producer」が未定義で帰属が成立しない。adapterはregistry、claim、receipt、stagingを書く (`s8b_attempt_registry.py:686-763,984-1048,1401-1437`) がconsumption markerはadmissionが書く (`s8b_holdout_admission.py:4349-4392`)。floor campaign全体をproducerと呼ぶならresult/result.mdも書く (`s8b_floor_campaign.py:7789-7844`)。判定: real。成果物影響: writer mutationを誤ったmoduleへ置き、DW-O10の書込み閉包を偽る。

- [実測] 前提3のlive共有rootは再現した。registry 193行、catalog 96行、freeze directory 1本、mtimeはいずれも2026-08-27 19:53:23だった。判定: refuted。成果物影響: 合成2段v1をfixtureとして扱う前提は維持できる。

- [実測] 前提4のt524差分はproduction `attempt_registry_core.py +29/-0`だけではない。`git diff --numstat HEAD...worktree-dev-wave-t524-slot-experiment-unit` はさらに `test_attempt_registry_core_equivalence.py +16/-2` と `test_attempt_registry_core_s8b_profile.py +5/-3` を示す。判定: real。成果物影響: Aの回帰test 2ファイルもrebase対象なので、親の重なり量は24追加・5削除を数え落としている。

- [実測] ただしt524のproduction追加は `_parse_genesis()` 内の `p3-8c-attempt-registry/v3` 専用29行で、Aのseeded replay、DomainProfile field、terminal validatorとはschemaも主hunkも分かれる。`git merge-tree $(git merge-base ...) HEAD worktree-dev-wave-t524-slot-experiment-unit` はcoreを自動mergeし、conflict markerを出さなかった。判定: refuted。成果物影響: 現時点で意味上・text上の衝突はなく、land順による行番号ずれと回帰再確認だけが必要である。

- [実測] 前提5のsubmodule記述は現物と食い違う。top-level `third_party/shirakami` 自体が存在せず、実在する `external/ccbench/third_party/shirakami/third_party/googletest` は `f8d7d77c...` を返し、`git submodule status --recursive` はrc=0だった。googletestの`.git` mtime 19:44はbrief mtime 19:49より前である。判定: real。成果物影響: 開始gateの説明は再現不能だが、本A成果物の設計には影響しない。

- [実測] 前提6のB1 spoolはworklog 1件、decision 1件が `docs/spool/` に実在する。判定: refuted。成果物影響: 最終foldに必要なB1記録は失われていない。

- [実測] P1-aの「単位A単体は未測定」は誤りで、前wave plan v2 `refs/s2-plan-v2.md:310-316` にA単体 `600-850 changed LOC / 35-55 node` が明記されている。現planの再見積り `1,250-1,500 / 新設55-70` と大きく違うが、「見積りが存在しない」わけではない。判定: real。成果物影響: 見積り差を誤差分析せず、未測定扱いで新しい数字へ置換している。

- [実測] P1-cは現物と両立しない。live 2段v1 genesisの `recovery_policy_sha256` は `c7c753a9...`、現HEADからimportしたscheduler値は `79c8098c...` で、genesisにはauthority idや方針原文がない。従ってtrusted profileを再構成して「両方読む」ことはできない。なおplan `:433` の現行digest `6ac1b69...` も古いが、不一致という結論は変わらない。判定: real / blocker。成果物影響: 合成2段v1を受理するなら新trust rootの裁定が要り、無ければplanどおりfail-closedにする必要がある。

- [実測] P1-bは `_locked()` の非再入性 (`s8b_holdout_admission.py:699-726`)、prelock hook位置 (`s8b_attempt_registry.py:984-1004`)、6 caller (`:1183,1439,1556,1666,1716,1756`) と整合する。P1-dはcatalog literalのtracked production consumer 0件、P1-eは現host `pegasus02` と整合する。判定: refuted。成果物影響: この3裁定を差し戻す現物理由はない。

- [実測] 親の「A4理由語彙は受理集合を狭める」(`brief.md:44-45`) はraw coreでは逆である。現空集合から4語へ増やすと `_assert_null_matrix()` `attempt_registry_core.py:952-964` が以前拒否したretryable terminalを受理する。planはv2 sealed validatorとの同時active化で全体を閉じると訂正済み (`s2-plan.md:384-390`)。判定: real。成果物影響: 理由集合だけを先にactive化すると防壁を緩めるが、A1'がv2 mutationを開かない限り発火しない。

- [実測] アンカー表12件の開始行に数値ずれはない。例外は意味上の2件で、`core profile 構築 :654-725` は実際には渡されたprofileでgenesisをparseする `_parse_genesis()` `:654-738` でありprofile構築ではない。またB1 capability `:303-370,5082-5127` はclass実体 `:303-368`、validator `:5082-5103`、lock guard `:5115-5137` に加え、肝心の使用時再検証とaction実行 `:5140-5227` を落としている。判定: nit。成果物影響: P1-cのprofile resolver所有層と、P1-bのlock/action検査位置を誤認しやすい。

## 総括

- [実測] blockerは3件: A1'規模未計数、A1'変異事前登録欠落、合成2段v1のtrust profile再構成不能である。
- [実測] 最も重いのは、A全体を分割した後のA1'についてLOC/nodeを再計数せず、1 waveへ載せた点である。
- [実測] 現物の回帰閉包は直接153 nodeにconsumer 19 nodeを加えた172 nodeである。
- [実測] t524はAのtest 2ファイルにも重なるが、現在のmerge-treeではcoreを含め衝突しない。
- [実測] A単体は最終成果物へ効かず、B2/D1/C/D2まで同時landして初めて材料reportとproof chainへ効く。
- [実測] pytest、collection、mutation本走は実施しておらず、緑は主張しない。