## 走査プラン (層 A)

**閉包定義の補正**

P1 は producer と欠陥を分離して使う。層 A には calibration、sanity、偵察、正式測定をすべて含め、層 A に入っただけでは欠陥としない。各 producer に `calibration`、`sanity/probe`、`exploration`、`formal` の用途を付け、欠陥判定は層 B で行う。

producer 条件は次に補正する。

- CCBench 実行ファイルを直接または委譲先経由で起動し、stdout、perf 出力、経過時間から throughput、latency、counter、比較用統計を導出する。
- その実行前に、同じ source/build/configuration に束縛された verifier の certified 証拠を要求しない。
- `Genome` オブジェクトを使わない shell/native 経路もあるため、「同じ genome + source」は「同じ protocol、compile-time configuration、source/build identity」へ一般化する。
- `perf stat ... /bin/true` の availability probe、build 時間、純粋な parser 単体試験は除外する。ただし CCBench を実際に起動して時間を測る sandbox/profile probe は層 A に残す。
- CCBench を起動せず既存値を集計する report/plotter は producer と二重計上せず、層 B の adapter/consumer として扱う。

**対象 path の母集合**

1. Izanagi 所有の実行コード:

   - `orchestrator/**/*.py`
   - `tools/**/*.py`
   - `tools/**/*.sh`
   - `tools/**/*.pbs`
   - `hooks/**/*.py`
   - `hooks/**/*.sh`

   これで campaign、calibrator、qualification、plotting、Pegasus job、scheduler wrapper、test、manual probe を覆う。

2. CCBench 自身の入口:

   - `external/ccbench/CMakeLists.txt`
   - `external/ccbench/cmake/**`
   - `external/ccbench/cc/**`
   - `external/ccbench/common/**`
   - `external/ccbench/include/**`
   - `external/ccbench/microbench/**`

   native `main()`、protocol target、`cc/*/script/*.sh` を含める。例えば native CLI は [external/ccbench/cc/silo/ycsb_silo.cc:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/external/ccbench/cc/silo/ycsb_silo.cc:24)、性能値の共通出力は [external/ccbench/common/result.cc:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/external/ccbench/common/result.cc:55) にある。

3. 間接 argv/configuration:

   - `orchestrator/**/*.json`
   - `tools/**/*.json`

   `canonical_benchmark_argv`、target、binary path など、Python source だけでは実体が決まらない argv を追うために読む。

4. 残余:

   - `external/ccbench/third_party/**` は vendored project が独自 benchmark を多数持つ。原則として CCBench genome の producer ではないため主母集合から分ける。ただし CCBench 本体または Izanagi script から参照される file/script は参照辺を辿って復帰させる。
   - runtime に外部から渡される executable、環境変数、scheduler 生成 argv は静的には完全列挙できないので `unresolved-external-argv` として残す。
   - `patches/**` は producer 入口ではないが source identity の一部として各 build 経路へ束縛されているかを確認する。

**実行する検索**

まず process 起動面を、特定の関数名だけでなく generic helper と injected callable も含めて拾う。

```bash
rg -n --pcre2 \
  --glob '*.py' --glob '*.sh' --glob '*.pbs' \
  '(subprocess\.(?:run|Popen|call|check_call|check_output)|asyncio\.create_subprocess_(?:exec|shell)|os\.(?:system|popen|spawn\w*)|(?:capture_)?measure_point\s*\(|(?:capture_)?run_once\s*\()' \
  orchestrator tools hooks
```

binary、build mode、性能値の導出面を独立に拾う。

```bash
rg -n -i \
  --glob '*.py' --glob '*.sh' --glob '*.pbs' --glob '*.json' \
  '(ycsb_[[:alnum:]_./${}"-]*\.exe|CCBENCH_TRACE|trace[[:space:]]*=[[:space:]]*False|throughput\[tps\]|throughput_tps|median_tps|fitness_tps|latency\[ns\]|perf[[:space:]]+(stat|record))' \
  orchestrator tools hooks
```

native CLI と upstream shell を拾う。

```bash
rg -n --glob '*.cc' --glob '*.cpp' --glob '*.cxx' \
  '\b(?:int[[:space:]]+)?main[[:space:]]*\(' \
  external/ccbench/cc external/ccbench/microbench

rg -n --glob '*.sh' \
  '(ycsb_.*\.exe|grep.*throughput|grep.*latency|perf[[:space:]]+(stat|record))' \
  external/ccbench/cc
```

verifier/certification 面は別検索にし、producer 検索式へ混ぜない。混ぜると「verifier の語がある file は安全」という誤分類になる。

```bash
rg -n \
  '(verify_trace_dir_with_capability|verify_trace_dir|verifier|certified|verification_capability|commit_receipt|require_persisted_certified_commit)' \
  orchestrator tools
```

