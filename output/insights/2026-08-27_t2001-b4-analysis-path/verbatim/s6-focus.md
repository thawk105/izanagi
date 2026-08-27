## 前提の確認

指定された射影資料 6 件と対象 10 file を全行確認した。Web 検索、pytest、任意の実走は行っていない。

実走については、本依頼に記録された親の結果のみを採用する。

- 対象 5 test file: 152 passed、0 failed
- 一覧検査: 60 passed、128 passed / 9 skipped、971 passed / 3 skipped
- provenance: 6618 件、新規違反なし

`parent-measurements.md:80-90` の 121 passed は古い記録であり、本依頼の 152 passed が後続記録である。

判定結果は closed 8、partial 3、regressed 0。

## 所見の対応表

| 所見 | 判定 | 実コード上の根拠 | 成果物影響 |
|---|---|---|---|
| sol F1: exact section hash が実効 gate でない | **closed** | raw hash は無条件比較になり、semantic hash は救済に使われない。`p3_b4_analysis_prereg_consumer.py:394-407`。formatting-only 変更も拒否する。`test_p3_b4_analysis_prereg_consumer.py:215-231` | section bytes が 1 byte でも変われば consumer 成功と closure receipt 発行を拒否する。 |
| sol F2: eligibility fixture が cutoff 後で恒真 | **partial** | 到達可能な 7 条件は不適格行を先頭に置き、除外されなければ 201 件目を押し出す。`test_p3_b4_analysis_ledgers.py:401-469`。一方、block id と 3 reference 条件は `reason=SCHEDULED` の時点で上流 validation が必須化する。`p3_b4_analysis_ledgers.py:350-358,914-928`。テストは seal 不能な object を private predicate へ直渡ししている。`test_p3_b4_analysis_ledgers.py:472-497` | 到達可能な eligibility 漏れによる manifest 汚染は検出可能になった。残る 4 条件の削除は現在の受理 artifact を変えず、閉鎖証拠だけが過大になる。残余は evidence 上の nit。 |
| sol F3: M12 の 2 層変異が第 3 gate で SURVIVED | **partial** | rows 比較と canonical bytes 比較を外しても `manifest != regenerated` が残る。`p3_b4_analysis_ledgers.py:1152-1163`。path は completeness を直接、さらに `build_contract_binding()` 内でも実行し、actual binding も比較する。`p3_b4_analysis_path.py:234-286`、`p3_b4_analysis_ledgers.py:1210-1232` | M12 を kill したという closure 証拠は依然成立しない。同じ forged manifest は別 gate に拒否され、登録 node は赤にならない。 |
| sol F4: assignment oracle が自己導出 | **closed** | test 内の独立 HMAC 計算と固定 digest/order がある。`test_p3_b4_analysis_ledgers.py:245-296`。8 block の固定列も実装出力と独立に固定される。`同:299-323` | 定数 assignment への置換は生存せず、二項帰無分布の前提崩壊を検出できる。 |
| sol F5: missing/missing の挙動検査なし | **closed** | `Fraction(1,2)` を直接期待する専用 node がある。`test_p3_b4_analysis_contract.py:364-374` | missing/missing を 0 または 1 に変えても `A_hat` や p 値の漂流前に検出する。 |
| sol F6: post-freeze fixture が byte gate に届かない | **closed** | 相互に異なるが両方 canonical な manifest を作り、`assert_manifest_unchanged_before_run()` だけを呼ぶ。`test_p3_b4_analysis_ledgers.py:709-733`。両 load 後の実効 gate は `p3_b4_analysis_ledgers.py:1280-1283` | valid manifest 間の post-freeze byte 差分を、canonicality・assignment・completeness と分離して拒否できる。 |
| sol F7: 12 理由の意味を保存しない | **closed** | raw arm/disposition/whiteboard/stage の不正 enum は catchall へ写る。`p3_b4_analysis_adapter.py:164-172`。`status_domain_error` は derived status 不成立に限定される。`同:474-509`。5 種の独立検査は `test_p3_b4_analysis_adapter.py:310-332` | invalid ledger の理由台帳が raw enum 不正を block status 不正として誤分類しなくなった。 |
| luna F1: 純関数直呼びが統合結果と区別不能 | **partial** | 通常の production caller は artifact producer と非返却 probe の 2 件へ exact pin された。`test_p3_b4_analysis_path.py:291-371`。probe が結果を返さない検査もある。`同:374-375`。ただし結果型に provenance はなく、直呼び自体は可能と明記される。`p3_b4_analysis_contract.py:19-23` | 自作 block から `ESTABLISHED` result object は今も生成可能。3 件目の通常 caller は赤になるが、dynamic call や class method、将来の downstream 受理は閉じていない。 |
| luna F2: source artifact が multiset 一致のみ | **closed** | declared/observed digest は block/arm 順の tuple 完全一致で、件数と双方の一意性も必須。`p3_b4_analysis_path.py:174-196`。arm 間 swap と duplicate bytes の専用検査がある。`test_p3_b4_analysis_path.py:515-550` | digest を別 arm へ付け替えた自己申告 JSON は拒否される。bytes 内容から意味値を再導出しない限界は残るが、これは親裁定どおり scope 外。 |
| luna F3: 文面 hash の論理和受理 | **closed** | sol F1 と同じ。raw と semantic は個別の必須 gate。`p3_b4_analysis_prereg_consumer.py:399-407` | semantic 等価な byte 改変を closure receipt へ混入できない。 |
| luna F4: receipt に consumer 実行結果がない | **closed** | receipt は canonical result bytes と hash を保持し、canonical payload に両方を含める。`p3_b4_analysis_path.py:89-99,416-537`。唯一の public producer は consumer 成功後に assembler へ到達する。`p3_b4_analysis_prereg_consumer.py:1027-1101` | public route の receipt は document/source/behavior 検証結果へ束縛される。private assembler の限界は後述する。 |

