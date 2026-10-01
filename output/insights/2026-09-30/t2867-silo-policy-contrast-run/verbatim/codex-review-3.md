## 総括

**NO-GO（発効束の記録補完が必要）。**  
初回所見は **closed 4 件、partial 1 件、regressed 0 件**です。  
指定された数値について、丸めを超える不一致はありません。  
「4 比較とも観測差が floor 内、条件付き優越なし」という解釈は事前登録と一致します。  
残る must-fix は correctness・bench の exact 引数の記録です。実験の無効を認定する所見ではありません。  
委任せず、指定資料の静的照合と手計算で確認しました。4,096 通りの符号反転の再計算は今回行っていません。

## 1 回目の所見の判定表

重大度は初回所見の区分です。

| # | 重大度・判定 | file・節／現在の記述 | 判定理由・必要な修正・根拠 |
|---|---|---|---|
| 1 | **must-fix／partial** | [決定 fragment・決定4補記](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/docs/spool/decisions/2026-09-30-dev-wave-t2867-contrast-run-1.md:36)：較正 record、verifier 実値、入力 schema を固定するファイルの hash を追加。引数は `python3 … --form <cpp\|ir> … --contrast-run-unit <単位 file>`。 | 較正・版・schema の識別と事後補記の表示は改善。ただし掲載されたものは **driver の起動テンプレート**で、verify・bench 自体の引数は依然「対象 commit が決める」。[事前登録 §12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/docs/silo-policy-generator-contrast-preregistration.md:459) が求める実行時の exact argv を、可変 path の対応と根拠付きで補う必要があります。 |
| 2 | must-fix／**closed** | [insight §5・§8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/output/insights/2026-09-30/t2867-silo-policy-contrast-run/README.md:82)：576 slot の一致に限定し、318 slot は版未照合と明記。 | 正しい限定になっています。抜き取りでも、`llm-cpp-1/events/000005-slot-result.json` の `critic_digest` に epoch があり、`llm-ir-3/events/000060-slot-result.json` と `reference-1/events/000003-slot-result.json` は `critic_digest: null`。 |
| 3 | should-fix／**closed** | [insight §0・§6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/output/insights/2026-09-30/t2867-silo-policy-contrast-run/README.md:120)：floor 内なのは `median(d)` と明記。最大値比較は登録外と限定。 | `comparisons[].primary.differences` と一致。`|d| > δ` は順に **2・3・5・5 対**。最大値の倍率も静的 10 µs 比と明記され、生成器の優越という読み方を抑えています。 |
| 4 | should-fix／**closed** | [決定 fragment・決定4 walltime](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/docs/spool/decisions/2026-09-30-dev-wave-t2867-contrast-run-1.md:33)：基準所要と倍率を追加。 | **1800/759 ≈ 2.37、900/289 ≈ 3.11、2700/1207 ≈ 2.24、3600/2135 ≈ 1.69**。事前登録 §11.0 の換算と、insight §3・決定7の前走実測も区別されています。補記時点については下記所見。 |
| 5 | should-fix／**closed** | [insight §0・§6.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/output/insights/2026-09-30/t2867-silo-policy-contrast-run/README.md:127)：明示的構造が目視で見つからなかった、と限定。実走の偏り・飢餓は未計測。 | `endpoints-v1.json[].body` から確認できる構造と、worker 別進捗の未計測を区別しています。追加修正は不要です。 |

## 新しい所見

1. **should-fix — 生成器の確率・重みの採用値が、所在の説明に留まっています。**

   対象：[決定 fragment・決定4「生成器」](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/docs/spool/decisions/2026-09-30-dev-wave-t2867-contrast-run-1.md:25)。

   **現在：**「§4.4・§4.5 の確率・重みの実値はこの file の定数」。

   **修正：** 採用値が登録本文どおりであることを明記し、少なくとも `next_state` 省略・葉選択 **1/2**、整数ゼロ **1/8**、進化の置換／field 追加 **4/5・1/5**、各一様選択、整数 log 重みの定義を対応付けてください。登録値と実装値の一致を未確認なら、その区別も必要です。

   **根拠：** [事前登録 §12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/docs/silo-policy-generator-contrast-preregistration.md:461) は、実装の commit・hash **と**確率・重みの実値を要求しています。現在は実装の識別はありますが、値の採用を明示していません。

2. **should-fix — walltime 根拠の事後補記が、補記表示の範囲外です。**

   対象：[決定 fragment・決定4 walltime と補記](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/docs/spool/decisions/2026-09-30-dev-wave-t2867-contrast-run-1.md:34)。

   **現在：** 初回所見を受けて追加された倍率が、通常本文に置かれています。その次の箇条書きだけが「2026-10-01、本走の完了後」「次を補った」と表示されています。

   **修正：** 倍率にも「2026-10-01 記録レビュー後の補記。walltime は変更なし」と付記するか、日付付き補記の中へ移してください。

   **根拠：** `verbatim/codex-review-2-unaccepted.md` 所見4と現行記述の対応。数値は正しいものの、発効時に記録済みだった内容と、本走後に説明を補った内容の区別が不完全です。

## 照合して一致した点

- [report-v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-contrast-run/output/insights/2026-09-30/t2867-silo-policy-contrast-run/report-v1.json:2098) の4比較の **median d・raw p・補正 p・正の対数・判定**は insight の表と一致。正の対数は **8・7・8・8**。Holm は各族の初段で止まり、全比較で `|median(d)| ≤ δ` です。
- `floor` の CV、batch 別 CV、`f=0.03`、`δ=0.0295588022415444` は一致。全48系列の `endpoint_cv` は精度不足の閾値 0.06 未満です。
- `descriptive` の score median・範囲・静的10 µs比・初期点 endpoint 数・A使用数は全 arm 一致。LLM×IR の正確な median **3,931,965.5**も、記載値への丸めが正しいです。worklog の対象数値にも不一致はありません。
- 事前登録 §7.3・§7.4・§13 に対する解釈は整合しています。母集団の等価性、生成器一般の優越、実走の公平性を確認したという過大主張は、修正対象箇所には残っていません。
- §8 は未照合の318 slot・trace保全を区別し、独立再計算も「不受理の初回レビューが報告した」と帰属を明記しています。今回、scheduler・modelUsage・trace保全の全件監査は行っていません。