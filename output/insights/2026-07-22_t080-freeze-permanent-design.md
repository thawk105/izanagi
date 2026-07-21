# [T-080] freeze 族恒久設計 wave の逐語凍結 (2026-07-22)

本ファイルは dev-wave [T-080] の段 1〜6 の逐語 (brief / codex 設計草案 / 敵対相談 2 本 / 親裁定 /
敵対レビュー 2 本 / 修正検証) を凍結する。成果物の正本は docs/freeze-permanent-design.md、
工程記録は docs/worklog.md と docs/decisions.md (D75)。

---
## 段 1: 親の brief

# brief: [T-080] freeze 族の恒久設計起草 (T-074+T-075 実作業)

## scope
- 成果物は設計パッケージのみ: 新規 `docs/freeze-permanent-design.md` + worklog 裁定パッケージ節 + decisions 記録。**コード・凍結成果物・テストは 1 byte も変えない** (実装は設計確定後の別 wave)
- 内容: (1) checker を pin しない新凍結形式、(2) dangling `frozen_at_head` を生まない生成手順、(3) S-1 歴代 5 世代 + holdout の全 6 freeze / trust root (`V1_FREEZE_SHA256`) / 世代交代許可表 (`_TRANSITION_V1_TO_G1`) / `FROZEN_MANIFEST` への移行計画、(4) ユーザー裁定が要る設計択一の列挙、(5) 実装 wave 分割案

## 確定済みユーザー裁定 (動かせない)
- [T-074] 恒久対応 (a): 「入力・出力を pin し checker は pin しない」設計へ移行 (worklog 2026-07-22 (1))
- [T-075] [T-074] と束ね: freeze を wave branch で生成 → rebase で SHA 書換え、を生成手順の変更で根絶 (生成時ガード / field 廃止の択一は本 wave で決める、と元パッケージが明記)
- [T-068]/[T-077]/[T-078] は本設計の確定後に再評価 — 本 wave では閉じない

## 前提の実測 (2026-07-22 再実測。read-only 設計 wave のためコード編集を伴う模擬は無し = 模擬と実差分の乖離なし)
- 6/6 世代の `frozen_at_head` が dangling (`git cat-file -t` 不成立、`fsck --unreachable --dangling` にも無い)。freeze commit `e5dfa84` の実親 `9c10b5f` ≠ 記録値 `2066ce6b` という rebase 由来の直接証拠あり
- 3 成果物とも generator 自己 bytes pin 現存 (`known_axes_freeze.json` の `/generator/sha256` = `s1_known_axes_freeze.py` 全 bytes、等)。verify 順は自己 hash → source → ancestry → 機械再構成
- holdout は `design_source`/`generator` の 2 drift (D73 (1)) が現存し、ancestry 以前に落ちる。`FROZEN_MANIFEST` の 3 pin は現在すべて一致
- `V1_FREEZE_SHA256` = holdout bytes (S-1 ではない、D72 (7))。`_TRANSITION_V1_TO_G1` は 12 pointer で `/known_axes_freeze/sha256` を含まない (D71 (2)(c))

## 不変条件
- 規律 2: 新形式は正しさゲートを正味で弱めない。`FROZEN_MANIFEST` の第三の独立値 (literal bytes pin) は維持する (D71 (5))
- 既存 canonical bytes は本 wave では不変。移行は将来の user-ratified 実装 wave でのみ行う
- 移行計画は D71 (2) の 3 方向閉塞、D71 (3) の holdout 人間確認者必須、D72 (6) の「S-1 semantic 4 pointer ≠ repository transition 面」の区別、D73 (2)(3) の ancestry マスク / 判別粗さ (git 障害・非 commit object の巻き込み) をすべて明示的に解決すること

## 親の provisional 裁定 (攻撃対象 — 一件ずつ採用/否認を返せ)
- (P1) gate は「入力 pin + 機械再構成 (挙動契約)」とし、「現行 worktree のコード bytes == 記録 hash」検査 (`/generator/sha256`、`/implementation_hashes/*`) を全廃する。コード hash の記録自体は残してよいが未検証 provenance metadata へ降格し、フィールドを gate 対象と構造的に分離する
- (P2) `frozen_at_head` は新形式で field 廃止。source closure の同一性は 63 source record + `ccbench_pin` が既に担う (D71 (6))。生成時ガード案 (main land 後に生成等) より廃止を優先する
- (P3) 移行は「新形式 freeze を新 schema として再発行 + 一回限りの transition receipt + `FROZEN_MANIFEST` 再 pin」(D71 (5) の形)。既存 6 freeze (git 履歴中の歴代含む) は書き換えず歴史成果物として据え置く
- (P4) holdout の新形式再発行は `confirmed_by` (人間確認者) 必須のため AI 単独工程にせず、ユーザー同席手順として移行計画に明記する
- (P5) `_TRANSITION_V1_TO_G1` / `_TRANSITION_GN_TO_GN1` は拡張せず旧 schema 用として凍結保持し、新形式には新しい transition 契約を別途定義する
- (P6) pin 波及面は Explore 地図の列挙 — `FROZEN_MANIFEST` / `V1_FREEZE_SHA256` + `EQUALITY_CHAIN_ADJACENCY` / 許可表 / `s8b_oracle_driver.py` / `s8b_oracle_manifest.py` / `s1_report.py` / `s1_direct_comparison.py` / `s1_verify_extime_calibration.py` / freeze 間 chain 2 本 (measurement→known、holdout→known) — を正とする。不足があれば具体的に指摘せよ

## 並列分割
- 段 2: codex 起草 1 本 (read-only / max)。段 3: 敵対相談 2 本並列 (正しさ境界レンズ / 整合・実効性レンズ)。**本 brief 自身も攻撃対象**
- 段 5/6: 実装差分なし。最終 doc は親が書く (= 親筆ハンクは doc 全体) ため、敵対レビュー 2 本を最終 doc へ当ててから commit する。変異 matrix・受入全走は対象外 (実装差分なし)、`check_docs.py` は通す

---
## 段 2: codex 設計草案 (gpt-5.6-sol / max / read-only)

# [T-080] freeze 族の恒久設計案

> 配置先案: `docs/freeze-permanent-design.md`  
> 状態: ユーザー裁定前の設計草案。コード、既存 freeze、テスト、worklog、decisions は変更していない。  
> 根拠: `docs/decisions.md:2714-2930`、`docs/worklog.md:688-730`。  
> 静的調査のみを実施し、pytest は実行していない。

本案の中心は次の三点である。

1. checker や解析実装の bytes は凍結 gate にしない。入力 pin、機械再構成された意味出力、外部 raw-bytes trust root を gate にする。
2. 新形式から `frozen_at_head` を削除する。不存在 SHA を「参考情報」として受理するのではなく、そもそも主張しない。
3. 旧 schema／`V1_FREEZE_SHA256`／旧 transition 表は歴史レーンとして不変保持し、新 schema は版付き・世代付きの別 path と別 transition 契約で開始する。

---

## 1. 新形式スキーマ

### 1.1 共通原則

field は次の二群へ構造的に分ける。

| 区分 | 意味 | verifier の扱い |
|---|---|---|
| `G` | 正しさ gate | 型、値、hash、再構成、cross-field 関係を fail-closed 検査 |
| `M` | 未検証 provenance metadata | schema と型だけ検査。現行 worktree の bytes とは比較せず、意味再構成にも使わない |

canonical 成果物の raw bytes は文書内で自己 hash しない。別モジュールの production trust root と、`orchestrator/tests/test_frozen_artifacts.py:33-50` の `FROZEN_MANIFEST` の双方で固定する。

推奨する初代 path は以下とする。

- `output/s1-freeze/known_axes_freeze.v2.g1.json`
- `output/s1-freeze/measurement_freeze.v3.g1.json`
- `output/s8b-freeze/holdout_freeze.v3.g1.json`

共通 record は次の形とする。

- `ArtifactRef = {path, sha256}`
- `SourceRecord = {path, sha256, key, lines?}`
- `provenance_unverified`:

```json
{
  "status": "unverified",
  "generator": {
    "path": "<repo-relative path>",
    "sha256_at_generation": "<64hex>"
  },
  "python_version_at_generation": "<string>",
  "related_implementations": [
    {
      "role": "<string>",
      "path": "<repo-relative path>",
      "sha256_at_generation": "<64hex>"
    }
  ]
}
```

`sha256_at_generation` は履歴説明用であり、現行ファイルとの一致を要求しない。canonical raw hash は外部 trust root により固定されるため、metadata の無断改変は raw-bytes gate で検出される。

### 1.2 S-1 known-axes: `s1-known-axes-freeze/v2`

現行構築点は `orchestrator/campaign/s1_known_axes_freeze.py:608-679`、schema と検査は同 `:67-74,700-766`。

#### field 一覧

| field | 区分 | 契約 |
|---|---:|---|
| `schema_version` | G | `"s1-known-axes-freeze/v2"` exact |
| `generation_number` | G | 初代は `1`。正整数 |
| `supersedes_sha256` | G | 現行 legacy known の raw SHA-256 `354f4b87…` |
| `what` | G | 現行の意味記述を維持 |
| `ccbench_pin` | G | 40 桁 commit。実 gitlink と一致 |
| `selection_rules` | G | `p2_2/backoff_fixed/sort/system_gate/stock_common` exact |
| `entries` | G | 3 workload × 6 configuration。現行の意味出力を維持 |
| `s1b_pairing` | G | 3 workload、flags 同一・predicate 差分を再検査 |
| `reference_values_note` | G | 現行の事前登録上の意味を維持 |
| `provenance_unverified` | M | generator と Python 実行環境の発行時記録 |

`entries` の下位 schema は現行を維持する。

- workload: `balanced`、`write-heavy`、`read-heavy`
- configuration: `system_gate`、`ident_all`、`p2_2_flag_opt`、`backoff_fixed_best`、`sort_best`、`stock_common`
- 各 entry に含まれる `sources[]` は引き続き `G` とする。
- 現行の recursive source は、top-level generator を除き 63 record ある。これらと `ccbench_pin` が source closure を担う。

ここで `.py` を指す source record も、checker 自己 pin ではなく、選定値を導いた宣言済み入力 closure として維持する。全 code-byte pin を一律に外すと D71 (6) の代替が失われるため、P1 はこの点で限定修正する。

#### 現行との差分

| 現行 field | 新形式 |
|---|---|
| `frozen_at_head` | 削除 |
| `generator` | `provenance_unverified.generator` へ移動し非 gate 化 |
| `python_version` | `provenance_unverified.python_version_at_generation` へ移動 |
| schema version なし | `schema_version` を追加 |
| 世代連鎖なし | `generation_number`、`supersedes_sha256` を追加 |
| 63 source record | gate のまま維持 |
| canonical raw pin はテストのみ | production trust root と `FROZEN_MANIFEST` の二面で固定 |

checker のコメント修正などで generator bytes だけが変わっても通る。一方、63 input source、ccbench、または再構成された `entries` が変われば落ちる。

### 1.3 S-1 measurement: `s1-measurement-freeze/v3`

現行構築点は `orchestrator/campaign/s1_measurement_freeze.py:240-279`、schema と検査は同 `:282-444`。

#### field 一覧

| field | 区分 | 契約 |
|---|---:|---|
| `schema_version` | G | `"s1-measurement-freeze/v3"` exact |
| `generation_number` | G | 初代は `1` |
| `supersedes_sha256` | G | legacy measurement raw SHA-256 `203de36b…` |
| `what` | G | 計測 freeze の意味記述 |
| `ccbench_pin` | G | known と同じ commit |
| `known_axes_freeze` | G | 新 known g1 の `{path,sha256}` |
| `cells` | G | 18 cell。現行 `CELL_KEYS` を維持 |
| `comparisons` | G | S-1a 9 対 + S-1b 3 対 |
| `s1b_pairing` | G | known からの射影と一致 |
| `operating_point` | G | `RECORDS/THREADS/EXTIME/REPS` exact |
| `workload_flags` | G | 3 workload の read ratio exact |
| `master_seed` | G | `20260715` |
| `schedule` | G | floor 8、block 1/2 各 4、各周 18 cell 一回ずつ |
| `schedule_hash` | G | canonical schedule SHA-256 |
| `analysis_contract` | G | `s1_stats` の挙動契約 |
| `provenance_unverified` | M | measurement generator と `s1_stats.py` の発行時 hash |

`known_axes_freeze` は現行
`implementation_hashes.known_axes_freeze` の意味を昇格・改名したものとする。これは implementation pin ではなく、上流成果物の raw output pin である。

`cells.*.source_pointer.path` は新 known g1 path を指す。

#### `analysis_contract`

`implementation_hashes.s1_stats` の代替として、以下を外部固定の挙動契約にする。

- `contract_id = "s1-stratified-exact-permutation/v1"`
- 2 strata、各群 4
- `C(8,4)^2 = 4900`
- tie は平均順位
- statistic は 2 倍整数 rank-sum
- `greater` は `>=`、`less` は `<=`
- `p_star = p_perm if gates_passed else 1.0`
- `family_p = max`
- effect sizes は判定非使用
- conformance case ごとに次を記録:
  - target/control 入力
  - alternative
  - expected statistic
  - p 値の numerator/4900
  - distribution の canonical SHA-256
  - float 出力は `float.hex()` 表現

少なくとも strict ordering、tie、greater/less 対称、stratified と pooled が異なる例、gate fail、family max を含める。新 verifier は現行 `s1_stats` をこの固定 vector に対して実行する。実装 bytes が変わっても挙動が同じなら通り、挙動が変われば落ちる。

#### 現行との差分

| 現行 field | 新形式 |
|---|---|
| `frozen_at_head` | 削除 |
| `generator` | metadata へ移動 |
| `python_version` | metadata へ移動 |
| `implementation_hashes.s1_measurement_freeze` | metadata へ移動 |
| `implementation_hashes.s1_stats` | metadata + `analysis_contract` に置換 |
| `implementation_hashes.known_axes_freeze` | top-level `known_axes_freeze` として gate 維持 |
| schema version field なし | `"s1-measurement-freeze/v3"` |
| 世代連鎖なし | generation fields を追加 |

### 1.4 holdout: `8b-holdout-freeze/v3`

現行構築点は `orchestrator/campaign/s8b_holdout_freeze.py:507-567`、検査は同 `:683-823`。現行 v2 世代 schema は `orchestrator/campaign/s8b_ratified_freeze.py:81-128,817-978`。

#### field 一覧

| field | 区分 | 契約 |
|---|---:|---|
| `schema_version` | G | `"8b-holdout-freeze/v3"` |
| `generation_number` | G | permanent 初代は `1` |
| `supersedes_sha256` | G | legacy holdout raw SHA-256 = `V1_FREEZE_SHA256` |
| `lifecycle_stage` | G | 初代 `"pre-measurement"`、floor 充填世代 `"ratified-floor"` |
| `what` | G | holdout freeze の意味 |
| `design_source` | G | `{path,sha256}`、現行 design bytes と一致 |
| `known_axes_freeze` | G | 新 known g1 の `{path,sha256}` |
| `match_convention` | G | 現行 file-level conjunction |
| `search` | G | file enumeration、除外 path、件数 snapshot |
| `holdouts` | G | `rr80/rr20` exact |
| `positive_control` | G | expressions と正の hit |
| `derangement` | G | `rr80↔rr20` |
| `confirmed_by` | G | 空でない人間確認者 |
| `confirmed_at` | G | RFC 3339 UTC |
| `env_tag` | G | g1 では `null`、floor 世代では登録済み tag |
| `floor` | G | g1 では `null` |
| `budget` | G | g1 では `null` |
| `floor_protocol` | G | g1 では `null`、以後 `{path,sha256}` |
| `floor_source` | G | g1 では `null`、以後 `{path,sha256}` |
| `measurement_closure` | G | g1 では `[]`、以後 exact closure |
| `refreeze_note` | G | lifecycle と整合 |
| `scope_note` | G | 現行の限界記述 |
| `binding_rule_note` | G | nearest-read-ratio-v1 と人間確認要件 |
| `provenance_unverified` | M | holdout generator の発行時情報 |

下位 schema は現行を維持する。

- `search`: `excluded_paths/file_count/file_enumeration/skipped_binary_count/top_level_dirs`
- `holdouts.<id>`: `candidate_id/ycsb/records/threads/unknownness_check/variant_binding`
- `unknownness_check`: `search_scope/expressions/per_axis_counts/conjunction_hits/zero_hit_output_sha256/positive_control/confirmed_by`
- `variant_binding`: `rule/anchor_workload/distances/entries/stripped_keys`

