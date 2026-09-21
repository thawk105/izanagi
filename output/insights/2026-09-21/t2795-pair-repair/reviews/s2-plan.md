# 計画の前提と結論

**認可 session 案を採用する。** 既存の候補・stock 評価を別々の `run_campaign` として残し、同一 process・同一 campaign・同一 output root に束縛された session の中で、取得済み claim の所有を再確認して使う。

指定資料は読めた。以下の行番号は現 worktree の読解位置であり、変更後の行番号ではない。**全検査は未実走・静的読解。実装、ファイル書出し、pytest、計測、job 投入は行っていない。**

根拠は、初投入で候補だけが成功し、stock は同 identity の `O_EXCL` で止まった事実と、修復方向を限定した D2187 である。claim の再取得・削除・退避や別 root は採らない。
参照: `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md:43,80,120`、親 brief `s1-brief.md`、逐語 `verbatim/D2187.md`。

# 1. (P1) 認可 session の設計 — 条件付き支持

**条件は、session を単なる「認可済み boolean」にせず、以下の束縛を sink で再検査すること。**

| 比較項目 | session 案 | 1 回の `run_campaign([候補, stock])` 案 |
|---|---|---|
| claim | 初回だけ取得、次回は所有確認 | 現行のまま 1 回取得 |
| source tree | 候補・stock を別 checkout にできる | 通常経路の `ccbench_dir` は 1 本 |
| stock の STOCK 性 | 既存 stock resolver と WAL 判定を維持 | coder 編集木でも前処理後 digest が一致すれば STOCK になり得る。「編集木だから必ず非 STOCK」は反証される |
| admission | 候補用 context と authority 無しの stock context を分離 | `build_context`・`capability_resolver` は各 1 本。source ごとの分岐 resolver は作れるが、候補 authority と stock 制約の分離を追加設計する必要がある |
| 検疫 reject | 候補が sink 未到達なら stock が初回認可を取る | 候補を除いた stock-only 呼出しと、候補 reject 処理を別に組み直す必要がある |
| 結果処理 | 両関数の単一結果処理を維持 | skip・abort を含めて arm ごとに結果を対応付け直す必要がある |
| 変更範囲 | sink の狭い拡張と session 配線 | sink は不変だが、tree・admission・結果処理を再編する |

先例は実在する。A-1 は `genomes(...)` を一括投入し、source context・balanced executor も使う。sweep は stock と候補を genome 列に並べる。ただし、それだけで S4 の別 checkout・検疫・LoopState 契約を満たすわけではない。
参照: `paper_story_a1_paired.py:7295,7545`、`backoff_sweep.py:252,484`、`loop.py:347,782`、`p3_s4_loop.py:2198,2230,2294,2300`。

したがって、対案は機構上不可能ではないが、D2183 の stock 隔離と既存結果処理を保持する本修復では session 案が小さい。

**API と初回取得**

- `loop.py` に loop 発行の session factory と opaque な session 型を置く。名前案は `authorization_session()`。
- `run_campaign(..., authorization_session=None)` を keyword-only で追加する。
- session は作成時点では未束縛。最初に測定 sink へ到達した呼出しが、現行 `_authorize_measurement` を通る。
- `_AuthorizationResult` に取得済み `AcquiredClaim` 等の session 保持に必要な内部値を加える。`campaign_claim.acquire_claim` の返値を保持し、**認可成功直後、perf preflight・layout・evaluate より前**に S を束縛する。
- 認可途中で失敗した場合は「認可済み」にしない。部分 claim が残った場合も再取得救済をせず、leaf の拒否に従う。
- session 終了はメモリ上の失効だけ。claim file は触らない。

参照: `loop.py:82,165,236,516,537,542`、`campaign_claim.py:75,383,446`。

**再利用時の検査**

再利用処理は `_authorize_measurement` の明示的な session 経路に置く。初回発行と再利用を同じ sink に集約し、driver に所有判定を置かない。

