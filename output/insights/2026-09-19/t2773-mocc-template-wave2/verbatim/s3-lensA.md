## 検査範囲

以下、`plan`＝`s2-plan.md`、`brief`＝`parent-brief.md`、`設計`＝`t2757-design-README.md`、`現物`＝e9e477ca の `cc/mocc/transaction.cc`。repo 内の行番号は HEAD `657e1e5a7` に対応する。

指定資料を読み、静的照合とメモリ上の DQ 対照を行った。ファイル変更・pytest・build・前処理・compute は実施していない。**must-fix は、計装新版への証拠移転を機械的に束縛する条件の不足、1 件。**

## 所見 1: 新計装の「本文保存」が機械 check に落ちていない

**real/refuted の判定材料：real。重要度：must-fix。**

plan:122 は「旧計装の検査本文は保存」と宣言するが、同:222–226、268–275、521–530、808–823 の検査には、新旧計装の検査本文・配置の対応を要求する具体的条件がない。

例えば、新計装の X 条件を `if (false && …)`、P の emit 条件を `if (false && !izanagi_perm_ok)` にする変更は、次を通り得る。

- 比較(i)/(ii)は計装なしなので影響しない。
- 比較(iii)では変更部分が TRACE=0 で消える。
- stock 12 走は、検査が正常でも無効でも X=P=0 になる。
- X/P の DQ 対照は「その位置の編集を拒否する」検査であり、元の検査が働くことを確認しない。
- 新 patch の実 SHA を新 JSON に記録しても、旧計装との意味の対応は証明しない。

旧検査の実体は `instr-mocc-lock-coverage.patch:20–44,53–69,79–82,93–96,106–111`。既存 `test_mocc_proof_surface.py:256` 以降の構造検査も、同:427 では旧 patch 適用 source に対して呼ばれる。新版への適用は plan に明示されていない。

これは実装済みの欠陥という判定ではなく、**plan の受入条件の不足**。D2134 項3の経路共通証拠を再利用するには、新版が旧検査を保存したという橋が要る。n=1 の目視で補っても、機械 `all_pass` の根拠には合算できない（D2134 項5）。

**是正案（逐語）：**

> 計装 template 版は、旧計装の各検査本文・TRACE guard・検査対象操作との前後関係を保存する。旧 patch と新 patch の対応を機械照合し、許す差を template による位置移動、diff context、および別検査で検証する `#line` 復元値に限定する。この照合を機械 check に含める。X 条件の恒偽化、P emit の無効化、検査点の対象操作後への移動を、それぞれ SHA 不一致だけに頼らず拒否する対照を置く。broken 4 patch の template 上での再走は追加しない。

## 所見 2: DQ は純粋式も「一式だけ」も保証しない

**real/refuted の判定材料：素通りは real。「plan が DQ pass を安全性証明としている」は refuted。重要度：should。**

`diff_quarantine.py:477–526` が調べるのは挿入 anchor と禁止 byte。呼出し、代入、lambda、複数文、再帰は解釈しない。

plan の逐語 helper をメモリ上で組み込み、実 `DiffQuarantine.validate()` に与えたところ、以下はすべて **DQ pass** だった。C++ の compile 成功や auditor の見逃しを実測したものではない。

| hole の例 | 契約違反 |
|---|---|
| `return (FLAGS_clocks_per_us == 2100) && (temp >= threshold);` | 外部 flag 読取・環境依存判定 |
| `return (FLAGS_temp_threshold = 0, temp >= threshold);` | global 書込み |
| `return (TotalThreadNum == 1) && (temp >= threshold);` | 禁止 tuple にない global 読取 |
| `return (printf("x"), temp >= threshold);` | 呼出し・外部副作用 |
| `return ([&] { static unsigned n = 0; return (++n & 1) && temp >= threshold; })();` | 状態保持・副作用・同じ入力の分類変化 |
| `return TRACE ? (temp >= threshold) : false;` | 生 directive を使わない verify/perf 判別 |
| `return mocc_is_hot(temp, threshold);` | 再帰・非停止 |
| `FLAGS_temp_threshold = 0; return temp >= threshold;` | 一物理行の複数文 |

