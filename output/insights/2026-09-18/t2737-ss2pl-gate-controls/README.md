# [T-2737] SS2PL runner の condition gate 問題 — (ii) patch の define 差分化と (iii) warm-up の対照材料 (2026-09-18)

authority: none
default_effect: no-state-change

- wave: `dev-wave-t2737-ss2pl-gate-controls` (branch `worktree-dev-wave-t2737-ss2pl-gate-controls`、基底 main `d2ebef7a4`)。repo の実装面差分は 0 byte (docs + この insight だけ)。
- 起点: ユーザー裁定 D2120 項 12 (2026-09-17) と `/dev-wave [T-2737]` 引数。一次資料 = `output/insights/2026-09-17/t2644-ss2pl-wfg-connect/README.md` §5 の 1〜3。
- 逐語: `verbatim/` (段 1 brief、段 2 plan、段 3 レンズ A / B、段 4 裁定、段 5 author 報告、段 6 fix 2 巡と レビュー 2 本、prompt 全部、probe 本体と試作 patch 2 本の `.md` 逐語)。受領証: `receipts/` (計算ノード 2 job の probe 受領証 JSON 原本と cell 表の射影、dispatch log、patch 差分 `.diff.txt`)。
- 計測: 計算ノード 2 job (`0:5036.nqsv` bnode022 = fix2 前、`0:5051.nqsv` bnode048 = **主資料**、各 150 秒前後)。性能値・trial は取っていない。

## 0. 先に限定すること (段 3 / 段 6 レンズ A の所見を採用)

1. **D2120 項 12 が要求する「stock 側 `ycsb_ss2pl.exe` target / owner TU の成立を含む比較」は、gate 不変では構造的に成立しない。** stock の `cc/ss2pl/CMakeLists.txt` は `WORKLOADS bomb tpcc` で `ycsb_ss2pl.exe` を持たず、gate の `_select_owner_entry` は `CMakeFiles/ycsb_ss2pl.exe.dir/` 配下の `transaction.cc` の compile entry を stock に要求する。試作 patch をどう変えても stock 側は変わらないので、inert arm (S) の 4 要求は現行登録簿では必ず `owner-tu-unresolved` (KIND は companion を stock へ渡すので手前の `configure-failed`) になる (§3 の current/O/S と revs/O/S、計算ノードで 2 job とも同じ)。
2. 本文書の **shadow 登録簿 T+ / T− (target を `tpcc_ss2pl.exe` に差し替え) の結果は機構診断**であり、production の認証や certified 選択に流用しない。tpcc target の owner TU が一致しても、runner が測る `ycsb_ss2pl.exe` の TU の「stock 逐語」(D790) は別命題である (`SS2PL_WORKLOAD_YCSB` で囲んだ差分は tpcc 側では消え ycsb 側では残る)。
3. 採否は書かない。本文書は再提示用の材料 (§6 の 1 表と §7 の裁定パッケージ案) までを置く。

## 1. 何を測ったか

### 1.1 試作 patch 2 版 (job dir のみ、repo の `patches/` へは入れない)

`verbatim/patch-revs.md` (revS、86,721 bytes、sha256 `8ccb4c59…`)、`verbatim/patch-abort-unconditional.md` (86,612 bytes、`f0b48d2c…`)。現行 patch からの差分は `receipts/current-vs-revs.diff.txt` (2,843 行)、2 版の差分は `receipts/revs-vs-abort-unconditional.diff.txt` (abort ブロックの `#if/#else/#endif` だけ。hunk offset と index hash は派生差分)。

revS = 「gate 不変のまま非 inert の drift を閉じ、S arm (IMPL=0, KIND=1, DLR=1, WFG=0) の owner TU 前処理 bytes を stock に近づける」最小改変。段 4 裁定 (`verbatim/s4-ruling.md`) の固定範囲:

