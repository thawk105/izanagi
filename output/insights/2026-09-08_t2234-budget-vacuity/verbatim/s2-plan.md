## 決定

1. 予約値 0 は P2 を採り、1 cell でも 0 なら `insufficient` にする。

規範は「全 cell を実走前に予約」し、不足時には未実施 arm 全体を対称に判定不能へ倒すことを要求する (`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:231-265`, `docs/phase3-8c-preregistration.md:237-239`)。1 cell が 0 なら、その cell の実時間は予約されていない。総和が正でも「全 cell の予約」にはならないため、総和 0 の場合だけ止める案は不十分である。

`BudgetError` にする案も採らない。既存の実行経路は `state == "insufficient"` を検出し、`symmetric_indeterminate()` で全 cell を停止した後、`reason="budget-insufficient"` の report と lifecycle terminal を生成する (`orchestrator/campaign/p3_autonomous_workload_trial.py:2165-2171`, `:4975-5003`)。予約 0 は malformed な型ではなく、既存の有限非負検査を通るが予約が不足している状態なので、この経路へ載せるのが意味的にも規律にも一致する。`ReservationCell` 自体の非負許容は維持し、`_check_limit_state` の十分性だけを狭める (`orchestrator/campaign/s8c_budget.py:122-128`, `:517-530`)。

なお `symmetric_indeterminate()` 自体は理由コードを返さず、`insufficient` なら cell id 集合を返すだけである (`orchestrator/campaign/s8c_budget.py:651-664`)。`budget-insufficient` を付けるのは supervisor 側である。

2. 規範の 2 条件は P3 どおり `BudgetLimits.__post_init__` に置き、違反は `BudgetError` にする。

対象は次の 2 条件である (`docs/phase3-8c-preregistration.md:163-165`)。

- arm 上限の最大値と最小値が `_TOLERANCE` 内で一致すること。
- H1/H2 上限の和が総上限と `_TOLERANCE` 内で一致すること。

違反は予算量の不足ではなく、規範外の limits なので `insufficient` にせず `BudgetError` とする。そうしないと supervisor が `budget-insufficient` と報告し、原因を誤分類する。

配置は型・有限性・coverage の正規化が済む `BudgetLimits.__post_init__` の末尾が適切である (`orchestrator/campaign/s8c_budget.py:89-112`)。読み戻しも `_ledger_from_raw()` の `:466` から `_limits_from_raw()` の `:330-337` を経て必ず `BudgetLimits(...)` を生成する。したがって新規予約だけでなく、手編集された ledger の limits も同じ検査を通る。

比較は既存の `_TOLERANCE = 1e-9` (`orchestrator/campaign/s8c_budget.py:39`) と、既存の `math.isclose(..., rel_tol=0.0, abs_tol=_TOLERANCE)` 規約 (`:467-472`) に合わせる。数学的完全一致ではなく、絶対誤差 `1e-9` 以下を同一と扱う。

3. P4 は許容差帯の中に total 層だけの数値 witness を作り、既存テストの主張を維持する。

次の limits を使う。

```python
total_bench_s = 23.9999999985
per_arm_bench_s = 8.0
per_holdout_bench_s = (11.99999999925, 11.99999999925)
```

予約値は既存どおり各 cell `4.0`、総和 `24.0` とする。この入力では Python の実値で次が成立する。

- holdout 上限和は `23.9999999985` で総上限と完全一致。
- total: `24.0 <= 23.9999999985 + 1e-9` は偽。
- arm: `8.0 <= 8.0 + 1e-9` は真。
- holdout: `12.0 <= 11.99999999925 + 1e-9` は真。

したがって total 層だけが失敗する。holdout ごとに個別の `+1e-9` があるため、2 holdout 合計では最大 `2e-9` の余地がある一方、total 層の余地は `1e-9` だけであり、その差に witness を置ける。`test_each_budget_layer_has_a_numeric_insufficient_witness[total]` を削除・xfail・例外期待へ変更せず、3 層すべての数値不足 witness と対称停止の主張を保てる (`orchestrator/tests/test_s8c_budget.py:51-65`)。

## 変更計画

1. `orchestrator/campaign/s8c_budget.py:104-112` の holdout map 正規化直後へ規範検査を追加する。

置換前:

