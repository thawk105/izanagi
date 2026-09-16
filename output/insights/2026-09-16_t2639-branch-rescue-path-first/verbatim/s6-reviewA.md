## 読んだ資料

指定の5資料はすべて読めました。`stage5.patch` は739行を確認しました。加えて、許可された実装2ファイルと対応テストの関連箇所を読みました。

以下の略記は、それぞれのファイルと行番号を指します。

- **L**：`tools/check_branch_landed.py`
- **R**：`tools/check_branch_rescue.py`
- **TL**：`orchestrator/tests/test_check_branch_landed.py`
- **TR**：`orchestrator/tests/test_check_branch_rescue.py`
- **A**：指定の `stage4-adjudication.md`

**静的レビューのみです。変更・テスト実走・Git状態の変更はしていません。** I1〜I7はA:67で射影外のbriefを参照しているため、その全文を確認したとは扱いません。`docs/failures.md` 本文も射影外なので、指定された5つの型タグを検査観点として用いました。

## 偽の landed を作れる経路 (real)

**今回の差分が新設する偽の landed 経路は、確認できませんでした。**

ただし、次の問題は **real** です。いずれも偽の landed が成立するという所見ではありません。

- **[捏造/幻覚] 証拠理由の誤表示。** registry解析不能でも `_receipt_match` が空の索引から `folded-receipt-absent` を返し、証拠層へ流れます。unit decisionはregistryの理由を保持します。根拠：L:1012、L:1323、L:1408、L:1444。
- **[テスト代表性] 変異登録の期待結果と実装経路の不一致。** 特にN05は、通常判定へ置換するだけでは `not-landed` になりません。詳細は変異節。
- **[ドリフト] 上限超過時の正例優先は残っています。** L:795で受理してからL:800で上限を検査します。ただし同一commitの四要素一致は存在し、今回導入した無証拠の受理ではありません。A:25、A:74どおり、本wave内で変更する提案はしません。

## 作れないと確認した経路 (refuted)

**1. batch応答だけで偽の一致を受理する経路：refuted。**

L:744で行数と終端LF、L:754で4要素、L:757でOID・型・サイズ形式・連番を検査し、chunk全行の検査完了後に返します。さらにL:794で**入力候補の同じcommit**を読み直し、L:704の四要素比較を通します。

- `missing` は式全体との一致だけを認め、結果は `None`。positiveにはなりません（L:750）。
- `ambiguous`・`dangling`・`notdir` はmissing扱いされず、通常のエラー形なら行数または4要素・フィールド検査で拒否されます。
- `%(rest)` によって入力のタグが分離され、missing応答が `<expr> missing` になるという想定と実装は整合します。ただし**Git実装・実応答は今回独立確認していません**。実Gitを使うTL:1730のfixtureは削除commitのmissing応答を通る構成です。仮にGitがタグ付きmissingを返すなら、結果はparse errorであり偽のpositiveではありません。
- blob OIDとcommit OIDの長さ比較は、同一repositoryのハッシュ形式が同じという整合性検査です。内容一致の証明にはならず、その証明はL:792、L:795が担います。
- タグはchunkごとの `enumerate` で生成・検査されます。呼出側もchunk局所のindexなので取り違えはありません（L:738、L:747、L:788）。
- `split` の要素数違いとASCII decode失敗は捕捉済み。行数一致と`zip`により、この処理で`candidates[index]`が範囲外になる経路はありません。サイズを整数変換しないため、その`ValueError`もありません。
- history出力のASCII decode例外は局所では漏れますが、assessment外周で `indeterminate` になります（L:779、L:1985）。

**2. `batch_safe` が証拠条件を弱める経路：refuted。**

4条件は候補の絞り込み方法を選ぶだけで、最終四要素比較を省略しません（L:783、L:794）。

Pythonの`isspace()`はASCIIの空白類に加えUnicode空白も除外するので、Gitとの非一致は保守的な退避を増やす方向です。空白・改行のないpathだけがbatchへ入り、非ASCIIの通常文字は入力側に残り、成功応答の`rest`は数字タグだけになります。

削除・tree・gitlink・symlinkは`metadata=None`となり、従来の`ls-tree`経路へ進みます。symlinkはblobですがmode `120000`で退避します。根拠：L:600、L:783、L:790。対応する分岐テストはTL:485です。

**3. S2の未着地pure-addを `not-landed` にする経路：refuted。**

`_spool_exact_positive_decision` の引数は `search` と `receipt_reason` だけで、`state`はありません。戻り値は`landed`か`indeterminate`だけです（L:1331）。

