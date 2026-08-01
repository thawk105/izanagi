NO-GO。防壁を偽緑にできる経路と、成立していない変異 kill が残っています。

## 総括

- must-fix: **11件**
  1. F49(a) 実 FS 永続性検査が自己確認
  2. 会計サマリ判定が偽陽性
  3. receipt 保存失敗が fail-open
  4. queue wait 値が誤計測・欠落
  5. `exec_calibrate` の module 形式で exact allowlist を迂回
  6. `env -S` / `exec -a` wrapper 迂回
  7. M5 / M7 / M11 の mutation kill が無効または未被覆
  8. `AGENTS.md` が login 上の pytest を例外許可
  9. runbook の build 並列度が実装・D102と矛盾
  10. D102 の login rc が自己矛盾
  11. `-n16` 未測定のまま「最大並列コストゼロ」と断定
- 仕様未実装: **9件**（§2〜§5 の実挙動 6件、§8 の mutation 証明 3件）
- 恒真・自己追認型の保証: **3件**
- 判定: **NO-GO**

必須資料はすべて読めた。現在の worktree は追跡済み17ファイル＋未追跡3ファイル。pytest・build・qsub は実行していない。軽量な純関数呼び出しで guard の迂回だけ再現した。

## must-fix

1. F49(a) の「実 FS 永続性」が同じ namespace の自己確認になっている

   [dispatch_compute.py:590](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:590) でファイルを作り、[dispatch_compute.py:421](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:421) が同じ path を `is_file()` するだけで、[dispatch_compute.py:666](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:666) で `output_dir_persistent=True` にする。計算ノードや別セッションからの観測がない。

   失敗シナリオ: private overlay に request/script が存在し、`qsub` と `qstat` は成功するが計算ノードからファイルが見えない → 自己検査は真 → F47 ラッチされず、後で generic infra failure になる。

   成果物影響: `submission-disabled.json` が作られず、receipt の `outcome.kind` が `f47` ではなく `infra` になり、同じ不永続環境から rc=16 の task-run を反復投入できる。

2. NQSV 会計サマリの判定が一単語 OR で偽陽性になる

   [_ACCOUNTING_RE:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:43) は `memory`、`walltime`、`nqsv` 等のどれか1語だけで真になり、[dispatch_compute.py:750](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:750) がそれを会計確認済みとして受理する。

   失敗シナリオ: 子 rc=0、`.e` に子自身の `memory usage warning` があるが、終了後の NQSV 会計サマリは未到着 → `accounting_verified=True` → rc=0。

   成果物影響: dispatcher receipt と task-run 台帳が未会計ジョブを緑として記録し、受理集合が裁定 §3 より拡大する。

3. receipt を一度も保存できなくても子 rc を返す

   [_persist_receipt():497](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:497) は preferred/fallback の両方が失敗すると `None` を返すが、成功経路の [dispatch_compute.py:793](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:793) は戻り値を無視して子 rc を返す。

   失敗シナリオ: 子 rc=0・会計確認済みだが、権限・容量・create-only 衝突で両 receipt write が失敗 → top-level rc=0、receiptなし。

   成果物影響: task-run 台帳だけが緑になり、PBS ID・host・interpreter・会計照合への参照が欠落する。

4. queue wait の起点が早すぎ、RUN を観測できないと値自体がない

   timer は `qstat -Q` より前の [dispatch_compute.py:624](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:624) で始まり、[dispatch_compute.py:696](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:696) でそのまま queue 起点になる。`queue_wait_s` は RUN を poll したときだけ [dispatch_compute.py:710](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:710) 記録される。

   失敗シナリオ: preflight 10秒＋qsub 20秒＋実 queue 30秒 → receipt は60秒を記録する。QUE と次の poll の間に完了した短い job → `queue_wait_s` 自体が欠落する。

   成果物影響: §9 の受入レポートに載る queue wait が過大または欠損する。

