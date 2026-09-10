## 総括

- 対象 23 件: **closed 17 / partial 5 / regressed 1**
- 残る must-fix: **FA-8、FA-9、FA-12、FB-1、FB-2、P-2、OTHER-1、DOC-1**
- blocker: **なし**。FA-1 の 35 分待機は閉じ、guard が通常 Bash 操作を全面停止する事象もなかった。
- 判定: **NO-GO**。実 F47 の見逃し、guard の literal command 迂回、無効な M7 変異証明が残る。

なお、pytest、実 qsub/qstat、build、mutation は実行していない。以下の `closed` は必須資料、全 `git diff HEAD`、実装・テストの静的追跡に基づく判定であり、実走緑を意味しない。

## 所見ごとの対応表

| ID | 判定 | 根拠／残る失敗シナリオ |
|---|---|---|
| FA-1 | closed | 一度構造化 ID が可視になった後、rc=0 で ID が消えれば END になる。[dispatch_compute.py:882](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:882)、実測文字列を使う期待は [test_pegasus_dispatch_compute.py:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:223)。投入直後の不在は終端ではなく F47 扱いになる。 |
| FA-2 | closed | `STG/Staging→QUE`、`EXT/Exiting/Post-running→END`。[dispatch_compute.py:130](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:130)、[test_pegasus_dispatch_compute.py:238](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:238)。 |
| FA-3 | closed | `site_policy.py` は future import 済み。[site_policy.py:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/site_policy.py:3)。FIX-A の production 3 module を静的に固定している。[test_site_policy.py:253](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_site_policy.py:253)。統合差分中の production Python 9 ファイルにも全て future import があることを別途確認した。 |
| FA-4 | closed | marker の write は計算ノード用 job script 内だけ。[dispatch_compute.py:279](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:279)。親は job ID・bnode hostname を検証するだけ。[dispatch_compute.py:490](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:490)。 |
| FA-5 | closed | request ID 一致と Started/Ended/Elapse の全連言。[dispatch_compute.py:465](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:465)、`MemoryError` 等の反例は [test_pegasus_dispatch_compute.py:463](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:463)。 |
| FA-6 | closed | preferred/fallback の双方が保存不能なら必ず rc=16。[dispatch_compute.py:1029](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:1029)、[test_pegasus_dispatch_compute.py:495](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:495)。 |
| FA-7 | closed | qsub 復帰時刻を起点とし、RUN 未観測なら終端時刻による上界と `observed=false` を記録。[dispatch_compute.py:817](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:817)、[dispatch_compute.py:926](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:926)。 |
| FA-8 | partial | 通常の parse 失敗→探索→qdel は閉じた。[test_pegasus_dispatch_compute.py:590](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:590)。ただし `qsub rc=0` → line 813 の receipt capture／line 814 の分岐中に SIGINT/SIGTERM → `active` はまだ false → line 1046 の cleanup を通らず孤児になる。[dispatch_compute.py:799](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:799)。 |
| FA-9 | regressed | transient 1 回→再試行は閉じたが、全 3 回 qstat 非ゼロだと即 infra・非ラッチになる。[dispatch_compute.py:827](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:827)、[test_pegasus_dispatch_compute.py:391](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:391)。実 F47 はまさに `Not permitted` の非ゼロ応答かつ marker/課金なしだった。[failures.md:888](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/failures.md:888)。入力 `F47資格情報不整合` → `qstat非ゼロ×3` → generic infra・ラッチなし → 次回も再投入、となる。 |
| FA-10 | closed | 全節目が共通の `flush=True` 出力を通る。[dispatch_compute.py:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:157)、呼出例 [dispatch_compute.py:798](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:798)。 |
| FA-11 | closed | M5 は probe と `_job_run()` の両層を通る。両方を落としたときだけ最終 assert が赤になり、それ以前の同入力 gate はない。[test_pegasus_dispatch_compute.py:292](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:292)、[dispatch_compute.py:224](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:224)、[dispatch_compute.py:336](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:336)。 |
| FA-12 | partial | 期待赤 node は実在するが、fixture が親／dispatcher の前段除去を迂回し、job shell へ task-run 変数を直接注入している。[test_run_tests_task_run.py:177](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_run_tests_task_run.py:177)。通常入力では先に [run_tests.py:816](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:816) と [dispatch_compute.py:710](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:710) が除去する。下流二層変異→人工 fixture は赤、実経路の受理挙動は不変、となり KILLED の自己追認になる。 |
| FA-13 | closed | テスト側の literal 9 要素と production 定数を独立照合。[test_run_tests_preflight.py:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_run_tests_preflight.py:26)、[test_run_tests_preflight.py:691](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_run_tests_preflight.py:691)。 |
| FA-14 | closed | 恒真 field は削除され、qsub 遅延・RUN 未観測を実時計で検査。[test_pegasus_dispatch_compute.py:546](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:546)、[test_pegasus_dispatch_compute.py:581](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:581)。 |
| FB-1 | partial | 分離形 `python -m module` は閉じた。[guard_bash.py:387](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:387)。しかし `python3 -mtools.pegasus.exec_calibrate argv.json` と `python3 -mpytest -q` は有効な Python CLI なのに ALLOW。解析が `args[i] == "-m"` だけだからである。[guard_bash.py:391](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:391)、[guard_bash.py:432](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:432)。 |
| FB-2 | partial | `env -S` と `exec -a` は閉じた。[guard_bash.py:294](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:294)。一方、元レビューの literal shell 形 `bash -xec 'pytest -q'`、`sh -euxc 'cmake --build build'` は ALLOW。`-c/-lc/-ic` の完全一致しか再帰しない。[guard_bash.py:169](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:169)、[guard_bash.py:509](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:509)。 |
| FB-3 | closed | configure と build の gate を別 node・別入口で観測するため、後段 gate の mask がない。[test_build_site_gate.py:249](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_build_site_gate.py:249)、[test_build_site_gate.py:287](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_build_site_gate.py:287)。 |
| FB-4 | closed | production `main()` が live site を注入し、LOGIN で rc=2 になる期待 node がある。[guard_bash.py:827](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:827)、[test_hooks.py:729](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_hooks.py:729)。 |
| FB-5 | closed | Ninja は読み取り専用 tool の閉集合のみ許可し、`clean` 等を拒否。ctest の `--show-only=<fmt>` も許可。[guard_bash.py:175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:175)、[guard_bash.py:488](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:488)、[test_hooks.py:646](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_hooks.py:646)。 |
| P-1 | closed | AGENTS.md は単一 nodeid を含む全 pytest を明示禁止。[AGENTS.md:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/AGENTS.md:29)。 |
| P-2 | partial | §8 の test/build/coverage の区別は実装と一致。[pegasus-runbook.md:371](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:371)。しかし §7 は依然「計算ノードでは最大並列」と無限定に主張する。[pegasus-runbook.md:259](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:259)。§7だけを入力→buildcache を `-j48` と解釈→実装既定16／provenance契約と不一致、が残る。 |
| P-3 | closed | 正常 dispatch は子 rc、rc=16 は infra/SUSPECT のみと一義化。[decisions.md:4558](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/decisions.md:4558)。 |
| P-4 | closed | `-n16` 未測定と最速非主張を runbook・D102 の双方が明記。[pegasus-runbook.md:272](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:272)、[decisions.md:4528](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/decisions.md:4528)。 |