各 process site について、argv の定義、binary の build、metric parser、artifact writer、verifier の順序を同じ関数と呼出し元まで読む。中核 spawn は [orchestrator/calibrator/runner.py:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/calibrator/runner.py:584)、実 spawn は同 `:661-664`、throughput 導出は同 `:1003` と `:1216`。ただしこれだけを producer 母集合とはしない。

generic helper の argv dataflow を必ず追う。既存検査は [orchestrator/tests/test_ccbench_spawn_sites.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/tests/test_ccbench_spawn_sites.py:28) で `calibrator/` と `campaign/` のみに限定され、`silo_ladder_rung1._run` を non-CCBench と分類しているが、実際には [orchestrator/campaign/silo_ladder_rung1.py:4360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/silo_ladder_rung1.py:4360) で CCBench argv を作り、同 `:4365-4395` で実行、parse、記録する。この種の helper を文字列 allowlist で落とさない。

**入口形態の数え方**

同じ spawn を共有する入口を潰さないよう、`entry_id` と `spawn_id` を別に数える。最終一覧は入口件数と、共通 spawn へ畳んだ producer 実装件数の両方を出す。

1. Python CLI:

```bash
rg -n --glob '*.py' '__main__' orchestrator tools
```

`main()` から producer までの到達を確認する。`__main__` が parser/report 専用なら層 A から除外する。

2. import 可能な公開関数:

```bash
rg -n --glob '*.py' '^(__all__[[:space:]]*=|(?:async[[:space:]]+)?def[[:space:]]+[A-Za-z][A-Za-z0-9_]*[[:space:]]*\()' \
  orchestrator tools
```

`__all__`、package `__init__.py` の再 export、module-level public function、public class methodを調べる。先頭 `_` はアクセス制御ではないので、private helper しか barrier がない場合は「止まっている」としない。

3. `tools/` shell/PBS:

   `*.sh` と `*.pbs` を別件数にする。直接起動、Python module への委譲、qsub への委譲を区別する。直接 producer の実例は [tools/pegasus/t141_region_profile.sh:1346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/tools/pegasus/t141_region_profile.sh:1346) から同 `:1420`、perf record 経路は同 `:1446-1477`。

4. test harness:

```bash
rg -n --glob '*.py' \
  '(measure_point[[:space:]]*\(|run_once[[:space:]]*\(|subprocess\.(run|Popen)|ycsb_.*\.exe|buildcache\.build[[:space:]]*\()' \
  orchestrator/tests
```

   - 実 binary/build を使える integration harness
   - subprocess を monkeypatch した synthetic harness
   - source を読むだけの structural harness

   の3種に分ける。後二者は入口母集合には記録するが、条件 (a) を満たさないため producer 数へ入れない。

5. `orchestrator/manual_probes/`:

```bash
rg -n \
  '(subprocess\.(run|Popen)|measure_point|run_once|ycsb_.*\.exe|throughput|latency|perf)' \
  orchestrator/manual_probes
```

現存する [orchestrator/manual_probes/test_t2000_legacy_build_probe.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/manual_probes/test_t2000_legacy_build_probe.py:1) は build probe なので、実 CCBench run が無いことを確認した上で negative entry とする。

6. 追加形態:

   native C++ CLI、`external/ccbench/cc/*/script/*.sh`、scheduler wrapper、injected `measurement_run` を別分類する。例えば `run_ss2pl_lock_study.py` は [tools/pegasus/run_ss2pl_lock_study.py:2684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/tools/pegasus/run_ss2pl_lock_study.py:2684) で binary を起動し、同 `:2507-2565` で throughput を導出する。

## 走査プラン (層 B)

層 B は producer からの forward trace と、official sink からの reverse trace を独立に作り、両者を突き合わせる。

**official sink の母集合**

```bash
rg -n \
  --glob '*.py' --glob '*.sh' --glob '*.pbs' --glob '*.json' \
  '(official_status|official_conclusion|fitness_tps|STAGE_COMMIT|winner|rank|ranking|headline|selector|publish_result|reports_dir|selection_evaluation)' \
  orchestrator tools
```

さらに `docs/**/*.md`、`README.md`、`output/**/*.{md,json,jsonl,dat,plt}` で artifact/schema/path の引用先を検索し、記述的 artifact が paper claim や headline へ再利用されていないかを確認する。文字列 `headline` が workload label に現れるだけでは official headline と数えない。

**producer ごとの forward trace**

各 producer について次を file:line で確定する。

1. metric が初めて数値になる parser/集約点。
2. 返り値、WAL stage、JSON schema、stdout、off-repo artifact のどれへ出るか。
3. schema/key/path を読む全 consumer。
4. consumer が report、selector、順位、headline のいずれを生成するか。
5. consumer 直前に verifier 証拠を要求するか。その証拠が source/build/configuration と数値へ束縛されているか。

