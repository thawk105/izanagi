## 総括

この plan はそのまま段 5 へ進めてはいけない。S4 を blocking とした判断自体は正しいが、提示された「brief 改訂後の条件付き実装」も provenance を偽るため成立しない。

critical / must-fix は severity 順に次の 5 件。

1. **[real / critical] S4 の条件付き案は cache hit 時に架空の `-j N` を記録する。** `jobs` は cache identity/completion manifest に無い一方、`BuildResult` は呼出時の既定値でコマンドを再構成し、WAL・floor manifest・ratified `floor_source` へ流れる。
2. **[real / critical] hostname + `PBS_JOBID` だけでは「非 Pegasus 不変」と Pegasus 安全側判定を同時に保証できない。** 別サイトの同名 hostname を誤認でき、判定失敗は重い処理をログインノードで実行する側へ倒れる。
3. **[real / must-fix] task_run 台帳と top-level rc が二つの真実になる。** 子 pytest rc=0 を green と記録後、親が会計欠落で rc=16 を返せる。
4. **[real / must-fix] S5 は plan 文面どおりでは機械執行にならない。** import bootstrap 欠落、`python3 -m pytest`、wrapper、`bash -lc`、`--setup-only` に穴がある。
5. **[real / must-fix] 「全コア・全 build」は成立しない。** 明示 `-n1` / `jobs=1` を維持し、scope 外には login-node 前提・上限 8 の直接 CMake builder が残る。

refute した裁定は **P2、P3、P4、P6**。P5 は「新 hook ファイルではない」という狭い命題だけは成立するが、それをもって S5 の機械執行が成立するという含意は refute する。P1 の自動 dispatch という選択自体は refute しないが、現 plan では計算ノード readiness と台帳整合が不足している。

plan の file:line は **75 引用、68 unique file:line を照合し、物理的不実在は 0 件**。ただし、意味的な誤引用が 2 件、弱い間接引用が 1 件ある。

## 1. file:line・symbol 全件照合

**[real] 物理的不実在は 0 件。** 引用されたファイル、開始行、範囲終端はすべて実在した。既存 symbol も `_available_cpus`、`_has_no_execution_flag`、`_is_acceptance_run`、`_is_full_suite`、`_call_and_record`、`cache_key`、`_v2_commands`、`_run`、`decide`、`_head_and_args`、`normalize_request_id`、`_accounting_summary`、`_scheduler_name_matches` を含め実在する。新設予定の `site_policy.py` と `dispatch.py` は plan 自身が未実在と明記しており、虚偽 line 引用ではない。

意味上の問題は次のとおり。

- **[real] golden の引用対象が違う。** plan が「独立 golden にも jobs がない」と引く [test_s8b_protocol_builder.py:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_s8b_protocol_builder.py:47) は floor protocol の canonical golden で、buildcache completion manifest や `binaries[*].build_argv` を対象にしていない。`jobs` 非流入の証明にはならない。
- **[real] CPU fallback の説明がコードと違う。** plan は [plan_v1.md:82](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:82) で `process_cpu_count → sched_getaffinity → os.cpu_count` とするが、現コードは `sched_getaffinity` の `AttributeError` しか捕らえない。[run_tests.py:106–120](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:106)
  
  入力: Python 3.10、`os.sched_getaffinity(0)` が `PermissionError`、`os.cpu_count()==8`  
  期待: 8 へ fallback  
  実際: `PermissionError` で停止。
- **[弱い引用]** [s8b_ratified_freeze.py:1321](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_ratified_freeze.py:1321) は既存 `floor_source` を読む helper であり、凍結連鎖の構築箇所ではない。直接の連鎖は [同:2967–2984](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_ratified_freeze.py:2967) と [同:3032–3040](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_ratified_freeze.py:3032)。

## 2. hostname 判定と非 Pegasus 不変条件

[plan_v1.md:70–80](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:70) の規則には次の反例がある。

