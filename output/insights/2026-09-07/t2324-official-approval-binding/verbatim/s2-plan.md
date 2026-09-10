## 変更計画 (file:line 粒度)

- `orchestrator/campaign/s8b_floor_campaign.py:42-45,465-475`

  無条件拒否という説明を、明示承認を要求する gate の説明へ更新する。関数骨格は次とする。

  ```python
  def _assert_official_permitted(
      mode: str,
      confirm_official_floor_run: bool,
  ) -> None:
      if mode == "official" and confirm_official_floor_run is not True:
          raise FloorCampaignError(
              "official mode は明示承認がないため core で拒否する "
              "(--confirm-official-floor-run が必要)"
          )
  ```

  `is not True` により、API 直接呼出しの `1` や truthy object は承認と扱わない。pilot では値を権限として使わない。

- `orchestrator/campaign/s8b_floor_campaign.py:5163-5168`

  「production official は不変に拒否」「dormant 結線」という旧コメントを、CLI・public wrapper・private core の各入口が同じ明示承認を独立に要求する説明へ更新する。

- `orchestrator/campaign/s8b_floor_campaign.py:7174-7226`

  public signature に keyword-only の `confirm_official_floor_run: bool = False` を追加する。

  ```python
  def run_campaign(
      ...,
      protocol_path: Path | str | None = None,
      confirm_official_floor_run: bool = False,
  ) -> dict:
  ```

  `:7185-7196` の `_nondefault_campaign_seams(...)` にはこの値を渡さない。既存の callable/non-default seam 拒否後、`:7207-7208` を次へ変更する。

  ```python
  if mode == "official":
      _assert_official_permitted(mode, confirm_official_floor_run)
  ```

  `_run_campaign_core(...)` へは独立 keyword として渡す。

- `orchestrator/campaign/s8b_floor_campaign.py:7229-7304`

  private core にも `confirm_official_floor_run: bool = False` を追加するが、`_nondefault_campaign_seams` へは渡さない。

  現状 `:7256-7260` の `floor_job_checkpoint.take_checkpoint_environment(os.environ)` は `os.environ.pop` を行う副作用であり、現在の gate `:7304` より先に動いている。次の順へ組み替える。

  1. `_validate_mode`
  2. `_nondefault_campaign_seams`
  3. `eligible_for_refreeze = _derive_refreeze_eligibility(...)` (`:7277-7279`)
  4. 既存の official seam/materializer 拒否 (`:7292-7299`)
  5. `_assert_official_permitted(mode, confirm_official_floor_run)`
  6. `take_checkpoint_environment(os.environ)` と resume 時の無効化
  7. materializer の固定、freeze/protocol 検証、run directory、build、claim、runner

  これで `_derive_refreeze_eligibility` は gate より前のまま、環境変数消費を含む全副作用は gate より後になる。build は `:7627` / `:7695`、cell claim は `:7879`、`runner.run()` は `:7926` なので、いずれも gate 後のままになる。

- `orchestrator/campaign/s8b_floor_campaign.py:8393-8406`

  `_parser()` に次を追加する。

  ```python
  parser.add_argument(
      "--confirm-official-floor-run",
      action="store_true",
      help="official floor campaign の明示承認",
  )
  ```

  `--confirm-user-freeze` (`:8435`) とは別 parser・別目的であり変更しない。

- `orchestrator/campaign/s8b_floor_campaign.py:8599-8630`

  CLI 拒否を次へ変更する。

  ```python
  if (
      args.mode == "official"
      and args.confirm_official_floor_run is not True
  ):
      print(json.dumps({
          "status": "refused",
          "reason": (
              "official mode は --confirm-official-floor-run による "
              "明示承認がないため拒否する"
          ),
      }, ensure_ascii=False))
      return 2
  ```

  `§8 未裁定`、`pilot のみ実行可` は削除する。`:8625-8630` の `run_campaign` 呼出しには `confirm_official_floor_run=args.confirm_official_floor_run` を渡す。CLI 拒否を通らない API 直接呼出しでも public/core gate が残る。

