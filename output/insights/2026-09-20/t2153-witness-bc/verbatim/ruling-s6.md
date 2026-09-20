# 段 6 裁定 — review A / B の所見 (2026-09-20 14:48 JST)

| # | 出所 | 判定 | 採否 | 対応 |
|---|---|---|---|---|
| A1 / A2 / B3 | m4 が等価変異 (c=0 で `selected ≤ N·c` は `== 0` と同じ)、直接検査が公開 evaluator の後ろで schema に遮られる | real / must-fix | 採用 | 変異 m4 を **m4′** (`or default_counts != default_expected:` → `or default_counts[1] != default_expected[1]:` = 対照 selected 検査だけを除去) に差し替え。T の直接検査 (`_assert_compile_time_branch_selection` を N=2 fixture の partial-default で呼び `(2,2)/(1,2)` → `compile-time-branch-selection-mismatch`) を**独立 node** `test_multisite_assert_rejects_default_partial_selection` に分離 (公開 evaluator を呼ばない) → fix-2 |
| A3 / B1 / B2 | baseline の既知赤 (docstring pin、S1 fixture、未確立持ち越し例) | real / must-fix | 採用 | fix-1 で対応済み (c91c9130)。S1 の未確立例は GATING 0/0 (要求 = 既定) の実 request へ。焦点走 own2 で検証中 |
| A4 | GATING の主張範囲 (DefineSpec patch の逐語 12 箇所、instr 複合枝・`#ifndef` 番兵は対象外) が module docstring・test 説明に無い | real / must-fix | 採用 | fix-2: G の module docstring に 1 文、T の multisite 正例 docstring に 1 文を足す (production 挙動は不変) |
| B5 | 新規正例の meaning 実走が T:1359 と T:1401 で重複 | real / nit | **不採用** | 所要は計算ノード xdist で数秒、`accepts_each_registry_macro` は全 21 macro の一様検査、`test_new_branch_selection_supply_meaning_and_admission` は supply + admission を含む独立の正例。統合しても成果物は変わらないが可読性を優先。記録のみ |
| B (G:909 `22-macro supply domain` の古い文言) | 既存 docstring / error 文の古い件数 | nit | 不採用 (本題外) | 起票せず insight に候補として記録 |
| B6 / A 判定 | 計算ノードの実 TU cell が未提示 | real / must (親) | 採用 | 統合 commit 後に generic dispatch で 3 構成 (gating-instr / gating-misattr (GATING + MISATTR) / rung1) を実走 → `stage6-compute/` |
| A5〜A8, B4, B7 | 受理拡大なし・全箇所観測は fail-closed・argv/cache 検査は機能・schema 変異は issuer に隠れない・不在検査は限定・B-4 赤は dirt 由来 | refuted / nit | 記録 | insight §6 に要点。A8 の補足 (裸 `-DM` は不在検査を外しても `preprocess-bytes-identical` で赤 = m6 の kill 正例は `=0` の 2 形) を変異台帳の帰属に反映 |
| B 変異案 | m7 (MISATTR entry 削除) は集合 pin・patch 束縛・factory 正例と冗長 | — | m7 は**残す** (事前登録済み、entry 削除は安価で意味のある変異) が、KeyError 型の赤は帰属表で別記し kill の成果として水増ししない。m3 の複数失敗・m6 の 3 token・m5 の 3 macro も同様 | |
| B 名称 | pin test 名 `…exact_38…` の改名 | nit | 不採用 | nodeid の変更は既存 test の改名で、本題外 |

