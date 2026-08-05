# 実装結果

D153 W1〜W5 の ledger 側契約へ適合する P4 batch-freeze prototype を実装しました。P4 充足・production 結線は主張しません。commit と docs 編集は行っていません。

## Δ 実装一覧

- Δ1: origin-wide `query_ordinal` / `replicate_ordinal` と member preimageを実装。[ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:608)、reducer 検査は同ファイル 1236 行、テストは [test_reflux_origin_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:1987)。
- Δ2: committed/prepared payload から replicate を除外し、terminal opening のみに配置。同 725、2268 行。
- Δ3: pre-seal projection から sealed/tombstoned query counter と tombstone count を除外。同 1027、2268 行。
- Δ4: `BatchTombstoned` を削除し、全 terminal path を committed→prepared→sealed に統一。固定長 member row と tombstone suffix は同 503、516、1177、1295 行。全 tombstone no-refund は test 911 行、部分 tombstone は 2125 行。
- Δ5: `member_sequence_commitment` を実装せず、payload が `cardinality + members` のみであることを固定。同 725、2268 行。
- Δ6: batch codec ceiling を独立 oracle で `2248` に固定。同 98、1869、テスト 2318 行。
- Δ7: salt を exactly 32 lowercase hex、非ゼロに変更。同 585、テスト 2318 行。
- Δ8: per-batch frame と origin-total partition/ledger bound を分離。同 1922、テスト 1428・2318 行。
- Δ9: manifest/authority/event/head/runtime を v2 化。同 72、1440 行、[authority v2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_authority_v2.json:1)。
- Δ10: `sealed_queries` は evidence 付き member row 数であり物理 query の証明ではないと明記。同 2–9、1295、3041 行。
- Δ11: outcome と evidence digest claim の単一 salted commitment、三値 matrix、codec/reducer 二層検査を実装。同 622、646、785、1177 行。テスト 2125 行。
- Δ12・Δ13: docs 記録なので未実装。
- Δ14: docs/handoff 所有なので未実装。interface delta は後述します。

## 検査結果

通過:

- `python3 -m py_compile` — 対象コード・テストとも成功。
- `git diff --check` — 成功。
- AST 一意性検査 — 23 test function、重複なし。
- `python3 tools/check_codex_agents.py` — 成功。
- `python3 tools/check_docs.py` — 成功。

計算ノード部分走は次の2回を試しました。

1. `orchestrator/tests/test_reflux_origin_ledger.py` 全範囲
2. 上記全範囲に加え、次の meta-test:
   - `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
   - `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`

いずれも `qstat -Q preflight rc=1`、wrapper rc=16 の dispatch infrastructure failure で、collection・test 本体は0件です。実行済み pytest の赤はありませんが、緑も主張しません。

## 独立 golden

- V01 は v2 event/head/state、member preimage、result/evidence preimageを手書き JSON/base64 bytes と標準 `hashlib` で再構築しました。
- V16 は test 側の独立 `_member_bytes` / `_result_bytes` と `hashlib` から prepared projection を構築し、実装の `_event_payload()` を期待値生成に使用していません。
- V21 は rejected `BatchSealed` frame を手書き JSON から構成し、2248件=`1,048,246 bytes`、2249件=`1,048,712 bytes` を literal pin しました。
- production feasibility helperや二分探索結果を golden 生成には使用していません。

## M-1〜M-18 対応

実変異は未走です。各変異の kill 予定 nodeid は次のとおりです。

| 変異 | 落ちる nodeid |
|---|---|
| M-1〜M-7 | `orchestrator/tests/test_reflux_origin_ledger.py::test_v17_member_identity_literal_replicates_and_origin_query_accounting` |
| M-8 | `orchestrator/tests/test_reflux_origin_ledger.py::test_v16_commit_reveal_privacy_order_exact_class_and_positive_cycle` |
| M-9〜M-13 | `orchestrator/tests/test_reflux_origin_ledger.py::test_v18_evidence_outcome_contract_and_fixed_member_tombstones` |
| M-14 | `orchestrator/tests/test_reflux_origin_ledger.py::test_v14_independent_i_q_k_floor_boundaries_and_aborted_seal` |
| M-15〜M-16 | `orchestrator/tests/test_reflux_origin_ledger.py::test_v20_preseal_projection_hides_execution_counters_and_replicates` |
| M-17〜M-18 | `orchestrator/tests/test_reflux_origin_ledger.py::test_v21_exact_salt_width_and_independent_codec_partition_oracle` |

各 node 内に個別の負例があります。M-4 は cross-batch replicate reset、M-5 は gap/duplicate query、M-7 は sealed/tombstoned 両方の invalid wire、M-10 は reducer 直呼びの未知 outcome、M-13 は evidence/outcome tamperを検査します。対を作れない M-1〜M-18 はありません。正例 P-1 は V17、P-2 は V18です。

## 所有外への波及

静的検索では、対象テスト以外の `orchestrator/campaign/`・`orchestrator/tests/` に ledger API、旧 authority path、旧 constructor の直接 caller/consumer は0件でした。

波及しうる面:

- `reflux_origin_ledger.py` は引き続き `reflux_ir.py` の canonical wire validatorを利用します。
- 並行 producer wave は、新しい nested member API、origin-wide query ordinal、terminal replicate opening、追加された origin seal counter、authority v2 pathへ追随が必要です。
- `BatchTombstoned` は消滅し、`SealedBatch.members` が read model の正本になりました。
- shared runner面では `conftest.py`、plain-runner coverage、real-repo serialization meta-testが関係します。
- docs/output 内の旧 schema/path参照は歴史記録または親の Δ12〜Δ14 所有面として未編集です。
- evidence/class referent resolver、物理 query receipt、proof-chain consumerは依然未実装です。

なお通常の Git index は sandbox 外で read-onlyだったため、親 indexへの `git add -A` は実行できませんでした。一時 indexでは削除/addを確認済みですが、実 worktree status は旧 authority削除＋v2新規の未stage状態です。親は受入前に必ず `git add -A` してください。

## 総括

- Δ1〜Δ11を許可された3ファイル内で実装しました。
- Δ12〜Δ14は指定どおり親のdocs/handoff作業として残しました。
- 静的検査は緑です。
- pytest本体はPegasus認証preflight障害で未実行です。
- 親は `git add -A`、対象23 node＋meta-test、変異M-1〜M-18、所有外全走を確認してください。