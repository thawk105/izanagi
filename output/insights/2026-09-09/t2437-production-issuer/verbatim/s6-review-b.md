静的レビューのみ実施した。対象は HEAD `636e943802cbb309694bf23ed3fe7794087438f4`。pytest は実行していない。

## 変異事前登録 11 件の判定

| ID | 判定 | mask・等価・過剰決定 | 予測される node / 再照準 |
|---|---|---|---|
| M1 | 成立 | mask・等価なし。`pipeline.py:2093-2097` だけが local rejected の typed 値を `EvalResult` へ渡す。 | `test_pipeline_verify_result_retention.py::test_local_rejected_repetition_retains_exact_verify_result_and_wal_binding` と `test_reflux_campaign_issuer.py::test_real_run_campaign_issues_rejected_record_and_originless_is_inert` の 2 node。 |
| M2 | 成立 | mask・等価なし。`pipeline.py:1870-1871` を `isinstance` 化または削除すれば直接観測できる。 | `test_pipeline_verify_result_retention.py::test_abort_rejects_non_exact_verify_result`。 |
| M3 | 不成立 | wire dict を `verify_result` に載せる単純変異は `_abort` の exact 型 gate `pipeline.py:1870-1871` に先に落ちる。前 wave と同型の mask。 | 現 node は `test_remote_fanout_abort_does_not_reconstruct_typed_verify_result` だが、TypeError で赤になるだけ。`_admit_verify_fanout_result()` の戻り値を projection 前に直接検査する専用 node へ再照準する。 |
| M4 | 要 exact 化 | 到達可能で等価ではないが、「live ref 化」が path だけか snapshot 書込み削除も含むかで赤集合が変わる。 | `reflux_result_evidence.py:1265-1268` の path だけを live WAL へ変えると、`test_campaign_producer_issues_real_wal_projection_and_resolves_interval` と `test_campaign_producer_snapshot_survives_append_while_live_ref_breaks`。この exact edit を登録すべき。 |
| M5 | 成立 | 2 番目の attempt は `frames[0].byte_start > 0` を明示しており、0 固定は等価でない。 | `test_reflux_result_evidence.py::test_campaign_producer_preserves_nonzero_offset_for_second_attempt`。 |
| M6 | 不成立 | derive と assemble の 2 gate を一変異にしている。現テストは invalid typed result による derive 拒否しか観測せず、assemble/path 検査の後置は SURVIVE しうる。 | M6a: derive を `reflux_result_evidence.py:1355` より後へ移し `test_campaign_producer_refuses_nonexact_verify_result_before_writes`。M6b: assemble/path 検査を後置し、不正 `expected_record_path` でも file 0 件を検査する新 node。 |
| M7 | 不成立 | `reflux_result_evidence.py:1210-1211` を削るだけでは、`1298-1299` の exact-object gate が `None` を拒否する。KILLED でも receipt 必須性ではなく例外型差への帰属になる。 | 同じ node `test_campaign_producer_refuses_absent_execution_receipt_before_writes` を使い、変異を「`None` を自己申告 dict に置換」に exact 化する。 |
| M8 | 不成立 | `loop.py:342-343` の return 削除は `context.origin_capability` の AttributeError で先に落ち、file 不生成を証明しない。中心 node も正例・collision と過剰結合している。 | originless 専用 node に分離し、非揮発 WAL の順序・件数・payload key と file 集合を比較する。変異は context-none 分岐で content marker を 1 件置いて return する形へ再照準する。 |
| M9 | 不成立かつ実装反例あり | 新規 identity-error は現 node が見るが、既存 terminal の 2 skip call site `loop.py:664-674,713-721` は未観測。さらに accepted terminal は `derive_physical_result()` が typed 値なしで受理する。 | M9a: 現 `test_identity_error_terminal_is_explicitly_refused`。M9b: identity resolution failure + accepted stock terminal。M9c:通常の accepted terminal recovery skip。3 変異・3 node に分割する。 |
| M10 | 不成立 | 2 述語が 1 ID。`len(genomes)` 削除後は receipt gate、balanced 削除後は既存 balanced gate `loop.py:447-462` が後で落とすため mask される。 | `_validate_result_evidence_context()` を直接呼ぶ M10a multiple-genome、M10b balanced の 2 node に分割する。 |
| M11 | 成立条件あり | `loop.py:356-365` の issuer call だけを catch して return する exact 変異なら単一理由。issuance は evaluate の catch 外 `loop.py:839-847` にある。 | `test_reflux_campaign_issuer.py::test_real_run_campaign_issues_rejected_record_and_originless_is_inert`。同 node 内では最初の再発行 collision `:509-518` が先に赤になる。 |