## 新しい欠陥

1. 構造 eligibility 4 条件は実効 gate ではない

`block_id`、`reference_tps`、`reference_snapshot_hash`、`reference_receipt_hash` は、sealed registry 内で `reason is SCHEDULED` が成立すれば `_validate_attempt()` から含意される。専用テストは seal 不能な object を `_attempt_is_eligible()` へ直渡しするため、コード削除変異は殺すが受理集合の変化を証明しない。

成果物影響: 現在の受理 artifact への影響はない。mutation closure の「各 eligibility 条件が実効 gate」という証拠だけが過大であり、nit と判定する。

2. assignment の kill は過剰決定されている

`test_assignment_matches_independent_fixed_hmac_vectors` と `test_fixed_assignment_vectors_are_concretely_nonconstant` が同じ定数化を別 oracle で殺す。後者は名前上は nonconstant 検査だが、実際には 8 block の完全な列を固定している。`test_p3_b4_analysis_ledgers.py:245-323`

成果物影響: assignment の安全性は強くなるが、X09 を単一 node・単一 oracle に帰属させることはできない。

3. source-shape と behavior の重複

X04、X05、X07 は consumer の AST shape と直接 behavior の両方で検出される。`p3_b4_analysis_prereg_consumer.py:609-641,703-750,819-954`。fix4 の3 probe間の独立性は成立したが、source mutation 全体の単一帰属までは成立していない。

成果物影響: 不正実装は拒否されるが、closure 報告で「どの gate が変異を殺したか」を一意に説明できない。

受理集合について、指示外の broadening は確認しなかった。確認した変化は次の意図された narrowing または理由分類変更だけである。

- formatting-equivalent な raw section 改変を拒否
- source artifact を順序付き一対一・重複なしに限定
- public receipt route を consumer 成功後に限定
- raw enum 不正の理由を catchall へ変更。受理・拒否自体は不変

## 限界申告の点検

正直に申告されている点:

- file-drawer は閉じていない。`p3_b4_analysis_ledgers.py:3-11`
- seed の一様性、実走前発行は証明しない。`同:8-11`
- source bytes から status、throughput 等を再導出しない。`p3_b4_analysis_path.py:5-16`
- production caller pin は直呼びを不可能にしない。`p3_b4_analysis_contract.py:19-23`、`p3_b4_analysis_prereg_consumer.py:22-24`
- raw section hash は無条件 pin、semantic hash は診断専用。`p3_b4_analysis_prereg_consumer.py:15-17`
- 「§6 前提条件 9 を充足」「file-drawer を閉じた」「直呼びを閉じた」という過大文言はない。

限定付きで強すぎる点:

- `B4AnalysisSourceClosureReceipt` の「verified consumer result」と `_load_canonical_consumer_result()` のエラー文は、private helper 単体の保証より強い。helper は schema と canonicalityしか検査せず、テスト自身が実 consumer 出力ではない `{"test_verified": true}` を渡して receipt を生成している。`p3_b4_analysis_path.py:89-99,444-499`、`test_p3_b4_analysis_path.py:585-624`
- public producerを通る限り consumer 成功は保証されるため luna F4 は closed としたが、receipt 単体は consumer 実走の偽造不能な証明ではない。
- `test_fixed_assignment_vectors_are_concretely_nonconstant` は検査名より強く、単なる非定数性ではなく 8 要素完全一致を要求している。過小申告である。

## 変異の帰属

ここで「単一理由」は、赤となる node が複数でも同じ対象述語だけに帰属できる場合を「はい」とした。AST、behavior、別 oracle が独立に反応する場合は「いいえ」とした。node は静的に期待される赤であり、私が実走した結果ではない。

