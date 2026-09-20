# [T-2153] 意味 witness の残件 (b)(c) — `#ifdef` の定義/未定義観測と非一意 directive の全箇所観測を足し、MISATTR / RUNG1 / TRIGGER_GATING を登録簿へ (枝選択 18 → 21)

- 日付: 2026-09-20
- branch: `worktree-dev-wave-t2153-witness-bc` (base = local main `947fd160a`、fresh worktree)
- 実装 commit: `b250dc9a942919c9d3591d1369093cb07391366a` (Codex `role=author` の実装 1 巡 + fix 2 巡を所有 path 限定で統合、統合は親)
- 対象: `orchestrator/campaign/condition_meaning_gate.py` (compile-time 枝選択 witness D1490 の 2 つの新型 + 登録簿 `_CONDITIONAL_BRANCH_WITNESSES` +3 + `_CONDITIONAL_BRANCH_SITE_COUNTS`)、`orchestrator/campaign/s8a_trigger_coverage.py` (`_require_condition_gate` の factory 配線 + MISATTR の default None)、test 4 file
- 前 wave: `output/insights/2026-09-19/t2153-witness-6/README.md` (15 → 17、D2161)、`output/insights/2026-09-17/t2153-witness-else-nested/README.md`、entry 1195 / 1704 の残件表
- 専用 handoff / job dir: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-bc/` (prompt・log・patch・probe・login/compute cell 原本・変異台帳。repo には逐語と要約だけ)

## 1. 依頼と守った裁定

依頼は「未対応 8 件のうち機構変更で届く (b) `IZANAGI_BREAK_TRIGGER_MISATTR` (`#ifdef` 非識別、外側条件) の定義/未定義観測と、(c) `IZANAGI_SILO_LADDER_RUNG1` ×2 / `BACKOFF_REQUESTED_US` ×2 / `BACKOFF_TRIGGER_GATING` ×12 の非一意に対する代表選択 (全箇所か決定的規則) を Codex author (D95) で実装し land まで。(d) SS2PL_* と探索 loop 配線・offline 供給・admission 永続化・S2 再走は含めない。変異 = 正例と負例。既存 stock / template の pre-image は byte 一致 (D2108 と同条件)。規律 2 を緩めない。仮想リスク向けの gate・検査・台帳・一般化は scope 外」。

守った裁定: D1490 (所有 TU の枝選択のみ主張)、D1491 (旧宣言経路は BACKOFF_FIXED 固定)、D1492 (配線は admission が成果物へ載る driver だけ)、D2161 (実 TU 実測で足す、代表 1 本を代表にしない)、D2141、規律 2 (受理集合は狭まる向きだけ)。設計判断は本 wave の decisions fragment (slug `witness-ifdef-and-multisite`、land の fold で D 番号が付く) に記録。

## 2. 何を変えたか (設計)

| 型 | 機構 | 登録 |
|---|---|---|
| (b) `#ifdef` 形 | 登録簿の directive が `#ifdef ` で始まる macro は要求腕 `-D<M>=1`、対照腕 **未定義** (`-D` なし、request の `default_value=None` を factory が要求)。supply の対照 compile argv に同 macro が残れば `supply-value-mismatch` (不在検査は `#ifdef` 登録 macro に限る)。green record 再検証は `#ifdef` 形だけ要求 argv から対象 macro の `-D` token を除いて対照 argv と比較 | `IZANAGI_BREAK_TRIGGER_MISATTR` (`cc/silo/transaction.cc`、N=1) |
| (c) 全箇所観測 | `_CONDITIONAL_BRANCH_SITE_COUNTS` に N を宣言 (未掲載 1)。逐語完全一致の全箇所に現行と同じ `directive / SELECTED() / #endif / COMPLETED() / directive` を挿入し、要求 (N·v, N) / 対照 (N·c, N) を要求。件数 ≠ N は N=1 で `compile-time-branch-start-not-unique` (逐語不変)、N>1 で `compile-time-branch-site-count-mismatch` (expected=N、observed=件数) | `IZANAGI_SILO_LADDER_RUNG1` (N=2)、`BACKOFF_TRIGGER_GATING` (N=12) |
| 配線 | `s8a_trigger_coverage._require_condition_gate`: `declaration=declare_define_runtime_meaning(request)`、MISATTR だけ `default_value=None`。`s8a_trigger_freq` は helper 共有で追随、`silo_ladder_rung1` は既配線で RUNG1 1/0 に自動追随 | — |
| 不変 | 既存 18 entry の値・順序・2-tuple、`DefineSpec` / `DEFINE_SPECS`、旧宣言経路・CLI `--meaning-case`、companion 注入、`_preprocess_argv`、record の key 集合、`ConditionalBranchMeaningDeclaration` / `CompileTimeBranchSelectionObservation` の field 集合 | — |

