## 所見

以下は read-only の静的検査と top-level transcript の `cwd` 集計結果である。pytest・性能計測は実行していない。

1. **blocker — task 単位の raw token 合計は比較可能な系列にならない**

   task-run の事前属性は `task_class`・粗い `task_kind`・自由文 objective・base commit だけで、難易度、同一 task identity、介入状態を持たない（[schema_v1.json:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/schema_v1.json:65)）。集計も task-level では `task_kind` だけ（[aggregate.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/aggregate.py:419)）。実 pilot の implementation 層だけでも lead time は 469.667〜34,532.085 秒と約 73.5 倍違う（[report:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/reports/20260720-20260722_task-efficiency.md:34)、[report:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/reports/20260720-20260722_task-efficiency.md:40)）。

   `model_calls` で割れば token/turn 強度にはなるが、turn 数の削減分を効果から除いてしまう。lead time・agent 数・sidechain 数も介入後に変わる量で、難易度の正規化子ではない。さらに Claude ledger は model 名を最終集計へ残さず全 model を加算する（[claude_session_ledger.py:755](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:755)）。

   **放置時:** before/after の差は task mix・難易度・model mixの差と区別できず、施策効果として評価できない。

2. **blocker — before cohort と介入境界が設計に存在しない**

   M8 が task-level の遡及不能を認める一方、d-v2 の payload には before/after、介入 ID、exposure、比較対象 task identity がない（[s2-plan-out.md:95](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:95)）。aggregate 変更も usage 独立集計と欠測率だけである（[s2-plan-out.md:107](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:107)）。base commit や時刻による後付け分割では、古い branch の worktree や非コード設定の exposure を確定できない。

   **放置時:** 結線直後に最初の削減施策を起票しても before 値がなく、T-598 の唯一の目的を初回から満たせない。

3. **blocker — cap 10 では交絡を分離する標本にならない**

   同じ cap なら nominal `n≤10`、fail-open 後の有効 n はさらに小さい。1 世代内で前後を均等に分けても最大 5 対 5。実 pilot は 10 run 中 implementation 8、documentation 2 なので（[report:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/reports/20260720-20260722_task-efficiency.md:7)、[report:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/reports/20260720-20260722_task-efficiency.md:134)）、同じ構成なら最良でも 4 対 4 と 1 対 1 である。

   現 pilot の実欠測は、agent event がある run が 1/10、その唯一の token 4 field が 4/4 欠測、したがって task-level token baseline は実質 0/10（[report:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/reports/20260720-20260722_task-efficiency.md:76)、[report:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/reports/20260720-20260722_task-efficiency.md:108)）。stage ID も合計 39/42、test count field は 32/156 欠測である（[report:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/reports/20260720-20260722_task-efficiency.md:117)）。開始自体も手動 CLI・opt-in のまま（[README.md:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/README.md:16)、[cli.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/cli.py:205)）。

   **放置時:** 少数かつ任意参加の前後群になり、task mix・outcome・時系列変化のどれか一つだけでも効果量を支配する。