| 区分 | 入力 | plan の判定 | 誤った結果 |
|---|---|---|---|
| **[real] false positive** | `socket.gethostname() == "pegasus02.example.invalid"`、PBS なし | 最初の label が `pegasus02` なので LOGIN | 非 Pegasus 機でテストが qsub/rc16 になり、cap32 の従来挙動を失う |
| **[real] false positive** | hostname `bnode123.other.example`、`PBS_JOBID=0:42.nqsv` | COMPUTE | 他サイトで test/build が affinity 全数となり、従来の cap32 / j16 を失う |
| **[real] false negative** | 実 bnode 上で `env -u PBS_JOBID ...`、または正規化済み `PBS_JOBID=873225.nqsv` | OTHER | 計算ノードなのに test cap32 / build j16 |
| **[real] fail-open** | Pegasus login で `socket.gethostname()` が `OSError` | OTHER | 重いテスト・build をログインノードで直接実行 |
| **[疑い] 将来 hostname** | `pegasus04`、または OS hostname が共通名 `pegasus` | 明示的に OTHER | 新 login node で直接重量処理。現時点の実ノードは 01–03 なので発現は未実測 |

特に二つ目は、hostname と PBS 環境変数がともに衝突・注入可能なので、brief の「hostname と PBS だけに依存して非 Pegasus へ漏らさない」[brief.md:33–40](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/brief.md:33) 自体が証明不能である。

`HOSTNAME` 環境変数の汚染だけでは plan は誤判定しない。これは **refuted**。一方、`PBS_JOBID` の汚染は直接判定に入る。`socket.gethostname()`、`platform.node()`、`/proc/sys/kernel/hostname` は通常同じ UTS hostname を見るため、単純な多数決にもならない。コンテナの UTS/mount namespace や shell 起動時から古い `HOSTNAME` が残った場合には差が出るが、plan は差を診断記録にも残さない。

さらに dispatcher の親環境 allowlist は [plan_v1.md:118](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:118) に `PBS_JOBID` を含まない。**[疑い]** これを子 `subprocess` の完全な `env` として実装すると、計算ノードの scheduler-owned `PBS_JOBID` まで消え、子自身が OTHER になる。親由来 allowlistと、ジョブ環境から取得する scheduler-owned variables を明確に分離すべきである。

### fail-open / fail-closed の向き

高コストなのは **Pegasus false negative** である。共有 login node で重量処理が走り、F3 型の外乱・計測汚染を起こす。[failures.md:52–60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/failures.md:52) 非 Pegasus false positive は開発停止になるが、rc16 として可視であり、誤った成果物を作らない。

`hooks/README` は proof-chain 書込みを unknown=fails-closed とする一方、読み取り衛生だけを被害がトークンだから fail-open としている。[hooks/README.md:59–70](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/README.md:59) [同:74–90](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/README.md:74) 本件を一律 OTHER に畳むのは後者の向きで、重量処理防止には不適切である。

必要なのは少なくとも `KNOWN_OTHER / PEGASUS_LOGIN / PEGASUS_COMPUTE / PEGASUS_SUSPECT` の分離である。一般 hostname は従来挙動、`pegasus*`・`bnode*` なのに証拠不足なら重量処理だけ停止、としなければ両不変条件を扱えない。

## 3. 既存 gate・rc・task_run 台帳

既存 preflight の順序を 13→15→14 のまま維持し、dispatch をその後へ置く点、および `_is_acceptance_run` と `_is_full_suite` を流用しない点は整合している。[run_tests.py:784–810](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:784) D97 が退けた二義化も避けている。[decisions.md:4298–4329](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/decisions.md:4298)

ただし task_run は破綻する。

**[real / must-fix] 入力から破綻まで:**

1. `IZANAGI_TASK_RUN_ID=X` を持つ login 親が dispatch。
2. compute 子の pytest が rc=0。
3. 子は `_call_and_record()` で `exit_status=0` を書く。[run_tests.py:724–775](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:724)
4. ジョブ終了後、親が `.e` または会計痕跡を取得できず rc16。[plan_v1.md:150–154](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:150)
5. 親は台帳を書かない設計。[plan_v1.md:112–118](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:112)

結果は「top-level rc16」なのに台帳は green。aggregate は rc0 を green、その他を infra と明確に区別する。[aggregate.py:149–201](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/task_runs/aggregate.py:149)