登録しなかったもの: `BACKOFF_REQUESTED_US` (transaction.cc 2 箇所 + `include/backoff.hh` 2 箇所。owner TU の 2 箇所だけの登録は D2161 (2) の部分登録。4 箇所同時観測には 1 macro に複数 file の箇所群を宣言し同じ shadow で計装する拡張 (capture・shadow・evidence schema) が要る → 残件)。配線しなかった driver: `s1_verify_extime_calibration` (TRIGGER_GATING を要求し admission を JSON へ載せるが、capture が genome configure と offline 供給を渡さない。配線と供給を同じ変更単位で扱う、D2161 理由 4)、`s8a_trigger_sweep` / `backoff_sweep` / `backoff_requested_us` (返り値を廃棄し永続化しない)、探索 loop (依頼で除外)。

## 3. 前提実測 (段 1、production CLI、main 947fd160a、login pegasus02、official 同形供給)

| cell | supply | meaning | admission |
|---|---|---|---|
| MISATTR 1 vs 0 (skeleton+instr+misattr 木、s8a genome) | **red `preprocess-bytes-identical`** | unestablished | **rejected** |
| MISATTR 1 vs 未定義 | green | unestablished | admitted (未確立 [MISATTR]) |
| TRIGGER_GATING 1 vs 0 / RUNG1 1 vs 0 / REQUESTED_US 1 vs 0 | green | unestablished | admitted |

新事実: 現行 gate では positive control MISATTR は要求 1 / 既定 0 では supply 赤 = `s8a_trigger_coverage` の misattr 腕は preflight で `RuntimeError` になる (実走記録なし。D48/AUD-4 の positive control が gate を通れない状態だった)。静的解析 (job dir `nest.sh`): 4 macro の全箇所は top / `#if BACK_OFF` / `#if NO_WAIT_LOCKING_IN_VALIDATION` の内側、MISATTR だけ `#if BACKOFF_TRIGGER_GATING` の内側 (configure の `CCBENCH_BACKOFF_TRIGGER_GATING=1` が要る。companion にはしない: CXX_FLAGS route の companion は CMake の cache define と二重 `-D` になる)。

## 4. 実 TU の実測 (最終 production 登録簿 b250dc9a9、official 同形供給)

| 構成 (木 / macro / 要求 vs 対照) | login (pegasus02) | 計算ノード (bnode003) |
|---|---|---|
| skeleton+instr (coverage 第 1 腕) / BACKOFF_TRIGGER_GATING / 1 vs 0 | supply green、meaning **green (12,12)/(0,12)**、admitted、未確立 [] | 同 |
| skeleton+instr+misattr (coverage 第 2 腕) / BACKOFF_TRIGGER_GATING / 1 vs 0 | 同 (12,12)/(0,12) | 同 |
| skeleton+instr+misattr / IZANAGI_BREAK_TRIGGER_MISATTR / 1 vs 未定義 | supply green、meaning **green (1,1)/(0,1)** (default define_value = null)、admitted、未確立 [] | 同 |
| skeleton+instr+misattr / MISATTR / 1 vs 0 | supply red、factory None (設計どおり拒否) | (login のみ) |
| rung1 / IZANAGI_SILO_LADDER_RUNG1 / 1 vs 0 | supply green、meaning **green (2,2)/(0,2)**、admitted、未確立 [] | 同 |
| sort / SORT_VARIANT / 1 vs 0 (既存) | green (1,1)/(0,1) | 同 |
| rung1 / RUNG1_REPORT / 1 vs 0 (既存、companion) | green (1,1)/(0,1) | (login のみ) |

login と計算ノードで 5 cell とも前処理 digest・byte 数・owner TU sha・compiler (g++ 11.4.0) が完全一致。configure: MISATTR / GATING は `s8a_trigger_coverage` の genome + 供給 4 引数、他は供給 4 引数。patched 木は pin 511c953 の shared clone に driver と同じ重ね順で `git apply` (misattr = template→instr→misattr、gating-instr = template→instr、requested-us = fixed→requested-us)。

**I1 (既存 macro の不変):** SORT / REPORT の record (supply・meaning・admission) を変更前 (main 947fd160a) と変更後 (b250dc9a9) で同 driver-id・同 configure で leaf 単位に比較: 異なる leaf は一時 path (`/tmp/izanagi_condition_supply_*`、`/tmp/izanagi_compile_time_branch_*`) を含む argv とそれに派生する `record_digest` / `record_id` / `admission_digest` だけ。key 集合・前処理 digest・byte 数・owner TU sha・dependency closure digest・counts・define_value・reason・proof_kind は同一。全既存 macro の canonical JSON byte 一致は主張しない (揮発 path を除いた一致まで)。

