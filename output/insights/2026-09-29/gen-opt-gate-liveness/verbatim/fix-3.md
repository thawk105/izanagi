## Storage の確認

`cc/silo/transaction.cc` が include する [transaction.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/external/ccbench/cc/silo/include/transaction.hh:7) は `tx_executor_concept.hh` を経て [workload.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/external/ccbench/include/workload.hh:5) を読みます。そこで見える `Storage` は前方宣言だけです。`YCSB` 列挙子の定義は [ycsb.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/external/ccbench/include/ycsb.hh:35) にあり、この翻訳単位からは見えません。

## 修正内容

[B1 patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/patches/broken-silo-b1-unregistered-first-read.patch) から `Storage::YCSB` による絞り込みを除き、key の末尾 byte が偶数かで省略対象を選ぶようにしました。patch 内に、この build は YCSB のみを走らせる旨を 1 行記しました。省いた読みは `(storage, key)` で保持し、commit 直前に `searchReadSet(omitted.storage, omitted.key)` で確認します。一貫読み、副 buffer、計数、`GATE_B1_FIRED` 行は維持しました。[make_patches.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/make_patches.py) に `--b1-only` を加え、指定された patch だけを再生成しました。

| ファイル | 行数 | SHA-256 |
|---|---:|---|
| `make_patches.py` | 209 | `09a398b8dd5cec3ed8398690d4ef991d777bea4f16f67fedae988f31f365f240` |
| B1 patch | 78 | `afebe882d609dc819b9248357af865e17679c6d9ef1a0989e89975b62bdff628` |

## 確認結果

pin の写しで `git apply --check` は計装 patch が **rc=0**、計装 patch 適用後の B1 patch が **rc=0** でした。両 patch 適用後の `cc/silo/transaction.cc` に対する `rg -n 'Storage::YCSB'` は **rc=1、該当なし**。`git diff --check` は **rc=0** です。build は**未実走**です。

`git -C external/ccbench status --porcelain` の出力は空です。

## 総括

指定された 2 ファイルだけを変更し、報告されたコンパイルエラーの原因となる `Storage::YCSB` 参照を B1 patch から除きました。