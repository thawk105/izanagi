## 総括

**判定は NO-GO。段5へ進めてはいけない。** plan 自身の S4 blocking に加え、運用面でも成立していない。

- 具体的な実行経路を **47 経路族**監査し、現 plan が止められないものは **34 件**。S4 の blocking を解消して条件付き実装まで行っても **32 件**残る。止まる13件中12件は Claude Bash hook 内だけで、Codex・端末・IDE等には効かない。これは機械保証ではなく、明確に**「謳うだけの保証」**である。
- dispatcher の致命的死因は最大3件に絞ると、(1) queue/HLD/親死亡を扱う期限付き状態機械・leaseがない、(2) 計算ノードの pytest/xdist/packaging と nested `python3` 実行環境が未実測、(3) `.o/.e`・会計の遅延を即時欠落と誤認して全体ラッチし得る、である。
- 1 wave の現実的な dispatch 回数は **6〜12回**。queue 待ちが1回5分なら **30〜60分**、10分なら **1〜2時間**が純粋な待ち時間になる。単一テストにも同じ待ちが入る現設計は、混雑時の通常 dev-wave として**成立しない**。
- 運用上 refute する親裁定は **P1、P2、P3、P4、P5、P6の全件**。
- pytest、qsub、cmake は一切実走していない。緑の報告はない。

## 1. 迂回可能性の悉皆

判定の `止まる*` は「Claude Code の Bash PreToolUse 内なら止まる」の意味であり、他 surface まで含む保証ではない。根拠は Codex hook が未配線であることと、既存 hook 自身が script・変数展開を既知限界としていること（[hooks/README.md:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/README.md:15)、[同:163](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/README.md:163)）。

| # | 経路 | plan後の判定 | 止めるべきか |
|---:|---|---|---|
| 1 | `python3 tools/run_tests.py ...` 通常CLI | 止まる・dispatch | 要 |
| 2 | `run_tests.main(..., site=OTHER)` を直接呼ぶ | 止まらない | 要 |
| 3 | `python3 -m pytest` | 止まる保証なし。plan は `python3.10` しか具体化していない | 要 |
| 4 | `python -m pytest` | 止まらない | 要 |
| 5 | `python3.10 -m pytest` | 止まる* | 要 |
| 6 | `pytest` | 止まる* | 要 |
| 7 | `py.test` | 止まる* | 要 |
| 8 | `.venv/bin/python -m pytest` | 止まらない | 要 |
| 9 | `.venv/bin/pytest` | basename 判定なら止まる* | 要 |
| 10 | `python3 -c 'import pytest; pytest.main(...)'` | 止まらない | 要 |
| 11 | `python3 driver.py` 内で pytest を呼ぶ | 止まらない | 要 |
| 12 | alias/function/改名symlink `pt` 経由 | 止まらない | 要 |
| 13 | `tox` / `nox` / `uv run pytest` / `poetry run pytest` | 止まらない | 要 |
| 14 | `run_tests.py --setup-only`、help/collect＋重いplugin初期化 | dispatchされない | 実コードが動く形は要 |

| # | 経路 | plan後の判定 | 止めるべきか |
|---:|---|---|---|
| 15 | `bash -c 'pytest ...'` | 再tokenizeが正しく実装されれば止まる* | 要 |
| 16 | `sh -c 'cmake --build ...'` | 同上 | 要 |
| 17 | `bash script.sh` | 止まらない | 要 |
| 18 | `sh script.sh` | 止まらない | 要 |
| 19 | `T=pytest; "$T" -q` | 止まらない | 要 |
| 20 | `CMD='cmake --build b'; sh -c "$CMD"` | 止まらない | 要 |
| 21 | `eval "$CMD"` | 止まらない | 要 |
| 22 | base64等で復号して shell stdin へ流す | 止まらない | 要 |
| 23 | `xargs` / GNU parallel がcommand fileを読む | 止まらない | 要 |
| 24 | `python3 -c 'subprocess.run(["cmake","--build",...])'` | 止まらない | 要 |

