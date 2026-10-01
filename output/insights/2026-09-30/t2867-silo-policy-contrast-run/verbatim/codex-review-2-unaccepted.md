## 総括

**NO-GO（記録の補記・訂正が必要）。**
指定された統計値・arm 別集計値に、丸めを超える不一致はありません。
4 比較とも「観測差が floor 内」、条件付き優越なし、という判定は事前登録と一致します。
ただし、発効束の必須実値と、判定器の版を「全件」確認した根拠の補記が必要です。
実験の無効や verifier の版違いを認定するものではありません。
静的照合と軽量な再計算を行い、ファイル変更・テスト・性能測定は行っていません。

## 所見

1. **must-fix — 発効束の必須実値が揃っていない。**  
   対象：[決定 fragment・決定4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/docs/spool/decisions/2026-09-30-dev-wave-t2867-contrast-run-1.md:20)。

   **現在：** correctness・bench の引数は「対象 commit の bytes が決める」、verifier の版は本走後の insight に記す扱いです。役割名・model・effort はありますが、入力 schema の版はありません。較正元 record の識別も関数名に留まります。

   **修正：** 較正 record の識別子、correctness・bench の exact argv、verifier の実値、各役割の入力 schema 版または対応する不変 artifact を補記してください。事後補記であることと根拠も明記します。

   **根拠：** [事前登録 §12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/docs/silo-policy-generator-contrast-preregistration.md:456) はこれらの実値を発効決定へ書くよう要求しています。commit によるコードの固定は記録されているため、実行条件自体が未固定だったとは断定しません。

2. **must-fix — verifier 版の「全件一致」は提示台帳だけでは裏付けられない。**  
   対象：[insight §5・§8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/output/insights/2026-09-30/t2867-silo-policy-contrast-run/README.md:81)。

   **現在：** 「判定器の版は全件 `campaign_verifier_epoch = E1:…`」「確かめた……判定器の版が1種類」。

   **照合結果：** 894 件中、epoch を含むのは **576 件＝初期点96＋評価480**で、値は一致しています。残る **318 件＝score240＋系列開始stock48＋参照30**には epoch がありません。

   **修正：** 「epoch を記録した576件で一致」と限定するか、残る318件を確認した別一次資料の path・key・照合方法を追記してください。

   **根拠：** [epoch ありの初期点](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/v1/ledgers/llm-cpp-1/events/000005-slot-result.json:7) の `critic_digest`。一方、[score](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/v1/ledgers/llm-ir-3/events/000060-slot-result.json:7) と [参照stock](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/v1/ledgers/reference-1/events/000003-slot-result.json:7) では同 key が `null` です。版違いがあるという指摘ではありません。

3. **should-fix — floor 内なのは対差の中央値であり、個別対差すべてではない。**  
   対象：[insight §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/output/insights/2026-09-30/t2867-silo-policy-contrast-run/README.md:118)。

   **現在：** 「median と対差では差が floor 内に収まった」。

   **修正：** 「登録した4比較の対差の中央値 `median(d)` は、いずれも floor 内だった」。

   **根拠：** `report-v1.json` の `comparisons[].primary.differences`。`|d| > δ` の対は表の順に **2/12・3/12・5/12・5/12**です。例えば IR 対 random の r=11 は `d=0.11762969`、`δ=0.02955880` です。

   「LLM の最良系列が非LLMの最良より大きい」という**観測最大値の大小自体は正確**で、§6には登録外の比較という限定もあります。§0も「観測した12系列の最大値」「静的10 µs比1.06〜1.11」と明記すると、生成器の優越や非LLM最大値に対する倍率との誤読を防げます。

4. **should-fix — walltime の採用根拠と倍率が省略されている。**  
   対象：[決定 fragment・決定4 walltime](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/docs/spool/decisions/2026-09-30-dev-wave-t2867-contrast-run-1.md:33)。

   **現在：** 「§11.0 の案」と1,800／900／2,700／3,600秒のみ。

   **修正：** 採用した基準所要と倍率を、実測・換算を区別して追記してください。記録値からは、job 1 が `1800/759≈2.37`、評価が実測最大289秒なら `900/289≈3.11`、前走scoreが `2700/1207≈2.24`、前走参照が `3600/2135≈1.69` です。

   **根拠：** 事前登録 §12 は「実測の最大所要への倍率」を要求します。§11.0 のscore・参照は換算で、決定7の前走実測とは区別が必要です。walltime の値そのものは一致しています。

5. **should-fix — 公平性の要約を目視で確認できた範囲に限定する。**  
   対象：[insight §0・§6.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/output/insights/2026-09-30/t2867-silo-policy-contrast-run/README.md:19)。

   **現在：** 「worker を恒常的に駐車させる endpoint は無い」。

   **修正：** 「目視では、特定workerを恒常的に駐車させる明示的な構造は見つからなかった。実走の偏り・飢餓は未計測」としてください。

   **根拠：** `endpoints-v1.json` の本文は構造の目視を支えますが、worker別の進捗を示しません。§6.1自身も実走での偏りは判定できないとしています。同じ規則・thread-local状態であることだけでは、公平性は確認できません。

## 照合して一致した点

- 4比較の median d・raw p・Holm p・正の対数・判定はすべて一致。全4096通りの符号反転による独立再計算も一致しました。Holm は各族 **0.025→0.05**で、両族とも初段で止まります。
- stock CV・batch別CV・`f=0.03`・`δ=0.02955880224`、arm別median・範囲・静的10 µs比・初期endpoint数・A使用は一致。worklogにも対象数値の不一致はありません。
- 条件付き優越に各族の両比較が必要なこと、「同等」が母集団の等価性の証明ではないこと、§7.4の判定順の読み方は整合しています。
- 事前登録とreportの実SHA-256、PIN表記、51項目の完了、894 slotのcertified・品質正常、台帳上の開始順とscheduleは一致しました。commit・生成器／親指示文hashの実物照合、scheduler記録・trace保全の完全監査は今回の確認範囲外です。