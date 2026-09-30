## 変更

- [scan-key patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/patches/fix-cicada-gc-records-scan-key.patch:7): `Tuple::body_` の key が空なら最新版の body の key を使うようにしました。patch の変更行は **+5 / −3** です。
- [CI script](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/.gcfix-ci/run_ci_build.sh:36): F が build 対象 commit の祖先で、`F..<commit>` が1〜2 commit、かつ merge commit を含まないことを検査します。

## 修理の意味と根拠

修理後の `scan()` は次の形です。

```cpp
// Inline inserts can leave the tuple's copied key empty.
std::string key(itr->body_.get_key());
if (key.empty())
  key =
      std::string(itr->latest_.load(memory_order_acquire)->body_.get_key());
```

通常の load・insert で `Tuple::body_` に key がある場合は前回の patch と同じ key を使います。`INLINE_VERSION_OPT=1` の insert でそこが空の場合は修理前と同じ最新版の key に戻るため、後で update された tuple もこの変更によって退行しません。

## 自己検査

- 厳密適用 (a)〜(i): 各構成で `git apply --check` **rc=0**、`patch_files()` → `apply_patch()` **rc=0**。
- 展開木の `transaction.cc` に対する clang-format 14 `--dry-run --Werror`: **rc=0**。
- `bash -n .gcfix-ci/run_ci_build.sh`: **rc=0**。`git diff --check`: **rc=0**。
- CMake build、計算ノードでの走行、CI script の実行時判定は**未実走**です。

## 所有外への波及

指定された2ファイル以外は編集していません。scan-key patch に新しい `#if`、`#define`、`IZANAGI_`、診断出力はありません。`external/ccbench` の `status --porcelain` と `diff --stat` はともに**空**で、元の状態です。

## 未解決

修正後の実行時 trace・ASan 結果と、2 commit の tip に対する CI build は未確認です。

## 総括

指定の2件を修正し、静的検査と9構成での厳密適用を完了しました。commit、submodule の HEAD・index 変更、計算ノード投入は行っていません。