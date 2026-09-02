## 読んだ資料

指定された 12 path はすべて読めた。読めなかった path はない。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/s1-brief.md`
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/artifacts/dev-wave-t2135-tictoc-cicada-space/s2-plan.md`
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/d1360-verbatim.md`
4. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py`
5. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/tests/test_campaign.py`
6. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/cicada/CMakeLists.txt`
7. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/cicada/transaction.cc`
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/cicada/include/transaction.hh`
9. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/cicada/README.md`
10. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cmake/Options.cmake`
11. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/between_run_floor.py`
12. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/cicada/util.cc`

## 正しさ境界の所見

1. `SINGLE_EXEC` 除外は正しい。これは高速経路ではなく、実行モデルの変更である。

   - `transaction.cc:85-119` では timestamp による version-chain 探索、pending 待ち、aborted version のスキップをすべて外し、無条件に `inline_ver_` を読む。
   - `transaction.cc:235-289` では新しい version の生成と timestamp 順挿入を外し、既存 inline version を write set に置く。特に `update(..., TupleBody&& body)` の `body` は `SINGLE_EXEC=1` 側で消費されず、通常側の `newVersionGeneration(..., std::move(body))` だけで使われる。
   - `transaction.cc:705-707` は既存 inline version の timestamp を更新し、`transaction.cc:762-768,952-955` は abort/commit 後の多版 maintenance を完全に省く。
   - README の「single version concurrency control」という記述 (`README.md:50-51`) はコードと整合するが、判断根拠は上記コードである。

   これを軸にすると、timestamp 可視性を持つ MVCC と単版動作、さらに update payload の扱いまで異なるものを同一 workload として比較する。段 2 の除外判断は十分に根拠があり、過剰除外ではない。

2. `WRITE_LATEST_ONLY` は可視性規則の緩和ではなく、保守的な abort 方針を加える最適化軸である。段 2 の採用判断を支持する。

   - 無効時の blind update は、`transaction.cc:263-271` で version chain を辿り、transaction timestamp の位置へ挿入する。
   - 有効時は `transaction.cc:242-262` で latest version が自 transaction より新しければ abort する。pending version が後で abort する可能性があっても自分を abort するため、これは false-positive を許す保守側の早期 abort である。
   - validation でも `transaction.cc:490-496` が latest を再読し、より新しい version があれば reject する。成功時だけ `transaction.cc:511-526` で head または timestamp 順位置へ install する。
   - 読み側の可視性選択 `transaction.cc:89-119` はこの flag を参照しない。

   有効時には「古い timestamp の blind write が成功する履歴」が減るが、成功した transaction が従う serializability 判定や read visibility は変わらない。正しさを緩めて速く完了させる flag ではなく、余分に abort して許容スケジュールを狭める flag である。`SINGLE_EXEC` との線引きは一貫している。

3. inline/reuse 系は、提示コード上は古い版の可視集合を変えない。

   - version chain を切り離す条件は `transaction.cc:806-838` の `MinRts` と `min_wts_` で共通であり、その後に `gcAfterThisVersion()` が呼ばれる。
   - `INLINE_VERSION_OPT` は切り離された inline version の権利返却 (`transaction.hh:178-183`)、新 version の inline 確保 (`:219-227`)、未 install version の abort cleanup (`:351-356`) を変える。
   - `REUSE_VERSION` は切り離し後の object を pool に戻すか delete するか (`transaction.hh:185-189`)、および pool から再初期化して取得するか (`:229-244`) を変える。
   - `util.cc:219-236` の DB teardown でも inline version を delete 対象から外すが、workload 実行中の可視性には関与しない。
   - promotion は読んだ body のコピーを内部 write にする (`transaction.hh:199-215`)。値の意味は保持する一方、物理 version と競合・abort は増減し得るため、まさに測定対象となる内部最適化である。

4. 今回の `SPACES` 登録だけでは、cicada の未検証測定経路は新たに開かない。ただし「判定器が唯一かつ完全な正しさ関門」という理解は誤りである。

   - `genome.py:108-118` の登録は宣言と lookup だけである。射影内の `space_for()` caller は `test_campaign.py` の test に限られる。
   - floor の `BASELINES` は silo/mocc だけ (`between_run_floor.py:58-71`) で、cicada は `:344-347` で unknown protocol として measurement 前に拒否される。
   - cicada の CMake SOURCES は `transaction.cc` と `util.cc` (`CMakeLists.txt:1-3`) だが、両 source に trace include、`#if TRACE`、trace hook 呼出しがないため、現行の文字列判定も false になる。
   - 一方、その判定器自身が「hook の意味論、verifier 通過、測定の正しさを証明しない」と明記している (`between_run_floor.py:111-121`)。さらに `measure_point_floor()` は直接呼べば判定を通らない (`:202-252`)。CLI も通過後は `trace=False` build を直接測るだけで、verifier は実行しない (`:362-403`)。
   - 別経路では、screening が verifier より先に bench を実行できることを test が固定している (`test_campaign.py:7532-7539,7630-7657`)。ただし official commit writer は certified 判定後に閉じている (`:7663-7749`)。

   したがって、今回の成果物は宣言に留まり正しさ境界を直ちに変えない。しかし、既存システム全体について「正しさ検証前の測定が存在しない」とは主張できない。

