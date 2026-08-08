静的解析上、この wave は実装可能です。以下の行番号は現状基準です。pytest の成否は確認していません。

重要な判断は二つあります。

- committed silo evidence の実ファイルは、契約以外にも driver/policy/runtime の歴史 hash を意図的に保持しています（[test_silo_ladder_rung1_evidence.py:1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1235)）。したがって「実ファイルを一字も変えず full verify-result が通る」は current content rebinding と両立しません。追加テストでは committed evidence を基礎に、契約以外の binding だけ current に再束縛して g1 historical 性を単一理由で検査します。
- [env_contract_activation.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract_activation.py:406) が明記する通り serial 検査は state-hash 検査の冗長診断です。serial だけの変異は `SURVIVED` が正しく、実効 head pin の kill には serial/state-hash の対変異が必要です。

## 1. silo historical 解決化

### production 編集

[silo_ladder_rung1.py:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:32) に `Callable` を追加し、[同:3517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:3517) を次の三層へ分けます。

1. resolver 対を追加する。

   - `_resolve_current_contract_sha256(recorded_hash, *, expected_env_tag)`:
     `env_contract.lookup(expected_env_tag)` を呼び、exact `ExecutionEnvironmentContract`、env_tag、記録 hash と current hash の一致を検査する。
   - `_resolve_historical_contract_sha256(...)`:
     `env_contract.resolve_by_contract_sha256(recorded_hash, expected_env_tag=...)` を呼ぶ。返値が exact `GenerationEntry` であること、その `contract` の env/hash が記録値と一致することを再検査する。
   - [s8b_ratified_freeze.py:2769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_ratified_freeze.py:2769) と [s8b_floor_campaign.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:308) と同型にする。

2. 現在の本体を `_validate_bindings_with_resolver(document, repo, *, contract_resolver)` へ移す。

   - [silo_ladder_rung1.py:3540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:3540) で先に `binding["calibration"]["contract_sha256"]` を取り出す。
   - resolver を一度だけ `expected_env_tag="pegasus"` で呼ぶ。
   - exact contract 型、env、hash を再確認後、現行の path/file SHA/toolchain/source 検査へ渡す。
   - [同:3668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:3668) の捕捉対象に `env_contract.EnvContractError` を追加し、未知・never-active hash を uncaught exception ではなく `EvidenceFailure("binding", ...)` にする。

3. wrapper を分離する。

   - 既存 `validate_current_bindings()` は current resolver を渡す。署名は不変。
   - module-private `_validate_historical_bindings()` は historical resolver を渡す。外部公開 API は増やさない。
   - [main():4838–4847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:4838) の `verify-result` だけを `_validate_historical_bindings` に変更する。

境界は次の通りです。

| 経路 | resolver | 編集 |
|---|---|---|
| attest [1938–1945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:1938) | current lookup | 変更なし |
| correctness [3747–3759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:3747) | current lookup | 変更なし |
| producer `_binding` [4438–4462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:4438) | current lookup | 変更なし |
| `_collect_command` 生成直後 [4707–4734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:4707) | `validate_current_bindings` | 変更なし |
| `verify-result` [4838–4847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:4838) | historical | ここだけ変更 |

`resolve_by_contract_sha256` の ever-active 検査 [env_contract.py:690–695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:690) は変更しません。

### テスト編集

- [test_silo_ladder_rung1_evidence.py:1262–1272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1262):
  `lookup("pegasus")` を、記録 `contract_sha256` に対する `resolve_by_contract_sha256(..., expected_env_tag="pegasus")` に置換する。exact `GenerationEntry` を検査してから `entry.contract` と path/SHA/hash を比較する。`HISTORICAL_SILO_EVIDENCE_IDENTITY` の g1 値は変えない。

