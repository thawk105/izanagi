# 実装計画

pytest は実行していない。以下は指定ファイル、D355/D840、参照先の静的検査だけに基づく計画である。

## 単位 A — reviewed spec candidate producer

### 編集面

新規 module を `orchestrator/campaign/s8b_oracle_spec_candidate.py` に置く。

- `:1-38` — import、入力 key 集合、`ReviewedSpecCandidate`、専用例外
- `:41-82` — strict な研究設計入力と freeze 軸の読込み
- `:85-105` — live generator hash の導出
- `:108-145` — materializer による binding identity の導出
- `:148-205` — spec 構築、canonical validation、bytes/hash の返却
- `:208-245` — preview-only CLI

`s8b_oracle_spec.py` は approval pin、loader、snapshot validator を持つ消費側の権威であり、生成時だけ必要な freeze・materializer・site compiler 依存を入れるべきではない。別 module にすれば、候補生成 capability を追加しても `load_approved_spec` と `validate_approved_spec_snapshot` の依存方向・受理条件を物理的に不変にできる。

### 入力

CLI は `--design PATH` だけを値入力とし、`s8b_oracle_artifacts.strict_load_json_object` で次の exact 6 keys を読む。

```text
n
master_seed
block_sizes
campaign_ids
run_contract
allowed_excluded_reasons
```

Python API も同じ mapping を受け取る。`holdout_ids`、`configuration_ids`、`binding_identity`、`generator_versions`、`schedule_sha256` は caller から受け取らない。

`cxx` は研究設計値にせず、既存の `buildcache.compilers_for_current_site()` (`s8b_oracle_driver.py:1377` と `s8b_floor_campaign.py:3831-3833` が使う同じ経路、定義は `buildcache.py:1628-1632`) から一度だけ解決する。

### 導出値

| 値 | 導出元と処理 |
|---|---|
| `holdout_ids` | canonical freeze path は `s8b_holdout_freeze.py:40-42`。`strict_load_json_object` (`s8b_oracle_artifacts.py:104-133`) で読み、`freeze["holdouts"]` の全 key を sort する。 |
| `configuration_ids` | 各 holdout について `_holdout_configuration_ids` (`s8b_oracle_manifest.py:577-606`) を呼ぶ。全 holdout の集合が同一でなければ拒否し、共通集合を sort する。これは将来の consumer 検査 `s8b_oracle_manifest.py:1220-1241` と同じ完全積条件になる。 |
| `generator_versions` | canonical 5 source は `_GENERATOR_SOURCES` (`s8b_oracle_manifest.py:65-74`) だけを正本とし、各 `root/path` を `_file_sha256` (`:186-194`) で live hash 化する。最終的に `_validate_generators` (`:458-498`) を含む spec validator が再照合する。 |
| `binding_identity` | sorted holdout × configuration の各 cell を `s8b_materialization.prepare_binding` (`s8b_materialization.py:98-146`) に渡す。`ccbench_pin` は入力済み `run_contract`、`cxx` は上記 site resolver 由来とし、返却された 5-key identity に `holdout_id` / `configuration_id` を付ける。genome、source token、variant ID、entry hash、binding hash の組立てを再実装しない。実 materialization の正本は `s1_direct_comparison.prepare_cell` (`s1_direct_comparison.py:593-723`)。 |
| `schedule_sha256` | `build_schedule` (`s8b_oracle_manifest.py:233-298`) に研究設計値と freeze 由来の二軸を渡し、`schedule_sha256` (`:301-303`) で導出する。 |
| `schema_version` | `s8b_oracle_spec.SCHEMA_VERSION` (`s8b_oracle_spec.py:18`) をそのまま使う。 |

### canonical strict bytes と SHA-256

`orchestrator/campaign/s8b_oracle_spec_candidate.py:148-205` では次の順に限定する。

