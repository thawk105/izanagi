## 総括

- must-fix は 1 件。新 authority module が凍結 source closure に含まれず、land を止めるべき。
- production module の直接 caller 4 件は実装報告どおりだが、共有凍結物の consumer と内容走査テストの列挙は閉じていない。
- import 時の index 構築は裁定どおりで、既存 import invariant、collection、plain runner 契約との衝突は見つからない。
- 凍結 JSON の bytes は不変。known axes の記録 SHA も既存 manifest と一致する。
- generator SHA drift は着手前から存在し、本 wave が新しく緑を赤にしたものではない。
- 新規 10 node は duration ledger 未登録だが、未登録自体を赤にする契約ではない。
- pytest は実走していない。15 candidate の一意性と凍結 3 entry の binding は read-only import probe で確認した。

## S1

- `real` — 実装報告の波及列挙は全件ではない。ただし production module の直接 caller は閉じている。`s1_measurement_freeze.py:29`、`s1_verify_extime_calibration.py:43-45`、`s8b_oracle_driver.py:68`、`t080_freeze_migration.py:670,1683,2166,2180` の4件。
- `real` — 共有凍結物の未列挙 consumer がある。`s8b_holdout_freeze.py:826-855` は known axes を直接読み、その hash と entry を後段 freeze へ入れる。`s1_direct_comparison.py:183-191` は downstream の measurement freeze を読む。
- `real` — bytes consumer の未列挙は `test_frozen_artifacts.py:41-45,162-179`、`test_backoff_extended_sweep.py:751-765`、意味 consumer は `test_reflux_ir.py:541-556`、`test_s8b_oracle_manifest.py:755-766`。
- `real` — 実装報告に無い production source 内容走査は、`test_campaign.py:5128-5168`、`test_p3_s4_loop.py:1129-1141`、`test_p3_build_authority_cli.py:1191-1197`、`test_p3_exploration_namespace.py:124-140`、`test_p3_b4_analysis_path.py:303-309`、`test_reflux_ir.py:292-298`。
- `real` — さらに `test_s8b_floor_campaign.py:1588-1615,6364-6409`、`test_s8b_floor_stats.py:875-901`、`test_s8b_oracle_manifest_contract.py:39-50`、`test_s8b_oracle_report.py:5597-5617`、`test_t1286_commit_receipt.py:653-698`、`test_t338_submission_gate_unit5.py:490-515`、`test_official_perf_closure.py:508-535`、`test_calibration_freeze_stage6_candidate_gate.py:375-383` が新 file の本文を走査する。
- `refuted` — 上記走査が現在の新 module に反応する対象文字列や call site はない。列挙漏れは実装報告の不備だが、これ自体による既存 exact inventory の更新要求はない。
- `real` — authority 自身の source closure が欠落している。`s1_known_axes_freeze.py:515-516,564-565` は `s6_sort_sweep` と `S` を pin するが、`sort_comparator_authority.py` を pin しない。これは must-fix。

## S2

- `refuted` — 現在の import 副作用が既存契約を破るという所見。eager index は `sort_comparator_authority.py:54-56`、consumer の top-level import は `s1_known_axes_freeze.py:29` で、いずれも裁定どおり。
- `refuted` — `test_campaign_import_invariant.py` は production module を import せず、tracked/untracked source を読んで AST 検査する契約である。`test_campaign_import_invariant.py:1002-1045`。新 module の相対 import はこの契約に適合する。
- `refuted` — plain runner 検査は test file の harness 有無を調べるだけ。`test_plain_runner_coverage.py:44-74`。新 test は `test_sort_comparator_authority.py:51-52` に `pytest.main` harness を持つ。
- `refuted` — trigger の遅延衝突検査は trigger cache 固有である。`test_s1_known_axes_freeze.py:263-303`。sort authority の eager 構築とは契約が異なる。
- read-only probe では `s6_sort_sweep.py:143-157` の15 candidateについて name、implementation が各15件一意で、凍結済み `sp_dd`、`sk_ad` 3 entry も binding を通った。pytest collection 全体は未実走。

## S3

- `refuted` — 凍結 JSON bytes が差分で変わったという所見。`output/s1-freeze/known_axes_freeze.json` と `measurement_freeze.json` に差分はない。known axes の実 SHA は `354f4b...` で `test_frozen_artifacts.py:42-45` の pin と一致する。
- `refuted` — generator drift が本 wave で初めて発生したという所見。記録値は `known_axes_freeze.json:5-8` の `1d4d45...`、着手前 HEAD の generator は `a9edc1...`、現差分は `9cc9f8...`。着手前から不一致だった。
- `real` — generator 編集により、新規生成時の `/generator/sha256` はさらに変わる。`s1_known_axes_freeze.py:726-755`。ただし既存 path は `generate()` が上書きを拒む。`s1_known_axes_freeze.py:917-929`。
- `refuted` — verifier の新規先行赤。`_validate_schema` は generator 照合より先に走るが、凍結3 entryは現 authority に一致する。`s1_known_axes_freeze.py:818-867`。
- `real` — 新 authority の bytes は generator pinにも source loopにも含まれない。generator は自分自身だけを hash し、source loop は文書記録済み pathだけを照合する。`s1_known_axes_freeze.py:754,864-881`。descendant commitで authorityだけ変更しても凍結参照は変わらず、受理集合を変更できる。

