## 所見 — 完了判定

- **must-fix — W5 の待機を aggregate throughput だけで合格にしない。** 根拠: [brief-stage1.md](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/brief-stage1.md:18)、[transaction.cc](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/verbatim/ccbench-F/cc/cicada/transaction.cc:919)。分岐は `thid_ == 1` の commit 冒頭だけなので、4 thread の総 throughput は残る worker に隠され得る。低下しても待機行を実行した証明にはならない。**影響:** 記録が「待機が実際に入った」と過大主張する。**直し方:** 2 thread 以上で runtime flag の 0／十分大きい値を同一 build に交互指定し、複数反復の throughput とともに、worker 1 が `sleepTics` の待機経路に入った直接の実行証拠を残す。`-thread_num=1` は worker 1 が存在しない対照として使える。1000 µs だけの総 throughput 差は合否条件にしない。

- **must-fix — D297 pass と「修正した TU の意図した差分」を別々に記録する。** 根拠: [md_19.txt](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/verbatim/md_19.txt:24)、[check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/tools/check_trace0_preprocess_identity.py:970)。C→G の期待 path は F の 3 file に `cc/cicada/include/transaction.hh` と `cc/cicada/transaction.cc` を加えた集合。header 規則が選ぶ stock・mocc・silo では Cicada consumer がなく、cicada genome は未選定の調査に留まる。既定の `INLINE_VERSION_OPT=0`、`WORKER1_INSERT_DELAY_RPHASE=0` なら Cicada の修正本体も不活性である。**影響:** D297 の緑を、修正した非既定 Cicada configure の同一性または正しさの証明と誤記する。**直し方:** C→G の expected path を更新して規則 v2 を実行し、結果に選定 configure と未選定 cicada を明記する。別に F→G の 2 file の変更行と、どの macro 条件で有効になるかを一次資料へ列挙する。ここでの「意図した変更」は D297 pass の対象外として明示する。

- **should — 24 genome の F 側 8 件再 build は必須ではない。** 根拠: [baseline-tuning-s8.md](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/verbatim/baseline-tuning-s8.md:5)、[md_19.txt](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/verbatim/md_19.txt:21)。既存の F 以前で 8 件失敗という記録と G の 24 件成功を結べば、依頼の build 完了判定に届く。**影響:** 再 build を削っても G の合否は変わらず、対照を新規実測したという記録だけが無くなる。**直し方:** 既存失敗ログの pin・flags と G の条件差を明記する。W5 の F 側失敗も既存ログを使える。

- **must-fix — CI 緑を項目 1・2 の検査として扱わない。** 根拠: [Options.cmake](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/verbatim/ccbench-F/cmake/Options.cmake:49)、[run_ci_build.sh](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/build/run_ci_build.sh:92)。上流 CI の既定 build は両不具合の非既定分岐も `ADD_ANALYSIS=1` も通らない。**影響:** G の CI 2 本が緑でも修正行が compile 不能なまま残り得る。**直し方:** CI 2 本とは別に promotion の 8 genome と W5 の非既定 build を成果物の独立した合否として読む。

## 所見 — 流用の実効性

- **must-fix — T-2854 の judge は OID だけの置換では走らない。** 根拠: [run_judge.sh](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/judge/run_judge.sh:14)、[run_ci_build.sh](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/build/run_ci_build.sh:9)。両 script は親を C2′ に固定し、judge は差分 path を F の 3 file に固定する。**影響:** G が正しくても事前検査で落ち、D297 と CI build の結果が出ない。**直し方:** G の直親を F にし、judge の C 基点は保持したまま親検査を F、C→G の expected path を 5 file に更新する。G を含む complete-history bundle を作り、F.bundle を流用しない。

