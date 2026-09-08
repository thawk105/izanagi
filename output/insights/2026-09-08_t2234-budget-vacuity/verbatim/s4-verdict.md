# 段 4 裁定 + プラン v2 + 変異事前登録 — [T-2234]

## 1. 所見の裁定 (real / refuted、採否、scope)

|#|所見|判定|採否|理由|
|---|---|---|---|---|
|A-1 / B-1|`test_p3_autonomous_workload_trial.py:9097` の fixture が holdout 和 4.0 ≠ total 2.0 で、規範検査を入れると既存 2 テストが setup で落ちる|**real (blocker)**|採用|変更面を 3 file にする。fixture を `{H1:1.0, H2:1.0}` にすれば holdout-set に関する主張は変わらない|
|A-2 / B-2|許容差 `1e-9` は規範本文から導けず、微小値 regime では新 3 検査を全部通ったまま「総予算 0 で held」になる|**real (blocker)**|採用 (形を変えて)|規範の「対称」「一致」は**厳密一致**で実装する。加えて **arm 上限・holdout 上限の正値**を要求し、当該 regime を閉じる|
|A-3 / B-3|`> 0.0` を `!= 0.0` にする変異は等価でない (`ReservationCell` が正規化後の float を保存しないため、比較を上書きした float subclass で差が出る)|**real (must-fix)**|部分採用|当該変異を**等価と申告しない** (事前登録から外す)。`ReservationCell` の field 正規化は本題外なのでユーザーの scope 指示に従い実装せず、次タスク候補として記録する|
|B-4|旧 ledger (予約 0 で `held` と記録) の読み戻しは `BudgetError` になるが回帰テストが無い|**real (must-fix)**|採用|新 gate ではなく、修正が保存済みデータに対して発火することを示す負例なので scope 内|
|A-4|親 brief の「予算停止を一度も発火させられない」は広すぎる。3 層の超過は現状でも発火する|**real (must-fix)**|採用|記録を「ゼロ予約を排除する述語が存在しない」へ訂正する|
|A-5 / B|親 brief の「`symmetric_indeterminate` の理由コード」は誤り。関数は cell 集合だけを返し、`budget-insufficient` は supervisor が付ける|**real (nit)**|採用|記録を訂正する|
|B|親 brief の「path を key にする pin は 2 箇所のみ」は不完全。`test_s8c_preregistration_invariant.py` と `test_s8c_preregistration_predicates.py` も path を pin する|**real (nit)**|採用|記録を訂正する。whole-file sha256 pin が 0 件である部分は否定されていない|
|B-5|production の schedule authority は未結線のままなので、本 wave を「実効化」「§5 解除」「C06 充足」と主張してはならない|**real (must-fix)**|採用|本 wave は休止中 consumer の狭い hardening と位置づける。記録でそう書く|

## 2. 実装しない real 所見 (裁定パッケージ候補・次タスク)

1. **極小正値 regime。** 上限も予約も `_TOLERANCE` 未満 (例: total 1e-9、arm 各 1e-9、holdout 各 5e-10、
   予約 各 5e-324) は、本 wave の全検査を通って `held` になる。閉じるには「最低予約量」または
   「事前コスト計画との結合」が要るが、どちらも事前登録の規範に無く、実装が決めると
   `output/insights/2026-09-02_t2159-c05-schedule-authority/README.md` §4.1 の R3 と同型の
   「権威のない仕様を実装が決める」構図になる。**実装せず記録する。**
2. **`ReservationCell.reserved_bench_s` の field 正規化。** `_finite_nonnegative` の戻り値を保存しない
   ため、比較を上書きした `float` subclass が受理済みオブジェクトに残る。1 行で直せるが、
   ユーザーの scope 指示 (仮想リスク向けの検査を足さない) に照らし本 wave では実装しない。

## 3. プラン v2 (段 5 実装子への指示の正本)

### 3.1 `orchestrator/campaign/s8c_budget.py`

**(a) `BudgetLimits.__post_init__` の末尾** (3 つの `object.__setattr__` の直後) に、次の順で追加する。
順序は「赤理由を一つに絞る」ための契約であり、入れ替えない。

```python
        for arm in sorted(_ARMS):
            if self.per_arm_bench_s[arm] <= 0.0:
                raise BudgetError(f"per_arm_bench_s.{arm} が正でない")
        for holdout in sorted(_HOLDOUTS):
            if self.per_holdout_bench_s[holdout] <= 0.0:
                raise BudgetError(f"per_holdout_bench_s.{holdout} が正でない")
        if min(self.per_arm_bench_s.values()) != max(self.per_arm_bench_s.values()):
            raise BudgetError("per_arm_bench_s が arm 間で対称でない")
        if (
            sum(self.per_holdout_bench_s[holdout] for holdout in sorted(_HOLDOUTS))
            != self.total_bench_s
        ):
            raise BudgetError("per_holdout_bench_s の和が総上限と一致しない")
```