**登録前後の supply (新規 3 macro):** MISATTR / RUNG1 (CXX_FLAGS route) は登録により共有 build root へ移行 (対照 root `default` → `requested`)、GATING (cache route) は分離のまま。4 cell とも前処理 digest・bytes・owner TU sha・dependency closure digest が登録前後で一致。

## 5. 主張の境界 (正直に書く)

- witness が確立するのは D1490 のまま「所有 TU において、宣言した N 箇所すべてで、その define の値 (`#ifdef` 形は定義の有無) が枝の選択を決めている」まで。動的到達性・枝本文・runtime 異常 (MISATTR の誤帰属の発火と検出) は主張しない。
- **GATING の 12 箇所は DefineSpec patch (`silo-backoff-trigger-gating-variant.patch`) の逐語 12 箇所**であり、計装 patch (`instr-silo-backoff-trigger-gating-tally.patch`) が足す `#if BACKOFF_TRIGGER_GATING && TRACE` と `#ifndef` 番兵は対象外 (module docstring に明記)。所有 TU 内の未宣言な条件指令を走査して red にする機構は足していない (裁定パッケージ候補、§7)。
- `declare_define_runtime_meaning` が None を返す request (例: 要求 = 既定、非対値) は従来どおり unestablished admit であり family 拒否ではない。MISATTR の driver 要求を 1/0 から 1/None へ直したことは「同一要求に対する受理の変化」ではなく要求の訂正。
- 受理集合: meaning arm 単独では狭まる向きだけ (unestablished admit → green admit / red reject)。supply の不在検査は `#ifdef` 登録 macro の未定義対照にだけ効く (過剰拒否の正例 = SORT 1/None で現行どおり green を test で固定)。
- 公開 driver の JSON (coverage / frequency の `condition_gates`、rung1 の `condition_gates`) は本 wave では取得していない。「未確立一覧が縮む」のは CLI cell (login + 計算ノード) で実証した範囲。
- 単体 test の正例は合成 fixture (N 箇所 + 両腕に無条件本文) + 実 compiler。実 TU の緑は §4 の CLI cell が担う。

## 6. 段ごとの所見 (要点)

- 段 2 plan: 3 件登録・REQUESTED_US 見送り・N は別 mapping (2-tuple consumer 3 件を壊さない、新 field は canonical bytes を変える)・green record 再検証の argv placeholder 比較 (G:4014) の修正必須・所有 5 file (rung1 driver test:105 の `None` pin)・brief の件数訂正 (登録簿は現物 18)。
- 段 3 consult A (正しさ境界): (A1) 12 箇所の主張が計装 patch の複合枝を含まない → 主張範囲を DefineSpec patch に限定して記録 (機構は足さない); (A2) 不在検査は `#ifdef` 登録 macro に限定 (全 `default=None` へ広げると NOINLINE 1/None の判定が変わる); (A3) 実 TU cell は coverage の 2 構成 (skeleton+instr / +misattr) を分ける; (A6) schema 変異 test は `require_issuer=False` 形。refuted: None 対応による旧経路拡大、全箇所観測の黙認経路、companion。
- 段 3 consult B (過剰・削除・pin): (B1) `s1_verify_extime_calibration` は D1492 の対象だが供給整合を欠く → 別変更単位; (B2) = A2; (B4) 新 field・汎用 validator・互換 framework を作らない; (B5) 未登録例は `SS2PL_LOCK_IMPL`、patch 束縛は `matches == [pair] * N`; (B7) 完了主張は CLI cell と公開 JSON を分ける。pin 表: `_COMPILE_TIME_BRANCH_MACROS` 末尾追加、集合 pin は独立列挙で追随、B-4 47 module 不変、凍結 manifest 不変。
- 段 5 author: sandbox で test 未実走 (qstat preflight rc=16)、親が計算ノード dispatch で実走。焦点走 1 (所有 3 file) = 302 passed / 1 failed (docstring 件数 pin の未追随)。焦点走 2 (consumer 18 file) = 1695 passed / 45 failed = S1 direct comparison 44 (fixture helper `_materialize_requested_condition_macros` が要求 macro ごとに 1 箇所しか足さず GATING N=12 で `site-count-mismatch` → prepare 拒否; `test_promotion_contract_carries_unestablished_meaning_macro` が GATING 1/0 を未確立例に使う) + B-4 probe の clean-tree test 1 (未 commit dirt 由来)。
- 段 6 review A / B: 両方 NO-GO。must = m4 が等価変異 (c=0 で `≤ N·c` は `== 0`) + 直接検査が公開 evaluator の後ろで schema に遮られる → m4′ (対照 selected 検査だけ除去) と独立 node 化; baseline 赤の解消; GATING 境界の docstring 明記; 計算ノード cell。refuted: 受理拡大・全箇所観測の黙認・argv/cache・schema の issuer mask・B-4。nit 不採用: 新規正例の重複 (可読性優先)、`22-macro` の古い文言、pin test 名。
- fix 1 (Codex): docstring pin 追随、S1 fixture を `_declared_site_count` 箇所化、持ち越し例を GATING 0/0 へ → 親 probe で 0/0 は stock-inert 経路になり S1 fixture の stock root が FIXED/NOINLINE の CMake mapping を欠くため `compile-command-drift` (fixture の限界)。fix 2 (Codex): 直接検査を独立 node `test_multisite_assert_rejects_default_partial_selection` へ、module docstring に主張範囲、持ち越し例を GATING 2/0 (非対値 = factory None、供給は同 root で green)。
- 再走 (計算ノード): 所有 4 file **445 passed**、consumer 20 file (clean tree) **1791 passed / 2 skipped**。全史 provenance 11,883 件・新規違反なし。
- 焦点走の運用: login から `run_tests.py` を投げると headroom があれば bounded local に落ち S1 24 件が `/tmp/.git` 由来の偽赤 → `--force-dispatch` を付けて計算ノードへ (1 走分の無駄)。