`lifecycle_stage == "pre-measurement"` では live search の conjunction 0 と positive control > 0 を必須にする。`ratified-floor` では、記録 snapshot、measurement closure、launch 時の検索運用性を現行 ratified-v2 相当の別層で検査する。`floor/budget` の null/non-null による schema 推測は廃止する。

#### 現行との差分

| 現行 field | 新形式 |
|---|---|
| `schema_version = 8b-holdout-freeze/v1` | `.../v3` |
| `frozen_at_head` | 削除 |
| `generator` | metadata へ移動 |
| `design_source` | gate 維持。現行 drift は人間同席で再確認 |
| `known_axes_freeze` | 新 known g1 path/hash へ更新 |
| `confirmed_by/confirmed_at` | gate 維持し、receipt で exact successor hash に束縛 |
| v2 generation header | 新 v3 generation 契約として明示 |
| lifecycle が floor/null から暗黙推論 | `lifecycle_stage` で明示 |

### 1.5 schema version 規則

- schema の意味を変更したら major path/version を再利用しない。
- 同じ schema 内の再発行は `gN+1` とし、既存 path を上書きしない。
- known の現行 unversioned schema は legacy v1 相当、新形式は v2。
- measurement は文書の `what` が既に “v2” を名乗るため、新 field の正式版は v3。
- holdout は legacy v1、既存 ratified-v2 と衝突しない v3。
- unknown schema は拒否し、field shape や `floor is None` から推測しない。
- legacy は exact raw-hash loader だけで扱い、新 verifier へ黙って変換しない。

---

## 2. `verify()` 契約

### 2.1 共通 API

公開 consumer は `verify_document()` を直接呼ばず、raw bytes を一度だけ読む public loader を使う。

返却型は概念上次を持つ。

- deep-immutable document
- raw SHA-256
- schema version / generation
- `VerificationReport`

失敗時は `FreezeVerificationError(report)` を送出する。文字列一致でエラーを分類してはならない。

canonical path の `verify()` は production trust root の expected raw SHA-256 を必須にする。任意の test/candidate path は明示された expected hash または `candidate_mode` でのみ検証でき、official consumer が未登録 path を受理する経路は持たない。

### 2.2 検査順序

1. raw bytes を一回だけ読む。
2. path に対応する外部 output root と raw hash を照合する。
   - 不一致でも parse 可能なら後段を継続し、複数原因を収集する。
3. UTF-8、duplicate key、NaN/Infinity を拒否する strict JSON parse。
4. `schema_version` dispatch、exact top-level keys、型検査。
5. 独立な input pin をすべて検査する。
6. 独立な局所 invariant、schedule hash、pairing、positive control、analysis conformance を検査する。
7. 上流依存が成立した項目について機械再構成を行う。
8. generation chain、transition receipt、active root を検査する。
9. error または必須 check の `not_evaluated` が一つでもあれば失敗する。

parse/schema が壊れて安全に走査できない場合だけ後段を `not_evaluated` にする。その場合も `blocked_by` を必ず記録し、「最初の例外しか見えない」状態を作らない。

### 2.3 family 別検査

#### known

- raw output root
- exact schema
- 63 source record を一件ずつ検査し、全 mismatch を列挙
- ccbench gitlink
- S-1b flags/predicate contract
- 現行抽出ロジックによる gate field の完全再構成
- `generation_number/supersedes_sha256` と receipt
- `provenance_unverified` は shape のみ

#### measurement

known の失敗があっても、schedule、schema、analysis conformance は独立に実行する。

- raw output root
- `known_axes_freeze` raw hash
- known の full verification
- schedule hash、round/cell balance
- comparison 12 対
- S-1b pairing
- `analysis_contract` conformance
- known からの `cells` 射影
- 全 gate field の再構成

#### holdout

`design_source` drift があっても known、search、authorization の独立検査を続ける。

- raw output root
- `design_source` と `known_axes_freeze` を独立検査
- `confirmed_by/confirmed_at`
- search 実行可能性
- snapshot zero-hit hash
- conjunction / positive control
- derangement と定数
- known からの variant binding
- lifecycle に応じた floor/budget/closure
- generation/approval/active chain

generator の現行 bytes 比較も ancestry も存在しないため、D73 (2) の「ancestry が恒久的に後段を隠す」経路自体が消える。

### 2.4 エラー分類

最低限、以下の stable reason code を設ける。

| code 群 | 例 |
|---|---|
| `document.*` | `read_failed`, `invalid_utf8`, `duplicate_key`, `invalid_number` |
| `schema.*` | `unknown_version`, `key_set`, `wrong_type`, `invalid_value` |
| `output.*` | `unregistered_path`, `raw_hash_mismatch` |
| `input.*` | `missing`, `unreadable`, `hash_mismatch`, `upstream_hash_mismatch`, `ccbench_mismatch` |
| `contract.*` | `pairing`, `schedule_hash`, `reconstruction`, `analysis_conformance`, `search_not_operational`, `holdout_became_known` |
| `authorization.*` | `missing_human`, `invalid_time`, `receipt_hash_mismatch` |
| `lineage.*` | `supersedes_mismatch`, `generation_gap`, `transition_forbidden`, `not_active` |
| `environment.git.*` | `unavailable`, `command_failed`, `object_missing`, `wrong_object_type` |
| `dependency.*` | `not_evaluated` + `blocked_by` |

`frozen_at_head` が無いため、新形式では「不存在 commit」「非 ancestor」「wrong object type」を ancestry 判定する必要はない。ただし ccbench、repository enumeration、legacy receipt 監査には Git が残る。Git 実行障害を input mismatch や ancestry mismatch へ書き換えてはならない。

legacy receipt の head 監査では以下を分離する。

- object が存在しない
- object は存在するが commit でない
- commit だが想定関係でない
- Git 自体の障害

### 2.5 mask 防止の構造

各 check に stable ID と依存辺を持たせる。

例:

```text
known.raw-root
├── known.schema
├── known.sources[*]
├── known.ccbench
├── known.pairing
└── known.reconstruct
    └── depends on sources + ccbench

holdout.schema
├── holdout.design-source
├── holdout.known-ref
├── holdout.authorization
├── holdout.search
├── holdout.snapshot
└── holdout.binding
    └── depends on known-ref
```

consumer は aggregate report 全体を refusal へ変換する。特定の例外文字列だけを握り潰す方式は禁止する。

---

## 3. 生成手順

### 3.1 canonical 生成順

初代 permanent bundle は依存 DAG 順に生成する。

1. schema/checker 実装を先に commit し、最終 integration base へ rebase する。
2. worktree が clean、submodule が期待 commit、canonical destination が不存在であることを確認する。
3. known g1 candidate を生成し、semantic verifier を通す。
4. known g1 raw hash を入力として measurement g1 を生成する。
5. ユーザー同席で holdout の repository search を再実行する。
6. ユーザーが `confirmed_by`、`confirmed_at` と生成対象 scope を与える。
7. holdout g1 を生成し、new known raw hash と current design source を検査する。
8. 一回限り transition receipt を生成する。
9. production root literal と `FROZEN_MANIFEST` に、新 3 artifact + receipt を独立に pin する。
10. canonical loader、receipt verifier、全 consumer を検証する。
11. artifact 3 本、receipt、literal roots は一つの user-ratified migration commit に含める。

known、measurement、holdout を別 commit で個別に発効させてはならない。途中状態では旧 legacy path を active のまま維持し、新 path は dormant とする。

### 3.2 wave branch の扱い

- candidate 生成は wave branch 上で許可する。
- canonical path への publish と人間 ratification は、最後の予定された rebase 後に行う。
- branch 名や `origin/main` を安全性根拠にしない。D71 (4) のとおり remote-tracking ref は publication の証明ではない。
- 例外的に後から rebase されても、新 artifact は commit SHA を持たないため、それだけでは壊れない。
- rebase が source bytes を変えた場合は post-rebase verification が赤になる。既存 canonical pathを上書きせず、新 candidate を作り直す。

したがって dangling 根絶の主防壁は「main 上で生成した」という運用主張ではなく、`frozen_at_head` の schema からの廃止である。

### 3.3 existing-file 二層防御

現行の `exists()` と exclusive create は維持する。

- known: `s1_known_axes_freeze.py:769-781`
- measurement: `s1_measurement_freeze.py:447-469`
- holdout: `s8b_holdout_freeze.py:570-599`

ただし新手順では「人間が canonical を削除して再生成」を廃止する。land 済み世代は削除せず、`gN+1` を新規作成する。

staging candidate は canonical directory 内の一時ファイルへ fsync 後、exclusive link/create で publish する。既存 canonical destination の上書き、truncate、atomic replace は禁止する。

### 3.4 機械ガード

必須:

- destination 不存在
- worktree clean
- source enumeration の生成前後一致
- known→measurement→holdout の raw hash chain
- forbidden field `frozen_at_head` 不在
- gate 部分に `/generator/sha256` と `/implementation_hashes/*` が無い
- metadata が再構成入力に使われていないこと
- canonical path は production root に登録済みでない限り consumer が拒否
- migration receipt と `FROZEN_MANIFEST` の双方が successor hash を固定
- rebase/merge 後 CI で再実行

hook は補助として同じ check script を呼んでよいが、hook 配線だけを保証にしない。

---

## 4. 移行計画

### 4.1 legacy inventory の訂正

D71 の「S-1 歴代 5 世代 + holdout 1」は、known-axes の 5 版だけを数える場合には一致する。しかし artifact history には standalone measurement 初版がある。

`4b9d86e…:output/s1-freeze/measurement_freeze.json:3` は `frozen_at_head=02c840c…` を持ち、この object も不存在である。

したがって receipt は最低でも 9 raw blob、7 distinct dangling anchor を inventory する。

| family | introduction commit | raw SHA-256 | recorded head |
|---|---|---|---|
| known | `80b30107…` | `1622ecadde1cf8fd432c804d198ded8f0b3ce89b19d02503c6b77fee86952cdd` | `c648bbe2…` |
| known | `15fcc08f…` | `e1b0a5348034b5bf6e938ff498802ccc2d43cd2b646ed745c5f3d803ca05fd8e` | `ca921338…` |
| known | `8f7fca22…` | `7a7458df4ee4350ff500f7b47662fe74ae8e3d0936430c1dda8c3a8fcb012f3e` | `c890e958…` |
| known | `b4e5cb62…` | `3eb808b4b751d5dc57e57e214fc6d7fea9a9c702a0208b5f0e87f094ae65bce1` | `0f304270…` |
| known | `e5dfa84c…` | `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516` | `2066ce6b…` |
| measurement | `4b9d86e3…` | `09dd1585ca28aebfbae0e724e4bacb299452dbad1b21eb67e893795d999756f6` | `02c840c4…` |
| measurement | `b4e5cb62…` | `5c719c076e17f385a781933c081bf02abcd85b9edb01ad8c50a37740c134a191` | `0f304270…` |
| measurement | `e5dfa84c…` | `203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a` | `2066ce6b…` |
| holdout | `911f6bc0…` | `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688` | `2e20d441…` |

旧 commit、旧 blob、旧 canonical bytes は書き換えない。receipt には full commit、parent、path、blob OID、raw SHA-256、recorded head、defect classification を記録する。

### 4.2 段階移行

#### Step 1: legacy lane の固定

- 現行 3 path と `FROZEN_MANIFEST` の既存値を維持する。
- `V1_FREEZE_SHA256` は変更しない。
- legacy loader は raw bytes exact pin だけを保証し、source/head が有効であるとは主張しない。
- 現行 broken verifier を official active consumer から外す。

対象:

- `orchestrator/tests/test_frozen_artifacts.py:33-50`
- `orchestrator/campaign/s8b_ratified_freeze.py:20-23,60-62,1329-1347`

#### Step 2: new schema/checker を dormant 導入

既存 holdout v1 の `TOP_LEVEL_KEYS` を `s8b_ratified_freeze.py:46,91` が import しているため、legacy module の schema 定数を新形式へ上書きしない。新 module を作る。

新規案:

- `orchestrator/campaign/s1_known_axes_freeze_v2.py`
- `orchestrator/campaign/s1_measurement_freeze_v3.py`
- `orchestrator/campaign/s8b_holdout_freeze_v3.py`
- `orchestrator/campaign/freeze_permanent_io.py`

既存抽出ロジックの参照点:

- known: `s1_known_axes_freeze.py:608-679`
- measurement: `s1_measurement_freeze.py:156-279`
- holdout search/binding: `s8b_holdout_freeze.py:472-567`

#### Step 3: known g1 発行

- legacy latest semantic fieldsを再構成する。
- `frozen_at_head` を削除。
- generator/python を metadata へ移す。
- 63 sources と ccbench pin は保持。
- `supersedes_sha256=354f4b87…`。
- old/new gate projection が一致することを receipt verifier で確認。

#### Step 4: measurement g1 発行

- known g1 を full verify。
- `known_axes_freeze` に known g1 raw hash を固定。
- current schedule/cells/comparisons を再構成。
- `analysis_contract` を追加。
- `supersedes_sha256=203de36b…`。
- D72 (6) の旧 4 pointer は「旧 JSON を同 schema 内で修正する場合」のみの一覧であり、この schema migration の repository allowlist には使わない。

#### Step 5: holdout g1 発行

AI 単独実行は禁止する。

- current design source を再 pin。
- new known g1 を pin。
- repository search を再実行。
- ユーザーが確認者名、確認時刻、対象 successor hash を承認。
- `confirmed_by` は nested `unknownness_check.confirmed_by` と一致。
- `floor/budget/floor_protocol/floor_source` は null、closure は空。
- `lifecycle_stage=pre-measurement`。
- `supersedes_sha256=V1_FREEZE_SHA256`。

これにより T-077 の design drift は再確認された入力へ更新され、generator drift は非 gate metadata へ再定義される。

#### Step 6: one-time transition receipt

配置案:

`output/freeze-migrations/legacy-to-permanent-g1.receipt.json`

exact schema:

```json
{
  "schema_version": "freeze-family-transition-receipt/v1",
  "transition_id": "legacy-to-permanent-g1",
  "legacy_inventory": [
    {
      "family": "s1-known-axes",
      "introduction_commit": "<40hex>",
      "introduction_parent": "<40hex>",
      "path": "<repo-relative>",
      "git_blob_oid": "<40hex>",
      "raw_sha256": "<64hex>",
      "recorded_frozen_at_head": "<40hex>",
      "anchor_status": "missing",
      "disposition": "legacy-history-only"
    }
  ],
  "successors": [
    {
      "family": "s1-known-axes",
      "path": "output/s1-freeze/known_axes_freeze.v2.g1.json",
      "schema_version": "s1-known-axes-freeze/v2",
      "generation_number": 1,
      "raw_sha256": "<64hex>",
      "supersedes_sha256": "354f4b87..."
    }
  ],
  "relations": [
    {
      "family": "s1-known-axes",
      "projection_contract": "known-legacy-to-v2/v1",
      "preserved_sections": [
        "/what",
        "/ccbench_pin",
        "/selection_rules",
        "/entries",
        "/s1b_pairing",
        "/reference_values_note"
      ],
      "removed_claims": ["/frozen_at_head"],
      "metadata_only": ["/provenance_unverified"]
    }
  ],
  "human_ratification": {
    "required": true,
    "scope": "holdout g1 + three-artifact migration bundle",
    "confirmed_by": "<user supplied>",
    "confirmed_at": "<RFC3339 UTC>",
    "holdout_successor_sha256": "<64hex>"
  }
}
```

receipt に `verified: true` のような自己申告は置かない。verifier が旧 blob、新 artifact、projection、human target hash を再計算する。

#### Step 7: raw roots と `FROZEN_MANIFEST`

`FROZEN_MANIFEST` の旧 8 entry は維持し、次の 4 entry を追加する。

- known g1
- measurement g1
- holdout g1
- transition receipt

shape count は 8 から 12 へ更新する。旧 3 canonical entry を新 hash で置換してはならない。

production 用には別の literal root registry を設け、テストで production root と `FROZEN_MANIFEST` が一致することを確認する。同じ dict を import して単一源化すると第三の独立値が失われるため、値は意図的に独立保持する。

#### Step 8: trust root と transition

`V1_FREEZE_SHA256` は legacy holdout の名前であり、意味を新 holdout hash へ差し替えない。

現行以下は旧 schema 用として保持する。

