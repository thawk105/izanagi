## 通り抜ける形の判定表 ((a)〜(n)、穴/fail-closed、real/refuted、scope 内/外)

**v1.1 は F918 の直接の握り潰しを拒否するが、「握り潰されていない」の証明にはならない。特に (a)、(c)、(n) は実在する構文上の反例である。**

以下は静的判定であり、pytest・分類関数・変異は実行していない。`real` は規則とコードから反例が成立すること、`refuted` はその形での通過主張が成立しないことを指す。各例は、既存の行範囲・suffix・第1引数名が一致し、別経路の被覆がない場合を前提とする。

`T` = `orchestrator/tests/test_ccbench_spawn_sites.py`。規則の正本は [brief:68](/home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s1-brief.md:68)。

| 形 | v1.1 の判定と理由 | real/refuted・scope |
|---|---|---|
| **(a) `return` の後に末尾 `raise`** | **被覆に数える＝穴。** 「最後の top-level 文が `ast.Raise`」を満たす。先行する無条件 `return` で到達不能でも判定は変わらない。既存 `_flow_block` が到達不能文を歩かないことは、handler の AST 末尾を直接見る新判定を救わない。 | **real・scope 内。** 名指しした再送出判定そのものの不足。MAYBE の末尾 bare `raise` にも同じ穴がある。 |
| **(b) handler 内の `try/finally` にだけ `raise`、finally が `return` 終端** | **数えない＝fail-closed。** handler の末尾は `ast.Try` であり、規則は「`try/finally` …の内側だけの raise」を明示的に拒否する。 | **refuted・scope 内。** ただし、その `Try` の後ろに到達不能な top-level `raise` を追加すると (a) 型の real な穴になる。 |
| **(c) enclosing try の finally が `return` / `break` / `continue`** | **被覆に数える＝穴。** handlers の検査だけでは finalbody による例外抑止を検出しない。break/continue は合法なループ内配置を前提とする。 | **real・scope 内と判断。** 親は保証限界に置くが、同じ try の明示的な抑止を拒否することは import・shadow・支配関係の新機構ではない。 |
| **(d) `contextlib.suppress(Exception)` 内の check** | **被覆に数える＝穴。** `with` は try stack に拒否条件を加えず、E は `Exception` の子なので実際には抑止される。 | **real・scope 外候補。** 一般の `__exit__` の意味解析は今回の限定判定を超える。名前だけの suppress 特例にも真正性の問題がある。 |
| **(e) 局所 `E2 = S1DriverError`、`except E2: pass`** | **数えない＝fail-closed。** module の既知束縛がない `E2` は MAYBE。「末尾が bare `raise`」でないため拒否する。 | **refuted・scope 内で既に拒否。** 「局所 alias は保証しない」は、この単純例まで穴になるという意味ではない。module の NONE 名を局所で上書きする別例は後述。 |
| **(f) module alias chain／`getattr` 式** | Name chain で E に解決できれば DEFINITE、`pass` は拒否。`getattr(mod, "DriverError")` は MAYBE なので `pass`・変換 raise は拒否、末尾 bare `raise` なら外側検査へ進む。 | **単純な握り潰しは refuted・scope 内。** ただし最終代入表は時系列の束縛証明ではなく、再束縛・分類優先順位は別問題。循環を NONE にしてはならない。 |
| **(g) `except (S1DriverError, PilotError): pass`** | **数えない＝fail-closed。** E の要素により tuple 全体が DEFINITE、末尾 Pass で拒否。 | **refuted・scope 内。** |
| **(h) `except* S1DriverError: pass`** | **数えない＝fail-closed。** 「TryStar の body 内の check は被覆に数えない」が明文。 | **refuted・scope 内。** ただし内側の変換 raise で先に成功 return すると、外側 TryStar を見落とす実装になる。TryStar 禁止は早期成功より優先させる必要がある。 |
| **(i) lambda／内包表記／入れ子 def** | **一律ではない。** T:1711 の `ast.walk(expression)` は lambda・内包表記内の call も現在 scope に記録する。try の外で lambda を定義し、後の呼出しだけを握り潰す形は **被覆に数える穴**。空の内包表記や遅延 generator も実行保証がない。通常の入れ子 `def _check()` の本体は別 scope なので、外側 sink にはその check を数えない。同期内包表記を直接 `except E: pass` で囲めば拒否する。 | **lambda／遅延・未実行式は real・scope 外候補**（実行・scope・支配関係）。**入れ子 def に包むだけの外側 sink 通過は refuted。** sink も子関数内にあれば、呼出し側の握り潰しは別途保証外。 |
| **(j) `if False:`／`if enabled:` 内の check** | **被覆に数える＝穴。** T:1797 は両枝を解析し、check の記録自体は枝の交差で消えない。injected 分岐はその記録を直接使う。 | **real・scope 外。** guard と sink の支配関係の証明は D1882 の却下事項に該当する。 |
| **(k) `built = other` の後で `check(built)`** | **被覆に数える＝穴。** T:2002 は sink の代入名、T:2181 は文字列一致を見る。campaign 用の名前 kill は injected の記録を無効にしない。 | **real・scope 外。** 値の同一性・再束縛追跡の追加に当たる。 |
| **(l) `raise SystemExit(0)`／`raise StopIteration`** | `SystemExit(0)` は非 bare の Raise として **被覆に数える**。`raise StopIteration` も「末尾 ast.Raise」で受理する読みになるが、`Y(...)` だけを変換とするのかは文言を統一すべき。 | **「例外でない」は refuted。両方とも例外。** SystemExit(0) は成功終了扱いへの変換として **real な保証不足**だが、拒否後に通常継続する証拠ではない。StopIteration の意味は利用文脈次第。終了状態の契約は **scope 外候補**。 |
| **(m) MAYBE handler が変換 raise** | **数えない＝fail-closed。** v1.1 が明示的に拒否する。 | **穴は refuted・scope 内。** 実際には E を捕まえない型なら過剰拒否だが、MAYBE という情報量に対する保守的拒否として正当。production の WAL handler は bare raise なので該当しない。 |
| **(n) 変換 raise の外側で `except PilotError: pass`** | **被覆に数える＝穴。** 「そこで追跡を止め被覆に数える」ため、明示的な外側の握り潰しを見ない。 | **real。問題は名指しした拒否伝播の scope 内。** 一般的な変換後例外追跡まで今 wave に足せるかは別問題。「名指し外」と断定して済ませる親の読みは支持しない。 |