- [test_silo_ladder_rung1_driver.py:926](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_silo_ladder_rung1_driver.py:926) の binding テスト群直後に次を追加する。

  1. `test_verify_result_accepts_committed_g1_contract_when_current_is_g2`
     - committed evidence を deep-copy。
     - `driver._binding(ROOT)` で driver/policy/runtime 等の非 calibration binding を current に更新し、calibration block だけ committed g1 のまま残す。
     - current が `GENERATIONS["pegasus"][1]`、記録が g1 であることを事前 assert。
     - 同じ document が `validate_current_bindings` では拒否、historical wrapper では成功することを assert。
     - temp JSON に保存し `main(["verify-result", "--json", ...]) == 0` を確認する。raw/evidence gate は実物を通し、契約以外の歴史 byte driftだけをテスト入力から除く。

  2. `test_verify_result_rejects_registered_contract_not_ever_active`
     - production の `resolve_by_contract_sha256` を使う。
     - production `00000001.json` を leaf validator で検証した singleton head=1 snapshot を注入し、登録済み g2 を記録値にする。
     - historical binding failure の detail が `登録済み.*ever-active でない` で、`main()` が rc=1 を返すことを確認する。
     - current lookup への fallback が呼ばれたら即失敗する tripwire を置く。

- [test_silo_ladder_rung1_driver.py:2489–2498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_silo_ladder_rung1_driver.py:2489) の collect テストは、current validator の呼出回数を 1 とし、historical wrapper に tripwire を置いて producer 境界を固定する。

## 2. g2 活性化

### 発行と head 更新

親が head=1 の状態で、repo root から一度だけ実行します。

```bash
python3 tools/issue_env_contract_activation.py \
  --active linux-baremetal=1 \
  --active pegasus=2
```

[issue tool:179–221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/tools/issue_env_contract_activation.py:179) の出力から state hash を取得し、直後に [env_contract.py:373–376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:373) を次へ更新します。

```python
_ACTIVATION_HEAD_SERIAL: int = 2
_ACTIVATION_HEAD_STATE_SHA256: str = (
    "<issue tool が表示した activation_state_sha256>"
)
```

発行直後から定数更新までの間は lookup を呼ばず、テストも走らせません。確認事項は次です。

- 新規 path は `env_contract_activations/00000002.json` 一件だけ。
- serial=2、previous hash=`f7807285…`。
- active rows は linux-baremetal g1 と pegasus g2 (`1346c20b…`)。
- `00000001.json` の bytes は `INITIAL_BYTES` と一致したまま。
- record と head 定数を同一 commit に収容する。

### `test_env_contract_activation.py` の追従

| 現行位置 | 編集 |
|---|---|
| [37–46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:37) `INITIAL_*` | genesis の歴史 golden なので不変 |
| [178–198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:178) `_actual_serial2` | synthetic head2 helperとして不変 |
| [343–360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:343) initial test | rename。record1 bytes と singleton head1 を引き続き検証した後、実 directory が names `{00000001,00000002}`、head=2、current rows `(linux g1, pegasus g2)`、ever-active が linux g1/pegasus g1/g2 の3 hashであることを追加 |
| [451–465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:451) synthetic tail rollback | 既に非空 head rollback を精密に検査。変更なし |
| [1467–1475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1467) real g2 synthetic | 変更なし |
| [1477–1495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1477) production tail deletion | regex を後述の head 不一致へ精密化 |
| [1498–1541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1498) valid suffix | 実 head2 から serial3 no-op を作らない。temp authority に immutable record1 を置き、valid g2 record2 を create-only 追加し、source head を synthetic head1 に pin して head 不一致を検査 |
| [1544–1564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1544) constants pass-through | 定数を動的参照するので変更なし |
| [1567–1697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1567) authorization/ever-active/history | 既に synthetic head2。変更なし |
| [1700–1706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1700) registered-never-active | temp の singleton record1 authority と head1 pin を使う形へ変更。g2 の拒否理由を維持 |
| [1709–1748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1709) lazy/import/cache | dynamic または synthetic head1。変更なし |
| [1751–1799](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1751) fork cache | child の期待 hashを `GENERATIONS["pegasus"][1]` に変更 |
| [1802–1818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1802) cwd independence | env_tag のみ検査。変更なし |
| [1940–2155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1940) issuer tests | genesis→serial2 の unit test なので `INITIAL_BYTES`、期待 filename `00000002`、handoff serial2 は変更しない |

### `test_env_contract.py` の追従

