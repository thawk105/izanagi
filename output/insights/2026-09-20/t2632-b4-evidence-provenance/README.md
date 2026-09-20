# [T-2632] B-4 の proposal・走行・参照点の対応証拠の出所 — 現存資料では 3 辺とも閉じない (裁定パッケージ)

- authority: none
- default_effect: no-state-change

可変状態の正本ではない。可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。
本書は wave `dev-wave-t2632-evidence-provenance` (branch `worktree-dev-wave-t2632-evidence-provenance`、起点 local main
`482f19b88`) の一次資料を凍結したものである。**実装面 (D95 決定 2) の差分は 0。** carrier・台帳・gate・検査は 1 つも作っていない。

- 実測日時: 2026-09-20 JST、機体 `pegasus02` (login node、読み取りのみ)。計算ノードへの dispatch は行っていない。
- 依頼: [T-2632] (P2、D2120 項 5 (3)) — B-4 の対応の各辺 (proposal ↔ 走行 ↔ 参照点) を、現存する WAL・receipt・campaign lock・insight の
  どれで結べるかを path と SHA-256 で示し、「閉じた」か「現存資料では閉じない (耐久 carrier の新設または D39 決定 3 の変更が要る)」かを
  結論する。§5 の 2 欄記入・床値・bootstrap 集合の定義・carrier や台帳の新設はしない。
- 前提: `output/insights/2026-09-16/t2632-b4-red-precursor-stock/README.md` (適格在庫 0 件)、
  `output/insights/2026-09-17/t2632-b4-s5-precheck/README.md` (§5 の 2 欄は今日記入できない)、D2100 (12 field は現行保存形式に出所なし)、
  D2120 項 5 (1)〜(3)。wave 開始後の裁定の再走査: D2150 項 2 (B-4 本走の site・PerfConfig・委任・環境契約の 4 項、2026-09-18) と
  D2172 (T-2632 の CLI 接続は AI の設計選択、2026-09-20) は本書の結論を変えない — 前者は §4.2 (3) の根拠を強める。

## 結論

**3 辺とも、現存資料では閉じない。** 閉じないのは carrier の不在 (辺 A)、object と祖先関係の定義不在 (辺 B)、集合の定義不在 (辺 C) で
あって、いずれも現物を探し足りないからではない。したがって **耐久 carrier の新設 (辺 A) と、参照点の object・祖先関係の定義 (辺 B) の
裁定が要る。** D39 決定 3 (whiteboard 5 field) の変更は必須ではない — 推奨する carrier は whiteboard の外に置く (§7)。付随して、
D2100 の呼び手が現行の `campaign.lock` (v2) を読めない欠陥を見つけた (§2.3、裁定 4)。

| 辺 | 両端 (本書の読み) | 現存資料で結べる範囲 | 判定 |
|---|---|---|---|
| A: proposal ↔ 走行 | 実行された proposal document の canonical sha256 (`p3_s4_loop.canonical_b4_proposal_sha256`、= registry の `initial_proposal_sha256`) ↔ その評価の WAL variant (`build_start.src_token` / `diffq-*` id) と whiteboard 行 (iteration) | **調査した 3 campaign と、§5 が選んだ base driver の precursor 保存経路には、proposal document を bytes で保持する harness carrier が無い** (3 campaign とも proposal は他機体の scratchpad path のみ、現存せず)。whiteboard 行 ↔ WAL variant の対応は base で **4 行 ↔ 3 variant** (順序で結ぶと誤対応)、sort で **iteration 2 の 1 行 ↔ 1 variant** (iteration 1 は dry-pass が counter だけ消費)、trigger だけ harness 書きの `reports/p3_s8a_trigger_loop_provenance.json` が iteration → variant を結ぶ。別系列 (trigger 軸の bounded supervisor と trigger driver の opt-in source-preimage) には proposal 保存と raw hash 束縛の先例があるが (§2.2)、base の precursor へは接続されておらず B-4 の canonical identity も持たない | **閉じない** |
| B: 走行 ↔ 参照点 | 赤 precursor の走行 ↔ 「祖先方向へ辿って最初に現れる certified snapshot の session-level throughput」の出所 (`reference_snapshot_hash` / `reference_receipt_hash`、`PerfConfig` と `env_tag` の一致) | 量そのもの (fitness_tps) は WAL `commit` / `bench_done` record にあり、record の canonical JSON の sha256 (`wal:<sha256>`、`layer3_report` の `source_ref` と現物で同じ値) で名指せる。しかし **「snapshot」「receipt」に当たる object を作る producer も、それらを hash する定義も、照合した範囲 (`orchestrator/campaign/` の module 名と B-4 参照 field の構築点) には無い** (T-2102 が同じ不在を確認)。**3 campaign の WAL には `parent` / `ancestor` / `iteration` の文字列が無い。loop_state は `iteration` と行順を持つが、それを proposal の祖先関係と定める契約は無く、base では行 → WAL attempt の束縛も無い** (辺 A)。加えて現物 3 campaign は `env_tag=linux-baremetal`・`default_perf()` (records 100000 / threads 4 / extime 1 / reps 2) で走っており、Pegasus 較正値で記入される §5 の `PerfConfig` / `env_tag` とは一致し得ない | **閉じない** |
| C: proposal ↔ 参照点 | 初期 proposal の bootstrap 所属 (`bootstrap_member`) と、その precursor に固定した参照点の対 | A と B の合成。bootstrap 集合は D2120 項 5 (2) で「非空入力が出るまで定義しない」と裁定済みで、集合が無い以上、所属も参照点との対も定義できない。publication 内側の 4 者束縛 (事前登録 §7.2 追記、`assemble_b4_raw_analysis`) は「宣言値の転記の一貫性」までで、宣言値が実 campaign の proposal から計算されたことは示さない (同 module の非保証) | **閉じない (定義で)** |

**空虚な真を結論にしない。** 現物 7 行はすべて `success` で赤 precursor は 0 件なので、「現存する precursor の辺が閉じない」という命題は
空虚に真である。本書が確定したのは、**現行保存形式で新しく走った campaign から赤 precursor が 1 件出ても、その 3 辺を現存の carrier 種別
(WAL・loop_state・campaign.lock・opt-in journal・insight) では harness の記録として結べない**ことである。