| # | 変更 | 閉じる drift |
|---|---|---|
| a | `ss2pl_lock.hh`: `rwlock.hh` と `ss2pl_study_lock.hh` を無条件 include、alias `using ReaderWriteLock = SS2PLStudyLockT<…>` だけ `#if SS2PL_LOCK_IMPL == 1`。`#error "SS2PL_DLR=n requires DLRn"` 撤去。`IMPL==0 && DLR==2` は `#error` | IMPL の `dependency-closure-drift` |
| b | `include/rwlock.hh`: `class ReaderWriteLock` だけを `#if !defined(SS2PL_LOCK_IMPL) \|\| SS2PL_LOCK_IMPL == 0` で囲む hunk を追加 (include 群と `#pragma once` は保持) | a の名前衝突回避 |
| c | 新規 header 3 本を `#pragma once` から include guard へ。study header は依存 include 無条件・宣言と定義は `#if IMPL==1` 内。`ss2pl_wfg.hh` は `<cstdint>` `<string>` 無条件・宣言は `#if WFG` 内。transaction.cc の `ss2pl_wfg.hh` include を無条件化 | WFG の `dependency-closure-drift`。`#pragma once` は `-E -P` で 7 空白 + 改行の残渣を残す (login 実測) |
| d | CMake: `_ss2pl_dlr_marker` 分岐を撤去し stock どおり `OPTIONS DLR1` 固定。stock transaction.cc の `#ifdef DLR0 / #elif defined(DLR1)` 5 組を `#if SS2PL_DLR == 0 / #elif SS2PL_DLR == 1` へ | DLR の `compile-command-drift` |
| e | **`wfg.cc` は CMake の `if(CCBENCH_SS2PL_WFG_DIAG EQUAL 1)` 条件のまま** (plan は無条件化を提案したが、runner の `validate_wfg_absence` が source 名の `wfg` を拒否する。owner TU の閉包には無関係なので不要) | — |
| f | abort 増分 (`TxExecutor::abort()` の `++result_->local_abort_counts_`) を `#if defined(SS2PL_WORKLOAD_YCSB) && SS2PL_WORKLOAD_YCSB` / `#else` 増分 / `#endif` の形で非 YCSB に戻す | S の stock 一致 (tpcc target) |
| g | S 復元: `common.hh` の legacy `DEFINE_*/DECLARE_*` 削除、`transaction.hh` の include 位置と constructor、`begin()`、`update()`、`delete_record()` の `break`、既取得ロック検査、`unlockList()` の brace、`insert()` の brace (fix1) を、IMPL=0・WFG=0・非 YCSB のとき stock 本文になるよう戻す | S の stock 一致 |

abort 無条件除去版 = revS から f だけを現行どおり (無条件除去) にした版。gate の負例対照 (S で必ず `stock-inert-mismatch` になるべき) と、runner の abort 所有権契約 (`validate_abort_counter_ownership`) との衝突を可視化する対照。

**足していないもの:** 新しい lock 意味論、KIND を IMPL=0 で効かせる細工、`#line` 指令、gate・runner・登録簿 (repo 側) の変更。

### 1.2 shadow 登録簿 (probe が job dir に生成、repo の gate は不変)

gate module の写しに、SS2PL 4 entry の完全一致 block 置換だけを施した 3 種: **O** = repo と byte 同一、**T+** = 4 行の `target` を `tpcc_ss2pl.exe` に、**T−** = T+ に加えて `SS2PL_LOCK_KIND` の companion `(("SS2PL_LOCK_IMPL","1"),)` を `()` に。受理条件は「repo bytes に許可置換だけを施した期待 bytes との全体一致」(selftest に `inert_values` / `owner_tus` / 式 / 非 SS2PL entry / logic の混入を拒否する負例 5 本)。読込は `orchestrator.campaign._t2737_gate_<id>` の固有名で `sys.modules` に登録し、正準 module を置き換えない (相対 import は repo の実 `source_digest` 等へ解決、`_patch_changed_paths` は shadow root の patch を読む。identity は受領証 `shadows[]`)。

### 1.3 cell と実行順 (45 cell、1 cell = 1 arm の 1 軸の supply + meaning)