## 整合・実効性の所見

1. promotion の含意制約は正しい。promotion を軸ごと落とす案は不適切である。

   - `transaction.cc:128-135` の唯一の実行 site は `INLINE_VERSION_OPT` の内側にある。
   - `transaction.hh:199-215` の定義も同じく `INLINE_VERSION_OPT` の内側にある。
   - したがってデータパス上、`(OPT,PROMOTION)=(0,1)` は `(0,0)` と同じである。段 2 の述語 `not PROMOTION or OPT` は `(0,1)` を除外するため、同一挙動の 2 点は残らない。
   - 一方、`(1,0)` と `(1,1)` は promotion 呼出しの有無が異なる。promotion 自体を落とすとこの有効な比較を失う。

   ただし `util.cc:330` の diagnostic print は OPT の外側で promotion 値を表示する。従って段 2 の「完全に inert」「同一 binary behavior」は厳密には強すぎる。正確には「CC/data-path behavior は同一で、起動時の option 表示だけ異なる」である。

2. `PARTITION_TABLE` の print 専用判定は一次資料で確認できた。親と段 2 の結論は正しい。

   `PARTITION_TABLE` の実コード出現は `ShowOptParameters()` の表示だけ (`util.cc:326-336`) である。`util.cc:189-217` の partition 初期化らしきコードは全体がコメントアウトされ、flag にも束縛されていない。従って探索軸としては死にフラグである。

   ただし README は「thread 数に table を分割して競合を防ぐ」と記述しており (`README.md:46-47`)、現行コードと明確に食い違う。放置すると将来の導出担当が README を根拠に死に軸を復活させ得るため、notes では「README の説明と異なり、現行 code は print のみ」と残すのが正確である。

3. `SINGLE_EXEC` が軸から外れたとき通常 build で 0 になる、という前提は静的には成立する。ただし「明示的に固定」ではなく「未指定なので default に落ちる」である。

   - default は `Options.cmake:33` の 0。
   - cicada target はそれを `SINGLE_EXEC` へ写像する (`CMakeLists.txt:8`)。
   - `Genome.cmake_defines()` は genome にある flag だけを `-DCCBENCH_*` にすることが既存 test で固定されている (`test_campaign.py:304-310`)。探索 build が全 CMake flag を明示する証拠はなく、逆に列挙した flag だけを明示する証拠がある。

   従って通常の fresh configure では 0 になる。既存の非標準 CMakeCache まで強制的に 0 に戻す主張ではないため、段 2 notes の「default 0」を「0 に固定」と言い換えない方がよい。

4. 空間サイズの workload 範囲は段 2 プランで明示されている。

   cicada は `ycsb tpcc bomb sbomb` を build 対象にする (`CMakeLists.txt:3`)。段 2 notes は `s2-plan.md:118-127` で 24 通りを「YCSB 向け」「YCSB workload での静的導出」と限定し、test 名も同じ範囲を示す (`s2-plan.md:167-172`)。従って mocc 先例との整合は取れている。他 workload の build 成功、軸の実効性、certification まで主張していない点も正しい。

5. 段 2 の提案 test は主要制約について非恒真である。

   promotion pair を厳密に `{(0,0),(1,0),(1,1)}` とする test は、制約削除と逆向き制約を検出できる。軸集合の完全一致 test は `SINGLE_EXEC` や delay flag の混入を検出する。現行 test はまだ cicada の KeyError を要求している (`test_campaign.py:248-251`) ため、計画どおり期待反転が必要である。

## cicada 各 flag の性格判定

