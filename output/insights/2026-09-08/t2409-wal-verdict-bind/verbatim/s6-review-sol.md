## 裁定との一致

実装述語は裁定どおりです。

- `record.payload` を使用。
- `type(anomalies) is int`、`anomalies == 0`、`certified is True`、`verdict == "serializable"` がすべて存在。
- `try/except Exception` の外、unknown tag と unmapped variant の `continue` より前。
- 違反時は [b10_backoff_shape_sweep.py:3415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/campaign/b10_backoff_shape_sweep.py:3415) で、campaign ID と variant を含む `legacy-wal-verdict` を送出。

保護対象も現時点の差分では不変です。

- 135 literal は各系列 45、計 135 のまま。
- balanced `8e5f0b48…`、read-heavy `27195442…` の golden は不変。
- 既存 completeness test は fixture に3値を加えただけで、assertion は不変。
- `_collect_report_inputs` は module 直下の非装飾 `FunctionDef` のまま。既存 AST test 4 箇所も残存。
- legacy binding、3 validator、lock binding、`wal.py` に差分なし。
- 新 helper は 2859 行、新 test は 2897 行以降で、2463〜2670 行には入っていません。
- Git 差分は実装 file と test file の2つだけです。

ただし、collector 正例は裁定 A10 に一致していません。詳細は所見に記します。

## 攻撃の結果

45 block record と campaign lock を変えず、90件と tag 15/75を維持したまま、任意の `verify_done` を変更すると次で停止します。

- `anomalies=1`: 3411行の比較が偽になり、3415行で送出。
- `anomalies=false`: 3410行の exact type 検査が偽になり、3415行で送出。
- `certified=false` または `1`: 3412行が偽になり、3415行で送出。
- `verdict!="serializable"`: 3413行が偽になり、3415行で送出。
- unknown tag、unmapped variantでも、それぞれ3429行、3433行へ到達する前に停止。

現物3系列の静的読取結果はすべて次のとおりです。

- WAL 135件、`verify_done` 90件。
- tag は legacy 15、performance 75。
- 3値は90/90で正常。
- 全 file が newline 終端。
- read-heavy の90件には `proof_surfaces` が存在しますが、追加述語は余分な key を参照しないため拒否しません。

止まらない変種も存在します。90件すべてを `anomalies=0`、`certified=true`、`verdict="serializable"` と自己申告したまま、実際の verifier 実行や `commits`、`aborts` などを偽造した WAL は通ります。これは段4の B1 で既に scope 外と裁定された真正性の限界で、新しい所見ではありません。

## 所見

1. **real / must-fix / NO-GO — collector 正例が production validator と campaign lock を全面的に stub 化している。**

   [test_b10_backoff_shape_sweep.py:3056](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:3056) で block record 読取を空配列にし、3065〜3073行で3 validator、3075〜3078行で lock 検査を stub に置換しています。これは裁定 A10 の「3 validator と lock を通過済みの専用 fixture」と、依存層を stub して得た正例を証拠にしないというレビュー条件に反します。呼出回数を記録しても、実検査を通った証明にはなりません。

   放置時: production の成果物値と受理集合は直ちには変わりませんが、正例の参照先が実 validator／lock ではなく stub になり、collector 経路の緑を本物と主張できません。

他に real な所見はありません。assertion の弱体化、skip／xfail、揮発 payload の期待値化、既存受理集合を緩める実装分岐は見つかりませんでした。

## GO / NO-GO

**NO-GO。**

実装述語自体は正しく、対象攻撃も停止します。しかし、裁定が must-fix とした production validator・lock 通過済み正例が未達です。実物の45 block record相当と campaign lockを用い、3 validatorと `_assert_report_lock_binding` を stub せず通す正例へ直す必要があります。

## 総括

正しさゲート本体は裁定どおりで、現物3系列も静的には受理されます。唯一の阻害事項は、collector 正例が両側の既存ゲートを stub 化した偽の統合証拠であることです。pytest は実行しておらず、緑とは報告しません。