| 検査 | 比較する値・関数 |
|---|---|
| 発行元 | loop factory が付与した private sentinel と exact session 型。caller が渡した辞書や `_AuthorizationResult` は受理しない |
| 同 process | factory が保存した PID、および取得済み `record.pid` を `os.getpid()` と比較。取得後は `campaign_claim.read_proc_starttime()` と保存 record の値も照合 |
| 現在の認可契約 | `execution_guard.require_certified_writer_authorization(...)` を毎回通す。`env_tag`・`clocks_per_us`・`numactl`・任意 `env_contract` の検査を省略しない |
| 契約 SHA | 上記が返した `contract.contract_sha256` と S の保存値を比較 |
| campaign identity | 現在の `build_context.policy` を `ident.bind_admission_policy` で束縛した cfg に、現在の契約を `ident.bind_environment_contract` で束縛し、`ident.campaign_id` を再計算して比較 |
| identity 全体 | `sha256(ident.canonical_preimage(bound_cfg))` と保存 `record.protocol_digest` も比較。短い campaign ID の比較だけにしない |
| use class | 現在の `declared_use_class` と S の保存値を exact 比較 |
| output root | `resolve_campaign_output_root(declared_use_class, output_root)` を再実行し、解決済み絶対 path を S と比較。空文字の一致だけでは通さない |
| claim root | `env_scope_dir(contract.env_tag, base_root)/claims` を再構成し、既存 directory・非 symlink・`write_capability_for_directory(..., policy=...)` を再検査 |
| claim 所有 | 再構成した claim path と `AcquiredClaim.path` を比較し、既存の `campaign_claim._read_existing_record(path)` で読んだ全 record を保存 `AcquiredClaim.record` と比較。欠落・破損・symlink・field 改変は拒否 |
| reservation | `read_binding(os.environ)` と `check_reservation(required_s=1, safety_margin_s=0, environ=...)` を毎回実行。保存 binding とも照合し、別 job の reservation へすり替わらないようにする |
| pre-write validator | 各呼出しの再計算 identity に対して毎回実行。初回だけで済ませない |
| execution receipt | 初回の receipt を S 内に caller から変更できない形で保存。required 契約では verified calibration を再ロードし、`receipt_matches_contract` で保存 receipt の束縛を再検算して再利用する。再 probe による別 receipt の発行はしない |

参照: `loop.py:177,185,199,202,205,215,222,223`、`campaign_claim.py:39,133,216,245`、`reservation.py:159,223,278`、`execution_guard.py:107,225`。

receipt の再利用は**同じ認可 session の継続**という意味である。再検算は現在の機械状態の再観測ではない。候補・stock は同じ receipt 内容を受け取り、S 内部の保存値を `CampaignSummary.execution_receipt` の変更で壊せないようにする。S 無しでは既存の receipt object の扱いも維持する。

`single_process=False` の契約では従来どおり claim を作らない。その場合も session の契約・identity・root 束縛を検査し、後から別契約へ転用できないようにする。

**S 無しの互換性**

S が無い呼出しには追加 keyword を内部転送せず、現在の `_authorize_measurement` 経路と順序を維持する。既存 assert は更新しない。

- `test_campaign.py:9222`: `load → attest → matches → read_binding → check_reservation → acquire_claim → evaluate → evaluate`
- `test_campaign.py:9314`: 同じ前段順序から `evaluate` 1 回
- identity 計算 1 回、receipt object 同一性の assert も維持する。

D553 への変更は「毎回取得」から「取得、または同 sink が取得した claim の所有再確認」への限定拡張である。D464 の leaf は bytes 不変とし、別 process・新しい S・S 無しによる同 path の再取得は引き続き拒否する。

# 2. (P2) CLI と候補・stock の隔離 — 条件付き支持

**`--run-iteration P --stock-control` を pair mode として採用する。別 flag は増やさない。** 既存 stock-only consumer を保つため、`pair_mode` と `stock_only` を明確に分ける。

参照: `p3_s4_loop.py:3072,3175,3199,3411,3427`。

| モード | 受理・排他 |
|---|---|
| pair | `--run-iteration` と `--stock-control`、`--isolate-worktree` 必須 |
| pair の候補入力 | `--coder-role`、`--allow-coder-derived-build` は候補だけへ有効 |
| pair の禁止 | 明示 `--value`、`--emit-planner-context`、`--no-build`、`--b4-reflux-ablation`、`--b5-slot` |
| stock-only | 現行の coder-role・coder authority・fixture・emit・no-build・B-4 排他を維持 |
| B-5 | stock-only または candidate-only を維持。pair × B-5 は argparse 段階で rc=2 |
| その他 | ingestion 排他、machine-generated-proposal の B-5 必須条件、B-4 receipt 条件、較正・verify の同時指定条件を維持 |

