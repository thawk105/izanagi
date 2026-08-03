静的監査のみで、pytest は実走していない。結論は「(P1) の一回限りの張り直し自体は成立するが、brief の不変条件・成果物影響・[T-360] への一般化は過大」である。

## 1. [REFUTED] (P1) は指定された既存 2 テストを壊さない

(a) 主張  
`state == "RUN" and not run_seen` の分岐内で一度だけ deadline を張り直す限り、指定された 2 テストは静的には赤くならない。

(b) 根拠  
時刻を進めるのは `_Clock.sleep()` だけであり、`_Scheduler` は qstat ごとに状態を 1 個消費する（[test:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:29)、[test:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:138)）。監視順序は RUN 初観測処理の後に overall 判定である（[dispatch:1215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1215)、[dispatch:1221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1221)）。

| test | 監視反復 | 時刻 | 状態 | (P1) 後の処理 |
|---|---:|---:|---|---|
| `test_overall_walltime_plus_grace_bound_qdels_running_job` | 0 | 0 | RUN | 初回 RUN。deadline は `0 + 1 + 0 = 1` に張り直される。`0 >= 1` は偽 |
| 同上 | 1 | 1 | RUN | 再設定なし。`1 >= 1` で `overall-timeout`、qdel |
| `test_unknown_scheduler_state_remains_bounded_by_overall_timeout` | 0 | 0 | UNKNOWN | RUN 分岐不発。queue 経過 0 < 20、`0 >= 1` は偽 |
| 同上 | 1 | 1 | UNKNOWN | RUN 分岐不発。queue 経過 1 < 20、`1 >= 1` で timeout、qdel |

したがって前者の履歴は `RUN, RUN`、後者は `UNKNOWN, UNKNOWN` のままである（[test:1308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1308)、[test:1334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1334)）。

(c) 成果物影響  
この 2 本では修正前後とも `rc=16`、receipt の理由は `overall-timeout`、`qdel.attempted=true` のまま変わらない。

(d) 修正案  
新 assignment は必ず `if state == "RUN" and not run_seen:` 内、timeout 判定より前に置く。毎 RUN で再設定すると前者の上界が消えるため不可。

## 2. [REAL・限定] 未被覆なのは QUE→RUN 遷移ではなく deadline 算術

(a) 主張  
brief の「順番待ちを挟んでから RUN する経路は未被覆」は広すぎる。遷移自体は既に複数テストが被覆し、未被覆なのは「queue 待ちが旧 deadline を消費する数値境界」だけである。

(b) 根拠  

- `QUE → RUN → END` は [test:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:206)。
- `STG(QUE) → RUN → END` は [test:745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:745)。
- `QUE → QSTAT_ERROR → RUN → END` は [test:779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:779)。
- qsub 後から RUN までの `queue_wait_s=5` も [test:1193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1193) で固定済み。
- `test_walltime_override_is_bound_to_pbs_and_total_bound` は名前に反し、実際には PBS 引数しか assert していない（[test:1366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1366)）。

反証となる deadline 境界テストは見つからなかった。したがって brief の狭い意味での「純増検出力」は real である。

(c) 成果物影響  
旧実装では新 node が `rc=16`、`overall-timeout`、qdel となり、修正後は child `rc=0` と receipt が完成する。変異台帳では、この node だけが `KILLED` になるべきである。

(d) 修正案  
現行 [test:1333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1333) 直後へ次の形を置く。

- 状態列: `("QUE", "QUE", "RUN", "RUN", "DONE")`
- 注入値: walltime 2 秒、grace 1 秒、poll 1 秒、queue timeout 10 秒、accounting grace 0
- 時刻列: `t=0 QUE → 1 QUE → 2 RUN → 3 RUN → 4 END`
- 旧 deadline は 3。旧実装は `t=3` で timeout
- 修正後は初回 RUN の `t=2` で deadline を 5 に張り直し、`t=4` の END に到達
- assert は `rc == 0`、状態列、`queue_wait_s == 2.0`、qdel 不在だけに絞る。receipt 全体や会計 payload は固定しない

変異は追加 assignment を旧式の `submitted_at + walltime_s + overall_grace_s` へ戻し、`expected_nodes` はこの新 node だけにする。実行選択は test file 全体として、他 node の追加赤を `MISMATCH` で検出すべきである。

## 3. [REAL] brief の不変条件 2 は実装と一致していない

(a) 主張  
brief は「RUN 未観測は queue timeout、RUN 後は walltime + grace」と書くが（[brief:39](/work/1/SFC/tanab/izanagi-jobs/466a006d/t363/brief.md:39)）、(P1) は pre-RUN の旧 overall deadline も残す。実効契約は別物である。

(b) 根拠  
pre-RUN の実効上界は次である。

```text
min(
  submitted_at + queue_wait_timeout_s,
  submitted_at + walltime_s + overall_grace_s
)
```

