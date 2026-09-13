## 総括

**real：提案の2個の README pin だけでは、sized policy 自体の凍結は機械的に強制されません。** README を維持したまま seed・証明書参照を変更できる経路が残ります。
D1452 の5値照合は恒真ではなく、有効です。ただし証明書の replay や成果物参照の固定まで保証するものではありません。
十進文字列の受理拡張には、非標準表記と float への変換時の不整合が含まれます。
`formal=false / final_estimate_eligible=true` は現行実装と整合しますが、正式測定の実行面が完成した意味にはなりません。
driver の変更だけで公開済み pilot や sizing 証明書は無効になりません。ただし現行 checkout での再 materialize は別です。
以下は静的検査と候補 JSON の読解による所見です。pytest・replay・測定は実行していません。

## 所見

参照の略記：`driver` は `orchestrator/campaign/paper_story_a1_paired.py`、`生成器`・`検証器` は指定された `tools/size_paper_story_a1_balanced.py`・`tools/verify_paper_story_a1_balanced_sizing.py`、`pilot事前登録` は指定された pilot preregistration の README、`plan` は指定された `s2-plan.md` です。

1. **real — policy の凍結検査に自己照合が残る。**

   `driver:1017` は sized policy の期待 SHA を `None` として返します。`driver:1695` は渡された policy とディスク上の policy を比較しますが、`load_policy` はその同じファイルを読み込んで渡します（`driver:1724`）。README は bytes の hash を検査するだけで、その本文と各 policy 値を照合しません（`driver:1710`）。

   したがって、凍結後にディスク上の `schedule_root_seed` を別の64桁 hexへ変更しても、形式検査（`driver:1467`）を通り、新しい seed から順序が生成されます（`driver:1759`）。README の seed 表・原像とは不一致のままです。提案の seed テスト（`plan:557`）は検出手段になりますが、runtime の束縛とは別です。

   **成果物影響：README の hash を変更せず、policy の seed・authority・適法な出力先・証明書参照を差し替えられます。**

   局所修正は、既存の policy hash 検査経路を sized にも適用することです。`plan:482` で確定した policy bytes の SHA を `_policy_identity` が返すようにすれば、README への逆参照は不要です。

2. **real — schedule 原像の選択時点は pilot 後であり、hash 化だけでは事後選択を排除できない。**

   3個の root とその原像、`result_authority`、出力先、README の構成は、いずれも今回選択可能な値です（`plan:404`、`plan:416`、`plan:427`、`plan:449`）。pilot 前から固定された値として扱ってはいけません。

   とくに原像の接頭辞や版文字列を変えれば、同じ workload・選択済み n に対して別の順序列を得られます（`driver:1762`）。pilot の時間推移や順序依存を見て原像を選別すれば、本走で配置される順序を選べます。残留効果がないとは登録していないため（`pilot事前登録:98`）、それは将来の対応差や分類を動かし得ます。**実際に選別した証拠はありません。**

   **成果物影響：原像の選別は policy の3 seed と本走の物理順を変更し、登録推定対象の実現値に影響し得ます。**

   `plan:455` の選び直し禁止は採用できます。ただし「pilot 後、本走前に新規選定した値」と明記してください。新規凍結と pilot 前の凍結を区別する必要があります。

   **refuted — 他の新規値が、この案で性能依存の選択を実行している。** `result_authority` の文言自体は統計分岐に使われず、提案は用途を非正式に制限しています。path の変更は参照・公開先を変えますが、この案では workload や観測値を選別していません。README も3 workload と既存の限界を残す構成です（`plan:431`）。変更可能だったことだけから、実際の事後選択とは認定しません。

3. **refuted — D1452 の追加照合は恒真、または argv との自己照合でしかない。**

   提案は自由な argv や sized policy から期待値を取得せず、pilot 事前登録の literal と型込みで比較します（`plan:53` 付近の追加コード）。出所は候補上下限が `pilot事前登録:166`、root が `:184`、試行回数が `:189` です。sized 分岐から必ず呼ばれます（`driver:1665`、`driver:1680`）。

   一方、既存 replay は指定された `VerificationConfig` から期待証明書を再生成します（`検証器:608`、`:711`）。それだけでは登録値との一致を保証しません。D1452 の「consumer が事前登録の値と照合する」（`verbatim/d1452.md:3`）に対し、提案には実効があります。

   **成果物影響：追加照合によって、登録外の試行回数・候補上下限を申告した証明書が consumer の受理集合から除かれます。**