| 変異 | 単一理由 | 実効 gate | 静的に期待される赤 node |
|---|---|---|---|
| X01 `parse_float=Fraction` を外す | はい | decimal token が float となり exact domain で拒否。`p3_b4_analysis_adapter.py:403-408` | `test_p3_b4_analysis_adapter.py::test_decimal_lexical_is_read_exactly_not_via_float` |
| X02 tie 境界 `<=` → `<` | はい。ただし複数層 | inclusive boundary の直接期待と consumer rank probe。`p3_b4_analysis_contract.py:525-528`、consumer `942-954` | contract `::test_certified_gain_boundary_is_inclusive_tie`、adapter `::test_decimal_lexical_is_read_exactly_not_via_float`、path `::test_rank_and_threshold_verification_probe_exports_no_analysis_result`、consumer の `current_document`、`selection_and_violation...`、`behavior_probes...` |
| X03 missing/missing を半分以外へ | はい | missing/missing 専用直接期待。`test_p3_b4_analysis_contract.py:364-374` | `::test_missing_against_missing_has_exact_half_score` |
| X04 contamination を protocol より前へ | **いいえ** | direct precedence、統合 combined case、AST branch order。`p3_b4_analysis_prereg_consumer.py:609-641` | contract `::test_protocol_violation_precedes_contamination`、path `::test_protocol_failure_precedes_contamination_in_combined_case`、consumer の `current_document`、`selection_and_violation...`、`first_n_and_violation_order...`、`receipt_public_route...` |
| X05 `A_min` を成立条件へ追加 | **いいえ** | below-A_min 成立 behavior と AST の `A_MIN` 禁止。`p3_b4_analysis_contract.py:732-750`、consumer `630-641,860-922` | 確定: contract の `establishes_below_a_min...`、`every_valid_input...`、path の `rank_and_threshold...exports...`、consumer の `current_document`、`selection_and_violation...`、`behavior_probes...`。helper 経由など patch shape に依存する追加 node は確定不可 |
| X06 batch 正規化を外す | はい | canonical sort と receipt hash の permutation 不変性。`p3_b4_analysis_ledgers.py:439-481` | `test_p3_b4_analysis_ledgers.py::test_batch_seal_is_permutation_invariant` |
| X07 first n → last n | **いいえ** | direct manifest expectation、precutoff fixtures、AST first-slice、selection behavior。`p3_b4_analysis_ledgers.py:1063-1076`、consumer `703-723,819-837` | ledgers の `manifest_selects_first_201...` と reachable eligibility 7 parameter node、consumer の `current_document`、`selection_and_violation...`、`behavior_probes...`、`first_n_and_violation_order...`、`receipt_public_route...`。自己導出型の一部 node は値の偶然一致があり得るため追加分は確定不可 |
| X08 violation count を filter 後へ移す | はい。ただし source-order gate のみ | literal な call 移動なら full registry を同じ関数で数えるため挙動は不変。実効 gate は AST 行順。`p3_b4_analysis_prereg_consumer.py:724-737` | consumer の `current_document`、`selection_and_violation...`、`first_n_and_violation_order...`、`receipt_public_route...`。filtered subset を実際に数える別 patch の node 集合は確定不可 |
| X09 assignment を定数化 | **いいえ** | 独立 HMAC vector と 8 block 完全列。`test_p3_b4_analysis_ledgers.py:245-323` | `::test_fixed_assignment_vectors_are_concretely_nonconstant` は必ず赤。常時 ON なら fixed-vector の block 003/007、常時 OFF なら block 000 も赤。定数値未指定のため exact parameter node 集合は確定不可 |
| X10 raw section hash gate を外す | はい | semantic 等価だが raw bytes が異なる fixture。`p3_b4_analysis_prereg_consumer.py:399-407` | `test_p3_b4_analysis_prereg_consumer.py::test_formatting_equivalent_raw_byte_changes_are_rejected` |
| X11 ordered bijection を multiset へ戻す | はい | arm 間 digest swap。`p3_b4_analysis_path.py:183-196` | `test_p3_b4_analysis_path.py::test_source_artifact_digest_swap_between_arms_is_rejected` |
| X12 receipt から consumer result binding を外す | **いいえ** | private assembler の canonical payloadと public consumer route の両方。`p3_b4_analysis_path.py:416-537`、consumer `1027-1077` | path `::test_private_closure_assembler_is_stable_and_binds_consumer_result`、consumer `::test_current_document_contract_literals_match_implementation`。field、hash、payload のどこを外すかで追加 node は確定不可 |

2 層以上が同じ入力を拒否する代表例:

- 元の M12: rows と canonical bytes を外しても object equality が実効 gate。さらに path の completeness 再呼出と actual binding 比較が残る。
- X04: verdict precedence の behavior と consumer AST branch order。
- X05: below-A_min behavior と AST の `A_MIN` 排除。
- X07: direct first-201 expectation、AST first-slice、consumer selection behavior。
- X09: fixed HMAC vector と 8 block 完全列。
- X12: private canonical receipt payload と public consumer-bound receipt。

実行時の同一 forged manifest に多層 gate が直接重なるのは M12 である。X04、X05、X07、X09、X12 は主として mutation harness 上の過剰決定である。

## 総括

closed 8、partial 3、regressed 0 と判定した。  
raw section hash、source digest 全単射、missing tie、post-freeze byte gate、reason mapping、consumer-result binding は閉じている。  
assignment 定数化も生存しないが、固定 vector と完全列で過剰決定されている。  
eligibility の到達可能な 7 条件は修復済みだが、構造 4 条件は上流 validation から含意される。  
M12 は第 3 gate と path の再検査が残るため、登録した mutation kill としては依然 SURVIVED である。  
純関数直呼びは production caller census までしか閉じておらず、結果 provenance は未解決のままである。