RUN 後だけが `first_RUN_observed_at + walltime_s + overall_grace_s` になる。[dispatch:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1181) と [dispatch:1219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1219) の連言がこの二重上界を作る。

生の案 (B) で pre-RUN overall を除くと、未知状態テストは `t=0..3` を UNKNOWN で通過し、fake scheduler が `t=4` に既定 DONE を返して child `rc=0` になるため、既存期待を確実に破る。従って「B は既存テストを壊す」は正しいが、「A だけが意味的に最小」は導けない。

(c) 成果物影響  
短い walltime を指定した QUE/HLD/UNKNOWN job は、queue timeout より先に overall timeout で qdel される既存挙動が残る。receipt の理由も `queue-wait-timeout` ではなく `overall-timeout` になり得る。

(d) 修正案  
(P1) は「既存受理集合を保つ最小差分」として採用可能。ただし不変条件を上記二段階の式へ直し、「queue timeout 単独」とは書かない。pre-RUN の phase 別整理は別裁定に分離する。

## 4. [CONDITIONAL] consumer のコード変更は不要だが、hash と再開条件は変わる

(a) 主張  
commit 済み・clean な状態なら、列挙された consumer に追加修正は不要であり、静的検査も赤くならない。未 commit または旧 mutation ledger 再開時だけ停止する。

(b) 根拠  

| consumer | 影響 |
|---|---|
| `mutation_harness.py` | dispatch source の実体 hash と HEAD blob hash を比較する（[mutation_harness.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:475)）。commit 後は両方が新 hash で一致 |
| 同上・未 commit | main は hash 検査より先に clean-tree gate で停止する（[mutation_harness.py:1920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:1920)） |
| 同上・旧 ledger | `repo_head`、`runner_sha256`、`runner_identity` の不一致で resume を拒否する（[mutation_harness.py:1657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:1657)） |
| `check_docs.py` | `_DISPATCH_SOURCE` から読むのは `TASKS[*].child_script` inventory だけ（[check_docs.py:2001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/check_docs.py:2001)）。deadline assignment は無関係 |
| `guard_bash.py` | exact path の集合だけを見る（[guard_bash.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/hooks/guard_bash.py:174)）。path 不変なので無関係 |
| `run_tests.py` / provenance | `dispatch(... task=...)` の API だけを消費する（[run_tests.py:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/run_tests.py:826)、[check_ai_provenance.py:1019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/check_ai_provenance.py:1019)） |

(c) 成果物影響  
新 ledger では HEAD / repo tree / runner identity hash が更新される。旧 ledger を誤って resume することはできない。bug 発火例では caller が受け取る値が infra `16` から実 child rc に変わる。

(d) 修正案  
コード＋テストを先に commit し、clean を確認してから新規 ledger を作る。旧 ledger へ `--resume` しない。`check_docs.py`、`guard_bash.py`、caller の変更は不要。

## 5. [REAL] D130 の条件を「完了」と扱うと docs が嘘になる

(a) 主張  
runbook §7.0 は deadline の意味を書いていないため修正不要。一方、D130 の現在形の欠陥記述は P1 後には既知 RUN 経路について古くなり、D131 の広い前提は未充足のままである。

(b) 根拠  
runbook の dispatch 部分は task inventory と admission だけである（[runbook:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/docs/pegasus-runbook.md:315)、[runbook:338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/docs/pegasus-runbook.md:338)）。

D130 は旧 assignment が現在も「順番待ちを実行時間から差し引く」と記述する（[D130:6349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/docs/decisions.md:6349)）。P1 後も assignment 自体は pre-RUN 用として残るため、同じ行を指して欠陥だと言い続けるのは誤誘導になる。

さらに D131 の共通前提は「`total_deadline` 修正と active job への qdel 禁止」の連言である（[D131:6400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/docs/decisions.md:6400)）。P1 は後半を実装しない。

(c) 成果物影響  
P1 だけで [T-360] の当該前提を全面完了にすると、UNKNOWN・stale QUE の active job を qdel し得る transport を「準備完了」と報告し、mutation ledger の完全性保証が過大になる。

(d) 修正案  
日付付き D130 本文は歴史として書き換えず、新しい記録で「既知 RUN 初観測経路は修正済み、UNKNOWN/stale-state と D131 の active-job qdel は未解決」と明記する。runbook 編集は不要だが、追加するなら二段階 deadline の正確な式を書く。

## 6. [REAL] (P2) を scope 外にすると、同型 qdel は実際に残る

(a) 主張  
UNKNOWN が実際には RUN 中なら P1 は一度も発火しない。これは単なる受理集合の美学ではなく、D131 が要求する active-job 保護の未達である。

(b) 根拠  
parser は閉じた RUN/QUE/HLD 等しか受理せず、未知文字列は `None` になる（[dispatch:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:111)、[dispatch:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:207)）。UNKNOWN では `run_seen` が偽のままなので queue/overall timeout に入り、except が qdel する（[dispatch:1192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1192)、[dispatch:1361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1361)）。

