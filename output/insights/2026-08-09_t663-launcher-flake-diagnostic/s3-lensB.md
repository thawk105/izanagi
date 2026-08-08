指定資料を実読しました。pytest は未実行です。`dispatch_compute.py` は中継経路確認のため追加読了しました。xdist 本体の内部実装と T-427 の資料は指定外のため未読です。

### 所見1 — F57 の既往 node は、計画上は全件を列挙している

(i) 主張：5 node の完全な漏れはない。ただし direct `Popen` と、後段の receipt checker までは同じ診断契約になっていない。

(ii) 根拠：

| F57 node | 実ファイル上の経路 | 判定 |
|---|---|---|
| `test_check_receipt_recomputes_usage_actuals_from_sealed_artifacts` | `_run_case` は [test:1281](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1281>)。F57 の再発もその準備段階 [failures:1355](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/docs/failures.md:1355>) | 初段は載る。checker 本体の [test:1295](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1295>) は別経路 |
| `test_manifest_is_appended_while_correlated_session_is_running` | direct `Popen` [test:1535](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1535>)、assert は [test:1561](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1561>) | 計画にはあるが、helper の direct-Popen 用シグネチャが未定義 |
| `test_all_repo_policy_reasoning_values_are_accepted[high]` | parametrize 内の `_run_case` [test:562](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:562>) | `[high]` を含む5展開すべて rc=0 |
| executable identity change | [test:1758](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1758>)。F57 も `_run_case` 段階 [failures:1408](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/docs/failures.md:1408>) | 初段は載る |
| impossible truth table | [test:1740](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1740>) | 初段は載る |

(iii) 影響：F57 の既知の落ち方は概ね捕捉できるが、direct `Popen` を誤って通常の `CompletedProcess` として扱うと診断自体が二次例外になる。`communicate(timeout=10)` が先に発火すれば、診断は表示されない。

(iv) 提案：`CompletedProcess`、`Popen`、in-process rc を共通化した診断 adapter を明記し、`TimeoutExpired` も診断対象にする。F57 node の「初段 launcher」と「receipt checker」を別分類する。

### 所見2 — assert message は中継されるが、全文保存は保証されない

(i) 主張：runner 自身は出力を捕捉して切り詰めていないが、dispatch 中継は failure stream を末尾64 KiBに制限する。さらに計画は tmp artifact を永続保存していない。

(ii) 根拠：`run_tests.py` は pytest に xdist を付ける [run_tests:377](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/run_tests.py:377>)、[run_tests:380](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/run_tests.py:380>)、[run_tests:384](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/run_tests.py:384>)。最終呼出しは `subprocess.call` で [run_tests:1867](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/run_tests.py:1867>)、`pytest.ini` に addopts はありません [pytest.ini:3](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/pytest.ini:3>)。

一方、dispatch は failure relay を64 KiBに設定 [dispatch_compute.py:34](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/pegasus/dispatch_compute.py:34>)、[dispatch_compute.py:759](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/pegasus/dispatch_compute.py:759>)、[dispatch_compute.py:771](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/pegasus/dispatch_compute.py:771>)。F57 自身も pytest tmp が終了時に失われたと記録しています [failures:1349](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/docs/failures.md:1349>)。

なお fake の `valid_output` は実際には attempt stdout/stderr ではなく output file に書かれます [test:99](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:99>)、[test:287](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:287>)。ただし production の stream サイズ自体に固定上限はありません。

(iii) 影響：長い診断は dispatch の末尾切り出しで先頭を失い、tmp path と receipt は後から回収できない。再発時に再び「assert 1 == 0 / stderr空」へ戻る可能性がある。

(iv) 提案：assert message は各 stream を head/tail の上限付き抜粋にし、bytes・sha256・省略量・path を必ず併記する。総メッセージを64 KiBより十分小さくする。全文が必要なら、failure 時だけ安定した failure-artifact directory へ atomic copy する。

