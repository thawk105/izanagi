## 所見対応表 (F1〜F10: closed / partial / regressed、根拠 file:line)

**実装の must-fix は確認しませんでした。F1〜F3 の反例は拒否されます。ただし、p8 の一変更対と変異 spec への反映は、完全に closed とは判定できません。**

以下、`T`＝[test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py)、`R6`＝[s6-ruling.md](/home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-ruling.md)、`Fix`＝[s6-fix.md](/home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-fix.md) とします。closed は指定された修正・記載の静的確認を意味し、変異実走済みを意味しません。

| 所見 | 判定 | 根拠 file:line |
|---|---|---|
| F1：変換先の再束縛 | closed | T:1813。ClassDef が1件、module 代入なし、局所束縛なしの全条件を要求。反例(a)は T:1821 で拒否。 |
| F2：親関数・引数の束縛 | closed | T:1751、T:1631。字句的親関数の body と全種類の引数を集約し、T:1778 で MAYBE を優先。 |
| F3：as 名の再束縛 | closed | T:1805。handler body の束縛集合に as 名があれば bare 扱いしない。 |
| F4：保証限界コメント | closed | T:2329。型名・as 名、finalbody 内 check を追加。束縛検査の細かな範囲については後述の nit。 |
| F5：専属負例・p8 | partial | T:3265、T:3298。n13〜n17 の単独反転は成立。p8 は T:3140 の共通 fixture が余分な PilotErr も追加し、R6:26 の厳密な一変更対ではない。 |
| F6：n3 の過剰決定、一変更対 | partial | n3 の期待値は維持され、問題は R6:12 に記録済み。p8 の追加は T:3125 にあるが、上記の差が残る。 |
| F7：M2/M4 の期待集合 | partial | R6:36、Fix:119以降で補正済み。T:1850、T:1800 と整合する。ただし実際の変異 spec は射影に含まれず、spec 反映までは確認できない。 |
| F8：TryStar 専属負例・未実走の記載 | closed | T:3265 の n14 は bare raise。T:3271 の skip と T:2335 の保証限界記載がある。 |
| F9：時刻表記 | closed | s4-ruling.md:1、R6:1、R6:15 に訂正済みの時刻と根拠が記載される。過去の実 mtime を今回再測定したという意味ではない。 |
| F10：scope 外の限界 | closed | T:2330、R6:16。指定事項を保証外として記載。穴を実装で解消したという判定ではない。 |

F1〜F3 は、次の反例を独立に組み立てて追跡しました。共通 import は以下です。各関数の sink 前に `marker = "BACKOFF_FIXED"` を置き、他の被覆経路はないものとします。

```python
from orchestrator.campaign.s1_direct_comparison import (
    DriverError as X, require_returned_condition_evidence,
)
```

**(a) module 再代入：**

```python
class PilotErr(RuntimeError): pass
PilotErr = X

def build(build_fn, genome):
    marker = "BACKOFF_FIXED"
    built = build_fn(genome)
    try:
        try:
            require_returned_condition_evidence(built)
        except X:
            raise PilotErr("r")
    except X:
        pass
    return built
```

内側 X は DEFINITE。`PilotErr` は E 名ではなく、R3a の `name not in module_assignments` に違反するため変換にもならない。bare=False のまま T:1821 で False。外側を調べる前に**被覆に数えない**。

**(b) 親関数による束縛：**

```python
class ChildError(X): pass

def outer():
    ChildError = X
    def inner(build_fn, genome):
        marker = "BACKOFF_FIXED"
        built = build_fn(genome)
        try:
            require_returned_condition_evidence(built)
        except ChildError:
            pass
        except X:
            raise
        return built
    return inner
```

`<module>.outer.inner → <module>.outer → <module>` を辿り、親の `ChildError` を local_names に追加。ChildError は NONE ではなく MAYBE、末尾 Pass により T:1802 で False。`outer` の代入を除き、`inner(..., ChildError=X)` とした引数版も T:1758 により同じ拒否となる。

**(c) as 名への再代入：**

```python
class ChildError(X): pass

def build(build_fn, genome):
    marker = "BACKOFF_FIXED"
    built = build_fn(genome)
    try:
        try:
            require_returned_condition_evidence(built)
        except X as exc:
            exc = ChildError("r")
            raise exc
    except ChildError:
        pass
    return built
```

内側 X は DEFINITE。handler body の束縛集合に `exc` が入り、T:1807 により bare=False。raise の値は Call でもないため変換分岐にも入らず、T:1821 で False。外側 ChildError を NONE として飛ばす経路へ到達しない。

