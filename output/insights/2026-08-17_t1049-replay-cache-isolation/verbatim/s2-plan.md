## (P0) の独立検証

結論は、現 HEAD `699c9cae` では (P0) を支持する。ただし厳密には「重複する値が皆無」ではなく、「異なる payload と衝突し得る `operation_id` が test 間で同時に replay cache に残らない」である。

静的な根拠は次のとおり。

- replay cache は `orchestrator/campaign/reflux_formal_consumer.py:277` の process-wide dict で、lookup は `:1045`、異 payload の拒否は `:1047-1051`、成功時の書込みは `:1065-1067`。
- production の唯一の間接呼出しは `orchestrator/campaign/reflux_origin_client.py:252-257`。`P6Unavailable` の receipt がある場合だけ consumer を呼び、`FormalContractRejected` は呼ばない。
- public origin 経路は `orchestrator/campaign/p3_autonomous_workload_trial.py:2286-2287` → `:938-972` → origin client という一本道。
- `pytest.ini:13` の収集範囲全体について全 Python call site を調べた結果、親の6 file外に呼出し経路はない。
- 親が挙げた5本の P3 test は全て ID を構築するが、実際に consumer へ到達するのは2本だけである。残り3本は preflight で終了する。
- `test_reflux_formal_consumer.py` では同じ定数を複数 test が使うが、既存 autouse fixture `orchestrator/tests/test_reflux_formal_consumer.py:196-202` が test 境界で cache を消している。
- pytest は実走していない。以下は静的結論であり、緑の報告ではない。

## 到達経路と operation_id の決まり方

表中の略記:

- `F` = `"fixture-formal-terminal-operation"`。`orchestrator/tests/test_reflux_formal_consumer.py:168`
- `P(path)` = `"public-origin-terminal-" + sha256(str(path))`。`orchestrator/tests/test_p3_autonomous_workload_trial.py:6494-6497`

| test | 到達点 | `operation_id` の決まり方 | replay cache |
|---|---|---|---|
| `orchestrator/tests/test_reflux_formal_consumer.py:698` `test_receipt_rejects_wrong_input_state_commitment` | direct consumer `:702` | `F`、fixture field 経由 | STATE で終了。書込なし |
| 同 `:711` `test_receipt_rejects_wrong_terminal_payload_digest` | direct consumer `:716` | `F` | PAYLOAD で終了。書込なし |
| 同 `:725` `test_receipt_exact_operation_replay_returns_cached_decision` | direct consumer `:728,734` | `F` | 1回目に書込み、2回目は byte-identical replay |
| 同 `:743` `test_receipt_same_operation_different_payload_is_rejected` | direct consumer `:754,761` | `F` | 1回目に書込み、2回目は意図した REPLAY |
| `orchestrator/tests/test_reflux_origin_client.py:169` `test_read_reserve_commit_and_seal_reject_absent_capability` | client method `:194` | 定数 `"seal-none"` | capability 検査で終了。consumer 未到達 |
| 同 `:352` `test_p6_unavailable_can_only_commit_aborted_origin` | client → consumer `:371` | 定数 `"typed-terminal"`、receipt 側 `:359` | 書込みあり |
| 同 `:383` `test_receipt_rejects_wrong_input_state_commitment` | client → consumer `:392` | 定数 `"wrong-state"` | STATE。書込なし |
| 同 `:401` `test_receipt_rejects_wrong_terminal_payload_digest` | client → consumer `:420` | 定数 `"wrong-payload"` | PAYLOAD。書込なし |
| 同 `:436` `test_client_rederives_projection_evidence_references`、2 parameter | client method `:453` | `"wrong-projection-" + field`、生成元 `:442` | client の projection 検査で終了。consumer 未到達 |
| 同 `:461` `test_client_rederives_receipt_evidence_root_from_digest_list` | client method `:499` | 定数 `"wrong-receipt-evidence-root"`、`:467,473` | evidence 検査で終了。consumer 未到達 |
| 同 `:507` `test_formal_receipt_exact_replay_matches_ledger_replay` | client → consumer `:515,521` | 定数 `"terminal-replay"` | 1回目に書込み、2回目は exact replay |
| `orchestrator/tests/test_p3_autonomous_workload_trial.py:6561` `test_origin_public_path_preserves_capability_identity_and_projects_terminal` | public origin → consumer `:6613` | `P(tmp_path)`、`:6564-6566` | 書込みあり |
| 同 `:6649` `test_origin_client_omission_is_typed_preflight_before_production_resolution` | public origin `:6665` | `P(tmp_path)` | client `None` を `p3_autonomous_workload_trial.py:2931-2935` で拒否。consumer 未到達 |
| 同 `:6675` `test_origin_arguments_are_all_or_none_before_artifact_creation` | public entry `:6683,6687` | `P(tmp_path)` | pair 検査 `p3_autonomous_workload_trial.py:2916-2919,3261-3265` で終了 |
| 同 `:6695` `test_origin_request_rejects_unregistered_exploratory_admission` | public origin `:6710` | `P(tmp_path)` | runtime 準備 `p3_autonomous_workload_trial.py:3006-3021` より前に終了 |
| 同 `:6720` `test_origin_public_result_distinguishes_partial_from_completed` | public origin → consumer `:6726` | `P(tmp_path)`、`:6723-6724` | partial report でも `_complete_origin_runtime` が走るため書込みあり |
| `orchestrator/tests/test_reflux_originless_compatibility.py:581` `test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set` | helper `:590` → public origin `:94-108` | `P(_fixed_width_bundle_root(tmp_path,...))`、`:124-130` | 書込みあり |

