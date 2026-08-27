静的検査のみ。pytest は実走しておらず、緑とは記録しない。

**所見 1: report channel は被検査コードから書けるため、K=1 の非 dispatch 走を偽の申告で受理できる**

- 種別: 停止級
- 根拠: manifest path を runner 環境へ渡し、report directory を manifest と同じ directory に置く設計である。[s2-plan.md:24](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s2-plan.md:24)、[s2-plan.md:108](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s2-plan.md:108)。mode `0700` でも launcher、runner、pytest は同一 uid なので書込みを隔離しない。ローカル pytest は環境を暗黙継承するか、`os.environ` の複製を受ける。[run_tests.py:1112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/run_tests.py:1112)、[run_tests.py:1260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/run_tests.py:1260)、[run_tests.py:2692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/run_tests.py:2692)。被検査テストは manifest から nonce、main、digest、K を読み、既知 schema の正規 report を K 個作れる。明示 `IZANAGI_ACCEPTANCE_SHARDS=1` は待ち手に上書きされず、K=1 の local 経路が実在する。[dev_wave_wait.py:824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/dev_wave_wait.py:824)、[run_tests.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/run_tests.py:290)。したがって「非 dispatch なら report は 0 件」という前提 [s2-plan.md:156](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s2-plan.md:156) は成立しない。
- 反証条件: K=1 の local acceptance で、テストが manifest parent に正規 report を 1 個書く敵対 fixture を実走し、launcher が outcome と receipt を生成しないことを示す。または pytest child の `open()` が権限エラーになり、trusted dispatcher だけが同 directory に書ける process-level 隔離を測る。
- 成果物影響: 現設計では compute child を起動していなくても v5 receipt が生成され、`runner_executed_sha256` は main digest、`verdict` は `child-green` のまま land を通る。台帳には偽の受入 receipt SHA と成功 verdict が残る。

**所見 2: P6 は通常の非 dispatch 受入を実際に落とし、queue 停止時などに land を不可能にする**

- 種別: 停止級
- 根拠: 現 runner は未設定時、eligible でなければ K=1 を選ぶ。[run_tests.py:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/run_tests.py:282)、[run_tests.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/run_tests.py:290)。新 launcher は site や bounded membership に関係なく未設定、空文字を K=2 に変えるため、OTHER、COMPUTE、bounded LOGIN では runner が明示 K=2 を ineligible として child 前に拒否する。[s2-plan.md:166](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s2-plan.md:166)、[run_tests.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/run_tests.py:294)。明示 K=1 で local child が正当に緑でも report 0 件で拒否される。これは queue 停止時に login local を使う現行運用とも衝突する。[pegasus-runbook.md:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/docs/pegasus-runbook.md:332)
- 反証条件: OTHER、COMPUTE、bounded LOGIN、queue inactive LOGIN の各 authoritative acceptance を、未設定、空文字、明示1で測り、従来受理された集合が全て別の authoritative 経路で receipt を取得できることを示す。
- 成果物影響: launcher は report 検査を outcome より前に行うため、失敗時は receipt が生成されない。[s2-plan.md:149](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s2-plan.md:149)。land は `acceptance-receipt-rejected` となり、台帳の receipt SHA、verdict、red/flake 集合を更新できない。

**所見 3: 「P 自身は旧 launcher なので落ちない」は条件付きであり、stale manifest 環境を含む全経路の試験がない**

