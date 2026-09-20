# 段2 plan — 結論と適用範囲

基本構成は **A1 core → A2 report ∥ A3 job body／launcher** とする。ただし、author 開始前に次の点を親の段4裁定で固定する必要がある。

- **P7 の「試走 n=1 は §7.4 第4段で止まる」は反証。** 第2段の floor 欠測、または第3段の certified endpoint 数不足が先に成立する。試走専用の記述報告を、本走の判定関数から分離する。
- **共通 Tier0 は現行に存在しない。** 現行 pipeline 内の trace／perf build 失敗は B 消費であり、Tier0 不合格へ読み替えない。
- **純粋な verifier wall は現行 WAL の時刻差だけでは取れない。** trace＋verify 区間と区別し、計時方法を決める。
- **新 driver の LLM build authority と機械生成候補の admission を閉じる必要がある。** stock 用 resolver の転用だけでは random／sweep 候補は受理されない。

根拠は `verbatim/prereg-s3.md:17`、`verbatim/prereg-s7.md:71`、`pipeline.py:619`、`p3_s4_loop.py:1917`・`:2959`。

以下、repo 相対パスは指定 worktree を基準とする。`L` は `orchestrator/campaign/p3_s4_loop.py`、`P` は `orchestrator/campaign/pipeline.py`、`C` は `orchestrator/campaign/loop.py`、`TJ` は `orchestrator/tests/test_p3_s4_loop_job_contract.py`、`V` は親 job directory の `verbatim/` を表す。新設ファイルの `:1（新設）` は作成位置であり、未存在の関数行番号を仮定しない。

**全検査は未実走・静的読解。** ファイル編集、pytest、build、計測、qsub、commit は実施していない。

# 1. Module 構成・共通評価 seam

`orchestrator/campaign/b5_generator_contrast.py:1（新設）` が生成器、系列台帳、単回評価 adapter、handshake、endpoint 再計測を所有する。`b5_generator_contrast_report.py:1（新設）` は台帳を読む純粋な解析 consumer とする。

import は次の一方向に固定する。

```text
b5_generator_contrast_report → b5_generator_contrast の純粋 schema／定数
b5_generator_contrast → p3_s4_loop／既存の campaign 部品
p3_s4_loop → 既存依存だけ
```

`L` から B-5 module を import しない。新しい標準ライブラリ等も不用意に `L` へ追加しない。これにより `test_p3_b4_wiring_probe.py:327` の import 閉包49、`test_p3_exploration_namespace.py:426` の layout 11／run_campaign 2 を維持できる。

**既存の利用面**

| 所在 | 現物 signature／定数 | B-5 での扱い |
|---|---|---|
| `L:115`・`:129` | `PIN`、`MARKER_ID` | そのまま利用。独自 pin・marker を作らない |
| `L:1574` | `default_cfg(reflux: bool=True, *, b4_reflux_ablation: bool=False, _b4_launch_context=None) -> CampaignConfig` | reflux on、非B4を基礎に B-5 key を別辞書へ追加 |
| `L:1661` | `calibrated_perf(workload_name: str) -> PerfConfig` | 全 session 共通 |
| `L:1653` | `default_perf() -> PerfConfig` | 本 driver では使用しない |
| `L:127` | `_current_site = site_policy.current_site` | site 解決。独自 hostname 判定で代替しない |
| `L:141` | `_admit_env_contract(site: str) -> ExecutionEnvironmentContract` | 既存 admission を通す |
| `L:150` | `_campaign_cfg_for_site(cfg, site, *, _contract=None) -> CampaignConfig` | site／environment identity を束縛 |
| `L:267` | `_load_masstree_prebuild_receipt(path: str \| os.PathLike[str]) -> tuple[str,str,str,str,Dict[str,str]]` | receipt 検証と5引数への射影を再利用 |
| `L:417` | `_require_condition_gate(source_root: str, genome: Genome, *, configure_args: Tuple[str,...]=(), stock_root: Optional[str]=None) -> dict \| None` | resolved 評価関数から既存どおり呼ぶ。B-5 が二重実行しない |
| `L:1917` | `_stock_capability_resolver(build_context: BuildRunContext)` | stock 関数内部で利用。候補へ流用しない |
| `L:1611`付近 | `_resolve_knowledge_manifest_argument(manifest_path: Optional[str \| os.PathLike[str]]) -> Optional[ResolvedKnowledgeManifest]` | LLM だけに利用 |
| `L:1619` | `_prepare_knowledge_campaign(cfg, resolved, *, classification: str, de_novo_claim: bool) -> tuple[CampaignConfig,Optional[CampaignLayout],Optional[Dict[str,Any]]]` | slot key を付けた後に呼び、receipt と layout のずれを防ぐ |
| `L:1900` | `_refresh_critic_digest(layout, *, reflux: bool) -> CertifiedCampaignView` | 候補評価後の既存 digest を再生成 |
| `L:1292` | `planner_context_payload(state, cfg, *, knowledge_input=None, k2_critic_diagnosis=None) -> Dict[str,Any]` | 系列台帳から組んだ state の射影に利用 |
| `L:1701` | `assert_value_literal_consistent(coder: CoderProposal) -> None` | 既存帰属検査を維持 |

評価関数の現物 signature は以下である。`FC` のような架空の既存引数へ置き換えない。

```python
_run_stock_control_resolved(
    cfg: CampaignConfig, perf: PerfConfig, sub: str,
    layout: CampaignLayout,
    contract: env_contract.ExecutionEnvironmentContract,
    resolved_site: str, *, stock_root: str, cache_root: str = "",
    build_context: BuildRunContext, dependency_prefix: str = "",
    fetchcontent_base_dir: str = "",
    masstree_source_dir: Optional[object] = None,
    mimalloc_source_dir: Optional[object] = None,
    googletest_source_dir: Optional[object] = None,
    fetchcontent_dependency_receipt: Optional[Dict[str, str]] = None,
) -> Dict
```

所在は `L:1931`。

