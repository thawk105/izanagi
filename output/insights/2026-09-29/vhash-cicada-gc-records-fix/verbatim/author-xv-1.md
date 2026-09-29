## 変更

- [修理 patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/patches/fix-cicada-gc-records.patch:1): 16 行。`gc_records()` の変更は **+5 / −1 行**で、上限内です。
- [起動器](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/.gcfix-launcher/launch_gcfix_run.py:604): build 別の `runs`、`cmake_extra`、6 種の `expect`、CUSTOM の TRACE=0 identity 比較を追加。既存 field と job は維持しました。
- [一段変異](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/.gcfix-work/onelevel-cicada-gc-records.patch:1) と [計数 patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/.gcfix-work/count-gcfix-skips.patch:1): 各 16 行、26 行。
- [CI script](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/.gcfix-ci/run_ci_build.sh:9): 親 OID を F に、作業ディレクトリ名とエラー文言を本 wave 用に変更しました。

## 修理の意味と根拠

[修理 patch の 7–13 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-x/patches/fix-cicada-gc-records.patch:7) は、最上段の wts 判定を保ち、連続する aborted 版を何段でも読み飛ばします。到達先が null または deleted 以外なら ERR、deleted なら従来の回収を行います。観測対象の設定では validation・commit・abort の経路を変更しないため、取引の受理集合は変わりません。

修理後の `gc_records()` 全文:

```cpp
void TxExecutor::gc_records() {
  // TODO: GC condition // const auto r_epoch = ReclamationEpoch;

  // for records
  while (!gc_records_.empty()) {
    Tuple* rec = gc_records_.front();
    Version* latest = rec->ldAcqLatest();
    if (latest->ldAcqWts() >= MinRts.load(memory_order_acquire)) break;
    // Later delete attempts can abort while their versions remain in the chain.
    while (latest != nullptr && latest->ldAcqStatus() == VersionStatus::aborted)
      latest = latest->ldAcqNext();
    if (latest == nullptr || latest->ldAcqStatus() != VersionStatus::deleted)
      ERR;
    delete rec;
    gc_records_.pop_front();
  }
}
```

F の `cc/cicada` は pin C と同一なので、F に当てた差分も次のとおりです。

```diff
-    if (latest->ldAcqStatus() != VersionStatus::deleted) ERR;
+    // Later delete attempts can abort while their versions remain in the chain.
+    while (latest != nullptr && latest->ldAcqStatus() == VersionStatus::aborted)
+      latest = latest->ldAcqNext();
+    if (latest == nullptr || latest->ldAcqStatus() != VersionStatus::deleted)
+      ERR;
```

## 自己検査

| 実走した確認 | rc |
|---|---:|
| `/usr/bin/clang-format --dry-run --Werror`（pin C に最終 patch を当てた `transaction.cc`） | 0 |
| 厳密適用 (a) C、(b) C+instr、(c) C1′+instr+tpcc、(d) F、(e) F+instr+tpcc、(f) F+instr+tpcc+broken：各 `git apply --check` と `patch_files()` → `apply_patch()` | 全て 0 |
| 参考 (g) C+version-lifetime、(h) C+forwarding-variant+forwarding-gc：`git apply --check` | 両方 0 |
| 計数 patch（F→instr→tpcc→fix→count）：`git apply --check` と harness 適用 | 0 |
| 一段変異を C と F に直接適用：`git apply --check` と harness 適用 | 両方 0 |
| `python3 -m py_compile`、`--list-jobs`、新 field と identity 両側の適用確認を含む `--dry-run`、`bash -n` | 全て 0 |

計算ノードへの投入、CMake build、実行時の期待値判定は**未実走**です。

## 所有外への波及

新 patch に `IZANAGI_`、新しい `#if`、MOCC marker はありません。したがって `test_p3_s4_loop.py` の裸マクロ登録、`test_ccbench_spawn_sites.py` の前処理条件走査、`test_mocc_template_proof.py` の marker 走査に新たな対象を作らないことを静的に確認しました。これらのテスト自体は未実走です。

`external/ccbench` は直接編集していません。最終確認の出力は `HEAD=68106660686232781bca3be792a750d3e19d7a8a`、`git -C external/ccbench status --porcelain` は空、`git -C external/ccbench diff --stat` も空でした。検査用の展開木は削除し、親から渡された参照用診断 patch は残しました。

## 未解決

F の CI build、ASan、TRACE=0 の命令列 identity、事前登録した各 run の合否は親による計算ノード実行待ちです。

## 総括

指定範囲の実装と静的・適用検査は完了しました。commit と submodule の HEAD・index の変更は行っていません。