## 7. scope 外 (裁定パッケージ候補、実装しない)

1. `BACKOFF_REQUESTED_US` の 4 箇所同時観測 (1 macro に複数 file の箇所群を宣言、owner TU + header を同じ shadow で計装、evidence schema の拡張)。
2. `s1_verify_extime_calibration` の factory 配線 + genome configure / offline 供給の整合 (D1492 対象、別変更単位)。
3. 所有 TU 内の未宣言な条件指令 (重ね当て patch の複合枝) の走査 (`#ifndef` 番兵の免除規則が要る)。
4. 公開 driver (coverage / frequency / rung1) の実走による `condition_gates` の取得。
5. (前 wave から継続) 探索 loop への meaning 配線 + offline 供給 + admission 永続化、SS2PL (T-2737 §7)、S2 の Pegasus 固定値。
6. 古い文言: `make_define_request` の error 文 `22-macro domain` (現物 40)。

## 8. 変異による裏取り

事前登録は `verbatim/ruling.md` (m0〜m8) と `verbatim/ruling-s6.md` (m4 → m4′、段 6 レビュー A/B の等価性指摘で訂正)。runner = `tools/mutation_worktree.py` (独立 shared clone `mutation-source` を source、固定 commit `b250dc9a9`、dispatch mode、`tools/run_tests.py --force-dispatch test_condition_meaning_gate.py test_s8a_trigger_sweep.py test_silo_ladder_rung1_driver.py test_s1_direct_comparison.py -q -rf` = 445 test)。

| 走 | spec | 結果 | 台帳 |
|---|---|---|---|
| probe (15:08〜15:36 JST) | `verbatim/mutation-spec-probe.json` (sha256 `3f48e9e0673ce1b2…`、全変異を SURVIVED・期待 node 空で登録し観測 node を集める、DW-M07 の probe) | baseline PASSED (32.3 s)、m0 SURVIVED、m1〜m8 は MISMATCH (= 観測 node が記録された) | `verbatim/mutation-ledger-probe.json` |
| final (15:36〜15:46 JST) | `verbatim/mutation-spec-final.json` (sha256 `955da7da64457083…`、probe の観測 node を完全集合として登録) | **baseline PASSED (32.5 s)、m1〜m8 KILLED (期待 node 完全一致 8/8)、m0 等価 SURVIVED、MISMATCH 0** | `verbatim/mutation-ledger-final.json` |

