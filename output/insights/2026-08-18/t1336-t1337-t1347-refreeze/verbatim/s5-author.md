## 総括

指定されたテストファイルの逐語 2 箇所だけを更新しました。docs、production コード、歴史 record は変更せず、commit もしていません。

### 変更内容

- [test_s8c_preregistration_core.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/tests/test_s8c_preregistration_core.py:56)

  - 変更前: `"対象別 between-run floor (H1 / H2)"`
  - 変更後: `"反復単位対比の判定パラメータ (H1 / H2: n・平均差の下限・差の標本 SD の上限)"`

- [test_s8c_preregistration_core.py:585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/tests/test_s8c_preregistration_core.py:585)

  - 変更前: `"4d082de6c6a19691dd8bad27127e9ebb03fdacc500aab555310c7883b7ba2635"`
  - 変更後: `"8ad36ad81439089be797c43133ce19b6082c0a9a3e21f6ead43b079f4c22107e"`

tuple は順序を維持した 9 要素のままです。

### hash の導出

production parser で次の両方を解析しました。

- 実文書 bytes: `8ad36ad81439089be797c43133ce19b6082c0a9a3e21f6ead43b079f4c22107e`
- 更新後の `_markdown()` fixture: `8ad36ad81439089be797c43133ce19b6082c0a9a3e21f6ead43b079f4c22107e`
- 一致: `True`

### `FIELD_NAMES` の全参照

同ファイル内の全出現は 10 箇所です。

- 定義: 53
- 全要素の fixture 合成: 68
- 集合全体との比較: 444
- 添字参照: 469、626、627、629、1224、1225、1228

添字参照は `[0]` または `[1]` だけです。今回変更した要素は `[2]` なので、追加追随は不要です。

### 旧 literal の全件検索

旧欄名は live なコード、docs、テストには残っていません。所有外の歴史資料には次が残っています。

- [ruling.md:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/output/insights/2026-08-03_t296-layer-c-calibration/ruling.md:139)
- [mutation-ledger-run4.json:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/output/insights/2026-08-16_t1186-decider-version/mutation-ledger-run4.json:315)、同 451
- [mutation-ledger-run3-probe.json:758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/output/insights/2026-08-16_t1186-decider-version/mutation-ledger-run3-probe.json:758)、同 942

旧 hash は除外指定の g1〜g5 各 line 1 に残っています。また、過去の逐語記録にも残っています。

- [s2-plan.md:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/output/insights/2026-08-16_t1132-t1134-prereg-contract/verbatim/s2-plan.md:139)
- [s3-lensB.md:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/output/insights/2026-08-16_t1132-t1134-prereg-contract/verbatim/s3-lensB.md:62)

これらは変更していません。

### 検査結果

実装済み・未実走です。

次の 2 nodeid を正規 runner へ投入しましたが、Pegasus の queue 事前確認が `rc=1`、runner が `rc=16` となり、テスト子は開始されませんでした。

- `test_current_markdown_extracts_nine_fields_and_conditions_1_to_12`
- `test_normalization_v2_conformance_corpus`

`git diff --check` と、文書・fixture の hash 一致確認は成功しています。runner が生成した今回限りの未追跡 dispatch ファイル 4 件は除去済みで、再生成可能です。

### 所有外への波及可能性

- production parser は欄集合と hash を汎用的に導出するため、コード変更は不要です。
- `_markdown()` は同ファイル内の多数のテストが共有しますが、外部からの import はありません。
- [test_s8c_preregistration_invariant.py:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/tests/test_s8c_preregistration_invariant.py:152) は最新 freeze record と実文書の hash 一致を検査します。g1〜g5 は旧 hash の歴史 recordとして不変なので、親側の新世代 refreeze が downstream の整合点になります。
- 同 invariant の世代間比較は既存世代同士の歴史的一致を検査するため、今回の worker では変更対象にしていません。