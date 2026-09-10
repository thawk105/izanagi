親 brief の機能方針は妥当です。ただし fixture 出力を固定する既存 golden が見つかったため、3 file だけでは関連テストが赤になります。段 4 では、機械的な pin 更新 2 file を scope に含める裁定が必要です。

## 実装プラン

### 1. `orchestrator/campaign/reflux_formal_consumer.py`

- 現在の [33〜35 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:33) は `model` の terminal 定数を import していない。

  変更後:

  ```python
  from . import reflux_origin_ledger as ledger
  from . import trigger_gate_binding
  from .model import STAGE_ABORT, STAGE_COMMIT
  from .reflux_origin_artifacts import (
  ```

- 現在の [861 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:861):

  ```python
  _require(FormalReasonCode.FC07, terminal.get("kind") == "commit")
  ```

  変更後:

  ```python
  _require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_COMMIT)
  ```

- 現在の [867 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:867):

  ```python
  _require(FormalReasonCode.FC07, terminal.get("kind") == "abort")
  ```

  変更後:

  ```python
  _require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_ABORT)
  ```

`_validate_wal_outcomes()` の他の判定式、FC07、`_wal_field()` は変更しない。

### 2. `orchestrator/tests/reflux_origin_fixture_builder.py`

- 現在の [22 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/reflux_origin_fixture_builder.py:22) の後へ追加:

  ```python
  from orchestrator.campaign.model import STAGE_ABORT
  ```

- 現在の [375〜381 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/reflux_origin_fixture_builder.py:375) は root `kind` と root payload fields を返している。

  変更後:

  ```python
  {
      "variant": "fixture-v",
      "stage": STAGE_ABORT,
      "env_tag": "fixture-env",
      "ts": 0,
      "payload": {
          "build_attempt_id": build_attempt_id,
          "candidate_attributable": True,
          "truncated": False,
          "witness_class_sha256s": [_CONSTRAINT_SHA256],
      },
  },
  ```

外枠だけを production の `WalRecord` 形状へ移す。witness fields は P1 の制約を検査する合成 payload であり、本番 producer の実在を意味しない。

### 3. `orchestrator/tests/test_reflux_formal_consumer.py`

- 現在の [14〜22 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:14) に追加:

  ```python
  from orchestrator.campaign import model as M
  ```

- 現在の [861〜868 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:861) の commit 合成 record を次へ変更:

  ```python
  wal = [
      trigger,
      {
          "variant": "fixture-v",
          "stage": M.STAGE_COMMIT,
          "env_tag": "fixture-env",
          "ts": 0,
          "payload": {
              "build_attempt_id": "placeholder",
              "verify_configs": ["s2", "legacy"],
          },
      },
  ]
  ```

  これにより stage は正しく、verify 順序だけが不正な FC07 テストになる。

- 現在の [878 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:878):

  ```python
  wal[-1]["witness_class_sha256s"] = []
  ```

  変更後:

  ```python
  wal[-1]["payload"]["witness_class_sha256s"] = []
  ```

- 現在の [902 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:902) も同様に:

  ```python
  wal[-1]["payload"]["witness_class_sha256s"] = [second_class]
  ```

- FC07 群の開始点である現在の [842 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:842) の前へ、次の 2 test を追加する。

負例の署名は、旧 root `kind` を FC07 が禁止することを名前に明記する:

```python
def test_fc07_rejects_legacy_root_kind_terminal_shape(case: _Case) -> None:
    trigger = _projection_records(case, 0)[0]
    legacy = {
        "kind": "abort",
        "build_attempt_id": "placeholder",
        "candidate_attributable": True,
        "truncated": False,
        "witness_class_sha256s": [
            case.records[0]["physical_result"]["constraint_sha256"]
        ],
    }
    _rewrite_wal(case, 0, [trigger, legacy])
    _assert_reason(case, C.FormalReasonCode.FC07)
```

この record は resolver の root attempt fallback により FC05B を通り、valid trigger により FC05C を通るが、terminal に `stage` がないため FC07 で拒否される。

通る正例:

```python
def test_fc07_accepts_production_commit_terminal_shape(case: _Case) -> None:
    record = copy.deepcopy(case.records[0])
    record["physical_result"] = {
        "build_attempt_id": record["physical_result"]["build_attempt_id"],
        "outcome": "accepted",
        "constraint_sha256": None,
    }
    _set_record(case, 0, record)
    _set_member(case, 0, outcome="accepted", constraint_sha256=None)

    trigger = _projection_records(case, 0)[0]
    terminal = {
        "variant": "fixture-v",
        "stage": M.STAGE_COMMIT,
        "env_tag": "fixture-env",
        "ts": 0,
        "payload": {
            "build_attempt_id": "placeholder",
            "verify_configs": ["legacy", "s2"],
        },
    }
    _rewrite_wal(case, 0, [trigger, terminal])

    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    assert result.reason_code is C.FormalReasonCode.P6_UNAVAILABLE
```

新しい terminal exact-key gate、型 gate、helper、reason code は追加しない。

### 4. 段 4 の裁定後に必要な既存 pin 更新

これは新しい検査や台帳ではなく、必須 fixture 変更に伴う既存 pin の同期である。

#### `orchestrator/tests/reflux_origin_fixture_baseline.json`

現在の [15〜17 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/reflux_origin_fixture_baseline.json:15):

```json
"byte_length": 909,
"canonical_sha256": "7d5ce12b170cf50335682719016708275a75aa262cca247345815cb93c9baaac"
```