## fix-2 (Codex、子木 branch `codex-t2153-bc-fix2`、所有: G (docstring のみ)・T)
1. T: `test_multisite_rejects_missing_or_wrong_selection[partial-default]` から直接検査を取り出し、独立 node `test_multisite_assert_rejects_default_partial_selection` (parametrize macro ∈ {RUNG1, GATING}) にする。公開 evaluator は呼ばず `_assert_compile_time_branch_selection` を直接呼び、`compile-time-branch-selection-mismatch` と observed `requested=(N, N),default=(1, N)` を assert。元 test の partial-default 分岐は公開 evaluator の red だけを残す。
2. G module docstring: 主張範囲の 1 文を追加 — "A declared multi-site witness observes exactly the N verbatim directive lines its DefineSpec patch adds; conditionals added by overlay patches (for example diagnostic composites such as ``#if BACKOFF_TRIGGER_GATING && TRACE``) and ``#ifndef`` supply guards are outside the claim." (逐語は fix子が整える。docstring pin test が拾う既存逐語 2 つは変えない)。
3. T の multisite 正例 (`test_new_branch_selection_supply_meaning_and_admission`) の docstring に同じ境界を 1 文。

## 変異事前登録 v2 (m4 → m4′、他は ruling.md のまま)
| id | 変異 (file / old 逐語 → new) | 期待 |
|---|---|---|
| m0 | G `"BACKOFF_TRIGGER_GATING": 12,` → 同行末尾に comment `  # declared sites` | SURVIVED (等価) |
| m1 | C `default_value=None if macro == MISATTR_DEFINE else 0,` → `default_value=0,` | KILLED |
| m2 | C `declaration=condition_meaning_gate.declare_define_runtime_meaning(request),` → `declaration=None,` | KILLED |
| m3 | G `"BACKOFF_TRIGGER_GATING": 12,` → `"BACKOFF_TRIGGER_GATING": 11,` | KILLED |
| m4′ | G `or default_counts != default_expected:` → `or default_counts[1] != default_expected[1]:` | KILLED (独立 node の直接検査) |
| m5 | G `selected_count=count * int(default_value or "0"), completed_count=count,` → `selected_count=evidence["default"].selected_count, completed_count=count,` | KILLED (schema test) |
| m6 | G `if expected_value is None and not stock_identity \` → `if False and expected_value is None and not stock_identity \` | KILLED (supply 単独 test: `=0` 2 形は green 化、裸 `-DM` は別理由の赤) |
| m7 | G の MISATTR entry 3 行を削除 | KILLED (factory 正例・集合 pin・S [misattr]; fixture 経由の KeyError は別記) |
| m8 | G `and _declared_contrast_is_undefined(request.macro) \` の行を削除 | KILLED (過剰拒否の正例 SORT 1/None) |
期待 node は fix-2 統合後の baseline (固定 commit) で確定し spec へ書く (DW-M08)。

## 追記 (14:55 JST): fix-1 の焦点走 (own2、login bounded local) の結果と fix-2 への追加
- own2 は runner が login の bounded local へ落ちた (dispatch でない) ため S1 の 24 件が `official output_root は repository 外でなければならない` の既知偽赤 (login の `/tmp/.git`、非帰属)。実赤は 1 件: `test_promotion_contract_carries_unestablished_meaning_macro` = GATING 0/0 が **supply `compile-command-drift`** (親 probe `probe_s1_gating0.py` で実測: 0/0 は stock-inert 経路になり、S1 fixture の `stock/` root には FIXED / NOINLINE の CMake mapping が無く requested 側だけに `-DBACKOFF_FIXED=-1 -DBACKOFF_NOINLINE=0` が残るため comparable argv が drift。fixture の限界であり production 意味論の欠陥ではない)。
- 親 probe で GATING **2/0** (非対値) は supply green (`requested-default-preprocess-different`、同 root の requested vs default) かつ factory None (`#if` 形は 1/0 だけ宣言) → unestablished が持ち越される。
- **fix-2 に項目 4 を追加**: `test_s1_direct_comparison.py` の `test_promotion_contract_carries_unestablished_meaning_macro` を `(("BACKOFF_TRIGGER_GATING", 2),)` へ変え、コメントで理由 (0/0 は stock-inert 経路で fixture の stock root が FIXED/NOINLINE mapping を欠くため drift、非対値 2 は factory 未宣言のまま供給 green) を書く。assert は不変。fix-2 の所有に `orchestrator/tests/test_s1_direct_comparison.py` を足す。
