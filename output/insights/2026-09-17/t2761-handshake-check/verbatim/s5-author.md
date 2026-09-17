## 差分要約

変更ファイルは `orchestrator/tests/test_pegasus_dispatch_compute.py` のみです。

- `:12`: 裁定の指定どおり `import shlex` を追加。
- `:2580`: `repo-current` / `repo-release-path` の parametrize を追加。
- `:2585`: 対象 test に `repo_root` 引数を追加し、`_job_script` へ渡す。
- `:2598–2636`: 6 値の位置限定正規化、P5 の二段検査、release 候補行の不在検査を実装。既存 3 assert は文言・相対順序を維持。

AST parse と `git diff --check` は成功しました。

## 実走結果

**実装済み・未実走。** 次のコマンドを試みましたが、PreToolUse hook が起動前に拒否しました。

```bash
python3 -m pytest orchestrator/tests/test_pegasus_dispatch_compute.py -k compute_marker_is_cross_namespace -p no:cacheprovider -q
```

対象 nodeid は以下の 2 件です。いずれも実走結果はありません。

```text
orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-current]
orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-release-path]
```

自動実行ガードの拒否理由は「Pegasus ログインノードでの pytest 起動は禁止」です。依頼で禁止された計算ノードへの dispatch は行っていません。

## anchor 逐語

`a-old-check` の old 全体です。末尾改行を含め、ファイル内の出現数が **1** であることを確認しました。

```python
    normalizations = (
        (
            "\nRESULT=" + shlex.quote(str(tmp_path / "result.json")),
            "\nRESULT=<SUBMISSION>/result.json",
        ),
        (
            "\nPROBE=" + shlex.quote(str(tmp_path / "interpreter_probe.py")),
            "\nPROBE=<SUBMISSION>/interpreter_probe.py",
        ),
        (
            "\nREQUEST=" + shlex.quote(str(tmp_path / "request.json")),
            "\nREQUEST=<SUBMISSION>/request.json",
        ),
        (
            "\nREPO=" + shlex.quote(str(repo_root)),
            "\nREPO=<REPO>",
        ),
        (
            "\nDISPATCHER=" + shlex.quote(str(repo_root / "tools" / "pegasus" / "dispatch_compute.py")),
            "\nDISPATCHER=<REPO>/tools/pegasus/dispatch_compute.py",
        ),
        (
            "\nMARKER=" + shlex.quote(str(tmp_path / DC._COMPUTE_MARKER_NAME)),
            "\nMARKER=<SUBMISSION>/" + DC._COMPUTE_MARKER_NAME,
        ),
    )
    normalized = script
    for needle, replacement in normalizations:
        # 正規化の前提 (値がちょうど 1 回、shell word として完結) が崩れた入力は
        # 保守的に拒否する。厳しくする方向だけで受理を増やさない。
        assert script.count(needle) == 1, f"normalization needle must occur once: {needle!r}"
        end = script.index(needle) + len(needle)
        assert end == len(script) or script[end] in "\n \t;&|", f"normalization needle is not word-terminated: {needle!r}"
        normalized = normalized.replace(needle, replacement, 1)
    # 環境値を除いた本文の release 候補行を保守的に拒否する。
    # FA-4 の release handshake 不在の代理検査。構文解析ではない。
    release_lines = [line for line in normalized.splitlines() if "release" in line.lower()]
    assert not release_lines, release_lines
    assert "while" not in script
```

## 波及

以下はすべて変更後の対象ファイル内の行番号です。

- 他の直接 caller: `:1064`、`:1117`、`:2300`、`:5383`、`:5970`、`:6162`、`:6659`。production を変更していないため、生成 script の挙動は不変です。
- 共有 helper: `_job_run_with_mocked_child` (`:4123`)、`_write_bound_job_run_request` (`:4185`)、`_make_bound_xdist_case` (`:5098`)。いずれも未変更です。
- 上記 helper の consumer test はそれぞれ 19 件、14 件、4 件。環境変数伝搬・job 実行契約、隔離・結果公開、xdist 依存解決の各検査への挙動変更は静的にはありません。
- 共有 fixture・conftest・`_REPO` は未変更。対象 test は既存の `tmp_path` を使い、収集 node が 1 件から 2 件になります。

## 総括

検査を甘くしていません。置換は指定された 6 値の完全な引用表現に位置限定で各 1 回だけ適用し、固定 basename・dispatcher suffix・marker 定数を残します。行末構文や別行の template 由来の `release` は残るため、大小無視の候補行検査で拒否します。needle の欠落・重複・word 終端不成立も拒否します。

production・他 test・docs は変更せず、commit も作成していません。実走の緑は未確認です。