## 親の実測値・前提の検証

**8個の明示的 raise がすべて `DriverError(...)` であることと、helper が送出しうる例外が E だけであることは別である。**

[s1:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s1_direct_comparison.py:358) の指定範囲では、raise は **369 / 371 / 376 / 379 / 384 / 392 / 396 / 403** の8個。376・379 は内部関数 `observed_requests` 内であり、これらも base の `DriverError(...)` を構築する。明示的に子 class を構築して送出する経路は、この範囲にはない。[s1:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s1_direct_comparison.py:113) の直接基底は `RuntimeError`、125 の `_SortSwoOracleRejected` はその子である。

ただし、以下は E への変換が保証されていない。

- 366・367 の `getattr` は、入力オブジェクトの属性アクセス処理が送出する例外を伝播しうる。
- 377〜380 の属性取得・集合・辞書構築、382 の比較には、明示的 raise 以外の失敗経路がある。
- 388 の `require_condition_gate_family` から変換するのは `ConditionMeaningGateError` だけ。他の例外まで変換するコードではない。
- 398 の unpack、399〜402 の属性アクセス・比較も E に包まれていない。

呼出し先の本文は射影対象でないため、その例外集合は確認していない。属性アクセス等が E の子 class を送出する可能性も、この helper の本文だけでは排除できない。従って NONE の根拠は、**「helper の明示的な拒否 raise が作る base E」への限定**でなければならない。

production の handler 順と v1.1 の静的な受理見込みは、訂正版と整合する。

| check | 確認した順序・外側構造 |
|---|---|
| s1:1218 | 1204-try：WAL tuple → bare raise、`_SortSwoOracleRejected` → 通常継続、`DriverError` → bare raise、`Exception` → 条件付き raise／継続。外側1151には handlers がなく、1380の finally に明示的な return/break/continue はない。 |
| s1:1295 | 1279-try：WAL → bare raise、`DriverError` → bare raise、`Exception` → status 代入。その外側は1204、1151。 |
| driver:1801 | 1730-try：WAL → bare raise、`S1DriverError` → `OracleDriverError` へ変換、`Exception` → aborted result の生成。外側1660の `Exception` handler は末尾 break。 |
| n_pilot:1018 | 1017-try：`S1DriverError` → `PilotError` へ変換。996-try は build call の側であり、この check を囲まない。 |

[driver:1729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_driver.py:1729) で `evaluate_started = True`、[1842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_driver.py:1842) ではその条件で再送出する。したがって、外側 handler の末尾が break という事実だけで production が実際に握り潰すとは言えない。一方、v1.1 はこの条件を証明して受理するのではなく、外側を見ないことで受理する。この違いが (n) の根本である。

`covered 38`、実際の分類結果、M1 KILLED は本段では確認していない。

## NONE 分類と規律 2 の整合

**NONE は「ClassDef が存在する」という構文事実だけでは健全でない。現在の E と現在の束縛が維持されるという前提が必要である。**

- `class Foo(DriverError)` は、変更されていない base E のインスタンスを捕まえない。この限定では親の説明は正しい。
- **s1 自身で** `class Foo(RuntimeError)` の後に `DriverError = Foo` とすれば、helper 内のグローバル参照も Foo に変わる。`except Foo: pass` を ClassDef 由来の NONE とすると実際の拒否を見落とす。Name chain による E 判定と ClassDef 判定が衝突する場合の優先順位も、v1.1 には不足している。
- **helper を import する別 module だけで** `DriverError = Foo` としても、s1 helper のグローバルは変わらない。これだけで同じ反例になるという主張は **refuted**。
- 別 module に独自の `class DriverError(RuntimeError)` があり、helper は s1 から import している場合、その class は真の E ではない。**クラス名が同じだけで DEFINITE にしない**という v1.1 の条件は必要である。
- module の `class Foo(...)` を根拠に NONE としながら、関数内で `Foo = S1DriverError` と再束縛して `except Foo: pass` とすると穴になる。(e) の未知の局所 alias と異なり、誤った NONE が MAYBE の拒否を迂回する。
- helper 定義 module について一般化すれば、`class Foo(RuntimeError); class DriverError(Foo)` も Foo が E の親になる反例。「別の ClassDef は E の親 class にはなれない」は一般命題として誤りであり、現在の直接基底が `RuntimeError` であることに依存する。

