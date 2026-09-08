## job 本体の通過可否

計画どおり実装された場合、通常経路は通過可能である。新 run kind の受理後、PBS 環境・walltime・hostname・`PBS_NODEFILE`・job script SHA・CCBench gitlink・依存 pin・凍結木の検査は既存経路をそのまま通る。driver 側も condition gate、3 個の静的 binary SHA の相異検査、exact 5 genomes、専用 report 生成を経て、PBS finalizer が unique commit 5 件と `.dat/.json` の regular non-symlink 実在を検査する構成である（[b10_backoff_grid.sh:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:186)、[backoff_extended_sweep.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:319)、[s2-plan.md:18](/home/SFC/tanab/.claude/jobs/e313582d/tmp/wave-t2418/s2-plan.md:18)）。

所見 1:  
(a) `write_failure_receipt` は全失敗を覆わない。書かれた場合は `run_kind` と `stage` が残るが、bootstrap 初期と捕捉不能終了には receipt がない。  
(b) `PY`・`OUTPUT_ROOT`・`OUTPUT_ROOT_READY` が揃わなければ何も書かない [b10_backoff_grid.sh:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:32)。run-kind、PBS 環境、Python、hostname の検査は output root 作成前である [b10_backoff_grid.sh:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:186)、[b10_backoff_grid.sh:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:260)。receipt が作られる場合は `run_kind` が明示される [b10_backoff_grid.sh:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:114)。  
(c) Python 不在、PBS 変数欠落、誤 node、SIGKILL、PBS walltime kill では、output root の failure receipt だけを探すと失敗理由も実行種別も失われる。  
(d) 最小是正は、submission receipt と request 固有 stderr を必須の失敗証拠として完了手順に明記し、「failure receipt は output-root-ready 後の捕捉可能エラーだけを覆う」と記録すること。

## 時間予算の見積り

所見 2:  
(a) 5 genomes が `SWEEP_CAP_S=11700` に収まる可能性は高いが、brief の「5 なので収まる」は実測済み上限ではなく比較見積りである。  
(b) 既存 T2266 は 8 genomes、本件は 5 genomes とされる [s1-brief.md:40](/home/SFC/tanab/.claude/jobs/e313582d/tmp/wave-t2418/s1-brief.md:40)。本件の nominal な性能 rep は `5 genomes × 5 reps × 3s = 75s` だが、driver はその前に trace on/off の 10 build、Masstree 準備、condition gate を同じ 11700 秒へ含める [backoff_extended_sweep.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:279)、[backoff_extended_sweep.py:915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:915)。plan 自身も未実測と認める [s2-plan.md:135](/home/SFC/tanab/.claude/jobs/e313582d/tmp/wave-t2418/s2-plan.md:135)。  
(c) T2266 実績の elapsed time、cache の cold/warm、node、pin が本件と同条件でない場合、8 対 5 という点数比較は時間上限にならない。特に最大 backoff は 1000 µs から 9999 µs に変わる。  
(d) 最小是正は、T2266 の request ID・sweep elapsed・cache 条件を引用すること。取得できなければ「強い見積り」と表記し、最初の 1 workload を pilot として elapsed を確認してから残り 2 本を判断する。

## 投入元の束縛

所見 3:  
(a) 「wave worktree から投入する」は人間の手順に留まり、submitter は実際の cwd が repo root か検査しない。  
(b) submitter は自分の位置から `REPO_ROOT` を求めるが、`cd` せずその場で `qsub` する [submit_b10_backoff_grid.sh:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/submit_b10_backoff_grid.sh:53)、[submit_b10_backoff_grid.sh:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/submit_b10_backoff_grid.sh:189)。job は `PBS_O_WORKDIR` を repo root として使う [b10_backoff_grid.sh:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:239)。  
(c) wave worktree 外の cwd から絶対 path で submitter を起動すると、job は別 directory に対して `git rev-parse` や submodule 検査を行い停止する。  
(d) submitter 起動時に `pwd -P == REPO_ROOT` を要求するか、`cd "$REPO_ROOT"` の後に qsub する。

所見 4:  
(a) commit 後投入でも、queued 中の HEAD・working tree は凍結されない。job script 自身の SHA は束縛されるが、実際に起動する Python driver と import 閉包は束縛されない。  
(b) spool 運用では `${BASH_SOURCE[0]}` は repo 内 file ではなく実行中の spool copy を指し、その SHA と投入時 SHA、実行開始時 HEAD の job-script blob を比較する [b10_backoff_grid.sh:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:369)。一方、driver は可変な `$REPO_ROOT/...py` から直接起動する [b10_backoff_grid.sh:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:584)。submitter は expected HEAD も clean 状態も渡さない。  
(c) qsub 後・job 開始前に、job script blobを変えず driver/import を commit または未 commit 編集すると、SHA 検査を通りながら投入時とは別のコードを測る。HEAD が動けば reservation は開始時 HEAD を記録するだけで、投入時 commit との差を検出しない。  
(d) submitter が clean tree と HEAD を固定し、expected commit を qsub 環境へ渡し、job が exact HEAD と clean tree を検査する。完全に閉じるなら、その commit の detached Izanagi worktreeから driverを起動する。

## 記録の残り方