```python
        object.__setattr__(
            self,
            "per_holdout_bench_s",
            _immutable_limit_map(
                self.per_holdout_bench_s,
                field="per_holdout_bench_s",
                expected_keys=_HOLDOUTS,
            ),
        )
```

置換後:

```python
        object.__setattr__(
            self,
            "per_holdout_bench_s",
            _immutable_limit_map(
                self.per_holdout_bench_s,
                field="per_holdout_bench_s",
                expected_keys=_HOLDOUTS,
            ),
        )
        if not math.isclose(
            min(self.per_arm_bench_s.values()),
            max(self.per_arm_bench_s.values()),
            rel_tol=0.0,
            abs_tol=_TOLERANCE,
        ):
            raise BudgetError("per_arm_bench_s は arm 間で対称でない")
        holdout_total = sum(
            self.per_holdout_bench_s[holdout]
            for holdout in ("H1", "H2")
        )
        if not math.isclose(
            holdout_total,
            self.total_bench_s,
            rel_tol=0.0,
            abs_tol=_TOLERANCE,
        ):
            raise BudgetError(
                "per_holdout_bench_s の和が total_bench_s と一致しない"
            )
```

2. `orchestrator/campaign/s8c_budget.py:517-530` の十分性へ全 cell 正値条件を追加する。

置換前:

```python
    total_reserved_bench_s = sum(cell.reserved_bench_s for cell in cells)
    by_arm = _sum_by(cells, key="arm")
    by_holdout = _sum_by(cells, key="holdout")
    total_ok = total_reserved_bench_s <= limits.total_bench_s + _TOLERANCE
    arm_ok = all(
        value <= limits.per_arm_bench_s[arm] + _TOLERANCE
        for arm, value in by_arm.items()
    )
    holdout_ok = all(
        value <= limits.per_holdout_bench_s[holdout] + _TOLERANCE
        for holdout, value in by_holdout.items()
    )
    return total_reserved_bench_s, total_ok and arm_ok and holdout_ok
```

置換後:

```python
    total_reserved_bench_s = sum(cell.reserved_bench_s for cell in cells)
    all_cells_reserved = all(
        cell.reserved_bench_s > 0.0 for cell in cells
    )
    by_arm = _sum_by(cells, key="arm")
    by_holdout = _sum_by(cells, key="holdout")
    total_ok = total_reserved_bench_s <= limits.total_bench_s + _TOLERANCE
    arm_ok = all(
        value <= limits.per_arm_bench_s[arm] + _TOLERANCE
        for arm, value in by_arm.items()
    )
    holdout_ok = all(
        value <= limits.per_holdout_bench_s[holdout] + _TOLERANCE
        for holdout, value in by_holdout.items()
    )
    return (
        total_reserved_bench_s,
        all_cells_reserved and total_ok and arm_ok and holdout_ok,
    )
```

`_check_limit_state` の名前、返却型、`reserve_all_cells()` からの直接呼び出し (`:556`) は維持する。C06 評価器が要求する関数集合と call edge (`orchestrator/campaign/s8c_preregistration_evidence.py:3781-3802`, `:3821-3831`) は変えない。

3. `orchestrator/tests/test_s8c_budget.py:25-36` の helper を、非対称な holdout 上限も表現できる形へ変える。

置換前:

```python
def _limits(
    *, total: float = 24.0, per_arm: float = 8.0, per_holdout: float = 12.0
) -> B.BudgetLimits:
    return B.BudgetLimits(
        total_bench_s=total,
        per_arm_bench_s={
            "on": per_arm,
            "off": per_arm,
            "swapped": per_arm,
        },
        per_holdout_bench_s={"H1": per_holdout, "H2": per_holdout},
    )
```

置換後:

```python
def _limits(
    *,
    total: float = 24.0,
    per_arm: float = 8.0,
    per_holdout: tuple[float, float] = (12.0, 12.0),
) -> B.BudgetLimits:
    return B.BudgetLimits(
        total_bench_s=total,
        per_arm_bench_s={
            "on": per_arm,
            "off": per_arm,
            "swapped": per_arm,
        },
        per_holdout_bench_s={
            "H1": per_holdout[0],
            "H2": per_holdout[1],
        },
    )
```

4. `orchestrator/tests/test_s8c_budget.py:39-48` の `_reserve` に任意の cells を渡せるようにする。

置換前:

```python
def _reserve(path: Path, *, limits: B.BudgetLimits) -> B.Ledger:
    return B.reserve_all_cells(
        path,
        ...
        cells=_cells(),
        limits=limits,
    )
```

置換後:

```python
def _reserve(
    path: Path,
    *,
    limits: B.BudgetLimits,
    cells: tuple[B.ReservationCell, ...] | None = None,
) -> B.Ledger:
    return B.reserve_all_cells(
        path,
        ...
        cells=_cells() if cells is None else cells,
        limits=limits,
    )
```

5. `orchestrator/tests/test_s8c_budget.py:51-57` の既存 3 層 parameter を、規範適合 limits に置き換える。

置換前:

```python
[
    pytest.param(_limits(total=10.0, per_arm=100.0, per_holdout=100.0), id="total"),
    pytest.param(_limits(total=100.0, per_arm=5.0, per_holdout=100.0), id="arm"),
    pytest.param(_limits(total=100.0, per_arm=100.0, per_holdout=5.0), id="holdout"),
]
```

置換後:

```python
[
    pytest.param(
        _limits(
            total=23.9999999985,
            per_holdout=(11.99999999925, 11.99999999925),
        ),
        id="total",
    ),
    pytest.param(_limits(per_arm=5.0), id="arm"),
    pytest.param(_limits(per_holdout=(5.0, 19.0)), id="holdout"),
]
```

関数名と `:62-65` の全 assertion は維持する。これにより total、arm、holdout の各 id は、他層を超過せず対象層だけで `insufficient` になる。

6. helper の型変更に伴い、`orchestrator/tests/test_s8c_budget.py:181` を次のように直す。

置換前:

```python
ledger = _reserve(tmp_path / "insufficient.json", limits=_limits(total=10.0))
```

置換後:

```python
ledger = _reserve(
    tmp_path / "insufficient.json",
    limits=_limits(total=10.0, per_holdout=(5.0, 5.0)),
)
```

このテストの主張は「insufficient ledger で一部 cell だけ走った場合の拒否」なので、期待例外や assertion は変えない。

7. 追加テストは `orchestrator/tests/test_s8c_budget.py:239` の `_run()` より前へ置く。schema、state 語彙、`_ledger_lock`、C06 entrypoint は変更しない。

## 追加テスト

|関数名|入力|期待結果|
|---|---|---|
|`test_all_zero_cell_reservations_are_insufficient`|`cells=_cells(0.0)`、`limits=_limits()`|予約作成は成功し、`state == "insufficient"`、総予約 `0.0`、`symmetric_indeterminate(ledger) == ledger.cell_ids`|
|`test_one_zero_cell_reservation_makes_whole_matrix_insufficient`|`h1-on` だけ `0.0`、残り 5 cell は `4.0`、標準 limits|全数値上限内でも `state == "insufficient"`、総予約 `20.0`、全 cell が対称に判定不能|
|`test_budget_limits_reject_asymmetric_arm_caps`|total `24`、arm `{on:8, off:8, swapped:9}`、holdout `{H1:12,H2:12}`|`BudgetLimits(...)` が `BudgetError`、`match="対称"`|
|`test_budget_limits_reject_holdout_caps_not_summing_to_total`|total `24`、arm 全て `8`、holdout `{H1:13,H2:13}`|`BudgetLimits(...)` が `BudgetError`、`match="total_bench_s"`|
|`test_normative_limits_with_positive_cells_are_held`|H1 の各 cell `1.0`、H2 の各 cell `2.0`。total `9`、arm 全て `3`、holdout `{H1:3,H2:6}`|`state == "held"`、総予約 `9.0`、`symmetric_indeterminate(...) == frozenset()`|
|既存 `test_each_budget_layer_has_a_numeric_insufficient_witness[total]`|total `23.9999999985`、holdout 各 `11.99999999925`、各予約 `4.0`|total 層だけが許容差超過し、既存 assertion のまま `insufficient`|
|既存 `...[arm]`|total `24`、arm 全て `5`、holdout `{12,12}`|arm 層だけが超過し、既存 assertion のまま `insufficient`|
|既存 `...[holdout]`|total `24`、arm 全て `8`、holdout `{5,19}`|H1 holdout だけが超過し、既存 assertion のまま `insufficient`|

## 変異事前登録候補

