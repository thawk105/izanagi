## 対応表

| 所見 | 判定・根拠 | 放置時に成果物がどう変わるか |
|---|---|---|
| F1 | **closed**。patch の戻し指定はファイル名なしの `#line N`（[patch:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:26) ほか）。各 hunk の戻し先は、stock の対応行を使う前処理比較（[test:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:187)）で照合され、親報告では PASS。 | この修正について、既定 build の `__FILE__` が変わる原因は解消。 |
| F2 | **partial**。行番号とファイル名を比較し、include 行も別途比較する（[test:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:146)）。`.rodata` 比較も追加済み（[driver:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:303)、[driver:411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:411)）。ただしテストは include を展開せず、実 compile と `.text`／`.rodata` の結果は未着。 | smoke が不一致なら、既定 build を inert とする根拠が成立しない。 |
| F3 | **partial**。待機後の記録は同じ版に対して行い、追加走査はない（[patch:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:217)）。status が単調に確定する通常経路では二重計数もしない。ただし最初の `VLIFE_VISIT` 後、外側の待機条件評価前に pending が committed になると、待機本体に入らず記録を失う（[patch:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:192)、[stock:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/external/ccbench/cc/cicada/transaction.cc:108)）。 | 稀な確定競合で先頭 K の候補と直上 wts が欠ける。 |
| F4 | **partial**。K 別の `deep_read_zero`／`candidate_read_zero` と parser の包含関係検査は整合する（[patch:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:243)、[driver:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:124)）。しかし deleted 版でも `vlife_reads_` を増やしてから失敗を返す（[patch:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:261)、[patch:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:268)）。 | 失敗 read の後の深い read が「既読 0 件」から外れ、両 field が過少になる。 |
| F5 | **closed**。validation の起点を `scan_start` として raw に出し、位置図は read site のみを使う（[patch:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:557)、[plot:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:132)）。 | 異なる起点の位置を同一尺度として図で比較する問題は解消。 |
| F6 | **partial**。`measure` は `--smoke-json` を必須とし、commit・patch SHA と選定 N を読む（[driver:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:309)、[driver:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:433)）。しかし一致する公開 hash と任意の許容 N を書いた JSON も通る。smoke の成功や較正 probe との整合は検証しない。 | 未較正の N を正式 measure raw にできる。 |
| F7 | **closed**。図 1 に read 位置、図 3 に生成・上書き基準の回収時年齢を追加（[plot:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:130)、[plot:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:167)）。図 2 は K と楽観的候補率、図 3 は境界年齢・公開間隔・回収時年齢・論理生存版数を描く。 | 指定項目の図上での欠落は解消。 |
| F8 | **closed**。workload、長い tx、GC 間隔、N、反復数を各図の注記に置く（[plot:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:48)、[plot:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:102)）。 | 図単体で条件を読めない問題は解消。 |
| F9 | **closed**。各較正 probe の直前に単独性確認がある（[driver:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:364)）。 | 競合を確認せず maxrss を採る経路は解消。 |
| B2 | **closed**。bucket 番号の平均を廃し、上界値による中央値・p90 を描く（[plot:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:41)、[plot:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:182)）。 | 時間軸の擬似的な平均 bucket 表示は解消。 |
| P1 | **closed**。時間系は 42 bucket、raw・parser・作図は同じ上界列を使う（[patch:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:46)、[patch:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:556)、[driver:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:38)）。実数照合では 2 µs→上界 2、3 µs→4、100,000 µs→131,072 で一致する。 | 100,000 µs 付近が一律 overflow になる問題は解消。 |

## 新たな所見

- **must-fix:** F3 の確定競合を塞ぐ必要がある。最初の観察が pending だった版について、外側の待機ループを通らず確定した場合も一度だけ記録すること。
- **must-fix:** F4 の「既読」を成功 read に合わせる必要がある。現状は deleted による失敗も既読数を進める。
- **must-fix:** F6 は入力 JSON の自己申告だけで N を束縛している。smoke の成功と probe に基づく選定を検証できる形で measure に結び付ける必要がある。
- **実走待ち:** F2 の実 binary 比較は親が投入した smoke の結果で確定する。既存テストの期待値変更、登録件数 pin の変更、条件 ID の受理集合の変更は、この commit の差分にはない（[commit の変更対象](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:1)、[条件選択:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:57)）。raw schema の受理集合は新 field に合わせて意図的に変更されている。

## 変異の被覆

| 変異 | 単一理由で殺す test nodeid |
|---|---|
| MUT-1 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_json_line_contract` |
| MUT-2 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_k_boundary_and_condition_subset`。patch の `>=` を文字列で固定しており、C++ の境界実行までは検査しない。 |
| MUT-3 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_patch_default_preprocess_matches_stock` |
| MUT-4 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_k_boundary_and_condition_subset` |
| MUT-5 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_worker_sum_and_readonly_denominator` |
| MUT-6 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_patch_default_preprocess_matches_stock` |
| MUT-7 | `orchestrator/tests/test_vhash_cicada_vlife.py::test_smoke_identity_binds_records` |

MUT-1〜5 はテスト構造からの判定、MUT-6・7 は fix 子が変異実走を報告しているが、この再レビューでは再実走していない。

## 総括

**NO-GO。** 残る must-fix は F3 の確定競合、F4 の失敗 read 計数、F6 の較正結果への実質的な束縛。加えて、既定 build の inert 判定は投入済み smoke の `.text`／`.rodata` 結果を待つ。