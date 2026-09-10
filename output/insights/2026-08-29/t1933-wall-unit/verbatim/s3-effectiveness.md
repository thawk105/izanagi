[所見 1] 約55秒は共通残差だが、「テストが1本も動いていない単一の固定床」とは同定できていない。
[分類] identification-gap
[根拠] `tools/acceptance_shards.py:862-872` は `duration = getattr(report, "duration", 0.0)` を `_REPORT_DURATIONS[nodeid] += float(duration)` で加算するだけである。`orchestrator/tests/conftest.py:2083-2085` は `with _real_repo_locks(access):` の内側で `return (yield)` しており、yield 前の lock 待ちは TestReport duration に含まれない。従って `wall - max_occ` には collection のほか worker idle、lock 待ち、scheduler、session suffix が入る。
[放置した場合に成果物がどう変わるか] 合成差分を単一処理と誤認し、床を同定したという過大主張になる。
[この所見が誤りである場合の条件] 全 worker の phase timeline で約55秒が同一の global no-test prefix に閉じ、lock 待ち、idle、suffix が計測誤差内でゼロと示されること。

[所見 2] 55秒全体を「下げようのない費用」と閉じるのも誤りであり、repo 側に短縮可能な collection-time work が少なくとも1件ある。
[分類] effectiveness
[根拠] `parent-findings.md:131-136` は「`orchestrator/tests/test_p3_exploration_namespace.py:63` の setcomp (cumulative、180 呼) | 2.70 秒 | 14%」「最後の 1 項だけが repo 側のコードである。`_call_names` が `ast.walk` を回しており (`ast.walk` は 1,153,351 呼で cumulative 2.66 秒)、これが collection 時に 180 回走っている」と記録する。実コードも `orchestrator/tests/test_p3_exploration_namespace.py:124-140` で全 `campaign_root.glob("*.py")` を parse、walk、import し、module import 時に `_CAMPAIGN_DRIVERS = _discover_campaign_drivers()` を実行する。`parent-findings.md:138-140` は bytecode の重複 compile も記録する。
[放置した場合に成果物がどう変わるか] collection を不可避費用として閉じ、実在する短縮候補を捨てる。ただし、この候補単独で full wall の10%以上を動かす証拠はまだない。
[この所見が誤りである場合の条件] AST scan と重複 compile を除去しても受理集合を保つ実装が存在しないか、同一 tip の full 3走でその除去可能分が D357 の解像度未満と確定すること。

[所見 3] T-080 の約100秒は10本が共有する1回の処理ではなく、共通 helper を各 node が独立に実行する費用である。
[分類] identification-gap
[根拠] `orchestrator/tests/test_s8b_oracle_driver.py:895-903` は cache を「process 内で引数ごとに 1 回だけ組む」と限定し、「各テストへは独立した実体コピーを渡す」「コピーは共有しない実体でなければならない」と明記する。`同:909-927` は process-local `_T080_E2E_BASE_CACHE` を key ごとに参照した後も、毎回 `shutil.copytree(base_root, root, symlinks=True)` を実行する。`同:938-945` の inventory では重い5 functionが 1、4、1、3、1 node、合計10 nodeである。これらは loadgroup marker を持たず、`analyze5.txt:6-16` でも別々の `node:` unit として現れる。
[放置した場合に成果物がどう変わるか] 「共有処理を1回短くすれば10本が短くなる」という実在しない実行像を成果物へ残す。正しくは、copy/build/verify の共通コード変更を10個の独立 invocationすべてへ効かせる必要がある。
[この所見が誤りである場合の条件] controller-wide の単一処理が1回だけ約100秒動き、その時間が10個の testcase durationへ重複計上されていることが phase trace で示されること。

[所見 4] 「LPTでも縮まらないなら実 schedulerでも縮まらない」という親の推論は成立しない。
[分類] identification-gap
[根拠] `parent-findings.md:13-15` は「LPT は最適 makespan の 4/3 近似の一種であり、実 scheduler の makespan はこれ以上になる。したがって『LPT でも縮まない』は『実 scheduler でも縮まない』を含意する向きで使う」と記す。しかし LPT makespan は最適値以上の実行可能解であり、任意の xdist 実 schedule と LPT の大小関係は保証されない。`analyze7.txt:2-5` の hold 後4走は LPT 上の差が `+19.3 / +2.7 / +2.3 / +3.8` 秒という観測であって、実 scheduler の介入結果ではない。
[放置した場合に成果物がどう変わるか] n の問題以前に、反実仮想が証明していない「単一処理なし」を確定事項として残す。
[この所見が誤りである場合の条件] この xdist schedulerについて、同じ入力の実 makespanと介入差が常に LPT makespanと介入差以上になる定理、または実 traceによる同値性が提示されること。

[所見 5] 段2の baseline 3走は n を増やさないが、同一 tip と直接観測で強度を上げる最小案である。ただし wave の明示 scope と衝突する。
[分類] measurement-cost
[根拠] `verbatim/rulings.md:26-29` は「同一 tip・同一条件で 3 走以上を逐次に取り、中央値で述べる」と定める。`s2-plan.md:210-212` は「同一 instrumentation tip、同一条件で逐次3走する」としており、D357上は最小本数である。一方 `brief.md:9-13` は「484 本の full 走」の事後解析で行い、「同定のために新しい full 受入測定を積み増さない」と明記する。
[放置した場合に成果物がどう変わるか] 実行すれば scope違反、実行しなければ current fixed-tip の負同定は provisional のままになる。
[この所見が誤りである場合の条件] 親の4走が同一 tested tip、同一条件、逐次実行であり、必要な実 worker traceも既に保存されているか、ユーザーが新規3走を明示的に許可すること。

