## 裁定と編集制限の不一致

**実装前に不一致を確認したため、指示どおり停止しました。ファイル変更はありません。**

`s4-ruling.md` §2 項4が採用する `s2-plan.md` §4 は、`test_layer3_report.py` の `_historical_exact_grammar_campaign` に **63分岐と新しい rewrite helper の呼出しを追加**するよう指定しています。

一方、今回の編集許可は同ファイルについて「歴史 param `[63, 62, 24]`、歴史 epoch 表、現行ラベル 63 → 85 **だけ**」に限定されています。

[現行 helper](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2344-impl/orchestrator/tests/test_layer3_report.py:560) は62以外で `assert grammar == 24` を実行します。許可された param 変更だけでは、追加する63ケースがここで必ず失敗します。裁定どおりの実装には、この helper の63分岐追加も編集許可へ含める必要があります。

## 現行の受理・拒否と scope

静的確認では、通常 decoder の v2 authority grammar は exact-63、歴史 decoder は63・62・24です。通常 decoder は62・24を拒否し、v1には別の既存処理があります。

裁定後は通常 v2 を85のみとし、63・62・24は歴史専用になります。旧63成果物は最新 checkout の certified consumer で拒否されます。scope 更新は未実装です。

## 変更ファイル・新設 node・検査結果

- 変更ファイル、新設・改名 node：なし。
- テスト、直接呼出し、検査除去による変異確認：未実走。
- `contract-loader-drift` による観測赤：0件。テスト未実走のためであり、問題がないことを示しません。
- meta-test の網羅的洗い出し・実走：停止に伴い未実施。
- commit・branch・index 操作：なし。

## 固定値・byte 一致確認

固定 known-answer 4件の独立算出、および旧 scope と新設定数の byte 一致検証は未実施です。新設定数もまだありません。

裁定の算出規則は確認しました。index は1始まり、fixture bytes は ASCII の `epoch closure fixture {index}\n`。epoch は domain `campaign-verifier-epoch/v1` に宣言順の UTF-8 path、NUL、fixture の32-byte SHA-256 digestを連結して SHA-256 を取ります。path hash は宣言順の UTF-8 path＋NUL の連結から算出します。

## 波及の確認範囲

直接確認した波及先は、上記 helper を共有する layer3 の歴史 report、certified 拒否、authority HEAD fallback の3系列です。いずれも63 param追加には helper の追随が必要です。

所有外 caller・共有 fixture・consumer test 全体の静的列挙は未完了です。

## 総括

実装前停止・変更なしです。
裁定は helper の63分岐追加を要求しますが、今回の編集制限はそれを許可していません。
この不一致を独自解釈で解消せず、報告しました。
実装・テスト・固定値検算は未完了です。