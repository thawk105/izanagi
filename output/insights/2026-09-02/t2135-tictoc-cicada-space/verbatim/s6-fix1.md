## 読んだ資料

- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/s6-parent-remeasure-2.md`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/s4-ruling.md`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/artifacts/dev-wave-t2135-tictoc-cicada-space/s6-review-b.md`
- [orchestrator/campaign/genome.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2135-fix1/orchestrator/campaign/genome.py:188)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2135-fix1/orchestrator/tests/test_campaign.py`
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2135-fix1/external/ccbench/cmake/Options.cmake`
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2135-fix1/external/ccbench/cc/cicada/transaction.cc`

## FIX-1 の修正内容

変更前:

> genome に列挙しない flag は -DCCBENCH_* に現れず、fresh configure では default 0 に落ちるが、既存の非標準 CMakeCache を戻す主張ではない。

変更後:

> 軸から外した SINGLE_EXEC は -DCCBENCH_* に現れず、fresh configure では Options.cmake の default 0 に落ちるが、既存の非標準 CMakeCache を戻す主張ではない。この説明は数値 boolean の SINGLE_EXEC に限定し、delay 系の default は 0 ではなく空値 (unset) である。

`default 0` の主張を `SINGLE_EXEC` に限定し、`fresh configure` を維持しました。

## FIX-2 の修正内容

変更前:

> WRITE_LATEST_ONLY は読み側の可視性が不変で、保守側に余分に abort する最適化軸として含める。

変更後:

> WRITE_LATEST_ONLY は読み側の可視性が不変で、保守側に余分に abort する最適化軸として含める。作用点は transaction.cc:242-262 の blind write 側と transaction.cc:490-529 の validation 側にある。

軸の採否は変えず、validation 側の引用を補完しました。

## 既存 assert 語句の維持確認

静的抽出した cicada notes で、以下を1件ずつ確認しました。

- `SINGLE_EXEC` / `多版から単版`: 維持
- `測るものそのもの` / `fresh configure`: 維持
- `PARTITION_TABLE` / `print 専用`: 維持
- `README の説明と現行コードが食い違う`: 維持
- `WORKER1_INSERT_DELAY_RPHASE`: 維持
- `INSERT_READ_DELAY_MS` / `INSERT_BATCH_DELAY_MS`: 維持
- `計測撹乱ノブ`: 維持
- `WRITE_LATEST_ONLY` / `読み側の可視性が不変`: 維持
- `余分に abort`: 維持
- `(OPT,PROMOTION)=(0,1)` / `(0,0)`: 維持
- `CC / data path の挙動が同一` / `起動時の option 表示だけは異なる`: 維持
- `24` / `YCSB workload`: 維持
- `静的導出` / `実測ではない`: 維持
- `bare define` / `導出不能として残す候補もない`: 維持
- `CLI から個別指定` / `全組合せが異なる挙動`: 維持

## 実走したもの・していないもの

- Python AST による notes の静的確認: PASS。既存 assert 語句と修正語句、計33語句を確認。
- cicada の軸集合、制約束縛、結合文字不在の静的確認: PASS。
- `git diff --check`: PASS。
- pytest、build、benchmark、測定: 未実走。
- 状態は「実装済み・未実走」です。

## 触っていないことの確認

- `TICTOC_SPACE.axes` と `CICADA_SPACE.axes`: 今回の fix では変更なし。
- `_tictoc_no_wait_not_both` と `_cicada_promotion_requires_inline_opt` の return 文: 変更なし。
- `TICTOC_SPACE.notes`: 変更なし。
- `orchestrator/tests/test_campaign.py`: 変更なし。
- `_no_wait_xor`、`SILO_SPACE`、`MOCC_SPACE`: 変更なし。
- `docs/`、`output/`、`external/ccbench/`: 編集なし。
- git add、commit、push、branch 作成・切り替え: 実行なし。

## 総括

FIX-1 は `default 0` の説明を `SINGLE_EXEC` に限定しました。
FIX-2 は `WRITE_LATEST_ONLY` の validation 側作用点を追記しました。
変更は `CICADA_SPACE.notes` の2箇所だけです。
既存 assert 語句はすべて静的確認済みです。
pytest は未実走で、変更は作業ツリーに未 stage のまま残しています。