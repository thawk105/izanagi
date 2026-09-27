## 変更アンカー表

| 所有単位 | file:line | 変更内容 | 依存 |
|---|---|---|---|
| A | `orchestrator/campaign/p3_s4_loop_policy.py:121–134,299–343,373–405,415–490` | campaign の用途・環境を一度だけ確定し、login の emit／preview／reject と計算ノードの評価に同じ identity を使う。計算側へ site 契約、clocks、numactl、依存 prefix、fetchcontent 受領証を渡す | `p3_s4_loop.py:130–184,287–330,3660–3681` の既存 helper |
| A | 同 `:299–370,415–490` | stock 単独、候補後の stock pair、loop 状態を進めない R2 を追加する。stock 用 build context と capability resolver は候補用と分ける | `p3_s4_loop.py:2304–2415,3817–3821,3858–3985` |
| A | `orchestrator/tests/test_p3_s4_loop_policy.py:137–210,341–411` 付近 | identity、実 source からの stock 分類、pair の順序、R2 の独立性、baseline の WAL 射影を検査する | A の実装 |
| B | `tools/pegasus/p3_s4_loop_pegasus.sh:54–224,303–325,376–395,728–789` | `IZANAGI_S4_POLICY_MODE` 分岐、排他、方策 pin、Python import、保全 root、driver argv を追加する。既存の前処理と `IZANAGI_BENCH_LOCK` を共用する | A の CLI |
| B | `orchestrator/tests/test_p3_s4_loop_job_contract.py:456–559,577–622,1219–1416` 付近 | 方策分岐の静的順序と実 shell の argv／env／失敗時 rc を検査する。既存 mode の期待 argv は維持する | B の job body |
| B | `tools/pegasus/admission_registry.json:124–129`、`tools/pegasus/README.md:333–390,445–476` | 登録済み **同一 body** の説明と、方策 mode の qsub 例・出力 root・walltime を更新する。新規台帳 entry は不要 | B の mode 契約 |
| 親 | `docs/phase3-silo-policy-runbook.md:13–30,34–90,105–108` | §0.2、§1(f)、stock、R2、保全と checkout の手順を更新する | A・B の確定 interface |

所有 path は A・B・親で重ならない。`p3_s4_loop.py` は編集しない。既存登録 body の mode と driver 引数を増やすだけなので `hooks/` と権限設定の変更は不要である。台帳の `dispatch-required` と job 内の計算ノード確認は既にある（`admission_registry.json:124–129`、job body `:17–29`）。hook の発火をこの判断の証拠にはしない。

## interface (関数署名・CLI・env・JSON field)

- A: `default_cfg(*, form, reflux=True, purpose="loop", env_tag=...)` のように用途と環境を identity に含める。計算実走だけは観測 site が `PEGASUS_COMPUTE` であることを確認する。login の読取り・preview は同じ `pegasus` identity を**明示選択**できるようにする。`measurement_env=pegasus` も `p3_s4_loop.py:170–184` と同じ位置で焼き、後段で再束縛しない。
- A: `--stock-control` を proposal 無しなら stock 単独、`--run-iteration` と併用なら候補→stock とする。stock 単独の初回基準取得には `--purpose baseline-bootstrap`、本 loop と pair には `--purpose loop` を使う。両者は同じ動作点だが別 campaign である。
- A: `--replay-proposal PROPOSAL.json --r2-run-id ID [--stock-control]` を R2 の入口とする。入力は `--run-iteration` と同じ `{coder,auditor}`。`search_config` に `evaluation_purpose="r2"` と `r2_run_id=ID` を焼く。R2 は `drive_iteration` を通さず、共有 gate と `run_one_iteration` 相当の評価を通す。
- A: `--fetchcontent-prebuild-receipt PATH` を受け、`L._load_masstree_prebuild_receipt` の五つの戻り値を `run_campaign` の既存引数へ渡す。`CMAKE_PREFIX_PATH` を `dependency_prefix` として渡し、`contract.env_tag`、`contract.clocks_per_us`、`contract.numactl`、`authorization_contract` は site 解決値から渡す。
- B: `IZANAGI_S4_POLICY_MODE=stock|pair|replay|replay-pair`、`IZANAGI_S4_POLICY_FORM=cpp|ir`、pair／replay 用の proposal path、R2 用 run id、共有 campaign base 用 `IZANAGI_S4_POLICY_OUTPUT_ROOT`、`IZANAGI_TRACE_ARCHIVE_ROOT` を受ける。方策 mode は T-2849、B-5、K2、既存 proposal／fixture／stock-control と排他にする。
- A の stock JSON は `outcome`、`variant`、`fitness_tps`、`abort_rate_pct`、`verdict` と WAL attempt の識別子を出す。`fitness_tps` は certified 評価の `EvalResult.fitness_tps`、`abort_rate_pct` は当該 attempt の `BENCH_DONE.leading_indicators.abort_rate × 100` から取り、欠損なら baseline を発行しない。abort 率の元は bench の比率値であり、verifier verdict でも `loop_state.json` でもない（`pipeline.py:1538–1551`、`calibrator/model.py:94–108`）。