- `s8b_ratified_freeze.py:61-62` `V1_FREEZE_*`
- 同 `:115-120` `_TRANSITION_V1_TO_G1`
- 同 `:125-128` `_TRANSITION_GN_TO_GN1`
- 同 `:133-155` `EQUALITY_CHAIN_ADJACENCY`

新規 `s8b_permanent_ratified_freeze.py` に別契約を置く。

legacy→permanent g1 は一般 transition allowlist ではなく one-time receipt だけで許可する。

permanent gN→gN+1 は gate projection に対して次だけを許可する。

- `/generation_number`
- `/supersedes_sha256`
- `/lifecycle_stage`
- `/env_tag`。`null→登録済み値` の初回だけ
- `/floor`
- `/budget`
- `/floor_protocol`
- `/floor_source`
- `/measurement_closure`
- `/refreeze_note`

`provenance_unverified` は transition 比較の前に projection から除く。`known_axes_freeze`、`design_source`、holdout 条件、variant binding の変更は同じ lineage では許可せず、新 genesis + 人間 ratification を要求する。

新 equality chain は genesis constant ではなく、実際に active となった generation raw hash を official artifact へ流す。

```text
active_generation.sha256
→ result.freeze_sha256
→ journal.campaign-start.freeze_sha256
→ cert.freeze_sha256
→ protocol.freeze.sha256
→ manifest.freeze_sha256
→ manifest.freeze.sha256
```

旧 `cert.v1_freeze_sha256` を汎用名へ読み替えず、新 launch-certificate schema を作る。

### 4.3 consumer 追随面

| 面 | 現行箇所 | 移行 |
|---|---|---|
| S-1 known→measurement | `s1_measurement_freeze.py:252-258,400-408` | new known raw ref + full v2 verify |
| known→holdout | `s8b_holdout_freeze.py:524-554,709-710,749-813` | new known g1 へ変更 |
| S-1 runner | `s1_direct_comparison.py:43,115-127,589-606` | raw-root 付き measurement v3 loader |
| S-1 report | `s1_report.py:750-770,824-846` | measurement v3 verified object を共有 |
| calibration | `s1_verify_extime_calibration.py:193-229,392-405` | `freeze_frozen_at_head` を削除し `{path,sha256,schema_version,generation_number}` を記録 |
| oracle driver | `s8b_oracle_driver.py:216-266` | null 値で schema 推測せず v3 loader を使用。known の再読込を verified object に統合 |
| oracle manifest | `s8b_oracle_manifest.py:617-685,733-809` | v3 freeze/known refs、active generation raw hash |
| raw loader | `s8b_freeze_io.py:30-68` | schema-specific semantic verification済み型との境界を明示 |
| v1 trust/transition | `s8b_ratified_freeze.py:60-155,901-1008,1286-1347,2600-2721` | legacy 不変、新契約を別 module に置く |
| approved roots | `s8b_approved.py:29,44-47` | legacy 値は維持し permanent approved module を追加 |
| floor protocol schema | `s8b_floor_contract.py:24-27,158-165` | v3 protocol schemaを別版で追加 |
| floor builder/run | `s8b_floor_campaign.py:330-389,1248-1324,2331-2467,2964-2988` | permanent root、汎用 cert、active hash |
| launch cert | `s8b_launch_cert.py:14-23,50-103` | legacy v1 維持、新 v2 cert は `freeze_sha256` |
| selector | `s8b_selector_freeze.py:38-55,308-347,592-608,735-756` | V1-only loader の扱いを明示。permanent selector は別 schema |
| prediction runner | `s8b_prediction_runner.py:330-376,537-559` | permanent verified holdout object |
| verdict | `s8b_verdict.py:791-850` | permanent floor generation と prediction basis を一致 |
| frozen literal | `test_frozen_artifacts.py:33-81` | old 8 維持 + new 4 |
| oracle tests | `test_s8b_oracle_driver.py:530-543,1208-1226` | typed exact findings、新 baseline |
| holdout tests | `test_s8b_holdout_freeze.py:147-401` | no-head schema、aggregate verification |
| S-1 tests | `test_s1_known_axes_freeze.py:43-99`、`test_s1_measurement_freeze.py:166-252` | behavior-preserving checker edit、stats conformance、root tamper |

P6 の列挙には少なくとも以下が不足していた。

- `s8b_approved.py`
- `s8b_floor_contract.py`
- `s8b_floor_campaign.py`
- `s8b_launch_cert.py`
- `s8b_selector_freeze.py`
- `s8b_prediction_runner.py`
- `s8b_verdict.py`
- `s8b_freeze_io.py`
- それぞれの direct tests
- standalone measurement 初版の historical blob
- `s8b_selector_freeze.py:565-566,621-623` の `pre_oracle_head` という隣接 dangling 候補

### 4.4 T-068 / T-077 / T-078

- **T-068:** 新 active consumer が ancestry を持たない新 schema へ移った後は、consumer 側で ancestry 文字列を握り潰す方式 B は不要になる見込み。ただし設計 wave では閉じない。移行完了後に「恒久設計により superseded」としてユーザー再裁定する。
- **T-077:** design drift は user-attended g1 で再 pin。generator drift は非 gate metadata へ再定義。新 holdout g1 が ratify されるまで閉じない。
- **T-078:** 新 baseline が pass する hermetic fixture から、単一 field だけを変える positive control に作り直す。baseline pass、mutant exact reason で fail、revert pass の三点を要求する。先行 drift に食われないことを aggregate findings で確認してから閉じる。

---

## 5. 設計択一

### A. `frozen_at_head`

- 選択肢:
  1. field 廃止
  2. tree hash や published ref へ置換
  3. 生成時ガードだけ追加
- 推奨: **1**
- 根拠: source identity は input records、ccbench、upstream raw hash が担う。Git commit は内容保証を追加せず、rebase と publication の意味を混同する。

### B. canonical path

- 選択肢:
  1. 旧 path を上書き
  2. schema + generation 付き別 pathで side-by-side
- 推奨: **2**
- 根拠: legacy bytes、V1 root、旧 transition を壊さず、途中 commit も green に保てる。

### C. code provenance metadata

- 選択肢:
  1. 完全削除
  2. `provenance_unverified` として保持
- 推奨: **2**
- 根拠:発行時実装の監査価値は残る。ただし gate や再構成入力に使わないことを field 名で明示する。

### D. `s1_stats.py` の代替 gate

- 選択肢:
  1. hash を単に外す
  2. external conformance vectors による挙動契約
  3. 別の code hash registry へ移す
- 推奨: **2**
- 根拠: 1 は正味の弱化、3 は自己 pin 問題の移動にすぎない。

### E. 人間確認の束縛

- 選択肢:
  1. 空でない `confirmed_by` 文字列だけ
  2. receipt が exact holdout successor hash と確認者・時刻・scope を束縛
  3. Git署名必須
- 推奨: **2**
- 根拠: 現行より強く、署名基盤の新設までは要求しない。AI は確認者名を発明してはならない。

### F. old ratified-v2 transition

- 選択肢:
  1. `_TRANSITION_V1_TO_G1` を拡張
  2. 旧表を維持し、new v3 transition を別定義
- 推奨: **2**
- 根拠: 旧世代の意味を遡及変更せず、D71 の三方向閉塞を one-time receipt で越えられる。

### G. 63 source record 中の code bytes

- 選択肢:
  1. 全削除
  2. T-080 では input closure として維持
  3. 各 source を semantic projection pin へ全面変換
- 推奨: **2**
- 根拠: 1 は D71 (6) の代替を失う。3 は有望だが別の大規模 schema 設計であり、今回同時に行うと gate の帰属が曖昧になる。

### H. historical inventory の母集団

- 選択肢:
  1. brief の 6 anchor だけ
  2. 実在する 9 blob／7 anchor 全件
- 推奨: **2**
- 根拠: standalone measurement 初版を落とすと「全 legacy freeze」の receipt にならない。

### worklog 裁定パッケージ転記案

```markdown
### [T-080] freeze 族恒久設計の裁定パッケージ

確定済み方向は「入力・出力を pin し checker は pin しない」「rebase で dangling を生まない」
の二点。設計案は、新 schema から frozen_at_head を削除し、旧 schema/V1 root/旧 transition を
歴史レーンとして保持、版・世代付き別 path + one-time receipt + FROZEN_MANIFEST 追加 pin で
permanent g1 を発行する。

裁定要:
1. side-by-side versioned path を採るか
2. code hash を provenance_unverified として残すか
3. s1_stats を外部 conformance vectors へ置換するか
4. holdout 人間確認を exact successor hash に receipt で束縛するか
5. old transition を不変保持し new v3 transition を別定義するか
6. receipt inventory を known 5 + measurement 3 + holdout 1 の 9 blob へ拡張するか

T-068/T-077/T-078 は本設計の実装・ratification 後まで閉じない。
```

---

## 6. 実装 wave 分割案

各 file は一つの wave だけが所有する。integration で不具合が見つかった場合は、その file の所有 wave に戻す。

| wave | 目的 | 排他的所有 file |
|---|---|---|
| W1 | common raw loader + known v2 | 新 `freeze_permanent_io.py`、新 `s1_known_axes_freeze_v2.py`、新 `test_s1_known_axes_freeze_v2.py` |
| W2 | measurement v3 + stats contract | 新 `s1_measurement_freeze_v3.py`、新 `test_s1_measurement_freeze_v3.py`、`test_s1_stats.py` |
| W3 | holdout v3 | 新 `s8b_holdout_freeze_v3.py`、新 `test_s8b_holdout_freeze_v3.py` |
| W4 | 人間同席 migration bundle | 新 artifact 3 本、receipt、root registry、`test_frozen_artifacts.py`、新 receipt test |
| W5 | S-1 consumer activation | `s1_direct_comparison.py`、`s1_report.py`、`s1_verify_extime_calibration.py` と各 test |
| W6 | permanent ratification/equality | 新 `s8b_permanent_ratified_freeze.py`、新 approved root module、新 launch-cert schema と各 test |
| W7 | oracle consumer | `s8b_oracle_driver.py`、`s8b_oracle_manifest.py`、対応 test |
| W8 | floor/selector/verdict consumer | `s8b_floor_contract.py`、`s8b_floor_campaign.py`、`s8b_selector_freeze.py`、`s8b_prediction_runner.py`、`s8b_verdict.py` と各 test |
| W9 | integration records | `conftest.py`、`test_real_repo_serialization.py`、phase doc、worklog、decisions、設計 doc |

merge 順は W1→W2→W3→W4→W5/W6→W7/W8→W9。W4 までは新 artifacts を dormant とし、legacy consumer を維持する。W7/W8 の activation が完了する前に legacy default を削除しない。

---

## 7. brief P1..P6 への逐条応答

### P1 — 修正採用

`/generator/sha256` と `/implementation_hashes.s1_measurement_freeze` は gate から全廃する。`s1_stats` は metadata + behavior conformance へ置換する。

ただし「現行 worktree の code bytes 検査をすべて全廃」を、known 内の63 source record にまで広げることは否認する。これらは D71 (6) が source closure と認定した入力 pin であり、今回一括削除すると規律 2 に反する。

`implementation_hashes.known_axes_freeze` は code pin ではなく upstream output pin なので、top-level `known_axes_freeze` へ移して維持する。

### P2 — 採用

新形式から `frozen_at_head` を削除する。未検証 metadata としても残さない。

生成時ガードだけでは rebase、publication、origin/main の意味問題を解決できない。field 廃止により、D73 (3) の ancestry error classification 問題は新形式から消える。ただし Git を使う別検査には typed classification を残す。

### P3 — 修正採用

「新 schema 再発行 + one-time receipt + `FROZEN_MANIFEST` 再 pin」を採る。

修正点は、旧 path の bytes を置換せず、versioned generation path を追加すること、および receipt inventory を brief の 6 件ではなく実在する 9 blob へ広げることである。

### P4 — 採用・強化

holdout g1 は AI 単独工程にしない。`confirmed_by` の入力だけでなく、receipt に exact successor raw hash、時刻、scope を記録し、ユーザーがその hash を承認する。

### P5 — 採用

旧 transition 表と旧 equality adjacency は拡張しない。legacy→permanent は one-time receipt、新世代は別 module／別 schema／別 equality chain とする。

特に official result が結ぶべき値は `V1_FREEZE_SHA256` ではなく、その run が実際に使用する active permanent generation の raw SHA-256 である。

### P6 — 修正

列挙された面は必要だが十分ではない。追加必須面は以下。

- `s8b_approved.py`
- `s8b_floor_contract.py`
- `s8b_floor_campaign.py`
- `s8b_launch_cert.py`
- `s8b_selector_freeze.py`
- `s8b_prediction_runner.py`
- `s8b_verdict.py`
- `s8b_freeze_io.py`
- 対応する protocol/cert/floor/selector/verdict tests
- standalone measurement 初版
- calibration 派生出力
- selector prediction の `pre_oracle_head`

### decisions 記録案

ユーザーが A〜H を裁定した後にのみ、次の趣旨を `docs/decisions.md` へ記録する。

```markdown
## DXX. freeze 族は input/output pin + checker 非 pin の permanent schema へ移行する

決定:
1. new schema から frozen_at_head を削除する
2. checker/analysis implementation bytes は gate にせず、挙動再構成・conformance で代替する
3. 63 source record、ccbench、upstream raw artifact refs、human confirmation は gate を維持する
4. legacy bytes、V1_FREEZE_SHA256、旧 transition/equality は不変保持する
5. versioned g1 artifacts + one-time receipt + independent literal roots を追加する
6. official equality chain は active generation raw hash を結ぶ
7. T-068/T-077/T-078 は migration 完了後に再裁定する

補足:
D71 の「S-1 5 + holdout 1」は known issuance の数であり、artifact history には standalone
measurement 初版が別にある。migration receipt は known 5 + measurement 3 + holdout 1 を列挙する。
```

---

## 8. リスクと未解決点

1. **history 数の前提差。** brief の 6 件と、静的履歴監査の 9 blob／7 anchor が一致しない。receipt schema 確定前に親が独立再確認する必要がある。

2. **`analysis_contract` の exact vector は未作成。** `s1_stats` hash を外す commit と conformance gate を導入する commit は同一でなければならない。vector が不足した状態で先に hash を外してはならない。

3. **人間確認は暗号署名ではない。** receipt の exact hash 束縛は現行の自由文字列より強いが、確認者認証そのものは repository review/process に依存する。

4. **63 source record の raw-byte brittleness は残る。** 今回は規律 2 のため維持する。将来 semantic projection 化するなら、別 decision と mutation matrix が必要。

5. **new checker 自体は current TCB になる。** checker 非 pin は、悪意ある checker を artifact が防ぐ設計ではない。独立 expected values、mutation tests、raw output roots、review separation が必要である。

6. **`FROZEN_MANIFEST` は同じ commit で更新可能。** 「第三の独立値」は cryptographic third party ではなく、別 literal・別 review surface という意味に留まる。改竄不能とは主張しない。

7. **holdout g1 はまだ oracle 実走可能でない。** `floor/budget` が null のため、T-068 の ancestry refusal は消えても floor/budget refusal は残る。g1 は floor 再測定の trust rootであり、ratified-floor 世代は後続である。

8. **legacy verifier は壊れたまま残る。** 旧 artifact は historical exact bytes としてのみ受理し、source/head が現時点で有効とは主張しない。legacy path を official active consumer が呼ばないことを機械検査する必要がある。

9. **selector prediction に類似問題がある。** `s8b_selector_freeze.py:565-566,621-623` の `pre_oracle_head` は実在 commit を要求するため、wave branch 生成後の rebase で同型に壊れ得る。permanent selector activation 前に、内容 pin へ移行するか別 task として明示する必要がある。

10. **派生成果物。** 既存 `output/env/linux-baremetal/calibration/s1_verify_extime.json:19` は legacy `freeze_frozen_at_head` を持つ。既存 bytes は歴史物として残し、新 calibration schema では raw freeze identity に置換する。

11. **中間状態の安全性。** 新 artifacts を追加してから consumer を切り替えるまで、旧 lane を active に保つ必要がある。schema の部分切替や、known だけ新・holdout は旧という混在状態を official path で受理してはならない。

12. **検証未実施。** 本草案は read-only 静的監査に基づく。pytest、mutation、`check_docs.py` の green は主張しない。
---
## 段 3a: 敵対相談 A (正しさ境界レンズ) — NO-GO、14 所見

総合結論は **NO-GO**。checker 非 pin 化の方向自体ではなく、その代替 gate・承認分離・世代発効契約が未成立であり、規律2を満たしたとは判定できない。

## 1. 所見

### A-1 — BLOCKER: checker 非 pin 化で受理集合が実際に広がる

