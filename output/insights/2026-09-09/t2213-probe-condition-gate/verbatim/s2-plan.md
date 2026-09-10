## プラン

1. 配線位置と共通 helper

   - `tools/pegasus/probes/t2187_adaptive_const_probe.py:33` の campaign import に `condition_meaning_gate` を加える。
   - 同 file `:174-190` の stock 定数群の直後に、driver 固有の reviewed default 表、関門対象外の既存 build flag 集合、関門実行結果型を置く。
   - 同 file `:686-725` の `genome_for()` 直後に、次の helper 群を追加する。
     - `_condition_requests_for_genome()`
     - `_require_requests_match_build_arguments()`
     - `_condition_gate_base_configure_args()`
     - `_require_condition_gate_for_genome()`
   - `_require_condition_gate_for_genome()` は一時 `FETCHCONTENT_BASE_DIR` を作り、`buildcache.prepare_masstree_fetchcontent()`、`capture_define_inputs()`、両 arm、`require_condition_gate_family()`を順に実行する。`admission.admitted` が偽なら例外にし、呼び出し元へ復帰させない。
   - sink 1 は `_certify_main()` 内、現在の `tools/pegasus/probes/t2187_adaptive_const_probe.py:3375` の `buildcache.build()`直前に置く。具体的には `:3374` を `def _build_trace_binary(genome=genome):` とし、その関数本体の先頭、`return buildcache.build(...)` の直前で呼ぶ。default 引数化は、閉包検査に sink の `genome` が実行時入力であることを見せ、現在の誤った `proven-unreachable` 判定を解消するためにも必要である。
   - sink 2 は `main()` の cell loop 内、現在の `:3749` の直前に置く。`build_started = time.monotonic()` は関門呼び出しの後へ移し、表示上の build 所要時間へ関門時間を混ぜない。
   - 両方とも `source_root` は `work_root` を正規化した値にする。これは `isolated_checkout` が `work_root` を返す `:3335` / `:3718` と、A+B+C 適用中の `:3336` / `:3719` の内側なので、`_applied_patch_stack()` 適用後の木を読む。
   - `stock_root` は別 checkout を増やさず、`assert_pinned_clean()` 済みの元 submodule を使う。sink 1 は `:3324-3326`、sink 2 は `:3657-3659` の `submodule` を正規化して渡す。patched `work_root` と clean `submodule` は別 root なので、`capture_define_inputs()` の distinct-root 条件 `condition_meaning_gate.py:827-839` も満たす。
   - sink 1 の `use_class` は `certified-selection`、sink 2 は `raw-measurement` とする。

