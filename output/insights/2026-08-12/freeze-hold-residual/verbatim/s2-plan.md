## 総括

実装は行っていません. 推奨プランは次の 3 file だけを変更します.

- `orchestrator/tests/growth_test_holds.py`
- `orchestrator/tests/test_growth_test_holds_contract.py`
- 新規 `tools/hold_inventory.py`

(P1) は条件付きで賛成です. `correctness_gate` を "現在の production acceptance path に接続された correctness gate か" と解釈するなら, 非 test caller がゼロの 4 件は `false` です. "correctness assertion を含むか" という意味なら `true` になり, brief の規則により保留自体を中止すべきです. この意味を第 4 束の隣接 comment と契約テストで明文化することを実装開始条件にします.

以下は `correctness_gate: false` を採用するプランです.

## Provisional 裁定

### (P1) 条件付き賛成

根拠は次のとおりです.

- `correctness_gate` は schema 上の bool であり, `False` 自体は有効です. validator は型だけを検査します. `growth_test_holds.py:28-36,176-203`.
- collection hook は flag の値に関係なく台帳一致だけで skip します. flag は skip reason と user property に記録されるだけです. `conftest.py:292-303,359-375`.
- inventory は true の key だけを `correctness_gate_keys` に分類します. 混在を想定した構造です. `growth_test_holds.py:215-229`.
- 既存 30 件が全て true なのは第 3 束固有の契約です. テスト名も `current_wave_contract` であり, schema 全体の恒久条件ではありません. `test_growth_test_holds_contract.py:123-141,247-256`.
- 4 function は duplicate identity, merge history, prefix extension, delete and recreate を検査しています. `test_t793_publication_ledger.py:180-185,259-350`. 対応実装は `ledger.py:228-252,311-383` です.
- ただし前渡し事実どおり非 test caller はゼロです. 現在の production decision を拒否または受理する経路には接続されていません. よって unique detector ではあるものの, 現在の system correctness gate ではないという分類が成立します.

`false` は "検査内容が correctness と無関係" という意味にはしません. 第 4 束の直前へ, "active non-test acceptance path がないことによる false であり, assertion の非一意性を意味しない" という comment を置きます. 将来 non-test caller が追加された場合はこの前提が崩れるため, 4 件を保留したままにしてはいけません.

### (P2) 賛成

`measured_seconds` は有限かつ非負なら schema が受理し, skip 判定には使われません. `growth_test_holds.py:196-203`, `conftest.py:292-303`.

既存 30 件の `None` は第 3 束に実測値を記録しなかったという束固有の事実です. 第 4 束では reason に D320 と非 test caller ゼロを明記し, human inventory では値を "観測値であり保留理由ではない" と表示します.

parametrize された 1 function は `conftest.py:267-270` で単一 key に正規化されるため, `measured_seconds=0.06` とします. `0.03 + 0.03 = 0.06` です.

### (P3) 賛成

集約器は source 台帳を変更せず読み取るだけとし, production gate や新しい解除経路を作りません.

性質検索として実行した `rg -n 'explicit-user-command-only' orchestrator/tests` では, production 側は `test_freeze_verification_hold.py:16-27,81-89`, test 側は `test_growth_test_holds_contract.py:93-102,123-132,173-198` で別々に検査されています. 両層を同時に投影する既存検査はありません.

### (P4) 賛成

置き場所は `tools/hold_inventory.py` とします. 横断的な運用表示であり, production package に test 台帳への依存を持ち込まないためです.

import 規約は absolute sibling import の検査を `orchestrator/campaign/*.py` にだけ適用しています. `test_campaign_import_invariant.py:963-983,1035-1043`. `tools/*.py` から `orchestrator.tests.growth_test_holds` を import してもこの規則には抵触しません. legacy import の正規表現も bare `campaign...` だけが対象です. `test_campaign_import_invariant.py:52-55`.

## A. [T-913] 第 4 束の投入

### 1. 台帳を追加する

`growth_test_holds.py:13-16` の直後に第 4 束の ruling 定数を追加します.

```python
RULING_2026_08_12_BUNDLE_4 = "2026-08-12 rulings 第 4 束"
```

`growth_test_holds.py:39-53` の `_hold()` は一切変更しません. `ruling`, `correctness_gate=True`, `measured_seconds=None` という第 3 束専用 helper のまま残します.