```python
_run_one_iteration_resolved(
    cfg: CampaignConfig, perf: PerfConfig,
    planner: PlannerProposal, coder: CoderProposal,
    state: LoopState, sub: str, do_build: bool,
    layout: CampaignLayout,
    contract: env_contract.ExecutionEnvironmentContract,
    resolved_site: str, log=print, cache_root: str = "",
    dependency_prefix: str = "", fetchcontent_base_dir: str = "",
    masstree_source_dir: Optional[object] = None,
    mimalloc_source_dir: Optional[object] = None,
    googletest_source_dir: Optional[object] = None,
    fetchcontent_dependency_receipt: Optional[Dict[str, str]] = None,
    build_context: Optional[BuildRunContext] = None,
    _b4_launch_context=None,
) -> Dict
```

所在は `L:2020`。

```python
load_proposal_file(
    path: str, *,
    b4_reflux_ablation: bool = False,
    b4_closed_critic_receipt_sha256: str | None = None,
    b4_prerun_publication: str | os.PathLike[str] | None = None,
    b4_attempt_id: str | None = None,
    knowledge_input: Optional[Dict[str, Any]] = None,
    coder_role: str | None = None,
    capture: dict | None = None,
) -> Tuple[PlannerProposal, CoderProposal, Optional[bool]]
```

所在は `L:2473`。

**private 名を跨ぐ判断：条件付きで可。** 同じ repo・同じ対象 commit 内の adapter として依存を明示し、上記 private 関数を B-5 の一箇所へ集中する。単なる public alias を十数個追加する必要はない。ただし既存関数には「B 消費の直前通知」「機械生成候補用 capability」「skip の復元禁止」を渡せないため、ここには最小 seam が必要になる。

推奨 public seam は `L:2020` の直後に置く次の形。型 `options` は上記既存 dependency 引数だけを保持し、任意の `run_campaign` kwargs を受け入れない。

```python
def run_budgeted_iteration(
    cfg, perf, planner, coder, state, sub, layout, contract, resolved_site,
    *, build_context, before_pipeline, capability_resolver=None,
    cache_root="", dependency_prefix="", fetchcontent_base_dir="",
    masstree_source_dir=None, mimalloc_source_dir=None,
    googletest_source_dir=None, fetchcontent_dependency_receipt=None,
) -> dict:
    # existing resolved implementationへ do_build=True で委譲
    # 検疫・condition gateの後、run_campaign直前にbefore_pipelineを呼ぶ
    # B-5だけbench_max_rounds=3を明示し、skipは復元せず返す
```

内部関数へ既定 `None` の keyword-only 引数を追加し、**既定呼出しでは kwargs・分岐・戻り値を変えない**。同じ仕組みで stock にも B-5 専用の明示 round 数を通す。`_resolve_duplicate` 自体は変更しない。

新 module は `run_campaign` を直接呼ばないため、`test_campaign.py:5418` の caller inventory は2のまま。直接呼ぶ設計へ変える場合は、同ファイルの semantic inventory、総数22、`:5500` の raw-AST inventory と総数18を一緒に更新し、`authorization_contract`／`declared_use_class` の明示検査を通す必要がある。

**admission の追加確認事項。** `L:2959` は `add_registered_coder_build_authority_argument(..., coder_entrypoint_site="orchestrator.campaign.p3_s4_loop.main")` を使う。新 CLI がその名を借りれば成立するとは仮定しない。author 前に登録側の正本を追加射影し、既存 authority を正規に受け取る seam または正当な登録箇所を確定する。`build_admission.py` の変更や架空 receipt は不可。

random／sweep は、同じ literal 検疫を通しつつ、生成器入力に結び付いた既存型の generator receipt を resolver で渡す。`L:1917` の resolver は **STOCK のみ**なので使用不可。生成器の由来を LLM と偽らないことと、hole の受理集合を同一にすることを別々に検査する。

# 2. A1-a／A1-b — random と sweep

**P6：条件付き支持。** Decimal の precision 100／130 で1000要素すべての floor 一致を要求する。未実走なので、一致済みとは書かない。根拠は `V/prereg-s4.md` §4.2、格子は `backoff_extended_sweep.py:55`、既存 seed は同`:112`。

新設位置は `b5_generator_contrast.py:1`。

```python
def integer_log_weights(prec: int) -> tuple[int, ...]:
    with decimal.localcontext() as ctx:
        ctx.prec = prec
        return tuple(int(((Decimal(v + 1) / Decimal(v)).ln()
                          * Decimal(2**128)).to_integral_value(
                              rounding=decimal.ROUND_FLOOR))
                     for v in range(1, 1001))
```

`weights100 == weights130`、件数1000、全要素正、`M=sum(weights)` を検査する。二精度一致は登録した再現性検査であり、数学的な区間証明とは呼ばない。

保存形式を次に固定する。

- 重み本体：整数1000個の JSON 配列、ASCII、空白なし、末尾改行なし。
- hash：その本体 bytes の SHA-256。
- 材料 JSON：schema、計算式、precision `[100,130]`、weights、M、`weights_sha256`、Python／decimal 版。
- hash 対象は envelope 全体ではなく、上記配列 bytes。親が試走 insight と将来の発効束へ写す。

```python
def random_value(w: str, r: int, a: int,
                 weights: tuple[int, ...]) -> tuple[int, int]:
    cumulative = tuple(itertools.accumulate(weights))
    M = cumulative[-1]
    L = (2**256 // M) * M
    # c=0から exact ASCII preimage をSHA-256→unsigned big-endianへ
    # U<Lなら bisect_right(cumulative, U % M)+1 とcを返す
```

整数は先頭ゼロなし、改行なし。`w` は3 workload、`r=1..12`、`a=1..30`。SHA 引き直しの c 増加は A を増やさない。生成後の重複・失敗による引き直しは禁止する。

```python
def sweep_order(w: str, r: int) -> tuple[int, ...]:
    grid = tuple(v for v in EXTENDED_SWEEP_US if 1 <= v <= 1000)
    # len=28、重複なしを検査
    return tuple(sorted(grid, key=lambda v: (
        sha256(f"b5-generator-contrast-v1|sweep|{w}|{r}|{v}".encode("ascii")).digest(),
        v)))
```

