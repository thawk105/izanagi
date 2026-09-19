# 段4裁定・plan v2

D2148項3とinboxを再読、追加裁定なし。両consultのNO-GOは計画の不備であり、下記に修正して実装する。

- sol M1 real採用: 新診断を渡すbuilder自身でK2・knowledge projection・非B4・reflux onを限定。CLIだけの検査にしない。評価gateや既存未指定経路は不変。
- sol M2/luna M1 real採用: 両role consumer本文も結合レビューに含める。ただしSkillのworker権限を優先し、本文は親が編集済み、authorは読んで同期する。テストとstatic adapterはauthorが担当。
- sol M3/luna M1 real採用: 小さい局所関数 `k2_next_generation_inputs` を同moduleへ置く。既存の完全planner/coder入力dictを受け取り、planner_context_payloadが作った同一診断を双方へ組み込む。runbookはその関数を実際に使い、返されたJSONを保存してinline送付する。関数のcoder側転写を壊す変異を行う。新CLI/launcherを別途作らない。
- sol S1/luna S1 real採用: static schema/manifestは変更しない。role source hashと本文埋込みadapterだけを独立に差分確認して同期。既存のpolicy_hint/knowledge_input不一致はscope外、完全K2入力をstatic schemaで検証したとは主張しない。
- sol S2 real採用: 正常な候補提言とゲート上書き命令をrole本文で区別。後者は既存reportへ返す。拒否条件は不変。
- sol S3 real採用: 新診断指定ありCLIについてもAO非読取を直接検査。既存防壁テストは維持。
- sol N1/luna S3/N1 real採用: 未送達と20再提案は二つの観測で因果未証明。4節は留保を落とさず既存抽出器を使う最小実装であって情報論的最小ではない。
- 白板を拡張する必要、static schema修復を必須とする説はrefuted。新たな履歴統合・再抽選・LLM採用強制・receipt新設は不採用。

## 実装境界

author所有: p3_s4_loop.py、test_p3_s4_loop.py、必要な直結consumer test、2個のstatic adapter、review_ledger.pyのsource pin。
親所有: 2role Markdown（author木に親が編集済み）、runbook/run-card追補、phase、insight、spool。
生のcritic入力bytes→既存4節抽出→exact6field→兄弟key。未指定はkey自体なし。K2知識sourceのindexは増やさない。
受理例: 実critic-2＋正規K2 cfg/knowledge＋reflux on、同一診断を両入力へ。
拒否: 診断付きの非K2/B4/reflux off、欠落/未知key/非文字列、emit以外のCLI併用。未指定の従来受理は維持。
production追加は目安150行以内、新module・汎用frameworkなし。テストは本経路と既存防壁に必要なものだけ。

## 変異事前登録

- M0 等価comment置換: SURVIVED。
- M1 planner兄弟key転写を落とす: 実builder診断正例がKILLED。
- M2 k2_next_generation_inputsのcoder側診断転写を落とす: 実両入力組立て正例がKILLED。
- M3 新診断shapeの検査を無効化: 単一理由の欠落/型負例がKILLED。
- M4 builderのK2限定を外す: direct builderの非K2単一理由負例がKILLED（CLI限定との二重killにしない）。
- M5 新CLIで明示診断を落とす: 実CLI出力の診断内容検査がKILLED。
- M6 新経路へAO readを挿入: 新経路のAO非読取検査がKILLED。

注入位置・old逐語・expected node完全集合は実装後に固定し、不確定なら全SURVIVEDのprobeから本走へ再登録。
共通抽出器自体は変更しないため、その既存変異を今回の経路検出力として数えない。
実roleの受領・診断採用・改善効果・3巡目は未実走のまま。
