# 段 4 裁定 — [T-2153] 意味 witness 対応集合 ((d)(e)(f) の 6 macro)

日付 2026-09-19。base = local main `657e1e5a7` (段 4 直前に `a99425b66` から ff-only で前進、本 wave 編集面への接触なし)。
入力: brief.md (P1〜P7)、plan.md、consult-a.md (レンズ A)、consult-b.md (レンズ B)。裁定 inbox (spool) に未 fold fragment なし。SS2PL patch 改訂 (T-2737 §7) は未裁定のまま — 本 wave は触れない。

## 所見の裁定 (real / refuted、採用 / 不採用、scope)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| plan-1 | REPORT の fixture は所有 TU `cc/silo/ycsb_silo.cc` を CMake target へ足さないと owner command が無い | real / 内 | 採用 (REPORT の場合だけ `target_sources(ycsb_silo.exe PRIVATE cc/silo/ycsb_silo.cc)` 相当を fixture 生成に加える。共通 helper の一般化はしない) |
| plan-2 | 共通 test fixture `SORT_VARIANT_SOURCE` に `#if SORT_VARIANT` ×2 → 登録後 `start-not-unique` | real / 内 (親が現物で確認) | 採用 (外側を `static constexpr int condition_gate_sort_variant = SORT_VARIANT;` の無条件値参照にし EVOLVE-BLOCK 内を唯一に。consumer test 3 本 + B3 の閉包を回帰) |
| plan-3 / A-2 | P3 の「既存機構では届かない」は強すぎる。複合行は観測可能、不採用理由は主張範囲・代表選択の scope・consumer の supply 拒否 | real / 内 | 採用 (P3 を書き換え、判定台帳は「観測可能だが採用しない」と「機構で届かない」を分ける) |
| plan-4 / A-3 | P2 の companion 保証は gate 単体に無く公開 driver 契約 (liveness configure が `[RUNG1, REPORT]` を同時要求 + `validate_compile_argv`)。CLI では REPORT 単独で発行される | real / 内 | 採用 (REPORT の主張を「companion RUNG1=1 の compile argv 下での footer 枝選択」に限定し、CLI 単独発行を主張境界として記録。driver 側の同時要求は既存 test が pin) |
| plan-5 / A-1 | REPORT 登録で supply の対照 build root が共有化 (G:1892) → family の「狭まる向きのみ」は meaning だけからは証明できない | real / 内 | 採用 (段 5 probe で REPORT の supply を登録前後で同一入力比較し、旧 red → 新 admit なら REPORT を保留)。A-1 の cache 履歴反例は実 CCBench には無い (CXX_FLAGS route は毎 configure `-DCMAKE_CXX_FLAGS=…` を明示、共有 root は既存 15 macro と同型) → 人工 CMake fixture は実装せず backlog |
| plan-6 / A-5 / B-5 | P5 の「template のみ」は誤り: KIND の directive は `wfg.cc:64/74` と `ss2pl_lock.hh` にある (所有 TU 内に無いだけ) | real / 内 | 採用 (記述を訂正) |
| A-4 | 変異の帰属競合 (supply が先に拒否する形は meaning 単独に帰属できない) | real / 内 | 採用 (事前登録を下記のとおり修正) |
| A-5 / B-2 | 親の事前実測は `FETCHCONTENT_BASE_DIR` 無し・`CMAKE_PREFIX_PATH` 引数ありで official 同形でない。official は BASE_DIR + SOURCE_DIR ×3 (引数) + env `CMAKE_PREFIX_PATH` (job body の export) | real / 内 / must | 採用 (段 5 probe と段 6 の最終実測を official 同形 = env CMAKE_PREFIX_PATH + `-DFETCHCONTENT_BASE_DIR=<scratch>` + SOURCE_DIR ×3 (cache、config.h あり) にする。段 6 は最終 production 登録簿で login 1 cell + 計算ノード generic dispatch 1 job (SORT + REPORT) を完了条件にする。SORT の official 同形 meaning が環境要因で赤なら SORT を land しない) |
| A-6 | 旧宣言経路 / CLI / shadow 分離への攻撃 | refuted | — |
| B-1 | `s6_sort_sweep` は gate の返り値を捨て provenance にも保存しない → 配線しても成果物の未確立一覧は縮まない | real / 内 (親が現物で確認) | 採用: **S6 は配線しない** (D1492、理由 = admission 非永続)。**p3_s4_loop_sort も配線しない**: 返却 dict の `condition_gate` は CLI で表示のみで永続化されず (親が現物で確認)、かつ capture が offline 供給引数を渡さないため meaning arm の導入は exploration loop の受理を環境要因で変えうる → 別変更単位 (裁定パッケージ候補: 探索 loop への meaning 配線 + offline 供給) |
| B-3 | consumer 回帰に `test_s8b_oracle_driver` (S1 実 record helper 経由) と `test_s8b_floor_campaign` が要る | real / 内 | 採用 (閉包表を段 5/6 の焦点走に含める、全体 5 分上限を author が確認) |
| B pin 表 | tuple pin / patch 宣言 helper / REPORT owner target / SORT 二重 directive / provenance author = must、他 (B-4 module 数、known-axes、rung1 自己 hash、oracle manifest、check_docs) = 不要 | real / refuted の混在 | 表のとおり採用 |
| B 削減案 | 配線全部後送 = refuted、probe 省略 = refuted、SS2PL 3 件の実測省略 = scope 縮小案 (ユーザー契約なので削らない)、計算ノード 1 本 = B-2 と兼ねる | — | SS2PL 3 件は probe で meaning 単独を診断として実測 (production 認証へ流用しない、D2141)。計算ノードは段 6 の official 同形 job と兼ねる |