`--b5-slot` の現行 OR 条件だけでは pair を通してしまうため、`:3183` に pair 明示拒否を加える。`:3199` の排他は pair と stock-only に分ける。

**見落とすと候補 authority を消す箇所が三つある。**

1. `:3302` の opt-in 必須条件にある `not a.stock_control` を、stock-only の例外へ狭める。pair 候補は従来の明示 authority を要求する。
2. `:3369` の `if a.stock_control` で候補 context を作らない。
3. `:3411` の stock 分岐で pair が候補を飛ばして return しない。

候補 context は現行候補と同じ authority で作る。stock context は別の `build_run_context(generator_id=BACKOFF_SWEEP)` とし、coder authority を与えない。両 context の **policy 値の一致を事前要求**し、不一致なら測定前に拒否する。stock resolver は既存 `_stock_capability_resolver(stock_context)` を使い、候補 resolver を流用しない。
参照: `p3_s4_loop.py:2005,2089,2278,3302,3369,3392`。

**worktree と実行順**

- 共通の `fixed_sub` に現行の `assert_pinned_clean(fixed_sub, PIN)` を行う。
- 候補用 `checkout(PIN, base_dir=fixed_sub)` に入り、候補の処理と cleanup を終える。
- stock 用には**新しい checkout context を作成**する。同じ context manager・候補 path を再利用しない。
- stock の template 適用先は stock checkout、比較用 `stock_root` は clean な `fixed_sub`。
- cache root は従来の共有 `build-variants`、campaign output root は同じものを使う。

参照: `p3_s4_loop.py:2051,2061,3384,3404,3486`。

S の配線は `main → drive_iteration → _run_one_iteration_resolved → run_campaign`、stock は `main → _run_stock_control_resolved → run_campaign`。各内部 API に既定 `None` の keyword-only 引数を追加し、非 `None` 時だけ下位へ渡す。公開 `run_one_iteration` や他 driver に session を自動導入しない。
参照: `p3_s4_loop.py:2019,2117,2312,2717,2850`。

CLI の既存候補・stock 分岐を並べ直して共用する構成を第一案とする。既存の二つの `run_campaign` 呼出しを使い、pair 専用の第三の sink 呼出しや layout constructor は増やさない。

# 3. (P3) 候補結果、例外、stock 起動 — 条件付き支持

**候補の通常結果・通常例外は stock の試行を止めない。rc は既存候補 CLI の規則を保持する。**

| 候補の終了 | S の状態 | stock と rc |
|---|---|---|
| certified | 束縛済み | 所有再確認して stock。候補 rc=0 なら stock rc を採用 |
| quarantine reject | 通常は未束縛 | stock が初回認可・claim を取得。候補 rc は既存 checkpoint／stop 判定に従い、reject だけで非零に変えない |
| aborted | sink 到達後なら束縛済み | stock を試行。abort を CLI failure と同一視しない |
| duplicate-skip | 束縛済み | stock を試行。候補 rc=1 を優先 |
| stopped-before | 未束縛 | stock を試行。候補の既存 rc 判定を保持 |
| proposal 読込み・候補 checkout・condition gate・評価後処理の例外 | 到達点に依存 | 例外を保存し、stock を試行してから元の traceback 付きで再送出 |
| stock 自身の失敗 | ― | candidate 非零優先。stock 成功を捏造しない |

参照: `p3_s4_loop.py:2198,2232,2290,2837,2865,3465,3501,3510`、旧集約 `p3_s4_loop_pegasus.sh:669`。

実装境界は次のとおり。

