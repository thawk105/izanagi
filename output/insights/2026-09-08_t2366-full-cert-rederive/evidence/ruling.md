# [T-2366] 段 4 裁定 — plan v2 と変異事前登録

裁定日時: 2026-09-08 07:50 JST。裁定 inbox 再走査: wave 開始後に main へ着地した D1792〜D1794 は受入 shard 観測 field の話で本 wave に触れない。対象 2 file は main 側で不変。

## 所見の裁定

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| 1 | A1 / B1 | plan の「identity/schema 検査を canonical evidence へ一括切替」は、渡された evidence の改竄 (attempt_id / acquisition_schema / acquisition_path だけの dict) を読み直しで**置換**して通すため、入力受理集合が広がる | real | 採用。既存の identity / schema chain / request_ids / 固定 field / cells 検査は**渡された evidence に対して据え置き**、それらの後に v4 だけ読み直し・再導出比較を足す |
| 2 | A2 | `_canonical_full_report` に `_require_materializable_authority` が無く partial canonicalizer と総関数が違う。brief の「manifest 無効 → indeterminate」は authority gate 後にしか到達しない | real | 採用。helper 冒頭に `_require_materializable_authority(policy, evidence)` を置く (partial 2865 と同型)。brief の記述は本裁定で訂正 |
| 3 | A3 | 読み直しを cells 検査より前に置くと例外契約 (どのエラーが先に出るか) が変わる | real (受理集合は不変) | 採用。読み直しは既存 full 検査 (structural / identity / schema / request / 固定 field / cells / historical) を**すべて終えた後** |
| 4 | A4 | production `_collect_command` では同じ evidence から report を作るので `report == expected` は構成上ほぼ恒真。縮むのは `materialize` 直接呼出しの API 境界と、二回読みの間の disk 整合性 | real | 採用 (実装は変えない)。DW-G05 の説明を「importable materializer の直接呼出しと二回読み間の整合性」へ限定して記録する |
| 5 | A5 / B1 後半 | brief P4 の「食い違う bytes は sha で拒否される」は誤り。渡された bytes は authority にせず、読み直した canonical bytes を materialize する (拒否ではなく置換) | real | 採用。P4 を訂正。拒否要件は新設しない |
| 6 | A6 | `_COLLECT_TEST_TOKEN` inventory に 4088 が欠けている (影響結論は不変) | real (軽微) | 採用 (記録のみ) |
| 7 | B2 | 変異 old が partial 側と重複し一意に定まらない | real | 採用。full 側の局所名を `canonical_full_evidence` / `full_report_matches_rederived_evidence` に固定する |
| 8 | B3 | 新規 3 node の受入所要時間台帳 add-only 登録が plan の実行項目に無い | real | 採用 (親の段 7 項目。実装子は台帳を触らない) |

## plan v2 (実装の権威)

対象 file はこの 2 つだけ: `orchestrator/campaign/paper_story_a2_certification.py`、`orchestrator/tests/test_paper_story_a2_certification.py`。

1. `_indeterminate_report` の直後に `_canonical_full_report(policy, evidence, *, attempt_id, current_pin) -> dict` を新設する。本体は現行 `_collect_command` の full else 枝 (driver 非 0 → `_indeterminate_report`、`raw_manifest_valid` 偽 → `_indeterminate_report`、それ以外 → `collect_results` + `report["source_commit"] = evidence["source_commit"]`、`AuthorityError` 伝播、既存例外 tuple → `_indeterminate_report(reason=str(exc))`) を**逐語**で移す。冒頭に `_require_materializable_authority(policy, evidence)` を置く。`attempt_root` は `Path(evidence["attempt_root"])`。
2. `_collect_command` の full else 枝を `report = _canonical_full_report(policy, evidence, attempt_id=attempt_id, current_pin=args.current_pin)` の 1 呼出しへ置換する。attempt 照合と既存の `_require_materializable_authority` 呼出しはそのまま残す。
3. `_validate_certification_result` の full/legacy 枝は、既存の全検査 (4437〜4525 相当) を渡された `evidence` に対して**そのまま**残す。最後の `return evidence` の直前に、`report_schema == CERTIFICATION_SCHEMA` の場合だけ次を足す:
   - `acquisition_path = evidence.get("acquisition_path")` が `str` でなければ `CertificationError("certification materialization evidence lacks acquisition authority")`
   - `canonical_full_evidence = validate_acquisition_bundle(policy, acquisition_path, current_pin=report["current_pin"])`
   - `expected = _canonical_full_report(policy, canonical_full_evidence, attempt_id=canonical_full_evidence["attempt_id"], current_pin=report["current_pin"])`
   - `full_report_matches_rederived_evidence = report == expected`
   - `if not full_report_matches_rederived_evidence: raise CertificationError("certification result differs from evidence re-derivation")`
   - `return canonical_full_evidence`
   legacy v3 full は従来どおり `return evidence` (identity-only)。legacy v1 partial・v2 partial 枝は 1 byte も触らない。
