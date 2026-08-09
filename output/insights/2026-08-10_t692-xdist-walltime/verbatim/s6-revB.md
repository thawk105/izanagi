判定は **NO-GO**。pytest の実走はしていません。

### 1. receipt payer が D63 閉包の外に残っている

- **重大度**: Critical
- **主張 / 根拠**: 並べ替え対象は `REAL_REPO_SERIAL_NODES` 内だけです（`conftest.py:261-275`）。一方、payer の `test_oracle_pipeline_contract_keyword_is_mandatory_positive_control` は canonical group 外で、`_run()` は実 repo の receipt memo を使います（`test_s8b_oracle_driver.py:1520-1555,2471-2488`）。cache/lock 失敗時は `_resolve_now()` へ fail-open します（`real_repo_receipt_memo.py:116-163`）。
- **再現条件**: 48 worker 全走で、payer と `real-repo` group が別 worker に割り当てられ、cache 不在・lock 失敗・store 失敗のいずれかが起きる。payer の実 repo 読み取りが submodule writer の patch 窓と重なる。
- **直し方**: payer を含む全 real-repo reader/writer を同一 group に閉じ込めるか、memo の fail-open を廃止して実 repo 用の明示的な read/write lock を導入する。順序定数だけでは閉包になりません。

### 2. collection 順は実行開始順を保証せず、性能予測も崩れる

- **重大度**: Major
- **主張 / 根拠**: 差分は canonical item の slot だけを入れ替えます（`conftest.py:264-275`）。`loadgroup` の scheduler は scope 数で並べ替えます（pytest-xdist 3.8.0: `xdist/plugin.py:130-140`, `xdist/scheduler/loadscope.py:374-382`）。監査（`test_real_repo_serialization.py:447-475`）は collection 配列しか見ません。
- **再現条件**: 通常の `tools/run_tests.py` の `--dist loadgroup` 全走で、payer の module scope が先に割り当てられる、または逆に group が先行する。collection audit は通過しても payer / CLI / binding の開始順が変わる。
- **直し方**: 実 scheduler の開始・終了時刻と cache owner を記録する acceptance control を追加する。`--no-loadscope-reorder` は必要条件になり得ますが、cross-group 同期の代替にはなりません。
- **性能影響**: baseline の `real-repo` 直列和 1388.80 秒に T-438 の 69.45 秒を加えると、同条件では group 下界は **1458.25 秒**です（`s1-measurement.md:16-24,81-83`）。875.67 秒は同時開始を仮定した条件値にすぎません（`s3-lensB.md:14-28`）。

### 3. T-438 の snapshot が Git index/env 契約を揃えていない

- **重大度**: Major
- **主張 / 根拠**: T-438 は `repo_tree_util.assert_repo_tree_unchanged()` を呼びます（`test_ruleops.py:2037-2063`）。helper の `git status` は timeout、`--no-optional-locks`、Git 環境の除去を持ちません（`repo_tree_util.py:16-23`）。対して RuleOps 本体は `GIT_*` を除去し、`GIT_OPTIONAL_LOCKS=0` を設定します（`tools/ruleops.py:306-318`）。
- **再現条件**: `GIT_INDEX_FILE` などが継承される、または別 worker の Git 処理が index lock を保持している状態で T-438 が開始される。snapshot 側と inventory 側が別 index を見たり、status が失敗・長時間停止する。
- **直し方**: snapshot と inventory で同一の Git 環境を使い、`--no-optional-locks` と bounded timeout を付ける。index を共有する reader/writer の lock 契約も明示する。

### 4. RuleOps 固定 20 秒 timeout が全走だけで再発し得る

- **重大度**: Major
- **主張 / 根拠**: `tools/ruleops.py:42,347-356` は全 Git subcommand に 20 秒固定 timeout を掛けます。T-438 は全履歴 inventory を実行します（`test_ruleops.py:2038-2047`）。同 node の `git log timeout` は受入全走で独立に 3 回記録されています（`docs/worklog.md:3346-3353`）。
- **再現条件**: 48 worker の計算ノードで Git object/I/O 競合が発生し、inventory 内の `git log` が 20 秒を超える。単独の `-n 0` 走は通っても、全走は rc 非 0 になる。
- **直し方**: T-510 として履歴量・要求量に基づく timeout 予算を別途裁定・実装するか、明示 waiver を用意する。group 順序変更では per-command timeout は直りません。

### 5. 正しい手書き `real-repo` marker は監査をすり抜ける

- **重大度**: Minor
- **主張 / 根拠**: hook は既存 marker があれば skip します（`conftest.py:255-259`）。監査は marker の形しか確認しません（`test_real_repo_serialization.py:506-510`）。canonical node に直接 `@pytest.mark.xdist_group("real-repo")` を付けても通過します。synthetic meta-test 自体がこの形を事前に付けています（同:625-629）。
- **再現条件**: T-438 などへ underscore ではなく、正しい positional `"real-repo"` の手書き marker を戻す。
- **直し方**: canonical node の直接 marker を AST/source 検査で禁止するか、hook が付与した provenance を監査対象にする。

収集 mismatch そのものは、現在の xdist 3.8.0 では controller が収集を抑止し、各 worker が同じ全 collection を送るため、この差分の決定性だけからは Critical と断定できません。ただし audit subprocess は xdist なしの単一 collection なので、実 worker 間の一致は全走で確認が必要です。

T-553 については、現在の group は `s8c-preregistration-candidate` を含む 3 名の golden に入っています（`test_real_repo_serialization.py:86-91`）。未知 group で失敗する仕様は、現状は意図した fail-closed と判断します。

## 総括

- **NO-GO**
- Critical: **1件**
- Major: **3件**
- Minor: **1件**
- **親が全走の前に必ず確かめるべきこと**:
  - 48 worker 全走で worker collection mismatch がないこと。
  - payer、CLI、binding、writer の実際の開始順・cache owner・lock 状態。
  - T-438 の `git log` timeout、index lock、`GIT_*` 継承。
  - `real-repo` group 直列和と wall の実測値。
  - 正しい手書き marker と優先順反転の mutation 検出。