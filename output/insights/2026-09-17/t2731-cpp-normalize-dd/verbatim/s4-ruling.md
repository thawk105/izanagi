# [T-2731] 段 4 裁定 — plan v2、所見の採否、変異事前登録、規律 7 の再検証発火条件

裁定の正本: **D2104 項 2** (main b4631a92e の `docs/decisions.md`、第 20 回 rulings 全件の fold で採番)。決定 = (a) `_cpp_normalize` に `-dD`。
wave branch は main b4631a92e を ff-only で取り込み済み (HEAD == main、clean)。

## 1. 所見の裁定

| 所見 | real / refuted | 採否 | scope | 処置 |
|---|---|---|---|---|
| B-1 `p3_s4_loop_trigger_gating.py:322/348` が pre-image を artifact 保存し再利用時の不一致で停止 | real (親が現物確認) | 採用 | 内 (説明) | 指令を持たない既存 proposal は pre-image が byte 一致なので影響なし。insight の consumer 節に「指令を含む proposal を同じ artifact path で再 materialize すると停止する」を明記。コード変更なし |
| B-2 probe test の `EVIDENCE_ROOT` (`:25`) が旧 job dir 固定 | real | 採用 | 内 | probe branch に限り今回の job dir (`…/dev-wave-t2731-cpp-normalize-dd/evidence`) へ 1 行変更。**Codex author (fix 子、probe worktree、workspace-write)** が書き、親が probe branch へ commit。wave branch には入れない |
| B-3 compiler 指定が現物より強い | real | 採用 | 内 | login = `_any_cxx()` → g++-12 (g++-13 不在)、compute = `compilers_for_current_site()` → system g++ 11.4.0 (T-2630 実測)。記録は選択規則 + 実記録で書き、compiler 間の byte 一致は主張しない |
| B-4 brief F-2 の列挙に `plain` 欠落 | real (軽微) | 採用 | 内 | 7 形 = plain を含む。brief は訂正せず本裁定で訂正 |
| A-1 include と指令の相対位置が失われ、`define→include→undef` と `include→define→undef` の 2 variant が同 identity | real (静的根拠 + 断片実測) | 採用 (記録) | **外** | P1 が新しく作る欠陥ではない (修正前から同一)。修復範囲は「登録済み M4 / M4b と基準 template の区別」に限定して書く。相対位置の解消は本 wave の scope 外 → insight §限界 + 裁定候補として記録 (gate 新設は提案しない) |
| A-2 `#pragma push_macro` / `pop_macro` の復元値は `-dD` に出ず、保存時点の違いを区別できない | real (断片実測) | 採用 (記録) | **外** | 同上。「任意のマクロ状態操作を被覆する」と書かない |
| A-3 trace diff-of-diffs は比較式不変だが受理集合は不変でない (`#if TRACE` 内の未使用 `#define`/`#undef` で D_variant ≠ D_stock) | real | 採用 | 内 (説明) | 狭まる向き (規律 2 と同方向)。「述語不変」は比較式 `D_variant == D_stock` の維持に限定し、受理集合不変とは書かない。除外処理は足さない |
| A-4 prefix の局所健全性は支持、全文・全 compiler の byte 同一は未実証 | real | 採用 | 内 | F-4 は「対象 pin・template・同一 compiler」条件付きの予測とする。全文比較は段 6 の実走 (`test_source_digest_stock_roundtrip` 実 submodule、probe baseline の token) で実測する |
| A-5 P2 は恒真でない。KILLED だけでなく失敗 node と赤理由の一致が要る | real | 採用 | 内 | 段 6 で observations.json の赤理由 (token != stock / current != reference) を照合して記録 (T-2630 A6-1 と同じ) |

親 brief への反論で覆った前提: F-3 は `BACKOFF_FIXED` と `BACKOFF_NOINLINE` の 2 つ。mocc pair は `#if TRACE` 追加もある (define/undef は無し)。

## 2. plan v2 (実装の正本 = s2-plan-out.md + 次の修正)

1. `_cpp_normalize`: plan の擬似 diff どおり (`-dD`、`_CPP_ENV_PREFIX_CACHE`、`_environment_only` flag の再帰、`startswith` 不成立で RuntimeError、spawn site 1 箇所)。docstring は plan の文面に `BACKOFF_NOINLINE` を足し、A-1 / A-2 を「残る限界 (相対位置・macro stack は識別しない)」として 1 行併記する。
2. test A〜H: plan どおり 8 node。B の docstring に「実 M6 の最終層は `buildcache._assert_no_trace_symbols`、この test は binary 検査をしない」を併記。
3. 登録簿 (`test_ccbench_spawn_sites` / `test_skip_classification` / duration ledger) は変更しない。
4. probe branch: wave の fix commit → `a519a7560`、`e35fb7c4e` を cherry-pick → fix 子で `EVIDENCE_ROOT` を今回の job dir へ変更 → commit。land しない。

## 3. gate の禁止 (署名) と通る正例

- 拒否 1: 有効枝に `#define` / `#undef` を持つ source は、その指令が本文で使われなくても **別 identity** (`resolve` は非 stock token を返す。RuntimeError ではない)。
- 拒否 2: preprocess 出力が同 argv の空入力出力 (環境 prefix) で始まらない → `RuntimeError("… 環境 prefix と不一致 … fails-closed")`。
- 通る正例: working-tree の CMake 供給だけが増え source が参照しない (inert template: `BACKOFF_FIXED` / `BACKOFF_NOINLINE`) → `resolve == "stock"`。comment-only → `"stock"`。

