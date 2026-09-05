## 1. 固定費 F の測り方

- **real — 親の 23–38 秒を run 固定費 `F` として 33 回掛けるのは過大評価。** この区間は純粋な `run_campaign()` 前置費ではなく、job/process 共通費 `J` と run 前置費の混合である。親自身もその限界を認めているが、数値計算では `J=0, F=33` として再び全額を 33 回掛けている。[parent-measurements.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/parent-measurements.md:27)、[同:98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/parent-measurements.md:98)、[同:110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/parent-measurements.md:110)

  1 job・1 process で 33 回連続呼出しするなら、少なくとも次は 1 回だけである。

  - shell/PBS envelope 検査、repo・Python・policy 解決：[b10_backoff_shape_campaign.sh:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/tools/pegasus/b10_backoff_shape_campaign.sh:19)
  - submit receipt 待ち・検証、HEAD/clean/script SHA 検査：[同:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/tools/pegasus/b10_backoff_shape_campaign.sh:141)
  - `qstat`、reservation 環境構築、scratch 作成：[同:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/tools/pegasus/b10_backoff_shape_campaign.sh:227)
  - gflags/glog の検査・configure/build/install：[同:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/tools/pegasus/b10_backoff_shape_campaign.sh:308)
  - Python process 起動と import：[loop.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:12)

- **real — 観測区間に入っていない per-run / per-row 終端費用がある。** `commit` の WAL 時刻は append 前に採られ、実際の write、file fsync、directory fsync はその後である。[wal.py:1410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/wal.py:1410)、[同:1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/wal.py:1165)。したがって `build_start.ts → commit.ts` は最後の commit WAL 耐久化を含まない。

  また `return` は `with ExitStack()` 内なので、復帰前に campaign lock の unlock/close と、該当時は A1 context reset が走る。[loop.py:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:396)、[同:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:652)、[lock.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/lock.py:84)、[wal.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/wal.py:163)。

- **real — job 終了側にも未算入費用がある。** driver 復帰後の `job-result.json` 作成、失敗記録、scratch 全削除がある。[b10_backoff_shape_campaign.sh:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/tools/pegasus/b10_backoff_shape_campaign.sh:303)、[同:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/tools/pegasus/b10_backoff_shape_campaign.sh:375)。これは基本的には job 共通費だが、scratch 内容量は実行した materialization 数に依存し得る。

- **refuted — 「23–38 秒から最大値か中央値を選べば F が決まる」。** 5 点は同一母集団ではない。3 種の source commit、3 種の job-script SHA、複数 workload・node を混ぜている。値自体は [parent-measurements.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/parent-measurements.md:15)、commit/script の差は各 submit receipt、例えば旧 [963545 receipt:1](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/f4aa966444a33e90af5131f79c4a67ca/submit-receipt.json:1) と現行 [974207 receipt:1](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/c42191d4f1e6ecdbd5b7eb7f3100df50/submit-receipt.json:1) で確認できる。

  中央値 28 秒は「この混合標本の中心」、38 秒は「観測最大」にすぎず、いずれも per-run F や worst-case 上限ではない。ばらつきは receipt 待ち、`qstat`、git status、依存 build、filesystem/node 状態などのどれにも帰属可能だが、区間内計時がないため原因は特定不能である。

## 2. 行の費用 R の測り方

- **refuted — 現行の `R=908 s` が「2 パスから 6 パスへの外挿」であるという指摘。** 提供された現版では、`84319b1127a6` の build、legacy 1 回、performance 5 回、commit がすべて WAL に存在する。[現行 WAL:1](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-balanced-formal-143a3f74/runs/wal.jsonl:1) から [同:9](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-balanced-formal-143a3f74/runs/wal.jsonl:9)。正確には `908.908 s` であり、親の 908 秒は切捨て近似である。

- **real — `R=235 s` と `R=121 s` は P6 への外挿。** これは 6 パスから 2 パスへ縮め、B-10 の performance 1 回を P6 の S2 1 回へ代用した scenario である。[parent-measurements.md:117](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/parent-measurements.md:117)。`235/908≈0.259` と幅が大きく、formal P6 の実測値ではない。

  同じ balanced campaign の次 variant は `build_start→commit≈374.728 s` で、最初の 908.908 秒と既に約 2.4 倍違う。[現行 WAL:10](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-balanced-formal-143a3f74/runs/wal.jsonl:10)、[同:18](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-balanced-formal-143a3f74/runs/wal.jsonl:18)。1 variant を 32 mask の共通 R にする根拠はない。

- **real — 一般論として「build があるから `R≥51 s`」は下限にならない。** cache hit 経路は実在し、compile を skip する。[buildcache.py:2564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/buildcache.py:2564)、[同:3161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/buildcache.py:3161)。また cache miss でも 51 秒は単一観測であり、時間の数学的下限ではない。