runner の `_require_condition_gates` (R:1980-2045) と同じ 3 呼び出し (`capture_define_inputs` → `make_define_request(default=AXIS_DEFAULTS, stock_comparison=requested==default)` → `evaluate_define_supply_effectuation` / `evaluate_define_runtime_meaning(declaration=None)`) を shadow module ごとに同じ instance で行い、4 軸そろった組だけ `require_condition_gate_family(use_class="raw-measurement")`。`configure_args` は R:1988-2003 と同じ組み方 (軸 cache key を除外、`-DFETCHCONTENT_BASE_DIR` は渡さない)。順序: pristine 8 → warm-up → 対応 warm 8 → KIND 固定 target 対 → abort 対照 4 → plain build 2 → 残り 20。staging は保存用 pristine (`<job dir>/thirdparty-src`、hydrate 出力、masstree `config.h` 無し) を attempt ごとに `cp -a` した複製で、原本は job 前後で不変 (受領証 `staging_original` / `staging_original_after`)。

### 1.4 計算ノード job

| job | request | node | probe | 所要 | 位置づけ |
|---|---|---|---|---|---|
| 1 | `0:5036.nqsv` | bnode022 | fix2 前 (sha `418448c9…`) | 157 秒 (PBS)、probe 152 秒、rc=1 | warm-up が `FETCHCONTENT_BASE_DIR` の dir 未作成で `BuildCacheError` (probe の欠陥、`prepare_masstree_fetchcontent` は既存 dir を要求。t316 probe は `mkdir` している)。warm 系 cell は `config.h` 不在で無効。ただし plain build (S 25 秒 / phase1 6 秒、成功) が masstree を build して staging に `config.h` を作ったため、**その後の 20 cell (current/O/S、current/T−/S、revs/O/S、revs/O/phase1、revs/T+/S の 5 組 × 4 軸) は `config.h` を観測しており有効** (16 cell は期待 reason と完全一致、revs/T+/S の 3 cell は条件付き予測どおり M) で job 2 と同じ結果。job 1 の probe (v1) の逐語は insight に置かず、sha256 と job dir `probe-v1/` で同定する |
| 2 | `0:5051.nqsv` | bnode048 | fix2 後 (sha `6ffae7be…`) | 149 秒 (PBS)、probe 144 秒、rc=0、`status=complete` | **主資料**。45 cell すべて予測と一致 (条件付き予測 I は S 一致未達なので M)。internal exception 0、予算未実施 0。`c++` = `/usr/bin/x86_64-linux-gnu-g++-11` 11.4.0、cmake 3.22.1、`tempfile.gettempdir()=/tmp` (空き 138.6 GB) |

## 2. 実測結果 — 45 cell (job 2、warm = helper warm-up 後。軸順 IMPL / KIND / DLR / WFG)

記号: O=`owner-tu-unresolved`、C=`configure-failed` (stock configure の stderr に CMake 警告 `Manually-specified variables were not used by the project: CCBENCH_SS2PL_LOCK_IMPL`)、D=`dependency-closure-drift`、A=`compile-command-drift`、M=`stock-inert-mismatch`、B=`preprocess-bytes-identical`、E=`requested-default-preprocess-different` (green)、P=`preprocess-failed` (stderr に `fatal error: config.h`)。meaning は全 cell `unestablished / meaning-witness-undeclared` (runner と同じく declaration=None)。

| patch / 登録簿 | staging | S | phase1 | family admitted |
|---|---|---|---|---|
| current / O | pristine | — | P / P / P / P | false |
| revS / T− | pristine | P / P / P / P | — | false |
| current / O | warm | O / C / O / O | D / E / A / D | false / false |
| current / T− | warm | M / M / M / M (残差 3,666 行) | — | false |
| revS / O | warm | O / C / O / O | **E / E / E / E** | false / **true** |
| revS / T+ | warm | M / C / M / M (残差 1 行) | KIND のみ: E | false |
| revS / T− | warm | M / M / M / M (残差 1 行) | E / **B** / E / E | false / false |
| abort 無条件版 / T− | warm | M / M / M / M (残差 218 行) | — | false |

「残差 n 行」は gate 自身の evidence `root_diff_line_count` (S の要求側と stock 側の前処理 bytes の差分行数。path 置換後)。細部は `receipts/cells-summary-2.json` (射影) と `receipts/probe-result-2.json` (原本、record の canonical JSON 全部)。