- 種別: must-fix
- 根拠: 待ち手は `tested-main` に launcher entry がある場合だけ main blob を選び、無ければ `tested-tip-bootstrap` を選ぶ。[dev_wave_wait.py:2558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/dev_wave_wait.py:2558)。選んだ bytes を stdin から実行することは確認できる。[dev_wave_wait.py:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/dev_wave_wait.py:848)。現在の main には launcher blob `b7d6192f8f8ab96dcdeb25b1809071b23b48df69` があるので、現時点の選択自体は旧 launcher になる。ただし成立条件は次の全てである。

  1. claim 時の tested main に launcher が存在する。
  2. main/tip の `run_tests.py` blob が等しい。[acceptance_launcher.py:436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/acceptance_launcher.py:436)
  3. 旧 launcher が継承する環境に manifest 2 key が無い。片方だけ、または stale な両方があると新 dispatcher は計画どおり qsub 前に拒否する。[s2-plan.md:57](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s2-plan.md:57)
  4. `IZANAGI_ACCEPTANCE_SHARDS=3` だけ存在する unbound request を新 dispatcher が完全互換で扱う。
  5. unbound compute result、outcome、completion、receipt v5 の全経路が不変である。

  計画の `test_unbound_tests_request_keeps_pathname_execution` は compute child の argv/stdin だけを固定し、旧 launcherから receipt、land までの全鎖や stale key を覆わない。

  land の exact 契約は root 27 field [dev_wave_land.py:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/dev_wave_land.py:102)、fingerprint 5 field、env 4 field、argv `["python3","tools/run_tests.py"]`、path、schema、authority、wave、holder、main/tip、rc、3 executed digest、log digest、scheduler、verdict別 checker/red/flake 条件である。[dev_wave_land.py:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/dev_wave_land.py:934)。さらに launcher、waiter、runner、checker の Git blobと content SHA を再照合する。[dev_wave_land.py:1021](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/dev_wave_land.py:1021)。計画は root field、env set、argvを変えないので schema破壊は見当たらないが、P自己受入の全鎖証明は不足している。
- 反証条件: main の旧 launcher bytesを実行し、新 dispatcherを使う production相当試験で、manifest key無し、片方だけstale、両方stale、shard keyだけ3の各ケースを測る。正常ケースでは実 receiptを現行 `dev_wave_land` に渡して land検証まで通す。
- 成果物影響: 条件違反時は P 自身の receipt が作れず land不能になる。root 27 fieldのどれか、特に launcher digest、runner digest、argvが変われば land rc=23となる。

**所見 4: atomic replace は regular-file先行作成しか閉じず、D859の妨害不能条件を満たさない**

- 種別: must-fix
- 根拠: 現状は `O_EXCL` で result を書くため regular-file先行作成で失敗する。[dispatch_compute.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:434)、[dispatch_compute.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:1040)。計画は atomic replace に変えるが、テストは同名 regular fileだけである。[s2-plan.md:199](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s2-plan.md:199)。被検査 child が `result.json` を directoryとして先行作成すれば fileからdirectoryへの `os.replace` は失敗する。submission directoryも mode `0700` だが同一 uidのchildには書ける。[dispatch_compute.py:2833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:2833)。さらに残存 descendant はtrusted replace後に再置換できる。report directoryにも同じ uid境界不在がある。
- 反証条件: regular file、symlink、空directory、非空directory、parent rename、childが残したwriterの各変異で、trusted result/reportが必ず公開され、公開後も launcher readまで変更不能であることを測る。
- 成果物影響: directory先行作成では result欠落となりdispatch receiptがinfra、outer acceptance receiptは欠落する。公開後の再置換が成功すれば、偽reportによって `child-green` receiptとland成功まで変わる。

**所見 5: 新しい発火条件の2述語は恒真で、複数のnegative fixtureは単一理由性を持たない**

- 種別: must-fix
- 根拠: `_dispatch_impl` は先に `spec = TASKS[task]` とする。[dispatch_compute.py:2697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:2697)。`task == "tests"` なら `argv_policy == "passthrough"` と `child_script == ("tools","run_tests.py")` は固定表から必ず成立する。[dispatch_compute.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:112)。したがって計画の3重条件 [s2-plan.md:48](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s2-plan.md:48) の後2項には単独で発火する入力がない。これは land がhelper内で既にSHA形式を狭めた後に再度SHA形式を見る既存の死んだ述語と同型である。[dev_wave_land.py:821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/dev_wave_land.py:821)、[dev_wave_land.py:1082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/dev_wave_land.py:1082)

  単一理由性がないfixtureは次である。

  - `test_binding_report_missing_is_rejected_before_outcome_and_receipt`: 1件欠落は件数とindex multisetの両方で拒否される。
  - `test_binding_reports_require_exact_index_multiset` の `[0,2]`: 同じく件数とindex集合の二重違反。
  - `test_non_dispatch_green_run_is_rejected_without_binding_reports`: directory/file欠落、件数、indexが同時に赤で、非dispatch固有の証拠を検査していない。
  - `test_result_and_report_atomic_replace_survive_child_precreation`: resultとreportの2層を同時に壊すため、先に失敗した層が後段を隠す。
  - `test_binding_is_exactly_limited_to_tests_passthrough_runner`: task、policy、child pathの各単独変異は残りの恒真述語に遮られる。