## 1. 対応の 3 辺と両端の object (本書の読み)

事前登録 §5.1.1 (適格性述語・共通参照点) と `p3_b4_analysis_ledgers.B4ScheduledAttemptInput` (17 field。うち D2100 が現行保存形式に出所なしと
分類したのが 12 field) から、辺の両端を次に置く。

| object | 定義の所在 | 現物での実体 |
|---|---|---|
| proposal | `--run-iteration` に渡す proposal JSON。B-4 の identity は `p3_s4_loop.canonical_b4_proposal_sha256` (receipt sha256 key を除いた canonical JSON の sha256)。registry の `initial_proposal_sha256` はこれと exact 比較される (`require_b4_proposal_registry_binding`) | 3 campaign では他機体の scratchpad path のみ (現存せず)。K2 3 巡目では insight に写し (§3.3) |
| 走行 (attempt) | 1 iteration の評価。WAL では variant id (`pipeline.variant_id` = genome + `src_token`、reject は `diffq-<sha256[:12]>` = genome + 提案コード) と `build_start.build_attempt_id` (現行、乱数 token)。checkpoint では whiteboard 行 (`{iteration, direction, magnitude, result, delta_pct}`、D39 決定 3) | 全 campaign に WAL と loop_state がある |
| 参照点 | 「祖先方向へ辿って最初に現れる certified snapshot の session-level throughput」(§5.1.1)。出所は `reference_snapshot_hash` と `reference_receipt_hash`、`PerfConfig` と `env_tag` の一致で特定 | 量は WAL `commit.fitness_tps` / `bench_done.median_tps` にしか無い (T-2102)。snapshot / receipt という object は無い |

赤 precursor の WAL 形 (`record_diff_reject`): `build_start` (`src_token=""`、`build_attempt_id`) → `abort` (`reason=diff-quarantine`、
`diff_quarantine` digest)。variant id の preimage に提案コード (`implementation`) が入るので **コード片には束縛される**が、proposal document
(planner / coder / prior_critic_reverse を含む JSON) の canonical hash には束縛されない。

## 2. 現物の棚卸し (path と sha256)

### 2.1 tracked な合成ループ campaign 3 件 (`git ls-files` で `loop_state.json` を持つ全 campaign)

| campaign | file | bytes | sha256 |
|---|---|---|---|
| base `p3-s4-loop-s4-autonomous-0b53a387` (commit `d862da319`、2026-07-09) | `campaign.lock` | 537 | `0b53a3876589a61ae35b318237751015acebb3761e612e4374f9944ffca7f7c9` |
| | `loop_state.json` | 692 | `616a5a1d83a7881c90d37469f1fa69a117d72fb5cd6f54f18ff031b63f34279f` |
| | `runs/wal.jsonl` | 6,687 | `2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611` |
| | `s4_loop_digest.txt` | 1,674 | `0eee68f16843e40abec9300a697dd6ffdfe45bc8c52aa5e8cc5a5879b1912e1f` |
| sort `p3-s5-sort-loop-s5-sort-autonomous-3be89e0d` (commit `c6e7fba6d`、2026-07-10) | `campaign.lock` | 629 | `3be89e0ddad8e8b2b37d35168c49affe7889ea580831973dc0d6d9706aaa4f97` |
| | `loop_state.json` | 255 | `f89b8b7c1d46f17dd16b25c68069b46f69e9dd638dd9026e7a8e8d3ce1ec6cd8` |
| | `runs/wal.jsonl` | 2,513 | `b901f23a502e4d3843454de807ca01666c145ee7d9d424a957bb366ef3e793a5` |
| | `s5_sort_loop_digest.txt` | 1,291 | `aed7e85bda1db38b25454c2fbaf145b36ac253d55d16c0370d6af4b2ea624a3f` |
| trigger `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5` (commit `d485a48dc`、2026-07-12) | `campaign.lock` | 672 | `3f72ecd58a6df4018d136bcbb8abb276114ba8d302c64aaf792c473ae4b1de0c` |
| | `loop_state.json` | 401 | `18d5e40bd4b4c8e6a4d09b8d4ac4b94c0ffb173b79092dfc7a6abe7e1aa2c79d` |
| | `runs/wal.jsonl` | 5,060 | `a539648d29afce9be036eba519b53f21fd1f8e1fb7bfe24549f4ec3ceac31ea3` |
| | `reports/p3_s8a_trigger_loop_provenance.json` | 3,528 | `cfbcd1257ac96ff9500f50993938b9f99dceaa36e3e2ca51dea387ff0f72a056` |
| | `reports/layer3_report.json` | 10,699 | `3f97e7694e614bb51f2d7bde9824fea9b79c5bc19614427a0ebed9a927031320` |
| | `s8a_trigger_loop_digest.txt` | 1,506 | `3825b39824096f97a61d95d89a37bd7d9616e5d40022a1e8182d7c66ce532e7e` |

`loop_state.json` の 3 件は前 wave (2026-09-16) の sha256 と一致する。この 3 campaign の他に proposal を運びうる file は無い
(`agent_outputs.jsonl` は tracked 0 件・`output/` 配下 0 件、`variants/` `spec/` dir も無い)。

### 2.2 現行保存形式が新規走行で残す carrier (code から)

