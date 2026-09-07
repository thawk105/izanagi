## 変異 11 件の対応表 (変異 / 赤にするテスト / 単一理由か / 判定)

| ID | 変異位置 | 赤にするテスト | 単一理由性 | 判定 |
|---|---|---|---|---|
| M-1 | `floor_campaign.sh:1221-1225` 条件付き append を無条件化 | [test_pegasus_floor_tools.py:2374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:2374) `test_floor_job_unset_approval_omits_flag_from_actual_argv` | **単一理由**。`OFFICIAL_APPROVAL_BOUND=0` を直接与えた tail で、実 argv の完全一致が壊れる。他 gate は介在しない。 | **有効な kill**。未承認 job の受理集合を開く変異。 |
| M-2 | `floor_campaign.sh:1221-1225` append を 2 回 | [test_pegasus_floor_tools.py:2386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:2386) `test_floor_job_exact_approval_appends_flag_once_in_actual_argv`、[同:4060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:4060) `test_floor_protocol_resolution_is_shared_by_all_consumers` | append の多重化だけに帰属する。後者は承認済み実 argv 全体を exact 固定している。 | **kill ではなく transport-shape sensitivity pin**。`argparse store_true` は重複 flag を受理し、受理集合も fail-closed 挙動も変わらない。 |
| M-3 | `s8b_floor_campaign.py:7209` public gate 呼出し削除 | [test_s8b_floor_campaign.py:7319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_floor_campaign.py:7319) `test_public_wrapper_rejects_unapproved_official_before_private_core` | **単一理由**。実 Git authority を `_test_holdout_authority` で構成し、有効な protocol / `VerifiedFreeze` / canonical path を渡す。private core は到達即 `AssertionError` の sentinel で、private gate に拒否理由を横取りさせない。 | **有効な kill。A-4 は閉じた。** 要求された「authority を通る入力」「private core を名指し」「到達自体を赤」を満たす。 |
| M-4 | `s8b_floor_campaign.py:7307` private core gate 呼出し削除 | [test_s8b_floor_campaign.py:7365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_floor_campaign.py:7365) `test_private_core_rejects_unapproved_official_before_downstream` | **単一理由**。CLI/public を通らず、valid `VerifiedFreeze` を渡し、直後の `_validate_protocol_against_current` を到達 sentinel にしている。 | **有効な kill**。 |
| M-5 | `s8b_floor_campaign.py:471` `is not True` を `if not confirm` へ | [test_s8b_floor_campaign.py:7386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_floor_campaign.py:7386) `test_official_permission_requires_exact_true` | **単一理由**。`False` / `None` は変異後も拒否されるが、truthy な `1` だけが通って `pytest.raises` を破る。 | **有効な kill**。 |
| M-6 | `floor_campaign.sh:554-558` 空文字分岐削除 | [test_pegasus_floor_tools.py:2297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:2297) `test_floor_job_official_approval_binding_rejects_empty_before_downstream` | 挙動は後続 `!=` が同じ空値を拒否し、rc=2、stage=`submit_binding`、downstream 未到達のまま。変わるのは文言だけ。 | **behavioral kill ではない。diagnostic sensitivity pin。A-5 は診断上のみ閉じ、受理集合の歯としては閉じていない。** |
| M-7 | `floor_campaign.sh:559-563` nonce 不一致比較削除 | [test_pegasus_floor_tools.py:2310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:2310) `test_floor_job_official_approval_binding_rejects_mismatch_before_downstream` | **単一理由**。submission nonce は valid hex、approval も非空で、空分岐や nonce 形式検査は発火しない。削除後は downstream に到達する。 | **有効な kill**。 |
| M-8 | `floor_campaign.sh:1218` `official` を `pilot` へ | [test_pegasus_floor_tools.py:2398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:2398) `test_floor_job_driver_mode_is_fixed_official_in_tokens_and_actual_argv`。完全 argv は同:2374 と同:4060 も赤にする。 | **単一理由**。stub driver は実 argv を記録し、mode の別受け口はない。 | **有効な kill**。pilot artifact へ戻る挙動変化を捕捉する。 |
| M-9 | `submit_floor.sh:84-87` 実投入必須 guard 削除 | [test_pegasus_floor_tools.py:2874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:2874) `test_submit_floor_real_run_requires_approval_before_staging_and_qsub` | **単一理由**。rc / exact stderr に加え、`output/env`、`output/claims`、外部 command sentinel が未生成であることを要求する。後段で別拒否されても早期 fail-closed 条件は満たせない。 | **有効な kill**。 |
| M-10 | `s8b_floor_campaign.py:8608-8615` CLI 拒否削除 | [test_s8b_floor_campaign.py:7122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_floor_campaign.py:7122) `test_main_official_without_approval_is_refused_before_protocol_load` | **単一理由**。protocol loader を到達即失敗 sentinel にしているため、public/core の後段拒否に隠れない。通常時は rc=2、`status=refused`、loader 0 回を要求する。 | **有効な kill**。 |
| M-11 | `s8b_holdout_freeze.py:1005` 世代拒否呼出し削除 | [test_s8b_holdout_freeze.py:1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_holdout_freeze.py:1285) `test_verify_rejects_unratified_generation_documents` | **過剰決定**。呼出し削除後も直後の `verify_document:1006-1009` が `set(doc) != TOP_LEVEL_KEYS` で全 generation field を拒否する。テストが赤になるのは専用文言が消えるためだけ。 | **behavioral kill ではない。diagnostic sensitivity pin**。M-11 の単一理由性は不成立。 |