### 所見3 — 6 field では7条件を一意に識別できない

(i) 主張：計画の6 fieldには `process.returncode` と `validator_rc` が欠けている。さらに「7択のどれか」は、実装上は単一原因とは限らない。

(ii) 根拠：

| 計画 field | accepted 条件との対応 |
|---|---|
| `limit_trigger` | limitなし |
| `evidence_status` | evidence complete |
| `metering_status` | metering complete |
| `process_group_residual` | residual == 0 |
| `termination_verified` | termination verified |
| `wall_clock_s` | accepted 条件そのものではない |

`accepted` は [codex_worker_launch.py:1029](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/codex_worker_launch.py:1029>) で7条件の積です。process rc は receipt の `codex_exit_code` [codex_worker_launch.py:1071](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/codex_worker_launch.py:1071>)、validator は `validator_rc` [codex_worker_launch.py:1072](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/codex_worker_launch.py:1072>) に既存保存されています。wall 判定自体は `job_wall_clock_s` で行われます [codex_worker_launch.py:1017](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/codex_worker_launch.py:1017>)。

(iii) 影響：validator failure は、計画の6 fieldだけなら「全て正常なのに不採用」に見える。process rc と validator rc が同時に失敗する場合もあり、単一の根本原因を自己申告したことにはならない。

(iv) 提案：`codex_exit_code` と `validator_rc` を必須追加し、`failed_predicates[]` として複数列挙する。「原因」ではなく「不成立だったゲート」と表現する。資源競合まで分離するなら、hostname、`PYTEST_XDIST_WORKER`、PID、limits、request ID、並行 wave の有無も記録する。

### 所見4 — 33 call site の機械書換えは、値よりも削除境界が危険

(i) 主張：現行コードを読む限り、計画の rc 値自体に明白な取り違えはない。parametrize 展開も reasoning 5件、legacy 2件、manifest field 3件とも初回 launcher rc は同じである。しかし混在する checker rc と receipt 内 rc を機械削除すると壊れる。

(ii) 根拠：reasoning は5値すべて受入対象 [test:554](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:554>)。manifest header は初回 `_run_case` が rc=0で、その後 checker が rc=2 [test:1385](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1385>)、[test:1404](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:1404>)。in-process launcher は int しか返さず stdout/stderr を持ちません [test:470](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:470>)。

また `receipt["launcher_rc"]` は独立した内部 binding assert です [test:490](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:490>)。

(iii) 影響：`checked.returncode == 2` のような本来残す検査、または receipt の整合性検査まで消すと、期待 rc を一箇所へ移しただけで検査強度を失う。direct `Popen` と in-process node は helper の型不一致も起こし得る。

(iv) 提案：関数名・mode・param値ごとの期待 rc 表を固定し、ASTまたは限定的な差分で `completed.returncode` だけを置換する。receipt/checker/assertion は削除対象外とする。収集後の40 node数も静的に検査する。

### 所見5 — 「フレークが直った」証拠は、有限回の緑だけでは得られない

(i) 主張：1回の全走の緑はもちろん、少数回の緑でも「フレーク消滅」の証明にはならない。今回の変更は主に診断とfixture余裕で、資源競合そのものを直していない。

(ii) 根拠：F57 は48-worker全走後の単独再走が緑になる型を繰り返しています [failures:1354](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/docs/failures.md:1354>)。また `run_tests.py` の既定上限は32 worker [run_tests:62](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/run_tests.py:62>)で、48 workerを再現するには明示指定が必要です。

(iii) 影響：対象file単独の緑や、余裕拡大後の全走の緑を、資源競合の解消と誤記録する危険がある。

(iv) 提案：最低限、(a)各失敗 predicate の fault-injection meta-test、(b)元の48-worker条件を再現した独立全走を複数回（3回は smoke の下限に過ぎない）、(c) request・node・worker・並行 wave・全走件数を記録する。有限回で不在は証明できないため、正直な記録は「診断経路を合成失敗で検証し、実負荷全走 N 回では再発を観測しなかった。フレーク消滅は未証明」とすべきです。