**攻撃シナリオ:** 新 known verifier の source mismatch 登録だけを削り、63 source の一つへ意味非影響のコメント変更を加える。artifact と raw root は不変、機械再構成結果も不変なので新形式は受理する。現行では verifier の1 byte変更自体が `/generator/sha256` 不一致となり、source 検査前に拒否される。

現行 self-pin も「self-pin 検査そのものを消す完全な悪意ある checker」には勝てない。しかし、単独の壊れた checker 変更を検知していた層を外す以上、同等以上の外部防壁が必要である。草案の mutation tests／review separation／independent values は配置・所有者・必須 test node・改変時の拒否条件がなく、現状は願望でしかない。

**根拠:** `s1_known_axes_freeze.py:721-741`、`s1_measurement_freeze.py:394-405`、`s8b_holdout_freeze.py:708-712`、設計案 §3.4、§8(5)。

### A-2 — BLOCKER: 同一コードによる再構成は code＋artifact 同時変更に無力

**攻撃シナリオ:** extractor と verifier を同時に変更し、例えば WAL の一意 argmax ではなく別点を選ばせる。そのコードで known／measurement／holdout を生成し、receipt、production roots、`FROZEN_MANIFEST` も同一 migration commit で更新する。63 input hash は正しく、壊れたロジックによる再構成とも一致するため全 gate が通る。

`build_document()` の再実行は「成果物が現行コードと一致する」ことしか証明せず、「現行コードが正しい」ことを証明しない。§8(6) の自認どおり、二つの literal root も同一 commit・同一 producer が更新できる。

**根拠:** `s1_known_axes_freeze.py:759-766`、`s1_measurement_freeze.py:430-444`、`test_frozen_artifacts.py:33-50`、`docs/decisions.md:2747-2751`、設計案 §3.1 Step 8–11、§8(6)。

### A-3 — BLOCKER: one-time receipt は producer 分離を実現していない

**攻撃シナリオ:** AI が artifacts、receipt、root literals を作り、receipt に既存ユーザー名を転記して一つの commit に入れる。verifier は hash と projection を再計算できても、「その receipt を人間が作った／承認した」ことは検証できない。

現行 ratified machinery は不完全ながらも、候補導入 commit G と approval commit A を分離し、A を `AI-Agent: none`、かつ approval＋pointer の追加だけに限定し、`G != A` を要求する。草案 Step 11 はこの機械的分離を捨てる退行である。

**根拠:** `s8b_ratified_freeze.py:524-536,1160-1182`、設計案 §3.1 Step 11、§4.2 Step 6、§8(3)(6)。

### A-4 — BLOCKER: 人間 ratification は三成果物 bundle を hash 束縛していない

**攻撃シナリオ:** 人間が holdout hash `H` を承認した後、measurement g1 の `analysis_contract` を弱い内容へ変更する。measurement は holdout から参照されないため holdout hash `H` は不変である。AI は receipt の measurement hash、production root、`FROZEN_MANIFEST` を更新し、`human_ratification.holdout_successor_sha256=H` を維持できる。receipt の scope は「three-artifact migration bundle」と主張しながら、機械的には measurement を人間承認へ束縛していない。

さらに §3.1 は人間入力を Step 6、最終 holdout 生成を Step 7 としており、人間が exact successor hash を確認する順序になっていない。hash を提示されて追認するだけなら semantic review の証拠にもならない。

**根拠:** 設計案 §1.3、§1.4、§3.1 Step 5–8、§4.2 Step 6、§5-E。

### A-5 — BLOCKER: `analysis_contract` の有限 vector は全入力挙動を pin しない

**攻撃シナリオ:** `s1_stats.py` を、列挙された conformance case だけ期待値を返し、それ以外の有効な計測入力では常に `p_perm=0` を返す実装へ変更する。strict ordering、tie、対称例等の全 vector は通るが、実測値では偽陽性を生む。別例として、wrong shape、非有限値、invalid alternative、空 `family_p` の拒否を削除しても、草案に列挙された正常形 vector は通る。

現行形式は `s1_stats.py` bytes の変更だけで拒否する。従って明確に「現行では拒否、新形式では受理」である。

**根拠:** `s1_stats.py:62-82,144-181`、`s1_measurement_freeze.py:400-405`、設計案 §1.3 `analysis_contract`、§5-D、§8(2)。

必要なのは有限例だけでなく、実際の各入力を独立実装で再計算する runtime oracle、または入力領域を覆う独立仕様である。

### A-6 — BLOCKER: aggregate report は missing check を検出しない

**攻撃シナリオ:** schema dispatch のバグで `holdout.search` または `known.reconstruct` check 自体が登録されない。これは `not_evaluated` ではなく「不存在」なので、§2.2 Step 9 の「error または必須 check の not_evaluated」が発火せず、残りが pass なら受理される。

必要なのは schema ごとの exact check-ID 集合、各 ID 一回、unknown／missing／duplicate の拒否、`blocked_by` の実在・非循環性まで含む closed-world report schema である。`candidate_mode` も official 型と同じ戻り型なら、consumer の誤指定だけで unregistered path を昇格できる。

**根拠:** 現行 holdout は search を無条件実行する `s8b_holdout_freeze.py:714-715`。型分離の既存例は `s8b_ratified_freeze.py:713-759`。設計案 §2.1、§2.2、§2.5。

### A-7 — MAJOR: `frozen_at_head` 廃止の根拠となる「63 source closure」は完全閉包でない

**攻撃シナリオ:** artifact が一時的な generator dependency 状態から生成されても、新形式にはその状態と単一 repository tree を結ぶ証拠がない。`provenance_unverified` の path/hash 群から、どの commit でそれらが同時に存在したかは再構成できない。

具体的に known generator は `campaign.lock` を選別判断に読むが、それを source record に加えていない。また `pipeline.variant_id` を import・実行するが、`pipeline.py` も63 recordに含まれない。従って「63 record＋ccbench が source closure」という P2 の前提は偽である。

legacy の dangling SHA を維持すべきという意味ではない。artifact 導入 commit G から `G^`／tree OID を導出して source blob を照合する、非自己参照の代替が必要である。現行 ratified-v2 は実際にその強い関係を検査している。

**根拠:** `s1_known_axes_freeze.py:24-27,156-166,223-226,264-267`、`s8b_ratified_freeze.py:919-942`、設計案 §1.2、§5-A、brief P2。

### A-8 — BLOCKER: known／measurement の後続世代と active 解決が未設計

**攻撃シナリオ:** `measurement_freeze.v3.g2.json` を弱い `analysis_contract` で追加し、literal root を g2 へ向ける。草案には known／measurement の gN→gN+1 allowlist、各世代の人間 approval、fork／gap／second genesis／revocation、active pointer の一意解決がないため、g1とg2のどちらが公式かを機械的に裁定できない。

§1.5 は全 family に世代を導入する一方、§4.2 Step 8 の具体的 transition は holdout だけである。現行 ratified machinery が持つ連番・fork・approval・active topology を設計前に削っている。

**根拠:** `s8b_ratified_freeze.py:1139-1283`、設計案 §1.5、§2.2 Step 8、§4.2 Step 8、§6 W6。

### A-9 — MAJOR: F9 型の「宣言したが毎回発火しない」が残る

**攻撃シナリオ:** holdout g1 発行後に `design_source` を編集する。artifact raw bytes と `FROZEN_MANIFEST` は変わらないため raw-root test は通る。canonical real-repo verifier が必須 CI nodeとして固定されていなければ drift は再び潜伏する。

「rebase/merge 後 CI で再実行」は、実行対象名、不在時 fail、required node の固定がない。F9 と同様に test file／登録が消えても保証文だけが残り得る。

**根拠:** `docs/failures.md:88-100`、`docs/decisions.md:2757-2765`、設計案 §3.4、§6 W1–W4。

### A-10 — MAJOR: D68(7) 型の fixture 隠蔽を禁止していない

**攻撃シナリオ:** 新 measurement test が現行同様 `build_document` を fixture document の echo に monkeypatch し、generator hash／expected values を動的注入する。production extractor が壊れても fixture と checker が同時に追随し、テストは通る。

§8(5) の「independent expected values」は配置も生成禁止規則もなく、W1–W3 の受入条件になっていない。D73 が要求した「外部 I/O だけ固定し、実 extractor と再構成を動かし、独立 golden と比較」を明文化する必要がある。

**根拠:** `test_s1_measurement_freeze.py:91-116`、`docs/decisions.md:2891-2896`、設計案 §6 W1–W3、§8(5)。

### A-11 — MAJOR: T-078 型の恒真 positive control を再生できる

**攻撃シナリオ:** search 実装を「holdout hit は常に空、positive hit_count は常に1」とする。草案の条件 `conjunction == 0` と `positive_control > 0` はどちらも通る。checker 非 pin のため code drift 自体も拒否されない。

positive control は同じ search 関数が自己生成する値ではなく、外部固定された exact fixture path＋bytesに対して、baseline pass／対象 mutant の単一理由 fail／revert pass を要求しなければならない。

**根拠:** `s8b_holdout_freeze.py:427-432,815-823`、`s8b_ratified_freeze.py:1390-1399`、`docs/decisions.md:2925-2929`、設計案 §1.4、§4.4、§8(5)。

### A-12 — MAJOR: receipt の Git 履歴検証に replace／grafts 防御がない

**攻撃シナリオ:** local `refs/replace/*` または grafts で introduction commit の parent/tree を差し替え、receipt verifier に偽の legacy blob・parent 関係を見せる。§2.4 は Git エラー分類しか定めず、単一 H の捕捉、shallow 拒否、replace refs 無効化・存在拒否、grafts 拒否を定めていない。

現行 ratified verifier はこの攻撃を明示的に閉じている。receipt が歴史証明を担うなら同等の hardening が必要である。

**根拠:** `s8b_ratified_freeze.py:269-325`、設計案 §2.4、§4.2 Step 6。

### A-13 — MAJOR: P6 と草案 §4.3 の波及面はまだ不足

**攻撃シナリオ:** permanent loader は hash `H` を検証したが、run marker が path を再読して別 bytes の identity を作る、budget ledger が legacy hash と結ばれる、または downstream report／judge が freeze identity を失った manifest だけを受理する。公式 chain が途中で別 lineageへ分岐しても、列挙された migration testsでは検出されない。

追加で監査・統合試験対象に要る面は少なくとも次である。

- `s8b_budget.py` — ledger が `freeze_sha256` を永続化・再照合する (`:208-223,353-366`)
- `s8b_run_marker.py` — caller path を再読して identity を作る (`:32-42,101`)
- `s8b_oracle_artifacts.py` — runtime marker は provenance 証明でないと自認 (`:2-5`)
- `s8b_oracle_report.py`／`s8b_oracle_judge.py` — downstream は現状 manifest hash までしか運ばない (`report.py:1272-1274`, `judge.py:135-140,260-261`)
- `s8b_materialization.py` — verified 型でなく任意 `Mapping` から binding を実体化する
- `hooks/guard_write.py`、`hooks/README.md`、`test_hooks.py` — 現行 namespace write contract と新 publish 手順の整合 (`guard_write.py:86-96`)

草案自身が追加した `s8b_approved.py` 以下の面も必要だが、上記を加えても実際の call graph と required test node の逆引きが要る。

### A-14 — MINOR: `ccbench_pin` の表現が未確定

**攻撃シナリオ:** measurement g1 が legacy projectionを理由に7桁 `"d706650"` を維持し、known g1 は40桁 gitlinkを持つ。「同じ commit」という散文だけでは equality が成立せず、prefix collision／誤った短縮値を許す余地が残る。

新 schema は両 artifact と実 gitlinkの40桁 full SHA完全一致を要求すべきである。

**根拠:** `s1_measurement_freeze.py:262`、`pin.py:28`、設計案 §1.2–§1.3。

## 2. brief P1..P6 の逐条判定

| 項目 | 判定 | 理由 |
|---|---|---|
| P1 | **条件付き** | checker 非 pin の方向は確定事項として受けるが、有限 vector＋同一コード再構成では現行 gate の代替にならない。独立 runtime oracle、closed-world check registry、checker変更とroot承認のcommit／review分離が成立するまで hash を外せない。 |
| P2 | **否認** | dangling field の温存は不要だが、単純廃止は生成時 repository tree と artifact の原子的関係を失う。導入 commit の親/tree OIDを外部導出する方式へ置換すべき。 |
| P3 | **条件付き** | side-by-side再発行は妥当。receipt・artifact・rootsを同一commitに入れず、候補commit、bundle全体をhash束縛した人間approval commit、activation commitを分離することが条件。 |
| P4 | **条件付き** | 人間同席だけでは不足。最終bytes生成後に、人間が独立取得した bundle hashを別record／別commitで承認する必要がある。 |
| P5 | **採用** | legacy transition／equalityを遡及変更せず、新契約を別schema・別moduleへ分ける方向は正しい。ただし新契約のactive topologyを先に完成させること。 |
| P6 | **否認** | brief の列挙は不足。草案追加分に加え、A-13の budget、run marker、oracle artifact/report/judge、materialization、hooks面が残る。 |

## 3. 設計択一 A..H の逐条判定

| 択一 | 判定 | 理由 |
|---|---|---|
| A | **否認** | option 1 の単純廃止では監査時点を失う。option 2を、自己参照SHAでなく導入commitの親/tree OIDとして実装すべき。 |
| B | **同意** | versioned side-by-side path は legacy bytesを壊さない。ただし active resolver が未設計。 |
| C | **同意（限定）** | `unverified` と明示し、gate・再構成・consumerから型で隔離するなら保持可能。ただし監査証拠や真正な発行実装とは呼べない。 |
| D | **否認** | finite conformance vectorsだけでは列挙外入力を拘束しない。実入力ごとの独立再計算が必要。 |
| E | **否認** | exact holdout hash は必要だが不十分。三成果物＋receiptの bundle hashを、生成後の別 human approval commitで束縛すべき。 |
| F | **同意** | old tableを不変保持し、新schemaのtransitionを別定義するのが安全。one-time receipt単独での発効は認めない。 |
| G | **否認（恒久案として）** | 全削除より現行63件保持の方が安全だが、完全 closureではない。未列挙 dependencyを追加し、分類を終えるまで「恒久閉包」と扱えない。 |
| H | **同意** | 静的Git読取でも known 5＋measurement 3＋holdout 1、7 distinct anchorを確認できた。ただしreceipt verifierのGit hardeningが条件。 |

## 4. 総合判定

**NO-GO**

最低限、次の再設計が必要である。

1. finite vectorを実入力用の独立統計 oracleへ置換する。
2. artifact候補、human approval、active root更新を別commit・別差分面へ分離する。
3. human approvalを holdout単体でなく三成果物＋receiptの bundle hashへ束縛する。
4. `frozen_at_head` を削る代わりに、導入commitの親/treeへ非自己参照で束縛する。
5. schemaごとの exact check-ID集合と candidate／official の別型を定義する。
6. known／measurementを含む全familyの世代遷移・fork拒否・active解決を確定する。
7. F9／D68／T-078再発を殺す具体的 mutation と required CI nodeを設計本文へ固定する。

pytest は実行しておらず、テスト green の主張はしていない。静的検査とGit読取のみの判定である。
---
## 段 3b: 敵対相談 B (整合・実効性レンズ) — NO-GO、15 所見 + 独立実測

# 総合判定: NO-GO

§4.1 の「9 raw blob / 7 dangling anchor」と9個の raw SHA-256 は再現できた。一方、transition 数の誤り、正しさゲートの弱化、原子的切替不能、未定義の lineage/receipt、D73(4) 未消化があり、恒久設計として実装へ渡せない。

pytest は実行しておらず、green は主張しない。

## 独立実測

`git log --all --reverse -- <path>` と `git show <commit>:<path> | sha256sum` の結果:

| family | commit | raw SHA-256 | 判定 |
|---|---|---|---|
| known | `80b30107…` | `1622ecadde1cf8fd432c804d198ded8f0b3ce89b19d02503c6b77fee86952cdd` | 表と一致 |
| known | `15fcc08f…` | `e1b0a5348034b5bf6e938ff498802ccc2d43cd2b646ed745c5f3d803ca05fd8e` | 一致 |
| known | `8f7fca22…` | `7a7458df4ee4350ff500f7b47662fe74ae8e3d0936430c1dda8c3a8fcb012f3e` | 一致 |
| known | `b4e5cb62…` | `3eb808b4b751d5dc57e57e214fc6d7fea9a9c702a0208b5f0e87f094ae65bce1` | 一致 |
| known | `e5dfa84c…` | `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516` | 一致 |
| measurement | `4b9d86e3…` | `09dd1585ca28aebfbae0e724e4bacb299452dbad1b21eb67e893795d999756f6` | 一致 |
| measurement | `b4e5cb62…` | `5c719c076e17f385a781933c081bf02abcd85b9edb01ad8c50a37740c134a191` | 一致 |
| measurement | `e5dfa84c…` | `203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a` | 一致 |
| holdout | `911f6bc0…` | `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688` | 一致 |