通常は先頭10点で B=10に達する。前処理の候補起因不通過では A を消費して次点へ進み、B 未達なら11点目以降も使う、という読みを推奨する。理由は §3 の「B 完走または A 到達」と §4.3 の「次点」「格子枯渇」を両立できるため。ただし「最初の10点」を提出数の上限と読む余地があるので、親裁定で明文化する。28点を使い切ったら枯渇、再巡回しない。

proposal は `L:630`・`:640` に合わせ、固定の機械的 planner metadata と `CoderProposal(value=v, implementation=f"double now_backoff = {v};")` を構築する。生成由来は別台帳 field に記録する。全 arm とも最終的に `load_proposal_file` の対応 schema、`CoderProposal.__post_init__` → `_assert_coder_value_domain`、既存 attribution／文法／検疫経路を通す。random／sweep に K2 の `knowledge_use` を捏造しない。

# 3. A1-c — 系列開始 stock と初回入力

所在は `b5_generator_contrast.py:1（新設）`、既存評価面は `L:1931`、成功判定は `L:1990`付近、入力射影は `L:1292`。

系列開始時、候補生成前に独立 `stock-start` slot を1 session 評価する。構成は全 arm とも較正＋legacy/performance verify、stock root は別の pinned-clean root。成功条件は以下の連言とする。

1. `_run_stock_control_resolved` の `outcome == "certified-stock"`。
2. admitted COMMIT が当該 attempt のものである。
3. `BUILD_START.src_token == STOCK`、variant が stock genome と一致する。
4. session 品質が成立し、fitness が有限・正である。

COMMIT の `fitness_tps` と同 attempt の `bench_done.median_tps` の整合を確認し、台帳へ `stock_start` と初期 `current_perf` を保存する。rc 0 や campaign ID だけを成功根拠にしない。

入力形は K2 round3 の `materials/planner-input-4.json:2`・`:30`・`:35`、`coder-input-4.json:2` に合わせる。

- planner：`current_perf={"throughput_tps": ..., "abort_rate_pct": ...}`。
- leading indicators：実測値または null。欠測を0へ変換しない。
- coder：既存の `baseline` 射影。
- whiteboard：初回は空。
- knowledge：固定した K2 manifest の射影。
- critic diagnosis：初回は key 自体を置かない。

random／sweep は stock 結果を台帳に記録するが、値生成・順序に使わない。

**stock 不成立なら、その系列を `stock-unestablished`／判定不能として停止する。** 不成立の初期値を使って LLM を動かさず、残りを埋めるための代替系列も作らない。これは性能による早期停止ではなく、`V/prereg-s6.md:24` の比較前提不成立である。

# 4. A1-d — session 品質と correctness

**P3：支持。ただし abort 分類と系列欠測の保持を追加する。**

新設 `classify_session(records, *, reps: int=5) -> SessionObservation` は、admitted な同一 attempt の WAL を読む。`L` の戻り値 `records` だけに依存しない。`records_by_stage` では反復 verify を一件へ潰すため、原 WAL の順序付き列も保持する。

COMMIT 後の品質分類は次のとおり。

```python
def quality_missing(bench: Mapping[str, object], reps: int) -> bool:
    # payloadの型・必須field不正は別途 evidence-invalid
    return (len(bench["tps"]) != reps
            or bench["unstable"]
            or bench["settled"] is not True)
```

根拠は `P:1461` の payload と `V/prereg-s5.md` §5.3。`rounds`、`cv`、`median_tps`、`bench_wall_s` も保存する。COMMIT を書き換えず、**「certified の歴史事実」と「B-5 endpoint 資格」を分離する**。

品質欠測は A/B を返さず、endpoint 候補から除外する。系列に品質欠測があった事実も残し、後の正常 endpoint で消さない。§7.4 第2段は系列の品質欠測を判定不能にするためである。

`P:1440` の `bench-no-throughput`、`:1449` の `bench-cv-undefined` は `bench_done`／COMMIT が無い場合もある。これらを単に「候補なし→fallback」へ流さず、保存された abort detail から測定欠測として扱う。明示的な I/O 障害等の証拠がある場合だけ機械故障へ分類する。

`bench_max_rounds=3` は `C:371` の既定と同じなので、**現在の挙動を得るだけなら明示不要**。ただし本実装では session 契約の束縛を test で観測できるよう、B-5 seam だけ `run_campaign(..., bench_max_rounds=3)` を渡す。既存経路に新 kwargs を増やさない。`C:751` は値3のとき evaluate kwargs を増やさず既定を用いる。

correctness は `C:153` → `P:193` の既存接続を利用する。

- `search_config["verify"]="legacy+performance"`。
- legacy 1回＋performance 5回。
- WAL の `workload` は `{"tag":"legacy"}`／`{"tag":"performance"}`。
- `P:2175` の repetition loop は一件の不通過で即 return。
- anomaly は B 消費、bench 不到達、COMMIT 不成立、endpoint 不採用。

`pipeline.py`／`loop.py` は変更しない。

# 5. A1-e — 系列 driver、A/B、停止、retry

**P2：条件付き支持。** `drive_iteration` を避けるだけでは、B 消費の永続化、digest、役割入力保存まで自動では引き継がれない。

新設 signature は次に固定する。

```python
def run_series(arm: str, w: str, r: int, *,
               ledger_root: Path, fetchcontent_prebuild_receipt: Path,
               knowledge_manifest: Path | None = None) -> SeriesResult:
    # stock-startを評価し、成立後に生成を開始
    # A<30かつB<10の間、原提案機会→検査→pipeline投入を記録
    # endpointを永続化してから5 fresh sessionを評価
```

`L:2598` の `drive_iteration`、`:2721` の入口 `check_stop`、`:1341` の停止判定は呼ばない。`MAX_ITER`／`MAX_WALLTIME_S`／`CONVERGE_STREAK`／`REVERSE_STREAK` は変更しない。`prior_critic_reverse` は入力として保存するが、停止には用いない。

