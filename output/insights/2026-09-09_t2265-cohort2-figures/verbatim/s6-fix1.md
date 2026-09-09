## 直したもの

- [submit_t2265_perf6.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh)
- [wait_t2265_perf6.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh)

指定された2本以外のrepo内fileは変更していません。7本のcell literalと60分walltimeは変更していません。

## F1..F11 の対応表

| 項目 | 対応 |
|---|---|
| F1 | `qstat -f` を廃止。pollごとに`qstat`一覧を1回取得し、行頭RequestIDとSTT列を解析。既知語彙は `tools/mutation_fanout.py` の正規化から `QUE`・`HLD`・`RUN`、親の実測から `PRR`。未知状態、qstat非0、header欠落はrc=4で停止 |
| F2 | terminal時はJSONを`present`または`missing`として記録し、欠測があっても残るjobを監視。全terminal後に全7行inventoryを出力。全presentはrc=0、missingありはrc=6 |
| F3 | qstat失敗、parse失敗、未知状態、timeoutの各経路で、その時点の全inventoryをstdoutへ出力 |
| F4 | 台帳読取直後に行数7、rep 0..6が各1回、job ID相異を検査。partialでも記録済みjobを最後まで監視し、最終rc=7。再投入処理なし |
| F5 | `IZ_MAX_WAIT_S` の既定を21600秒へ変更し、queue待ち余裕の根拠をコメント化 |
| F6 | `set -o noclobber`を維持し、台帳作成と全metadataを単一のcreate-only redirectへ統合 |
| F7 | qsub受理後のID検査、時刻取得、台帳追記が失敗した場合、`*** ACCEPTED JOB MAY BE UNRECORDED ***` とjob IDをstderrへ表示 |
| F8 | `IZ_DESIGN_PATH`を必須化。指定commitの実在確認と、指定pathのblob SHA-256一致を投入前に検査。台帳へ`design_path`も記録 |
| F9 | 7回それぞれのqsub直前にsubmit treeのHEADとtracked-cleanを再検査 |
| F10 | `IZ_LEDGER`をcanonicalな `/home/SFC/tanab/.claude/jobs/` 配下の絶対pathに限定 |
| F11 | 入力検査より先に`command -v qsub`を実行し、不在時はrc=2 |

## 自分で走らせた検査

- `bash -n submit_t2265_perf6.sh`: rc=0
- `bash -n wait_t2265_perf6.sh`: rc=0
- qsub不在PATH: rc=2
- `IZ_LEDGER`未設定: rc=2
- 許可外ledger path: rc=2
- `IZ_DESIGN_*`未設定: rc=2
- 存在しないdesign commit: rc=2
- design SHA-256不一致: rc=2
- 既存ledger: rc=2
- 偽NQSVによる段階的6-of-7: rc=6。最初のmissing後も残る6本を待ち、2 pollにつきqstat呼出しは2回
- 未知STT `MYSTERY`: rc=4、全7行inventoryあり
- qstat自体がrc=17: waiter rc=4、全7行inventoryあり
- header欠落: rc=4、全7行inventoryあり
- 全7本live、待機上限0秒: rc=5、全7行inventoryあり
- 3行partial台帳: 記録済み3本をterminalまで監視後rc=7
- 7行だがjob ID重複: 全行監視後rc=7
- 全7本terminalかつJSON present: rc=0、全7行inventoryあり
- `git status --short --untracked-files=all`: rc=0、出力なし

一時fixtureは削除せず、`/tmp/t2265-perf6-tests.5BwI21` に残しています。

## 未実走・限界

- 禁止に従い、実機qsub、job投入、性能測定は実行していません。
- 実NQSVへのwaiter接続は行わず、提示された実測形式を再現した偽qstatで検査しました。
- qsub受理後の台帳追記失敗経路は、投入禁止および許可されたledger rootがsandbox外であるため未実走です。
- JSONの168点完全格子とidentityは検査していません。裁定どおり親の責務として残しています。

## 波及可能性

- submit実行側は新たに`IZ_DESIGN_PATH`を渡す必要があります。
- 台帳には`design_path` metadata行が増えます。waiterは`columns`行までmetadataを読み飛ばすため整合します。
- 呼出し側は新しい集約rcとして、missingのrc=6とpartialのrc=7を扱う必要があります。
- 未知のNQSV STTは意図的に監視エラーになります。

## 総括

F1〜F11を指定された2本だけで反映し、構文、preflight拒否、NQSV一覧解析、fail-closed、timeout、partial台帳、6-of-7と全presentを偽環境で確認しました。qsubは一度も実行していません。