| # | 経路 | plan後の判定 | 止めるべきか |
|---:|---|---|---|
| 25 | `cmake --build` | 止まる* | 要 |
| 26 | `cmake -S ... -B ...`。FetchContent/compile probeを含み得る | 明示的に許可 | 重い形は要 |
| 27 | `cmake --install`。大量copy/custom scriptを含み得る | 止まらない | 重い形は要 |
| 28 | `make -j48` / `--jobs` | 止まる* | 要 |
| 29 | `ninja -C ...` | 止まる* | 要 |
| 30 | `ctest` | 止まる* | 要 |
| 31 | `make`（`-j`なし） | 止まらない | 要 |
| 32 | `gcc` / `g++` / `clang++` を直接多数起動 | 止まらない | 要 |
| 33 | 通常の `buildcache.build/build_v2` | S4未実装なので止まらない。S4解除時だけ止まる | 要 |
| 34 | `_run(..., site=OTHER)` 正規注入seam | S4実装後も止まらない | 要 |
| 35 | coverage 4 module の直接実行 | S4未実装なので止まらない。条件付きでのみ停止 | 要 |
| 36 | `silo_ladder_rung1.py` の直接build経路 | 止まらない | 要 |
| 37 | `t152_write_intent_coverage.py` の直接build経路 | 止まらない | 要 |
| 38 | その他 Python module 内の `subprocess.run(cmake...)` | 止まらない | 要 |
| 39 | allowlist済み `tools/pegasus/exec_calibrate.py argv.json` | 任意argvを `execv` でき、止まらない | 要 |
| 40 | `build-variants/...` / `ycsb_*.exe` の直接実行 | 止まる* | 要 |
| 41 | 改名・symlink・別directoryの任意バイナリ | 止まらない | 要 |
| 42 | `ld-linux` / `gdb --args` / `valgrind` 経由 | 止まらない | 要 |
| 43 | `perf stat/record ...` | 止まる* | 要 |

| # | surface | plan後の判定 | 止めるべきか |
|---:|---|---|---|
| 44 | `codex exec` 子が内部shellでpytest/build | 止まらない | 要 |
| 45 | Codex の直接 subprocess/exec surface | 止まらない | 要 |
| 46 | Claude以外のAI、plugin、MCP、automation tool | 止まらない | 要 |
| 47 | ユーザー端末、SSH、tmux、IDE test runner、cron | 止まらない | 要 |

特に重大なのは次である。

- **real:** plan は `site` をテスト用の正式注入seamとして公開するため、P3の「escape hatchなし」と正面衝突する（[plan_v1.md:94](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:94)、同:189、同:203）。
- **real:** `tools/pegasus/*` の一括許可は広すぎる。`exec_calibrate.py` はJSONの先頭argvをそのまま `os.execv()` する（`tools/pegasus/exec_calibrate.py:12-42`）。これは sanctioned path 内にある汎用実行トランポリンである。
- **real:** S4 の caller 棚卸しは不完全。直接CMakeを持つ `silo_ladder_rung1.py:2111-2142, 3786-3814`、`t152_write_intent_coverage.py:355-387` がscope外に残っている。
- **refuted:** `HOSTNAME=bnode001 PBS_JOBID=...` の単純な環境変数偽装だけでは `socket.gethostname()` は変わらないため、通常CLIのsite判定は欺けない。
- **real:** ただし未知host・policy import失敗は `OTHER` へfail-openする計画なので、hostname変更、将来の`pegasus04`、import破損では全防壁が消える（[plan_v1.md:76](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:76)、同:235）。

## 2. dispatcher の運用的死因

