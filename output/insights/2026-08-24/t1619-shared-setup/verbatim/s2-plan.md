## 総括

- `test_s8c_preregistration_predicates.py:138-175` で snapshot 評価結果を外側 `tuple` にし、既存 module fixture から共有する。
- 同ファイル `:187,:198,:207,:252,:279` の 5 件だけへ `@pytest.mark.xdist_group("s8c-predicate-snapshot")` を付ける。
- `test_real_repo_serialization.py:125-129,1036-1040` に group 名と 5 node の独立 literal oracle を置く。
- exact-match test は共有 snapshot と、実 HEAD を新たに評価した別値を比較し、恒真化を避ける。
- `REAL_REPO_SERIAL_NODES` は不変。現行直列実測 82.93 秒より作業を減らすため、103.0 秒 floor 未満の見込みだが、親の再実測を受入条件とする。

## P1/P2/P3 の判定

### P1: 二点セットは採用。ただし理由の一部は不成立

現在の評価回数は次のとおりである。

| 構成 | snapshot 構築内 `evaluate_all` | 各 test の snapshot 評価 | exact の実 HEAD 評価 | 合計 |
|---|---:|---:|---:|---:|
| 現在の 5 worker 分散 | 5 | 5 | 1 | 11 |
| group だけ | 1 | 5 | 1 | 7 |
| 結果 fixture だけ、5 worker 分散 | 5 | 5 回分を各 worker fixture へ移動 | 1 | 11 |
| group と結果共有 | 1 | 共有 1 | 1 | 3 |

根拠は snapshot 構築内の評価が `test_s8c_preregistration_predicates.py:145-149`、各 test の評価が `:190-191,:201-203,:214-215,:256-257,:283-284` にあること、および module fixture が `:170-175` にあること。worker 分散時に setup が 5 回、直列時に 1 回だった実測は `measurements.md:13-26,34-43` にある。

したがって、「二点セットで完全に共有する」は成立する。一方、「片方だけでは効かない」は文字どおりには不成立で、group だけでも既存 fixture の重複を 5 回から 1 回へ減らす。ただし結果評価は残るので、採るべき実装は二点セットである。

実装は `current_commit_snapshot` を `tuple[Path, str, tuple[core.PredicateResult, ...]]` 相当に拡張し、`test_s8c_preregistration_predicates.py:170-175` で snapshot 結果を一度だけ `tuple(...)` 化する。

### P2: 成立

手書き decorator 禁止は全 test ではなく、呼び出し側から渡された canonical node だけが対象である。

- `_assert_no_direct_xdist_group_decorators` は `canonical_nodes` をファイルと関数へ展開し、その関数だけを AST 検査する: `test_real_repo_serialization.py:935-980`。
- 実際の呼び出しは `REAL_REPO_SERIAL_NODES` をそのまま渡す: `test_real_repo_serialization.py:1310-1318`。
- 対象 5 件は `REAL_REPO_SERIAL_NODES` の literal `conftest.py:338-433` に存在しない。
- group marker の一般契約は「最大 1 個、positional string 1 個、kwargs なし」であり、手書き自体は禁止していない: `test_real_repo_serialization.py:835-860`。
- conftest が `real-repo` を追加するのも `REAL_REPO_SERIAL_NODES` のみで、既存 marker があれば二重追加しない: `conftest.py:1317-1323`。

よって 5 関数へ直接 decorator を付けてよい。`REAL_REPO_SERIAL_NODES` には追加しない。

### P3: 成立

`s8c-predicate-snapshot` は projected source 内の既存名と衝突せず、positional string 契約にも適合する。次を明示更新する。

- `_XDIST_GROUP_NAMES_GOLDEN` に `"s8c-predicate-snapshot"` を追加: `test_real_repo_serialization.py:124-129`。
- 欠落 decorator を名前集合だけでは検出できないため、5 canonical node の独立 literal 集合も同じ golden 節へ追加し、収集結果と照合する: `test_real_repo_serialization.py:124-129,1036-1040`。対象 test 側や conftest から導出してはならない。

現在の全処理を直列化した実測が 82.93 秒である: `measurements.md:28-43`。新実装はそこから snapshot 評価を 4 回削るため、静的には 103.0 秒 floor を超える方向ではない。ただし性能値なので、最終判定は親の同条件実測で行い、103.0 秒以上なら不採用とする。

## 検出力の対応表