## 所見

### 既存 accepted terminal の skip が発行拒否にならない

重大度: must-fix

根拠: `orchestrator/campaign/loop.py:309-327,655-674,712-721`、`orchestrator/campaign/reflux_result_evidence.py:685-703`。

成果物影響: 再開時に、過去 attempt の WAL と現在 run の execution receipt を混ぜた `physical_result.outcome="accepted"` record と参照が新規発行され、missing record だった集合と resolver の受理集合が変わる。

反証可能な主張: accepted terminal を持つ campaign を同じ context で再実行すると、`verify_result=None` でも accepted 分岐が通り、`ResultEvidenceIssuanceRefused` ではなく record 発行へ到達する。

最小修正: context ありの両 skip 分岐では generic issuer を呼ばず、無条件に明示拒否する。対応後は `_result_evidence_attempt_id()` を削除できる。accepted の通常評価だけは現行どおり typed 値不要でよい。

### 中心正例が production receipt 条件を迂回している

重大度: blocker

根拠:

- テスト契約は `linux-baremetal` で `attestation_mode="none"`: `env_contract.py:292-300`、`test_campaign.py:104-118`。
- 実 `_authorize_measurement()` は required の場合だけ receipt を返す: `loop.py:184-187`。
- 正例はその結果を wrapper で `execution_guard.build_receipt()` に置換する: `test_reflux_campaign_issuer.py:311-324,433-439`。
- 一方、docstring は「trace creation だけ stub」と主張する: 同 `:433-435`。
- public issuer は receipt の発行元や schema を検査せず、dict と `contract_sha256` だけを見る: `reflux_result_evidence.py:1298-1307`。実際、任意の fixture schema が使われている: `test_reflux_result_evidence.py:354-359`。

成果物影響: 実経路では発行拒否になる site でも、テストでは execution-provenance と record が作られるため、「fixture-origin scope で発火可能」という成果物の値と参照が偽陽性になる。

反証可能な主張: `_install_fixture_receipt_authorization()` を外すと、同じ中心正例は `execution_receipt=None` のため `reflux_result_evidence.py:1210-1211` で拒否される。

最小修正: 中心正例は wrapper なしの required-attestation 契約と実 `_authorize_measurement()` の non-None 結果で走らせる。加えて public issuer が任意 dict を authenticated receipt と扱わないよう、既存 execution-guard の発行・検証面へ束縛する。実 receipt を用意できないなら、この正例を中心完了証明として数えない。

B5 の 3 stub 判定:

- `trace_runner`: 裁定どおり。`pipeline._execute_verification_repetition()` 本体を呼び、trace file の生成だけを差し替える。実 verifier は残る (`test_reflux_campaign_issuer.py:327-353`)。
- `_has_git_ancestor`: tmp root を選択的に許す環境 seam。issuer・verifier・resolver を迂回しない (`:71-81`)。ただし「stub は trace だけ」という字面には含まれていない。
- receipt wrapper: 機構を通らない緑を作る。実 authorization の `None` を non-None に置換し、receipt 不在拒否 gate を迂回する。

### 変異台帳へ誤った KILLED を記録できる

重大度: must-fix

根拠: M3 の exact 型 gate `pipeline.py:1870-1871`、M7 の二重 receipt gate `reflux_result_evidence.py:1210-1211,1298-1303`、M8 の None dereference `loop.py:342-347`、M10 の後段 balanced gate `loop.py:447-462`。