| シナリオ | 判定 | planが壊れる箇所 |
|---|---|---|
| gen_S queue混雑 | **realな設計欠落／現在の混雑は疑い** | marker待ち・queue timeout・最大待ち時間・interactive fallbackがない。各テストが無期限に親を塞ぐ。queue構成は変わり得る（runbook §0）。 |
| 2時間walltime kill | **real** | 2時間はcertification値の転用にすぎず、test envelopeを導出していない。PBS kill前のfinalize reserveがなく、resultが残らずrc16へ潰れる。既存rung1は残walltimeを検査する（`silo_ladder_rung1.sh:399-426`）。 |
| `qsub`失敗 | **realだがfail-closed** | rc16で停止するだけ。transient retry、別queue、qloginへの引渡しがなく、全テスト不能。nonce directoryだけ増える。 |
| `qstat`一時障害 | **real** | immediate 1回の失敗をF49無効セッション扱いし、`submission-disabled.json`を永久ラッチし得る。schedulerの瞬断が全wave停止に昇格する。 |
| jobが`HLD` | **realな未設計状態** | qstat可視だけは満たすがcompute markerは来ない。QUE/RUN/HLD/終了の状態機械も期限もなく親が待ち続ける。 |
| 親sessionが先に死亡 | **real** | SIGINT/SIGTERM以外、SIGHUP、例外、SIGKILL、ホスト切断を回収できない。release前なら最大2時間待つ孤児、release後なら重い孤児testになる。 |
| `.o/.e`返却遅延 | **real** | NQSVのeventualなlog返却にgrace/retryがない。欠落と早合点してrc16＋全体ラッチになる。 |
| `.o/.e`数十MB | **real** | repo配下 `/home` に置く設計でquotaを圧迫する。既存collectorはstderr全文を `read_text()` する（`collect_receipt.py:147-151`）。size cap、streaming accounting scan、tail制限がない。 |
| 同一dirへの複数wave | **衝突自体はrefuted** | nonceごとのqsub cwdなら `.o/.e` は分離される（[plan_v1.md:126](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:126)、同:140）。ただしglobal `submission-disabled.json` はwave間で相互停止する。 |
| `$PBS_O_WORKDIR`とworktree | **real** | planはsubmission dirからqsubするため `$PBS_O_WORKDIR` はrepo rootではない。jobのcwd契約が未定義。runbookが要求するworktree submodule実体化も、targeted runでは警告だけで続行する（`run_tests.py:577-642`）。 |
| queue中のsource drift | **疑いだが設計上可能** | commit/tree/dirty bytesをsnapshotせずlive worktreeを実行する。他sessionが編集すると「投入したコード」と「走ったコード」が変わる。 |

release marker方式はF49の裏取りには有効そうに見えるが、lease・heartbeat・期限がないので、F47型事故を「消えるrequest」から「2時間残る孤児request」へ変えるだけである。

## 3. 計算ノード上で成立するか

runbookの実測事実だけで判定すると **NO-GO（成立未確認）** である。

| 前提 | runbook実測による判定 |
|---|---|
| `python3` | **不成立が実測済み。** Intel Python 3.9.13へ解決する（[runbook:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:157)）。 |
| `/usr/bin/python3.10` | **成立。** 3.10.12の実使用実績あり。 |
| top-level interpreter選択 | 候補gateで回避可能。ただし候補選択自身を3.9互換shellで実装する必要がある。planは未指定。 |
| nested `python3` / shebang | **不成立。** top-levelだけ3.10にしても、`#!/usr/bin/env python3` や子の `python3` は3.9へ戻る。`tools/task_run.py:1` 等、多数存在する。PATH先頭へ選定3.10のshimを置く設計がない。 |
| pytest / pytest-xdist / packaging | **未実測。致命的。** runbookに計算ノード上のimport成功事実がない。ログインノードのxdist 3.8.0を一般化できない。 |
| `~/.local` Python 3.10 site-packages | **未実測。** `/usr/bin/python3.10` がusersiteを読むか、`PYTHONNOUSERSITE`、module環境、venvがどうなるか不明。 |
| 外部network | **不可が実測済み**（runbook §7.1）。package欠落をjob内pipで修復できない。 |
| `_ensure_xdist()` | 正しくcompute認識された通常経路では呼ばない計画なのでpip経路は閉じる。ただしsite false-negativeでは現行pip→失敗→直列fallbackが復活し、「最大並列」を破る。 |
| `git` | runbookの実ジョブで `git worktree` / `git ls-files` が使われており、利用可能性は支持される。ただしdispatcher preflightとしての `command -v` は必要。 |
| g++-13 | **計算ノードでは未実測。** 3本のreal-build canaryは不在ならskipするため、計算ノード全走rc=0でもC++検出力が得られる保証はない（`test_s8b_floor_campaign.py:2357-2393`、`test_s8b_oracle_driver.py:3817-3822`）。 |
| `/scr` | 計算ノード限定で成立。colon除去も必要。 |
| `/work`・`/home` | 共有可視性は支持される。ただし大量logは `/work` 優先というrunbook §6にplanが反する。 |
| worktree submodule | **事前実体化が必要という実測あり**（runbook §7.1）。dispatcherはsnapshotも実体化receiptも持たない。 |

