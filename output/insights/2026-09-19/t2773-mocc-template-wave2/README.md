# [T-2773] mocc の auditor-live 相当の機械実証 wave 2 — 温度述語 template の接続、同一性 3 比較、DQ / consumer 束縛の対照、auditor の mocc 節、n=1 (2026-09-19)

authority: none
default_effect: no-state-change

- wave: `dev-wave-t2773-mocc-template-wave2` (branch `worktree-dev-wave-t2773-mocc-template-wave2`、base = local main `657e1e5a7` (作成時 `a99425b66`、peer 通知を契機に ff-only で前進))
- 起点: ユーザーの `/dev-wave [T-2773]` 引数とユーザー決定 (2026-09-19)「mocc 温度述語軸のオンボーディング段階 A を承認し、T-2773 wave 2 の機械実証を認可する。探索および pin 前進は認可しない」。設計正本 = `output/insights/2026-09-17/t2757-mocc-mutation-proof-design/README.md` §5・§8〜§13、D2134 項 1〜9。wave 1 = [T-2772] (`output/insights/2026-09-18/t2772-mocc-mutation-proof-wave1/`、worklog entry 1666)。引数の「wave 1 = t2780」は pilot discriminator ([T-2780]) で、D2134 項 8 の wave 1 ではない。
- 逐語: `verbatim/` (親 brief、段 2 plan、段 3 レンズ A / B、段 4 裁定、段 5 author 報告、段 6 レビュー A / B・裁定・fix 報告、prompt 8 本、n=1 の素材と実応答)。sha256 は `verbatim/MANIFEST.json`
- 計測: compute (Pegasus gen_S、generic dispatch) 1 回 = `compute-1.json` (request 11161.nqsv、Elapse 352 秒、all_pass=True)。repo に commit した proof JSON はその bytes (`8d82f7b3e`)。login 生死確認 2 回 (`liveness-run-1.log` = 親 script の GNU patch fuzz で rc=2、`liveness-run-2.log` = git apply へ直して rc=0)。焦点走 2 回 (gen_S 11065.nqsv = 658 passed / 2 skipped、11230.nqsv = 660 passed / 2 skipped)

## 0. 位置づけと非解禁

D2134 項 8 の wave 2 (template 接続の実証) を実装・実走した。ユーザー決定は軸オンボーディング段階 A (人間承認) と本 wave の実証を認可し、段階 B (敵対レビュー) は本 wave の段 6 レビュー 2 本で兼ねた。
**本 wave の緑は、mocc の変異探索・pin 前進・温度述語の正式な軸採用 (段階 C 以降)・certified 比較のいずれも認可しない** (D2134 項 9、本 wave の decisions fragment `docs/spool/decisions/2026-09-19-dev-wave-t2773-mocc-template-wave2-2.md` = fold で採番される D)。旧 pin ↔ pin 候補の D297 比較は別 T ([T-2756])。

## 1. 成果物

