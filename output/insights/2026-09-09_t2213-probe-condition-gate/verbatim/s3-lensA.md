## blocker

1. **runtime meaning arm は実質無効で、`certified-selection` でも `unestablished` を受理する。規律 2 違反。**

   - `condition_meaning_gate.py:954-974`: `declare_define_runtime_meaning()` は registry に無い macro へ `None` を返す。registry は `:245-282` であり、対象13 macroは全件対象外。
   - `condition_meaning_gate.py:613-630`: `MeaningWitnessDeclaration` は `BACKOFF_FIXED` 以外を拒否する。
   - `condition_meaning_gate.py:3300-3306`: `None` は `unestablished/meaning-witness-undeclared` になる。
   - `condition_meaning_gate.py:4063-4068`: meaning は `green` **または `unestablished`** なら成功。`use_class` は `:4034-4037` で語彙を検査するだけで、`certified-selection` を厳しくしない。
   - `s2-plan.md:83` は全件 `unestablished` になると認識しているのに、`:12` は `admission.admitted` だけを検査する。したがって runtime meaning は13件とも保証ゼロのまま通る。
   - 通る正例: supply が green の `BACKOFF_INCR_MILLI=1000` について meaning が `unestablished` でも family admission は `admitted=True` になる。
   - 成果物影響: supply 側だけ通った binary が certified 選択、性能レポート、台帳へ入り、条件の実行時意味が証明済みであるかのように参照される。

   保証を成立させるには、少なくとも次の runtime witness が必要である。

   | macro | 必要な witness |
   |---|---|
   | `BACKOFF_INCR_MILLI`, `BACKOFF_MAX_US`, `BACKOFF_UPDATE_US` | 決定的な時計・commit列で、刻み、上限、更新時刻が宣言値どおり変わる state-transition witness |
   | `BACKOFF_COUNT_WINDOW`, `BACKOFF_COUNT_CAP_US` | count到達とcap到達の境界で `check_update_backoff_at()` の返値が宣言どおり変わる witness |
   | `BACKOFF_STEP_ADAPT`, `BACKOFF_STEP_MIN_MILLI`, `BACKOFF_STEP_MAX_MILLI` | gradient列に対する adaptive step の倍増、半減、上下限を観測する witness |
   | `BACKOFF_DYN_CEILING` | ceiling の増減とclamp結果を観測する witness |
   | `BACKOFF_TRACE` | 0でtrace観測が無く、1で規定schemaの観測が出る compile-and-run witness |
   | `BACKOFF_TRACE_TERMINAL_US` | `TRACE=1` と必要なcount条件を伴い、閾値直前では出ず閾値後にterminal flushが出る witness |
   | `BACKOFF_STEP_POLICY` | policy 0、1、2ごとのdelta変換を観測する multi-case witness |
   | `BACKOFF_STEP_POLICY_SEED` | `STEP_POLICY=2` を伴い、seedごとの決定的assignment列を観測する witness |

   default/inert 値には「変化」ではなく、stock と同じ観測になる equivalence witness が必要である。現行クラスはこれらを宣言できず、compile-time branch witness 自体も `condition_meaning_gate.py:12-21` が runtime reachabilityやbranch body semanticsを保証しないと明記している。したがってこれは現行 scope 内の単なる配線では実現不能で、core API、registry、専用harness、負例の追加が必要である。そこまで行わないなら両 deferred entryを残す必要がある。

