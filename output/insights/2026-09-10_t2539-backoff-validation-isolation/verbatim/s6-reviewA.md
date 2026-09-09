## 親の所見 1 の判定

**real。**

`_classify_edits()` が root 編集を確定した後も、先に `_build_closure()` を完走させています（[check_silo_validation_isolation.py:1168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:1168)、[同:1175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:1175)）。そこで追加行の未解決 call が `UNKNOWN_EDITED_CALLEE` を投げ（[同:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:883)）、交差生成処理（[同:1201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:1201)）へ到達しません。

親の単調性の説明は正しいです。既知の root または到達済み callee に edit があれば、以後の展開失敗によってその要素が V から消えることはありません。

直し方:

- [check_silo_validation_isolation.py:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:822) の閉包構築を、部分閉包と任意の `expansion_error` を返す形にする。
- [同:1175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:1175) 以降を、部分閉包との交差計算を先に行い、優先順位を「交差あり → INTERSECTION、交差なしで未消費または展開不完全 → ERROR、完全かつ交差なし → NO_INTERSECTION」とする。
- [同:1194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:1194) の `unconsumed` も、既知の交差を ERROR へ上書きしてはならない。
- test には列挙された 7 patch を追加し、すべて rc=1、root depth=0 を固定する。

## 親の所見 2 の判定

**real。判定自体は段 4 の V 定義に対して正しい。test へ固定すべきです。**

`writePhase()` は [transaction.cc:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:557)、root は [同:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:383) です。両者を結ぶのは caller の `commit()`（[同:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:706)）であり、下向き閉包には入りません。

現在の test は claim の boolean しか確認していません（[test_silo_validation_isolation.py:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/tests/test_silo_validation_isolation.py:261)）。次の具体例を追加すべきです。

```python
rc, payload = _invoke(
    REPO / "patches" / "broken-silo-early-unlock-validation.patch"
)
assert rc == 0
assert payload["verdict"] == NO_INTERSECTION
assert payload["unconsumed_edits"] == []
assert {
    target
    for edit in payload["classified_edits"]
    for target in edit["targets"]
} == {"TxExecutor::writePhase/0"}
assert payload["claim_boundary"][
    "write_phase_write_writeback_correctness_covered"
] is False
```

## real 所見

### 1. default argument により、実際の callee 編集が偽の「交差なし」になる

- 何が壊れるか: validation が呼ぶ関数を編集しても `NO_STATIC_VALIDATION_CLOSURE_INTERSECTION` になる。
- 根拠: 定義側は形式引数数で symbol 化され（[check_silo_validation_isolation.py:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:526)、[同:662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:662)）、call 側は実引数数を使用します（[同:767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:767)）。一致しない既存 call は ERROR にせず外部 leaf として捨てられます（[同:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:806)、[同:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:883)）。
- 反例入力: [silo_op_element.hh:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/include/silo_op_element.hh:32) を次のように変更する patch。

```diff
-  Tidword get_tidword() { return tidword_; }
+  Tidword get_tidword(int = 0) {
+    Tidword wrong = tidword_;
+    wrong.tid ^= 1;
+    return wrong;
+  }
```

[transaction.cc:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:453) の引数なし call は C++ 上この関数を呼び続けますが、checker は `/0` を解決できず、編集を `/1` の非到達 region と判定します。

- 直し方: `FunctionRegion` に最小実引数数と最大実引数数を持たせ、default argument と parameter pack を考慮して候補を絞る。複数候補を型情報なしで一意化できなければ ERROR。上記 patch を depth=1 の FAIL test にする。

### 2. 実体で呼ばれる `Tidword` constructor が閉包から欠落する

- 何が壊れるか: validation 内の `Tidword check;` が実行する constructor を編集しても交差なしになる。
- 根拠: 呼出抽出は `name(` 形だけです（[check_silo_validation_isolation.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:729)）。さらに constructor initializer の最後の `obj_(0)` を関数名として拾うため（[同:629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:629)）、[tuple.hh:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/include/tuple.hh:24) は実質 `Tidword::obj_/1` と誤抽出されます。実際の constructor 呼出箇所は [transaction.cc:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:449) です。
- 反例入力:

```diff
-  Tidword() : obj_(0){};
+  Tidword() : obj_(0) { throw 0; };
```

これは validation の local construction を停止させますが、現解析では root から constructor edge が張られません。

- 直し方: constructor initializer list を含む署名を正しく抽出し、first-party class 型の自動変数宣言から implicit constructor edge を張る。解決不能なら ERROR。`Tidword()` 編集が `Tidword::Tidword/0` depth=1 と交差する test を追加する。

### 3. test は一般 callee 解決と claim 境界の一部を固定していない

- 何が壊れるか: callee 検出力や「純 timing 非保証」が退行しても test が検出しない。
- 根拠: 閉包 test は root、TxExecutor helper、2 comparator だけを確認しています（[test_silo_validation_isolation.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/tests/test_silo_validation_isolation.py:169)）。claim test は `pure_timing_or_side_effect_freedom_proven` を確認していません（[同:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/tests/test_silo_validation_isolation.py:261)）。
- 具体的な変異:
  - [checker:811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:811) の一般 `by_name` 候補を常に空にする。既存の期待 symbol は維持される一方、`loadAcquire`、`atomicLoadGE`、`get_tidword` が閉包から落ちる。この変異は現行 assertion 上は静的に生存する。
  - [checker:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:35) を `True` にしても現行 claim test は検出しない。
- 直し方: `loadAcquire/1` または `ReadElement::get_tidword/0` を編集する FAIL patch test、ならびに pure-timing boolean と対応する `does_not_prove` 要素の assertion を追加する。

## refuted 所見

- **edit span が会計から静かに消える疑い:** refuted。各 `+`/`-` run は `_finish_span()` で span 化され（[checker:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:320)）、分類 loop の各経路は `classified` または `unconsumed` のどちらかへ追加します（[同:1065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:1065)）。未消費専用 test もあります（[test:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/tests/test_silo_validation_isolation.py:221)）。意味上の誤分類は上記 real 所見に残りますが、単純な未会計経路はありません。
- **明示 ERROR や例外が rc=0 へ倒れる疑い:** refuted。初期 verdict は ERROR、一般例外も ERROR のまま保持され（[checker:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:170)、[同:1231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:1231)）、rc=0 は明示的な NO_INTERSECTION だけです（[同:1242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/tools/check_silo_validation_isolation.py:1242)）。危険なのは例外処理ではなく、未解決の既存 call を正常な外部 leaf とする経路です。
- **正例が完全な恒真である疑い:** refuted。正例 test は 6 span の ID、Backoff region、2 CMake macro、その閉包参照なしを個別に固定しています（[test:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/tests/test_silo_validation_isolation.py:96)）。decoy と深さ 1、2 の対照もあり、単なる「常に NO_INTERSECTION」では通りません。ただし上記の resolver 回帰までは固定できていません。
- **既存 test の期待値変更または既存 gate の受理集合拡大:** refuted。変更対象は新規 checker と新規 test のみで、checker は未接続の standalone CLI です。既存 gate の期待値変更はありません。

## 総括

親の所見 1、2 はともに real。特に所見 1 は既知交差を ERROR が上書きする検出力欠陥です。  
加えて default argument と implicit constructor に、偽の「交差なし」を作れる実害のある閉包欠落があります。  
read-only の静的レビューのみで、test は実走していません。