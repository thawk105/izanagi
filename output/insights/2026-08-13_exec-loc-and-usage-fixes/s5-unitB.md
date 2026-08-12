## 変更したファイルと差分の要約 (file:line)

- [tools/claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/tools/claude_session_ledger.py:7)
  - canonical `message.id` 一致を model call 同一性の公理として明記。
  - `message.id` の上限を 256 ASCII 文字に限定。
  - member-local 検証、usage dominance、model・tool・request identity 検証からなる 3 相 resolver を追加。
  - `population.request_identity` を更新し、`dedup_algorithm_version` と旧台帳との比較不能性を追加。

- [test_claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/orchestrator/tests/test_claude_session_ledger.py:472)
  - 指定された正例・負例に加え、tool subset、model 一致、terminal usage、root 帰属、request collision の全 replica 伝播を追加。
  - `parentUuid`・`agentId` が異なる 4 replica fixture を実測群 1 相当にした。

## resolver の相構造と、各相で何を書き何を書かないか

- 相 1: alias conflict、timestamp・usage anomaly、terminal usage 欠落、usage regression などを全 member について計算する。代表写像と最終 invalid 集合は書かない。
- 相 2: message 群と、代表へ写像後の request 群をローカル計画上で検証する。canonical ID、全 terminal usage、全 `USAGE_FIELDS` の dominance、model 一致、tool subset、request ID 整合を確認する。`parentUuid` と `agentId` は比較しない。
- 相 3: 全検証後に代表写像、root/sidechain 帰属、invalid 集合を一括適用する。代表が invalid になった場合は全 replica を invalid にする。

## 現行の受理・拒否挙動 → 変更後の受理・拒否挙動

- 従来 fatal だった検証済み同一 usage replicaと、支配可能な部分 snapshotを 1 call として受理する。
- 等値 replica は決定的代表へ集約する。
- 比較不能 usage、異なる request ID、model 不一致、tool 非包含、非 canonical ID、loser anomaly は引き続き fatal。
- request ID が代表写像後も複数 model call を指す場合は `request_id_collision` のまま fatal。
- root member が一つでもあれば、支配 memberがsidechainでもrootへ1回だけ帰属する。

## 過大計上・過小計上を防ぐ根拠 (どのテストがどちらを落とすか)

- 過大計上:
  - `test_replicated_message_id_with_identical_usage_counts_once` が4重計上を検出。
  - `test_partial_snapshot_replica_uses_dominating_usage` が部分 snapshot の二重計上を検出。
- 過小計上:
  - `test_incomparable_usage_replicas_remain_fatal` が各 usage field を無視した誤統合を検出。
  - `test_same_message_and_usage_with_different_request_ids_remains_fatal` が別 request の統合を検出。
  - tool・model・terminal usage・noncanonical ID の各負例も誤統合を拒否する。
- anomaly 隠蔽:
  - `test_replica_loser_anomaly_is_not_hidden_by_representative` が loser の usage regression 消失を検出。
- request collision:
  - `test_request_collision_invalidates_representative_and_all_replicas` が代表だけを無効化して loser を計上する退行を検出。

## 実走した nodeid と結果

pytest 本体は実走できておらず、緑とは報告しない。

- `orchestrator/tests/test_claude_session_ledger.py` 全体
  - `tools/run_tests.py` 経由で試行。
  - pytest 収集前に `qstat -Q preflight rc=1`、runner `rc=16`。
- 新規主要 5 nodeid の焦点走
  - 同じく収集前に runner `rc=16`。
- `--collect-only`
  - 同じく runner `rc=16`。

Pegasus login の観測 headroom は最終確認時約 0.50 GiBで、直接 pytest への迂回は規律上行っていない。AST parse と `git diff --check` は成功したが、pytest の緑には数えていない。

## 既存テストで期待値を変えたもの (あれば。無ければ「なし」)

`test_request_dedupe_uses_final_usage_and_all_three_input_fields` の `population.request_identity` を新しい意味へ更新し、dedup version／比較不能性の期待を追加した。

`test_raw_ids_do_not_merge_across_file_or_sidechain_provenance` と `test_strict_issue_matrix_covers_every_classification` の期待値・分類集合は一切変更していない。

## 所有外への波及可能性

- `tools/collect_wave_usage.py`: `collect_report()` の直接 caller。replica を含む入力では model call・token 合計が正しい1回分へ変わり、保存する `ledger_report.population` に新フィールドが増える。
- `orchestrator/tests/test_collect_wave_usage.py`: actual ledger を使う selector testと、mock report fixtureがある。単一 file の計上は不変だが親の統合走対象。
- `hooks/guard_bash.py`、`orchestrator/tests/test_hooks.py`、`test_check_docs.py`: ledger の admission class・pathを参照するが、本変更は admission bitを変えない。
- 共有 fixtureは所有テスト内の `_assistant()` のみ拡張。外部共有 fixtureの変更はない。
- repo内検索では、旧 `request_identity` の完全一致 consumerは所有テスト以外に見つからなかった。
- docsと実 transcript全走は親担当。実1,045 file／30 collision群がすべて解決するかは未確認。

## 総括

指定された2ファイルだけを変更し、canonical `message.id` を軸とする3相 replica resolver、usage dominance、tool・model・request検証、root帰属、request collisionの全component無効化、dedup version識別を実装した。4 replicaと部分snapshotの正例、比較不能・異種request・loser anomaly・非canonical IDなどの負例を追加し、過大計上と過小計上の双方を固定した。既存のcollisionおよびstrict分類tripwireは弱めていない。pytestはPegasus基盤障害により未実走であり、親はheadroomまたはqueue復旧後に対象ファイル全体を再走する必要がある。