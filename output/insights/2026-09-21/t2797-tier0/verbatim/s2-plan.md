実装案は **P1・P2を採用し、P4・P5の失敗分類とP6の配置根拠を修正する**形です。build は子の既存 condition gate 直後に置き、smoke は既存 `run_once` を使います。編集・commit・テスト実行はしていません。以下の行番号は現 checkout に対するものです。

参照表記を短くするため、`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/`、`V/` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/verbatim/` を表します。

## 1. U2：挿入位置・build・権限

**挿入位置は `C/p3_s4_loop.py:2279` の B-5 分岐から、同ファイル:2281 の submission 書込みまでの間。** `do_build=False` は既に:2232で戻り、検疫は:2235、condition gate は:2245で実施済みです。stock の別経路 `:2019` には追加しません。

なお、`pipeline._build_one` は公開・モジュール関数ではありません。正確には **`C/pipeline.py:1555` の `_prepare_evaluation_core` 内、:1985の閉包**です。直接 import して呼ぶ設計は採りません。

### 関数構成

`C/p3_s4_loop.py:1991` 付近に次を追加する案です。

```python
def _b5_tier0_build_inputs(
    cfg, genome, sub, *,
    build_context, capability_resolver,
    backoff_grammar_version,
):
    # 実 source evidence と admission、compiler を返す。
    ...

def _run_b5_tier0_smoke(
    binary, *, contract, timeout_s,
):
    # gateway 実行と出力検収。fitness は返さない。
    ...