- 共通 CLI 検査、契約、policy、K2 identity の確定は pair の共通 preflight。ここで失敗したら pair 全体を拒否する。
- 候補固有の proposal 読込み、agent-input 処理、checkout、`drive_iteration`、候補出力を候補 step の例外範囲に入れる。
- 保存した候補例外を stock 例外で上書きしない。両方なら、候補例外を主として stock 例外を chain または traceback 出力で併記する。
- 候補が通常 return で非零、stock が例外なら、stock traceback を明示して候補 rc を返す。候補 rc=0、stock が例外なら stock 例外を再送出する。
- `SystemExit` を step 内で扱う場合も code を保存し、stock 後に非零優先を適用する。`KeyboardInterrupt`・強制終了まで「必ず stock が走る」とは約束しない。

取得後に候補処理が例外となっても、S は認可成功直後に束縛済みなので stock が使える。一方、S の不一致や claim 改変を検知した場合は、新しい S に差し替えて救済しない。

# 4. (P4) job body の 1 起動化 — 支持

`tools/pegasus/p3_s4_loop_pegasus.sh` は以下の差分とする。

| 現在の位置 | 変更 |
|---|---|
| `:147` | env の未設定／`0`／`1`／不正値の規則を維持 |
| `:152` | `stock_identity_argv` を削除し、空または `(--stock-control)` の pair 用 argv を作る |
| preflight、`:163` より前 | stock=1 かつ proposal path 無しを `refuse`、rc=2。明示 fixture と pair の組合せも拒否 |
| `:672` | 既存 proposal 起動に pair 用 argv を追加。K2 argv は従来の 1 組だけ |
| `:679` | fixture 起動は従来の argv を維持 |
| `:686`〜末尾 | 独立 stock 起動と shell 内の二段集約を削除。driver が返す集約 rc をそのまま exit |

既定の pair 用配列は空なので、未設定／`0` 時の argv 要素と順序を変えない。shell の変数名 `candidate_rc` を残せば、既存 fragment の不要な変更も抑えられる。

B-5 の先行分岐と `exit "$b5_rc"`、`:79` の B-5 × stock env 拒否は維持する。trap・compute-result schema・reservation provisioning は変更しない。

**job contract 更新箇所**

- `test_p3_s4_loop_job_contract.py:66`：stock mode、identity argv、stock rc、shell 集約の逐語 pin を新契約へ変更。
- `:549`：静的 driver 起動箇所数 **3→2**。runtime は proposal／fixture のどちらでも 1 起動。
- `:613`：stage-order の独立 stock 起動 marker を更新。
- `:976`：fixture driver fragment は維持し、prebuild より前の起動を引き続き拒否。
- `:1306`：代用 Python が `--stock-control` の存在で「二つ目の rc」を選ぶ仕様を廃止。単一 driver の指定 rc を返す。
- `:1869`：古い shell 集約・identity 転送 mutation の組を更新。
- `:1912`：既定 argv exact test は期待値不変。
- `:1933`：proposal／K2 の pair を「1 履歴、同時指定」として検査。fixture は preflight 拒否 test へ移す。
- `:1953`：shell は集約済み rc の透過だけを検査。候補失敗後の stock と優先順位は Python driver test が担う。
- `:2150`：`candidate_rc=0` anchor を残すなら不変。変更する場合は B-5 late-branch test も追随。

# 5. (P5) stdout と pair 判定 — 支持

正常に結果を得た場合は、候補・stock 各 outcome 行を出す。候補行は `ran/outcome/variant/iteration`、stock 行は `outcome/variant/fitness_tps/verdict` の既存情報を維持する。最後に診断用の `p3 S4 pair: candidate_rc=... stock_rc=...` を driver から出す。

参照: `p3_s4_loop.py:3420,3503`、旧 shell 出力 `p3_s4_loop_pegasus.sh:690`。

例外時は対象を識別できる `candidate`／`stock` の `outcome=exception` 行と stderr traceback を出せるが、variant・fitness・WAL outcome を補作しない。

stock 成功は現行の次の積を維持する。

`certified ∧ not aborted ∧ variant == variant_id(stock_genome) ∧ BUILD_START.src_token == STOCK`

`skipped`／`identity-skipped` は新規測定成功にしない。stock は LoopState・whiteboard・checkpoint を更新せず、既存条件に従って critic digest だけを再生成する。
参照: `p3_s4_loop.py:2092,2096,2110`。