2. **要求集合は実 build の有効値集合ではない。規律 2とF794の「正例が実 build値集合を見ない」型に該当する。**

   - `s2-plan.md:35-57,118-120` は `genome.flags ∩ DEFINE_SPECS` と同じ集合であることだけを検査する。
   - しかしA+B+CのCMakeは、`cicada-adaptive-params.patch:11-13`、`cicada-adaptive-dynamic.patch:9-15`、`cicada-adaptive-counterfactual.patch:9-15` により13 macro全部へdefaultを与え、universal definitionsへ出す。`buildcache.py:3188-3192` のCMake configure後、owner TUが見る有効集合は明示flagsだけではない。
   - 通常の5-field cellは `t2187_adaptive_const_probe.py:697-713` から明示要求が3件だけだが、実compileでは残り10件もdefault値で定義される。extendedは10件、policy cellは12件、terminal diagnosticだけが13件になる。
   - 空flagsと、reviewed非registry4件を欠く部分flagsは `s2-plan.md:31-37` で拒否されるため「完全な空集合で緑」は閉じている。ところが reviewed4件とregistry macro 1件だけの部分flagsは受理でき、残り12件はCMake defaultとして未検査になる。型違いは `:27-28` で拒否される。
   - さらに `_condition_gate_base_configure_args()` が参照実装 `screening_driver.py:159-168` と同様に他のdomain macroを除けば、各macroは実 genome の組合せではなく単独で評価される。例えば実 build の custom seed は `STEP_POLICY=2` と組になるが、seedのprobe側はpolicy default 0となる。
   - 通る正例: 5-field cellは計画された request-set testでは「3件がflagsとexact一致」として通るが、実compileの10個の暗黙defaultは対象外のままになる。
   - 成果物影響: hidden defaultやmacro間相互作用が変わっても測定値が誤った条件へ帰属し、選択順位、レポートのarm名、再現台帳の参照がずれる。

   要求集合は `Genome.flags` ではなく、**実 whole-genome configureから得たowner TU compile commandの有効13値**から再導出しなければならない。また各macroのcontrolは、他の12値を実 buildと同じに保って一値だけを変える必要がある。

3. **性能artifactの時間と実行ホスト状態へ観測者効果が混入する。規律 1違反。**

   - main binaryのargv自体は `buildcache.py:3188-3195` のままで、gate resultもcache keyへ入らない。cache keyは `buildcache.py:624-642` の genome、pin、trace、source token、compiler、既存build admissionだけである。gate build rootとmainの `${TMPDIR}/build-variants` は共有しない。この部分に直接のbinary汚染経路は見つからない。
   - 一方、計画は毎cellで `prepare_masstree_fetchcontent()` を先行させる。これは単なる準備ではなく `buildcache.py:2052-2079` で `masstree_build` を実行する。その後、各requestがowner TUをrequested/controlの2回configure・preprocessする。
   - `condition_meaning_gate.py:1566-1575` と `buildcache.py:3518-3531` はenv指定無しならambient環境を継承する。compiler wrapper cache、OS page cache、CPU温度、周波数状態への副作用を隔離していない。
   - `t2187_adaptive_const_probe.py:3653-3655,3872-3880` の全体wall/CPU timerはgateより前に始まる。`s2-plan.md:14,97` が動かすのはcellの `build_started` だけなので、artifactの `wall_seconds`、`cpu_seconds`、`cpu_over_elapsed`、`job_total_seconds` にはgate時間が入る。
   - certify側も `t2187_adaptive_const_probe.py:3333-3334,3388-3397` のbuild deadlineとbuild phaseへgate時間が入り、正しいbuild単体なら予算内の正例をtimeoutへ変えうる。
   - 通る正例: gateがgreenの通常performance runはthroughput測定へ到達するが、同じbinaryでもartifactの総wall/CPU値はgate追加分だけ変わる。
   - 成果物影響: レポートの時間値は必ず変わり、host状態の影響がthroughputへ出ればcell順位とcertified選択も変わりうる。

   gate preflight、performance build、測定のtimerを分離し、測定前のsettle契約まで固定する必要がある。単に `build_started` を後ろへ動かすだけでは足りない。

4. **構造化recordは生成されても成果物へ残らない。規律 3違反。**

   - API側は `condition_meaning_gate.py:656-674` でarm、status、reason、evidenceを持ち、admissionも `:680-692` でrecord IDsと `unestablished_meaning_macros` を返す。
   - しかし `s2-plan.md:13-14` の両sinkはhelperを呼ぶだけで、返却値をpayloadへ保存する記述が無い。
   - sink 1ではhelperがdeadline worker内に置かれ、workerは `t2187_adaptive_const_probe.py:1537-1545` でbuilderの返値だけを親へ送る。現行builderの返値は `:3374-3389` の `BuildResult` なのでgate recordは親payloadへ届かない。
   - cache keyにもgate admissionは含まれないため、既存artifact欄から後でrecordを復元できない。
   - 通る正例: supply/meaning/familyがすべて評価されbuildが成功しても、performance rowとcertification receiptにはrecord ID、reason、unestablished集合のどれも無い。
   - 成果物影響: 後段は「何が壊れたか」も「どのgate recordがこのbinaryを認めたか」も裁定できず、レポートと台帳のproof-chain参照が欠落する。

