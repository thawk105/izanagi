静的検査の結果です。以下の trace は、別記がなければ X/P 証拠と正しい commit witness を与える前提です。実行・変異実測はしていません。

### A1 — must-fix：P1 は初期存在を検査せず、認定に都合のよい初期状態を選んでいる

根拠：`s2-plan.md:11,253`、設計 `README.md:83`、`orchestrator/verifier/dsg.py:659–664`。

次は P1〜P3 をすべて通過します。

```text
C 0 0 2 1 1 0 0 0 1
R 0 9 aa 1 0
E 0
```

しかし、初期集合に `(9,aa)` が無ければ、存在しない値を読んだ履歴です。write が無いため、P1 はこれを初期存在と決めます。反対向きもあります。

```text
C 0 0 2 1 0 1 0 0 1
W 0 5 aa I 2 1
E 0
```

初期集合に `(5,aa)` が既にあれば成功した INSERT と整合しませんが、P1 は初期不存在と決めます。最初の U/D についても、不存在の初期状態を排除できません。

これは「必ず非直列化可能」という反例ではなく、**実際の初期集合に対する妥当性が入力から決まらないのに certified にする反例**です。設計の「初期に無く、最初が INSERT」という条件を、plan は「最初が INSERT なら初期に無い」へ逆転しています。

修正案：P1 を初期集合の検査完了条件として扱わないこと。段1の認定に必要な初期存在を何の既存証拠から確定できるかを、印の撤去前に示す必要があります。指定入力だけで確定できない場合、文書に「推定」と書くだけでは依頼の「判定できない場合は認定しない」を満たしません。初期一覧の新設を本 wave に無断で広げることも避けるべきです。

**放置した影響：初期集合と矛盾する trace が、新たに certified の集合へ入ります。**

### A2 — should：不存在・abort・自己読みの説明を、native set の実装に合わせる必要がある

根拠：`external/ccbench/cc/silo/transaction.cc:195–277,27–40,602–616`、同 `include/tuple.hh:24,40–53`、`s2-plan.md:41`。

指定された silo 実装では、次のようになります。

- 木に key が無い読みは `transaction.cc:230` で戻り、read set に入りません。
- `absent` の record も `:260` で戻ります。R の材料が増えるのは `:277` です。
- 自分の insert を読む場合は write set から `:216–219` で返り、追加の R は生じません。
- 未 commit insert は `tuple.hh:50–53` で `lock=true, absent=true`。他取引は `transaction.cc:255` で待ちます。commit 後に正常に読み取れれば、`:663–665` で設定された committed version が R に載ります。
- abort は挿入 record を除去・解放します。**abort 後に待機中 reader がどう安全に終了するかまでは、この読解から保証できません。** 少なくとも「abort 版の R が必ず出る」とはいえません。

新規 tuple の版は初期化時には `(0,0)` です。仮に壊れた読み経路がその版を記録したなら、次は既存 orphan で落ちます。

```text
C 0 0 2 1 1 0 0 0 1
R 0 5 aa 0 0
E 0
```

一方、誤って `(1,0)` と記録されれば A1 の穴になります。これは正常 silo の挙動ではなく、版の誤記録を仮定した例です。

また、指定ソースの emitter 自体は `:602–616` の **v2** です。native set の挙動は確認できますが、親が測った v3 build と同一の emitter であるとは確認できません。

修正案：自己版 I/U の fixture は「合成形式として採用する意味」の試験と明記し、実 emitter の正例と区別すること。実 v3 emitter の対応確認は親の証拠に帰属させてください。

**放置した影響：認定集合そのものより、abort・自己読みを検証済みとする主張が実装の証拠を超えます。**

### A3 — should：P3 は必要だが、通常の DSG cycle 検査とは別の保証である

根拠：`s2-plan.md:13–21`、`orchestrator/verifier/dsg.py:674–681`、`external/ccbench/cc/silo/transaction.cc:75–81,185–188`。