**台帳 schema：`b5-generator-contrast-ledger/v1`**

系列 header に cohort、purpose=`pilot`、arm、workload、series、block、HEAD／PIN、構成、job identity を置く。イベントには少なくとも以下を持たせる。

- `event_seq`、event kind、時刻。
- 原提案番号 `a`、評価番号 `b`、論理 slot key、物理 attempt 番号。
- proposal／実入力の path と hash、生成由来。
- campaign ID、full preimage hash、variant、build attempt ID、WAL 参照。
- outcome、A/B 消費、failure class、品質、fitness、anomaly、whiteboard 射影。
- endpoint 固定、再計測、fallback／欠測の理由。

append-only は **連番の不変 JSON イベント群**で実現する。各ファイルは同 directory の一時ファイルへ書き、flush／fsync 後に atomic publication、既存宛先は上書きしない。集約 `series.json` は再生成可能な view とし、正本にしない。

A は proposal の検査前に `proposal-opportunity` で消費する。空出力もその機会の結果として閉じる。B は `L:2171`付近の `run_campaign` 呼出し直前 seam で `pipeline-submitted` を durable に記録する。成功時の後付け加算は禁止する。

| 分岐 | 現物位置 | A | B | 台帳上の処理 |
|---|---|---:|---:|---|
| 原提案の空出力、JSON／schema不正 | `L:2473` | 1 | 0 | `proposal-rejected` |
| 値域違反 | `L:640`・`:1685` | 1 | 0 | 同上 |
| literal 帰属不一致 | `L:1701`・`:2078`付近 | 1 | 0 | 同上 |
| grammar preflight reject | `L:2057`以降 | 1 | 0 | diff reject の WAL と結合 |
| diff-quarantine reject | `L:2130`付近 | 1 | 0 | rejected。次の原提案へ |
| pipeline 前の condition gate 不成立 | `L:2145`付近 | 1 | 0 | 候補起因／機械故障／分類不能を証拠付きで区別 |
| 共通 Tier0 不合格 | **現行未実装** | 1 | 0 | 将来の exact 契約。現行 build と混同しない |
| 投入後の trace／perf build 失敗 | `P:1910`以降 | 1 | 1 | candidate failure。無料 retry 不可 |
| verify anomaly | `P:655`・`:2137` | 1 | 1 | reject、benchなし |
| bench abort | `P:1400`以降 | 1 | 1 | 原因別分類。自動 fallback にしない |
| certified＋正常品質 | `L:2190`付近 | 1 | 1 | endpoint 候補 |
| certified＋品質欠測 | `P:1461` | 1 | 1 | endpoint 資格なし、品質欠測保持 |
| stock-start／score／block-stock | `L:1931`ほか | 0 | 0 | 探索 A/B 外の論理 session |

**Tier0 の扱い。** `V/prereg-s3.md:23` 自体が未成立を明記している。本 wave の試走を既存経路の費用測定として進めるなら `tier0_status="not-implemented"` を明示し、§3.1 完全適合を主張しない。固定スモークを実装するなら内容・timeout・build authority を親が先に指定する。condition gate を無断で「共通 Tier0」と改名しない。

**retry**

`V/prereg-s3.md:34` に従い、同候補・同入力・同予定位置の追加2回まで。台帳は論理 A/B を増やさず物理 attempt を増やす。anomaly、品質赤、候補 compile failure、候補処理中の walltime は retry 対象にしない。分類不能も無料 retry にしない。

`C:589` の retryable abort 集合は B-5 §3.3 と同一とは限らない。これを B-5 の分類器に代用しない。途中 kill は開始イベントと scheduler 証拠から後処理で分類し、終了イベント欠落を成功扱いしない。

node 喪失後に別 job へ移る場合、開始 stock と後続評価の「同 job」は維持できない。新しい stock を無料追加して系列を継続する設計にはしない。本試走では同 job 内で可能な retry と、候補処理前の起動 retry を実装し、途中 allocation 喪失は系列欠測として親へ返す。

# 6. A1-f — fresh layout と identity

**P1：条件付き支持。** 通常の別 slot は分離できる。ただし同 slot の再起動、物理 retry、hash8 衝突まで「構造的に絶対起きない」とは言えない。

`ident.py:196` の preimage は `spec_content / ccbench_commit / search_tag / search_config / trial`。slot は `search_config` に焼く。

```text
b5_slot = b5-generator-contrast-v1|<arm>|<w>|<r>|<kind>|<n>
```

| 用途 | arm／r／kind／n |
|---|---|
| 探索 | `llm|random|sweep-matched`、系列番号、`search`、原提案番号a |
| 系列開始 stock | 当該 arm、系列番号、`stock-start`、1 |
| endpoint 再計測 | 当該 arm、系列番号、`score`、1..5 |
| block stock | `stock`、block番号、`block-stock`、1..5 |

探索では grammar reject も固有 layout を持ちうるので、slot 番号に B ではなく A を使う。評価番号 B は台帳で別に保持する。

加えて `b5_cohort="t2797-beta-v1"` を付け、試走と将来本走を分離する。物理 retry は同じ `b5_slot` のまま `b5_attempt=0,1,2` で別 campaign にする案を推奨する。これにより terminal abort を削除せず fresh な物理評価へ進める。論理 slot と campaign を一対一だと仮定しない。

既存 campaign／tests の読解・検索では `b5_slot` は未使用。`workload` を別の意味で再利用せず、較正設定は D75／D2183 と同じ `perf_workload` を用いる。

`layout.py:594` は campaign ID から directory を作る。`C:580` はその layout の WAL を replay し、`:695` の `v in done` で skip する。同 v でも slot ごとに別 layout なら、前 slot の terminal は見えない。

ただし `ident.py:226` は hash の先頭8桁で directory を決める。全試走 slot の ID と full preimage を事前比較し、衝突・既存の不一致 lock は fail-closed とする。既存 lock を削除して進めない。

