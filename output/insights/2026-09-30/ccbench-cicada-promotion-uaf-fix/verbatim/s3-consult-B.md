## 所見 — 研究前進への対応

- **must-fix** — P1 の最小案は読み取り専用 tx の promotion を止めるだけです。TPC-C は読み取り専用指定を立てないため、この案で YCSB の巡回が消えても TPC-C の異常終了は閉じません。根拠: [plan:17,25,42](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:17)、[依頼:13,20](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/md_32.txt:13)。**放置時:** promotion 修理 commit の原因帰属と TPC-C 完走の確認が分離したままになります。**直し方:** YCSB の巡回と TPC-C の異常終了を別々に帰属し、後者が残ればその原因の修理まで単位 F の完了条件に含める。

- **should** — 削れない核は、8 genome の修理後 build、代表 genome の YCSB・TPC-C 判定、TPC-C の反復完走、UAF の修理前後 ASan、および壊しの witness 帰属です。根拠: [依頼:15–22](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/md_32.txt:15)、[plan:42–44](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:42)。**放置時:** いずれかを削ると、該当する修理 commit の効果または判定器の検出力を成果物で示せません。**直し方:** この核を固定し、修理前の8 genome *全数* build や CI の重複実行は要求に結び付く場合だけ行う。

## 所見 — 実効性と見積り

- **must-fix** — 「前 wave の実行本文を流用できる」は広すぎます。`build_genomes.py` は27 build と待機実験まで固定し、F の直子・変更2 path を要求します。`launch_cicada_run_g.py` は G の直子、固定 build 群、旧診断 patch、`ALL|DIAG` だけを受けます。CI build と D297 script も F の直子を要求するため、merge tip／修理 tip のままでは入力検査で止まります。根拠: [build_genomes.py:214–33](/work/1/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:214)、[launch_cicada_run_g.py:53–66](/work/1/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:53)、[run_ci_build.sh:40–52](/work/1/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/run_ci_build.sh:40)、[run_judge.sh:71–85](/work/1/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/run_judge.sh:71)。**放置時:** build・CI・判定の記録が得られず、見積りの条件も実行不能です。**直し方:** CMake 設定、macro 束縛、判定器呼出し、CI コマンドを部品として流用し、bundle・OID・merge 親・対象 genome／cell・期待失敗の集計を今回用に組み直す。`check_format_ci.sh` は checkout を渡せばほぼそのまま使えます。`check_patch_apply.sh` は全 Cicada patch の旧系列を列挙するため、必要な「tip→計装→壊し」の厳密適用には対象系列を絞る必要があります。

- **must-fix** — 診断「8 条件 ×45秒」は plan 自身の列挙と一致しません。YCSB 対照／診断だけで8走、TPC-C は4回避条件×2 cell に土台・初回 Debug／ASan が加わり、再現不安定ならさらに増えます。壊しの build・判定も「壊し・CI 250秒」に明示されていません。根拠: [plan:15–17,44,52](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:15)、[前 wave:144–152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:144)。**放置時:** 0.64 node 時間という投入見積りが過小になり、2 node 時間の判断ができません。**直し方:** build と走行を variant×cell×反復で数え直し、診断・確認・CI を別 request に分けて合算する。前 wave の690秒、gc wave の1,024秒は別の条件集合の実績としてのみ使う。

- **should** — `launch_gcfix_run.py` の `CUSTOM` は再利用しやすい一方、許可する base が C・C1・F に固定され、既定の Cicada macro も promotion 設定ではありません。前 wave の promotion trace は repo 外で `#error` を外した診断変種です。根拠: [launch_gcfix_run.py:33–55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/launch_gcfix_run.py:33)、[同:1418–44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/launch_gcfix_run.py:1418)、[前 wave:103–105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:103)。**放置時:** 別 SHA・別 genome の結果を今回の確認として誤記し得ます。**直し方:** base 許可、macro、patch 順、判定条件を今回用に限定して直し、ASan では `detect_leaks=0`、TPC-C では反復ごとの完走／異常終了を保存する。

## 所見 — 土台・D297・所有

- **must-fix** — D297 は「拒否 rc＋非 Cicada path 差分0」だけでは、依頼の「意味が変わる TU を除いて取り直し」を満たしません。path が同じでも各 TU の前処理結果はこの記録からは分かりません。根拠: [依頼:22](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/md_32.txt:22)、[plan:9,15,46](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:9)、[前 wave:129–134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:129)。**放置時:** 記録に「取り直した」と書けず、新 tip の D297 pass も言えません。**直し方:** 意味が変わる Cicada TU を明示して除き、残る TU の同一性結果を今回の tip で取り直す。既存検査器の拒否は別に記録し、pass と呼ばない。

- **should** — merge 土台は TPC-C の既知の削除経路欠陥を避け、両既存 SHA を保存する合理的な選択です。ただし、新 branch を push 候補の「一本化決定」と扱ってはいけません。根拠: [plan:34–38](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:34)、[T-2921・T-2924](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/worklog-items-T2921-T2922-T2924-T2925.md:1)。**放置時:** 記録が人間の push・branch 整理の裁定を先取りします。**直し方:** merge は今回の local 検証土台と明記し、既存 branch を動かさず、push・pin の選択を人間手番として残す。

- **should** — 所有外の `fix-*.patch` 新設や計装 patch の repo 内改変は plan にありません。一方、依頼の成果物は ledger entry を求め、plan は先例に従い登録しない扱いです。根拠: [依頼:26–33](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/md_32.txt:26)、[plan:19,38,50](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:19)、[patches/README.md:965–990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix/patches/README.md:965)。**放置時:** ledger 成果物の有無が依頼と食い違います。**直し方:** 壊し patch を既存の非登録先例で扱うなら、依頼の ledger 指定との相違と理由を一次資料に明記する。`fix-*.patch`、gitlink、既存計装 patch は増改変しない。

## 所見 — 過剰

- **should** — 単位 D の全候補計数を一括実装する必要はありません。early abort の status 集計、版 pointer の回収・再利用追跡、読み取り専用転換停止は、最初の witness・backtrace で該当経路が示されてからで足ります。根拠: [plan:15–17](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:15)。**放置時:** 診断用 build と走行が増え、修理 commit の帰属に使わない記録が増えます。**直し方:** まず巡回 witness と検証起点の差、TPC-C 最初の失敗点を採る。示された候補にだけ一要因対照を足す。witness の tx・key・版と壊し発火の対応は削らない。

- **nit** — 確認段で「修理前後を全 cell 交互」と、診断段の K・R 対照反復が重なります。CI も修理後 tip に一度通せば要求を満たします。根拠: [plan:15,42,46](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:15)。**放置時:** 同じ失敗事実と CI 結果を重測し、node 時間を消費します。**直し方:** 診断で得た修理前再現を同じ SHA・設定の対照として再使用し、修理後の受入走行と最終 tip の CI に集中する。

## 総括

plan の修理前後の対照と merge 土台は有効です。先に直すべき点は、**TPC-C 原因を独立に閉じること、旧 script の固定前提を今回用に直すこと、条件数から node 時間を再計算すること、D297 の未変更 TU を実際に取り直すこと**です。これは指定資料の静的検査による所見で、build・テストの実測は行っていません。