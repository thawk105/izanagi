# 段 4 裁定 — dev-wave-growth-hold-inventory

base 4cbaf041 / main tip dff2f3e0 / 2026-08-23

## 裁定の枠組み

秒数では判定しない (D463)。既定は D335 (成長比例テストは恒久保留、削除は却下済み)。
保留を外すのは、承認済みの**例外**が成立する node に限る。

- **D451**: 保留すると当該防壁を守る既定走行 node が**ゼロ**になるなら保留しない。
- **D452**: 変異事前登録の `expected_nodes` は既定 skip されない node に限る。
- **D312**: 受入全走 5 分は達成目標であって合否判定ではない。設計択一を閾値の跨ぎで決めず、
  実際の交換レートで判断する。閾値を満たすために検査を弱めることも禁止。

親 brief の「全走 5 分が絶対上限」は誤りだった (段 3 luna #5 が指摘、権威元は D312)。
「遅いから hold 継続」という論法は本裁定では使わない。

## 前提の再実測 (引数の 2 前提はいずれも否定)

- corpus `/home/SFC/tanab/.codex/sessions` は実在。セッション開始時 5,482 file / 5.13 GiB、
  約 50 分後に 5,505 file。**自分が起動した codex 子が rollout を書いて増えている** —
  D463 の「通常運転で単調に増える集合」の実地観測。
- 16 node は opt-in 実走で 20 items 全 PASS / 544.05 秒。壊れていない。
- 登録 reason 本文は「corpus 不在 / rollout 待ち」ではなく成長比例コストだった。
  引数の前提は変数名 `_ROLLOUT_REASON` からの推測であり、本文と食い違う。
- corpus が無いマシンでは 14 件は skip、`_ROLLOUT_REASON` 2 件は `ValidationError` で赤。
  ただし既定走行の `test_real_rollout_collector_golden_is_source_bound` (L6134) が
  `_REAL_ROLLOUT` を無防備に読むので、**既定スイートは既に corpus 実在を前提**にしている。

## 所見の real / refuted 裁定

| # | レンズ | 所見 | 裁定 | 処置 |
|---|---|---|---|---|
| sol 1 | 分類 | F(t) に tracked-index-at-tip が抜けている | **real** | 採用。reason へ両軸を書く。`hold_axis` は実測で大きい output_artifacts を維持 (corpus rglob 0.045 秒 > index 0.031 秒) |
| sol 2 | 分類 | pack-objects は tip 依存でない | refuted (親と一致) | 記録のみ |
| sol 3 | 分類 | 実 golden を導出する既定 node は存在する | **real** | 採用。親の「唯一の実 golden node」は誤り。M2 が唯一なのは route 比較**呼出し**の変異防壁 |
| sol 4 / luna 3 | 両方 | replay の代替は非等価 | **real** | 採用。再導入 |
| sol 5 | 分類 | cleaned-snapshot の absent-manifest 契約も最後の防壁 | **real** | 採用。再導入 |
| sol 6 | 分類 | M1 が変異期待 node 正本と不整合 | **real** | 採用 (拡大あり、下記) |
| sol 7 | 分類 | reeval token は運用上の恒真 | **real** | 部分採用。gate は新設せず、token を「記録であって自動解除条件ではない」と明記する |
| sol 8 | 分類 | D335 違反の削除は計画されていない | refuted | 記録のみ。「registry 行削除」を「テスト削除」と書かない |
| sol 9 / luna 6 | 両方 | cold/warm の比例一般化は未測定、同時実行で汚染 | **real** | 採用。全秒数を「同時実行下の一点観測」へ格下げし、段 6 で serial 単独再測定 |
| luna 1 | 実効性 | pinned fast path の fallback が沈黙 | **real** | 採用。pinned 案を捨て固定 `_REAL_ROLLOUT` 案を採る |
| luna 2 | 実効性 | pinned 案は rglob を残し比例源を除去しない | **real** | 同上 |
| luna 4 | 実効性 | fixture 二重計上と parametrize 数え違いは無い | refuted | 記録のみ |
| luna 5 | 実効性 | 300 秒の権威元欠落 | **real** | 採用。D312 で解決 |
| luna 7 | 実効性 | 現案では zero-hold 例外は起きない | refuted | 2 件残るので成立。ただし下記の閾値監視は残す |
| luna 8 | 実効性 | 行削除で count/digest が変わる、pin consumer 未監査 | **real (親は監査済み)** | pin は contract test L43-45 に実在。稼働中 wave の同 file 差分は `--color=no` 6 行のみで L43-45 に非接触。編集可 |
| luna 9 | 実効性 | 既存変異登録は壊れない | refuted | 記録のみ |
| luna 10 | 実効性 | 禁止 file は触らない | refuted | 所見 8 の条件つきで成立 |

## sol 6 の拡大 — 変異正本との矛盾は M1 だけではない

`orchestrator/tests/test_codex_reasoning_ab.py:4-19` が `DW-M08 expected mutation nodes` の
正本であり、「親の mutation harness はこの一覧を期待 node 正本として新旧双方を突き合わせる」
と明記する。そこで名指しされた node のうち **7 件が現在 hold 中**である。

| 変異 | 期待 node | 状態 |
|---|---|---|
| M1 | `test_m1_snapshot_head_pin_is_independent` | hold |
| M2 | `test_m2_production_golden_requires_both_routes` | hold |
| M3 | `test_m3_snapshot_mode_change` / `test_m3_symbolic_head_is_required` / `test_m3_ignored_extra_and_missing` / `test_m3_focus_artifact_directions` | **4 件すべて hold** |
| M5 | `test_m5_generated_session_rows_require_set_equality` (既定) / `test_verify_replays_complete_fake_codex_experiment` | 2 件中 1 件 hold |

M1・M2・M3 は既定で走る期待 node が **1 件も無い**。D452 が名指しした失敗モード
「期待 node が skip され、変異は必ず SURVIVED になる」に現に該当している。

## 16 node の確定裁定 — 再導入 14 / 削除 0 / hold 継続 2

### 再導入 14 件

| node | 秒 | 根拠 |
|---|---|---|
| `test_m2_production_golden_requires_both_routes` | 0.55 | D451 (route 比較呼出しの変異防壁が他に無い) + D452 (M2 の期待 node) |
| `test_m3_snapshot_mode_change` | 6.95 | D451 + D452 (M3) |
| `test_m3_symbolic_head_is_required` | 3.82 | D451 + D452 (M3) |
| `test_m3_ignored_extra_and_missing` | 14.95 | D451 + D452 (M3) |
| `test_m3_focus_artifact_directions` | 18.32 | D451 + D452 (M3) |
| `test_m1_snapshot_head_pin_is_independent` | 3.32 | D452 (M1 の期待 node。D451 単独では非該当 — L4060 が HEAD mismatch を動的に通す) |
| `test_verify_replays_complete_fake_codex_experiment` | 171.83 | D451 + D452 (M5)。代替 L9138-9141 は source 文字列 2 本の grep で何も実行しない |
| `test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure` | 7.16 | D451 (absent-manifest 5 field 契約を assert する既定 node がゼロ。代替 L1818 は directory が空になることしか見ない) |
| `test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested` | 7.49 | D451 (生成・manifest・rejection の三層が固有) |
| `test_agent_sandbox_binds_exclude_attempt_receipt_directory` | 29.39 | D451 (既定 node は自己申告 `attempt_receipts_bound=False` を見るだけ。実 argv の bind 集合照合はここだけ) |
| `test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation` | 7.77 | D451 |
| `test_attempt_four_is_rejected_before_launch` | <0.005 | D451 |
| `test_pos_neg_submodule_initialization_state_mismatch_is_rejected` | <0.005 | D451 (既定 L4778 は happy path のみ) |
| `test_prompt_replacement_count_zero_expected_and_excess` | 250.68 → 要再測 | D451 + 比例源除去後に再導入 (下記) |

### hold 継続 2 件

| node | 秒 | 根拠 |
|---|---|---|
| `test_forbidden_commits_are_unreachable_in_both_cases` | 0.01 | D451 非該当。既定 `test_snapshot_submodule_object_store_is_recursive` (L2059-2077) が clean な POS snapshot へ `verify_snapshot` を通しており、forbidden object 防壁は既定で残る。変異正本にも名前が無い |
| `test_parent_numstat_controls_remain_pinned` | 6.91 | D451 非該当。manifest literal は既定 L1412 が pin し、派生 snapshot との照合は既定 L2077 の `verify_snapshot` が行う。変異正本にも名前が無い |

いずれも 0.01 秒 / 6.91 秒と安いが、**安さは D451 の判定基準ではない**。防壁が残る以上 D335 が適用される。
逆に「安いから戻す」を認めると、D335 の恒久保留が秒数判断へ退化する。

### 削除 0 件

検出力が完全に重複する node は 1 件も無い。D335 は削除を却下済みであり、
本 wave のユーザー命令が許す「重複ゆえの削除」に該当する node も見つからなかった。

## 択一 1 の裁定 — replay を hold しない

段 2 の「静的防壁を D451 の代替と認めるか」は **認めない**。
`test_m5_generated_session_rows_require_set_equality` は production source に文字列が
2 本あることしか見ない。CLAUDE.md が監査で疑えと定める「恒真な保証 (謳うだけで発火しない assert)」
そのものであり、D451 の代替防壁として数えられない。171.83 秒は D312 により却下理由にならない。

## 択一 2 の裁定 — 固定 `_REAL_ROLLOUT` 参照を採る

`pinned_label="POS"` 案は採らない。luna 1/2 のとおり、(a) `rglob` が残り比例源が消えない、
(b) fast path を外れると**沈黙して**全走査経路へ戻り、遅くなるだけで緑のまま通る。

採る案: `orchestrator/tests/test_codex_reasoning_ab.py:6105-6107` を、既存の固定定数
`_REAL_ROLLOUT` (L87-91) の直接参照と `TOOL._verify_rollout_sha(source_rollout, "POS")` へ置換する。
F(t) が固定 path になり D463 の「非比例」へ移る。source identity は SHA 検証により強くなる。
unpinned 解決経路の意味論は既定走行の約 40 本 (L4915-6032) が合成 corpus で守っており、失われない。

## 択一 3 の裁定 — validator は追加せず、token は記録と明記する

`_validate_hold_rows` への reeval token validator は**追加しない**。

- gate 新設は条件 dispatch 13 (`DW-O13`) の発火であり、最遅読了段は段 2 前である。
  可能性が判明したのは段 3 待機中で、期限を過ぎている。入口の巻き戻し規則に従えば
  段 2 からの再実行が要る。gate を作らなければ巻き戻しは不発であり、fail-closed を保てる。
- ユーザー命令は「機械可読な形で**残す**」であり、強制ではない。
  `tools/hold_inventory.py:79-92` が `growth_test_hold_inventory()` の `holds` 行
  (reason を含む) をそのまま出力するので、既存 consumer が機械可読に公開する。
- sol 7 のとおり評価主体は存在しない。よって **token 自身に「これは記録であって自動解除条件ではない」
  と書く**。台帳が「再評価条件あり」と誤読される事故を、注記ではなく token の中身で塞ぐ。
- 既定 evaluator の新設は裁定パッケージへ送る (下記)。

## 比例源除去後の再測定 (sol 9 / luna 6 の採用)

現在の全秒数は、親が pytest と probe を同一ノードで一部同時に走らせた**一点観測**である。
段 6 で次を serial・単独で再測定し、台帳にはその値を書く。

- 変更後の `orchestrator/tests/test_codex_reasoning_ab.py` 全走
- 変更後の `test_prompt_replacement_count_zero_expected_and_excess` 3 param

再測定前に予算適合を確定と書かない。cold 329.754 秒 / warm 約 18.5 秒から成長率を外挿しない。

## 変異事前登録 (DW-M01 / DW-M08)

本 wave はテスト強化 wave なので、新旧両走を登録する。
**旧 = hold 有効 (node が skip される状態)、新 = hold 解除後**。
新だけが検出する差分を示す。harness は `tools/mutation_harness.py`、baseline 緑必須。

| ID | 変異位置 | 期待 (新) | 期待 (旧) | 単一理由性の確認 |
|---|---|---|---|---|
| MUT-1 | `tools/codex_reasoning_ab.py` `derive_independent_golden` の `return _compare_golden_routes(route_a, route_b)` を `return route_a` へ | KILLED: `test_m2_production_golden_requires_both_routes` | SURVIVED (期待 node が skip) | fixture は例外を出さず通るので consumer は無影響。`test_derive_independent_golden_wires_pins` は `_find_rollout` を monkeypatch し 3 回目で RuntimeError を期待するので無影響 |
| MUT-2 | `tools/codex_reasoning_ab.py` の `expected_sessions` 構築を actual と常に一致させる (grep 対象文字列 `sorted(actual_sessions) != sorted(expected_sessions)` と `generated session row set mismatch` は**変えない**) | KILLED: `test_verify_replays_complete_fake_codex_experiment` | SURVIVED | 文字列を変えないので静的 node `test_m5_generated_session_rows_require_set_equality` は緑のまま。mask を避けた設計 |

M1 は変異登録**しない**。期待 node `test_m1_snapshot_head_pin_is_independent` への変異は
既定走行の L4060 も殺すため単一理由性が立たない (DW-M01 が登録を禁じる形)。
D452 の「登録せず親の直接実測で裏を取って記録する」に従い、再導入は D452 の正本整合として行い、
変異による検出力の純増は主張しない。この事実を worklog へ書く。

MUT-1 / MUT-2 とも、実装前に対象が一箇所であることをコードで確認する (DW-M04)。

## 編集面 (段 5 実装子へ)

編集してよい path は 2 つだけである。

1. `orchestrator/tests/growth_test_holds.py`
   - `_HOLD_ROWS` から再導入 14 行を削除する。
   - `_SNAPSHOT_CORPUS_REASON` / `_ROLLOUT_REASON` は参照が消えるので削除する。
   - 残る 2 行へ、実測日・実測秒・生き残る既定防壁 node・両成長軸・
     「記録であって自動解除条件ではない」を含む reason を書く。
   - `RELEASE_EXPLICIT_USER_COMMAND_ONLY`、環境変数名、token 値、他 file の hold 行、
     `measured_seconds` field は変更しない。
2. `orchestrator/tests/test_codex_reasoning_ab.py`
   - `:6105-6107` を `_REAL_ROLLOUT` 直接参照 + `_verify_rollout_sha` へ置換する。
   - 他は変更しない。

3. `orchestrator/tests/test_growth_test_holds_contract.py`
   - `:43-45` の 3 定数だけを再計算値へ更新する。**手書きしない**。
     `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-growth-hold-inventory/probe_pins.py` と
     同じ手順で算出する (現行 3 値の再現を検証済み)。
   - **他の行には一切触れない** (稼働中 wave が `--color=no` を L1266/1827/1924/1949/1985/2079 へ入れている)。

編集してはならない path: `orchestrator/tests/conftest.py`、`tools/hold_inventory.py`、
`tools/codex_reasoning_ab.py` (変異は harness が一時的に行う)、上記 3 つ以外の全 path。

## 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. **reeval token の既定 evaluator を作るか。** 現状 token は記録であり、barrier node が
   将来 hold されても何も赤くならない。`_validate_hold_rows` を拡張して
   `barrier_nodes` が `GROWTH_TEST_HOLDS` に入っていないことを検査すれば、既存の import 時
   enforcement 点を使って非恒真にできる。gate 新設にあたるため本 wave では実装しない。
2. **変異期待 node 正本と hold registry の整合を機械検査するか。** 今回 7 件の矛盾が
   人手の読みでしか見つからなかった。`DW-M08` の一覧と `GROWTH_TEST_HOLDS` を突き合わせる
   検査があれば構造的に塞げる。
3. **`_find_rollout` の unpinned 全走査に上限や警告を設けるか。** production
   (`tools/codex_reasoning_ab.py:5848`) も unpinned で呼ぶ。corpus が伸び続ける以上、
   いずれ production 側でも顕在化する。関連起票 [T-1523]。