`L:1826` の `_resolve_duplicate` は過去 certified を復元し、whiteboard を success にできる。B-5 seam は `summary.skipped`／`identity_skipped` を **この復元より前に** `duplicate-skip`／`identity-skipped` として返す。成功を復元せず、B の機会も増やさない。

評価ごとの fresh submit-tree 案は、K2 round3 `README.md:54` のように同 campaign ID・別物理 root で分離できる。ただし source checkout、receipt、WAL 所在の管理が評価ごとに増え、identity だけで slot を識別できない。本案は **jobごとに専用 submit-tree、session ごとに slot layout と隔離 CCBench worktree**とする。

# 7. A1-g／A1-h — endpoint、再計測、状態継承

新設位置は `b5_generator_contrast.py:1`。endpoint 規則は `V/prereg-s6.md:3`、anomaly 波及は同`:8`。

```python
def select_endpoint(evaluations: Sequence[Evaluation],
                    disqualified_values: set[int]) -> Endpoint | None:
    # certified、品質正常、anomaly失格でない評価だけ
    # key=(-session_median_tps, value, evaluation_slot)
    # 選択したvalue/source/proposal bytes/出所slotを返す
```

選択結果を `endpoint-fixed` イベントへ書いてから、同じ literal／source の5 fresh score session を同 job で回す。再生成した coder 出力で置き換えない。5 session の median を score とし、探索時の最大値は score に流用しない。

再計測 anomaly は直ちにその候補を不採用にし、次点を選ばない。残る無意味な score session は未実施と記録できるため、53は常に実施する数ではなく上限になる。機械欠測・品質欠測は score missing、stock fallback で埋めない。

fallback は `pending-block-stock` として系列台帳へ残し、consumer が同 workload・block の正常な stock 5 session の median を結合する。遅い certified endpoint は fallback に変更しない。

**必須追加：anomaly の横断波及。** consumer は全台帳の `(workload,value)` anomaly 集合を先に作る。別 arm／別系列で既に採用された同値 endpoint も不採用へ訂正する。元の certified／score イベントは保持し、日付付き結果訂正として報告する。他 arm の結果を生成器入力へ還流しない。

**whiteboard の系列継承**

slot layout を系列 layout に再利用しない。系列正本は台帳、各評価の `LoopState` は既存 `project_whiteboard` を使う一件分の adapter とする。系列 checkpoint を初期化して停止を迂回する方法ではない。

- pipeline 投入済み評価だけを評価番号1..Bへ写す。
- A-only rejection は別イベントへ保持し、次の評価 k の whiteboard 件数へ混ぜない。
- five fields は `L:647` の `iteration/direction/magnitude/result/delta_pct`。`delta_pct=None`。
- certified＋品質欠測でも既存 whiteboard の success は certified の意味として保存し、品質は別の構造化結果に残す。
- digest は `L:1900` の admitted view 経路で slot ごとに生成し、親へ渡す履歴を台帳が束ねる。

```python
def expected_whiteboard(ledger: SeriesLedger, next_evaluation: int) -> list[dict]: ...
def assert_inherited_inputs(
    ledger: SeriesLedger, planner_input: Mapping, coder_input: Mapping,
    *, next_evaluation: int,
) -> None: ...
```

検査は件数だけでなく、台帳の評価1..k−1からの射影と **順序・値・全fieldが完全一致**することを要求する。親が proposal を置く前と job が受理するときの両方で呼ぶ。critic diagnosis の exact 6 field と planner／coder 間の同一性も既存 `L:1270`／`:1292` の経路で確認する。

`current_perf` は初回 stock、以後は既存形式の直前評価の構造化結果から射影する。失敗時に過去の正常値を「直前の測定値」として無印で残さない。欠測表現と role prompt の較正構成への更新は親の試走入力仕様で固定する。round3 の配線規模をそのままコピーしない。

# 8. A2 — report consumer と P7 の反証

新設 `b5_generator_contrast_report.py:1` の入口を次に固定する。

