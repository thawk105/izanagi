## 所見一覧

静的検査では、**実装を止める欠陥は確認できませんでした**。ただし、実装後の checker・pytest・変異実走は未確認です。以下の `s1-brief.md`／`s2-plan.md` は指定された親ジョブ配下のファイルを指します。

1. **refuted — H3 追加による fixture の変更漏れ**

   `tools/check_docs.py:833,6379` は必須 H3 の件数と孤児見出しを検査します。定数だけ、または文書だけを変更すれば赤になります。plan は実文書への追加に加え、`s2-plan.md:371–381` で合成 `self_doc` の追加も明示しています。

   また、`_SELF_SECTIONS` は段8の期待参照集合と「全節」の展開に共通して使われます（`tools/check_docs.py:841,906,3429`）。追加による参照集合の拡大も整合します。是正不要です。

2. **real — growth hold により実 repo 検査は通常走で省略される**

   `orchestrator/tests/growth_test_holds.py:581,593,605` に実 repo の3関数が登録され、`orchestrator/tests/conftest.py:1821,2178` は明示 opt-in がない場合に skip を付けます。

   したがって、通常の pytest 成功だけでは実文書の受理を証明できません。一方、実 repo の checker 成功だけでも合成 fixture の更新を証明できません。plan はこの区別と別途 checker 実走を既に記載しています（`s2-plan.md:455–479`）。その受入分離を維持してください。

3. **refuted — SKILL literals・予算・YAML の不整合**

   plan のコードブロックを抽出して再計数した結果は、SKILL **4,241 bytes／最長223文字**、YAML **208 bytes**でした。20 literals はすべて存在し、YAML 本文案と期待定数は末尾 LF を含め一致します（`s2-plan.md:279–335`）。

   `CLAUDE.md` は3回、`$next-tasks` と「クラス 2」は各2回出ますが、新呼出しは `exact_literals` を渡しません。存在検査なので矛盾しません（`tools/check_docs.py:5215–5239`）。4,243-byte 上限には2 bytes の余白しかなく、巨大で実質無効な予算でもありません。

4. **refuted／nit は real — SELF_LIMITS 超過と縮約による義務欠落**

   指定された置換をメモリ上で適用すると **5,999 → 5,996 bytes／最長73文字**となりました。差分は順に −34、−9、＋57、−18、−21、−90、−35、＋171、−21、−3 bytes、合計 −3 bytes です。

   編集条件、安全義務の削除禁止、裁定境界、関連正本との同時 commit、検査義務は保持されています（`docs/skill-self-improvement.md:41–83`、`s2-plan.md:116–193`）。増枠しないため D782 の上限引上げ手順は発火しません。

   **nit:** plan の表は各置換範囲の末尾 LF を数えていません。例えば L3–5 は LF 込みなら **306→272 bytes**で、表の305→271とは各1 byte違います（`s2-plan.md:102–113`）。差分とファイル総量は正しいので、計数規約の明記で足ります。

5. **refuted — routing／既存3 skill・3 command の pin 破壊**

   置換前後の `## routing` から次の H2 直前までを比較し、byte 同一を確認しました。その他の `DEV_WAVE_EXACT_VISIBLE_SECTIONS` 対象も編集対象外です（`tools/check_docs.py:651`）。

   既存 guard 本体・3呼出しは変更せず、個別呼出しを追加する計画です（同`:5108,6534–6568`）。既存 pin を弱める変更はありません。

6. **refuted — next-tasks command の既存契約違反**

   指定 diff と5接頭辞置換をメモリ上で適用すると **26,574 bytes／最長83文字**でした。27,100／100以内で、frontmatter の2 key、`$ARGUMENTS` **0件**、共通自己改善契約への到達性を保持します。`$1` は別の文字列で、混同されていません（`tools/check_docs.py:779,6050–6118`）。

   既存 exact-byte assertion の26,903→26,574更新も plan にあります（`orchestrator/tests/test_check_docs.py:2536–2548`、`s2-plan.md:383–390`）。更新漏れがあればこのテストが赤になります。

7. **refuted／実走は未確認 — 変異 matrix の専属性・恒真 pin**

   `s2-plan.md:400–445` の独立した手書き期待値なら、M1・M3〜M6 は新規 `PIN` 自体で検出できます。M1で既存孤児検査も赤になることを、新規 pin の証拠に代用する必要はありません。

   M2は guard 呼出し削除により YAML 不一致の finding が消え、専用 positive control が失敗する設計です。新規5負例も、H3欠落・byte超過・YAML不一致・literal欠落・余分な file を個別に狙っています。`_pad_to_bytes()` は改行で埋めるため最長行違反を併発しません（`orchestrator/tests/test_check_docs.py:6461`）。

   M0の通常コメントの句読点変更は等価変異として妥当です。実装後は、各指定 node の失敗箇所を確認し、別の赤や収集失敗を KILLED に数えないでください。

8. **refuted — 実測値・既存 skill 余白の誤った一般化**

   既存 SKILL の実測は rulings **2,999**、cleanup-branches **2,646**、dev-wave **4,839 bytes**で、plan と一致しました。上限も3,000／3,100／5,500です。plan は「共通する余白率はない」と明示し、rulings の比率を設計上選んでいます（`s2-plan.md:315–323`）。

   repo 外原本も **13,255 bytes／208 bytes**で、SHA-256 はそれぞれ plan 記載の `39d3247e…982d2`／`22dac38b…fbb` と完全一致しました。主要アンカーは plan の補正値が現物と一致します。

## must-fix と nit の振り分け

- **must-fix：なし。** 検査した範囲では、plan に従う変更で既存契約を誤って受理・拒否する欠陥は見つかりませんでした。
- **nit：byte 表の末尾 LF の扱い。** 放置しても checker の受理集合は変わりませんが、置換範囲の実測値を再現すると各1 byteずれます。
- **nit：brief の D744 の射程表現。** `.agents/**` 全体を docs 面と呼ぶと対象を広く読みすぎます。今回の SKILL.md と interface YAML に限定してください。
- **受入時の未確認事項：実走結果。** 通常 pytest の成功だけを完了根拠にすると、growth hold が省略した実 repo の拒否を見逃せます。plan 記載の個別 checker 実走が必要です。

## brief の前提への反証

P3を支える3事実は反証できませんでした。

- 終端 H3 集合は実際に3 command のままです（`tools/check_docs.py:838`）。
- 共通契約は実際に5,999／6,000 bytesです（同`:289`）。
- 既存3 skill は個別 guard 登録を持ちます（同`:6534–6568`）。

したがって、**「checker 登録済みだから docs／skill 文書だけで完了できる」という前提は成立しません**。command interface 登録と自己改善終端登録は別です。D1890の終端追加と項37の既存 skill 同等扱いを満たすための最小 checker/test 登録には、現物上の根拠があります。

限定的な反証は `s1-brief.md:14` の「D744＝`.agents/**` は docs 面」という一般化です。指定逐語の D744 は `SKILL.md` と `.agents/**/agents/*.yaml` に射程を限定しています。plan はこの点を既に補正しています（`s2-plan.md:487`）。

## 総括

**レンズAでは、plan は実装へ進められる内容です。** 本文案・定数・fixture 更新・独立 pin は静的に整合し、縮約後の予算と routing 不変も再確認できました。

ファイル変更、pytest、checker、変異実走は行っていません。実装後の合成 fixture 検査と実 repo 検査を両方通し、指定した新規 pin 自体による変異検出を確認するまでは、受入成功とは判定できません。
