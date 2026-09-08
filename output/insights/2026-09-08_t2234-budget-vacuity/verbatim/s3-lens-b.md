## 破壊面の全数

呼び出し側から AST で辿った結果、非規範 `BudgetLimits` の既存 fixture は次の 5 構築箇所で全数だった。

- `orchestrator/tests/test_s8c_budget.py:54`、`:55`、`:56`
  - 新しい `BudgetLimits.__post_init__` では decorator 評価中に `BudgetError` となり、未修正なら test module 自体が collection error になる。
  - プランは 3 件とも規範適合値へ修正している。
- `orchestrator/tests/test_s8c_budget.py:181`
  - `total=10` に対して holdout 和が `24`。プランは `(5, 5)` へ修正している。
- `orchestrator/tests/test_p3_autonomous_workload_trial.py:9097-9101`
  - `total=2` に対して holdout 和が `4`。この helper を使う `:9128-9142` と `:9145-9160` の 2 テストが `BudgetError` になる。
  - プランはこのファイルを変更対象に含めていない。

意図的な coverage 負例 `test_s8c_budget.py:77-89` は、新検査より先に既存 coverage 検査が発火するため壊れない。標準 `_limits()` を使う他のテストも `24 / 8 / (12,12)` で規範適合である。

`_check_limit_state` の結果を消費する経路は 2 本だけである。

- 新規予約: `reserve_all_cells` の `s8c_budget.py:555-567` が結果から `held` / `insufficient` を決める。production 側は `p3_autonomous_workload_trial.py:4964-5003` で `insufficient` を対称停止へ投影する。
- 読み戻し検証: `_ledger_from_raw` の `s8c_budget.py:466-481` が保存済み state と再計算結果の一致を要求する。

保存済み ledger の読み戻し入口は次の 4 箇所で全数である。

- 既存 ledger の再予約: `s8c_budget.py:572-589`
- 新規作成直後の再読込: `s8c_budget.py:590-592`
- `settle` の更新前: `s8c_budget.py:604-605`
- `settle` の更新後: `s8c_budget.py:646-648`

いずれも `_read_ledger -> _ledger_from_raw -> _limits_from_raw -> BudgetLimits` を通る (`s8c_budget.py:330-337,466,497-498`)。checked-in の `s8c-budget-ledger/v1` 実体は見つからなかった。

decoy の `BudgetLimits(1.0, {}, {})` は実行されない。source 文字列を一時 repository に書いて commit し (`test_s8c_preregistration_predicates.py:4555-4580`)、評価器が blob を `ast.parse` するだけである (`s8c_preregistration_evidence.py:751-803`)。親の読解は正しい。

## 所見

1. プランは既存 2 テストを確実に壊す変更面を落としている。

   - 根拠: `orchestrator/tests/test_p3_autonomous_workload_trial.py:9076-9101,9128-9160`。プランの変更対象は `s8c_budget.py` と `test_s8c_budget.py` に限られる (`s2-plan.md:43-263`)。
   - 壊れる具体的入力: `total_bench_s=2.0`、arm 全て `2.0`、holdout `{H1:2.0,H2:2.0}`。holdout 和 `4.0 != 2.0`。
   - 重大度: **blocker**
   - 最小修正は当該 fixture の holdout を `{H1:1.0,H2:1.0}` にすること。テストの主張は弱まらない。

2. 新しい 3 検査をすべて通り、総予算 0 のまま `held` になる通常の float 入力がある。

   - 根拠: `_TOLERANCE=1e-9` (`s8c_budget.py:39`)。プランは一致検査にも上限検査にも同じ絶対許容差を使い、予約の実在は単に `> 0.0` とする (`s2-plan.md:73-92,118-136`)。
   - 壊れる具体的入力:
     - total `0.0`
     - arm `{on:0.0, off:5e-10, swapped:1e-9}`
     - holdout `{H1:5e-10, H2:0.0}`
     - 6 cell の予約をすべて `5e-324`
   - arm の最大差 `1e-9` と holdout 和の不一致 `5e-10` は一致扱いになり、各予約は正値だが全合計も `1e-9` 未満なので、結果は `held` になる。
   - 重大度: **blocker**
   - 想定された千秒単位の値域では一致検査は恒真ではない。一方、実装が値域や事前コストとの結合を強制しないため、受理領域には一致検査が実質恒真となる微小値 regime が残る。ゼロ上限を malformed とするか、予約を許容差より大きくするか、正式コスト計画との結合まで待つかは裁定が必要である。

3. `ReservationCell` が検証済み float を保存しないため、`> 0.0` は受理済みオブジェクト上の信頼できる比較になっていない。

   - 根拠: `_finite_nonnegative` は `isinstance` で subclass を許可して plain float を返す (`s8c_budget.py:43-49`) が、`ReservationCell.__post_init__` は返り値を捨てる (`:122-128`)。プランは元オブジェクトを直接比較する (`s2-plan.md:118-121`)。
   - 壊れる具体的入力: `float(0.0)` の subclass で `__gt__` だけ常に真にした値を全 cell に渡す。候補 state は `held` になるが、JSON には `0.0` が保存され、作成直後の再読込で `BudgetError` となって不整合 ledger が残る (`s8c_budget.py:590-592`)。
   - 重大度: **must-fix**
   - `ReservationCell` に plain float を保存する正規化、または exact builtin type 制約と負例が必要である。

