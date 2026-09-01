## 所見一覧

- **B1 BLOCKER** — login node と compute node が書いた mtime を単一の「Lustre clock」と扱う根拠がなく、放置すると clock bound、drift 範囲、collection の off-path 件数が変わる。
- **B2 BLOCKER** — `confirm` は Created より後に作られるのに Created 前 anchor とされており、放置すると `pre_created` と `o_created_hi` が誤って狭まり、physical residual の範囲も変わる。
- **B3 MAJOR** — receipt の `queue_wait_s` は会計の Created→Started ではなく qsub 復帰→qstat RUN 初観測であり、放置すると標本の queue 待ちを 208 秒から 5.34 秒へ誤置換する。
- **B4 MAJOR** — current dispatcher は Created と Request Name を会計受理条件にせず、別名 `dispatch.sh.e*` も許すため、放置すると有効な job が `accounting_missing` または parse failure として主集合から落ちる。
- **B5 MAJOR** — session 実装は K=2 と K=3 を許すのに script は全743本を K=3 固定で読むため、放置すると正規の K=2 session が破損 session と同じ `missing_shards` に分類され、受理集合と D1320 再現値が変わる。
- **B6 MAJOR** — accounting・handled 完備を要求すると queue timeout、共有 deadline 到達、collection timeout の長時間 session が落ちやすく、放置すると中央値と特に p90・最大値が短い側へ偏る。
- **B7 MAJOR** —全 worker の `start()` 済みは全 job の投入済み・RUN 済みを意味せず、collection 失敗時には worker を終了するため、放置すると P2 と overlap 診断が collection を過度に off-path と判定する。
- **B8 MAJOR** — marker、report、login log、stderr、receipt の mtime はそれぞれ異なる「最後の書込み」境界であり、放置すると区間名が実事象より数秒から accounting grace 分ずれる。
- **B9 MINOR** — root `junit.xml` を読むという brief と shard `junit.xml` だけを読む script 契約が一致せず、放置すると parent merge の参照有無が成果物間で食い違う。
- **B10 MINOR** — 743本走査の CPU・メモリ規模は小さいが snapshot ではないため、放置して active session と同時実行すると欠測理由と mtime が走査中に変わる。

## field の実在と意味

標本の値は次のとおりです。

| field | 標本値 | 実装から確定できる意味 |
|---|---:|---|
| Created Request Time | 02:24:47 | NQSV 会計上の request 作成時刻。qsub 呼出し開始や confirm 作成時刻そのものではない |
| Started Request Time | 02:28:15 | NQSV 会計上の開始時刻。標本では compute-visible mtime と同じ秒 |
| Ended Request Time | 02:32:09 | NQSV 会計上の終了時刻。標本では result mtime と同じ秒で、会計 stderr の最終書込みより10秒早い |
| Elapse | 238秒 | NQSV の resource accounting 値。表示上の Started→Ended 234秒とは一致しない |
| receipt queue_wait_s | 5.34秒 | qsub 復帰後の login monotonic clock から、qstat が初めて `RUN` と解釈された観測まで |
| state_history[].elapsed_s | 可変 | preflight `qstat -Q` 直前から各 qstat 観測まで。confirm や Created 起点ではない |

会計値は [sample-accounting.txt](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/sample-accounting.txt:12)、対応する file 時系列は [sample-session-tree.txt](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/sample-session-tree.txt:16) で確認できます。

`queue_wait_s` は [dispatch_compute.py:3891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/pegasus/dispatch_compute.py:3891) で qsub 復帰後を起点にし、[dispatch_compute.py:3949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/pegasus/dispatch_compute.py:3949) で qstat `RUN` 初観測時に確定します。コメント自身も「scheduler 上の実 RUN 開始ではなく初観測」と明記しています。

標本では 5.34秒後、すなわち約02:24:52に qstat が `RUN` と解釈された一方、compute-visible は02:28:15です。従ってその `RUN` は少なくとも「計算ノードで job script が動き始めた時刻」ではありません。

食い違いの正体が NQSV の request-level staging 状態なのか、qstat 表示仕様なのか、state parser の誤対応なのかは、射影資料からは分かりません。後続 poll の生 qstat stdout は receipt に保存されず、`state` だけが残るためです。なお `_scheduler_state` も対象 request block へ状態行を明示的に束縛していません。

権威は次のように分けるべきです。

- queue・実行・終了の scheduler accounting: Created、Started、Ended、Elapse。
- dispatcher の観測挙動と timeout: receipt の `queue_wait_s`、`state_history`。
- `Elapse=238` と Started→Ended=234 の差の厳密な NQSV 内部理由も資料だけでは分かりません。プランどおり同値扱いせず差を報告するのが正しいです。

また current dispatcher の accounting gate は [dispatch_compute.py:1881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/pegasus/dispatch_compute.py:1881) で Request ID、Group、Started、Ended、Elapseだけを要求し、Created と Request Name は要求しません。`accounting_verified=true` でも新 script の必須 field が存在する保証はありません。

## mtime の測点としての妥当性

