## 実装したもの

- [p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/campaign/p3_b4_raw_record_producer.py:57)
  - 非保証の固定 tuple。
  - 構造化拒否・deferred・write・assembly 型。[line 103](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/campaign/p3_b4_raw_record_producer.py:103)
  - 有限十進変換と入力 token 保存。[line 293](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/campaign/p3_b4_raw_record_producer.py:293)
  - symlink を拒否する単一 fd snapshot。[line 348](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/campaign/p3_b4_raw_record_producer.py:348)
  - 事前確定 path への排他 publish、同一 bytes の冪等成功、異なる bytes の拒否。[line 427](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/campaign/p3_b4_raw_record_producer.py:427)
  - certified receipt bundle の snapshot 検証。[line 608](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/campaign/p3_b4_raw_record_producer.py:608)
  - WAL prefix、当該 attempt の先頭 `ts`、終端 record、campaign lock、receipt、sidecar、consumption、checkpoint からの arm 導出。[line 753](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/campaign/p3_b4_raw_record_producer.py:753)
  - 閉じた request API。[line 1102](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/campaign/p3_b4_raw_record_producer.py:1102)
  - 201 block の最終組立て、pair と publication 内一意性の再検査。[line 1282](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/campaign/p3_b4_raw_record_producer.py:1282)

- [test_p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/tests/test_p3_b4_raw_record_producer.py:113)
  - M01〜M18 の一対一 node 登録。
  - WAL、loop state、campaign identity lock、critic receipt、consumption、commit receipt は既存 writer 経由で生成。
  - 全件欠測 201 block 正例。[line 637](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/tests/test_p3_b4_raw_record_producer.py:637)
  - certified 201 block 正例。[line 667](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/tests/test_p3_b4_raw_record_producer.py:667)
  - 指定の自走 harness。[line 705](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-raw-producer-author/orchestrator/tests/test_p3_b4_raw_record_producer.py:705)

## 現行の受理・拒否挙動

変更前の frozen consumer は適合 raw bytes と対応 source bytes を受理していたが、それらを生成する repo 内経路は無かった。既存 consumer の受理集合は変更していない。

新 producer は以下を受理する。

- exact `B4PrerunPublication` と locator 5 field の閉じた request。
- issuer が `attempt_id` に割り当てた `artifact_path` のみ。
- certified receipt、marked campaign identity、launch sidecar、consumption record、WAL prefixを再検証できる pair。
- 終端 record がある試行、または終端 record 不在で既存 campaign lock を取得できる試行。
- 既存 target が同一 bytes の冪等再実行。

以下は構造化拒否する。

- 判断 fieldを含む unknown request field。
- symlink、読取不能、schema・identity・hash binding 不一致。
- 当該 attempt の WAL 先頭 `ts` が欠落または同値。
- 非有限十進の `reference_tps`。
- publication 内の重複 `(campaign_id, iteration, arm)`。
- 異なる既存 target bytes、欠けた201件、最終組立て時の異なる `pair_id`。

終端 record 不在かつ `CampaignBusy` の場合は artifact を書かず `B4RawRecordDeferred` を返す。

## 実走した検査

テストは実装済みですが、未実走です。

- `test_m13_integer_reference_and_complete_evidence_are_accepted`
  - `python3 tools/run_tests.py ... -q`
  - pytest 到達前に rc=16。
- 新規 test file 全体の `--collect-only`
  - 同じく pytest 到達前に rc=16。

原因は、login node の headroom 予約台帳が read-onlyで local scopeを作れず、dispatch 側も `qstat -Q` が `Unknown user-id` で失敗したためです。

内訳:

- 緑: pytest node 0件。
- pytest の赤: 0件。collection 前に停止したため不明。
- infrastructure 赤: 2件、いずれも rc=16。
- 未実走: 新規22 node、M01〜M18変異 harness、制約 meta-test。

静的検査は通過しました。

- 両新規 file の AST parse と import。
- test node 22件、変異 mapping 18件・重複なし。
- 公開 API の引数に判断 field が無いこと。
- 変更 path が許可された2 fileだけであること。
- `_SOURCE_CLOSURE_PATHS` 所有 fileの working tree hashがHEADと同一。
- 禁止された名乗りと禁止 field名が新規 production fileに無いこと。
- U+0300〜U+036F が両 fileに無いこと。

制約 meta-test候補として、plain-runner一覧、B-4 caller census、certified-writer census、COMMIT producer census、critic digest caller census、process-launch census、build materializer census、pytest collection censusを洗い出しましたが、上記infra障害により未実走です。

