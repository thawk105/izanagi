## 変更 1: `orchestrator/campaign/s8b_oracle_report.py`

- 現在の `main()` 2547 行で `ratified = ...load_ratified_freeze(root)` を得た直後、現 2548 行の `reverify_published_freeze` より前へ次を挿入する。

```python
s8b_ratified_freeze.assert_g1_floor_selection_identity(ratified, root)
```

- 挿入後は新 2548 行になる。`OfficialManifest` exact type の 2546 行分岐内なので、legacy report の受理経路は変えない。
- `RatifiedFreezeError` は現 2566 行ですでに catch 済み。型追加や別例外への包み替えは不要で、`str(exc)` の `[floor-selection-rule-mismatch] ...` を stderr に保持して rc=2 となる。
- report の source bytes が変わるため、`PIN_GATE_SPEC_RAW` の report hash と外側 hash を再 pin する。

## 変更 2: `orchestrator/tests/test_s8b_oracle_report.py`

- 現 32–46 行の campaign import 群へ `s8b_holdout_freeze as holdout_freeze` を追加する。既存の `ratified_fixture` import は現 30 行を使う。
- CLI テスト群が始まる現 1658 行の直前に、実 g1 の選択違反を作る file-local helper を置く。選択済み `result.json` の固定 run id `20260718T120000Z` を `20260718T115959Z` に変えた earlier copy を作り、`ratified_fixture._commit_exact`（`test_s8b_ratified_freeze.py:286`）でその 1 file だけ commit する。
- helper は `holdout_freeze._derive_floor_selection_eligibility` だけを「earlier_rel のみ True」へ差し替える。強制本体 `assert_g1_floor_selection_identity` は差し替えない。
- 現 `test_cli_official_resolves_ratified_freeze_and_verifies`（1658–1730 行）は、実強制を `wraps` した spy と reverify spy の順序を追加確認し、正常 g1 が強制を通過する正例にする。
- 同テスト直後へ report の負例と引数同一性テストを追加する。既存 helper `_ratified_cli_manifest` の signature・戻り値は変えず、judge/verdict 側との共有依存を安定させる。

## 変更 3: `orchestrator/campaign/s8b_oracle_judge.py`

- 現 749 行の `load_ratified_freeze(root)` の直後、新 750 行として同じ強制を挿入し、現 750 行の historical reverify より前に置く。

```python
s8b_ratified_freeze.assert_g1_floor_selection_identity(ratified, root)
```

- judge は現 743–747 行で official manifest exact type を要求済みなので、公式判定経路すべてが対象になる。
- `RatifiedFreezeError` は現 767 行ですでに catch 済み。catch 型追加は不要で、理由を stderr に保持して rc=2 にする。
- judge の source bytes も `_GENERATOR_SOURCES` 対象なので再 pin が必要。

## 変更 4: `orchestrator/tests/test_s8b_oracle_judge.py`

- 現 21–26 行の import 部へ `s8b_holdout_freeze` と `test_s8b_ratified_freeze as ratified_fixture` を追加する。
- `_cli_observations` が終わる現 726 行と、CLI parameterized test が始まる現 729 行の間に、judge 専用の負例 helperと3テストを置く。
- 実 g1 と official manifest は `report_fixtures._ratified_cli_manifest`（report test 321–403 行）を使う。この helper は `load_emitter_g1` を経由して `build_production_emitter_g1` を使っている。
- report test 側の helper は編集せず、earlier result の作成処理も judge test 内へ閉じる。これにより R/J の編集 path と helper 所有は衝突しない。

## 変更 5: `orchestrator/campaign/s8b_verdict.py`

- 現 828 行の `load_ratified_freeze(root)` の直後、新 829 行として強制を挿入し、現 829 行の historical reverify より前に置く。

```python
s8b_ratified_freeze.assert_g1_floor_selection_identity(ratified, root)
```

- 外部 `--freeze` の byte/hash load は現 826 行で従来どおり先に行う。その後、active ratified g1 の選択 identity を強制してから manifest・prediction・oracle の各 consumer へ進む。
- `RatifiedFreezeError` は現 871 行ですでに catch 済み。catch 型追加は不要。
- `s8b_verdict.py` は `s8b_oracle_manifest.py:65–73` の `_GENERATOR_SOURCES` に無く、現 source sha256 の repo 内 literal pin も静的検索で 0 件だった。P2どおり再 pin 対象にしない。

## 変更 6: `orchestrator/tests/test_s8b_verdict.py`

