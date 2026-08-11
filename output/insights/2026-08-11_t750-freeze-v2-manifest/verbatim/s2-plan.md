# 段 2 実装プラン

指定された資料はすべて読めた。以下は read-only の静的プランであり、実装・pytest・実走・queue 投入は行っていない。

## provisional 裁定 P1〜P5

| 裁定 | 判断 | 根拠と補強 |
|---|---|---|
| P1 | 賛成。ただし「人間」は既存 trust model 内の意味に限定 | approval 発行 CLI、`--approver`、既定承認を作らず、canonical record と非 merge・逐語 `AI-Agent: none`・approval だけを追加する commit を要求する。これは `s8b_ratified_freeze.py:525-549` と同型だが、暗号学的な人間証明ではない。 |
| P2 | 賛成、さらに holdout 集合と順序も固定 | `configuration_ids` は各 active holdout の構成集合と exact 一致させる。併せて `holdout_ids == sorted(active.holdouts)`、両 ID list の重複なし・辞書順を要求する。holdout ごとの構成集合が異なる場合、union/intersection に丸めず拒否する。 |
| P3 | 賛成 | 承認 record 内の `budget` と別入力 budget の canonical bytes を比較し、数値型の違いも不一致にする。上限値は発明せず、人間がゼロ・巨大値を承認した場合も「その数値を承認した」という裁定どおり扱う。 |
| P4 | 賛成。任意の repo 内 path よりさらに狭める | A は `output/s8b-freeze-candidates/`、B/C は `output/s8b-oracle-manifest-candidates/` のみ許可する。canonical namespace・root 外・symlink・既存 leaf を拒否する。 |
| P5 | 条件付き賛成 | 最終所有は素集合にできるが、`s8b_v2_freeze_fixture.py` は両単位の正例源になる。最初に fixture 拡張だけを直列で確定し、その後 A/B を並列化する。A が fixture を所有したまま B と同時編集する形にはしない。 |

## 単位 A — W-3 freeze v2 producer

### `s8b_holdout_freeze.py` の変更点

- `s8b_holdout_freeze.py:11-21`
  - strict JSON、有限数検査、floor protocol/result 検査に必要な import を追加する。
  - `s8b_floor_contract`、`s8b_floor_stats`、`env_contract`、`s8b_launch_cert.parse_official_run_path` を利用する。`s8b_floor_campaign.py` は import も編集もしない。

- `s8b_holdout_freeze.py:34-39`
  - 次の定数を追加する。
    - `V2_SCHEMA_VERSION = "8b-holdout-freeze/v2"`
    - `FLOOR_PROTOCOL_REL = "output/s8b-freeze/floor_protocol.json"`
    - `V2_CANDIDATE_REL = "output/s8b-freeze-candidates/holdout_freeze.v2.g1.json"`
    - `BUDGET_APPROVAL_REL = "output/s8b-freeze-budget-approvals/g1.json"`
    - v2 added-key、floor result exact-key、budget exact-key、approval exact-key 集合
    - approval scope の固定文字列
  - `TOP_LEVEL_KEYS`、T-080 定数、ratified transition table は変更しない。

- `s8b_holdout_freeze.py:144-151` の直後
  - `_strict_load_object_bytes(raw, label)` を追加する。UTF-8、duplicate key、NaN/Infinity、top-level object を拒否する。
  - `_canonical_bytes(value)` を `ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False` で定義する。
  - 既存 `_load_json` は変更せず、v1 の受理集合に影響させない。

- `s8b_holdout_freeze.py:154-180` の git helper 群の後
  - captured HEAD の blob を読む `_blob_at_head()` と、HEAD/worktree bytes の一致検査を追加する。
  - v1 は canonical `FREEZE_REL` を `_read_regular_nofollow` で一度捕捉し、SHA-256 が `t080_freeze_migration.HOLDOUT_RAW_SHA256` と一致した場合だけ使う。実測 hash をそのまま新しい trust root にしない。
  - budget approval は固定 path の HEAD blob、worktree bytes、unique introduction、履歴不変、非 merge、逐語 `AI-Agent: none`、commit diff が approval 1 file の追加だけ、を検査する。`approver` 文字列だけでは承認扱いしない。

