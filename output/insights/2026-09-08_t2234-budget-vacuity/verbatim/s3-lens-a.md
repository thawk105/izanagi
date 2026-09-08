## 所見

1. **変更対象 2 file では完結せず、既存 2 テストが setup 中に落ちる。**

   **根拠:** `BudgetLimits.__post_init__` に和の検査を置く計画 (`s2-plan.md:45-93`) に対し、`test_p3_autonomous_workload_trial.py:9097-9101` は `total=2.0`、holdout 上限 `{H1:2.0,H2:2.0}` を構築する。この helper は `:9128-9159` の 2 テストから呼ばれ、検査対象へ到達する前に例外になる。プランは変更対象を 2 file に限定している (`s2-plan.md:305-311`)。

   **壊れる具体的入力:** `BudgetLimits(total=2, arms={on:2,off:2,swapped:2}, holdouts={H1:2,H2:2})`。holdout 和 `4 != 2` で `BudgetError`。`H1=H2=1.0` へ直せば規範適合し、既存 2 テストの holdout-set に関する主張は変わらない。

   **重大度:** blocker

2. **`1e-9` 許容差は規範本文から導けず、literal な規範違反を受理する。テストも許容差境界を固定しない。**

   **根拠:** 規範は arm 上限を「対称」、holdout 和を総上限に「一致」と定めるだけで許容差を規定していない (`docs/phase3-8c-preregistration.md:163-165`)。プランは別用途の ledger 再集計規約を流用して `math.isclose(..., abs_tol=1e-9)` とする (`s2-plan.md:13-22,73-92`)。また差 `1.0`、`2.0` の負例しかなく (`s2-plan.md:271-272,284-287`)、`abs_tol=1e-8` への弱体化は全計画テストを通り得る。

   **壊れる具体的入力:** arm `{on:0,off:0,swapped:5e-10}`、total `1`、holdout `{0.5,0.5}` は非対称なのに受理される。total `5e-10`、arm 全 `0`、holdout `{0,0}` も和が不一致なのに受理される。逆に、正確に等しい arm `{8,8,8}` や total `9`、holdout `{3,6}` は誤発火しない。許容差を正式な意味とするなら、差 `0.5e-9` の正例と `1.5e-9` の負例を両検査へ足す必要がある。

   **重大度:** must-fix

3. **`> 0.0` から `!= 0.0` への変更は、現在の受理型全体では等価変異ではない。**

   **根拠:** `_finite_nonnegative` は一度 `float(value)` へ変換するが (`s8c_budget.py:43-49`)、`ReservationCell.__post_init__` は戻り値を field へ保存しない (`s8c_budget.py:122-128`)。したがって比較演算を上書きした `float` subclass が保持される。プランの等価性主張 (`s2-plan.md:293`) は builtin `int/float` にしか成立しない。

   **壊れる具体的入力:** `float` subclass が `__gt__` を常に `False`、`__ne__` を常に `True` と返す値 `WeirdFloat(1.0)` を全 6 cell に入れる。現行案の `> 0` は `insufficient`、変異後の `!= 0` は数値上限内なら `held` になる。

   **重大度:** must-fix。最小対応はこの変異を「等価」と申告しないこと。field の正規化追加は本題を越えるため別裁定が要る。

4. **親 brief の「予算停止を一度も発火させられない」は広すぎる。**

   **根拠:** 現行 `_check_limit_state` は三層の超過時に実際に false を返す (`s8c_budget.py:517-530`)。既存テストも三層それぞれの `insufficient` witness を持つ (`test_s8c_budget.py:51-65`)。恒真なのは「全 cell の予約が実在する」という未実装の述語であり、consumer 全体ではない。

   **壊れる具体的入力:** 各 cell `4.0`、total 上限 `10.0`、arm・holdout 上限 `100.0` では、現行コードでも total 層が発火して `insufficient` になる。

   **重大度:** must-fix。パッチの方向は変わらないが、主張は「ゼロ予約を排除する検査が存在しない」へ限定すべき。