## 4. 規律 7 の再検証発火条件 (結果を見る前に登録、2026-09-17 07:10 JST)

identity 版の変更に対する再検証。**次の予測が実走で一致したときだけ「F1016 の登録済み衝突を修復した」と書く。**

| 対象 | 予測 (修正後) | 修正前 (T-2630 実測) | 観測手段 |
|---|---|---|---|
| M3b (top-level `SLEEP_READ_PHASE`) | N1a・N1b 赤 (stock token ≠ "stock"、variant token ≠ reference) + N2a・N2b 赤 | N2a・N2b のみ | recipe v2 (計算ノード) + observations.json の赤理由 |
| M6 (top-level `TRACE`) | 同上 4 node。`assert_trace_diff_matches_head` は通過 (backoff.hh に TRACE 参照なし)、nm 層が最終層 | N2a・N2b のみ、trace 検査通過 | 同上 |
| M0 (comment-only) | SURVIVED、token 一致 | SURVIVED | 同上 |
| M3a / M4 / M4b / M1 / M2 | M3a: N1b+N2b、M4/M4b: 4 node、M1: N1b+N2b、M2: 4 node | M3a: N2b、M4/M4b: N2a+N2b、M1/M2 不変 | 同上 |
| baseline (未変異 template) | PASSED。stock token = "stock"、variant token = `d8a4a10d163d14c391745b8e7c89322349e7ebe60f539c2913a340e94c0383cc` (T-2630 と同値 = golden 不変の実測) | 同値 | probe baseline の token.txt |
| 実 submodule (pin 511c953、stock checkout) | `test_source_digest_stock_roundtrip` 緑 (silo 8 genome が "stock") | 緑 | 受入・焦点走 (login) |
| 記録済み測定 | 無効化しない。stock / 指令を含まない template variant の token は同値 | — | 規律 7 |

## 5. 変異事前登録 (DW-M01)

### (a) source-level (`orchestrator/campaign/source_digest.py`、runner = 新 8 node 限定、dispatch)

| ID | 置換 (一意) | expected_nodes (test_campaign.py::) | status |
|---|---|---|---|
| S1-drop-dD | argv の `"-dD", ` を削除 | A `test_source_digest_toplevel_macro_directives_change_identity`、B `test_source_digest_toplevel_trace_directives_change_identity`、F `test_source_digest_skipped_macro_directives_affect_only_live_variant`、H `test_source_digest_same_value_source_redefine_changes_identity` | KILLED |
| S2-drop-removeprefix | `return r.stdout.removeprefix(prefix)` → `return r.stdout` | D `test_source_digest_unused_universal_supply_preserves_stock`、E `test_source_digest_unused_protocol_supply_preserves_digest` | KILLED |
| S3-tautologize-startswith | `if not r.stdout.startswith(prefix):` → `if not True:` | G `test_source_digest_cpp_environment_prefix_mismatch_fails_closed` | KILLED |
| S0-comment-only | docstring の 1 語だけ変更 | [] | SURVIVED |

置換 anchor の逐語は author の実装後 (fix 後の最終 commit) に確定し、spec の sha256 を台帳に記録する (DW-M07)。
runner = `python3 tools/run_tests.py orchestrator/tests/test_campaign.py -k "<8 node の名前 or 連結>" -q -rf --force-dispatch` (8 node のみ選択されることを collection で確認)。

### (b) recipe v2 (carrier = `patches/silo-backoff-fixed.patch` sha a5e0710c…、runner = probe test 4 node、dispatch)

`recipe-spec-v2-draft.json` のとおり (M0 SURVIVED []、M1 [N1b,N2b]、M2 [4]、M3a [N1b,N2b]、M3b [4]、M4 [4]、M4b [4]、M6 [4])。
anchor は T-2630 と同一 (carrier 不変を sha で確認済み)。最終 spec の sha256 は harness 投入時に記録。

## 6. 主張の限定 (insight に書いてよい / 書いてはいけない)

レンズ A の表を採用する。書いてよい: 「登録済み M3b / M6 は stock と別 identity になった」「M4 / M4b を基準 template と区別した」「対象 stock / template の token は維持された」「M6 は trace 差分検査を引き続き通過し nm 層が残る」。
書いてはいけない: 「file 間のマクロ効果をすべて被覆した」「非再帰境界を全面的に閉じた」「include と指令の相対位置も区別する」「全 compiler で token 不変」「mocc・pragma・computed 系に残存経路はない」。

## 7. 段 5〜6 の手順

1. author 子 (wave worktree、workspace-write) → 親が差分を検収 → commit (AI-Agent trailer、provenance 検査) → 焦点走 (login、`test_campaign.py -k source_digest or trace_diff`、`test_ccbench_spawn_sites.py`、`test_skip_classification.py`、`test_check_trace0_preprocess_identity.py`)。
2. 変異 container worktree (`.codex/worktrees/t2731-mutcontainer`、fix 後 tip) で (a) を dispatch。probe worktree (wave tip + cherry-pick 2 + EVIDENCE_ROOT fix) で (b) を dispatch。両者は並列。
3. 段 6 レビュー 2 本 (read-only、wave worktree)。must-fix があれば fix 子 → 再 commit → (a)(b) の anchor 再検証。
4. 受入全走 (`dev_wave_wait.py acceptance --lease-optional`)。
