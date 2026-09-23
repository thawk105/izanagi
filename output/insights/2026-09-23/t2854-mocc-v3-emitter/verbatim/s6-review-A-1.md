**判定: GO（静的レビュー A として、親の計算ノード検証へ進めてよい）。** C3 の追加によって成果物を壊す具体的な経路は確認できませんでした。裁定 §3 の実走による完了判定は未了です。

以下の `transaction.cc` は、指定された `review/files/cc/mocc/transaction.cc` の物理行番号です。header の参照は pin ではなく C3 `53f6b097` の本文に基づきます。

| 区分 | 所見 |
|---|---|
| must-fix | なし |
| should | なし |
| nit | なし |

成立した real 所見、および修正要求に値する未解消の疑いはありません。

**不成立の攻撃**

- **C の重複・欠落:** `transaction.cc:1162` の v3/v2 は排他的。`transaction.cc:1330` の commit は validation 成功時だけ writePhase を一度呼ぶ。正常に戻る成功取引では C/E が各一本になる。
- **v3 の形式不一致:** `transaction.cc:1163`、`:1176`、`:1192` と X 四箇所は C3 の helper 契約に一致。C/R/W/X はそれぞれ 10/6/7/5 token、nS/nQ は 0。`parse.py:346` 以降の受理契約と矛盾しない。
- **abort・validation 失敗からの種別漏れ:** `include/tpcc.hh` の RETRY は query 再生成、begin、setter を再通過する。abort が context を消さなくても次の試行が上書きする。RLL/CLL の処理から commit を直接呼ぶ経路もない。
- **quit・例外からの種別漏れ:** quit による retry 打切り後は worker が終了し、別 workload に移らない。worker 内に例外を捕捉して次取引へ復帰する経路もない。成功時は `transaction.cc:1318` で clear し、TRACE build の成功 commit 計数は quit により省略されない。
- **誤った表番号:** 正常 read と UPDATE/INSERT/DELETE は API 引数 `s` を要素の `storage_` に保存する。表を渡さない `read_set_.emplace_back(key, tuple)` は aborted を設定する失敗経路にあり、その試行は emitter に到達しない。表番号は実際に参照する Masstree の番号と一致する。
- **YCSB の v2 bytes 変更:** context 0 の C/R/W/X/E の既存式は保持されている。ここで確認できるのは同じ取引情報に対する出力形式・bytes の保持であり、別実行間のスケジュールや trace 全体の一致ではない。
- **TRACE=0 への追加コード漏出:** C++ の追加はすべて `#if TRACE` 内。独立した文字処理照合でも、TRACE 部分を除いた本文と論理行番号は C1′ と一致した。レビュー用 C1′/C3 ファイルの blob は、それぞれ C/C3 の git object と一致した。
- **TRACE=1 の警告原因:** 追加変数は使用され、helper の引数型・スコープ・波括弧に問題を認めない。ただし `-Wall -Wextra -Werror` の成功は未実走であり、保証しない。
- **YCSB の証拠面消失:** `transaction.cc:1219`、`:1244`、`:1277`、`:1301` に既存の `izanagi_trace::emit_lock_violation(` が残る。validation の P stream も不変。`model.py` の literal TRACE 領域抽出と X/P 正規表現に適合する。
- **比較基点 C の誤り:** C1′ の mocc blob は C と同一。C..C3 の差分は header 二つと mocc 一つで、C の既存 X/P 計装を保持した上への追加を検証する基点として整合する。pin 全体や D297 の合格へ一般化はできない。

**変異の前提への攻撃**

| 変異 | 静的レビュー結果 |
|---|---|
| M1m | context 読みを 0 にすれば TPC-C が v2 を出す。期待する schema 失敗と整合する。派生理由の併発も裁定で許容されている。 |
| M2 | D1 の成功 commit 直後の quit により、旧順序では C/E を出した成功取引の計数だけが落ちる。witness 差を作る筋は成立する。 |
| M3m | W の表 6→5 は双方とも有効な表番号で、行数・frame・種別は維持する。content-table を狙う変異として整合する。 |
| M4m | C の種別 1↔2 は双方とも有効値で、R/W の表・件数は維持する。content-txtype を狙う変異として整合する。 |
| M5m | `transaction.cc:1283` の `#line 1187` 削除で、`:1290` の ERR の論理行は **1193→1207**。次の `#line 1195` で復元される。共通 transaction.cc を使う ycsb/tpcc/bomb/sbomb の四 entry に効く構造で、include 指令は変わらない。 |

M3m/M4m の**理由集合が実際に単独となること**、M5m の **4 不一致・17 一致**は、検査器・compile database を含む実走結果で確定する必要があります。上表は KILLED の認定ではありません。

## 総括

C3 の emitter に修正必須の問題は見つからず、**静的レビュー A は GO**。ファイル書込み・テスト・build は実行していません。親は裁定 §3 の前処理・構文・binary・witness・YCSB certified・変異検査を完了してから成果物を完了扱いにしてください。TPC-C certified および D297 合格は、このレビューでも主張しません。