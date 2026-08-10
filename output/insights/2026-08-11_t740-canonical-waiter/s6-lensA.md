静的レビューのみ実施し、pytest は再実走していない。結論は **blocker あり、NO-GO**。

## R1〜R12 判定

| 要件 | 判定 | 根拠 |
|---|---|---|
| R1 lease 寿命 | **部分的** | 通常成功では `keep_lease=True` として保持し、同期失敗では `finally` から release する。[tools/dev_wave_wait.py:559–585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:559)。ただし public `main()` の signal 窓で非成功終了しても保持したままになる（RA1）。 |
| R2 tree identity | 満たす | worktree、非 detached、branch suffix、tracked clean を claim 前に検査する。[tools/dev_wave_wait.py:354–377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:354)、呼出順は [tools/dev_wave_wait.py:510–513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:510)。 |
| R3 signal cleanup | **部分的** | handler と core の捕捉はあるが、handler 復元区間が cleanup 外（RA1）。[tools/dev_wave_wait.py:567–585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:567)、[tools/dev_wave_wait.py:597–613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:597)。 |
| R4 bounded wait | 満たす | acceptance 既定7200秒、producer は任意上限。[tools/dev_wave_wait.py:147–165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:147)、[tools/dev_wave_wait.py:280–287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:280)、[tools/dev_wave_wait.py:429–439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:429)。 |
| R5 `/proc` start-time | 満たす | field 22を取得し、後続観測と照合。不読時はstderr付きpid-only縮退。[tools/dev_wave_wait.py:216–261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:216)。ただし縮退警告をテストが固定していない。 |
| R6 死後grace | 満たす | 5秒周期、最大30秒、両fileを要求。[tools/dev_wave_wait.py:289–296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:289)。 |
| R7 pattern面不存在 | 満たす | production CLIにpattern/positional面なし。[tools/dev_wave_wait.py:140–148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:140)。literal exact集合と公開CLI拒否もある。[test_dev_wave_wait.py:285–307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:285)。 |
| R8 到達証明・結合 | **部分的** | `run` の期待列は概ね固定されるが、全 `_Effects` 呼出列のexact比較にはなっていない。結合検査も主張するcwd/capture面を直接観測しない（RA4、RA5）。 |
| R9 mutation再照準 | 静的には満たす | exact PID、exact state、成功時保持、postcheck、message、release、両file、branch preflightの実効anchorは存在する。[tools/dev_wave_wait.py:244–261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:244)、[tools/dev_wave_wait.py:414–418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:414)、[tools/dev_wave_wait.py:523–585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:523)。mutation kill の実測は本レビューでは未確認。 |
| R10 message trailer | **部分的** | 読んだ時点の非空・`AI-Agent:` 行は検査するが、そのbytesをcommitへ束縛していない（RA2）。[tools/dev_wave_wait.py:442–451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:442)。 |
| R11 canonical例 | **部分的** | script自身はcommandをそのまま実行し、余計なflagを合成しない。[tools/dev_wave_wait.py:550–556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:550)。しかしrunbookが新scriptを参照していない（RA3）。 |
| R12 poll 30〜120 | 満たす | parserで30〜120、既定30。[tools/dev_wave_wait.py:30–33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:30)、[tools/dev_wave_wait.py:133–165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:133)。 |

## 所見

### RA1 — blocker — signal handler復元区間でleaseを無音保持する

主張: 受入command成功後、`run_acceptance()` がlease保持状態で戻ってからsignal handlerを復元し終えるまでにSIGTERM/SIGHUP/SIGINTを受けると、`_SignalReceived` がcleanup済みのcore外へ伝播する。`main()` の外側はこの `BaseException` を捕捉しないため、processは非成功終了する一方でleaseはreleaseされない。

根拠: `_SignalReceived` は `BaseException` 派生。[tools/dev_wave_wait.py:78–81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:78)。成功時はreleaseを飛ばす。[tools/dev_wave_wait.py:559–585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:559)。その後のhandler復元はcore外で、外側の捕捉は `_StageFailure`、`Exception`、`KeyboardInterrupt` のみ。[tools/dev_wave_wait.py:646–663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:646)。cleanup中も、abort完了とrelease開始の間など同種のsignal窓がある。[tools/dev_wave_wait.py:573–580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:573)。

**成果物影響**: 非成功終了したwaveがleaseをTTLまで保持し、後続の受入全走とlandを最大2400秒停止させ、無音死防止という本成果物の中心目的を破る。

提案: handlerの有効期間全体をlease所有状態機械へ含め、signal maskまたは二段階cleanupで「保持成功をpublic `main()`が正常returnした時点」に確定する。少なくともhandler復元中の `_SignalReceived` を捕捉してreleaseし、cleanup中の再signalもrelease確認まで遅延させる。public `main()`へ実signalを送るsubprocessテストを追加する。

### RA2 — must-fix — trailer検査がcommitしたmessage bytesへ束縛されない