- `s8b_holdout_freeze.py:848-870` の no-follow reader の後
  - `_validate_v2_candidate_output(root, output)` と create-only writer を追加する。
  - 検査後の通常 `Path.open()` ではなく、root directory FD から `O_DIRECTORY|O_NOFOLLOW` で各 component を辿り、leaf は `O_CREAT|O_EXCL|O_NOFOLLOW` で作る。検査と open の間の symlink 差替え窓を残さない。

- `s8b_holdout_freeze.py:958` と parser `:961` の間
  - `build_v2_g1_candidate(...)` と `generate_v2_g1_candidate(...)` を追加する。
  - 全入力の捕捉・検証・文書構築・canonical serialization が完了してから、最後に一度だけ writer を呼ぶ。
  - `build_document:514-574`、`generate:577-606`、`verify_document:690-831`、`verify:833-845`、`verify_cli_with_t080_receipt:878-958` の本体は変更しない。

- `s8b_holdout_freeze.py:961-973`
  - `generate-v2-candidate` subcommand を純増する。
  - argv は `--floor-result PATH`、`--budget PATH`、任意 `--output` のみ。`--output` の既定は `V2_CANDIDATE_REL`。
  - `--freeze`、`--approver`、`--approved-at`、`--budget-approval`、generation 番号指定は設けない。v1 と budget approval は固定 path から読む。

- `s8b_holdout_freeze.py:976-996`
  - 現在の `else == verify` を明示的 `elif args.command == "verify"` にし、新 subcommand 分岐を追加する。
  - 既存 `search/generate/verify` の引数と return code は変えない。

### v2 g1 top-level schema と導出元

`TOP_LEVEL_KEYS` は `s8b_holdout_freeze.py:609-614` の18件、追加6件は `s8b_ratified_freeze.py:100-104` である。

| top-level key | 値の導出元 |
|---|---|
| `what` | 捕捉した v1 `/what` を deep copy |
| `schema_version` | 固定値 `8b-holdout-freeze/v2` |
| `frozen_at_head` | candidate 構築開始時に一度捕捉した `git rev-parse HEAD` |
| `design_source` | `path` は v1 `/design_source/path` のまま、`sha256` は `frozen_at_head:path` の Git blob bytes |
| `known_axes_freeze` | v1 record を完全コピー。ただし `frozen_at_head:path` の blob hash が記録値と一致しなければ拒否 |
| `generator` | `path` は v1 `/generator/path` のままかつ `SCRIPT_REL` と一致必須、`sha256` は `frozen_at_head:SCRIPT_REL` の blob bytes |
| `match_convention` | v1 の同 field を deep copy |
| `search` | v1 の同 field を deep copy |
| `holdouts` | v1 の同 fieldを deep copy |
| `positive_control` | v1 の同 fieldを deep copy |
| `derangement` | v1 の同 fieldを deep copy |
| `confirmed_by` | v1 の同 fieldを維持。budget approver へ読み替えない |
| `confirmed_at` | v1 の同 fieldを維持 |
| `floor` | `result.floors[h]` から `diagnostics` を除き、`{"by_holdout": {h: {"pairs", "scale_ref", "scalar_alt"}}}` へ射影 |
| `budget` | 独立に strict-load した budget と、human approval record `/budget` の canonical bytes が一致した値 |
| `refreeze_note` | 固定 prefixと、budget approval record の repo-relative path・raw SHA-256 から作る監査文字列 |
| `scope_note` | v1 の同 fieldを維持 |
| `binding_rule_note` | v1 の同 fieldを維持 |
| `generation_number` | exact integer `1` |
| `supersedes_sha256` | 捕捉 v1 raw SHA-256。ただし先に T-080 固定値との一致を要求 |
| `env_tag` | full-validated floor protocol `/env_tag`。result `/env_tag` および official result path の env tag と exact 一致 |
| `floor_protocol` | `{"path": FLOOR_PROTOCOL_REL, "sha256": SHA256(protocol raw bytes)}` |
| `floor_source` | `{"path": canonical repo-relative floor-result path, "sha256": SHA256(result raw bytes)}` |
| `measurement_closure` | 現在の repository scan で得た holdout conjunction-hit path のうち専用 role を除いた集合を辞書順に並べ、各 raw bytes を hash |

