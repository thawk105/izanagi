# [T-2234] 8c 予算 consumer の恒真な保証を発火する形へ直した

**日付:** 2026-09-08
**wave:** `worktree-dev-wave-t2234-budget-vacuity`
**base:** local main `cc9bba523ac7804aadb7891d686bf4c925789a3f`
**取り込んだ main:** `f7f2d8fbc9449392f437777ef0220729a1fc648d` (28 commit、docs と output のみ)
**実装 commit:** `d883df7e64c2f952030b544cd05c4cbd5dcc6143`

## 1 行で

6 cell すべての予約値が 0 でも `held` として受理され、予算保証が一度も発火しなかった。
事前登録の規範が要求する形 — 予約の実在、arm 上限の対称性、holdout 上限の和と総上限の一致 — を
consumer へ入れ、負例 10 件と変異 12 件 (全件 KILLED) で発火することを実測した。

## 2. 何が恒真だったか (先行 wave の記録を訂正する)

`output/insights/2026-09-02_t2159-c05-schedule-authority/README.md` §5 の R6 が本件の一次実測である。

**親の段 1 brief は「予算停止を一度も発火させられない」と書いたが、これは広すぎた。**
段 3 レンズ A が現物で反証した。現行の `_check_limit_state` は総上限・arm 上限・holdout 上限の
3 層について超過を実際に検出し、既存テストも 3 層それぞれの `insufficient` witness を持っていた。
**恒真だったのは「予約が実在することを要求する述語が存在しない」ことである。** 全 cell の予約が 0 なら
「予約の和 ≤ 上限」は必ず成立するので、`held` が無条件に返る。
加えて、規範が要求する arm 上限の対称性と holdout 上限の和の一致は、どの consumer も検査していなかった。

`symmetric_indeterminate` が理由コードを返すという brief の記述も誤りだった。同関数は cell ID 集合
だけを返し、`budget-insufficient` を付けるのは supervisor 側である。

## 3. 段 3 が摘出した blocker 2 件

**(a) 変更面が 2 file では閉じない。** `orchestrator/tests/test_p3_autonomous_workload_trial.py` の
supervisor fixture が holdout 上限の和 (4.0) と総上限 (2.0) を食い違わせていたため、規範検査を
入れると既存 2 テストが setup 段階で落ちる。両レンズが独立に指摘した。

**(b) 許容差を発明すると保証が別の形で恒真化する。** 段 2 プランは既存の ledger 再集計規約を
流用して `math.isclose(..., abs_tol=1e-9)` で「対称」「一致」を判定していた。レンズ B が、
この形では次の入力が新しい 3 検査を**すべて通り**、総予算 0 のまま `held` になることを示した。

```
total_bench_s      = 0.0
per_arm_bench_s    = {on: 0.0, off: 5e-10, swapped: 1e-9}
per_holdout_bench_s= {H1: 5e-10, H2: 0.0}
各 cell の予約      = 5e-324
```

arm の最大差 1e-9 と holdout 和の不一致 5e-10 がどちらも許容差内に入るためである。

## 4. 裁定 (段 4)

1. **規範の「対称」「一致」は厳密一致 (`!=` / `==`) で実装する。** 規範本文
   (`docs/phase3-8c-preregistration.md` の「累積ベンチ実時間の上限」の項) は許容差を定めていない。
   許容差を置けば、それは実装が発明した仕様になる — 先行 insight §4.1 の R3 が警告した
   「権威のない仕様を実装が決める」構図そのものである。
2. **arm 上限と holdout 上限の正値を要求する。** これで §3(b) の regime が閉じる。
   **総上限の正値は検査しない。** holdout 上限が正で、その和が総上限に厳密一致するなら総上限は
   必ず正になるので、冗長な検査は等価変異を生むだけである。
3. **予約値が 0 の cell が 1 つでもあれば `held` にせず `insufficient` にする。**
   新しい state も新しい gate も足さず、既存の `symmetric_indeterminate` が
   実走前に 6 cell を対称停止させる経路へ載せる。
4. **規範違反の上限は `BudgetError`。** 予算不足ではなく入力が規範に反するので、
   `insufficient` にすると supervisor が `budget-insufficient` と誤って報告する。

## 5. 規範を厳密一致にしても既存の 3 層 witness は保てる