成果物影響: mutation 台帳が狙った gate ではない赤を KILLED と記録し、発行 record の値・参照を変える回帰が再導入されても検出済みと誤認される。

反証可能な主張: 上記 M を素朴に適用すると、期待する artifact 差へ到達する前に別の例外または gate で赤になる。

最小修正: 上表の再照準どおり、M3/M6/M9/M10 を分割し、M7/M8 を exact な artifact-changing mutant にする。

### 受入所要台帳用の実測値が不足

重大度: must-fix

根拠: `acceptance_duration_ledger.json:11827-11851` には既存 `test_reflux_result_evidence.py` node だけがあり、新規 19 node は 0 件。提示された実測も「7 passed」と aggregate のみで per-node duration がない。

成果物影響: 受入所要台帳の参照集合が 19 node 欠け、main 取り込み後の add-only 登録と acceptance shard 証跡を確定できない。certified 選択値自体はまだ変わらないが、受入台帳が不完全になる。

反証可能な主張: 台帳を nodeid で検索しても、下記 19 件は存在しない。

最小修正: 親の実走 JUnit から各 node の実測秒を回収し、main 取り込み後に 19 件を一括 add-only する。値はこのレビューでは作らない。

## 既存 consumer への回帰

反例なし。

- `EvalResult` の 2 field は末尾既定値付き (`pipeline.py:301-313`)。production constructor は keyword 使用で、既存 field readerも `p2_2.py:384-392`、`backoff_sweep.py:420-431`、`paper_story_a2_certification.py:3625-3635` のように必要 field だけを読む。
- repository-wide の静的検索で、`EvalResult` または `CampaignSummary.results` 全体を `asdict`、`vars`、`__dict__`、JSON 化する production 経路は見つからない。
- `run_campaign()` の追加引数は既存 `*` より後の keyword-only、末尾、既定 `None` (`loop.py:368-401`)。既存 production caller は指定していない。
- `reflux_result_evidence.py` の `__all__` は追加だけ (`:44-63`)。formal consumer は旧名を named import しており (`reflux_formal_consumer.py:68-74`)、exact `__all__` consumer や star import は見つからない。
- 親が直した eval-exception WAL abort は `loop.py:807-833` で無条件に残り、正例も 2 abort を要求する (`test_reflux_campaign_issuer.py:778-793`)。
- capability の欠落・空・非 str 拒否は `loop.py:346-355`、3 形のテストは `test_reflux_campaign_issuer.py:796-823`。直りきっている。

既存テスト期待値の弱体化も反例なし。既存 test の assert 書換えはなく、`test_reflux_result_evidence.py:1081` 以降への追加と新規 2 file だけである。

新規 test file の自走登録は成立する。

- `test_pipeline_verify_result_retention.py:194-195`
- `test_reflux_campaign_issuer.py:835-836`

どちらも `pytest.main()` を実行する `__main__` があり、README の自走側条件 `orchestrator/tests/README.md:105-126` を満たす。pytest 専用 allowlist へ追加しないのが正しい。既存 `test_reflux_result_evidence.py` は allowlist 済み (`README.md:151`)。

台帳登録対象は次の 19 node。実測所要は提示資料にない。