spoolにはany-path探索も通常判定も適用されません（L:1381、L:1448）。receipt不在・候補0ならL:1338から`indeterminate`になり、probe一致も集約を変更しません（L:1594）。削除spoolもfallback対象外です（L:1419）。

**4. S2がtimeoutを握り潰して landed にする経路：refuted。**

例外伝播の形は変わりますが、timeoutは`truncated`のSearchResultとなり、`search.incomplete=True`、unitの`indeterminate`、`integrity_incomplete=True`へ進みます（L:145、L:1423、L:1336、L:1480）。

戻り値の `_unit_incomplete` 自体は呼出側で使われませんが、unit verdictが残り、集約のL:1598がlandedを阻止します。全体deadlineも切れていれば、最後のref再確認などで外周の`indeterminate`へ進みます（L:1938、L:1985）。

**5. decisiveの組合せ：偽のlandedはrefuted、表示の紛らわしさはreal。**

| 状態 | exact decisive | receipt decisive |
|---|---:|---:|
| spool：exact一致 | true | false |
| spool：exact探索不完全 | true | false |
| spool：exact不一致 | false | true |
| spool：receipt一致、解析失敗、fallback対象外 | false | true |
| 非spool | true | true |

両方falseになる経路はありません。非spoolではreceiptが`not-applicable`でも両方trueです（L:1451、L:1463）。さらに負例にはclosed-world層も追加されます（L:1744）。

S4はこれらをそのまま抽出するため、「trueの層はすべて実際に判定を決めた」と読むと誤解します（R:1540）。ただし`outcome=not-applicable`も運ばれます。A:11の方針に反し、「常に一層」という一般条件を追加すべきではありません。

**6. S4から判定への逆流：refuted。**

S4は既存payloadを書き換えず、追加dictを生成します。assessmentの`complete`は従来どおり`expected_conclusive`です（R:1610、R:1627）。

後段はassessment直下の`complete`と`verdict`を使用し、details内の`complete`を読みません（R:2067、R:2113、R:2137）。削除許可への転用もなく、**[権限逸脱]はrefuted**です（R:1613）。

## 恒真・恒偽の検査

**S4の`complete`が恒真・恒偽という疑い：refuted。**

- **真になる実出力経路：** 全stateを列挙してsummaryへ件数を書き、全unitを出力した場合です（L:1711、L:1712、L:1811）。未証明が3件あっても、説明が揃い上限以内ならdetailsの`complete=True`です。親の報告と矛盾しません。
- **偽になる実出力経路：** state列挙後、最初のunit処理が例外で中断すると、summaryは正の件数、`proof_units`は初期値の空配列のままです（L:377、L:1721、L:1985）。R:1552の件数比較が偽になります。
- 子JSONを取得できなければ初期値false（R:1498、R:1510）。説明対象が101件なら`truncated=True`によりfalseです（R:1550）。

これは「説明が揃ったか」の値です。assessment全体の判定完了とは別で、TR:1651とTR:1665も両者を区別しています。

## 変異 N01〜N09 の単一理由性

具体的な変異patch・実行結果は射影にありません。以下は登録文とコードからの静的判定であり、KILLEDの申告ではありません。