### 所見6 — P1 は「sealed normal attempt」に限定すべき

(i) 主張：production 無編集は、F57で実測された rc=1 の通常 attempt には合理的だが、全失敗経路には足りない。

(ii) 根拠：production は preflight を receipt生成用 try の外で実行します [codex_worker_launch.py:1802](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/codex_worker_launch.py:1802>)。失敗時は main が stderr と rc=2を返すだけです [codex_worker_launch.py:2585](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/codex_worker_launch.py:2585>)。実際、workspace-write preflight test は receiptなしを期待しています [test:853](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:853>)。また `_run_case` の外側 timeout は10秒です [test:434](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:434>)。

(iii) 影響：preflight失敗、TimeoutExpired、強制終了では7条件の診断は得られない。P1を一般化すると、T-190完了を過大記録する。

(iv) 提案：「F57型のsealed normal attemptをtest側で診断可能にした」と範囲を限定する。全経路を要求するなら、早期receiptまたは親側sidecarを別裁定にする。

### 所見7 — P2 の余裕拡大は根拠薄く、回帰を隠し得る

(i) 主張：`max_wall=6`、evidence=2、termination=0.2 は、login nodeの84件のp90からの推定であり、F57の48-worker計算ノード負荷を根拠にしていない。

(ii) 根拠：brief自身が計測場所をlogin nodeと明記しています [brief:21](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t663-flaky-truth-table/brief.md:21>)。計画は6/2/0.2への変更を提案 [s2-plan:56](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t663-flaky-truth-table/s2-plan.md:56>)し、正常系の多くを現行3秒から外します。一方 production はevidence deadline到達で強制停止します [codex_worker_launch.py:1239](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/codex_worker_launch.py:1239>)。

(iii) 影響：`[high]` を含むnormal-controlの再発が消えても、3秒設定での回帰を検査しなくなっただけかもしれない。diagnosticを実負荷で発火させる機会も減る。

(iv) 提案：元の3/1/0.05を維持するnormal-control sentinelを少なくとも1本残す。余裕拡大は実測後に、時間予算を検査しないcall siteだけへ限定する。

### 所見8 — P3 は F57/T-190 全体の close を主張できない

(i) 主張：原因を「分離可能」にしたことと、原因を実際に分離したことは別です。P3は launcher test の診断改善までに縮めるべきです。

(ii) 根拠：briefはT-190を本 waveで閉じるとしています [brief:53](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t663-flaky-truth-table/brief.md:53>)。しかし現在のF57には、Codex launcherではなくgit timeout [failures:1399](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/docs/failures.md:1399>)、PBS elapse timeout [failures:1431](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/docs/failures.md:1431>)、共有checkout上の別wave競合 [failures:1425](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/docs/failures.md:1425>)も含まれます。T-427の資料は未読で、同一族という主張も検証していません。

(iii) 影響：F57全体を閉じたと記録すると、非launcher producerの再発を誤って解決済み扱いし、受入 gate の赤を誤帰属する。

(iv) 提案：記録は「T-663 launcher診断経路を追加」「F57 launcher subfamilyの次回観測可能性を改善」に限定する。実負荷で実際に artifact を得るまで、T-190/F57の原因分離完了やフレーク修復は未完了とする。

## 総括

Must-fix:

- `codex_exit_code` と `validator_rc` を追加し、単一原因でなく failed predicates として表示する。
- direct `Popen`、in-process、TimeoutExpired を共通診断契約にする。
- 全文assertではなく上限付き抜粋＋永続failure artifactにする。
- 元の3秒予算のsentinelと、48-worker反復受入を残す。
- T-190/F57のclose表現をlauncher診断限定へ狭める。

Nit:

- `valid_output` はstdout/stderrではなくoutput fileであり、briefのサイズ根拠を分けて記録する。