## 変更一覧

指定7ファイルのみ変更しました。以下、ADC／CBR／TA／TR／TDを略称として使います。

| ファイル | 変更箇所・内容 |
|---|---|
| `tools/audit_dangling_commits.py`（ADC） | `AuditReport:84` にmode追加。`audit_with_offrepo:1689` にmode検査・off早期返却。`_print_offrepo_report:1922` に専用開示。`main:1978` にCLI・root分岐追加 |
| `tools/check_branch_rescue.py`（CBR） | `_child_env:209` からroot環境変数を除外。`_audit:1790` のargvとsummary全3経路をoff固定 |
| `.claude/commands/cleanup-branches.md:37` | 指定candidateとbytes完全一致 |
| `tools/check_docs.py:789` | digest定数のみ更新 |
| `orchestrator/tests/test_check_docs.py`（TD） | `581` digest、`663` synthetic本文、`9948/9953` baseline、`9954` 超過fixture更新 |
| `orchestrator/tests/test_audit_dangling_commits.py`（TA） | `4195`以降に指定8テスト追加 |
| `orchestrator/tests/test_check_branch_rescue.py`（TR） | `349` p04 assert追加、`1639`以降に指定4テスト追加 |

新設helperはTAの `_mode_fixture:4180`（到達不能commitとlanded参照付き外部copy）、`_forbid_offrepo_io:4191`（禁止I/Oのtrap）です。production helperの新設はありません。

差分規模（追加＋削除）はADC **46行**、CBR **10行**。TA/TR追加は合計 **252行**。すべて上限内です。

cleanup commandは **6,181 bytes**、SHA-256は次のとおり。`sha256sum`とcandidateとのbytes比較で確認しました。

```text
7cc008fabc10b3b495eedfeb0bfbee2de14a3c908e1eb5aa6dd7ff4d7ebaf8ae
```

## 実走結果

| 実走範囲 | 結果 |
|---|---|
| `PYTHONPATH=. python3 orchestrator/tests/test_audit_dangling_commits.py` | **166 passed、0 failed** |
| `PYTHONPATH=. python3 orchestrator/tests/test_check_branch_rescue.py` | **88 passed、0 failed** |
| pytest.mainによる `test_branch_rescue_ledger.py` と `test_plain_runner_coverage.py` 全node | **38 passed、0 failed** |
| TDの名前に`cleanup`を含む22関数の直接呼出し | **22 passed、0 failed** |
| `python3 tools/check_docs.py` | **rc 0、違反なし** |
| `git diff --check` | **rc 0** |

新設nodeはすべて指定名のまま実走しました。nodeidのprefixはTA/TRの上記ファイルパスです。

```text
TA::test_explicit_off_ignores_env_and_preserves_core
TA::test_explicit_off_touches_no_offrepo_io
TA::test_explicit_off_disclosure_is_distinct_from_missing_root
TA::test_explicit_full_suppresses_copy_that_off_reports
TA::test_explicit_full_matches_legacy_root_report[cli]
TA::test_explicit_full_matches_legacy_root_report[env]
TA::test_explicit_off_with_cli_root_is_usage_error[no-env]
TA::test_explicit_off_with_cli_root_is_usage_error[env]
TA::test_explicit_full_without_root_is_execution_failure[absent]
TA::test_explicit_full_without_root_is_execution_failure[empty]
TA::test_explicit_full_missing_root_preserves_elapsed_overrun

TR::test_audit_child_argv_is_explicit_off
TR::test_child_env_omits_offrepo_root
TR::test_audit_summary_discloses_off_for_all_outcomes[zero]
TR::test_audit_summary_discloses_off_for_all_outcomes[finding]
TR::test_audit_summary_discloses_off_for_all_outcomes[invalid]
TR::test_audit_summary_discloses_off_for_all_outcomes[timeout]
TR::test_audit_summary_discloses_off_for_all_outcomes[decode]
TR::test_real_audit_off_reports_landed_external_copy_with_or_without_env
TR::test_p04_missing_ledger_and_real_audit_zero_is_rc0
```

