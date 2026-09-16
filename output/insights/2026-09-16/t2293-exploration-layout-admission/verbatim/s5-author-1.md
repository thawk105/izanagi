## 変更 file と差分の要約

指定の3ファイルに実装しました。commit は作成していません。

- `orchestrator/campaign/reflux_result_evidence.py`：import、両 exact-type gate、`_context_roots` の注釈を変更。全6変異の `old` anchor と完全一致を確認。
- `orchestrator/tests/test_reflux_result_evidence.py`：探索 layout 正例、両入口の型負例、root 外負例を追加。
- `orchestrator/tests/test_reflux_campaign_issuer.py`：`_drive_campaign` の use class を引数化し、探索統合テストを追加。

変更前：探索 layout は `"layout must be an exact CampaignLayout"` で拒否されていました。
変更後：exact な両 layout が型 gate を通り、subclass・duck・型等価 impostor・非 layout は拒否され、既存の包含検査と発行条件も維持されます。

## 新設・変更 test の nodeid 一覧

新設20 node、変更2 nodeです。parametrize id を含む一覧は末尾の「総括」に記載します。

## 実走した検査と結果 (実走していないものは「未実走」と明記)

- `PYTHONPATH=.`、`tempfile.mkdtemp()` 配下で直接呼出し：新設・変更の単体21ケース、既存 `test_campaign_producer_*` の残り13ケース、計34ケース成功。
- M1／M2／M5：登録された projection 負例すべてで `DID NOT RAISE` を確認。
- M3／M4：登録された単体観測点で赤化を確認。M4 の root 外負例は拒否地点が前に移り、期待文言不一致になりました。
- M6：探索単体正例1ケースのみ成功。全観測集合の SURVIVED 判定ではありません。
- 変異はメモリ上で適用し、`finally` で復元。production ファイルの不変を確認。
- AST 検査、`git diff --check` 成功。

指定 runner は `qstat -Q` preflight 失敗で rc=16、子プロセス未起動です。**pytest による2モジュール全走は未実走**です。

探索統合テストは直接呼出しを実施しましたが、実 `run_campaign` 内でログインノードの build guard が CMake configure を拒否しました。verifier 到達・統合成功は未確認です。compiler 不在による skip ではありません。M3／M4 の統合観測点、consumer tests も未実走です。

## 波及可能性の静的列挙

- `_producer_layout` の既存 caller は同一テストモジュール内。既定 official を維持し、既存13ケースの直接実行も成功しました。
- `_issue_producer_record` の注釈変更はテスト入力型の拡張のみで、実行処理は不変です。所有外からの直接参照は検索で見つかりませんでした。
- `_drive_campaign` の既存 caller は `_drive_required_campaign` と `test_originless_campaign_has_legacy_literal_artifact_and_wal_shape`。既定 official を維持していますが、既存統合テストは未実走です。
- production caller は `loop._issue_campaign_result_evidence`。共有 `reflux_origin_fixture_builder` は未変更です。
- `reflux_formal_consumer` は parse／resolve を利用し、consumer test は production source の AST も検査します。該当処理・schema は未変更ですが、consumer 全体の無影響までは実証していません。

## 総括

変更関数は、production の `_ordered_attempt_materials`／`_context_roots`／`issue_campaign_result_evidence`、テスト helper の `_producer_layout`／`_log_producer_attempt`／`_issue_producer_record`／`_drive_campaign`、以下のテストです。単体負例用に fixture・入力生成・拒否検証 helper 7関数も追加しました。

以下は `orchestrator/tests/test_reflux_result_evidence.py::` に続く nodeid です。

```text
test_campaign_producer_issues_real_wal_projection_and_resolves_interval[official]
test_campaign_producer_issues_real_wal_projection_and_resolves_interval[exploration]
test_campaign_producer_refuses_layout_subclasses_before_writes[official]
test_campaign_producer_refuses_layout_subclasses_before_writes[exploration]
test_campaign_producer_refuses_duck_layout_before_writes[frozen]
test_campaign_producer_refuses_duck_layout_before_writes[namespace]
test_campaign_producer_refuses_non_layout_values_before_writes[str]
test_campaign_producer_refuses_non_layout_values_before_writes[path]
test_campaign_producer_refuses_non_layout_values_before_writes[none]
test_campaign_producer_refuses_type_equality_impostor_before_writes[official]
test_campaign_producer_refuses_type_equality_impostor_before_writes[exploration]
test_campaign_producer_refuses_exploration_root_outside_evidence_root_before_writes
test_ordered_wal_projection_refuses_layout_subclasses[official]
test_ordered_wal_projection_refuses_layout_subclasses[exploration]
test_ordered_wal_projection_refuses_duck_layout[frozen]
test_ordered_wal_projection_refuses_duck_layout[namespace]
test_ordered_wal_projection_refuses_non_layout_values[str]
test_ordered_wal_projection_refuses_non_layout_values[path]
test_ordered_wal_projection_refuses_non_layout_values[none]
test_ordered_wal_projection_refuses_type_equality_impostor[official]
test_ordered_wal_projection_refuses_type_equality_impostor[exploration]
```

新設統合 nodeid：

```text
orchestrator/tests/test_reflux_campaign_issuer.py::test_real_run_campaign_exploration_issues_rejected_record
```

上記単体21 node は直接実走成功。統合1 node は実走を試みましたが build guard で完了できず、pytest 全走・consumer・完全な変異全走は未実走です。残る懸念は、実行可能な環境での統合検証です。最終差分は所有3ファイルのみで、runner が生成した一時成果物は撤去済みです。