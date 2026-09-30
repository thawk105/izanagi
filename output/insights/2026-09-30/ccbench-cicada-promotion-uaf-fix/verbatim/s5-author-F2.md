## 変更の中身（F1・F2・F3、file:line）

- **F1:** [transaction.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-f/md32-scratch/files/cc/cicada/include/transaction.hh:201) で、読み取り専用 tx の promotion を抑止しました。
- **F2:** [cicada_op_element.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-f/md32-scratch/files/cc/cicada/include/cicada_op_element.hh:35) に promotion 由来の目印を追加し、[transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-f/md32-scratch/files/cc/cicada/transaction.cc:205) で後続 `update()` の body を新版へ移すようにしました。
- **F3:** [transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-f/md32-scratch/files/cc/cicada/transaction.cc:754) で、INSERT tuple を退避し、索引から除去、`writeSetClean()`、delete の順にしました。

3 本の [差分と commit message 案](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-f/md32-scratch) を置きました。commit はしていません。使い捨て clone は削除済みで、`external/ccbench/` は編集していません。

## 現行挙動と変更後の挙動

従来は読み取り専用 tx も promotion され、promotion 後の `update()` は既存 write を見つけると body を捨て、abort は INSERT tuple を `writeSetClean()` より先に解放していました。変更後はそれぞれ抑止、body の置換、解放順の修正が行われます。promotion 以外の既存 write への二重 update は従来どおり素通りです。

## 検査の結果（実走範囲・未実走）

- clang-format 14：変更 3 file、rc=0。
- `g++-11 -std=c++20 -fsyntax-only`：指定の 4 文脈すべて rc=0。
- 前処理比較：既定と `OPT=1, PROMO=0` の両方で、意味のある差分は F3 の abort 本文のみ。生の差分には `__LINE__` による診断表示の行番号変化が 2 か所あります。
- 計装 patch：trace は単独、TPC-C は trace 適用後の `git apply --check` がともに rc=0。
- F1→F2→F3：土台から各 `git apply --check` と適用が成功し、完成した 3 file と byte 単位で一致しました。`git diff --check` も rc=0。

上流 CI の全 build、計算ノードでの走行、ASan は**実装済み・未実走**です。

## 波及の静的列挙

TPC-C・YCSB の tx ループは Cicada の `TxExecutor` を使うため変更の利用側です。他 protocol の file は変更していません。既存の `cicada-forwarding-*`、`cicada-ro-gcflag-variant`、`cicada-vhash-hot-block-variant`、`broken-cicada-*`、`fix-cicada-gc-records*` の Cicada hunk は、update・abort 周辺の文脈または行位置の再確認対象です。これら既存 patch の適用検査は実走していません。

## 総括

親が commit に使える 3 本の差分、message 案、完成 file を `md32-scratch/` に残しました。F3 は報告された abort 中の UAF 順序を直しますが、並行読み手の tuple 寿命と `OPT=0` の既存の未回収は、この修理範囲外です。