TDの直接実走対象は以下の22関数です。

```text
test_codex_cleanup_branches_skill_contract_pins_exact_surface
test_cleanup_command_budget_is_pinned_and_enforced
test_cleanup_skill_one_byte_change_is_rejected
test_cleanup_command_one_byte_change_is_rejected
test_cleanup_skill_additional_h2_is_rejected
test_cleanup_command_closing_hash_h2_is_rejected
test_cleanup_command_leading_space_h2_is_rejected
test_cleanup_command_setext_h2_is_rejected
test_cleanup_command_invalid_backtick_info_is_rejected
test_cleanup_metadata_policy_block_is_rejected
test_cleanup_checker_invocation_line_is_required
test_cleanup_checker_rc_rules_are_required_with_invocation
test_cleanup_checker_negated_invocation_is_rejected
test_cleanup_checker_literals_scattered_across_sections_are_rejected
test_cleanup_address_edge_rejects_split_lines
test_cleanup_address_edge_rejects_id_adjacent_decoy
test_cleanup_address_edge_rejects_non_code_span_path_decoy
test_cleanup_address_edge_rejects_raw_html_block
test_cleanup_address_edge_rejects_link_definition
test_cleanup_address_edge_rejects_frontmatter_decoy
test_cleanup_address_edge_accepts_rewording
test_cleanup_address_edge_accepts_baseline
```

初回TRは **85 passed、3 failed**。新設summaryテストの通知キー誤記（`kind`→既存契約の`code`）を修正し、全88件を再実走しました。TDは初回importがgrowth-holdに拒否されたため、明示された実走指示に基づき所定の解除トークンを設定して上記22関数を実行しました。

TD全体、親の`tools/run_tests.py`統合実走、変異本走、実根での性能測定は未実走です。

## 期待値変更

既存ADC/CBRテストの期待値は変更していません。p04は既存assertを保持し、`offrepo_scan == "off"`と`complete is True`の2assertだけ追加しました。

TDは指示されたdigest・synthetic本文・baseline・超過fixtureだけ更新しました。上限6,204 bytes、違反fixture6,205 bytes、違反文言は維持しています。skip・削除・期待値緩和はありません。

## 波及可能性

指定の検索語を `tools orchestrator .claude docs` に対して検索しました。

- `audit_with_offrepo`の直接callerはADC自身とTA。既存API呼出しは既定`None`により互換です。
- CBRの`_child_env`はGit（277）、landed（1571）、audit（1792）、補助起動（2181）に波及します。Git・landed・audit各子の環境からrootが消えることを実走確認しました。
- cleanupのconsumerは`check_docs.py:6619`、TDのdigest/予算/edge検査、`test_branch_rescue_ledger.py:344`。関連検査は成功しています。
- `test_plain_runner_coverage.py`とREADME allowlistは変更不要。新test fileはなく、meta-testも成功しています。
- `acceptance_duration_ledger.json`、共有`conftest.py`は未変更。新nodeの所要登録・統合実走は親側の確認対象です。
- `docs/pegasus-runbook.md:859`、`docs/decisions.md:11502`、archiveの旧挙動説明に検索hitがあります。現行入口の説明更新は親担当です。
- `tools/mutation_worktree.py`、`tools/dev_waves/daemon.py`、`tools/pegasus/dispatch_compute.py`、`test_pytest_collection_config.py`等の同名環境helperは別実装であり、本変更の直接callerではありません。

## 受理集合の自己申告

変更前は、省略＋rootで走査・抑止、省略＋rootなしで未実施表示（rcはfindings次第）でした。rescueの子はenv rootを継承し、走査・抑止しえました。

変更後は以下です。

