## 総括

**限定実装済み・未実走です。closedにはしません。** テストは `tools/run_tests.py` が `qstat -Q preflight rc=1`／終了コード16で停止し、子プロセス未起動でした。緑のnodeはありません。

変更は4ファイル、production追加62行、test/meta追加269行で上限内です。

- [s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2527-author/orchestrator/campaign/s1_known_axes_freeze.py:864)：既存rootによる旧文書識別、`historical=False` API、CLIの歴史閲覧、6種のsource SHAだけを補正した現行全文照合。
- [test_s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2527-author/orchestrator/tests/test_s1_known_axes_freeze.py:908)：12テスト追加。
- [conftest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2527-author/orchestrator/tests/conftest.py)：実repo／ccbench reader 11 node登録。
- [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2527-author/orchestrator/tests/test_real_repo_serialization.py)：対応する既存meta登録11件。

旧artifact・判定・hold・独立golden・consumer本体は変更していません。stage／commit操作もありません。

**確認状況**

変更前CLIのgenerator SHA不一致拒否を確認しました。変更後4ファイルのAST解析と `git diff --check` は成功しています。

ランナーへ指定した未実走範囲は、known-axes、measurement、calibration、oracle、real-repo serialization、plain runner coverage、freeze hold、growth hold contract、hold inventory、T-080の各テストファイル全体です。新設nodeに伴う分類・共有fixture閉包・自走runner・hold契約を棚卸し対象に含めました。親の全走やcheckerを代替しません。

実物閲覧の正例と、**実builderを呼んだ後の単一差分注入**は別テストです。どちらも今回は未実走であり、成功証拠とは報告しません。

**所有外への波及**

- measurementの `_verify_known_axes`、calibrationの `validated_target`、oracle非adapter経路は既定の現行意味照合を維持。
- direct comparisonはmeasurement経由の間接consumer。
- measurement共有fixture `real_known_axes_doc` の実生成→golden→実検証は不変。
- holdoutの入力束縛・variant照合、T-080のbuilder／schema／pairing参照は不変。
- plain runnerは既存の関数自動列挙と `tmp_path` 供給で追加nodeを扱うため変更不要。

**変異anchorと投入予定node集合**

以下の `N(x)` は完全nodeid
`orchestrator/tests/test_s1_known_axes_freeze.py::test_historical_` ＋ `x`
を表します。各行がその変異への投入予定全集合です。変異本走は未実施です。

| 変異 | old → new anchor | node集合 |
|---|---|---|
| M1 | `if not known_historical and generator_doc["sha256"] != actual_generator:` → `if generator_doc["sha256"] != actual_generator:` | `{N(real_artifact_is_readable)}` |
| M2 | `known_historical = hashlib.sha256(raw).hexdigest() == KNOWN_AXES_RAW_SHA256` → `known_historical = True` | `{N(content_and_identifiers_are_bound)}` |
| M3 | `if actual != expected and not (known_historical and path_rel in _HISTORICAL_CODE_PATHS):` → `if actual != expected and not known_historical:` | `{N(input_copy_sha_and_existence_remain_bound)}` |
| M4 | `if doc != expected_doc:` → `if not known_historical and doc != expected_doc:` | `{N(current_use_rejects_single_flags_difference)}` |
| M5 | `current["sha256"] = recorded["sha256"]` → `current.clear(); current.update(recorded)` | `{N(current_use_preserves_source_key_comparison)}` |
| M6 measurement | `known_axes.verify_document(doc, source_resolver=source_resolver)` → 同呼出しへ `historical=True` 追加 | `{N(measurement_and_calibration_keep_current_semantics)}` |
| M6 calibration | `verifier = verify_fn or s1_known_axes_freeze.verify_document` → `verifier = verify_fn or (lambda doc: s1_known_axes_freeze.verify_document(doc, historical=True))` | `{N(measurement_and_calibration_keep_current_semantics)}` |
| M6 oracle | `s1_known_axes_freeze.verify(known_path, source_resolver=lambda relative: root / relative)` の複数行呼出しへ `historical=True` 追加 | `{N(oracle_nonadapter_reaches_current_semantics)}` |

**残所見:** oracleテストは非adapter経路への到達と、known-axes拒否理由の単一追加を検査します。旧holdout由来の別拒否が残るため、oracle全体の可否を単独反転させるkillとは主張しません。旧識別子改変の拒否も、非コード入力SHA検査のkillとは区別しています。