逆に compute 側 xdist 不在や dispatcher bootstrap 失敗では `_call_and_record()` に届かず、rc16 の infra run 自体が台帳から消える。dispatch receiptだけでは task_run aggregate は読まない。

したがって process の `rc=0` 自体は「子 rc0かつ会計照合済み」で一義的にできるが、**台帳の green と top-level success が同義でなくなる**。dispatch 専用 event、または親・子を一つの correlated run として確定する commit protocol が必要である。

D96/D97 に従う新 D と境界テストは必須。[decisions.md:4269–4296](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/decisions.md:4269) `tools/check_wave_startup.py` は qsub を明示的に scope 外としているため readiness の代替にはならない。[check_wave_startup.py:1–6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/check_wave_startup.py:1) dev-wave checker は rc16も単なる `CHECK_FAILED` へ畳む。[checker.py:320–344](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/dev_waves/checker.py:320)

また、会計一時欠落で create-only の `submission-disabled.json` を立てた後の、安全な解除手続が plan にない。[plan_v1.md:154–156](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:154) `.e` の遅延一回で、この wave 自身の再受入まで恒久停止し得る。P3 の escape/recovery 全廃と両立しない。

## 4. jobs と proof chain

独立照合結果は次のとおり。

| 面 | `jobs` / `-j N` 流入 | 根拠 |
|---|---:|---|
| `cache_key()` | なし | [buildcache.py:121–135](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:121) |
| v2 identity | なし | [buildcache.py:219–234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:219) |
| `contract_sha256` | なし | [env_contract.py:97–102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/env_contract.py:97)、[同:145–160](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/env_contract.py:145) |
| v2 completion manifest | なし | [buildcache.py:527–538](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:527) |
| `BuildResult.build_argv` | **入る** | [buildcache.py:335–367](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:335) |
| campaign WAL | **入る** | [pipeline.py:501–516](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/pipeline.py:501) |
| floor manifest/result | **入る** | [s8b_floor_campaign.py:988–1014](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_floor_campaign.py:988)、[同:1138–1155](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_floor_campaign.py:1138) |
| ratified `floor_source` | **入る** | [s8b_ratified_freeze.py:2967–2984](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_ratified_freeze.py:2967)、[同:3032–3040](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_ratified_freeze.py:3032) |
| 既存 WAL golden/fixture | **逐語で入る** | [bench_first_screen_reject…jsonl:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/fixtures/bench_first_screen_reject_6f169f90.jsonl:2) |

**[real / critical] cache-hit 失敗シナリオ:**

- 非 Pegasus で j16 の v2 binary を cache に作る。
- 同一 identity を Pegasus compute で呼ぶ。
- cache entry は `jobs` を持たないので hit。
- planned `_v2_result()` は現在地の j48 で `build_argv` を再構成する。[buildcache.py:469–485](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:469)
- `cached=true` の binary が実際には j16 で作られたのに、WAL/floor は j48 と記録する。

legacy 経路も cache hit 前に呼出時 `jobs` でコマンドを組み立てるため同じ問題を持つ。[buildcache.py:584–605](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:584)

したがって [plan_v1.md:289–293](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:289) の「今後は実際の affinity 由来値を正直に記録」は成立しない。actual build argv を completion metadata または別の durable build receipt に保存し、cache hit はそれを読む必要がある。それは completion schema・fixture・consumer の改修であり、brief の proof-chain 不変条件をさらに狭める裁定が要る。

既存 `output/s8b-freeze` bytes が自動的に書き変わるわけではない点は **refuted**。しかし新しい floor/WAL/result bytes は変わる。また登録済み Pegasus receipt は既に `-j 48` を逐語保存している。[calibration-753f…json:12–38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:12)

**[real / should-fix] 非 Pegasus 挙動も完全には不変でない。** coverage 4 箇所を `subprocess.run(..., check=True)` から `buildcache._run()` へ寄せると、非ゼロ時の例外が `CalledProcessError` から `RuntimeError` へ変わる。[s2_verify_calibration.py:244–250](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s2_verify_calibration.py:244)、[buildcache.py:739–745](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:739)