## 3. (ii) patch の define 差分化 — 成立した比較と成立しない比較

### 3.1 非 inert (phase1 = IMPL 1 vs 0、KIND 0 vs 1 (companion IMPL=1)、DLR 0 vs 1、WFG 1 vs 0): **patch だけで 4 軸とも green、登録簿変更なし**

| 軸 | 現行 patch (current/O/phase1) | revS (revs/O/phase1) | 閉じた変更 |
|---|---|---|---|
| IMPL | D (閉包不一致: `ss2pl_study_lock.hh` の条件 include) | E (閉包一致、bytes 4,911,267 vs 4,893,887) | 1.1 の a・b |
| KIND | E (現行でも green) | E (byte 長は 4,911,267 で同じだが digest 相違、companion IMPL=1 で効く) | — (現行から直す drift は無い) |
| DLR | A (argv 差 `-DDLR0` vs `-DDLR1`; 閉包は一致) | E (4,893,500 vs 4,893,887) | 1.1 の d |
| WFG | D (閉包不一致: `ss2pl_wfg.hh` の条件 include) | E (4,896,264 vs 4,893,887) | 1.1 の c |

family admission は `revs / O / phase1 / warm` だけが `admitted=true` (2 job とも)。試作は a〜d を束ねた 1 版なので、各 hunk 単独の必要十分性までは実測していない (段 6 レビュー B の B2)。試作 patch は S と phase1 の `ycsb_ss2pl.exe` を `-Wall -Wextra -Werror` で build でき (job 2: S 12 秒、phase1 5 秒)、S build に対する runner の `_wfg_absence_evidence` は accepted (3 TU、`wfg.cc` は source list に無い)。

### 3.2 inert (S): **gate 不変では成立しない。層ごとに何で止まるか**

| 層 | cell | 結果 | 読み |
|---|---|---|---|
| 現行登録簿 (target ycsb) | current/O/S、revs/O/S | O / C / O / O | patch を何に変えても stock に `ycsb_ss2pl.exe` が無い限りここで止まる (§0-1)。KIND は companion `SS2PL_LOCK_IMPL=1` を stock configure に渡すため手前の C |
| target を tpcc に (shadow T+) | current/T−/S | M (3,666 行) | 現行 patch は S でも stock から大きく離れている (`INERT_DECLARED_DIFFERENCES` の 3 箇所以外に無条件差分あり、段 2 plan §2) |
| 同上 + patch を revS に | revs/T+/S | M (1 行) / C / M (1 行) / M (1 行) | 復元で残差は **1 行** (計算ノード receipt の `root_diff_line_count=1`)。その 1 行が `ERR` macro の展開する `__LINE__` (stock 97 行目、revS 154 行目) であることは login の `-E -P` diff (`verbatim/probe-readme.md`) が根拠で、receipt の行数だけでは内容は特定できない。今回の固定復元範囲では消えず、`#line` 指令による同期は未実施 (試作には入れていない)。KIND は companion のため C のまま |
| 同上 + KIND の companion を外す (shadow T−) | revs/T−/S | M (1 行) ×4 | KIND も owner entry と前処理まで進むが同じ 1 行の残差で M |
| 負例対照 | abort 無条件版/T−/S | M (218 行) | abort 増分を無条件除去すると差分行数が 1 → 218 に増える (gate は行位置を揃えて数えるので 1 行の削除で後続行がずれた分も含む。意味変更の箇所数ではない)。両版とも red なので「abort 単独で green → red を反転させた」対照は未成立。差分行数の増大の対照までである |

**KIND の緊張 (段 1 の P2、実測で確定):** companion ありでは S の KIND が C (stock に companion を渡せない)、companion なしでは phase1 の KIND が B (`revs/T−/phase1/kind` = requested と default の bytes digest 一致 = IMPL=0 では KIND は効かない)。同じ登録簿で S と phase1 の両方の KIND を通す形は、KIND が IMPL に従属する現設計では存在しない。解く形は (a) KIND を IMPL=0 でも効く直交軸にする (新しい lock 意味論 = 研究側の設計変更) か (b) KIND を IMPL に畳む (IMPL ∈ {0 stock, 1 study 排他, 2 study RW}; runner の `ARM_CONFIG` / `AXIS_*` / `CACHE_TO_DEFINE` と登録簿が変わる) のどちらか。本 wave はどちらも実装していない。

