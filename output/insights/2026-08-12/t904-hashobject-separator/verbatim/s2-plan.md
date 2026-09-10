# 実装プラン

## 1. 実装差分

対象は [tools/codex_reasoning_ab.py:1330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1330) の 1 行だけとする。

変更前:

```python
object_id = _git(snapshot, "hash-object", "--no-filters", relative).decode().strip()
```

変更後:

```python
object_id = _git(snapshot, "hash-object", "--no-filters", "--", relative).decode().strip()
```

`--no-filters` は引き続き option として解釈させ、その直後の `--` で option parsing を終了し、`relative` を常に path operand とする。`_run`、`_git`、`cat-file`、reason 文字列、例外種別、`RC_SNAPSHOT` は変更しない。

## 2. 追加テスト

挿入位置は [orchestrator/tests/test_codex_reasoning_ab.py:1417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:1417)、現在の `test_uninitialized_nested_submodule_is_manifested_and_accepted` の直後、`test_uninitialized_nested_submodule_gitlink_pin_rejects_change` の直前とする。

関数名:

```python
test_leading_dash_untracked_path_is_accepted_only_outside_object_store
```

骨格:

```python
def test_leading_dash_untracked_path_is_accepted_only_outside_object_store(
    tmp_path: Path,
) -> None:
    snapshot, _, _ = _synthetic_nested_submodule_snapshot(tmp_path)
    TOOL._seal_git_object_closure(snapshot)

    relative = "-answer"
    payload = b"t904 leading-dash untracked artifact\n"
    (snapshot / relative).write_bytes(payload)

    object_id = TOOL._git(
        snapshot, "hash-object", "--stdin", input_bytes=payload
    ).decode().strip()
    assert TOOL._run(
        ("git", "cat-file", "-e", object_id),
        cwd=snapshot,
        check=False,
    ).returncode != 0

    reasons, _, _ = TOOL._git_closure_reasons(snapshot, (relative,))
    assert reasons == []

    stored_id = TOOL._git(
        snapshot, "hash-object", "-w", "--stdin", input_bytes=payload
    ).decode().strip()
    assert stored_id == object_id

    contaminated_reasons, _, _ = TOOL._git_closure_reasons(
        snapshot, (relative,)
    )
    assert (
        f"untracked artifact entered git object store: {relative}"
        in contaminated_reasons
    )
```

この形にする理由:

- `_synthetic_nested_submodule_snapshot` は既存の一時 repo helper であり、新しい fixture は不要。
- 既存の同 helper 利用テストと同じく、`TOOL._seal_git_object_closure` 後に `_git_closure_reasons` を直接呼ぶ。
- `benchmark_snapshots` は履歴 corpus と実 repository の clone に依存し、不在時は skip される。また既存利用 node は growth hold の対象なので、今回の局所回帰には使わない。
- 最初の `cat-file -e` で「object store 未混入」を明示的に成立させる。`hash-object --stdin` は `-w` を付けないため store を変更しない。
- `_git_closure_reasons` が例外を送出すればテストはその場で失敗し、正常復帰した場合だけ `reasons == []` を検査できる。
- 後半は stdin 経由で同じ blob を store に入れ、既存の正確な reason が残ることを確認する。

### 負例被覆の判断

既存の [test_codex_reasoning_ab.py:1444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:1444) は、initialized submodule に blob を注入し、一般的な `git object store contains unreachable objects` reason を検証している。しかし、先頭 `-` の root untracked path も、`tools/codex_reasoning_ab.py:1331-1333` の専用 reason も通らない。

したがって exact な負例被覆としては不足している。別関数は増やさず、上記の正例テスト後半に混入相を追加する。既存テストの期待値は変更しない。

## 3. 呼び出し元・consumer