5. `exec_calibrate` は module 形式で exact-path 拒否を迂回できる

   [_script_target():317](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:317) は `python -m` の module 名を path として解決しない。したがって `python3 -m tools.pegasus.exec_calibrate argv.json` は許可される。対象 module は [exec_calibrate.py:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/exec_calibrate.py:32) で JSON 内の任意 argv を `os.execv` する。

   失敗シナリオ: JSON に `["python3","-m","pytest","-q"]` を置き module 形式で起動 → guard は許可 → login node で pytest 実行。

   成果物影響: dispatcher receiptも task-run 親記録もない login-host 緑が完了報告へ混入し、実行環境参照が誤る。

6. wrapper parser が executable を値として捨てる

   `env -S` は value option として登録されているが [guard_bash.py:183](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:183)、[_skip_wrapper_options():260](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:260) は split-string 内の command 全体を捨てる。`exec -a harmless pytest -q` も `-a` を未知 flag として飛ばし、`harmless` を head と誤認する。

   失敗シナリオ: `env -S 'pytest -q'` または `exec -a harmless pytest -q` → `decide(..., LOGIN)` が許可 → 実 shell は pytest を実行。

   成果物影響: login-host test/build の受理集合が広がり、計算ノード receipt・台帳参照を欠く緑が作れる。

7. M5・M7・M11 は有効な mutation kill になっていない

   - M5: [test_pegasus_dispatch_compute.py:183](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:183) は probe の AST が変われば赤になる。しかし probe を記録だけにして3.9を選んでも、[_job_run():287](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:287) が再度 version/import を拒否する。受理挙動は変わらない。
   - M7: [test_run_tests_task_run.py:138](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_run_tests_task_run.py:138) は fake dispatcher seam だけを見る。親の pop を変異しても、dispatcher allowlist、job script、job child の [dispatch_compute.py:553](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:553)、[dispatch_compute.py:259](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:259)、[dispatch_compute.py:309](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:309) が後段で除去する。
   - M11: 新テストは `_run_cmake_build` を直接検査するだけ（[test_build_site_gate.py:200](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_build_site_gate.py:200)）。coverage 各 module の configure 直前 gate、例えば [s2_verify_calibration.py:262](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s2_verify_calibration.py:262) を削除すると、login で configure が走り、その後の build gate が拒否するだけで新テストは赤にならない。

   失敗シナリオ: M5/M7 を単一変異 → structural/fake testだけ赤、実受理挙動は不変。coverage configure gateを削除 → login configure実行にもかかわらず該当 red nodeなし。

   成果物影響: mutation 台帳が M5/M7/M11 を `KILLED` と誤記し、F46・台帳一回性・build gate の証明強度を過大報告する。

8. `AGENTS.md` が login node の pytest を例外許可している

   [AGENTS.md:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/AGENTS.md:29) は全 partial test を計算ノードへ送ると言いながら、[AGENTS.md:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/AGENTS.md:32) で「自分が触った1ファイルの極小 pytest」を login 上で許可する。runbook §7 の [pegasus-runbook.md:255](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:255) と正面衝突する。

   失敗シナリオ: Codex が pegasus02 上で変更ファイル1本を直接 pytest → AGENTS上は準拠、裁定上は違反。

   成果物影響: completion report に PBS ID・compute host を持たない login-host pass が正規の緑として載る。

9. runbook の build 並列度が実装と D102 に反する

   [pegasus-runbook.md:370](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:370) は全 build の `-j` を割当コア数に合わせるよう要求する。一方、正しい実装は [buildcache.py:337](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:337) と [buildcache.py:571](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:571) で既定16を維持し、[decisions.md:4534](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/decisions.md:4534) もそれを要求する。

   失敗シナリオ: affinity 48 の compute で既定 buildcache → 実際は `-j16` → checklistでは不合格。checklistに従い `jobs=48` を渡す → cache hit の provenance が架空の `-j48` になりうる。

   成果物影響: build report が正しい `-j16` を違反扱いするか、WAL/floor/ratified 参照へ誤った build argv を流す。