- `intent`、`confirm`、`handled`: `_write_json_x` による create-only file です。再追記されず、mtime は JSON を最初に書いた時刻です。ただし関数進入時刻ではなく書込み時刻です。`handled` は receipt 永続化と scheduler log relay の後に作られます。
- `receipt.json`: create-only で一度だけ書かれます。`state_history` を逐次追記した file ではなく、全履歴をメモリ上で作った後の最終 materialization 時刻です。preferred write 失敗時には別 path の fallback receipt となります。
- `login-collection.log`: subprocess 復帰後に作られるため collection return の上側 proxy です。ただし `_write_bytes_create_only` は一時 file を書いて hard-link するので、mtime は最終 path の link 時刻ではなく一時 inode の書込み時刻です。
- `report.json`: 同じ `_write_bytes_create_only` です。pytest sessionfinish で payload 完成後に一度だけ書かれますが、publication 時刻そのものではありません。
- `compute-visible.json`: compute node の shell が一時 file を書き `mv` した時刻です。job script 開始直後の proxy として使えます。
- `izdw-*.e*`: scheduler 側が生成・追記する file です。mtime は会計 summary を含む最後の書込みであり、Ended そのものではありません。
- shard `junit.xml`: pytest 所有 file で、mtime は最後の書込みです。提示実装には event marker としての create-only 保証がありません。
- `result.json`: guard file を最終 payload の別 inodeで置換します。最終 mtime は child result の最終書込みです。

directory mtime は entry の create、link、rename、unlinkのたびに変わります。標本の root directory mtime が root junit 作成後になっているように、特定の job event を表しません。現プランの主式は directory mtime を使っていませんが、sample tree の directory 行を測点へ昇格させてはいけません。

## 時計

「file mtime は Lustre clock」という P4 の表現は実装からは成立しません。コードが `utime` で共通時計を刻んでいるわけではなく、次の別 host から共有 filesystem へ書かれます。

- intent、confirm、handled、login log、receipt: login node。
- compute-visible、report、shard junit、result: compute node。
- accounting stderr: NQSV/scheduler 管理経路。

Lustre が全 mtime を一つの metadata-server clock で刻むのか、client clock を inodeへ反映するのか、その保証も login node と compute node の同期保証も射影資料にはありません。従って login log と compute report を「同一時計」として直接比較する collection 検査は未証明です。

B2 はさらに独立した因果方向の誤りです。実装順は、

```text
intent 作成
qsub
qsub 復帰
submitted_at 記録
confirm 作成
```

です。[dispatch_compute.py:3751](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/pegasus/dispatch_compute.py:3751) と [dispatch_compute.py:3775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/pegasus/dispatch_compute.py:3775) がこれを示します。NQSV Created は qsub が request を作った時刻なので、因果 anchor は次です。

- Created より前: `intent`。
- Created より後: `confirm`。

プランの `confirm` を前側へ置く式は逆です。標本で Created と confirm が同じ表示秒なのは1秒分解能で潰れているだけで、順序の反証ではありません。

offset の上下限式自体は「全 marker が同じ filesystem clockに属し、因果分類が正しい」という条件では妥当です。しかし現状は両条件を満たしません。さらに NQSV 表示と標本 mtime は双方とも秒単位に見え、丸め方の仕様もありません。`q=1s` が十分な外向き幅である保証も資料中にはありません。

raw `R_s` は static offset なら duration 内で相殺します。この部分は残せます。ただし時計の step、drift、login/compute 間 mtime source 差まで相殺するとは言えません。

## コーパスの不揃いと選択バイアス

実在しうる不揃いは次のとおりです。

- K=2 session: [acceptance_shards.py:1033](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/acceptance_shards.py:1033) は shard count 2と3を正規値として受理します。K=3固定 script は正規 K=2を `missing_shards` に誤分類します。
- confirm 無し: intent 作成後、qsub失敗または request ID取得前に失敗した経路で起こります。
- handled 無し: orphan の可能性を排除できない cleanup、worker 強制終了、共有 deadline 到達で起こります。
- report/junit 無し: qdel未開始、compute bootstrap失敗、pytest異常終了、worker終了で起こります。
- accounting summary 無し: qdel未開始、scheduler log収集期限切れ、log名不一致で起こります。
- receipt 無し: worker終了、preferred と fallback の永続化失敗、または `receipt-setup-shard-N.json` だけ残る経路があります。
- 複数 attempt: current codeは session内 nonceを `shard-N` に固定し、submission directoryを create-onlyで作るため、正常な再 attempt は実装されていません。複数 `.e*` を即座に「複数 attempt」と解釈する根拠はありません。

scheduler log探索の current実装は `izdw-shard-N.e*` と `dispatch.sh.e*` の双方を候補にし、複数なら dispatcher 自身が infrastructure failure にします。[dispatch_compute.py:1672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/pegasus/dispatch_compute.py:1672) に対し、プランの glob は前者だけです。

長い側へ偏る明確な経路があります。

