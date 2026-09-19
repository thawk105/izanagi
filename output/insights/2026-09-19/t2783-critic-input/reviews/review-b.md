## 総括

**GO（静的レビュー範囲）。mustなし。** 基点との差分と未commit文書、指定author生成adapterを確認しました。pytest・変異は実行していません。

- **must: 0件。** production追加は85行で既存module内に収まり、汎用化・評価ゲート追加・既存テスト弱化はありません。builderのK2／非B4／reflux on限定と、両入力への診断転写は裁定に整合しています。
- **should / real:** [brief.md:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/brief.md:2) の「届かず20を再提案」は因果を示唆し、同:7の「最小」も無限定です。裁定とnext-run-planでは既に適切に限定されています。briefには「未送達と20再提案は別観測」「既存抽出器を再利用する局所案」と短く追補すれば十分です。
- **nit / real:** [agent_outputs.py:3](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2783-critic-input/orchestrator/campaign/agent_outputs.py:3) の「入力射影はこのmoduleをimportしてはならない」は、今回の純粋抽出関数の再利用と説明が合いません。「AO記録を読まない。明示bytesの抽出は可」へのコメント修正で足ります。module分割は不要です。

**検証経路:** M1〜M6は、builder転写・coder転写・型検査・K2限定・CLI転写・AO読取りという実際の追加経路を狙っています。ただし提示資料は変異候補／期待結果であり、KILLED実績としては数えません。role本文の文字列検査も、実roleの受領・採用の証明ではありません。runbookはこの限界を明記しています。

**refuted:** 白板拡張、static schema／manifest修復、新launcher・receiptの追加を必須とする指摘。指定adapterの変更は本文・source pin・派生digestに限定され、schemaとruntime境界は維持されています。旧adapter mismatchと既知originless hash候補は、新規mustに数えていません。

次走計画は同機体・同jobのstock対照を含み、予算未確定・3巡目未認可・因果未証明を保っています。本GOは親の残りの実走検証を代替しません。