`growth_test_holds.py:64-157` の既存 30 行は並べ替え, 再整形, helper 置換をせず bytes を維持します. 現在の tuple 終端 `growth_test_holds.py:158` の直前へ, `GrowthTestHold(...)` を行ごとに明示構築した 4 行を追記します. 新 helper は作りません. 理由は measured value が行ごとに異なり, 明示構築の方が束の異質性を隠さないためです.

各行の固定値は次のとおりです.

| node_id | measured_seconds | reason が明示する保証 |
|---|---:|---|
| `test_t793_publication_ledger.py::test_duplicate_root_kind_ordinal_identity_is_rejected` | `0.01` | duplicate identity 保証と非 test caller ゼロ |
| `test_t793_publication_ledger.py::test_unchanged_ledger_bytes_across_merge_history_are_accepted` | `0.04` | unchanged merge history の受理と非 test caller ゼロ |
| `test_t793_publication_ledger.py::test_committed_non_prefix_ledger_history_is_rejected` | `0.06` | prefix-only history 保証と非 test caller ゼロ |
| `test_t793_publication_ledger.py::test_committed_delete_and_recreate_is_rejected` | `0.03` | delete and recreate 拒否と非 test caller ゼロ |

全 4 行で次を明示します.

- `hold_axis="provenance-chain"`
- `ruling=RULING_2026_08_12_BUNDLE_4`
- `correctness_gate=False`
- `release_condition=RELEASE_EXPLICIT_USER_COMMAND_ONLY`
- `collateral_note=None`

### 2. 契約を束ごとに分ける

`test_growth_test_holds_contract.py:30-32` を 34 entry 用に更新します.

- `_EXPECTED_HOLD_COUNT = 34`
- `_EXPECTED_KEY_SHA256 = "99a9bdc379c3de828ee50ad2da15d16ce7c122d609751d181dbeb8d871539317"`
- `_EXPECTED_ROW_CONTRACT_SHA256 = "a9b2ea9d9524b32d099b6388dea8260635c5ffa4f692f1c330e04a28f0b91d62"`

同箇所の直後へ `_BUNDLE_4_MEASURED_SECONDS` を追加し, 4 key と `0.01`, `0.04`, `0.06`, `0.03` を exact pin します.

`test_growth_test_holds_contract.py:123-141` を次の構造へ置き換えます.

- 第 4 束を `_BUNDLE_4_MEASURED_SECONDS` の exact key set で抽出する.
- 残りを第 3 束とし, exact count が 30 であることを検査する.
- 第 3 束には現在の検査を全て残す.
  - ruling は `"2026-08-12 rulings 第 3 束"` のみ.
  - 全行 `correctness_gate is True`.
  - 全行 `measured_seconds is None`.
  - 全行の解除条件が exact literal.
- 第 4 束は別に検査する.
  - exact 4 key.
  - ruling は `"2026-08-12 rulings 第 4 束"` のみ.
  - 全行 `correctness_gate is False`.
  - `hold_axis` は全行 `provenance-chain`.
  - measured map は key ごとの exact equality.
  - 全行の解除条件が exact literal.
- 現在の除外対象検査 `test_growth_test_holds_contract.py:133-141` は全台帳に対して維持する.

これにより `all(...)` の検出力を捨てず, 各束へ限定して保持します. global key digest と exact 第 4 束 key set の差集合が第 3 束 30 key になるため, 第 3 束の key 検出力も維持されます.

`test_growth_test_holds_contract.py:247-256` は次のように更新します.

- `correctness_gate_keys` は全 key ではなく, 第 4 束 4 key を除いた第 3 束 30 key と exact equality にする.
- inventory row も第 3 束は全て true, 第 4 束は全て false と別々に検査する.
- `test_growth_test_holds_contract.py:257-274` の collateral note exact map は変更しない. 新規 4 行は `None` なので既存 2 件だけの map が維持される.

### 3. 3 pin の再計算