test runner が生成した2件の一時 dispatch診断 directoryは、許可外の `output/` 変更を残さないため削除しました。診断物のみで、同じ失敗時に再生成できます。

## 変異点と落ちる node の対応

共通 prefixは `orchestrator/tests/test_p3_b4_raw_record_producer.py::` です。

| 変異 | 登録 node |
|---|---|
| M01 | `test_m01_precursor_is_copied_from_the_sealed_registry` |
| M02 | `test_m02_only_the_issuer_planned_result_path_is_used` |
| M03 | `test_m03_assignment_comes_from_attempt_wal_first_record_timestamps` |
| M04 | `test_m04_final_assembly_rejects_different_on_off_pair_ids` |
| M05 | `test_m05_campaign_identity_lock_is_snapshotted_once_for_classification_and_commit_receipt` |
| M06 | `test_m06_lowercase_wal_commit_maps_only_to_uppercase_raw_commit` |
| M07 | `test_m07_non_binary_exact_decimal_lexeme_is_preserved` |
| M08 | `test_m08_publication_rejects_reuse_of_campaign_iteration_arm_tuple` |
| M09 | `test_m09_stable_nonterminal_wal_is_not_classified_as_executed` |
| M10 | `test_m10_certified_off_digest_absence_sets_treatment_fired_true` |
| M11 | `test_m11_unproved_crash_and_stopped_before_dispositions_are_never_emitted` |
| M12 | `test_m12_nonterminating_reference_ratio_has_only_named_rejection` |
| M13 | `test_m13_integer_reference_and_complete_evidence_are_accepted` |
| M14 | `test_m14_busy_campaign_with_no_terminal_record_is_deferred_without_publish` |
| M15 | `test_m15_lock_free_campaign_with_no_terminal_record_is_published` |
| M16 | `test_m16_judgment_fields_are_unknown_request_fields` |
| M17 | `test_m17_terminal_receipt_original_is_opened_once_before_copy_validation` |
| M18 | `test_m18_symlinked_evidence_is_rejected_with_regular_control` |

mapping の完全性と一対一性は静的に確認済みです。ただし変異実走ができていないため、実際の kill 数が複数または0になる点は未判定です。M01〜M18すべてがこの未検証対象です。

## 非保証として書いたもの

- ``initial_proposal_sha256`` を計算・記録する経路が repo に無いため、precursor と実 campaign の束縛は転記に留まる。
- flock は advisory である。
- model hash は存在せず ``model_snapshot`` は非 hash の識別子である。
- ``treatment_fired`` は receipt 水準の意味に限定され、その decision で次を合成したことを証明しない。
- treatment precursor の詳細 class は現状の証拠から作れない。
- producer は凍結された analysis source closure の外にある。

## 波及可能性

- 現在、所有外の production callerは無い。将来の sanctioned commandが `publish_b4_attempt_result` と `assemble_b4_raw_analysis` の主要 caller候補。
- testは `commit_receipt_support` と、既存 closed-critic・prerun-issuer testのprivate fixtureを共有するため、それらのfixture変更の影響を受ける。
- 出力は `parse_raw_analysis_records`、`evaluate_b4_artifacts`へ直接渡すため、frozen consumer側schemaの将来変更が統合testへ波及する。
- production側はissuer、closed critic、launcher、WAL、loop state、campaign lock、commit receiptの既存実体へ依存する。
- 既存 fileは変更しておらず、`p3_b4_analysis_path.py` のhashもHEADと一致する。

## 実装しなかったもの と 理由

- CLI、sanctioned command、正式B-4実走、qsub、性能測定: scope外かつ明示禁止。
- docs、既存test、analysis closure、launcher、WAL、lock等の変更: 許可外。
- 新しい署名、nonce、seal、一回性台帳、slot occupancy機械: 裁定で禁止。
- overall raw fileの別pathへの書込み: issuerが事前確定したoverall pathが無いため。assemblyはcanonical bytesと402 source bytesを返す。
- precursorとcampaignの追加認証、producer意味論のclosure認証: 本waveの2 fileでは閉じられない。
- commit: 明示禁止。
- 変異実走とpytest緑確認: login/queue infrastructure障害のため未完了。

## 総括

許可された2 fileだけにproducerと22 test nodeを実装し、既存file・docs・`output/`には変更を残していません。実装は静的検査済みですが、pytestと変異harnessはinfra障害で未実走です。したがって状態は「実装済み・実走未完了」です。