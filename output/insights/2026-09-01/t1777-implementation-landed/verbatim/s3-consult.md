## 所見

- [real] balanced5 の terminal-invalid recovery は、実走中断後の典型状態では発火しない — `orchestrator/campaign/wal.py:1897-1916` — `build_done`、`verify_done`、`bench_done` のどれかが active attempt の開始後にあると、abort 生成箇所 `wal.py:1962-1983` より前に例外となる。片側 commit 後も未 commit 側には build/verify があるため同じである。着地済みなら、balanced5 に限りこの状態を terminal-invalid abort へ閉じる分岐と、verify 後中断・片側 commit の試験が存在するはずである。

- [real] 現 pilot profile は登録されているが、`--study-id paper-story-a1-20260901-balanced5-pilot-v1` から実行可能ではない — `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:87-90` — preregistration が `null` で、submit は `paper_story_a1_paired.py:2341-2344`、measure も `paper_story_a1_paired.py:4906-4913` から readiness gate `paper_story_a1_paired.py:1472-1483` により必ず拒否される。試験自身もこの拒否を要求する (`orchestrator/tests/test_paper_story_a1_paired.py:1386-1390`)。着地済みなら、pilot preregistration の実在 path/hash、更新済み profile hash、対応試験があるはずである。

- [real] T-1777 の手順には pilot preregistration を凍結する段が割り当てられておらず、(1) 完了から (2) へ進めない — `/home/SFC/tanab/.claude/jobs/f9febbbc/tmp/wave-t1777/t1777-next-task-verbatim.md:3-7` — (4) は pilot と sizing の後に作る「別 study」の policy と事前登録である。したがって pilot profile の実行準備は (1) の profile 完成か、少なくとも (2) 前の未記載作業である。

- [refuted] 両 arm の build/verify 前置きは宣言だけではなく実行経路に入っている — `orchestrator/campaign/loop.py:512-525,563-589` — 各 arm を `_prepare_evaluation` し、2 件とも `_PreparedEvaluation` のときだけ `_run_balanced_schedule` を呼ぶ。build と verify の実体は `orchestrator/campaign/pipeline.py:1190-1312,1346-1635` にある。

- [refuted] 単一 lock と 5-rep 実行は実際に発火する — `orchestrator/campaign/pipeline.py:1953-2088` — 1 個の `with bench_lock()` が全 block loop を包み、各 `measure_point` へ `reps=5` を渡す。block loop 内に WAL または receipt の書込みはない。

- [refuted] 各 10 対組の AB/BA 配置は実装済みである — `orchestrator/campaign/pipeline.py:596-630` — bit ごとに `A^5 B^5 B^5 A^5` または `B^5 A^5 A^5 B^5` を作り、`pipeline.py:1973-1980` が 5 件単位へ分割する。

- [不明] D1295 項目 4 の逐語と現在の profile は一致しない — `orchestrator/campaign/paper_story_a1_paired.py:3151-3163` — D1295 は `static10 - adaptive` を要求する一方、v3 は workload ごとの `variant - baseline`、具体的には fixed10/fixed5/fixed2 から no-backoff を引く。これは D1262 `docs/decisions.md:41087-41106` には一致するため、コード欠陥か D1295 の更新漏れかは決定間の優先関係なしには確定できない。

- [real] D1295 項目 5 は profile の estimand 文字列までで、事前登録本文への限定記載は未着地である — `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:56-90` — estimand はあるが preregistration は未束縛で、残留効果の無い直接効果と同一視しない本文も実在しない。着地済みなら、その文言を含む preregistration と profile の path/hash があるはずである。

- [refuted] collector は片側 commit や不完全な arm を valid として受理しない — `orchestrator/campaign/paper_story_a1_paired.py:3549-3562,3763-3803` — 各 arm に完全な stage 列と最終 commit を要求し、2 arm のいずれかに error があれば workload 全体を invalid とする。ただし WAL 上の terminal-invalid 化は前述のとおり部分実装である。