- `orchestrator/campaign/s8b_holdout_freeze.py:932-955`

  挙動は変えず、理由だけを現行責務へ直す。

  - `:933` docstring: 「承認束縛未裁定」ではなく、「世代別承認を検証しない v1 経路で世代 schema document を拒否する」。
  - `:938-941` message の要旨:

    ```python
    "世代 document は v1 verify_document 経路では発効しない: "
    f"世代 schema field {present} を検出したが、"
    "この経路は世代別承認束縛を検証しない (fail-closed)"
    ```

  - `:944-955` `_verify_source` docstring: v2 の旧世代 blob 照合は `s8b_ratified_freeze.load_ratified_freeze` 側の責務であり、v1 active freeze は引き続き worktree bytes 完全一致だけを受理する、と記す。

  `s8b_ratified_freeze.py:1-12,1418` に世代別 approval/active chain の実 authority が既にあるため、新しい経路や信頼根は作らない。

- `tools/pegasus/submit_floor.sh:7-11,28-35,36-70`

  usage と引数 parser に zero-arity の `--confirm-official-floor-run` を追加する。

  ```bash
  CONFIRM_OFFICIAL_FLOOR_RUN=0

  --confirm-official-floor-run)
    CONFIRM_OFFICIAL_FLOOR_RUN=1
    shift
    ;;
  ```

  引数を要求済みにしてはならない。未指定 submission も作れるが、承認 env は export されず、driver の CLI/core gate が拒否する。

- `tools/pegasus/submit_floor.sh:299-307,621-624`

  既存 `$NONCE` を再利用し、新しい nonce・receipt field は作らない。

  ```bash
  export_spec="IZANAGI_SUBMISSION_NONCE=$NONCE"
  if [[ "$CONFIRM_OFFICIAL_FLOOR_RUN" -eq 1 ]]; then
    approval_value=$NONCE
    [[ "$approval_value" != *','* && "$approval_value" != *$'\n'* ]] || {
      echo "official approval value contains qsub -v delimiter" >&2
      exit 2
    }
    export_spec+=",IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=$approval_value"
  fi
  ```

  ambient に同名 env が存在するだけでは追加しない。

- `tools/pegasus/floor_campaign.sh:544-552`

  `CURRENT_STAGE=submit-binding` と既存 submission nonce 検査の直後、receipt 待機・copy より前に次を置く。

  ```bash
  OFFICIAL_APPROVAL_BOUND=0
  if [[ ${IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN+x} == x ]]; then
    if [[ -z "$IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN" \
        || "$IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN" != "$IZANAGI_SUBMISSION_NONCE" ]]; then
      write_failure 2 submit_binding \
        "official floor approval nonce must exactly match IZANAGI_SUBMISSION_NONCE"
      exit 2
    fi
    OFFICIAL_APPROVAL_BOUND=1
  fi
  export -n IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN 2>/dev/null || :
  ```

  `${VAR+x}` で未設定と空文字を区別する。設定済み空文字は不一致として `write_failure 2 submit_binding`。`export -n` により Python driver は raw env を継承せず、検証済みの local boolean から CLI flag だけを受け取る。

  この位置は receipt copy/source identity、reservation、gflags/glog build、driver より前である。拒否監査用の既存 attempt/failure/checkpoint 以外の campaign 副作用は起こさない。

- `tools/pegasus/floor_campaign.sh:1200-1207`

  固定 argv を official に変更し、条件成立時だけ末尾へ 1 個 append する。

  ```bash
  driver_argv=(
    "$PY" -I -B "$REPO_ROOT/orchestrator/campaign/s8b_floor_campaign.py"
    --mode official
    --protocol "$REPO_ROOT/$PROTOCOL_PATH"
  )
  if [[ "$OFFICIAL_APPROVAL_BOUND" -eq 1 ]]; then
    driver_argv+=(--confirm-official-floor-run)
  fi
  ```

  mode 用 env・argv・`eval` は追加しない。