- **must-fix — md_17 起動器には C／C1 固定と job 固定が残る。** 根拠: [launch_cicada_run.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/launch_cicada_run.py:25)、同[BUILDS・JOBS](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/launch_cicada_run.py:37)、同[checkout](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier-ext/launch_cicada_run.py:1017)。`PIN_C` だけ変えても `STOCK_TPCC` 等の C1 固定、identity plan、既存 job cell、CMake の `OPT=0` が残る。**影響:** 検証結果が G 以外、または promotion を無効にした build に帰属する。**直し方:** job dir の複製で使用 build の base・CMake 値・job cell・identity plan を G 用に限定して更新し、result の `build_source_oids` と compile/cache 値を読む。旧 C／C1 向けの破壊 variant job は今回の結果に混ぜない。

- **must-fix — 較正 driver は現行 G 用のままではない。** 根拠: [driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/tools/vhash_cicada_tuning/driver.py:239)、同[checkout](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/tools/vhash_cicada_tuning/driver.py:452)、[model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/tools/vhash_cicada_tuning/model.py:78)。`patchharness.checkout(pin.CURRENT_PIN)` は旧 pin、待機 build は未定義 macro `WORKER1_INSERT_DELAY_RPHASE_US=1000` を渡し、runtime argv は新しい `-worker1_insert_delay_rphase_us` を渡さない。**影響:** G を作っても W5 は待機 0 のまま測られ得る。**直し方:** job dir の複製で checkout を G に束縛し、待機量を runtime flag に移す。compiler は既存 policy の GCC 11 解決、依存 cache は clean clone、build と出力は計算ノードの scratch を用いる。repo の `pin.py` は変更しない。

- **should — dispatch の並列数と node 時間を再見積りする。** 根拠: [run-build.sh](/work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/run-build.sh:3)、[brief-stage1.md](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/brief-stage1.md:19)。T-2854 は同一 checkout から同時 dispatch しないため木を分けている。D297 の既往約 0.28 node 時間は GCC 2 版を同じ node で並走した実績で、G の header 比較や非既定 build 48 本の所要を保証しない。**影響:** 「4 本同時・合計 1 node 時間未満」が投入計画の確定値になる。**直し方:** job ごとに独立 checkout から dispatch し、P7 は暫定見積りと記す。2 node 時間の確認線は維持する。

## 所見 — 過剰と削除

- **should — A2 は今回の 2 件から外せる。** 根拠: [brief-stage1.md](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/brief-stage1.md:10)、[transaction.cc](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/verbatim/ccbench-F/cc/cicada/transaction.cc:126)。`ADD_ANALYSIS=1` の未定義 `start` は実在する別の compile 不具合だが、依頼の項目 1・2 ではない。**影響:** 入れると G の差分 path は同じでも変更範囲・非既定 build・レビュー対象が増える。**直し方:** 今回は記録に発見事項として残す。入れる裁定なら、その build 成功を別の必須結果にする。

- **should — promotion trace の使い捨て変種を「標準 patch の正しさ判定」と同列に置かない。** 根拠: [instr-cicada-trace.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/patches/instr-cicada-trace.patch:52)、[transaction.hh](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/verbatim/ccbench-F/cc/cicada/include/transaction.hh:207)。標準 patch は promotion と TRACE の同時使用を `#error` で意図的に止める。さらに read_set の重複登録を親が「無害」と断定する根拠はなく、trace の R 行にも影響する。**影響:** `#error` を外した実験の緑を、標準計器で保証された正しさとして記録する。**直し方:** 使うなら job dir の診断変種と明記し、R 行・integrity の実値を読む。標準 patch が当たらない／そのままでは promotion を測れない事実も md_19 の指示どおり記録する。promotion の正しさを主張しないなら変種は削れる。

- **nit — `tpcc_cicada.exe` の promotion 8 本、F cell × 1 thread、format の 2 image は削れる。** 根拠: [brief-stage1.md](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/brief-stage1.md:17)、[md_19.txt](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/verbatim/md_19.txt:21)。24 genome の対象は YCSB、TPC-C F cell は項目 3 の専用 wave が扱う。format は上流相当の clang-format 14 を 1 回通せば本件の判定値は得られる。**影響:** 削ると追加診断値だけが減り、2 件の受入値は変わらない。**直し方:** YCSB 24 件、TPC-C の小走行 M・R2、CI format の 1 環境へ絞れる。一方、CI build 全 protocol、W5 の実行確認、C→G D297 は削れない。