**pair 成立は両 attempt の WAL outcome で判断する。** rc=0、同じ campaign ID、二つの stdout 行だけでは成立としない。候補 reject と stock certified の組も pair 成功ではない。
参照: `tools/pegasus/README.md:384,387`、逐語 `verbatim/D2183.md`。

# 6. F1019 恒久対応の結合検査

**最低 1 本は `p3_s4_loop.main()` から入り、実認可・実 claim・実 reservation・実 layout・実 WAL を通す。**

新 node 案: `test_pair_main_pegasus_real_claim_and_wal`。

1. fixture 専用の絶対 output root を作り、`env/pegasus/claims` を事前 provisioning する。
2. `IZANAGI_EXPLORATION_OUTPUT_ROOT` を設定し、実 layout resolver を使う。default durable policy の入力だけを fixture root に向け、root／mount／write capability 検査は実物を使う。
3. canonical な site 判定を `PEGASUS_COMPUTE` に設定する。driver の `_current_site` だけを変えて execution guard を OTHER のままにしない。
4. `ec.lookup("pegasus")` と `ec.authorize("pegasus")` を実使用し、`single_process is True` を assert。
5. 有効 reservation env を設定する。
6. proposal、候補 checkout、stock checkout を別 path で用意し、`main(["--run-iteration", P, "--stock-control", "--isolate-worktree", "--allow-coder-derived-build", ...])` を呼ぶ。
7. 候補→stock の両評価について、実 sink と実 `pipeline.evaluate` が WAL を生成する。

**fixture の採否**

| 既存 fixture | 用途と制約 |
|---|---|
| `test_campaign.py:9064` `_campaign_reservation_environment` | A1 の正例／欠落負例で再利用可。実 boot ID と整合した env を作る |
| `conftest.py:159` `valid_reservation_environment` | A2 の第一選択。返す辞書を `monkeypatch.setenv` で設定する必要がある |
| `test_campaign.py:9126` `_single_process_test_policy` | fixture root の durable policy 作成に利用可 |
| `test_campaign.py:9101` `_mock_required_attestation` | A1 の呼出し順テストには可。ただし receipt は `fixture-required-receipt` なので、実 WAL consumer を通す結合検査に無条件流用しない |
| `test_campaign.py:5835` `_mock_pipeline` | 実 evaluate を残して build／trace／bench を代用する足場。v2 build、grammar keyword、各評価の build context に合わせて局所 adapter を付ける |
| `test_campaign.py:137,157` | 合成 SourceEvidence と proof source の足場 |
| `test_p3_s4_loop.py:10143` | 実 pipeline が COMMIT・STOCK record を作る既存例。ただし OTHER／layout 差替えは継承しない |
| `test_p3_s4_loop.py:9669` `_stock_cli_fixture` | 結合検査には不採用。site、layout、checkout、run_campaign を差し替えている |

attestation は stub 可だが、結合検査には実契約 SHA と整合した v2 receipt／verified calibration fixture を使い、WAL consumer の admission を無条件通過にしない。`_mock_pipeline` の `_BUILD_CONTEXT` identity assert と bench の script index にも注意し、評価ごとに context を合わせる。
参照: `test_campaign.py:5924,5940,5976`。

**stub 境界**

- 可：build、trace 実行、bench、attestation の観測、condition gate、patch 適用、checkout、quarantine の機械的入力、compiler 依存の SourceEvidence、perf preflight。
- 不可：`run_campaign`、`_authorize_measurement`、session 検査、`require_certified_writer_authorization`、`acquire_claim`、reservation 読込み／検査、identity、layout、campaign lock、WAL append/replay、resumability。
- `pipeline.evaluate` 全体の stub は A1 単体には可。**結合正例では実 evaluate を残す。** 成功 WAL record の手書きや `records_by_stage` の偽応答では F1019 の対応としない。

**必須 assert**

- `acquire_claim` は実処理を呼ぶ spy で **1 回**。
- claim file は **1 個**、identity・protocol digest・PID・record 内容が候補後と stock 後で同じ。
- reservation の実検査は両 sink 到達時に行われる。
- 候補と stock の BUILD_START／terminal record が同一 campaign WAL に存在。
- 候補・stock は異なる source root、同一 output root・policy・identity。
- stock は authority 無し、STOCK 専用 resolver。
- stock outcome は実 WAL の STOCK 条件で決まる。非 STOCK evidence の負例は成功しない。
- stock 前後で候補 checkpoint／whiteboard が不変。
- stdout に両 outcome、rc に非零優先規則。