- **厳密一致 (`!=` / `==`) を使い、`math.isclose` や `_TOLERANCE` を使わない。** 規範は「対称」
  「一致」としか書いておらず、許容差は実装が発明した仕様になるため (所見 A-2)。
- **総上限の正値は検査しない。** holdout 上限が正で、その和が総上限に厳密一致するなら
  総上限は必ず正になる。冗長な検査は等価変異を生むので置かない。
- 既存の coverage 検査 (`_immutable_limit_map`) はこれらより前に発火するので、
  `test_budget_limits_require_arm_and_holdout_coverage` の期待は変わらない。

**(b) `_check_limit_state`** に、全 cell の予約が正であることを足す。

```python
    total_reserved_bench_s = sum(cell.reserved_bench_s for cell in cells)
    all_cells_reserved = all(cell.reserved_bench_s > 0.0 for cell in cells)
    ...
    return (
        total_reserved_bench_s,
        all_cells_reserved and total_ok and arm_ok and holdout_ok,
    )
```

関数名・引数・戻り値の型・`reserve_all_cells` からの呼び出しは変えない。

### 3.2 `orchestrator/tests/test_s8c_budget.py`

- `_limits()` helper の `per_holdout` を `tuple[float, float]` にし、既定を `(12.0, 12.0)` にする。
- `_reserve()` に `cells` 引数 (既定 `None` → `_cells()`) を足す。
- 3 層 witness の param を規範適合値へ置換する。**関数名と assertion は変えない。**
  - `total`: `_limits(total=23.9999999985, per_holdout=(11.99999999925, 11.99999999925))`
  - `arm`: `_limits(per_arm=5.0)`
  - `holdout`: `_limits(per_holdout=(5.0, 19.0))`
- `test_stale_lock_is_fail_closed_and_partial_insufficient_run_is_rejected` の
  `_limits(total=10.0)` を `_limits(total=10.0, per_holdout=(5.0, 5.0))` にする。
- 追加テスト (`_run()` の前へ置く):

|関数名|入力|期待|
|---|---|---|
|`test_all_zero_cell_reservations_are_insufficient`|全 6 cell 予約 `0.0`、`_limits()`|`state == "insufficient"`、`total_reserved_bench_s == 0.0`、`symmetric_indeterminate(ledger) == ledger.cell_ids`|
|`test_one_zero_cell_reservation_makes_whole_matrix_insufficient`|`h1-on` だけ `0.0`、他 5 cell `4.0`、`_limits()`|3 層はすべて上限内なのに `state == "insufficient"`、`total_reserved_bench_s == 20.0`、全 cell が対称に判定不能|
|`test_budget_limits_reject_nonpositive_caps[arm]`|total `24.0`、arm `(0.0, 0.0, 0.0)`、holdout `(12.0, 12.0)`|`BudgetError`、`match="per_arm_bench_s"` かつ `"正でない"`|
|`test_budget_limits_reject_nonpositive_caps[holdout]`|total `24.0`、arm `(8.0, 8.0, 8.0)`、holdout `(0.0, 24.0)`|`BudgetError`、`match="per_holdout_bench_s"` かつ `"正でない"`|
|`test_budget_limits_reject_asymmetric_arm_caps[gross]`|total `24.0`、arm `{on:8.0, off:8.0, swapped:9.0}`、holdout `(12.0, 12.0)`|`BudgetError`、`match="対称"`|
|`test_budget_limits_reject_asymmetric_arm_caps[ulp]`|arm `swapped` を `math.nextafter(8.0, 9.0)` にする|`BudgetError`、`match="対称"`|
|`test_budget_limits_reject_holdout_caps_not_summing_to_total[gross]`|total `24.0`、arm `(8.0,8.0,8.0)`、holdout `(13.0, 13.0)`|`BudgetError`、`match="総上限と一致しない"`|
|`test_budget_limits_reject_holdout_caps_not_summing_to_total[ulp]`|total `math.nextafter(24.0, 25.0)`、holdout `(12.0, 12.0)`、arm `(8.0,8.0,8.0)`|`BudgetError`、`match="総上限と一致しない"`|
|`test_normative_limits_with_positive_cells_are_held`|H1 の 3 cell 各 `1.0`、H2 の 3 cell 各 `2.0`、total `9.0`、arm `(3.0,3.0,3.0)`、holdout `(3.0, 6.0)`|`state == "held"`、`total_reserved_bench_s == 9.0`、`symmetric_indeterminate(ledger) == frozenset()`|
|`test_zero_reservation_ledger_recorded_as_held_is_rejected_on_read`|`_reserve` で作った正常 ledger の JSON を書き換え、全 cell の `reserved_bench_s` と総予約を `0.0` にし `state` は `"held"` のまま残す。その path へ `B.settle(...)` を呼ぶ|`BudgetError`、`match="limit state"`|

