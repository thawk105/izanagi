A〜H の実装は完了しました。ただし Pegasus queue の障害により、動的テストと変更後時間の実測は未完了です。commit は行っていません。

## A〜H の対応

- A — 対応した。assembly が source artifact の evidence pointer を再読込し、判断値・binding・非保証 tuple を再導出結果と照合します。pointer 欠落、改ざん、不一致は拒否します。
- B — 対応した。terminal checkpoint の未追従と、lock 取得後の WAL 変化は publish せず deferred。B-1 の残余は指定文言で非保証へ追加しました。
- C — 対応した。4 種類の赤詳細 entry を検出し、空の赤節は構造化拒否します。両 arm 一律 true の逆向き M10 負例も追加しました。
- D — 対応した。終端記録がある場合、launch sidecar、consumption、loop state、admission sidecar の欠落・schema 不良を `evidence_issues` に記録し、`protocol_ok=false` の artifact を残します。
- E — 対応した。manifest `driver` と両 receipt/campaign の `driver_kind` を照合します。
- F — 対応した。executable、role file、projection closure 全要素を推移的に no-follow snapshot し、同じ bytes を verifier に渡します。
- G — 対応した。M01/M02/M03/M05/M08/M13/M17 を実効 gate へ再照準し、M10 逆向き負例を追加しました。
- H — 対応した。closure、role、executable、publication reload、既存 identity 走査を共有 context/batch へ畳み、共有 certified fixture は cross-worker lock 下で一度だけ生成します。ただし変更後 wall time は runner 障害で未実測です。

## 直したもの

- [p3_b4_raw_record_producer.py:57](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/campaign/p3_b4_raw_record_producer.py:57) — 残余 flock、後日再開、closure 認証限界を非保証へ追加。
- [p3_b4_raw_record_producer.py:687](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/campaign/p3_b4_raw_record_producer.py:687) — projection closure の推移的 snapshot と context cache。
- [p3_b4_raw_record_producer.py:719](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/campaign/p3_b4_raw_record_producer.py:719) — 既存 receipt verifier を同一 role/executable/closure bytes に束縛。
- [p3_b4_raw_record_producer.py:931](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/campaign/p3_b4_raw_record_producer.py:931) — 4 クラスの赤詳細 entry 判定。
- [p3_b4_raw_record_producer.py:1006](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/campaign/p3_b4_raw_record_producer.py:1006) — D の evidence issue、checkpoint deferred、lock 後 WAL 再読。
- [p3_b4_raw_record_producer.py:1492](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/campaign/p3_b4_raw_record_producer.py:1492) — publish/assembly 共通の証拠再導出。
- [p3_b4_raw_record_producer.py:1711](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/campaign/p3_b4_raw_record_producer.py:1711) — 二次走査を避ける B-4 batch publish。
- [p3_b4_raw_record_producer.py:1831](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/campaign/p3_b4_raw_record_producer.py:1831) — assembly の全 source 再導出と完全一致検査。
- [test_p3_b4_raw_record_producer.py:285](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/tests/test_p3_b4_raw_record_producer.py:285) — M01〜M18 の新しい対応表。
- [test_p3_b4_raw_record_producer.py:523](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/tests/test_p3_b4_raw_record_producer.py:523) — certified evidence の cross-worker 一回生成。
- [test_p3_b4_raw_record_producer.py:922](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/tests/test_p3_b4_raw_record_producer.py:922) — pointer-free raw 注入、判断値改ざん、非保証欠落の敵対テスト。
- [test_p3_b4_raw_record_producer.py:957](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/tests/test_p3_b4_raw_record_producer.py:957) — checkpoint window と WAL 変化の同期テスト。
- [test_p3_b4_raw_record_producer.py:1014](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/tests/test_p3_b4_raw_record_producer.py:1014) — 終端済み補助証拠欠落の全件記録。
- [test_p3_b4_raw_record_producer.py:1060](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix2/orchestrator/tests/test_p3_b4_raw_record_producer.py:1060) — 201 block を共有 batch 経路へ変更。

## テスト時間

- 変更前: 親実測 897 秒。主要 2 node は 619.80 秒、614.80 秒。
- 律速: projection closure の12ファイル再 hash。単発の同値診断は import 込み wall 3.4 秒で、レビューの約1.5秒/armと整合しました。
- 変更後: full-file 実測なし。全 runner 試行が `rc=16`、`child_started=false` で停止しました。
- 除去した反復コスト:
  - closure、role、executable は batch/assembly ごとに1回
  - pre-run publication reload は batch ごとに1回
  - identity 集合走査は batch 開始時に1回
  - admission、環境契約、projection は test worker ごとに1回
  - certified 共有 evidence は pytest run ごとに1回
- 残るコストは402件の実 receipt bundle、WAL、loop state、lock、sidecar の固有 snapshot/hash/parse、および402件の実 evidence 生成です。時間配分は queue 復旧後の実測が必要です。

## 実走した検査

動的 node は実走できませんでした。