holdout 上限の和 = 総上限を強制すると、予約総和が総上限を超えれば必ずどれかの holdout も超えるので、
「総上限層だけが不足」という witness は素朴には作れなくなる。層別比較が持つ許容差
`_TOLERANCE`=1e-9 の帯を使うと構成できる。親が Python で直接評価して確認した値:

|param|total|per_arm|per_holdout|total_ok|arm_ok|holdout_ok|
|---|---|---|---|---|---|---|
|`[total]`|23.9999999985|8.0|(11.99999999925, 11.99999999925)|**偽**|真|真|
|`[arm]`|24.0|5.0|(12.0, 12.0)|真|**偽**|真|
|`[holdout]`|24.0|8.0|(5.0, 19.0)|真|真|**偽**|

いずれも holdout 上限の和は総上限に厳密一致し、arm 上限は厳密に対称である。
`test_each_budget_layer_has_a_numeric_insufficient_witness` の関数名と assertion は変えていない。

## 6. 厳密一致を許容差へ戻す変異を殺す負例

ULP 級の差は `!=` では拒否され、`math.isclose(rel_tol=0.0, abs_tol=1e-9)` では受理される。
この差が、許容差を入れ直す変異 (M7・M9) を殺す負例になる。

|入力|`!=` の判定|`isclose(abs_tol=1e-9)` の判定|
|---|---|---|
|arm `(8.0, 8.0, math.nextafter(8.0, 9.0))` — 差 1.7763568394002505e-15|拒否|受理|
|total `math.nextafter(24.0, 25.0)`、holdout `(12.0, 12.0)` — 差 3.552713678800501e-15|拒否|受理|

`json.dumps` / `json.loads` の round-trip は上記すべての値で厳密一致するので、台帳の読み戻しで
判定が変わることはない (親が実測)。

## 7. 変異 matrix (12 件・全件 KILLED)

`tools/mutation_harness.py`、`--runner-mode dispatch`、runner 対象は
`orchestrator/tests/test_s8c_budget.py`、anchor commit `d883df7e64c2f952030b544cd05c4cbd5dcc6143`。
逐語は `verbatim/mutation-spec.json` と `verbatim/mutation-ledger.json`。

**期待 node は 2 段構えで確定した。** 先に全 12 件を `expected_status=SURVIVED` で登録した probe を
走らせて実際に落ちる node を観測し (`verbatim/mutation-probe-ledger.json`)、その完全集合を
本走 spec の `expected_nodes` にした。単一 node と決め打ちしていたら M1・M3 (3 node) と
M6・M8 (2 node) で MISMATCH になっていた。

|id|変異|殺した node 数|殺したテスト|
|---|---|---|---|
|M1|`cell.reserved_bench_s > 0.0` → `>= 0.0`|3|全ゼロ / 1 cell ゼロ / 旧台帳読み戻し|
|M2|`all(...)` → `any(...)`|1|1 cell ゼロ|
|M3|`all_cells_reserved and` を削除|3|全ゼロ / 1 cell ゼロ / 旧台帳読み戻し|
|M4|arm 正値 `<= 0.0` → `< 0.0`|1|非正上限 `[arm]`|
|M5|holdout 正値 `<= 0.0` → `< 0.0`|1|非正上限 `[holdout]`|
|M6|arm 対称性の `raise` を `pass`|2|非対称 `[gross]` / `[ulp]`|
|M7|arm 対称性を `isclose(abs_tol=_TOLERANCE)` へ緩める|1|非対称 `[ulp]`|
|M8|holdout 和の `raise` を `pass`|2|和不一致 `[gross]` / `[ulp]`|
|M9|holdout 和を `isclose(abs_tol=_TOLERANCE)` へ緩める|1|和不一致 `[ulp]`|
|M10|`total_ok = True`|1|3 層 witness `[total]`|
|M11|`arm_ok = True`|1|3 層 witness `[arm]`|
|M12|`holdout_ok = True`|1|3 層 witness `[holdout]`|

集計は `KILLED=12 / MISMATCH=0 / SURVIVED=0 / TIMEOUT=0`、`registered=12`・`matching=12`、
baseline は `PASSED` (rc=0、失敗 node 0)。