これらを全面的に防ぐ束縛・真正性解析は D1882 の却下範囲に接する。前提を無条件の事実として説明せず、残存限界と未規定の分類競合を明示する必要がある。

規律2については比較対象を区別する。

1. **v1 との比較：** v1.1 は、変換再送出で追跡を止める点では受理を広げる。一方、未知型を MAYBE として拒否する点では狭める。従って受理集合全体を単純な包含関係にはできないが、(n) 型の新規受理は確実にある。
2. **現行 main との比較：** [T:2175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py:2175) の一致条件を保存して `and unswallowed` を加える限り、injected 分岐の受理集合は main の部分集合になる。F918 型を拒否するので、意図した範囲では真に狭まる。
3. **不変条件との関係：** brief の「受理形を増やす向きの変更は不採用」を provisional v1 にも適用するなら、v1.1 は抵触する。main を比較基準にするなら抵触しない。基準を明記すべきであり、main より狭いことだけで全残存穴を正当化はできない。

F918 の義務は「**握り潰さず変換して再送出する**」である。「変換 raise を一度見れば外側の握り潰しを不問にする」とは書かれていない。(n) を F918 の義務そのものと説明するのは過剰な一般化である。

## 推奨 (scope 内で塞ぐ最大 3 件、裁定パッケージ候補)

**本 wave 内で直ちに追加すべき規則は2件。** どちらも指定された handler／try の構文検査で閉じ、production 4 check の確認済み形を拒否しない。

1. **末尾 raise の手前の制御脱出を拒否する。**
   位置：[T:1700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py:1700) 直前に予定する handler 判定。

   追加文案：

   > 「DEFINITE・MAYBE とも、末尾 Raise だけでは再送出済みとしない。handler の同一実行 scope に Return・Break・Continue が存在する場合は被覆に数えない。入れ子関数・class・lambda の本体は当該 handler の実行文として走査しない。」

   handler 内のループ脱出まで保守的に拒否する形だが、現在受理に必要な WAL・E の handler は該当しない。(a)、条件付き return、(b) に到達不能 raise を足す形を負例にする。

2. **enclosing finally の明示的な抑止を成功判定より先に拒否する。**
   位置：[T:1866](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py:1866) の stack 管理と新判定。

   追加文案：

   > 「check からの例外伝播時に実行される enclosing finalbody に、同一実行 scope の Return・Break・Continue が存在する場合は被覆に数えない。この検査および enclosing TryStar の拒否は、変換再送出による追跡停止より先に行う。」

   handlers 用 stack と、実行される finally の保持を混同しない。例えば check が try の handler／else 内にある場合も、その try の finally は作用する。s1:1380 の finally には該当する脱出文がなく、確認した production 4箇所はこの追加条件で落ちない。

**裁定パッケージへ返す候補：**

- **(n) の保証範囲。** 穴自体は名指しした拒否伝播の問題であり、scope 外と処理済みにしない。変換後の一般的な型・伝播追跡と、driver の条件付き再送出を証明する実装は拡張になる。「限定判定として受け入れる」か「production を維持できる追加解析を許す」かを返す。コメントだけで閉包の完全保証を維持してはならない。
- **(d)、(i)、(j)、(k)：** context manager の抑止、遅延実行・呼出し境界、条件支配、値の再束縛。今回の限定判定外の解析が必要。
- **NONE の再束縛・親子関係・helper 由来の保証：** import 真正性・shadow の一般解析と、helper の例外集合の扱い。今回の ClassDef 表を無条件に健全と名乗らない。
- **(l)：** 変換先の終了コード・反復終了等を、条件拒否としてどこまで許すかという契約。

加えて、実装前の文言修正として、非 bare Raise の扱いを統一する必要がある。`raise exc` や `raise S1DriverError(...)` は必ずしも別型への「変換」ではない。これらまで追跡停止させれば、外側の `except E: pass` も通る。少なくともこの例を、未規定のまま author の判断へ渡すべきではない。

## 総括

**v1.1 は main より狭いが、(a)、(c)、(n) を通す。** (a) と (c) は今回の判定内で塞げる。(n) は、production の受理を維持するために追跡を打ち切った保証上の欠落であり、D1882 の名指し外と断定できない。

親の raise 数・直接基底・handler 順の訂正は確認できた。ただし「明示的 raise は base E」と「helper の全例外は base E」、「ClassDef がある」と「実行時にも別 class に束縛されている」は区別が必要である。

本回答は指定資料の静的検査のみ。テストの緑・変異の検出結果は主張しない。