| 変異 | 判定と根拠 |
|---|---|
| **N01** | **real：変更位置を特定する必要あり。** 旧M1のL:1328だけ変えても、通常spoolではL:1425に上書きされます。L:1338の最終fallbackを変えるなら、候補0の負例で単一理由になり得ます。旧位置のままなら登録から外し、再照準してください。 |
| **N02** | **refuted：modeだけの負例に別の阻止層は見当たりません。** OID/typeは通り、L:795のmode比較が最後の阻止点です。TL:1791がその差だけを注入します。type/oidのcaseまで単一理由と一般化してはいけません。 |
| **N03** | **real：偽のlanded防止の説明は成立しません。** 誤ったcommitへの対応付けはL:794で再確認されます。一方、現fixtureは両行に同じblobを注入し、本物のwitnessも残しています（TL:1749、patch:238）。タグ検査を外すと、最初のcommitを拒否して本物のwitnessでlandedになり得ます。これはprotocol違反拒否の単一理由テストとしては成立し得ますが、偽の着地検出ではありません。 |
| **N04** | **real：登録が複数の異なる経路をまとめています。** batch異常を単に全候補`None`へ丸めても、候補数が残ればL:1360で依然`indeterminate`です。spoolなら候補0に丸めてもL:1338が阻止します。「indeterminateでなくなる」の期待は一般には成立しません。対象の変更点と期待理由を限定できない登録は外してください。 |
| **N05** | **real：期待したnot-landedへ到達しません。** 引数を正しく付け替えても、spoolの`any_path`はNoneなので通常判定L:1352が`indeterminate`を返します。単純置換なら引数不整合にもなります。またTL:1809の禁止stubで赤くなることは、登録した負例機序の証明ではありません。現登録は外すべきです。 |
| **N06** | **refuted：上書き前のerror decisionは独立した阻止層ではありません。** L:1418のregistry-error除外を外すと、L:1425が先のdecisionとincompleteを上書きし、実在witnessでlandedになり得ます。これは単一理由を構成できます。ただし現状のreceiptテストはbaselineから赤なので、そのまま変異検出の証拠にできません。 |
| **N07** | **refuted：colon正例には事前の空白退避がありません。** 正しい式ならwitnessを証明でき、colonで壊した式は証明できません（L:737、TL:1730）。具体的なsplit方法は未提示なので、期待nodeの一致は未確認です。 |
| **N08** | **refuted：説明出力の検査として別の判定gateはありません。** 説明を削除するとTR:1655の具体値比較が失敗します。verdict検査は引き続き通る構成で、S4契約の変異として分離されています。 |
| **N09** | **refuted：子出力なしのdetailsに限れば単一理由です。** `None`はR:1510で早期returnし、後段の列挙検査を通りません。そこで`complete=True`とする変異はTR:1728で検出できます。assessment直下のfalseは、details内の誤表示を訂正しません。 |

**N03の補足：** 中間報告で述べた「別検査でも阻止」は、誤ったcommitの証拠採用についてです。現fixture全体が再確認で必ず拒否される、という意味ではありません。

A:109の逐語どおり、少なくともN01・N04は変更点の確定、N05は登録の除外・再照準が必要です。N02のtype/oid版など、別gateが同時に拒否するcaseを単一理由の実績に数えるべきではありません。

## 親の実測への反論

**数値自体への反論：なし。ただし独立検証はしていません。**

同じverdict・理由内訳とprocess削減は、この差分の構造と整合します。ただし2つの固定OIDでの一致から、全入力の受理集合不変までは言えません。S2は意図的に、receipt不在でもexact証拠のあるspoolを受理するよう拡張しています（L:1418）。

**report_sha256の説明：realな訂正点。**

S4追加だけでは変わりません。ハッシュ対象は追加説明を含むrescue出力ではなく、**子checkerの生stdout**です（R:1625）。実装報告`stage5-author.md:94`は、この区別が不正確です。S1/S2や証拠理由修正、計測値によって子stdoutが変われば、ハッシュは変わります。

**receipt赤1件への親裁定：支持します。ただし修正範囲を限定してください。**

- **判定変更の疑い：refuted。** L:1408の照合後、registryがerrorの場合だけ証拠用`receipt_reason`をregistryの理由へ戻すなら、verdict・rc・受理集合は変わりません。unit decisionは既にL:1323でregistryの理由を選び、fallbackはL:1418で禁止されています。
- **正常なreceipt不在を壊す疑い：refuted。** errorの場合だけの修正なら、L:1014の本当の不在とTL:1851の期待値を保持します。
- **注意：** fragment解析失敗等を扱うL:1403まで無条件にregistry理由で上書きする案は別です。今回の根拠は、正常にfragmentを解析した後のregistry-error表示に限定できます。
- **期待値を現挙動へ合わせる案：採りません。** `absent`への厳密比較に変更してもverdict検査自体は弱まりませんが、解析不能と不在を区別する説明契約は弱まります。単に該当assertを削るなら検査範囲も狭まります。S4が証拠理由を人へ運ぶ以上、A:53のscope内で誤表示を直すほうが適切です。

親の「209緑／1赤」という結果を、こちらが実走確認したとは扱いません。指摘された赤の原因は静的に確認できました。

## 総括

**新たな偽の landed 経路は確認できません。** 一方、現状を検証完了とは扱えません。receipt証拠理由の修正と、N01・N04・N05の登録再整理が必要です。

受理については、正常な通常blobのspoolがmain履歴の同じcommitで四要素一致すれば、receipt不在でもlandedを返せます。  
拒否については、receipt不在だけ・探索不完全・解析不能からlandedを作る経路はなく、未証明として残ります。

通る正例はTL:1805です。mainに同じfragmentを置いた後に削除しても、その履歴上のwitnessを証明してlandedになります。これは静的に確認したテスト構成であり、実走の緑を申告するものではありません。