10. D102 が同じ決定内で login の rc を二通り主張している

   [decisions.md:4522](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/decisions.md:4522) は dispatcher が子 rc を返すとするが、[decisions.md:4555](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/decisions.md:4555) は login node の test が rc=16 になるとする。実装は [run_tests.py:938](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:938) と [dispatch_compute.py:787](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:787) により、正常 dispatch 後は子 rc を返す。

   失敗シナリオ: login から投入した child rc=0 → 実装 rc=0、D102末尾の期待 rc=16。

   成果物影響: decisions 正本が `tools/run_tests.py` の受理集合とレポート判定値を誤って固定する。

11. `-n16` 対照前に「最大並列のコストは実質ゼロ」と断定している

   [pegasus-runbook.md:272](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:272) と [decisions.md:4528](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/decisions.md:4528) は48対32だけでゼロと結論している。仕様は [adjudication-plan-v2.md:241](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/adjudication-plan-v2.md:241) で、過去の48対16の45%差を検証する `-n16` 対照を必須にしている。

   失敗シナリオ: 48≈32だが48が16より遅い → docsは未測定の差をゼロと報告する。

   成果物影響: 受入レポートと D102 が未取得の対照結果を既知事実として記録し、最大並列既定の根拠を偽る。

## should-fix

1. F21型の production 配線回帰を検出できない

   LOGIN/SUSPECT のテストは `decide(..., site=...)` への直接注入だけ。[test_hooks.py:927](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_hooks.py:927) の subprocess smoke は `ls` と WAL 書込みしか実行せず、[guard_bash.py:726](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:726) の live site 注入を試さない。

   失敗シナリオ: `main()` が `_runtime_site()` を渡さない回帰 → direct unitは全て通る → production loginでは `pytest -q` を許可。

2. dispatch 免除「閉集合」テストが実装定数から期待値を導出している

   [test_run_tests_preflight.py:679](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_run_tests_preflight.py:679) は production の `_PEGASUS_DISPATCH_EXEMPT_FLAGS` 自体を parametrize する。

   失敗シナリオ: 誤って `--lf` を免除集合へ追加 → テストも自動的に `--lf` を正例扱い → login で test execution が dispatch されないのに緑。

3. guard の positive/introspection 境界が意味ではなく token 存在だけで決まる

   [guard_bash.py:385](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:385) は任意の `ninja -t` を許可するため、`ninja -t clean` も通る。[guard_bash.py:390](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:390) は `ctest --show-only=json-v1` を認識しない。

   失敗シナリオ: `ninja -t clean` → mutating toolを許可。`ctest --show-only=json-v1` →非実行形を拒否。

4. §9 の worker 数を receipt から構造的に復元できない

   request は元 argv だけを持つ（[dispatch_compute.py:573](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:573)）。result の [dispatch_compute.py:328](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:328) に worker 数がない。

   失敗シナリオ: `-n` 無指定 → compute child 内で48が決まる → receipt単独では実 worker 数が分からず、stdout解析に依存する。

5. task-run persistence は依然 best-effort

   [_record_task_run():725](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:725) と [_dispatch_and_record():893](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:893) は記録失敗を黙殺する。

   失敗シナリオ: child rc=0、台帳 write が OSError → top-level rc=0、台帳は0件。既存 convention を維持した形だが、A3の「親が1回記録」との境界を明文化すべき。

6. 実装子の pass 報告は compute 受入証拠として使えない

   [u1.md:20](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/u1.md:20)、[u2.md:24](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/u2.md:24)、[u3.md:41](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/u3.md:41)、[u4.md:19](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/u4.md:19) は直接 pytest/harness の結果だが、PBS ID・host・receipt がない。現セッションの hostname は `pegasus02`。

   失敗シナリオ: 親がこれらを計算ノード受入の緑として転載 → 実行場所を証明できない pass が最終レポートに入る。段9で再実行が必要。

