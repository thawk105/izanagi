## レンズ A

指定資料を静的に照合しました。**主要数表の転記は一致していますが、記録の意味を変える誤記・限定漏れがあるため NO-GO** です。以下、資料名は insight 内の相対パスです。

### must-fix

**A1 — §1 の着地後 main SHA が違う。**

- 対象: README §1「local main が `65966f4d8` へ進んだ」。
- 照合元: `measurements/p3-attempts.jsonl:51` は監査 HEAD が `65966f4d8…`、`main_after` が **`5733c0f08…`**。`verbatim/s4-ruling.md:11` も後者を明記。
- 影響: 監査対象 tip と着地後 main を取り違えた履歴になる。
- 置換案: 「T-2803 の tip `65966f4d8…` の land が完了した 2026-09-21 00:12:00 JST（記録上の main_after=`5733c0f08…`）」。

**A2 — §4・§7 が replay と実装の非同値条件を落としている。**

- 対象: §4「実装と同じ候補選択」、§7 の限界。
- 照合元: `verbatim/s5-author-self-run-summary.md:24–30` の7項目。特に **mode 検査省略、他 partition の代表候補選択と因果非同定、時刻のみのログの日付補正、同名 land JSON の上書き**が未記載。`receipt_reuse_replay.py.txt:163–170,227–239`、`audit_attempt_ledger.py.txt:48–52,194–204`。本体 `_read_audit_receipt`（checker:2451以降）は directory 0700／regular file 0600 等を検査する。
- 影響: 現行関数による bytes の検証成功を、本番 lookup の受入条件まで検証した結果と読ませる。
- 置換案: 「選択集合・ancestry・距離順・prefix/raw correction は現行実装を使用する。一方、候補集合は残存受領証の厳密な mtime 順で近似し、mode 等の `_read_audit_receipt` 検査は再現しない」。続けて上記4項目と「preclaim 未対応時は postmerge を推定しない」を追記する。

`_commit_range`／`_build_ancestry` の使用、距離・filename順、最初の prefix 成功後の raw correction による fallback は、probe と checker:2606–2646 で一致しています。

**A3 — §5 の分類表は probe の分岐を正確には表していない。**

- 対象: §5「attributes 単独差＋root `.gitattributes` 変更」、checker変更／partition跨ぎの定義。
- 照合元: `receipt_reuse_replay.py.txt:210–244`。
- 相違: root変更を調べるのは**旧形だけ**。新形・中間形は「原因未特定」。複合差は原因を連結する。他 partition は任意の存在判定ではなく、距離・filename・mtime・partition順で選んだ代表候補と比較する。全 partition に候補なし、replay失敗、未判定の分岐も表にない。
- 影響: 分類規約を因果の単独同定と誤読し、未判定や複合差を4種へ強制的に割り当てる定義になる。
- 置換案: 「主分類は probe の比較規約による。代表候補との差は単独原因の証明ではない。複合差・replay失敗・未判定は別記する」。旧形条件と未判定分岐を表へ追加する。

今回の87行の集計に二重計上はなく、checker SHA→系統の**7対応は定数と一致**しています。

**A4 — attributes digest 差から原因を確定しすぎている。**

- 対象: §1・§6.1 の「候補集合変化だった」、§6.1「期間中に root `.gitattributes` を変えた commit は0」、§8「errno 起因の不一致は0件」。
- 照合元: `receipt_reuse_replay.py.txt:212–225` は旧形・attributes差・比較区間のroot変更なしから参考ラベルを付けるだけ。checker:2320–2387 の fingerprint は working/index、info/global/system attributes、errnoも含む。JSONL の26件は `bindings_diff` が `attributes` のdigest差で、`gitattributes_commits=[]`。
- 影響: 分類上の参考ラベルを原因の実証へ昇格し、errno等の未識別要因を不存在と記録する。
- 置換案: 「26件は probe の規約で旧形候補集合変化の参考区分に分類された。検査した26比較区間ではroot変更なし。digest差の内訳は復元しておらず、errno等を個別に排除していない。3候補を支持する原因は確認できなかった」。

**A5 — unsupported 10本を「受領証が残っていない走」としている。**

- 対象: §6.2 の母集団説明、§7末尾。
- 照合元: `audit_attempt_ledger.py.txt:108–114,228–231`。unsupported は開始を解析できない**ファイル**で、集計期間の判定も attempt開始ではなく file mtime。`p3-attempts.jsonl:52` は T-2803 の `land-wait-3.log`。
- 影響: ログ形式の欠測を受領証消失・別監査10件と誤って数える。
- 置換案: 「unsupported 10本は、file mtime が対象期間内の解析不能ログファイルである。監査attempt数・受領証の有無は確定していない」。

**A6 — P-4 の同一node・queue値、main履歴の断定に照合可能な出所が不足する。**

