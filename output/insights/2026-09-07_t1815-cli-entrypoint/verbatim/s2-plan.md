## 根本原因

親の仮説 P1 は確認できた。

1. `s8c_preregistration.py:36-38` は、ファイルパス直接起動時に `sys.path` と `__package__` を補うだけで、実行中の `__main__` module を canonical 名 `orchestrator.campaign.s8c_preregistration` へ登録していない。
2. `-m` でも問題は残る。CPython 3.10 の `runpy` は対象コードを `sys.modules["__main__"]` の namespace で、`__name__="__main__"` として実行するためである。[CPython 3.10 `runpy.py`](https://github.com/python/cpython/blob/3.10/Lib/runpy.py#L161-L185)
3. CLI 評価中、`s8c_preregistration.py:1775-1777` が canonical 名で評価器を import する。評価器は `s8c_preregistration_evidence.py:18` の相対 import で core を要求するため、canonical core がもう一度生成される。
4. 評価器は canonical core の `PredicateResult` を返す（`s8c_preregistration_evidence.py:1473-1483`）。一方、`_normalize_predicate_results` は `__main__.PredicateResult` を要求する（`s8c_preregistration.py:1739-1755`）。別クラスなので `isinstance` が偽になり、`predicate-result-type` が発生する。
5. それを `s8c_preregistration.py:1850-1856` の広い `except Exception` が `ERROR / evaluator-exception` 12 件へ変換する。

したがって、壊れているのは厳格な型検査ではなく module identity である。

`s8c_gate_report.py` の直接起動は別の単純な欠陥で、`s8c_gate_report.py:16` の相対 import より前に `__package__` bootstrap が存在しない。このため module body の初期化中に `ImportError` となり、`_main()` の JSON 例外処理にも到達しない。

## 修正プラン (file:line)

### `orchestrator/campaign/s8c_preregistration.py:36-39`

現在の bootstrap を次で置換する。

```python
if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

if __name__ == "__main__":  # pragma: no cover - CLI execution
    sys.modules["orchestrator.campaign.s8c_preregistration"] = sys.modules[__name__]
```

重要点は、canonical 登録を `if __package__ in {None, ""}` の外に置くこと。これにより、

- ファイルパス直接起動: path/package bootstrap 後に `__main__` を canonical 名へ登録
- `-m` 起動: `__package__` は既に設定済みでも、`__name__ == "__main__"` により登録
- 通常 import: `__name__` が canonical 名なので追加処理なし

となる。

直接起動時は `orchestrator.campaign` package の `s8c_preregistration` attribute が設定されない可能性があるが、CPython 3.10 の `IMPORT_FROM` は package attribute lookup が失敗すると、`package.__name__ + "." + requested_name` を構成して `sys.modules` から取得する。したがって、評価器の `from . import s8c_preregistration as core` は上記登録だけで同じ module object を取得できる。[CPython 3.10 `ceval.c` の `import_from`](https://github.com/python/cpython/blob/3.10/Python/ceval.c#L5644-L5673)

`setdefault` は採らない。既存の別 instance が canonical key に入っていた場合に二重実体化を保存してしまうため、CLI の実行 instance を明示的に代入する。

### `orchestrator/campaign/s8c_gate_report.py:10-16`

`sys` import と、相対 import より前の bootstrap を追加する。

```python
import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import s8c_preregistration as _prereg
```

gate report 自身の canonical alias は不要である。直接起動でも、ここから import される core は通常の canonical import となり、gate report を逆 import する経路もない。

### 採らない案

- `_normalize_predicate_results` の `isinstance`、12 件検査、ID 集合検査、evidence 型検査は一切変更しない。
- duck typing、class 名比較、`__module__` 無視などの緩和は採らない。
- `DECIDER_VERSION` は `s8c-decider/v9` のままにする。library 経路の受理論理は変化せず、CLI を同じ論理へ接続し直すだけである。
- `_default_registry_results` の例外握り潰しは本 wave では変更しない。
- 条件凍結成果物と `docs/phase3-8c-preregistration.md` は変更しない。
- bottom guard から canonical module を再 import して `main()` を呼ぶ thin runner 案は採らない。module bodyを二度実行して別クラスを残すうえ、新しい入口または再実行制御が必要になり、今回の identity 修正より広い。
- `exec`/子 process で `-m` へ転送する案も、process/error/signal semantics を変え、そもそも現行 `-m` 自身が同じ欠陥を持つため不採用。

## 新設テストの設計

新規 `orchestrator/tests/test_s8c_cli_entrypoints.py` を追加する。既存 `test_s8c_gate_report.py:434-461` は `-m` の引数エラー経路（rc=2）だけを検査しており、正常な評価経路、core の型 identity、ファイルパス直接起動を観測しない。したがって既存テストは変更せず、実プロセス入口の同値性を新しい integration test file に分離する。これは重複ではなく別 surface の検査である。

予定構成は次のとおり。

- `:1-18`: `json`、`subprocess`、`sys`、`Path`、`pytest` と repo root、絶対 CLI path を定義。
- `:20-34`: in-process report から `(id, status.value, reason_code)` を取り出す helper。
- `:36-48`: `prereg-path`、`prereg-module`、`gate-path`、`gate-module` の4ケースを parameterize。
- `:51-95`: 実プロセス実行と library report との比較。
- 末尾: 指定された自走 harness。

中心部分は次の形にする。

```python
@pytest.mark.parametrize(
    ("kind", "invocation"),
    [
        pytest.param("prereg", "path", id="prereg-path"),
        pytest.param("prereg", "module", id="prereg-module"),
        pytest.param("gate", "path", id="gate-path"),
        pytest.param("gate", "module", id="gate-module"),
    ],
)
def test_cli_entrypoint_matches_library_report(
    kind: str,
    invocation: str,
) -> None:
    expected = P.activation_report_at(_ROOT, "HEAD")

    # core-blob-mismatch 同士の比較で恒真化しないよう、評価 commit と
    # 実行中 core bytes が一致することを先に要求する。
    assert (
        P.read_blob_at(_ROOT, expected.commit, P.CORE_MODULE_PATH)
        == _CORE_PATH.read_bytes()
    )

    if kind == "prereg":
        target = (
            [sys.executable, str(_CORE_PATH)]
            if invocation == "path"
            else [
                sys.executable,
                "-m",
                "orchestrator.campaign.s8c_preregistration",
            ]
        )
        command = [
            *target,
            "check",
            "--json",
            "--repo-root",
            str(_ROOT),
            "--commit",
            expected.commit,
        ]
    else:
        target = (
            [sys.executable, str(_GATE_PATH)]
            if invocation == "path"
            else [
                sys.executable,
                "-m",
                "orchestrator.campaign.s8c_gate_report",
            ]
        )
        command = [
            *target,
            "--repo-root",
            str(_ROOT),
            "--commit",
            expected.commit,
        ]

    completed = subprocess.run(
        command,
        cwd=_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    expected_predicates = [
        (item.id, item.status.value, item.reason_code)
        for item in expected.predicates
    ]

    if kind == "prereg":
        actual_predicates = [
            (item["id"], item["status"], item["reason_code"])
            for item in payload["predicates"]
        ]
        actual_effective = payload["effective"]
    else:
        actual_predicates = [
            (item["id"], item["status"], item["reason_code"])
            for item in payload["predicates"]["results"]
        ]
        actual_effective = payload["source"]["effective"]

    assert completed.stderr == ""
    assert actual_predicates == expected_predicates
    assert actual_effective is expected.effective
    assert completed.returncode == (0 if expected.effective else 1)

    if kind == "gate" and invocation == "path":
        assert completed.returncode == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
```

predicate status や reason の literal は置かず、同じ resolved commit の `activation_report_at` を oracle にする。gate direct の rc=1 だけは、brief が指定する現行不変条件「effective=false」と直接起動の公開契約を検査するため意図的に固定する。

現行 HEAD では恒真にならない。

- `prereg-path` と `prereg-module`: library の混合 status/reason に対し、実プロセスは12件すべて `ERROR / evaluator-exception` なので predicate 比較で失敗する。
- `gate-path`: stdout が JSON になる前に相対 import traceback で終了するため `json.loads(completed.stdout)`、stderr 空検査の双方で失敗する。
- `gate-module`: 現行でも通る対照ケースとなる。

## 波及と焦点走対象

静的な consumer は次のとおり。

- `s8c_preregistration_evidence.py:18,1473-1483,3368-3498`: core 型を生成する直接 consumer。今回の修正対象となる identity edge。
- `s8c_gate_report.py:16,111-117`: activation report の射影 consumer。
- `p3_autonomous_workload_trial.py:52,954-973,5163-5166`: `effective_at` と capability 再検証。
- `trial_registry.py:43,4106-4137,5747-5779,6462-6465`: capability 型検査、発効再評価、acceptance。
- `campaign_lock.py:49-112`: 現行62-path enforcement source closure。core は `:64` に含まれる。
- `campaign_lock.py:117-142`: pre-T733 の歴史的24-path closureにも core が `:132` に含まれる。

P3 の「両 file が enforcement source」という前提は一部反証された。`s8c_preregistration.py` は含まれるが、`s8c_gate_report.py` は現行 closure に含まれない。

影響は以下。

- core bytes の SHA-256 と `ActivationReport.core_module_blob_sha256` は新 commit に対応して変わる。
- commit 前は `contract_loader_binding.py:348-382` が disk/HEAD 不一致を `contract-loader-drift` として拒否する。また core 自身も `s8c_preregistration.py:1895-1904` で `core-blob-mismatch` になる。焦点走は変更を commit した後に行う必要がある。
- enforcement path 集合、順序、schema、検証論理は変わらない。新規 binding の digest 値だけが新 commit の bytes に追随する。
- 歴史的 binding は記録 commit の blob に対して検証されるので、歴史的受理 grammar は変わらない。
- `test_t671_source_binding.py:37-110,235-264,387-397` は core を exact closure と mutation face として検査している。path 集合の期待値変更は不要。
- `test_artifact_admission.py:46-115` は pre-T733/E1 closure に core path を列挙している。bytes literal は持たず、path 集合も不変なので期待値変更は不要。
- gate report を closure に追加すると62-path集合を変え、受理面を広げるため、本 wave では行わない。

`git grep` から得た焦点走対象 file 集合は次のとおり。

- `orchestrator/tests/test_s8c_cli_entrypoints.py`（新規）
- `orchestrator/tests/test_s8c_gate_report.py`
- `orchestrator/tests/test_s8c_preregistration_core.py`
- `orchestrator/tests/test_s8c_preregistration_invariant.py`
- `orchestrator/tests/test_s8c_preregistration_predicates.py`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py`
- `orchestrator/tests/test_reflux_origin_binding.py`
- `orchestrator/tests/test_trial_registry.py`
- `orchestrator/tests/test_t671_source_binding.py`
- `orchestrator/tests/test_artifact_admission.py`
- `orchestrator/tests/test_ccbench_spawn_sites.py`

`growth_test_holds.py`、`test_growth_test_holds_contract.py`、`test_hold_inventory.py`、`test_real_repo_serialization.py` にも名前上の grep hit はあるが、既存 s8c test の nodeid/metadata 参照であり、変更 production module の実行 consumer ではないため上の焦点集合から除外する。

## 不確実な点・親へ返す判断

- 親 brief の P3 は「両 file が enforcement source」の一点だけ訂正が必要。gate report を closure に追加して整合させるのではなく、「core のみ bound」と記録を直すべきである。
- CPython 3.10 の `IMPORT_FROM` fallback を前提にした最小修正である。他 Python 実装まで保証対象なら package attribute を明示設定する別設計が必要だが、今回指定された CPython 3.10 では不要。
- 受理集合を変える箇所は静的には見つからなかった。変更されるのは CLI 到達性、module identity、commitごとの source digest 値であり、predicate/conjunction/lock grammar ではない。
- read-only 制約に従い、pytest・CLI 回帰テストは実走していない。結果を緑とは報告しない。

## 総括

修正は production 2ファイルの bootstrap と、新規実プロセス test 1ファイルに限定できる。core を `__main__` と canonical 名の同一 object として登録し、gate report に直接起動 bootstrap を加えることで、直接パス・`-m`・library import の3形式を同じ厳格な判定経路へ収束させられる。`DECIDER_VERSION`、凍結成果物、規律2の検査、受理集合は変更しない。