入力: 非 Pegasus、CMake build rc=2  
現行: `CalledProcessError`  
plan 後: stderr末尾だけを持つ `RuntimeError`。  
少なくとも失敗契約の互換性が変わる。

## 5. guard_bash

### import と live 配線

**[real / plan 欠落]** plan は run_tests の repo-root bootstrapを明記する一方、guard には「policy importを追加」としか書いていない。[plan_v1.md:47–49](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:47)、[同:201–205](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:201)

guard は `$CLAUDE_PROJECT_DIR/hooks/guard_bash.py` として直接起動される。[settings.json:19–25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/.claude/settings.json:19) 現在は stdlib importだけである。[guard_bash.py:42–53](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:42) ここへ単純に `from orchestrator.campaign ...` を足すと repo root が `sys.path` に無い。top-level importなら `main()` の例外処理にも届かず、内部で捕えて OTHER に倒せば direct heavy commandを許可する。どちらも不正である。

unit testを `decide(..., site=...)` 注入にすること自体は環境非依存なので正しい。したがって「unitがPegasusと他環境で必ず異なる」は **refuted**。しかし既存 subprocess smoke は guard_bash について `ls` と protected WAL書込みしか試さない。[test_hooks.py:757–797](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_hooks.py:757) production `main → current_site → heavy refusal` の連鎖は一度も発火せず、F21 型の seam-only 恒真保証が残る。[failures.md:263–273](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/failures.md:263)

### command 静的検査

以下は新規則未実装のため、plan 文面と現 parserからの**静的予測**であり、実走結果ではない。

| command | plan上の結果 | 判定 |
|---|---|---|
| `git status` | allow | 正常 |
| `python3 tools/check_docs.py` | allow | 正常 |
| `python3 tools/check_codex_agents.py` | allow | 正常 |
| `python3 tools/run_tests.py -q` | allow | 正常。ただし一次 policy が OTHER へ失敗すると login 実走 |
| `qsub job.sh` | allow | 正常 |
| `pytest -q` | deny | 正常 |
| `python3 -m pytest -q` | allowになり得る | **偽許可**。specは `python3.10` しか列挙せず、F41の正式形は `python3 -m pytest` |
| `sudo -u tanab pytest -q` | head=`tanab` | **偽許可**。wrapper option parserが文字列の option 値を飛ばせない。[guard_bash.py:176–196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:176) |
| `bash -lc 'pytest -q'` | recursionなし | **偽許可**。planは exact `-c` のみ |
| `python3 tools/run_tests.py --setup-only` | sanctioned + no dispatch | **偽許可**。pytest fixture setupは実行される |
| `ninja -t targets` | deny | **偽拒否**。read-only introspectionだがhelp/version以外を全拒否 |
| `make -n -j48` | deny | **偽拒否**。dry-runでも `-j` だけで拒否 |
| `python3 tools/run_tests.py && pytest -q` | 第2 segment deny | 正常 |
| `codex exec ...` | allow | 正常。ただし Codex 自体には hook 未配線。[hooks README:15–24](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/README.md:15) |

P2 の `--setup-only` 除外は特に成立しない。repo の全 suiteには autouse fixtureがあり、環境を変更する。[conftest.py:116–129](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/conftest.py:116) さらに module fixtureは実 CCBench材料の構築・検証を行い、fixtureによっては複数のgit subprocessも起動する。[test_s1_measurement_freeze.py:43–60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_s1_measurement_freeze.py:43)、[test_task_run_ledger.py:38–59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_task_run_ledger.py:38) これは「非実行形」ではない。

## 6. 親 brief の実測一般化