### 3.3 (ii) の費用と隙間 (採否材料)

- **TU / arm 束縛の隙間 (§0-2):** target=tpcc の shadow で S が一致しても、認証されるのは tpcc target の `transaction.cc` であり、測定する `ycsb_ss2pl.exe` の TU ではない。YCSB 専用 define (`SS2PL_WORKLOAD_YCSB`) で囲んだ差分 (abort 所有権の移動、common.hh の legacy flag 削除) は ycsb 側に残る。gate を「ycsb TU の stock 逐語」の防壁として使う目的には届かない。
- **`__LINE__` の残差:** 1.1 の g まで復元しても 1 行残る (login diff で `ERR` の `__LINE__`)。今回の固定復元範囲では消えなかった。`#line` 指令で行番号を stock に同期する案は未実施で、それが唯一の消し方かどうかは検証していない (他のソース配置の変更で消える可能性を排除していない、段 6 レビュー B の B7)。`#line` は gate の比較対象 (前処理 bytes) を人為的に揃える操作なので、試作には入れていない (`verbatim/s6-fix1-report.md`)。
- **runner の abort 所有権契約との衝突:** revS (f を `#if` で囲む) は `validate_abort_counter_ownership` (token 走査、`#if` を評価しない) に **拒否**される (`transaction=1, workload=2`)。abort 無条件版は受理されるが S の gate 比較は 218 行の M。「S の stock 一致」と「runner の abort 所有権契約」は現行の両契約のままでは同時に満たせない (受領証 `static_contracts`)。plain build の成功と WFG 不在検査の受理は、runner の全契約の受理を意味しない。
- `_study_lock_header_declarations` は 2 版とも受理。`_validate_compile_definitions` は plain build 2 本で受理 (`DLR1` 固定 + `SS2PL_DLR=0` の意味的矛盾を検査する code は runner に無い)。`collect_inert_witness` (宣言差分と実体の一致 flag) は**未実走**。revS では `INERT_DECLARED_DIFFERENCES` の transaction.cc 項が実体と合わなくなるので flag は false になりうるが、runner はそれを拒否理由にしない (R:1735-1747、段 3 レンズ B の B3)。
- B / D arm (DLR=2) は scope 外。試作は `IMPL==0 && DLR==2` を `#error` にしているので、gate の DLR=2 要求 (companion なし = IMPL=0 で比較) は前処理失敗で red になる。DLR=2 を通すには DLR にも IMPL=1 の companion (→ S での C) か、stock 経路の wound-wait 実装が要る。
- 規律 1: 性能 build (WFG=0) に計器 TU は入らない (`wfg.cc` は条件付き、S build の WFG 不在検査 accepted)。ただし `ss2pl_wfg.hh` は無条件 include (中身は `#if` で空) なので、閉包に header 名として現れる。

## 4. (iii) warm-up — 成立した比較