```python
def build_report(ledgers: Sequence[SeriesLedger], *,
                 purpose: Literal["pilot", "registered"]) -> dict: ...
def exact_sign_flip_p(differences: Sequence[float]) -> float: ...
def holm_six(raw_p: Mapping[ComparisonKey, float]) -> dict: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

入力は系列台帳3 arm分と block-stock 台帳。出力は JSON と同じ値から作る表。consumer は build・qsub・追加測定を行わない。schema、slot 重複、attempt の所属、endpoint 固定前後、正の有限 score、台帳と証拠の対応不成立を区別して報告する。

登録本走用には `V/prereg-s7.md` の順をそのまま実装する。

| 部品 | 規則 |
|---|---|
| stock CV | 全15 session の標本CVと、3 blockそれぞれ5 sessionの標本CVの計4つ |
| floor | `CV_stock=max(4 CV)`、`f=max(0.03,CV_stock)`、`δ=ln(1+f)` |
| 精度 | endpoint 5 session の CV が `2*f` **を超える**対を精度不足 |
| 対差 | `d_r=ln(score_LLM/score_b)` |
| exact p | 全 `2**n` 符号反転、平均が観測平均以上の tail。n≤12 |
| fallback≤1対 | 全対の主解析で判定、副解析併記 |
| fallback≥2対 | fallbackを含む対を除く副解析で p・median・block medianをすべて再計算 |
| 対不足 | 使用対<6、またはいずれかの block に1対未満 |
| Holm | 族6固定、判定不能・規約不適合は計算上 p=1 |
| workload優越 | 両baselineで補正有意、median(d)>δ、全block median(d)>0 |

判定順は固定する。

1. 規約不適合。
2. 欠測・stock不成立・floor不成立。
3. certified endpoint 数による生成不成立。
4. 対不足・精度不足。
5. 条件付き優越。
6. `abs(median(d)) <= δ` の同等。
7. `median(d) < -δ` の逆向き記述差。
8. 残る判定不能。

**P7：反証。** 試走は1 blockのstock5件しかなく、登録 floor の4CVを作れない。また、正常完走しても certified endpoint 数は各arm最大1で、第3段の6未満に該当する。第4段だけを理由として返す実装は判定順違反になる。

代案は `purpose="pilot"` の独立した記述経路。`registered_judgment="not-applicable-pilot"` とし、「登録比較に必要な系列数・block・floorを満たさない」と記す。score、fallback数、certified endpoint数、A/B、品質欠測、anomaly、費用を報告する。stock5件のCVを出しても「本走の f(w)」とは呼ばない。優越・同等の判定は出さない。

合成データ test は、12対×3blockでの明瞭な正差、零差、逆差、片baselineだけの勝利、floor最大値、精度境界の等号、fallback1→2の解析切替、残存5対、block空、p=1穴埋めを含める。等絶対差の11正／1負で `13/4096`、10正／2負で `79/4096` を固定例にする。

# 9. A3 — job mode と login launcher

**P4：条件付き支持。** 同 job のオンライン K2 手番には job 内待機が適合する。ただし「唯一の形」は反証で、FIFO／socket等も可能。本 wave では共有ファイルの atomic handshake を採る。

**P5：条件付き支持。** 既存 job body 拡張が最小。ただし「pin／registryの更新不要」は成立しない部分がある。

変更位置は `tools/pegasus/p3_s4_loop_pegasus.sh:54` より前の B-5 mode 判定と、`:596` より前の driver 分岐。既存 `:596–621` の candidate／stock 呼出し本文は保持する。

| env | 値域・条件 |
|---|---|
| `IZANAGI_S4_B5_MODE` | `series`／`block-stock`。未設定だけ off、設定済み空値は拒否 |
| `IZANAGI_S4_B5_ARM` | seriesでは `llm`／`random`／`sweep-matched`、block-stockでは `stock` |
| `IZANAGI_S4_B5_WORKLOAD` | 3 workload名。β launcherはwrite-heavyに固定 |
| `IZANAGI_S4_B5_SERIES` | 先頭ゼロなし1..12。βは1 |
| `IZANAGI_S4_B5_BLOCK` | 1..3。βは1 |
| `IZANAGI_S4_B5_LEDGER_ROOT` | 非空絶対path。job別directory |
| 既存K2 env | LLMで必須、random／sweep／block-stockでは禁止 |

B-5 env の一部だけ設定、空値、不正値、既存 `PROPOSAL_PATH`／`FIXTURE_VALUE` との併用、`STOCK_CONTROL=1` との併用を repository path 解決前に rc=2で拒否する。`STOCK_CONTROL=0`／未設定は許容する。

現行 `:95` の K2 proposal-path 必須条件は、**B-5 LLM のみ例外**にする。旧 K2 の条件・argv・rcを維持する。dummy proposal path を入れて既存検査を通す方法は採らない。

系列起動は1箇所とする。

```text
"$PY" -B -m orchestrator.campaign.b5_generator_contrast run-series
  --arm "$IZANAGI_S4_B5_ARM"
  --workload "$IZANAGI_S4_B5_WORKLOAD"
  --series "$IZANAGI_S4_B5_SERIES"
  --block "$IZANAGI_S4_B5_BLOCK"
  --ledger-root "$IZANAGI_S4_B5_LEDGER_ROOT"
  --fetchcontent-prebuild-receipt "$prebuild_receipt"
  [LLM専用のK2引数]
```

block-stock は同 module の `run-block-stock`。shell の1つの B-5 呼出し箇所へ subcommand を配列で組む。calibrated／verify／B／A／N_eval／rounds は driver 内部固定で、変更可能な CLI flags にしない。

**handshake**

- stock成立後、jobが `request-<a>.json` を atomic publication。次評価番号k、期待whiteboard、stock／過去評価の射影参照を含む。
- 親は実入力・prompt・各role出力を保存し、最後に `proposal-<a>.json` を renameして公開する。proposal本体の既存schemaに独自fieldを混ぜず、sidecarでslotと入力hashを束縛する。
- jobは15秒間隔、1待機操作につき45分上限でpollする。
- 評価後 `slot-<k>.json` を公開し、A-only rejectは別のproposal結果fileへ公開する。
- kだけをproposal名に使うと前処理reject後に同名再提出が必要になるため、**proposalはa、評価結果はk**とする。

45分timeoutは、候補処理前の通信／供給中断であることが確認できれば機械故障の同一操作retry。追加2回後は欠測。**LLMが実際に空出力を返した場合はA消費**であり、通信timeoutと混同しない。親の応答が無いだけで原因を断定できない場合は分類不能欠測とし、無料再生成しない。wait中のjob walltimeと候補実行中のwalltimeも区別する。

**TJ 更新位置**

- `TJ:65` の `STOCK_PINS` は維持。
- `TJ:176` の required に `B5_PINS` を追加。旧 `k2-proposal-required` は旧mode限定条件を含むpinに更新。
- `TJ:519` の検査は、旧 `p3_s4_loop` 呼出し数3を維持し、B-5呼出し1を別に数える。全driverがprebuild後であることを検査する。
- `TJ:548` のstage orderへ、B-5 env判定→K2判定→path解決、prebuild→B-5分岐→旧分岐を追加。
- `TJ:1866` 以降の既存 argv 完全一致 test は期待値を維持。
- B-5 LLM／random／sweep／block-stockがそれぞれ1起動、不正envがprebuild／trap前に拒否、旧経路へ落ちない実shell testを追加。

PBS指示行 `:5` の3時間pinは変えない。launcherがqsub CLIで上書きする。13465.nqsv の優先順位probeは親提示の既知証拠として引用し、本段の実測とは書かない。

**launcher**

`tools/pegasus/b5_contrast_launch.py:1（新設）`：

```python
def validate_submit_tree(repo: Path, expected_head: str) -> SubmitTree: ...
def build_job_environment(spec: PilotJob, tree: SubmitTree) -> dict[str, str]: ...
def qsub_argv(spec: PilotJob, tree: SubmitTree) -> list[str]: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

