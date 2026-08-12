F1〜F4 を実装しました。この巡で編集したのは所有内の 2 file のみです。

- F1 — [t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:524) `repository_roots_from_git_identity()`
  - 述語: 非空の登録は、strict 解決成功時も `FileNotFoundError` 時も、最終的に `roots.add(registered.parent)` される。
  - 後者の `registered` は `Path(registered_text).resolve(strict=False)`。
  - コードは初期 roots 生成後に `add()` しか行わず、`remove()` / `discard()` / skip はないため、roots が減ることはありません。
  - [test_t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:1044) を、欠落した登録が主張する root も含まれる期待へ改名・更新しました。

- F2 — [test_t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:105) `_config()`
  - `Path(C.__file__).resolve().parent` から実 bytes を取得。
  - 一時 package の同梱物: `wrapper.py`、`t810_harness_schema.py`、`t810_runner_policy.py`、`CCBench`、`dependencies.json`。
  - 子 process の述語: `PYTHONPATH == str(shim)`。repo root は含まず、その不在も assert しています。
  - authority 検査・依存 hash は追加しておらず、R2 は未解決のままです。

- F3 — [test_t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:921) `test_generated_script_executes_staged_wrapper_cli()`
  - 既存の `argv == slot["wrapper_argv"]` と `Path(argv[-1]) == request_path` は維持。
  - 実行述語を `subprocess.run([str(script_path)], ...)` に変更し、shebang・`set -eu`・全 script 行を通します。
  - timeout 30 秒、exit code 2、stdout、PBS ID、hostname の期待値は不変です。

- F4 — [t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:676) `prepare_group()` と [test_t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:822)
  - publication 前に既存の `_assert_staged_file_identities(slot)` を適用。
  - 述語: shipped wrapper と byte 同一なら `prepare_group()` が成功する。同じ fixture 形で staged wrapper を1 byte変更し、申告 hash もその実 bytes に合わせた自己整合入力は `T810CoordinatorError` で拒否される。
  - spy・monkeypatch・新しい authority/API は追加していません。

wave 開始前から tracked のテストについて、assert・`pytest.raises`・期待値・skip/xfailを一つも変更していません。変更したテストは本 wave で新設されたものです。

静的な波及可能性:

- `prepare_group()` の直接 callerは、staged identity 不一致をreceipt読取・publicationより前に拒否されます。
- `coordinate()` はF1の追加rootを継承し、外部linked worktreeの登録主張も保護対象になります。
- repository外でwrapperを実行するproducerは、上記2 Python依存fileもstageする必要があります。
- repo内には改名前のテストnodeid参照はありませんが、repo外の固定nodeid selectorは追随が必要な可能性があります。
- docs・guard・budget・runner policy本体・validator・policy JSON・commitには触れていません。
- worktreeに残る他2 fileの変更は前巡からの継承分で、この巡では変更していません。

検証は `py_compile` 2 fileがrc=0、`git diff --check`も問題なしです。契約どおりpytestは走らせていません。状態は**実装済み・未実走**です。

## 総括

F1の受理拡大を除去し、F2/F3の統合経路をrepository-externalなscript直接実行へ直し、F4をanchor gateの削除を殺せる受理・拒否対へ変更しました。親による計算ノード実測待ちです。