同じ byte 規則では `getenv`、`rand()`、`rdtscp()` 等の呼出しも拒否されない。`util.hh:5,30,32` はその関連宣言を取り込む。

一方、`thid_`・`result_`・CLL/RLL/read/write set は `transaction.hh:31–52` のインスタンス member。file-scope helper から裸で参照して現在の executor を取得できる、とは言えない。その形は compile error になり得る。ポインタや関数経由で触れるにはアクセス経路の提示が必要であり、**現在の executor への具体的経路は未確認**。

plan:409 と型16追記案（同:561）は、禁止 tuple を完全な機械フィルタと扱わず、値渡し二引数と定数による比較・論理結合に限定している。この文章契約は上記を禁止する。ただし auditor の完全検出は保証しない（設計:287–288,306–307）。

**是正案（逐語）：**

> `SYNTAX_CONTRACT_FORBIDDEN` は禁止例の列挙であり、完全な識別子 blacklist ではない。DQ pass は物理行の封じ込めを示すだけで、一式性・純粋性・停止性・読取契約の充足を示さない。列挙にない global、lambda/static、再帰、組込関数、通常式中の TRACE 参照も、許可された比較・論理結合の集合から外れるものとして監査する。

## 所見 3: P3 の型・brace・fallback に反例はない

**real/refuted の判定材料：refuted。重要度：must-fix 候補を棄却。**

- `tuple.hh:38` の温度は unsigned 32-bit bit-field、`common.hh:40,67` の閾値は uint64。元の比較でも閾値との通常算術変換により温度値は保存される。`std::uint64_t` 二引数への値渡しは温度を狭めず、閾値も切り詰めない。
- 整数比較なので `temp >= threshold` と `!(temp < threshold)` は同値。符号付き化や浮動小数点 NaN の問題はない（plan:35,52,198–200）。
- 296 は両前処理枝が `} else if (...) {` を持つため、選択後の brace 対応は保存される（plan:66–76、現物:280–314）。
- 970 の `|| (*itr).failed_verification_` は両枝にある（plan:90–95、現物:970）。
- OFF で helper 宣言全体が消える外側 guard がある（plan:33–46）。

ただし、これは比較意味と構造の静的確認。OFF の実 resolver 一致や build 成功を確認済みとはしない。

**是正案（逐語）：**

> P3 の二引数は `std::uint64_t` とし、温度・閾値の値を保存する。四 callsite と970の fallback は逐語案どおり固定する。静的な意味保存と、後続で取得する OFF resolver 同一性・実 build の結果は分けて記録する。

## 所見 4: 三比較の分離と復元値は妥当

**real/refuted の判定材料：refuted。重要度：must-fix 候補を棄却。**

メモリ上で plan:28–46 を数えると helper は19行、四 site の純増は各4行、合計35行。復元値は次の算術と一致する。

`17+19=36`、以後は `990/991/1158/1169/1187/1195 +35`
＝ `1025/1026/1193/1204/1222/1230`。

各比較の意味も分離されている（plan:180–228）。

| 比較 | 主張できること | 主張できないこと |
|---|---|---|
| 無 template ↔ OFF | resolver の正規化 source identity が stock | 実 TU 全体・binary の完全同一 |
| OFF ↔ ON-B | source digest が異なり ON が別 identity | 意味が異なること、性能改善 |
| 同一状態の計装なし ↔ あり | TRACE=0 の論理行・非空本文列が一致 | TRACE=1 の検査有効性 |

`source_digest.py:1665` の正規化は include を除去する。したがって「前処理本文一致」はこの resolver の正規化範囲として読む必要がある。

plan:226 の正数行数・count・SHA・実比較 bool と、`s3_mocc_mutation_proof.py:276–317` の実装を使えば、各復元点の後続非空行に伝播する ±1 は検出される。template の行数を誤算しても、**基準側を実 template source から独立に前処理する限り**同様。D1687 を CC-native 骨格の承認に流用する記述は認めなかった。

