# [T-091][T-092][T-093] hardening wave の子出力逐語 — 2026-07-26

本 wave の codex 子出力を逐語で凍結する。親の裁定・実測は材料レポート
(`2026-07-26_t091-t093-hardening.md`) を正本とし、本文書は一次資料としてのみ参照する。
各節は生成順。子の主張は**親が検証した範囲でのみ**採用しており、逐語そのものは裁定ではない。

---

## 段2 プラン起草 (codex, read-only, reasoning=max)

# 実装プラン v1

基準 `be40317` に対する静的読解結果である。コード編集・`pytest` 実行は行っていない。

## 1. 現行の受理・拒否挙動

### T-091 の現状

- [`_valid_receipt()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:51) は `source_repins`、`metadata_fields`、`reconstruction`、`repin_report` に schema-valid な合成値を入れる。
- [`test_deterministic_fields_and_reconstruction_rerun_reject_mismatch_f2()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:379) は、一致した決定論 field を受理し、`repin_report[0].diff_summary.new_line_count` の不一致を `_assert_deterministic_fields()` の直呼びで `receipt.derivation_mismatch` として拒否する（392–397 行）。
- 一方、public 経路の正例 [`test_state_active_valid_after_schema_topology_and_all_independent_gates()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:525) は `_patch_full_gate_to_pass()` を使う。その helper は `_verify_receipt_derivation` を対象に含め（342 行）、355 行で no-op に差し替える。このため、schema/topology が正しければ、H_mig 再導出値と不一致でもこの正例上は `active-valid`、refusal 空として受理されうる。
- production 自体は `_verify_receipt_derivation()` が再導出後に `_assert_deterministic_fields()` を呼び（[`1113–1118 行`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1113)）、不一致を `receipt.derivation_mismatch` にする。欠けているのはこの挙動を public `verify_receipt()` から撃つ負例である。

### T-092 / T-093 の現状

対象は [`test_real_freeze_gate_lists_floor_and_budget_null()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1186)。

- `_independent_t080_receipt_blob()` は履歴に receipt path の commit がなければ `None` を返す（[`136–147 行`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:136)）。
- `None` の場合、テストは legacy source drift 2 件と floor/budget null 2 件の計 4 refusal を受理し、observation `None` を要求する（1190–1200 行）。したがって post-R の現リポジトリで R が見つからなくても緑になり得る。
- R が見つかった場合は、`verify_receipt()` の `active-valid`、gate の refusal `{floor-null, budget-null}`、GateDecision の observation `None` を要求する（1201–1211 行）。ただし `_introduction` は捨てられ、R OID を確認していない。
- `expected_items` の 13 source-repin は receipt の `record["migration_blob_sha256"]` を expected に流用し（1214–1220 行）、metadata 2 件も同様である（1221–1226 行）。recorded 値・shape・順序は固定するが、15 個の observed 値そのものは独立 oracle になっていない。
- ancestry 2 件だけは `_independent_ancestry_item()` が Git を直接調べる（[`150–172 行`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:150)）。
- GateDecision の observation が `None` なのは、floor/budget refusal が残ると `_make_gate_decision()` が envelope を抑止する production 契約による（[`111–122 行`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_driver.py:111)）。17 items は `ReceiptResolution` 側だけに存在する。

## 2. U1 の設計

### fixture の選択と拡張

`test_t080_freeze_migration.py` 内で `_t080_repo` 相当なのは [`_repo_with_schema_valid_receipt()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:319)（319–333 行）である。

- `TemporaryDirectory` 内で独立 Git repo を作る。
- basis commit を作り、canonical な active receipt を追加する。
- R は receipt と、オプション指定時の `extra.txt` だけを追加し、`AI-Agent` trailer も制御できる。

[`_repo_with_receipt()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:307) は receipt bytes が `{}` のため schema-invalid であり、U1 には不適切。

ただし現行 `_repo_with_schema_valid_receipt()` の basis は `base.txt` しか持たず、receipt の決定論 field も `"b"*64` 等なので、そのままでは production derivation を完走できない。319–333 行を次のように後方互換で拡張する。

1. 既存 caller を変えない既定値 `derivation_ready=False` を追加する。
2. `True` のとき、basis commit へ以下を配置する。

   - `KNOWN_AXES_REL` と `HOLDOUT_REL` の byte-exact な凍結 JSON。
   - `SOURCE_REPIN_SPECS` と `METADATA_SPECS` が参照する全 path。重複を除けば現行は 6 path。
   - source path を含む commit graph。これにより `_build_repin_report()` が全 path を読める。

3. 新 basis と copied artifact を使って production `_derive_deterministic_fields()` を一度呼び、`artifacts`、`source_repins`、`metadata_fields`、`repin_report`、再構成 hash を schema-valid receipt へ反映する。
4. 改竄 callback を適用してから canonical bytes を書き、R commit を作る。commit 後の worktree 改竄にすると `receipt.issued_but_missing` が先に出るため禁止する。

### `_patch_full_gate_to_pass()` の回避方法

helper 自体は利用するが、返された production 関数を使って次の 2 関数だけ戻す。

- `_load_artifact`
- `_verify_receipt_derivation`

`_verify_receipt_derivation` だけ戻し、`_load_artifact` を346行の `{}` stub のままにすると、`known` / `holdout` の pointer 解決が `receipt.repin_invalid` になり、狙った比較へ届かない。

その他の重い独立 gate は stub のままにする。`verify_receipt()` の順序は次のとおりである。

1. history/schema/topology（[`1855–1860 行`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1855)）
2. known/holdout artifact bytes（1862–1881 行）
3. ancestry 2 件（1882–1900 行）
4. positive control、live scan、current ccbench（1901–1912 行）
5. gitlink、known closure、schema、pairing（1913–1919 行）
6. holdout closure、metadata closure、最後に derivation（1920–1925 行）
7. 各 check は1926–1935行で個別収集される。完全な fail-fast ではないが、receipt または artifact load が失敗すると derivation 自体が list に追加されない。また他 gate の失敗は exact-singleton refusal を壊す。

完全 stub-free にするなら、fixture はさらに positive fixture、holdout live scan、ccbench checkout と H_mig gitlink、63/12/51 closure、known schema/pairing、holdout/metadata closureまで満たす必要がある。これは [`_t080_stub_free_e2e_repo()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:293) 相当の重い fixture になるため、今回の単一 derivation 負例には過剰である。

### 改竄 field

`reconstruction.holdout.projected_document_sha256` を選ぶ。

- schema は holdout reconstruction の `status == "pass"` と各 hash の64桁形式だけを要求する（[`465–478 行`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:465)）。
- known 側にだけ projected/rebuilt の相等制約がある（479–480 行）。holdout projected の1 nibble変更は schema-valid のままである。
- source/metadata/repin report の cross-field に触れないため、`receipt.repin_invalid`、source closure、metadata closureを直接発火させない。
- `_verify_reconstruction_static` は public `verify_receipt()` の check listにはなく、変更値を public 経路で拒否するのは derivation comparison（1103–1110 行）だけである。
- 値は先頭 nibbleを `0`、元が `0` なら `1` に変え、必ず異なる64桁 hexにする。

### 追加テストと assert

[`test_deterministic_fields...`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:379) の直後へ public 負例を追加する。

assert は包含ではなく、次の ordered 1-tuple 完全一致とする。

```text
(
  "migration-receipt-verify: [receipt.derivation_mismatch] "
  "reconstruction.holdout.projected_document_sha256 が H_mig 再導出値と不一致",
)
```

併せて次を要求する。

- `result.state == "invalid"`
- `result.t080_freeze_migration_observation is None`

これにより、狙った derivation refusal 以外が混入した fixture 不備も検出できる。

## 3. U2 の設計

### T-092: R OID pin

P2 の「pre-R 分岐を削除し post-R 固定」は妥当である。

- `ROOT` は現在の real repo 固定で、R 発効は歴史事実である。
- pre-R 挙動は別の hermetic test [`test_t080_gate_hermetic_primary_states_exact()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1253) の `never-issued` case（1281–1288 行）が保持している。
- real-repo golden に互換分岐を残す必要はない。

