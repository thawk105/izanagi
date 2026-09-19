# [T-2153] 意味 witness 対応集合を既存機構で届く範囲だけ広げた — (d)(e)(f) の 6 macro を実 TU で実測し、SORT_VARIANT と RUNG1_REPORT の 2 件を登録簿へ足した (15 → 17)

- 日付: 2026-09-19
- branch: `worktree-dev-wave-t2153-witness-6` (base = local main `657e1e5a7`、着手時 `a99425b66` から段 4 直前に ff-only で前進)
- 実装 commit: `7cc76d98b9e3eca34d8002f3078dca051c8be87b` (Codex `role=author` の実装 1 巡 + fix 1 巡を所有 path 限定で統合、統合は親)
- 対象: `orchestrator/campaign/condition_meaning_gate.py` の compile-time 枝選択 witness (D1490) 登録簿 `_CONDITIONAL_BRANCH_WITNESSES`、`orchestrator/campaign/silo_ladder_rung1.py` の meaning 評価配線 (1 行)、test 4 file
- 前 wave: `output/insights/2026-09-17/t2153-witness-else-nested/README.md` (13 → 15)、`output/insights/2026-09-17/t2153-s2-pegasus-calibration/README.md` (S2 実機)、entry 1195 (`output/insights/2026-09-02/t2153-meaning-witness/README.md`)
- 専用 handoff / job dir: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/` (probe 本体・cells.json 原本・launcher・log。repo には入れない)

## 1. 依頼と守った裁定

依頼は「残り 10 件のうち (d) `SS2PL_LOCK_IMPL` / `SS2PL_LOCK_KIND` / `SS2PL_DLR` / `SS2PL_WFG_DIAG`、(e) `SORT_VARIANT`、(f) `IZANAGI_SILO_LADDER_RUNG1_REPORT` を対象とし、各件を実 TU で witness が立つか実測してから対応集合へ足す。(b)(c) の機構変更 (定義/未定義の観測・複数箇所の代表選択) と S2 driver の Pegasus 4 固定値変更は scope 外 (理由を記録)。実装は `condition_meaning_gate.py` 系、Codex author (D95)。規律 2 を緩めない。追加 gate・一般化は scope 外」。

守った裁定: D1490 (witness は所有 TU の枝選択のみを主張)、D1491 (旧宣言経路と CLI の `--meaning-case` は `BACKOFF_FIXED` 固定のまま)、D1492 (配線は未確立一覧が実際に縮む driver だけ)、D1569 / D1613、D2141 (shadow 登録簿の結果は機構診断であり production 認証へ流用しない)。

## 2. 6 件の判定 (実測で確定)

| macro | 判定 | 所有 TU 内の directive | 実測 (login、official 同形供給) | 根拠 |
|---|---|---|---|---|
| `SORT_VARIANT` | **足した** | `#if SORT_VARIANT` ×1 (`cc/silo/transaction.cc`、EVOLVE-BLOCK 内) | supply green、meaning **green (1,1)/(0,1)**、admitted、未確立 [] | entry 1195 の「driver 配線が編集面を超える」は、配線が factory 呼び出し 1 行で済み、S1 (official sort_best cell の経路) は既配線で自動追随するため解消 |
| `IZANAGI_SILO_LADDER_RUNG1_REPORT` | **足した** | `#if IZANAGI_SILO_LADDER_RUNG1 && IZANAGI_SILO_LADDER_RUNG1_REPORT` ×1 (`cc/silo/ycsb_silo.cc`) | supply green (登録前後で前処理 digest・bytes 完全一致: `a14dc4657a72` / `2775e7dc9e93`、4,479,871 / 4,479,486)、meaning **green (1,1)/(0,1)**、admitted、未確立 [] | companion `IZANAGI_SILO_LADDER_RUNG1=1` の compile argv 下の footer 枝選択。entry 1195 の懸念「再注入で実 build に RUNG1=1 が無くても緑」は、唯一の公開 consumer `silo_ladder_rung1` が rung-liveness build でのみ REPORT を要求し RUNG1 を同時要求・実 compile argv 照合するため公開経路では到達不能 (§4 の境界) |
| `SS2PL_LOCK_IMPL` | **観測可能だが足さない** | 一意なのは複合行 `#if SS2PL_LOCK_IMPL == 1 \|\| SS2PL_WFG_DIAG` ×1 だけ。本来の意味を担う `== 1` ×15 / `== 0` ×4 は非一意 | shadow: supply red `dependency-closure-drift`、meaning green (1,1)/(0,1) | 複合行 1 本を代表にするのは entry 1195 が退けた「代表 1 箇所で macro 全体の意味を過大主張」= (c) 代表選択 (scope 外)。現行 patch は supply 拒否のまま (T-2737 §7 未裁定) |
| `SS2PL_WFG_DIAG` | **観測可能だが足さない** | 同じ複合行 ×1 のみ。`#if SS2PL_WFG_DIAG` ×44 は非一意 | shadow: supply red `dependency-closure-drift`、meaning green (1,1)/(0,1) | 同上 |
| `SS2PL_DLR` | **既存機構では届かない** | `#if SS2PL_DLR == 1` ×1 | shadow: supply red `compile-command-drift`、**meaning red `compile-command-drift`** ("requested/default owner compile commands differ beyond the tested define") | CMake が `DLR0`/`DLR1` marker define を同時に変えるため、meaning arm の argv 比較 (試験 macro の -D 以外は一致必須) で赤 |
| `SS2PL_LOCK_KIND` | **宣言不能** | 所有 TU `cc/ss2pl/transaction.cc` に directive なし (実体は `wfg.cc:64/74`、`ss2pl_lock.hh:52` の template 引数) | 現行 gate: supply green、meaning 未宣言 (admit) | factory は `source_rel ∈ spec.owner_tus` を要求 (header 不可、BACKOFF_NOINLINE だけ例外)。`owner_tus` 拡張は DefineSpec の意味変更 (supply arm の対象 TU も動く) で scope 外 |