- queue-wait-timeout は既定900秒で qdel へ進みます。Started、Ended、accountingが残らなければ主集合から除外されます。
- 共有 deadline 到達時は未完 worker が終了され、handled/accountingが欠けます。
- login collection timeoutも同じ deadline付近で発生し、親がworkerを終了します。
- accounting grace期限切れは scheduler artifact 到着の遅い jobを落とします。

したがって `primary_included_sessions` は「743本の分布」ではなく「K=3かつ保存成果物が完全な complete-case 分布」です。除外 counterを出すだけでは p90・最大の選択バイアスは補正されません。qdelでも C/E/markerがあれば残す規則は正しいものの、保存されなかった長時間例は戻りません。

## login collection の並行性

実装順は確認できました。

1. shardごとに worker processを順に `start()`。
2. 全 `start()` が返った後、親 processが同期的に `collect_login` を実行。
3. collection成功後に初めて Pipeからworker結果を待つ。

根拠は [acceptance_shards.py:1306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/acceptance_shards.py:1306)、[acceptance_shards.py:1335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/acceptance_shards.py:1335)、[acceptance_shards.py:1353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/acceptance_shards.py:1353) です。

ただし `process.start()` は fork済みを意味するだけで、qsub完了、Created、RUNを意味しません。各 workerは dispatcher内部の共有 control lockも通るため、collection開始時に未投入の shardがあり得ます。

P2 が成立する条件は限定的です。

- collectionが実際のjob区間と重なるには、collection return前に少なくとも一つのjobが投入・開始していること。
- collectionが親の臨界経路に載らないには、collectionが成功して最後のworker payload readyより先に戻ること。
- collectionが全workerより遅ければ、親は結果を読まずcollectionを待つため、その超過分は臨界経路です。
- collectionが例外または非0なら、親はworkerを終了してsessionをinfra failureにします。

`login-collection.log` は subprocess完了後に書かれますが、timeoutや書込み例外では存在しません。[run_tests.py:1435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/run_tests.py:1435) から [run_tests.py:1457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/run_tests.py:1457) がその経路です。

off-path の保存済み証拠には、compute reportとの cross-host mtime比較より、login log mtimeと最後の `handled` mtimeの比較の方が強いです。両方ともlogin node側で書かれ、handledはreceipt永続化後かつworker payload送信前にあります。ただし payload readyそのものの時刻は保存されていないため、正確な寄与秒数までは出ません。

## script の実装可能性

予定 pathだけなら概算は次です。

- stat対象: 約18,575 file path。
- 内容を開く対象: accountingとreceiptを合わせて完全時約4,458 file。
- 行数: session 743行、shard 2,229行。
- 大きい `report.json`、junit、2.3MB級 login logは内容を読まずstatだけ。

逐次処理なら CPUとメモリはlogin nodeで問題になりにくい規模です。全receipt JSONを同時保持しても16GiB級には遠いと見込まれますが、所要時間はLustre metadata応答に依存するため静的検査から秒数は主張できません。

注意点は負荷より一貫性です。rootはsnapshotではなく、`--expected-sessions 743` はdirectory数だけを確認します。別sessionが実行中なら、inventory後にconfirm、report、handledが出現し、同じ走査内で状態が混ざります。また約1.9万件のmetadata readはactive acceptanceと共有filesystem上で競合します。実行可能という結論は、他のacceptance sessionが動いていない時間に一度、逐次走査する条件付きです。

## 親 brief 自身の欠陥

- P1は正しいです。非対中央値 `338-263` を paired residualと扱うべきではありません。
- P2は「worker processとの並行性」までしか静的に証明できません。「全jobとの並行性」や「off-path」は証明していません。
- P3の confirm→Created は因果方向が逆です。confirmはqsub復帰後なので、保存値からこれを投入前遅延とは呼べません。
- P3の「主項」も実測前の仮説に留まります。Ended→handledにはpoll、accounting待ち、receipt永続化、log relayが含まれますが、parent mergeとroot junit作成は含まれません。
- P4は「別時計の可能性」を認識していますが、全file mtimeを一つのLustre clockへ畳んだ時点で不十分です。
- briefは root `junit.xml` を解析対象に挙げますが、script契約は shard junitだけです。root junitはhandled後のparent merge測点なので、参照するか未計測とするかを統一する必要があります。
- 743本を単一K=3 corpusと暗黙に扱っていますが、正規実装はK=2も生成します。

## 総括

プランはこのまま author段へ渡せません。raw の `S_s-J_s` と per-session closureは実装可能ですが、時計補正区間とcollection overlap判定にはBLOCKERがあります。

最低限必要な修正は、Createdの因果 anchorを `intent < Created < confirm` に直すこと、login/compute/schedulerのmtimeを同一時計と扱わないこと、K=2を破損と区別すること、accountingの許容pathと実在fieldをcurrent dispatcherに合わせることです。主分布はcomplete-caseであり長い側が落ちうる、と成果物上でも明記する必要があります。

pytestや実データ743本の走査は実行しておらず、以上は指定資料と実装の静的検査結果です。