したがって、

```text
set(g1) =
  TOP_LEVEL_KEYS
  ∪ {generation_number, supersedes_sha256, env_tag,
     floor_protocol, floor_source, measurement_closure}
  = s8b_ratified_freeze.V2_TOP_LEVEL_KEYS
```

となる。

v1 から変わる leaf は `/floor`、`/budget`、`/refreeze_note`、`/schema_version`、`/generator/sha256`、`/design_source/sha256`、`/frozen_at_head` と追加6 field のみであり、すべて `s8b_ratified_freeze.py:128-133` の `_TRANSITION_V1_TO_G1` 内にある。特に `generator/path`、`design_source/path`、`known_axes_freeze`、holdout/search/binding は変更しない。

### floor result と closure

floor result は次をすべて満たす場合だけ受理する。

1. repo 内の canonical relative path で、`s8b_launch_cert.py:147-180` により official `result.json` path と判定される。
2. non-symlink regular file を一度捕捉できる。
3. exact result key 集合、`schema == s8b-floor-result/v2`、`mode == "official"`、`eligible_for_refreeze is True`。
4. `freeze_sha256` が固定 v1 hash、`protocol_sha256` が固定 protocol raw hash、env tag が protocol/path と一致。
5. protocol は `s8b_floor_contract.validate_protocol:105-227` を通り、その freeze record が v1 canonical path/hash を指す。
6. expected cells は v1 holdout binding から独立導出し、`s8b_floor_stats.verify_floor_artifact:434-667` が空の problem list を返す。
7. result の holdout/configuration 集合が expected cells と exact 一致する。

`measurement_closure` は caller 引数にしない。`search_repository` の現在 hit を再導出し、同一 run directory の `result.json`、`manifest.json`、`journal.jsonl`、`launch_certificate.json` と `floor_protocol`、generation candidate pathを除外する。残りの path は canonical relative・一意・regular no-follow・辞書順で `{canonical_path,sha256}` にする。これにより `s8b_ratified_freeze.py:898-927` の schema を満たし、将来の `:980-1001` の G/H/worktree hash 検査へ渡せる。

現 repo に実 floor result はないため、通常の CLI は floor result の読取り段階で失敗し、writer を一度も開かない。空 result、pilot、`eligible_for_refreeze=false`、protocol/result の自己申告だけを揃えた artifact も拒否する。

### budget approval record

固定 path `output/s8b-freeze-budget-approvals/g1.json` の exact schema は次とする。

```json
{
  "approved_at": "YYYY-MM-DDTHH:MM:SSZ",
  "approver": "non-empty human identifier",
  "budget": {
    "oracle_shared": true,
    "per_holdout_bench_s": {
      "<every-v1-holdout-id>": 0
    },
    "total_bench_s": 0
  },
  "scope": "s8b-holdout-freeze/v2:g1-budget"
}
```

- top-level exact key 集合は `{approved_at, approver, budget, scope}`。
- budget exact key 集合は `{total_bench_s, per_holdout_bench_s, oracle_shared}`。
- bool を数値として受理せず、各数値は有限非負、per-holdout keys は v1 holdouts と exact 一致、`oracle_shared is True`。
- raw record は canonical bytes と byte-for-byte 一致させる。
- CLI が別途読む budget JSON の canonical bytes と `approval["budget"]` の canonical bytes を比較する。正規化後の float 値同士では比較しない。
- approval record を作る CLI/APIは実装しない。

### 出力 gate の署名

A の出力を受理する条件は、次の論理積をすべて満たす場合だけとする。