- 現 23–34 行の import 部へ `s8b_holdout_freeze` と `test_s8b_ratified_freeze as ratified_fixture` を追加する。
- CLI 節の `_write_json` 後、現 998 行付近へ verdict 専用の earlier-result helper、負例、正例を置く。負例では `build_production_emitter_g1` の実 generation path と sha256 をそのまま `--freeze` / `--freeze-sha256` に渡し、pre-gate loaderも実体を使う。
- 現 `test_cli_preserves_freeze_and_floor_source_wiring`（1016 行）では gate collector を追加し、`ratified` object の同一性、root、呼出順を照合する。期待順は `freeze, ratified, selection, reverify, ...` に更新する。
- synthetic `object()` を active freeze としている次の既存テストは、選択強制を no-op seam に明示的に差し替えて本来の検査点まで到達させる。
  - `test_cli_rejects_non_verdict_oracle_schema_without_output`（1131 行）
  - `test_cli_rejects_freeze_identity_mismatch_before_consumers`（1195 行）
- この no-op は既存テストの直交した目的を保つためだけに使い、新しい負例では絶対に使わない。

## 変更 7: `orchestrator/tests/test_s8b_oracle_manifest.py`

- `PIN_GATE_SPEC_RAW` 内の judge hash（現 86–87 行）と report hash（現 92–93 行）を、実 file bytes から再計算した値へ置換する。
- その変更後の `PIN_GATE_SPEC_RAW` 全体の sha256 を計算し、`PIN_GATE_SPEC_SHA256`（現 63–65 行）を置換する。
- canonical raw bytes、固定 literal、末尾 LF 無しという golden の性質は維持する。live hash 計算へ置き換えるなど、テストを自己追随させる変更はしない。

## テスト設計

| 経路 | 負例 | 正例 | 呼び出し引数・同一性 |
|---|---|---|---|
| report | 新規 `test_report_cli_real_g1_rule_mismatch_preserves_selection_reason`、現 1730 行直後 | 現 1658 行の `test_cli_official_resolves_ratified_freeze_and_verifies` を拡張 | 新規 `test_report_cli_selection_gate_receives_loaded_ratified_and_root`、負例の隣 |
| judge | 新規 `test_judge_cli_real_g1_rule_mismatch_preserves_selection_reason`、現 726 行直後 | 新規 `test_judge_cli_valid_real_g1_reaches_reverify_after_actual_selection_gate`、同 CLI 群 | 新規 `test_judge_cli_selection_gate_receives_loaded_ratified_and_root`、同 CLI 群 |
| verdict | 新規 `test_verdict_cli_real_g1_rule_mismatch_preserves_selection_reason`、現 998 行付近 | 新規 `test_verdict_cli_valid_real_g1_reaches_reverify_after_actual_selection_gate`、同位置 | 現 1016 行の wiring test を拡張 |

負例の共通骨子は次のとおり。

- `build_production_emitter_g1`（966–1196 行）が `tmp_path/repo` に独立 git repo、production-shaped g1、承認、active pointer を作る。実 repo からは v1 trust rootを読むだけで、書込み先、git操作、artifact はすべて `tmp_path` 内で完結する。build/measure は固定 seam で、性能測定は走らない。
- 固定された選択済み 12:00 の result bytes を 11:59 の official path へ複製し、その path のみ `_commit_exact` で追加する。
- manifest 先例 1499–1540 行と同じく、eligibility 導出だけを earlier=True、selected以外=False とする。実 `assert_g1_floor_selection_identity` が `earliest-eligible-official-run-id/v1` 違反を検出する。
- 各 `main()` が rc=2、出力未作成、stderr に `floor-selection-rule-mismatch` を保持し、eligibility call が earlier path に対して実行されたことを確認する。

正例は、無変異の実 g1 に対して強制関数を `wraps` し、実強制が正常終了した後に `reverify_published_freeze` へ到達したことを spy で確認する。report/judge は有効な manifest と input で rc=0・出力作成まで確認する。verdict は実 `--freeze` load と実選択強制を通した後、意図的な downstream sentinel を reverify から返して到達を確認する。

引数照合は先例 1350–1365、1419–1438 行と同じ collector 形にし、`selection_calls == [(loaded_ratified, root)]` を確認する。さらに `selection_calls[0][0] is loaded_ratified` と Path の完全一致を明示し、順序逆転や再 load した別 object を許さない。

## 再 pin 手順

1. R/J の source 編集が確定した後、`Path(...).read_bytes()` に対する sha256 を report と judge それぞれ再計算する。
2. 得た report 値を `PIN_GATE_SPEC_RAW` 現 93 行、judge 値を現 87 行の既存64桁 literalへ置換する。path、key順、compact JSON、その他の bytes は変更しない。
3. 更新後の Python source を AST parseし、`PIN_GATE_SPEC_RAW` 代入の bytes literalを `ast.literal_eval` で取り出す。その bytes の sha256 を再計算し、現 64 行の `PIN_GATE_SPEC_SHA256` に置換する。
4. 最終静的照合として、raw JSON 内の report/judge hashが各実 file hashと等しく、`sha256(PIN_GATE_SPEC_RAW)` が外側 literalと等しいことを独立に再確認する。
5. `PIN_GATE_SCHEDULE_SHA256`、`APPROVED_SPEC_SHA256`、schema、canonicality検査は変更しない。