さらに、親 brief の「task_run記録の実行環境が計算ノードになる」は成果物として証明できない。`test_run` eventのfieldにはhostname、PBS job ID、queueが存在せず（`tools/task_runs/schema.py:321-325`）、queue待ちもcompute childの `duration_s` に入らない。記録処理は例外を全て握りつぶすbest-effortである（`run_tests.py:693-721`）。この主張は台帳の実フィールドに存在しない。

## 4. 待ち時間の実害

trigger名は回数の義務ではないが、現waveの分割から保守的に推定すると次になる。

- baseline: 1
- U1/U2/U4のafter-change: 最低3。S4を解放すれば4
- 親の統合後受入: 1
- review-fix / after-failure: 0〜2
- 変異matrix: 1〜4
- final: 1

したがって **6〜12 dispatch** が現実的下限である。単一nodeidを何度も再走すればさらに増える。

| 1回のqueue待ち | 6 dispatch | 8 dispatch | 12 dispatch |
|---:|---:|---:|---:|
| 2分 | 12分 | 16分 | 24分 |
| 5分 | 30分 | 40分 | 60分 |
| 10分 | 60分 | 80分 | 120分 |

runbookの「投入7秒後に開始」は1回だけの観測であり、混雑時の上限ではない（runbook §3）。一方、実計算ノード全走は `-n48=132秒`、`-n16=91秒` の実績があるため、5分queueなら**実行より待ちが長い**。

さらに毎回 `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` を再実行するので、12回ならpreflightだけで48 scheduler/accounting callになる。certification用の重い提出手順を単一テストへ複製している。

結論は、queue待ちが常時秒単位という未証明前提に依存しない限り、通常dev-waveとして成立しない。

### 代替設計

| 案 | 長所 | 短所 | brief不変条件との整合 |
|---|---|---|---|
| waveの段5〜6中、1つの `qlogin -q interactive` allocationを保持 | queue待ち1回、即時targeted test、実環境preflightを最初に1回実施可能 | allocation中のLLM思考時間は48 coreを遊ばせる。切断に弱い | 開始時にhostname/PBS/affinity=48をgateすれば重い処理は全てcompute |
| 1本のresident qsub worker＋0700 request queue | queue待ち1回、親切断後も継続、Codexはloginで編集しcompute workerへ依頼可能 | lease、認証、source snapshot、shutdownが必要で実装量が大きい | network不要。全commandをcomputeで実行できるが、まず100行以下の生死probeが必要 |
| mutation/受入を1本のbatch内でまとめる | 変異ごとのqueue待ちを1回へ圧縮。snapshot内で変異・復元可能 | 編集→結果→再編集の対話性はない。batch内の復元保証が必要 | 重い処理はcompute。DW-M05の復元検査をjob内に移す必要あり |
| qloginでtargeted、最終全走だけqsub | 日常feedbackと切断耐性の折衷 | allocationが2種類になり運用が複雑 | どちらもcomputeなので不変条件は維持 |