```text
SafeA(root, raw_output) :=
  root は既存・non-symlink directory
∧ CLI root は compile-time ROOT であり --root がない
∧ raw_output は空でない raw POSIX relative path
∧ absolute、\, //、末尾 /、NUL/control、"."、".." component を含まない
∧ raw_output == output/s8b-freeze-candidates/holdout_freeze.v2.g1.json
∧ output/s8b-freeze/ とその子孫ではない
∧ root FD から leaf までの全既存 component が O_NOFOLLOW で開ける directory
∧ leaf が存在しない
∧ leaf を O_CREAT|O_EXCL|O_NOFOLLOW で生成できる
```

通る正例は `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`。`output/s8b-freeze/holdout_freeze.v2.g1.json`、`../outside.json`、root 外 absolute path、symlink parent、既存 regular file、既存 symlink はすべて拒否する。

## 単位 B/C — reviewed spec と oracle manifest CLI

### 新 module

`orchestrator/campaign/s8b_oracle_spec.py` を新設する。現時点では存在しないため既存 line 番号はない。

理由は、human approval の canonical bytes・Git provenance・固定 namespace を、一般用途の manifest builder から分離するためである。`s8b_oracle_manifest.py` の既存 programmatic API を「approved」と見なす変更はしない。

固定 path は次とする。

```text
output/s8b-oracle-spec/reviewed_spec.json
output/s8b-oracle-spec/reviewed_spec.approval.json
output/s8b-oracle-spec-candidates/reviewed_spec.json
```

本 wave は最初の2 pathへ実ファイルを作らない。

### reviewed spec schema

top-level exact key 集合は次の8件とする。

```json
{
  "allowed_excluded_reasons": [],
  "binding_identity": [],
  "campaign_ids": {},
  "generator_versions": {},
  "run_contract": {},
  "schedule_parameters": {},
  "schedule_sha256": "<64 lowercase hex>",
  "schema_version": "s8b-oracle-reviewed-spec/v1"
}
```

`schedule_parameters` の exact key 集合は次の5件。

```json
{
  "block_sizes": {"<block-id>": 1},
  "configuration_ids": ["..."],
  "holdout_ids": ["..."],
  "master_seed": "...",
  "n": 1
}
```

各 field の検査は次のとおり。

- `n/master_seed/block_sizes/holdout_ids/configuration_ids` を `build_schedule:202-251` に渡して rows を再生成する。
- 再生成 schedule の `schedule_sha256:254-256` と spec 値を exact 比較する。
- `run_contract` は `s8b_oracle_manifest.py:40-43` の key 集合と exact 一致させたうえで `_validate_run_contract:377-408` に通す。既存 validator の「必須 key の部分集合」受理を spec 境界へ持ち込まない。
- `campaign_ids` は `block_sizes` と一対一、値は非空・重複なし。
- `binding_identity` は再生成 schedule に対して `_validate_binding_identity:468-518` を通す。
- `generator_versions` は `_validate_generators:411-451` を通す。
- `allowed_excluded_reasons` は非空文字列・一意・順序を含めて承認 bytes に固定する。
- spec raw は strict canonical bytes、末尾 LF なしとする。

`binding_identity`、generator pin、除外理由も spec に含めるのは、manifest CLI に別の caller-controlled 入力面を残さないためである。`campaign_config_preimages` は含めず、既存 `build_manifest:739-747` と同じく再導出する。

### spec approval record

固定 pathの exact schema は既存 ratified approval と同じ4-field形にする。

```json
{
  "approved_at": "YYYY-MM-DDTHH:MM:SSZ",
  "approver": "non-empty human identifier",
  "scope": "s8b-oracle-reviewed-spec/v1",
  "spec_sha256": "<SHA-256 of exact reviewed_spec.json raw bytes>"
}
```

次をすべて要求する。

- strict canonical bytes、exact key集合、固定 scope、UTC seconds。
- `spec_sha256` は spec の一度捕捉した raw bytes hash と一致。
- spec は先行 commit で一意導入され、approval 時点まで改変されていない。
- approval は後続の非 merge commitで導入され、逐語 `AI-Agent: none`。
- approval commit の diff は approval record 1 file の追加のみ。
- spec/approval の HEAD blob と worktree bytes が一致。
- approval writer、`--approver`、approval 既定値は作らない。

### `s8b_oracle_manifest.py` の変更点