- **refuted（formal S8b 経路に限る）— 33 行で広く cache hit して 51 秒級の build が消える懸念。** campaign identity 自体は cache key に入らないので、「別 campaign identity」だけでは miss を証明しない。一方、key は genome、trace、`src_token`、admission receipt を含む。[buildcache.py:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/buildcache.py:624)。formal S8b は admission preimage に毎回異なる絶対 `source_root` を含めるため、実装自身が hit 不成立を明記している。[同:2312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/buildcache.py:2312)。現行 B-10 の最初の 2 行も trace/perf とも `cached:false` である。[現行 WAL:2](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-balanced-formal-143a3f74/runs/wal.jsonl:2)、[同:11](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-balanced-formal-143a3f74/runs/wal.jsonl:11)。

  ただし 33 行 producer はまだ存在しないため、将来の P6 がこの exact admission/materialization を通るという条件を外して断定してはならない。[phase3-8c-wiring-design.md:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8c-wiring-design.md:379)

- **real — B-10 の 3 workload の R を P6 の 32 mask 行へ直接使えない。** mask ごとの source、commit 数、正式 workload、`do_bench`、extime/reps が未確定である。[s2-plan.md:119](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/t2261-v8-cost/s2-plan.md:119)。現時点では、凍結済みの構成要素ごとの scenario 帯と、R を変数のまま残した感度式を返すべきである。単一 R を選ぶなら、formal protocol 凍結後に 32 mask 全行の分布を測る必要がある。

## 3. 現行コードであることの裏取り

- **real — submit receipt の `source_commit` 単独では実行 bytes を保証しない。** receipt は投入時の申告であり、immutable checkout や全 import bytes の manifest ではない。[974207 receipt:1](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/c42191d4f1e6ecdbd5b7eb7f3100df50/submit-receipt.json:1)

- **refuted — ただし今回、receipt 以外の裏付けが全くないわけではない。** 実行 script は driver 前に HEAD が receipt commit と一致し、worktree が clean であることを検査する。[b10_backoff_shape_campaign.sh:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/tools/pegasus/b10_backoff_shape_campaign.sh:208)。さらに実行 script・commit blob・receipt の SHA 三者一致を要求する。[同:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/tools/pegasus/b10_backoff_shape_campaign.sh:217)。receipt の script SHA は実際の `c7ed565…` blob と一致し、driver stdout と WAL が gate 通過後の実行を示す。[driver.stdout:1](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/c42191d4f1e6ecdbd5b7eb7f3100df50/job-attempts/974207.nqsv/driver.stdout:1)

  限界は、clean 検査後から import/実行中までの TOCTOU と、実行した Python module 群の個別 hash receipt がない点である。「現行 commit に gate された走行」は妥当だが、「実行 bytes が完全に証明済み」は過剰である。

- **real — 並列化コードが live commit に含まれ、既定経路から選ばれることは裏付けられる。** `d719c1e35`、fix `da45b6b2b`、`76b824f94` はすべて `c7ed565…` の祖先である。pipeline は `workers` を指定せず verifier を呼ぶため、既定値は affinity と file 数の最小、上限 16 になる。[pipeline.py:1472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1472)、[parse.py:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/verifier/parse.py:493)。worker 数が 2 以上なら `ProcessPoolExecutor` 経路へ入る。[parse.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/verifier/parse.py:627)

- **real — ただし live で並列枝が成功した直接証拠はない。** worker/bootstrap failure 時には全ファイルを黙って直列再読込する。[parse.py:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/verifier/parse.py:794)。WAL は worker count/PID を記録していない。旧・現行で同一 variant の 1672.789→908.908 秒、commit 数差 1–4% は強い状況証拠だが、node が `bnode003` と `bnode015`、commit も異なるため因果分離ではない。効いていないとする積極的証拠はないが、「実発火済み」は未証明である。

## 4. 倍率の式

**real — §11 の literal な (b) は duplicate skip するため、33R の式は比較対象が違う。** §11 自身が `sealed_queries≤32` としている。[phase3-8c-wiring-design.md:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8c-wiring-design.md:624)

完全形は少なくとも次である。

```text
Ca = Ja + Σ(i=1..33) [Pi + Ri + Ei] + Ha

Cb = Jb + Pb + Eb + D + Σ(i∈32 physical rows) Ri + Gb
```

- `J`: job/process 共通費
- `P/E`: run 前置・終端費
- `H`: 33 run をつなぐ controller/materialization 費
- `D`: duplicate が skip までに払う費用
- `G`: 1 run 内の行間費用

同質化して `J` が共通、完全な run 固定費を `F=P+E`、`G=31g`、`H=0` と仮定した場合だけ、

```text
M_current = [J + 33(F + R)] / [J + F + 32R + D + 31g]
```

となる。duplicate も物理実行できる反実仮想 `(b*)` は、

```text
M_* = [J + 33(F + R)] / [J + F + 33R + 32g]
```

である。

したがって、

- **refuted — `33(F+R)/(F+33R+32g)` が literal な §11 (b) との式。** これは `J=0` の反実仮想 `(b*)` にだけ対応する。
- **refuted — `33(F+R)/(F+32R)` が正確な現行 (b) の式。** `J`、`D`、`31g`、終端費を落とした上側近似にすぎない。
- **real — 親の構造式 [parent-measurements.md:102](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/parent-measurements.md:102) は前版より改善しているが、数値代入が不整合。** `33 s` は `J+前置費` の観測なのに、数値式では全額を反復 F に置いている。