**是正案（逐語）：**

> 比較(i)の保証名は「実 resolver が定める正規化前処理 source identity の stock 一致」とする。比較(iii)の基準列は実 template 適用 source から独立に取得し、計装側の復元番号表から生成しない。比較(iii)は TRACE=1 検査本文の有効性を保証しない。

## 所見 5: P1 は妥当だが、新 template 上の hot 発火証拠ではない

**real/refuted の判定材料：再走不足を理由とする棄却は refuted。保証範囲の注意は real。重要度：should。**

D2134 項3は broken 4 本を経路共通証拠に分類している。したがって template 版を新設して再走しない P1 は整合する。plan:837 も、新 template 上で hot 負例を再観測したとは書かないとしている。

wave 2 の hot-U 正数 commit と閾値0は、現物:454–477 の制御フローから459到達を推論する材料になる。しかし X=P=0 自体は459での早期 lock と993での後段 lock を区別しない。D2134 項4が定めた「負例発火による実行証拠」は wave 1 のもの（wave1 README:72–75）。

**是正案（逐語）：**

> wave 2 の12走は template ON-B の正常系対照であり、template 上で hot-update 負例が発火したことを主張しない。hot 専用負例の到達・X三検査点の検出は wave 1 の固定 producer に束縛された経路共通証拠として参照する。四 site 全動的被覆、read-hot、RLL 再試行、DELETE 被覆は主張しない。

所見1の計装保存条件を満たせば、この限定で P1 を採用できる。

## 所見 6: timeout・空走・別 integrity を緑にする方針ではない

**real/refuted の判定材料：refuted。重要度：should（実装時の確認条件）。**

plan:253 は新12走用の完走検査、同:275 は全走の certified・cycles=0・X=P=0・他 integrity clean・txn/write正数を要求する。これは恒真条件ではない。

再利用元の `_silent` は `certified is True`、`verdict == "serializable"`、各ゼロ、正数の txn/write、他 integrity を要求する（`s3_mocc_mutation_proof.py:341–362`）。**ただし `_silent` 単独には timeout/終了状態の確認がない。** それは同:385–415 の matrix 完走検査が担うため、新版にも両方が必要。

wave 1 の4-thread負例に許された integrity 異常を、wave 2 の stock 対照へ移す理由はない（wave1 README:92–95、plan:275）。

**是正案（逐語）：**

> 全12走について `_silent` 相当の内容検査と、benchmark/verifier の終了状態検査をともに必須とする。timeout、異常 rc、verifier record 欠落、txn/writeゼロ、別 integrity 異常は all_pass=False とする。wave 1 の観測専用負例に対する免除は継承しない。

## 所見 7: P8 の隔離方針は妥当だが、実効 define を射影に明記する

**real/refuted の判定材料：誘導・deny-only逆転は refuted。実効 macro context の列挙不足は real。重要度：should。**

plan:756–802 は期待 verdict・fitness・親推論を除き、A1′をDQで除外せず直接見せ、未実走候補を `not_run` とする。A1′の diff に旧負例の告白コメントはない。A2′・B′も設計:281–288 と一致する。

deny-only 対照も正しい。`auditor_gate.py:205–221` は machine reject をそのまま返し、machine pass の場合だけ digest と auditor 内容を検査する。plan:365–372 はこの順序に対応している。

ただし入力一覧（plan:762–767）には実効 define が明記されていない。template は既定OFFなので、source SHA と diff だけでは当該 run で ON 枝が有効だったことまでは伝わらない。また「性能値を除いた射影」の具体的 field は未確定。

**是正案（逐語）：**

> auditor 射影には候補ごとの base/source/diff digest に加え、`MOCC_TEMP_PREDICATE`、`TRACE`、`RWLOCK` 等の実効 macro context を含める。verify 結果は許可 field を選んで新規生成し、raw run record、wall_seconds、throughput、fitness、WAL、期待 verdict を渡さない。B′へ実走結果を帰属させる前に、baseへB′を適用した source と実走 source、および macro context の一致を確認する。

