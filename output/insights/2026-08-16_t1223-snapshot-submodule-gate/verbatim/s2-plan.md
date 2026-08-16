## プラン

1. `tools/codex_reasoning_ab.py:695-712` の `_snapshot_spec` に、oracle へは出さない検査設定を追加する。

```python
"require_initialized_submodule_depth": 1,
```

この値は「深さ 1 から指定深さまでを `initialized` 必須」と定義する。

2. `tools/codex_reasoning_ab.py:1692-1700` の manifest SHA 計算直後、既存 pin 照合の前に次の骨格を追加する。`enforce_closure` 分岐の外へ置き、`git_object_closure=False` でも迂回不能にする。

```python
required_depth = expected.get(
    "require_initialized_submodule_depth", 1
)
if (
    isinstance(required_depth, bool)
    or not isinstance(required_depth, int)
    or required_depth < 1
):
    reasons.append(
        "require_initialized_submodule_depth must be a positive integer"
    )
else:
    manifest_paths = {row["path"] for row in submodule_manifest}
    for row in submodule_manifest:
        path = row["path"]
        depth = 1 + sum(
            1
            for parent in manifest_paths
            if parent != path and path.startswith(parent + "/")
        )
        if (
            depth <= required_depth
            and row["initialization"] != "initialized"
        ):
            reasons.append(
                f"required submodule is uninitialized at depth {depth}: {path}"
            )
```

3. `tools/codex_reasoning_ab.py:1703-1724` の oracle dict は変更しない。特に `require_initialized_submodule_depth` を返さない。したがって、従来から正規な snapshot の `manifest_sha256` は変化しない。

4. `orchestrator/tests/test_codex_reasoning_ab.py:1895-2051` の合成 submodule テスト群へ、独自 spec 作成 helper、未初期化 top-level repo helper、正負テストを追加する。既存 `test_uninitialized_nested_submodule_is_manifested_and_accepted` は変更しない。

既定 spec caller の静的影響は次のとおり。

| caller | 静的判定 |
|---|---|
| `tools/codex_reasoning_ab.py:1508` | `_build_snapshot_base` は `1481` から `715-762` を呼び、source で initialized な submodule だけを初期化する。source の深さ 1 が initialized なら通る。fresh worktree、または legacy base で深さ 1 が未初期化なら意図どおり赤になる。 |
| `tools/codex_reasoning_ab.py:2210` | trial 起動前に検査するため、未初期化 top-level を持つ既存 schedule snapshot は起動前に赤になる。正規に build された snapshot は通る。 |
| `tools/codex_reasoning_ab.py:2371` | `2210` を通った後、snapshot は `2139-2141` で read-only bind されるため通常は再び通る。外部並行変更や sandbox 破れで初期化状態が落ちた場合だけ追加 reason で赤になる。 |
| `tools/codex_reasoning_ab.py:4885` | 過去 oracle が未初期化 top-level を受理していた場合、replay は新たに赤になる。例外は `4952-4953` で replay failure として収集される。これは意図した受理集合縮小である。 |
| `tools/codex_reasoning_ab.py:5561` | CLI へ未初期化 snapshot を直接渡した場合、`5645-5651` により `RC_SNAPSHOT` で拒否される。 |
| `tools/codex_reasoning_ab.py:2475` | 指定一覧外だが同じ既定 verifier を通る。schedule の manifest pin が一致していても、top-level 未初期化なら新 gate が先に拒否する。 |

## (P1)(P2) の検証

(P1) は支持する。

`_submodule_inventory` は、各 repository から得た相対 path を実 snapshot 上の `candidate` に変換し、`tools/codex_reasoning_ab.py:1018` で snapshot root 相対の path に正規化する。親が initialized の場合だけ `1032-1034` で再帰するため、nested 行には必ず initialized な全祖先行が存在する。

したがって深さは、slash の個数ではなく、manifest 内の「`parent + "/"` が path の先頭にある厳密な祖先行の数 + 1」で機械的に求められる。

- root 直下の宣言 `external/ccbench` は、文字列に slash があっても祖先行がないため深さ 1。
- nested の `external/ccbench/third_party/shirakami` は `external/ccbench/` が前置されるため深さ 2。
- `deps/a` と `deps/ab` は `parent + "/"` で比較するため誤って親子扱いしない。

実データでも root の `.gitmodules:2` は `external/ccbench`、その子の `external/ccbench/.gitmodules:2` は `third_party/shirakami` であり、`1018` の正規化後は上記の親 prefix になる。

また標準起動は `docs/dev-wave/operations.md:141-143` で、開始時は非再帰の `git submodule update --init`、受入直前だけ recursive である。`tools/codex_reasoning_ab.py:729-760` も source で initialized な階層だけ snapshot へ伝播する。よって全深度必須は、標準起動途中に作られた snapshot を壊す。深さ 1 は、標準手順が常に保証する範囲内で最大の一様な深度要求である。

(P2) も支持する。ただし `orchestrator/tests/test_codex_reasoning_ab.py:1228-1231` だけでは fallback を証明できない。同テストは `_snapshot_spec("POS")` のコピーなので、新 key もコピーされるからである。