## 独立検査

### FA-1 / FA-9 / marker

FA-1 は親実測の正確な `Batch Request: <ID> does not exist on nqsv.`、rc=0 を fixture が再現しており、可視後の次 poll で END、子 rc=0 に到達する。初回 qstat 成功・ID不在は END にせず F47 ラッチになるため、投入直後の偽終端も作っていない。

FA-9 は逆に過剰緩和されている。「qstat 失敗そのものではラッチしない」は transient には正しいが、3 回失敗後に marker を待たず終了するため、既知の `Not permitted + markerなし + 課金なし` も generic infra に落ちる。

marker は production scan 上、計算 job script の write と親 verifier 以外に生成箇所がない。親が marker を書く自己確認経路はない。ただし unit test の fake scheduler は当然 marker を模擬生成するため、実 FS 永続性そのものは今回実走していない。

### 変異の再照準

| 変異 | 判定 | 前段 mask／赤理由／事前登録 |
|---|---|---|
| FA-11 / M5 | 有効 | probe より前に 3.9 を拒否する検査なし。probe＋`_job_run()` の両方を落とした場合だけ `pipeline_rc == INFRA_RC` が単独で赤。期待 node は [fa.md:39](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/fa.md:39) に mutation 未走前から登録済み。 |
| FA-12 / M7 | **無効** | 通常経路では親 pop と dispatcher allowlist が先に同入力を除去する。fixture はそこを通らず job shell に直接注入するため、赤理由が実受理挙動に束縛されていない。期待 node の登録自体はあるが、proof として無効。 |
| FB-3 / M11 | 有効 | configure は subprocess 到達、build は helper 直接呼出で相互 mask がない。各 node の赤理由は一つ。期待 node は [fb.md:30](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/fb.md:30) に登録済み。 |

### テストの甘化