4. **blocker — `worktree → project slug` は実データ上の関数ではない**

   `~/.claude/projects/` は 46 directory で、Claude-worktree 型 39、Codex-worktree 型 1、その他 6。top-level JSONL 305 file の top-level `cwd` を JSON parse した結果は次のとおりだった。

   - Claude-worktree slug 配下 97 file のうち、37 file が worktree と非-worktree cwd を混在し、3 file は複数 worktree 名を持つ。
   - その他 slug 配下 208 file のうち、145 file が worktree cwd を持つ。
   - 明示的な `--claude-jobs-*` project も 2 directory、4 file 存在する。

   現 t598 transcript 自体が main cwd と worktree cwd を同一 file に持つ（[993b…jsonl:6](/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi--claude-worktrees-dev-wave-t598-ledger-consumer/993bbe1f-00d6-436b-b65c-9a73b95ceaf3.jsonl:6)、[同:89](/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi--claude-worktrees-dev-wave-t598-ledger-consumer/993bbe1f-00d6-436b-b65c-9a73b95ceaf3.jsonl:89)。また t057 slug の同一 session が t088 と t057 を移動している（[9769…jsonl:67](/home/SFC/tanab/.claude/projects/-home-SFC-tanab-github-izanagi--claude-worktrees-dev-wave-t057-test-speed/9769f607-39e4-46e1-89bf-038321556a8e.jsonl:67)、[同:150](/home/SFC/tanab/.claude/projects/-home-SFC-tanab-github-izanagi--claude-worktrees-dev-wave-t057-test-speed/9769f607-39e4-46e1-89bf-038321556a8e.jsonl:150)。main slug 内にも t495 worktree の record がある（[1ba2…jsonl:47](/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/1ba2ef34-84f2-41b6-a85d-caffa9bf25db.jsonl:47)）。

   plan は derived slug が無ければ全 root 探索をせず欠測にする（[s2-plan-out.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:59)）。したがって cwd filter は、目的 record が別 project directory に保存された時点で到達不能になる。

   **放置時:** wave token の一部または全部が systematic に欠け、残る標本は「Claude が期待 slug へ保存した session」に偏る。

5. **blocker — slug/window は一つの task-run を一つの session へ束縛しない**

   collector は指定 project directory 内の全 JSONL を発見し（[claude_session_ledger.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:262)）、時間・cwd が合う全 request を加算する（[claude_session_ledger.py:495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:495)、[同:731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:731)）。同じ worktree の親 session、別対話 session、背景 job を区別する session ID は推薦案 A にない（[s2-plan-out.md:187](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:187)）。

   既知の task-run 同士が重なれば plan は usage を丸ごと欠測にするが、別 root の run・task-run を持たない背景 session は検出できず混入する（[s2-plan-out.md:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:60)）。main 直作業や通常対話は手動 start しない限り母集団外である。

   **放置時:** 既知 overlap は欠測、未知 overlap は他作業の token 混入となり、同じ条件が逆方向の誤差を生む。

6. **blocker — fail-open 欠測は施策の効きと相関する**

   欠測条件は、file cap、総 byte、record/request/tool identity 上限（[claude_session_ledger.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:28)、[同:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:552)）、`limit_reached`、timestamp 不完全・順序逆転、collision、malformed/unreadable、slug 解決失敗、task window 重複である。既定は 25 file で、現 corpus ではこれを超える project が 7 directory、うち Claude-worktree 型が 4 directory あった。plan は strict issue と limit を usage 欠測へ落とし、そのまま `task_end` を書く（[s2-plan-out.md:98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:98)、[同:105](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:105)）。

   長い session、多数 turn・sidechain、長い task window ほど上限・strict issue・overlap に当たりやすい。施策がそれらを短くした場合、after 側では token だけでなく「観測される確率」も上がる。欠測値は `task_end` 後に再取得できない。

   **放置時:** coverage 変化を施策効果として読み、真の差を減衰・誇張・逆転させ得る。

7. **must-fix — task window と transcript の時計・終端が同じ基準ではない**

   task-run の開始・終了 timestamp はローカル `datetime.now(timezone.utc)`（[ledger.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:92)、[同:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:537)）。Claude 側は transcript の `record["timestamp"]` を使い、欠損時には file mtime を使う（[claude_session_ledger.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:379)、[同:507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:507)）。UTC 表記は揃うが、同じ clock producer である契約も skew 検査もない。

   さらに plan の上端は `collection_started_at` であり（[s2-plan-out.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:52)）、collector は `task_end` より前に動く（[s2-plan-out.md:105](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:105)）。finish を呼ぶ現行 assistant turnや、走査中に flush される tail は task に含まれない。

   **放置時:** task 境界付近の call が task ごとに異なる量だけ脱落し、特に長い最終 turn や active transcript を持つ run が過小計上される。

## 親 brief の実測への反証