登録簿の会員は 15 → **17**、供給 domain 39 のうち未対応は 23 → **21**。entry 1195 の「残り 10 件」は本 wave 後 **8 件** ((b) 1、(c) 3、(d) 4)。

## 3. 何をどう測ったか

すべて既存の部品。新しい機構は無い。

| 段 | 部品 | 現物 |
|---|---|---|
| brief 前 | production CLI そのまま (登録簿未変更) を login で 6 macro | `verbatim/login-pre/*.stdout.jsonl` (供給は前 wave M0b と同形: `-DCMAKE_PREFIX_PATH` 引数 + SOURCE_DIR ×3、BASE_DIR なし) |
| 段 5 (i) | Codex author が書いた使い捨て probe (shadow 登録簿を固有 module 名で読込、正準 module 不変、5 候補 × 要求 1 / 既定 0、REPORT は登録前後の supply 比較) を親が login で実行 | probe 本体 = job dir `t2153_witness_candidates_probe.py` (sha256 `09ed5c865864d5646c0bfeb6c46c94a9256a816a2fbf29dbd2bc1f365fd01389`、150 行、selftest PASS)、原本 `probe-out/cells.json` (977,781 bytes)。射影 `verbatim/s5-probe-result-summary.md`、入力 `verbatim/s5-probe-sidecar.json` |
| 段 6 | 最終 production 登録簿 (commit `7cc76d98b`) の CLI を official 同形供給で login と計算ノードで実走 | `verbatim/stage6-login/`、`verbatim/stage6-compute/` (bnode055、`10879.nqsv`、Elapse 12 s、job body は `compute-official-body.sh.txt`) |

official 同形供給 = env `CMAKE_PREFIX_PATH=<gflags-install>:<glog-install>` (official job body `tools/pegasus/floor_campaign.sh` の export と同形) + `-DFETCHCONTENT_BASE_DIR=<scratch>` + `-DFETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}=/work/1/SFC/tanab/izanagi-thirdparty-cache/<name>` (`s8b_floor_campaign._condition_gate_offline_configure_args` と同じ 4 引数、masstree cache は `config.h` あり)。compiler g++ 11.4.0、cmake 3.22.1。patched tree は現行 pin `511c953` の shared clone に各 patch を `git apply` (scratch `/work/1/SFC/tanab/dev-wave-scratch/t2153-witness-6-20260919/`)。

**login と計算ノードで、SORT / REPORT とも前処理 digest・bytes・owner TU sha・compiler が完全一致** (SORT `ff30961ccf8d` / `527b6edff128`、4,471,878 / 4,471,661、owner `4a6c99d88c13`; REPORT 上表)。