7種類の recorded head はすべて `git cat-file --batch-check` で `missing`。`git fsck --unreachable --dangling` にも該当なし。`e5dfa84c…` の実親は `9c10b5f…`、記録値は `2066ce6b…` だった。

## 所見

### B-1 — MAJOR: `_TRANSITION_V1_TO_G1` は12でなく13 pointer

brief の数値主張は誤り。実測:

```text
len(_TRANSITION_V1_TO_G1) = 13
contains("/known_axes_freeze/sha256") = False
```

`/known_axes_freeze/sha256` が無い点だけは正しい。13個は [s8b_ratified_freeze.py:115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:115) に列挙され、`/schema_version` も含む。D72自身の「12 pointer」も現行コードと不一致である（[decisions.md:2800](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2800)）。

### B-2 — BLOCKER: 有限 conformance vector は現行 code hash gate と同等でない

現行は `s1_stats.py` の全bytes一致を拒否条件にしている（[s1_measurement_freeze.py:400](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:400)）。設計案 §1.3/§5-D は「少なくとも」数個の vector だけに置換する。

しかし `s1_stats` の入力は任意の有限数16個であり（[s1_stats.py:62](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_stats.py:62)）、列挙された vector 以外でだけ誤る実装を容易に構成できる。固定 vector を特別扱いし、それ以外で tail 判定を逆転させても新 gate は通る。

したがって受理集合は厳密に広がる。brief の「正しさゲートを正味で弱めない」と両立しない。完全な独立参照アルゴリズム、形式仕様、または対象入力領域を覆う同値性証明が必要。

### B-3 — MAJOR: 「解析実装 bytes は pin しない」と63 source維持が自己矛盾

設計案 §1冒頭は解析実装bytesを gate にしないと宣言する一方、§1.2では63 source recordを全て gate に残す。

実物を `jq` で数えると、generatorを除く63 record中、`.py` は24 record、6種類の実装ファイルである。現行 verifier はこれらを現行worktreeのbytesと全件比較する（[s1_known_axes_freeze.py:731](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:731)）。

よって「input」と呼び替えただけで、解析・選定実装のraw code pinが残る。Option G-3を将来へ送るなら、今回の案はT-074/P1を完了する恒久設計ではない。

### B-4 — BLOCKER: 原子的切替規則とW5→W7/W8の順序が両立しない

設計案 §3.1 は3 artifactを個別発効させないとし、§8(11)は「knownだけ新・holdoutは旧」のofficial混在を禁止する。

しかし§6では、W4後にW5がS-1 consumerを新known/measurementへ切替え、holdout側はW7/W8まで旧laneに残る。これは設計案自身が禁止した混在状態そのもの。

全familyを切り替える単一active-bundle pointer、またはW5/W7/W8を一つの原子的activation commitにまとめる設計がない。

### B-5 — BLOCKER: Step 1 は列挙された対象ファイルだけでは実行できない

Step 1 は「broken verifierをofficial active consumerから外す」とするが、対象一覧に `s8b_oracle_driver.py` がない。実際のofficial gateは現在も:

- holdout verifierを [s8b_oracle_driver.py:216](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:216)
- known verifierを [同:249](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:249)

で直接呼ぶ。

driverを変えなければStep 1は未達。変えればW7の排他的所有と衝突し、refusal集合を変えるためT-068の再裁定と対応テストも同時に必要になる。Step 1..8を独立したgreen commitとして並べられる計画ではない。

### B-6 — MAJOR: D73(4) の observation 伝播先は未消化

D73(4)はWAL、oracle report、judgeのいずれにも格納先がないことを問題にしている（[decisions.md:2879](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2879)）。

設計案の `VerificationReport` はloaderの一時戻り値にすぎず、以下を定義していない。

- `campaign-start` 等のWAL schema
- `s8b_oracle_report.py` のobservation field
- `s8b_oracle_judge.py` の受理・表示契約
- calibration成果物への構造化記録

§4.3のcalibration変更も `freeze_frozen_at_head` を削除してidentityを記録するだけで、observation伝播ではない。新schemaにancestryが無いことは、legacy laneのobservationを無言で捨てる根拠にならない。

### B-7 — BLOCKER: permanent lineage／approval／active rootの契約が未定義

§2.2はgeneration chain、receipt、active rootを検査すると言うが、以下のexact schemaがない。

- known/measurementのg2以後のtransition許可面
- family bundleのactive pointer
- holdout gNのapproval、revocation、cancellation
- active選択の一意性と履歴不変条件
- receiptの9 inventory／3 successors／relationsの件数、一意性、完全性

既存v2にはapproval/pointer/tombstoneのexact schemaがある（[s8b_ratified_freeze.py:100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:100)）。新案はこれに相当する契約を「別module」に先送りしているだけで、実装可能な仕様になっていない。

また `ArtifactRef` / `SourceRecord` のcanonical repo-relative path規則もない。raw hash不一致後も後段を続ける設計なので、未信頼documentのabsolute pathや`..`を読む危険がある。既存のpath防壁相当（[s8b_ratified_freeze.py:857](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:857)）が必要。

### B-8 — MAJOR: 人間によるexact hash承認の順序が閉じていない

§3.1は、

1. 人間が確認者・時刻を与える
2. holdoutを生成
3. receiptを生成

という順だが、successor raw hashは2の後でしか確定しない。hash確定後に人間が再承認する工程がない。

さらにreceiptの `human_ratification` が直接束縛するのは `holdout_successor_sha256` だけで、scope文字列が称する「three-artifact migration bundle」のknown/measurement hashを人間が承認した証拠にはならない。

必要なのは「candidate bundle digest確定 → 人間承認 → approval record固定 → activation」の二段階手順。

### B-9 — MAJOR: holdoutのpre-measurement verifierは意図した実走後に自己失効する

§1.4は `lifecycle_stage=pre-measurement` でlive conjunction 0を必須にする。holdoutを実走すればrepository内にhitが生じるため、g1は意図した使用後にfull verify不能になる。

その後g2を検証するとき、歴史g1をlive searchまで再検査するのかsnapshotだけ検査するのかが未定義。現行v2は、immutable snapshot検査（[s8b_ratified_freeze.py:1015](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1015)）とlaunch時のlive scan（[同:2464](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:2464)）を分離している。新案はこの重要な層分離を曖昧に戻している。

### B-10 — MAJOR: 必須 `worktree clean` と同一worktree内の逐次candidate生成が衝突

§3.4はworktree cleanを必須guardにし、§3.3はcanonical directory内へcandidateをstagingする。一方§3.1ではknown→measurement→holdoutを同じbundleで順次生成する。

known candidateを作った時点でworktreeには未追跡ファイルが生じるため、次のmeasurement/holdout生成時にはcleanでない。各generatorにguardを適用すると手順が停止する。

「開始時snapshotに対しbundle-owned pathだけを許す」か、列挙対象外の隔離一時dirで全candidateを構成するtransaction仕様が必要。

### B-11 — MAJOR: consumer地図はまだ不完全

`git grep` の再計数:

| pattern | tracked全体 | `orchestrator/**/*.py` |
|---|---:|---:|
| known canonical path | 42行 / 17 file | 4行 / 4 file |
| measurement canonical path | 10 / 6 | 3 / 3 |
| holdout canonical path | 53 / 31 | 13 / 13 |
| `frozen_at_head` | 203 / 31 | 68 / 10 |
| `V1_FREEZE_SHA256` | 73 / 11 | 53 / 6 |
| `known_axes_freeze` | 307 / 39 | 66 / 16 |

§4.3／P6追加列挙に明示的な移行・歴史物判定がない参照には少なくとも以下がある。

- [test_s8b_budget.py:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_budget.py:20)
- [test_s8b_oracle_report.py:37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_report.py:37)
- [test_s8b_protocol_builder.py:54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_protocol_builder.py:54)
- [test_s8b_selector_input.py:18](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_selector_input.py:18)
- [report.json:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/reports/s1_direct_comparison/report.json:3)
- D73(4)上必要な `s8b_oracle_report.py`、`s8b_oracle_judge.py`、WAL schema

「対応するdirect tests」という総称では、排他的file ownershipにもmigration checklistにもならない。

### B-12 — MAJOR: W1..W9の所有集合は完全でも素集合でもない

具体的な欠落・衝突:

- §4.3で変更対象の `s8b_freeze_io.py` を所有するwaveがない。
- W4の「root registry」とW6の「approved root module」はexact file名と責務境界がない。
- 新testがpytest-onlyなら更新が必要な `orchestrator/tests/README.md` にownerがない。
- real repoを読む新known testは `conftest.py` と独立goldenの同時更新が必要になり得るが、両者はW9まで遅延される（[conftest.py:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:47)、[test_real_repo_serialization.py:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_real_repo_serialization.py:30)）。
- W8はselector activationを目的とするが、§8(9)は `pre_oracle_head` の内容pin化／別task化が未決と認める。実装前提がwave表に存在しない。

したがって「各fileは一waveのみ所有」は検証可能な列挙になっていない。

### B-13 — MAJOR: `FROZEN_MANIFEST` の8→12は算術上正しいが、旧8保持を検査しない

現行testは全宣言entryのhashを回すだけ（[test_frozen_artifacts.py:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:61)）で、shapeは `len == 8` と64hexしか検査しない（[同:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:75)）。

したがってStep 7では少なくとも次が必要。

- dictへ4件追加
- `len == 12` へ変更
- docstring／件数説明更新
- `legacy 8 key ∪ new 4 key` のexact key-set検査

件数だけ12にすれば、旧entryを1件落として別entryを足してもshape testは通る。D71(5)の「旧literal pin維持」を機械保証しない。

### B-14 — MAJOR: T-075の最終裁定文言と§3.2の運用が一致していない

確定記録は「wave branch生成→rebaseでSHAが変わる運用を、生成手順の変更で根絶」とする（[worklog.md:712](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:712)）。ところが§3.2は同じwave branch上のcandidate生成を許し、根絶の実体をfield削除だけに置く。

元の裁定パッケージが「生成時guardかfield廃止か」を選択肢にしていたことは事実（[worklog.md:426](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:426)）。しかし最終裁定が「手順変更」と表現された以上、schema変更だけを手順変更とみなすことを設計者が独断で確定してはならない。

最低限、field廃止をT-075の履行とみなす明示確認と、publish後rebaseを検出・無効化する機械手順が必要。

### B-15 — MAJOR: briefにも複数の事実・推論誤りがある

- 「全6 freeze」はartifact inventoryとして誤り。実在するのは9 blob／7 anchor。
- transitionは12でなく13。
- 「自己hash→source→ancestry→機械再構成」という共通順序は事実でない。holdoutはdesign→known→generator→ancestry（[s8b_holdout_freeze.py:709](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:709)）、measurementはknown verifierを入れ子で先に呼ぶ。
- 「read-onlyだから模擬と実差分の乖離なし」は成立しない。模擬をしなかったことは、将来実装とのモデル差がない証拠ではない。
- P6のconsumer集合は、上記grep結果により不十分。

## D71 / D72 / D73 制約の消化対応表

| 制約 | 設計案の対応 | 判定 |
|---|---|---|
| D71(2)(a) known変更→holdout hash不一致 | §§3.1, 4.2 Steps 3–5 | 部分。side-by-sideは方向として有効だがcutoverが非原子的 |
| D71(2)(b) holdout変更→V1 root破損 | §4.2 Steps 7–8 | 方向は消化。legacy root維持 |
| D71(2)(c) transitionにknown hashなし | §4.2 Steps 6, 8 | 部分。one-time receiptの完全性契約が未定義 |
| D71(3) holdout人間確認必須 | §§3.1, 4.2 Step 5 | 部分。hash確定後の再承認工程なし |
| D71(4) `origin/main` はpublication証明でない | §3.2 | 消化 |
| D71(5) 第三のliteral pin維持 | §§1.1, 4.2 Step 7 | 部分。12件exact key-setと旧8保持の検査なし |
| D71(6) 63 source closure | §1.2 | 表面上維持。ただしraw code pin残存でT-074/P1と衝突 |
| D72(2)/(10) checker self-pin blocker | §§1.2–1.4 | 部分。generatorは外すが解析code pinと有限vector問題が残る |
| D72(3)/(5) closure＋manifest波及 | §4.2 | 部分。activation transactionがない |
| D72(6) semantic 4 pointer≠repo transition面 | §4.2 Step 4、§4.3 | 部分。consumer/test漏れあり |
| D72(7) V1 rootはholdout bytes | §4.2 Step 8 | 消化 |
| D72(8)/(9) observation／consumer格下げ | §§2.4, 4.4 | 未消化。永続伝播先なし |
| D73(1) holdout design＋generator drift | §4.2 Step 5 | 部分。人間ratification後まで未解決 |
| D73(2) ancestry後段mask | §§2.2–2.5 | 新laneのみ消化。legacy切替途中は未解決 |
| D73(3) git障害／wrong object分類 | §2.4 | 部分。reason code案はあるがreceipt監査アルゴリズムなし |
| D73(4) observation格納先なし | 該当節なし | **未消化** |
| D73(5) T-068を親が独断失効させない | §4.4 | 記帳上は維持。ただしStep 1が実質的に先取り |
| T-077/T-078再裁定境界 | §4.4 | 「閉じない」と書くだけで、実装wave前の再裁定停止点がない |

## brief P1..P6 逐条判定

| provisional裁定 | 判定 | 理由 |
|---|---|---|
| P1 | **否認** | 有限conformance vectorではexact code hashの保証を代替できない。また63 source内のraw code pinをどう扱うか未解決 |
| P2 | **条件付き** | field廃止自体はdangling claimを消すが、T-075の「生成手順変更」とみなす明示確認、publish/rebase guard、legacy observation処理が必要 |
| P3 | **条件付き** | side-by-side＋receipt方針は妥当だが、receipt完全性、active bundle、原子的cutoverが未定義 |
| P4 | **条件付き** | 人間必須は採れる。candidate hash確定後の明示承認と、三artifact全体を束縛するbundle digestが必要 |
| P5 | **採用** | 旧transition/equalityを遡及拡張しない原則は整合する。ただし新contractの未定義部分は別途埋める必要あり |
| P6 | **否認** | grep再計数でtest、派生成果物、observation伝播面、wave ownerの不足が残る |

## 最終判定

**NO-GO。**

最低限、次を設計へ戻す必要がある。

1. `s1_stats` の非弱化な代替gate
2. 3 familyを束ねるexact active-bundle／approval／lineage schema
3. hash確定後の人間承認transaction
4. holdout snapshot検査とlive launch検査の分離
5. D73(4)のWAL/report/judge伝播契約
6. consumerとwave所有のexact file一覧
7. T-068/T-077/T-078の再裁定停止点
8. 13 pointerへの事実訂正とmanifest exact key-set検査
---
## 段 4: 親裁定

# 段 4 裁定: [T-080] 敵対相談 2 本 (両 NO-GO) の所見処理

前提: 本 wave は設計 wave であり、成果物は「ユーザー裁定向け設計パッケージ」。相談の NO-GO は
「codex 草案をこのまま実装可能な仕様として確定するな」であり、wave の失敗ではない。裁定の結果を
反映した設計パッケージ v2 を親が起草し、それを最終レビューへかける。

## 裁定の総括

- 承認済み裁定 [T-074]/[T-075] の方向を覆す新事実は無い (両相談とも方向自体は攻撃していない)。
  wave は止めない
- ただし [T-075] の充足形について B-14 が real: 「field 廃止 = 生成手順の変更」とみなすことの
  明示確認はユーザーへ返す (親が独断確定しない)。設計択一に含める
- 相談所見のうち refuted は 0 件。BLOCKER/MAJOR 全件を real と裁定し、設計要件または設計択一へ
  反映する。親が直接裏取りした 4 件: B-1 (13 pointer 実測)、A-7 (campaign.lock:157 と
  pipeline import:27 が record 外)、B-13 (len==8 のみ)、B-3 (py 24 record / 6 実装ファイル)

