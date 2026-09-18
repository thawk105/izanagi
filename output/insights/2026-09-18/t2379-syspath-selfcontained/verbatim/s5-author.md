## 変更面

`orchestrator/tests/test_s8b_approved.py:31`

```diff
-from tests.skiputil import Skip, skip  # noqa: E402
+from orchestrator.tests.skiputil import Skip, skip  # noqa: E402
```

`orchestrator/tests/test_profiler_directive.py:341`

```diff
-    from codex_roles import policy  # noqa: PLC0415
+    from orchestrator.codex_roles import policy  # noqa: PLC0415
```

## 検査

worktree 直下で `python3 -B -c` を使用。標準ライブラリ・外部依存の探索パスを保持し、リポジトリ内の探索パスは root のみに限定しました。各検査を fresh process で実行し、すべて終了コード 0 でした。

```text
IMPORT_PASS orchestrator.tests.test_s8b_approved
IMPORT_PASS orchestrator.tests.test_profiler_directive
DIRECT_CALL_PASS test_derived_directive_is_accepted_by_the_role_policy_check
DID_RAISE from tests.skiputil import Skip, skip | ModuleNotFoundError: No module named 'tests'
DID_RAISE from codex_roles import policy | ModuleNotFoundError: No module named 'codex_roles'
```

変更後アンカーの `grep -c -x` 出力は、指定順に各 1 件です。

```text
1
1
```

`git diff --stat`:

```text
 orchestrator/tests/test_profiler_directive.py | 2 +-
 orchestrator/tests/test_s8b_approved.py       | 2 +-
 2 files changed, 2 insertions(+), 2 deletions(-)
```

`git status --porcelain`:

```text
 M orchestrator/tests/test_profiler_directive.py
 M orchestrator/tests/test_s8b_approved.py
```

`git diff --check`: 出力なし、終了コード 0。所有外の差分はなく、各ファイル +1/-1 のみです。

対象 2 ファイルの選択走・受入全走・変異実走: **実装済み・未実走**。指示どおり pytest と `tools/run_tests.py` は起動していません。

## 波及の静的列挙

- 所有外の caller: `orchestrator` / `tools` の検索では、対象モジュールを呼ぶ production caller は見つかりませんでした。名前の参照は説明文・README・実行時間台帳でした。
- 共有 fixture: `conftest.py` と fixture の利用箇所は変更なし。`skiputil.py` と policy の実装も変更なしです。
- consumer test: `test_s8b_protocol_builder.py` は既に同じ `orchestrator.tests.skiputil` を使用しています。`test_campaign_import_invariant.py` の campaign import 検査に対し、今回の対象 import は campaign 名前空間を参照していません。
- 検査関数・期待値・受理条件は変更せず、import の解決経路だけを変更しました。

指定検索:

```sh
grep -rn "from tests\.skiputil\|from codex_roles import" orchestrator tools
```

結果: 出力なし、終了コード 1（該当なし）。

## 総括

plan v2 の指定 2 行を逐語どおり実装しました。import・直接呼出し・旧 import の反実仮想検査は期待どおりです。commit・ステージング・stash・branch 操作は行っていません。選択走と受入・変異実走は親側に残っています。