- `s8b_oracle_manifest.py:3-18`
  - `argparse`、`sys` と direct-script package bootstrap を追加する。
  - spec と ratified module は CLI helper 内で遅延 importし、既存 import graphへの影響を限定する。

- `s8b_oracle_manifest.py:693-769`
  - 本体を `_build_manifest_from_snapshot(freeze, freeze_record, freeze_source_path, ...)` へ抽出する。
  - 既存 `build_manifest(...)` は `:698-700` と同じく caller の freeze path を読み、同じ引数・検査・戻り型で内部 helperへ渡す wrapper とする。既存 programmatic 受理集合は変更しない。
  - CLI用 `build_manifest_from_ratified(...)` は `load_ratified_freeze` が返した immutable document/hashだけを snapshot helperへ渡し、freeze fileを再読込しない。
  - generation path は loader が保証する世代番号から `output/s8b-freeze/holdout_freeze.v2.gN.json` と導出し、record hash は `ratified.sha256` を使う。

- `s8b_oracle_manifest.py:772-807`
  - 既存 `_atomic_create_json` / `write_manifest` は変更しない。既存 APIの任意 path受理を狭めない。
  - CLI専用 writer を `:807` の後へ追加し、Aと同じ raw path・dirfd・nofollow・exclusive-create 規律を適用する。

- `s8b_oracle_manifest.py:935` の後
  - `_parser()`、`build_approved_manifest()`、`main()` と direct CLI entrypoint を追加する。

### CLI surface

```text
python3 orchestrator/campaign/s8b_oracle_manifest.py \
  build-approved \
  --output output/s8b-oracle-manifest-candidates/manifest.json
```

argv に存在する値入力は `--output` だけである。以下は parser に登録せず、指定時は argparse rc=2 とする。

```text
--schedule
--schedule-path
--n
--master-seed
--block-sizes
--holdout-id
--configuration-id
--freeze
--freeze-path
--campaign-id
--campaign-ids
--spec
--approval
--approver
--root
```

処理順は次とする。

1. `load_ratified_freeze(ROOT)` を一度呼ぶ。legacy fallback はしない。
2. 固定 path の reviewed spec と approval を一度捕捉して検証する。
3. active freeze の全 holdout を列挙する。
4. spec の schedule parameters から scheduleを再生成し、hashを照合する。
5. exact cell集合を検査する。
6. active snapshotと approved specから manifestを構築する。
7. 最後に CLI専用 safe writerで出力する。

### configuration exact 検査

`s8b_oracle_manifest.py:530-559` の `_holdout_configuration_ids` は再利用できる。同じ module 内の既存検査であり、stock 実在も同時に確認できる。

```text
spec_holdouts == sorted(active.document["holdouts"])
and
for every h:
    set(spec.configuration_ids)
      == _holdout_configuration_ids(active.document, h)
and
spec.configuration_ids == sorted(spec.configuration_ids)
```

holdout ごとの集合が異なる場合、単一の global `configuration_ids` では表現不能なので明示拒否する。union、intersection、先頭 holdout の集合を使う fallback は設けない。この検査は CLI 専用経路に置き、generic `build_manifest` へ追加しない。

### active がない現 repo での戻り

`load_ratified_freeze:1315-1334` は `resolve_active_generation:1214-1312` を経由し、現 repo では `:1254-1256` の `RatifiedFreezeError(reason="no-active")` になる。

CLI はこれを次へ写像する。

```text
stderr: refused: no-active-ratified-freeze
return code: 2
output: directory/file とも未作成
```

active が存在するが approved spec がない場合は `no-approved-spec`、spec/approval が壊れている場合は「不在」と丸めず固有の invalid reason を返す。`namespace-dirty` など active loader の別 reason も `no-active` に丸めない。

## テスト面

### fixture の直列前置き

`orchestrator/tests/s8b_v2_freeze_fixture.py:67` の後へ、純粋な synthetic helper を追加する。

- full v2 floor result と protocol
- budget JSON と canonical budget approval
- reviewed spec と approval
-固定 schedule/hash の golden
- candidate の expected floor projection

実計測、subprocess、repo canonical pathへの書込みは fixture 内に入れない。