[所見 6] ungrouped node を実 critical workerへ帰属させる最小観測は nodeid→workerだけであり、全 phase timing は現目的の must-fix ではない。
[分類] overbuild
[根拠] `tools/acceptance_shards.py:800` には既に `_REPORT_WORKERS: dict[str, str] = {}` があり、`同:862-872` で nodeid と worker を収集し、`同:973-989` で `normalized_workers` と occupancy を構成している。最小の恒久形は `同:999-1022` の reportへ `node_to_worker` を1 field追加し、`同:61-66` の closed field集合を更新するだけである。対して `s2-plan.md:79-120` は setup/call/teardown、controller milestone、collection、prewarmまで提案する。
[放置した場合に成果物がどう変わるか] mappingなしで positive な critical-worker帰属を述べれば推定のままになるが、phase schema全体を実装しても current negative conclusion自体は変わらない。
[この所見が誤りである場合の条件] 成果物が単なる node/frontier帰属ではなく、55秒を特定 routineの開始終了へ帰属させる positive identificationまで必須と裁定されること。

[所見 7] hold有効という条件付き負結果は台帳要求を満たし得るが、fixed argvだけでは regimeを固定できず、現資料は fixed-tip証拠を満たしていない。
[分類] regime-dependence
[根拠] `orchestrator/tests/conftest.py:1668-1680` は環境変数で growth holdを opt-in解除でき、`同:2020-2030` は opt-inなしなら skip markerを付ける。`parent-findings.md:176-177` は「同定結論は『これらの hold が効いている状態』に対する主張である」と記す。`s2-plan.md:287` 自身も「mixed-tip corpus のため、historical candidate group と現 default hold 状態が混在している」と認める。
[放置した場合に成果物がどう変わるか] 「現行 argvでは単一処理なし」という無条件主張になり、hold解除時に `s8c-preregistration-candidate` が再び wallを決める事実を隠す。
[この所見が誤りである場合の条件] hold registryと解除環境が固定 argv receiptの証明対象に含まれ、同一 tipの3走でも regime交代が起きないこと。

[所見 8] `0.9 <= ΔW / ΔU <= 1.1` を同定条件にするのは未裁定の過剰 gateで、実効的な短縮候補を誤って捨てる。
[分類] effectiveness
[根拠] `s2-plan.md:17-20` は「full wall の中央値が概ね x 秒短くなる」を独自に定義し、`同:263-269` は ratioが0.9未満なら frontierとして単一同定を拒む。一方、逐語のD357 `verbatim/rulings.md:26-28` が定めるのは同一条件3走以上の中央値と「10%未満なら変化なし」だけであり、x-for-x比率は要求していない。
[放置した場合に成果物がどう変わるか] full wallを10%以上確実に短縮する routineでも、並列 handoffにより局所短縮より壁短縮が小さいだけで「同定していない」とされる。
[この所見が誤りである場合の条件] ユーザーが「wallを決める」を x-for-x の単独支配に限定し、10%以上の実効短縮だけでは同定に数えないと裁定すること。

[所見 9] report v2、session milestone、互換 reader、epoch gate、timeline閉包をこの waveで実装するのは過剰実装である。
[分類] overbuild
[根拠] `brief.md:30-31` は「解析は既存 artifact の事後読取だけ。計測系へ観測を差し込まない」「親の解析 script は repo 外」と定める。`s2-plan.md:96-134` は schema bump、process state、phase validation、最大18,900 phase record、session milestone、v1/v2 readerを提案し、`同:246` は timelineがJUnit wallと一致しなければ同定停止とする。`brief.md:12-13` は単一処理を指さない場合も「負結果として閉じ、短縮案を作らない」と明記する。
[放置した場合に成果物がどう変わるか] 同定成果ではなく恒久 telemetry frameworkがwaveの主成果になり、既存artifactだけで閉じるという段階導入を破る。
[この所見が誤りである場合の条件] mapping-onlyでは結論が変わらず、phase timingの各 fieldがそれぞれ成果物の positive identificationを1行で変えると示され、別途実装権限が与えられること。

[所見 10] 現 regimeで s8c candidateを短縮することと、T-080の一部だけを同一 workerへ寄せてcache共有することは実行しない方がよい。
[分類] effectiveness
[根拠] `parent-findings.md:164-177` は `s8c-preregistration-candidate` の現在値を「0.0 秒」とし、15 nodeがskipされていると記す。従って `s2-plan.md:140-170` が詳述する `git add -A` を現 defaultで短縮しても wallは動かない。T-080 groupingについては `verbatim/rulings.md:10-15` が「paired full K=3中央値が10%未満の差なら採用しない」「pre 244.810秒、post 245.707秒、差+0.37%」「焦点6 nodeではcache共有が成立したが、その費用はfull wallのcritical pathの下へ隠れた」と確定している。
[放置した場合に成果物がどう変わるか] 正しく配線された局所短縮へ実装とfull走を費やし、D1260と同じ no-effect結果を再演する。
[この所見が誤りである場合の条件] s8c holdが解除された同一 tipの3走で同 groupが10%以上のleadを持つか、T-080変更が一部のgroupingではなく現在の全 critical frontierへ共通に効き、事前解析で10%以上のwall差を下限保証できること。

## 総括

現時点では「同定できた」と言ってはならない。hold有効regimeの共通collection残差とT-080独立実行frontierまでは分かったが、LPTの誤った含意、mixed-tip、実worker帰属欠落によりfixed-tipの単一処理なしは未確定である。
scopeを守るなら「現artifactではここまでで、単一処理は未同定」という負結果で閉じるべきであり、追加権限がある場合だけ mapping-only観測と同一 tip 3走へ進むのが最小である。