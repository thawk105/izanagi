# [T-1421]/[T-1384] C06 (budget consumer) の machine_checkable 昇格

## 要約

8c 事前登録条件6 (budget consumer) を D529 手順 (契約 JSON `machine_checkable` 反転・
`_MACHINE_EVALUATORS` registry 登録・`DECIDER_VERSION` v5→v6 bump・第10世代
condition-freeze record 発行を不可分の1commit) で machine_checkable へ昇格した。
T-1355 (C07→v4)・T-1379 (C05→v5) と同型の昇格。実装 commit `2b19d26b`。

昇格後も C06 は `SATISFIABLE_CONDITION_IDS` が空集合のため `SATISFIED` を返さず、
`UNSATISFIED`/`EVIDENCE_UNDEFINED` のいずれかに留まる (発効しない)。8c 事前登録は本 wave 後、
12条件中 10条件が machine_checkable (残る C03/C08 は staged 未着手、T-1422 が調査中)。

## 段別成果

- **段1 brief**: `verbatim/s1-brief.md` (専用handoff全文、段1〜段9の生きた記録を含む)。
- **段2 codex plan** (read-only, rc=0): `verbatim/s2-plan.md`。新世代 condition-freeze record の
  実体 (`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g10.json`、
  `prepare-revision` CLI) を特定。`_MACHINE_EVALUATORS` の定義順序移動が必須と指摘。
- **段3 敵対相談2レンズ** (read-only, 両方 rc=0): `verbatim/s3-lensA.md` (正しさ境界・整合性、
  blocker 0)、`verbatim/s3-lensB.md` (実効性・regulation2、blocker 1件)。
- **段4 親裁定**: lensB blocker (過去commitのreason code遷移) を親が `evaluate_all`/
  `_evaluate_undefined` を直接読んで検証し refuted と裁定 ({{D:c06-past-commit-reason-drift-is-precedented}}
  参照、fold後は実番号)。reachability検査の甘さは scope外・後続waveへ送ると裁定
  ({{D:c06-reachability-gap-deferred}})。変異 M1-M4 を事前登録。
- **段5 実装** (workspace-write, rc=0): `verbatim/s5-author.md`。diff は計画v2と file:line 単位で
  完全一致 (親が直接 `git diff` で確認)。
- **段6 敵対レビュー2本** (read-only, 両方 rc=0): `verbatim/s6-reviewA.md` (diff正確性、blocker 0、
  hash・g10 recordを独立再計算し一致確認)、`verbatim/s6-reviewB.md` (回帰・consumer網羅性、blocker 0、
  g10がuntrackedのため明示的git add必要と指摘)。

## 親が独自に発見・検証した事項 (git に入らない情報、詳細は worklog)

段5実装後、`orchestrator/tests/test_p3_autonomous_workload_trial.py`・
`orchestrator/tests/test_trial_registry.py` を含む consumer test 拡張焦点走で10件の追加redを発見。
`git stash` による安全なA/B検証 (2回、100%再現性) で自分の変更に起因すると確定し、根本原因を
`orchestrator/campaign/contract_loader_binding.py` の `capture_contract_loader_binding()` が
`CONTRACT_LOADER_RELATIVE_PATHS` (対象に `s8c_preregistration.py` を含む) の disk bytes と HEAD blob
の不一致を検出する commit前提の tripwire (`test_current_repository_snapshot_exactly_matches_head` と
同型) と特定した。統合commit (`2b19d26b`) 後、該当11nodeidを含む consumer sweep を再実走し
**1275 passed, 0 failed** で全解消を確認した。

## 変異 matrix

`mutation/mutation-spec.json`・`mutation/mutation-out.json`。baseline PASSED、
**4/4 KILLED、SURVIVED 0、MISMATCH 0**。

- M1: 契約 `machine_checkable: true→false` (13ノードで検出)
- M2: `_MACHINE_EVALUATORS` から `6: _evaluate_c06` 除去 (7ノードで検出)
- M3: `_c06_field_path_verdict` の行数一致検査 (`_c06_expected_rows(tree) != _C06_EXPECTED_CELL_ROWS`)
  を無効化 (2ノードで検出。当初の候補 (supervisor reachability の呼出集合検査) は SURVIVED し、
  reachability検査の甘さの実測証拠となったため、negative controlが直接検査する行数一致検査へ
  再照準した)
- M4: `DECIDER_VERSION` v6→v5 revert (3ノードで検出)

`test_s8c_preregistration_invariant.py` の3件の `@s8c-preregistration-candidate`
(xdist_group付き) node は、harness の期待node事前登録が「pytest collectionに実在しない」として
拒否したため `--deselect` で mutation run から除外した (いずれも他の検出nodeに対し redundant な
検出層、単一理由性に影響なし。詳細は worklog 次の一手 `{{T:mutation-worktree-xdist-group-node-registration-gap}}`)。

## 一次資料

- 実装 commit: `2b19d26b` (branch `worktree-dev-wave-t1421-c06-machine-checkable-promotion`)
- D529 (`docs/decisions.md`)、D533
- テンプレート commit: `9f89da3d` ([T-1379] C05→v5)、`73b66eca` ([T-1355] C07→v4)