`math` の import を test module へ足してよい。

### 3.3 `orchestrator/tests/test_p3_autonomous_workload_trial.py`

`:9097-9101` の `per_holdout_bench_s` を `{"H1": 1.0, "H2": 1.0}` にする。
**それ以外は変えない。**このテストの主張 (holdout-set の一致・不一致) は変わらない。

### 3.4 触ってはならないもの

- C06 契約 JSON、`s8c_preregistration_evidence.py`、`test_s8c_preregistration_invariant.py`、
  `test_s8c_preregistration_predicates.py`。
- ledger schema `s8c-budget-ledger/v1`、`state` の値域 `{"held","insufficient"}`。
- `_ledger_lock` / `_check_limit_state` の関数名と、`reserve_all_cells` からの呼び出し辺。
- 既存テストの関数名・assertion・期待例外。

## 4. 変異事前登録 (DW-M01。実装前に登録する)

各変異は「その入力を拒否する層が前後にも内側にも他に無い」ことを実装後に確認する。

|#|変異位置|変異内容|殺すテスト (単一理由)|
|---|---|---|---|
|M1|`_check_limit_state` の `cell.reserved_bench_s > 0.0`|`>= 0.0`|`test_all_zero_cell_reservations_are_insufficient`|
|M2|同 `all(...)`|`any(...)`|`test_one_zero_cell_reservation_makes_whole_matrix_insufficient`|
|M3|`_check_limit_state` の return|`all_cells_reserved and` を削除|`test_all_zero_cell_reservations_are_insufficient`|
|M4|arm 正値検査|`<= 0.0` を `< 0.0`|`test_budget_limits_reject_nonpositive_caps[arm]`|
|M5|holdout 正値検査|`<= 0.0` を `< 0.0`|`test_budget_limits_reject_nonpositive_caps[holdout]`|
|M6|arm 対称性検査|`if` 本体の `raise` を `pass`|`test_budget_limits_reject_asymmetric_arm_caps[gross]`|
|M7|arm 対称性検査|`!=` を `math.isclose(..., rel_tol=0.0, abs_tol=_TOLERANCE)` の否定へ緩める|`test_budget_limits_reject_asymmetric_arm_caps[ulp]`|
|M8|holdout 和検査|`if` 本体の `raise` を `pass`|`test_budget_limits_reject_holdout_caps_not_summing_to_total[gross]`|
|M9|holdout 和検査|`!=` を `math.isclose(..., rel_tol=0.0, abs_tol=_TOLERANCE)` の否定へ緩める|`test_budget_limits_reject_holdout_caps_not_summing_to_total[ulp]`|
|M10|`_check_limit_state` の `total_ok`|`True` 固定|既存 `...witness[total]`|
|M11|同 `arm_ok`|`True` 固定|既存 `...witness[arm]`|
|M12|同 `holdout_ok`|`True` 固定|既存 `...witness[holdout]`|

**過剰拒否の正例 (受理集合を縮小する wave の必須登録)。** 次が緑のままであること:

- `test_normative_limits_with_positive_cells_are_held` (規範適合・非一様 holdout 上限)
- `test_all_three_layers_within_limit_are_held`
- `test_budget_limits_require_arm_and_holdout_coverage` (期待例外が `coverage` のまま)
- `test_prepare_s8c_budget_inputs_accepts_matching_ratified_holdout_ids`
- `test_prepare_s8c_budget_inputs_rejects_mismatched_holdout_id_set`

**登録しない変異。** `cell.reserved_bench_s > 0.0` を `!= 0.0` にする変異は、`ReservationCell` が
正規化後の float を保存しないため builtin float 以外では等価でない (所見 A-3)。等価とも
KILLED とも申告せず、事前登録から外す。

## 5. 親が実測した数値 (段 4 で確認済み)

すべて `python3` で直接評価して確認した。

- 規範適合 fixture 8 件すべてで `holdout 和 == 総上限` が厳密に真、`min(arm) == max(arm)` が真、
  全上限が正。唯一 `coverage-neg` (total 1.0、holdout (1.0,1.0)) だけ和が一致しないが、
  これは coverage 検査が先に発火するので影響しない。
- 3 層 witness は各 param で対象層だけが偽になる (total / arm / holdout)。
- ULP 負例: `nextafter(8.0,9.0)` は `!=` で拒否、`isclose(abs_tol=1e-9)` では受理。
  `total=nextafter(24.0,25.0)` と holdout `(12.0,12.0)` も同様。したがって M7・M9 は必ず殺せる。
- `json.dumps`/`loads` の round-trip は上記すべての値で厳密一致する (読み戻し経路で崩れない)。