所見 5:  
(a) 各 job の完了証拠は強いが、3 workload 全体を「揃った」と判定する fan-in がプランにない。submitter の rc=0 は qsub 3 回の受理しか意味しない。  
(b) submitter は manifest/submitted/failed を追記して終了するだけである [submit_b10_backoff_grid.sh:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/submit_b10_backoff_grid.sh:177)。各 job の `completion.json` は個別 root にだけ作られる [b10_backoff_grid.sh:645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:645)。runbook は全 request の終端・rc・receipt・artifact hash の exact 照合を要求する [pegasus-runbook.md:1428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/docs/pegasus-runbook.md:1428)。  
(c) 1 本が timeout/失敗し、2 本だけ completion を残した場合でも、submission receipt だけ見れば「3 本投入済み」に見える。  
(d) plan に明示的な fan-in 段を追加し、manifest の 3 workload と各 `completion.json` の `run_kind`・workload・PBS job ID・artifact hash・scheduler stderr を照合するまで wave を完了扱いしない。

所見 6:  
(a) JSON report からは各 point の rep 配列を数えて 5 回と読めるが、可搬 report の明示的な計測契約に `reps=5` と `extime_s=3` がない。`.dat` 単体では反復数も分からない。  
(b) plan の共通 disclosure fields は run kind・探索値・formal status だけである [s2-plan.md:75](/home/SFC/tanab/.claude/jobs/e313582d/tmp/wave-t2418/s2-plan.md:75)。JSON は各 rep を持つ一方、`.dat` provenance には反復契約が指定されていない [s2-plan.md:94](/home/SFC/tanab/.claude/jobs/e313582d/tmp/wave-t2418/s2-plan.md:94)。既存同型 report も `reps`/`extime` を top level に持たない [backoff_extended_sweep.py:768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:768)。  
(c) 第2段の担当者が `.dat` だけ受領した場合、または JSON の配列長を設定値と誤認した場合、「REPS=5・EXTIME=3sで測った」という契約を成果物単体から確認できない。  
(d) `reps`、`extime_s`、できれば `records`・`threads` を search_config、JSON top level、`.dat` provenance に同値で記録する。

## 停止基準の不在の扱い

所見なし。`formal_grid_status="not_selected_in_this_wave"` と `formal_stopping_criterion_status="not_defined_in_this_wave"` を search_config と report に重ねて置く設計は、`status="complete"` が「job 完走」を意味し「飽和判定完了」を意味しないことを十分区別している [s2-plan.md:39](/home/SFC/tanab/.claude/jobs/e313582d/tmp/wave-t2418/s2-plan.md:39)、[s2-plan.md:100](/home/SFC/tanab/.claude/jobs/e313582d/tmp/wave-t2418/s2-plan.md:100)。

## 親 brief の実測と一般化

所見 7:  
(a) 「t810 dispatcher ではないので orphan hold の問題圏外」は latch の適用範囲としては正しいが、「orphan の危険がない」と一般化してはならない。むしろ直接 qsub は hold の保護外である。  
(b) runbook は `submit_*.sh` の直接 qsub を orphan-hold の対象外と明記する [pegasus-runbook.md:1556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/docs/pegasus-runbook.md:1556)。submitter 自身には待機・取消・group completion がない。  
(c) submit session が一部 qsub 後に死ぬ、または親が request を追跡しなくなると、job は継続し得るが hold や fan-in は残らない。  
(d) brief を「t810 の orphan-hold latch は干渉しない。ただし直接 qsub の孤児化・部分投入は別途監視する」に訂正し、所見5の fan-in を加える。

walltime の一般化は所見2のとおり過剰である。一方、「新規 Pegasus 実行体は不要」は支持できる。既存 job body と submitter は runbook の登録表に既に存在し、分類は path 粒度である [pegasus-runbook.md:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/docs/pegasus-runbook.md:449)、[pegasus-runbook.md:494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/docs/pegasus-runbook.md:494)。

## runbook との整合

所見 8:  
(a) runbook は run-kind を列挙していないため三値化による直接の列挙漏れはないが、「wave worktree からの exploration campaign」に要求する環境変数と本プランが不整合である。  
(b) runbook は `IZANAGI_EXPLORATION_OUTPUT_ROOT` の export を要求し、未設定なら materialize が fail-fast と述べる [pegasus-runbook.md:1642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/docs/pegasus-runbook.md:1642)。現行 job は `IZANAGI_OFFICIAL_OUTPUT_ROOT` だけを export する [b10_backoff_grid.sh:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:559)うえ、driver は official durable policy/use class を使う [backoff_extended_sweep.py:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:968)。  
(c) runbook の「exploration campaign」が T2418 を含むなら未設定で停止する契約になる。含まないなら、runbook の語が広すぎて運用者を誤導する。  
(d) 最小是正は、T2418 の数値探索走が official durable-root 経路を使う例外なのかを runbook に明記すること。含める設計なら、job と driver を exploration root 契約へ揃える。

## 根拠なしの疑い

なし。実時間、qsub spool の実機 bytes、`IZANAGI_EXPLORATION_OUTPUT_ROOT` の下流 `ensure()` 発火有無は、未確認事項として断定せず上記の条件付き所見に留めた。

## 総括

最大の阻害点は、投入時の repo commit/working tree が凍結されないことと、3 workload の完了を束ねる fan-in がないことの2点である。これらを直せば、job 内部の新 run-kind routing、condition gate、静的 binary SHA 検査、exact 5 commits、専用 report 実在検査は一貫しており、探索走そのものは成立する見込みが高い。

11700 秒への収容は妥当な比較見積りだが実測上限ではない。成果物には `reps` と `extime_s` を明示し、runbook の exploration-root 契約も解消すべきである。テスト・PBS 投入は実行しておらず、緑とは判定していない。