HEAD full OID、tracked clean、CCBench HEAD==`L.PIN`、CCBench clean、専用submit-tree、外部evidence rootを既存job契約に合わせて検査する。shell文字列を評価せず、argv listで `qsub` を呼ぶ。`-q gen_S -b 1 -l elapstim_req=08:00:00`、block-stockだけ03:00:00、`-o/-e`を明示する。`--dry-run` はenvとargvを表示し、qsubもdirectory作成も行わない。

`admission_registry.json:112` の既存job body登録は不変。ただし**新login launcherの登録は別件**である。既存submitter群と同じ `local-ok` の適切な分類を親が確認し、未実測を偽らず登録する。別job body案では、これに加えて新PBS bodyの登録、preambleの維持、契約test複製が必要になるため採らない。

# 10. β — 4 job の配置、53 session、費用測定

**P8：条件付き支持。** write-heavy の選択と8時間／3時間は親briefの既知測定に整合するが、完走保証ではない。

β launcherは次の4 jobだけを作る。

| job | 内部順序 | session上限 | walltime |
|---|---|---:|---|
| random | stock1 → 探索10 → score5 | 16 | 08:00:00 |
| sweep-matched | 同上 | 16 | 08:00:00 |
| LLM | stock1 → 親手番付き探索10 → score5 | 16 | 08:00:00 |
| block-stock | stock5 | 5 | 03:00:00 |

`3*(1+10+5)+5=53≤60` を定数と試走scheduleの両方で検査する。A=30でも pipeline投入は10まで。既定外workload／r／追加jobをβ launcherで生成しない。機械retryは同じ論理slotの物理試行であり別計上する。残り7枠を追加探索に使わない。

配置は **block-stock→random→sweep→LLMの直列実行**を推奨する。各job内もsession直列、verify fanoutなし。§5.2の直列測定に合わせ、試走が本走の均衡配置を再現するとは主張しない。親手番はLLM job開始から対応可能な時間帯に固定する。並列投入を採る場合は別node割当だけでは「同一条件」を保証できず、試走配置の逸脱として明記する。

1 sessionの暫定見積りは、

```text
build＋legacy verify＋5×(3秒trace＋約115秒verifier)
＋bench 5rep＋settle／準備 ≈ 12〜14分
```

16 sessionは約3.2〜3.7時間、LLM手番10×約5分を足して約4〜4.6時間。8時間はこれへの余裕であり、45分待機が毎回発生する最悪ケースを吸収する値ではない。登録の最大3 bench round、物理retry、前処理不通過も費用へ残す。

**計時の現物制約**

`P:639` の verify payloadにはverifier wallもrep番号もない。`P:2130` は各rep終了後に `verify_done` を出す。取得可能なWAL差分は以下である。

| 値 | 計算／出典 | 意味 |
|---|---|---|
| build区間 | `build_done.ts - build_start.ts` | trace／perf両buildと周辺処理 |
| legacy区間 | 最初の`verify_done.ts - build_done.ts` | trace＋verifier＋周辺処理 |
| performance rep区間 | 同attemptの隣接`verify_done.ts`差 | 前rep後処理＋次trace＋verifier等 |
| verify全区間 | 最終`verify_done.ts - build_done.ts` | 全verify passの区間 |
| bench本体 | `bench_done.payload.bench_wall_s` | `P:1409`のmonotonic計時。初回settle前部分は含まない |
| bench周辺込み | `bench_done.ts - 最終verify_done.ts` | settle等も含む |
| session全体 | B-5 adapterの開始／終了monotonic差 | condition gate等を含む |
| job | scheduler Elapse | prebuild・待機・失敗込み |

**これを純粋な verifier wall と呼んではならない。3秒を差し引いても純粋値にはならない。**

純粋値がβの必須成果なら、親裁定後にB-5限定の計時adapterを追加する案を推奨する。`P:484` の executor は既に `trace_runner`／`verifier_runner` seamを持つため、元callableへ同じ引数で一度だけ委譲する計時wrapperを使い、戻り値・例外をそのまま返す。pipelineファイル／WAL schemaは変更せず、B-5側のsidecarへ workload tag・rep ordinal・attempt・開始終了を記録する。ただし現行 `run_campaign` からこのseamを渡す口はないため、**runtime adapterの配線方法は段4で確定が必要**。無断のグローバルmonkeypatchをauthor既定案にはしない。

実測記録には各rep／session、正常・失敗・retry、build cache hit、bench rounds、session分布と最大、job Elapse総和、queue待ち、LLM手番時間・費用を含める。結果は `output/insights/2026-09-20/t2797-b5-contrast/` の既知結果台帳へ親が保存し、主標本へ入れない。発効commitは作らない。

# 11. Pin 閉包、test、変異 matrix

`test_official_perf_closure.py:495` の述語は、単なる文字列出現ではなく、`if/ifexp/while` 条件中の `perf`／`perf_*`／`*_perf`／`*_perf_*` 名等を検出する。たとえば `if len(tps) != perf.reps:` は該当する。`calibrated_perf(w)`を無条件に呼ぶだけなら該当しない。

A1は完成sourceへこの既存述語を適用し、該当すれば `_REVIEWED_PERF_FILES:44` にB-5 coreを追加する。本案は品質・current_perf検査を持つため追加対象になる可能性が高い。report／launcherも実際の述語で判定し、不要なentryを先回りで足さない。reportが該当する実装になった場合、そのinventory変更は統合担当A1に返し、並列編集しない。

| file | pinへの影響 |
|---|---|
| `L` | default identity／argv不変。run_campaign 2、layout 11、import閉包49を維持 |
| B-5 core新設 | direct run_campaignなし。perf inventoryは述語で判定 |
| B-5 report新設 | WAL writerなし。解析だけ |
| job body | TJのB-5 pin／mode分岐追加。旧PBS・STOCK pin維持 |
| launcher新設 | 新login entryのadmission分類が必要 |
| `test_campaign.py` | 本案では変更不要。callerを増やす代案なら更新必須 |
| namespace／B4 tests | 本案では期待値更新不要。失敗したらimport逆流等を先に調べる |
| `admission_registry.json` | 既存body登録は維持、新launcher登録のみ |
| README／insight | author編集外。親が契約と未成立事項を記録 |