| 層 | 現在の call site | 波及 |
|---|---|---|
| 直接 production caller | `tools/codex_reasoning_ab.py:1524` の `verify_snapshot` | 唯一の production `_git_closure_reasons` 呼び出し |
| snapshot 構築 | `build_snapshot:1399` | 構築完了時の oracle 検証 |
| 実行前後検証 | `_supervise_one:2048,2209` | Codex 実行の前後 snapshot 検証 |
| pair 起動前検証 | `supervise_pair:2313` | schedule と snapshot manifest の照合 |
| replay | `_replay_manifest:4723`、呼び元 `verify_manifest:4871` | 保存済み oracle の再検証 |
| CLI | `main:5394,5399,5430` | `build-snapshot`、`verify-snapshot`、supervise 経路 |
| 直接テスト | `test_codex_reasoning_ab.py:893,1377,1457` | stale graph、clean nested closure、submodule object injection |
| `verify_snapshot` テスト | 同ファイル `:763-764,795,903,946,977,987,1000,1010,1029,1045,1490` | 通常 path の回帰面。期待値変更なし |
| fixture consumer | 同ファイル `:283` の `benchmark_snapshots` | production snapshot 構築を間接利用。今回の新規テストでは不使用 |

所有外の関連面:

- `orchestrator/tests/growth_test_holds.py:64-79` は `benchmark_snapshots` 系の重い既存 node を登録している。新規テストは固定サイズの synthetic repo のみなので登録・同ファイル編集は行わない。
- `orchestrator/tests/conftest.py:347-385` と `test_growth_test_holds_contract.py:118-119` は上記 registry の consumer。registry を変えないため波及なし。
- `hooks/README.md:82` は CLI の read-only 起動契約、`tools/check_ai_provenance.py:517-518` は二対象ファイル名を文字列として参照するだけであり、interface・対象ファイル集合とも不変。
- 静的検索上、他の production Python ファイルから `_git_closure_reasons` または `verify_snapshot` を直接呼ぶ箇所はない。

## 4. 受理集合の変化

変化するのは、次をすべて満たす入力だけである。

1. `_git_closure_reasons` の `untracked` 要素である。
2. `(snapshot / relative).is_file()` が真。
3. argv 上の `relative` 自体が `-` で始まり、従来 `hash-object` の option と誤認されたもの。今回の正例は root-level の `-answer`。
4. そのファイル内容の blob が object store に存在しない。
5. その他の closure 条件に違反がない。

この場合だけ、従来の `_run` 非ゼロによる `ValidationError(RC_SNAPSHOT)` から、正常な OID 計算、`cat-file -e` 非ゼロ、reason なしへ変わる。

変わらない範囲:

- `normal` や `dir/-answer` のように argv token が `-` で始まらない path は、separator の前後で同じ bytes を `--no-filters` で hash する。
- blob が store に存在する場合は、`cat-file -e` と既存 reason により拒否されたまま。
- 存在しないもの、directory、非 regular file は `path.is_file()` の `continue` が先に働く。
- `_status_sets:1413-1438` は path を引数にせず porcelain `-z` 出力を data として読むため、leading-dash 非対称はない。
- `_expected_filesystem_files:1148-1165` は `set(untracked)` を合成し、`_filesystem_file_set:1081-1105` は相対 path 文字列を収集するだけなので不変。
- production の `_snapshot_spec:675-677` は全要素を `f"{ARTIFACT_DIR}/{name}"` にするため argv token は `-` で始まらない。確認した production 6 call site は `spec=` を渡さないので、現在の certified 出力には到達しない。
- reason literal、例外クラス、rc、既存テスト期待値には変更を加えない。

## 5. 親が行う検証

本段では tmp へ書けないため、pytest を実走していない。親は実装後に `tools/run_tests.py` 経由で、新規 node、既存の clean nested closure、既存の object injection、続いて `test_codex_reasoning_ab.py` 全体を実走する。`--` を除く変異では新規テストの最初の closure 呼び出しが異常終了することを検出対象とする。

## 総括

- production 差分は `hash-object` の path 直前へ `--` を足す 1 行だけ。
- synthetic repo を使う新規 1 関数で、未混入の受理と混入時の既存 reason を連続検証する。
- 受理集合の増分は、実在する leading-dash untracked file の blob 未混入ケースだけ。
- 最大のリスクは、既存の submodule 負例を exact な untracked-path 被覆と誤認すること。