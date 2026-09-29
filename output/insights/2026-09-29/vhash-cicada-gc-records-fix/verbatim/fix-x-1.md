## 変更

- [scan-key patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/patches/fix-cicada-gc-records-scan-key.patch:1)を作成しました。`scan()` の key 取得を `Tuple::body_` に変更し、コメントを更新しました（+2 / −3行）。
- [ASan 用の使い捨て patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/.gcfix-work/asan-abort-uaf-workaround.patch:1)を作成しました。`writeSetClean()` で、abort が削除済みの INSERT 要素を読み飛ばします（+1行）。
- [起動器](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/.gcfix-launcher/launch_gcfix_run.py:1193)の CUSTOM identity 判定に、各 TU の compile command 一致を追加しました。命令列一致も引き続き要求します。

## 修理の意味と根拠

修理後の `scan()` の該当部分です。

```cpp
for (auto&& itr : scan_res) {
  // Copy the index tuple's key before the latest version changes.
  std::string key(itr->body_.get_key());
  ReadElement<Tuple>* re = searchReadSet(s, key);
```

`Tuple::body_` は [tuple.hh:34](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/external/ccbench/cc/cicada/include/tuple.hh:34) にあります。初期 load は [tuple.hh:74](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/external/ccbench/cc/cicada/include/tuple.hh:74) の `init()` で最初の版の body からコピーし、insert は [transaction.cc:314](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/external/ccbench/cc/cicada/transaction.cc:314) で body 付きの版を作って [tuple.hh:95](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/external/ccbench/cc/cicada/include/tuple.hh:95) の `init()` に渡します。版の生成は [transaction.hh:217](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/external/ccbench/cc/cicada/include/transaction.hh:217) です。通常の body 付き最新版では同じ key になり、body の無い削除版が最新版のときに空 key を避けられます。`INLINE_VERSION_OPT=1` の初期化でも inline 版の body からコピーするため、初期 body 自体に key が無い場合は修理前後とも空 key です。

## 自己検査

- 厳密適用 (a)〜(i)：各構成で scan-key patch 最終適用の `git apply --check` **rc=0**、`patch_files()` → `apply_patch()` **rc=0**。
- F + gc-records + scan-key 上の ASan 回避 patch：`git apply --check` **rc=0**。
- CCBench の `.clang-format` を含む展開木で `/usr/bin/clang-format --dry-run --Werror`：**rc=0**。
- `python3 -m py_compile`：**rc=0**。新 spec 相当の CUSTOM `--dry-run`：**rc=0**。5 patch と identity 両側の適用確認もすべて rc=0。
- build、ASan 走行、実行時 identity 判定、trace 判定は**未実走**です。

## 所有外への波及

新 patch に `#if`、`#define`、`IZANAGI_`、MOCC marker はありません。既存テストの期待値と所有外ファイルは変更していません。`external/ccbench` の `status --porcelain` と `diff --stat` はともに空でした。

## 未解決

ASan と V3 の実行結果、および実行時の compile command・命令列一致は親の確認走行待ちです。

## 総括

指定された3ファイルの修正と静的・適用検査を完了しました。commit、submodule の HEAD・index 変更、計算ノード投入は行っていません。