# [T-2418] 段 4 裁定 — 静的 backoff 右側 3 点の探索走

裁定時刻 2026-09-09 01:45 JST。裁定 inbox 再走査: main は `b57e35426` へ進み、D1836 (第 16 回索引) が
T-2418 = D1813 と再確認した。**D1813 を覆す新しい裁定は無い。**

## 0. 裁定前に親が現物で測った新事実 (段 1 brief に無かったもの)

先例 `t2266-tail` の**実走記録** (`output/insights/2026-09-07_t2266-tail-measurement/README.md`) を読み、
本 wave の投入可否に直結する 4 点を確認した。

1. **符号化の高域枝は既に正式系列が通っている。** `patches/silo-backoff-fixed.patch` の合成枝は
   `BACKOFF_FIXED/1000` で 4 分岐し、`>= 3000` の枝だけが `BACKOFF_FIXED - 2000` を物理値にする。
   凍結格子 `EXTENDED_SWEEP_US` の上端 1000 は `encode` で 3000 になるため、**この高域枝は
   認証済みの正式格子が既に発火させている。** 2000 / 4000 / 9999 は同じ枝を通る。
2. **`t2266-tail` の初回投入は 3 job とも 90 秒で関門に落ちた。** 原因は関門文脈での masstree
   `config.h` 不在 ([T-2320] の第 2 層欠陥)。**これは修正済み** (`2177b85aa`) で、3 回目の投入
   (job 979843〜845) が完走している。現行 main はこの修正を含む。
3. **`_T2266RepCapture.reps_for` の恒真テスト欠陥があった。** 凍結 view が list を tuple に、dict を
   `MappingProxyType` に変えるのに突合が `list == tuple` で行われ、必ず不一致になった。単体テストは
   view を list / dict で手組みしていたため実経路を一度も通しておらず、見逃した。**現行実装は
   `tuple(tps) if type(tps) in {list, tuple}` で正規化して修正済み。**
4. **時間予算は見積りでなく実績で言える。** 2 回目の投入は 02:36→02:47 の 11 分で 8 genome の
   build・verify (serializable, anomaly 0)・bench (5 rep, CV<0.3%)・commit まで完走した。
   本探索は 5 genome である。さらに **backoff を大きくすると throughput が落ち、3 秒枠あたりの
   transaction 数が減るため、律速である直列性検査はむしろ短くなる**
   (`verify-cost-dominates-not-build` の実測則)。`SWEEP_CAP_S=11700` に対して余裕は大きい。

## 1. 所見の裁定

### 相談 A (正しさ境界)

- **所見 1 (静的 binary SHA 検査が不完全でも通る): real / 採用 / scope 内。**
  `_require_distinct_static_binary_hashes` は静的でない `BuildResult` を無条件に読み飛ばし、
  確認できた amount が 2 未満なら成功する。先例 `t2266-tail` はこの穴を
  `_require_distinct_t2266_binary_hashes` (8 genome の完全性を要求) で塞いでいる。
  **探索走をその防壁なしで走らせることは、先例に対する正しさ検査の弱体化であり規律 2 に反する。**
  → `_require_distinct_t2418_binary_hashes(builds, ordered_genomes)` を新設し、
  ちょうど 5 genome、全 trace-disabled `BuildResult` の存在、genome 束縛、5 つの相異 sha256 を
  fail-closed で要求する。`_prebuild_backoff_binaries` へ
  `require_all_t2418_binary_hashes: bool = False` を足して呼ぶ。
  **既存 `require_all_binary_hashes` の式と t2266 の呼び方は 1 文字も変えない。**
  - 禁止の署名: `_require_distinct_t2418_binary_hashes(builds, ordered_genomes)` は、
    `len(ordered_genomes) != 5`、いずれかの `(canonical, False)` が
    `buildcache.BuildResult` でない、`built.trace is not False`、
    `built.genome.canonical() != canonical`、`bin_sha256` が完全 sha256 でない、
    2 つの canonical が同じ sha256、相異 sha256 が 5 個でない、のいずれかで `RuntimeError`。
  - 通る正例: 5 genome (`none` / `adaptive` / `fixed-2000us` / `fixed-4000us` / `fixed-9999us`) の
    trace-disabled build が 5 つの相異 sha256 を返す場合、例外を出さずに返る。

- **所見 2 (正値の runtime meaning が `unestablished`): real (記述として) / 不採用 (scope 外) /
  ただし文言は採用。** 上記 0-1 のとおり、高域枝は認証済みの正式格子 (1000 点) が既に通しており、
  正値の meaning witness が `unestablished` であることは**探索走に固有ではなく、既存 sweep 全体と
  同一の境界**である。T-2418 にだけ pointwise meaning gate を課すのは、正式系列より厳しくする
  scope 外の追加であり、その不在は弱体化ではない (規律 2 は緩んでいない)。
  → 実装しない。**brief と成果物の文言を「Python codec と wire 値の構成を実測した。
  runtime の物理量は既存 sweep と同じ枝を通るが、正値の意味 witness は既存同様 unestablished である」
  に狭める。** この境界は裁定パッケージへ載せてユーザーへ返す。