- **should — GCC 2 版の D297 は維持する。** 根拠: [D297.md](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/verbatim/D297.md:22)、[D2293.md](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/verbatim/D2293.md:9)。compiler 依存のため複数 compiler で判定する裁定である。**影響:** 1 版へ削ると G の D297 完了記録が裁定より弱くなる。**直し方:** T-2854 同様 GCC 11・12 を維持する。

## 所見 — 他 wave との重なり

- **must-fix — 一次資料に適用順と重なりの種類を書く。** 根拠: [instr-cicada-trace.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/patches/instr-cicada-trace.patch:52)、同[commit 付近](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/patches/instr-cicada-trace.patch:107)、[instr-cicada-version-lifetime.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/patches/instr-cicada-version-lifetime.patch:828)。trace patch の header hunk は 207 行の直前、transaction.cc の hunk は commit 分岐の前後にある。version-lifetime patch は同じ `commit()` 冒頭に worker 1 の独自待機を追加するので、両 macro を有効にすれば意味上は二重待機になる。broken 系 patch は trace patch が置く `#line 909/934` を context にしている。**影響:** patch の適用失敗、または通っても待機時間を二重に数えた wave 結果が出る。**直し方:** 一次資料に「G を土台に、trace patch、必要なら TPC-C trace patch、その後に各 broken patch」「forwarding 系はその系列の既定順」「version-lifetime の待機 macro と G の W5 macro を同時に有効にしない／同時使用時は合算」と書く。実際の G への適用可否は親の静的・実測確認結果として記録する。

- **should — 親の patch 実測を G 全体へ一般化しない。** 根拠: [brief-stage1.md](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/brief-stage1.md:12)。実測は Cicada file が同一だった C 作業木への `instr-cicada-trace.patch` の適用であり、G や他の cicada patch 54 本の適用結果ではない。行数不変は `#line` の論理行番号維持に役立つが、hunk の context 一致と offset 0 を保証しない。**影響:** pin 前進 wave に未確認の「54 本厳密適用済み」を渡す。**直し方:** G で確認した patch 名・順序・適用結果だけを書く。C での実測は C の事実として残す。

## (P1)〜(P7) への意見

| 項 | 判定 |
|---|---|
| P1 | 行数維持は有益。ただし TRACE=0 や全 patch の無 offset 適用をそれだけで断定しない。 |
| P2 | `write`→`update` は compile 修正の中心。read_set 重複を「無害」と確定せず、promotion の実行結果と trace の R 行で扱う。 |
| P3 | runtime flag と `sleepTics` の置換は source 定義に整合する。実効待機は直接観測が必要。 |
| P4 | A2 は別件として外せる。入れるなら `ADD_ANALYSIS=1` build が必須。 |
| P5 | 既定 YCSB・TPC-C 小走行は妥当。promotion 変種は診断扱い、F cell × 1 は省略可。 |
| P6 | CI 2 本と D297 は必要。非既定 build を独立合否にし、W5 の throughput だけの判定を修正する。 |
| P7 | 0.28 node 時間の D297 先例は参考値。4 job の合計と scratch・dispatch 制約を反映した暫定見積りにする。 |

## 総括

G の 2 件を閉じるには、**G 上の 24 genome build、W5 分岐の直接の実行証拠、標準 trace が適用できる範囲の小走行、上流相当 CI 2 本、C→G の D297、および修正 2 file の意図した差分の記録**が必要です。現在の brief は、W5 の観測量と流用 script の固定値で偽の緑または実行前失敗を生み得ます。今回は指定どおり静的検査のみで、file 編集・test・build は行っていません。