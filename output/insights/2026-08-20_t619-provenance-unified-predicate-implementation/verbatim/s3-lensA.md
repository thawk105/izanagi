レビュー結論は、blocker 1件、must-fix 2件、nit 1件です。

[severity: blocker] [tools/check_ai_provenance.py:1720] `authoritative` が `_ledger_policy_is_visible` の実呼び出しへ明示配線されていない → `_known_violation_audit` へ未使用フラグを追加するのではなく、同呼び出しに `authoritative=authoritative` を渡す。未配線だと `333605d6` が stale 扱いとなり、既定監査は rc=2 で失敗する。

[severity: must-fix] [tools/check_ai_provenance.py:1471] `ancestry=None, authoritative=True` の CAB 経路が `_has_co_authored_by_policy()` の lineage 判定だけで、第2項を評価しない → authoritative 時は ancestry=None を拒否するか、CAB seed 集合を取得して両方向判定を実装する。

[severity: must-fix] [tools/check_ai_provenance.py:1408] CAB seed 集合が空の場合、計画案は常に False とするが、提示された数式は空集合なら第2項が真になる → 「seed が存在しない規則は非適用」という前提を数式・実装・テストへ明記し、plan:689 の `bool(seeds)` と整合させる。

[severity: nit] [s2/plan.md:720] HEAD drift の rc=2 優先、起動時 pin 回数、graft 非存在/空ファイル、複数 replace ref の受入テストが不足している → drift 時に findings を出力せず rc=2 となるテストと、guard の境界ケースを追加する。

独立検証では、非空 seed に対する `applies_epoch` と bitset の CAB 判定は、epoch/seed 自身を含む反射性も含めて数式と一致します。コード全文の epoch/選択集合 consumer に、列挙された箇所以外の漏れはありません。

現在の repo では policy add は `50c1ef4e...` の1件のみ。shallow=false、graft ファイルは非存在、replace ref は空で、guard による false rc=2 は起きません。既存台帳42件も変更後述語で全件 visible=True です。

byte 数は一致します。`104+77+129+38=348B`、統合文は180B、`docs/ai-provenance.md` は6270B→6102B、family は8977B→8809B。両 needle の出現数も各1件です。forward correction も現在の candidate は1件だけで、選択集合拡大による将来の strict 化は計画どおりです。

## 総括

プランは主要設計を満たしていますが、ledger の authority 配線を明示修正し、authoritative oracle と空 seed の意味を確定させてから実装へ進むべきです。