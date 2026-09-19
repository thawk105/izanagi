# scanner fix1 — 親の実データ所見と修正要求

親が wave worktree (a99425b66) で scanner を実走し (rc=0、20 秒、子の out/ と md が byte 一致)、record を読んだ。

## 所見 1 (must-fix): (A) `path-missing` の大半は test が tmp に作る合成 fixture の path

例: `test_audit_dangling_commits.py::test_positive_control_deleted_branch_work_is_reported` の
`tools/lost_implementation.py` (合成 repo に書く file)、`test_artifact_admission.py::test_unknown_t733_exact62_grammar_is_rejected_for_both_read_purposes` の
`orchestrator/campaign/unknown_t2483.py` (拒否の負例)。file 別では test_audit_dangling_commits 64 件、test_dev_wave_land 47 件、
test_ccbench_spawn_sites 35 件、test_ruleops 31 件、test_spool_fold 28 件で、いずれも合成 repo / 拒否負例の literal。
これらは「対象不在」ではない。

要求: (A) の `path-missing` / `flag-missing` / `docs-heading-missing` を出す関数のうち、次のいずれかの
合成指標を持つものは (A) から外し、record の `suppressed` に `synthetic-fixture` 理由付きで残す (summary にも件数)。
- 引数に `tmp_path`, `tmp_path_factory`, `tmpdir`, `pytester`, `testdir`, `monkeypatch` のいずれかを持つ
- 本文に `tempfile`, `mkdtemp`, `TemporaryDirectory`, `ScratchTree`, `write_text`, `write_bytes`, `mkdir`, `pytester.` のいずれかの名前が現れる
- literal が `pytest.raises` の `with` block 内、または `match=` / `assert ... in` の message 比較にだけ現れる
残った (A) は「対象が repo 実体を指すのに不在」の見込みが高いものだけになる。抑制で (A) が 0 件に近づいても構わない (それが事実)。

## 所見 2 (must-fix): (B) `identical-body` が decorator を無視している

`fingerprint()` は `fn.args` と本文だけを hash しており、`@pytest.mark.parametrize` の値が違う関数同士
(例: `test_schema_v2.py::test_acquisition_receipt_rejects_each_bad_field` と `test_attestation_profile_rejects_each_bad_field`) が
同一 group になる。これらは別の受理集合を検査しているので (B) ではない。

要求: fingerprint に decorator_list を含める (lineno 等の位置属性は落とす。`ast.dump(..., include_attributes=False)` で可)。
kind 名は `identical-body-and-decorators` にする。decorator 抜きの一致は (B) に数えず、record の `notes` に
`identical-body-only` として peer を残す (集計には含めない)。

## 所見 3 (should): 変異 proof の対象 module を引くための `production_targets`

各 record に `production_targets` を足す: その test file の module-level import (`import x` / `from x import y`) のうち
repo 内 (`orchestrator.`, `tools.`, `hooks.` またはそれらの相対 path) を指すものについて、関数本文で参照されている名前
(module alias の属性参照、または from-import した名前) に対応する module の repo-relative path の list。
不明なら空 list。summary に「(A)(B)(C) 候補 (protected 除く) の production_targets 別件数」を足す。

## 所見 4 (should): Markdown に group 単位の一覧を足す

- (B1) group ごとに member 全部 (file:line qualname、protected、referenced_by の有無、台帳秒) を 1 表。
- (B2) 重複 row の一覧 (file:decorator 行、row 位置、値 repr)。
- (C) 全件。
- (D) を pin 先 (docs path または定数名) 別に件数・行数・台帳秒で集計した表 (上位 30)。

## 所見 5 (nit): `unresolved` 5,215 件は summary に種別内訳を出す

`unevaluable-parametrize-row` など kind 別の件数だけで良い。