## 個別裁定 (採用 = 設計パッケージ v2 へ反映)

| 所見 | 裁定 | 反映先 |
|---|---|---|
| A-1/A-2 (checker 非 pin の代替防壁が願望) | real・採用 | 設計要件: required test node の明文固定、両 literal root の独立更新面、承認分離 |
| A-3/A-4/B-8 (単一 migration commit は G≠A 承認分離の退行、bundle hash 未束縛、順序不整合) | real・採用 | 生成→承認→発効の 3 段 transaction。人間承認は候補 bundle digest (3 成果物 + receipt) 確定後 |
| A-5/B-2 (有限 vector は挙動を pin しない) | real・採用 | 統計 gate = 独立参照実装による全実入力の再計算。vector は補助検査に格下げ |
| A-6 (missing check 未検出) | real・採用 | closed-world check registry (schema ごとの exact check-ID 集合、unknown/missing/duplicate 拒否) |
| A-7 (63 closure 不完全) | real・採用 | closure 補完 (campaign.lock、pipeline.py 等) + 完全性判定基準を設計に明記。P2 は修正 |
| A-8/B-7 (世代遷移・active 解決・approval schema 未定義) | real・採用 | 設計要件 + 「裁定後の第 2 設計段で exact schema 化」を残課題として明示 |
| A-9 (F9 型再発) | real・採用 | required CI/test node の名指し固定を設計要件へ |
| A-10 (D68(7) fixture 隠蔽の禁止漏れ) | real・採用 | 実装 wave 受入条件に echo-fixture 禁止 + 独立 golden を明文化 |
| A-11 (T-078 型恒真 positive control) | real・採用 | 外部固定 fixture + baseline/mutant/revert 3 点要求 |
| A-12 (git replace/grafts 防御) | real・採用 | receipt verifier の hardening 要件 (既存 ratified 相当) |
| A-13/B-11/B-12 (波及面・wave 所有の不足) | real・採用 | 波及面 v2 表 + 実装 wave 開始時の再列挙義務。W 分割を修正 |
| A-14 (ccbench 40 桁不統一) | real・採用 | 新 schema は 40 桁 full SHA 完全一致 |
| B-1 (13 pointer) | real・採用 | 事実訂正 + D72 (3) の「12」への erratum を worklog へ |
| B-3 (raw code pin 残存の自己矛盾) | real・採用 | 設計択一へ: 63 record 中の実装 pin の扱い (T-080 では維持 + 恒久閉包と呼ばない、将来 semantic 化は別裁定) |
| B-4/B-5 (原子的切替不能、Step 1 実行不能) | real・採用 | active-bundle pointer による単一発効点へ再設計。oracle driver を Step 1 対象に含め、T-068 との衝突を裁定停止点として明示 |
| B-6 (D73 (4) observation 伝播未消化) | real・採用 | 設計に observation 伝播契約の節を追加 (WAL/report/judge/calibration) |
| B-9 (pre-measurement live search の自己失効) | real・採用 | snapshot 検査と live launch 検査の層分離 (既存 v2 の分離を踏襲) |
| B-10 (clean guard と逐次生成の衝突) | real・採用 | bundle-owned path 許容の transaction 仕様 |
| B-13 (manifest exact key-set) | real・採用 | len==12 + 旧 8 ∪ 新 4 の exact key-set 検査 |
| B-14 (T-075 文言の充足形) | real・採用 | 設計択一へ (ユーザー明示確認) + publish 後 rebase の検出ガードを要件化 |
| B-15 (brief の誤り群) | real・採用 | 親 erratum として worklog へ (6→9 blob、12→13 pointer、検査順の家系差、「模擬乖離なし」の過大表現) |

## P1..P6 の最終形 (v2 へ反映)

- P1 → 修正: generator/self 系 hash gate は全廃。`s1_stats` は独立参照実装の全入力再計算 gate へ。
  63 record 内の実装 pin は本移行では維持し「恒久閉包」とは呼ばない (B-3・A-7)
- P2 → 修正: field 廃止は維持しつつ、receipt/lineage 層で導入 commit へ非自己参照束縛 (A-7 代案)。
  T-075 充足の明示確認をユーザーへ (B-14)
- P3 → 修正: side-by-side + receipt は維持。ただし 3 段 transaction と active-bundle pointer を条件化
- P4 → 強化採用: bundle digest 確定後の人間承認 commit (AI-Agent: none、G≠A)
- P5 → 採用 (両相談一致)。新契約の exact schema は第 2 設計段の残課題
- P6 → 否認を受理: 波及面 v2 表に相談指摘の全面を統合

## scope 裁定

- 本 wave で書くもの: 設計パッケージ v2 (docs/freeze-permanent-design.md) + 記録。コード変更なし
- scope 外 (裁定パッケージとしてユーザーへ): 設計択一の裁定そのもの、T-068/T-077/T-078 の処理、
  実装 wave の起動、exact schema 化 (第 2 設計段)
- 変異テスト事前登録: 実装差分が無いため対象外 (D72 (12) と同じ扱い)。worklog に射程を明記する

---
## 段 6a: 敵対レビュー 1 (traceability/正しさ) — 対象 = 親起草 v2、NO-GO、14 所見

結論は **NO-GO**。相談所見の語句はほぼ回収されているが、複数が先送り・恒真化され、親の合成で新しい BLOCKER も生じている。

## 1. 所見

### R1-1 — BLOCKER: §5 の独立統計 gate は入力が存在せず、実行不能

