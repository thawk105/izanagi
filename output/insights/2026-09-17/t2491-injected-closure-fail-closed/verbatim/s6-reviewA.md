## 裁定 R0〜R4 との一致 (ずれの file:line 表)

**R0〜R4 の指定された構文規則に、受理集合を広げる実装逸脱は確認できない。ただし、再束縛による実在の穴は残る。** これらは「逐語的な裁定との一致」と「実際の拒否伝播の保証」を分けて扱う必要がある。

以下、`T` は `orchestrator/tests/test_ccbench_spawn_sites.py`。反例は既存の suffix・第1引数・行範囲が一致し、別経路の被覆がない場合を前提とする。判定は静的読解であり、分類関数・pytest は実行していない。

| 規則 | file:line | 判定 |
|---|---|---|
| R0 | T:1835、T:2048 | 一致。Expr の値、単一 Name target の Assign／AnnAssign の値が Call の場合だけ、その Call を記録する。 |
| R1 | T:1613、T:1981 | 一致。scope ごとに stack を初期化。body／orelse／handler を push し、Python の `finally` で pop。解析対象の finalbody は当該 try を積まず処理する。 |
| R2 | T:1730、T:1745 | 一致。全 stack の TryStar、全 finalbody の脱出文を、R3 の変換による早期成功より先に拒否する。入れ子 def／class／lambda には降りない。 |
| R3・分類 | T:1751 | 指定された現 scope の body・global/nonlocal・module assignment を MAYBE とし、DEFINITE、NONE の順に判定する。tuple は DEFINITE 優先、次に MAYBE、残り NONE。 |
| R3・handler | T:1783 | 一致。body 位置だけを内側から追跡。NONE は読み飛ばし、それ以外は脱出文と末尾 Raise を検査する。 |
| R3・raise | T:1794 | 一致。`raise`、as 名、DEFINITE の E 名の構築を bare 扱い。module ClassDef 名の構築を変換扱い。それ以外を拒否する。変換先の再束縛除外は裁定にも書かれていない。 |
| R3・継続 | T:1803 | 一致。DEFINITE 変換は成功終了、MAYBE 変換は拒否、DEFINITE bare は同じ try の残り handler を飛ばして外側へ進む。 |
| R4 | T:2302 | 一致。既存の行範囲・名前一致に `and unswallowed` を追加。限定保証と主要な未検査範囲をコメント化している。 |

R0 により、lambda・内包表記・短絡式・入れ子式の**内部の helper Call** は記録されない。`ast.walk` 自体は残るが、AST オブジェクトの同一性条件で除外される。Return、AugAssign、複数 target、属性 target、decorator／default の Call も記録対象外である。

production の4 check は、この制限を通る。

| sink → check | 記録と追跡 |
|---|---|
| n_pilot:997 → 1018 | Expr の直下の Call。1017 の DEFINITE handler が `PilotError(...)` へ変換し成功。 |
| s1:1208 → 1218 | 単一 Name target の Assign。1204 の WAL=MAYBE bare、子 class=NONE、DriverError=DEFINITE bare。外側1151の finally に脱出文なし。 |
| s1:1288 → 1295 | Expr の直下の Call。1279 の WAL／DriverError を経て、1204、1151へ追跡。 |
| s8b driver:1788 → 1801 | Expr の直下の Call。1730 の WAL=MAYBE bare、S1DriverError=DEFINITE 変換。1660 の handler 追跡前に成功する。 |

R1 について、with（T:1971）、if（T:1912）、ループ、match（T:2024）は同じ stack を保って body を解析する。入れ子関数は親から再帰解析せず、T:1613 の別 iteration で空 stack から開始する。class 本体自体は独立した flow 解析対象に登録されず、親 scope の check に混入しない。

decorator／default は T:1894 の親 scope・親 stack で `_record_expression` に渡される。ただし `returned_evidence_call=None` なので、injected check にはならない。

## 穴 / fail-closed の判定 ((a)〜(e) と追加の形)