4. **real — 十進文字列の追加は、正規の数値表記だけに限定されていない。**

   `_positive_decimal` は `Decimal(str(value))` を直接使い、有限かつ正であることだけを検査します（`driver:1252`）。提案の追加 float 検査は有限性だけです（`plan:33` 付近）。

   | 入力例 | 提案された局所検査 |
   |---|---|
   | `0`、`-1`、`"-0"`、bool | 拒否 |
   | `"NaN"`、`"sNaN"`、`"Infinity"` | 拒否 |
   | `"1e3"`、`" 1000 "`、`"１０００"`、`"1_000"` | 受理 |
   | `"1e-9999"` | Decimal は正、float は `0.0` なので有限性検査を通る |

   本番証明書と一致しない `1000` 等は後段の exact 数値照合で落ちます。しかし、例えば k の `" 2.8315526875186725 "` は本番証明書と数値一致します。さらに `"2_.8315526875186725"` は Decimal では一致しても、統計側の `float(workload["k"])`（`driver:4713`）では変換できません。提案の検査が変換するのは元文字列ではなく Decimal 値なので、この差を捕捉しません。

   **成果物影響：policy の受理表記が広がり、検査を通った値が統計処理で変換エラーになる経路も追加されます。**

   sized 分岐内で元値の float 変換も確認し、正値条件を保持する局所修正が必要です。文字列の表記をどこまで許すかも明示してください。生成器の `.17g`（`生成器:127`）は指数表記を出し得るため、指数表記を一律禁止する案にはしません。

5. **refuted — `formal=false` と `final_estimate_eligible=true` は矛盾する。**

   `driver:1404` は sized に後者の `true` を要求します。統計側では pilot のみ分類前に戻り（`driver:4707`）、sized は区間・分類を計算します（`:4713`）。対して v3 raw consumer は結果と receipt の `formal=false / promotion_prohibited=true` を要求します（`:7641`）。公開 README も非正式と表示します（`:8116`）。

   したがって **plan の P1-3 不採用は現行実装に照らして正しい**です。これは「登録された本走解析の対象になる」と「正式結果としての権限」を別に扱っています。

   [T-1505] の逐語は「正式測定の認可は人間手番のまま維持する」（`verbatim/t1505.md:3`）であり、policy の `formal` key の意味までは定義していません。逐語だけから「認可前に将来用 `formal=true` を記述することも禁止」とは断定できません。ただし逆案では policy と実際の出力が食い違います。

   **成果物影響：plan は分類可能な非正式 profile を作ります。正式測定・正式成果物の完成や投入認可を意味しません。**

6. **refuted — 今回 driver を変更すると、公開済み pilot と sizing 証明書が無効になる。**

   sizing の入力は pilot JSON の bytes・観測値です（`生成器:407`、`検証器:340`）。replay receipt が記録する source は生成器と検証器であり、driver は含まれません（`検証器:726`）。pilot の source binding 検査も、記録の構造・対応関係を検査し、driver の現行 bytes との一致を要求していません（`driver:4787`、`:7654`）。

   これは規律7の「現行コードとの差は、それだけでは何かを無効にする理由にならない」（`CLAUDE.md` の規律7）と整合します。

   **real — ただし再 materialize は現行 bytes 同一性に依存する。** `driver:8674` は `_verify_current_source` を呼び、記録済み commit・blob・working SHA と現行 checkout を照合します（`:7478`、`:7491`）。

   **成果物影響：既存 pilot と証明書の値・有効性は維持されますが、変更後 checkout での同じ raw bundle の再公開経路は拒否され得ます。**

   この既存制約を「pilot が無効になった」と説明してはいけません。今回の証明書生成には、その再公開は不要です。

7. **refuted — 本 wave が anomaly の即 reject を弱める経路を新設する。**

   **無い。** 提案は sized 統計値の型・証明書照合・pin に限定され、`verify-not-certified` と anomaly 検査（`driver:5188`）や bench 前の correctness gate を変更しません。

   **成果物影響：正しさゲートの受理集合を広げる変更は確認できません。**