- [270–282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:270): current Pegasus golden を g2 path `calibration-94a4b79fa31bba3c.json`、SHA `94a4b79f…` に更新し、g2 entry と同一 object を assert。
- [378–384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:378): expected active index を `{linux-baremetal: 0, pegasus: 1}` とし、Pegasus current が tail、g1 は current でないことを固定。
- [592–600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:592): g1 historical resolution は ever-active のためそのまま成功。変更なし。
- [618–621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:618): immutable record1 を leaf 検証した synthetic head1 snapshot で g2 never-active を検査する形へ変更。
- [839–881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:839): current `REGISTRY` だけでなく全 `GENERATIONS` を走査する。期待件数を全3 entry/required 2へ変更し、歴史 g1 の既知 self-inconsistent calibration を引き続き保持。
- [1124–1137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:1124): `test_pegasus_g1_contract_sha256_golden` に改名し、`lookup` でなく generation 0を使う。g1 hash は不変。
- [1140–1153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract.py:1140): g2 golden は変更なし。

### authority directory を参照する他の面

- [test_silo_ladder_rung1_driver.py:926–955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_silo_ladder_rung1_driver.py:926) は `glob("*.json")` で動的に両 record を含むため変更不要。
- [test_t419_probe_causality.py:1586–1627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_t419_probe_causality.py:1586) は directory pathspec の検査。`record_name` を `00000001.json/00000002.json` の2値 parameterize にして新 tail も明示的に固定する。
- production T419 の [lookup:3394–3410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/tools/pegasus/probes/t419_probe_causality.py:3394) と [dirty scope:3491–3505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/tools/pegasus/probes/t419_probe_causality.py:3491) は動的 current/directory参照なので変更不要。
- [test_t126_pegasus_tools.py:1428–1447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_t126_pegasus_tools.py:1428) は activation receipt を code identity から意図的に除外する契約。変更しない。
- [test_env_attestation.py:1276–1295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_attestation.py:1276) は g1/g2 両 calibration を列挙済み。変更不要。
- [conftest.py:43–96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/conftest.py:43) は任意契約用 singleton synthetic authority。head=1 のままにする。

## 3. [T-660] head=2 検出力

[test_env_contract_activation.py:1490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:1490) は次へ絞ります。

```python
match=(
    r"activation authority 検証失敗: "
    r"activation head (?:serial|state hash) 不一致"
)
```

### 空 chain node

追加するべきです。現在、空 chain の exact 理由を直接 pin する node はありません。production tail deletion が head=1 で空 chain に mask されていた履歴を、head=2 の非空 rollback test と分離できます。

[test_env_contract_activation.py:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:451) の直前に `test_empty_chain_rejection_is_distinct_from_head_pin_mismatch` を置き、`validate_activation_records(())` が exact `activation record chain が空` になることだけを検査します。production gate は増やさず、既存 [leaf:355–356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract_activation.py:355) の理由を固定するテストです。

### DW-O19

統合 candidate commit 後・clean tree で、repo 外に次の spec を置きます。

```json
{
  "schema": "izanagi-dev-wave-mutation-spec/v1",
  "estimated_run_seconds": 600,
  "timeout_seconds": 3600,
  "hang_timeout_seconds": 300,
  "mutations": [
    {
      "id": "T660-serial-diagnostic",
      "category": "negative",
      "replacements": [{
        "file": "orchestrator/campaign/env_contract_activation.py",
        "old": "    if terminal_serial != expected_head_serial:",
        "new": "    if False and terminal_serial != expected_head_serial:"
      }],
      "expected_nodes": [],
      "expected_status": "SURVIVED",
      "hang_risk": false
    },
    {
      "id": "T660-effective-head-pin",
      "category": "negative",
      "replacements": [
        {
          "file": "orchestrator/campaign/env_contract_activation.py",
          "old": "    if terminal_serial != expected_head_serial:",
          "new": "    if False and terminal_serial != expected_head_serial:"
        },
        {
          "file": "orchestrator/campaign/env_contract_activation.py",
          "old": "    if terminal_hash != expected_head_state_sha256:",
          "new": "    if False and terminal_hash != expected_head_state_sha256:"
        }
      ],
      "expected_nodes": [
        "orchestrator/tests/test_env_contract_activation.py::test_production_loader_rejects_tail_deletion_with_source_head_unchanged"
      ],
      "expected_status": "KILLED",
      "hang_risk": false
    }
  ]
}
```

親の実行形は次です。