- 反証条件: 各述語を1個ずつ無効化するmutation matrixで、その述語専用fixtureだけが赤になることを示す。発火不能な2述語は削除するか、`TaskSpec` が独立入力になる実在経路を示す。
- 成果物影響: 現計画のままでは対象guardを無効化してもテストが緑のままになり、変異matrixとinsight台帳が実際より強い検出力を記録する。複数guardが同時に弱化した実装が入ると偽receiptとland成功を止められない。

**所見 6: 「env_allowlistの受理集合は変わらない」は誤りで、size上限も着地可能な値に固定されていない**

- 種別: must-fix
- 根拠: allowlist自体を変えないので、D397の「key追加」手続が直接発火しない点は正しい。しかし現在はallowlist外のmanifest keyが `request_env` に載らず無視される。[dispatch_compute.py:2796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:2796)。変更後は片方だけ、空文字、不正manifestをqsub前に拒否するため、受理集合は明確に狭まる。[s2-plan.md:57](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s2-plan.md:57)。従って「受理集合は一切変えない」[s2-plan.md:40](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s2-plan.md:40) は誤りである。

  またmanifest size上限の具体値と境界試験がない。現在のmainと同じ `run_tests.py` は96,988 bytesで、base64だけで129,320 bytesになる。64 KiB級の既存上限を流用すれば新launcherの全production走が拒否される。
- 反証条件: 3 keyそれぞれについて未設定、空文字、任意値、片側のみを旧版と新版で比較し、狭まる集合を明記する。加えて現在のmain runner blobを使い、manifest上限内のpositive controlと上限+1のnegative controlを測る。
- 成果物影響: malformedまたはstale環境ではreceipt欠落、land不能となる。size上限不足ではP後の新launcherが全report走を開始前に拒否し、Qのactivation receiptを作れない。

**所見 7: P5の25.0%は残余の上限ではなく、dispatcher単独改変を落とした歴史的比率にすぎない**

- 種別: must-fix
- 根拠: 24件中6件は「dispatcher導入後のrunner編集commitのうち、同じcommitでdispatcherも編集した割合」である。[worklog-phase3-0827-1028.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/docs/archive/worklog-phase3-0827-1028.md:79)。これはfuture waveの確率でも、残余受理集合の大きさでもない。main blob runnerは実行時にtip側 `tools.pegasus.dispatch_compute` をimportする。[run_tests.py:1307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/run_tests.py:1307)。report pathも環境から得られるため、dispatcherだけを改変したwaveでもqsubを省略し、正規reportを書き、0を返せる。briefの「runnerとdispatcherの両方を編集したwaveだけ」[s1-brief.md:51](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s1-brief.md:51) は残余を過小評価する。
- 反証条件: `run_tests.py` を一切変えず、dispatcherだけを「qsubせず正規reportを作って0を返す」変異へ置換し、新launcherがreceiptを生成しないことを示す。またはdispatcher bytesがreport authorityより前にmainへ束縛されることを示す。
- 成果物影響: 直さないとinsightと台帳に「残余25.0%、両file同時編集だけ」と誤記される。実際にはdispatcher単独waveでも偽の `child-green` receiptとland成功が可能である。

## 総括

最重は所見1で、report channelが被検査pytestから書けるためP6とD859が同時に破れる。  
親が最初に測るべきものは、明示K=1のlocal acceptanceでテスト自身が正規reportを作る敵対probeである。  
これがreceiptを生成するなら、channel境界を再設計するまで実装投入を止めるべきである。