### 新規 node

| 追加先 | node | assert の要旨 | 期待値を緩めない理由 |
|---|---|---|---|
| `test_s8b_holdout_freeze.py:749` 後 | `test_v2_g1_candidate_exact_schema_projection_and_transition` | fixtureから作った candidate の24 key、全導出値、hard-coded transition allowlistとの diff一致 | 新しいv2正例だけを追加し、v1正例は触らない |
| 同 | `test_v2_candidate_requires_existing_eligible_official_floor` | missing/pilot/eligible falseで出力なし | 新拒否の追加 |
| 同 | `test_v2_candidate_rejects_floor_binding_and_projection_drift` | schema、freeze hash、protocol hash、env、cells、floors改変をparameterizeして拒否 | fixture正例から1点だけ壊す |
| 同 | `test_v2_candidate_budget_must_equal_human_approval_canonical_bytes` | `100`対`100.0`を含むcanonical差、holdout欠落、extra keyを拒否 | 数値比較への緩和を禁止 |
| 同 | `test_v2_candidate_rejects_nonhuman_or_noncanonical_budget_approval` | AI trailer、merge、extra commit file、duplicate key、非canonical rawを拒否 | approver文字列だけで通る経路を新たに閉じる |
| 同 | `test_v2_candidate_derives_exact_measurement_closure` | fixture hit集合から専用roleを除いた辞書順path/hashとexact一致 | caller申告closureを受理しない |
| 同 | `test_v2_candidate_output_gate_rejects_escape_namespace_symlink_and_existing` | canonical namespace、`..`、absolute、symlink parent、既存leafを全拒否し正例1件だけ作成 | writer受理を候補rootへ狭める |
| 同 | `test_v2_candidate_cli_has_no_approval_issuance_surface` | `--approver/--approval/--freeze` が argparse rc2 | 承認面を追加しない |
| 同 | `test_v2_candidate_has_no_floor_execution_or_queue_surface` | 新command call graphにfloor campaign起動・scheduler/queue APIがない | W-1/W-2/queue面を開かない |
| `test_s8b_ratified_freeze.py:1869` 後 | `test_produced_v2_g1_is_loadable_only_after_synthetic_ratification` | fixture producer bytesをGへ導入し、別human A commit後だけreal loaderが受理 | verifier期待を変えずproducer互換性を追加検証 |
| 同 | `test_produced_v2_g1_without_approval_pointer_is_no_active` | producer candidateだけならreason=`no-active` | 既存未承認拒否を具体的producerへ強化 |
| `test_s8b_oracle_manifest.py:794` 後 | `test_reviewed_spec_candidate_and_human_approval_round_trip` | fixture spec/approvalがcanonical loaderを通る | 新schemaの正例のみ |
| 同 | `test_reviewed_spec_rejects_schema_canonical_hash_and_history_tamper` | unknown/missing/duplicate/NaN、spec hash、履歴改変を拒否 | schemaを緩めない |
| 同 | `test_reviewed_spec_rejects_ai_approval_and_has_no_approval_writer` | AI trailerとapproval発行API不存在 | AI自己承認面を閉じる |
| 同 | `test_schedule_sha256_fixture_literal_rejects_builder_drift` | fixtureに独立固定したschedule rows/hashと再生成結果を比較 | 実装から期待hashを自己再計算しない |
| 同 | `test_approved_cli_regenerates_fixture_schedule_and_writes_manifest` | approved spec＋synthetic active snapshotからmanifestを安全rootへ作成 | generic builderの期待値は変更しない |
| 同 | `test_approved_cli_rejects_human_approved_subset_configuration_spec` | approval/hashが正しい縮小specでもactive構成集合不一致で拒否 | hash tamper検査だけに依存せずA-9を閉じる |
| 同 | `test_approved_cli_rejects_holdout_or_configuration_order_drift` | exact setでも非canonical順序は拒否 | scheduleの多義性を増やさない |
| 同 | `test_approved_cli_argv_has_only_output` | schedule/freeze/spec/campaign/approver系optionが全てrc2 | caller供給面を純減 |
| 同 | `test_approved_cli_uses_ratified_loader_without_legacy_fallback` | loaderを各1回spyし、legacy loader未呼出し | active authorityを弱めない |
| 同 | `test_approved_cli_returns_no_active_without_v2` |現状相当rootでrc2、reason、出力なし | v1 fallbackで緑にしない |
| 同 | `test_approved_cli_output_gate_rejects_escape_namespace_symlink_and_existing` | Aと同じ負例群＋manifest candidate正例 | 既存writerの広いAPIをCLIへ持ち込まない |