| test | 残す assert | 共有後に依存する計算 | 意味保存 |
|---|---|---|---|
| `test_current_repository_snapshot_has_zero_satisfied_predicates` | status 合計 `:192`、evidence 非空 `:193-194`、path と SHA 長 `:195` | fixture が snapshot commit に対して一度実行した `tuple(evaluate_all(head, repo_root=root))` | 全 `PredicateResult` を省略せず共有し、3 assert は変更しない。 |
| `test_current_repository_snapshot_exactly_matches_head` | 完全等値 `:204` | 左辺は共有 snapshot 結果。右辺は従来どおり `evaluate_all("HEAD", repo_root=_ROOT)` をこの test で新規実行する `:203` | 別 root、別 commit 引数、別呼出しの比較なので恒真ではない。 |
| `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` | C01-C12 の全 status/reason literal `:216-249` | 共有結果から同じ `{item.id: (item.status, item.reason_code)}` を計算 | 12 行すべて残り、評価値だけを再利用する。 |
| `test_current_repository_c12_registry_reports_unwired_allocation_consumer` | C12 status/reason `:259-260` | 共有結果から同じ `{item.id: item}["C12"]` を計算 `:258` | assert と C12 選択は不変。 |
| `test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer` | C12 status/reason `:285-286` | `_result` の実体である「全評価して ID map から選択」`test_s8c_preregistration_predicates.py:133-135` を、共有結果への ID map 適用に置換 | `_result` は汎用 test helper であり、固有 production helper 呼出しではない。計算結果と assert は同じ。 |

共有値は外側を `tuple` にして list の append、pop、並べ替え経路を消す。`PredicateResult` 自体の定義は今回の射影外なので深い immutable 性までは断言しないが、対象 5 件には属性代入、evidence の in-place 更新、共有 tuple の更新がない。使用は反復、辞書内包、属性読出し、等値比較だけである: `test_s8c_preregistration_predicates.py:190-204,214-249,256-260,283-286`。

fixture の参照者もこの 5 件だけであり、同じ group により同一 worker へ置かれる。module fixture の再要求は pytest の同一 cached object を返し、fixture 内から自身を呼ぶ再入経路もない。

exact-match test では、次の形を保つ。

```python
root, head, snapshot = current_commit_snapshot
actual = tuple(M.get_registry().evaluate_all("HEAD", repo_root=_ROOT))
assert snapshot == actual
```

`actual = snapshot`、fixture から同じ値を二つ返す案、snapshot 結果を両辺へ使う案は恒真化するため不採用である。

## 負の対照の設計

各変異は別々に適用し、対象 node だけを baseline、変異後の順で実行してから復元する。C12 の 2 件は観測する status/reason が完全に同じなので、production-only 変異で片方だけを赤、他方だけを緑にすることはできない。異なる変異を別 run で各 node に当てる。

| 対象 test | 1 byte 変異 | 期待する赤 |
|---|---|---|
| zero-satisfied | production の `evaluate_all` 出力境界で、ある `EvidenceRef.blob_sha256` の hex 文字を 1 byte 削除し 63 byte にする | `test_s8c_preregistration_predicates.py:195` の `len(...) == 64`。status と evidence 非空は維持し、狙った assert で赤にする。 |
| exactly-matches-head | snapshot 側だけで、`_write(... CONTRACT_FILE.read_bytes())` `:166` の後、commit `:167` の前に JSON whitespace 1 byteを別の有効 whitespace へ置換する | 意味上の status/reason は同じだが contract blob SHA が異なり、`:204` の完全等値だけが赤になる。 |
| gap-reason | snapshot 内の `p3_autonomous_workload_trial.py` にある `MAX_APPROVED_GENERATIONS = 2` の `2` を `1` へ置換 | C11 が `generation-cap-not-lifted` 側へ移り、`:244` の C11 literal が赤になる。この変異契約は `:1127-1133,3231-3246` に既存根拠がある。 |
| C12 registry | snapshot 内の実 consumer call の `check_reservation` 最終 `n` を `x` へ置換 | C12 が `allocation-enforcement-consumer-absent` へ移り、`:259-260` が赤になる。既存 control は `:1134-1154`。 |
| C12 binding helper | snapshot 内の実 consumer call の `read_binding` 最終 `g` を `x` へ置換 | C12 の同じ status/reason 変化を `:285-286` が検出する。read-binding edge の既存 control は `:983-999`。 |

production source 本体は今回の許可射影に含まれないため、source の byte offset や file:line は捏造できない。実装子は各 anchor が production source に一意に存在することを先に検査し、一意でなければその変異を実行してはならない。

exact-match について、両評価より前に同じ production byte を静的に変えるだけでは双方へ同じ変更が入り、等値が保たれ得る。これは `:138-143` の docstring が述べるとおり resolver mutation の kill test ではなく、snapshot と HEAD の commit-blob 投影同値性検査だからである。したがって exact 用の正しい負例は、上表のように snapshot 側だけを 1 byte 変える非対称変異である。

## consumer 列挙