## plan v2 (確定)

1. **登録簿 +2** (`orchestrator/campaign/condition_meaning_gate.py` `_CONDITIONAL_BRANCH_WITNESSES` 末尾、既存順維持): `"SORT_VARIANT": ("cc/silo/transaction.cc", "#if SORT_VARIANT")`、`"IZANAGI_SILO_LADDER_RUNG1_REPORT": ("cc/silo/ycsb_silo.cc", "#if IZANAGI_SILO_LADDER_RUNG1 && IZANAGI_SILO_LADDER_RUNG1_REPORT")`。docstring の件数 15 → 17。`DEFINE_SPECS` / factory / 計装 / 比較 logic / 旧宣言経路 / CLI は不変。
   **条件:** 段 5 probe で (a) SORT の meaning が official 同形供給で (1,1)/(0,1) 緑、(b) REPORT の meaning が緑かつ supply が登録前後で同一入力に対し admitted 不変 (旧 red → 新 admit なし)。満たさない macro は足さず、理由を insight に記録。
2. **配線:** `orchestrator/campaign/silo_ladder_rung1.py:2232` の `declaration=None` → `declaration=condition_meaning_gate.declare_define_runtime_meaning(request)` の 1 行のみ。S6 / p3_s4_loop_sort は配線しない (理由は上表 B-1、D1492 に従い driver 名付きで記録)。S1 は既配線で自動発火 (official sort_best cell)。
3. **test:** `_COMPILE_TIME_BRANCH_MACROS` +2 (末尾、登録簿と同順)、`_patch_added_branch_declaration` は REPORT の複合 directive を test 側の独立した期待逐語で patch から検索 (登録簿から取らない)、`T:988` を `[patch_declaration[1]]` へ、fixture builder は登録 directive を既定に使う、REPORT fixture は companion を `#define` せず既存注入経路で両 argv に RUNG1=1 があることを検査、REPORT の owner TU を fixture CMake target へ追加、共通 `SORT_VARIANT_SOURCE` の外側 directive を無条件値参照へ、非対値 test (1/None, 1/1, 0/0, 0/1 で factory None) を新 2 macro へ明示パラメータ追加、S1 実 evaluator 経路 (`test_s1_direct_comparison` 651-728 付近) で SORT の確立を明示検査、rung1 driver test で宣言が factory 経由になったことを検査 (REPORT だけ未確立から除かれ RUNG1 / BACKOFF_FIXED は未確立のまま)。
4. **正例 (承認外の過剰拒否の検出、DW-M01):** REPORT 正しい複合枝 + 両 argv RUNG1=1 → admitted; SORT の実構造 (`#else`、EVOLVE-BLOCK、活動中の外側条件) → green; 枝本文だけ変えても witness は赤にならない; REPORT 確立後も他 macro の未確立項目が残る; 新 2 件の非対値は factory None (family admit まで一律に期待しない)。
5. **段 5 の順序 (P7):** author が (i) job-dir probe `probe_meaning_candidates.py` (≤100 行、repo 外、shadow 登録簿を固有 module 名で読込、正準 module 不変、出力 JSON は plan の項目) → 親が login で実行 (5 候補 × 1/0、official 同形供給、REPORT は登録前後の supply 比較を含む) → 結果を確認して (ii) 同 author が確定集合を実装。
6. **段 6 完了条件:** 焦点走 (B-3 の閉包表) 緑、変異 matrix、最終 production 登録簿での official 同形 cell (login 1 + 計算ノード dispatch 1 job で SORT / REPORT)、受入全走。
7. **不変条件:** 規律 2 (受理集合は狭まる向きのみ、REPORT は登録前後 supply 比較で裏取り)、D1491 (旧宣言経路 BACKOFF_FIXED 固定)、`DEFINE_SPECS` 不変、factory 1/0 条件不変、凍結成果物・calibration・durable manifest 不変、実装面は Codex author のみ。

