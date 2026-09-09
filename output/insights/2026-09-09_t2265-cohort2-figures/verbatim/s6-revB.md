### 所見 1

**主張**: 実機 NQSV 出力では `found` が一度も立たないため、投入直後の最初の job を `absent` と誤認し、JSON が無いので待たずに rc=4 で終了する。

**根拠**: [`wait_t2265_perf6.sh:59`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:59) は `qstat -f` の rc を捨て、[`wait_t2265_perf6.sh:61`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:61) の `Job Id:` が一致した場合だけ `found=1` にする。実測出力は `Request ID:`、`Current State = Running` なのでどの規則にも一致せず、END 節の [`wait_t2265_perf6.sh:71`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:71) から `absent - -` が返る。直後に [`wait_t2265_perf6.sh:82`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:82) へ入り、JSON がまだ無ければ [`wait_t2265_perf6.sh:87`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:87) の `fail_monitor` が発火する。残り 6 job、timeout、sleep には到達しない。

**これが本当なら何が壊れるか**: 7 本を正常投入しても waiter は最初の poll で失敗し、完了待ちも成果物収集も始まらない。

**確度**: real

### 所見 2

**主張**: 生存判定は成功した `qstat` 一覧の `RequestID` 列を完全一致で引き、`STT` は証拠のある `QUE`、`HLD`、`RUN`、`PRR` だけを扱い、それ以外や解析不能を未知として即時 fail-closed にすべきである。

**根拠**: 実測では生存 job の完全な ID が一覧の第 1 列にあり、終了 job は一覧から消え、8 文字で切れる `ReqName` は同定に使えない。repo consumer は [`tools/mutation_fanout.py:1114`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/mutation_fanout.py:1114) で NQSV 語彙 `QUE`、`HLD`、`RUN` へ正規化し、[`tools/mutation_fanout.py:1247`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/mutation_fanout.py:1247) では `QUE`、`HLD` だけを取消可能な既知状態としている。`PRR` は親の実機観測で一覧上の生存状態と確認済みである。一方、この consumer 自身の入力 parser は [`tools/mutation_fanout.py:1108`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/mutation_fanout.py:1108) と [`tools/mutation_fanout.py:1112`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/mutation_fanout.py:1112) で PBS Pro の `Job Id:`、`job_state =` に依存するため、その parser は流用できず、語彙だけが参考になる。既存 waiter は qstat state を推測せず、[`tools/dev_wave_wait.py:2018`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/dev_wave_wait.py:2018) から NQSV accounting の `accounting_ended` へ判定を委譲しており、追加の state 語彙は提供していない。現行 wait の `Q|H|W|R|E|S|T|B` は [`wait_t2265_perf6.sh:93`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:93) にしか根拠がなく、実機 NQSV 語彙ではない。また [`wait_t2265_perf6.sh:59`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:59) は qstat 自体の失敗も「不存在」へ潰している。

**これが本当なら何が壊れるか**: scheduler 障害や未知状態を終了または生存と誤分類し、早期終了か根拠のない待ち続けが起きる。

**確度**: real

### 所見 3

**主張**: NQSV での qstat 不在は「terminal」の証拠にしかならず、単なる `-f expected_json` を job 成功の証拠にする現在の区別は妥当でない。

**根拠**: [`wait_t2265_perf6.sh:82`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:82) は不在時に regular file があるだけで `DONE=1` とするため、job がまだ JSON を書いている途中でも現在の parser 誤認と組み合わさって完了扱いできる。さらに仮に PBS 形式の `F` 分岐へ入っても、[`wait_t2265_perf6.sh:97`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:97) は非ゼロ `Exit_status` でも `DONE=1` とし、[`wait_t2265_perf6.sh:101`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:101) は失敗を表示するだけで最終 rc に反映しない。既存 waiter が利用する別証拠は、非空の明示的 done file と NQSV accounting の終了記録である（[`tools/dev_wave_wait.py:2007`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/dev_wave_wait.py:2007)、[`tools/dev_wave_wait.py:2016`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/dev_wave_wait.py:2016)）が、後者の示された interface は終了しか証明せず成功 exit は証明しない。この wave で利用可能な成功証拠は、親が [`s4-ruling.md:100`](/home/SFC/tanab/.claude/jobs/4e2c74ed/tmp/wave/s4-ruling.md:100) から定められた完全性と identity を満たす JSON、または JSON の正常 close 後だけ作る明示的成功 marker であり、scheduler exit を必要とするなら権威ある accounting 結果が別途必要である。

**これが本当なら何が壊れるか**: 空または途中までの JSON、あるいは失敗 job の残骸を成功成果物として親へ渡せる。

**確度**: real

### 所見 4

**主張**: terminal job の JSON が一つ欠けただけで waiter 全体を即時終了するため、裁定が許す「6 本 complete なら作図」の判定経路へ届かない。