厳格な定義では、11 件中 behavioral kill は **M-1、M-3、M-4、M-5、M-7、M-8、M-9、M-10 の 8 件**です。M-2、M-6、M-11 は別枠です。

## テスト弱体化の検査

skip / xfail の追加、テストファイルの削除、期待成功から期待失敗への無根拠な反転はありません。主要な旧 assert と新 assert は次のとおりです。

| 対象 | 旧 assert | 新 assert | 評価 |
|---|---|---|---|
| CLI official 拒否 | `status == "refused"`、`"§8" in reason` | 同じ rc/statusに加え、`"--confirm-official-floor-run" in reason`、旧文言不在、protocol loader 0 回 | 強化。M-10 を先段に帰属可能。 |
| public official 拒否 | `pytest.raises(..., match="official")`、`not out_root.exists()` | valid authority、exact reason、private core 0 回、output なし | 強化。A-4 の要求形。 |
| job mode | 実 argv `["--mode","pilot",...]`、source token の直後が `pilot` | 未承認時の完全 argvは `official`、承認時の完全 argvは `official + flag`、flag count=1 | 意図した反転。完全一致は維持。 |
| qsub export | `export_spec == NONCE` | 承認済み実投入では `NONCE,APPROVAL=NONCE` を完全一致。evidence-root 経路も 3 field 完全一致 | 意図した反転で、exactness は維持。 |
| ambient confirmation | 実 qsub の export spec 完全一致 | dry-run stdout について新旧 confirmation env 不在と nonce 存在を確認 | この改名テスト単体では部分一致へ弱くなったが、実投入の完全一致は別テストが維持。RB-5。 |
| holdout generation 拒否 | `pytest.raises(..., match="未承認世代...")` | 新理由の 2 substring と旧 `未裁定` / `§8` 不在 | 診断 pin は強化。ただし M-11 の behavioral kill にはならない。 |
| job-result / failure golden | `"mode":"pilot"`、`pilot floor ...` | `"mode":"official"`、`official floor ...` | 意図した完全反転。緩和なし。 |

fixture については、旧 `_assert_official_permitted = lambda` monkeypatch が除去され、official helper が `confirm_official_floor_run=True` を実 gate に渡す形になっています。gate 自体を stub で消す旧形より強いです。public 正例は実 authority を通し、private core だけを境界 sentinel にしています。shell テストも production source から切り出した実 fragment / tail を実行しており、承認分岐や argv 構築そのものを stub に置換していません。

現行 HEAD hash、working-tree hash、実行時刻、repo の絶対 pathを期待値へ焼き込んだ追加はありません。`tmp_path` の絶対 path はテスト自身が生成した同一 argvとの照合であり、揮発する repo 成果物 pin ではありません。

## pin 閉包の取り残し