- **所見 3 (run-path テストが自己整合で恒真): real / 採用 / scope 内。**
  → 捕捉した各引数を独立 literal `[(0,-1),(1,-1),(1,4000),(1,6000),(1,11999)]` と exact 比較する。
  併せて選択された config の `run_kind` / `spec_slug` / `trial` も literal で照合する。

- **所見 4 (`p2_2.REPS` から期待値を作ると「5 反復」が恒真): real / 採用 / scope 内。**
  D1813 の「既存 sweep と同じ反復数」は本 wave の完了条件そのものなので、共有定数に追随する
  テストでは守れない。→ `p2_2.REPS == 5`、`p2_2.EXTIME == 3`、捕捉した `PerfConfig.reps == 5`、
  `PerfConfig.extime == 3`、各 report point の rep 数 5 を、**独立 literal** で pin する。

- **所見 5 (job が driver / patch の working bytes を HEAD に拘束しない): real / 不採用 (scope 外) /
  運用で緩和。** これは全 run kind (認証済み正式系列を含む) に共通する既存の性質であり、
  共有 job 本体へ新しい gate を足すことは引数が明示的に scope 外とした。
  → 運用で閉じる: **投入は wave worktree ではなく、wave の commit から作る専用の detached
  submit-tree から行い、投入から job 終端まで一切編集しない。** 投入時の HEAD と
  `git status --porcelain` が空であることを記録する。裁定パッケージへ載せる。

- **所見 6 (`EXTENDED_SWEEP_US` の consumer): real / プラン支持。** 変更なし。
- **所見 7 (`run_kind` の語彙が系統ごとに別): real / 一部採用。** T810 系への登録は不要という
  結論を採用する。**T2418 report が既存 T2266 consumer に拒否される負テストを 1 件足す**
  (「混ぜない」の境界を実際に発火させるため)。T810 側には触れない。
- **所見 8 (campaign identity だけでは「混ぜない」の十分条件でない): real / 実装は不採用
  (scope 外) / 文言は採用。** 提案された「既存正式 consumer に `run_kind=="extended"` を必須化」は
  正式系列の受理集合を変える変更で、本 wave の編集面の外である。現状 T2418 成果物が正式 consumer に
  最終的に拒否されることは相談 A が経路つきで確認した。→ brief の一般化を
  「identity の分離 + 専用 schema/stem + 機械可読な開示 + 既存 consumer の exact 照合の合わせ技」
  に書き換える。提案は裁定パッケージへ。
- **所見 9 / 10 / 11 (brief の一般化): real / 採用。** brief の文言を次のとおり訂正する。
  - 「3 点は構成できる」→「codec と wire 値の構成を実測した。gate 通過・build・runtime は未実測」
  - 「F660 は発火しない (実測)」→「main 側登録簿と guard 実装による静的確認。hook 発火の実測ではない」
  - 「反復数は自動的に同じ」→「配線は共有定数で同じ。literal 5 / 3 は独立テストで固定する」

### 相談 B (実効性・投入経路)

- **所見 1 (failure receipt は全失敗を覆わない): real / 採用 (運用)。**
  → 完了確認の必須証拠を「submission receipt + 各 job の stdout/stderr + `completion.json`」とする。
  コード変更なし。
- **所見 2 (walltime が見積り): real / 採用しつつ実績で置換。** 上記 0-4 の実績
  (8 genome / 11 分) と、backoff を上げると直列性検査が短くなるという実測則により、
  **見積りではなく先例実績に基づく比較**として記録する。pilot 分割はしない —
  3 job は独立ノードで同時に走り、条件を割って同時投入するのが既定 (1 ノード直列は却下)。
- **所見 3 (submitter が cwd を検査しない): real / 採用 (運用)。**
  → 投入は必ず submit-tree の root を cwd にして行う。`PBS_O_WORKDIR` が submit-tree root で
  あることを投入直後に receipt で確認する。コード変更なし (引数が gate 追加を scope 外とした)。
- **所見 4 (qsub 後に driver bytes が凍らない): real / 所見 A-5 と同型 / 同じ運用で閉じる。**
- **所見 5 (3 workload の fan-in が無い): real / 採用 (運用)。**
  → 3 本すべての `completion.json` の `run_kind` / `workload` / `campaign_id` / artifact hash を
  照合するまで完了扱いにしない。
- **所見 6 (report に反復契約が無い): real / 採用 / scope 内。**
  → `reps` / `extime_s` / `records` / `threads` を search_config・JSON top level・`.dat` provenance の
  3 か所へ同値で載せる。**D1813 の「同じ反復数」を成果物単体で確認できるようにするのが目的**なので
  本題の開示に含まれる。