したがって、live cache に残り得る ID は、互いに異なる `"typed-terminal"`、`"terminal-replay"` と、test ごとの `tmp_path` 由来 `P(path)` だけである。`F` の再利用は既存 file-local fixture で隔離されている。

親の6 fileのうち、次は実行到達ではなく静的参照だけである。

- `orchestrator/tests/test_reflux_origin_ledger.py:931` は `:990` で method の signature を検査するだけ。subprocess も client import `:1815` 後に `read_origin` `:1829` を呼ぶだけ。
- `orchestrator/tests/test_trial_registry.py:888,1792` は projection serializer `:904,1840` のみで、receipt、consumer、cache に到達しない。
- `orchestrator/tests/test_reflux_originless_compatibility.py:568` は origin 引数なしの `run_trial` だけで、origin runtime を作らない。

### `_ISSUED_RECEIPTS`

`_ISSUED_RECEIPTS` は `operation_id` を key にしない。各 `FormalConsumerReceipt` の生成ごとに新しい `object()` を作り `orchestrator/campaign/reflux_formal_consumer.py:219,237`、その object を key に `:922` で保存し、同じ receipt の seal だけを `:393` で参照する。dict が key object 自身を保持するため、残留中に別 receipt が同じ key identity を得ることもない。

全書込 test は以下である。

| file | `_ISSUED_RECEIPTS` を書く test 全数 | 書込経路 |
|---|---|---|
| `test_reflux_formal_consumer.py` | `:331`, `:671`, `:698`, `:711`, `:725`, `:743`, `:770` | `_evaluate` `:313-316` → `_issue_receipt`。`:743` は receipt 2個。既存 fixture `:196-202` で隔離 |
| `test_reflux_origin_client.py` | `:352`, `:383`, `:401`, `:436` の2 parameter、`:461`, `:507` | `_p6_result` が `:133-150` で直接登録。`:461` は forged receipt も `:472-489` で登録 |
| `test_p3_autonomous_workload_trial.py` | `:6561`, `:6720` | `_complete_origin_runtime` → `evaluate_formal_origin` → `_issue_receipt` |
| `test_reflux_originless_compatibility.py` | `:581` | `_origin_enabled_bundle` `:94-108` から同じ production 経路 |

従って `_ISSUED_RECEIPTS` の test 間残留は現在、照合衝突ではなく不要な object/bytes の保持だけである。seal の移植、上書き、再利用をする test も存在しない。

## 実装案の比較

### (a) 何も実装しない

コード差分はゼロ。T-1049 は `orchestrator/tests/test_p3_autonomous_workload_trial.py:6494-6497` で前提解消済みとして閉じる。

成果物影響: 現 main では certified 選択の値・受理集合、材料 `report.json`、`attempts.jsonl`、trial lifecycle の値・digest・参照は全て不変。変更されるのは T-1049 の管理状態だけ。

弱点は、将来この test helper が定数へ戻っても、単独 test では検知できず全走の順序依存赤として再発し得ること。