すべての新規正例は `s8b_v2_freeze_fixture.py` の生成物を経由する。個別test内で別の「通るfreeze/spec」を手書きしない。

### 影響を受ける既存 node

期待値は一切変更しない。

- v1 producer/verify:
  - `test_generate_refuses_overwrite_and_requires_confirmation`
  - `test_verify_rejects_source_hash_and_binding_tamper`
  - `test_verify_tolerates_per_axis_drift_and_rejects_snapshot_tamper`
  - `test_exempt_none_preserves_v1_prefix_report_bytes`
  - `test_verify_rejects_active_generation_worktree_drift`
  - `test_verify_rejects_unratified_generation_documents`
  - `test_verify_cli_accepts_active_t080_receipt_exact_match`
  - `test_verify_direct_cli_accepts_active_t080_receipt_exact_match`
  - `test_verify_cli_active_receipt_hash_mismatch_is_immediate_red`
  - `test_verify_cli_same_bytes_at_noncanonical_path_are_rejected`
  - `test_verify_cli_issued_receipt_failure_never_delegates_to_legacy_verify`
  - `test_verify_cli_known_axes_fire_condition_mismatch_is_red`
  - `test_verify_cli_rejects_bytes_changed_while_receipt_is_verified`
  - `test_verify_cli_rejects_artifact_changed_while_adapter_runs`
  - `test_verify_cli_never_issued_delegates_to_legacy_verify_and_keeps_drift_red`
  - `test_source_guard_has_no_static_concrete_axis_encoding`

- ratified compatibility:
  - `test_happy_path_resolves_and_loads`
  - `test_production_emitter_staged_builder_is_git_deterministic_across_roots`
  - `test_journal_manifest_may_precede_generation_and_executable_mode_is_accepted`
  - `test_legacy_freeze_binds_v1_by_constant`
  - `test_legacy_freeze_rejects_wrong_bytes`
  - `test_generation_with_nan_rejected`
  - `test_generation_with_approval_field_rejected`
  - `test_generation_supersedes_mismatch_rejected`
  - `test_namespace_dirty_rejected`
  - `test_candidate_generation_not_loadable`
  - `test_no_production_module_constructs_ratified_freeze_directly`

- oracle manifest:
  - `test_s8b_oracle_manifest.py:145-571` の schedule、builder、writer、binding、preimage、generator pin、tamper、single-block 全node。
  - `:594-703` の per-pair floor/budget snapshot 全node。
  - `:709-794` の strict JSON、run-contract pin、required freeze snapshot 全node。
  - これらは既存 `build_manifest` wrapper の受理意味論を守る回帰面で、assert更新はしない。

## 不変条件の機械的保証

| brief不変条件 | 落ちる検査 node |
|---|---|
| 1. v1受理集合、T-080、V1 hash不変 | 上記v1既存node群、`test_legacy_freeze_binds_v1_by_constant`、`test_legacy_freeze_rejects_wrong_bytes`。特に正常受理は `test_verify_rejects_source_hash_and_binding_tamper` 内の生成・verify、`test_verify_cli_accepts_active_t080_receipt_exact_match`、direct CLI nodeが守る。全入力に対する数学的同値までは有限nodeでは証明できないため、実装差分でも既存関数本体非変更を必須にする。 |
| 2. canonical namespaceへ書かない、pin不変 | 両 `*_output_gate_rejects_*`、`test_namespace_dirty_rejected`、`test_produced_v2_g1_without_approval_pointer_is_no_active`、既存 `test_frozen_artifacts_match_manifest` と `test_manifest_shape_is_exact`。 |
| 3. transition table不変 | `test_v2_g1_candidate_exact_schema_projection_and_transition` が期待pointer集合をtest側literalでも固定し、`test_generation_supersedes_mismatch_rejected` が連鎖を固定する。 |
| 4. fail-closed、AI自己承認なし | budget/specのnonhuman approval node、argv surface node、subset configuration node、legacy fallback禁止node。 |
| 5. 実走データを作らずfixtureのみ | `test_v2_candidate_has_no_floor_execution_or_queue_surface` と、全正例の fixture経由制約。production環境で実データが存在しないこと自体を恒久保証するnodeはない。 |
| 6. queue投入なし | `test_v2_candidate_has_no_floor_execution_or_queue_surface`。実装moduleからqueue/scheduler APIへの到達が追加された場合に落とす。外部processが別途queue投入しないことの保証はない。 |

