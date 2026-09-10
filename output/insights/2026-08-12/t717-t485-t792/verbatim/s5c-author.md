## 総括

[T-717] の既定 walltime を 40 分から 60 分へ変更し、[T-792] の 6 import を canonical namespace へ統一しました。変更は指定された 3 ファイル・7 行だけです。

- 実装済み・未実走です。pytest、`run_tests.py`、各 checker は親が計算ノードで実施するため起動しておらず、緑は申告しません。
- 期待値、`sys.path`、fixture、`conftest.py`、docs、scope 外テストは変更していません。
- `git diff --check` は成功しました。最終差分は所有 3 ファイルだけです。
- `git add`、commit、checkout は行っていません。
- module identity と consumer を静的追跡した結果、node 1 の patch 対象と SUT の helper は同一 object になります。既存 test module の二重化も増えていません。
- 訂正後裁定に反すると判断した点はありません。

## 変更後の全 7 行

```text
tools/pegasus/dispatch_compute.py:28
DEFAULT_WALLTIME = "01:00:00"

orchestrator/tests/test_real_repo_serialization.py:826
    from orchestrator.tests import repo_tree_util

orchestrator/tests/test_real_repo_serialization.py:827
    from orchestrator.tests import test_s8b_protocol_builder as sut

orchestrator/tests/test_real_repo_serialization.py:909
    from orchestrator.tests import test_s8b_binding_driftguards as driftguard_tests

orchestrator/tests/test_real_repo_serialization.py:910
    from orchestrator.tests import test_s8b_oracle_driver as driver_tests

orchestrator/tests/test_s8b_protocol_builder.py:37
from orchestrator.tests import repo_tree_util  # noqa: E402

orchestrator/tests/test_s8b_protocol_builder.py:38
from orchestrator.tests.skiputil import Skip, skip  # noqa: E402
```

該当箇所は [dispatch_compute.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t717-t485-t792/tools/pegasus/dispatch_compute.py:28)、[test_real_repo_serialization.py:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t717-t485-t792/orchestrator/tests/test_real_repo_serialization.py:826)、[test_s8b_protocol_builder.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t717-t485-t792/orchestrator/tests/test_s8b_protocol_builder.py:37) です。

## 受理・拒否挙動

[T-717] は既定要求時間だけを 60 分へ伸ばします。明示的な walltime override、形式検査、task・request・receipt の受理集合には触れていません。

既存の参照は変更せず、次のままです。

```text
tools/pegasus/dispatch_compute.py:1293  walltime: str = DEFAULT_WALLTIME,
tools/pegasus/dispatch_compute.py:1832  walltime: str = DEFAULT_WALLTIME,
tools/pegasus/dispatch_compute.py:1926  parser.add_argument("--walltime", default=DEFAULT_WALLTIME)
```

`tools/run_tests.py:920` と `tools/check_ai_provenance.py:1693` は walltime を明示せず `dispatch()` を呼ぶため、新しい経路を追加せず定数変更が伝播します。

[T-792] は import 解決と module identity だけを修正しました。2 node の assert、skip 条件、期待値、受理集合は不変です。

## 旧 import の残存 grep

`from tests import|from tests\.` を全 Python ファイルへ検索した結果、残存は **1 件**です。

```text
orchestrator/tests/test_s8b_approved.py:31:
from tests.skiputil import Skip, skip  # noqa: E402
```

これは段 4 追補で明示された scope 外所見です。同ファイルは承認定数の契約テストであり、今回修正する 2 node や node 1 の `repo_tree_util` patch 結線には参加しません。契約どおり変更していません。

`tests.repo_tree_util` または `from tests import repo_tree_util` の残存は **0 件**です。

## 旧 walltime literal

production・test を含む repo の非 docs／非 output 領域で literal `"00:40:00"` を検索し、結果は **0 件（`rg` rc=1、出力なし）**でした。

既存テストは引き続き値を定数から導出しています。

```text
orchestrator/tests/test_pegasus_dispatch_compute.py:255
f"elapstim_req={DC.DEFAULT_WALLTIME}"

orchestrator/tests/test_pegasus_dispatch_compute.py:2467
DC._walltime_seconds(DC.DEFAULT_WALLTIME)
```