4. `materialize` 本体、schema 識別子、report の形、成果物の形は変えない。
5. テスト (同 file 内、`_partial_materializer_forgery_case` の隣に `_full_materializer_forgery_case(tmp_path, attempt_id)` を新設: `_policy` + `preregister_attempt` + `_write_receipt_bundle(policy, root)` (全 driver 成功) + `validate_acquisition_bundle` + `_canonical_full_report` で正規 `observed-positive` report を作って返す)。負例 3 node、名前はこのとおり:
   - `test_full_materializer_rejects_forged_status_from_positive_evidence`: `status` を `"observed-positive"` → `"reject"`
   - `test_full_materializer_rejects_forged_effects_from_positive_evidence`: `effects[<最初の workload>]` を別の finite float へ
   - `test_full_materializer_rejects_indeterminate_report_from_full_success_acquisition`: disk は全 driver 成功のまま、渡す evidence dict の `driver_rcs[<最初の workload>]` を 7 に偽造し、それと整合する `_indeterminate_report(..., reason="compute driver exited nonzero: {'<workload>': 7}")` を渡す
   いずれも `pytest.raises(A2.CertificationError, match="differs from evidence re-derivation")` と `not (repo / policy.tracked_destination).exists()` を assert する。正例として `test_p2_a6_full_v3_path_collects_and_materializes` に `A2._canonical_full_report(policy, evidence, attempt_id=root.name, current_pin=CURRENT_PIN) == report` を 1 行足してよい (切り出し前後の同一性の明示)。
6. 既存 test の期待値は変えない。`test_synthetic_pbs_free_preregister_through_analyze_positive` が再導出差だけで赤になった場合に限り、report の構築を 2418 と同型 (`evidence["raw_results"]` + `frozen_files=evidence["raw_files"]` + `attempt_root=root`) へ寄せてよい。status / 成果物の期待は変えない。それでも赤なら実装の誤りとして止める。

## scope 外 (実装しない)

- legacy v3 full / v1 partial の再導出。図生成器・schema 版。渡された receipt bytes と disk の不一致を「拒否」する新要件 (所見 5)。`materialize` 直接呼出しの呼び手検査。受入台帳の編集 (親が段 7 で producer の `--add-only` で行う)。

## 変異事前登録 (DW-M01。逐語 old は実装後の最終 commit で DW-M07 に従い再検証して固定する)

| id | category | 置換 (意味) | 期待 | 期待 node |
|---|---|---|---|---|
| M01-rederive-removed | negative | `expected = _canonical_full_report(...)` → `expected = report` | KILLED | 新規負例 3 node |
| M02-reread-removed | negative | `canonical_full_evidence = validate_acquisition_bundle(...)` → `canonical_full_evidence = evidence` | KILLED | `test_full_materializer_rejects_indeterminate_report_from_full_success_acquisition` のみ |
| M03-always-reject | positive (過剰拒否の正例) | `if not full_report_matches_rederived_evidence:` → `if True:` | KILLED | 2418 / 5274 / 3331 / 3395 / 3431 / 3455 / 3477 / 3499 の 8 正例 (probe で確定) |
| M04-equivalent-swap | positive (等価) | `report == expected` → `expected == report` | SURVIVED | (空) |

M05 候補 (helper 冒頭の `_require_materializable_authority` を外す) は `_collect_command` と `materialize` の同名呼出しが冗長 gate になり単一理由性が無い (DW-M03) ため登録しない。本走は probe (全件 SURVIVED 登録で観測 node 収集) → final の 2 段、`--runner-mode dispatch`、runner argv は `python3 tools/run_tests.py orchestrator/tests/test_paper_story_a2_certification.py -q -rf --force-dispatch`。

## brief の訂正 (記録用)

- 行番号: full validator 終端 4526、evidence return 1804〜、synthetic 正例の定義 5274。`_COLLECT_TEST_TOKEN` test は 7 件 (4088 を含む)。
- 「manifest 無効 → indeterminate」は authority gate 後に到達可能な evidence に限る。
- P4: 渡された bytes は authority にせず、読み直した canonical bytes を materialize する (拒否ではなく置換)。
- DW-G05: production CLI では collector と validator が同じ evidence から導くのでほぼ恒真。縮むのは `materialize` を直接呼ぶ API 境界 (tests・将来の呼び手) と二回読みの間の disk 整合性である。