- `tools/pegasus/floor_campaign.sh:1325-1330,1356-1361,1373-1378`

  文言と job-result を official に揃える。

  - `"official floor result is missing finite W-2 floor metrics"`
  - `"mode": "official"`
  - `"official floor driver returned nonzero"`

  schema version、key 集合、nonce、source/script hash は変更しない。

- 運用文書

  - `tools/pegasus/README.md:217-257`: command を `submit_floor.sh --confirm-official-floor-run` にし、固定 official、nonce-bound env、未指定時の拒否、人間性を保証しない範囲を記す。
  - `docs/phase3-8b-restart-runbook.md:49,165-197,229-241`: 固定 pilot・official 空集合という旧運用を、D926 の固定 official + 明示承認へ置換する。pilot W-2 は完了済みの歴史として分離する。
  - `docs/pegasus-runbook.md:1641-1645` 付近: sanctioned floor submission は承認引数付き `submit_floor.sh` だけであり、raw `qsub -v` を組み立てないと追記する。
  - `docs/phase3.md:64,112-126` 付近: dated historyは残しつつ、T-2324 完了時点で旧「無条件拒否」が superseded されたことを現況追記する。

## 引数・env の命名と検査位置

具体案は次の組に固定する。

- submitter/driver CLI: `--confirm-official-floor-run`
- scheduler transport env: `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN`
- Python keyword: `confirm_official_floor_run`

既存 pilot 系の実名は `--confirm-irreversible-pilot-holdout` と `IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT` であり、文字列・用途とも衝突しない。

検査位置は次のとおり。

- submit 側: nonce の `^[0-9a-f]{32}$` 検査 (`submit_floor.sh:299-307`) 後、`qsub_cmd` 構築前の `:621` 付近。承認値を export spec へ append する直前に `,` と改行を拒否する。
- job 側: `floor_campaign.sh:547-551` の submission nonce 再検査直後。`${VAR+x}` で設定有無を判定し、設定済みなら空文字も含め exact 不一致を拒否する。
- Python 側: raw env は読まない。job が検証済み state を CLI flag へ射影し、argparse の exact bool を public/core へ渡す。
- receipt schema、job-result schema、admission claim key には承認値を書かない。

## 承認 flag の 1 個性を固定する検査

D324 (`docs/decisions.md:14662-14684`) の二層を `test_pegasus_floor_tools.py:2222-2309` で維持する。

- 主検査: `_run_floor_driver_tail` を承認 env 未設定/一致の 2 ケースで実行し、stub の実 argv を完全一致させる。

  未設定:

  ```python
  [
      "--mode", "official",
      "--protocol", expected_protocol,
  ]
  ```

  一致:

  ```python
  [
      "--mode", "official",
      "--protocol", expected_protocol,
      "--confirm-official-floor-run",
  ]
  ```

  後者では `actual_argv.count("--confirm-official-floor-run") == 1` も明示する。

- 従検査: job script 全体を POSIX `shlex` で token 化し、次を固定する。

  - driver path token は resolver と本起動の 2 個。
  - `resolve-current-protocol` は 1 個。
  - `--mode` は 1 個で、直後は `official`。
  - `--confirm-official-floor-run` は script 全体で 1 token。
  - `--resume` は 0 個。
  - mode 受け口用の `IZANAGI_FLOOR_MODE` と `eval` は 0 個。

生文字列の `source.count` だけを検出主体にしない。条件付き append を削除して無条件化する変異は「未設定時の実 argv」が、2 個 append する変異は「一致時の実 argv」と token 数が、それぞれ赤にする。

## テスト変更一覧

- `orchestrator/tests/test_s8b_floor_campaign.py:775-825`

  `_private_run_campaign` / `_run_campaign` の official fixture は、gate monkeypatch ではなく `confirm_official_floor_run=True` を明示する。承認と無関係な official E2E が新 gate で落ちないようにする。