| carrier | 書き手 | 何を持つか | 辺 A に効くか |
|---|---|---|---|
| `loop_state.json` の whiteboard | harness (`project_whiteboard`) | `{iteration, direction, magnitude, result, delta_pct}` の 5 field だけ (D39 決定 3 / D1846) | variant id も proposal hash も無い。dry-pass (`--no-build`) は counter を消費して行を残さない。重複提案 (`_resolve_duplicate`) は前 iteration の WAL を再利用して行だけ足す (docstring: 「whiteboard/checkpoint は id を持たず分類だけが汚染」) |
| `runs/wal.jsonl` | `pipeline.evaluate` / `record_diff_reject` | variant・stage・env_tag・ts・payload。`build_start` に `genome` / `src_token` / `build_attempt_id` (現行) / `build_admission` (現行、`coder-authored` class は `input_sha256: null`) | iteration も proposal hash も無い (`iteration` / `proposal` / `attempt_id` / `parent` / `ancestor` / `snapshot` / `receipt` の文字列出現は 3 campaign の WAL で 0) |
| `campaign.lock` | harness | identity の preimage (現行は `authority` / `identity_preimage` / `schema_version`) | 走行にも proposal にも触れない |
| `reports/p3_s8a_trigger_loop_provenance.json` | **trigger driver の harness** (`p3_s4_loop_trigger_gating._append_provenance_entry`、iteration ごと merge 追記、`save_loop_state` より前) | `entries[iteration] = {proposal_path, auditor_diff_digest, outcome, variant, build_attempt_id (現行), trigger_gate_binding_commitment (現行)}` | iteration → variant を harness が結ぶ。**proposal は path だけ** (bytes / hash は無い)。`auditor_diff_digest` は auditor が審査した working_diff の sha256 (`auditor_gate.py`) でコード片の hash。**base / sort driver にはこの side channel が無い** |
| `runs/agent_outputs.jsonl` (opt-in journal) | `--agent-inputs` (live、評価前、`variant: None`) または `--record-agent-output` (ingested、事後、`--agent-variant` / `--agent-wal-ref` は WAL 実在を検査) | `provenance.source_sha256` (= 指定 file の raw bytes sha256)、`output` (role の出力 object)、`refs` (`wal:<canonical sha256>`) | proposal file の raw bytes と variant / WAL record を結べる。ただし **opt-in・呼び手の申告** (module docstring: 「not proof of delivery」)、live 経路は variant を持たない、B-4 identity (canonical hash) は記録しない。production での実例は K2 手動 loop (§4.3) |
| `reports/layer3_report.json` | `layer3_report` generator | `runs[].variant` と `source_ref = wal:<sha256>` (bench_done record の canonical hash) | 走行 ↔ WAL record の束縛。proposal には触れない (辺 B の record 名指しに使える形) |
| `<run_root>/proposals/<workload>.g<N>.json` (段 8c bounded supervisor、trigger 軸限定) | `p3_autonomous_workload_trial.py` (T-178 の `silo-backoff-trigger-gating` 専用 supervisor。自ら「generic evolution daemon ではない」と書く) | proposal document (planner / coder / auditor / prior_critic_reverse / descriptor_sha256) を保存し、generation record に path・sha256 と harness outcome を持つ。`autonomous_trial_completeness.py` が proposal・provenance・`build_attempt_id`・WAL start・source artifact を照合する | **段 6 レビューが見つけた先例 (親の初稿では欠落)。** trigger 系列の運用記録 (`output/README.md`: 「探索の運用記録であって正式 proof chain ではない」) で、base の precursor には接続されていない。B-4 の canonical identity (`canonical_b4_proposal_sha256`) は持たない |
| `source-bindings/<proposal raw sha256>.preimage` (trigger driver の opt-in) | `p3_s4_loop_trigger_gating._write_source_preimage_artifact` (`require_source_preimage_artifact` 時) | proposal file の **raw bytes sha256 を名前**にした、materialized source の digest preimage (内容は proposal JSON ではない) | 同レビューが見つけた先例。proposal raw hash ↔ source preimage の束縛で、検疫拒否・dry-pass より後の経路。base driver には無い |
| insight (`output/insights/**`) | 親 (人手) | 任意 | 親が写した proposal と run summary (K2 3 巡目) は path + sha256 で結べるが、harness の記録ではなく親の申告 |

### 2.3 消費側

`p3_b4_prerun_caller` (D2100) が読むのは checkpoint の whiteboard と `campaign.lock` だけで、WAL・provenance report・journal は読まない。
`_MISSING_SOURCES` の 12 件は保存形式の既知の制限に基づく静的分類であり、本書はそれを現物で裏付けた (§6)。

**付随して見つけた欠陥 (実装せず §7 の裁定 4 へ):** 同 caller は driver を `lock.get("trial")` (top-level key) で判定するが、現行の
`campaign.lock` は `campaign-lock/v2` (`{authority, identity_preimage, schema_version}`、`trial` は `identity_preimage` の JSON 文字列の
内側) であり、K2 3 巡目の lock (`f1ab4966ec7fb702c477ae022b0652f4478868191623e884c75cf989987f9ce4`) では `trial` が top-level に無い。
したがって現行形式の campaign は `unknown trial: None` → `CampaignInputUnreadable` になり、**不足報告にも空 batch の発行器到達にも至らない**。
tracked 3 campaign (v1 形、top-level `trial` あり) でだけ D2100 の経路が通る。decoder は既存 (`orchestrator/campaign/campaign_lock.py` の `decode_campaign_lock`。`wal.py` が `campaign_lock_codec` の別名で import、
`wal._campaign_lock_value` が使う)。本 wave では test も caller も触っていない。

## 3. 辺 A: proposal ↔ 走行 — 閉じない

### 3.1 whiteboard 行 7 件の対応表

| campaign | whiteboard 行 (iteration / result) | WAL variant (build_start の ts 順) | 結ぶ資料 | 判定 |
|---|---|---|---|---|
| base | it 1 / success (decrease, small) | `20bbb4c1a855` (FIXED=40、`src_token=6857284…`、2026-07-09 09:48 JST) | 順序のみ。archive worklog `docs/archive/worklog-phase3-0702-0713.md` (2026-07-09 (3)) が「iteration2 が iteration1 の WAL を再利用」と散文で記す | 順序では結べるが記録ではない |
| base | it 2 / success (decrease, medium) | **無し** (重複提案 → `_resolve_duplicate` が it 1 の WAL を再利用) | 同 archive の散文だけ | **順序で結ぶと `27d1d016998e` (FIXED=30) に誤対応** |
| base | it 3 / success (decrease, medium) | `27d1d016998e` (FIXED=30、`src_token=2040cffa…`) | 同上 | 散文の消去法 |
| base | it 4 / success (decrease, medium) | `dad58f9f9000` (FIXED=40、`src_token=cc549892…`、it 1 と genome 同一で src_token 別) | 同上 | 散文の消去法 |
| sort | it 2 / success (increase, medium) | `aa32126d769f` (SORT_VARIANT=1、`src_token=572ff2d1…`) | 同 archive (2026-07-10 (2)): 「リハーサル (dry-pass) が iteration カウンタを 1 消費 … iteration=2」 | whiteboard の it 1 は存在せず、番号は attempt の identity にならない |
| trigger | it 1 / success (increase, medium) | `e1785940172e` (`src_token=d4239293…`) | `reports/p3_s8a_trigger_loop_provenance.json` `entries["1"]` (harness 書き) | iteration → variant は harness が結ぶ。proposal は `/home/tanab/tmp/claude-1025/.../scratchpad/prop.json` (現存せず) |
| trigger | it 2 / success (increase, small) | `ca5206c3dac5` (`src_token=1d116d99…`) | 同 `entries["2"]` | 同上 (`prop_it2.json`、現存せず) |

