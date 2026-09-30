## 所見

### 1. 不正な macro 値が `#error` を通過する — must-fix

根拠: [silo-lock-order-variant.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/patches/silo-lock-order-variant.patch:9) の `#ifndef` は「定義済み」しか確認せず、12・15 行の `#if` は未定義の識別子を 0 として評価する。

再現入力: `-DSILO_ORDER_VARIANT=foo`。`foo` は未定義なら 0 と評価され、範囲検査を通って stock 枝が選ばれる。`-DSILO_ORDER_VARIANT=1 -DNO_WAIT_LOCKING_IN_VALIDATION=1 -DNO_WAIT_OF_TICTOC=foo` も不正値のまま通る。

**受理の含意:** 指定値が 0/1 ではない build を、契約上有効な build として受け入れる。**拒否の含意:** 値を 0 または 1 の単一トークンに限定すれば、これらの入力は build 前に拒否される。

放置時は、候補を選んだつもりの成果物が stock の実行体となり、レポートや台帳の build 条件と実体が食い違いうる。推奨 fix は、マクロ値を文字どおり `0`/`1` に限定する前処理チェックを追加し、未定義識別子・式・範囲外値を負例に加えること。fix 後に通るべき正例は `SILO_ORDER_VARIANT=1, NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0`。

## 総括

**NO-GO。** 所見は上記 must-fix 1 件。静的検査では、禁止名を通す候補、既定 profile の受理・拒否順の変更、sort の集合・順序・TID 読み、通知位置、gate の先行書き込み、condition gate の既存 macro への波及について、追加の具体的な破れは見つからなかった。M1〜M6 の単一理由性はコードとテストの照合に限って確認した。テストは実行していない。