| 形 | 静的判定・根拠 | DW-G05：受理集合への影響 |
|---|---|---|
| **(a) 変換先の module 再代入** | **穴。** T:1802 は ClassDef 名の存在だけを見る。`class PilotErr(RuntimeError)` の後に `PilotErr = X` とし、内側で `except X: raise PilotErr(...)`、外側で `except X: pass` とすると、実際は E の再送出なのに変換成功で停止する。局所再代入でも同様。 | E を外側で握り潰すこの形が covered に残る。main より新しく増えた形ではない。 |
| **(b) 親関数・引数の束縛** | **穴。** T:1751 は `_lexical_scopes` と args を見ない。module の `class ChildError(X)` に対し、引数 `ChildError=X` または親関数の `ChildError=X` があると、`except ChildError: pass` を NONE として読み飛ばす。 | 実行時には E を捕まえる handler が covered に残る。 |
| **(c) as 名の再代入** | **穴。** T:1795 は名前一致だけ。`except X as exc: exc = ChildError(); raise exc` を bare と読み、外側の `except ChildError: pass` を NONE として飛ばせる。 | 別例外への変換と外側の握り潰しを covered に数える。 |
| **(d) E 名の Call を bare 扱い** | **通常形は正しい。** T:1800 は `injected_error_names` 所属と DEFINITE の両方を要求する。`raise X(...)` 後の外側 `except X: pass` は拒否される。`raise Exception(...)` をこの経路で bare にはしない。 | 真の E の再構築では受理拡大なし。引数・親 scope の shadow がある場合は (b) の限界を継承する。 |
| **(e) DEFINITE 後の break と handler／orelse skip** | **穴ではない。** break は handler のループだけを抜ける。外側 try の body 位置は引き続き検査される。handler／orelse 内から出た例外を、その同じ try の handlers は捕まえないので skip は正しい。finalbody は先にR2で検査済み。 | 握り潰す外側 body-handler を飛ばす受理拡大はない。 |

(a)〜(c) は実在の限界だが、R3 が明記した構文規則には従っている。D1882 が除外した shadow・値追跡を、実装者が独自に追加しなかったことを、そのまま裁定違反とはできない。

追加の形も確認した。

- **変換後の外側 swallow／MAYBE bare の未変換経路：穴。** T:1804 の早期成功で未検査になる。裁定表9・10で scope 外とされた形である。
  **DW-G05:** この経路で拒否を消すプログラムが受理集合に残る。
- **with の抑止、条件付き check、結果名の再代入：穴。** 裁定表11の既知限界どおり。
  **DW-G05:** helper が実行されない形、拒否が抑止される形、別の値を検査する形が受理集合に残る。
- **同じ try の finalbody 内の check に続く `return`：穴。** R1 が当該 try を積まないため、`finally: check(built); return built` の拒否抑止をR2は検出しない。R1の明文に従った結果であり、実装逸脱ではない。
  **DW-G05:** finalbody 内の check 自身の拒否を消す形も covered に残る。
- **未知名・Attribute の handler が変換する形：fail-closed。** MAYBE の変換は T:1805 で拒否する。裸の `raise SystemExit(0)`、`raise mod.Err(...)`、`raise 1` も拒否する。
  **DW-G05:** これらによる受理拡大はない。

production 4 sink に (a)〜(c) の具体的な再束縛形はない。指定3 production ファイルのASTも確認し、関係する E 名・変換先 class 名について、対象関数の引数、Name store、module の Assign／AnnAssign に該当再束縛はなかった。4 check は finalbody 内でもない。

s8b の変換後追跡停止は実際に受理へ影響する。ただし production の1660側 handler は `evaluate_started` 条件で再送出するため、**解析が証明していないことと、production が握り潰していることは別**である。

## 新 test の単一理由性

| 負例 | 判定 |
|---|---|
| n1 | 単一。DEFINITE handler の末尾が Pass。 |
| n2 | 単一。bare handler の末尾が Pass。 |
| n3 | **過剰決定。** Return による脱出禁止と、末尾が Raise でない条件の両方に違反する。 |
| n4 | 単一。末尾 top-level 文が If。内部に Raise があっても受理しない。 |
| n5 | 単一。末尾 Raise は満たすが、先行 Return を脱出検査が拒否する。 |
| n6 | 単一。handler は bare 再送出を満たし、finally の Return だけが拒否理由。 |
| n7 | 単一。未知 ChildError=MAYBE の末尾 Pass。後続 X の handler は適法。 |
| n8 | 単一。R0で記録されない。 |
| n9 | 単一。末尾 Raise・脱出禁止は満たし、SystemExit の raise 形だけが不適格。 |
| n10 | **過剰決定。** TryStar 禁止を外しても、handler の末尾 Pass で拒否される。 |
| n11 | 単一。内側の DEFINITE bare は適法で、外側 handler の末尾 Pass だけが拒否理由。 |
| n12 | **再束縛規則への帰属がない。** 実装では MAYBE→Pass で拒否するが、再束縛検査を外して DEFINITE に誤分類しても Pass で拒否する。 |

正例は実際に次の経路を通る。

- p1：空 stack。
- p2：DEFINITE bare。
- p3：DEFINITE 変換。
- p4：MAYBE tuple の bare、NONE の読み飛ばし、DEFINITE bare 後の残り handler の打切り。
- p5：外側への bare 継続。ただし成功例だけでは「外側を見た」ことを証明せず、n11 が補完する。
- p6：handler position の skip。
- p7：as 名の bare 扱い。ただし外側 swallow がないため、「bare として追跡継続」と「即成功」を区別できない。

**n7 と p4 は完全な一変更対ではない。** p4 は WAL tuple と後続 Exception handler も加えている。ただし、n7 は MAYBE の Pass を拒否し、p4 は NONE の Pass を通すため、NONE/MAYBE の区別には実効性がある。ClassDef 有無だけを変える対を追加すれば帰属はさらに明確になる。