- `_DEFERRED_GATE_MEMBERS` は閉じています。

  - `s8b_floor_campaign.py` の `invoke_build` sink は実体 [4705行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:4705)。定義 [test_ccbench_spawn_sites.py:890](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_ccbench_spawn_sites.py:890) と自己 golden [同:2665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_ccbench_spawn_sites.py:2665) はともに 4705。
  - `main` の campaign sink は実体 [8632行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:8632)。定義 [test_ccbench_spawn_sites.py:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_ccbench_spawn_sites.py:898) と自己 golden [同:2669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_ccbench_spawn_sites.py:2669) はともに 8632。

- [acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/acceptance_duration_ledger.json:1463) は未更新です。残存する死んだ nodeid は次の 7 件です。

  - `test_floor_job_has_no_confirmation_dataflow_and_keeps_admission_order`
  - `test_floor_job_invokes_fixed_pilot_cli_without_bypass`
  - 同 `[confirmed-flag-appended-once]`
  - 同 `[unconfirmed-four-arguments]`
  - `test_submit_floor_export_spec_has_no_confirmation_env`
  - `test_main_official_mode_always_refused`
  - `test_run_campaign_core_rejects_official_with_zero_side_effects`

- ledger に無い新設・改名 nodeid は次の 17 件です。

  - `test_floor_job_has_nonce_bound_official_confirmation_dataflow_and_keeps_admission_order`
  - `test_floor_job_official_approval_binding_accepts_exact_nonce`
  - `test_floor_job_official_approval_binding_leaves_flag_absent_when_env_unset`
  - `test_floor_job_official_approval_binding_rejects_empty_before_downstream`
  - `test_floor_job_official_approval_binding_rejects_mismatch_before_downstream`
  - `test_floor_job_unset_approval_omits_flag_from_actual_argv`
  - `test_floor_job_exact_approval_appends_flag_once_in_actual_argv`
  - `test_floor_job_driver_mode_is_fixed_official_in_tokens_and_actual_argv`
  - `test_submit_floor_without_option_ignores_ambient_confirmation_env_in_dry_run`
  - `test_submit_floor_real_run_requires_approval_before_staging_and_qsub`
  - `test_main_official_without_approval_is_refused_before_protocol_load`
  - `test_main_official_with_approval_forwards_exact_bool_to_run_campaign`
  - `test_public_wrapper_rejects_unapproved_official_before_private_core`
  - `test_public_wrapper_approved_official_forwards_exact_true_to_private_core`
  - `test_private_core_rejects_unapproved_official_before_downstream`
  - `test_official_permission_requires_exact_true`
  - `test_v1_source_verification_keeps_worktree_exactness_and_names_v2_authority`

- live docs の未更新箇所は次のとおりです。いずれも裁定上は親の段 7 所有ですが、land 前の pin 閉包には必要です。

  - [tools/pegasus/README.md:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/README.md:226): 引数なし実投入を案内し、pilot と説明。
  - 同 `:247-250`: 「承認引数は要らない」「qsub は nonce と evidence rootだけ」。
  - 同 `:251-256`: 固定 `--mode pilot`、job-result mode pilot、official 受理集合空。
  - 同 `:260`: `pilot floor driver returned nonzero`。
  - [docs/phase3-8b-restart-runbook.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/docs/phase3-8b-restart-runbook.md:49): official 二重拒否を現況扱い。
  - 同 `:165-197`: 固定 pilot、無条件 official 拒否、official 空集合、W-2 pilot 先行を現況扱い。
  - 同 `:221-222`: official の受理集合が変わらないとの記述。
  - 同 `:229-241`: 実投入手順に承認引数がなく、「承認引数不要」と明記。
  - 同 `:244-252`: pilot と同じ即時退避を前提とする記述。裁定どおり official result の repo-relative 読取りと整合させる必要がある。
  - 同 `:448-449`: 固定 pilot 経路で走らせるとの決着文。
  - [docs/phase3.md:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/docs/phase3.md:112) と `:118-127`: official 空集合、固定 `--mode pilot`、段階 3・4 未着手という現況。
  - [docs/pegasus-runbook.md:1641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/docs/pegasus-runbook.md:1641)-1644: sanctioned path が承認引数付き `submit_floor.sh` であることと、raw `qsub` は nonce 束縛保証外であることが未記載。

- `§8 未裁定` の残存は dated paper-story 3 件だけで、裁定 §6 により履歴として維持対象です。`pilot のみ実行可` は新テストの「不在」assertだけです。変更不要です。