2. 実 build からの要求導出

   `genome_for()` の `flags` はすべて exact `int` である。`Cell` の整数 field は `:223-236`、float の step は `incr_milli` / `step_min_milli` / `step_max_milli` が `int` に正規化する `:238-252`、trace は `int(backoff_trace)` になる `:704-713`、seed と terminal 値も `int` のまま入る `:714-724`。`Genome.flags` 自体も `Dict[str, int]` 契約である `orchestrator/campaign/model.py:39-47`。一方、`WORKLOADS` の値は `str` だが `:192-210` の実行時引数であり、build genome ではない。

   `_condition_requests_for_genome()` は概ね次の形にする。

   ```python
   flags = dict(genome.flags)
   if any(type(value) is not int for value in flags.values()):
       raise TypeError(...)

   specs = condition_meaning_gate.DEFINE_SPECS
   ungated = set(flags).difference(specs)
   if ungated != _REVIEWED_NON_GATE_BUILD_FLAGS:
       raise RuntimeError(...)

   macros = sorted(set(flags) & set(specs))
   if not macros:
       raise RuntimeError(...)
   missing_defaults = set(macros).difference(_CONDITION_GATE_DEFAULTS)
   if missing_defaults:
       raise RuntimeError(...)

   requests = tuple(
       condition_meaning_gate.make_define_request(
           driver_id=driver_id,
           macro=macro,
           requested_value=flags[macro],
           default_value=_CONDITION_GATE_DEFAULTS[macro],
           stock_comparison=(
               flags[macro] == _CONDITION_GATE_DEFAULTS[macro]
               or str(flags[macro]) in specs[macro].inert_values
           ),
       )
       for macro in macros
   )
   ```

   作成後、`[(request.macro, request.requested_value)]` と、元の `flags` から得た sorted domain tuple を exact 比較する。重複、欠落、値の差を一つでも認めない。さらに `Genome.cmake_defines()` が作る実引数 `orchestrator/campaign/model.py:61-63` に、request の route/value が存在することも `screening_driver.py:126-156` と同型に照合する。

   reviewed default 表は、この driver に現れうる 13 macro のローカル表にする。

   | macro | `default_value` |
   |---|---:|
   | `BACKOFF_INCR_MILLI` | 100000 |
   | `BACKOFF_MAX_US` | 1000 |
   | `BACKOFF_UPDATE_US` | 10 |
   | `BACKOFF_COUNT_WINDOW` | 0 |
   | `BACKOFF_COUNT_CAP_US` | 0 |
   | `BACKOFF_STEP_ADAPT` | 0 |
   | `BACKOFF_STEP_MIN_MILLI` | 100000 |
   | `BACKOFF_STEP_MAX_MILLI` | 100000 |
   | `BACKOFF_DYN_CEILING` | 0 |
   | `BACKOFF_TRACE` | 0 |
   | `BACKOFF_TRACE_TERMINAL_US` | 0 |
   | `BACKOFF_STEP_POLICY` | 0 |
   | `BACKOFF_STEP_POLICY_SEED` | 11400714819323198485 |

   値は probe の stock 定数 `:174-184` および既存の全体表 `orchestrator/campaign/screening_driver.py:51-68` と一致させる。`backoff_sweep.py:81-85` の 3 macro 表は対象が足りない。`screening_driver._CONDITION_DEFAULTS` の直接再利用も、private API への依存に加え同 module が `pipeline` を eager import する `screening_driver.py:29-32` ため、probe の lazy-import 契約 `test_t2187_adaptive_const_probe.py:781-810` を壊す。したがって driver 固有 subset を持つ。

   `BACK_OFF`、`NO_WAIT_LOCKING_IN_VALIDATION`、`NO_WAIT_OF_TICTOC`、`WAL` は `DEFINE_SPECS` 外なので要求にはしない。ただし黙って落とさず、この4件だけを `_REVIEWED_NON_GATE_BUILD_FLAGS` として exact 一致させる。追加の非 registry flag、4件の欠落、domain request 0 件はいずれも build 前に拒否する。これにより、新しい flag を足したのに registry または明示的レビューを更新しない経路は通らない。

3. `MeaningWitnessDeclaration` と stock 比較

   `MeaningWitnessDeclaration` は `condition_meaning_gate.py:613-630` により `BACKOFF_FIXED` 専用である。`genome_for()` が作る集合 `t2187_adaptive_const_probe.py:697-724` に `BACKOFF_FIXED` は無いので、2 sink とも legacy の `MeaningWitnessDeclaration` は作らない。各 request には `declare_define_runtime_meaning(request)` を渡すが、現行13 macroはいずれも registry witness 対象外なので、meaning arm は `condition_meaning_gate.py:3300-3306` の `unestablished` 記録になる。

   stock 比較は `requested == reviewed default` または `str(requested) in spec.inert_values` とする。関連する `inert_values` は `condition_meaning_gate.py:79-137,151-154` の実物では次のとおりである。

   - 明示 inert: `INCR=100000`、`MAX=1000`、`COUNT_WINDOW=0`、`STEP_ADAPT=0`、`DYN_CEILING=0`、`TRACE=0`、`TRACE_TERMINAL_US=0`、`STEP_POLICY=0`、`UPDATE_US=10`。
   - `inert_values=()` だが default 等値で stock になる値: `COUNT_CAP_US=0`、`STEP_MIN_MILLI=100000`、`STEP_MAX_MILLI=100000`、`STEP_POLICY_SEED=11400714819323198485`。
   - sink 1 の tuned cell `:255` は `MAX=1000` だけが stock。dynamic cell `:256-269` は `MAX=1000` と `TRACE=0` が stock。cohort 2 の policy 1/2 `:270-300` はそれらに既定 seed が加わる。
   - sink 2 の5-field cellは、各値が上記 default と一致するときだけ stock。extended performance では `TRACE=0` が stock、diagnostic では `TRACE=1` が non-stock。policy 0 は stock、1/2 は non-stock。policy 2 の custom seed は既定値と一致するときだけ stock。terminal macro は現行コードでは非零時だけ追加されるため、実際に要求される terminal 値は non-stock である。