**負例**

- S 無しで同じ cfg/root に 2 回 `run_campaign`。2 回目は引き続き `ClaimError`。同 process の逐次呼出しでも旧形の失敗を再現できる。
- 初回後の identity、PID、契約 SHA、use class、output root、claim record 各 field の改変を拒否。
- claim 欠落・破損、reservation 欠落・不一致、receipt 再検算失敗を拒否。
- caller 構築の偽 session、終了済み session を拒否。
- pair × B-5 を main 経由で rc=2、layout／claim 未到達で拒否。
- candidate reject／例外でも stock が測定へ到達する。
- candidate 認可成功後の例外でも claim の取得回数が増えない。

root 不一致や identity 不一致は既存の別検査でも落ち得るため、**session の該当拒否点で、evaluate／新規 claim／WAL 変更より前に落ちる**ことまで assert する。

この結合検査は compiler での STOCK 成立・Pegasus production 測定を証明しない。F1019 には「認可経路の結合欠落を固定、実機 pair は別予算で未実施」と記録する。

# 7. pin 閉包と既存 test

path 検索に加え、`run_campaign`、`_authorize_measurement`、`_AuthorizationResult`、`drive_iteration`、`stock_identity_argv`、`STOCK_CONTROL` の key 側も検索した。hit 0 だけを「pin 無し」の根拠にはしていない。

| 変更 file | pin と扱い |
|---|---|
| `loop.py` | `test_campaign.py:9222,9314` の順序不変。`:5408` の semantic caller inventory、`:5496` の raw-AST inventory は呼出し点を増やさないので不変 |
| `p3_s4_loop.py` | `test_p3_exploration_namespace.py:426` の layout **11**、run_campaign **2**、既定 runtime **1**を維持する構成。実装で constructor を追加した場合だけ実数を再集計して更新 |
| 同上 | `test_p3_b4_wiring_probe.py:329` の import 閉包 **49**は既存 campaign module だけを使う限り不変見込み。B-4 到達経路 pin `:735` も検査する |
| 同上 | `test_p3_s4_loop.py:9775` の run-iteration 排他 case を pair 正例へ変更。stock-only の coder-role／authority 排他は残す。condition gate 順序 pin `:91` は維持 |
| shell | job contract `:66,549,613,1306,1869,1933,1953` を更新。既定 argv `:1912` と fixture fragment `:976` は維持 |
| `test_campaign.py` | 新 session tests を追加。本番 caller inventory の期待数を「テスト追加」を理由に増やさない |
| `test_p3_s4_loop.py` | 専用結合 fixture と CLI tests を追加。既存 stock-only・B-5・source 判定 tests を残す |
| docs | README の現行契約を更新。過去 insight・D2183 本文は当時の記録として保持 |

`test_ccbench_spawn_sites.py` は process 起動点を固定している。B-5 の `default_runner` は `:99`、`run_campaign` の build 到達認識は `:845`。今回 Python subprocess を追加せず、既存 checkout helper を呼ぶだけなので目録は不変。shell の driver 起動数は別途 job contract が固定する。

`tools/pegasus/admission_registry.json:118` の job body は引き続き `dispatch-required`。SHA pin ではなく分類 record であり、`test_p3_s4_loop_job_contract.py:1815` の exact 辞書も不変。registry 更新は不要。

実装後の焦点対象は campaign、S4、job contract、exploration namespace、B-4 wiring、spawn-site、および B-5 consumer tests。適用される runner 経由で実行し、docs／Codex agents checker、commit 後 provenance checker、親指定 acceptance と変異検査を続ける。**本段ではすべて未実走。**

# 8. consumer の取り残し確認

現物の semantic inventory は「約 19 driver」ではなく、**17 ファイル・22 呼出し点**である。
参照: `test_campaign.py:5408,5433`。