**n11 は外側追跡の拒否を単独で検証する。** ただし外側 Exception を誤って MAYBE としても拒否されるため、DEFINITE 分類そのものの専属検証ではない。

作者による変異期待集合の訂正は妥当である。M2で n8 は反応せず、M4で n5 は反応しない。段4の「M2=n1〜n12」「M4=n4・n5」をそのまま使ってはならない。

## regression

差分上、campaign の状態計算は維持されている。

- `returned_evidence_names` の生成・kill・交差処理は不変。
- `_campaign_checked_root` とその利用条件は不変。
- Try 分岐の既存 state／continues／exits 計算は保持され、追加は injected 用 stack の操作だけ。
- `_injected_check_unswallowed` は injected の記録用 bool を返し、campaign の状態へ書き戻さない。
- `returned_evidence_checks` は T:1610 の宣言、T:1842 の書込み、T:2303 の読取りが整合し、読取りも3要素 unpack に更新済み。

したがって、**campaign の判定値を変える差分は見当たらない**。旧 synthetic の期待値を書き換えた差分もない。

injected では、記録対象を絞り、既存一致条件へ bool を AND している。共通 coverage は不変なので、新しい受理集合は main の受理集合の部分集合になる。残存穴があることは、この包含関係を否定しない。

親の `s6-focus1.log` には **child rc=0、66 passed／1 skipped** の実走記録がある。ただし、log 自身が受入全走ではないと明記している。短縮出力から skip の nodeid は直接読めないため、TryStar の実走済みを主張しない。本レビューによるテスト実行、変異検出、未実走ケースまで含む「1 bit不変」の実測主張はしない。

## must-fix と nit (DW-G05 の 1 行付き、修正案)

**本 wave の裁定内で、実装変更を必須とする must-fix は確認できない。** 以下は非blocking所見。ただし、実在穴を「軽微」と評価しているわけではない。

1. **保証限界の記載不足 — T:1751、T:1795、T:1802、T:2312。**
   (a)〜(c) と finalbody 内 check の形を裁定パッケージへ追加すべき。現コメントの「result-name rebinding」だけでは、例外型名・as 名の再束縛まで明確には伝わらない。
   **DW-G05:** 放置すると上記の握り潰し形が covered に残るが、裁定どおりの受理集合からの実装逸脱ではない。
   修正候補はコメントの補足。変換先の `local_names`／`module_assignments` 除外、args／親 scope の束縛検査、as 名の再代入拒否は、裁定を更新する場合の実装候補として分離する。

2. **TryStar 専属負例の不足 — T:3206。**
   n10を保持し、`except* X: raise` の負例を追加する。R2の先行順序には、外側 TryStar＋内側 DEFINITE 変換の負例も有効。
   **DW-G05:** 現状の受理集合は変わらないが、TryStar 拒否を削除・後置して受理集合を広げても、現在の n10 では検出できない。

3. **再束縛優先順位の専属負例の不足 — T:3228。**
   n12を保持し、module に `class ChildError(X)`、関数内に `ChildError = X`、handler に `except ChildError: pass` を置く負例を追加する。再束縛判定を外した場合だけ NONE へ誤分類され、通過する形になる。
   **DW-G05:** 現状の受理集合は変わらないが、局所再束縛のMAYBE優先を削除して受理集合を広げても、n12では検出できない。

4. **n3 の過剰決定、n7/p4 の非対称性 — T:3147、T:3065、T:3183。**
   「全負例が各1理由」という報告は修正すべき。既存期待値は維持し、必要ならClassDef有無だけが違う対を追加する。
   **DW-G05:** この報告・fixture のままでも現在の受理集合は変わらないため、nit。

5. **変異期待集合の資料間不一致 — s4-ruling.md／s5-author.md。**
   親の変異宣言では、作者が説明した M2／M4 の訂正を反映する。実測なしに期待 killer を増やさない。
   **DW-G05:** 閉包検査の受理集合は変わらないが、変異の帰属を誤報するため、nit。

既存テストの期待値変更は提案しない。

## 総括

**R0〜R4 の実装は裁定の限定規則に沿っており、main より受理を広げる差分はない。production 4 check も静的には記録・受理される。**

一方、変換先・親 scope／引数・as 名の再束縛、finalbody 内 check の拒否抑止は通り抜ける。「一般に握り潰されていない」ことの証明にはならず、裁定上の保証限界として残す必要がある。

新 test の「各1理由」は成立しない。特に n10 と n12 は、名付けた規則を外しても拒否が残る。今回の must-fix は0件、専属負例の追加と保証限界・変異期待集合の補正を非blocking所見とする。実走の根拠は親 log の66 passed／1 skippedのみで、本レビューは静的検査に限る。