## 6 件の判定 (段 5 実測で確定、現時点は provisional)

| macro | 分類 | 根拠 |
|---|---|---|
| SORT_VARIANT | 足す (条件付き) | 一意 `#if SORT_VARIANT`、supply 緑実測済み、consumer = S1 (自動発火、official) |
| IZANAGI_SILO_LADDER_RUNG1_REPORT | 足す (条件付き) | 一意複合行、companion RUNG1=1 下の footer 枝選択、consumer = silo_ladder_rung1 (配線 1 行、admission を JSON へ保存) |
| SS2PL_LOCK_IMPL | 観測可能だが採用しない | 唯一の一意 directive は複合行 1 本、本来の意味を担う 19 箇所は非一意 = (c) 代表選択 (scope 外)。supply `dependency-closure-drift` で family 拒否 (T-2737 §7 未裁定)。meaning 単独は probe で診断記録 |
| SS2PL_WFG_DIAG | 観測可能だが採用しない | 同上 (44 箇所非一意、複合行は LOCK_IMPL と共有) |
| SS2PL_DLR | 既存機構では届かない (要実測) | 一意 `#if SS2PL_DLR == 1` はあるが CMake が `DLR0`/`DLR1` marker を同時に変え、meaning arm の argv 比較で `compile-command-drift` |
| SS2PL_LOCK_KIND | 宣言不能 | 所有 TU `cc/ss2pl/transaction.cc` に directive なし (実体は `wfg.cc:64/74`、`ss2pl_lock.hh:52` の template 引数)。`owner_tus` 拡張は DefineSpec の意味変更 (supply arm の対象 TU も動く) で scope 外 |

## 変異の事前登録 (anchor は実装後に確定、DW-M07)

| id | 種別 | 変異 | 期待 | 帰属 (単一理由) |
|---|---|---|---|---|
| m0 | positive | 登録簿近傍 comment の等価変更 | SURVIVED | — |
| m1 | negative | 登録簿から SORT entry を削除 | KILLED: tuple pin test + SORT 正例 test (meaning が unestablished に戻る) | 登録簿の有無だけが理由 |
| m2 | negative | 登録簿から REPORT entry を削除 | KILLED: 同上 + rung1 の REPORT 確立 test | 同上 |
| m3 | negative | REPORT の登録 directive から `IZANAGI_SILO_LADDER_RUNG1 && ` を落とす | KILLED: patch 束縛 test (patch に一致行なし) | 登録簿と patch の束縛 |
| m4 | negative | rung1 配線を `declaration=None` へ戻す | KILLED: rung1 driver test (meaning-only red fixture で 正常版 reject → 変異版 admit、または宣言型の検査) | 配線の有無だけが理由 (他 arm は緑の fixture を使う) |
| m5 | negative | factory の `requested != "1"` を `requested not in {"0","1"}` へ緩める (受理拡大) | KILLED: 非対値 test (0/0, 0/1 で None を期待) | factory 条件 |
| m6 | negative | 共通 fixture `SORT_VARIANT_SOURCE` の外側 directive を元の `#if SORT_VARIANT` 塊へ戻す (test 側) | KILLED: SORT 正例 test が `start-not-unique` | 一意性検査 (test 側の変異、DW-M08 の検出力対照) |
| m7 | negative | `_effective_companions` が spec companion を補完しない (companion 空) | KILLED: REPORT 正例 test (`companion-define-mismatch` または非識別) | companion 注入 |

m7 は既存機構への変異であり、REPORT fixture が companion を `#define` しない設計に依存する (companion を `#define` すると恒真)。走行 spec は `izanagi-dev-wave-mutation-spec/v1`、runner argv に `-rf`、spec / out は checkout 外。

## 裁定パッケージ候補 (scope 外、実装しない)
- 探索 loop (p3_s4_loop_sort / s6_sort_sweep) への meaning 配線 + offline 依存供給 + admission の永続化 (B-1)。
- 共有 build root の cache 履歴依存 (A-1) に対する gate 側の対照 (人工 CMake fixture)。
- SS2PL: 代表枝の採用方針・patch 改訂 (T-2737 §7)・`owner_tus` 拡張。S2 driver の Pegasus 4 固定値。