- **既存実装形が既にある (段 4 直前の裁定 inbox 再走査で判明、D2131 2026-09-18):** condition gate を通す 9 driver (`screening_driver`、`backoff_sweep`、`paper_story_a1/a2`、`b4_binary_record`、`s8b_floor_campaign`、`b10_backoff_static_tail_formal`、`backoff_extended_sweep`、t316 probe) はすべて `orchestrator/campaign/buildcache.prepare_masstree_fetchcontent` で masstree を準備してから関門へ供給する。**SS2PL runner だけがこれを欠く。** (iii) の実体は「runner に同じ 1 段を関門前に足す」であり、T-2644 probe の生 `cmake --build --target masstree_build` は D2131 が direct-cmake-target sink として却下した形。
- **対 (同じ staging 複製・同じ木、job 2):** warm-up 前 = pristine 8 cell が全部 P (`fatal error: config.h`、requested 側の前処理で止まるため stock 側は未到達)。`prepare_masstree_fetchcontent` 1 回 (ccbench_dir = revS clone、base = attempt 固有 dir、source dirs = 複製 staging、dependency_prefix = gflags;glog、**13.7 秒**、`config.h` 10,448 bytes sha256 `e9a4ecd3…`) の後 = 同じ 8 cell が §2 の値 (current/O/phase1 は D/E/A/D、revs/T−/S は M×4) に進み、**stock 側の前処理も通った** (S の M は stock 側 bytes との比較結果であり、stock 側前処理が成功した証拠)。`config.h` は共有 staging の masstree source dir に生成されるので、stock / current / revS の 3 clone すべてに効く。原本 staging は前後で不変。
- warm-up だけでは admission は 1 つも増えない (§2: pristine → warm で変わるのは reason_code が P から次の判定へ進むこと)。前後の不変は `config.h` の状態で見たものであり、staging 全 file の不変証明ではない。configure-failed 3 cell の診断 configure は rc=0 で、control 側 stderr 全文に CMake の未使用変数警告 (`CCBENCH_SS2PL_LOCK_IMPL`) が残る = gate の C は「rc≠0」ではなく「stderr 非空」による。job 1 では plain build の `cmake --build ycsb_ss2pl.exe` の依存として masstree が build され、同じ効果が偶然出た (helper でなく build graph 経由)。
- 費用: 13.7 秒 / job。`FETCHCONTENT_BASE_DIR` は既存 non-symlink directory かつ canonical path が必須 (job 1 の内部例外の原因。probe fix2 で t316 と同形の `mkdir` → `resolve(strict=True)` を入れ、selftest に入口検査の正負例を追加)。

## 5. probe と production の差 (F29)、主張しないこと

- probe (`verbatim/probe.md`、Codex `role=author` + fix 2 巡) は runner の production 関数 (`clone_network_free`、`_apply_patch`、`_expected_cache`、`_condition_request_inputs`、`_target_compile_entries`、`_validate_compile_definitions`、`_wfg_absence_evidence`、`validate_abort_counter_ownership`、`_study_lock_header_declarations`) と gate の production 関数を import して呼ぶ。runner の `build_target` / `run()` / `controls` mode は呼んでいない。gate 4 軸を 1 arm で通す形は runner と同じ「個別軸比較」であり、phase1 の全 define を同時に入れた TU の比較ではない。
- shadow は `DefineSpec` の宣言 (target / companion) だけを変えた診断で、gate logic は byte 同一 (受領証 `shadows[]` に期待 bytes 一致の検算)。
- **主張しないこと:** (ii)(iii) の採否、runner の `controls` / `sweep` が動くこと、D790 の inert 性、性能、runtime correctness、tpcc target での一致が ycsb TU の認証になること、B/D arm の成立。
- login の前検査 (author、`verbatim/probe-readme.md`): selftest 17 PASS、login-precheck rc=0 (前 wave の warm 済み staging を使用、pristine の証拠ではない)、S の `-E -P` `cmp` は不一致・残差 1 箇所 (`__LINE__`)。親も job dir の probe で selftest を実走 (rc=0、17 PASS、07:29 JST)。

## 6. 再提示用の 1 表