- `git diff HEAD` 上、skip / xfail の追加はない。
- 揮発性の実 PBS payload は焼き込まれていない。`424242` は fake scheduler ID、`874129` 等は実測を説明する docs。
- FA-13 は literal 期待集合になっている。
- build の一部 wiring testは production policy から jobs を導出するが、別の site-policy testが `COMPUTE=48`、`OTHER=16` を literal に固定しているため、全体として自己追認にはなっていない。
- material な例外は FA-12 の人工的な M7 fixture。

### 非 Pegasus (`OTHER`)

通常域は、HEAD版と現行 `decide(..., site="OTHER")` の代表 25 command を比較して差分 0、test cap 32・buildcache jobs 16 も維持されている。

しかし「1 bit も不変」は厳密には成立しない。

`site=OTHER`、`process_cpu_count()=None`、`sched_getaffinity()` が `PermissionError`、`cpu_count()=7` の入力では、

- HEAD版 `tools/run_tests.py:117-120`: 例外伝播、テスト非実行
- 現行 [site_policy.py:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/site_policy.py:81): 7 を採用して実行継続

となる。これは裁定 A7 の要求と `OTHER` 完全不変が衝突しているため、例外として仕様へ明記するか、site別に扱う裁定が必要である。

### guard_bash

production `main()` に LOGIN site の JSON を入力した軽量 probeでは、次の 8 例がすべて hook rc=0だった。各コマンド自体は実行していない。

| 通常操作 | hook rc |
|---|---:|
| `git status --short` | 0 |
| `python3 tools/check_docs.py` | 0 |
| `codex exec review-this-diff` | 0 |
| `qsub job.sh` | 0 |
| `python3 tools/run_tests.py -q` | 0 |
| `rg TODO .` | 0 |
| `cat AGENTS.md` | 0 |
| `qstat -Q` | 0 |

したがってセッション全体を止める通常操作の偽拒否 blocker はない。一方、次はすべて LOGIN でも hook rc=0だった。

- `python3 -mtools.pegasus.exec_calibrate argv.json`
- `python3 -mpytest -q`
- `bash -xec 'pytest -q'`
- `sh -euxc 'cmake --build build'`

また `pytest -h` は非実行形だが拒否される。[guard_bash.py:428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:428)。成果物影響を示せないため、これは must-fix ではなく backlog とする。

### docs

P-1、P-3、P-4 は実装と一致。P-2 は §8 は正しいが §7 の無限定表現が残る。

加えて runbook §8 の F47 記述は現実装と一致しない。[pegasus-runbook.md:386](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:386) は親が作った receipt/output dir の即時確認を (a) の証拠とし、会計欠落を含む一件でも恒久停止すると書く。実装は計算ノード marker を終了後の猶予内に確認し、marker 有効・会計のみ欠落なら invocation 限定 rc=16でラッチしない。[dispatch_compute.py:956](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:956)。

D102 の「direct literal command は第二防壁で拒否」も、FB-1/FB-2 の literal 迂回が残る限り実装より強い主張である。

## 残る must-fix と成果物影響

1. **FA-8:** qsub 前後の signal cleanup を原子的にする。成果物影響: 親が infra 終了した後も孤児テストが走り、受入時の負荷・単独性を汚染する。
2. **FA-9:** qstat 全失敗後も bounded に marker／F47 証拠を収集して transient と資格情報不整合を分ける。成果物影響: 本物の不永続 submission をラッチせず、無効投入を反復する。
3. **FA-12:** M7 を親入力から最終 child までの実経路へ再照準する。成果物影響: mutation 台帳が二重記録防止を KILLED と誤記する。
4. **FB-1:** attached `-mfoo` / `-mpytest` を解析する。成果物影響: dispatcher receipt／task-run のないログインノード実行が成功扱いになり得る。
5. **FB-2:** `-xec` / `-euxc` 等、`c` を含む shell option bundle を再帰解析する。成果物影響: 同じくログインノード上の test/build が証拠なしで実行される。
6. **P-2:** runbook §7 を「テスト既定」と buildcache/coverage の例外まで限定する。成果物影響: operator が buildcache を最大並列化すると実 build argv の provenance を偽り得る。
7. **OTHER-1:** A7 の例外回復と OTHER 完全不変の矛盾を裁定する。成果物影響: 非 Pegasus の permission-denied host で task-run の有無と worker 数が旧版から変わる。
8. **DOC-1:** runbook §8 の F47証拠・marker時点・会計非ラッチを実装へ合わせる。成果物影響: 親自身の dir を永続性証拠にする自己確認や、一時的会計遅延による誤った恒久停止を誘発する。