| 物 | path | 内容 |
|---|---|---|
| template (proof 用骨格) | `patches/mocc-temperature-predicate-variant.patch` (sha256 `229419ef…`) | touch set = `cmake/Options.cmake` + `cc/mocc/transaction.cc`。file-scope helper `mocc_is_hot(std::uint64_t temp, std::uint64_t threshold)` (anonymous namespace、`inline`) の本体内に唯一の EVOLVE-BLOCK (`mocc-temperature-predicate`、hole = `return temp >= threshold;` 1 行、`#else` = stock 等価述語の逐語)。4 site (296 / 459 / 566 / 970) は `#if MOCC_TEMP_PREDICATE` helper 呼出 `#else` 原文逐語 `#endif`、970 の `\|\| (*itr).failed_verification_` は両枝で保存。外側 guard `#if MOCC_TEMP_PREDICATE // file-scope helper` (完全一致 1 行 = condition gate の一意 witness)、`#ifndef … #error`。`CCBENCH_MOCC_TEMP_PREDICATE` (既定 0) を universal へ相乗り。`IZANAGI_` トークンなし。helper 名に `izanagi` を含めない (nm 計数と混ぜない) |
| 計装 template 版 | `patches/instr-mocc-lock-coverage-temperature.patch` (sha256 `7e6c97bb…`) | preimage = e9e477ca + template。旧計装 (`instr-mocc-lock-coverage.patch`、sha `e9e65b78…`、不変) の 6 hunk の追加本文・guard・前後 context を byte 不変で保ち、`#line` 7 箇所を 17/990/991/1158/1169/1187/1195 → 36/1025/1026/1193/1204/1222/1230 (offset 19 + 35×6) へ再生成。旧計装は template 適用後に `git apply` 不可 (hunk 1 の context)、本 patch は template なしに不可 |
| 軸定数 module | `orchestrator/campaign/axis_mocc_temperature.py` | `MARKER_ID` / `SOURCE_REL` / `TEMPLATE_PATCH` / `INSTRUMENTATION_PATCH` / `FLAG` / `PIN = pin.CURRENT_PIN` (探索用、不変) と `PROOF_PIN = e9e477ca` (proof 用) の分離 / `FROZEN_TEMPLATE_{HOLE,BLOCK}_BYTES` / `TEMPLATE_TOUCH_SET` / `SYNTAX_CONTRACT_{ALLOWED,FORBIDDEN}` (禁止例の列挙であって完全な blacklist ではない) / `AUDITOR_MOCC_REQUIRED` (7 項目の固定 literal) / `require_proof_binding` (束縛だけ、`all_pass` は見ない) / `auditor_projection` (正しさの形だけ、性能・作業量・未知 key は fail-closed) / `check_auditor_definition` (項目境界で分割) / `introduces_mocc_marker` と `mocc_axis_modules` (gate の鍵 (a)(b)) |
| 新 driver | `orchestrator/campaign/s3_mocc_template_proof.py` | wave 1 / T-2294 の helper を import で再利用 (旧 driver・旧 JSON・旧 check は不変)。build 5 本、template ON-B の stock 12 走、同一性 3 比較、計装保存 check、DQ 13 + deny-only 4、consumer 束縛 3、auditor 定義、旧 proof の sha 鎖、condition gate (cache route、mocc owner) → 30 check |
| 新 test | `orchestrator/tests/test_mocc_template_proof.py` | 13 node (gate、JSON consumer、鍵の 4 ケース、束縛 3 対照 + 内容改変対照、軸契約、DQ 13 + 4、論理行列、計装保存 4 対照、射影の性能 field 拒否、auditor 項目の削除・移動対照、condition gate driver ID、per-key 入力由来 (30 key)、実 resolver の OFF = stock / ON-B ≠ stock) |
| 新 JSON | `output/env/pegasus/calibration/s3_mocc_template_proof.json` | schema `s3-mocc-template-proof/v1`、template / 計装版 / wave 1 JSON (`c99aedb9…`) / T-2294 JSON の sha に束縛 |
| auditor | `.claude/agents/auditor.md` (sha `a0912ebb…` → `dc63a311…`) + pin 3 箇所 (`orchestrator/codex_roles/review_ledger.py`、`.codex/role-adapters/auditor.json`、`orchestrator/tests/test_reflux_originless_compatibility.py`) | 型 8 / 9 / 13 / 16 とチェックリスト 11 / 12 / 13 に mocc 追記、5 分類、DQ pass の限定。型番号・description 不変 |
| 登録簿閉包 | `condition_meaning_gate.py` (DefineSpec cache route + 外側 guard 行の witness + decode 集合、供給 39→40 / witness 15→16)、`condition_gate_test_support.py` (`_OPTIONS` 2 行)、`test_condition_meaning_gate.py` (cache route 22→23)、`materializer_admission.py` (新 `_build_variant` NON_ADMISSIBLE)、`test_p3_build_authority_cli.py`、`test_ccbench_spawn_sites.py` (Counter 35/39/25/25 → 36/40/26/26)、`screening_driver.py`、`test_campaign.py` (軸期待表 1 行) | |
| docs | `patches/README.md` に template と計装 template 版の節 | |

## 2. compute の実測 (`compute-1.json` = repo の JSON、gen_S 11161.nqsv、Elapse 352 秒、driver HEAD 2d76e785f)