4. sink 2 の観測者効果分離

   - 関門は現在の `:3729-3747` で `evidence` と build admission を確定した後、`:3749` の前で実行する。関門へ渡すのは `genome` から作った request であり、関門の返却値は `buildcache.build()` の引数へ渡さない。
   - 現在の build 呼び出し `:3749-3760` は、`genome`、`trace=False`、`cc`、`cxx`、既存 admission/evidence/cache root/work root をそのまま保つ。特に `trace=False` は `:3752` のままにする。
   - `buildcache.build()` は `buildcache.py:3188-3195` で、本 build の define を元の `genome.cmake_defines()` と `CCBENCH_TRACE=0` だけから作る。関門 request、stock comparison、gate admission はこの argv に入らない。
   - 関門側の CMake build root、decoder、FetchContent base はすべて一意な temporary directory に置き、性能 build の `cache_root` へ書かない。`build_started` も関門後に取る。
   - 変化経路になりうるのは、関門が誤って `genome.flags` または `work_root` を変更する場合である。前者は関門前に得た `source_evidence.genome_sha256` と build request の照合 `buildcache.py:645-656,3173-3175` で拒否される。後者は build 出口の evidence 再計算 `buildcache.py:3284-3289,3352-3377` で拒否され、fresh candidate は publish/measurement されない。したがって受理された性能 build の argv、define、binary には関門由来の変更経路を残さない。
   - なお sink 2 は `buildcache.trace=False` ではあるが、`--backoff-trace` diagnostic 時は `genome.flags["BACKOFF_TRACE"]=1` になりうる。これも実 build 値として関門要求へ含める。

5. 繰延べ台帳

   `orchestrator/tests/test_ccbench_spawn_sites.py` では次を連動させる。

   - `:911-935`: `_DEFERRED_GATE_MEMBERS` の probe 2 entry を削除する。
   - `:2671-2679`: exact ledger set から同じ2 tupleを削除する。
   - `:2682-2701`: probe の理由文を逐語比較する2 tupleを削除し、代わりに probe path の deferred entry が0件であることを明示する。
   - `:2706-2720`: live sink 対応と `len(matched_sinks) == len(_DEFERRED_GATE_MEMBERS)` は一般式なのでコード変更不要だが、残る5 entryを数えることを静的に確認する。
   - `:2566-2584`: counter の分類本体は変更しない。関門配線後、probe の両 sink が `deferred` ではなく `covered` へ入ることを確認する。
   - `:2895-2919` の production 分類 exact test に probe の2 sinkを加え、各々 `Counter({"covered": 14, "proven-unreachable": 24})` を固定する。14件には、実 genome の最大13 domain macroに加え、positive-control metadata にだけ現れる `IZANAGI_BREAK_NOREAD_VALIDATION` が含まれる。実要求が13件以下であることは別の runtime request-set testで固定する。
   - probe 側の挿入で sink 行番号はずれるが、旧 lineno entry自体を削除するので新番号への更新はしない。

6. 負例

   8型への対応を次の挙動テストで固定する。

   - `test_ccbench_spawn_sites.py:2813-2837` 付近に、production probe sourceの2関門呼び出しをメモリ上で一つずつ除去する mutation testを追加する。各変異で対応 sink が `failure-reachable` になり、もう一方は covered のままであることを要求する。これは「関門変数が無い」ではなく、閉包が ungated build sinkを拒否する挙動を見る。sink 1 の `genome=genome` default 化により、この変異が現在の `proven-unreachable` 穴を通らなくなる。
   - `orchestrator/tests/test_t2187_adaptive_const_probe.py:1352-1582` 付近に、5-field、extended、policy 2 custom seed、diagnostic、terminal の実 `genome_for()` 出力を通す testを追加する。要求の `(macro, requested_value)` 集合が `flags ∩ DEFINE_SPECS` と exact 一致し、値がすべて exact `int` であることを検査する。
   - 同 testで `make_define_request()` を monkeypatch して1値を変える、または1 requestを落とす変異を作り、helper の postcondition が例外にすることを要求する。これが「実 build値集合と関門要求集合の不一致」の負例になる。
   - `DEFINE_SPECS` 外の未知 flagを足した `Genome` と、domain値を `"1"` にした `Genome` も拒否させる。empty candidate即 returnと黙示 dropを同時に殺す。
   - `test_t2187_adaptive_const_probe.py:180-237` の compute-heavy test fixtureでは、新しい関門 helperも test-only stubにする。production skipは作らず、既存の main-path testsが実 CMakeへ逸脱することだけを防ぐ。
   - 別の負例で gate helperを red/例外にし、同期化した build deadlineまたは build spyが一度も呼ばれないことを sink 1/2それぞれで確認する。例外を握り潰す、環境変数、`ContextVar`、条件付き skipは導入しない。

   F794の8型との対応は、empty request拒否が「恒真な守り」、sink mutationが「関門がbuild後ろ」と「sink欠落」、exact value/route比較が「偽正例」と「実 build値集合を見ない」、red時 build spy 0回が「迂回口」、台帳0件が「wildcard」、production evaluator発行 recordだけを familyへ渡すことが「偽 record」を担当する。