## must-fix

1. **default/inert要求はclean upstreamとのbyte identity比較になり、正規cellが全件赤になる。**

   - `condition_meaning_gate.py:977-985,1827-1839,2516-2533` は requested値がdefaultまたはinertなら、controlをclean `stock_root`、control値を`None`にする。
   - 一致しないpreprocessed bytesは `:2628-2669` で `stock-inert-mismatch` になる。
   - A patchだけでも `cicada-adaptive-params.patch:53-65` はstockのliteralをcast式へ変え、active `static_assert` を追加する。default値でもpreprocessed bytesはupstream stockと同一ではない。B/Cの追加コードも同様である。
   - 全cert cellは `t2187_adaptive_const_probe.py:255-300` で `BACKOFF_MAX_US=1000` を含む。performance gridは `:559-568` がstock controlを必須にし、diagnostic固定cellもceiling 1000である。したがって両sinkとも少なくとも1件のstock比較で赤になり、main buildへ達しない。
   - 通るべき正例: `CERT_TUNED_CELL`。計画自身 `s2-plan.md:89` がMAXだけstockと認識しているが、その1件でrejectされる。
   - 成果物影響: 受理集合が空になり、certified成果物、性能レポート、台帳更新が一件も生成されない。

   default要求を落とすのは受理緩和なので不可。actual patched-defaultとの同値性とupstream stock意味の同値性を分けて証明できる比較方式が必要である。

2. **提案された負例は、関門を一度も実行しない偽実装を通せる。**

   - `_complete_gate_function_names()` は `test_ccbench_spawn_sites.py:970-991,1071-1088` で、到達可能性を見ずbody内に3つのcall名があればcomplete helperと数える。
   - caller側は `:1690-1704` でcomplete helper名のcallがあればcoveredになる。
   - `s2-plan.md:117` のcall削除mutationはcaller配線だけを見ており、`:121` は成功経路でhelper自体をstub化し、`:122` のred testもhelperをmonkeypatchして例外化する。production helperの実挙動を通さない。
   - 次の偽実装で、closure分類、call削除mutation、red build-spy、request-set単体testをすべて満たせる。

   ```python
   def _require_condition_gate_for_genome(*args, **kwargs):
       return None
       condition_meaning_gate.evaluate_define_supply_effectuation(...)
       condition_meaning_gate.evaluate_define_runtime_meaning(...)
       condition_meaning_gate.require_condition_gate_family(...)
   ```

   - `genome=genome` も保証を作らない。`genome` は `t2187_adaptive_const_probe.py:3330` で一度束縛され、workerは `:1541` で常に`builder()`と零引数呼出しするため、closureからdefaultへ移しても現行挙動は同じである。変わるのはstatic検査からの見え方だけである。
   - 通る正例: 上のno-op helperをproductionへ置き、sink前のhelper callは残す実装。
   - 成果物影響: 実gate 0回でもclosure台帳はcoveredとなり、未検証binaryの測定値とcertification receiptが受理される。

   production helperへearly returnを入れる変異と、family callの返値を無視する変異を追加し、実helperをstub化せずkillする必要がある。これはF918の再発条件そのものである。