推奨は「段5〜6で1 allocationを再利用し、最終全走・変異matrixは1本のbatchへ束ねる」案。ただし計算ノードは外部network不可なのでCodex自体を計算ノードへ移してはならず、login側controllerとcompute側command workerを分離する必要がある。

## 5. 「最大限並列」の実効性

**real:** `affinity=48` は「48 coreを所有している」の意味ではない。gen_Sは48/48割当だが `Exclusive submit=OFF` である（[runbook:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:45)）。

- 同nodeに別の48-thread jobが同居すれば、最悪96 runnable worker/48 physical coreとなり、CPUだけなら各jobの実効能力は概ね半減し得る。両jobが115 GiBを前提にすればOOM競合も起きる。
- memory上限115 GiBを48 workerで割ると、master・OS・build子を無視しても **2.40 GiB/worker**。10 GiBを予約すれば **2.19 GiB/worker**。各worker 2 GiBならpytestだけで96 GiBとなり、CMake/linker子で上限へ接近する。
- 既存実測は `-n32=10.5s`、`-n96=13.0s`。worker数を3倍にして時間が **23.8%悪化**し、処理率も約 **19%低下**している（`tools/run_tests.py:10-15`）。
- より強い計算ノード実測では、bnode003専有で `-n48=132s`、`-n32=132s`、`-n16=91s`。48は16より **45%遅い**（[worklog archive:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/archive/worklog-phase3-0726-12-0727-19.md:82)）。
- real-repo groupのcritical pathは81秒で、workerを増やしても短縮できない。同実測では高並列によりsubprocess系flakeも発生している。
- planは明示 `jobs=1` を維持するため、real build canaryは計算ノードでも1並列のまま（[plan_v1.md:178](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:178)、`test_s8b_floor_campaign.py:2378-2382`）。これはP4の逐語に違反する。
- test側も明示 `-n1` を後勝ちで許すので、「既定48」であって「全実行48」ではない。

それでもユーザー指示どおり48を既定にするなら、最低限次を記録すべきである。

- PBS job ID、queue、assigned host、queue待ち時間、RUN開始時刻
- requested worker数、actual affinity、actual起動worker数
- pre/postの同居job・`pgrep`・load・PSI
- master/worker別RSS、job全体peak RSS、OOM/memory event
- Python実体・version、pytest/xdist/packaging version、module list、PATH
- wall time、worker startup時間、collected/passed/skipped/failed、flake再走結果
- `-n16/-n32/-n48` の対照。ただし既定を勝手に16へ戻さず、「48が遅い」という結果を正直に残す
- `jobs=1`、CLI `-n` 等の明示上書きがあった場合は「最大並列ではない」と記録する

## 6. 既存 Pegasus 資産との重複

新dispatcherにはdirty dev worktree、同期rc返却、task_run引渡しという固有要件はある。しかしplanは、それが既存資産を再利用できない理由を示していない。

重複する機能は少なくとも次である。

- nonce/create-only submission dir
- qstat/pegasusinfo/budget/quota preflight
- qsub stdout/stderr capture
- request ID parser
- immediate qstat
- submit receipt
- Python候補gate
- `/scr` job dir
- scheduler log/accounting照合

既存資産の方が持ち、新planから落ちているものもある。

- 危険なcompiler/CMake/Python/Git環境変数の消毒（`silo_ladder_rung1.sh:48-58`）
- Pythonのisolated mode
- qstat 30秒timeout
- scheduler残walltimeの実測とfinalize reserve
- source identity、job script hash、qsub cwdの束縛
- compute側failure receipt
- pinned third-party staging

planは `collect_receipt.py` のprivate helperだけを再利用し、submission本体を四重実装しようとしている（[plan_v1.md:152](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:152)）。これは規律5「盛らない」に反する。少なくとも以下の比較なしに新規dispatcherを正当化できない。