- 対象: §6.3 の `bnode019`、mtime差10／8秒、`queue_wait_s=5.23`。§6.1「6件中5件は main に入らなかった版」、§8「checker変更2回」と各commit時刻。
- 照合元: `force-dispatch-{1,2}.meta.txt:2–12` にある hostname は login の `pegasus02`。`.out.txt:7` は dispatch receipt の保存先を指すが、receipt本文は指定資料にない。`.err.txt:27–29` の request作成→開始は9／7秒であり、表のmtime差とは別の計測点。P-2はmainへの採用履歴を出力しない。
- 影響: 同条件対照と救済頻度の根拠を第三者が検証できない。
- 是正案: 「同一node・queue値は dispatch receipt の〈保存path・field〉による」と逐語を添える。main履歴も、checker bytesの変化と採用関係を示す出力を添える。それまでは「指定保存資料では未確認」とする。**値が誤りと確認したのではなく、裏付けが不足しています。**

### nit

- **loadの欠測件数**: §6.2の範囲1.44〜4.93は一致。ただし17行中値があるのは13行、4行はnull（P-3 stdout:72,79,83,93）。結論は変わらないが、「load1観測13行、欠測4行」を追加すると明確。
- **約1/7**: §6.3の「1/7」は丸め。err各5–6行の差は35.140235990秒／5.236608358秒。「約1/7」とする。

## レンズ B

### must-fix

**B1 — 「現行checkerの祖先受領証なしは2回だけ」の範囲が欠ける。**

- 対象: README §1・§8、fragment title。
- 照合元: P-2 stdout:61–62の2件に加え、README §6.3自身が P-4初回の現行checker・別partition coldを記録している。P-1 after1 stdout:6,23も新partitionを示す。
- 影響: P-4を含む診断全体では成立しない「だけ」になる。
- 置換案: 「**P-4実行前の凍結目録に基づくM＋Rでは**、現行checkerの同partition祖先候補なしは2件。P-4初回は別枠」。

**B2 — §8 が区画統一による救済対象を観測済みと読ませる。**

- 対象: 「観測では T-2803 着地時のland 1回が該当」。
- 照合元: P-2 stdout:62ではconfig・inheritedに複合差がある。`s4-ruling.md:18`、`s3-consult-A.md:165–167` は祖先・bindings・時系列が揃う場合だけ救済可能としている。
- 影響: 「partition跨ぎを観測」と「統一後に再利用可能」を同一視し、回避回数を実績化する。
- 置換案: 「land 1件とP-4初回はpartition跨ぎの観測例である。統一後の全bindings一致とlookup前の利用可能性は未検証なので、救済可能件数は確定しない」。

**B3 — fragment title が事後推定を実績として要約する。**

- 対象: fragment:7「warm / coldを実測した」「coldは0件」。
- 照合元: README §7、P-2 stdout:2、裁定A1。
- 影響: worklogの見出しだけでは「当時coldが0件だった」と読める。本文:13の「数値を再掲しない」とも運用が揃わない。
- 置換案: 「T-2803着地後の残存受領証から再利用可能性を事後診断し、計算ノードdispatchを対照測定した（診断のみ・実装差分なし）」。

### should

該当なし。記録の正しさに関わらない改善はnitへ分類しました。

### nit

- **削れる重複**: README §2・§3・§9・§10とfragment本文の作業経緯が重複する。`origin.md:4–9` の診断結論には不要。READMEは方法の訂正に必要な経緯だけに絞り、工数・事故はfragmentから詳細資料へリンクすればよい。
- **外部値の出所**: §8の1.7〜3.5秒は本waveのstdoutではなく、`s1-brief.md:4,32` が指す **T-2803 insight** 由来。memo化が毎走の費用を減らし、coldの原因を消さないという区別は妥当。元insightの該当節へ直接リンクを付ける。
- **未裏付けの作業時刻・工数**: §3・§10の55.8秒、各段の分刻み時刻、48 MB、fragmentの3分／6分等は、指定の計測stdoutだけでは確認できない。launcher記録等の出所を付けるか、省く。`codex 5本`もreview/focus終了後の実数に更新する。

依頼への対応は、landログの突合、他bindingの分類結果、計算ノード対照を備えています。混雑時・login同条件対は未観測と明記され、480秒保証等の禁止文も概ね守られています。「効果見積り付き」は条件式と計算ノード対の29.9秒で満たせますが、B2の条件とA6の出所補完が必要です。

## 総括

**照合単位を表の1行・対応1組・値1組として、81件を照合し80件一致、1件不一致**でした。重複掲載は数え直していません。

| 照合対象 | 件数 | 一致 |
|---|---:|---:|
| P-1基準件数・旧3partition内訳 | 6 | 6 |
| REUSE集計・M内訳・R候補なし8行・M参考1行 | 18 | 18 |
| ATTEMPT集計・land7行・24行のM成功との結合・load範囲・参考間隔 | 38 | 38 |
| P-4時間5値・request/rc/監査件数2組 | 7 | 7 |
| checker系統7対応・probe SHA4本 | 11 | 11 |
| 着地後main SHA | 1 | 0 |

35.1／5.2秒、57.85／27.31秒、差29.9秒は一致。**受入17行・land7行は24行すべてMのreplay成功に対応**します。この一致件数には、出所不足のnode・queue・main変更履歴や作業工数を含めていません。全数値を検証済みとは扱えません。

must-fixは **A1 main SHA、A2非同値条件、A3分類定義、A4原因の過剰断定、A5 unsupportedの意味、A6出所不足、B1「2回だけ」の範囲、B2救済条件、B3 fragmentの実績表現**。

**NO-GO。主要数表を作り直す必要はありませんが、上記の訂正と証拠補完が必要です。**