## 4. 主張の境界 (正直に書く)

- witness が確立するのは D1490 のまま「所有 TU において、その define の値が宣言した枝の選択を決めている」で、動的到達性・枝本文の正しさ・runtime 異常の発火は主張しない。REPORT はさらに **companion `IZANAGI_SILO_LADDER_RUNG1=1` を含む compile argv の下で** footer 枝が選ばれることまでで、footer の実行や報告値の正しさは主張しない。
- **companion の保証は gate 単体には無い。** `_effective_companions` は spec の companion を補完して gate 自身が注入するので、CLI で REPORT 単独を要求すれば実 build に RUNG1 が無くても green が出る。公開 driver 経路 (`silo_ladder_rung1` の liveness configure `[RUNG1, REPORT]` + `validate_compile_argv`) では欠落しない。
- 単体 test の正例は実 patch の directive 逐語を持つ **合成 fixture** + 実 compiler。実 TU の実走は §3 の login / 計算ノード cell が担う。
- REPORT の登録で supply の対照 build root が別 root から要求側との共有へ移る (CXX_FLAGS route の既存 15 macro と同形)。同一入力で前処理 digest・bytes は一致したが、任意の CMake cache 履歴に対する受理集合包含の証明ではない (backlog、§7)。
- 受理集合: meaning arm 単独では狭まる向きだけ (unestablished admit → green admit / red reject)。official (s8b floor / oracle) の sort_best cell では S1 の既配線により本 wave 後に初めて SORT の meaning arm が走る。§3 の official 同形 cell は green だが、実 campaign での record はまだ無い。

## 5. 配線 (D1492)

| driver | 扱い | 理由 |
|---|---|---|
| `silo_ladder_rung1._require_condition_gates` | **配線した** (`declaration=None` → factory、1 行) | REPORT を rung-liveness build で要求し、admission を `gap_leg.condition_gates` として `silo_ladder_rung1.json` へ保存する |
| `s1_direct_comparison._condition_records_for_genome` | 変更なし (既配線) | `_CONDITION_DEFAULTS` に SORT_VARIANT: 0 があり、sort_best (要求 1) で factory が自動発火し `condition_gate_receipt` へ載る |
| `p3_s4_loop_sort._require_condition_gate` | **配線しない** | 返却 dict の `condition_gate` は CLI で表示のみで永続化されず、capture が offline 供給引数を渡さない (meaning arm の導入は探索 loop の受理を環境要因で変えうる) → 別変更単位 (§7) |
| `s6_sort_sweep._preflight_condition_gate` | **配線しない** | 返り値を捨て provenance にも保存しない |
| `tools/pegasus/run_ss2pl_lock_study.py` | 対象外 | KIND 0 vs 1 / DLR 0 vs 1 で登録簿の 1/0 対と不一致、現行 patch は supply 全 arm 拒否 (T-2737) |

## 6. 段ごとの所見 (要点)