5. **親 brief の理由コード帰属は誤りだが、プランでは訂正済み。**

   **根拠:** `symmetric_indeterminate()` は cell ID 集合だけを返す (`s8c_budget.py:651-664`)。`budget-insufficient` は report builder と supervisor が付ける (`p3_autonomous_workload_trial.py:2156-2191,4975-5000`)。親 brief はこれを関数自身の理由コードと書いている (`s1-brief.md:69-73`)。

   **壊れる具体的入力:** 1 cell が `0.0` の `insufficient` ledger を関数へ渡すと、返るのは `frozenset(cell_ids)` であり理由文字列ではない。

   **重大度:** nit

## プランのうち支持できる部分

3 検査はいずれも恒真・恒偽ではなく、計画した主要負例は対象を正しく隔離している。

|検査|発火する入力|非発火すべき入力|検査を除去した場合|
|---|---|---|---|
|全 cell 正値|`h1-on=0`、他 5 cell=`4`、標準 limits。total=`20`、arm・holdout も上限内|H1 各 `1`、H2 各 `2`、total=`9`、arm=`3`、holdout=`{3,6}`|one-zero テストが `held` になり失敗する|
|arm 対称性|`{8,8,9}`、total=`24`、holdout=`{12,12}`|`{8,8,8}`|非対称 cap の例外テストが失敗する|
|holdout 和|total=`24`、holdout=`{13,13}`、arm 全 `8`|total=`9`、holdout=`{3,6}`|和不一致の例外テストが失敗する|

- 全ゼロ・1 cell ゼロ・arm 非対称・holdout 和不一致の 4 負例には空振りがない。`all` から `any` の変異も one-zero 負例が直接殺す。
- `test_normative_limits_with_positive_cells_are_held` は検査削除では緑のままになるが、これは負例ではなく誤発火を防ぐ正例なので問題ではない。なお `test_all_three_layers_within_limit_are_held` も `not` 除去変異を殺すため、帰属は固有ではないが誤帰属でもない。
- 変更計画 5 は total・arm・holdout の単独 witness を維持しており、主張を弱めない。変更計画 6 は total と holdout の複合不足になるが、当該テストの主張は「insufficient ledger の部分実走拒否」だけなので弱体化ではない。
- production の受理集合が広がる経路は見つからない。新しい論理積と constructor 例外はいずれも既存受理入力を拒否側へ移すだけで、test helper の拡張は production surface ではない。
- 変異の KILLED 帰属は、所見 3 の等価変異申告を除けば正しい。total-only witness も親の実測どおり対象層だけを殺す。
- module 名、entrypoint、call edge、schema、state 語彙を変えない計画は規律 5 に適合し、一般化や framework 化にも踏み込んでいない。

## 親 brief の誤り

- consumer 全体が「一度も発火しない」のではなく、ゼロ予約でも三層の `<=` が通ることが欠陥である。所見 4 の限定が必要。
- `symmetric_indeterminate` が理由コードを返すという帰属は誤り。所見 5 のとおり supervisor 側の責務である。
- constructor 調査は数え方が不整合である。host Python の実行可能な call site は 5 個 (`s8c_budget.py:333`、`test_p3...:9097`、`test_s8c_budget.py:28,79,85`)。`test_s8c_preregistration_predicates.py:4394` は一時 candidate へ書く source 文字列内の第 6 の textual call で、host 側では実行されない。
- import、`getattr`、`import_module`、`__import__` を静的検索した範囲では、別名・動的 constructor 経路は見つからなかった。したがって列挙漏れではなく、5 件と 6 件の分類説明不足である。
- loader が無条件 raise する事実 (`p3_autonomous_workload_trial.py:2074-2079`) と、実コードに明示的なゼロ予約 caller がないという事実は支持できる。ただし C06 評価器は引き続き必ず `EVIDENCE_UNDEFINED` を返すため (`s8c_preregistration_evidence.py:3837-3842`)、本変更を C06 充足と報告してはならない。

## 総括

- プランは現状のままでは受理不可で、未計画の supervisor fixture 修正が blocker である。
- 三つの検査と主要負例は発火し、production の受理集合を広げる変更も見つからない。
- ただし `1e-9` を規範上の同一性とする裁定、およびその境界テストが不足している。
- `> 0` と `!= 0` の等価変異申告は現在の型検査下では誤りである。
- 変更計画 5・6は規律 2 を弱めず、必要な fixture 修正も主張を保った調整として実施できる。
- 以上は静的検査結果であり、pytest を実走して緑とは確認していない。