[§5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:150) は `cells` から 12 比較の statistic・p 値・family 判定を再計算するとする。しかし [§3.2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:100) が維持する `cells` は workload/configuration/variant/source_pointer だけで、観測値を持たない。現行 schema も [`CELL_KEYS`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:66) は同じであり、実際の統計入力は [`s1_report.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:574) が WAL assessment から組み立てている。

v2 schema には次がすべて無い。

- target/control の実測 2×4 値
- その値を取得する immutable source pointer
- 凍結された statistic、p numerator、family 判定
- 草案にあった `analysis_contract`

したがって A-5/B-2 は反映ではなく、実行不能な要件への置換である。さらに補助 vector も wrong shape、非有限値、invalid alternative、空 family、effect-size 計算を列挙しておらず、仮に観測値を追加しても現行 `s1_stats.py` 全 bytes gate の射程を代替しない。

### R1-2 — BLOCKER: R7 は [T-074] と §2 の双方に違反する

[T-074 の確定文言](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:710) は「入力・出力を pin し checker は pin しない」。v2 はさらに [§2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:61) で「checker / 解析実装の現行 worktree bytes 検査を全廃」と宣言する。

一方、[§3.1/R7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:97) は 24 record / 6 Python 実装の raw bytes pin を維持する。静的再計数でも以下の 6 ファイル・24 record であり、現行 verifier は [`source` 全件を現行 worktree bytes と比較](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:731)する。

- `axis_trigger_gating.py`
- `backoff_sweep.py`
- `genome.py`
- `p3_s4_loop_sort.py`
- `s6_sort_sweep.py`
- `s8a_trigger_sweep.py`

「producer code も入力である」という狭い読みなら T-074 の文字面に余地はある。しかし v2 自身が「解析実装 bytes を全廃」と定義したため、その逃げ道は使えない。R7 は通常の択一ではなく、**承認済み裁定を一時的に修正・段階化する再裁定**として提示すべきである。

また「全削除すると D71(6) を失う」は偽の二択である。導入親 tree の blob 束縛や semantic projection で provenance を保ちつつ、現行 worktree raw-code equality は除去できる。

### R1-3 — BLOCKER: §6 は成果物を導入 commit に結ぶだけで、生成入力 tree に結んでいない

[§6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:173) が検査するのは、「導入 commit が存在し、その commit の成果物 blob が現在の成果物 bytes と一致する」ことだけである。

欠けているのは A-7 の核心である。

- G が非 merge であること
- G の親が生成開始時に捕捉した H と同一であること
- 各 source record が G^ または指定 tree の blob と一致すること
- `campaign.lock`、glob の列挙結果、gitlink 等も同じ tree に同時存在したこと
- 導入 commit が一意で、削除・再追加や rename で差し替えられていないこと

攻撃者は tree Q／dirty worktree で生成した JSON を、無関係な親 P を持つ G へ追加できる。G の成果物 blob は一致するので §6 の記述どおりなら通る。

現行 ratified verifier はこれより強く、[`G^ == frozen_at_head`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:919) と [`G^` の source blob hash](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:934) を検査している。「A-7 の代案を採用」は過大主張である。

### R1-4 — BLOCKER: G→receipt→A→roots→X の commit graph と承認境界が閉じていない

[§7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:189) と [§8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:219) からは次が決まらない。

- receipt は G、A、独立 R commit のどこで導入されるか
- A が approval record 以外を変更できるか
- G/R/A/X の ancestry と全 pairwise 非同一性
- merge commit の可否
- bundle digest の hash algorithm、domain separator、component 順、canonical bytes
- approval record の exact schema、scope、expiry
- `confirmed_by/confirmed_at` と後発の A の対応関係
- X の author/authorization

receipt は G の導入情報を得た後でしか作れない一方、A の digest は receipt hash を必要とする。receipt を A に含めれば `AI-Agent: none` の人間承認 commit に生成物を混ぜる。独立 R にすれば、現設計にない第四の commit 境界が必要になる。

現行機構は [`A の diff が approval + pointer の追加だけ`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1160)と検査する。v2 の `G != A` だけでは明確な退行である。

### R1-5 — BLOCKER: active-bundle pointer は「原子的切替」を保証しない

[§7-X](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:204) は official 混在が「構造的に生じない」と断言するが、次が未定義である。

- pointer を一度だけ読み、3 family 全体を同一 H から解決する bundle-level loader
- family 間 raw hash、generation、supersedes、known参照の整合規則
- pointer 更新中・長時間 process 中の snapshot semantics
- stale approval、revocation、cancellation 後の activation 拒否
- X を実行できる主体

[§4 の loader](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:127) は単一 document を返す。consumer が known と holdout を別々に resolve し、その間に pointer が変われば混在する。また [Step 2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:216) では consumer を未接続のままにし、[Step 7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:231) で pointer 導入と全 consumer のコード切替を同時実行する。初回 X は「pointer だけの発効点」ではない。

必要なのは、現行 ratified のように [H を一度捕捉する resolution object](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1185) を bundle 全体へ拡張した exact 契約である。これを §13 へ送ったまま R9 を裁定させてはならない。

### R1-6 — BLOCKER: Step 7→8 の順序が D73(4) と逆

[Step 7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:231) で refusal 集合を変えて official lane を切り替えた後、[Step 8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:235) で初めて WAL/report/judge/calibration の observation 格納先を追加する。

しかし [D73(4)](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2879) は observation 伝播を格下げ・拒否集合変更の条件としている。現順序では、X 後かつ Step 8 前に「official gate は変わったが、その変化を永続記録できない」状態が存在する。

observation schema と consumer 伝播は X より前に dormant 導入するか、X と同一 transaction に含める必要がある。

### R1-7 — BLOCKER: §11 は必要なユーザー裁定を落としている

[§8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:241) は T-077/T-078 を設計者判断で「解消される」と扱い、T-068 は再裁定すると書く。しかし [§11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:281) に三件の択一が無い。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:700) は三件とも移行設計後の再評価対象であり、親が閉じないと明記している。

少なくとも次をユーザー裁定へ出す必要がある。

- T-068: 方式 B を実装する／恒久設計で superseded とする／legacy lane 用に残す
- T-077: 人間同席の再 pin を二重 drift の十分な解消とみなすか
- T-078: 外部 fixture 契約を旧裁定の充足とみなすか
- X の実行主体: A が自動 activation まで許可するのか、X も人間 commit を要するのか
- approval の意味: digest の確認だけか、成果物内容の semantic review まで含むか
- R9 の family 世代政策: lockstep 世代か、整合する任意 tuple か
- receipt lineage: output 導入 commit のみか、G^ source tree まで承認対象か

fork/gap/revocation を [§13](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:324) に送ることも、単なる schema 詳細ではなく policy の先送りである。

### R1-8 — MAJOR: A-1/A-2 の代替防壁は依然として process 願望

二つの literal root は [Step 6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:227) で同時更新される。別 commit、別 owner、別 approval の要求はない。

独立参照実装は統計だけで、known の選定 extractor と holdout の search/snapshot は同一 producer と verifier の同時変更に対する独立 oracle を持たない。bundle digest 承認は「この bytes を承認した」ことしか示さず、壊れた extractor の意味を検証しない。

[§14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:342) 自身が悪意ある checker を防げないと認めているため、A-1/A-2 を「解消済み」とすることはできない。

### R1-9 — MAJOR: closed-world registry、required node、positive fixture が恒真化可能

- exact check-ID 集合は [§13(3)](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:329) へ先送りされている。
- [§10](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:271) の required node は「例」であり、`test_file.py::test_name` の literal 名も required CI workflow もない。
- node 一覧自身が消された場合に誰が赤にするか未定義である。
- positive fixture は exact path/hash、所有者、root registry への pin が無く、fixture と期待値の同時更新を拒否できない。

現行 repo には [`REAL_REPO_SERIAL_NODES`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:47) のような literal node 集合と独立 golden がある。v2 はそれより抽象的であり、A-6/A-9/A-11 の全件反映には達していない。

### R1-10 — MAJOR: Git hardening と path 防壁が既存 ratified 相当ではない

[§4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:143) は replace 無効化と grafts/shallow 拒否までは書くが、以下がない。

- 検証開始時に単一 H を捕捉し、全 query を H に固定する
- `refs/replace/*` の存在自体を拒否する
- introduction の一意性、object type、parent count
- HEAD が検査中に動く TOCTOU の拒否
- delete/re-add、rename/copy の扱い

現行 verifier は [単一 H 捕捉と replace/grafts/shallow 拒否](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:306)を実装している。

また repo-relative の lexical 検査だけでは symlink component を通じた repo 外読取を防げない。Git tree の blob として読むか、symlink 非追随・regular-file・root containment を exact 化する必要がある。

### R1-11 — MAJOR: source closure の「完全性判定基準」は完全性を判定できない

[§3.1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:93) は「最低限」2 依存を足し、import graph + I/O trace で完全性を検証するとする。しかし trace が観測できるのは実行された分岐だけである。

現 generator は [`glob()` で campaign 集合を列挙](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:241)するため、出力は読んだ file bytes だけでなく、ディレクトリ membership と「ファイルが存在しないこと」にも依存する。git query、submodule tree、環境、動的 import、subprocess も同様である。

さらに「63 record を含む」としながら最低 2 つを追加するため、新 exact record 数・重複規則すら決まっていない。§13(6) への先送りは A-7 の閉鎖ではない。

### R1-12 — MAJOR: 規律2の acceptance-set 損失が明示されていない

v2 が現行 gate から失うが、差分として開示していないものは少なくとも次である。

| 現行で拒否 | v2 で新たに受理し得るもの |
|---|---|
| `s1_stats.py` の任意 bytes drift | 12 実例に影響しない入力検証、effect-size、将来入力だけの破損 |
| generator/checker の missing-check drift | root bytesが不変で、曖昧な required-node 検査も通る変更 |
| holdout `verify_document()` 時点の live hit | snapshot は一致するが現在 repo に holdout hit がある状態 |
| G^ source blob と成果物の関係 | 成果物 blob だけが導入 commit と一致する状態 |
| 現行 ratified の A diff/topology 制約 | G≠A だけを満たす approval/activation |

snapshot/live 分離自体は合理性があるが、「static verify の受理集合を広げ、launch gate だけで回収する」という規律2上の交換条件として提示されていない。

### R1-13 — MAJOR: §9/§12 は依然として完全でも素集合でもない

[§9](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:246) は「完全列挙」を名乗るが、少なくとも次が exact file として無い。

- holdout が G として pin する [`docs/phase3-8b-descriptor-design.md`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:30)
- 63+ source record と追加される `campaign.lock` 群
- `test_s8b_repo_scan_invariant.py`
- `test_hooks.py`
- `test_plain_runner_coverage.py`
- WAL schema の実装 file と direct tests
- report/judge/materialization/run-marker の exact direct-test 一覧

「上記 module の direct tests」は migration checklist でも排他的所有集合でもない。[§12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:306) も W-c が active-pointer 契約、W-e が pointer 導入を持ち、hooks の owner は無い。B-11/B-12 は部分反映に留まる。

### R1-14 — MINOR: 現行 tree に対する file:line が既に不正確

v2 は oracle driver の direct call を `:216,249` とするが、現行 tree では holdout が [`:222`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:222)、known が [`:257`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:257) である。意味上の指摘は正しいが、「すべて再実測」とする文書の証拠 locator としては更新が必要である。

### 過大主張の検査

| 言明 | 成立条件 | 判定 |
|---|---|---|
| §2「checker / 解析実装 bytes 検査を全廃」 | G に raw implementation equality が残らない | **不成立**。24 record を維持 |
| §2「登録されなかった検査が沈黙 pass する経路を作らない」 | exact ID 集合とその存在を外側から固定 | **未成立**。ID は §13 へ先送り |
| §5「挙動が同じなら通り、判定が変われば落ちる」 | 全入力・期待出力が schema にあり、全 normative behavior を再計算 | **不成立**。再計算入力自体が無い |
| §6「将来 commit SHA を持つのは構造的に不可能、field 自体が根」 | field が自己 commit G を指す場合に限定 | **過大**。既知の G^ を記録する設計は可能で、現行 ratified が採用 |
| §6/§14「履歴書換えは fail-closed 検出」 | 単一 H、unique introduction、immutable receipt、required node が成立 | **条件未充足** |
| §7「official 混在は構造的に生じない」 | bundle resolver が一度だけ H/pointer を捕捉し、全 consumer がそれだけを使う | **未成立** |
| §9「pin/consumer の完全列挙」 | pinned input・consumer・test・hook・派生物の exact file 集合 | **偽** |
| §10「test file 削除で保証文だけ残る経路を塞ぐ」 | node 名を外部または独立 literal で required 化 | **未成立** |
| R1「commit SHA を主張しなければ dangling は構造的に不可能」 | “成果物内の当該 field”だけを指す | **狭義のみ真**。receipt 自身の commit ref は dangle し得る |
| §14「承認分離 + test + review が同時更新を塞ぐ」 | reviewer/required-node/approval diff が独立かつ exact | **process 条件付き**。機械保証ではない |

## 2. traceability 対応表

| 相談所見 | v2 反映先 | 判定 |
|---|---|---|
| A-1 | §§2(3–4), 7-A, 10, 14 | **骨抜き**。root は同時更新、required node は例示のみ |
| A-2 | §§2, 5, 7, 14 | **骨抜き**。統計以外の独立 oracle が無く、code+artifact 同時変更が残る |
| A-3 | §§2(4), 7-A | **部分**。G≠A はあるが A diff・ancestry・receipt commit が未定義 |
| A-4 | §7-A | **部分**。3成果物+receipt を後承認する方向は反映、digest/record exact 契約なし |
| A-5 | §5 | **実行不能**。`cells` に統計入力・出力が無い |
| A-6 | §§2(5), 4, 13(3) | **部分**。unknown/missing/duplicate は書いたが exact ID 集合を先送り |
| A-7 | §§1.2, 3.1, 6, 13(6) | **部分**。2依存は追加したが G^ source-tree 束縛を欠落 |
| A-8 | §§3, 7-X, 13(1) | **骨抜き/先送り**。fork/gap/revocation/active 一意性が未定義 |
| A-9 | §10 F9 | **骨抜き**。literal node 名・required CI 面なし |
| A-10 | §10 D68 | **反映**。echo禁止、実 extractor、独立 golden を明記 |
| A-11 | §§8, 10 T-078 | **部分**。3点要求はあるが fixture の exact pin と T-078 裁定なし |
| A-12 | §§4, 6 | **部分**。replace disable/grafts/shallow はあるが単一 H・存在拒否・unique intro なし |
| A-13 | §§9, 12 | **部分**。指摘 module は増えたが exact test/owner 集合でない |
| A-14 | §§3.1–3.2 | **反映**。40桁 gitlink 完全一致 |
| B-1 | §1.2 | **反映**。13 pointer へ訂正 |
| B-2 | §5 | **実行不能**。A-5 と同じ |
| B-3 | §§3.1, 11-R7 | **未解決**。択一化したが §2/T-074 と矛盾 |
| B-4 | §§7-X, 11-R9, 13(1) | **部分**。pointer 方針のみで bundle snapshot 契約なし |
| B-5 | §§8-7, 9 | **部分**。driver と T-068 stop は入ったが初回 X が code+pointer 同時変更 |
| B-6 | §§8-8, 13(2) | **部分かつ順序誤り**。伝播を X より後へ配置 |
| B-7 | §§4, 13(1) | **骨抜き/先送り**。path 防壁概念は追加、lineage/approval/active は未定義 |
| B-8 | §7-A | **部分**。hash確定後のbundle承認は反映、approval exact schemaなし |
| B-9 | §3.3 | **反映**。snapshot と live launch を分離 |
| B-10 | §7-G | **反映**。開始 snapshot + bundle-owned path を記載 |
| B-11 | §9 | **部分**。列挙を拡張したが exact file checklist ではない |
| B-12 | §12 | **部分**。W-a..f は責務名で、完全な素集合 file ownership でない |
| B-13 | §8-6 | **反映**。`len==12` + 旧8∪新4 exact key-set |
| B-14 | §§6, 11-R1 | **概ね反映**。明示確認へ戻した。ただし「根絶」の根拠は過大 |
| B-15 | §§1.1–1.2 | **事実訂正は反映**。9 blob/7 anchor、13 pointer。旧の共通検査順・模擬乖離なし主張は再掲していない |

## 3. 総合判定

**NO-GO。**

この doc をユーザー裁定用パッケージとして提出してはならない。理由は、実装詳細が未確定だからではなく、裁定対象となる骨格そのものに以下の未成立があるためである。

1. §5 の中心 gate が現 schema から実行できない。
2. §6 が生成入力 tree を束縛せず、A-7 を満たしていない。
3. G/receipt/A/X の承認 transaction と active bundle の snapshot semantics が閉じていない。
4. observation 伝播が X より後で、D73(4) に逆行する。
5. R7 が [T-074] の再裁定であることを隠している。
6. T-068/T-077/T-078、X の権限、approval の意味等が §11 から欠落している。
7. A-1/A-2/A-6/A-8/A-9/A-12/A-13 と B-7/B-11/B-12 は「反映済み」と呼べない。

pytest は実行していない。判定は静的読取、現行 JSON/schema の照合、Git 履歴・実装の読取だけに基づく。
---
## 段 6b: 敵対レビュー 2 (事実/整合) — 対象 = 親起草 v2、NO-GO、16 所見

## 再実測の基線

主要な数量は再現できた。

- `git log --all --reverse -- <3 paths>` と各 `git show <commit>:<path> | sha256sum` で、known 5・measurement 3・holdout 1 の9 blob、表の raw SHA-256、7 distinct anchor を確認。
- 7 anchor はすべて `git cat-file -t` 不成立。`git fsck --unreachable --dangling --no-reflogs` にも該当なし。
- `e5dfa84^ = 9c10b5f…`、記録値は `2066ce6b…`。
- `_TRANSITION_V1_TO_G1` は13 pointer、`/known_axes_freeze/sha256` なし。
- generator を除く source record は63件、そのうち `.py` は24 record／6 path。
- `FROZEN_MANIFEST` は8件。

## 所見

### R2-1 — BLOCKER: §5 の統計 gate は入力も比較対象も schema に存在しない

[§3.2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:100) は `cells`、`comparisons`、schedule 等しか定義していないのに、[§5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:150) は「`cells` から statistic・p 値・family 判定を再計算し、凍結値と一致」とする。

実測:

- `jq '[.cells[]|keys_unsorted]|unique' measurement_freeze.json` → `workload/configuration/variant/source_pointer` のみ。
- top-level に観測値、statistic、p 値、gate 結果、family 判定はない。
- `rg s1_stats s1_measurement_freeze.py` でも `s1_stats.py` は hash 対象であり、統計計算には使われない。

従って再計算元も「凍結値」もなく、記述どおりには実装不能である。これは§13にも残課題として載っていない。

### R2-2 — BLOCKER: §2 の「解析実装 bytes pin 全廃」と §3/R7 が正面衝突する

[§2-2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:61) は checker／解析実装の worktree bytes 照合を「全廃」とする。一方、[§3.1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:93) と R7 は、実装6ファイル・24 record の raw hash gate 維持を推奨する。

`jq ... | awk '/\.py$/'` の実測は24 record／6 pathで文書どおりだが、呼び名を「入力 closure」に変えても raw code pin である。現行 worktreeと比較するのか、導入 commit の親 treeと比較するのかも未定義で、実装者は両原則を同時に満たせない。

### R2-3 — MAJOR: source closure は既知の追加欠落すら列挙し切れていない

`campaign.lock` と `pipeline.py` の欠落は正しい。しかしさらに、

- `s1_known_axes_freeze.py` は `campaign.model.Genome` を直接 import。
- `pipeline.variant_id()` は `Genome.canonical()` と `source_digest.STOCK` に依存。
- `model.py` と `source_digest.py` は63 recordにない。

`import graph + I/O trace` だけでは、未通過分岐、directory enumeration、新規ファイルという負の入力も閉じない。§13へ送るなら、R7を実装可能な択一として提示できる段階ではない。

### R2-4 — BLOCKER: §6 は source records を単一 repository tree に束縛していない

[§6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:169) が要求する再検査は「導入 commit の artifact blob が現在の成果物 bytes と一致」だけである。記録する親 commitについて、全 `SourceRecord`、ccbench gitlink、search入力がその親 treeに同時存在したことを検査していない。

これは相談 A-7 の核心だった「生成時入力を一つの tree に束縛する」を満たさず、親 commitは実質未使用 metadataである。

### R2-5 — BLOCKER: `--diff-filter=A` から導入 commit は一意に再導出できない

実測では、現行9 blobに対して

```text
git log --all --diff-filter=A -- <path>
known       80b30107 のみ
measurement 4b9d86e3 のみ
holdout     911f6bc0 のみ
```

であり、§1の残り6行はGit上の `A` ではなく既存pathの変更である。

将来の版付きpathでも、検索ref、first-parent/full ancestry、merge commit、delete→re-add、同一bytesのcherry-pickをどう処理するかがない。squash/cherry-pickはcommit SHAを変え、単なる「main到達可能」は候補を選択しない。複数候補時の拒否規則と、非merge・追加一回の履歴制約が必要である。

### R2-6 — BLOCKER: 「3段 transaction」と§8の状態遷移が一致しない

[§7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:189) は G/A/X の3 commitを称するが、§8は実際には、

```text
G → receipt → A → literal roots → X → observation
```

を独立stepとして要求する。receiptはGの後でないと作れず、A digestに必要なのでG commitには含められない。root更新もAの後である。にもかかわらず、commit親子関係、receipt/root commitの差分allowlist、A≠Xは未定義で、機械検査はG≠Aだけである。bundle digestのcanonical serialization・hash algorithmもない。

さらに§6は「発効後に承認record」と書く一方、§7ではAがXより前である。

### R2-7 — BLOCKER: Xをobservation伝播より先に発効できない

[§8 step 7–8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:231) は、全consumerを新laneへ切り替えた後にWAL/report/judgeへobservationを追加する。これでは新official laneが一段階、D73(4)の伝播契約なしで存在する。

一方§12のW-eは切替とobservationを同一waveにまとめており、§8の「各step独立にgreen」とも一致しない。

### R2-8 — BLOCKER: active-bundle pointer のbootstrapとtrust rootがない

[§7-X](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:204) には以下がない。

- pointerのpath、schema、raw hashのroot
- legacyを初期activeとするg0/bootstrap表現
- g1 pointerのparent
- 複数承認済みbundleからofficialを一意に選ぶ規則
- rollback、fork、gap、pointer削除・差替えの拒否
- legacy consumerとpointer consumerの並存時のresolver契約

しかもstep 6で新pathをproduction rootへ登録し、step 7までinactiveにするため、§4のcandidate/canonical二型だけでは足りない。`approved-but-inactive` と `active-official` の型が必要である。核心を§13へ先送りしたままR9で方式だけ選ばせても実装できない。

### R2-9 — BLOCKER: §7-Gのguardは逐次生成との両立条件を定義していない

「開始snapshot + bundle-owned pathのみ増加」は方向としては両立可能だが、許可pathの事前確定、既生成fileのbyte不変、削除・rename・symlink・ignored file・並行writerの扱いがない。

また現行holdout searchはtracked＋untrackedを列挙し、`output/s8b-freeze/` だけを除外する。staging先とfinal pathが違えばsnapshot対象やhit pathが変わり得る。

加えて現行 [guard_write.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/hooks/guard_write.py:86) は `output/s8b-freeze/` への直接Write/Editを拒否する。hooks調整は§9に挙がるだけで、Gより前のstepにもW-a..W-fのownerにもない。

### R2-10 — MAJOR: closed-world registryとrequired nodeが同じ可変コードに閉じている

check-ID集合の正本場所とrequired nodeの外部固定面がない。checker変更で検査本体とIDを同時に削れば、同じmutable registryに対するexact-set検査は通る。§10も「例」を挙げるだけでexact node名・CI manifest・不在検査主体を定義せず、check-ID一覧は§13へ先送りしている。

repo内にはこの設計が依存できるrequired-node manifestもCI設定も示されていない。A-1/A-6への回答として未成立である。

### R2-11 — MAJOR: W-a..W-f は素集合でもcoverage集合でもない

具体例:

- §9のhooksにownerがない。
- W-aのloaderとW-cのactive resolverのfile境界がない。
- W-cのapproval契約とW-dのreceipt/approval責務が重なる。
- direct testsを総称で済ませ、exact file ownershipを示していない。
- `s8b_holdout_freeze.py` はknown成果物を直接消費するが§9にない。
- W-b/W-cでreal-repo testを追加するのに、`conftest.py` と独立goldenはW-fまで遅延する。
- `tools/check_docs.py`、`docs/README.md`、新設production root/pointerのexact fileが割当にない。

従って「各fileは一waveのみ所有」は検証不能で、§9全面も覆っていない。

### R2-12 — BLOCKER: R1..R9に答えてもbriefは書けない

§13自身が、lineage/approval/pointer/receipt、observation、check-ID、source closure、transition全般を未仕様としている。さらにbundle digest符号化、導入commit探索、root registry場所、inactive型、pathのsymlink防壁も本文外である。

またR8は事実の正誤であって択一ではなく、R4/R9の代案は本文自身がBLOCKER／矛盾として排除済みである。R2やR9で非推奨案を選ぶと§3～§8全体が無効になるが、代替仕様はない。これは裁定パッケージではなく、推奨案への同意確認と未完成仕様の混在である。

### R2-13 — MAJOR: worklog／phaseとの状態整合が取れていない

[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:717) のT-080は今も「全6 freeze」で、9 blob／13 pointerのerratumは追記されていない。

さらにworklogはT-077をT-080後の再評価、T-078をT-077待ちとしているが、本文はR項目なしに「step 3で解消」「§10で再定義」と処理を決めている。T-068だけにある明示的再裁定停止点がT-077/T-078にはない。

[phase3.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:66) は依然holdout v2再凍結を現行計画とし、同文書にはS-1 freeze実体の生成・commitが未了という現物と反する記述も残る。

### R2-14 — MAJOR: 提出物の証拠リンクとlint coverageが欠ける

[冒頭](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:9) が逐語正本として挙げる `output/insights/2026-07-22_t080-freeze-permanent-design.md` は存在しない。

`python3 tools/check_docs.py` は「違反なし」だったが、[LIVING_DOCS](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:26) に対象文書がなく、`docs/README.md`にも登録されていないため、この結果は対象文書のpath参照を検査していない。対象文書内に禁止されたdocs間行番号参照は見つからず、§9で既存物として挙げたfileは存在した。

### R2-15 — MAJOR: 「rebase由来の直接証拠」は証拠能力を過大表示している

`e5dfa84^=9c10b5f` と記録anchor `2066ce6b` の不一致が証明するのは、「記録HEADが最終commitの親ではなく、現在objectもない」ことまでである。rebase、amend、cherry-pick、別branch HEADからの生成は区別できない。reflogにも該当証拠は残っていない。

従って「rebaseと整合する証拠」ならよいが、「rebase由来の直接証拠」は事実主張として強すぎる。

### R2-16 — MINOR: 行位置とmanifest検査の記述が不正確

現行行位置は次のとおり。

- known generator hash照合: `724–727`。`:722` はpath比較。
- `campaign.lock` のpath構築: `157`、実読込は`160`。
- oracle verifier直接呼出し: holdout `222`、known `257`。`:216,249` は各blockの開始。
- manifestは`len==8`とhash一致だけでなく、pathの`output/` prefixと64 lowercase hexも検査する。「のみ」は誤り。ただし旧8 exact key-setを検査しないという本旨は正しい。

## 総合判定

**NO-GO。**

主要な実測値は概ね正しいが、統計gate、親tree anchoring、commit topology、active pointer bootstrap、guard、observation順序が実装不能または未定義である。さらにR1..R9だけでは第2設計段の主要判断が何も閉じず、worklog・phase・逐語証拠も未整合である。

この状態で「ユーザー裁定用パッケージ」として提出してはならない。pytestは実行しておらず、テストgreenの主張はしていない。
---
## 段 6c: 修正検証 (対象 = 全所見反映後の改稿版) — NO-GO (残 6 条件の列挙)

## 総合判定: NO-GO

改訂版は30所見の論点を本文へほぼ回収しましたが、提出基準を満たしていません。

- 解消: 9件
- 部分解消: 18件
- 未解消: 0件
- 意図的受理: 3件

主因は、統計契約の誤り、`H` の二重定義、§8/§12 の実行順矛盾、存在しない証拠ファイルです。これらは R 項目・§13・§14 のいずれにも正しく収納されていません。

## 30所見対応表

| 所見 | 改訂版の該当節 | 判定 | 根拠 |
|---|---|---|---|
| R1-1 | §3.2、§5、§14 | 部分解消 | `observations`/`analysis_results` は追加されたが、Holm の意味が現行実装と不一致。効果量も凍結対象外で、exact schema の残課題化もない。 |
| R1-2 | §2(2)、§3.1、R7 | 解消 | raw code pin を `[T-074]` の「部分修正の再裁定」と明記し、worktree/H-tree/削除を択一化した。隠れた矛盾ではなくなった。 |
| R1-3 | §3.1、§6 | 部分解消 | G非merge、`G^`、source blob、gitlink、成果物blobの束縛は追加。ただし `H` の二重定義、`--all` とH固定の矛盾、新設 observations のWAL由来入力がHに束縛されない問題が残る。 |
| R1-4 | §7、R5/R13/R14、§13(1)(2) | 部分解消 | R、literal×2、A allowlist、X主体・承認意味を追加。しかし `confirmed_by/at` と後発Aの関係、R/literal/Xのparent/diff/merge制約が閉じていない。 |
| R1-5 | §4、§7-X、§8 steps 2–3、R9/R15、§13(1) | 解消 | pointer一回読取、bundle resolver、g0 bootstrap、lockstep政策、revocation等の第2段送りが明示された。第1設計段の骨格としては回収済み。 |
| R1-6 | §8 steps 2–8、§12 | 部分解消 | §8では observation をX前へ移したが、§12の依存順が W-d→W-e で逆転している。 |
| R1-7 | R10–R15、§13 | 解消 | T-068/T-077/T-078、X主体、承認意味、family政策が裁定項目になった。fork/gap等も§13へ明記。 |
| R1-8 | §2(3)(4)、§5、§7、§14 | 意図的受理 | literal二面は別commit化。一方、known/holdoutの独立oracle不在と同一repo内rootの限界は§14でユーザー受理対象として明示。 |
| R1-9 | §4、§10、§13(4)、§14 | 意図的受理 | required node manifest、exact fixture pin、check-ID全列挙予定を追加。ただしmanifest/registryごと消す攻撃は機械拒否不能と§14で明示。 |
| R1-10 | §4、§6 | 部分解消 | replace存在拒否、grafts/shallow、object/parent、tree blob読取を追加。ただし検証HEADと生成親を同じ`H`で表し、全ref探索とも衝突している。 |
| R1-11 | §3.1、§13(7) | 部分解消 | 既知4依存と列挙snapshotを追加し「完全性を証明できない」と訂正。ただし恒久限界を§14/R項目のユーザー裁定へ出していない。 |
| R1-12 | §14 | 部分解消 | 受理集合表は追加されたが、効果量破損、observation出所不一致、registry同時変更等の損失が不足し、§14自身に過大主張もある。 |
| R1-13 | §9、§12、§13(8) | 解消 | 「完全列挙」「素集合」の主張を撤回し、実装前のexact再列挙・所有表確定を明示した。 |
| R1-14 | §1.2 | 解消 | oracle locator を `:222/:257` に訂正済み。 |
| R2-1 | §3.2、§5 | 部分解消 | 再計算元と凍結値は概念上追加されたが、Holm誤記とexact schema欠落により推奨R4はまだ閉じていない。 |
| R2-2 | §2(2)、R7 | 解消 | T-074の部分修正であることを正面から開示した。 |
| R2-3 | §3.1、§13(7) | 部分解消 | `model.py`/`source_digest.py` まで追加したが、完全性不能をユーザー受理項目へ出していない。 |
| R2-4 | §6 | 部分解消 | H-tree source束縛は追加。ただしHの意味衝突とWAL observationsの出所束縛が残る。 |
| R2-5 | §6(1) | 部分解消 | 一意追加、非merge、delete/re-add拒否は追加。ただし「全queryをH固定」と「`--all`全ref探索」が両立せず、探索domainが確定していない。 |
| R2-6 | §7、§8 | 部分解消 | G→R→literal×2→A→X の順は示されたが、全commitの機械的topologyと `confirmed_by/at` の時間関係が未閉鎖。 |
| R2-7 | §8、§12 | 部分解消 | §8本文では修正したが、wave依存表が再び逆順。 |
| R2-8 | §4、§7-X、§13(1) | 部分解消 | g0と三型を追加したが、A前の状態を `approved-inactive` と呼ぶ矛盾がある。pointer exact schemaは§13で明示。 |
| R2-9 | §7-G、§8 step 0、W-0、§13(5) | 解消 | 許可path事前確定、変更/削除/rename/symlink拒否、並行writer検出、hook先行waveを追加。staging exact化も§13にある。 |
| R2-10 | §10、§14 | 意図的受理 | literal node manifest/meta-testを導入する一方、同repo内可変コードである限界を明示的に受理対象化。 |
| R2-11 | §9、§12、§13(8) | 部分解消 | 素集合との過大主張は撤回したが、§8との順序矛盾と、挙動保存を検証するreal-repo goldenがW-fまで遅れる問題が残る。 |
| R2-12 | R1–R15、§13 | 部分解消 | 裁定項目は増えたが、R4等の非推奨案を選ぶと現骨格から第2段へ進めない。closure限界、approval expiry、統計family意味も裁定外。 |
| R2-13 | §1、R8、R10–R12、W-f | 部分解消 | T-068/077/078と「6 freeze」erratumは表面化。ただしworklogは依然6、phase3の既知矛盾も未修正。 |
| R2-14 | 冒頭、§9 docs面 | 部分解消 | `docs/README.md` 登録は追加されたが、逐語ファイルは依然不存在。`tools/check_docs.py` の対象追加も未実施と本文自身が認める。 |
| R2-15 | §1.1 | 解消 | 「rebaseと整合するが、amend/cherry-pick等と区別不能」に弱められ、証拠能力が適正化された。 |
| R2-16 | §1.2 | 解消 | known `724–727`、lock `157/160`、oracle `222/257`、manifest検査内容を正確に訂正。 |

## 改訂で新規に入った問題

### 1. BLOCKER: `family 判定 (Holm)` は事実・計算契約とも誤り

[§3.2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:126) は `analysis_results` に「family 判定 (Holm)」を置くとします。しかし現行の [`family_p()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_stats.py:175) は intersection–union の `max(p*)` です。さらに [`s1_report.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:704) は4-family Holmを明示的に実行しません。

したがって二通りとも成立しません。

- S-1a/S-1b内部のfamily判定を指すなら、Holmではない。
- S-1/S-2/S-3の4-family Holmを指すなら、S-2/S-3入力がmeasurement freezeに無く、observationsから再導出できない。

R4の推奨案はこのままでは仕様化不能です。

### 2. BLOCKER: `H` が二つの異なるcommitを意味する

[§4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:171) の `H` は「検証開始時のHEAD」、[§6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:216) の `H` は「生成基準commit = G^」です。通常、X後の検証HEADとG^は同一ではありません。

さらに§4は「全queryをH固定」としつつ、§6は `--all` で全refを探索します。可変ref集合への探索は捕捉した単一HEADに固定されません。少なくとも `H_verify` と `H_generate` を分け、導入探索をどの到達可能graphに限定するか確定する必要があります。

### 3. BLOCKER: §8と§12の実行順が逆

[§8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:278) は、

```text
pointer/observation dormant → consumer pointer化 → G/R/literal/A → X
```

です。一方、[§12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:410) は、

```text
W-b/W-c → W-d(G/R/literal/A) → W-e(consumer pointer化/observation配線) → W-f(X)
```

です。W-dとW-eが逆です。また挙動保存を確認すべきconsumer移行のreal-repo goldenがW-fまで遅れています。

### 4. MAJOR: 統計bytes pinの代替範囲を過大表示

`analysis_results` は効果量を含みませんが、現行 `s1_stats` は [`EffectSizes`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_stats.py:39) を公開し、reportにも永続化します。効果量だけを壊す変更は新gateを通り得ます。

それにもかかわらず[§14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:432) は「挙動変更は再構成/独立再計算で拒否」と一般化しています。これは§5の「known/holdoutには独立oracleがない」とも矛盾します。

### 5. MAJOR: observationの出所束縛がanchoring主張から漏れる

[§5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:190) は observations と WAL の照合をstatic verifyから外します。一方§6は「生成入力treeまで束縛」と主張します。

新しいmeasurementの主要入力こそWAL observationsです。source pointerをどのH-tree blob/recordへ束縛するか、A前にどのauditを必須にするかがありません。§13(3)はWAL/reportへの伝播schemaであり、`observations`/`analysis_results` 自身のexact schema課題ではありません。

### 6. MAJOR: approval状態と時系列が自己矛盾

- [§3.3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:142) は `confirmed_by/confirmed_at` を§7の承認へ束縛するとする。
- しかし[§7-G](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:241) でAより前に値を入力する。
- literal登録直後・A前の成果物を [`approved-inactive`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:249) と呼んでいる。

Aを指すならG時点では未確定です。検索同席者を指すなら「Aへ束縛」が誤りです。A前の型は少なくとも `registered-unapproved-inactive` 相当でなければなりません。

### 7. MAJOR: 証拠ポインタが依然不存在

冒頭が逐語正本とする

```text
output/insights/2026-07-22_t080-freeze-permanent-design.md
```

はrepo内に存在しません。

`docs/README.md` への登録は追加されていますが、[`tools/check_docs.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:26) の `LIVING_DOCS` にはまだ対象文書がありません。

## 事実主張のspot check

| 対象 | 結果 |
|---|---|
| 9 blob / 7 anchor | 正確。known 5、measurement 3、holdout 1。表のSHA先頭も一致し、7 anchorはすべてobject不在。 |
| `e5dfa84^` と記録anchor | 正確。親は `9c10b5f…`、記録は `2066ce6b…`。 |
| known generator `724–727` | 正確。generator raw hash照合。`:722` はpath照合。 |
| imports `:26/:27`、lock `:157/:160` | 正確。`Genome`/`variant_id` import、lock path構築/読込。 |
| oracle `:222/:257` | 正確。holdout/known verifierの直接呼出し。 |
| hook `:91–94` | 正確。`output/s8b-freeze/` 拒否。 |
| ratified `:306`付近 | 正確。shallow、replace存在、grafts、HEAD捕捉が実装されている。 |
| ratified `:919/:934`付近 | 正確。`G^ == frozen_at_head` と親treeのsource blob照合。 |
| ratified `:1160`付近 | locatorは正確。ただし現行allowlistは「approval + pointerの2追加」で、新設計の「approvalのみ」と同一ではなく類似機構。 |
| transition pointer | 正確に13件。`/known_axes_freeze/sha256` は無い。 |
| `FROZEN_MANIFEST` | 8件。`len==8`、hash、`output/` prefix、64 lowercase hexを検査し、旧8 exact key-setは検査しない。 |
| source records | generator除外63 record、`.py` は24 record/6 path。4つの既知追加依存は現行recordに無い。 |
| 逐語ファイル | 不正確。指定pathは不存在。 |

## 提出可能にする最低条件

1. `family_p` と4-family Holmを分離し、R4の凍結対象・再導出入力を訂正する。
2. `observations`/`analysis_results` のexact schemaと効果量・WAL束縛を§13へ追加する。
3. `H_verify`/`H_generate`、導入探索domain、G/R/literal/A/Xのparent/diff制約を分離する。
4. §8と§12のwave順、`confirmed_by/at`、A前の状態型を修正する。
5. 不存在の逐語ポインタ、worklogの「6 freeze」、phase3、lint対象を整合させる。
6. 非推奨R案を選んだ場合は第1設計段へ戻ること、source closure限界とapproval expiryをユーザー裁定事項として明記する。

pytestは実行していません。判定は静的読取とGit履歴・object・schemaの照合だけに基づき、テストgreenは主張しません。
---
## 段 6d: 最終チェック (6 条件の充足判定、high) — 6/6 充足 + 軽微 4 件 (反映済み)

## 6条件の判定

1. **充足 — family 判定の訂正**

   [§3.2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:126) は `family_p` を intersection–union の `max(p*)` とし、4-family Holm を measurement freeze 外と明記している。現行実装も [`family_p()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_stats.py:175) が `max()` を返し、[`s1_report.py`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:704) は4-family Holmを未実施としている。効果量も §3.2 で凍結対象に含めた。§5・§14の損失範囲も更新済み。

2. **充足 — exact schema の残課題化**

   [§13項目2b](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:445) に `observations` / `analysis_results` の単位、丸め、`float.hex()`、効果量の field 構成、WAL source pointer、A前照合手順が明記されている。

3. **充足 — `H_v` / `H_gen` の分離**

   [§4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:179) は検証時 HEAD を `H_v` と定義し、履歴探索を `H_v` から到達可能な graph に限定して `--all` を禁止している。[§6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:224) は生成基準を `H_gen = G^` と別定義し、入力 tree を `H_gen` に束縛している。

4. **充足 — wave 順・時系列・A前型**

   [§8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:296) は dormant pointer → consumer pointer化 → G/R/literal/A → X、[§12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:427) も W-d → W-e → W-f で同順序になっている。`confirmed_by/at` は [§3.3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:148) でG時点の同席記録、Aは事後のbundle束縛と整理された。A前は [§7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:264) の `registered-inactive`、A後が `approved-inactive` である。

5. **充足 — 逐語ファイルの実在**

   `ls` で [逐語ファイル](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-22_t080-freeze-permanent-design.md) を確認した。138,859 bytes、SHA-256 は `6b02415ac0f21e0d2525e4c00a8b53c7333735825f3a2d480c6010f2e7278d23`。ただし現時点では git 未追跡で、HEADにはまだ存在しない。

6. **充足 — 差し戻し・R16・approval expiry**

   [§11冒頭](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:370) は非推奨案選択時に第1設計段へ差し戻すと明記。[R16](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:411) はsource closureの恒久限界を裁定事項化し、[§13](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:441) はapproval expiryを残課題に収載している。

## 再改訂で新規に入った誤り

- **効果量の再導出契約が欠落**: §3.2では効果量を凍結したが、[§5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:196) が独立実装で再計算すると列挙するのは statistic・p numerator・family判定だけで、効果量の計算主体・計算規約がない。「`analysis_results` と完全一致」だけでは効果量を誰が再導出するか定まらない。

- **裸の `H` が残存**: `H_v` / `H_gen` へ分離した一方、[§3.1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:116)、§7、§8、R1、R7、§14に `H`、`G/H`、`H-tree` が計6か所残る。いずれも原則 `H_gen` へ置換すべき未定義略記である。

- **四型と「三型」の不一致**: [§4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:166) は四型だが、[§12 W-a](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:422) はなお「loader/三型」としている。

- **R16追加後の範囲表記が未更新**: §11本文はR16まであるが、[運用・境界見出し](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:397) は `R10..R15`、[§13見出し](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:439) は `R1..R15 裁定後` のまま。後者はR16未裁定でも第2設計段へ進める記述になる。

## 総合判定

**条件充足** — 指定された6条件はすべて充足。

ただし上記4件の新規誤りが残るため、文書全体を無条件の提出可とは判定しない。検証基準は HEAD `6f128394dc38` の作業ツリー。指定どおり pytest は実行していない。
---
## 段 6d 後の親対応

最終チェックの新規指摘 4 件 (効果量の再計算主体、裸の H 6 箇所、「三型」表記、R 範囲表記 2 箇所) を
同日中に doc へ反映した。反映後 check_docs 緑。