- **all_pass = True (30 check)**。condition gate 3 本 green (mocc owner、`ycsb_mocc.exe`、cache route、witness = 外側 guard 行)。
- identity: 無 template digest = template OFF digest = OFF baseline (`6454d9f3…`、`src_token = "stock"`)。ON-B (hole = `!(temp < threshold)`) は `41f52341…` で別 identity。保証名 = 「実 resolver (`source_digest`) が定める正規化前処理 source identity の stock 一致」。
- trace0: 計装なし ↔ あり (計装 template 版) の TRACE=0 論理行列は OFF 543 / 543、ON-B 548 / 548 で一致。ON-B の binary は nm izanagi 0、strings 0 / 0、`.text` 差分 0 行 (等長 build dir)。
- 計装保存: `added_body_identical` / `operation_contexts_identical` / `line_restorations_match` すべて True、offset は template 適用前後の実 source の差分から `[19, 35, 35, 35, 35, 35, 35]`。
- DQ: benign 受理、stock-frame → `frame-altered`、fallback / CLL / RLL / validation / X / P / write-registration / RLL-write-registration → `outside-region`、directive / comment-splice → `hole-escape`、bad-anchor → `malformed`。deny-only: matching-pass / mismatched-digest / reject-or-uncertain / machine-reject-preserved すべて True。
- consumer 束縛: alias-rejected / wrong-oid-rejected / literal-accepted-and-marker-detected すべて True。auditor 定義: tools = Read / Grep / Glob、7 項目 True、性能 field の拒否 True、12 走の射影が受理。wave 1 JSON 32 check・T-2294 JSON 14 check とも all_pass を確認。
- 12 走 (template ON-B、TRACE=1、計装 template 版): すべて serializable・certified・cycle 0・X = P = 0・他 integrity clean。W: 1 thread ≈ 18.5〜19.4 万 txn、4 thread ≈ 20.2〜20.5 万 txn (R = W ≈ 87〜96 万)。U: 1 thread ≈ 109〜110 万 txn、4 thread ≈ 350〜368 万 txn、R 行 0。verifier wall 最大 52.9 秒 (u_cold_t4)、benchmark は各 1.0 秒 (extime=1)。**この 12 走は template ON-B の正常系対照であり、template 上で hot 負例が発火したことは主張しない** (`hot_path_evidence` は wave 1 JSON への参照)。

## 3. login の生死確認 (`liveness-run-2.log`、build のみ、benchmark なし)

- template は e9e477ca 複製へ `git apply` 可 (2 file)。旧計装 patch は template 適用後に不適用 (hunk 1 context)、新計装版は template なしに不適用。marker parse (begin 20 / if 22 / else 24 / endif 26 / end 27、hole 1 行)、frozen bytes 一致、外側 guard 行 17 で一意。
- OFF TRACE=0、ON seed TRACE=1 / 0、ON-B TRACE=0、ON-B + 計装 TRACE=1 / 0 は `-Wall -Wextra -Werror` で build 通過。ON-B 計装なし ↔ あり の TRACE=0 `.text` は一致 (59,854 行)。
- **OFF TRACE=0 の `.text` は無 template base と 2 行差** (`mov $0x4a9` → `$0x4cc` = 論理行 1193 の `ERR;` が展開する `__LINE__` 1193 → 1228。template は `#line` を持たない)。identity の正本は resolver の正規化前処理 (include を剥がすため `ERR` は未展開) なので設計どおり stock 一致であり、**無 template と OFF の実 TU・binary の完全同一は主張しない**。
- attempt 1 (`liveness-run-1.log`) の rc=2 は親 script が GNU `patch --dry-run` (fuzz 2・offset 許容) で旧計装を当ててしまった script 側の誤りで、driver・author の `git apply --check` (厳密) とは一致しない。attempt 2 で直した。実装差分には帰属しない。

## 4. 検査・変異