| id | 変異 (file / 置換) | 結果 | 落ちた node (帰属) |
|---|---|---|---|
| m0 | G `_CONDITIONAL_BRANCH_SITE_COUNTS` の GATING 行末に comment | SURVIVED (等価、期待どおり) | — |
| m1 | C `default_value=None if macro == MISATTR_DEFINE else 0` → `default_value=0` | KILLED 1/1 | S `test_coverage_condition_gate_passes_exact_factory_pair[misattr]` (実 helper の request.default 観測、単一理由) |
| m2 | C `declaration=…declare_define_runtime_meaning(request)` → `declaration=None` | KILLED 2/2 | 同 `[misattr]` `[gating]` (declaration の型、単一理由) |
| m3 | G GATING の N 12 → 11 | KILLED 9/9 | T: 登録簿 / patch 束縛 (`[pair]*N` の独立期待 12 と `_declared_site_count` の比較) + GATING の全正負例 (`accepts_each_registry_macro`、`new_branch_selection…`、`multisite_rejects…[directive/inactive/partial-default/undef]`、`multisite_assert…`、schema 正例) = fixture が 12 箇所を作るため 11 との不一致 `site-count-mismatch` が波及。単一 seam (宣言 N) だが node は多い |
| m4′ | G `or default_counts != default_expected:` → `or default_counts[1] != default_expected[1]:` (対照 selected 検査だけ除去) | KILLED 4/4 | T `test_multisite_assert_rejects_default_partial_selection[RUNG1/GATING]` (独立 node、評価側の直接検査 = 意図した帰属) + `multisite_rejects…[partial-default-*]` 2 件 (公開 evaluator: 評価側が通した (1,N) を record 発行時の schema が `admission-contract-invalid` で拒否し reason の assert が落ちる = 別防壁の検出。kill の成果は前者で数える) |
| m5 | G schema の default selected 期待を record 値に置換 | KILLED 4/4 | T `test_new_branch_green_schema_rejects_count_value_and_argv_mutations[3 macro]` + 既存 `test_compile_time_green_schema_rejects_missing_or_mutated_observations` (schema seam) |
| m6 | G supply の不在検査を `if False and …` で無効化 | KILLED 3/3 | T `test_undefined_contrast_rejects_compile_define_in_supply[tokens0 / tokens2]` (`=0` の 2 形が green 化 = 不在検査単独の検出) + `[tokens1]` (裸 `-DM` は値 1 = 要求と同じで `preprocess-bytes-identical` の別理由の赤、reason の assert が落ちる。単独の kill 正例には数えない) |
| m7 | G 登録簿の MISATTR entry 3 行を削除 | KILLED 12/12 | T の MISATTR 正例 / `#ifdef` factory 正例 / schema / supply 3 形 / 外側条件負例 2 + S `[misattr]` + 集合 pin (`test_v1_domain_and_claim_boundaries_are_exact`) + 登録簿 / patch 束縛。fixture は test 側の独立期待表から作るので KeyError ではなく factory None / unestablished による assert 落ち。多 node だが seam は 1 つ (entry 削除) |
| m8 (過剰拒否の正例) | G 不在検査の `_declared_contrast_is_undefined` 条件を削除 (全 `default=None` へ拡大) | KILLED 1/1 | T `test_if_macro_none_contrast_keeps_cmake_default_supply_behavior` (SORT 1/None の supply が現行どおり green であること = 受理集合を縮めすぎない正例、単一理由) |

DW-M02: 所見ゼロを変異なしで緑と数えていない。DW-M03: m4′ / m6 の過剰決定は上表で帰属を分けた。DW-M05: 変異中は親の worktree 編集と子の起動を止めた (mutation-source は独立 clone)。probe → final の 2 走は DW-M07 の手順で erratum ではない (probe は期待 node を集めるための登録)。

## 9. 逐語一覧

| file | 内容 |
|---|---|
| `verbatim/brief.md` / `verbatim/ruling.md` / `verbatim/ruling-s6.md` | 段 1 brief (P1〜P6)、段 4 裁定 (plan v2、変異事前登録 m0〜m8)、段 6 裁定 (m4′、fix-2、追記) |
| `verbatim/s2-plan.md`、`verbatim/s3-consult-{a,b}.md` | 段 2 plan、段 3 相談 2 本 |
| `verbatim/s5-author-impl.md`、`verbatim/s6-review-{a,b}.md`、`verbatim/s6-fix-{1,2}.md`、`verbatim/s6-focus-logs-before-fix.md` | 段 5 author 報告、段 6 レビュー 2 本、fix 2 巡の報告、fix 前の焦点走要約 |
| `verbatim/login-pre/`、`verbatim/login-before/`、`verbatim/login-after/`、`verbatim/stage6-compute/` | 段 1 前提実測 (5 cell)、変更前 (7 cell)、変更後 login (7 cell)、計算ノード (5 cell、bnode003) の CLI stdout.jsonl |
| `verbatim/nest-static-analysis.{sh.txt,out.txt}` | 各 directive 箇所の外側条件の静的列挙 |
| `verbatim/mutation-spec-{probe,final}.json`、`verbatim/mutation-ledger-{probe,final}.json` | 変異 spec 2 本と台帳 2 走 |