既定値なら未知状態の実効上界は `min(900, 1800+300)=900` 秒であり、実際に走行中でも 15 分で qdel され得る（[dispatch:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:28)）。

(c) 成果物影響  
現行 caller では tests/provenance receipt が infra `16` となり、`run_tests` の task-run 台帳も実 child rc ではなく `exit_status=16` を記録する（[run_tests.py:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/run_tests.py:881)）。将来の mutation bundle では ledger が部分状態または transport parse error で停止する。

(d) 修正案  
任意 UNKNOWN を RUN 扱いする修正は採らない。`state_history[0] == "UNKNOWN"` の既存期待を壊し、scheduler schema drift や malformed output を長時間受理するからである。別 blocker として、scheduler が提供する started timestamp 等の権威ある証拠で RUN を確認する案と、証拠不明時の qdel/orphan 方針を裁定する。少なくとも [T-360] 完了条件からは外さない。

## 7. [REAL・限定] (P3) の local は必要だが、それだけでは実行形が確定しない

(a) 主張  
dispatcher 自身を変異するため `runner-mode=local` は正しい。しかし flag だけでは「計算ノードで local 実行」を保証せず、「関連 node 限定」も collateral regression を見落とす。

(b) 根拠  
dispatch mode は source hash を変異前に一度検査するが（[mutation_harness.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:475)）、その後 target を書き換えて test command を起動する（[mutation_harness.py:1251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:1251)）。target が dispatcher なら、変異体自身が transport になる。

一方、local mode でも command が `tools/run_tests.py` なら Pegasus login 上では再び dispatcher を呼ぶ（[run_tests.py:928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/run_tests.py:928)）。`python -m pytest` なら site gate を迂回して login node で pytest を走らせる。runbook は login node の部分 pytest も禁止する（[runbook:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/docs/pegasus-runbook.md:254)）。

local ledger では dispatch receipt/job stdout path が null である（[mutation_harness.py:879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:879)）。

(c) 成果物影響  
dispatch mode では transport 破損が P1 test kill ではなく `PARSE_ERROR` として台帳を止め得る。login-local では運用違反となる。狭い node 選択では、変異が既存 overall/unknown 上界まで壊しても ledger が検出しない。

(d) 修正案  
明記すべき実行形は「外側で qsub/qlogin により確保した計算ノード上で、内側 harness を `--runner-mode local`」。変異 command は少なくとも新 node、overall、unknown、queue-wait timing を含め、可能なら test file 全体を選択する。`expected_nodes` だけは新 node 1 件に限定する。外側 job log/ID は ledger と別に保存する。

## 8. [REAL] certified 成果物影響と「束ねほど発火確率が上がる」は根拠不足

(a) 主張  
brief の「計測 dispatch」「certified 選択が欠測台帳を根拠にする」は現行 caller から導けない。また、束ねで発火確率が上がるとも実測からは言えない。

(b) 根拠  
dispatcher 自身が「dev harness 専用で certification submitter を置換しない」と明記する（[dispatch:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:3)）。現行 `TASKS` は tests と provenance の 2 種だけである（[dispatch:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:55)）。

旧実装で初回 RUN 観測までを `q`、walltime を `W`、grace を `G` とすると、RUN 後に残る監視予算は `W + G - q`。束ねでリスクが増えるのは、長い内側実行がこの短縮分まで消費する場合だけである。一方、束ねは qsub 回数を多数から 1 回へ減らすため queue 暴露回数は減る。

D130 の実測 queue 待ちは 21〜264 秒で既定 grace 300 秒未満、41 変異規模は未実測と明記されている（[D130:6332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/docs/decisions.md:6332)）。発火確率の順序づけを支える観測ではない。

(c) 成果物影響  
現在直接変わるのは dispatch receipt の `outcome`、qdel、tests の task-run `exit_status`、provenance rc、将来の mutation ledger 完遂性である。現行 certified 選択・材料レポート・製品試行台帳の値を変える caller は存在しない。

(d) 修正案  
DW-G05 は「test/provenance receipt と task-run / mutation 台帳が infra 失敗へ誤分類される」に縮める。certified 影響は将来 certification caller が追加された場合の条件付き影響とする。「束ねで発火確率が上がる」は「束ね runtime が要求 walltime の余裕を使い切る場合、単発当たりの影響が大きくなり得る。確率は未測定」へ訂正する。

## 総括

- (P1) は一回限りの RUN 張り直しなら成立するが、pre-RUN の実効上界は queue timeout 単独ではなく `min(queue, W+G)` である。
- UNKNOWN/stale-state の実走 job qdel は残り、P1 だけでは D131 の active-job 保護も [T-360] 前提も閉じない。
- certified 成果物影響と「束ねほど発火確率が上がる」は現行 caller・実測に支えられず、local 変異には外側計算ノード実行の明記が要る。