- **所見 7 (orphan-hold の一般化): real / 採用 (文言 + 運用)。**
  → 「t810 の orphan-hold latch は干渉しない。直接 qsub の孤児化・部分投入は fan-in で見る」。
- **所見 8 (runbook の exploration root との語の衝突): real / 採用 (開示 1 field)。**
  D1813 の「探索」は**標本への帰属**の話であり、runbook の
  `IZANAGI_EXPLORATION_OUTPUT_ROOT` が指す**campaign layout の use class** とは別語である。
  探索走を exploration root へ移すと durability policy と declared use class が変わり、
  「既存 sweep と同じ枠」から外れる。→ **移さない。** 代わりに開示へ
  `declared_use_class: "official"` を 1 field 足し、2 つの「探索」を機械可読に区別する。
  runbook への追記は scope 外 (裁定パッケージへ)。

### 親が追加する不変条件 (先例の事故から)

- **F-恒真: report のテストを凍結 view の手組みで書かない。** `_T2418RepCapture` と
  `_load_t2418_report_points` のテストは、`artifact_admission` の凍結 view (list→tuple、
  dict→`MappingProxyType`) を**実際に通した**入力で検査する。list / dict を手で組んだ view で
  代用してはならない。先例はこの手組みのせいで `list == tuple` の必ず偽になる突合を
  見逃し、実走の report 段で 3 job が止まった。
- `orchestrator/tests/test_campaign.py` が
  `("orchestrator/campaign/backoff_extended_sweep.py", "campaign.loop.run_campaign"): 1` を pin して
  いるので、**`run_campaign` の呼び出しを増やさない** (T2418 も既存の 1 か所を通す)。

## 2. プラン v2 (確定)

段 2 プランをそのまま採り、次の 6 点を足す。

1. `_require_distinct_t2418_binary_hashes` を新設し、`_prebuild_backoff_binaries` の
   `require_all_t2418_binary_hashes` から呼ぶ (所見 A-1)。t2266 の経路は不変。
2. 開示 field に `declared_use_class` / `reps` / `extime_s` / `records` / `threads` を足す
   (所見 A-4・B-6・B-8)。値は `p2_2` から読み、テストは独立 literal で pin する。
3. run-path テストと report テストは独立 literal で exact 比較する (所見 A-3・A-4)。
4. report のテストは凍結 view を実際に通す (親の追加不変条件)。
5. T2418 report が T2266 consumer に拒否される負テストを 1 件足す (所見 A-7)。
6. `run_campaign` の呼び出しを増やさない。

**実装しないもの (裁定パッケージでユーザーへ返す):** 正値の pointwise meaning gate、
job 本体への working-tree 拘束、既存正式 consumer への `run_kind=="extended"` 必須化、
runbook の exploration-root 語の整理。

## 3. 変異事前登録 (DW-M01、実装前に固定)

各変異は 1 か所を変え、赤理由が 1 つに絞れることを実装後に確認する。

| # | 変異 | 期待して赤になる node |
|---|---|---|
| m01 | `T2418_REQUESTED_US` を `(2000, 4000, 9998)` にする | exact 定数 test |
| m02 | 静的点の flags を `encode_static_backoff_us` を通さず生値にする | 5-genome exact projection test |
| m03 | `T2418_CLAIM_SCOPE` を `T2266_CLAIM_SCOPE` と同値にする | disclosure exact test |
| m04 | `formal_stopping_criterion_status` を search_config から落とす | disclosure exact test |
| m05 | T2418 分岐で `t2266_config_for` を選ぶ | identity (slug/trial/scale) test |
| m06 | `_require_distinct_t2418_binary_hashes` を即 return にする | binary 完全性 test |
| m07 | `PerfConfig(reps=p2_2.REPS - 1)` にする | reps literal pin test |
| m08 | PBS `case` から `t2418-explore` を落とす | shell routing test |
| m09 | PBS finalize の T2418 commit 数を 8 にする | finalizer test |
| m10 | submit script の `B10_RUN_KIND` 転送条件から T2418 を外す | forwarding test |
| m11 | 未完走でも `materialize_t2418_report` を呼ぶ | CLI completion test |
| m12 | report stem を t2266 の stem と同じにする | artifact stem test |
| m13 | `reps_for` の `tuple(tps)` 正規化を外す | 凍結 view を通した report test |

m13 は先例が実走で踏んだ欠陥の再発検査であり、恒真な手組み view では殺せない。

## 4. 段 5 の所有と境界

実装子は 1 本 (Codex `role=author`、D95)。編集面は
`orchestrator/campaign/backoff_extended_sweep.py`、
`orchestrator/tests/test_backoff_extended_sweep.py`、
`tools/pegasus/b10_backoff_grid.sh`、`tools/pegasus/submit_b10_backoff_grid.sh` の 4 file だけ。
docs 編集と commit は行わない。