### (b) 共通 autouse fixture

実装場所は `orchestrator/tests/conftest.py:295-307` の次。既存 fixture をそのまま拡張するなら `test_reflux_formal_consumer.py:196-202` は二重 clear になるため整理が必要。

- `conftest.py:41-59` の plain-import 契約上、formal module の top-level import は避け、fixture 内 import が必要。
- それでも module load が各 workerで強制され、import lookup、setup、teardown、dict clear が全 test node に乗る。静的には `orchestrator/tests` に212 test file、8,421 test function定義があり、parameter nodeはさらに多い。
- test 境界だけで clear するため、同一 test 内の replay は維持できる。
- 一方、定数 `operation_id` の再導入や、本来検出すべき test 間 state leak を毎回消してしまう。今回の旧不具合そのものを緑に隠す fixtureになる。
- `_ISSUED_RECEIPTS` までclearすると、将来 module/session-scoped fixture が発行した receipt を function fixture が無効化する危険もある。

成果物影響: 入れなくても現 main の成果物は不変。具体的な production 成果物差を示せないため、現状では nit。P0 が偽なら report 作成 `p3_autonomous_workload_trial.py:2296-2338` より前に停止し、report/lifecycle の受理集合が変わるが、静的検査はその条件を否定した。

### (c) 定数への巻戻しを殺す pin だけ追加

最小案は `orchestrator/tests/test_p3_autonomous_workload_trial.py:6564-6566` の直後に、`producer.terminal_operation_id` が `P(tmp_path)` と完全一致する assertion を1本追加すること。新しい test node、production変更、cache clear は不要。

利点は、`terminal_operation_id="public-origin-terminal"` への正確な巻戻しを、重い全走や test 順序に依存せず既存の成功 test で止めること。欠点は test helper の実装形を pin し、別の安全な namespace方式にも更新を要求すること。

成果物影響: assertionを入れなくても現 main の成果物は不変なので、DW-G05 上は防御的 nit。将来定数化された場合は receipt record の `operation_id` `reflux_formal_consumer.py:375` と、それから算出される `formal_receipt_sha256` `:401-402` が変わり、衝突時は report/lifecycle terminal の受理が失われる。

### (d) writer closed-set の静的 guard

新規 `orchestrator/tests/test_reflux_replay_cache_contract.py:1` で test source の AST を走査し、consumer/client/public-origin の writer集合と、定数または `tmp_path` 由来という分類を閉集合として pin する案。

これは cache を clear しないため本物の漏洩を隠さず、新規 call site をレビュー対象にできる。一方、alias、helper、動的 dispatchを独自 call graphで追う保守コストがあり、今回の一度限りの静的監査を test suiteへ複製する。

成果物影響: 入れなくても現 main の certified 選択、材料 report、試行台帳は不変で、将来の test追加だけが対象となる。従って現状では nit。

## 推奨と反証条件

推奨は **(a) 何も実装せず、T-1049 を前提解消として閉じる** である。

共通 autouse fixture は8,421以上の testへコストを広げ、既知の定数回帰を隠す。pin や closed-set guard は有効な防御策ではあるが、現 main の成果物や受理集合を変えず、production invariantも既存 test `test_reflux_formal_consumer.py:743-767` ですでに固定されているため、この wave で足す必然性はない。`reflux_formal_consumer.py:1027-1067` は no-touch とする。

この推奨を反証する観測は次のいずれかである。

- 現 HEAD の親による計測で、異なる pytest nodeから同一 `operation_id` と異なる request bytes の成功書込みが記録される。
- `:6494-6497` を旧定数へ戻す事前登録 mutationが既存の焦点検査と受入全走を通過し、managerが「この再発を deterministic に殺すこと」を受入要件と裁定する。この場合は (c) が最小の修正となる。
- `_ISSUED_RECEIPTS` について、別 testの receiptが過去の exact seal objectを再利用する経路が見つかる。この場合だけ同 state の隔離を再検討する。

## 総括

現 main に未隔離の replay-cache 衝突は静的には残っていない。実行到達するのは親の6 file中4 fileで、6 file外の経路はない。`_ISSUED_RECEIPTS` も新規 object seal keyのため test間衝突しない。

従って実装は行わず、特に共通 autouse fixtureは追加しないことを推奨する。pytestは実走しておらず、緑は報告していない。