- 同 `:6347-6355,6491-6493,11068,11508,11788,12636,12776`

  `_assert_official_permitted` を旧 1 引数 lambda で無効化している箇所を閉じる。可能な箇所は実引数 `confirm_official_floor_run=True` へ置換し、どうしても局所 patch が必要なら新 signature を受ける形にする。対象 test は以下。

  - `_deterministic_official_artifacts`
  - `test_repo_root_seam_runs_production_clean_scan_on_real_tmp_repo`
  - `test_real_seal_protocol_to_floor_official_core_e2e`
  - `test_new_seam_defaults_delegate_to_production_functions`
  - `test_second_scan_digest_shift_persists_claim_but_issues_no_certificate`
  - `test_official_scan_rejection_has_zero_filesystem_side_effects`

- 同 `:7081-7131`

  セクション見出しを「official は明示承認必須」に変更する。既存 `test_main_official_mode_always_refused` は `test_main_official_without_approval_is_refused_before_protocol_load` へ書き換え、rc=2、`status=refused`、理由に新 flag、理由に `§8` が無いこと、protocol loader 未呼出しを主張する。

  新設 `test_main_official_with_approval_forwards_exact_bool_to_run_campaign` は下流を stub 化し、CLI flag が `confirm_official_floor_run=True` として public wrapper へ 1 回渡ることを主張する。

- 同 `:7273-7299`

  - `test_run_campaign_core_rejects_official_materializer_injection_before_side_effects` は承認を `True` にして、materializer gate の意味を維持する。
  - `test_run_campaign_core_rejects_official_with_zero_side_effects` は public wrapper の未承認負例として改名・維持する。
  - 新設 `test_private_core_rejects_unapproved_official_before_side_effects` で private core 直接呼出しも拒否し、out_root・claim・build が無いことを確認する。
  - 新設 `test_official_permission_requires_exact_true` で `False`、`None`、`1` を拒否し、exact `True` だけを受理する。

- 同 `:7547-7567`

  `test_refreeze_seam_classifier_covers_and_classifies_every_core_seam` の非 seam 除外集合を

  ```python
  {"out_root", "mode", "resume_dir", "confirm_official_floor_run"}
  ```

  とする。classifier の期待集合と `REFREEZE_DISQUALIFYING_SEAM_NAMES` の 18 名 exact 一致はそのまま残す。

- 同 `:7786-7809`

  `test_core_derives_refreeze_eligibility_at_entry_and_finalizes_without_args` が指定された call-order pin。`:7804-7806` の逐語を新しい `_assert_official_permitted(mode, confirm_official_floor_run)` 呼出しへ更新し、さらに

  ```python
  derive_index < approval_gate_index < checkpoint_env_take_index
  ```

  を固定する。runner より前という既存 assert も残す。

- 同 `:7932-7939,8026-8032`

  旧 pilot confirmation parameter/flag が存在しない検査は残す。新 official 系と旧 pilot 系が別系統であることを明記する。

- `orchestrator/tests/test_pegasus_floor_tools.py:1337-1375`

  `test_floor_driver_consumes_checkpoint_environment_before_core_dispatch` は現状、`_validate_mode` より前の env pop を要求しており、新しい「gate より前に副作用なし」と衝突する。次の 2 本へ分ける。

  - `test_unapproved_official_does_not_consume_checkpoint_environment`
  - `test_approved_or_pilot_core_consumes_checkpoint_environment_before_effectful_dispatch`

- 同 `:2196-2219`

  `test_floor_job_has_no_confirmation_dataflow_and_keeps_admission_order` を `test_floor_job_has_nonce_bound_official_confirmation_dataflow_and_keeps_admission_order` へ変更する。exact 比較が receipt copy、reservation、gflags/glog build、driver より前で、raw env の export 属性解除も driver より前であることを検査する。