P3 を省くと、次が P2 と既存 integrity を通ります。

```text
C 0 0 2 1 0 1 0 0 1
W 0 5 aa D 2 1
E 0
C 1 0 2 2 0 1 0 0 1
W 1 5 aa U 2 2
E 1
```

DSG は `0→1` の ww 一本だけです。しかし D が不存在を作り、U が既存行の更新を意味するなら、成功した操作列として成立しません。`I→I` も同様です。P3 は cycle を増やすためではなく、**直列順へ並べても操作の前提条件が成立しない履歴を除くため**に必要です。

正しい初期状態、key ごとの正しい版順、一取引一最終版という前提では、P3 が正常履歴を落とす反例は見つかりませんでした。ただし、それらの前提まで P3 自身が証明するわけではありません。

修正案：P3 は今回の存在意味の範囲として維持し、P1 の正当性の代用にしないこと。

**放置した影響：P3 を省くと、cycle は無いが成功操作として成立しない trace を certified にします。**

### A4 — should：段2では、存在推定だけでなく「再挿入後も版順が単調」という前提が破れる

根拠：`external/ccbench/cc/silo/transaction.cc:157,191,567–579,682–686`、`s2-plan.md:11,173`、設計 `README.md:137–142`。

DELETE は木から record を除去します。再 INSERT は新規 tuple を作り、旧 DELETE の版を commit 計算へ引き継ぎません。別 worker による同 epoch の再挿入では、版が逆転し得ます。以下はその **native API からの静的な推論例**です。

```text
C 0 0 2 99 1 0 0 0 1
R 0 5 aa 1 0
E 0
C 1 0 2 100 0 1 0 0 4
W 1 5 aa D 2 100
E 1
C 2 1 2 1 0 1 0 0 1
W 2 5 aa I 2 1
E 2
```

実行順が「初期行を読む→削除→再挿入」なら合法ですが、plan は版順の最初を I とし、初期 genesis 読みを拒否します。ww の順序も実際の存在遷移と逆になります。版が一致すれば既存 `version_dups` で拒否されます。

ただし、**通常の TPC-C が削除済みの同じ NewOrder key を再利用するとは確認していません**。この例を段1の実 trace が不正である証拠には使えません。

段2に直接関係する別の欠落は、Delivery の空 scan です。`tpcc_tx_delivery.hh:45–50` は結果が空でも処理を続けます。見えなかった初期 key は R/W だけでは列挙できず、P1〜P3 は取りこぼしを検出しません。これは設計 §4.3 の初期一覧・述語読みの担当です。

修正案：段1の違反0件を、Delivery・scan・再挿入の検証へ一般化しないこと。段2対応は今回へ追加せず、段1の認定根拠と切り分けてください。

**放置した影響：段2へ流用すると、初期行の取りこぼしを見逃し、再挿入を含む合法履歴を拒否する可能性があります。**

### A5 — should：cycle より存在違反を優先する変更は、印の撤去に必要ない

根拠：`s2-plan.md:43,180,225,247`、`orchestrator/verifier/model.py:551–560`、単位4記録 `README.md:19–20`。

plan は、既存 cycle fixture に独立した delete 版読みを追加すると、従来の `non-serializable` を `indeterminate` へ変えます。しかし `certified` は既に `serializable and clean()` なので、存在件数を `clean()` に入れるだけで認定は拒否できます。

依頼逐語には cycle 優先を変更する明示指示がなく、単位4記録は cycle を従来どおり返すとしています。brief の負例期待を理由に、一般の verdict 優先順位まで変更する必要はありません。

修正案：cycle 優先を維持し、存在違反単独なら indeterminate、cycle 併存なら non-serializable と存在詳細を両方返す。対応する優先順位変異は今回の検出力から外すことを推奨します。

**放置した影響：certified 集合は変わりませんが、既存の異常分類と旧 JSON の verdict が変わります。**

### A6 — should：経路設計は妥当だが、schema 判定と診断比較の具体化が必要