|対象検査|1 行変異候補|必ず殺すテスト|
|---|---|---|
|全 cell が正値|`cell.reserved_bench_s > 0.0` を `>= 0.0` にする|`test_all_zero_cell_reservations_are_insufficient`、`test_one_zero_cell_reservation_makes_whole_matrix_insufficient`|
|「全 cell」の量化|`all(...)` を `any(...)` にする|`test_one_zero_cell_reservation_makes_whole_matrix_insufficient`。正値 cell が 5 個あるため mutant は誤って `held`|
|arm 上限対称性|`min(self.per_arm_bench_s.values())` を `max(...)` にする|`test_budget_limits_reject_asymmetric_arm_caps`。比較が max 対 max になり mutant だけ受理|
|arm 上限の許容差|当該 `abs_tol=_TOLERANCE` を `abs_tol=1.0` にする|`test_budget_limits_reject_asymmetric_arm_caps`。差 1.0 が誤って許容される|
|holdout 和と総上限の一致|`if not math.isclose(` を `if False and not math.isclose(` にする|`test_budget_limits_reject_holdout_caps_not_summing_to_total`|
|holdout 和の許容差|当該 `abs_tol=_TOLERANCE` を `abs_tol=2.0` にする|同テスト。差 2.0 が誤って許容される|
|total 数値層|`total_ok = ...` を `total_ok = True` にする|既存 parameter の `[total]`|
|arm 数値層|`arm_ok = all(...)` を `arm_ok = True` にする|既存 parameter の `[arm]`|
|holdout 数値層|`holdout_ok = all(...)` を `holdout_ok = True` にする|既存 parameter の `[holdout]`|
|正しい入力の受理|どちらかの `if not math.isclose(` から `not` を除く|`test_normative_limits_with_positive_cells_are_held`。正しい limits が誤って例外になる|

等価変異として、`cell.reserved_bench_s > 0.0` を `cell.reserved_bench_s != 0.0` にする変更は、既存の有限非負検査 (`orchestrator/campaign/s8c_budget.py:43-49`, `:128`) の下では等価であり、テストで殺せない。`all_cells_reserved` と他の論理積の順序変更、H1/H2 の加算順序変更、arm の最大・最小取得順序変更も等価変異として KILLED 対象に数えない。

## 反証と残る穴

- この案が止めるのは正確な `0.0` だけである。`5e-324` のような極小正値は予約として受理されうる。正式 workload の事前コスト計画との対応や最低予約量は本 wave の規範・scope に無いため、ここでは新設しない。
- arm 対称性と holdout 和は数学的完全一致ではなく、最大 `1e-9` の差を許容する。既存 consumer 全体の浮動小数規約との整合を優先した結果である。
- P4 の total-only witness は現在の `_TOLERANCE = 1e-9` に依存する。許容差を将来変更する場合は値を再計算する必要がある。
- 旧版で作られた「予約 0、state held」の ledger は、自動で `insufficient` に移行しない。読み戻し時に新しい `_check_limit_state` が false を返し、保存済み state との不一致として `BudgetError` になる (`orchestrator/campaign/s8c_budget.py:474-481`)。これは fail-closed だが互換移行ではない。
- 親 brief の「`symmetric_indeterminate` の理由コード」という表現は厳密には誤りである。理由文字列は supervisor が付け、関数自身は集合だけを返す。
- C06 評価器は runtime の値妥当性を証明せず、最終的にも `EVIDENCE_UNDEFINED` を返す (`orchestrator/campaign/s8c_preregistration_evidence.py:3837-3842`)。本変更は runtime consumer の恒真性を直すが、C06 を `SATISFIED` にする変更ではない。
- pytest は実走していない。P4 の浮動小数比較だけを読み取り専用の Python 式で確認した。

## 総括

P2 と P3 を採り、予約 0 は `insufficient`、規範外 limits は `BudgetError` とする。  
全 cell 正値検査は `_check_limit_state`、arm 対称性と holdout 和検査は `BudgetLimits.__post_init__` に置く。  
読み戻しも `BudgetLimits` を必ず再構築するため、同じ規範検査が手編集 ledger にも作用する。  
P4 は `1e-9` の層別許容差の差を利用して total-only witness を維持でき、既存テストを弱める必要はない。  
変更対象は `s8c_budget.py` と `test_s8c_budget.py` のみで、C06 の名前、呼び出し辺、schema、state 語彙は維持する。