1. 既存submitterから共通submission核を抽出できない理由  
2. 既存script hash/proof chainを変更できない範囲  
3. dirty worktree用の差分だけを薄いwrapperにできない理由  
4. resident allocation/qloginという既存runbook経路を却下する理由  

## 7. 親 brief の一般化への攻撃

- **real:** `pegasus02`上のPython 3.10、xdist 3.8.0、96 coreはログインノード1台の観測であり、計算ノードのpackage/site/PATHを証明しない。
- **real:** 計算ノードで成立が証明されているのは `/usr/bin/python3.10` の存在まで。pytest/xdist/packagingの同時importは未実測。
- **real:** top-level Pythonだけ選び、nested `python3` が3.9へ戻る問題を親もplanも落としている。
- **real:** compute上のg++-13は未測定。移動後もC++ canaryがskipする可能性がある。
- **疑い:** 「3,900件級全走が他利用者への外乱源になる」は合理的なリスクだが実測ではない。runbookが証明するのは共有nodeと全coreを掴まない運用方針までで、実際のCPU/RSS/load・他利用者影響は測っていない（[brief:45](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/brief.md:45)）。
- **real:** dev-wave契約は別programを起動する成果物について実行時依存をbrief前に実測するよう要求する（`docs/dev-wave/core.md:33-39`）。compute package probeなしでdispatcherをbrief化した時点で順序違反。
- **real:** briefは75行あり、dev-wave契約の10〜30行を超えている（`docs/dev-wave/core.md:24-31`）。scope外の形式所見だが、詳細設計をbriefへ先取りした結果、実測gateが埋没している。

## 8. P1〜P6 の refute

| 裁定 | 判定 | refute理由 |
|---|---|---|
| P1 自動dispatch | **REFUTE** | qloginという準拠経路は既にrunbook §2にあるため「自動dispatchがなければ準拠経路なし」は偽。しかもS4は拒否のみで、自説と不整合。 |
| P2 全testを1件でもbatch dispatch | **REFUTE** | 単一testへnode1台・2時間requestを要求し、queue待ちが本体になる。`--setup-only`等も実コードを動かせるのに非実行扱い。 |
| P3 escape hatchなし | **REFUTE** | `site=OTHER`注入seam、policy import fail-open、未知host、直接pytest、script、Codex等が事実上のescape hatch。名前付きenv varを置かないだけ。 |
| P4 affinity全数=max | **REFUTE** | affinityは専有でも最速でもない。実測で48は16より45%遅い。明示`-n`・`jobs=1`も温存するため逐語保証にもならない。 |
| P5 既存hookへの追加だから規律5非衝突 | **REFUTE** | file数ではなく機構複雑性が問題。既知限界を持つ文字列blocklistを拡大してもsandboxにならず、Codexには未配線。 |
| P6 scope外列挙 | **REFUTE** | campaign driver、Codex/他surface、既存submitter再利用をscope外にすると「全て計算ノード」が達成不能。scopeを狭めるなら成果物名も「sanctioned entrypointの一部」へ狭めるべき。 |

## scope 外 real

- repo hookだけでユーザー端末・IDE・任意バイナリまで禁止するのは不可能。真の全経路保証にはsite管理者側のlogin-node cgroup、scheduler policy、OS-level wrapper等が必要。
- task-run schemaにhost/PBS ID/queue waitがなく、briefが主張する実行環境移動を台帳で証明できない。schema変更は現scope外だがreal。
- S4の `build_argv` 凍結連鎖問題はplan自身が既に示した別レンズのreal findingであり、これだけでも段5停止条件である。
- `silo_ladder_rung1.py`、`t152_write_intent_coverage.py`、`exec_calibrate.py` は現scope外扱いが不当で、ユーザー要求を保つならscope内へ戻す必要がある。

以上はDW-S03/DW-O05に従う静的敵対検査のみ。実機probeがないまま「計算ノードで成立」と裁定してはならない。