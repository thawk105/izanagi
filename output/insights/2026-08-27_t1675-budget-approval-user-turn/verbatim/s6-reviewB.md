**所見 1: N1 の AST denylist は承認者流入を実効的に閉じていない**

- 種別: must-fix
- 根拠: `orchestrator/tests/test_s8b_budget_approval_preflight.py:105-136`
- 反証条件: 次のような変異を入れ、N1 または専用の behavioral negative が赤になること。

```python
from os import environ as source

key = "appro" + "ver"
if not approval[key].strip() and "S8B_APPROVAL_USER" in source:
    approval[key] = source["S8B_APPROVAL_USER"]
```

  `environ` は `ast.Attribute` ではなく import alias なので検出されない。`--identity` のような option、`__import__("sub" + "process").check_output(["git", "config", ...])`、`"confirmed" + "_" + "by"` も現検査を迂回できる。環境変数がテスト時だけ不在なら、既存 approver 負例も赤にならない。
- 成果物影響: AI が制御できる argv、環境変数、git config、active v1 由来の値を approver fallback にする実装が N1 を通過し得る。親裁定 `stage4-adjudication.md:82-84,90-93` の機械的な gate になっていない。

**所見 2: timestamp の parametrize は二つの判定で過剰決定され、canonical timestamp 判定を殺さない**

- 種別: must-fix
- 根拠: `orchestrator/tests/test_s8b_budget_approval_preflight.py:244-294`、`tools/s8b_budget_approval_preflight.py:196-208`
- 反証条件: parser は通るが再整形比較だけに落ちる値、例えば `2026-1-01T00:00:00Z` を別 node にし、parser 拒否変異と canonical 比較変異を別々に赤にすること。
- 成果物影響: `tools/s8b_budget_approval_preflight.py:205-208` を削除しても現 `[timestamp]` は `strptime` で拒否され続ける。preflight が production loader より広い timestamp を受理し、貼り付けた pin が builder では拒否される回帰を見逃す。

9 変異の現在の帰属は次のとおり。共通 nodeid prefix は  
`orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_rejects_each_approval_contract_violation`。

| id | 実際の最初の拒否 | 単一理由性 |
|---|---|---|
| `approval-keys` | tool `:187-188` | あり。parse は通り、canonical writer 使用のため canonical 比較にも先取りされない |
| `scope` | tool `:191-192` | あり |
| `approver` | tool `:193-195` | あり |
| `timestamp` | tool `:199-204` | なし。parser を緩めても `:205-208` が拒否する |
| `oracle-shared` | freeze `:1270-1271` | あり |
| `total-finite-nonnegative` | freeze `:1272-1279` | あり |
| `budget-keys` | freeze `:1267-1269` | あり。外側 key 集合は変えていない |
| `holdout-exact-set` | freeze `:1280-1283` | あり。ただし所見 3 の mutation-location 問題あり |
| `per-holdout-finite-nonnegative` | freeze `:1284-1293` | あり |

**所見 3: MU-3 は登録された位置に判定点がなく、現状のままでは再現可能な変異ではない**

- 種別: must-fix
- 根拠: `stage4-adjudication.md:128,133-134`、`tools/s8b_budget_approval_preflight.py:209-213`、`orchestrator/campaign/s8b_holdout_freeze.py:1267-1283`
- 反証条件: tool 内の exact な差分、例えば `holdout_ids` を candidate 側の部分集合へ差し替える変異を明記し、その変異だけで `[holdout-exact-set]` が赤になることを示すこと。
- 成果物影響: verify 内に集合比較はなく、既存 production の `_validate_budget` へ委譲している。同関数の比較を緩めれば loader も同時に弱まり、親が登録対象外とした「`_validate_budget` 側の holdout 検査」そのものになる。現記述では MU-3 の KILLED 証拠を一意に再現できない。

**所見 4: linked-leaf 拒否は `O_EXCL` と leaf `O_NOFOLLOW` に過剰決定されている**