- 同 `:2222-2309`

  helper に承認 transport state を渡せるようにし、既存 `test_floor_job_invokes_fixed_pilot_cli_without_bypass` を `test_floor_job_invokes_fixed_official_cli_and_conditionally_appends_approval_once` へ変更する。前節の実 argv・token 二層検査をここへ置く。

- 同 `:2322-2340,2533-2558,2597-2628,2709-2752`

  - base `export_spec` が nonce 1 本で始まる検査は維持。
  - 新設 `test_submit_floor_confirmation_option_exports_nonce_bound_official_env` で option 指定時だけ、承認 env の値が receipt nonce と exact 一致することを確認。
  - `test_submit_floor_export_spec_has_no_confirmation_env` は ambient の新 official env と既存 pilot envを与えても、CLI option 無しならどちらも `qsub -v` へ入らないことを確認。
  - 新設 `test_submit_floor_checks_confirmation_value_for_qsub_delimiters_before_append` で `,`・改行検査の位置を構造固定。
  - `test_submit_floor_rejects_removed_confirmation_option_without_artifacts` は旧 pilot option の拒否として残す。
  - receipt の `PRE_KEYS` / `RECEIPT_KEYS` は変更しない。

- 同 `:2928-2999,3898-3931,4026-4143,4208-4309`

  driver tail の全 golden を official へ変更する。

  - `test_floor_liveness_terminal_reads_job_staging_failure_json`
  - `test_floor_protocol_resolution_is_shared_by_all_consumers`
  - `test_floor_driver_failure_propagates_rc`
  - `test_floor_driver_zero_rc_rejects_missing_w2_floor_metric`
  - job-result writer failure 2 本の prefix/helper

  期待値は `"mode": "official"`、新 flag 1 個、official failure 文言にする。

- 新設 shell binding tests

  `test_pegasus_floor_tools.py:2196` 付近に次を置く。

  - `test_floor_job_official_approval_binding_accepts_exact_nonce`
  - `test_floor_job_official_approval_binding_leaves_flag_absent_when_env_unset`
  - `test_floor_job_official_approval_binding_rejects_mismatch_before_build_and_driver`
  - `test_floor_job_official_approval_binding_rejects_empty_before_build_and_driver`

  後二者は rc=2、`write_failure` の引数が `2 / submit_binding / exact-match 理由`、build/driver marker 不在を主張する。

- `orchestrator/tests/test_s8b_holdout_freeze.py:1285-1301`

  `test_verify_rejects_unratified_generation_documents` の「未裁定」コメントを更新し、拒否継続、新しい v1-path 理由、`未裁定` 不在を確認する。

- `orchestrator/tests/test_s8b_ratified_freeze.py:940-963`

  fixture の `_assert_official_permitted` monkeypatch を除き、core 呼出しに `confirm_official_floor_run=True` を渡す。v2 generation の approval authority と floor official 起動承認を混同しない。

テストは実走していない。以上は静的読解と検索による変更対象であり、緑とは報告しない。

## (P1)〜(P4) への判断

- (P1) 固定 official 化を妨げる、生きた pilot consumer は現時点で見つからない。

  - production の `.sh` / `.py` を検索すると、`submit_floor.sh` を起動する別 consumer は 0 件。`floor_campaign.sh` の path consumer は receipt/checkpoint 検証だけで、pilot 起動 consumer ではない。
  - `test_pegasus_floor_tools.py:2270-2309` は D323/D324 の旧 pin であり production consumer ではない。
  - `s8b_floor_campaign.py` は pilot API 自体を保持するが、`floor_campaign.sh` 経由を要求していない。
  - missing な between-run floor は別 driver `orchestrator/campaign/between_run_floor.py:6-28,81-84,292` が担当し、write-heavy/balanced/read-heavy を直接列挙する。D1639 (`docs/decisions.md:50272-50288`) もこの量と official floor campaign を分離している。
  - floor pilot は `docs/paper-story/2026-08-26.md:63-65,274-281` で request `945229.nqsv` の 12 cell完走済み。現 worktree の `output/env/pegasus/floor/attempts/submissions/*/submit-receipt.json:1` にある 3 件は dry-run 1 件と古い実投入 2 件で、今後の consumer ではなく履歴証拠である。
  - `phase3-8b-restart-runbook.md:165-197,229-241` と `tools/pegasus/README.md:223-252` は現在も pilot 手順を掲げるが、実 consumer ではなく完走前の運用文言が残ったもの。今回 official 手順へ更新する。

  よって D926 の固定 official 化をそのまま実装できる。pilot APIそのものは削除しない。