```bash
python3 -m orchestrator.campaign.queue_state

T660_SPEC=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/t660-mutation-spec.json
T660_LEDGER=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/t660-mutation-ledger.json
T660_SPEC_SHA="$(sha256sum "$T660_SPEC" | awk '{print $1}')"

python3 tools/mutation_harness.py \
  --repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation \
  --spec "$T660_SPEC" \
  --expected-spec-sha256 "$T660_SPEC_SHA" \
  --out "$T660_LEDGER" \
  --runner-mode dispatch \
  --detached \
  -- python3 tools/run_tests.py --force-dispatch \
  orchestrator/tests/test_env_contract_activation.py::test_production_loader_rejects_tail_deletion_with_source_head_unchanged \
  -q -rf
```

serial-only が緑なのは state-hash gate が同じ rollback を拒否するためです。これを kill と報告してはいけません。対変異だけが実効 head pin の kill 証拠です。終了後は harness の復元に加え、`git diff --exit-code`、`git status --short`、HEAD blobとの byte一致を確認します。

## 4. floor 再発行のユーザー逐語案

この手番は activation/silo の candidate commit 後、受入前に行います。

```bash
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation

test -t 0
test -z "$(git status --porcelain)"

python3 -m orchestrator.campaign.t080_freeze_migration verify \
  --path output/t080-migration/legacy-freeze-repin.receipt.json
```

出力が `state="active-valid"`、`refusals=[]`、`t080_freeze_migration_observation` が object であることを確認します。その後:

```bash
FLOOR_BACKUP=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/floor_protocol.pre-g2.json

test ! -e "$FLOOR_BACKUP"
test -f output/s8b-freeze/floor_protocol.json
mv -- output/s8b-freeze/floor_protocol.json "$FLOOR_BACKUP"

python3 -m orchestrator.campaign.s8b_floor_campaign \
  freeze-protocol \
  --confirm-user-freeze
```

CLI 形は [s8b_floor_campaign.py:3519–3555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:3519) と一致します。非0なら削除・上書き・commitをせず、その場で停止します。

成功後の照合:

```bash
python3 - "$FLOOR_BACKUP" output/s8b-freeze/floor_protocol.json <<'PY'
import hashlib
import json
import pathlib
import sys

old_path, new_path = map(pathlib.Path, sys.argv[1:])
old = json.loads(old_path.read_bytes())
new_raw = new_path.read_bytes()
new = json.loads(new_raw)

assert type(old) is dict and type(new) is dict
assert len(old) == len(new) == 18
assert set(old) == set(new)
changed = {key for key in old if old[key] != new[key]}
assert changed == {"contract_sha256"}, changed
assert old["contract_sha256"] == "e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01"
assert new["contract_sha256"] == "1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c"
assert len(new_raw) == 774
print("floor_sha256=" + hashlib.sha256(new_raw).hexdigest())
print("unchanged_keys=17 changed_keys=contract_sha256")
PY

git diff --check -- output/s8b-freeze/floor_protocol.json
git diff -- output/s8b-freeze/floor_protocol.json
git add -- output/s8b-freeze/floor_protocol.json
test "$(git diff --cached --name-only)" = "output/s8b-freeze/floor_protocol.json"

git commit --only \
  -m "[T-657] reissue floor protocol for pegasus g2" \
  -m "AI-Agent: none" \
  -- output/s8b-freeze/floor_protocol.json
```

再発行後、Codex が行う追従は次です。

- [test_frozen_artifacts.py:45–46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_frozen_artifacts.py:45): path/key/countを変えず、line 46 の SHA値だけを新 file SHAへ更新。[同:139–153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_frozen_artifacts.py:139) の23件/keysetは不変。
- [test_s8b_protocol_builder.py:108–119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_s8b_protocol_builder.py:108) と [同:401–417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_s8b_protocol_builder.py:401): 新 SHAへ更新。byte length 774 は不変。
- [test_s8b_floor_campaign.py:3245–3254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_s8b_floor_campaign.py:3245): protocol SHA、新 calibration SHA `94a4b79f…`、g2 contract SHA `1346c20b…` へ更新。
- selector prediction/journal、歴史 seal、committed silo identity、g1 contract golden は更新しない。

## 5. commit列と受入順序

1. **A: silo commit**  
   resolver分離、verify-result routing、silo testsのみ。head=1でも成立する独立変更。

2. **B: activation handoff-anchor commit**  
   親が tool で作った `00000002.json`、head定数、activation/env-contract/T660テスト追従を同一 commit にする。`00000001.json` 不変を確認する。この commit 単独は main へ land しない。