- 段 2 plan: REPORT fixture は所有 TU を CMake target へ足す必要 / 共通 test fixture `SORT_VARIANT_SOURCE` に `#if SORT_VARIANT` ×2 → 登録後 `start-not-unique` / P3 の「届かない」は強すぎる / companion 保証は driver 契約 / REPORT は supply 実行形が変わる。
- 段 3 consult A (正しさ境界): REPORT の登録前後 supply 比較を事前登録 (採用) / P2・P3 を同基準で裁く (採用、P3 を「観測可能だが採用しない」へ) / companion 保証は公開 driver に限定 (採用) / 変異帰属の整理 (採用) / 事前実測は official 同形でない (採用、BASE_DIR + env PREFIX_PATH へ) / 旧経路・shadow 分離は反証。
- 段 3 consult B (過剰・削除): S6 は admission 非永続で配線対象外 (採用) / official 供給の実形 (採用) / `test_s8b_oracle_driver` を閉包に (採用) / pin 表 (tuple・patch 宣言・REPORT target・SORT 二重 directive・provenance = must、B-4 module 数・known-axes・rung1 自己 hash・oracle manifest・check_docs = 不要)。
- 段 5: author (probe → 実装) は sandbox の `qstat -Q` preflight で test 未実走 (rc=16)、親が計算ノード dispatch で実走。焦点走 1 = 371 passed / 2 failed (REPORT 正例: supply `preprocess-output-empty`、toy fixture の所有 TU が `#if…#endif` だけで既定 0 の前処理出力が 0 byte、F29 型の代表性)、焦点走 2 (consumer 7 file) = 925 passed / 9 skipped (344.57 s、上位所要はすべて既存 t080 系)。
- 段 6 review A / B: 両方 NO-GO (must = REPORT fixture、変異登録の訂正、official 同形確認と insight; nit 採用 = rung1 の実 helper 検査、companion 負例の位置づけ; 反証 = bytes 不変、主張境界、S1 fixture、B-4 pin、凍結 hash)。fix 1 (Codex): REPORT fixture に無条件行、rung1 実 helper test (evaluator を観測 wrapper、factory / 登録簿は実物)、companion 負例 docstring。再走 = **374 passed**。閉包焦点走 (B-4 wiring probe / ccbench_spawn_sites / rung1 ×2 / s8b materialization・pilot / build_site_gate / mocc ×2) = **350 passed / 2 skipped**。
- 焦点再レビュー: GO (新規 must-fix / regressed なし)。A/B 所見の closed 表は `verbatim/s6-focus.md`。partial = 変異結果・受入・insight commit・変異の帰属表 (本 README §8 と受入・land の受領証で親が閉じた)。
- 全史 provenance 監査 (統合 commit 後): 11,631 件、新規違反なし。

## 7. scope 外 (裁定パッケージ候補、実装しない)

1. 探索 loop (`p3_s4_loop_sort` / `s6_sort_sweep`) への meaning 配線 + offline 依存供給 + admission の永続化。
2. 共有 build root の cache 履歴依存 (consult A-1) に対する gate 側の対照 (人工 CMake fixture)。実 CCBench では CXX_FLAGS route が毎 configure `-DCMAKE_CXX_FLAGS=…` を明示するため反例は成立しない。
3. SS2PL: 代表枝の採用方針・patch 改訂 (T-2737 §7)・`owner_tus` 拡張。S2 driver の Pegasus 4 固定値。
4. 探索 loop の capture に offline 供給引数が無い問題 (consult B-2)。

## 8. 変異による裏取り

事前登録は `verbatim/ruling.md` (m0〜m7)、spec は `verbatim/mutation-spec.json` (sha256 `ae0ce806c52c…`)、再登録 spec は `verbatim/mutation-spec-m7.json` (`1fe17af9153b…`)。runner = `tools/mutation_worktree.py` (独立 shared clone `mutation-source` を source、固定 commit `7cc76d98b`、dispatch mode、`tools/run_tests.py test_condition_meaning_gate.py test_silo_ladder_rung1_driver.py test_s1_direct_comparison.py -q -rf`)。

| 走 | 結果 | 台帳 |
|---|---|---|
| run 1 (22:52〜23:06) | **baseline PARSE_ERROR** (受領証行 0、stdout 空、rc=1、85.7 s) で harness が中止。親が保持 container 内で同じ command を手動実走 → 374 passed (dispatch 10924) = 一過性。resume command は baseline を再走せず同じ理由で中止 (別 scratch root + 新 --out で走り直し)。**erratum として残す** | `verbatim/mutation-ledger-run1-baseline-parse-error.json` |
| run 2 (23:12〜23:33) | baseline PASSED (374 passed、queue 待ち込み 428 s)。**m1〜m6 KILLED (期待 node 完全一致 6/6)、m0 SURVIVED (等価、期待どおり)、m7 MISMATCH (期待 4 node に対し実 9 node)** | `verbatim/mutation-ledger-run2.json` |
| m7 再走 (23:35〜23:53) | baseline PASSED。**m7 KILLED (9/9 完全一致)、m7b KILLED (3/3 完全一致)** | `verbatim/mutation-ledger-m7-rerun.json` |

最終集計: 9 変異 (m0〜m7 + m7b) = **8 KILLED + 等価 1 SURVIVED、MISMATCH 0、期待 node 完全一致 8/8** (m7 の初回は probe と明記した erratum)。