いずれも記録される unswallowed=False が T:2324 の AND 条件を満たさず、当該 check は被覆に寄与しません。

## regressed の探索 (production 4 check、入れ子 scope、module scope)

production 原文と AST を独立に確認しました。関連5名と、対象関数の引数・束縛・module Assign/AnnAssign・ファイル全体の global/nonlocal 集合との交差はいずれも空でした。束縛確認には Name Store 以外の import、def/class 名、except 名等も含めています。

| check | 静的追跡 |
|---|---|
| s1:1218 | s1:1204 の try。1311 の WAL tuple は MAYBE bare、1314 の `_SortSwoOracleRejected` は NONE、1321 の DriverError は DEFINITE bare。外側1151は handler なし。1380の finally に脱出文なし。受理維持。 |
| s1:1295 | 1279の try で WAL=MAYBE bare → DriverError=DEFINITE bare。その後1204、1151へ進み、上記と同じ。受理維持。 |
| s8b_oracle_driver:1801 | 1730の try。1808の WAL=MAYBE bare、1811の S1DriverError=DEFINITE。OracleDriverError は module ClassDef が1件で再束縛なし。1812の変換で True。1660の外側 handler 追跡は停止する。 |
| n_pilot:1018 | 1017の try。1028の S1DriverError=DEFINITE。PilotError は module ClassDef が1件で再束縛なし。1029の変換で True。 |

s1 の経路は裸の `raise`、他2件は Call による変換なので、R3c の as 名再束縛検査による誤拒否もありません。

**入れ子 scope：** T:1494 の scope 登録、T:1613 の try stack 初期化、T:2318 の同一 scope の check 参照は維持されています。`<module>.outer.inner` は正常に扱える構造です。ただし、**受理集合が完全に不変という意味ではありません**。親の束縛を追加した結果、反例(b)は意図どおり受理から拒否へ変わります。

親に関連する例外名の束縛がない通常形は同じ経路を通ります。親で別名 import した例外なども「束縛あり」と保守的に扱うため、値として安全な形まで拒否する場合がありますが、これは R6:21 が指定する集合の結果です。入れ子関数の body 自体を親の束縛収集で誤走査することはありません（T:1279）。

**module scope：local_names は常に空集合にはなりません。** T:1751 でファイル全体の `global_nonlocal_names` を先に入れ、module の body だけを skip するからです。

例えば、別関数に `global PilotErr` があるだけでも、module check の `raise PilotErr(...)` は変換先から除外されます。修正前は module scope の local_names が空だったため、これは拒否側への変更です。ただし R6:21 の集合定義には一致し、受理を広げる退行ではありません。module に `.args` を参照することもありません。

## 新負例の単一理由性と変異予測の検算

| 例 | 現行の拒否理由 | その規則だけを外した場合 |
|---|---|---|
| n13 — T:3298 | 局所 X を MAYBE と分類し、MAYBE handler の変換を拒否 | M11で X が DEFINITE。PilotErr は再束縛なしの単一 ClassDefなので変換成功。**受理へ反転**。 |
| n14 — T:3265 | R2の TryStar 拒否 | これだけを外すと X=DEFINITE、末尾 bare raise、外側なし。**受理へ反転**。3.11以降が前提。 |
| n15 — T:3310 | PilotErr の module 再代入により変換不成立 | M12で変換成功し、外側 X の Pass を追跡する前に True。**受理へ反転**。 |
| n16 — T:3324 | 引数 ChildError=MAYBE、末尾 Pass | M11で ChildError=NONE。Pass を飛ばし、後続 X の bare raise を受理。**受理へ反転**。 |
| n17 — T:3336 | handler 内で再束縛した exc を bare と認めない | M13で bare 扱いとなり、外側 ChildError=NONE を飛ばす。**受理へ反転**。 |

したがって、**M11 の n13＋n16、M12 の n15、M13 の n17 という予測は静的に整合**します。n12 は M11 後も DEFINITE handler の末尾 Pass で拒否されるため、追加 killer にはなりません。完全赤集合の実測確定は未了です。

p8 は ChildError=NONE → X=DEFINITE bare で受理され、ChildError の ClassDef だけを除けば n7 同様に拒否されます。意味上の反転要因は一つです。

しかし、**実際の n7/p8 の source 差は ClassDef 一つではありません**。p8 は共通正例 fixture の T:3140 によって PilotErr と ChildError の両方を追加します。PilotErr はこの経路で参照されず交絡は確認できませんが、R6:26 の「ChildError を足しただけ」という厳密な契約には未達です。