| flag | 判定 | 根拠 |
|---|---|---|
| `BACK_OFF` | 最適化軸 | abort/leader work の待機方針のみ。`transaction.cc:770-772,962-966`; `Options.cmake:20` |
| `INLINE_VERSION_OPT` | 最適化軸 | inline object の確保、GC 権利返却、abort cleanup、DB teardown を切替。可視性 cutoff は共通。`transaction.hh:173-189,217-227,343-365`; `transaction.cc:806-838`; `util.cc:219-236` |
| `INLINE_VERSION_PROMOTION` | 最適化軸、`PROMOTION => OPT` 制約あり | 同じ body の内部 version promotion。全データパス site が OPT 内。`transaction.cc:128-135`; `transaction.hh:199-215` |
| `REUSE_VERSION` | 最適化軸 | 到達不能となった version object の pool 再利用と再初期化。`transaction.hh:173-197,229-244,358-364` |
| `SINGLE_EXEC` | 測定対象の変更、除外 | timestamp 可視性、version 生成・挿入、maintenance を迂回し単版化。`transaction.cc:85-119,235-289,705-707,762-768,952-955` |
| `WRITE_LATEST_ONLY` | 最適化軸 | blind write の historical install を許すか、latest でなければ保守的に abort するかを切替。read visibility 自体は不変。`transaction.cc:242-282,488-529` |
| `WORKER1_INSERT_DELAY_RPHASE` | 非軸、計測撹乱 | 特定 worker に人工 delay。`transaction.cc:919-927`; `Options.cmake:49` |
| `INSERT_READ_DELAY_MS` | 非軸、計測撹乱 | 人工 delay 用 cache option。`CMakeLists.txt:12`; `Options.cmake:35-39` |
| `INSERT_BATCH_DELAY_MS` | 非軸、計測撹乱 | 人工 delay 用 cache option。`CMakeLists.txt:13`; `Options.cmake:35-39` |
| `PARTITION_TABLE` | 非軸、print 専用の死にフラグ | 実コードは option 表示だけ。`util.cc:326-336` |
| `TRACE` | 非軸、正しさ測定モード | trace-enabled correctness と trace-disabled performance を分ける mode であり最適化ではない。`Options.cmake:14-20` |

## 親 brief の (P3) への判定

親の「`SINGLE_EXEC` と `WRITE_LATEST_ONLY` は最適化軸である」という一括裁定は覆す。2 flag を分けなければならない。

- `SINGLE_EXEC`: 覆す。最適化軸ではなく単版実行へのモデル変更であり、登録しない。
- `WRITE_LATEST_ONLY`: 支持する。可視性規則や serializability を緩めず、blind write の許容スケジュールを保守側に狭める abort/install 最適化であり、登録する。

従って段 2 プランが下した「前者除外、後者採用」という線引きは正しい。

## 登録すべきでない軸

- `SINGLE_EXEC`: 多版 MVCC と同じ測定対象ではなくなる。update payload の扱いも通常経路と異なる。
- `PARTITION_TABLE`: 現行 code では option 表示以外に効果がない。
- `WORKER1_INSERT_DELAY_RPHASE`: 特定 worker への人工 delay。
- `INSERT_READ_DELAY_MS`、`INSERT_BATCH_DELAY_MS`: 人工 delay。
- `TRACE`: correctness/performance build mode の境界であり、性能最適化軸ではない。

`WRITE_LATEST_ONLY`、`INLINE_VERSION_OPT`、`INLINE_VERSION_PROMOTION`、`REUSE_VERSION`、`BACK_OFF` は静的に分類できる。今回の候補中、軸の性格自体を「導出不能」として落とすべきものはない。cicada の verifier 実測が未成立であることは certification の未完了であって、軸分類不能とは別である。

## 裁定パッケージ候補

- 既存の pre-verifier measurement surface の扱いを別 package で明示する候補がある。`between_run_floor.measure_point_floor()` の直接呼出し、text-only trace evidence 後の trace-disabled floor、pipeline screening の verify 前 bench が存在する。今回の登録では実装変更しないが、将来 cicada を floor/campaign consumer へ接続するとき、D1360 の「未検証性能観測を official report・selector・順位へ入れない」をどの admission で強制するかを独立に確認すべきである。
- cicada trace-hook 移植時に、`INLINE_VERSION_PROMOTION` が作る同値 body の内部 write を workload write として verifier に見せるか、内部 maintenance として区別するかも別 package の対象である。今回の genome 登録 scope では実装しない。

## 見落としの自己申告

- 読めなかった指定資料はない。
- pytest、build、benchmark、verifier は実走していない。緑は主張しない。
- production pipeline 本体は射影対象外だったため、screening と commit gate の確認は `test_campaign.py:7532-7749` が固定する契約に基づく。repo 全体の未射影 caller 閉包までは独立に証明していない。
- `WRITE_LATEST_ONLY` の判定は制御フロー上の静的判定であり、runtime の性能、starvation、verifier 緑を主張しない。

## 総括

`SINGLE_EXEC` は単なる高速化ではなく、多版の可視性・version 管理・update 経路を変えるため除外が必須である。
`WRITE_LATEST_ONLY` は正しさを緩めず、より多く abort する保守的な CC 最適化であり採用してよい。
promotion の含意制約は正しく、promotion 自体を落とす必要はない。
`PARTITION_TABLE` はコード上 print 専用で、README の機能説明は現行実装と食い違う。
今回の登録は測定経路を直ちに開かないが、既存の pre-verifier measurement surface は別 package で扱うべきである。