- (P2) 文言だけ直し、挙動は変えない判断を採用する。

  D926 は floor official submission の承認輸送だけを裁定している。v2 generation は `s8b_ratified_freeze.py:1-12,69-72,109-124,1418` に独立した approval/active-chain authority がある。したがって `s8b_holdout_freeze.verify_document` の v1 経路で generation field を拒否する挙動は維持し、理由を「未裁定」から「この v1 経路は世代承認を検証しない」へ直す。

- (P3) 承認は core 引数で渡し、core は env を読まない判断を採用する。

  repo 内に floor official 承認 env の既存契約はない。D1628 のとおり raw env を authority にせず、shell の nonce exact 比較で authority を確定し、export 属性を外してから CLI bool へ射影する。承認 bool は seam、receipt、claim、artifact field のいずれにも入れない。

- (P4) 「現在の callsite を動かさない」は反証されたため、そのまま採用しない。

  `s8b_floor_campaign.py:7256-7260` は `take_checkpoint_environment(os.environ)` を呼び、実体 `floor_job_checkpoint.py:474-490` は `environ.pop` を行う。現在の core gate `:7304` より前に既に副作用がある。

  gate は `_derive_refreeze_eligibility` (`:7277-7279`) の後、checkpoint env 消費の前へ移す。これにより指定された導出順を保ちながら、build `:7627/:7695`、claim `:7879`、runner `:7926`、filesystem write のすべてより前にできる。

## pin 閉包の取り残し

- 更新必須の source/comment pin

  - `s8b_floor_campaign.py:42-45,465-475,5166-5167,7207-7208,7256-7304,8393-8406,8601-8630`
  - `_assert_official_permitted` の test 参照:
    `test_s8b_floor_campaign.py:815,6350,6492,7805,11068,11508,11788,12636,12776`
  - 外部 test fixture:
    `test_s8b_ratified_freeze.py:940-963`
  - old freeze reason:
    `s8b_holdout_freeze.py:933,940,951` と
    `test_s8b_holdout_freeze.py:1294-1301`

- 更新必須の shell golden

  - `test_pegasus_floor_tools.py:2196-2219`: confirmation dataflow/order
  - `:2222-2309`: fixed pilot argv、D324 token/actual argv
  - `:2322-2340,2533-2558,2597-2628,2709-2752`: `qsub -v` export
  - `:2958-2999`: liveness failure 文言
  - `:3898-3931`: resolver + driver argv
  - `:4026-4143`: job-result mode、driver/metrics failure 文言
  - `:4208-4309`: tail helper に必要な承認済み local state

- seam/eligibility pin

  - `test_s8b_floor_campaign.py:7547-7567` の non-seam 除外集合へ承認引数を追加する。
  - `s8b_floor_contract.py:42-50` の 18 名集合は変更しない。
  - `s8b_floor_campaign.py:7118-7131` の判定式は変更しない。
  - `s8b_holdout_admission.py:753-771` の admission key 6 項目も変更しない。
  - `test_s8b_floor_campaign.py:7786-7809` の導出順 pin を更新する。

- schema pin

  - `submit_floor.sh:348-389,679-709` の pre-submit/receipt payloadは変更しない。
  - `floor_campaign.sh:629-691` の submit receipt exact key集合は変更しない。
  - `floor_submit_receipt.py:14` の job script path は同一なので変更不要。
  - `JOB_RESULT_KEYS` は mode の値だけが変わり、key集合は不変。