## 分割案

- R: `s8b_oracle_report.py` と `test_s8b_oracle_report.py`
- J: `s8b_oracle_judge.py` と `test_s8b_oracle_judge.py`
- V: `s8b_verdict.py` と `test_s8b_verdict.py`
- P: `test_s8b_oracle_manifest.py` の再 pinのみ。R/J の最終 source bytes が揃ってから開始する。

4単位の編集 path は素集合である。J/V は report test の `_ratified_cli_manifest` を importするが、本案ではその helper の signature・実装を変更しない。負例 helper は各 test file 内に個別配置し、共有 `test_s8b_ratified_freeze.py` と `s8b_holdout_freeze.py` は読み取り利用だけにするため、共有 helper の同時編集衝突もない。

V は P に依存せず並行可能。P だけが R/J に順序依存する。worklog は canonical `docs/worklog.md` を直接編集せず、親統合側が実走結果確定後に spool fragment 1件として直列処理し、D1526 実装完了を記録する。新しい decision は作らない。

## 受理集合の変化

新たに拒否されるのは、active freeze が g1 で、従来の load/historical reverify は通るが床値選択 identity を満たさない公式入力である。具体例は、g1 が 12:00 の resultを `floor_source` に選んでいる一方、11:59 に導出上 eligible な official resultが存在する入力で、report/judge/verdict の3 CLIすべてが `floor-selection-rule-mismatch` で拒否する。選択入力が導出不能なら `floor-selection-eligibility-underivable`、protocol/path/env chainを再構成できなければ `floor-selection-unverifiable` で同様に拒否する。

拒否されないままなのは次の入力である。

- 選択済み result が最古の eligible official runである正常 g1。
- `generation_number != 1` の ratified freeze。exact `RatifiedFreeze` 型検査後、強制関数は 3591–3592 行でそのまま returnする。
- report の legacy manifest経路。2546 行の official exact-type分岐へ入らない。
- P1どおり `verify_manifest` を直接呼ぶ consumer。signatureや選択 token要求は変えない。
- `build_manifest` / `write_manifest` の公開迂回口、母集合、導出被覆、advisory上限は本変更では変えない。

## 波及の静的列挙

report `main()` の呼び手は次のとおり。

- `test_s8b_oracle_report.py`: 1658、1733、1752、1777、1820、1848、1866、1904、1931（subprocess `-m`）、1976、2213、2398、4204 行の各テスト。
- `test_s8b_oracle_driver.py:4227`: `test_transient_prepare_failure_retries_once`。
- 公式入力を使う上記テストは `_ratified_cli_manifest` または `_build_v2_repo` の production-emitter実 g1を使うため、選択規則を満たす。legacy/exploration入力は gate前の分岐・型拒否なので影響しない。

judge `main()` の呼び手は次のとおり。

- `test_s8b_oracle_report.py:1879,1895` の `test_judge_cli_reverifies_official_manifest_and_legacy_cannot_reach_verdict`。
- `test_s8b_oracle_judge.py:751,756` の `test_judge_cli_rejects_non_observations_schema_without_output`。
- いずれも公式側は `_ratified_cli_manifest` の実 g1であり、新強制を通過する。

verdict `main()` の呼び手は `test_s8b_verdict.py` のみで、1006、1013、1105、1169、1185、1222 行。`tools/`、`scripts/`、production moduleから3つの `main()` を直接呼ぶ箇所は静的検索上0件である。

既存のままでは明確に赤くなるテストは次の3つ。

- `test_s8b_verdict.py::test_cli_preserves_freeze_and_floor_source_wiring`: synthetic `object()` が実 gateの exact型検査で拒否され、期待 rc=0を満たさない。
- `test_s8b_oracle_manifest.py::test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`: 古い report/judge hashで source照合に失敗する。
- `test_s8b_oracle_manifest.py::test_build_approved_valid_fixture_output_depends_only_on_spec_pin`: pin有効側が古い generator hashで失敗する。

さらに verdict の non-verdict-schema test と freeze-identity-mismatch testは、補修しなくても rc=2のため表面的には緑のままだが、実 gateが先に拒否して本来の検査点へ届かない。変更6の no-op seam追加で、この偽陽性を防ぐ。source構造を読む `test_official_perf_closure.py`、`test_s8b_oracle_manifest_contract.py`、`test_s8b_oracle_artifacts.py` の期待集合・対象関数は変わらない。

## 総括

- 3つの `main()` すべてで load直後、historical reverify前に同じ選択強制を入れる。
- 既存 catch が `RatifiedFreezeError` を処理するため、例外型追加は不要。
- 各経路を実 g1負例、実強制の正例、引数・object同一性で固定する。
- report/judge の実 source hashと、その raw blob hashだけを literal再 pinする。
- pytestは指示どおり未実行であり、本プランは指定 worktree内の静的検査に基づく。