根拠：`orchestrator/verifier/core.py:39–50`、`parse.py:624–663,807–846,898–899`、`dsg.py:345,610–625`、`test_verifier.py:3417–3447`。

共通検査を builder の外側へ置く案について、packed・tuple・fallback 間で必ず結果がずれる欠陥は見つかりませんでした。次を実装条件として固定してください。

- compact の schema 判定は、先頭 file だけを見ない。既存 core と同じく neutral file を許容すること。
- key の表は `write_key_id/read_key_id` の token から取り、op token の `token_table=-1` を使わないこと。
- winner 行だけを検査すること。全 occurrence を使うと legacy と存在件数がずれます。
- worker fallback の中では検査しないこと。提案どおり `from_compact` の後処理なら二重計上を避けられます。

例えば、同じ txid の先行 frame が I、最後の frame が U で、その key に genesis 読みがある入力では、全 occurrence を使う誤実装だけが存在違反を増やします。ただし dup_txid により両経路とも非認定なので、verdict 比較だけでは見逃します。

v2 の wire bytes は `report.py:96–136` の明示的射影を維持すれば保てます。field 初期化と schema 分岐の費用まで含めた時間の完全一致は保証できず、plan の留保は適切です。

**放置した影響：主に非認定 trace の存在件数・詳細が経路でずれ、比較が verdict だけなら検出されません。**

### A7 — should：変異の帰属は概ね良いが、重複・orphan・cycle 試験を検出力へ混ぜないこと

根拠：`s2-plan.md:169–180,199,216–225`、`orchestrator/verifier/model.py:498–506`、`parse.py:426–427`。

登録された主要変異について、**記載どおりの fixture と対照を作れば、必ず orphan・framing・X/P が代わりに殺すものは見つかりませんでした**。I+genesis と D版読みは producer・frame・証拠面を整えれば存在検査へ帰属できます。

ただし、次は分ける必要があります。

| 試験・変更 | 存在検査の証拠にならない判定 |
|---|---|
| orphan と存在違反の併置 | 非認定だけ。存在検査を消しても orphan が拒否する |
| version dup／genesis commit／last-wins | 非認定だけ。既存 integrity が拒否する |
| cycle 併存 | `not certified` だけ。cycle が拒否する |
| W/R を追加・削除する fixture 修正 | C の件数を合わせなければ framing が拒否する |
| overflow fixture の版変更 | C/W と対応 R を揃えなければ mismatch／orphan が拒否する |

また「異種 op を任意の一つへ潰す」変異は、選んだ op と周辺 R により別の存在違反が残る可能性があります。混在 W だけの最小 fixture で、`ambiguous-write-version` の件数・種別を検査してください。

修正案：独立した負例では `replace(ig, existence_violations=0).clean()` と、一行修正した実 fixture の certified を併用する計画を維持すること。重複版等を理由に検査を省略した件数0は、存在正常の証拠に数えないでください。

**放置した影響：受理集合の欠陥が残っていても、変異 kill を存在検査の実証として過大計上できます。**

## 総括

- 最大の問題は P1 です。初期状態の推定と、実際の初期集合との整合検査は同じではありません。
- 最初の I、未書込み key の genesis 読みは、既存 integrity に触れず曖昧なまま認定されます。
- 親の「実 trace で違反0件」は、その標本への適合を示し、規則の健全性までは示しません。
- 不存在読みは正常 silo では R を増やさず、自己 insert の読みも追加 R を作りません。
- P3 は成功した存在操作列の整合性に必要であり、今回の本題に含めてよいと判断します。
- 段2の空 scan・初期一覧・再挿入問題は今回へ拡張せず、段1の結果から一般化しないことが必要です。
- 共通検査の配置と v2 の射影維持は妥当です。cycle 優先変更は撤去条件から外すべきです。
- pipeline 配線を足す必要はありません。ただし A1 を未解決のまま「§3.3 完了」として印を撤去する計画には賛成できません。