- 焦点走 1 (gen_S 11065.nqsv、fix 前、JSON 依存 2 node を deselect): 658 passed / 2 skipped (既存 skip)。焦点走 2 (gen_S 11230.nqsv、fix 後、deselect なし): 660 passed / 2 skipped。
- 変異 matrix: `mutation-spec-final.json` / `mutation-ledger.json` (harness `tools/mutation_harness.py`、runner = `run_tests.py --force-dispatch` で新 test + 旧 mocc test 2 本 + condition gate + spawn_sites + build authority + codex agents + 軸期待表 node + s8b materializer 閉包 node、`--runner-mode dispatch`、repo HEAD `6861225c0`、spec sha `c8f80765…`、00:33〜01:08 JST): **baseline PASSED、16/16 KILLED (期待 node 完全一致)、等価 M0 SURVIVED、MISMATCH / PARSE_ERROR / TIMEOUT 0**。期待 node は dispatch 形の probe (`mutation-probe-ledger.json`、全 SURVIVED 期待・node 空で観測、23:53〜00:32 JST) で実測して固定した (login probe は使わず、login node を静かに保った)。主 killer は新 test の意味検査で、sha 束縛だけの JSON consumer が単独 killer なのは M10 / M11 (JSON 自身の変異) だけ。

| # | 変異 (対象 / 内容) | 期待 | 結果 | 赤 node (test_mocc_template_proof.py は略、他は file::name) |
|---|---|---|---|---|
| M0 | driver の docstring を等価な文言へ (SURVIVED 検出の正例) | SURVIVED | **SURVIVED** | — |
| M1 | template の stock 枝 `>=` → `>` | KILLED | **KILLED** | axis_contract、quarantine_controls、gate、JSON consumer |
| M2 | template の site 566 だけ ON 側を旧比較に戻す | KILLED | **KILLED** | axis_contract、gate、JSON consumer |
| M3 | 計装 template 版の `#line 1204` → 1205 | KILLED | **KILLED** | instrumentation_logical_rows、instrumentation_preserves_body、gate、JSON consumer |
| M4 | template の helper 外側 guard を削除 | KILLED | **KILLED** | test_condition_meaning_gate.py::test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches、axis_contract、logical_rows、preserves_body、off_matches_stock、quarantine、gate、JSON consumer |
| M5 | 軸 module の `MARKER_ID` を別名へ | KILLED | **KILLED** | axis_contract、off_matches_stock、quarantine、gate、JSON consumer |
| M6 | 束縛関数の sha 検査を削除 | KILLED | **KILLED** | consumer_binding_controls |
| M7 | gate の鍵 (a) を常に False | KILLED | **KILLED** | gate_activation_controls、consumer_binding_controls |
| M8 | `compute_checks.dq()` の subtype 比較を削除 | KILLED | **KILLED** | checks_are_input_derived (fix F1 で追加した対照) |
| M9 | auditor.md 型 16 の mocc 追記 1 文を削除 | KILLED | **KILLED** | auditor_definition_items_are_item_scoped、gate、JSON consumer |
| M10 | JSON の template sha を 1 文字変更 | KILLED | **KILLED** | gate、JSON consumer |
| M11 | JSON の top-level `all_pass` を false | KILLED | **KILLED** | gate、JSON consumer |
| M12a | `condition_meaning_gate` の新 DefineSpec entry を削除 | KILLED | **KILLED** | test_ccbench_spawn_sites.py::test_patch_define_inventory_matches_condition_gate_registry、test_condition_meaning_gate.py の 3 node (registry 束縛 / `[MOCC_TEMP_PREDICATE]` 受理 / domain exact)、condition_gate_uses_new_driver_id |
| M12b | `materializer_admission` の新 entry を削除 | KILLED | **KILLED** | test_p3_build_authority_cli.py の 2 node、test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches |
| M13 | `template_on_benign_identity_distinct` check を定数 True | KILLED | **KILLED** | checks_are_input_derived |
| M14 | 計装 template 版の X 入口検査を `false && …` に恒偽化 (patch bytes) | KILLED | **KILLED** | instrumentation_preserves_body、quarantine_controls、gate、JSON consumer |
| M15 | `auditor_projection` の allowlist に `wall_seconds` を追加 | KILLED | **KILLED** | auditor_projection_rejects_performance_fields、checks_are_input_derived、gate、JSON consumer |

  M9 で `test_codex_agents.py` は赤にならなかった (fixture root で検査するため live file の sha drift は `check_codex_agents.py` 側で出る)。repo 内 gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な防壁ではない (D387)。
- 受入全走: 本 wave の記録 commit を含む tip で land 前に 1 回投入 (結果は land の受領証と worklog)。

## 5. n=1 定性 (D38 決定 4 の点 5 / 6、機械 `all_pass` には入れない)

