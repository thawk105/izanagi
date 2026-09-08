1.

- 所見: 2026-09-03 の 902/904 秒を切った層は collection が直接起動した dispatcher の queue-wait 900 秒であり、このプランの特定への攻撃は反証される。
- 根拠: `229e030a:tools/mutation_harness.py:1408-1418` は collection だけを `dispatch_compute.py` へ直結し、`tools/pegasus/dispatch_compute.py:68-71` は `DEFAULT_QUEUE_WAIT_TIMEOUT_S = 900.0`、poll 5 秒、`同:3951-3965` は `now - queue_started >= queue_wait_timeout_s` で `queue-wait-timeout` とする。候補のうち、当時の harness 外側 watchdog は実際には両方 5400 秒 (`docs/failures.md:10859-10867`)、本走側 D612 は 3600 秒 (`tools/run_tests.py:1346-1372`)、RUN 後 deadline は既定 3600+300 秒 (`dispatch_compute.py:3891-3946`)、accounting は 60 秒、cleanup は 90 秒、scheduler command は 30 秒 (`同:68-76,580-595`)、acceptance shard は 5100 秒 (`tools/run_tests.py:79,2323-2352`)、fanout barrier は 120 秒で以後無期限 (`tools/mutation_fanout.py:741-785,805-819`)、wrapper は `process.wait()` 無期限 (`tools/mutation_worktree.py:824-830`) である。さらに記録は child 未起動を明記する (`docs/failures.md:20564-20582`)。
- 判定: refuted
- 影響: 無し
- 対処: 904 秒の歴史的特定は採用する。

2.

- 所見: 親 brief と F762 の「collection / 本走とも dispatcher 直呼び」という原因記述は、本走について誤りである。
- 根拠: `229e030a:tools/mutation_harness.py:2049-2053` の baseline と `同:2169-2176` の mutation は、いずれも `_run_tests(repo, command, ...)` へ元の `command` を渡す。現行でも dispatch mode の runner は `tools/run_tests.py` だけに制限される (`tools/mutation_harness.py:775-810`)。直呼びは collection の `dispatch_compute.py` 構築だけ (`229e030a:tools/mutation_harness.py:1407-1418`) であり、親記述は `brief.md:24-30`、F762 は `docs/failures.md:20568-20572`。
- 判定: real
- 影響: 本走にも伝播欠落があったという原因帰属が誤り、不要な本走用伝播修正で harness の受理集合を狭め得る。実際の当時の失敗は collection で台帳作成前に止まる。
- 対処: 親 brief と裁定入力を「当時の欠落は collection 直呼びだけ」に訂正する。

3.

- 所見: 現行 HEAD の直接 harness 経路では、fresh collection、baseline、通常 mutation、hang mutation、resume pending mutationの全てに D612 上書きが届くため、伝播欠落は反証される。
- 根拠: collection は `_dispatch_timeout_overrides` の結果を `--queue-wait-timeout` / `--overall-grace` にする (`tools/mutation_harness.py:1395-1418,1445-1492`)。baseline と mutation は同じ `command` を使い (`同:2127-2134,2247-2258`)、`runner_env = os.environ.copy()` は D612 を除かない (`同:1933-1943`)。`run_tests.py:1295-1304` もコピーから D612 を除かず、`同:1346-1372` が dispatcher kwargs にする。resume は保存 collection と baseline を検証して pending mutationだけを同じ `_apply_mutation` へ送る (`mutation_harness.py:2697-2753,3141-3157,3262-3277`)。
- 判定: refuted
- 影響: 無し
- 対処: 伝播修正は追加しない。

4.

- 所見: fanout と worktree wrapper を経由しても D612 は失われず、commit 後ならプランの harness 内修正は全 shard に効く。
- 根拠: bounded scope は `environment = os.environ.copy()` を渡し (`tools/mutation_fanout.py:1380-1395`)、launcher の `Popen` は env を置換せず (`同:1617-1624`)、`os.execv` も現環境を継承する (`同:814-819`)。wrapper の `_git_env` が除くのは非許可 `GIT_*` だけ (`tools/mutation_worktree.py:138-145`)、harness child へその env を渡す (`同:746-749,805-818`)。wrapper resume も `--resume` を同じ child に付加する (`同:712-743`)。
- 判定: refuted
- 影響: 無し
- 対処: fanout、wrapper への別修正は不要であり、片側だけ直る問題もない。

5.

- 所見: restore、fanout contract、fanout driver 自身は新規 compute dispatch の呼び出し点ではなく、provenance と直接焦点走は別入口だが D612 を使うため、未列挙の伝播欠落経路はない。
- 根拠: restore は `target.write_text(original)` と検証だけ (`tools/mutation_harness.py:1199-1220`)。contract の process 起動は固定 HEAD 用 `git` だけ (`tools/mutation_fanout_contract.py:213-229`)。fanout driver は wrapper を起動するだけ (`tools/mutation_fanout.py:656-688,1617-1624`) で、失敗後の scheduler 操作も 30 秒の `qstat` / `qdel` 制御である (`同:1086-1096,1211-1249`)。provenance は `_dispatch_timeout_overrides(environ=os.environ)` を dispatcher kwargs へ展開する (`tools/check_ai_provenance.py:2307-2341`)。直接焦点走は `run_tests.py:1346-1372` の同じ D612 経路を通る。
- 判定: refuted
- 影響: 無し
- 対処: restore、contract、provenanceを本修正対象へ加えない。

6.