## リスク

- 受理集合が黙って広がる箇所
  - `build_manifest:693-769` の抽出時に、既存 path loader、known-axes探索、run-contractの部分集合受理まで変更すると既存APIが変わる。wrapperの旧nodeを無変更で通す必要がある。
  - configuration exact検査をgeneric `build_manifest`へ入れると既存programmatic受理を狭めるため、CLI専用に置く。
  - parserの既存 `else` を残すと未知subcommandがverifyへ流れる可能性があるため明示分岐にする。
  - closureの専用role除外を広げすぎると未申告hitを隠す。除外集合は4 run artifact＋protocol/sourceだけをliteral固定する。
  - `_validate_run_contract` は現在extra keyを許すため、spec境界でexact key検査を忘れるとspec受理が広がる。

- hash pinが自己再計算へ退化する箇所
  - v1 `supersedes_sha256` を「読んだv1の現在hash」だけから作ると改変v1を自己追認する。先にT-080固定値と比較する。
  - schedule hashの正例を同じ `build_schedule` からtest内で計算すると、builder変異と共変する。fixtureにrows/hashの独立literalを置く。
  - budgetの両側を同じparsed objectから作ると比較が恒真になる。budget rawとapproval rawを独立捕捉する。
  - generator/design hashをworktreeから採ると、実行中のdirty producerを自己pinする。captured HEAD blobとworktree一致を先に要求する。
  - spec candidate builderがgenerator hashを自動生成しても、それ自体は承認ではない。固定human approval bytesが独立anchorである。

- AIが自己承認できる経路
  - `approver`文字列のみの検査、approval生成CLI、`--approver`、missing approvalの既定補完は全て禁止する。
  - specとapprovalを同じAI commitへ入れる、approval commitへ別変更を同梱する、AI trailerと`none`を併記する経路を拒否する。
  - 逐語 `AI-Agent: none` は暗号署名ではなく、AIが偽装可能という既知限界が残る。署名方式への変更は新裁定が必要。
  - in-process monkeypatchや直接private helper呼出しはCLI trust boundary外であり、最終権威はgeneration approvalとactive pointerに残る。

- `output/s8b-freeze/`へ書く経路
  - 既存legacy `generate --output` とgeneric `write_manifest(path, ...)` は任意path APIを維持するため、依然としてprogrammaticには到達可能である。今回閉じるのは新v2 subcommandとofficial manifest CLI。
  - path検査後に通常openするとsymlink swapでcanonical namespaceへ到達しうるため、dirfd＋nofollow writerが必須。
  - spec/budget approval candidate writerがcanonical pathを受理するとAIがauthority fileを設置できるため、candidate rootだけに制限する。
  - 人間が後日generation/approval/activeをcanonical namespaceへ設置する手番は意図的にscope外であり、本waveからは呼び出さない。

## 総括

- Aは旧generator module内で、固定v1・validated floor・human-approved budgetからg1 candidateだけを作る。
- B/Cは固定canonical reviewed specとactive ratified freeze以外のauthority入力をCLIから排除する。
- v1 API、transition table、ratified verifier、凍結pin、canonical namespaceは変更しない。
- 最大リスクは、Git trailerが人間性の暗号証明でないことと、既存generic writerの広いpath APIが残ることである。