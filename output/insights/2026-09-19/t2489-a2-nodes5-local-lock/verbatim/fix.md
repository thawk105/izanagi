所有2ファイルの試作部分を撤去しました。

- `tools/pegasus/paper_story_a2_certification.sh`：候補exportを削除。基準`7975385b55a2e3451f6c80d584a9312f44d5199d`と全12,307 bytes一致。
- `orchestrator/tests/test_paper_story_a2_job_contract.py`：候補専用harness・wrapper・継承testを撤去。5node既定fixture、A2/A6 nodefile負例、`qsub -b 5`期待を保持。

基準とのtest関数名比較では追加・削除なし。新設・改名なし。`git diff --check`成功。

所有外への静的影響は、A2/A6 policyの共通job-body参照、submitter、認証test、hooks/admission登録、実行時間台帳です。これらとprobe 2ファイルは未変更。単一node専用fixtureも保持しています。

| 所見 | 状態 |
|---|---|
| 候補export・専用試作の撤去 | 実装済み・未実走（partial） |
| 5node受理・既存拒否理由・認証条件の維持 | 静的確認済み・親の実走待ち（partial） |

## 総括

テストは指示どおり未実走で、緑・closedとはしていません。docs編集、git add/commit、qsubは行っていません。親docsに起因する期待赤はありません。