## P1〜P5 の判定 (real / refuted / 要修正、根拠 file:line)

**P1 — 要修正のうえ既存 job body の mode を推奨。** 兄弟 body は gflags／glog／masstree、receipt、reservation、Python shim、pin 検査を重複させる（job body `:303–325,376–395,` 後半の事前構築）。既存 body なら T-2850 が使う T-2849 分岐 `:54–90,728–747` を保ち、分岐の排他と方策 driver 起動だけを足せる。静的 test は既存 `p3_s4_loop` 呼出し **2 箇所**と B-5 呼出し **1 箇所**を数える（job 契約 test `:546–559`）。方策呼出しは別文字列で一箇所と検査すれば既存期待値を変えずに済む。兄弟 body なら新台帳 entry と独立した shell 契約が要る。hook test はどちらの案でも hook 自体を変えない限り不要。方策 pin は短縮 `axis.PIN` をいったん CCBench の `rev-parse --verify '<pin>^{commit}'` で 40 桁へ解決し、その値で HEAD を比較する。現行の 40 桁 regex を短縮 pin に直接当てない（`axis_silo_function_policy.py:10`、job body `:376–395`）。`resolve_python` は方策 module も import できることを確認する（job body `:303–325`）。方策分岐でも `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を driver 前に export する（`:744,768`）。

**P2 — 親案の一部を refuted。** stock は `BASE` から `SILO_POLICY_VARIANT` を除いた genome、pin の原型 source、**方策 template patch 無し**で評価する。`0` を明示した patch 済み source より、この組合せのほうが `source_digest.resolve_evidence` の現行／HEAD digest 比較で `STOCK` と判定される根拠が明確である（方策 patch `:9,30–36,60–75`、`source_digest.py:2439–2455,2307–2317`）。stock 用 `build_run_context(generator_id=BACKOFF_SWEEP)` と `L._stock_capability_resolver` を使い、coder authority は候補にだけ渡す（`p3_s4_loop.py:2304–2315,3817–3821`）。pair は一つの authorization session で候補を先に、別の使い捨て CCBench checkout の stock を後に試みる（`:3858–3985`）。stock は `loop_state.json` と `policy_history.jsonl` の iteration を増やさず、同じ campaign の WAL と critic digest には載せる。ただし**初回 stock 単独を loop campaign に入れると、後の pair の同一 stock variant は terminal skip になる**（`:2333–2336,2409–2412`、README `:383–390`）。従って baseline bootstrap は別 campaign に置き、loop campaign の最初の stock は pair 内で測る。初回 coder 入力に同動作点の実測 baseline が必要なので、既存の適格な測定が無い今回、stock 単独 job 自体は必要である。

**P3 — real。** 実 LLM の寄与を見る一系列は `--form cpp`。形は既に `search_config.form` に入る（方策 driver `:121–130`、runbook `:29–30`）。

**site と保存先 — 要修正。** 方策 driver は `ENV_TAG='linux-baremetal'`、clocks `1800` を固定し、計算ノード契約を渡していない（`:41,299–327,336–343`）。計算側は `L._admit_env_contract` と `L._campaign_cfg_for_site` に倣う。login では「測定 site」を偽装せず、campaign identity の `pegasus` を明示して emit／preview／reject を行う。`exploration_campaign_layout` の実体は `<base>/exploration/campaigns/<campaign-id>`（`layout.py:594–602`）。既定 base は**実行 checkout の** `output` なので、AI worktree と detach checkout のままでは履歴が割れる（`:375–405`）。全 CLI と job に同じ repo 外 base を指定し、job body が `:39` で消す `IZANAGI_EXPLORATION_OUTPUT_ROOT` を方策 mode の検証後に再設定する。投入 checkout は AI worktree 容器外の wave tip detach checkoutとし、login の駆動もその checkout から行う。

**P4 — real、ただし loop の `--run-iteration` の別名だけでは不足。** 既存 backoff 軸は保存 proposal を `--run-iteration` に渡すことが R2 の入口で、R2/G の差は proposal の作り方にある（見積り稿 §8.3）。方策軸でも同じ `{coder,auditor}` を再読込し、共有検疫、型付き検査、単独 TU、auditor digest／veto、書込後 digest を再照合する（方策 driver `:88–118,169–196`）。一方、R2 は旧 loop の iteration／履歴／予算を動かさないので別 campaign identity と直接評価が要る。fresh R2 campaign なら stock pair 可。R2 は新しい有限履歴の判定であり、原判定の再確認ではない（見積り稿 §8.1）。

**P5 — real、検査位置は job body。** 方策 mode の全値で保全 root を必須にし、絶対 path かつ repo 外を driver 起動前に検査する。既存 mode は変更しない。pipeline は env を読み、保全関数は絶対 path を要求するが、repo 外制約はここでは検査しない（`pipeline.py:2270,2499,2946–2961`）。保全は `IZANAGI_TRACE_ARCHIVE_ROOT` を qsub env で渡す既存 opt-in と同じである（D2261 項3）。

## test と変異の事前登録候補

最小 test は次のとおり。A は実 `source_digest` と WAL consumer を通す小さな stock fixture、B は既存の実 shell harness を拡張する。単に stub の返り値を再確認する test にはしない。

| 単位 | test 名の案 | 赤になる破壊 |
|---|---|---|
| A | `test_policy_stock_source_is_stock_and_has_no_policy_flag` | patch を stock に当てる、flag 1 を残す |
| A | `test_policy_stock_baseline_uses_same_attempt_bench_wal` | 別 attempt の abort 率を読む、percent 変換を落とす |
| A | `test_policy_pair_candidate_then_stock_one_session` | 順序・session・stock context のいずれかを変える |
| A | `test_policy_login_and_compute_select_same_campaign` | env marker、admission policy、出力 base の片側を変える |
| A | `test_policy_r2_rechecks_auditor_without_advancing_loop` | digest 再照合を抜く、loop state／history を進める |
| B | `test_policy_mode_actual_job_argv_and_archive_env` | receipt、pin、保全 root、bench lock の転送を抜く |
| B | `test_policy_mode_excludes_existing_modes_before_checkout` | T-2849／B-5／K2 との混在を許す |
| B | `test_policy_driver_runs_once_after_prebuild` | driver の重複起動、前処理前起動 |

事前登録する変異は七本とする。

| 壊す行 | 期待して落ちる test | 単一理由性 |
|---|---|---|
| 方策 driver `:307` 相当で stock genome に `axis.FLAG:1` を残す | A stock source | stock source の分類だけを検査する fixture にする |
| stock source に `patchharness.applied` を追加 | A stock source | pin／compiler は正常な fixture を使用する |
| stock baseline 射影の `abort_rate × 100` を除く | A baseline WAL | certified WAL と非 null の abort 率を入力にする |
| pair の stock 用 context に coder authority を渡す | A pair | 候補の gate を通した後、context の帰属を検査する |
| R2 経路で `drive_iteration` を呼ぶ | A R2 | 有効 proposal で前段 gate を通し、state 増分だけを見る |
| job body `:376–395` 相当の方策 pin 選択を旧 `L.PIN` に戻す | B actual job pin test | 模擬 CCBench HEAD を方策 pin に合わせる |
| job body `:728–789` 相当の方策分岐を receipt 作成より前へ移す | B driver order | env・pin を正常にし、順序だけを変える |

既存の静的検査は `p3_s4_loop` 呼出し数 2、B-5 呼出し数 1 と既存分岐の順序を維持すれば期待値変更不要（job 契約 test `:546–559,581–622`）。新しい方策呼出しの数と順序は別 assertion にする。

## E2E 手順と見積りの材料

1. wave tip から AI worktree 容器外の専用 detach checkout を作り、`tools/dev_wave_submodule_init.py --worktree "$REPO_ROOT"` で submodule を初期化する。方策 `axis.PIN` へ CCBench を合わせ、tracked clean を確認する（Pegasus README `:445–457`）。stock 単独と pair は別 job checkout にし、共有するのは明示した campaign base と保全先だけにする。
2. stock 単独 job は stock 1 評価。trace 有効 build、legacy verify 1 rep、性能構成 verify 5 rep、trace 無効 build、bench 5 rep を行う。成功 JSON の `fitness_tps` と `abort_rate_pct` を取得する。
3. 同じ wave tip detach checkout で、共通 campaign base と `pegasus` identity を指定して runbook §1(a) の `--emit-coder-input` を実行する。得た JSON だけを coder に渡す。§1(b) の C++ coder、§1(c) の `--preview-diff`、失敗時 `--record-reject`、通過時 §1(d) の auditor、§1(e) の `{coder,auditor}` proposal を順に作る。
4. fresh pair job checkout の qsub へ `POLICY_MODE=pair`、`FORM=cpp`、proposal path、共通 campaign base、repo 外の archive root を渡す。job は候補を評価した後、候補が reject／例外でも stock を試みる。候補が pipeline に到達すれば上記の build 各2・verify 1+5・bench 5 を候補と stock の計2評価で行う。構造 gate で reject された場合、候補の build／verify／bench は0で、stock 1評価だけになる。pair 成立は job rc ではなく両 attempt の WAL で判定する（Pegasus README `:375–390`）。
5. 既知の**評価固有費**は write-heavy 1評価 217〜509秒、build 15〜17秒、legacy verify 7〜16秒、性能構成 verify 5 rep×34〜91秒、bench 約17秒（再現見積り稿 `:221–226`）。gflags／glog／masstree の前処理だけを切り出した信頼できる秒数は、今回指定された資料では確認できない。job Elapse の試走を前処理込みの単価に使う。現行 script の walltime 宣言は `03:00:00`（job body `:2–6`）。stock／pair とも初回はこの要求値を維持し、Elapse を記録して次を縮める。実投入と焦点走・変異・受入の合計が **2 node 時間以上**なら、D2212 項4に従い投入前に親が見積りを示して確認を取る。LLM の直列時間は別記する。
6. 保全先は repo 外の `/work/1/SFC/tanab/izanagi-repro-archive/t2865-stage-f-20260927/`。job ごとに `-o`／`-e` を repo 外 evidence dir に指定し、receipt と `compute-result.json`、campaign WAL、保全 inventory を回収する。

## runbook 節立て

- **§0.2 投入前の確定値:** wave tip detach checkout、方策 pin、共有 campaign base、archive root、計算費用。
- **§1(a)〜(e) 共通引数:** `--form cpp`、`pegasus` campaign identity、同じ出力 base を各 CLI に明記する。
- **§1(f) 計算投入:** 方策 mode の qsub env、proposal path、receipt、pair の候補→stock 順、WAL による成立判定。
- **§1(stock) 初回 baseline:** 別の bootstrap campaign の stock 単独、JSON の二つの scalar、loop campaign の stock skip を避ける理由。
- **§1(R2) 保存候補の再実行:** 同じ proposal schema、auditor 再照合、別 campaign、任意の stock pair、旧判定との関係。
- **§1(保全) trace:** 絶対・repo 外 root、qsub env、inventory の確認。§3 には loop の checkpoint と R2 の分離を追記する。

## 未確定点 (親の裁定が要るもの)

- 初回 baseline を別 `baseline-bootstrap` campaign に置く案。これは親 brief の「stock 単独→同じ campaign の pair」を訂正する。現行 WAL の terminal skip 契約を変えない最小案として推奨する。
- R2 の反復識別子を必須 `--r2-run-id` とする案。同じ保存候補を複数回再評価する際に別 campaign を得るため推奨する。
- node 時間の投入確認は、親が実装・検査の job Elapse 見積りを合算した後に行う。現時点の 217〜509秒は評価固有費で、前処理込みの job Elapse ではない。

## 総括

既存 Pegasus body に方策 mode を追加する。登録済み body と前処理を共用でき、既存 mode の期待値も維持できる。  
stock は原型 source と方策 flag 無しの genome で評価し、候補とは build authority を分ける。  
初回 baseline は別 bootstrap campaign、候補後の stock は loop campaign の同じ job で測る。  
login と計算ノードは同じ `pegasus` identity と共有 campaign base を明示する。  
R2 は保存 proposal と auditor を再検査し、loop 状態を進めない別 campaign で評価する。  
方策 mode だけ repo 外の trace 保全先を必須にする。  
親への裁定依頼は bootstrap campaign の分離と必須 R2 run id の二点。  
本段は読取り専用の計画であり、build・pytest・実測は行っていない。