- [refuted] D1297 の変更対象は、ファイルまたは分岐自体が丸ごと欠落してはいない — `orchestrator/campaign/ident.py:36-80`, `orchestrator/campaign/wal.py:97-150`, `orchestrator/campaign/loop.py:253-283`, `orchestrator/campaign/pipeline.py:532-631`, `orchestrator/campaign/paper_story_a1_paired.py:1527-1789,1872-1914,4074-4250`, `tools/pegasus/paper_story_a1_paired.sh:28-60` — 閉包 4 member、profile、schedule、collector、selector、job script の分岐は存在する。欠陥は WAL recovery の射程と pilot profile の未凍結状態である。

- [refuted] `paper_story_a1_paired.v3-sized.json` の不存在は (1) の欠落ではなく (4) の未了である — `orchestrator/campaign/paper_story_a1_paired.py:752-754` — driver と job には将来の selector があるが、sized policy は pilot、sizing certificate、選択された n/df/k/sigma を要求する (`paper_story_a1_paired.py:1012-1124`)。T-1777 もそれらの後に別 study を凍結すると定める。

## D1295 7 項目の対応表

| 項目番号 | 対応する file:line | 判定 |
|---|---|---|
| 1 | `paper_story_a1_paired.py:4987-5035,5067-5085`; `loop.py:512-525,563-589`; `pipeline.py:1190-1635` | 着地 |
| 2 | `pipeline.py:1953-2088` | 着地 |
| 3 | `pipeline.py:596-630,1973-1980,2075-2087` | 着地 |
| 4 | `paper_story_a1_paired.v3-pilot.json:188-305`; `paper_story_a1_paired.py:3057-3078,3151-3163` | 部分。D1295 逐語とは不一致、D1262 とは一致 |
| 5 | `paper_story_a1_paired.v3-pilot.json:56-90`; `paper_story_a1_paired.py:1230-1244,1472-1483` | 部分。estimand はあるが事前登録本文は未着地 |
| 6 | `paper_story_a1_paired.py:1872-1914`; `loop.py:268-283`; `pipeline.py:1953-2003` | 着地 |
| 7 | `pipeline.py:2093-2197`; `paper_story_a1_paired.py:3549-3562,3763-3803`; `wal.py:1897-1916` | 部分。完走後発行と collector invalid は着地、実走中断の WAL terminal-invalid recovery は未着地 |

## 親 brief の誤り

- `s1-brief.md:22-24` の「中断を terminal invalid へ閉じる経路まで入っている」は一般には誤りである。引用された `wal.py:1834` は marker 検査、`wal.py:2004` は誤った recovery を拒否する分岐、`wal.py:2015` は wrapper にすぎない。実際の recovery は build/verify 後の中断を `wal.py:1897-1916` で拒否する。

- この穴を覆う試験もない。`test_a1_non_certifying_marker.py:155-200` の fixture は `build_start` しか記録せず、`test_a1_non_certifying_marker.py:347-367` はその狭い窓だけを terminal-invalid と確認している。

- `s1-brief.md:30-32` は pilot profile を「着地済み」と数えるが、実行 readiness を検査していない。profile は意図的に preregistration 未凍結であり、現在の selector からは qsub に到達しない。

- それ以外の coordinator、単一 lock、block 配置、collector、job selector に対する file:line は、実物と概ね一致する。

## 総括

親の「実装面の純増はゼロ」は支持しない。最小の純増集合は次である。

1. balanced5 recovery を、build/verify/bench 後の中断と片側 commit でも残る active arm を terminal-invalid abort へ閉じるよう修正し、その2状態を試験する。
2. pilot 用事前登録を凍結し、`v3-pilot` profile の path/hash、登録済み profile hash、試験を更新して、pilot study-id を実行可能にする。

`paper_story_a1_paired.v3-sized.json` はこの集合に含めない。これは pilot と sizing 後の (4) で作る成果物である。D1295 項目 4 の contrast 不一致は、実装変更前に D1262 と D1295 のどちらを正本とするか裁定が必要である。

検査は指定どおり静的に行い、pytest は実行していない。