7. 中核3ファイルが未追跡

   [dispatch_compute.py:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:1)、[test_pegasus_dispatch_compute.py:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:1)、[test_build_site_gate.py:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_build_site_gate.py:1) が `??`。

   失敗シナリオ: 親が `git commit -am` → dispatcher本体と検査がcommitから脱落 → login dispatchは import failure/rc16。

## nit

- `git diff --check HEAD` は [site_policy.py:127](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/site_policy.py:127) の余分な EOF 空行で失敗する。

  失敗シナリオ: diff hygiene gate → rc≠0。研究成果物への直接影響はない。

## 裁定 §2〜§5 照合

| 要件 | 実装位置 | 判定 |
|---|---|---|
| §2 stdlib-only・4文字列状態 | `site_policy.py:4,10` | 適合 |
| hostname小文字化・末尾dot・first label | `site_policy.py:19` | 適合 |
| `bnode[0-9]+` はPBS非依存COMPUTE | `site_policy.py:28,38` | 適合 |
| `pegasus0[1-9]`＋NQSV証拠 | `site_policy.py:40` | 適合 |
| unknown/hostname失敗のSUSPECT規則 | `site_policy.py:36,42,56` | 適合 |
| qsub＋qstat marker | `site_policy.py:47` | 適合 |
| refusal/API/message | `site_policy.py:65,73,115` | 適合 |
| CPU fallback・test/build既定 | `site_policy.py:78,100,108` | 適合。A7だけ裁定済み変更 |
| §3 rc16・keyword-only seam・gate順13→15→14 | `run_tests.py:107,910,917` | 適合 |
| dispatch免除の閉集合 | `run_tests.py:111,381` | 現行値は適合。テストは自己追認 |
| `--setup-only/show` 非免除 | `run_tests.py:111`、test `:696` | 適合 |
| `_NO_EXECUTION_FLAGS` 不変 | `run_tests.py:92` | 適合。`--setup-only` は既存集合に残る |
| SUSPECT拒否・LOGIN dispatch | `run_tests.py:927,938` | 適合 |
| COMPUTE xdist fail-closed・OTHER従来経路 | `run_tests.py:951,969` | 適合 |
| 子からtask-run ID除去、親1回記録 | `run_tests.py:816,858`、dispatcher `:553,309` | 実経路は適合。M7 killは無効、保存失敗はbest-effort |
| root/queue/node/walltime/qstat-Q | `dispatch_compute.py:24,562,627,637` | 適合 |
| job内interpreter/import/PATH/hostname/cwd assert | `dispatch_compute.py:186,235,248,253,287` | 実装は適合 |
| QUE/RUN/HLD・期限・qdel | `dispatch_compute.py:694,469` | 適合 |
| F49(a) real-FS persistence | `dispatch_compute.py:421,666` | **不適合 MF1** |
| F49(b) immediate qstat | `dispatch_compute.py:659` | 適合 |
| F49(c) 会計猶予 | `dispatch_compute.py:725,750` | 状態機械は存在、predicateは **不適合 MF2** |
| `.o/.e` bounded tail | `dispatch_compute.py:344` | 適合 |
| 子rc返却・infra16・receipt | `dispatch_compute.py:787,793` | rcは適合、receipt persistenceは **不適合 MF3** |
| §4 buildcache jobs=16 | `buildcache.py:335,569` | 適合 |
| cache hit前提と実cmake直前gate | `buildcache.py:598,749` | 適合 |
| coverage 4モジュール、`check=True`維持 | `s2:230`、`s3:123`、`s5:119`、`s8a:90` | 適合 |
| scope外3経路 | wave diff | 変更なし、適合 |
| §5 `decide(..., site=None)`・legacy gate順 | `guard_bash.py:644` | 適合 |
| import bootstrap・login fallback | `guard_bash.py:60,211` | 適合。import失敗は既知loginでfail-openしない |
| heavy direct forms・shell再帰・segment | `guard_bash.py:337,360,401,408` | 基本適合 |
| wrapper option処理 | `guard_bash.py:177,260` | **不適合 MF6** |
| sanctioned exact path | `guard_bash.py:161,317` | direct pathは適合、module形式は **不適合 MF5** |
| known limitationsの明記 | `guard_bash.py:37` | 適合。「全経路保証」は主張していない |