- **[refuted]「計算ノードで Python 3.10 を一度も測っていない」ではない。** runbook は job `0:873225.nqsv` で `/usr/bin/python3.10` を実使用済み。[pegasus-runbook.md:157–162](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:157)
- **[refuted] xdist にも計算ノード上の過去実測がある。** bnode003 で Python 3.10.12、pytest 9.1.1、xdist 3.8.0。[2026-07-26_t057-test-suite-speed.md:11–20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/output/insights/2026-07-26_t057-test-suite-speed.md:11)
- **[疑い / must resolve]** これは一部node・過去時点の観測であり、全bnode・現在の user-site importabilityを保証しない。`/home` は共有だが、`site.ENABLE_USER_SITE=False`、`PYTHONNOUSERSITE`、HOME差、minor版差なら `~/.local` は見えてもimportできない。[pegasus-runbook.md:327–328](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:327)
  
  入力: bnode上で `/usr/bin/python3.10` は存在するが `import xdist` が失敗  
  結果: 全候補不合格→rc16、pytest未起動、task_runも無し。安全側停止ではあるが、P1が求める準拠経路は提供できない。
- **[疑い / must resolve]** login の `g++-13` 不在は compute の toolchainを証明しない。登録済みbnode011 receiptは実際に g++-11 を使っている一方、buildcache の既定は g++-13。[calibration-753f…json:29–38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:29)、[buildcache.py:118](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:118) computeでもg++-13が無ければ全走はC++依存テストをskipしてrc0になり得る一方、実buildは失敗する。F22に従い、計算ノードで依存全量を事前列挙し、skip数とtoolchainを受入証拠に含める必要がある。[failures.md:275–287](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/failures.md:275)
- **[real]** `jobs` が cache key に無いという実測・静的事実から、「wall-clockだけ変わりproof chainは変わらない」は導けない。上記のとおり実行コマンドbytesへ流れる。

F46 の教訓に対し、候補Pythonを計算ノード内で版数/import gateする方針は正しい。[failures.md:871–886](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/failures.md:871) ただし「fail-closedで検出できる」と「このwaveの受入が実行可能」は別問題である。

## 7. provisional 裁定

- **P1: 未refute。ただし現実装案は未成立。** 自動dispatchは技術的に可能だが、compute dependency readiness、scheduler-owned環境の保持、task_run commit protocolが必要。
- **P2: refute。** `--setup-only` はfixtureを実行し、`--collect-only` もmodule importとcollection hookを実行する。「非実行形」の閉集合が誤っている。
- **P3: refute。** hostname衝突した非Pegasus機、compute false-negative、または一度立ったsubmission-disabled latchから回復不能になる。無制限なenv bypassは不可だが、監査済み recovery/unlatch と、受入rc0には使えないbreak-glass診断経路が必要。
- **P4: refute。** plan自身が明示 `-n` と `IZANAGI_TEST_NPROC` の後勝ちを維持する。[plan_v1.md:108](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/plan_v1.md:108) `-n1` は1 workerで走る。実build canaryも `jobs=1` を明示する。[test_s8b_floor_campaign.py:2378–2381](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_s8b_floor_campaign.py:2378) 「既定だけ最大」と「すべて最大」は別である。
- **P5: 狭義では成立、S5達成の根拠としてはrefute。** ファイル数は増えないが、import失敗・wrapper bypass・Codex未配線がある。
- **P6: refute。** proof-chain/WAL consumer改修と、scope外の直接campaign buildを扱わずに「全buildをcomputeで最大並列」は達成できない。

## scope 外 real

**[scope 外 real] `t152_write_intent_coverage.py` が brief の「全build」から漏れている。**

このdriverは buildcacheを通らず直接CMake buildし、`DEFAULT_JOBS=MAX_JOBS=8` で固定されている。[t152_write_intent_coverage.py:37–44](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/t152_write_intent_coverage.py:37)、[同:340–385](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/t152_write_intent_coverage.py:340) 成果物も `host_role: login-node` と記録する。[同:684–706](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/t152_write_intent_coverage.py:684)

入力例:

```bash
IZANAGI_T152_CCBENCH_SHA=<sha> CMAKE_PREFIX_PATH=<deps> \
python3 orchestrator/campaign/t152_write_intent_coverage.py
```

guardはPython script越しの内部CMakeを見ず、buildcacheのlogin gateも通らない。その結果、Pegasus login上で複数のj8 buildが実行できる。これは親が裁定パッケージへ回し、S4/P6のscopeを再定義すべき real finding である。

以上は全て静的検査であり、pytest・qsub・cmakeは実走していない。緑の報告はない。