Read/Grep/Glob は完全な path 隔離ではない点も維持すべきである（D38 決定3、現行 auditor:28）。

## 所見 8: auditor 追記の行番号・既存 Silo 保持は整合する

**real/refuted の判定材料：refuted。重要度：must-fix 候補を棄却。**

plan:545 は既存 Silo 説明を残すと明記しており、追記案も protocol を限定する。

- CLL三条件＋counter は旧計装:57–64 と一致。
- tidword 比較1010–1013、counter/searchWriteSet判定1024–1036は現物と一致。
- write_set 登録477、RLLへの write-set登録905–913も一致。
- hot read の absent 非検査を明示する案（plan:553）は現物:341–364と整合。
- P は sort 前後の size/multiset に限定されている（plan:557、D1686）。
- I absent は維持する（plan:752、`test_mocc_proof_surface.py:410–427`）。

**是正案（逐語）：**

> mocc の追記は既存 Silo 説明を保持した protocol 限定の追加とする。P を CLL/RLL 全体の保証に拡張せず、hot read の absent 非検査と I absent/write-intent 未実証を維持する。

## 所見 9: P5/P6 の限定は妥当。ただし plan の親引用に誤りがある

**real/refuted の判定材料：P5/P6 の限定は妥当。引用誤りは real。重要度：should／nit。**

P5 の literal という書き方自体を拒否する理解は不適切。plan:448–454 は正しい値の literal を同じ束縛検査へ通し、別OIDを拒否すると訂正している。D2134 項6と整合する。ただし実 consumer は未導入であり、今回の対照から任意の consumer 経路が閉じたとは言えない。

P6 の二鍵（plan:480–519）は EBS 所属を使わず、D2134 項6に沿う。新 JSON の存在・再導出・束縛を要求するが、任意の新 patch の実使用を自動追跡する仕組みではない。

また、plan:829 の「P4の『七hunk』は訂正」は提示 brief に存在しない引用。brief:50 は `#line` 再生成だけを述べる。六hunk・七復元点という計数自体は正しい。

**是正案（逐語）：**

> P5 の今回の成果は束縛APIと対照であり、将来 consumer の実 checkout/source との接続実証ではない。consumer 導入時に実使用 source/template/PIN の束縛を必須検査する。
> 旧計装 patch は六hunk・七復元点である。提示された親 brief の P4 に hunk 数の誤記はない。

## 総括

**(a) must-fix 一覧**

- **1件：新計装の本文・guard・検査位置が旧計装を保存することを機械 check にする。** TRACE=0 同一性、正常系の沈黙、新 SHA 束縛だけでは、無効化された X/P を排除できない。broken 4 本の再走追加は不要（所見1、D2134 項3）。

**(b) P1／P3／P8 の当否**

- **P1：条件付き妥当。** 所見1を補い、新 template 上の hot 負例発火を主張しない。
- **P3：静的には妥当。** 型、296のbrace、970のfallback、OFF helper消失は整合。実 resolver/build は未確認。
- **P8：方針は妥当。** A1′直接提示、告白コメント排除、期待値隔離は成立。実効 define とverify射影 fieldを明記する。

**(c) DQ／auditor の素通り形**

DQ は、flag/global 読取・代入、comma式の副作用、関数/時刻/乱数呼出し、lambda/static状態、再帰、通常式中のTRACE判別、一行複数文を通し得る。主要9形と benign はメモリ上の実DQで pass を確認した。型16の許可集合はこれらを禁止するが、**auditor が実際に見逃すかは未実測・不確実**。DQ pass と auditor pass のどちらも安全性証明ではない（設計:287–288,306–307）。

**(d) 親 brief への異議**

brief:47 の正常系12走と同:50の行番号再生成だけでは、新計装への経路共通証拠の移転が未完。P5の literal-PIN 拒否は表記ではなく値・実sourceとの不一致として限定する。P6は登録を検出する gate であり全 consumer 経路の閉鎖ではない。P8には実効 macro context を追加する。一方、P3の意味保存を否定する根拠と、提示 brief に「七hunk」の誤記があるという根拠は認めなかった。