- 種別: must-fix
- 根拠: `orchestrator/tests/test_s8b_budget_approval_preflight.py:165-199`、`tools/s8b_budget_approval_preflight.py:66-80,111-116`
- 反証条件: leaf 側の `O_NOFOLLOW` だけを除去して現 node が赤になること、または leaf の唯一の gate は `O_EXCL` であると契約を限定すること。
- 成果物影響: 現 node では leaf `O_NOFOLLOW` を消しても symlink は `O_CREAT|O_EXCL` により `EEXIST` で拒否される。leaf nofollow 防護の消失をテスト結果から検出できない。

4 拒否の帰属は以下である。

- repo 内: `_is_within`、tool `:100-103`。独立。
- 既存 regular leaf: `O_EXCL`、tool `:111-116`。独立。
- symlink parent: `_open_parent_nofollow` の component `O_NOFOLLOW`、tool `:68-80`。独立。
- symlink leaf: `O_EXCL` と leaf `O_NOFOLLOW` の双方。独立でない。

**所見 5: verify の無変更検査は candidate と repo しか見ず、一般の「file を書かない」を固定していない**

- 種別: must-fix
- 根拠: `stage4-adjudication.md:80-81,99`、`orchestrator/tests/test_s8b_budget_approval_preflight.py:208-241`
- 反証条件: `candidate.with_suffix(".verified")` のような sidecar write 変異を入れて赤になること。`tmp_path` 全体の snapshot または write API の spy で検査できる。
- 成果物影響: candidate と monkeypatch 済み repo を一切変えず、その隣へ新規 file を作る verify は現在の 17 node を通過し得る。read-only tool という成果物契約を満たさない。

**所見 6: preflight と production loader の受理集合が同一であることを接続していない**

- 種別: must-fix
- 根拠: tool の複製実装 `tools/s8b_budget_approval_preflight.py:184-214`、loader `orchestrator/campaign/s8b_holdout_freeze.py:1307-1339`、tool 正負例 `orchestrator/tests/test_s8b_budget_approval_preflight.py:208-307`、loader を呼ぶのは過剰決定済み N2 `:147-162` のみ
- 反証条件: 同じ canonical candidate と matching hash を tool と `_load_budget_approval` の双方へ渡す differential test があり、各単一違反について受理、拒否、理由が一致すること。
- 成果物影響: loader に条件が追加または変更されても preflight が古い受理集合を維持できる。ユーザーへ表示した pin が production では通らない状態を焦点走が検出できない。予定中の `test_s8b_holdout_freeze.py` はこの differential 接続を持たない。

**所見 7: 予定された焦点走は repo-wide Python consumer を取りこぼしている**

- 種別: must-fix
- 根拠: `orchestrator/tests/test_campaign_import_invariant.py:1001-1049`、`test_check_subprocess_bytecode_guard.py:223-224` と `tools/check_subprocess_bytecode_guard.py:64-74,339-370`、`test_campaign.py:4641,5128-5169`、`test_login_headroom.py:1602-1643`、`test_t338_submission_gate_unit5.py:490-515`、`test_p3_build_authority_cli.py:194-210,630-668`
- 反証条件: 下記 node を焦点走へ加えるか、それぞれの列挙が変更 file を除外することを参照関係で示すこと。
- 成果物影響: 新規 Python file の parse、import namespace、subprocess、authority call-site、定数 census の回帰が、提示された 3 file 走だけでは未検査になる。

## MU 対応表

| MU | 赤になる exact nodeid |
|---|---|
| MU-1 | `orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_rejects_noncanonical_bytes` |
| MU-2 | `orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_rejects_each_approval_contract_violation[scope]` |
| MU-3 | 登録文どおりでは `none`。tool 内に比較がない。call-site の部分集合差し替えへ具体化した場合のみ `orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_rejects_each_approval_contract_violation[holdout-exact-set]` |
| MU-4 | `orchestrator/tests/test_s8b_budget_approval_preflight.py::test_skeleton_rejects_repo_existing_leaf_and_symlink_traversal` |
| MU-5 | `orchestrator/tests/test_s8b_budget_approval_preflight.py::test_n1_has_no_approver_input_source_and_skeleton_has_no_authority_values` |
| MU-6 | 成功後に canonical path へ書く変異なら `orchestrator/tests/test_s8b_budget_approval_preflight.py::test_verify_success_prints_hash_and_pin_and_changes_no_repo_bytes` |