3. **F794の8型判定。**

   | 型 | 判定 |
   |---|---|
   | 恒真な守り | **該当**。明示macro空は `s2-plan.md:31-37` で拒否するが、meaningは全件`unestablished`でも `condition_meaning_gate.py:4063-4068` で恒真に近い受理になる。 |
   | 関門が最初のbuildより後ろ | benchmarkの2 sinkについては**非該当**。配置は `s2-plan.md:13-14` で `buildcache.build` 前。ただしfamily判断前に `masstree_build` が1回走る。 |
   | 偽正例 | **該当しうる**。明示route/valueは `s2-plan.md:57` で一致するが、hidden defaultと他macroの実組合せをprobeしない。 |
   | 迂回口 | 明示flag、env、`ContextVar` は**0件**。ただし `unestablished` の意味上の迂回と、no-op helperを許すテスト迂回が残る。 |
   | wildcardの逃がし道 | **非該当**。ledger照合は `test_ccbench_spawn_sites.py:939-946` のpath、kind、scope、line完全一致で、計画は両entryを削除する。 |
   | 偽recordの受理 | **非該当**。`condition_meaning_gate.py:3979-4024` がschema、digest、production issuer capabilityを検査する。`unestablished` は偽recordではなく、正規発行された弱いrecordである。 |
   | 正例が実build値集合を見ない | **該当**。5-fieldの明示3件対、CMake有効13件。`s2-plan.md:118` のtestもこの不完全な積集合を正解として固定する。 |
   | 閉包からのbuild sink欠落 | 現行fileには `buildcache.build` が `:3375` と`:3749`の**2件だけ**なので列挙上は非該当。ただしclosure greenが実発火を証明しない点はmust-fix 2のとおり。 |

   迂回棚卸しとして、candidate build sinkは2件中2件ともhelper後、certifyの例外handlerは2本中build継続0、context managerの例外抑止0、mode分岐による未配線0、無効化引数0、無効化default 0である。残る実質迂回はcellあたり3、10、12、13件の`unestablished` meaningである。

## nit

- `isolated_checkout()` は `t2187_adaptive_const_probe.py:658-684` で固定の `${TMPDIR}/ccbench-src` を作るが、finallyはclean確認だけで削除しない。木は測定中も生存し、同じTMPDIRでの再実行は`:665-666`で失敗する。gateの一時build rootは終了時に消えるため、main cache rootとの直接共有は無い。
- `condition_meaning_gate.py:857,862,932` の「22-macro」表記は実registry 38件と不一致だが、本配線の受理判定には影響しない。
- read-only制約に従い、pytestやlive CMakeは実走していない。上記は静的読解による判定であり、緑の主張はしていない。

## 親 brief への指摘

- `brief-t2213.md:54,61` のF1402は誤りで、正本はF794。これは段2と依頼文の訂正どおりである。
- `brief-t2213.md:14-17` の「参照実装はruntime meaningも保証する」という含意は過大である。`backoff_sweep.py:133-155` も `BACKOFF_FIXED=-1` 以外は宣言`None`で、`condition_meaning_gate.py:4063-4068` により`unestablished`を受理する。
- 不変条件3 `brief-t2213.md:58-61` は、明示flagsとCMakeがowner TUへ供給する有効define集合を同一視している。5-fieldだけで10個の暗黙defaultが漏れる。
- P2 `brief-t2213.md:79-80` はT-2417のリスクを消さない。policyとseedをflagsから拾えても、meaningは未確立で、個別probeが実policy/seed組合せを保持する保証も無い。
- P3 `brief-t2213.md:81-86` の両entry削除は時期尚早である。entry 1も2も、runtime witness、実有効13値、record永続化、no-op mutationが揃うまで解除条件を満たさない。
- 完了条件 `brief-t2213.md:19-22` の「ledger削除、closure緑、call削除mutation赤」は、上記no-op helperでも成立するため発火証拠にならない。

## 総括

現プランはNO-GOである。`unestablished` はrawだけでなくcertifiedでも受理され、runtime meaningは何も保証しない。  
さらに5-fieldの実compileは13 macroを受けるのに要求は3件だけであり、親briefの不変条件3も成立しない。  
逆方向には、defaultをclean upstreamとbyte比較するため、現行正規cellはすべてsupply赤になる。  
性能artifactの総時間にはgate処理が混入し、構造化recordは成果物へ残らない。  
既存scopeの配線だけでは解消できないため、core witnessとwhole-genome評価までscopeを広げ、両deferred entryはそれまで維持すべきである。