60 分そのものを pin するテストは追加していません。

## node 1 の module identity

変更後、node 1 は以下の key で module をロードします。

```text
sys.modules["orchestrator.tests.repo_tree_util"]
sys.modules["orchestrator.tests.test_s8b_protocol_builder"]
```

後者の SUT も module 冒頭で同じ canonical import を行うため、その global `repo_tree_util` は同じ

```text
sys.modules["orchestrator.tests.repo_tree_util"]
```

を指します。

したがって node 1 の

```python
mock.patch.object(
    repo_tree_util,
    "assert_repo_tree_unchanged",
    recording_wrapper,
)
```

は、SUT の `test_build_and_write_leave_repo_tree_unchanged()` が呼ぶ属性そのものを差し替えます。旧 key `sys.modules["tests.repo_tree_util"]` をロードする repo 内経路は残っていません。

両対象ファイルの repo root を追加する既存 `sys.path` 操作は変更していません。

## 所有外への静的波及

`repo_tree_util` の consumer は変更後、次の 4 ファイルだけで、すべて canonical import です。

- `test_real_repo_serialization.py`
- `test_s8b_protocol_builder.py`
- `test_ruleops.py`
- `test_campaign_import_invariant.py`

特に既存先例の `test_ruleops.py` と `test_campaign_import_invariant.py` と同一 namespace へ揃いました。`orchestrator.tests.repo_tree_util` と `tests.repo_tree_util` の両方をロードする repo 内経路はありません。

`skiputil` は repo 全体では未統一です。

- `from skiputil import ...`: 15 test files。すべて変更なし。
- `from orchestrator.tests.skiputil import ...`: 今回の `test_s8b_protocol_builder.py` だけ。
- `from tests.skiputil import ...`: scope 外の `test_s8b_approved.py` だけ。

このため full-suite の path 状態によっては `skiputil`、`orchestrator.tests.skiputil`、`tests.skiputil` という複数 key が存在し得ます。ただし identity を跨ぐ辺は見つかりませんでした。

- protocol builder は canonical `skip` が投げる canonical `Skip` を同じファイルの `_run()` で捕捉します。
- `test_s8b_approved.py` も自身が import した `skip`／`Skip` の組を内部で使用します。
- pytest 配下では各 `skip()` が `pytest.skip()` を使用します。
- protocol builder の `Skip` や `skip` を別 consumer が importする箇所はありません。

したがって今回の変更による `skiputil` consumer の例外型不一致や捕捉漏れは静的にはありません。scope 外の `test_s8b_approved.py` に残る単独焦点走の偽赤可能性は、段 4 追補どおり既存所見として残ります。

## pytest の test module 二重化

`orchestrator/` と `orchestrator/tests/` に `__init__.py` はなく、pytest が test file を top-level 名で収集する既存性質は変わりません。変更後は、例えば次の 2 key が併存し得ます。

```text
test_s8b_protocol_builder
orchestrator.tests.test_s8b_protocol_builder
```

同様に oracle driver と binding driftguards も top-level／canonical の 2 object になり得ます。しかし変更前も top-level／`tests.test_*` の 2 object になり得たため、test module の二重化個数は増えていません。

さらに protocol builder の両 object は、どちらも同じ canonical `orchestrator.tests.repo_tree_util` を束縛します。このため node 1 に必要な helper identity は、test module 自体が二重でも維持されます。

node 2 では canonical driver と、driftguards が top-level importする driver が別 objectになり得ますが、同 node は関数へ `inspect.getsource()` を適用して文字列を検査するだけです。module identity、共有属性、fixture object identity を比較していないため、裁定どおり `test_s8b_binding_driftguards.py` の transitive 修正は不要です。

## 検査状態

- 指定成果物・段 4 追補・前回停止報告: 読了
- 変更行数: 7 行置換
- `git diff --check`: 成功
- 静的 grep／consumer／module identity 追跡: 実施
- pytest・関連 node・受入全走: **未実走**
- `check_codex_agents.py`／`check_docs.py`: **未実走**
- docs 編集: なし
- stage／commit／checkout: なし
- 最終 `git status`: 所有 3 ファイルのみ modified