例えば `R=908, g=3, T=J+F=33, D=0` とだけ分かる場合、終端費等を無視しても、

```text
(b*) : F=0,J=33 なら約0.997、F=33,J=0 なら約1.032
(b)  : F=0,J=33 なら約1.028、F=33,J=0 なら約1.064
```

である。親の 1.032 / 1.064 は観測から一意に得た値ではなく、「混合区間を全部反復費とした端点」である。

なお「33 倍」は 1 回の物理実行から 33 record を合成する再利用案との比較なら成立するが、それは §11 の (b) ではない。[parent-measurements.md:144](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/parent-measurements.md:144)

## 5. 一般化の検査

- **real — 「倍率の上限は約 1.6 倍」は観測範囲を超える。** なお提供された現版は既に 1.62 ではなく 2.05 と書いている。[parent-measurements.md:129](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/parent-measurements.md:129)。しかし 2.05 も正式な上限ではない。38 秒は標本最大であって F の上限ではなく、121 秒も P6 全 mask の R 下限ではないためである。「この仮定の scenario 値」と改称すべきである。測定だけから 1.6 や 2.05 という非自明な上限は出ない。

- **refuted — 「終端 seal が存在しない」こと自体。** generic `run_campaign()` に別個の campaign seal がない、という狭い主張は正しい。[loop.py:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:652)

- **real — そこから「終端費用がない」と一般化するのは誤り。** commit WAL の append/fsync、ExitStack の unlock/close、caller 復帰後、job-result、EXIT cleanup が残る。`loop.py:652` の return だけでは呼出し境界の時間を閉じられない。

- **real — 「実際の regime では 1.03–1.17 倍」は表現過剰。** (a)/(b) のいずれも走らせておらず、formal P6 の R も未測定である。これらは B-10 を使った model scenario である。親自身の保証限界 [parent-measurements.md:176](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/parent-measurements.md:176) と本文の断定が食い違う。

- **real — 裁定に効く未測定費用が残る。**

  - 33 run の controller・各 query materialization・run 間遷移費
  - 各 run 最終 commit の WAL 耐久化と lock 解放
  - formal 32 mask の R 分布、commit 数、cache/admission identity
  - `do_bench`、preflight、settle、高 CV 再測定の実費
  - silent verifier fallback の有無
  - claim 数増加に伴う走査費、WAL replay/repair の履歴依存費
  - job 終了時 cleanup の内容量依存費

  これらは producer 未実装という設計上の未確定と直結する。[phase3-8c-wiring-design.md:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8c-wiring-design.md:379)。D1561 に従い、ここから択一を選ぶことはできない。[decisions.md:48169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/decisions.md:48169)

## 総括

real と裁定した所見と数字のずれ方向:

- job/process 共通費を 33 回の F にした — **倍率を大きい側へ**ずらす。
- 最終 WAL fsync、context 解放、run 間 controller 費を落とした — 主に (a) の 33 回分が欠け、**倍率を小さい側へ**ずらし得る。
- `D` と行間費を分母から落とした簡略式 — **倍率を大きい側へ**ずらす。
- B-10 の 908/235/121 秒を P6 の共通 R とした — 908 は P6 より重い可能性が高く、その場合は**倍率を小さい側へ**ずらす。ただし正式 protocol 未確定なので向きの確定自体はできない。
- 51 秒を普遍的 build 下限とした — R を過大評価し、**倍率を小さい側へ**ずらす。formal S8b の cache miss 自体は支持されるが、所要 51 秒は下限ではない。
- 1.6/2.05 を「上限」とした — P6 外への一般化で、**倍率の上側を不当に切る**。
- receipt 単独で実行 bytes を保証した — 数字の向きではなく、**現行コードへの帰属確度を過大表示**する。
- verifier 並列化の速度差を因果確定した — 観測 R 自体は変わらないが、将来 R への一般化の確度を過大表示する。

refuted と裁定した心配:

- 現版の 908 秒が 2 パスから 6 パスへの外挿である、という指摘。908.908 秒は 6 verify パスを含む実測である。
- formal S8b の 33 行で cache が広く hit する、という懸念。現行 admission/materialization のままなら miss する。
- live job に並列化コードが含まれていない、という懸念。commit ancestry と job-side HEAD gate は包含を支持する。ただし並列枝の実発火までは未証明。
- generic `run_campaign()` に別個の終端 seal がある、という旧 brief の記述。seal はないが、終端費用はある。

親が裁定へ返す前に必ず直すべき 1 件:

- **23–38 秒を `F` から外し、`J_job/process + P_run + P_first-row` の未分離観測として式へ戻すこと。** そのうえで literal (b) の分母を `J+F+32R+D+31g` とし、終端・run 間費を明示する。これを直すまでは 1.03–1.17、1.6、2.05 のいずれも裁定用の倍率として提示できない。

静的・既存証拠の読取りだけを行い、pytest や新規実走はしていない。