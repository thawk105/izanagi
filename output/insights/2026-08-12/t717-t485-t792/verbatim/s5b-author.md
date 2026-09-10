## 総括

実装は開始せず、worktree を無変更のまま停止しました。

- T-717/T-792 の裁定内容を静的に検査したところ、T-792 の指定された4行だけを変更すると、第一 node の monkeypatch が SUT の helper module に届かず、既存期待値が赤になると判断しました。
- 裁定は所有外ファイルの修正を禁じているため、T-717 だけを部分適用することもせず、停止条件に従いました。
- pytest、Python interpreter、テスト、commit、`git add`、`git checkout` は実行していません。すべて未実走です。
- docs を含め、ファイル変更はありません。最終 `git status --short --branch` は branch 名だけを表示し、差分はありません。
- 裁定に反すると考える点は、T-792 が直接4行だけを正規化し、transitive import を正規化しない点です。詳細は「二重 import の判定」に記します。

## 現行の受理・拒否挙動

scope に入る前の現行挙動は次のとおりです。

T-717 は、Pegasus dispatch の既定 walltime が40分です。明示的な `--walltime`／`walltime=` override は引き続き受理され、`HH:MM:SS` でない値、分・秒が範囲外の値、合計0秒以下は拒否されます。予定変更は既定値だけであり、task、request、receipt の受理集合は変えません。

T-792 の2 node は、段1実測では `from tests import ...` が解決できず `ModuleNotFoundError` で拒否されています。本来の assert は以下を検査します。

- `test_protocol_builder_repo_tree_guard_is_wired_to_real_root`: 実 repo-tree helper が厳密に1回呼ばれ、builder と writer が同一 guard action 内で実行されること。
- `test_ratified_memo_has_a_real_resolution_payer`: 正本 payer が memo を使わず実 repo root を渡し、opt-in node だけが `patch_ratified_loader` を使用すること。

この assert や受理条件は変更していません。

## 対象行の逐語

停止したため「変更後」の行は存在しません。現在の行は次のままです。

```text
tools/pegasus/dispatch_compute.py:28:
DEFAULT_WALLTIME = "00:40:00"

tools/pegasus/dispatch_compute.py:1293:
    walltime: str = DEFAULT_WALLTIME,

tools/pegasus/dispatch_compute.py:1832:
    walltime: str = DEFAULT_WALLTIME,

tools/pegasus/dispatch_compute.py:1926:
    parser.add_argument("--walltime", default=DEFAULT_WALLTIME)
```

```text
orchestrator/tests/test_real_repo_serialization.py:826:
    from tests import repo_tree_util

orchestrator/tests/test_real_repo_serialization.py:827:
    from tests import test_s8b_protocol_builder as sut

orchestrator/tests/test_real_repo_serialization.py:909:
    from tests import test_s8b_binding_driftguards as driftguard_tests

orchestrator/tests/test_real_repo_serialization.py:910:
    from tests import test_s8b_oracle_driver as driver_tests
```

裁定どおりなら `:28` は `"01:00:00"`、後者4行は `from orchestrator.tests import ...` になりますが、既知の赤を作るため適用していません。

## DEFAULT_WALLTIME の全参照と波及

Python production/test 内の全出現は6件です。

```text
tools/pegasus/dispatch_compute.py:28
tools/pegasus/dispatch_compute.py:1293
tools/pegasus/dispatch_compute.py:1832
tools/pegasus/dispatch_compute.py:1926
orchestrator/tests/test_pegasus_dispatch_compute.py:255
orchestrator/tests/test_pegasus_dispatch_compute.py:2467
```

役割は次のとおりです。

- `:28`: 値の唯一の定義。
- `:1293`: `_dispatch_impl()` の既定引数。
- `:1832`: `dispatch()` の既定引数。
- `:1926`: CLI `--walltime` の argparse 既定値。
- test `:255`: qsub argv の期待を `DC.DEFAULT_WALLTIME` から導出。
- test `:2467`: 受入実測時間に対する下限を同定数から導出。

値を直接 literal pin するテストはありません。共有 `conftest` にも `DEFAULT_WALLTIME` 依存はありません。

所有外 caller では次が `walltime` を渡さず、`dispatch()` の既定値を使用します。

- `tools/run_tests.py:920`
- `tools/check_ai_provenance.py:1693`

したがって予定されたT-717変更は両 caller の計算ノード要求時間を40分から60分へ伸ばします。`tools/run_tests.py` に新しい引数経路を作る必要はなく、裁定と一致します。