実際に現行 30 entry に対して実行し, 現行 3 pin と一致することを確認した 1 command です. 実装後も同じ command を使います.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c 'import hashlib,json; from orchestrator.tests.growth_test_holds import GROWTH_TEST_HOLDS,growth_test_hold_key_digest; payload=json.dumps([[key,hold.hold_axis,hold.ruling,hold.correctness_gate] for key,hold in sorted(GROWTH_TEST_HOLDS.items())],ensure_ascii=False,separators=(",",":")).encode("utf-8"); print(f"_EXPECTED_HOLD_COUNT = {len(GROWTH_TEST_HOLDS)}"); print(f"_EXPECTED_KEY_SHA256 = \"{growth_test_hold_key_digest(GROWTH_TEST_HOLDS)}\""); print(f"_EXPECTED_ROW_CONTRACT_SHA256 = \"{hashlib.sha256(payload).hexdigest()}\"")'
```

row digest は `measured_seconds` を含まないため, `0.01`, `0.04`, `0.06`, `0.03` は束別契約で別途 exact pin する必要があります.

### 4. 適用点は変更しない

`conftest.py:267-270,346-375` は変更しません. parametrize 2 node は同一 function key に正規化され, 1 台帳 entry で双方へ skip が付与されます.

対象 4 function は `REAL_REPO_SERIAL_NODES` の外という前渡し事実を使います. `xdist_group` は追加せず, serialization golden も変更しません.

## B. [T-914] 統合 inventory

### 1. 新規 file の構成

新規 `tools/hold_inventory.py` を次の予定行構成で作ります.

- `tools/hold_inventory.py:new:1-18`
  - module docstring, `argparse`, `json`.
  - production source と test source を import.
  - schema literal `izanagi-hold-inventory/v1`.
- `tools/hold_inventory.py:new:21-48`
  - production projection.
  - `HELD`, sorted 21 check IDs, count, digest, `dict(REASON)` を取得.
  - release は `condition`, `mechanism="manual-source-edit"`, `target="orchestrator/campaign/freeze_verification_hold.py:HELD"` を持つ.
- `tools/hold_inventory.py:new:51-78`
  - test projection.
  - sorted 34 entriesを `growth_test_hold_inventory()` から取得.
  - release は exact env 名, exact token, `explicit-user-command-only` を持つ.
  - status は ambient env に左右されない `held-by-default` とする.
- `tools/hold_inventory.py:new:81-108`
  - `hold_inventory()` が両層を固定順で返す.
  - 各層に `what`, `reason` または `ruling`, `release` を必須で含める.
- `tools/hold_inventory.py:new:111-145`
  - human renderer.
  - 各層の status, count, ruling, release 方法を先に表示し, 続いて全 check ID または node ID と reason を表示.
  - `measured_seconds` は `observed_seconds` と表示し, hold rationale ではないことを明記.
- `tools/hold_inventory.py:new:148-170`
  - JSON renderer と `--format human|json`.
  - default は human.
  - canonical 起動形は次の 2 つとする.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.hold_inventory --format human
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.hold_inventory --format json
```

集約器は source object を変更せず, `held_marker()` も呼びません. import 時に marker を出さず, production の env release 口も追加しません.

### 2. 契約テスト 1 本

`test_growth_test_holds_contract.py:247-274` の後へ, 1 functionだけ追加します. 予定名は `test_integrated_hold_inventory_projects_every_source_layer_exactly` です.

この 1 function で次を検査します.

- layer ID は production と test の exact 2 層.
- production items の check ID set は `HELD_CHECK_IDS` と exact equality.
- production status, ruling, count, digest, release target は source と exact equality.
- test items の node ID set と row payload は `GROWTH_TEST_HOLDS` と exact equality.
- test release env と token は source constants と exact equality.
- JSON render を再 parse すると inventory object と exact equality.
- human render に両層の全 ID, ruling, reason, release 方法が存在する.
- 同一 ID の重複と, source にない余分な ID を拒否する.

純増検出力: 各 source 層の単独契約が緑のままでも, 統合 inventory が一方の層, 1 item, または解除経路を落とす壊れ方をこの検査だけが捕捉します.

## 編集してはいけない file

- `orchestrator/tests/conftest.py`
- `orchestrator/tests/test_t793_publication_ledger.py`
- `orchestrator/publication/ledger.py`
- `orchestrator/campaign/freeze_verification_hold.py`
- `orchestrator/tests/test_campaign_import_invariant.py`
- `orchestrator/tests/test_real_repo_serialization.py`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-freeze-hold-residual/brief.md`
- frozen artifact, publication ledger, output registry の全 file
- `growth_test_holds.py:64-157` の既存 30 row bytes

## 検査境界

この段では file 編集も pytest も実行していません. pytest green は未確認です. 実行したのは read-only の digest command と限定 `rg` だけです.

実装後の現環境で許される確認は, 上記 digest command, human と JSON の両 CLI import, `git diff --check`, 変更 file 一覧の静的確認までとします. pytest と受入 wall は writable tmp を持つ後続段へ委ね, 走らせる場合は repository 規律どおり `tools/run_tests.py` 経由にします.