`orchestrator/tests/test_b5_generator_contrast.py:1（新設）` に以下を置く。

| test群 | 正例／負例と変異 |
|---|---|
| 重み | 100／130一致、1000正整数、保存hash。1要素改変をkill |
| random | preimage bytes、既知vector、U=L−1／L、累積境界。区切り改変・`>=`反転をkill |
| sweep | 28点、hash順、同hashのv順、通常10評価、前処理失敗後の次点。数値順変異をkill |
| proposal | literal／value一致、3arm共通検疫。範囲外・式・余分な文をreject |
| identity | 同v別slot、stock／score分離、retry論理ID維持、既定preimage不変。slot key除去をkill |
| A/B | 空／schema／grammar／検疫はAのみ、投入後build／anomalyはB。消費点前後移動をkill |
| 停止 | `check_stop`を呼ぶと失敗するspy、A30／B10境界、性能・reverseによる停止なし |
| quality | reps欠落／unstable／settled false・Noneを個別に拒否。OR→AND等をkill |
| stock | certified＋STOCK＋正常品質のみ成功。非STOCK・skip・欠測を拒否 |
| 継承 | k−1件の完全一致、順序交換・他系列混入・delta非null・diagnosis不一致をreject |
| endpoint | 最大median、v昇順、slot昇順、固定後再計測。同値規則反転・固定前測定をkill |
| anomaly | 同w,vの横断失格、後発訂正、次点選び直し禁止 |
| retry | 証拠付き機械故障だけ＋2、同入力hash。品質赤retry・attempt4をkill |
| handshake | atomic公開、a/k分離、空出力とtimeout区別。timeoutを候補赤へ変更する変異をkill |
| session上限 | 53、B11／score6／block-stock6拒否、物理retry別計上 |
| 委譲 | bench_max_rounds=3、verify設定、receipt5引数、既存gateの呼出順 |

A2は `test_b5_generator_contrast_report.py`、A3は `test_b5_contrast_launch.py` とTJを所有する。reportには判定順の前後交換、fallback閾値2→3、Holm族縮小、標本CV→母CV、片baseline勝利の採用、pilotへ優越を返す変異を置く。TJにはB-5拒否削除、旧modeへの落下、driver二重起動、旧argv変更をkillするtestを置く。

新testファイルは既存TJ`:1927`同型の `__main__` harnessを持ち、subprocessは `PYTHONDONTWRITEBYTECODE=1`／Python `-B`。後段の実走は指定の `tools/run_tests.py` を通す。本段では **未実走・静的読解**であり、変異killも予測である。

# 12. Author 分割と受渡し条件

A1を先行させ、以下を受渡し契約として固定した後にA2／A3を並列化できる。

- `b5-generator-contrast-ledger/v1` と全eventの必須field。
- 論理slot／物理attempt／A／B／評価kの対応。
- 品質、機械故障、候補起因、分類不能、fallbackのenum。
- endpoint固定とanomaly訂正の表現。
- `run-series`／`run-block-stock`／入力継承検査のCLI。
- pilotとregistered reportの分離。

A1進行中にA2／A3がschemaを独自に補完する並列化は採らない。A2とA3の間にはコード編集依存がない。結合testの不具合は所有者へ戻し、同一fileを二者で直さない。

共通Tier0、admission、純verifier計時を未裁定のまま「authorが適当に補う」ことは不可。独立な純粋生成器／解析testの準備は進められるが、実機試走可能とする受入はそれらの処置確定後とする。

## 総括

| 前提 | 判定 |
|---|---|
| P1 slot identity | **条件付き支持**。別slotを分離。cohort／物理attempt、hash8衝突、再起動skipを別途扱う |
| P2 drive_iteration迂回 | **条件付き支持**。停止不適用に加え、B投入点・digest・系列台帳の継承が必要 |
| P3 WAL品質分類 | **支持**。COMMITとendpoint資格を分離。bench abortと系列欠測も保持 |
| P4 job内handshake | **条件付き支持**。実用的だが唯一ではない。a/k分離とtimeout分類が必要 |
| P5既存job body拡張 | **条件付き支持**。旧argv維持、TJ更新、新launcher登録が必要 |
| P6 Decimal100／130 | **条件付き支持**。全要素一致を受入条件にする。未実走 |
| P7 n=1は第4段で停止 | **反証**。第2／第3段が先行する。pilot専用の記述報告へ分離 |
| P8 write-heavy・8h／3h | **条件付き支持**。費用試走の暫定設定。完走・最悪待機吸収の保証なし |

**author所有file**

| 担当 | 所有file |
|---|---|
| A1 core | `orchestrator/campaign/b5_generator_contrast.py`、`orchestrator/campaign/p3_s4_loop.py`、`orchestrator/tests/test_b5_generator_contrast.py`、`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/tests/test_official_perf_closure.py` |
| A2 report | `orchestrator/campaign/b5_generator_contrast_report.py`、`orchestrator/tests/test_b5_generator_contrast_report.py` |
| A3 job／launcher | `tools/pegasus/p3_s4_loop_pegasus.sh`、`tools/pegasus/b5_contrast_launch.py`、`orchestrator/tests/test_p3_s4_loop_job_contract.py`、`orchestrator/tests/test_b5_contrast_launch.py` |
| 親／統合 | `admission_registry.json` の新launcher登録、README、insight、spool、必要な受入記録。authorはcommitしない |

**親裁定が必要な事項**

1. βでは共通Tier0未実装を明示した費用試走とするか、先にexactスモーク契約を追加するか。
2. 新LLM入口の正規build authorityと、random／sweepのgenerator receipt経路。関連正本を追加射影する。
3. 純verifier wallの計時adapterをどこで接続するか。WAL差分はtrace＋verify区間に限る。
4. sweepの前処理候補不通過後は11点目以降へ進む解釈の確定。
5. P7をpilot専用記述報告へ修正すること、試走の直列4job順序。
6. LLM失敗時のcurrent_perf欠測表現と、較正条件を反映した試走prompt／実入力。

本走認可、発効束、発効commitは本planの成果に含めない。