非 Pegasus について、未裁定の受理 bit 変更は静的差分から見つからなかった。`guard_bash` の `site=None` は [guard_bash.py:648](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:648) で新しい重量 gate を通らず、`run_tests.py` は [run_tests.py:969](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:969) の従来経路へ入る。OTHER の cap32 / build16 は [site_policy.py:100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/site_policy.py:100) で維持される。例外は裁定済みA7の `PermissionError` fallbackだけである。

skip/xfail の追加、既存 assert の削除、実PBS ID・hostname・hashの焼込みは見つからなかった。fake IDは固定fixtureである。一方、dispatch免除期待値の自己導出と production site 配線の未検査は上記のとおり。

## F46・F42

F46 の実装自体は「記録だけ」ではない。probe が version/import 失敗で非0を返し、job shellが選択を拒否し、さらに `_job_run()` が再assertする。ただし二重防壁のため、M5の単一変異は受理挙動を変えず、有効な mutation kill にならない。

F42 の自走 harness は静的に存在する。

- `test_site_policy.py`: `_run()` [253](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_site_policy.py:253)、`__main__` [275](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_site_policy.py:275)
- `test_build_site_gate.py`: `_run()` [253](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_build_site_gate.py:253)、`__main__` [271](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_build_site_gate.py:271)
- `test_pegasus_dispatch_compute.py`: `_run()` [403](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:403)、`__main__` [407](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:407)

`test_plain_runner_coverage.py` 自体は実行していない。

## M1〜M14 静的 kill 検査

| 変異 | 期待 red node | mask / 単一理由 | 判定 |
|---|---|---|---|
| M1 | site policy `:31`、preflight `:645` | 純分類の直後を観測、先行拒否なし | 有効 |
| M2 | site policy `:199` | COMPUTE 48を固定値で照合 | 有効 |
| M3 | site policy `:180` | `PermissionError` 単一fixture | 有効 |
| M4 | site policy `:217` | SUSPECT refusalを直接照合 | 有効 |
| M5 | dispatcher test `:183` | ASTだけ赤。後段version assertが実挙動をmask | **無効** |
| M6 | dispatcher test `:232` | immediate qstat削除は単一理由で赤 | 有効。ただしF49(a)は未証明 |
| M7 | task-run test `:138` | fake seamだけ赤。実dispatcherの3段除去がmask | **無効** |
| M8 | hook test `:529` | python実体variantを直接照合 | 有効 |
| M9 | hook test `:542` | `sudo -u` のhead誤認だけで赤 | 有効。ただし現行 `env -S` 穴あり |
| M10 | hook test `:559` | shell再帰削除だけで赤 | 有効 |
| M11 | build test `:118,200` | central/build helperは赤。coverage configure gate削除は未発火 | **部分無効** |
| M12 | hook test `:571` | import失敗fallbackを直接照合 | 有効 |
| M13 | site policy `:207` | OTHER/cap32/j16を固定値で照合 | 有効 |
| M14 | hook test `:625` | 登録済み3正例は単一理由 | 有効。ただしpositive集合は不完全 |

厳密な恒真・自己追認は次の3件である。

- F49(a): 書いた本人が同じ namespace で存在確認する。
- dispatch閉集合: production定数から正例を生成する。
- `queue_wait_included_in_parent_duration=True`: productionが無条件に書いた真偽値をテストがそのまま照合し、実時間関係を検査しない。