**根拠**: [`wait_t2265_perf6.sh:87`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:87) は missing を記録して残りを待つのではなく、その場で process を終了する。一方、裁定は [`s4-ruling.md:68`](/home/SFC/tanab/.claude/jobs/4e2c74ed/tmp/wave/s4-ruling.md:68) と [`s4-ruling.md:109`](/home/SFC/tanab/.claude/jobs/4e2c74ed/tmp/wave/s4-ruling.md:109) で、1 本を除外して残り 6 本なら作図すると定めている。waiter は missing job を terminal-failed として記録しつつ他の live job を最後まで待ち、全件の候補一覧と非成功を含む集約結果を返す必要がある。

**これが本当なら何が壊れるか**: 1 本だけ途中死した正常な 6-of-7 ケースでも、残る 6 本の完了を待てず作図可否を決められない。

**確度**: real

### 所見 5

**主張**: `IZ_MAX_WAIT_S=7200` は最後に開始する job の queue 待ちを約 1 時間以内と暗黙に仮定しており、その queue 上限に実測根拠がないため既定値としては妥当と断定できない。

**根拠**: timeout は [`wait_t2265_perf6.sh:18`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:18) の 7200 秒で、全 job 共通の時計が [`wait_t2265_perf6.sh:51`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:51) から始まり、[`wait_t2265_perf6.sh:123`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:123) で打ち切られる。job 自体の上限は [`submit_t2265_perf6.sh:98`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:98) と裁定 [`s4-ruling.md:90`](/home/SFC/tanab/.claude/jobs/4e2c74ed/tmp/wave/s4-ruling.md:90) の 3600 秒なので、最後の job が上限近く走る場合、7200 秒から runtime、poll、scheduler 終了反映の余裕を引いた約 1 時間しか queue に使えない。必要値は `最大 queue 待ち予算 + 3600 秒 + poll/終了反映 margin` であり、提示された事実から queue 予算自体は算出できない。

**これが本当なら何が壊れるか**: 7 本が時間差で開始し、最後の job の queue 待ちが約 1 時間を超えると、正常な live job を残したまま rc=5 になる。

**確度**: plausible

### 所見 6

**主張**: submit と wait の header/job-row 形式は整合していて metadata が header に化ける writer 経路もないが、wait は 1 行以上あれば受理するため 3 本だけの部分台帳を完全な cohort と区別できない。

**根拠**: submit は [`submit_t2265_perf6.sh:69`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:69) から metadata を二列で書き、最後に `columns` と五列名を同じ `printf` で書く。動的 metadata は [`submit_t2265_perf6.sh:27`](/work/1/SFC/tanab/izanagi/.claude/jobs/4e2c74ed/tmp/wave/s4-ruling.md:27) 相当ではなく、実ファイルの [`submit_t2265_perf6.sh:27`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:27) から hexadecimal に制限され、header より後に metadata を追加する処理もない。wait の exact header は [`wait_t2265_perf6.sh:28`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:28) と一致し、job row の五列 parse も submit の [`submit_t2265_perf6.sh:113`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:113) と整合する。しかし wait の cardinality 条件は [`wait_t2265_perf6.sh:44`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:44) の「1 本以上」だけで、rep 0..6、件数 7、重複 job ID を検査しない。また qsub 成功後の date または台帳追記失敗経路が [`submit_t2265_perf6.sh:100`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:100) から [`submit_t2265_perf6.sh:116`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:116) にあり、部分台帳が全 accepted job を表す保証もない。3 行なら記録済み 3 本は放置せず terminal まで監視する一方、最後は partial/incomplete として非ゼロで全 inventory を返し、自動再投入してはならない。

**これが本当なら何が壊れるか**: 3 本だけの台帳でも条件次第で waiter が正常終了し、「7 本投入」の前提と 6-of-7 停止規則をすり抜ける。

**確度**: real

### 所見 7

**主張**: wait は正常な全件終了時にだけ JSON path の present/missing を渡し、失敗時の全件 inventory、rep と job ID の対応、terminal 分類を渡さないため、親への完了判定 handoff は不完全である。

**根拠**: 台帳から `rep_index` を読むものの [`wait_t2265_perf6.sh:34`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:34)、保存する配列は [`wait_t2265_perf6.sh:39`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:39) の job ID と JSON path だけである。最終出力も [`wait_t2265_perf6.sh:131`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:131) から path の present/missing だけで、そこへ達する前の fail や timeout では全 7 本を列挙しない。元の台帳には対応関係が残るが、wait stdout 単独では復元済みの明示的 handoff にならない。168 点、座標、identity の内容検査は裁定 [`s4-ruling.md:98`](/home/SFC/tanab/.claude/jobs/4e2c74ed/tmp/wave/s4-ruling.md:98) どおり親の責務なので wait に移す必要はないが、親が検査できるよう全行について `rep_index/jobid/expected_json/terminal evidence/present-or-missing` を必ず返す必要がある。

**これが本当なら何が壊れるか**: 親は一部失敗時に「どの JSON が候補として揃ったか」を waiter の結果だけから確定できず、168 点と identity の実測へ安定して進めない。

**確度**: real

## 総括

投入前に、PBS Pro parser を NQSV の exact `RequestID`/`STT` 判定へ直し、未知状態を fail-closed にしつつ terminal failure を集約して残りを待ち、7 本分の rep/job/JSON inventory を必ず返すよう修正すべきである。