主張: message fileはmerge前に一度読むだけで、その後 `git commit --dry-run -F path` と `git commit -F path` が同じpathを再読する。検査後にfileを非空・trailerなしの内容へ交換すればcommitは成功し、postcheckも通って受入commandが投入される。

根拠: 検査は [tools/dev_wave_wait.py:442–451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:442)、実際のcommitは時間を隔ててpathを再読する [tools/dev_wave_wait.py:523–546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:523)。commit後はmessageではなく `HEAD..main` だけを確認して投入する。[tools/dev_wave_wait.py:548–555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:548)。

**成果物影響**: trailerなしmerge commit上で受入全走が成功してもprovenance監査でland不能となり、1055〜1273秒の全走結果が廃棄される。

提案: message bytesを一度だけ読み、検査した同一bytesをstdinまたは安全に作成した固定fileからdry-runとcommitへ渡す。さらにcommit直後、受入投入前に作成commitのmessageを再読して `AI-Agent:` 行を確認するraceテストを置く。

### RA3 — blocker — 正本scriptがrunbookから到達不能

主張: scopeの成果物は「runbook §7.3から新scriptを参照する」までだが、現状の§7.3は依然 `wave_land_window.py claim` と手書き手順だけで、`dev_wave_wait.py` の参照・canonical invocation・producer例がない。

根拠: briefの必須成果物は [brief.md:5–6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t740-canonical-waiter/brief.md:5) と [brief.md:61–67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t740-canonical-waiter/brief.md:61)。現行runbookはprimitive直接呼出しのまま。[docs/pegasus-runbook.md:757–769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:757)、手書き状態機械も残る [docs/pegasus-runbook.md:771–810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:771)。read-only `git status --short` でも変更は新規code/testの2ファイルだけだった。

**成果物影響**: 運用consumerが従来の手書きloopを使い続け、誤claim判定・main取り込み漏れ・無音待機が再発して受入結果をland不能にする。

提案: land前に§7.3をcanonical waiter中心へ更新し、acceptance例は裁定R11どおり `-- python3 tools/run_tests.py` の裸形にする。producerもPID file例だけを掲載し、pattern例を置かない。

### RA4 — must-fix — R8の「全 `_Effects` 呼出列exact比較」を満たさない

主張: fakeは未消費queueだけを確認し、記録された全event列を通常は比較しない。このため、例えば全失敗releaseの直前へ `effects.sleep(30)` を追加しても既存suiteは緑のままになり、実運用ではlease解放だけが30秒遅れる。

根拠: `assert_drained()` はqueue残量だけを見る。[test_dev_wave_wait.py:121–125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:121)。全run列を比較するのは主にparameterized stage testだけ。[test_dev_wave_wait.py:561–575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:561)。裁定R8は各negative caseについて全 `_Effects` 呼出列のexact比較を要求する。[s4-adjudication.md:64–68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t740-canonical-waiter/s4-adjudication.md:64)。

**成果物影響**: release遅延・追加poll・隠れた環境分岐が緑のまま入り、後続waveの受入開始とland可能時刻が誤って遅延する。

提案: negative testごとに `fake.events` 全体をliteral列とexact比較する。少なくともrelease回数、全sleep、monotonic、file read、command capture、target stage 1回を一つのassertで固定する。

### RA5 — must-fix — 結合検査が主張するcwd/capture面を観測していない

主張: 結合検査は実Git・実lease helperを使う点は有効だが、受入commandが単なる `sys.exit(0)` なので、そのcommandだけ別cwdで実行したりstdout/stderrをcaptureして隠しても緑のままになる。またbehind=0だけで、実merge・message trailer経路は結合されない。

根拠: commandはcwdも出力継承も検証しない。[test_dev_wave_wait.py:759–777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:759)。assert対象はrc、lease保持、releaseのみ。[test_dev_wave_wait.py:779–798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:779)。

**成果物影響**: 受入commandが別checkoutで走る退行でもrc=0を受入完了として保持でき、実際のland対象tipに対する全走証拠が失われる。

提案: childに期待repoの絶対pathを渡して `Path.cwd()` を照合させ、stdout/stderr sentinelが親processへ継承されたこともassertする。shell metacharacterをliteral argvとして渡す検査と、mainを1 commit進めた実merge/trailer結合ケースも追加する。

## 各テストの緑のまま残る破壊例

以下は「各node単体が見逃す変更」。`★` は現行suite全体でも生存しうるもの。