4. 旧 ledger の fail-closed 方向は正しいが、プランの説明は条件付きであり、回帰テストもない。

   - 根拠: 規範適合 limits の旧 ledgerなら、再計算が `insufficient`、保存 state が `held` なので `s8c_budget.py:474-481` で `BudgetError` になる。旧 limits 自体が非規範なら、`:466` の `BudgetLimits` 再構築で先に失敗する。
   - 壊れる具体的入力: 6 cell 全て予約 `0.0`、state `held`、limits `24 / 8 / (12,12)` の保存済み v1 ledger。
   - 重大度: **must-fix**
   - 安全面では bench 前停止なので正しい。ただし production では lifecycle start 後に予約を読む (`p3_autonomous_workload_trial.py:4923-4964`) ため、例外は experiment-wide indeterminate と restart 禁止へ進む (`:5088-5118`)。互換移行ではないことを受理するなら、旧 ledger の raw fixture を使う負例を追加すべきである。

5. production で変更を発火させる schedule authority が未結線である。

   - 根拠: `_load_s8c_schedule_authority` は常に例外を送出し (`p3_autonomous_workload_trial.py:2074-2079`)、`_prepare_s8c_budget_inputs` は limits/cells へ到達できない (`:2082-2153`)。呼び出しは予約より前である (`:4956-4964`)。
   - 壊れる具体的入力: 任意の `registered-effective` かつ `do_build=True` の trial。limits の値に関係なく schedule 読込で停止する。
   - 重大度: **must-fix**
   - 裁定パッケージ候補は「本 wave を dormant consumer の狭い hardening として完了し、実効化や §5 解除を主張しない」対「別 wave で schedule authority と正式コスト計画を結線してから実効化を主張する」の二択。現 scope では前者を推奨する。

## プランのうち支持できる部分

- 予約 0 を新しい state ではなく既存 `insufficient` へ倒す P2 は、schema と state 語彙を変えず supervisor の対称停止へ接続できる。
- 規範違反 limits を `BudgetError` とする P3 は、予算不足との原因混同を避ける。配置も新規入力と保存済み ledger の双方を通る。
- P4 の total-only witness は計算どおり成立する。`24.0` は total 上限だけを超え、arm と各 holdout は個別の `1e-9` 帯内に残る。既存 assertion を弱める必要はない。
- C06 の pin は壊れない。
  - `entrypoints` 3 件は不変 (`s8c_preregistration_evidence_contract.v1.json:258-261`)。
  - `field_paths` は不変で、dataclass field と属性 chain も残る (`:236-242`; `s8c_preregistration_evidence.py:3646-3754`)。
  - `reachable_from` 3 chain は不変 (`contract:244-255`; evaluator `:3524-3546`)。
  - `_ledger_lock`、`_check_limit_state` と required call edge は維持される (`evidence.py:3781-3802`)。
  - supervisor からの 4 target も不変 (`:3813-3831`)。
  - 同名 object の import・局所定義は増えず、D613 の再訪条件に該当しない。
  - invariant の exact function set も変わらない (`test_s8c_preregistration_invariant.py:81-84,351-359,482-496`)。
- gate、検査 framework、ledger schema、state、一般化を追加しておらず、scope の逆方向への逸脱はない。上記 blocker を直すための fixture 修正も主張の弱化ではない。

## 親 brief の誤り

- `s1-brief.md:84-85` の「実装差分 2 file」は不完全である。既存 2 テストを維持するには `test_p3_autonomous_workload_trial.py` を含む 3 file が必要になる。
- 「path を key にする pin は 2 箇所のみ」は、production 判定だけを指すなら理解できるが、repository 全体の記述としては誤りである。`test_s8c_preregistration_invariant.py:81-84,123-127` と `test_s8c_preregistration_predicates.py:29-34` も path を明示的に pin している。whole-file SHA pin がないという部分は否定されない。
- `s1-brief.md:70-71` の「`symmetric_indeterminate` の理由コード」は不正確である。関数は cell 集合だけを返し (`s8c_budget.py:651-664`)、`budget-insufficient` を付けるのは supervisor (`p3_autonomous_workload_trial.py:2156-2191`)。
- schedule authority の到達不能、p3 fixture が 2 テストを壊すこと、decoy source が実行されないことについて、親の事実認定は正しい。

## 総括

プランは C06 pin、schema、既存 3 層 witness を維持しており、基本配置も妥当である。  
ただし p3 fixture の未修正だけで既存 2 テストが赤になるため、現状のまま author へ渡せない。  
さらに微小正値と絶対許容差により、総予算 0 でも `held` になる受理領域が残り、恒真化修正としては blocker である。  
旧 ledger は実際に `BudgetError` へ fail-closed するが、非規範 limits ではより早く失敗し、production lifecycle も消費する。  
production authority は依然到達不能なので、本 wave を dormant hardening と位置付ける裁定が必要である。  
pytest は実走しておらず、結論は静的経路検査と浮動小数式の確認に基づく。