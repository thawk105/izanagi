## 所見一覧

**must-fix 0 件、real / nit 1 件。** 静的検査では、実装と plan v2 の不一致、既存テストの期待値変更、変異期待集合の追加漏れは見つかりませんでした。pytest・変異走行は実施していません。

- **real / nit：commit message の「cells を消して C02 を足すだけ」は操作の省略が強い。** 実際には report hash 更新に加え、N3 は v2 から v5 への更新と cross-binding・attempt registry の構築を行っています。「参照 hash 等を整合させた上で」と補足すると正確です。根拠：`impl-29b0f70d7.patch:9`、`test_s8c_acceptance_receipt_v2.py:985`、同 `:492`。実装の受理集合を変える問題ではありません。

## 既存テストへの波及

指定の 4 パターンで `orchestrator/tests/` を検索し、該当する 4 ファイルを確認しました。

- **refuted：既存の空 cells 負例の期待文言が変わる。** 既存 E は complete・cells=[]・C02 欠落ですが、mandatory-reasons が新判定より先に拒否します。根拠：`test_s8c_acceptance_receipt_v2.py:906`、`s8c_acceptance_receipt.py:2039`。
- **refuted：trial registry の complete fixture が新たに拒否される。** `_base_report` は一時的に complete・cells=[] ですが、検証へ届く complete fixture は descriptor 付き cell を設定します。build 正例も cell を保持しています。根拠：`test_trial_registry.py:560`、同 `:1055`、同 `:1652`、同 `:1841`。
- **refuted：layer3／旧 receipt fixture が新判定に巻き込まれる。** 実 verifier に渡す両 fixture は v1。`rederive_arm_execution` の対象外です。根拠：`test_layer3_report.py:632`、`test_s8c_acceptance_receipt.py:98`、`s8c_acceptance_receipt.py:1999`。
- **refuted：既存の partial 正例が m2 でも追加で赤になる。** 既存 mixed-terminal 正例は descriptor を保持します。status 反転だけでは新条件を満たしません。根拠：`test_s8c_acceptance_receipt_v2.py:426`、同 `:1375`。

## 変異事前登録の成立性

N2＝追加 parametrized 負例、N3＝descriptor 隠蔽負例、P＝追加 partial 正例、E＝既存 C02 欠落負例です。

| 変異 | 静的に予測する赤 node 完全集合 | 判定 |
|---|---|---|
| m1 | N2[v2]、N2[v5]、N3 | refuted：登録漏れなし |
| m2 | N2[v2]、N2[v5]、N3、P | refuted：既存 partial node の追加失敗なし |
| m3 | N2[v2]、N2[v5]、N3 | refuted：登録漏れなし |
| m4 | N2[v2] | refuted：N3 の最終検証は v5 |
| m5 | E | refuted：診断順 pin という登録と一致 |
| m6 | なし（SURVIVED） | refuted：非等価ではない |

根拠：`test_s8c_acceptance_receipt_v2.py:906`、同 `:931`、同 `:962`、同 `:1002`、`s8c_acceptance_receipt.py:2039`。

文字列計数と AST 解析で以下も確認しました。

- m1／m4 は `if rederive_arm_execution and any(` を含む行、m2／m3／m6 は `trial.status == "complete"` を anchor にすると、それぞれ source 全体で **1 件**です。裸の `rederive_arm_execution` や `"complete"` の全体置換は使わないでください。
- m5 は隣接する mandatory ブロック＋新ブロックを old、逆順を new とする **一意の置換**で表現でき、置換後も構文解析できます。
- m6 の status は JSON から得た文字列です。文字列同士の等値比較の左右交換なので等価です。根拠：`s8c_acceptance_receipt.py:911`、同 `:918`。

m5 の E は「C02 欠落」と「complete の descriptor 不在」を同時に満たします。単独の受理条件を検出する変異とは扱えませんが、裁定 `s4-adjudication.md:76` は既に診断順 pin と限定しています。その他の変異に、静的に別理由の失敗は見つかりませんでした。完全集合の実測確認は未完了です。

## 記述の正確さ

- **refuted：「v5 では current capability まで届いていた」がコード上成立しない。** 新判定以前の verifier 通過後、current capability は v5 と同一 bytes の再検証を要求します。裁定の C2/C3 実測記録と整合します。ただし、このレビューでは元の実測ログを独立確認していません。根拠：`s4-adjudication.md:23`、同 `:30`、`s8c_acceptance_receipt.py:2096`。
- **refuted：partial 正規形の受理維持という主張が過大。** P は partial・C02 保持・certifying=False・current capability を確認します。no-build leaf は status を含まないため、helper 内の status 更新順にも矛盾はありません。根拠：`test_s8c_acceptance_receipt_v2.py:1002`、`autonomous_trial_completeness.py:4165`。
- **refuted：「実行を名乗らない」や certified 成果物到達の過大主張。** 対象 commit message にその主張はありません。変更対象は complete と descriptor 証明の対応です。
- **refuted：D519／D1757／D949 違反。** partial 許容を維持し、legacy に campaign 現物の追加要求をせず、既存 gate では排除できなかった complete・cells=[]・C02 を拒否します。legacy v2〜v4 のこの形の受理集合は狭まります。根拠：`rulings-verbatim.md:9`、同 `:78`、同 `:93`、`s8c_acceptance_receipt.py:2053`。

## scope 外候補

新たに報告する実在問題はありません。

**refuted：scope 膨張。** 全差分は production の 8 行と test の 3 関数・4 node の追加だけです。既存 helper・期待値・duration 台帳・conftest・`test_ccbench_spawn_sites.py` に変更はなく、subprocess 呼出し箇所も増減していません。根拠：`impl-29b0f70d7.patch:22`、同 `:41`。

## 総括

静的レビュー上、実装の修正要求はありません。記述 nit は「だけ」に省略された再ハッシュ等の明確化です。m1〜m6 は登録どおり成立すると判断しますが、期待 node 完全集合と受入結果の確定には、親による実走結果が必要です。