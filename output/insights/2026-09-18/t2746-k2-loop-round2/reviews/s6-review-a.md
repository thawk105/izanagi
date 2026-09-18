## 所見

以下、`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/`。判定は静的レビューによるものです。テストは実行していません。

### must-fix

1. **real — critic の取込みと再抽出で空白の扱いが異なり、正常に取り込んだ AO が renderer に拒否される。**

   根拠: `C/p3_s4_loop.py:2598–2606` は見出し直後の改行を除き、本文に `rstrip()` だけを適用します。一方、`C/layer3_report.py:188–195` は `strip()` を適用します。本文が空白や空行で始まると一致しません。既存の追加 fixture 自体が `"  exact text"` を保存しています (`T/test_p3_s4_loop.py:9027,9081`)。

   **成果物影響:** 取込み成功済みの critic を含む campaign で材料レポート全体が生成不能になります。

   最小是正: 原文の範囲選択と末尾処理を両側で一致させる。既存の先頭空白を保持する期待値は変えず、この取込み結果を renderer へ渡す検査を追加する。空見出し `## ` の扱いも、両正規表現の `*` / `+` 差を解消する。

2. **real — コードブロック内の見出しを critic の正式な節として受理する。**

   根拠: `C/p3_s4_loop.py:2598`、`C/layer3_report.py:188` は行頭の正規表現だけで見出しを抽出し、fenced code block を区別しません。4 見出しが例示コード内に各1回だけ存在する Markdown でも欠落検査を通過します。両側が同じ誤抽出をするため、再抽出一致も防壁になりません。

   **成果物影響:** critic が例示した文字列が `mechanism_hypotheses.attribution` に正式な帰属として掲載されます。実際の節と例示が両方ある場合は誤って重複拒否します。

   最小是正: fenced code block 内を見出し候補から除外する抽出規則を両側で共有する。例示内だけに4見出しがある負例と、正式な節に見出し例を含む正例を置く。

3. **real — planner/coder の非 null variant は取込み口で受理されても renderer が拒否する。**

   根拠: `C/p3_s4_loop.py:2683–2686` は planner/coder について WAL の任意 stage に variant があれば受理します。`C/layer3_report.py:172,179–180` は全 AO に commit の存在を要求します。たとえば abort だけが残る variant に結び付けた coder 出力が該当します。裁定 A8 は非 null に「WAL 実在」を要求しています。

   **成果物影響:** 拒否・中断された提案の記録を正規の取込み口から追加すると、それまで生成できた材料レポートが生成不能になります。

   最小是正: planner/coder は WAL 全体の variant 集合で照合する。critic の条件とは分け、取込みから report まで同じ受理条件になる検査を追加する。

4. **real — provenance の主張限定が公開契約に不足している。**

   根拠: `C/p3_s4_loop.py:2575` に申告入力と実消費を区別するコメントはありますが、`C/agent_outputs.py:1–6` の docstring、`C/p3_s4_loop.py:2554,2569`、`C/layer3_schema.json:510–565` には `mode`・`ts`・入力 hash・prompt hash の意味が明記されていません。`mechanism_hypotheses` は renderer docstring (`C/layer3_report.py:12–13`) で非実証と明記する一方、schema (`C/layer3_schema.json:443`) には description がありません。

   **成果物影響:** schema や保存 AO だけを読む利用者が、`live` を実生成の観測、`ts` を生成時刻、hash を実送達の証明として過大解釈できます。

   最小是正: docstring と schema description に、`mode` は記録方式、`ts` は記録時刻、入力 hash は呼出し側が申告した保存 JSON の canonical hash、prompt hash は指定ファイルの bytes hash と明記する。機序仮説も LLM の帰属記録であり実証ではないと明記する。

### nit・確認限界

5. **real — 既存経路の bytes 同一性を追加テストだけでは証明していない。**

   根拠: `T/test_p3_s4_loop.py:9235` からの `test_agent_live_main` は評価関数を置換し、同じ新実装の AO 無効／有効を比較しています。変更前実装との比較ではありません。差分上、未指定時は追加の capture・agent_record 引数を渡さず、AO 追記も通りません (`C/p3_s4_loop.py:2500,3023,3041`)。

   **成果物影響:** 現時点で値の変化は確認していませんが、この検査を「旧実装との bytes 同一性の実証」と記録すると検証範囲を過大に表します。

   最小是正: 報告を静的互換確認と実測範囲に限定する。bytes 同一を主張する場合は親の比較実測を根拠にする。

### refuted

6. **refuted — 入力側防壁の3検査が恒真である、または現在の入力生成経路が AO を読むという疑い。**

   根拠: `C/p3_s4_loop.py:1176–1248,1531–1562,2905–2927` に AO 読取りはありません。`T/test_p3_s4_loop.py:9358–9437` は AST への reader 呼出し挿入、実入口での reader 呼出し禁止、同一 layout の AO 不在／正常／破損による出力比較を含みます。指定された変異は失敗する構造です。ただし AST 検査は一般的な推移的依存解析ではありません。

   **成果物影響:** 確認した経路では AO の追加・内容が planner 入力や certified 選択へ還流しません。

   最小是正: 現状への修正要求なし。変異の実走結果は親が確認する。

7. **refuted — proposal 全体の planner 偽装、出力 hash の入力 hash 扱い、harness 外の writer 増加。**

   根拠: `C/p3_s4_loop.py:2641–2660` は stage/key と planner wrapper・5 key を検査します。入力 hash は指定入力から計算 (`:2692`)、live も role 別入力から計算 (`:2583`) しています。manifest・critic digest・WAL ref の照合は `:2670–2703` にあります。`git grep` で本番 writer 呼出しは `:2594,2709` の2箇所だけでした。保存面の不変検査は `T/test_p3_s4_loop.py:9054–9085` で WAL・lock・loop_state・digest・receipt を名指ししています。

   **成果物影響:** これらの疑いによる参照偽装や正しさゲートの受理集合変更は確認できません。通常 report の `certifying_input=false` / `acceptance_receipt=null` も維持されています (`C/layer3_report.py:983–984`)。

   最小是正: 現状への追加修正要求なし。hash の真正性に関する説明は所見4で補う。

## 総括

**新規 must-fix は4件です。** 特に所見1・3は、正規取込みに成功した AO が材料レポート生成を止める実装間の不整合です。所見2は原文との一致検査を通過する誤帰属です。

既知の赤2件は、双射エラー文言変更 (`C/layer3_report.py:338`) と新設 fixture の WAL 構成 (`T/test_layer3_report.py:5464`) に帰属し、親の説明と整合します。

正しさゲート本体の変更は確認していません。編集・テスト実行・commit・push は行っておらず、緑の追加主張はありません。