| テスト | 緑のまま残る具体的破壊 |
|---|---|
| `test_pid_probe_calls_kill_zero_for_exact_pid` | artifact条件を削除しても、このfixtureでは両fileがある。 |
| `test_producer_waits_while_pid_alive_then_completes_after_death` | done/artifactの片方を無視しても両方trueなので緑。 |
| `test_producer_dead_without_required_file...` | start-time束縛を削除してもfixtureのPIDは最初からESRCH。 |
| `test_producer_accepts_exactly_one_pid_source` | pid-fileの複数行や巨大入力を許可しても正例 `"123\n"` は緑。 |
| `test_producer_rejects_invalid_pid_source` | PID `0` や非ASCII数字を許可してもneither/bothだけなので緑。 |
| `test_producer_cli_surface_has_no_pattern_input` | ★ CLI外の環境変数からpattern fallbackを追加してもliteral option集合は不変。 |
| `test_producer_start_time_change...` | ★ 後続 `/proc` 読取失敗をUNKNOWNでなくALIVEへ倒しても、本fixtureは有効statだけ。 |
| `test_producer_file_visibility_grace_is_bounded` | grace上限を撤去しても10秒でfileが揃うこのnodeは緑。 |
| `test_acceptance_non_acquired_state...` | ★ 10回目のheld/queuedをacquired扱いする退行は、1回しか観測しないため生存。 |
| `test_acceptance_ignores_acquired_outside...` | ★ `queued` のdiagnosticにacquiredがあれば投入する分岐を足してもfixtureはheld。 |
| `test_acceptance_rejects_claim_json` | ★ JSON array `["acquired"]` を受理する退行は未検査。 |
| `test_held_and_queued_refresh_main...` | ★ 4回目以降だけmain再取得を省略しても3 claimで終了する。 |
| `test_acquired_reloads_main...` | 2回目以降のacquisitionだけreloadを省略しても1 acquisitionしかない。 |
| `test_merge_required_without_message...` | ★ messageなしをbehind=1だけ拒否し、behind≥2で投入する退行は未検査。 |
| `test_merge_sequence_and_postcheck...` | ★ trailer検査後のmessage file交換はfakeが表現せず、RA2が生存。 |
| `test_nonzero_stage_blocks...` | ★ Git stdoutが負数・過大値等の場合の許可は、非0rcだけを見る本testでは生存。 |
| `test_merge_failure_aborts_before_release` | ★ `merge --abort` 非0を成功扱いする退行はabort成功しか与えないため生存。 |
| `test_acceptance_command_red...` | ★ childのsignal負returncodeを0へ正規化する退行はrc=23しか扱わない。 |
| `test_abnormal_path_always_releases` | ★ public `main()`の成功後signal窓はcore直接呼出しでは発火しない。 |
| `test_release_failure_overrides...` | ★ release subprocess非0やmalformed JSONを成功扱いする退行は未知stateしか扱わない。 |
| `test_acceptance_cli_contract` | ★ `--max-wait-seconds 0` や不正wave文字列の許可は未検査。 |
| `test_identity_preflight_rejects...` | ★ inside-worktree結果やdetached判定を無視する退行はwrong suffix/dirtyしか扱わない。 |
| `test_merge_message_requires...` | ★ 検査後にtrailerを消すTOCTOUは未検査。 |
| `test_signal_path_releases...` | ★ handler設置を全部削除しても内部例外を直接注入するため緑。 |
| `test_default_wiring_with_real_git...` | ★ acceptance childだけ別cwd/captureありで起動しても `sys.exit(0)` は緑。 |

期待値については、option集合、rc、state、argvはテスト側literalでありproduction定数からのsemantic importはない。一方、`DW._Effects`、`DW._CommandResult`、`DW._StageFailure`、特に `DW._SignalReceived` をproductionから使う。[test_dev_wave_wait.py:20–24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:20)、[test_dev_wave_wait.py:53–72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:53)、[test_dev_wave_wait.py:726–733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:726)。signal testはこの結合のため、実handlerが消えても緑になる。

## 受理集合・既存consumer

裁定外の恒常的な新規投入許可は見つからなかった。任意command、pid-only縮退、残余race、wave digestだけのrelease権限は段4で明示的に残された既知限界である。message fileの事前存在検査、未知state・duplicate JSON拒否、最大待機時間はプランv2またはR4/R10で承認済み。

`tools/wave_land_window.py` はread-only `git diff` 上で変更なし。新scriptもcampaign namespaceをimportしておらず、repo scanはuntracked PythonをAST parse対象に含める設計である。[test_campaign_import_invariant.py:1001–1044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_campaign_import_invariant.py:1001)。静的には新規import invariant違反は見つからない。ユーザー提示の114 passedは既知事実として扱うが、本レビューでは再実走していない。

commit成功後のpostcheck失敗・受入赤は、作成済みmerge commitを巻き戻さずreleaseする実装であり、裁定済みプランと一致する。[tools/dev_wave_wait.py:541–585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:541)。通常のclean successで誤releaseする経路は見つからなかった。

## 総括

**blockerあり。NO-GO。**

land前に最低限、RA1のpublic signal/cleanup所有状態、RA2のmessage bytes束縛、RA3のrunbook canonical参照を閉じる必要がある。RA4・RA5も段4で採用済みのR8を未充足のままにするため、同じfix集合で修正対象とすべきである。