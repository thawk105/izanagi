静的読解の結論は、恒久化は **NO-GO** である。段2プランの D103/D105/D117 解釈は親 brief より正しいが、G01 は全走同値を証明せず、D117 の契約と証拠保存も未充足である。テストは実行しておらず、緑とは主張しない。

## `_artifact` 5 field の比較

根拠は [`_artifact()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:849)、[`_validate_artifact()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:859)、[`_run_tests()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1116)。

| field | 現行 dispatch 経路 | 提案の束ね経路 | 痩せる証拠 |
|---|---|---|---|
| `runner_mode` | `"dispatch"` | 内側 harness は `"local"` | 内側台帳単体からは「compute 上の outer job 内で local」か「login 直 local」か区別不能 |
| `receipt_path` | collection / baseline / 各 mutation ごとの receipt 絶対 path | `null` | mutation ごとの request ID、job ID、queue/accounting、child rc、state history が消える |
| `job_stdout_path` | 各 run の scheduler stdout path | `null` | mutation ごとの外部 stdout 再照合先が消える |
| `stdout` | receipt が指す各 job stdout の全文 | 各 inner test subprocess の捕捉出力 | test 出力自体は残るが、compute marker・probe・job wrapper 出力とは結び付かない |
| `stdout_sha256` | `SHA256(stdout.encode("utf-8"))`。外部 job stdout と再照合される | 同じ計算だが embedded `stdout` との自己整合のみ | 「正しい run の出力か」ではなく「同じ JSON 内の文字列と hash が一致するか」へ弱くなる |

`test_output_sha256` も baseline / mutation について同じ `stdout` 文字列の hash であり、現行では `stdout_sha256 == test_output_sha256` である（[`baseline`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1239)、[`mutation`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1316)、[`validators`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1492)）。

提案する outer `job_stdout_sha256` は「束ね job 全体の stdout」の hash であり別物である。計画どおり別 field に保てば化けない。ただし producer が per-record `stdout` に outer stdout を誤投入しても、両 hash を同時生成すれば validator は通る。per-mutation 固有 sentinel と outer-only sentinel を使い、両者が交差しない契約テストが要る。

消えるものは、各 mutation の receipt/job stdout だけではない。per-run の request、job name、queue wait、walltime、qsub/qstat/accounting 記録、compute hostname marker、interpreter probe、stage、child rc、scheduler fault domain、dispatch entrypoint identity、および queue を含む `duration_s` の意味も失われる。

## 所見

| # | 所見 | file:line 根拠 | これが real なら成果物が何にどう変わるか | 深刻度 | 提案する最小の対処 |
|---:|---|---|---|---|---|
| 1 | 【確認】親 brief の「採用済みパターン」は誤り。D103 は glob / 任意 command を拒むが、D105 は task 集合を明示的に `{"tests","provenance"}` へ固定し、D117 は第3 task を未裁定として返している。段2プランの解釈が正しい。 | [brief:26-29](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/brief.md:26)、[D103:4599-4617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/decisions.md:4599)、[D105:4710-4714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/decisions.md:4710)、[D117:5551-5558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/decisions.md:5551) | 未裁定の `mutation` が第3の受理 task となり、受理集合が2要素から3要素へ拡大する。 | blocker | AI は新 D の案までに止める。ユーザーに「D105/D117 を supersedeして第3 taskを許可」か「TASKSを維持し専用 sealed qsub wrapper」に裁定を返す。後者を推奨。 |
| 2 | 【確認】D117 契約は未充足。特に child の実効 env、stdin、artifact の永続性、signal rc が未閉鎖である。 | [plan:184-238](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:184)、[`_job_run`:485-498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/pegasus/dispatch_compute.py:485)、[D117:5551-5558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/decisions.md:5551) | 細工した request や親環境により、台帳外の pytest 挙動・入力・終了意味が受理される。 | blocker | 下記 D117 照合表の「未充足」を実装前契約にする。 |
| 3 | 【確認】allowlist は過大。さらに requested env を検査しても、child は `os.environ.copy()` を丸ごと継承するため実効 allowlist にならない。 | [plan:191-204](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:191)、[dispatch:485-492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/pegasus/dispatch_compute.py:485)、[harness:1120-1130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1120) | 親の `PYTHONPATH` 等で probe/harness 起動コードが変わり、同じ ledger verdict が別コード実行の結果になり得る。 | blocker | requested allowlist は原則空にし、job script の probe 前と `_job_run` の両方で clean env を構築する。必要値は env 転送でなく型付き request field にする。 |
| 4 | 【確認】`--repo` / `--spec` / `--out` の path 検証案はあり、「どこにもない」は当たらない。しかし inner test argv の全走性、selector、`-p` plugin 等は固定されていない。 | [plan:206-238](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:206)、[runner identity:436-509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:436)、[CLI:1857-1896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1857) | `-k` / nodeid / `--ignore` で全走を縮小、または pytest plugin をロードしても sanctioned task として台帳化される。 | blocker | mutation task の test command を canonical `tools/run_tests.py` 全走 argv に完全一致させ、selector・positional target・任意 plugin を拒む。 |
| 5 | 【確認】`_SANCTIONED_PATHS` への追加は不要で、追加すると危険。dispatcher は既に sanctioned。`mutation_harness.py` を追加すると早期許可され、login 上の直 local 実行を許す。現計画も `runner_mode=local` の login 直起動を閉じていない。 | [guard:174-183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/hooks/guard_bash.py:174)、[guard:603-605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/hooks/guard_bash.py:603)、[plan:331-343](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:331) | login 直 local run が同じ v4 ledger を作り、compute 移設済みという証拠主張が偽になる。 | blocker | sanctioned path は増やさない。harness 自身の real-run site gateと、hook の専用「直 mutation harness 拒否」を追加する。hook を scope 外にするなら、その穴をユーザー裁定へ返す。 |
| 6 | 【確認】新 task の文書/test 層が不完全。`test_check_docs.py` は task inventory を `tests/provenance` 正規表現で扱うため更新必須だが、段2は「必要な場合のみ」としている。 | [plan:438-443](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:438)、[test_check_docs:1358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/orchestrator/tests/test_check_docs.py:1358)、[runbook:338-343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/pegasus-runbook.md:338) | 実装 enum と規範 task 表がずれても、文書 gate の受理集合検査が不正確になる。 | must-fix | `test_check_docs.py` と runbook exact inventory を必須 scope に入れる。 |
| 7 | 【確認】run 単位の outer receipt だけでは、per-mutation scheduler evidence を代替しない。fresh 1回なら最終 ledger の全 record が同じ job と推論できるが、これは outer manifest が真正かつ永続である場合だけ。 | [brief:58-60](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/brief.md:58)、[plan:345-378](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:345)、[artifact validator:859-908](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:859) | mutation 単位の job/node/rc/queue 証拠が消え、「各 verdict がどの scheduler 実行に属するか」が弱くなる。 | must-fix | outer manifest を正式な canonical artifact とし、「証拠粒度が run 単位へ変わる」ことを schema/decision に明記する。 |
| 8 | 【確認】提案 transport は ignored な `output/pegasus-dispatch/` にしか置かれない。既存凍結 ledger の例でも receipt/job stdout path はレビュー時点で既に不在だった。 | [.gitignore:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/.gitignore:25)、[plan:345-378](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:345)、[既存 ledger:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/output/insights/2026-08-02_t243-parallel-docs-spool/mutation-ledger.json:32) | 凍結台帳が参照する receipt/stdout/manifest が後で消え、hash の対象 bytes を再監査できなくなる。 | blocker | raw receipt、outer stdout/stderr、transport manifest、必要な request を tracked `output/insights/<wave>/evidence/` へ固定コピーし、その hash を台帳から結ぶ。 |
| 9 | 【確認】resume 時の attempt 対応を再構成できない。計画は ledger before/after hash を持つが、同じ ledger path を上書きし、旧 bytes や各 attempt の追加 record ID を保持しない。 | [plan:355-378](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:355)、[atomic overwrite:1790-1808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1790) | 複数 receipt があっても「どの mutation がどの attempt/job で完了したか」が一意に復元できない。 | must-fix | attempt ごとに immutable ledger snapshot、`completed_ids_before/after`、`added_record_hashes`、request ID を保存し、連鎖を validator で検査する。 |
| 10 | 【確認＋推論】local artifact の二つの hash は embedded stdout への自己整合であり、出力の意味を拘束しない。誤って outer stdout を両 field に入れれば照合は恒真化する。 | [artifact:849-856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:849)、[validators:1492,1563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1492) | 誤った出力対象でも hash は一致し、verdict の証拠が別 job/log にすり替わる。 | must-fix | inner/outer に異なる sentinel を出す契約テストを追加し、inner hash・outer raw-byte hash・receipt hash を別名・別 validator に固定する。 |
| 11 | 【確認】`LEDGER_SCHEMA` は v4 固定で、loader は exact schema/root keys/identity を要求する。bump すれば旧 v4 を拒否し、据え置けば compute-bundle provenance を内側 ledger だけで識別できない。repo 内の機械 reader は loader 以外を確認できなかったが、外部 reader は未確認。 | [schema:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:30)、[loader:1637-1668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1637) | bump は凍結 v4 の読取/再開を壊し、据え置きは同じ schema 名で証拠密度の違う台帳を並べる。 | must-fix | inner record の意味を変えないなら v4を維持し、必須・永続・相互参照付き `mutation-transport/v1` envelope を新設する。inner fieldsを変えるならv5とv4 read-only互換 branchを同時実装する。 |
| 12 | 【確認】G01 は targeted `-n 0` であり、親 brief の「全走 test command 不変」と矛盾する。段2自身も full suite の追加失敗、xdist、長大 stdout、cross-test interaction を見逃すと認めている。 | [brief:36-40](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/brief.md:36)、[plan:48-56](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:48)、[plan:148-168](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:148) | targeted では同値でも全走の `failed_nodes` / verdict が変わり、誤った GO を出せる。 | blocker | targeted run は smoke と明記し、GO 判定は2件以上を canonical 全走 command で dispatch/bundle 両方実行する。弱めるならユーザー再裁定が必要。 |
| 13 | 【確認】G01 の比較射影は事前記載されているが、恒久経路の task/env/receipt/manifest/hook を通らない。同じ `spool_fold.py` の3変異だけで、並列度差、順序依存、cross-node lock、長出力、resume を分けない。 | [plan:29-31](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:29)、[plan:86-146](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:86)、[DW-G01](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/dev-wave/core.md:42) | restricted verdict 一致が「移設全体が安全」という合格へ過大解釈される。 | must-fix | 合格条件を「restricted smoke」と「永久 GO」に分離し、後者に全走、恒久 dispatcher、transport validation、resume 1回を入れる。候補1件は別 subsystemへ振る。 |
| 14 | 【確認】§C の M01–M08/P01 は現在すべて old逐語 count=0、期待 node count=0で、DW-M04 の実在事前登録ではなく設計メモである。段2自身も段4再固定を宣言している。 | [plan:416-432](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:416)、[DW-M01](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/dev-wave/mutation.md:5)、[DW-M04](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/dev-wave/mutation.md:22) | 注入不能または別 gate に当たる候補を KILLED と数え、検出力台帳を水増しできる。 | must-fix | 段4で統合後の exact oldを `count=1`、期待 nodeをcollect実在へ固定するまで prereg と呼ばない。 |

## §C 候補の個別攻撃

| # | 所見 | file:line 根拠 | これが real なら成果物が何にどう変わるか | 深刻度 | 提案する最小の対処 |
|---:|---|---|---|---|---|
| 15 | 【M01】写像を直接読むだけの fixture は構造検査。wrong child が実際に scheduler/child 契約を壊したことを証明しない。 | [plan:420](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:420) | 診断文字列/定数だけで赤となり、実効 fail-closed の kill を過大計上する。 | must-fix | valid request を `_job_run` まで通し、実際に起動された child path と ledger artifact を観測する。 |
| 16 | 【M02】crafted child request で親 gate を迂回する方向は妥当。ただし親子が同じ helper を共有するなら、helper変異は両層を同時に弱め、二層独立性を証明しない。 | [plan:421,434](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:421)、[DW-M03](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/dev-wave/mutation.md:16) | 子だけの trust-boundary 欠陥か共通 validator 欠陥かが台帳から区別不能になる。 | must-fix | child 直 fixtureを維持し、親-only、child-only、共通 helper の threat を別IDにする。空 allowlist の正例も登録する。 |
| 17 | 【M03】dispatcher の `runner_mode` guard を消しても、計画する harness scheduler-envelope側が nested dispatch を拒めば mask される。 | [plan:422](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:422)、[plan:331-343](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:331) | 期待 node以外の後段 gateで同じ入力が拒否され、単一理由性が成立しない。 | must-fix | 実効 gateへ再照準するか、二重 gate の同時変異として明記し単独 kill 集計から外す。 |
| 18 | 【M04】pure estimator の数値 assertion は診断 kill である。`N+1` が実際に不足 walltime を受理する境界を示していない。 | [plan:423](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:423)、[DW-M03](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/dev-wave/mutation.md:16) | 数式が変わっただけで KILLED となり、実際の verdict/復元保護が未検証のままになる。 | must-fix | fixed は不足 request を qsub 前に拒否し、mutant は受理する境界 fixtureにする。直下の十分 walltime 正例も置く。 |
| 19 | 【M05】fake clock で queue のみ進める設計は概ね単一理由。ただし node は「fixed は active job を qdel しない／mutant はする」を観測すべきで、算術比較だけでは不足。 | [plan:424](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:424) | 赤がメッセージ差だけなら、実際の run 完遂/verdict保全を示さない。 | must-fix | qdel未呼出し、child rc伝播、receipt outcomeまで assertionする。 |
| 20 | 【M06】distinct temp root fixture は方向として妥当だが、legacy/composite lock が残れば shared lock mutantを手前で maskし得る。 | [plan:425](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:425)、[current lock:1814-1835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1814) | competitor が別 lock で拒否され、shared lock の検出力を誤って KILLED とする。 | must-fix | fixtureでは他lock namespaceを分離し、shared lockだけ同一にする。release後に双方を受理する正例も置く。 |
| 21 | 【M07】deadline fixture の残時間が不足すると collection/baseline/前 mutation の gateで先に落ちる。現 old/node は未実在。 | [plan:426](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:426) | 「次の mutation を適用しない」gate以外の失敗を killに数える。 | must-fix | baselineと第1 mutationは完遂し、第2 mutation直前だけ境界になる時計を固定する。十分時間の正例を追加する。 |
| 22 | 【M08】outer stdout hash の方向は妥当だが、stdout 一種類に偏る。receipt、ledger before/after、attempt delta の取り違えを殺さない。 | [plan:427](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:427) | stdoutだけ真正でも、別 ledger/別 attempt をreceiptに結べてしまう。 | must-fix | receipt hash、ledger hash、attempt追加IDをそれぞれ独立変異にし、inner/outer sentinelを分ける。 |
| 23 | 【P01】fresh/resume の正例を一nodeにまとめると、どちらが過剰拒否されたか分からない。他の新 rejection 軸の正例も不足。 | [plan:428](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage2-plan.md:428) | validatorが正常なfull command/shared path/empty envを拒否しても、受理集合縮小を十分検出できない。 | must-fix | fresh、resume、canonical full command、same repo、valid shared out、empty envを独立正例として登録する。 |
| 24 | 【確認】既存 task-enum test は親の unknown-task guardだけを消す変異に対して実効 killにならない。直後の `TASKS[task]` が `KeyError` にし、scheduler非到達とrc16は維持され、`"ValueError"` 診断 assertionだけが赤になる。 | [dispatch:956-960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/pegasus/dispatch_compute.py:956)、[test:1397-1426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/orchestrator/tests/test_pegasus_dispatch_compute.py:1397) | task closure の挙動が不変なのに KILLED と数え、受理集合検出力を水増しする。 | must-fix | unknown guard削除でなく、rogue entryを `TASKS` に追加して本当にschedulerへ到達させる変異へ替える。 |

## 追加すべき変異

「予定 anchor」は現時点では old が存在しないため、段4で `count=1` を確認してから登録すること。

| ID | file:line / old逐語 | 期待 node | 狙う実効 gate |
|---|---|---|---|
| A01 | [`dispatch_compute.py:68`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/pegasus/dispatch_compute.py:68)、old `    "provenance": _TaskSpec(` を「同じ provenance entryの前に固定 child の `rogue` entryを挿入」に置換 | `test_task_kind_enum_rejects_rogue_before_qsub` | task 受理集合を本当に拡大し、qsub呼出しで殺す |
| A02 | [`mutation_harness.py:1122`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1122)、old `        "PYTEST_ADDOPTS",` → `"PYTEST_ADDOPTS_DISABLED",`（現 count=1） | `test_bundled_full_run_ignores_pytest_addopts_selection` | 外部 `-k no_match` で全走が縮むことを殺す |
| A03 | [`dispatch_compute.py:1360`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/pegasus/dispatch_compute.py:1360)、old `        return child_rc` → `        return 0`（現 count=1） | 既存 `test_dispatch_state_machine_returns_child_rc_after_accounting` | child失敗を成功へ偽装する挙動 |
| A04 | 予定 anchor `_validate_mutation_request`、old `if inner_args != canonical_test_args:` → `if False and ...` | `test_mutation_task_rejects_targeted_or_selector_test_command` | canonical全走の受理集合 |
| A05 | 予定 anchor `_job_run`、old `child_env = _sanitized_child_environment(spec, requested_env)` → 現行 `os.environ.copy()` 型 | `test_job_run_scrubs_inherited_python_and_pytest_environment` | requested env以外の親環境漏洩 |
| A06 | 予定 transport anchor、old `"completed_mutation_ids_after": completed_after,` → `completed_before` | `test_mutation_transport_attempt_records_exact_record_delta` | receiptとmutation IDのattempt対応 |
| A07 | 予定 hook anchor、old `if _is_direct_mutation_harness(...):` → `if False and ...` | `test_bash_login_rejects_direct_mutation_harness_but_allows_plan_only` | login直 heavy run の受理集合 |
| A08 | 予定 persistence anchor、old `if not durable_transport_exists:` → `if False and ...` | `test_missing_durable_transport_is_infra_not_success` | 証拠未保存を成功扱いする挙動 |

## D117 契約照合

| 契約 | 段2案の状態 | 判定 |
|---|---|---|
| D105 supersede | 新D fragment案のみ。ユーザー裁定なし | 未充足 |
| 子側 `env_allowlist` 強制 | requested env の subset check は提案済み | 字面は部分充足。継承 `os.environ` が残るため実効契約は未充足 |
| stdin | `subprocess.call()` に `stdin=DEVNULL` なし、計画にも明記なし | 未充足 |
| cwd | request repoとの一致、job script `cd`、`os.chdir`、child `cwd` を提案 | 計画上は充足。symlink解決を同一 helperで固定する必要あり |
| artifact visibility | spec/out shared path検証は提案済み | 実行時可視性は部分充足。ignored sidecarとattempt対応欠落により証拠契約は未充足 |
| child rc の意味 | 0/1/2/3/16 を提案 | 部分充足。signal由来128+N、未捕捉例外、rc1時のledger完全性が未定義 |

## env allowlist の査定

| env | 無いと何が壊れるか | 判定 |
|---|---|---|
| `GIT_CONFIG_NOSYSTEM` | caller値を渡す必然性は確認できない。必要ならchild内で固定値`1`にできる | allowlist不要 |
| `IZANAGI_TEST_NPROC` | caller指定の並列度だけ変わる。無ければcompute affinity既定になり、suite集合は変わらない | 原則不要。必要なら範囲制約付き整数fieldとしてreceiptへ記録 |
| `IZANAGI_TEST_TRIGGER` | task-run IDを除いた内側runでsuite選択を保つ必要性を確認できない | 不要 |
| `IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS` | 無い方が deletion preflight は強い。通常mutationはファイル置換であり削除を要しない | 過大、削除 |
| `PYTEST_ADDOPTS` | 計画どおり非許可。harnessはinner runner直前に除去する | 非許可は正しい。ただしharness/probe起動前の親env全体は別途sanitize必須 |

## scope 分類

基準は「無いと verdict・復元・単一走行・要求された証拠のどれが壊れるか」。DW-G02/G04 は [`core.md:47-61`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/dev-wave/core.md:47)。

| 項目 | 分類 | 理由 |
|---|---|---|
| 固定されたcompute起動経路 | 不可欠 | 実行場所移設そのもの。ただし汎用第3 taskである必要はなく、専用sealed wrapperでもよい |
| argv/env/stdin/cwd/rc validator | 第3 taskを採るなら不可欠 | 無いとtask名だけ閉じても実行内容・path・環境の受理集合が開く |
| shared authoritative lock | 不可欠 | node-local `/tmp` のままでは単一走行を維持できない |
| 明示walltimeとqueue/running deadlineの整合 | 不可欠 | active jobの早期停止はverdict/復元を変える |
| `N+2` 自動walltime計算・queue query・係数1.5 | 本wave外 | 保守的な明示walltimeとhard boundで代替可能。DW-G02で後続へ送る |
| harness自己deadline・新rc3 | 本wave外 | scheduler signalと既存復元で成立するなら必須でない。発火artifactが無いならDW-G04で後続へ送る |
| durable transport envelope | 不可欠 | P4のrun単位証拠とresume attempt対応を失う |
| permanent composite lock | 条件付き | 旧runnerが生存する場合だけ必要。発火条件未確認 |
| cutover drain | 一回の確認は必要、恒久機構は本wave外 | live old jobが無いことを確認すれば恒久featureは不要。存在時のみDW-G04発火 |
| hook専用拒否＋harness site gate | 不可欠 | 無いとlogin直localが同じschemaの台帳を生成できる |

段2が落としている必須項目は、ユーザー裁定、canonical全走argvの固定、clean child env、stdin閉鎖、durable evidence archive、attempt record delta、login直起動gate、`test_check_docs.py` 更新、全走G01である。

## 新 gate の層網羅

| 層 | 現状/計画 | 判定 |
|---|---|---|
| 親 CLI | task membershipとargv/env validatorを提案 | 部分充足 |
| 子 `_job_run` | task membershipは既存、requested env再検査を提案 | 継承env・stdinで未充足 |
| job script | hostname/probe/cdは既存 | probe前のenv sanitizeなし |
| harness | scheduler-envelope案あり | login直 `runner_mode=local` を閉じない |
| hook | dispatcherは既にsanctioned | direct harness拒否がscope外 |
| tests/docs | dispatch/harness testsを列挙 | hook test、`test_check_docs.py`、永続artifact testが欠落 |

hook/harness層を実装scopeに入れない場合は、「sanctioned dispatcherだけを保証し、直 local を機械的には閉じない」という裁定パッケージとして返すべきで、全層 fail-closed を実装したとは主張できない。

## 総括

- blocker あり。恒久実装は NO-GO。
- 最大の証拠劣化は、per-mutation receipt/job stdout が消え、outer manifestまでignored pathで失われる点。
- G01はtargeted `-n 0`であり、親briefの全走不変を証明しない。
- §Cの9候補はold逐語・期待nodeとも未実在で、M03は後段gateにmask、M01/M04は診断kill寄り。
- D103ではなくD105/D117が支配的で、第3 task追加にはユーザー裁定が必要。
- 裁定択一は「D105/D117をsupersedeして厳格な第3 task」対「閉enumを維持した専用sealed wrapper」。
- 推奨は後者。変更面と受理集合を最小に保てる。
- テストは一切実行しておらず、静的所見のみである。