## 所見

1. 既知の極小正値 regime は閉じていない。今回の実装漏れではなく、裁定済みの scope-out である。
   - 根拠 (`orchestrator/campaign/s8c_budget.py:113`, `orchestrator/campaign/s8c_budget.py:530`; `s4-verdict.md:18`)
   - 壊れる具体的入力: 総上限 `1e-9`、arm 各 `1e-9`、holdout 各 `5e-10`、全 6 cell の予約を最小正 subnormal `5e-324` とする。全検査を通り、総予約 `3e-323` で `held` になる。
   - 成果物影響: 実質的に空に近い予約でも ledger の `reservation.state` が `held` になる。
   - 重大度 (nit): 最低予約量は規範に無く、段 4 が明示的に実装対象外としているため、本 wave の差し戻し理由にはしない。

## 攻撃して壊れなかった箇所

置換された既存 fixture の主張は保たれている。

|fixture|静的判定|
|---|---|
|3 層 witness `total`|予約総量 `24.0` に対し、総上限との差は `1.499998347753717e-9` なので `total_ok` だけが偽。各 holdout は `12.0 <= 11.99999999925 + 1e-9`、arm は上限内であり、holdout 上限和も総上限に厳密一致する (`orchestrator/tests/test_s8c_budget.py:64`)。|
|3 層 witness `arm`|総量と holdout は一致し、各 arm の `8.0 > 5.0 + 1e-9` だけが偽 (`orchestrator/tests/test_s8c_budget.py:71`)。|
|3 層 witness `holdout`|総量・arm は上限内で、H1 の `12.0 > 5.0 + 1e-9` だけが偽 (`orchestrator/tests/test_s8c_budget.py:72`)。|
|stale-lock fixture|新 limits では total と holdout の双方が不足理由になるが、テストの主張は「insufficient ledger の一部実行を拒否」であり維持される (`orchestrator/tests/test_s8c_budget.py:189`)。この fixture 単独の total-only 性は失ったが、専用 `total` witness が M10 を捕捉する。|
|p3 holdout fixture|`BudgetLimits` は規範適合になり、対象関数は limits の型と holdout 集合だけを見る。matching の返却 cells と mismatching の例外理由は変わらない (`orchestrator/tests/test_p3_autonomous_workload_trial.py:9076`, `orchestrator/campaign/p3_autonomous_workload_trial.py:2129`)。|

追加負例は対応する検査を実効的に殺す。

- 全ゼロでは `all_cells_reserved and` を除くか `>` を `>=` にすると、3 層はすべて上限内なので `held` となり assertion が失敗する (`orchestrator/tests/test_s8c_budget.py:259`)。
- 1 cell ゼロでは残り 5 cell が正なので、`all` を `any` にすると `held` になる。total `20`、arm 最大 `8`、holdout 最大 `12` で、別層による masking はない (`orchestrator/tests/test_s8c_budget.py:271`)。
- arm ゼロと holdout `(0,24)` は、それぞれ正値検査を除くと後続の対称性・和検査を通る (`orchestrator/tests/test_s8c_budget.py:300`)。
- arm gross/ULP は正値かつ holdout 和一致、holdout gross/ULP は正値かつ arm 対称なので、対象検査以外で先に拒否されない (`orchestrator/tests/test_s8c_budget.py:310`, `:326`)。
- arm ULP 差は `1.7763568394002505e-15`、holdout total ULP 差は `3.552713678800501e-15`。どちらも `abs_tol=1e-9, rel_tol=0` の `math.isclose` では一致扱いになるため、M7・M9 は指定 ULP case の期待例外を確実に失わせる。
- `test_normative_limits_with_positive_cells_are_held` は負例ではなく過剰拒否対策の正例であり、個別検査の削除を殺さないのは目的どおり (`orchestrator/tests/test_s8c_budget.py:340`)。

各検査には発火・非発火の双方がある。

|検査|発火する regime|発火しない regime|
|---|---|---|
|arm 正値|`(0,0,0)`|`(8,8,8)`|
|holdout 正値|`(0,24)`|`(12,12)`|
|arm 対称性|`(8,8,9)` または ULP 差|`(8,8,8)`|
|holdout 和|total `24`、`(13,13)` または total の ULP 差|total `24`、`(12,12)`|
|`all_cells_reserved`|6 cell 中いずれかが builtin `0.0`|全 cell `4.0`。極小正値は所見 1 の既知境界。|

上限値は `_finite_nonnegative` の戻り値を保存するため、float subclass の比較上書きでは4検査を迂回できない (`orchestrator/campaign/s8c_budget.py:90`)。`ReservationCell` は戻り値を保存しない既知限界があるが、ゼロを正と偽装しても公開予約経路では JSON 読み戻し後に builtin `0.0` となり、limit state 不一致で受理されない (`orchestrator/campaign/s8c_budget.py:141`, `:607`)。

M1〜M12 は masking されていない。M1/M3 は全ゼロ、M2 は1ゼロ、M4/M5 はゼロだけが新規正値検査へ到達し、M6〜M9 は他の新規条件を満たす。M10〜M12 は上表のとおり対象層だけが偽である (`s4-verdict.md:115`; `orchestrator/campaign/s8c_budget.py:535`)。

旧 ledger 負例の例外理由も単一である。書換え後も schema、4 hash、cell matrix、`cell_ids`、limits、予約再集計値、budget 値は整合し、document 全体の content hash 検査は存在しない。`_check_limit_state` だけが `sufficient=False` を再計算し、保存された `"held"` との比較で `BudgetError("reservation の limit state が不一致")` になる (`orchestrator/campaign/s8c_budget.py:353`, `:445`, `:479`, `:487`)。`all_cells_reserved` を外せば読み戻しも `settle(... actual_bench_s=0.0)` も通るため、このテストは読み戻し経路を実効的に捕捉する (`orchestrator/tests/test_s8c_budget.py:363`)。

production の受理方向は、非正・非対称・和不一致 limits の拒否と、ゼロ cell の `held` から `insufficient` への縮小だけである。変更は裁定指定の3ファイル内に収まり、指示外の framework、schema、gate、参照変更はない (`s5-implementation.diff:1`)。

## 総括

- 静的レビュー上、新規 blocker / must-fix はない。
- 置換 fixture の各 assertion は維持され、専用3層 witness は対象層だけを偽にする。
- M1〜M12 は指定入力において他層に masked されず、ULP case も `1e-9` 許容差への戻しを殺す。
- 旧ゼロ予約 ledger は content 改変一般ではなく、再計算した limit state との不一致だけで拒否される。
- 実走はしておらず、上記はコード経路と数値の静的判定である。