8. **real〔nit〕—「1.1秒から本番でも数分」という一般化には根拠が足りない。**

   本番候補は全 workload で候補1個・認証1回で停止しています（`sizing-certificate.candidate.json:1`）。実装は十分統計量の長さ `trials` の配列を生成し（`生成器:613`）、最初の認証成功で終了します（`:711`）。候補格子全体を本走するわけではなく、分位点や二分探索など試行回数と単純比例しない処理もあります（`:347`、`:368`）。

   よって、試行回数を100倍にして総所要時間も100倍とする外挿は成立しません。ただし、**1.1秒と0.36秒の逆転の原因を、この資料だけから一意に特定することもできません。** 前者の候補履歴・起動条件・計時区間が提示されていないためです。後者の速さと整合する実装上の理由と、2実測の差の原因は分ける必要があります。

   **成果物影響：証明書・policy・登録解析の値への波及は確認できないため nit。** brief の所要時間説明（`s1-brief.md:47`）を訂正し、凍結済み設定の変更理由には使わないでください。

9. **refuted — D1452 を各 consumer に重複実装する必要がある。real — 本走実行面の未完了は残る。**

   balanced 証明書の意味検査は共通 driver に集約されています。次の経路は共通 loader／validator を通ります。

   - submit selector：`driver:3349`
   - job preflight：`tools/pegasus/paper_story_a1_paired.sh:559`
   - measurement：`driver:7209`
   - arm consumer：`driver:5323`
   - materializer：`driver:8721`、`:8640`

   別の証明書 consumer として headline driver はありますが、別 path の headline 証明書・receipt を束縛する経路です（`orchestrator/campaign/paper_story_a1_headline.py:1510`）。今回の balanced 証明書を読む別 driver は検索範囲で見つかりませんでした。独立検証器の argv 依存は所見3のとおり残りますが、登録適合性を確認する consumer と役割を分ける案は成立します。

   一方、job の第三者 source staging は pilot 限定（`tools/pegasus/paper_story_a1_paired.sh:1362`）、計測本体は pilot attempt 契約を無条件要求します（`driver:7077`）。plan はこの未完了を正しく認識しています（`plan:493`）。

   **成果物影響：証明書・policy の loader 受理を完成しても、sized 本走は実行可能になりません。**

## 構成した偽の証明書 (攻撃点 2 への回答)

登録違反だが内部再計算とは整合する、最小の反例です。

```text
元：sizing-certificate.candidate.json の全内容
変更：policy.candidate_grid.maximum を 4096 → 4095
その他：変更しない
```

両上限で実現候補列は同じ `30,40,…,4090` です（`生成器:139`）。候補 JSON は最初の `n=30` で停止しており、子 seed に上限値は含まれません（`生成器:553`）。そのため、`n_max=4095` を渡した既存 verifier が再生成する内容と整合する構成です。これは静的構成で、replay は実行していません。

canonical JSON として保存したと仮定し、policy の証明書 SHA もその bytes の SHA に更新します。

- **plan の十進文字列対応を適用し、D1452 照合だけを省いた場合**：既存 consumer は上限を検査せず、入力・n・df・k・sigma の照合を通します（`driver:1325`、`:1355`）。
- **D1452 照合を追加した場合**：`maximum != 4096` で拒否します。
- README の証明書 hash を据え置いた不一致まで現在の runtime は検出しません。ここが所見1の policy bytes 固定を必要とする理由です。

これは「数値結果が違う」反例ではなく、**事前登録と異なる設定の証明書を受理する**反例です。

## 親裁定へ返す項目

- 今回の局所追加として、既存経路による **sized policy bytes の SHA 固定**と、十進文字列から実計算への変換整合性を含める。
- schedule 原像・3 seed は「pilot 後、本走前の新規選定」として確定する。pilot 前から凍結済みだったとは記述しない。
- `formal=false` 案を採用し、**正式性の扱いと pilot 専用 source 契約の本走対応**は未完了の裁定パッケージ候補として返す。本 wave の完了名は「証明書・policy の凍結」とする。
- 再 materialize の現行 source 同一性制約は既存の別課題として返し、公開済み pilot の無効化や再測定には結び付けない。