- **省略時**：CLI root優先、次にenv、両方なしは従来表示。互換経路を維持。
- **off**：APIの非空rootsも無視。findingsはcoreと同一、抑止・unreferenced copiesは空。外部I/Oなし。
- **off＋CLI root**：usage error、rc 2、terminal行なし。
- **full＋rootなし**：snapshot前に実行不能、rc 2、terminal行あり。超過開示順序も維持。
- **full＋同じroot**：既存経路とreport・非時間依存の報告行が一致。
- **未知のAPI mode**：RuntimeError。
- **rescue**：常にoff。実fixtureで、単独fullは抑止1・rc 0、rescueはenv有無とも同じ未記帳commit・rc 3・complete trueを確認。

受理集合の変更は上記の明示modeと掃除入口に限定しました。省略＋envによるad-hoc走査経路は残ります。

## 変異 matrix の対象行と予想 killer

以下の`old`は**実装後の現物にある逐語anchor**です。変異実走結果ではなく、単独変異に対する予想です。

| ID | 対象・old anchor | 変異／予想killer |
|---|---|---|
| M0 | ADC:1699 `"""既存 findings に repo 外の同一実体による抑止を後段適用する。"""` | docstringだけ変更。**SURVIVED** |
| M1 | ADC:1714 `requested = accepted = rejected = ()`、1733 `if offrepo_scan == "off" or not requested or not accepted:` | offでもroots検証・通常走査へ送る。TA::`test_explicit_full_suppresses_copy_that_off_reports` |
| M2 | ADC:2034 `if args.offrepo_scan == "off":` | off分岐でenv rootを取得する。TA::`test_explicit_off_ignores_env_and_preserves_core` |
| M3 | ADC:1702 `if offrepo_scan == "full" and not offrepo_roots:` | root必須の拒否ブロックを除去。TA::`test_explicit_full_without_root_is_execution_failure[absent]` |
| M4 | CBR:1797 `[sys.executable, str(audit_tool), "--repo", str(repo), "--offrepo-scan", "off"],` | flag pairを除去。TR::`test_audit_child_argv_is_explicit_off` |
| M5 | CBR:220 `"GIT_CONFIG_NOSYSTEM",` | allowlistにroot環境変数を復元。TR::`test_child_env_omits_offrepo_root` |
| M6 | ADC:1925 `"audit_dangling_commits: repo 外走査は明示 off"` | off開示を従来の未指定2行へ置換。TA::`test_explicit_off_disclosure_is_distinct_from_missing_root` |
| M7 | ADC:2025 `parser.error("--offrepo-scan off と --offrepo-root は併用できません")` | usage拒否を除去。TA::`test_explicit_off_with_cli_root_is_usage_error[no-env]` |
| M8 | CBR:1803/1809/1840。下記3行 | 全summaryからmodeを除去。TR::`test_audit_summary_discloses_off_for_all_outcomes`の全5parameter |
| M9 | `tools/check_docs.py:789` `"7cc008fabc10b3b495eedfeb0bfbee2de14a3c908e1eb5aa6dd7ff4d7ebaf8ae"` | 旧digestへ戻す。TD::`test_codex_cleanup_branches_skill_contract_pins_exact_surface` |
| M10 | ADC:1733 `if offrepo_scan == "off" or not requested or not accepted:` | 返却前に`_load_blob_metadata`呼出しを挿入。TA::`test_explicit_off_touches_no_offrepo_io` |
| M11 | ADC:1733 同上 | 返却前に`_enumerate_offrepo_candidates`呼出しを挿入。TA::`test_explicit_off_touches_no_offrepo_io` |

M8のold全文（各行はfile内で一意）：

```python
        return [], {"offrepo_scan": "off", "complete": False, "returncode": None, "reported_commit_count": None,
        return [], {"offrepo_scan": "off", "complete": False, "returncode": result.returncode,
        "offrepo_scan": "off", "complete": complete, "returncode": result.returncode,
```

M9の復元先：

```text
a6380f90dcaf8e5e5ac21cc9af0619e000697816257f3e3e8a8844595dad1f26
```

## 総括

実装と指定範囲の機能検証を完了しました。最終結果は**314件成功、失敗0件**です。所有外編集・docs作成・git add・commitは行っていません。

親には統合runner実走、変異本走、docs更新、実根の所要受理を引き渡します。本wave全体のclosed判定はしていません。