| caller | 呼出し位置 | 影響 |
|---|---|---|
| `b10_backoff_static_tail_formal.py` | 761 | 不変、S 無し |
| `b10_backoff_shape_sweep.py` | 4474 | 不変 |
| `backoff_extended_sweep.py` | 1446 | 不変 |
| `backoff_repro.py` | 172 | 不変 |
| `backoff_sweep.py` | 484 | 不変 |
| `demo.py` | 57,67 | 不変 |
| `p2_2.py` | 376 | 不変 |
| `p3_kickoff.py` | 152,159 | 不変 |
| `p3_s4_loop.py` | 2083,2280 | 更新要、pair 時だけ S を転送 |
| `p3_s4_loop_sort.py` | 413 | 不変 |
| `p3_s4_loop_trigger_gating.py` | 811 | 不変 |
| `p3_s4_red.py` | 207,217 | 不変 |
| `paper_story_a1_paired.py` | 7295,7545 | 不変 |
| `paper_story_a2_certification.py` | 3803 | 不変 |
| `s6_sort_sweep.py` | 413 | 不変 |
| `s8a_trigger_sweep.py` | 515 | 不変 |
| `sanity_silo.py` | 59 | 不変 |

`s8b_floor_campaign.py:7209` の同名 `run_campaign` は別関数で、この inventory へ混ぜない。他 caller の連続測定を本修復で自動的に session 化しない。

追加 consumer：

- `_run_stock_control_resolved`：本番 caller は `p3_s4_loop.py:3415`。pair 接続を更新。直接テスト `test_p3_s4_loop.py:10215` は既定引数で不変。
- base `drive_iteration`：本番 caller は同 `:3487`。pair 接続を更新。sort `:524`、trigger `:1005` の同名関数は別実装で不変。
- `run_one_iteration`：同 `:2312`、非 pair 公開口として不変。
- B-5 `slot_argv`：`b5_generator_contrast.py:478`、`:484` は stock-only と proposal を択一で起動。**不変**。
- B-5 launcher：`tools/pegasus/b5_contrast_launch.py:99` の PIN 読取り、`:150,173` の job/env 構築は不変。
- `tools/pegasus/README.md:368`〜`:390`：**更新要**。1 process・1 claim session、proposal-only pair、候補固有 authority、driver 集約を記載。
- `docs/phase3.md:495`：過去の不成立を消さず、隣接する修復項目を追加。実測 pair 未成立・未投入を区別する。
- failures F1019：`docs/failures.md:27839` の該当項へ、結合検査と模擬範囲を追記する。親の既存文書運用に従って記録する。

# 9. 段 4 で事前登録する変異候補

以下の node 名は新設案。**KILLED は期待であり、未実走。** 各変異を独立適用し、別 gate に偶然止められた場合は目的の検査を殺したと数えない。

| 変異 | 期待 KILLED node |
|---|---|
| 再利用時にも `acquire_claim` を呼ぶ | `test_pair_main_pegasus_real_claim_and_wal` |
| 初回 claim 取得を省く | 同上の取得回数・claim file assert |
| S 無しでも claim 取得を省く | `test_no_session_second_campaign_keeps_claim_error` |
| S を stock へ渡さない | 結合正例 |
| S を評価成功後にしか束縛しない | `test_pair_stock_after_postauthorization_exception` |
| 発行元検査を外す | `test_authorization_session_rejects_foreign_value` |
| PID 検査を外す | `test_authorization_session_rejects_pid_mismatch` |
| identity 比較を外す | `test_authorization_session_rejects_identity_mismatch` |
| protocol digest 比較を外す | `test_authorization_session_rejects_preimage_mismatch` |
| 契約 SHA 比較を外す | `test_authorization_session_rejects_contract_mismatch` |
| declared_use_class 比較を外す | `test_authorization_session_rejects_use_class_mismatch` |
| resolved root 比較を外す | `test_authorization_session_rejects_output_root_mismatch` |
| claim record 比較を外す | `test_authorization_session_rejects_claim_record_change` |
| reservation 再検査を外す | `test_authorization_session_rechecks_reservation` |
| receipt 再検算を外す | `test_authorization_session_rechecks_execution_receipt` |
| pre-write validator を初回だけにする | `test_authorization_session_rechecks_prewrite_validator` |
| 正しい束縛でも再利用を拒否する | 結合正例・session 単体正例 |
| pair × B-5 の拒否を外す | `test_pair_cli_rejects_b5_before_side_effects` |
| pair 候補の opt-in を不要にする | `test_pair_candidate_requires_coder_authority` |
| stock に候補 context／checkout を渡す | `test_pair_separates_stock_authority_and_worktree` |
| candidate reject／例外で early return | `test_pair_stock_after_candidate_failure` |
| stock rc を常に優先する | `test_pair_candidate_nonzero_has_priority` |
| STOCK 条件を外す／逆転する | 既存 `test_stock_control_rejects_non_stock_certified_source` と結合正例 |
| job body を旧 2 起動へ戻す | `test_pair_job_invokes_driver_once`、静的起動数 pin |
| fixture + stock を受理する | `test_pair_fixture_refused_before_trap` |
| env 既定を on にする | 既存 `test_default_job_invokes_driver_once` |