whiteboard の key 集合は 3 campaign とも `{delta_pct, direction, iteration, magnitude, result}` で、variant / hash / attempt id を持つ行は 0。
base は **4 行 ↔ 3 variant** で全単射でなく、順序で結ぶ試み (`verbatim/parent-edge-probe.json` の `order_join_attempt`) は it 2 を
`27d1d016998e` に、it 4 を空に写す — archive の記述 (it 2 は it 1 の WAL を再利用) と WAL の ts 順を合わせると、it 2 が空で it 3・4 が後続の
2 variant (`27d1d016998e`・`dad58f9f9000`) に当たると**推定**される。これは記録ではなく推論である。
**同じ genome (FIXED=40) が `src_token` 違いで 2 variant (`20bbb4c1a855` / `dad58f9f9000`) になっている**ので、genome からの逆引きでも
一意にならない。

### 3.2 proposal 側

3 campaign とも proposal document は保存されていない。trigger の provenance report が持つ `proposal_path` 2 件は他機体
(`/home/tanab/...`) の scratchpad で、本機体に現存しない (`proposal_paths_exist_now = {1: false, 2: false}`)。
`auditor_diff_digest` (`15ed554a…` / `db820e59…`) は working_diff の sha256 であって proposal JSON の canonical hash ではなく、
逆算もできない。したがって **`initial_proposal_sha256` に相当する値は 7 行のどれについても現存資料から計算できない。**

### 3.3 現行形式での実例 — K2 手動 loop 3 巡目 (2026-09-19、Pegasus、repo 外)