`tools/codex_reasoning_ab.py:1610` は明示 `spec` を default spec と merge しない。したがって、本当に独立した spec が key を欠く場合に効くのは verifier 内の `expected.get(..., 1)` だけである。新しい負例では、非空の独自 spec から key を意図的に省き、さらに `git_object_closure=False` としても新 reason が出ることを固定する。

## 新規テスト設計

`orchestrator/tests/test_codex_reasoning_ab.py:2001` 付近に `_synthetic_verify_snapshot_spec(snapshot, *, enforce_closure)` を追加する。spec は次を持つ。

- `head`: `git rev-parse HEAD`
- `branch`: `TOOL.BRANCH`
- `tracked_paths`, `numstat`, `untracked`, `forbidden`: 空
- `hashes`, `modes`: `.gitmodules` と `root.txt` の実値
- `git_object_closure`: 引数値
- `require_initialized_submodule_depth`: helper では意図的に省略

負例用 repo は次のローカル合成 command 列で作る。

1. child source で `git init`、`child.txt` を `git add`、固定 user 設定付きで `git commit`。
2. `git rev-parse HEAD` を gitlink commit として取得。
3. snapshot で `git init`。
4. `root.txt` と、path が `deps/child`、URL が child source のローカル path である `.gitmodules` を作る。
5. `git add root.txt .gitmodules`。
6. `git update-index --add --cacheinfo 160000,<child_head>,deps/child`。
7. commit 後、`git branch -M <TOOL.BRANCH>`。
8. `git submodule add/update` は実行しない。これにより worktree と `.git/modules/deps/child` の双方が存在しない正規な `"uninitialized"` 状態になる。
9. `_seal_git_object_closure(snapshot)` を呼び、無関係な closure reason を除く。

提案テスト名は `test_verify_snapshot_rejects_uninitialized_top_level_submodule_with_custom_spec`。`git_object_closure=False` の独自 spec を渡し、次を検査する。

```python
assert TOOL._snapshot_spec("POS")[
    "require_initialized_submodule_depth"
] == 1
assert "require_initialized_submodule_depth" not in spec

with pytest.raises(TOOL.ValidationError) as caught:
    TOOL.verify_snapshot(snapshot, "POS", spec=spec)

assert caught.value.reasons == (
    "required submodule is uninitialized at depth 1: deps/child",
)
assert caught.value.rc == TOOL.RC_SNAPSHOT
```

正例は既存 `_synthetic_nested_submodule_snapshot` (`1895-2001`) を再利用する。これは top-level `deps/child` が initialized、`deps/child/third_party/grandchild` が uninitialized である。`_seal_git_object_closure` 後、独自 spec に `require_initialized_submodule_depth=1` を明示して検証する。

提案テスト名は `test_verify_snapshot_accepts_initialized_top_level_with_uninitialized_nested_submodule`。返った `oracle["submodules"]` の状態が順に `"initialized"`、`"uninitialized"` であることまで固定する。これにより、全深度要求への誤変異も検出できる。どちらも実 repo やネットワークを使わない。

## 変異候補

| 変異行 | 変異 | 必ず落ちるテスト |
|---|---|---|
| `tools/codex_reasoning_ab.py:695-712` の新規 spec 行 | `require_initialized_submodule_depth` を削除する | 負例内の `_snapshot_spec` policy assertion |
| `tools/codex_reasoning_ab.py:1693` 付近の新規 fallback | `expected.get(..., 1)` を `expected.get(..., 0)` にする | `test_verify_snapshot_rejects_uninitialized_top_level_submodule_with_custom_spec` |
| 同新規 gate | gate 全体を `if enforce_closure:` 内へ移す | `git_object_closure=False` を使う同負例 |
| 同新規 depth 算出 | manifest 祖先数を `path.count("/") + 1` に置換する | top-level path が `deps/child` の同負例 |
| 同新規比較 | `depth <= required_depth` を `depth >= required_depth` にする | `test_verify_snapshot_accepts_initialized_top_level_with_uninitialized_nested_submodule` が nested 未初期化を拒否される |

## リスク

- slash 数を深さにしてはいけない。root 直下の `external/ccbench` や `deps/child` は slash を含む。
- prefix 判定には必ず末尾 `/` を加える。単純 `startswith(parent)` は兄弟 path を祖先と誤認する。
- gate を `enforce_closure` の片側へ入れると、独自 spec が `git_object_closure=False` で迂回できる。
- 未初期化 fixture を `git submodule deinit` で作ると admin dir が残り、`tools/codex_reasoning_ab.py:974-980` の「検査不能」例外になりうる。最初から gitlink だけを登録する。
- oracle dict、manifest 行、`_submodule_inventory`、`_git_closure_reasons` は変更しない。特に新 spec key を oracle へ転記しない。
- legacy の未初期化 artifact が replay で赤になるのは互換性事故ではなく本修正の目的だが、親の受入報告では明示する。
- pytest は実行していない。以上は read-only の静的検査結果である。

## 総括

(P1) の深さ 1 裁定と (P2) の verifier 側 fallback をともに支持する。  
深さは slash 数ではなく、manifest path の delimiter-aware な祖先行数から算出できる。  
既定 key は `require_initialized_submodule_depth=1`、欠落時の verifier 既定も 1 とする。  
検出は reason 追加だけで行い、正規 oracle の key 集合と bytes は変えない。  
合成 repo の負例と nested 未初期化を残す正例で、fail-open と過剰拒否の双方を固定する。