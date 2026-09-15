## 裁定からの逸脱

**refuted / scope 内**：逸脱なし。統合差分は現物の `git diff` および実装子のpatchと一致する103行。本体変更は6283–6284行の `except CampaignAbort: raise` 追加だけで、テストは指定位置への2本追加のみ。scope外の実装はない。

## 停止の伝播

**refuted / scope 内**：当該abortを飲む層は見つからない。

- `CampaignAbort` 節は `RuntimeError`／`TimeoutExpired` 節より前。
- bare `raise` により元の例外オブジェクトを再送出する。
- 通常・retry・再開の `_run_session` 呼出しから `runner.run()` まで、当該例外を捕捉して継続する節はない。
- 7957–7963行で `terminal/status=aborted` と元の理由をjournalへ書き、再送出する。post-probe、失敗session生成、結果組立には進まない。

## 受理集合の変化

**refuted / scope 内**：受理を広げる変更はない。certified経路は6259行で早期returnし、追加節を通らない。最終inspectionの条件も未変更。

厳しくなるのは非certified経路で測定callbackから `CampaignAbort` が出た場合の実行継続条件だけ。plain `RuntimeError`、`TimeoutExpired`、非abortの `FloorCampaignError` は従来の処理に残る。

## 既存テストの改変

**refuted / scope 内**：既存テストの削除・改名・緩和・skip化なし。

HEADとの比較で、トップレベルの既存テスト359本すべてが残り、追加後は361本。既存関数・クラスのASTも不変。新設2本以外のテストへの変更はない。

## 実装子の報告との照合

**refuted / scope 内**：静的に照合できた内容に食い違いなし。新設位置9914・9962行、103行patch、対象2ファイルが一致する。報告に挙がる全関数nodeidと自走harnessファイルは存在する。

**不明 / scope 内**：runnerのrc=16と子未起動という実行履歴は、独立したログで裏付けていない。ただし報告はテスト・収集・変異検査を明確に「未実走」としており、緑の偽装はない。本レビューでもpytestは実走していない。AST解析と `git diff --check` は成功した。

## 親の裁定への反証

**refuted / scope 内**：継承関係、節の順序、certifiedの早期return、retry枠の消費に関する判断は現物と整合する。裁定の変更箇所以降の行番号は実装前基準で、統合後の＋2行は自然な移動。

**real / scope 外**：冒頭33–34行と測定直前コメントの「例外経路でもpost-probeを必ず実行」は、今回のabort経路には成立しない。裁定が既に認めた不一致である。

**real / scope 外**：runner・launcher内部には広い例外捕捉が残る。「どこで発生したabortでも停止する」とは一般化できない。今回のwrapperからの伝播を妨げるものではない。

## must-fix と nit の仕分け

- **must-fix：なし。**
- **nit：real / scope 外**のpost-probeコメントの不一致。裁定どおり変更対象外。
- **未確認：不明 / scope 内**の回帰・meta-test・M1〜M3実走結果。静的整合性だけでは実走成功を認定できない。

## 総括

**refuted / scope 内**：指定範囲の実装不備は見つからず、静的レビューでは裁定に忠実。停止伝播と受理集合の変更方向も意図どおり。テスト・変異検査の実走成否は未確認。