7. 波及と検証対象

   production記号名と probe pathで `orchestrator/tests/` を検索した結果、直接影響するのは次である。

   - `orchestrator/tests/test_t2187_adaptive_const_probe.py:30-36` は module全体を実 importする。`genome_for()` の直接 consumerは `:963-970,1352-1370,1464-1519,1562,1815-1819,2724`。値生成自体は変えず、要求導出テストを追加する。
   - 同 file `:411-730,943-1036,1272-1310` などは `_certify_main()` / `main()` の成功 build経路を通るため、`:180-237` の test fixtureへ関門 stubが必要になる。既存受理期待値は緩めない。
   - `test_ccbench_spawn_sites.py:912-934,2671-2701` だけが sink linenoを pinしている。repo内検索では `3375` / `3749` を probe sinkとして pinする別 testは無い。
   - `test_dynamic_backoff_transitions.py:1817-1839` は trace parserだけ、`test_plot_dynamic_backoff.py:17` と `test_backoff_counterfactual_cohort2_analysis.py:17` は schema/constantsだけを利用するため、helper追加の直接影響はない。
   - `test_hooks.py:3064-3065,3294-3304` と `tools/pegasus/admission_registry.json:196` は path単位の compute-side分類であり、行番号や driver SHAを pinしていない。
   - `test_condition_meaning_gate.py` は関門 API の consumerだが、API本体を変更しないため既存契約への変更はない。
   - この段では pytestは実走していない。read-only制約下で、全文読解、`rg`参照確認、AST sink列挙、および対象file単独の静的分類だけを行った。

## 段 1 brief への指摘

- `docs/failures.md` に F1402 は存在しない。8型の正本は `docs/failures.md:21319-21348` の **F794** であり、D1402は `docs/decisions.md:44497` の別項目である。
- sink 1 の deferred entryは、現行閉包では実際には使われていない。対象file単独の静的分類では `<module>._certify_main._build_trace_binary` が `Counter({"proven-unreachable": 38})` になった。zero-argument nested functionの閉包変数 `genome` を入力として追えていないためである。ledger削除と緑だけでは発火を証明しないので、`genome=genome` default化と関門除去 mutationが必要である。
- sink 2 は「trace無効の性能 build」だけではない。`buildcache.build(trace=False)` は共通だが、diagnostic modeでは `t2187_adaptive_const_probe.py:704-713` により `BACKOFF_TRACE=1` の instrumented binaryを同じ sinkで作る。
- 不変条件3の「`DEFINE_SPECS` に在るものをfilterすれば、新 macroも素通りしない」は過大である。`DEFINE_SPECS` 外の新 flagは単純な積集合では黙って落ちる。非 registry 4 flagの exact集合検査が別途必要である。
- 「2 fileの変更」だけでは既存の full driver testsが実関門へ入り、実 CMakeを走らせる。`test_t2187_adaptive_const_probe.py:180-237` の compute-heavy seam更新は必要な波及であり、briefの成果物一覧から漏れている。
- アンカー表が示す `test_ccbench_spawn_sites.py:2580` は一般的な `deferred` counter加算であり、probe固有の期待 counterではない。現行fileに probe分類の literal counter assertは無く、件数 assert `:2720` も動的な長さ比較である。

## scope 外の所見

`condition_meaning_gate.py` は registryが38 macroであると `:12,243-244` に記す一方、`make_define_request()` と検証エラーは `:857,862,932` で「22-macro domain」と表示している。今回の配線には影響しないため変更対象に含めない。

## 総括

- patched `work_root` 内で、sink 1の `:3375` と sink 2の `:3749` より前に同じ完全な関門 familyを配線する。
- 要求は各 buildへ渡す `Genome.flags` の exact `int` 値から導出し、未知の非 registry flagと要求集合の差を拒否する。
- inert/default要求には clean元 submoduleを stock rootとして渡し、現行 macroには custom `MeaningWitnessDeclaration` を作らない。
- probeの deferred 2 entryと全逐語期待を外し、両 sinkの covered counterを固定する。
- 関門除去と要求値不一致の mutationで発火を固定し、red時に build spyが0回であることを確認する。
- この段では実装、file書換え、commit、pytest実走は行っていない。