opt-in journal と insight の写しで辺 A をどこまで結べるかの、親が観測できた最良例。campaign dir は repo 外
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-round3/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/`) で、
`campaign-artifacts-cannot-enter-repo` により repo へは複製されていない。**下表の campaign 側 4 file は親が 2026-09-20 19:10〜19:11 JST に
読んで sha256 を記録した観測である。同 job root の `submit-tree/` は 19:26:40 JST (dir mtime) に消え、19:33 JST に不在を確認した (別 wave が
同 job root を稼働中で、主体は特定しない)。段 6 の独立レビュー (19:24〜19:32 JST) は指定 path を不在として再確認できなかった。** repo 外の
campaign 成果物は 1 時間の内に消えうる — これ自体が「journal / job dir は耐久 carrier ではない」の実例である。insight 側 3 file は tracked で、
レビューが sha256 を独立再計算し一致した。

| 資料 | path | sha256 | 何を結ぶか |
|---|---|---|---|
| journal | `<campaign>/runs/agent_outputs.jsonl` (3 行) | `66d3e737c1e4bb2e651805d97d40e047093f85273642464d24b23b797813efce` | `planner_proposed` / `coder_proposed` / `critic_attributed` の 3 envelope。すべて `mode=ingested` (事後)、`variant=002642c7ac96`、`refs` = WAL 5 record の canonical hash (全件 WAL に解決)。`source_sha256` = `verbatim/planner-4.json` (`59122afb…`)、`verbatim/coder-4.json` (`49ca42a1…`)、`verbatim/critic-3.md` (`5cd8f518…`) の raw bytes |
| WAL | `<campaign>/runs/wal.jsonl` (5 record) | `eb8927b78129a8700ceec9c30a13df1fa7287b1c5520f6cf19ae48b191aa4daa` | variant `002642c7ac96`、`env_tag=pegasus`、`build_attempt_id=b83c62a8…`、`build_admission.input_sha256=null` |
| checkpoint | `<campaign>/loop_state.json` | `917ba3d3b34df45eff85aa536999dd30b895256fdefaef68214431ae88a1f950` | whiteboard 1 行 (it 1 / success)。id 無し |
| insight | `output/insights/2026-09-19/k2-loop-round3/materials/proposal-4.json` | `bd3e5fd2110cc75313a8692f9c6e4c3ba4b20aa5050f0c99a50ab049ea12d53f` | `--run-iteration` に渡した proposal file の写し (親の申告)。canonical B-4 hash = `c9b2595a90fc30b0e030e26379cbdfa2dd7d80b7fd35d3d3dee9cc2e55d56f55` (本書で計算) |
| insight | `output/insights/2026-09-19/k2-loop-round3/materials/run-summary.json` | `245ebeb314b44c95a6c0d68dcb915820508de099b3005ac9d35f7f9993306b18` | variant・`wal_refs` 5 件・whiteboard・verify / bench / commit の写し |
| insight | `output/insights/2026-09-19/k2-loop-round3/materials/wal-refs.json` | `c03aa8a6faea7dceed455bce08b50802d4c0bfb7e6de36552886c034d1c782ad` | 同 5 件の `wal:` ref |

読み: (1) journal は planner 出力 / coder 出力の **raw file** を variant と WAL record に結ぶが、実行された **proposal file** (planner + coder +
`prior_critic_reverse` を束ねた別 file) の hash は持たない — `source_sha256` 2 件はどちらも `proposal-4.json` の raw sha256 と一致しない
(`ao_source_sha256_matches_insight_proposal = [false, false]`、親の観測)。(2) canonical B-4 hash (`c9b2595a…`) は、親が読んだ campaign 側
4 file (lock・loop_state・WAL・journal) には現れない (本書が insight の写しから計算した値)。campaign dir の他の file (`reports/` `spec/`
`variants/` `insights/`、受領証) は全域検索する前に dir が消えたので、それらに無いとは言わない。(3) 3 envelope とも `mode=ingested` で、
harness が評価時に書いた記録ではない。したがって
**現行形式の最良例でも、B-4 が要求する identity (canonical hash) と走行の束縛は harness の記録として残らない。** 親が insight に写す形は
「現存資料 (insight)」として辺 A を path + sha256 で名指せるが、写しが harness の読んだ bytes と同一であることは親の申告である。

### 3.4 判定

**閉じない。** 現存資料で結べるのは (a) trigger driver の iteration → variant (harness)、(b) K2 3 巡目の raw role 出力 → variant (opt-in journal、
事後申告、実物は 19:26 JST 以後不在)、(c) 親が insight に写した proposal → run summary (申告)、(d) trigger 系列の supervisor による proposal
document 保存と source-preimage の raw hash 束縛 (§2.2、base 未接続・canonical identity なし) まで。§5 が選んだ base driver
(`silo-backoff-magnitude`) には (a)(d) が無く、(b)(c) は harness の記録ではない。**不在断定はこの範囲 (調査した 3 campaign と base driver の
precursor 保存経路) に限る。** 不足は「先例の無い carrier の新設」ではなく、**base への接続と B-4 canonical identity の束縛の追加**である
(§7 の裁定 1)。

## 4. 辺 B: 走行 ↔ 参照点 — 閉じない

### 4.1 量の所在 (現存)

certified な走行の session-level throughput は WAL `commit.fitness_tps` と `bench_done.median_tps` / `tps[]` にあり (T-2102)、各 record は
canonical JSON の sha256 `wal:<sha256>` で一意に名指せる。**実装は 2 つある** — `agent_outputs.canonical_bytes` (`sort_keys` /
`ensure_ascii=False` / `separators=(",", ":")` / **`allow_nan=False`**) と `layer3_report._canonical_bytes` (同じ引数で `allow_nan` 指定なし)。
`layer3_report.canonical_record_ref` が `agent_outputs` の関数を呼ぶのは `ao` 経路だけで、`wal` 経路は独自実装を使う。現物の有限 JSON では
両者の bytes は同一で、本書の ref は `agent_outputs.canonical_sha256(vars(record))` で計算し、trigger の `layer3_report.runs[].source_ref` と
値が一致した (レビューが独立再計算)。非有限値の受理域だけが異なる。
3 campaign の certified 6 variant について (`verbatim/parent-edge-probe.json` の `reference_candidates`):

| campaign | variant | fitness_tps | env_tag | `bench_done.run_cmd` から読める PerfConfig | commit record の ref |
|---|---|---|---|---|---|
| base | `20bbb4c1a855` | 491,796.5 | linux-baremetal | threads 4 / records 100000 / extime 1 / clocks 1800 / rratio 50 / skew 0.9 / rmw false | `wal:9bce3bc47e9d1b603cf39733df061bb41fe8e4704234d239c0f60751cb10d989` |
| base | `27d1d016998e` | 525,721.5 | linux-baremetal | 同上 | `wal:98af80643f35475046303f0abedfd9dd4e0e2ced77eb353f17181fe888975e60` |
| base | `dad58f9f9000` | 487,088.5 | linux-baremetal | 同上 | `wal:6e598a426dee8bccd7ab65d7f0dc3b522323b064f4b7e9a56c582bc2742d0d47` |
| sort | `aa32126d769f` | 274,871.5 | linux-baremetal | 同上 | `wal:d3c74339da9f706053a6eaddcd1c0ab9290628495a5abb56526dae08744bcb98` |
| trigger | `e1785940172e` | 275,614.5 | linux-baremetal | 同上 | `wal:4f40b669b157d87ee69a2c7cf2995ae9f1700911513ab7147ac3f9983c111a1e` |
| trigger | `ca5206c3dac5` | 276,472.0 | linux-baremetal | 同上 | `wal:2d68cc8a15d25fe1bc5cd1d3af27fa8a76ba1bfdd242217442a437d371ff05fa` |

trigger の `layer3_report.json` の `runs[].source_ref` 2 件は、本書が再計算した `bench_done` record の ref と一致する
(`source_refs_match_bench_wal_refs = true`)。**この ref 形は現存し、消費側 (layer3) の先例もある。**

### 4.2 閉じない理由 3 つ

1. **object の不在。** `reference_snapshot_hash` / `reference_receipt_hash` が何の bytes の sha256 かを定める producer・定義が、照合した
   範囲に無い。根拠は module 名だけではない — `orchestrator/campaign/` に `snapshot` / `receipt` を名に持つ B-4 用 module も
   `throughput receipt` 型も無く、加えて B-4 参照 field (`reference_*`) の構築点を辿ると実祖先から構成する production producer は無く、
   事前登録 consumer の自己検査用 fixture だけである (T-2102 と同じ結論。レビューが独立に照合)。WAL record の canonical hash を
   receipt hash と**読む**ことはできるが、それは新しい定義 (裁定) であって現存資料の読み出しではない。
2. **祖先関係の不在。** 「precursor から祖先方向へ辿って最初に現れる certified」を決めるには precursor と各 certified の系譜が要る。
   3 campaign の WAL には `parent` / `ancestor` / `iteration` の文字列が無い (親の probe は WAL 文字列だけを検索した。loop_state には
   `iteration` が top-level と whiteboard 行にあり、文字列出現は base 5 / sort 2 / trigger 3 — レビューの再計数)。loop_state の `iteration` と
   行順は**順序の情報**ではあるが、それを proposal の祖先関係と定める契約は事前登録にも code にも無く、重複提案 (§3.1) は新しい評価を
   作らないので行順と評価の系譜は同一でない。行順で読むにしても辺 A の行 ↔ variant 対応が要る — それが base で壊れている。
   つまり不足は「順序情報そのものの欠落」ではなく「既存の順序の意味と、行 → attempt の対応の未確定」である。
3. **一致条件の不成立。** §5.1.1 は receipt を `PerfConfig` と `env_tag` の一致で特定する。`PerfConfig` (`pipeline.PerfConfig`) は
   `records / threads / workload / extime / reps` の 5 field で、`bench_done.run_cmd` から読めるのは threads・records・extime と workload の
   3 key (rratio / skew / rmw) だけである — **`reps` は宣言値として現れず (`tps[]` の長さから推定できるだけ)、`ycsb_max_ope` は run_cmd に
   無い。** 現物 6 variant は `env_tag=linux-baremetal`・`default_perf()` の動作点 (records 100000 / threads 4 / extime 1 / reps 2) であり、
   §5 の 2 欄が Pegasus 較正値 (records 1M / 1M / 2M、threads 48、`env_tag=pegasus`) で記入されれば一致し得ない。つまり現物の certified 行は、
   B-4 本走の参照点には**なれない**ことが今日の時点で確定している — D2150 項 2 (2026-09-18) が B-4 本走の site を Pegasus 計算ノード・
   tag `pegasus`、`PerfConfig` を較正 3 件の出力値 + 復元値 + 選択値 (reps 候補 5 は候補のまま) で確定している (記入は D1483 の順序後)。

### 4.3 判定

**閉じない。** 参照点の object (何を snapshot / receipt と呼び何の bytes を hash するか) と祖先関係 (同 campaign の whiteboard 順序か、
別の系譜か) の**定義**が先に要り、定義後に carrier (辺 A と同じ side channel に `reference` 欄を持たせるのが自然) が要る (§7 の裁定 2)。

## 5. 辺 C: proposal ↔ 参照点 — 閉じない (定義で)

`bootstrap_member` と `reference_*` の対は A と B の合成であり、両方が閉じない以上閉じない。加えて bootstrap 集合そのものが
D2120 項 5 (2) で「実際に非空入力 (適格な赤 precursor ≥ 1) を扱う時点で裁定し、今は定義しない」と裁定されているので、所属の真偽は
今日は定義できない。publication の内側では block id・precursor hash・on / off receipt の 4 者が束縛されている (事前登録 §7.2 追記) が、
それは registry の宣言値の転記の一貫性までで、宣言値の出所を示さない — 本書の 3 辺はまさにその「出所」である。

## 6. D2100 の 12 field との対応 (静的分類の現物裏付け)

| field | D2100 の不足理由 | 本書の現物 | 辺 |
|---|---|---|---|
| `attempt_id` | whiteboard iteration → B-4 attempt identity の写像が無い | whiteboard に id 無し。base 4 行 ↔ 3 variant、sort it 1 不在。trigger だけ side channel | A |
| `block_id` | precursor を block へ割る artifact が無い | 同上 + manifest 不在 | A / C |
| `digest_red_classes` | precursor を WAL digest 証拠へ結ぶ checkpoint key が無い | 赤 precursor の WAL 形は `diffq-*` + `abort.diff_quarantine` にあるが、行 → variant の写像が無い | A |
| `workload` / `calibrated_workload_member` | 校正済み workload の束縛が無い | §5 未記入 (前 wave)。現物は `default_perf()` の rratio 50 | B |
| `initial_proposal_sha256` | whiteboard と WAL の genome / src_token は proposal document を保持しない | 3 campaign に proposal 無し。K2 3 巡目でも canonical hash は campaign dir に無い (§3.3) | A |
| `bootstrap_member` | 事前固定した集合が無い | D2120 項 5 (2) | C |
| `reference_tps` / `reference_snapshot_hash` / `reference_receipt_hash` / `reference_is_unique` | 一意に選ばれた祖先 receipt / snapshot が束縛されていない | 量は WAL にあり ref で名指せる。object と祖先の定義が無い。env_tag / PerfConfig は一致し得ない | B |
| `arm_digest_received` | attempt ごとの digest 受領 / 非受領の記録が無い | WAL・loop_state に無し。`s4_loop_digest.txt` は campaign 単位で上書き (per-attempt でない) | A |

## 7. 裁定パッケージ (ユーザーへ返す。本 wave では何も実装しない)

**既裁定で閉じる (返さない):** 少数の赤の扱いは記述報告まで (D1986 項 4)。母集合を作るための追加基盤は採らない (D1936 項 8)。
`bootstrap_member` を batch 所属で真にしない (D2100)。bootstrap 集合は非空入力が出るまで定義しない (D2120 項 5 (2))。§5 の 2 欄の
順序 (D1483)。

**返す:**

1. **辺 A の耐久 carrier。** 択一 —
   - (α) **base driver に、trigger driver と同型の harness 書き side channel を足す** (`reports/<driver>_provenance.json`、iteration ごと、
     `save_loop_state` より前)。持たせる最小 field = `iteration`、`variant` (certified / fail は `pipeline.variant_id`、reject は `diffq-*`)、
     `build_attempt_id`、`initial_proposal_sha256` (= `canonical_b4_proposal_sha256(document)`、harness が読んだ bytes から計算)、
     `wal_refs` (その attempt の record の canonical hash)、`outcome`。**whiteboard の 5 field は不変で、D39 決定 3 に触れない**
     (planner へ射影する `project_whiteboard` は side channel を読まない)。重複解決 (`_resolve_duplicate`) と dry-pass も行を残す
     (§7.1 の全件報告と整合)。
   - (β) D39 決定 3 を改訂し、`WhiteboardEntry` に不透明な `variant` / `proposal_sha256` を足す。planner 射影から除けば structural
     inference の経路は増えないが、凍結された型 (D1846、5 field) と、その型を読む consumer が動く (`p3_b4_prerun_caller` 自身は
     `{iteration, result}` の部分集合検査なので壊れないが、`project_whiteboard` の射影規則は D39 決定 3 の改訂として書き直しになる)。
   - (γ) opt-in journal (`--agent-inputs`) を B-4 marker 走行で必須化し、live envelope に canonical hash と variant を足す。live 経路は
     評価前に書くため variant を持てず、2 record transaction でない (docstring) ので、単独では (α) の代替にならない。

   - (δ) trigger 系列の先例 (§2.2: bounded supervisor の `proposals/` 保存 + `autonomous_trial_completeness` の照合、trigger driver の
     source-preimage) を base driver へ移植する。proposal document の保存と raw hash の束縛は既にある形だが、supervisor は trigger 軸専用
     (「generic evolution daemon ではない」と自ら限定) で運用記録の位置付け、source-preimage は proposal JSON でなく materialized source の
     preimage、いずれも B-4 の canonical identity を持たない。移植するなら (α) の field を足すことになり、(α) と独立の択ではない。

   **推奨: (α)。** 理由 — 既存の先例 2 つ (trigger driver の provenance side channel = harness 書き、trigger 系列 supervisor の proposal 保存 +
   completeness 照合) が動いており、凍結型と leak 防壁に触れず、赤 precursor (`diffq-*`) も同じ形で残せる。**不足は carrier の発明ではなく、
   base への接続と B-4 canonical identity (`canonical_b4_proposal_sha256`) の束縛の追加である。** 実装は Codex author の別 wave (実装面)。
   D2100 の「走査 framework・sidecar 入力・ID 規約・耐久 carrier・resolver は作らない」は呼び手の責務の限定であり、driver 側 carrier の
   新設を禁じてはいない — ただし D1936 項 8 との線引き (母集合を**作る**基盤ではなく、出た precursor を**結ぶ**記録) を裁定文に書く。
2. **辺 B の定義。** 3 点とも事前登録 §5.1.1 の**解釈の確定**であり、複数の読みがあることを隠さず択一で返す。値の凍結は §5 の順序 (D1483) に従う。
   - (i) `reference_snapshot_hash` / `reference_receipt_hash` の実体 — 推奨: snapshot = 祖先 certified attempt の WAL `commit` record、
     receipt = 同 `bench_done` record とし、hash は record の canonical JSON の sha256 (64 hex)。**canonicalization は 1 つを名指す** —
     推奨は `agent_outputs.canonical_bytes` (`allow_nan=False`、非有限値を拒否)。`layer3_report._canonical_bytes` は現物で同じ bytes を
     出すが `allow_nan` を指定しないので、定義には採らない (§4.1)。新 object・新 producer を作らない。
   - (ii) 祖先関係 — **未確定で、少なくとも 3 つの読みがある**: ① 同一 campaign 内の時間順 (precursor の iteration より前の whiteboard 行の
     うち最後の `success` に対応する attempt を、裁定 1 の side channel の `iteration` → `variant` で引く)、② proposal が派生した入力
     snapshot の系譜 (planner / coder が読んだ whiteboard・digest の版から遡る)、③ campaign をまたぐ明示的な parent 系譜 (現行に
     記録は無い)。推奨は ①。ただし ① でも、祖先が無い・同着の複数候補・`PerfConfig` / `env_tag` 不一致は §5.1.1 どおり不適格
     (`design_not_feasible` / protocol violation) とし、別基準へ切り替えない。重複提案は新しい評価を作らないので、行順と評価の系譜が
     同一でないことを ① の定義文に書く。
   - (iii) `PerfConfig` / `env_tag` の一致 — **承認された `PerfConfig` の全 field (records / threads / workload の全 key (`ycsb_max_ope` を
     含む) / extime / reps) と `env_tag` の一致を、出所を名指して確認する。** `bench_done.run_cmd` と record の `env_tag` で確認できるのは
     threads・records・extime・workload 3 key・env_tag までで、`reps` と `ycsb_max_ope` は run_cmd から確認できないため、不足として残し
     部分一致を全体一致と呼ばない (D2150 項 2 の 3 種の出所と同じ区別)。
3. **順序。** 裁定 1・2 は §5 の 2 欄 (D1483) と独立に決められるが、carrier の実装と定義の発効は、B-4 の供給源となる新規 base campaign
   (前 wave の順序 (3)) の**起動前**に要る。起動後に足すと、その campaign の precursor は辺 A を欠いたまま残る (遡及で埋めない — 規律 7)。
4. **D2100 呼び手の lock 読取りの局所修正 (§2.3)。** `p3_b4_prerun_caller` が top-level `trial` を読む点を、既存 codec
   (`campaign_lock.decode_campaign_lock`) 経由の `trial` 読取りへ直すか。推奨: 直す (D2120 の「防壁は既存契約の欠陥だけを局所修正」
   と同型。受理形を v1 / v2 の両方に広げるのではなく、codec が受理する形だけにする)。放置すると、現行形式で走った新規 base campaign は
   赤 precursor が出ても D2100 の「不足報告 + 空 batch 到達」に乗らない。実装は Codex author の別 wave、test の lock fixture も v2 形へ。

## 8. 本書が閉じないこと・言わないこと

- 赤 precursor の供給 (自然発生率、新規 base campaign の起動) — 前 wave の範囲。本書は 1 件も作っていない。
- §5 の 2 欄の記入 (D1483)、床値、bootstrap 集合の定義 — 依頼の範囲外、既裁定。
- (α) の実装可否・費用 — 実装面は Codex author の別 wave。本書は設計の最小 field を示しただけで、schema・test・凍結との整合は未検討。
- K2 手動 loop の campaign が B-4 の供給源に**なる**とは言わない (K2 は knowledge arm、campaign identity `409e13f8` は非 B-4)。§3.3 は
  現行形式の carrier の実例としてだけ引いた。
- 現物 7 行の proposal が「失われた」とは言わない — 他機体の scratchpad に当時存在した事実は変わらず、本機体・本 repo に**現存しない**
  (規律 7: 再現できないことと事実でないことは別)。
- 親の実測 script 3 本 (`verbatim/parent-probe-procedure.md` に逐語) は job dir に親が直接書いた read-only probe で、実装面を Codex author に
  書かせる規約に対しては軽い側に倒している ([T-317] 未裁定)。段 6 の read-only レビューに sha256・件数・ref の独立再計算を求めた
  (§9)。tracked な現物 (3 campaign の 14 file、insight 3 file、verbatim JSON 2 本) は全 hash が独立再計算で一致した。
- K2 3 巡目の repo 外 campaign 4 file (§3.3) は親の 19:10〜19:11 JST の観測であり、19:26 JST 以後は不在で、レビューは独立に再確認できなかった。
  同 file 群に関する記述 (journal の `mode=ingested`、`source_sha256` と proposal raw hash の不一致、v2 lock の `trial` の位置) は
  `verbatim/parent-ao-probe.json` に残した親の観測値と、code (`_ingest_agent_output`、`campaign_lock.py`) からの構造的帰結で支える。実物での
  再確認は、同じ形の campaign が次に走った時点で行う。
- 「無い」の射程は、調査した 3 campaign・base driver の precursor 保存経路・`orchestrator/campaign/` の照合範囲に限る。trigger 系列の先例
  (§2.2) は段 6 レビューが見つけたもので、親の初稿は見落としていた。他の系列 (例: A-1 / A-2 / floor の driver) に proposal 保存の carrier が
  あるかは調べていない — B-4 の供給源は base driver なので結論には効かない。
- `canonical_b4_proposal_sha256` を B-4 の identity と置いたのは code の現行定義であり、事前登録が凍結した定義ではない (§5.1.1 は
  「初期 proposal」と書くだけ)。identity の定義自体の裁定は本書の範囲外。

## 9. 段 6 read-only レビュー (1 本、2 レンズ) と反映

軽量版 (docs-only) だが、一次資料から事実を再抽出する wave なので段 6 の read-only codex review 1 本 (`gpt-6-astra`、`reasoning=medium`、
2 レンズを 1 本で担う: A = 束縛の意味論と断定の射程、B = 過剰・削除・scope と裁定パッケージの整合) を回した。起動 19:23:59 JST、
出力 19:32 JST (`check_codex_output` rc=0)。逐語は `verbatim/stage6-review.md`。判定は **NO-GO (must-fix 3・should-fix 3・nit 1)、
全件 real・全件採用**。すべて文書訂正で閉じ、carrier・台帳・gate・test は作っていない。

| # | 所見 | 判定 | 反映 |
|---|---|---|---|
| 1 | must-fix: 裁定 2 (iii) の一致案が `PerfConfig` 全 field を覆わない (`reps`・`ycsb_max_ope` が `run_cmd` に無い) | real | §4.2 (3) と §7 裁定 2 (iii) を「全 field の一致を出所を名指して確認し、run_cmd で確認できない項目は不足として残す」へ訂正 |
| 2 | must-fix: 見落とし carrier — trigger 系列 supervisor の `proposals/` 保存 + completeness 照合、trigger driver の source-preimage。不在断定が広すぎる | real | §2.2 に 2 行追加、結論表 A・§3.4・§7 裁定 1 (δ) で不在断定を「調査 3 campaign と base driver の precursor 保存経路」へ限定、不足を「base への接続 + canonical identity の束縛」へ改めた |
| 3 | must-fix: 「loop_state に `iteration` の出現 0」は現物と不一致 (親の probe は WAL だけを検索。loop_state は base 5 / sort 2 / trigger 3) | real | 結論表 B と §4.2 (2) を「WAL には無い。loop_state は iteration と行順を持つが祖先関係と定める契約が無い」へ訂正 |
| 4 | should-fix: `wal:` ref は「同じ関数」ではない (`agent_outputs.canonical_bytes` は `allow_nan=False`、`layer3_report._canonical_bytes` は未指定。現物の有限 JSON では同値) | real | §4.1 と §7 裁定 2 (i) で 2 実装を区別し、定義に採る canonicalization を名指した |
| 5 | should-fix: 祖先の読みの択一を明示すべき (同一 campaign 時間順 / 派生元 snapshot の系譜 / campaign 間の明示系譜) | real | §7 裁定 2 (ii) を 3 択 + 推奨 ① + 不適格条件の形へ改めた |
| 6 | should-fix: K2 の親観測と独立確認の区別 (レビュー環境で repo 外 path が不在。canonical hash の「campaign 全域不在」は収録手順で再現できない) | real | §3.3 に観測時刻・消失時刻・レビュー不能を明記、「無い」を親が読んだ 4 file に限定、§8 に限界を追加。親も 19:33 JST に不在を再確認した |
| 7 | nit: `B4ScheduledAttemptInput` は 17 field (12 は D2100 の不足分類)、§3.1 の「実際は」は推定 | real | §1 と §3.1 を訂正 |

レビューが独立に一致を確認した範囲: 3 campaign の 14 file の sha256 全件、WAL 行数 / variant 数 / whiteboard 行数 (15/3/4、6/1/1、12/2/2)、
whiteboard の `iteration` 値、success 7 / rejected 0、trigger provenance の variant 2 件の WAL 実在、certified 6 variant の commit ref と
`fitness_tps`、trigger の bench ref 2 件と `layer3_report.source_ref` の一致、insight 3 file と verbatim JSON 2 本の sha256、
`canonical_b4_proposal_sha256` の定義と親 probe の呼び出し、`diffq_variant_id` / `auditor_diff_digest` の意味、D39 決定 3 と 5 field、
archive 2 エントリ (it 2 再利用・sort dry-pass)、D2100 の 12 field、D2150 項 2 の tag `pegasus`、caller と v2 codec の構造的不整合。
レビュー後の訂正は親が行い、焦点再レビューは起動していない (訂正は所見の対案どおりの文書変更で、新しい主張を足していない)。

## 収録物

| file | 内容 |
|---|---|
| `verbatim/stage1-brief.md` | 親の段 1 brief (訂正前の逐語、(P1)〜(P3) の provisional 裁定を含む) |
| `verbatim/parent-edge-probe.json` | 親の実測出力 1 — 3 campaign の file sha256・whiteboard・WAL record (canonical ref 付き)・順序結合の試み・参照点候補・trigger provenance / layer3・K2 insight materials (sha256 `fa32cae3b29556b8e776195265b7f9c17fc68b96f6d47efe46aa911a419e797b`) |
| `verbatim/parent-ao-probe.json` | 親の実測出力 2 — K2 3 巡目 campaign (repo 外) の `agent_outputs.jsonl` の束縛内容と WAL ref の解決 (sha256 `a54b8950e7c725c232c59fe81992d7e91d3ab7c0b1ebd60d3a4691b7788eff09`) |
| `verbatim/parent-probe-procedure.md` | 上 2 本と先行棚卸しの script の逐語 (`.py` は repo に入れない) |
| `verbatim/stage6-review.md` | 段 6 read-only codex review の逐語 (NO-GO、所見 7 件、再計算照合表) |