- `test_pipeline_verify_result_retention.py` の 5 node: `test_local_rejected_repetition_retains_exact_verify_result_and_wal_binding`、`test_remote_fanout_abort_does_not_reconstruct_typed_verify_result`、`test_abort_rejects_non_exact_verify_result`、`test_accepted_evaluation_does_not_retain_one_pass_verify_result`、`test_prebuild_abort_retains_generated_build_attempt_id`
- `test_reflux_campaign_issuer.py` の 7 node: `test_real_run_campaign_issues_rejected_record_and_originless_is_inert`、`test_context_shape_rejects_multiple_genomes_and_balanced_before_writes`、`test_context_exact_type_and_root_binding_precede_campaign_writes`、`test_identity_error_terminal_is_explicitly_refused`、`test_originless_eval_exception_after_terminal_preserves_legacy_abort`、`test_issuance_rejects_invalid_origin_capability_campaign_id`、`test_signature_keeps_context_keyword_only_after_verify_fanout_hosts`
- `test_reflux_result_evidence.py` の 7 node: `test_campaign_producer_issues_real_wal_projection_and_resolves_interval`、`test_campaign_producer_preserves_nonzero_offset_for_second_attempt`、`test_campaign_producer_refuses_absent_execution_receipt_before_writes`、`test_campaign_producer_refuses_interleaved_attempt_before_writes`、`test_campaign_producer_refuses_nonexact_verify_result_before_writes`、`test_campaign_producer_treats_create_only_collision_as_failure`、`test_campaign_producer_snapshot_survives_append_while_live_ref_breaks`

## 無駄 (削るべき箇所)

- `loop.py:309-327` の `_result_evidence_attempt_id()` は accepted skip の誤発行を可能にする互換層であり、skip を明示拒否へ直した後は用途がなくなるため削除すべき。
- `test_reflux_campaign_issuer.py:311-324` の receipt wrapper は中心正例を偽陽性にするため削除・置換すべき。
- `test_reflux_campaign_issuer.py:433-576` は正例、再発行 collision、originless、record collision を 1 node に詰めており、変異の落下理由を曖昧にする。少なくとも M8 と M11 の対象部分は専用 node へ分離すべき。
- それ以外の production gate、content-addressed writer、root containment、trigger binding 導出について削除すべき無駄の反例なし。

## 段 4 裁定との食い違い

- §5 の「identity-error / 既存 terminal skip は明示拒否」に対し、accepted terminal skip は発行可能 (`loop.py:655-674,712-721` と `reflux_result_evidence.py:685-703`)。
- §5 の「trace 生成だけが唯一の stub」に対し、中心正例は receipt wrapper を必要とする (`test_reflux_campaign_issuer.py:311-324,433-439`)。
- §5 の「authenticated execution receipt」に対し、public issuer は任意 dict の発行元・schema を検査しない (`reflux_result_evidence.py:1298-1307`)。
- S1〜S3 の配置、source prefix snapshot、write 前 derive、issue 例外伝播、S4 非実装については反例なし。
- 親が段 5 で直した 2 件は閉じている。

## 裁定パッケージ候補 (scope 外の real な所見)

実装提案はしない。

- S4 production caller は依然不在。fixture real build は `p3_autonomous_workload_trial.py:5408-5411`、no-build は `p3_s4_loop_trigger_gating.py:788-794`、registered trial は `trial_registry.py:782-783` で止まる。
- completeness は `origin_campaign_run` を search key 集合へ受理せず (`autonomous_trial_completeness.py:830-844`)、rejected-only run は `built_and_benched >= 1` を満たさない (`:4130-4136`)。
- Layer3 の一次参照は WAL と whiteboard のみ (`layer3_report.py:234-266`)。result-evidence record は材料レポート参照へ入らない。
- record 最終書込み失敗時、source・projection・provenance は既に書かれている (`reflux_result_evidence.py:1355-1373`)。tombstone 自動接続はない。
- `attestation_mode=none` site の receipt 契約は未解決 (`env_contract.py:292-300`、`loop.py:184-187`)。

これらを放置すると、certified 選択自体は D338 により増えないが、report は result-evidence を参照せず、ledger は missing record または FC01 以降の拒否に留まる。

## 総括

blocker 1 件、must-fix 3 件。中心正例は real verifier・derive・assemble・issuer・resolver を通す一方、receipt を test wrapper で注入しているため、裁定された production 発火可能性を証明していない。さらに accepted recovery skip は実際に誤発行可能である。

既存 consumer 回帰、既存期待値の弱体化、自走 harness の欠落には反例なし。M3/M6/M7/M8/M9/M10 は再照準が必要で、新規 19 node の実測所要も受入前に回収が必要。