| 案・比較 | 成立した比較 (証拠 cell) | 成立しない比較 (証拠 cell) | 必要な変更層 | 費用・隙間 |
|---|---|---|---|---|
| (iii) warm-up | pristine → `prepare_masstree_fetchcontent` 1 回で stock / patched 両木の前処理が通る (job 2 pristine 8 → warm 8) | warm-up だけでは admission は変わらない | runner に 1 段 (他 9 driver と同形、D2131) | 13.7 秒 / job。base dir の事前作成が必要 |
| (ii) 非 inert IMPL / DLR / WFG | 試作 patch だけで E (revs/O/phase1、raw-measurement の admission=true) | — | patch のみ (1.1 の a〜d) | phase1 の study lock / WFG 計器の呼び出し保持は author の局所検査 (`work/check_phase1_projection.py`、include と pragma を除いた 6 file の個別前処理) で確認。最終版 (fix1 後) はその検査で transaction.cc が `insert()` の括弧 1 箇所だけ現行と異なり、完全な bytes 一致は未達。依存 header 展開・実 TU 全体・binary は射程外。B/D の DLR=2 は scope 外 |
| (ii) 非 inert KIND | companion ありで E (現行でも green) | companion なしで B (revs/T−/phase1/kind) | 登録簿 (companion) と軸設計 | KIND は IMPL に従属 → S と両立しない (3.2) |
| (ii) inert S、現行登録簿 | — | O / C (current/O/S、revs/O/S) | **stock に `ycsb_ss2pl.exe` が無い限り不可 (gate 不変の前提では層が無い)** | §0-1 |
| (ii) inert S、shadow T± | owner entry 解決、前処理到達、残差 1 行まで復元 (revs/T±/S) | M (残差 1 行、login diff では `__LINE__`)、KIND は T+ で C | patch (1.1 の f・g) + 登録簿 target (+ companion) + 残差 1 行の解消 (`#line` 同期は未実施・唯一性未検証) | tpcc の認証は ycsb TU の認証ではない (§0-2)。revS は runner の abort 所有権契約に拒否される。abort 無条件版は 218 行の M (両版 red、反転対照は未成立) |

## 7. 裁定パッケージ案 (採否は書かない。再提示のための択一の骨子)

1. **(iii) だけを採る:** runner の `_require_condition_gates` の前に `prepare_masstree_fetchcontent` を 1 段足す。効果は「pristine staging で gate が前処理まで進む」こと。gate の拒否理由は現行 patch のままなら §2 の current/O のとおり残るので、**単独では `controls` は動かない**。
2. **(ii) を非 inert 側だけ採る:** 試作 patch の a〜d (+ e) を本 patch へ入れる。phase1 型の arm (全軸が既定と異なる) は gate を通る。S 型・C 型の arm (既定と一致する軸を含む) は現行登録簿では通らないので、`controls` mode 全体はなお動かない。runner 側の `INERT_DECLARED_DIFFERENCES` と abort 所有権契約はそのまま。
3. **(ii) を inert 側まで採る:** 2 に加えて (a) 登録簿の `target` を stock に実在する target へ (gate logic は不変だが、認証対象 TU が測定 TU と別になる隙間を受け入れる)、(b) KIND の従属を解く軸設計 (3.2 の a か b、runner の軸表が変わる)、(c) `__LINE__` の残差を `#line` で同期するか、gate の inert 比較で `__LINE__` 差を許す拡張 (= gate の変更、本 wave の前提外) を選ぶ、(d) abort 所有権契約か S 一致のどちらかを譲る。**4 点すべてにユーザー判断が要る。**
4. **別案 (本 wave の前提外、列挙のみ):** SS2PL study を condition gate の対象から外す (= (i)、D2120 項 12 で不採用確定)、stock に ycsb target を足す pin 前進 (D16/D18 の手続き)。

## 8. 工数と逐語

- wave 所要: 06:20 JST 起動 → 段 5 author 06:52–07:16、fix1 07:19–07:23、fix2 07:27–07:30、計算ノード job 1 07:24–07:26、job 2 07:30–07:39、段 6 レビュー 07:41–。
- Codex 子: plan 1、consult 2、author 1、fix 2、review 2。計算ノード job 2 (各 150 秒)。
- 段 6 レビューの所見と裁定は `verbatim/s6-revA.md`、`verbatim/s6-revB.md`、`verbatim/s6-review-ruling.md`。
- sha256: probe `6ffae7beaa263fca7b769a6ef90e5d0273241793451c57b917bd837bcd96a61f` (38,745 bytes)、revS `8ccb4c59e467253c73f90f27b0891f5f67ba66311e9a65ca261582282580db50` (86,721)、abort 無条件版 `f0b48d2cd66712c87974634c0ce337c03536152632a766f3772bed3ac26d0130` (86,612)、job 2 受領証 `receipts/probe-result-2.json` (4,321,412 bytes)。