- floor job を `--mode pilot` と仮定する生きたテストは残っていません。`test_pegasus_floor_tools.py:1374` の `mode="pilot"` は checkpoint env 消費順の API 単体テストで、wrapper mode の期待ではありません。その他の pilot API テストも独立した pilot 受理集合の検査です。

- test file 集合の新設・削除はありません。[test_plain_runner_coverage.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_plain_runner_coverage.py:44) は directory を動的列挙するため、明示集合の更新は不要です。

- 自走 harness は一部未閉鎖です。

  - `test_pegasus_floor_tools.py:4478-4483` と `test_ccbench_spawn_sites.py:3519-3524` は `pytest.main([__file__, "-q"])` を持つ。
  - `test_s8b_floor_campaign.py` は `__main__` がなく、新設・改名した M-3/M-4/M-5/M-10 系テストを `PYTHONPATH=. python3 <file>` では実行しない。
  - `test_s8b_holdout_freeze.py` は末尾 `plain_runner="none"` で、M-11関連の新設テストを直接実行しない。
  - 両ファイルは `orchestrator/tests/README.md:164,166` の pytest-only allowlist に載っているため既存 meta-testには拒否されませんが、今回指定された自走条件そのものは満たしません。

## 所見 (must-fix)

**RB-1 [must-fix] M-2、M-6、M-11 を behavioral kill と数えられない。**

M-2 は argv 多重性だけ、M-6 は空専用文言だけ、M-11 は専用拒否理由だけを pin します。特に M-11 は直後の exact top-level schema 拒否により過剰決定です。mutation 対応表では 8 behavioral kills と 3 diagnostic / structural sensitivity pins に分離する必要があります。

成果物影響: DW-M01 の「11 件すべてが受理集合または fail-closed 挙動を kill する」という検証記録が事実と異なるものになります。

**RB-2 [must-fix] acceptance duration ledger が改名・新設 test nodeid に追随していない。**

旧 nodeid 7 件が残り、新 nodeid 17 件が欠落しています。

成果物影響: acceptance の shard 割当・所要時間根拠・node coverage が、実際に収集される suite と一致しません。

**RB-3 [must-fix] 新設・改名テストのうち 2 test file が要求された自走 harness を持たない。**

`test_s8b_floor_campaign.py` は直接起動するとテストを走らせず、`test_s8b_holdout_freeze.py` は growth hold の `plain_runner="none"` です。既存 pytest-only allowlist は meta-testを満たしますが、今回要求された `PYTHONPATH=. python3 <file>` の検証経路にはなりません。

成果物影響: A-4、M-4、M-5、M-10、M-11 の新テストを単独ファイル実行で検証したという証拠を作れません。

**RB-4 [must-fix] live 運用文書が旧 pilot interface のままである。**

README は引数なし real submission を案内し、restart runbook と phase3 は official 空集合・固定 pilot を現況として扱っています。段 7 親所有でも、実装と同じ変更単位の完了条件として未閉鎖です。

成果物影響: 文書どおりの実投入は新 guard で rc=2 になり、また job-result / failure の期待 mode と文言を誤判定します。

## 所見 (nit)

**RB-5 [nit] 改名された ambient-env テスト単体では exact export spec が部分一致へ弱くなった。**

旧 `test_submit_floor_export_spec_has_no_confirmation_env` は実 qsub の `export_spec == NONCE` を要求しました。新 [test_submit_floor_without_option_ignores_ambient_confirmation_env_in_dry_run](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:2842) は nonce の stdout 内存在と confirmation env 不在だけです。ただし承認済み実 qsub の完全一致は同ファイル `:2663-2691`、evidence-root 付き完全一致は `:2757-2763` が維持しているため、suite 全体の主張低下には至りません。

## 総括

production の承認配線自体と M-1、M-3、M-4、M-5、M-7、M-8、M-9、M-10 の単一理由性は静的には成立しています。特に A-4 は要求された sentinel 構造で閉じています。

ただし A-5 は専用診断を識別できるようになっただけで、`-z` 削除後も不一致比較が同じ入力を拒否します。M-11も exact schema拒否に過剰決定され、M-2も受理集合不変です。この3件を kill から分離し、ledger、自走 harness、live docs を閉じるまではレビュー通過とは判定できません。

repo は変更しておらず、pytestも実走していません。以上は指定 worktree と提供 patch に対する静的検査です。