1187–1201 行を次の形にする。

1. `assert independent is not None`。
2. `introduction, raw = independent`。
3. `introduction == "8bec195d096f852fd2b47070aa18a3b151613f0a"`。
4. `hashlib.sha256(raw).hexdigest() == "b84f783218496f0750ed583a317be474a2207b3fe5661a67fab54b2d53723e3c"`。
5. 以後は現行 post-R body のみを実行する。
6. expected envelope の `migration_basis_commit` も receipt 自身から取らず、`"f04ae50b3c7be800885447be514b59f2405a4e83"` を使う。

したがって P2 に対案は出さず、R raw SHA-256 と H_mig literalも同時に固定する強化案とする。

### T-093: observed の意味と導出コマンド

[`_basis_blob()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:722) は Git blobの内容 bytesを返す。`_derive_repins_and_metadata()` はその bytesへ `_sha256()` を適用する（[`1238–1252 行`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1238)）。

したがって observed は40桁の Git blob OIDではなく、blob内容の64桁 SHA-256 である。例えば同じ path でも次の2値は別物である。

```text
git blob OID: f80660188169f3d86d4e655f793ec3c242b52dc3
内容 SHA-256: 8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311
```

receipt や production specを importせず、H_mig の Git blobから15件を順番どおり導出するコマンドは次とする。

```bash
H_MIG=f04ae50b3c7be800885447be514b59f2405a4e83

while IFS= read -r path; do
  printf '%s  ' "$path"
  git cat-file blob "${H_MIG}:${path}" | sha256sum | cut -d' ' -f1
done <<'EOF'
orchestrator/campaign/s8a_trigger_sweep.py
orchestrator/campaign/s6_sort_sweep.py
orchestrator/campaign/p3_s4_loop_sort.py
orchestrator/campaign/s8a_trigger_sweep.py
orchestrator/campaign/s8a_trigger_sweep.py
orchestrator/campaign/s6_sort_sweep.py
orchestrator/campaign/p3_s4_loop_sort.py
orchestrator/campaign/s8a_trigger_sweep.py
orchestrator/campaign/s8a_trigger_sweep.py
orchestrator/campaign/s6_sort_sweep.py
orchestrator/campaign/p3_s4_loop_sort.py
orchestrator/campaign/s8a_trigger_sweep.py
docs/phase3-8b-descriptor-design.md
orchestrator/campaign/s1_known_axes_freeze.py
orchestrator/campaign/s8b_holdout_freeze.py
EOF
```

得られる unique 値は次の6個で、既存 tuple の各行へ第4要素として直接重複記載する。path→hash の lookup helperで expected を再構成しない。

| path | 件数 | 内容 SHA-256 |
|---|---:|---|
| `s8a_trigger_sweep.py` | 6 | `8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311` |
| `s6_sort_sweep.py` | 3 | `28270e905785c787f1eb74cebcf34f8feb98e1e7cec738dee14611c9ab3dad1a` |
| `p3_s4_loop_sort.py` | 3 | `0e716a6cda268e3d158774c344d002a8daf49fa7dd4ab9bbb1bb5c9e0d30d8b0` |
| `phase3-8b-descriptor-design.md` | 1 | `5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae` |
| `s1_known_axes_freeze.py` | 1 | `1d4d45a3de4926c6aae76906f7b4b72d3fead51e9cdf62ff03f80a0379c364e0` |
| `s8b_holdout_freeze.py` | 1 | `41c0b6a7b348acb0960b354f80ab79ba3376d4214a73f11d5ee739b04337d4b0` |

[`_T080_SOURCE_GOLDEN`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:71) の13行と `_T080_METADATA_GOLDEN` の2行を `(artifact, pointer, recorded, observed)` に拡張し、1214–1226行は `receipt[...]` との `zip` を削除する。expected items は golden tupleだけから構築する。

P1 の「13 + 2 = 15件すべて literal pin」は妥当である。production `_make_observation()` は source 13件と metadata 2件の両方で receipt の `migration_blob_sha256` を observed に転記しており（[`1821–1832 行`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1821)）、独立性の欠如は同じである。

### ancestry 2 件

ancestry は literal observed pin の対象外とし、現行 `_independent_ancestry_item()` を維持する。

- recorded commit objectがなければ `status="missing-commit"`、`observed=None`。
- objectが後から利用可能になれば `ancestor` / `not-ancestor` へ変わり、observed はその時点の `validation_head` になる。
- recorded OID、artifact、subjectは現行どおり literal。
- status と observed は独立 Git commandで動的に期待値を作る。

## 4. 揮発性の検査

literal 化してよいもの:

- R commit `8bec195...`
- R raw SHA-256 `b84f783...`
- H_mig `f04ae50...`
- H_mig の15個の blob内容 SHA-256
- schema version、migration ID、receipt path
- frozen recorded hashと recorded ancestry OID
- source-repin / generator-metadata の status

literal 化してはいけないもの:

- `validation_head`: 現在の `HEAD` なので commitごとに変わる。
- ancestry の `observed`: commitが存在する場合は `validation_head` そのものになる。
- ancestry の `status`: dangling objectが後から取得されると `missing-commit` から変わり得る。
- current worktree の source SHA-256: 通常開発で変わる。必ず `git cat-file blob "$H_MIG:$path"` から得る。
- current ccbench checkout HEAD:作業状態で変わり得るため、この golden の新 literalにはしない。

floor/budget null refusalは既存凍結 JSON bytesが不変である限り安定しており、今回も弱めず exact のまま残す。

## 5. 所有分離の確認

編集対象は次の素集合になる。

- U1: `orchestrator/tests/test_t080_freeze_migration.py`
- U2: `orchestrator/tests/test_s8b_oracle_driver.py`

共有 helper の編集は不要。

- U1 は自ファイル内の `_repo_with_schema_valid_receipt()` だけを後方互換で拡張する。
- U2 は自ファイル内の golden tuple、independent R helperの利用箇所、real-repo testだけを変更する。
- driver側の `_t080_stub_free_e2e_repo()` をU1から import・移動しない。
- `orchestrator/campaign/**`、`output/s8b-freeze/**`、`output/t080-migration/**`、docs は変更しない。

恒久的な production 修正を要する scope 外所見は、今回の静的読解では認めていない。

## 6. 変異点の提案

すべて一時 mutant であり、実装案には含めない。

| ID | file:line と一時変更 | 新テストの期待 | 帰属 |
|---|---|---|---|
| U1-M1 | `t080_freeze_migration.py:1924` の derivation check entryを削除 | U1負例が refusal空・`active-valid` へ反転して KILL | 成立。既存直呼びテストはpublic wiringを通らない |
| U1-M2 | `:1103–1106` で holdout reconstruction comparisonだけをskip | 改竄した projected hashが通り、U1が KILL | 成立。既存直呼び負例は `repin_report` 改竄なのでこの比較欠落を検出しない |
| U1-M3 | `:1088` の expected holdout projected hashを、再導出した `holdout_sha` ではなく receipt自身の値にする | 自己参照により改竄が通り、U1が KILL | 成立。valid receipt正例では値が同じため既存正例は赤にならない |
| U1-M4 | `:1118` の `_assert_deterministic_fields(receipt, expected)` を削除 | public gateが改竄を受理し、U1が KILL | 成立。既存379–397行は `_assert_deterministic_fields` を直接呼ぶので mutant を迂回する |
| U2-M1 | `:33` の `RECEIPT_REL` を履歴に存在しない sibling pathへ変更 | 旧テストは `independent is None` の4 refusal枝で緑、新テストはR不存在／OID不一致で KILL | T-092 帰属候補。既存テストの多くは production constantを共有するため静的には旧real testだけが穴になるが、親実測で全走帰属を確認する |
| U2-M2 | `:1825` の source observedを `recorded_sha256` に変更 | 13件 literalとの不一致で KILL | **帰属不成立**。現行テストも receiptの migration hashをexpectedにしているため既にKILLする |
| U2-M3 | `:1831` の metadata observedを `recorded_sha256` に変更 | metadata 2件 literalとの不一致で KILL | **帰属不成立**。現行テストも同じ理由で既にKILLする |

T-093 の増分は「expected oracleをreceiptから独立させること」であり、固定済みの正しいR bytesに対する単純な production mapper mutantは現行testにも検出される。このため production-only・凍結成果物不変という条件では、T-093固有の単独帰属 mutantを作りにくい。ここを過大に KILL 帰属してはならない。

## 未解決の疑問

1. T-092 の必須 R OIDに加えて、R raw SHA-256とH_migも同じtestで literal pinする強化を採るか。推奨は採用。
2. T-093 に固有の mutation 帰属を必須とするか。必須なら、production-only 制約を緩めて test oracleの自己参照再導入 mutant、または凍結成果物ではない disposable R fixture の改竄を許す裁定が必要。制約を維持するなら、U1/T-092は固有KILL、T-093は上表の「帰属不成立」を正直に記録する。
---

## 段3 敵対相談 A = 正しさ境界 (read-only, max)

静的検査のみで、`pytest` は実行していない。以下の KILL/SURVIVE は実測結果ではなく、コード上の帰属判定である。

## A-1 — golden tuple の4要素化が既存3要素 consumerを取り残す

**根拠:** プランは既存定数を `(artifact, pointer, recorded, observed)` へ拡張するが、stub-free E2E は現在も3要素 tupleを構築して同じ定数と比較している。[plan-v1.md:170](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:170) [test_s8b_oracle_driver.py:450](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:450) [test_s8b_oracle_driver.py:457](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:457)

**成果物影響:** 計画どおり実装すると既存受入 node の比較は必ず不一致になり、安易に旧 assert を削れば report の `artifact/pointer/recorded` 参照を守っていた検出力が失われる。

**重大度:** must-fix

**対案:** 既存3要素定数を維持して observed 専用15要素 tupleを別設置するか、旧 assert 側で定数の先頭3要素を明示射影し、旧検査を残す。

## A-2 — 変異7件のうち、U2の3件は主張された帰属を満たさない

**根拠:** 静的帰属は次のとおり。

| 変異 | 判定 |
|---|---|
| U1-M1 | public check entryだけの欠落として新U1への帰属候補 |
| U1-M2 | holdout comparisonだけの欠落として新U1への帰属候補 |
| U1-M3 | holdout expectedの自己参照として新U1への帰属候補 |
| U1-M4 | `_verify_receipt_derivation` 内の assert呼出し欠落として新U1への帰属候補 |
| U2-M1 | 新しい `independent is not None` が検出する候補。R OID equalityの証拠ではない |
| U2-M2 | 現行テストも receiptのmigration hashを期待するため既存テストが検出する |
| U2-M3 | holdout metadataではrecordedとmigration hashが異なるため、現行テストが既に検出する |

プラン自身もU2-M2/M3を「帰属不成立」と認めている。[plan-v1.md:227](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:227) [plan-v1.md:232](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:232) 現行期待値はreceiptのmigration hashである。[test_s8b_oracle_driver.py:1214](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1214) [test_s8b_oracle_driver.py:1221](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1221)

**成果物影響:** U2-M2/M3を新規KILLとして数えると、変異台帳が実在しないT-093増分検出力を証明したことになり、report/certified選択のproof referenceが偽の検査証拠を指す。

**重大度:** must-fix

**対案:** U2-M2/M3は新規KILLから除外する。U1-M1〜M4もDW-M08どおり旧HEAD比較で帰属を実測する。

## A-3 — 15 literalは値として独立だが、単一real-repo vectorなので恒真化できる

**根拠:** 15値をテストへ直接記載する案自体は、receipt導出や実行時Git導出ではなく、真のliteralと認められる。[plan-v1.md:132](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:132) [plan-v1.md:159](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:159)

しかし production `_make_observation()` を「receiptを無視して、その15 literalを常に返す」実装へ変えても、提案real-repo比較は成立し続ける。既存stub-free E2Eはitemsの件数しか確認せず、report再検証も同じproduction `_make_observation()`を再利用するため共通モードになる。[test_s8b_oracle_driver.py:458](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:458) [s8b_oracle_report.py:213](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_report.py:213) [s8b_oracle_report.py:233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_report.py:233)

またknown generatorはrecordedと提案observedが同じ `1d4d45...` であり、この1件は `observed = recorded` mutantを識別不能である。[test_s8b_oracle_driver.py:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:87) [plan-v1.md:167](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:167)

ancestry 2件は`validation_head`とobject到達性で変動するため、現行real-repo testでは安定literal化できない。プランがこれをliteralと呼ばず動的Git期待値に残した点は正しい。[plan-v1.md:176](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:176) [t080_freeze_migration.py:1833](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1833)

**成果物影響:** 別rootのvalid receiptでもreal Rのobserved値を出すproductionへ退化でき、receipt固有でない15参照がreport/WALへ載る一方、提案goldenはその退化を検出しない。

**重大度:** must-fix

**対案:** stub-free hermetic fixtureのbasis sourceを既知bytesへ変更し、その別SHA-256をliteral pinする第2 vectorを追加する。これなら「real値を常時返す」production mutantをT-093固有にKILLできる。P1の15件は「15 KILL」ではなく「15 literal cell」と記録する。

## A-4 — T-091は依然stub群に依存し、実gate相互作用を検証しない

**根拠:** プランは `_load_artifact` と `_verify_receipt_derivation` だけを戻し、他checkをstubのままにする。[plan-v1.md:51](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:51) [plan-v1.md:58](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:58) helperはreceiptを受け取るknown/holdout/metadata closureもno-op化する。[test_t080_freeze_migration.py:336](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:336) [test_t080_freeze_migration.py:351](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:351)

実gateではこれらがderivationより前に、同じmutable receiptを受け取る。[t080_freeze_migration.py:1913](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1913) [t080_freeze_migration.py:1924](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1924)

反例mutantは `_verify_metadata_closure()` が正常検査後に改竄されたholdout projected hashを正しい値へ書き戻す変更である。実gateではderivation前に改竄が消えて受理側へ倒れるが、提案テストでは同関数がstubなので改竄が残り、期待refusal比較は成立する。

**成果物影響:** 不正receiptが`invalid`から`active-valid`へ受理集合を広げ、floor解除後には17-item envelopeがcampaign-start/WALへ流れ得るのに、T-091変異台帳はpublic gateを保護済みと誤記録する。

**重大度:** must-fix

**対案:** 既存stub-free E2E fixtureを拡張して負例を撃つ。少なくともreceiptを引数に取る全先行checkを実関数で走らせ、上記「先行checkがreceiptを修復する」mutantを事前登録する。これは規律2の「ゲートを緩める変異」そのものである。[CLAUDE.md:65](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/CLAUDE.md:65)

## A-5 — P5のfield裁量にはderivation対象外と先行refusal対象が混在する

**根拠:** D78は`live_scan_sha256`をpost-R再導出不能と明記する。[decisions.md:3173](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3173) 実際、deterministic expectedのholdoutには`projected_document_sha256`しかなく、`live_scan_sha256`は比較されない。[t080_freeze_migration.py:1083](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1083) [t080_freeze_migration.py:1103](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1103)

source/metadataのmigration hashを改竄すれば、derivationより先のclosure checkも発火する。[t080_freeze_migration.py:1915](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1915) [t080_freeze_migration.py:1922](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1922)

**成果物影響:** 実装子の選択次第で、台帳が`receipt.derivation_mismatch`ではなく別gateの拒否をT-091 KILLとして帰属し、derivation無効化後の受理集合を未検査のままにする。

**重大度:** must-fix

**対案:** P5を却下し、v1が選んだ `reconstruction.holdout.projected_document_sha256` に親裁定を固定する。[plan-v1.md:72](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:72)

## A-6 — P2は既存pre-R検査を「保持した」と誤認している

**根拠:** 削除対象のreal-repo分岐は実freezeに対する具体的なlegacy drift 2件とfloor/budget 2件を検査する。[test_s8b_oracle_driver.py:1190](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1190) 一方、代替とされたhermetic testはlegacy verifierをmockし、固定文言を注入している。[test_s8b_oracle_driver.py:720](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:720) [test_s8b_oracle_driver.py:1275](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1275)

post-R固定による受理集合の縮小自体は規律2違反ではないが、「旧assertを弱めない」というbrief不変条件は満たしていない。[brief.md:46](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/brief.md:46)

**成果物影響:** never-issued状態でlegacy/floor/budget refusalの一部が欠落してもreal artifact由来の構造化拒否vectorを検査できず、report・台帳の拒否理由参照が変わる。

**重大度:** must-fix

**対案:** R固定testから分岐を外すのは維持しつつ、旧real-pre-R refusal検査を別nodeへ移す。receipt resolutionだけをnever-issuedへ固定し、legacy verifierとreal freezeは実物を使う。

## A-7 — P4の「commit後」は正しいが、帰属手順が不足している

**根拠:** DW-O19はtracked fileの一時変異を統合commit後に限定しているため、時期自体は正しい。[operations.md:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/operations.md:112) [operations.md:117](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/operations.md:117)

しかしテスト強化waveでは、同じ変異を新テストと変更前HEAD版へ走らせ、「新だけが検出する差分」が必要である。[mutation.md:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/mutation.md:47) [mutation.md:52](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/mutation.md:52) P4は「新テストがKILLするか」しか要求せず、プランもT-093帰属を未裁定のまま残している。[brief.md:72](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/brief.md:72) [plan-v1.md:237](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:237)

**成果物影響:** 既存テストによる先取りKILLを新規検出力として台帳へ記録し、certified選択・reportが参照する検査証拠の帰属が偽になる。

**重大度:** must-fix

**対案:** 変異ごとに旧HEAD版と新HEAD版の失敗nodeを記録する。U2-M2/M3は除外し、T-093固有mutantを確定できるまで統合commitへ進まない。復元時はDW-O19に加え、内容一致・単一走行guardも必須とする。

## A-8 — U1の`state`とobservation assertはexact refusalの帰結である

**根拠:** refusalが1件あればobservation生成条件を満たさず、historyがissued-but-missingでないfixtureではstateは`invalid`になる。[t080_freeze_migration.py:1936](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1936) [t080_freeze_migration.py:1942](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1942)

**成果物影響:** exact refusalと別々の検出単位として数えると、変異台帳がU1の検出力を水増しする。成果物値への追加保護はない。

**重大度:** nit

**対案:** 両assertは整合性pinとして残してよいが、独立KILL・独立検出力には数えない。

## Scope外所見

なし。上記対案はすべてテストまたは変異手順内であり、production恒久修正を要求しない。

## 総合判定: NO-GO

T-093は現案のreal-repo単一vectorだけではproduction-onlyの増分検出力を示せず、変異帰属契約を満たさない。  
さらにtuple consumer取り残しとT-091のstub相互作用マスクがあり、「検出力を上げた」という成果物主張を現状では受理できない。
---

## 段3 敵対相談 B = 整合・実効性 (read-only, max)

静的検査のみ実施し、pytest は実行していない。

### B-1 — 既存 golden tuple の4要素化が別の E2E consumer を破壊する

- **根拠**: プランは既存 `_T080_SOURCE_GOLDEN` / `_T080_METADATA_GOLDEN` を4要素化するが（[plan-v1.md:159](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:159>)）、既存 E2E は生成した3要素 tuple と同じ定数を直接比較している（[test_s8b_oracle_driver.py:448](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:448)、[同:453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:453)）。さらにこの E2E の basis は `ROOT` の現在の source bytes をコピーする（[同:286](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:286)、[同:346](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:346)）。
- **成果物への影響**: そのままでは受入全走が tuple arity 不一致で停止し、安易に第4要素まで比較すると将来の通常 source 編集で current-basis E2E が false red になり、H_mig literal を現行値へ更新する圧力が生じる。
- **重大度**: must-fix
- **対案**: 既存3要素定数を維持し、real-repo 専用の4要素定数を別名で逐語定義する。既存 E2E を `row[:3]` 比較へ変える案も可能だが、current-basis の observed を H_mig literal と比較してはならない。

### B-2 — U1 の「commit 前改竄 callback」に実在する入口がない

- **根拠**: プランが明記する追加引数は `derivation_ready=False` だけだが（[plan-v1.md:39](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:39>)）、後段では未定義の「改竄 callback」を適用するとしている（[同:47](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:47>)）。現行 helper は receipt 書込みから R commit まで内部で完了し、引数は `extra_path` と `trailer` のみ（[test_t080_freeze_migration.py:319](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:319)、[同:327](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:327)）。
- **成果物への影響**: commit 後に改竄すると `receipt.issued_but_missing` が受理集合へ入り、狙った単独 `receipt.derivation_mismatch`、`state=invalid`、observation null の証拠にならない。
- **重大度**: must-fix
- **対案**: `mutate_receipt: Callable[[dict], None] | None = None` を明示追加し、導出値の反映後・canonical 化前に一度だけ呼ぶ。既存 caller では `None` を既定とする。

### B-3 — P2 は full history・初期化済み submodule・Git 環境を暗黙前提にしている

- **根拠**: production は shallow repository を明示拒否する（[t080_freeze_migration.py:595](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:595)）うえ、current ccbench checkout の存在と HEAD を要求する（[同:934](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:934)）。`conftest.py` が保証するのは同一 pytest invocation 内の直列 group だけ（[conftest.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/conftest.py:44)、[同:95](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/conftest.py:95)）で、README は submodule 不在を具体検知して skip する契約を置く（[README.md:94](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/README.md:94)、[同:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/README.md:107)）。また test-local `_run_git` は `GIT_*` を継承する（[test_s8b_oracle_driver.py:128](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:128)）一方、production は除去する（[t080_freeze_migration.py:540](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:540)）。
- **成果物への影響**: shallow CI、submodule 未初期化の別 worktree、または `GIT_DIR` 等を持つ runner では、同じ repository bytes でも `active-valid`／R OID期待から外れて受入が false red になる。
- **重大度**: must-fix
- **対案**: full history・R/H_mig reachable を real-repo test の明示前提にし、submodule 不在は README 契約どおり具体検知して skip するか runner で初期化を強制する。独立 Git helper も test-local な sanitized env を使う。`.git` が file の worktree 自体は Git command 経由なので問題ない。

### B-4 — land 後は D78 (6)(f) と (10) の残余記述が虚偽になる

- **根拠**: D78 (6)(f) は real-repo observed の literal pin を「不能」と記す（[decisions.md:3181](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3181)）。D78 (10) も独立 pin 不在と三つの穴を未解消としている（[同:3233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3233)、[同:3236](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3236)）。同文書は追記型である（[同:3214](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3214)）。
- **成果物への影響**: decision/proof-chain の参照は、実テストが R・H_mig・observed を pin 済みなのに「証拠不在」と返し、台帳上の closure 状態が実装と逆になる。
- **重大度**: must-fix
- **対案**: 既存歴史文を直接改稿せず D78 (11) を追記し、(6)(f) と (10) の該当残余を supersede する。「source-repin 13 + generator-metadata 2 を独立 literal pin、R OID/raw/H_mig も固定、ancestry 2 は意図的に動的、(6)(a)〜(e),(g) は残存」と限定して記す。

### B-5 — 親 worklog で T-091〜093 を別々のトップレベル項目にしないと台帳検査が赤になる

- **根拠**: 現行末尾の次の一手は T-091、T-092、T-093 を別 ID として保持する（[worklog.md:479](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/worklog.md:479)、[同:481](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/worklog.md:481)、[同:483](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/worklog.md:483)）。`check_docs.py` は各トップレベル項目の先頭 ID しか抽出せず（[check_docs.py:593](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:593)）、後続 entry または見送り台帳への保存を要求する（[同:1078](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1078)）。
- **成果物への影響**: `[T-091] / [T-092] / [T-093]` の一項に束ねると後二つの参照が消失扱いとなり、`check_docs` が受入不能になる。
- **重大度**: must-fix
- **対案**: 親の統合 worklog では三つをそれぞれ先頭 ID にした別トップレベル完了項目として記録する。D78 追記だけでは sink にならない。

### B-6 — T-093 の mutation 帰属が brief の成果条件と未裁定のまま衝突している

- **根拠**: brief は「新テストが production mutant を KILL」を親成果物とする（[brief.md:54](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/brief.md:54>)）。一方プランは U2-M2/M3 を現行テストでも KILL されるため「帰属不成立」と認め（[plan-v1.md:232](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:232>)）、T-093 固有帰属を未解決の問いに残す（[同:239](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/plan-v1.md:239>)）。
- **成果物への影響**: このままでは mutation 台帳が T-093 を虚偽の KILLED と記すか、brief の受入条件を満たさないかの二択になる。
- **重大度**: must-fix
- **対案**: 実装前に親が「T-093 は production-only 固有 mutant=N/A、独立導出の静的証拠を採用」と明示裁定するか、disposable R/test-oracle mutation を許可する。DW-O19 の統合 commit 後・単一 diff・`git checkout --`・内容一致という機械手順自体は整合している（[operations.md:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/operations.md:112)）。

### 確認済みの非所見

- 既存として引用された file:line、関数、fixture はすべて実在した。未定義なのは B-2 の新規 callback seam。
- R OID、receipt raw SHA-256、H_mig、6 unique／15行の内容 SHA-256 は Git object から独立再計算してプランと一致した。`validation_head`、ancestry status/observed、current source hash、current submodule OID の新規 literal 混入はない。
- U1/U2 の編集ファイル所有は素集合。相互 import はない。U2 module の外部 import はあるが、変更定数の consumer は B-1 の同ファイル E2E のみ。
- `test_s8b_repo_scan_invariant.py` の既知 conjunction hit は空集合のままで、予定する hash／refusal 文言は新 hit を作らない。production 修正を要する scope 外所見はない。

## 総合判定: NO-GO

B-1 は現行テストを直接破壊し、B-2 は U1 の狙った拒否経路を実装不能にする。  
加えて環境契約、D78/worklog 台帳、T-093 mutation 裁定を実装前に閉じる必要がある。
---

## 段5 実装 U1 = T-091 (workspace-write, high)

## 変更前の挙動

- public 正例では `_verify_receipt_derivation` が stub のため、合成 receipt は `active-valid` として受理されていました。
- 導出値不一致は `_assert_deterministic_fields()` の直呼びでのみ拒否され、public `verify_receipt()` 経由の負例はありませんでした。

## 変更点

[orchestrator/tests/test_t080_freeze_migration.py](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/wt-u1/orchestrator/tests/test_t080_freeze_migration.py:320) のみ変更しました。

- `_repo_with_schema_valid_receipt()` に後方互換な `derivation_ready=False` と `mutate_receipt` を追加。
- `derivation_ready=True` で凍結 JSON 2本、重複除去6 path、ccbench gitlink を basis commit に配置。
- production `_derive_deterministic_fields()` の結果を反映後、canonical bytes 化前に callback を1回だけ実行。
- holdout projected hash の先頭 nibble を確実に変更する public 負例を追加。
- refusal の ordered 1-tuple完全一致、`state == "invalid"`、observation `None` を固定。
- 本番コード・凍結成果物・docs・tools は変更なし。commit も未作成です。

## 実行結果

- 新規 nodeid:
  `orchestrator/tests/test_t080_freeze_migration.py::test_public_gate_rejects_tampered_holdout_projected_hash_t091`
  — **1 passed in 0.33s**
- 対象ファイル全体:
  `python3 -m pytest orchestrator/tests/test_t080_freeze_migration.py -q`
  — **39 passed in 1.80s**
- `python3 tools/check_codex_agents.py` — OK
- `python3 tools/check_docs.py` — 違反なし
- `git diff --check` — 成功

変更前基準走は pytest 自体が **38 passed** でしたが、終了後に sandbox の `.agents` mount cleanup エラーで外側の終了コードが101になりました。最終走では再発せず終了コード0です。

## stub のまま残した check

全 gate を検証したものではありません。

- `_verify_known_closure`: 63 source path が必要ですが、fixture は裁定指定の6 pathのみ。テスト内に「stub のため gate 間相互作用は未検証」と明記。
- `_validate_positive_control`: positive-control fixtureを持たないため。
- `_verify_ccbench_current`: temp repoに checkout済み submoduleがないため。
- `_verify_holdout_live_scan`: full repositoryおよびpositive-control環境を持たないため。

receipt を取るその他の先行 check、`_load_artifact`、`_verify_receipt_derivation` は実関数へ戻しています。

## 波及可能性

既存 caller は次の5件のみで、すべて新引数を省略しているため従来経路のままです。全39件の成功で確認しました。

- `test_gate_normalizes_unexpected_check_exceptions_and_continues_g5`
- `test_state_active_valid_after_schema_topology_and_all_independent_gates`
- `test_invalid_r_topology_keeps_independent_ccbench_refusal_j4`
- `test_invalid_r_trailer_is_rejected_exactly`
- `test_issued_but_missing_continues_independent_checks_and_observation_is_null_f4`

リポジトリ全体の grep で、所有外ファイルからの caller はありません。将来 production specの6 path、凍結JSON schema、導出形式が変更された場合は新しい derivation-ready fixtureが影響を受けます。

## 残る赤

なし。作業ツリーの変更は指定されたテストファイル1本だけです。
---

## 段5 実装 U2 = T-092+T-093 (workspace-write, high)

## 変更前の挙動

- real-repo テストは R が履歴にない場合、legacy drift 2 件＋floor/budget 2 件を正解として受理していました。
- post-R では floor/budget の 2 refusal を要求していましたが、observed 15 件を receipt 自身から期待値化していました。
- fixture E2E は observation の件数 `17` のみを検査していました。
- `_run_git` は外部の `GIT_*` 環境変数を継承していました。

## 変更点

[orchestrator/tests/test_s8b_oracle_driver.py](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/wt-u2/orchestrator/tests/test_s8b_oracle_driver.py:90) のみ変更しました。

- 既存 `_T080_SOURCE_GOLDEN` / `_T080_METADATA_GOLDEN` は未変更。
- real-repo 専用定数へ observed 15 cell、R OID、R raw SHA-256、H_mig を literal pin。
- receipt との `zip` と pre-R 分岐を削除。R 不在は「full history が必要」と明示失敗。
- `validation_head` と ancestry の status/observed は動的導出を維持。
- fixture E2E は `HEAD^` の basis blob raw bytesから SHA-256 を独立導出し、15 observation と exact 比較。
- real-repo 定数固定への退化を検出するため、当該 fixture のみ非実行ドキュメント blob を一時ディレクトリ内で分岐。リポジトリの docs は未変更。
- `_run_git` を production と同じ `GIT_*` 除去環境へ変更。
- production、`output/**`、docs、tools は未変更。commit も未作成。

## 実走結果

- 直接対象:

  `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`  
  `test_real_freeze_gate_lists_floor_and_budget_null`  
  → **2 passed**、65.18秒

- 全ファイル:

  `python3 -m pytest orchestrator/tests/test_s8b_oracle_driver.py -q`  
  → **81 passed, 1 skipped**、1451.88秒

- `python3 tools/check_codex_agents.py` → rc=0
- `python3 tools/check_docs.py` → rc=0
- `git diff --check` → rc=0

skip は既存 nodeid `test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2`。`gcc-13` / `g++-13` 不在による環境条件で、赤ではありません。

## 波及可能性

- `_t080_stub_free_e2e_repo()` の他の5 callerは新引数の既定値が `False` のため挙動不変。対象 E2Eだけが fixture-local blobを変更します。
- `_run_git` の全 callerは外部 Git 設定を継承しなくなるため、ambient `GIT_*` に依存していた環境では結果が変わります。これは意図した hermetic 化です。
- real-repo テストは shallow historyやR欠落環境で明示的に赤になります。
- consumer の `migration.verify_receipt()`、`driver.gate_check()`、report observation 再構成は引き続き検査されます。
- private helperの他ファイルからの caller/import は静的検索でありませんでした。

## 残る赤

なし。作業ツリーの変更は指定されたテストファイル1本だけです。
---

## 段6 敵対レビュー A = 検出力と正しさ境界 (read-only, max)

## 所見

### RA-1 / T-091 のコメントが stub 境界を網羅していない

**1行要約:** ordered 1-tuple は有効だが、「gate 間相互作用は未検証」の対象がコメント上 `_verify_known_closure` だけに見える。

**根拠:** 共通 helper は `_validate_positive_control`、`_verify_ccbench_current`、`_verify_known_closure`、`_verify_holdout_live_scan` を stub 化しており、T-091 の復元リストにも含まれない一方、コメントは `_verify_known_closure` だけを記載している。[test_t080_freeze_migration.py:381](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:381)、[test_t080_freeze_migration.py:485](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:485)、[test_t080_freeze_migration.py:493](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:493)。実装報告側は4件すべてを正しく列挙している。

**成果物影響:** 実環境でこの4 gate のいずれかも拒否した場合、レポート・台帳の refusal 集合は singleton でなくなるが、このテストだけではその追加理由を検出しない。certified の reject 自体は変わらない。

**重大度:** nit

**対案:** コメントを4件の列挙に直し、「ordered 1-tuple はこれらを pass 固定した条件下の保証」と明記する。stub 解消までは不要。

## 静的検査結果

- `git diff HEAD` の対象は指定されたテスト2ファイルだけ。本番コード・`output/**` の差分はない。
- 既存 `_T080_SOURCE_GOLDEN` / `_T080_METADATA_GOLDEN` は無変更で、新定数はその直後に追加されている。[test_s8b_oracle_driver.py:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:71)
- real-repo の15件は receipt から組み立てず、literal だけで expected items を構成している。[test_s8b_oracle_driver.py:1355](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1355)
- R raw SHA-256、H_mig、6 distinct blob の SHA-256 は、read-only の Git 履歴・`cat-file` で literal との一致を確認した。
- E2E oracle は fixture の非実行 document blobを分岐させ、commit 後の `HEAD^:<path>` を test-local Git で読む。receipt、production 導出関数、live worktree hash は期待値に使っていない。[test_s8b_oracle_driver.py:469](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:469)、[test_s8b_oracle_driver.py:594](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:594)
- T-091 は導出後・commit 前に64桁 hexの先頭 nibbleを変更する。[test_t080_freeze_migration.py:359](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:359)、[test_t080_freeze_migration.py:472](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:472)。復元済みの先行 gate はこの reconstruction field を拒否せず、production の derivation entry が期待する exact reason を生成する。[t080_freeze_migration.py:1901](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1901)、[t080_freeze_migration.py:1924](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1924)
- `mutation_calls == 1`、`state == "invalid"`、observation `None` は fixture／整合性 pin であり、独立 KILL には数えられない。主検出力は ordered refusal 完全一致。[test_t080_freeze_migration.py:495](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:495)
- R は現在の HEAD の祖先で、receipt path の最初の導入 commit でもある。したがって削除された pre-R 分岐は現 post-R テストでは到達不能だった。R 欠落時は明示 fail へ強化されている。[test_s8b_oracle_driver.py:1335](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1335)
- `_run_git` の `GIT_*` 除去は production の環境処理と整合し、既存 assert の弱化はない。[test_s8b_oracle_driver.py:226](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:226)

## M1〜M7 の静的判定

| 変異 | 新テスト | 変更前 HEAD | 帰属 |
|---|---|---|---|
| M1 derivation entry 削除 | KILL | SURVIVE | T-091 |
| M2 holdout comparison skip | KILL | SURVIVE | T-091 |
| M3 expected を receipt 自身から取得 | KILL | SURVIVE | T-091 |
| M4 `_assert_deterministic_fields` 呼出削除 | KILL | SURVIVE | T-091 |
| M5 `RECEIPT_REL` を未履歴 sibling へ | KILL | SURVIVE | T-092 |
| M6 real-repo 15値を常時返却 | KILL | SURVIVE | T-093 |
| M7 source observed を recorded に変更 | KILL | **KILL** | 帰属不成立 |

M7 は変更前 test が receipt の `migration_blob_sha256` を expected にしていたため既存防御が先に成立する。新規検出力へ計上してはならない。M1〜M6 は事前登録どおり新旧差分が成立する静的構造である。

規律2/3については、受理集合を広げる変更はなく、欠落履歴は fail-closed、拒否理由と observation は構造化されたままであり、緩みは認めない。scope外の本番所見もない。

**総合判定: GO**  
must-fix なし。M1〜M6 の新規帰属は成立し、M7 の既存 KILL も識別できている。  
RA-1 は境界説明の nit。pytest・変異実走は行っておらず、最終実測は親に委ねる。
---

## 段6 敵対レビュー B = 実行時・整合・波及 (read-only, max)

静的レビュー結果は **must-fix 2件、nit 1件**です。差分は指定されたテスト2ファイルだけで、本番コード・成果物の変更はありません。制約どおり pytest は実行していません。

## 所見

### RB-1 / Git 環境の sanitize が同一処理内で分断され、別 repository view を参照・更新し得る

- 根拠: `_run_git` と新 `_git_blob_sha256` は sanitized env を使う一方、直後の `git show` と ancestry 2操作は ambient env のままです。`orchestrator/tests/test_s8b_oracle_driver.py:226-266`, `:270-283`
- 根拠: E2E 子プロセスも `os.environ` を丸ごと継承し、その中で `rev-parse`・`add`・`commit` を直接実行します。`orchestrator/tests/test_s8b_oracle_driver.py:519-569`
- 同じ分断は `commit-tree`、`hash-object`、履歴 `show` にもあります。`orchestrator/tests/test_s8b_oracle_driver.py:667-675`, `:764-769`, `:2367-2374`
- 成果物影響: ambient `GIT_DIR` 等があると、正しい revision が受入集合から脱落して台帳・certified/report が生成されないか、子の `git add/commit` が別 repo の index/HEAD を汚染する。
- 重大度: **must-fix**
- 対案: 全直書き Git subprocess に `_sanitized_git_env()` を渡し、子 Python の env も sanitized env＋`PYTHONPATH`/`PYTHONNOUSERSITE` にする。`commit-tree` は sanitized env に author/committer 4変数だけを追加する。`protocol.file.allow=always` は現在どおり invocation-local の `-c` を維持する。

### RB-2 / D78既知2箇所に加え、現行 worklog の3タスクも land 後に虚偽になる

- 根拠: D78 (6)(f) は literal pin 不能、(10) は独立 pin 不在と記録しています。`docs/decisions.md:3181-3182`, `:3233-3238`
- 追加箇所: worklog 末尾は T-091〜093を「着手可能」「現状は未実装」としています。`docs/worklog.md:479-484`
- `check_docs.py` は前エントリの ID が後続トップレベル項目か見送り台帳へ保存されることを要求します。`tools/check_docs.py:1070-1085`
- 成果物影響: 試行台帳の最新次アクション集合が完了済み T-091〜093を未完として指し、実装状態への参照が3件 stale になる。
- 重大度: **must-fix（親の段7）**
- 対案: 予定どおり D78 (11) を追記し、worklog 新規エントリへ T-091・T-092・T-093を別々のトップレベル完了項目として載せる。過去 worklog と dated insight は歴史記録なので改稿しない。他に虚偽化する living docs は見つからない。

### RB-3 / 6 distinct blob の照合に15個の Git subprocessを起動している

- 根拠: 13＋2 cellそれぞれで `_git_blob_sha256` を呼ぶため、重複 path も再読します。`orchestrator/tests/test_s8b_oracle_driver.py:595-606`
- 子報告値は対象2 node合計65.18秒、全ファイル1451.88秒ですが、変更前基準がなく増分は実測不能です。`impl-u2.md:23-32`
- 成果物影響: certified値・受理集合・参照は変わらず、受入全走の walltimeだけが最大9プロセス分余計に延びる。
- 重大度: **nit**
- 対案: path→digest を6件だけ導出・キャッシュし、15 cellの順序へ展開する。重い fixture の呼出回数自体は増えていない。

## 攻撃面の確認結果

- 揮発性: R、R raw、H_mig、6 distinct blob の実 Git objectを読み取り、全 literal と一致した。production は current worktreeでなく `migration_basis_commit` の blobを読むため、通常の `s8a_trigger_sweep.py` 編集では15 cell literalは変化しない。`orchestrator/campaign/t080_freeze_migration.py:722-728`, `:1061-1082`
- 既存3要素 golden は未変更。`orchestrator/tests/test_s8b_oracle_driver.py:71-89`
- `validation_head` は動的、ancestry の status/observed も動的です。`orchestrator/tests/test_s8b_oracle_driver.py:270-291`, `:1354-1394`
- `distinct_basis_blob` はcurrent fixture bytesへ非空bytesを追加し、期待値をfixture Gitから再導出するため上流編集に追随します。`orchestrator/tests/test_s8b_oracle_driver.py:469-475`, `:594-611`
- shallow/R欠落は skipせず失敗し、submodule未初期化も `active-valid` assertまでに失敗します。別worktreeもRを含むdescendantなら動的HEAD、pre-Rなら明示失敗です。`orchestrator/tests/test_s8b_oracle_driver.py:1335-1346`
- repo scan invariant は三軸 `ycsb_*` の同一ファイル conjunctionだけをhitとします。追加hex・refusal・fixture commentはいずれの式も追加せず、`rr80=[] / rr20=[]` と整合します。`orchestrator/campaign/s8b_holdout_freeze.py:34-55`, `:270-282`; `orchestrator/tests/test_s8b_repo_scan_invariant.py:21-35`

全 caller も確認済みです。

- `_repo_with_schema_valid_receipt`: 新規T-091だけ `derivation_ready=True`。既存5 callerはすべて既定 `False/None`。`test_t080_freeze_migration.py:480,558,609,623,642,717`
- `_t080_stub_free_e2e_repo`: 対象E2Eだけ `distinct_basis_blob=True`。他5 callerは既定 `False`。`test_s8b_oracle_driver.py:577,657,697,784,809,2361`
- `_run_git`: caller群は `_independent_t080_receipt_blob`、`_t080_repo`、E2E helper、T-080各欠陥テスト、real-repo test、G12競合テスト、generator履歴探索です。`test_s8b_oracle_driver.py:257,377-400,421-483,594,666,677,769,794-813,1354,1794-1803,2367`
- どの caller もambient `GIT_*` を意図的に必要としていません。submodule file transportは `-c protocol.file.allow=always` を明示済みです。`test_s8b_oracle_driver.py:477-480`
- real-repo nodeidは既存の直列化台帳に残り、名称変更もありません。`orchestrator/tests/conftest.py:94-100`, `orchestrator/tests/test_real_repo_serialization.py:67-75`

本番修正を必要とする新規所見はありません。RB-1の対処はテストファイル内だけで完結します。

**総合判定: NO-GO**  
RB-1の分断されたGit環境は、今回のhermetic化目的を満たさず外部repoへの副作用経路も残す。  
RB-1修正と親段7のRB-2反映後は、レンズB上の残余はnitのみです。
---

## 段6 fix = RB-1/RB-3 (workspace-write, high)

修正完了しました。編集は [test_s8b_oracle_driver.py](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/wt-fix2/orchestrator/tests/test_s8b_oracle_driver.py:223) のみです。commit はしていません。

- **RB-1: closed**
  - 直書き Git subprocess: **全 13 箇所**
  - sanitized 済み: **13/13 箇所**
  - 今回修正: 11 箇所、既存済み: 2 箇所
  - E2E 子 Python 環境: 2/2 箇所を sanitized env＋`PYTHONPATH=""`＋`PYTHONNOUSERSITE="1"`へ変更
  - `commit-tree` は sanitized env に author/committer 4 変数だけ追加
  - `protocol.file.allow=always` は invocation-local のまま
- **RB-3: closed**
  - 15 cell・6 distinct path を確認
  - blob subprocess を15回から6回へ削減し、元の15 cell順へ展開
  - exact 比較・期待値・順序は不変
- **regressed: なし**（通常環境の必須走・ファイル全走）

検査結果:

- 指定2 node:
  - `test_real_freeze_gate_lists_floor_and_budget_null`
  - `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`
  - **2 passed in 78.42s**
- ファイル全走:
  - `python3 -m pytest -q orchestrator/tests/test_s8b_oracle_driver.py`
  - **81 passed, 1 skipped in 1483.46s**
  - skip: `test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2`（ccbench/toolchain 条件不足）
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `py_compile` / `git diff --check`: 成功

追加の poisoned `GIT_*` 敵対走は **2 failed in 52.46s** でした。テスト内13箇所ではなく、所有外の [s8b_holdout_freeze.py](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/wt-fix2/orchestrator/campaign/s8b_holdout_freeze.py:147) と [s1_known_axes_freeze.py](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t091-093/wt-fix2/orchestrator/campaign/s1_known_axes_freeze.py:89) の production Git runner が ambient env を継承するためです。権限境界に従い変更していません。

波及可能性:

- `_t080_stub_free_e2e_repo` の同一ファイル内6 caller
- real-repo nodeを直列化対象として参照する `conftest.py` と `test_real_repo_serialization.py`
- `migration.verify_receipt` / `driver.gate_check` が呼ぶ上記 production Git runner
- private helperの所有外 importはなし

本番コード、`output/**`、`docs/**`、`tools/**` の差分は **0 byte** です。
---

## 段6 焦点再レビュー (read-only, max)

| 前段所見 | 判定 | file:line 根拠 |
|---|---|---|
| RA-1 | **closed** | helper が stub 化する13件は [test_t080_freeze_migration.py:381](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:381)、T-091 が戻す9件は [同:485](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:485)。差集合は `_validate_positive_control` / `_verify_ccbench_current` / `_verify_known_closure` / `_verify_holdout_live_scan` の4件で、親コメントの列挙・pass固定条件と一致する [同:493](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:493)。 |
| RB-1 | **closed** | 前段所見の対象だった同ファイル内の直書き Git subprocess は、外側9件（`:239,248,263,273,282,701,793,2404,3583`）と child 内4件（`:536,553,560,565`）の13/13件で sanitized env を使用する。sanitizer 本体は [test_s8b_oracle_driver.py:226](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:226)、child Python 2件も sanitized env ベース [同:586](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:586)、[同:860](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:860)。 |
| RB-2 | **partial** | T-091 は [test_t080_freeze_migration.py:469](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_t080_freeze_migration.py:469)、T-092 は [test_s8b_oracle_driver.py:1370](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1370)、T-093 は [同:90](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:90) に実装済み。一方、D78 は独立 literal pin 未解消の記録を残し [decisions.md:3181](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3181)、[同:3233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3233)、worklog も3件を未着手扱いしている [worklog.md:479](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/worklog.md:479)。親段7が未実施。 |
| RB-3 | **closed** | 13+2 cell の列を維持したまま [test_s8b_oracle_driver.py:621](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:621)、`dict.fromkeys` で6 distinct pathだけを導出 [同:629](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:629)、同じ列へ再展開して15件を exact 比較している [同:633](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:633)。production の source→metadata 順序 [t080_freeze_migration.py:1821](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1821)、[同:1827](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1827) と一致する。 |

## 残余所見

### RF-1 / RB-2 の親段7文書統合が未了

- 根拠: 実装済みコードと、未実装・独立 pin 不在を記す [decisions.md:3233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3233)、[worklog.md:479](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/worklog.md:479) が不一致。
- 成果物影響: 試行台帳の最新次アクションが完了済み3件を未完として示し、レポート利用者が証拠充足状態を誤認する。
- 重大度: **must-fix（親段7）**
- 対案: D78 (11) を追記して (6)(f)/(10) を supersede し、worklog に T-091・T-092・T-093 を別トップレベル完了項目として記録する。追加レビュー wave は不要。

fix 起因の退行は静的には認めない。

- `protocol.file.allow=always` は引き続き invocation-local [test_s8b_oracle_driver.py:480](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:480)。`commit-tree` には必要な author/committer 4変数が残る [同:696](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:696)。通常 commit は repo-local identity を設定済み [同:424](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:424)。
- 既存3要素 golden は無変更 [同:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:71)。15 cell は値・順序・exact 比較を保持し、重複path間の digest 矛盾もない。
- `git diff HEAD` は指定テスト2ファイルだけで、本番・`output/**`・docs の差分は0 byte。

## Scope 外

production の Git runner は ambient `GIT_*` を引き続き継承する [s1_known_axes_freeze.py:89](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s1_known_axes_freeze.py:89)、[s8b_holdout_freeze.py:147](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_holdout_freeze.py:147)。poisoned env では別 repository view により成果物生成停止・誤判定へ至り得るが、既存問題かつ本番修正を要するため本 wave の退行・must-fix には算入しない。

**総合判定: NO-GO**  
RA-1・RB-1・RB-3 は closed、fix 起因の弱化はない。  
ただし RB-2 が partial のため、親段7の文書・台帳更新前の現ツリーは完了扱いにできない。pytest は実行していない。