| consumer | 波及と plan |
|---|---|
| 対象 5 node の収集 nodeid | pytest/xdist 上では末尾に `@s8c-predicate-snapshot` が付く。source test 名は不変。 |
| group 名 oracle | `test_real_repo_serialization.py:125-129` に新名を literal 追加する。 |
| group membership | 名前集合だけでは decorator 1 件の欠落を検出できないため、同ファイル `:124-129` に 5 canonical node の独立 literal、`:1036-1040` に exact membership assert を追加する。 |
| collection report | marker の canonical node、fixture closure、args を収集する `test_real_repo_serialization.py:546-568` が新 marker と module fixture を観測する。 |
| marker shape 契約 | `_assert_xdist_group_contract` `:835-864` が marker 1 個、positional string、group 名閉包を検査する。 |
| decorator provenance | `_assert_no_direct_xdist_group_decorators` `:935-988` は REAL canonical だけが対象。対象 5 件は射程外。 |
| shared fixture closure | `_assert_fixture_closure_complete` `:898-932` は REAL canonical と交差する fixture だけを seed にする。新 fixture は対象 5 件だけなので `REAL_REPO_SERIAL_NODES` 追加は不要。 |
| REAL_REPO_SERIAL_NODES | `conftest.py:338-433`、付与 hook `:1317-1323`、priority `:1400-1416` は変更しない。 |
| shard assignment | `test_real_repo_serialization.py:1152-1167` が全 live group を `ItemRecord` にし、group closure を検査する。新しい 5-node component が割れないことをこの test で確認する。 |
| loadgroup scheduler | `conftest.py:1026-1044` が loadgroup 時だけ台帳 reorder を有効化し、`:904-908,947-979` が同じ suffix を一つの work unit として所要値を合算する。live 同一 worker 契約は `test_real_repo_serialization.py:3737-3792`。 |
| duration ledger runtime lookup | `conftest.py:911-921` は `@group` を除いて ledger lookup する。従って ledger key は suffix なしのまま、再実測後の duration 値だけを更新する。 |
| ledger 更新 tool | 親の地図が示す `tools/update_acceptance_duration_ledger.py:28` の `_strip_group_suffix` も suffix を落とす。位置の根拠は `measurements.md:73-75` で、本体は今回の射影外。変更不要だが、再生成時の回帰確認対象。 |
| acceptance duration 台帳 | 現状値と stale entry は `measurements.md:51-59`。新 group により collected nodeid は変わるが、正規化後の JSON key は変えない。5 件の値は親の after 実測で更新する。stale 6 件目の整理は T-1620 で、本実装に含めない。 |

期待される収集 nodeid は次の 5 件である。ledger key と焦点指定では `@...` を除いた形を使う。

```text
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_snapshot_has_zero_satisfied_predicates@s8c-predicate-snapshot
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_snapshot_exactly_matches_head@s8c-predicate-snapshot
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review@s8c-predicate-snapshot
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_c12_registry_reports_unwired_allocation_consumer@s8c-predicate-snapshot
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer@s8c-predicate-snapshot
```

許可された 3 source を literal 検索した範囲では、新 group 名の既存 consumer はない。

## 実装単位と焦点テスト

実装子は 1 本にまとめる。変更が同じ fixture、5 consumer、collection oracle の一つの原子的契約だからである。

1. `test_s8c_preregistration_predicates.py:138-175` で snapshot 結果を外側 `tuple` として module fixture に格納する。
2. 同ファイル `:187,:198,:207,:252,:279` に同じ direct decorator を付け、`:190-204,:214-249,:256-260,:283-286` を共有結果の読出しへ変更する。assert と関数名は全て残す。
3. `test_real_repo_serialization.py:125-129` の独立 group 名 oracle と 5-node oracle、`:1036-1040` の membership 検査を更新する。
4. `conftest.py:338-433` と `REAL_REPO_SERIAL_NODES` 関連箇所は変更しない。
5. 実装後、親が同条件 before/after と新 group 鎖長を測り、103.0 秒未満を確認してから duration 値を更新する。

焦点 nodeidは suffix なしで指定する。

```text
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_snapshot_has_zero_satisfied_predicates
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_snapshot_exactly_matches_head
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_c12_registry_reports_unwired_allocation_consumer
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer
orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes
orchestrator/tests/test_real_repo_serialization.py::test_canonical_real_repo_nodes_have_no_handwritten_xdist_group_decorator
orchestrator/tests/test_real_repo_serialization.py::test_shard_assignment_preserves_live_xdist_group_components_and_split_control
orchestrator/tests/test_real_repo_serialization.py::test_loadgroup_scheduler_keeps_same_group_on_one_worker_and_control_detects_absence
```

この段では read-only 条件どおり実走しておらず、緑とは報告しない。