1. 上記導出値と研究設計値から document を1回組み立てる。
2. `validate_reviewed_spec(document, root=root)` (`s8b_oracle_spec.py:105-180`) を必ず通す。
3. validator が返した copy を既存 `_canonical_bytes` (`s8b_oracle_spec.py:98-102`) で UTF-8・sorted keys・compact separator・非有限値拒否の bytes にする。
4. その bytes を `strict_load_json_object` へ戻し、再 canonical 化との byte-for-byte 一致を確認する。
5. `sha256(raw_bytes)` を計算し、`ReviewedSpecCandidate(raw_bytes, sha256, document, schedule)` として返す。

schema、schedule、binding、generator の validator を producer に複写しない。producer 固有の検査は「入力6 keys」「freeze の全 holdout が同じ configuration 集合を持つ」「strict round-trip」だけとする。

CLI は canonical bytes を末尾 LF なしで stdout、`sha256=<64hex>` を stderr に出す。`--output`、fixed-path installer、writer API は設けず、producer 自身は repo 内へ durable file を書かない。materialization の使い捨て resource は既存 context manager (`s8b_materialization.py:125-146`) に cleanup を委ねる。

段7で `output/insights/` に裁定パッケージを置く場合も、それは producer の戻り値を親 orchestration が保存する別手番である。producer に `SPEC_REL` や manifest candidate directory への書込み権限は持たせない。

### 専用テスト

新規 `orchestrator/tests/test_s8b_oracle_spec_candidate.py`:

- `:1-76` — fake freeze、canonical source files、materializer spy
- `:79-135` — freeze/live source/schedule/binding の完全導出
- `:138-170` — production serializer から独立した bytes/hash 照合
- `:173-205` — configuration 集合不一致と validator bypass の負例
- `:208-240` — preview CLI と durable namespace 非書込み

既存 `s8b_oracle_spec_fixture.independent_canonical_bytes` (`s8b_oracle_spec_fixture.py:27-35`) を独立 serializer として再利用し、fixture production 化や同 file の編集は行わない。

## 単位 B — durable 発行 lifecycle 検査

### 編集差分

`orchestrator/tests/test_s8b_oracle_manifest_contract.py` を次の範囲で編集する。

- `:5-14` — `hashlib`、`tempfile`、`s8b_oracle_spec` の import を追加
- 現行 `:130-146` — zero-file assertion を削除ではなく lifecycle helper と repository-state test に置換
- 新 `:130-225` — lifecycle helper、現実の repo 状態検査、正例・負例

既存 node は意味に合わせて次へ置換する。

```text
test_durable_reviewed_spec_lifecycle_matches_approval_state
```

helper の判定は次の exact state machine とする。

| approval pin | 許される durable regular file |
|---|---|
| `APPROVED_SPEC_SHA256 is None` | 2 namespace 合計 0 件 |
| 64-hex pin `h` | `SPEC_REL` の1件だけ。bytes の SHA-256 が `h` と完全一致 |
| その他 | 拒否 |

列挙対象は以下の両 namespace 配下の全 file である。

```text
output/s8b-oracle-spec
output/s8b-oracle-manifest-candidates
```

承認済みでも manifest candidate は0件であり、`output/s8b-oracle-spec/reviewed_spec.json` 以外の sibling/subdirectory file も拒否する。canonical spec の欠落、pin 不一致、余分な durable file はそれぞれ別の assertion message にする。

### 実際に発火する経路

repository-state test は毎回、実 repo の次を直接読む。

```text
s8b_oracle_spec.APPROVED_SPEC_SHA256
ROOT/output/s8b-oracle-spec/reviewed_spec.json
ROOT/output/s8b-oracle-manifest-candidates/**
```

したがって lifecycle は次の具体的な状態遷移で発火する。

```text
現在:
(None, durable files = empty)
  -> unapproved branch が通る

将来の承認 diff:
(h, reviewed_spec.json bytes B only, SHA256(B) = h)
  -> approved branch が通る

不正発行:
(None, reviewed_spec.json exists)
(h, reviewed_spec.json missing)
(h, SHA256(reviewed_spec.json) != h)
(h, reviewed_spec.json + any other durable file)
  -> それぞれ落ちる
```