**登録しなかった変異が 1 件ある。** `> 0.0` を `!= 0.0` にする変異は、`ReservationCell` が
`_finite_nonnegative` の戻り値を field へ保存しないため、比較を上書きした `float` subclass の下では
等価にならない (段 3 レンズ A の所見)。等価とも KILLED とも申告せず事前登録から外した。

## 8. 過剰拒否の正例

受理集合を縮小する wave なので、承認外の過剰拒否を検出する正例も登録した。すべて緑である。

- `test_normative_limits_with_positive_cells_are_held` — 規範適合かつ非一様な holdout 上限
  (H1 の 3 cell 各 1.0 / H2 の 3 cell 各 2.0、total 9.0、arm 各 3.0、holdout (3.0, 6.0)) で `held`
- `test_all_three_layers_within_limit_are_held`
- `test_budget_limits_require_arm_and_holdout_coverage` — 期待例外が `coverage` のまま
  (新しい検査より前に coverage 検査が発火する)
- `test_prepare_s8c_budget_inputs_accepts_matching_ratified_holdout_ids`
- `test_prepare_s8c_budget_inputs_rejects_mismatched_holdout_id_set`

## 9. 実装しなかった real 所見 2 件 (次の一手へ回す)

1. **極小正値 regime は閉じていない。** total 1e-9、arm 各 1e-9、holdout 各 5e-10、予約 各 5e-324 は
   本 wave の全検査を通って `held` になる。閉じるには「最低予約量」か「正式 workload の事前コスト
   計画との結合」が要るが、どちらも事前登録の規範に無い。実装が決めれば §4 の裁定 1 と同じ
   「権威のない仕様」になるため、実装せず裁定へ返す。
2. **`ReservationCell.reserved_bench_s` の field 正規化。** `_finite_nonnegative` の戻り値を保存
   しないため、比較を上書きした `float` subclass が受理済みオブジェクトに残る。1 行で直せるが、
   本 wave の scope 指示 (仮想リスク向けの検査を足さない) の外である。
   なお公開経路では JSON へ `0.0` が書かれ、読み戻しで `BudgetError` になるので、
   不整合な台帳が黙って通ることはない (段 6 レビュー A が現物で確認)。

## 10. 本 wave が主張しないこと

- **C06 は充足しない。** `_evaluate_c06` は終端が常に `EVIDENCE_UNDEFINED` であり、本変更で
  判定は 1 ビットも動かない。
- **C05 の schedule 正本は結線していない。** `p3_autonomous_workload_trial._load_s8c_schedule_authority`
  は今も引数を捨てて無条件に例外を送出するので、production の limits / cells は到達不能である。
  したがって本 wave は**休止中 consumer の hardening** であり、現時点の production 挙動は変わらない。
- **事前登録 §5 の予算欄の解除も主張しない。** 解除条件は実 consumer と正式 workload の事前コスト
  計画の両方であり、後者は本 wave の外にある。

## 11. 検査の実測

- 焦点走 (計算ノード job 985361.nqsv): **575 passed / 6 skipped、103.38 秒、赤 0。**
  対象は変更した 2 test file と、`s8c_budget` を参照する 3 test file
  (`test_s8c_preregistration_invariant.py`、`test_s8c_preregistration_predicates.py`、
  `test_real_repo_serialization.py`)。
- provenance 全史監査: 8988 件、新規違反なし。
- 段 6 敵対レビュー 2 本: blocker・must-fix ともに 0 件。
- 受入全走の結果は worklog の該当エントリに記録する。

## 12. verbatim

- `verbatim/s1-brief.md` — 段 1 brief (§2 の誤りを含む)
- `verbatim/s2-plan.md` — 段 2 プラン
- `verbatim/s3-lens-a.md` — 段 3 レンズ A (受理集合と正しさゲート)
- `verbatim/s3-lens-b.md` — 段 3 レンズ B (契約 pin と破壊面)
- `verbatim/s4-verdict.md` — 段 4 裁定・プラン v2・変異事前登録
- `verbatim/s5-author.md` — 段 5 実装子の報告
- `verbatim/s6-review-a.md` / `verbatim/s6-review-b.md` — 段 6 敵対レビュー
- `verbatim/mutation-spec.json` / `verbatim/mutation-ledger.json` — 変異本走
- `verbatim/mutation-probe-ledger.json` — 期待 node を集めた probe