```

build 2回は helper に隠さず、`_run_one_iteration_resolved` の condition gate 後に置きます。

```python
tr = buildcache.build_v2(
    genome, trace=True,
    admission=admission,
    build_context=build_context,
    source_evidence=evidence,
    **build_options,
)
pf = buildcache.build_v2(
    genome, trace=False,
    admission=admission,
    build_context=build_context,
    source_evidence=evidence,
    **build_options,
)
```

理由は `T/test_ccbench_spawn_sites.py:738` が `buildcache` 呼出しも build sink として拾い、同:1048以降が condition gate の先行を検査するためです。呼出し元だけで gate を済ませ、別 helper 内で無条件 build する形は避けます。

### pipeline と同じ値を作れるか

| 値 | 現在の供給元と Tier0 の扱い |
|---|---|
| `build_context` | `C/p3_s4_loop.py:3407`。機械生成は generator context、LLM は既存 CLI が発行した coder authority を束縛。同じオブジェクトを再利用し、再発行しない |
| capability | 機械生成は同:1991、:3424の resolver。Tier0 と後続 pipeline に同じ resolver を渡す。LLM は現行どおり `None` |
| source evidence | `source_digest.resolve_evidence(genome, cfg.ccbench_commit, ccbench_dir=sub, cxx=resolved_cxx, backoff_grammar_version=...)`。pipeline の実呼出しは `C/pipeline.py:1805` |
| compiler | `buildcache.compilers_for_current_site()`。pipeline の alias は `C/pipeline.py:91`、Pegasus は `C/buildcache.py:1863` の `gcc/g++` |
| admission | `derive_build_admission` → `require_build_admission`。generator/review capability の exact type 分岐を `C/pipeline.py:1840` と揃える |
| v2 selector | `campaign_options["env_contract"]` と同じ値。既存契約 `contract` があるだけで、非 v2 経路を勝手に v2 化しない |
| cache root | `cache_root or os.path.join(buildcache._ccbench_dir(), "build-variants")`。`C/pipeline.py:1956` と一致させる |
| dependency | `dependency_prefix` と FetchContent の base/source dirs/receipt を `C/pipeline.py:1964` と同じ条件で渡す |
| その他 | `declared_use_class="exploration"`、現在の grammar version。B-5 が現在供給しない snapshot descriptor、qualification policy、expected toolchain は追加しない |

通常の B-5 driver は prebuild receipt を必須にし、子はその場合 `env_contract` を渡すため v2 になります（`C/b5_generator_contrast.py:485`、`C/p3_s4_loop.py:2268`）。子を直接使う B-5 経路で v2 selector が無い場合は、pipeline と同じ `buildcache.build` 分岐も用意します。**Tier0 だけ常に v2 にする案は不採用**です。

source evidence の runtime proof binding は production の `resolve_evidence` が既に生成します（`C/source_digest.py:2413`、:2460）。pipeline の補完処理 `C/pipeline.py:1824` を省略した偽 evidence で代用しません。

### cache 再利用の根拠と限界

`C/buildcache.py:1301` の identity は genome、pin、trace、source、compiler/toolchain、site、dependency、admission 等で決まります。さらに contract hash が cache directory を分けます（同:2704）。

特に次を満たせば、Tier0 と後続 build の key は一致します。

- 同じ `applied(...)` 区間内の同じ `sub` を使う。admission の source receipt に **source root も入る**（`C/source_digest.py:249`）。
- 同じ capability 入力を使う。admission の wire body に process nonce は入らない（`C/build_admission.py:703`）。
- trace/perf ごとに、上表の全引数と ambient build 環境を保持する。
- Tier0 通過後に source を変更しない。

したがって正常時は **build API は計4回呼ぶが、実コンパイルは trace/perf 各1回**、後続2回は検証付き cache hit です。condition gate 自身の独立検査はこの「2回」に含めません。

ただし `C/buildcache.py:2716` は完成 entry より先に `.building` claim を検査します。stale claim、source/toolchain 変化、破損 entry に対して再利用成功を保証しません。claim を消したり検証を省いたりせず停止します。

T-2632 land 後に引数が変わって一致を維持できない場合の代替は、まずその新引数を Tier0 に同様に渡すこと。それでも難しければ build-input 作成だけを共通化する別変更を検討します。`run_campaign(do_bench=False)` を Tier0 代わりに呼ぶ案は、WAL・claim・certification 境界を動かすので採りません（`C/loop.py:697`、:734）。

### authority・目録への波及

| 面 | 判定 |
|---|---|
| coder authority | `C/materializer_admission.py:152` の既存 `p3_s4_loop.main` を利用。driver の新登録なし |
| `EXPECTED_CODER_SITES` | `T/test_p3_build_authority_cli.py:71` は変更不要 |
| 手書き CMake materializer | 新しい CMake argv を組まない。`C/materializer_admission.py:191` の集合は変更不要 |
| `"--build"` exact 閉包 | `T/test_s8b_floor_campaign.py:8079` は文字列定数を含む関数を拾う。新 helper に `"--build"` 定数を置かない。build 結果の `build_cmd` をそのまま記録する |
| build admission 検査 | 同:8127の `admission/build_context/source_evidence` 検査に通るよう、上記3引数を呼出しで明示する |
| certified-writer inventory | 新しい `run_campaign/evaluate` 呼出しなし。`T/test_campaign.py:5418` の子2箇所、:5500の2回は不変 |
| contract-loader closure | `C/campaign_lock.py:49` の現集合に子・buildcache・runner・benchparse・lock は既に含まれる。新 production module を作らないので path 集合の変更不要。子の blob hash は当然変わる |
| official perf closure | `T/test_official_perf_closure.py:60` に子は既登録。`run_once(use_perf=False)` は同:27の tracked call を増やさない。固定 `False` に新しい perf 判定分岐も不要 |
| build sink closure | `T/test_ccbench_spawn_sites.py:2903` を必須回帰に含める。新 build sink を deferred 例外へ登録しない |

Tier0 前に必要な環境契約確認は既存 `env_contract.authorize` と `execution_guard.require_certified_writer_authorization` を使います（`C/execution_guard.py:107`）。これは campaign claim の先取りとは別です。`loop._authorize_measurement` を先に呼んで claim を二重取得しません。

## 2. 固定 smoke の契約

根拠は `C/pipeline.py:147` の既存小構成と、`orchestrator/calibrator/runner.py:584` の gateway です。**小構成は Tier0 専用**とし、後続 legacy＋performance correctness はそのまま実行します。

Pegasus で提案する exact argv は次です。

```text
<pf.binary>
--thread_num=4
--ycsb_tuple_num=200
--extime=1
--ycsb_rratio=50
--ycsb_zipf_skew=0.9
--ycsb_rmw=true
--ycsb_max_ope=5
--clocks_per_us=2100
```

- binary は今回得た **trace-disabled `BuildResult.binary`**。
- `clocks_per_us` は直書きせず `contract.clocks_per_us`。現在の Pegasus 契約は2100、prefix は空（`C/env_contract.py:253`）。
- `numactl=list(contract.numactl)`。Pegasus で `NUMA` 定数の `--interleave=all` を混ぜない。
- workload の rr5/50/95 を smoke に流用しない。全候補で rr50。
- `use_perf=False`、`strict_returncode=True`、`rep_returncodes=[]`、明示 timeout。`measure_point` の反復・settle・品質再測定は使わない。
- gateway が一時 cwd、`log/`、`FLAGS_*` 除去、後片付けを担当する（`runner.py:636`）。

`_run_b5_tier0_smoke` 全体の実行部分を既存 `bench_lock()` で囲みます。lock path は既存 env を継承し、Tier0 独自 lock は作りません。lock 待ちは Tier0 wall に含め、**subprocess timeout が lock 待ちまで制限するとは主張しません**（`C/lock.py:43`）。

起動点の追加は次の1行だけです。

```python
# T/test_ccbench_spawn_sites.py:41
("campaign/p3_s4_loop.py", "<module>._run_b5_tier0_smoke"): 1
```

追加先は `_BOUNDED_RUN_ONCE_CLIENTS`。`_GATEWAY`、direct spawn、non-CCBench 除外には足しません。

### 出力の通過条件

`runner.run_once` は内部で `parse_bench_stdout` を呼びます（`runner.py:710`）。返った metrics を既存 consumer で検収します。

1. rc が `[0]`。
2. `integer_abort_commit_counts(metrics)` の `commit_counts_ > 0`。
3. `throughput_tps(metrics)` が finite かつ正。
4. 例外・timeout が無い。

パーサは `orchestrator/calibrator/benchparse.py:22`、:55、:68。`throughput_tps` の既存 fallback、`commit_counts_/actual_extime` も契約に明記します。smoke の値は `tier0.smoke` の検収証拠にだけ保存し、`fitness_tps`、bench payload、`current_perf`、endpoint 選択へ写しません。

holdout 保護は **rr20/rr80 に対して ratio 単独でも発火**します。tuple/thread を小さくして回避できません（`orchestrator/holdout_observation.py:216`、:1194）。rr50 を採り、特別な admission token は作りません。

### timeout

**実値は未確定です。** 試走資料にこの smoke の実測はありません。P3に従い、親の gen_S 実測で得た最大所要を `m` とし、提案式を `τ = max(1, ceil(3m)) 秒` とします。倍率3は設計候補であり実測値ではありません。

測定時の外側上限には既存 gateway の120秒を明示して使えますが、それを本番の根拠済み timeout と扱いません。親の実測後に整数 `τ` をコード・header 契約・insight に固定することを実装完了条件にします（brief:24）。

## 3. sidecar・U1・report

### 接点 schema

`C/p3_s4_loop.py:1918` の既存 create-once writer を使用します。ファイル fsync → rename → directory fsync の順を保持し、開始印を最終結果へ上書きしません。

**`tier0-start.json`**

```text
schema = "p3-s4-loop-b5-tier0-start/v1"
b5_slot, campaign_id, genome, identity_preimage_sha256
contract_id = "b5-tier0/v1"
ts_utc
```

**`tier0.json`**

```text
schema = "p3-s4-loop-b5-tier0/v1"
上記の identity 4 field と contract_id
status = "passed" | "rejected" | "error"
reason = null | 固定 reason code
failure_class = null | "candidate" | "unclassified-missing"
started_at_utc, finished_at_utc, wall_s
builds = trace/perf の完了済み結果の配列
smoke = 未実施なら null、それ以外は実行・検収結果
```

`builds` の各要素は `trace`、binary path/full SHA256、`cached`、configure/build argv。`smoke` は exact argv、timeout、rc、wall、commits、throughput、検収成否を記録します。未取得値は `null`、NaN/Inf は保存しません。

開始印は evidence 解決・build の前。最終結果は判定後、**submission より前**。不通過では submission を書かず戻ります。

`drive_iteration` の digest 抑止集合にも新 outcome を加える必要があります（`C/p3_s4_loop.py:2876`）。これを忘れると、Tier0 が WAL を作らない正常な拒否経路で certified campaign admission を試みます。CLI の rc3 分岐 `:3535` には `rejected-tier0` を追加します。

### P4の修正：全例外を候補起因にしない

`C/buildcache.py:2717` の stale claim、admission 不一致、I/O 障害まで「候補のコンパイル失敗」にまとめる案には反対です。

| 観測 | outcome / failure_class | 処置 |
|---|---|---|
| コンパイラ終了失敗、smoke非0、解析不通過、smoke timeout | `rejected-tier0` / `candidate` | submissionなし、retryなし。searchは次のAへ |
| admission・identity・cache integrity・分類不能I/O | `unclassified-missing` / `unclassified-missing` | submissionなし、retryなし、系列停止 |
| 開始印だけ残存 | `tier0-interrupted` / `unclassified-missing` | Aのみ、retryなし、未完走 |
| 明示的に観測した投入前timeout | `rejected-tier0` / `candidate`、reason=`pre-submit-timeout` | Aのみ |
| submissionあり | 従来の投入後分類 | B消費を維持 |

build の終了失敗は `C/buildcache.py:3816` の `_run` が普通の `RuntimeError` に変換します。したがって **`RuntimeError` 全体や例外文面で分類しない**こと。既存 `_b5_proposal_rejected` 同様に拒否境界を識別するか、識別できないものを `error` に残します。依存物障害の無料 retry を今回一般化しません。

### `classify_slot`

変更箇所は `C/b5_generator_contrast.py:297`。

- slot-start と expected slot/genome を照合した後、submission の有無を先に確定する。
- submission が無い場合に Tier0 terminal/start を読む。
- schema、identity、contract、status/reason の組合せを検証する。
- `passed` だけでは `submitted=True` にしない。
- malformed JSON、別 slot、未知 status は成功・候補拒否にしない。
- 有効な submission と rejected sidecar が同居した場合は矛盾として扱い、**既に発生したBを取り消さない**。
- rc3だけで Tier0 拒否と判定しない。

`_execute_slot` の timeout 上書き `:603` も変更し、投入前と投入後を区別します。開始印だけから scheduler walltime の原因を断定しない点がP5の修正です。

### A/Bと台帳

新 event kind は不要です。

- search の Tier0 拒否は既存 `proposal-rejected` に `tier0` field を追加。
- 通過後の評価は既存 `pipeline-submitted` / `evaluation-result` に同じ証拠を添付。
- score は既存 `score-session`。
- `EVENT_FIELDS` の全件必須項目は増やさず、追加 field として扱い、過去台帳を壊さない（`C/b5_generator_contrast.py:231`）。

Aは既に `:717` で消費済み。Bは `:618` の `submitted_once` のみで進めます。以前の retry attempt が投入済みなら、その後の Tier0 拒否でもBを返しません。

score の Tier0 拒否では探索A/Bを増やさず、`:805` の非certified分岐で停止。stock-start/block-stock はTier0対象外です。

### headerと段階導入

`C/b5_generator_contrast.py:551` を次に置き換えます。

- `tier0_status="implemented"`
- `tier0_contract`：対象slot、両build、smoke flags、clock/prefixの解決規則、timeout、parser/通過条件、失敗処理、smoke非fitnessの宣言。
- stock headerにも同じ契約を載せ、`applies_to=["search", "score"]` で対象外を明示。

ただし **U1だけの段階で implemented と広告しません**。U2が子に公開する契約定数を `_header` が読む構成にし、定数未導入の中間状態は現状の未実装表示を維持します。新しい実行 gate は作りません。統合後のU1検査で実装済み表示を確定します。

### reportで必須の修正

`C/b5_generator_contrast_report.py:308` の `_reconcile` に投入前の Tier0 証拠回収を追加します。WALを再認証せず、sidecarとattempt identityだけを照合します。

**同:379の `unresolved_search` を `submitted is True` に限定する修正が必須です。** 現状のまま投入前attemptを回収すると、そのattemptまでBへ加算されます。

- Aは既存 `proposal-opportunity` / `slot-attempt-start` の最大値で回収できる（同:391）。開始印ごとに加算しない。
- physical attemptはslot keyで重複排除。
- logical sessionはsubmissionありだけ。
- `tier0_rejections`、`tier0_interrupted` を別集計し、既存 `preprocess_rejections` に混ぜない。
- terminal eventとsidecarの両方があるattemptは二重回収しない。
- 過去の `not-implemented` 台帳はそのまま読める。過去台帳を書き換えない。
- 新契約を宣言する台帳では、その契約とTier0証拠の整合を検査する。

## 4. テスト計画

根拠は既存 producer fixture `T/test_b5_generator_contrast.py:134`、report crash fixture `T/test_b5_generator_contrast_report.py:521`、子のdigest分岐 `C/p3_s4_loop.py:2876` です。

**新規 `T/test_b5_tier0.py` をU2が所有**し、次の実体を検査します。

| 提案node | 検査対象 |
|---|---|
| `test_smoke_exact_argv_and_parser` | 実 `_run_b5_tier0_smoke` → 実 `run_once` → 実 parser。argvを記録するfixture executableで検証 |
| `test_smoke_rejects_nonzero_or_invalid_output` | rc非0、空出力、commit=0、counter不正、throughput非finite/非正 |
| `test_smoke_timeout` | 終了しないfixture executableを実gatewayの短いtimeoutで停止 |
| `test_smoke_uses_bench_lock` | 実lockを保持する別processとの排他 |
| `test_tier0_sidecars_are_create_once` | 実writerで完成JSON、上書き拒否、identity保存 |
| `test_tier0_build_arguments_match_pipeline` | source/admissionを実関数で生成し、引数とcache identityを独立照合 |
| `test_b5_submission_follows_tier0_pass` | 開始→両build→smoke→結果→submissionの順序 |
| `test_tier0_rejection_skips_certified_digest` | 拒否がdigest admissionへ進まずrc3になる |
| `test_non_b5_and_stock_skip_tier0` | 既定経路・stock経路の不変 |

fixture executable はCCBenchの生死証明ではありません。gateway、parser、timeout、lock の検査用です。`run_once`、parser、admission、classifier、reportそのものはstubしません。

build成功・cache hit・correctness継続の生死確認は、**親のgen_S実測へ回します**。そこで実proposal、実source、実buildcacheを使い、Tier0のtrace/perfとpipelineのbinary hash一致、後続の `trace_cached/perf_cached=True`、通常verify/benchの継続を記録します。buildcacheを成功stubに置換したテストでP2を検収しません。

U1の既存2ファイルには、実sidecar/WAL fixtureを使って以下を追加します。

- `rejected-tier0` でAだけ進み、retryなし。
- random30件、sweep28件の全拒否。
- LLM拒否後も `next_evaluation=b+1` とwhiteboardが不変。
- score拒否で系列停止、fallbackへの置換なし。
- earlier submitted retryのBを維持。
- 開始印だけ／通過直後／submission直後の各crash回収。
- malformed・別slot・矛盾sidecar。
- smokeの数値を極端に変えてもendpoint/current_perf不変。

固定期待値の変更は次です。

- `T/test_b5_generator_contrast.py:328` の `tier0_status=="not-implemented"`：統合後は実装済み契約の独立期待値へ変更。
- `T/test_b5_generator_contrast_report.py:26` のfixture：新契約fixtureと過去未実装fixtureを分け、後者の読取り回帰を残す。
- `T/test_b5_generator_contrast.py:689` の `SESSION_BUDGET_S=1800`、2700秒等は今回変更しない。
- `_reconcile` のコード変更に伴い、同report testのM24文字列置換アンカーも追従させる。

親の検証対象には上記に加え、build-authority、materializer、certified-writer、spawn/define、official-perf closureを含めます。実行は親が `tools/run_tests.py` 経由で行います。

## 5. 変異matrix候補

アンカーは `C/p3_s4_loop.py:2281`、`C/b5_generator_contrast.py:618`、`C/b5_generator_contrast_report.py:379`。以下のnode名は新規提案です。

| 変異 | 落とすnode |
|---|---|
| Tier0呼出し削除／submissionを先に書く | `test_b5_submission_follows_tier0_pass` |
| traceまたはperf buildを省く | `test_tier0_build_arguments_match_pipeline`＋親の実build確認 |
| capability resolver・grammar・dependency引数を落とす | `test_tier0_build_arguments_match_pipeline` |
| Tier0だけ別cache root/source rootを使う | 同上＋親のcache hit確認 |
| smokeをtrace binaryへ変更 | `test_smoke_exact_argv_and_parser` |
| workload ratioをsmokeへ流す／rr20へ変更 | 同上、holdout gateway拒否 |
| rcを無視 | `test_smoke_rejects_nonzero_or_invalid_output` |
| commit/throughput検収を外す | 同上 |
| timeoutを外す | `test_smoke_timeout`。親側にも外側上限を置く |
| lockを外す | `test_smoke_uses_bench_lock` |
| Tier0拒否をsubmitted扱い | `test_tier0_rejection_consumes_A_only` |
| 拒否をmachine retryに含める | `test_tier0_rejection_is_not_retried` |
| start-only回収を削除 | `test_reconcile_tier0_interrupted_A_only` |
| `unresolved_search` のsubmitted条件を削除 | 同上 |
| 以前のsubmitted attemptのBを返す | `test_retry_then_tier0_reject_retains_B` |
| 拒否をdigest抑止集合から外す | `test_tier0_rejection_skips_certified_digest` |
| smoke throughputをfitness/current_perfへ流す | `test_smoke_metrics_do_not_enter_selection` |

この段では変異を実行していないため、KILLEDとは報告しません。

## 6. P6・P7：設計のみ

### 親運用

**同時1系列／親session、同時親数p=4を運用案として採用。ただし「§7.1から4が必然的に導ける」という根拠は棄却**します。

`V/prereg-7-1.md:4` は各cell12系列を3blockへ4系列ずつ配置し、同:8は **workloadごとの12組全体**へ6順序を各2回割り当てています。brief:32の「blockあたり12組×6通り」は誤りです。

具体案は、各blockで1workloadの4組を4つの処理列へ割り当て、各組内の3armを保存済み順序で順次実行すること。これを3workload分行えば、各blockは12組・36系列、同時LLMは最大4です。各workloadの12系列には6順序を2回ずつ割り当て、block別にはその4系列分を切り出します。

親はLLM系列開始前に確保し、系列終了でそのcontextを廃棄します。p=4は同時枠数であり、4本の会話履歴を36系列へ持ち回る意味ではありません。block間は前blockの**最終測定**から1時間以上空け、別process群とします。score/block-stockの配置も事前保存します（`V/prereg-4-1.md:11`、`V/prereg-7-1.md:7`）。

| 数値 | 種別・意味 |
|---|---|
| 10〜13分／巡 | 試走実測。`V/insight-6.md:47` |
| 2700秒 | 現行契約。`C/b5_generator_contrast.py:50`、:644 |
| 780/2700 ≈ 28.9%、余裕約3.46倍 | 算術。将来の上限保証ではない |
| 36系列×10巡＝360巡、60〜78親時間 | 拒否なしの外挿。`V/d2200-item1.md:50` |
| p=4で15〜19.5時間 | 親作業部分の理想割算。全実験elapsedではない |
| A=30なら最大1080機会 | 登録上限。試走実測ではない |

1親が4系列を順番待ちにする案では、4×780＝3120秒となり2700秒を超えます。同時4系列を扱うなら親も4本必要です。今回、親spawnやschedule実装は行いません。

### walltime

**3arm共通 `W=ceil(21259k)` 秒、block-stockは `Wstock=ceil(5447k)` 秒を設計案とします。** 出所は `V/insight-6.md:42` のjob Elapse実測です。lock待ち・親待ちの推定値を差し引きません。

| kの候補 | 3arm共通W | block-stock |
|---:|---:|---:|
| 2 | 42,518秒＝11:48:38 | 10,894秒＝3:01:34 |
| 3 | 63,777秒＝17:42:57 | 16,341秒＝4:32:21 |

gen_S上限86,400秒という資料上の制約では `k≤86400/21259≈4.064`。倍率2は未承認の候補です（`V/d2200-item1.md:44`）。

block-stockは探索armではなく5sessionの別jobなので別基準を認める案です。ただし、その区別と数値を§12へ明記します。系列開始stockとscore5回は共通Wの内側です。

限界は、試走がwrite-heavyのみで、Tier0追加前・共有lock時代の値であることです（`V/insight-6.md:14`）。balanced/read-heavyやA=30の完走を保証しません。上限不足でもn・correctnessを下げない登録規則を維持します。

`SESSION_BUDGET_S=1800` は子実行timeoutではなく、次slotを始めるための残時間判定です（`C/b5_generator_contrast.py:507`、:522）。今回変更しません。試走最大session1521秒との差は279秒ですが、Tier0追加費がその範囲に収まるかは親の実測で確認が必要です。

deadlineは既に **scheduler開始時刻＋要求walltime** で算出しています（`tools/pegasus/p3_s4_loop_pegasus.sh:371`）。将来Wを変更してもdriver起動時刻から計算し直しません。handshakeの2700秒と残1800秒の判定は別条件で、job末尾では2700秒を全て使えない場合があります。

総実行wallの管理上限と各jobのWは別に再提示します。311〜329 node時間は外挿であり、予約上限の総和ではありません（`V/d2200-item1.md:49`）。

## 7. 所有と順序

所有はbrief:36を基本に、次の素集合とします。

| 単位 | 所有path |
|---|---|
| U1・今すぐ着手 | `C/b5_generator_contrast.py`、`C/b5_generator_contrast_report.py`、`T/test_b5_generator_contrast.py`、`T/test_b5_generator_contrast_report.py` |
| U2・T-2632 land後 | `C/p3_s4_loop.py`、新規 `T/test_b5_tier0.py`、`T/test_ccbench_spawn_sites.py` |
| 親・統合記録 | `output/insights/2026-09-21/t2797-tier0/README.md`、decisions fragment、worklog fragment |

pipeline/buildcache/runner、materializer登録、campaign-lock集合、official-perf検査本体は**本案では編集不要の回帰対象**です。T-2830のjob body・launcher・両test・README、T-2632の別所有pathには触れません。

順序は次です。

1. 本planのschema・状態遷移を固定。
2. U1がconsumer・台帳・crash回収を実装。子未実装の中間状態を実装済み表示にしない。
3. T-2632 land後、U2が新mainで行番号・引数を再照合して実装。
4. 親がgen_Sでsmoke所要・実build/cache再利用・正負経路を確認し、timeout整数を固定。
5. U1/U2統合状態でheader契約と全回帰を確認し、記録を完成。
6. §12 hash採取、倍率・発効commitの再提示、本走投入は別段。

## 総括

- **P1：賛成。** Tier0は子の候補経路だけ。stock除外、driverのbuild authority追加なし（`C/p3_s4_loop.py:2234`）。
- **P2：条件付き賛成。** 同一source root・admission・build引数ならcache再利用可能。閉包 `_build_one` の直接呼出しは不可。異常claimを自動回収しない（`C/pipeline.py:1985`、`C/buildcache.py:2716`）。
- **P3：賛成。** rr50固定、小構成1回、既存gateway/parser、bench lock。timeout整数は親の実測待ち（`runner.py:584`）。
- **P4：一部修正。** 候補失敗はAのみ・retryなし。admission/cache/I/Oの分類不能まで候補起因にしない。scoreは探索A/Bを増やさない（`C/b5_generator_contrast.py:618`、:797）。
- **P5：賛成、証拠の射程を限定。** 開始印だけではtimeout原因を断定できない。reportの投入前回収と、B加算へのsubmitted条件が必須（`C/b5_generator_contrast_report.py:308`、:379）。
- **P6：p=4案には賛成、導出根拠に反対。** 1親1系列・fresh contextを守る運用上の選択。§7.1の6順序はworkloadごとの12組全体（`V/prereg-7-1.md:8`）。
- **P7：条件付き賛成。** 21259秒を共通基準、block-stock5447秒を別基準。倍率・総wall上限は未確定。1800秒はtimeoutではない（`C/b5_generator_contrast.py:522`）。
- **未確定事項：** T-2632後の引数差分、smoke timeoutの実値、実buildによるcache hit確認、追加費と1800秒の整合、倍率・発効commit。今回の静的検査を実測・受入成功とは扱わない。