恒真化を避けるため、同 file に一時 directory を用いた以下の test を置く。

- `test_durable_reviewed_spec_lifecycle_accepts_exact_pinned_file`
- `test_durable_reviewed_spec_lifecycle_rejects_unapproved_file`
- `test_durable_reviewed_spec_lifecycle_rejects_hash_mismatch`
- `test_durable_reviewed_spec_lifecycle_rejects_extra_file`

最後の負例が単位Bの純増検出力、すなわち「承認済みの canonical pinned file 以外が存在したら拒否」を直接発火させる。

production module には lifecycle gate を追加しない。この検査の実効経路は repository acceptance test であり、runtime consumer の新しい admission 条件ではない。

## 受理集合の変化

合法な lifecycle state を `(pin, durable-map)` と書く。

```text
L_current = {(None, empty)}

L_after =
    L_current
    union
    {(h, {SPEC_REL -> B}) | SHA256(B) = h}

L_current is a strict subset of L_after
```

生の不正状態まで含めると、現行 zero-file test が偶然許す `(non-None, empty)` は計画後に拒否される。これは受理集合の拡大ではなく、pin 設定済み・file 欠落という不可能状態の fail-closed 化である。

producer の受理集合は、現行の `P_current = empty` から、freeze・live source・研究設計値の全検査を通る入力集合 `P_after` へ純増する。

消費側は完全に不変である。

- 触る production 行: 新規 candidate module のみ。
- 触らない行:
  - `APPROVED_SPEC_SHA256` / `SPEC_REL`: `s8b_oracle_spec.py:19-23`
  - `_load_approved_spec_bytes`: `:183-201`
  - `validate_approved_spec_snapshot`: `:204-256`
  - `load_approved_spec`: `:259-276`
  - `verify_manifest`: `s8b_oracle_manifest.py:1018-1166`
  - approved spec projection comparison: `:1123-1157`

したがって、現 checkout では pin が `None` のままなので consumer の受理集合は前後とも空である。将来 pin を設定した場合の受理 predicate も同じコードのままであり、`C_before = C_after` である。

## 既存テストへの波及

変更する production file は新規 path なので、既存 test からの直接 import は0件である。直接被覆は新規 `test_s8b_oracle_spec_candidate.py` が担う。

一方、`campaign/*.py` 全体を静的列挙する既存 test は新 module を参照するため、次が波及面になる。

- `orchestrator/tests/test_s8b_oracle_manifest_contract.py::test_loader_production_consumer_sets_are_pinned_for_spec_reverification`
- `orchestrator/tests/test_s8b_oracle_manifest_contract.py::test_verify_manifest_production_consumer_set_is_auxiliary_pin`
  - 新 module は `load_official_*` と `verify_manifest` を呼ばないため expected consumer set は不変。
- `orchestrator/tests/test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches`
  - `prepare_binding` は使うが、candidate module から `buildcache.build*` や direct CMake を呼ばない。
- `orchestrator/tests/test_s8b_floor_campaign.py::test_production_use_perf_keyword_call_sites_are_a_closed_set`
  - producer は性能測定や `use_perf` call site を追加しない。
- `orchestrator/tests/test_p3_build_authority_cli.py::test_python_ccbench_manual_materializers_are_explicitly_non_admissible`
  - producer 自身に `--build` や独自 materializer を置かない。
- `orchestrator/tests/test_s8b_ratified_freeze.py::test_no_production_module_constructs_ratified_freeze_directly`
  - active freeze 不在を補うための `RatifiedFreeze(...)` 偽造は行わない。
- `orchestrator/tests/test_s8b_oracle_report.py::test_build_observations_production_caller_is_main_only`
  - generator source を hash するだけで report API を呼ばない。

直接編集される contract test では、既存3 inventory node に加えて lifecycle 5 node が赤になりうる。`s8b_oracle_spec.py`、`s8b_oracle_manifest.py`、`s8b_materialization.py` は編集しないため、それらを直接参照する既存 test の期待値更新は不要である。

## 変異事前登録