3. **ユーザー C: floor artifact commit**  
   B の上で逐語手順を実施する。これにより `git archive HEAD` や tmp clone を使うテストも g2 authority と g2 floor の両方を見られる。

4. **D: integration candidate commit**  
   FROZEN_MANIFEST、floor golden、siloを含む残りの追従を収容する。HEAD/archiveを読むテストがあるため、受入前に candidate commit が必要。修正した場合は新 candidate commitを作り再走する。

5. **受入・変異・全走後、D tipだけを main に一度で land**  
   BやCだけを mainへ先行取り込みしない。main ref は旧green tipから最終tipへ一度に進むため、壊れた時間窓を作らない。

受入順序案:

1. identity/activation:
   `test_env_contract_activation.py`、`test_env_contract.py`、`test_env_attestation.py`
2. silo:
   `test_silo_ladder_rung1.py`、`test_silo_ladder_rung1_driver.py`、`test_silo_ladder_rung1_evidence.py`
3. floor/oracle:
   `test_s8b_protocol_builder.py`、`test_s8b_floor_contract.py`、`test_s8b_floor_campaign.py`、`test_frozen_artifacts.py`、`test_s8b_prediction_runner.py`、`test_s8b_ratified_freeze.py`、`test_s8b_ratified_verify.py`、oracle系、`test_pegasus_floor_tools.py`、`test_campaign.py`
4. related:
   `test_t419_probe_causality.py`、`test_t126_pegasus_tools.py`
5. DW-O19、復元後のT660 node再走
6. `python3 tools/run_tests.py --force-dispatch -q -rf` 全走
7. `python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`
8. 最終commit後 `python3 tools/check_ai_provenance.py`

## 6. リスク表

| リスク | 壊れうる面 |
|---|---|
| historical resolverを本体へ直書きして producerまで歴史化 | silo producer [1942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:1942)、[3758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:3758)、[4439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:4439)、collect [4734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:4734) |
| `EnvContractError` を捕捉しない | verify-result が structured rejectionでなく traceback化する [3668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:3668) |
| recordとhead定数が分離 | authority loader全体が fail-closed [env_contract.py:519–532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:519) |
| issue tool後、head更新前にlookup | valid suffix injectionとして全current consumerが一時拒否 |
| current g1仮定の取り残し | `test_env_contract.py:270,378,618,839,1124`、activation test `343,1498,1700,1751` |
| record2をruntime bindingへ含め忘れ | [silo_ladder_rung1.py:254–275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/silo_ladder_rung1.py:254)、driver test 926 |
| T419/T126を同じ意味で変更 | T419はdirectory dirty scope [3491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/tools/pegasus/probes/t419_probe_causality.py:3491)、T126はrecord除外が正契約 [1443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_t126_pegasus_tools.py:1443) |
| floor artifactだけ更新しpinを残す | frozen manifest 45–46、builder 118/413、floor e2e 3245–3254 |
| floor再発行失敗時に自動復旧して証拠を消す | writerは失敗成果物を自動削除しない設計 [s8b_floor_campaign.py:660–679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:660) |
| g2 floorが未commitのままcloneテスト | prediction HEAD blob検査 [s8b_prediction_runner.py:1564–1570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_prediction_runner.py:1564)、floor e2e clone |
| serial-only変異をkillと誤報 | state hash [env_contract_activation.py:412–416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract_activation.py:412) がmaskする |
| user commitにAI変更が混入 | dirty stage5 tree。Bを先にcommitし、Cで staged path exact一件を検査する |
| mainへ中間commitを個別land | g2 activationと旧floorの壊れた窓。最終tipだけを一度でlandする |

## 総括

- silo は shared validation core＋current/historical resolver 対にし、verify-resultだけを historical 化する。
- producer三経路と collect自己検証は current のまま固定する。
- `00000002.json` は親が発行toolで作り、head=2定数と同一commitへ収容する。
- head=1依存テストは、production期待をg2へ、never-active検査をsynthetic head1へ分離する。
- floorはactivation commit後にユーザーが再発行し、17 key不変を照合して単独commitする。
- 最重要リスクは、serial-only変異が冗長state-hashにmaskされる点と、中間commitの先行landである。
- 未確定点は、literal committed silo fileのfull pass要求が既存current byte rebindingと両立しない点である。