- 対象 file 単独: `rc=16`
- 単一 M13 node: `rc=16`
- mutation mapping node: `rc=16`
- 対象 fileと名指し meta-test 11件の合同走: `rc=16`
- 原因: `qstat -Q preflight rc=1`、dispatch child 未起動
- 動的内訳: 0 green / 0 red / 未実行29 node

実行できた静的検査:

- `py_compile`: 2 file 成功
- projection snapshot hash と既存 closure hashの一致: 成功
- AST による M01〜M18 の18個一意 node対応: 成功
- 許可外差分確認: 許可された2 fileだけ
- runner が自動生成した今回分の診断 directory 5個は完全指定で除去済み。再実行で再生成可能です。

## 変異 M01〜M18 の再照準

| 変異 | 実効 gate / 登録 node |
|---|---|
| M01 | assembly の sealed registry 再導出 — `test_m01_assembly_rederives_precursor_from_the_sealed_registry` |
| M02 | issuer leaf lookup と実 publish path — `test_m02_planned_path_lookup_and_publish_use_the_issuer_leaf` |
| M03 | 逆順 WAL timestamp と exact position — `test_m03_assignment_comes_from_attempt_wal_first_record_timestamps` |
| M04 | A gateを同期点で越えた最終 pair_id gate — `test_m04_final_assembly_rejects_different_on_off_pair_ids` |
| M05 | classification と receipt hash の同一 bytes object — `test_m05_campaign_lock_classification_and_receipt_share_one_byte_buffer` |
| M06 | lowercase COMMIT 写像 — `test_m06_lowercase_wal_commit_maps_only_to_uppercase_raw_commit`。複数落ちは裁定どおり維持 |
| M07 | WAL decimal lexeme — `test_m07_non_binary_exact_decimal_lexeme_is_preserved`。複数落ちは維持 |
| M08 | publish 側を同期点で越えた assembly identity gate — `test_m08_publication_rejects_reuse_of_campaign_iteration_arm_tuple` |
| M09 | terminal record 実在 — `test_m09_stable_nonterminal_wal_is_not_classified_as_executed`。複数落ちは維持 |
| M10 | 赤詳細0件の eligibility gate — `test_m10_empty_red_section_is_rejected_instead_of_marking_both_arms_true`。逆向き一律 true を kill |
| M11 | 証拠のない disposition 禁止 — `test_m11_unproved_crash_and_stopped_before_dispositions_are_never_emitted`。複数落ちは維持 |
| M12 | publish 層の非有限十進拒否 — `test_m12_nonterminating_reference_ratio_has_only_named_rejection` |
| M13 | 他の正例を非整数有限十進に分離した integer control — `test_m13_integer_reference_is_the_only_integer_acceptance_control` |
| M14 | busy lock 同期点 — `test_m14_busy_campaign_with_no_terminal_record_is_deferred_without_publish`。複数落ちは維持 |
| M15 | lock取得可能時の欠測 publish — `test_m15_lock_free_campaign_with_no_terminal_record_is_published`。複数落ちは維持 |
| M16 | closed request schema — `test_m16_judgment_fields_are_unknown_request_fields` |
| M17 | snapshot 後に original receipt を破壊する ABA control — `test_m17_terminal_receipt_validation_survives_original_replacement` |
| M18 | terminal receipt と role file の推移的 symlink 拒否 — `test_m18_symlinked_evidence_is_rejected_with_regular_control` |

## 受理集合の変化

新たに拒否または deferred になるもの:

- source evidenceから再導出できない planned artifact
- raw判断値、assignment、binding、非保証 tuple の改ざん
- 赤詳細 entry が0件の block
- manifest driverとcampaign/receipt driver_kindの不一致
- role、executable、projection closureのsymlink
- checkpoint未追従、またはlock取得中にWALが変化した試行

新たに記録されるもの:

- terminal recordがあり、補助証拠が欠落・破損した試行。行を落とさず `protocol_ok=false` と構造化 evidence issueを残します。

正式 B-4 markerを欠くlockless receiptは、従来どおり狭い方向に拒否します。

## 波及可能性

- 既存 consumerへ渡す raw analysis schemaは変更していません。
- source artifactには `evidence_issues` と `transitive_evidence` が追加されます。
- 単件 callerは従来のAPIを利用可能です。201件生成には判断値を受け取らないB-4専用batch APIを追加しました。
- `p3_s4_loop.py` のflock保持範囲は未変更で、B-1の残余は非保証です。
- docs、既存test、analysis closure、`output/` の実 artifactには変更を残していません。
- 2 fileは未commit・未stageのままです。

## 総括

A〜H のコードと敵対テストは実装済みで、変更面は指定された2 fileに限定されています。特に、planned fileへの判断値注入、checkpoint window、空の赤節、終端後の証拠欠落、driver未束縛、推移的symlink、7変異の無効帰属を修正しました。

ただし指定 runnerは全試行で計算 childを起動できず、29 nodeの緑と120秒以下の目標は未確認です。現状は「実装済み・静的検査済み・動的検査未実走」です。