| 壊す1行 | 期待して落ちる pytest node id |
|---|---|
| freeze の `holdout_ids` を sort せず入力順のまま使う | `orchestrator/tests/test_s8b_oracle_spec_candidate.py::test_candidate_derivation_is_order_independent` |
| configuration 集合の holdout 間一致検査を削除する | `orchestrator/tests/test_s8b_oracle_spec_candidate.py::test_candidate_rejects_nonuniform_configuration_products` |
| generator SHA を固定値または caller 入力へ置換する | `orchestrator/tests/test_s8b_oracle_spec_candidate.py::test_candidate_hashes_live_canonical_generator_sources` |
| `schedule_sha256(schedule)` を入力値または別 object の hash に置換する | `orchestrator/tests/test_s8b_oracle_spec_candidate.py::test_candidate_returns_independent_canonical_bytes_and_sha256` |
| `validate_reviewed_spec` 呼出しを削除する | `orchestrator/tests/test_s8b_oracle_spec_candidate.py::test_candidate_calls_reviewed_spec_validator_exactly_once` |
| producer から `root / SPEC_REL` へ書き込む | `orchestrator/tests/test_s8b_oracle_spec_candidate.py::test_candidate_leaves_durable_namespaces_untouched` |
| unapproved branchを durable file 非空でも許す | `orchestrator/tests/test_s8b_oracle_manifest_contract.py::test_durable_reviewed_spec_lifecycle_rejects_unapproved_file` |
| approved branchの SHA-256 比較を削除する | `orchestrator/tests/test_s8b_oracle_manifest_contract.py::test_durable_reviewed_spec_lifecycle_rejects_hash_mismatch` |
| manifest candidate directoryを列挙対象から外す | `orchestrator/tests/test_s8b_oracle_manifest_contract.py::test_durable_reviewed_spec_lifecycle_rejects_extra_file` |

## provisional 裁定への回答

- **P1 — 支持する。** approval loader と、freeze/materializer/live source に依存する生成器の分離が必要である。新規 `s8b_oracle_spec_candidate.py` に置き、consumer module は編集しない。
- **P2 — 支持する。** lifecycle は repository publication の契約であり、production consumer に新 gate を足すと不変条件2の検証対象を増やしてしまう。実 repo path を読む contract testと非恒真的な正負例で十分に発火させる。
- **P3 — 支持する。** active ratified freeze がない状態で `n`、seed、block、campaign、run contractをrepo内 authorityから確定する根拠はない。これらと除外理由は exact external inputとし、軸・binding・generator・schedule hashだけを機械導出する。

反対意見はない。未確定なのは具体的な研究設計値と、人間が承認する最終 bytes/hashだけであり、producer/lifecycle の実装択一ではない。

## 親による実測

実装後は少なくとも次を `tools/run_tests.py` 経由で実測する。

- 新規 candidate producer test
- `test_s8b_oracle_manifest_contract.py`
- `test_s8b_oracle_manifest.py`
- `test_s8b_materialization.py`
- 上記 campaign-wide inventory nodes

この計画段ではいずれも実走しておらず、緑とは主張しない。

## 総括

- **編集 file と行範囲:** 単位Aは新規 `orchestrator/campaign/s8b_oracle_spec_candidate.py:1-245` と新規 `orchestrator/tests/test_s8b_oracle_spec_candidate.py:1-240`。単位Bは `orchestrator/tests/test_s8b_oracle_manifest_contract.py:5-14,130-225`。
- **受理集合:** durable lifecycle は合法状態上で `{unapproved-empty} ⊊ {unapproved-empty, approved-exact-one}`。producer は空集合から検証済み候補集合へ増えるが、3 consumer の受理集合は完全に同一。
- **未解決の設計択一:** なし。研究設計の具体値と最終承認 bytes/hash は意図的に外部入力・ユーザー手番として未確定のまま残す。
- **親 brief への反対意見:** P1、P2、P3をすべて支持する。scope、不変条件1〜6、v1据え置きのいずれにも反対なし。