## S4

- `refuted` — scope逸脱は差分にない。未 commit 差分は裁定された4 fileだけで、`sort_swo_oracle.py`、凍結 JSON、`test_frozen_artifacts.py` の `FROZEN_MANIFEST` は未変更。
- `refuted` — contract ID、保証境界、protocol versionへの変更はない。新 module の公開面は error と exact binding APIだけ。`sort_comparator_authority.py:9-12`。
- `refuted` — 独立 membership API、公開 mapping、stock `comparator=None` 特例、`STOCK_IMPL_NOTE` 拒否はない。private indexと `require_sort_name_comparator_binding` のみ。`sort_comparator_authority.py:25-65`。
- `refuted` — 既存テスト期待値の変更はない。`test_s1_known_axes_freeze.py:145-210` は新規 test の挿入だけ。
- `refuted` — 明示要求の欠落はない。生成2経路は `s1_known_axes_freeze.py:494-540`、schema検証は `:818-850`、error変換は `:87-94`、重複検出は `sort_comparator_authority.py:25-51`、正負テストは `test_sort_comparator_authority.py:16-48` と `test_s1_known_axes_freeze.py:145-210`。
- authority source pin の欠落は段4の明示項目外だが、凍結検証層の参照閉包として must-fix。

## S5

- `real` — 新規 nodeid は10件で、duration ledgerには全件未登録。`test_sort_comparator_authority.py:16-48` の5件と `test_s1_known_axes_freeze.py:145-210` の5件。台帳は `acceptance_duration_ledger.json:17643` で17639件。
- `refuted` — 未登録 node が loaderやschedulerを赤にするという所見。lookup missは `None` となり、unknown unitには既知 duration の既定順位が使われる。`conftest.py:1522-1542,1600-1614`。
- `判定不能` — 台帳未更新のまま90% coverage testが緑かは、live collection未実走のため断定しない。契約は exact coverageではなく90%以上。`test_acceptance_schedule_order.py:660-714`。したがって推測 duration を追加する必要はないが、全走後の実測更新は台帳品質の追随事項。
- `refuted` — 新 test file の収集契約違反。`pytest.ini:12-14` により収集対象で、self-run harnessもある。permanent exclusion検査でも filename に `verifier` / `oracle` を含まない。`test_pytest_collection_config.py:423-433`。
- 現時点で静的に見つかった受入赤候補は90% coverage境界と、must-fixの未凍結 authority sourceだけ。全走の赤なしは主張しない。

## S6

- `refuted` — module/API/helper名の不整合。裁定指定の `sort_comparator_authority`、`require_sort_name_comparator_binding` を使い、S1 helperも `_require_sort_name_comparator_binding` で既存 `_require_trigger_name_mask_binding` と同形。`sort_comparator_authority.py:1-12,59-65`、`s1_known_axes_freeze.py:87-94,164-186`。
- `refuted` — import-time 重複 error 型の不整合。両 index builder とも重複は `RuntimeError`。`trigger_gate_binding.py:85-95`、`sort_comparator_authority.py:43-48`。
- `real` — public rejection errorの基底だけは慣行と異なる。既存は `TriggerGateBindingError(Exception)`、新規は `SortComparatorAuthorityError(ValueError)`。`trigger_gate_binding.py:47-48`、`sort_comparator_authority.py:17-18`。明示 catchされ成果物には影響しないため nit。
- `refuted` — node名の非ASCII問題。追加10 test名はすべてASCIIで、追加箇所に parametrize はない。`test_sort_comparator_authority.py:16-48`、`test_s1_known_axes_freeze.py:145-210`。

## must-fix

- `MF-1 real` — `s1_known_axes_freeze.py:515-516,564-565,864-881` が `sort_comparator_authority.py` の bytesを凍結しないため、authorityだけを後続commitで変更すると凍結JSONと参照hashを変えずに文書の受理集合を変更できる。

## nit

- 実装報告の波及列挙は、共有凍結物 consumerとproduction-wide AST/content scanを多数落としている。
- `SortComparatorAuthorityError` の `ValueError` 継承は既存 trigger error の慣行と異なる。
- duration ledgerの10 node未登録は受入必須違反ではないが、全走実測後のscheduler台帳更新候補。