停止により literal `"00:40:00"` は現在も production の `dispatch_compute.py:28` に1件残っています。test 内には同 literal はありません。「production・test に残っていない」という変更後条件は未達です。

## `orchestrator.tests` import の既存先例

正規 namespace import は既に複数箇所で使われています。代表例は以下です。

```text
orchestrator/tests/test_ruleops.py:24
orchestrator/tests/test_campaign_import_invariant.py:27
orchestrator/tests/test_calibration_freeze_authority_contract.py:17
orchestrator/tests/test_role_session_isolation.py:32
orchestrator/tests/test_dev_waves_cli.py:23-24
orchestrator/tests/test_dev_waves_integration.py:35
orchestrator/tests/test_campaign_lock_wal_consumers.py:24
orchestrator/tests/test_artifact_admission.py:38
orchestrator/tests/test_p3_autonomous_workload_trial.py:39
orchestrator/tests/test_run_tests_task_run.py:25
```

よって `orchestrator.tests` namespace 自体は成立しています。問題は、今回読み込むモジュール内部に旧 namespace の import が残る点です。

停止したため、対象ファイル内の `from tests import` は現在も4件残っています。「同ファイルに0件」という変更後条件は未達です。

## 二重 import の判定

結論は「同一 module object にはならず、第一 node では危険が現実化する」です。

`orchestrator/tests` には `__init__.py` がなく、namespace package として読み込まれます。Python は次を別の `sys.modules` key として扱います。

```text
tests.repo_tree_util
orchestrator.tests.repo_tree_util
```

同様に、各 `test_s8b_*` module も2つの名前で読み込めば別 object です。

### 第一 node

指定変更後、node は次を canonical import します。

```python
from orchestrator.tests import repo_tree_util
from orchestrator.tests import test_s8b_protocol_builder as sut
```

一方、`test_s8b_protocol_builder.py:37` は現在も次のままです。

```python
from tests import repo_tree_util
```

したがって、旧 import が解決する環境では次の2 object が生じます。

- node が patch する `orchestrator.tests.repo_tree_util`
- `sut.test_build_and_write_leave_repo_tree_unchanged()` が呼ぶ `tests.repo_tree_util`

node の `mock.patch.object(..., "assert_repo_tree_unchanged", recording_wrapper)` は前者だけを書き換えます。SUT は後者を呼ぶため `helper_calls` は増えず、`test_real_repo_serialization.py:878` の次の期待が失敗します。

```python
assert len(helper_calls) == 1
```

さらに、焦点走と同じ path 条件でトップレベル `tests` 自体が解決しなければ、canonical `sut` の import 中に `test_s8b_protocol_builder.py:37` で再び `ModuleNotFoundError` になります。どちらの場合も指定4行だけでは第一 node を直せません。

### 第二 node

`test_s8b_binding_driftguards.py:43` は、現在も `test_s8b_oracle_driver` をトップレベル名で importします。一方、指定変更後の node は `orchestrator.tests.test_s8b_oracle_driver` を直接 importします。この2つも別 module object です。

ただし第二 node の assert は function/module identity、`isinstance`、共有 module 属性を比較していません。対象 function に `inspect.getsource()` を適用し、以下の文字列だけを検査しています。

- payer に `ratified_memo`／`patch_ratified_loader` がない
- payer に `root=ROOT` がある
- opt-in functions に `patch_ratified_loader` がある

したがって、第二 node の現行 assert に限れば、二重 object が直接赤を作る根拠はありません。ただし import-time globals や fixture registry は別々になるため、namespace 正規化としては不完全です。

## 再裁定が必要な範囲

第一 nodeを成立させるには、少なくとも所有外の次の transitive import を canonical 化する必要があります。

```text
orchestrator/tests/test_s8b_protocol_builder.py:37
from tests import repo_tree_util
```

第二 nodeも module identity を統一するなら、次も対象候補です。

```text
orchestrator/tests/test_s8b_binding_driftguards.py:43
import test_s8b_oracle_driver as driver_fixtures
```

いずれも今回の所有ファイル外であり、現行裁定では編集できません。所有範囲を広げるか、transitive import を含めない別の同一-object結線方法を裁定し直す必要があります。

## 検査状況

- brief／段4裁定: 読了
- 静的 grep／ソース追跡: 実施
- pytest／関連テスト: 未実走
- `check_codex_agents.py`／`check_docs.py`: 未実走
- commit／stage: 未実施
- docs 編集: なし
- code/test 編集: なし
- worktree: clean