n3 の過剰決定、n10 の TryStar＋Pass、n12 の再束縛規則への非専属性は残っています。追加例がそれを補う構成であり、既存例まで「各1理由になった」とは言えません。

## 変異 anchor と comment の検査

Fix の old/new 文字列を抽出し、対象ファイルの実 bytes と照合しました。**M0〜M13 の old はそれぞれ1箇所、各単独置換後の全文は AST 構文解析可能**でした。ファイル変更・テスト実行はしていません。

| 変異 | old の先頭 |
|---|---|
| M0 | T:2326 |
| M1 | s8b_oracle_n_pilot.py:1028 |
| M2 | T:1857 |
| M3 | T:1768 |
| M4 | T:1802 |
| M5 | T:1748 |
| M6 | T:1850 |
| M7 | T:1813 |
| M8 | T:1790 |
| M9 | T:1793 |
| M10 | T:1800 |
| M11 | T:1778 |
| M12 | T:1813 |
| M13 | T:1805 |

M7/M12 は同一 old を使いますが、別々の変異としては問題ありません。

- **M4：** `region_nodes` は同じ method 内の T:1730 で定義された入れ子関数です。置換先から参照でき、handler 内の If を降りて Raise を列挙できます。n4 は反転し、n5 は先行する T:1800 の脱出検査で拒否され続けます。
- **M8：** 二つ目の `return "none"` は ClassDef 条件の外側にあります。未知 ChildError は前段のどの条件にも当たらず、そこへ到達します。先行 return による到達不能コードではありません。
- **M2：** n8 は R0 で check 自体が記録されず不変。他の負例は bool 恒真化で反転する予測と整合します。3.10では14件、3.11以降では n10/n14 を含め16件です。

保証限界コメント T:2327 は、指定された次の項目をすべて含みます。

| 項目 | 記載 |
|---|---|
| helper の明示拒否に限定 | T:2327 |
| 再束縛検査の射程 | T:2329 |
| finalbody 内 check | T:2330 |
| 変換後の外側追跡停止 | T:2331 |
| MAYBE が E を捕まえ bare 再送出する未変換経路 | T:2332 |
| with、guard、結果名再束縛 | T:2333 |
| Python 3.10での TryStar 未実走 | T:2335 |

大項目の欠落や、一般的な例外伝播の証明を名乗る追記はありません。ただし「module, local and argument bindings」は要約です。実際の module 再代入収集は直下の単純 Assign／値付き AnnAssign に限られ（T:1567）、as 名は handler body の構文的束縛検査です。字句的親関数を含むことも明示すると、射程がより正確になります。

## must-fix と nit

**must-fix：0件。** 今回の裁定に反し、閉包検査の受理集合を広げる未修正箇所は示せませんでした。

1. **nit：p8 を厳密な一変更対にする。**
   新規 p8 専用の source 組立てで、n7 に ChildError の ClassDef だけを追加する。既存19例の source・期待値は変更しない。
   **DW-G05：放置しても現在の閉包検査の受理集合は変わらないが、「source が一変更だけ」という比較契約が成立しない。**

2. **nit／受入記録：実 spec の M2/M4 反映を確認する。**
   補正内容は R6 と Fix で正しい。実 spec が射影されていないため、反映完了の判定は保留する。
   **DW-G05：閉包検査の受理集合は不変だが、旧期待集合を使うと変異結果の帰属判定が MISMATCH になる。**

3. **nit：再束縛コメントを具体化する。**
   「module 直下の単純代入」「現関数と字句的親関数の束縛・引数」「as 名は handler body」を明記する。module scope でも global/nonlocal 集合を含む点は記録に残す。
   **DW-G05：コメント修正で受理集合は変わらない。現状の短い表現から検査範囲を過大解釈する余地を減らす。**

## 総括

R3a〜R3c はレビュー A の反例を拒否し、production 4 check は静的に受理を維持します。n13〜n17 の単独反転と M11〜M13 の予測、全変異 anchor の一意性・置換後の構文成立を確認しました。残る差は、p8 が厳密な一変更対ではないことと、実 spec への反映が未確認であることです。

今回 pytest・変異は実行していません。実走証拠は親の [s6-focus2.log](/home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-focus2.log) の **71 passed／2 skipped** のみです。Python 3.10での n10/n14 skip は依頼の説明とコードに整合し、TryStar・変異の実走成功や受入全走完了は主張しません。