**既存の certified WAL 系で読む箇所**

- verifier 実行と anomaly 即 reject: [orchestrator/campaign/pipeline.py:1472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/pipeline.py:1472) と同 `:1505-1516`。
- 全 verify 後の certified 設定: 同 `:1593-1635`。
- COMMIT 前条件と receipt 発行: 同 `:1636-1676`、`:1714-1772`。
- WAL の live COMMIT receipt 検証: [orchestrator/campaign/wal.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/wal.py:692) から同 `:717`。
- persisted COMMIT の verifier evidence 再検証: [orchestrator/campaign/artifact_admission.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/artifact_admission.py:686) から同 `:771`。
- certified view の生成: 同 `:1297-1336`、exact 型境界は同 `:1361-1382`。
- certified report の例: [orchestrator/campaign/backoff_sweep_report.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/backoff_sweep_report.py:52) から同 `:82`、[orchestrator/campaign/backoff_extended_sweep_report.py:457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/backoff_extended_sweep_report.py:457) から同 `:503`。
- Layer 3 は historical report と certifying report を分ける。historical は [orchestrator/campaign/layer3_report.py:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/layer3_report.py:541)、certifying path は同 `:682-772`。

`CampaignReadPurpose.HISTORICAL_RAW` を使う report は自動的に official とも安全とも判定しない。[orchestrator/campaign/p2_2_report.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/p2_2_report.py:71) は raw `bench_done` を集め、同 `:112-193` で順位と winner を作る。表示される epoch 限定と、paper/headline での位置づけまで読んで判定する。

**「止まっている」とする十分条件**

次のいずれかを file:line で示せた場合だけ stopped とする。

- official sink が verifier 発行の capability/receipt を必須とし、receipt が raw verifier evidence、source/build identity、対象 variant、terminal payload に束縛され、別の raw writer が無い。
- persisted artifact consumer が receipt を再検証し、未認証 `bench_done` を順位や性能表から除外する。
- artifact が descriptive 専用であるだけでなく、official consumer 側にもその artifact を拒否する機構がある。
- nominal type を barrier とする場合、その constructor/issuer が caller から作れず、issuer closure が verifier 成功点に限定される。

次は stopped の根拠にしない。

- caller 0。
- leading underscore、`__all__` 非掲載。
- `certified: true` という caller 供給 boolean。
- caller 自身が作れる hash、非空 issuer 名、docstring の「official ではない」という説明だけ。
- 出力先が off-repo であること。
- calibration/report という file 名。

**最優先で確認する concrete seam**

[orchestrator/campaign/s8c_result_judge.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/s8c_result_judge.py:33) は `judge` と `publish_result_table` を公開する。一方で:

- correctness 判定は caller 供給の boolean/string を受理する同 `:452-459`。
- attestation は caller 供給 raw values の SHA-256 と非空 issuer だけを確認する同 `:505-529`。
- `throughputs` を raw 入力として受理する同 `:472-492`。
- `judge()` が順位を導出する同 `:1959-2028`。
- `publish_result_table()` が `official_status` と `selection_evaluation` を書く同 `:2413-2438`。
- table payload は `official_conclusion` を持つ同 `:2316-2329`。

したがって、既存 producer の throughput を caller が許容形式へ移し、自己申告 gate と自己計算 hash を添えるだけで official/selection table へ到達できないかを、純粋な in-memory witness で確認する。外部 issuer が trust root だという同 `:1-9` の説明だけでは stopped としない。外部 issuer の実装と権威が checkout 外なら `unresolved external trust` とし、P5 の closed 結論を禁止する。

対照として SS2PL plotter は [tools/plotting/plot_ss2pl_lock_study.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/tools/plotting/plot_ss2pl_lock_study.py:429) で「certified fitness、floor、oracle、selection evidence ではない」と明記する。ただし、この表示だけでなく、その artifact を読む official consumer が無いことまで逆向きに確認する。

## 恒真性の自己検査

