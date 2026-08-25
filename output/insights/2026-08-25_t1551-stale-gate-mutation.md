# [T-1551] stale registry 検査の変異 matrix と新旧両走

wave: `worktree-dev-wave-t1551-stale-registry-gate`
統合 commit: `15db216bd64e82805397ba31e42243bcfe7074f0`
変更前 HEAD: `c3c5ca0ab9cfd733f2a26eea0154e43936960bd4`

## 一次資料の所在

repo の外に置いた。job dir は job の削除で消えるため durable 側へ複製した。

| file | sha256 |
|---|---|
| `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1551-stale-registry-gate/mutation-ledger-final.json` | `8344ce3c3bef2803a5ffa5ceef9a89affccd0ba45760b69ad23caa7025eeda87` |
| `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1551-stale-registry-gate/mutation-ledger-prechange.json` | `43759ae473daf637152901cd86dc7f46f1571b154329845cd019149aa52f326f` |

spec は同 dir の `spec-final.json` / `spec-old.json`。
spec 本体は `output/insights/2026-08-25_t1551-mutation-spec-final.json` にも置く。

前 wave の一次資料 `mutation-ledger-mut5-survived.json` も同じ場所の別 wave dir
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-flaky-quarantine/`) にある。

## 本走 (統合 commit `15db216b`)

runner argv: `python3 tools/run_tests.py --force-dispatch -rf` +
`test_flaky_test_holds_contract.py test_pytest_collection_config.py`
`test_real_repo_serialization.py test_run_tests_task_run.py`
runner-mode: `dispatch`。

```
summary: {"KILLED": 10, "MISMATCH": 0, "PARSE_ERROR": 0, "SURVIVED": 0, "TIMEOUT": 0,
          "completed": 10, "matching": 10, "recorded": 10, "registered": 10}
baseline: PASSED (failed_nodes = [])
```

| 変異 | 置換 | 落ちた node |
|---|---|---|
| t1551.m01 | 委譲条件を旧 `numprocesses` 形へ戻す | 3 |
| t1551.m02 | serial 経路の callsite を `if False and` | 1 |
| t1551.m03 | `get_plugin("dsession")` を `object()` にして常に委譲 | 2 |
| t1551.m04 | `if missing:` を `if False and missing:` | 3 |
| t1551.m05 | 絞り込み判定を無効化 (過剰拒否の正例) | 10 |
| t1551.m06 | shard guard を無効化 (過剰拒否の正例) | 1 |
| t1551.m07 | `if missing:` を `if len(missing) == 1:` | 1 |
| t1551.d01 | controller hook の callsite を `if False and` | 1 |
| t1551.d02 | `workers.add(worker_key)` を落とす | 1 |
| t1551.d03 | `len(finished) >= expected` を `>` | 2 |

### 帰属の但し書き

- **t1551.m05 は単一理由ではない。** 10 node を落とす過剰決定であり、
  受理集合を広げる変異ではなく、承認外の過剰拒否を検出する正例として登録した。
  kill 件数を配線の証明として数えない。
- **d01 / d02 / d03 は diagnostic sensitivity pin である。**
  実 xdist では各 worker が同じ入力を拒否するため、controller 側の再検査は
  stale の拒否については冗長である。これらの kill を「受理集合を守った」と数えない。
  ただし同じ hook が行う hold 集約は冗長でなく、controller 側の集計出力の唯一の入力である。

## 新旧両走 (DW-M08)

変更前 HEAD `c3c5ca0a` の使い捨て worktree。baseline PASSED。
anchor が変更前にも実在する 3 件だけを対象にした。

```
summary: {"KILLED": 0, "MISMATCH": 1, "PARSE_ERROR": 0, "SURVIVED": 2, "TIMEOUT": 0,
          "completed": 3, "matching": 2, "recorded": 3, "registered": 3}
```

| 変異 | 変更前 | 変更後 |
|---|---|---|
| t1551.m04 | KILLED、1 node (`test_complete_collection_rejects_a_stale_registered_node`) | KILLED、3 node |
| t1551.m07 | **SURVIVED、0 node** | KILLED、1 node |
| t1551.d01 | **SURVIVED、0 node** | KILLED、1 node |

新テストだけが検出する差分は 2 件。m04 は旧 suite が単に壊れていたのではないことの対照である。
同じ走行を 2 回行い、結果は一致した (1 回目は走行完了後の証拠退避が
cross-device rename で失敗したため、同一 device へ置き直して再走した)。

## conftest module の二重実体 (control 設計の根拠)

`orchestrator/tests/__init__.py` が無いため、pytest が conftest plugin として登録する
module と、test file が `from orchestrator.tests import conftest` で得る module は別実体である。

pytest 実行中の観測 (`pytest_configure` で plugin manager を走査):

```
IZANAGI_IDPROBE registered=1
IZANAGI_IDPROBE name='<repo>/orchestrator/tests/conftest.py' id=... __name__='conftest' file=...
IZANAGI_IDPROBE sysmodules={'conftest': ...}
```

別途の直接確認:

```
same object: False   (id が異なる)
A.__name__ conftest   B.__name__ orchestrator.tests.conftest
```

前 wave の control は後者を patch していたため、`-p orchestrator.tests.conftest` で
二重登録したときだけ注入が効いていた。本 wave の control は `-p` に頼らず、
登録済み plugin を実 path で 1 件だけ特定して patch し、
対象が 1 件でなければ plugin 自身が専用メッセージで落ちる。