fresh な Claude `auditor` subagent (Read / Grep / Glob のみ、本会話非参照、期待 verdict・fitness・親の推論を渡さない) に、template (seed) + 計装 template 版を当てた e9e477ca の source を base として候補 3 本を独立監査させた (`n1/INPUT.md`、`n1/manifest.json`、実応答 `n1/auditor-response.md`、2026-09-19 23:41〜23:46 JST)。

| 候補 | 内容 | 実応答 | 帰属 |
|---|---|---|---|
| A1' | validation phase 1 の `lock((*itr).rcdptr_, true);` を削除 (marker 外、告白コメントなし) | **reject** | 型 13 (marker 外への侵食) + 型 8 (write_set 被覆を狭める)。cold record が W_LOCKED にならず publish、hot では早期 lock が隠す (型 8 の記述の実例)。verifier が見逃す機序 (lock は trace されない、torn read) を演繹。提案 test = cold arm での X 赤化、hot-only 緑を certify に使わない、DQ の positive control |
| A2' | hole を `(FLAGS_clocks_per_us == 2100) && (temp >= threshold)` に | **reject** | 型 16 (読取契約違反) = 内容は型 3 (環境判別述語) + 型 2 (identity alias)。既定値では stock と一致し certified を継承、別環境では恒偽で純 OCC に縮退。提案 test = 構文契約 gate の対 (thid_ / result_ の負例と B の正例) |
| B' | hole を `!(temp < threshold)` に | **pass** (nit 2) | 論理等価 (`std::uint64_t` の全順序)、4 site・骨格に差分なし。nit = stock と同値なので比較計測は tie、helper 全体が `#if` 内なので marker の `#else` 枝は到達不能で冗長 (parser 契約のための frame) |

弁別成功 (両 reject / 両 pass に倒さず、各々独立判定)。auditor は `output/` を読まず、`diff_digest` は manifest の値を転記 (Bash を持たない)。注記として base の `#if TRACE` 内 G2 witness (e9e477ca 由来) に `std::getenv` があることを射程外の事実として報告した。**限界**: n=1・planted 候補・A1'/A2' は未実走 (`not_run`)、B' の射影 12 走は driver 側の template sha 束縛に依る。

## 6. 段 2 / 段 3 / 段 4 / 段 6 の所見と裁定 (逐語は `verbatim/`)

- 段 2 plan (`gpt-6-astra`、medium、860 行): template 19 行 helper と `#line` の再生成表 (6 hunk・7 復元点)、実 resolver の使用可、12 走 + build 5 本、DQ 13 対照、束縛関数と `all_pass` の分離、gate 鍵の判定 code、auditor 追記 7 箇所 + pin 3 箇所、登録簿逐語、変異候補 14、異議 10 件 (witness 一意性、fixture 閉包、PIN 分離、循環回避、時間予測、helper 名)。
- 段 3 レンズ A (must-fix 1: 計装 template 版の本文保存が機械 check に無い / should 5 / refuted 4 = P3 型・brace・fallback、三比較、auditor 行番号、DQ pass を安全性と扱う記述なし)。レンズ A は DQ pass する契約違反 9 形 (`FLAGS_*` 読取、comma 式の副作用、lambda / static、再帰、通常式中の TRACE 参照、一行複数文 等) を実 parser で確認。
- 段 3 レンズ B (must-fix 1: auditor-live 機械要件 (1) の read-only 契約・入力射影の構造検査が JSON に未接続 / should 5 / refuted: pin 3 箇所・閉包・cache route・鍵の偽陽性)。
- 段 4 裁定 (`verbatim/s4-ruling.md`、R1〜R21): R1 = `instrumentation_body_preserved`、R2 = auditor 定義に tools と射影、R4 = 保証名の限定、R5 = 12 走は正常系対照、R13 = helper 名、R14 = cache route + 外側 guard witness、R15 = PIN 分離、R16 = 束縛と `all_pass` の分離、R17 = 鍵 (a)(b)、R20 = author 1 本。refuted のうち不採用にした所見なし。
- 段 5 author (`gpt-6-astra`、medium、31 分): 16 file (新規 5 + 既存 11) を実装、起動器の終端 commit `3e7463217`。未完 2 件 = `.codex/role-adapters/auditor.json` (sandbox が `.codex/` を read-only mount、Errno 30) と `liveness-run.sh` (job dir へ書けない)。前者は T-1356 前例 (dd9df29dc / 068532c45) と同じく親が `render_adapter` 出力で置換し D105 waiver (reason=codex-sandbox-readonly-dotcodex、2026-08-18 承認) 付きの別 commit `2d76e785f`。後者は親が計測操作 script として job dir に書いた (R20 / D95 決定 2 からの所有逸脱、DW-O12 で記録。repo には入れない)。
- 段 6 レビュー A / B (`gpt-6-astra`): 両者 NO-GO、must-fix = 「`compute_checks` の 30 check の成立入力 → 1 箇所破壊 → 当該 key 偽 の対照が無い (M8 の DQ subtype 比較削除、tools の Bash 混入が素通り)」の 1 件 (親も同所見)。B の 2 件目 (liveness-run-1 の rc=2 と author 報告の矛盾) は refuted (親 script の fuzz、§3)。nit = OFF `.text` 差の記録 (R4 と矛盾せず)、X 恒偽化対照の式、author 報告との時点差、親 script の所有逸脱。fix 1 巡 (`gpt-6-astra`、6 分、test file 1 本、`6861225c0`): per-key 対照 30 key + F2。fix 後の焦点再レビューは投じず、変異 matrix と焦点走 2 で裏取り。
- n=1 (§5) は fix 後の source (production code は fix で不変) で実施。