identity と protocol digest、PID と record 等は重複防御があるため、単純な異常入力だけでは一方の削除変異が生き残り得る。該当比較以外を整合させた unit fixture と拒否点 assert を用意し、結合正例だけに全変異を背負わせない。

# 10. author 分割と引渡し

**A1 → A2 の直列を支持する。** A1 が API、session 不変条件、例外型、初回束縛タイミングを固定し、A2 がその API を使用する。

- A1 完了条件：S 無しの順序 test を維持し、session 正例・各束縛負例・旧形 ClaimError を追加。leaf 差分ゼロ。
- A2 完了条件：CLI・別 worktree・例外後 stock・job body 1 起動・実認可結合 test・pin 閉包を揃える。
- 親：段 4 の変異事前登録、独立検証、docs／insight／F1019、受入、land を担当。pair 再投入・4 巡目は本 wave に含めない。

所有 file は末尾表のとおりとし、A2 は A1 の `test_campaign.py` を編集せず、必要な fixture は参照利用または自分の test file に局所追加する。

## 総括

| provisional | 判定 |
|---|---|
| P1 session | **条件付き支持**：sink の束縛再検査と receipt 再検算を必須化 |
| P2 CLI | **条件付き支持**：stock-only を分離し、候補 opt-in 必須条件も修正 |
| P3 失敗後 stock | **条件付き支持**：通常例外を保存・診断・再送出し、候補非零優先 |
| P4 job body | **支持**：proposal pair を 1 起動、fixture pair は preflight rc=2 |
| P5 出力 | **支持**：両 outcome を出し、成立判定は WAL のまま |

確定設計の要約：

1. loop 発行の S を pair 内だけで共有し、最初の測定到達時に束縛する。
2. 次回は現在の契約・identity・root・reservation・claim 所有を検査する。
3. claim 取得は 1 回、leaf と identity preimage は不変。
4. 候補・stock は別 checkout、別 build context、同 policy・同 WAL。
5. 候補 reject／abort／通常例外後も stock を試行する。
6. shell は 1 driver の集約 rc をそのまま返す。
7. main 経由の Pegasus 契約結合検査で実 claim・reservation・WAL を通す。
8. 実機 STOCK 成立と pair 測定は本 wave の成果に含めない。

| 所有者 | 所有 file |
|---|---|
| A1 | `orchestrator/campaign/loop.py`、`orchestrator/tests/test_campaign.py` |
| A2 | `orchestrator/campaign/p3_s4_loop.py`、`tools/pegasus/p3_s4_loop_pegasus.sh`、`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/tests/test_p3_s4_loop_job_contract.py` |
| A2・必要時のみ | `orchestrator/tests/test_p3_exploration_namespace.py`、`orchestrator/tests/test_p3_b4_wiring_probe.py` |
| 親 | `tools/pegasus/README.md`、`docs/phase3.md`、F1019 の記録、修復 insight、decisions／worklog fragment、変異事前登録 |
| no-touch | `campaign_claim.py`、reservation leaf、admission／verifier の受理条件、既存 submit-tree-pair |

親裁定を要する残件は、**P1 の receipt 再利用条件と、P3 の通常例外後の再送出方式をこの具体案で採用するか**。新たな計測予算や claim leaf 変更の裁定は求めない。

**検査状況：未実走・静的読解。**