| M | 判定 | 反証・限定 |
|---|---|---|
| M4 | **refuted** | token object の実在自体は real だが、`tokens` は `agent_run` 専用である（[schema_v1.json:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/schema_v1.json:173)、[同:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/schema_v1.json:210)）。`0/0` は空欄でなく agent event 不在。P1 の「既存欄に producer を足すだけ」「新 schema 不要」という動機は崩れる。task-run の authority/append namespace を再利用できる点だけは残るが、それだけでは d-v2 の測定妥当性を正当化しない。 |
| M6 | **限定付き** | t598 という単例は real。ただし 305 file の集計で 145 file が Claude-worktree 型でない slug に worktree cwd を持ち、37 file が worktree slug 内で cwd を混在、3 file が複数 worktree を移動した。一般化は refuted。 |
| M8 | **限定付き** | task-run 時間窓付きの比較可能な過去 baseline を復元できない点は real。一方、main slug 内には多数の過去 worktree cwd record があり、「worktree slug が少ない＝raw transcript 自体が無い」という推論は refuted。plan はその raw dataを unambiguous task に戻す方法も、前向き baseline 期間も持たない。 |
| M9 | **限定付き** | 40 file / 3.9 s は親の単発実測として扱えるが、線形外挿は不可。探索は bucket が file cap を超えると directory walk 自体を早期停止し（[claude_session_ledger.py:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:327)）、読取は 512 MiB で停止する（[同:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:31)）。823 MB 全量を現実装が走査するという前提が成立しない。 |
| M11 | **限定付き** | all-root の lexicographic discovery が別 project で cap を消費する現象はコード上も real。ただし `--project` は探索を狭める key であって、wave を一意・完全に表す key ではない。上記の slug/cwd 反例により「事実上唯一の wave key」という一般化は refuted。 |
| M12 | **real** | 実 corpus で同一 request ID が別 session file に存在した（[8a8b…jsonl:11](/home/SFC/tanab/.claude/projects/-home-SFC-tanab/8a8bf0f4-c673-4747-894a-ed2730dcfffd.jsonl:11)、[fe7d…jsonl:9](/home/SFC/tanab/.claude/projects/-home-SFC-tanab/fe7da981-c93c-4a1a-a549-73dc92b8b278.jsonl:9)）。しかも collision は strict 専用でなく `FATAL_ISSUES` にも入る（[claude_session_ledger.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:73)）。親の帰結より強く、該当 scope では non-strict でも失敗する。 |
| M13 | **限定付き** | 現 root が final marker・run cap・date cap の各条件で拒否される点は real（[ledger.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:542)、[同:553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:553)）。ただし任意 root を `init-pilot` する既存経路はある（[cli.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/cli.py:43)、[ledger.py:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:359)）ため、「どの新 root もコード変更なしには開始不能」は refuted。task-level v2 event の開始にコードが要る、までが正しい。 |

## 測定として成立するか

**不成立。** d-v2 は task ごとの不完全な記述統計を保存できる可能性はあるが、削減施策の before/after 評価器にはなっていない。

成立条件は少なくとも次のとおりである。

- 最初の施策より前に prospective baseline cohort を完了し、run ごとに介入 exposure と比較可能な task identity／事前 strata を固定する。
- cap 10 を評価標本として使わず、想定効果量・分散・層数に基づく n を事前に決める。同じ cap のままなら descriptive telemetry に主張を限定する。
- 1 task-run と Claude session を排他的に束縛するか、canonical session ID を使う。移動 session・背景 session・main 直作業を母集団から黙って落とさない。
- 同じ時計基準で task 境界を定義し、terminal usage が flush された後に収集する。
- cap・strict・slug・overlap 欠測が token量や介入状態と相関する間は、非欠測 run の平均差を効果量にしない。

## 総括

最重所見は、**比較可能な before cohort と介入 exposure が設計に存在しないこと**である。  
raw token 合計は task mixを測る量であり、現 schema の task_kind だけでは効果量にならない。  
さらに実 transcript は project slug と worktree の一対一対応を明確に反証している。  
nominal n=10 と非ランダムな fail-open 欠測は、この帰属誤差を統計的にも救えない。  
したがって d-v2 を T-598 の before/after 結線として land する判断は止め、段 4 で測定設計へ差し戻すべきである。