- closure 登録簿

  - `orchestrator/tests/test_official_perf_closure.py:44-68,174-189,266-368` は既に `s8b_floor_campaign.py` と `s8b_holdout_freeze.py` を列挙する。新しい perf call/guard/file は増えないため登録変更不要。
  - process/materializer 起動点は増えないため `test_materializer_registry_covers_all_python_build_launches` の registry 変更不要。
  - `test_env_contract.py:80-99` は file 単位登録だけで、Python に新しい env literal を加えないため変更不要。
  - `orchestrator/tests/acceptance_duration_ledger.json:1463-1466,11308-11319,11338-11339,11371,13372,13494,13704,14151` には旧/new test nodeid が混在する。意味論 pin ではなく scheduling hint なので、推測時間を手書きしない。親の実 pytest/JUnit 後に正規 updater で新 nodeid・実測値を再生成する。

- runbook/docs

  - 更新: `tools/pegasus/README.md:217-257`
  - 更新: `docs/phase3-8b-restart-runbook.md:49,165-197,229-241`
  - 更新または現況追記: `docs/pegasus-runbook.md:1641-1645`
  - 現況の supersede 追記: `docs/phase3.md:64,112-126`
  - `docs/decisions.md` の D323/D324/D926 は歴史的裁定なので書き換えない。
  - `docs/failures.md:17106-17124` は当時の見落とし記録なので書き換えない。
  - `docs/paper-story/2026-08-26.md` / `2026-09-05.md` と `output/insights/**` は dated evidence であり改変しない。

- hooks 設定

  `.claude/settings.json` と `hooks/**` には対象識別子/pathの pin は無かった。`test_hooks.py:2709-2713,2955-2959,3102-3106` は job body=`dispatch-required`、submitter=`local-ok` という実行場所分類だけであり、この変更で分類は変わらない。hooks 設定・登録簿の更新は不要。

- 新識別子の期待閉包

  実装後、`--confirm-official-floor-run` は submitter usage/parser、job の条件付き append、driver parser/拒否文言、tests、runbook だけに現れるべきである。`IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` は submitter export、job exact-match/export解除、tests、runbook だけに限定し、Python production source、receipt、manifest、result、claim、ledger schemaには出現させない。

## 段 5 の分割境界

U1 と U2 の間に同一 file の編集衝突はない。

- U1: `orchestrator/campaign/s8b_floor_campaign.py`、`s8b_holdout_freeze.py`
- U2: `tools/pegasus/submit_floor.sh`、`floor_campaign.sh`、影響する `orchestrator/tests/*.py`

ただし意味論上の handshake はある。

- U1 が確定する Python flag/keyword 名を U2 の job argv と tests が使う。
- U1 の gate 前倒しにより、U2 所有の `test_pegasus_floor_tools.py:1337-1375` の checkpoint env 順序テストを更新する必要がある。
- U2 の D324 test は U1 parser に同 flag が存在することを前提にする。

したがって file 境界の引き直しは不要だが、名称を先に固定し、U1 を適用後に U2 tests を合わせる。docs 本文は D95 に従って親が統合時に更新し、どちらの author unit にも重複所有させない。duration ledger は実測後の親処理に分離する。

## 総括

D926 を最小に写す経路は、

`submit_floor.sh --confirm-official-floor-run`
→ `qsub -v IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=<submission nonce>`
→ job の nonce exact 一致
→ raw env の export解除
→ fixed `--mode official`
→ driver 末尾へ承認 flag 1 個
→ CLI/public/private core の明示承認 gate

である。

未設定は flag を運ばず、設定済みの不一致・空文字は `submit_binding` で fail-closed、core の `True` 以外は全拒否とする。18 seam 集合、refreeze eligibility 式、receipt schema、admission key 6 項目、artifact schemaには触れない。静的調査のみで、ファイル変更・commit・pytest 実走は行っていない。