- launch 起点の forward inventory と official sink 起点の reverse inventory を別々に作り、一致しない辺を `unresolved` として残す。片方の allowlist からもう片方を生成しない。
- known positive control として `runner.measure_point`、`between_run_floor`、`t141_region_profile.sh`、`silo_ladder_rung1`、`run_ss2pl_lock_study.py` を必ず検出する。
- negative control として `/bin/true` の perf availability probe、pure parser test、build-only manual probeを producer から除外できることを確認する。
- `trace=False` を消しても producer 検出数がゼロにならないことを確認する。これは binary path、process primitive、metric parser の三つを独立検索する理由でもある。
- verifier call を仮に除いた場合、COMMIT/report 判定が `unblocked` へ反転する手順になっているか確認する。「COMMIT という名前だから certified」と判定しない。
- `certified=True`、issuer 名、raw hash だけの synthetic inputを accepted とする consumer は negative mutation として扱う。固定 allowlist が同じ結果を返すだけの検査にしない。
- caller 0、private 名、現在の CLI 非配線を barrier として使っていないか、全 stopped row を再点検する。
- calibration/sanity を層 A から消して見かけ上欠陥ゼロにしていないか確認する。層 A には残し、層 B の semantic role で非欠陥化する。
- 最終件数は `A-confirmed`、`A-negative`、`unresolved-dynamic`、`B-blocked`、`B-unblocked`、`B-external-trust` に分ける。未解決を blocked に丸めない。
- この自己検査は一時的な検索と既存コード読解だけで行い、新しい test、gate、allowlist、台帳を repository に追加しない。

## 判定の限界

- 静的調査は binary を build できること、実際の `CCBENCH_TRACE` 値、実 argv、verifier verdict、性能値の正しさを証明しない。
- dynamic import、`eval`、shell expansion、scheduler が生成する argv、checkout 外の configurationや issuer は完全には解決できない。
- filesystem permission、symlink race、TOCTOU、実行中の artifact 差替え、process isolation は証明しない。
- test の monkeypatch が本番と同じ挙動であることや、test が実環境で通ることを証明しない。
- 現在 caller が無いことは将来または直接 import による呼出し不能を意味しない。
- console/stdout の数値を人間が手で report や文書へ転記する経路は、repo 内の静的 call graphでは閉じられない。
- `output/` の過去 artifact が生成時点で正しかったこと、現在の verifier と同じ意味で certified だったことは証明しない。規律 7 に従い、現行コードとの差だけで無効化もしない。
- vendored `external/ccbench/third_party/**` の独立 benchmark 全体、checkout 外の publication system、外部 issuer は別残余になる。
- 本段では build、benchmark、測定、pytest を実行していないため、「緑」「closed」「実測済み」とは報告しない。

## 親の provisional 裁定への指摘

- **P1 は入口集合が狭い。** Python CLI と公開関数だけでは、native `main()`、`external/ccbench/cc/*/script/*.sh`、`tools/*.sh`、PBS、generic process helper、injected callableを落とす。実例は `t141_region_profile.sh:1346-1477`、`silo_ladder_rung1.py:4360-4395`、`run_ss2pl_lock_study.py:2684-2716`。P1 は上記の補正版へ広げるべきである。

- **P2 は現時点の読解では否定されない。** screening は [orchestrator/campaign/pipeline.py:1553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/pipeline.py:1553) で bench-first、screen reject は同 `:1579-1591`、生存候補は全 verify 後に同 `:1634` へ到達する。consumer 側も [orchestrator/critic/digest.py:834](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/critic/digest.py:834) で screen rejection の性能値を射影しない。ただし全 report/selector を逆走して確定する。

- **P3 は維持できる。** `measure_point_floor()` が直接 import 可能という事実だけでは official 到達を示さない。ただし leading underscore や caller 0 を barrier にしてはならない。

- **P4 の結論候補は維持できるが、理由を修正すべきである。** 規律 1 が要求するのは性能 run が trace-disabled build であることで、別 run の verifier 証拠を不要とすることまでは導かない。D1373 の実装も [orchestrator/campaign/between_run_floor.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/between_run_floor.py:114) で verifier 成功を証明しないと明記する。また floor JSON は [orchestrator/campaign/screening_driver.py:305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2169-measurement-surface-closure/orchestrator/campaign/screening_driver.py:305) で読み込まれ、同 `:410-414` で比較閾値になる。安全性は「calibration だから」ではなく、その consumer が未認証 reject または記述用途に限定されることから立証する。

- **P5 の「D1360、D58、certified writer admission の三層で全経路が塞がる」という根拠は誤りである。** standalone producer はその三層を通らない。さらに `s8c_result_judge` の公開 seam は caller 供給の gate/hash から official/selection tableへ到達できる構造を持つ。したがって P5 は少なくとも現時点で採用不能であり、上記 in-memory witness と downstream consumer 確認で `B-unblocked` か `B-external-trust` のどちらかに確定させる必要がある。

## 総括

調査は「全 process/metric surface の forward scan」と「official/report/selector/rank/headline の reverse scan」を独立に行い、入口形態別件数と共通 spawn 別件数を併記する。calibration や sanity は層 A から除外せず、層 B の用途で非欠陥化する。

最重要確認点は、既存 spawn inventory が generic helper、`tools/`、shell/PBS、native CLI を覆わないことと、`s8c_result_judge` の caller-asserted correctness attestation が official/selection publication の実 barrier になっているかである。本段は静的な調査プランのみであり、閉包成立やテスト成功は主張しない。