- 所見: プランの `outer_timeout_s >= Q_eff + G_eff` は dispatcher の締切構造を表しておらず、過剰拒否と取りこぼしの両方を作る。
- 根拠: queue timeout は `now - queue_started >= queue_wait_timeout_s` 単独で判定される (`tools/pegasus/dispatch_compute.py:3951-3965`)。`overall_grace_s` は `run_observed_at + walltime_s + overall_grace_s` にだけ加わる (`同:3891-3894,3936-3946`)。さらに cleanup は別の `cleanup_budget_s`、既定 90 秒である (`同:76,3653-3666`)。D612 parser は grace 0 も受理する (`orchestrator/tests/test_t2337_dispatch_timeout_overrides.py:35-40`) が、外側 `communicate(timeout=timeout_s)` は dispatcher の qsub と `queue_started = submitted_at` より先に始まる (`mutation_harness.py:1971-1999`; `dispatch_compute.py:3751-3775,3890-3892`) ため、Q=900、G=0、outer=900 というプラン上の等号正例でも外側が先に切り得る。
- 判定: real
- 影響: G が大きいだけの設定を queue 待ち不足として拒否する一方、G=0 の等号を通して orphan hold、rc=2、terminal record 欠落を許す。受理される mutation 実行集合と拒否境界が誤る。
- 対処: scope 外・裁定パッケージ候補。queue 待ち、RUN 後 walltime、cleanup のどこまでを外側 watchdog が覆う契約かを先に裁定し、G を queue slack と見なす現プランの式と 2400 秒等号テストは採らない。

7.

- 所見: 親の t2195 読解は、900 秒で切る層だけは hang mutation の外側 watchdog と正しいが、「5件が TIMEOUT として mutant に帰属する」という結果が誤りである。
- 根拠: hang mutation は `spec.hang_timeout_seconds` を選ぶ (`tools/mutation_harness.py:2247-2254`) が、timeout 後は status 算出より先に `_dispatch_orphan_stop` が呼ばれる (`同:2259-2269`)。dispatch mode の `timed_out` は必ず `OrphanHoldStop` を返す (`同:327-390`)、source は復元せず保全される (`同:2315-2357`)、main は最初の該当 mutation で rc=2 を返す (`同:3304-3313`)。また queue が 1800 秒まで QUE なら collection 自体が先に `queue-wait-timeout` となる (`dispatch_compute.py:3951-3965`)。
- 判定: real
- 影響: mutation summary の `TIMEOUT` は増えず、最初の該当 mutationにも terminal record は追加されない。残り4件へ進まず、fanout は wrapper rc=2 を拒否する (`tools/mutation_fanout_contract.py:1315-1323`)。
- 対処: 親 brief を「条件が揃えば最初の hang mutation の外側 watchdog が発火し、orphan hold と rc=2 で全走停止」に訂正する。

8.

- 所見: プランの新 gate は D612 の伝播修正ではなく、届いた値と spec の運用上の不整合を早期拒否へ変える別機構であり、主題の scope を超える。
- 根拠: 現行の伝播は所見3、4の全経路で成立し、親の完了条件は「上書きが届かない経路がコード上で0」 (`brief.md:9-10`)。一方、プランの新条件は `runner_mode == "dispatch" and bool(overrides) and timeout_s < Q_eff + G_eff` を新たに拒否する (`s2-plan.md:78-118`) だけで、上書きの転送も混雑下での走行可能性も増やさない。
- 判定: real
- 影響: 正しく上書きが届く既存 spec を起動前 rc=2 に変え、mutation 台帳と fanout 受入結果を生成不能にする。伝播についての値や受理集合は既に正しい。
- 対処: scope 内の最小対処は新 gate と helper refactor を本 wave から削ること。watchdog 互換性を機械化するなら scope 外・裁定パッケージ候補とする。

9.

- 所見: commit 前に実行不能なのは mutation/fanout 走行であり、通常の焦点 test まで commit 後へ送るというプランの理由付けは過大である。
- 根拠: 直接 harness 実走は tool bytes と HEAD blob の不一致を拒否する (`tools/mutation_harness.py:757-770`)。fanout wrapper は `git worktree add --detach ... preflight.commit` で committed checkout を作る (`tools/mutation_worktree.py:534-550`) ため、未 commit 修正は赤になる以前に実行対象へ入らない。merger も `_FIXED_HEAD_PATHS` の harness、wrapper、runner、dispatcher、contract を HEAD に束縛する (`tools/mutation_fanout_contract.py:35-41,232-266`)。対して焦点 test は作業木の module を直接 importする (`orchestrator/tests/test_t2337_dispatch_timeout_overrides.py:7-9`)。
- 判定: real
- 影響: 無し。結果値や受理集合は変わらないが、修正前赤の確認機会を不必要に失う。
- 対処: 順序は「commit 前に直接焦点 testで修正前赤と修正後挙動を確認できる範囲を確認、commit、その後に mutation/fanout 実走」とする。mutation/fanout を未 commit で走らせない点は維持する。

## 総括

(a) real の件数: 5 件。  
(b) 特定: 歴史的な 904 秒は正しく、fresh collection 直呼び dispatcher の queue-wait 900 秒である。現行の t2195 読解では最初の hang mutation の外側 900 秒が候補だが、帰結は TIMEOUT record ではなく orphan hold と rc=2。  
(c) プラン採用: そのままは不可。伝播 scopeを維持するなら実装を削除し、watchdog 互換性まで広げるなら deadline の意味と境界式を別裁定してから再計画する。  
(d) 親 brief の誤り: あり。本走直呼び、1800+300を queue 待ち2100秒とする説明、5件のTIMEOUT帰属、純増を伝播欠落とする分類が誤り。