N2 は `orchestrator/tests/test_s8b_budget_approval_preflight.py:147-162` で明示的に contract test とされ、MU gate には数えられていない。この扱いは親裁定と一致する。

## 焦点走に足すべき対象

最低限、次の exact node を足すべきである。

- `orchestrator/tests/test_campaign_import_invariant.py::test_real_repository_legacy_namespace_matches_exception_ledger`  
  `:1001-1049` で tracked と untracked の Python を parse する。

- `orchestrator/tests/test_check_subprocess_bytecode_guard.py::test_real_repo_clean`  
  checker `:64-74,339-370` が `orchestrator/` と `tools/` の全 Python を parse する。

- `orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`  
  `:5128-5169` で tests を除く repo-wide Python を parse するため、新規 tool が母集合に入る。

- `orchestrator/tests/test_login_headroom.py::test_ceiling_numeric_literal_occurs_only_in_login_headroom_module`  
  `:1602-1622` で tracked と untracked の全 file を読む。

- `orchestrator/tests/test_login_headroom.py::test_local_budget_constants_are_defined_only_in_login_headroom_leaf`  
  `:1625-1643` で `orchestrator/` と `tools/` の Python を parse する。

- `orchestrator/tests/test_t338_submission_gate_unit5.py::test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink`  
  `:490-515` で tests を除く repo 全 Python を parse する。

- `orchestrator/tests/test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact`  
  `:194-210,630-668`。新規 file が index または commit に入った後でなければ母集合へ入らない。

追加的な参照関係は次のとおり。

- `orchestrator/tests/test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact` は `:508-535,855-859` で新規 tool を読むが、現 source に perf marker がないため AST parse は省略される。
- `orchestrator/tests/test_calibration_freeze_stage6_candidate_gate.py::test_stage6_candidate_gate_caller_inventory_matches_repository_and_docs` は `:119-127,375-403` で新規 tool を列挙するが、対象 predicate がないため parse は省略される。
- `orchestrator/tests/test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests` は `:423-433` で新規 test filename を列挙するが、現在の名前は filter 外。
- `orchestrator/tests/test_skip_classification.py::test_readme_conditional_unrun_census_names_all_nodes` は `:315-324` で `orchestrator/tests/README.md` を読む。ただし allowlist 節ではなく後段の「条件付き未実走」節だけを検査する。
- `tools/check_docs.py:128-169` の `LIVING_DOCS` に `orchestrator/tests/README.md` はなく、docs checker は今回の allowlist edit の gate ではない。
- 予定済み `test_plain_runner_coverage.py` は `:44-86` で allowlist と新規 test file を直接照合するため適切。
- 予定済み `test_s8b_holdout_freeze.py` は changed file の直接 consumer ではなく、production loader の基準確認に留まる。

## 総括

- 停止級はないが、検査証拠としては must-fix が残る。
- 9 param のうち 8 件は一つの判定へ帰属し、JSON parse や canonical 比較の先取りもない。
- timestamp だけは parser と canonical 再整形比較で過剰決定されている。
- N1 の AST denylist は具体的に迂回可能で、承認者流入の gate として弱い。
- N2 は過剰決定済み contract test と明記され、実効 gate には数えられていない。
- skeleton の repo、既存 leaf、symlink parent は独立だが、symlink leaf は二重拒否である。
- MU-1、2、4、5、6 は各一 node に帰属する。MU-3 は変異位置の具体化が必要である。
- fixture に approval の現行 pin hashは差し込まれておらず、時刻や pid の揮発値も期待値へ固定していない。
- 既存テスト期待値の変更は README allowlist 1 行だけで、production loader の受理集合も変更していない。
- このレビューでは pytest を実走しておらず、親提示の `17 passed` は十分性の根拠に用いていない。