変更後:

```json
"byte_length": 975,
"canonical_sha256": "271323c60ad2af8b4034872096d5c1c5066f26c6c85689252dd5ce762ddd3bc6"
```

現在の [25 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/reflux_origin_fixture_baseline.json:25) を変更:

```json
"canonical_sha256": "631a5fa04f9cc1a5442c5660410bb27b1ad03ef76f5da3fe3d4603ac5577c82c"
```

`build_result_evidence_record.byte_length` は 1848 のまま。

#### `orchestrator/tests/test_reflux_result_evidence.py`

現在の [24〜27 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_result_evidence.py:24) を、in-memory で再計算した次の値へ更新:

```python
_RECORD_RAW_GOLDEN = "631a5fa04f9cc1a5442c5660410bb27b1ad03ef76f5da3fe3d4603ac5577c82c"
_LEDGER_EVIDENCE_DIGEST_GOLDEN = "631a5fa04f9cc1a5442c5660410bb27b1ad03ef76f5da3fe3d4603ac5577c82c"
_OUTER_SALTED_COMMITMENT_GOLDEN = "5aaf3851fe1c8b55ee009a35b9f319cc1feee93d45df7a99c68a56da8bba6cf7"
_WRONG_DOMAIN_PREFIXED_RAW_GOLDEN = "515e7f7ca39461903b9d3291dd010b9576732ff2674f1b29e677aba6032399c3"
```

[150 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_result_evidence.py:150) の `len(actual) == 1848` は変更不要。

## P1〜P4 の採否

- P1: 採用。`orchestrator/campaign/` の exact identifier 検索では `candidate_attributable` と `witness_class_sha256s` は consumer の [870〜877 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:870) にしかない。production abort は [pipeline.py:1071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/pipeline.py:1071) と [pipeline.py:1206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/pipeline.py:1206) で別 payload を作る。`reflux_source_closure.py:85-86` も `wal.abort.payload.witnesses` という別名である。producer 新設は scope 外とし、rejected 本番 projection が FC07 で止まる限界を残す。
- P2: 採用。[_wal_field():821-825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:821) の撤去は attempt、verify、witness 全体の受理集合を狭める別変更になる。root `kind` 旧形状は `stage` 不在で拒否できるため、fallback は触らない。
- P3: 採用。[model.py:28-29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/model.py:28) の `STAGE_COMMIT` と `STAGE_ABORT` を使う。
- P4: 採用。D1665 型の exact-key/type gate は [_wal_trigger():726-764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:726) に限定された先行裁定である。terminal に同等 gate を新設せず、既存 FC07 の 2 判定だけを直す。

## 走らせる test file 集合

`orchestrator/tests/` で `reflux_formal_consumer` を grep すると直接参照は次の 3 file:

- `test_reflux_formal_consumer.py`
- `test_reflux_origin_client.py`
- `test_trial_registry.py`

変更する fixture builder の直接 importer も含めた保守的な参照閉包は次の 10 file:

- `test_p3_autonomous_workload_trial.py`
- `test_reflux_formal_consumer.py`
- `test_reflux_origin_artifacts.py`
- `test_reflux_origin_binding.py`
- `test_reflux_origin_client.py`
- `test_reflux_origin_fixture_builder.py`
- `test_reflux_origin_topology.py`
- `test_reflux_result_evidence.py`
- `test_reflux_source_closure.py`
- `test_trial_registry.py`

親はこの 10 file を `tools/run_tests.py` 経由で実行すべきである。この段では pytest は実行していない。

## 親 brief との食い違い

- pin 閉包の説明は一部食い違う。3 source file 自体は `FROZEN_MANIFEST` に無いことを確認したが、fixture 出力には既存 pin がある。
  - `reflux_origin_fixture_baseline.json:15-25` が ordered WAL projection と result evidence の hash／length を固定。
  - `test_reflux_result_evidence.py:24-27` が result bytes と派生 commitment を literal golden で固定。
  - したがって「`source_wal_ref.sha256` が自己計算されるため内部整合する」だけでは関連テストは通らない。
- commit producer の意味は確認できたが、brief の行表現は厳密ではない。payload は `pipeline.py:1762-1786`、実際の production `wal.log(... STAGE_COMMIT ...)` は `pipeline.py:1796-1800`。qualification sink は `1802-1806`。
- fixture の `_wal_records()` は brief の `360-379` ではなく、現物では `362-382`、旧 terminal 本体は `375-381`。
- それ以外の主要事実は現物と一致した。現在の HEAD も brief 記載の `d19d2182fbc324f67b47f600be70136d6503aa59` で、tracked worktree は clean だった。

## 総括

- P1: 採用。rejected 本番 projection の既知 FC07 限界は残す。
- P2: 採用。`_wal_field()` は変更しない。
- P3: 採用。`STAGE_COMMIT`／`STAGE_ABORT` を import して使う。
- P4: 採用。terminal exact-shape gate は追加しない。
- core 修理は consumer 2 判定、fixture terminal 外枠、consumer test の更新と正負 2 test。
- 親が段 4 で裁定すべき残点:
  - fixture 出力変更に必須な `reflux_origin_fixture_baseline.json` と `test_reflux_result_evidence.py` の既存 pin 更新を scope に含めるか。推奨は含める。
  - 3 file 固定を優先して pin を更新しない場合、少なくとも fixture baseline test と result-evidence golden tests が既知の赤になることを受け入れるか。