## 実装した差分

- [tools/dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/tools/dev_wave_wait.py)
  - `_red_check_payload_nodeids` を純粋関数として切り出した。
  - 非帰属 exact 3 field、`rerun_rc == 1` と、flake exact 5 field、3 rc 全て `0` だけを受理する。
  - bool、attributable、未知分類、field 過不足、不正 rc、空 nodeid を `_StageFailure` にする。
  - `red_nodeids` と `flake_nodeids` を別々に sorted・unique とし、重複を拒否する。
  - `_verify_runner_blob_identity` を追加し、全 `non-attributable-only` で request の tested main/tipを使って runner の blob type と SHA 等値を検査する。
  - `_RedCheckResult`、診断、outer receipt を2集合対応にし、schemaをv4へ更新した。
  - 変更前は red 非空だけが成立した。変更後は2集合の和が非空なら成立する。
  - child-green の受理条件は維持し、両集合を常に空配列で出す。

- [tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/tools/dev_wave_land.py)
  - exact outer schemaをv4へ更新し、`flake_nodeids` を必須 fieldにした。v3 fallbackはない。
  - child-green は両集合空、non-attributable-only は各集合の型、整列、一意性、相互排他、和集合非空を要求する。
  - 全 non-attributable-only について tested main/tipの runnerを `cat-file -t` と `rev-parse` で検査する。
  - `_AcceptanceVerification` から `LandResult.as_json()` まで flake集合を分離したまま伝搬する。
  - `acceptance_flake_nodeids` は既定値 `None` の keyword-only fieldとした。
  - D389の child rc、checker rc/status、checker receipt SHA、checker blob等値条件は変更していない。

## テスト

主な追加・変更テストと変異対応は次のとおり。

- M1〜M3:
  - `test_red_check_payload_rejects_non_exact_node_shapes`
  - flake余分 field、flake rc非0、非帰属 rc非1、bool、未知分類、attributableを拒否する。

- M4:
  - `test_red_check_payload_rejects_unsorted_duplicate_or_overlapping_sets`
  - `test_land_rejects_verdict_field_inconsistency`
  - 非整列、重複、red/flake重複を waiterとlandの双方で拒否する。

- M5:
  - `test_flake_only_publishes_v4_receipt_with_separate_nodeids`
  - `test_land_accepts_flake_only_and_emits_flake_nodeids`
  - redが空でもflakeが非空なら受理されることを固定する。

- M6:
  - `test_non_attributable_runner_blob_mismatch_is_indeterminate`
  - waiterがrunner不一致時にouter receiptを発行しないことを固定する。

- M7:
  - `test_land_runner_gate_uses_tested_main_after_main_reaches_tip`
  - 現在のmainではなくrequestのtested mainを使うことを固定する。

- M8:
  - `test_non_attributable_runner_object_must_be_blob`
  - `test_land_rejects_non_blob_runner_objects_even_when_trees_match`
  - SHAだけでなくobject typeがblobであることを要求する。

- M9:
  - `test_land_rejects_tampered_acceptance_receipt`
  - v3およびv4の `flake_nodeids` 欠落を拒否する。

- M10:
  - `test_land_accepts_flake_only_and_emits_flake_nodeids`
  - `test_land_accepts_mixed_red_and_flake_nodeids_without_merging_sets`
  - `LandResult` と結果JSONの両方へflakeが残ることを固定する。

裁定の正例も配置した。

- 正例1:
  - `test_child_green_accepts_different_main_and_tip_runner_blobs`
  - `test_child_green_receipt_does_not_require_main_tip_runner_equality`

- 正例2:
  - `test_mixed_red_and_flake_receipt_preserves_disjoint_sets`
  - `test_land_accepts_mixed_red_and_flake_nodeids_without_merging_sets`

F366対応として、次の既存 producerテストを実際の書込 bytes、`json.loads`、実 consumer述語の相互 pinへ拡張した。

- `test_main_green_wave_red_is_attributable`
- `test_main_green_wave_green_is_recorded_as_flake`
- `test_main_red_is_non_attributable_without_wave_rerun`

既存 helper、schema assertion、診断 exact比較、`LandResult` equality、既定JSON、64 KiB境界のfillerも更新した。

## 波及の静的列挙

- runtime outer receipt consumerは引き続き `tools/dev_wave_land.py` のみで、本検証とrelease-authorityが共有 `_receipt_object` を通る。
- release-authorityはv4 exact field集合を受理し、v3を拒否する。
- 既存 `LandResult(...)` call siteは新 fieldが既定値付きkeyword-onlyのため破壊しない。
- 発行済みv3 receiptは意図的に再利用不能となり、新waiterでの撮り直しが必要。
- test fileの新設や改名はないため、plain-runnerのfile集合meta-test更新は不要。
- `tools/check_acceptance_reds.py`、docs、spool、commitには触れていない。

## 未了・懸念

- 指示どおりpytestとplain test runnerは未実走。緑は主張しない。
- 5 fileの構文compile、重複test名検査、変更file範囲、`git diff --check` は静的に成功した。
- 親は指定3 test fileを `tools/run_tests.py` 経由で実測し、既知の環境赤と今回の回帰を分離する必要がある。
- docs、台帳、受入全走、mutation実走、commit、provenance監査は親の担当として残した。

## 総括

指定5 fileだけに実装し、docsとcommitには触れていない。  
waiterとlandをreceipt v4、red/flake別集合、全非帰属経路のrunner blob gateへ揃えた。  
裁定の正例2件とM1〜M10を狙うテスト、および実producer-consumer相互 pinを追加した。  
構文と差分は静的確認済みで、pytestは指示どおり未実走。  
状態は「実装済み・未実走」。