| id | 変異 | 結果 | 帰属 (単一理由か) |
|---|---|---|---|
| m0 | 登録簿近傍 comment の等価変更 | SURVIVED (期待どおり、等価) | — |
| m1 | 登録簿から SORT entry 削除 | KILLED 7/7 | tuple pin・domain pin・SORT 正例 2 + `#undef` 負例・registry 正例 [SORT] は fixture builder の登録簿 lookup **KeyError**、S1 正例は宣言型 assert。meaning の unestablished 検出に一括帰属しない |
| m2 | 登録簿から REPORT entry 削除 | KILLED 7/7 | 同上 (fixture 経由 4 件は KeyError)、rung1 実 helper test は宣言型 None。getsource pin は落ちない (期待に含めない) |
| m3 | REPORT の登録 directive から companion operand を落とす | KILLED 1/1 | patch 束縛 test のみ (test 側の独立逐語との不一致)。fixture は登録 directive から作られるので他 REPORT test は通る — 独立 patch pin が必要な変異 |
| m4 | rung1 配線を `declaration=None` へ戻す | KILLED 2/2 | getsource pin + 実 helper test (REPORT 宣言型の不一致) |
| m5 | factory が 0/0 でも宣言 (受理拡大) | KILLED 3/3 | 非対値 test の 3 macro × `0-0` のみ。`0-1` は `default != "0"` が残るため SURVIVED (期待どおり含めない)。宣言可能集合の拡大の検出であり family admit の証明ではない |
| m6 | 共通 fixture の外側 `#if SORT_VARIANT` 塊を復元 (test 側) | KILLED 3/3 | SORT 正例 2 = `start-not-unique`、`#undef` 負例 = 無条件値差分が消え supply green 前提の崩壊。一意性検出に一括帰属しない |
| m7 | `_effective_companions` が spec companion を補完しない | 初回 MISMATCH (4 期待 / 9 実) → 再登録後 KILLED 9/9 | **過剰決定** (DW-M03): `make_define_request` が spec companion を request へ写すため、補完しない mutant では全 REPORT request が `request-contract-invalid` (companion undeclared) で落ちる = request 契約の検出であって meaning 単独ではない。非対値 4 + rung1 実 helper も同じ理由 |
| m7b | `_configure_defines` が companion を configure へ注入しない (注入 seam のみ) | KILLED 3/3 | registry 正例 [REPORT] と REPORT 正例 2 = 両 arm の `companion-define-mismatch`。companion 欠落負例は理由コードが同じなので検出しない (期待に含めない) |

DW-M02: 所見ゼロを変異なしで緑と数えていない。DW-M05: 変異中は親の編集と worktree へ書く子の起動を止めた (mutation-source は独立 clone、共有木観測は 3 走とも一致)。

## 9. 逐語一覧

| file | 内容 |
|---|---|
| `verbatim/brief.md` / `verbatim/ruling.md` | 段 1 brief (P1〜P7)、段 4 裁定 (plan v2、変異事前登録) |
| `verbatim/s2-plan.md`、`verbatim/s3-consult-{a,b}.md` | 段 2 plan、段 3 相談 2 本 |
| `verbatim/s5-author-probe.md`、`verbatim/s5-author-impl.md`、`verbatim/s5-probe-result-summary.md`、`verbatim/s5-probe-sidecar.json` | 段 5 author 2 巡の報告、probe 結果要約、probe 入力 |
| `verbatim/s6-review-{a,b}.md`、`verbatim/s6-fix-1.md`、`verbatim/s6-fix-1.patch.txt`、`verbatim/s6-focus-logs-before-fix.md`、`verbatim/s6-focus.md` | 段 6 レビュー 2 本、fix 報告と差分、fix 前の焦点走要約、焦点再レビュー |
| `verbatim/login-pre/*.stdout.jsonl` | brief 前の production CLI 6 走 (登録簿未変更) |
| `verbatim/stage6-login/*.stdout.jsonl`、`verbatim/stage6-compute/*` | 最終登録簿での official 同形 cell (login / 計算ノード) |
| `verbatim/mutation-spec.json`、`verbatim/mutation-spec-m7.json`、`verbatim/mutation-ledger-run1-baseline-parse-error.json`、`verbatim/mutation-ledger-run2.json`、`verbatim/mutation-ledger-m7-rerun.json` | 変異 spec 2 本と台帳 3 走 (run 1 は erratum) |
| `verbatim/s6-focus-logs-after-fix.md` | fix 後の焦点走・閉包走・official 同形 cell の要約 |