## 7. 主張しないこと・残件

- mocc の変異探索・pin 前進・certified 比較の開始、温度述語が正式な変異軸として承認されたこと (段階 C 以降は別裁定)。
- template 上で hot 負例が発火すること、4 site 全動的被覆・read 側 hot・RLL 再試行・DELETE の被覆 (D2134 項 3・4)。
- 無 template ↔ OFF の実 TU・binary 同一 (`ERR` の `__LINE__` で 2 行差、§3)、その性能影響がゼロであること (未測定)。
- 任意の直書き経路・全 consumer 経路の閉鎖。実 loop driver (consumer) は未導入で、導入時にその実 checkout との束縛検査が別途要る。
- DQ pass が純粋性・一式性・停止性・読取契約の充足を示すこと (物理行の封じ込めだけ)。auditor pass が C++ の意味上の安全性証明であること。
- stock mocc の観測間隙 (設計 §3.2 (a)) の再現 (別 T-2774)。旧 pin ↔ pin 候補の D297 比較 (別 T-2756)。

## 8. 段 8 (自己改善) の候補と routing

- 候補 1 (所有の逸脱、本 wave で実測): R20 で author 所有にした job dir の生死確認 script を author は書けず (sandbox は repo 内だけ)、親が書いた。既存正本 `DW-C01`「子の成果物は repo 内に書かせ、親が実行後 repo 外へ退避」が既にこの形を規定しており、親の裁定 (R20) が正本に反していた。routing = docs 変更なし (正本で規定済み)、次回は裁定に DW-C01 の形を書く。
- 候補 2 (near miss、本 wave で実測): 親の生死確認 script が GNU `patch --dry-run` (fuzz 2・offset 許容) を使い、driver の厳密適用 (`git apply --check`) と食い違って旧計装が「当たる」と誤判定 (attempt 1 rc=2)。同型の再発は無く F 化しない。routing = 親の memory (計測 script の patch 適用は driver と同じ厳密適用にする)。
- 候補 3 (手順、本 wave で実測): レビュー B の射影に失敗した attempt の log (`liveness-run-1.log`) だけを渡し、成功した attempt 2 を渡さなかったため must-fix 1 件が artifact になった。既存 memory「継続巡のある author の最終報告をレビュー射影に渡す」と同族。routing = 同 memory へ追記、docs 変更なし。
- 候補 4 (手順の確認、本 wave で実測): 変異の期待 node を login probe でなく dispatch 形の probe (全 SURVIVED 期待) で採る手順は `DW-M07` が既に規定しており、17 変異を 40 分・login 無負荷で観測できた。routing = 変更なし (正本どおり)。
- 以上、docs (入口・reference・failures・decisions) への変更はゼロ。段 8 の commit は作らない。

## 9. verbatim 一覧

`verbatim/MANIFEST.json` に sha256。
