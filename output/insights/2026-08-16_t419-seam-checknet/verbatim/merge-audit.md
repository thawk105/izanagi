## 総括

- 判定: 合成は正しい。修正は不要です。
- wave 側と main 側の全差分が両ファイルに残っています。
- 重複定義・重複 import はありません。
- floor protocol API の食い違いはありません。
- fixture のインターフェースも両親で一致しています。
- ファイル編集、docs 編集、commit は行っていません。

監査結果:

1. 消えたハンク: 問題なし  
   merge-base から各親への差分と、反対側の親から staged 合成結果への差分の stable patch-id が、両ファイル・両方向ですべて一致しました。

2. 重複定義・重複 import: 問題なし  
   top-level 関数・クラス・定数名と import を検査し、重複は 0 件でした。

3. API の食い違い: 問題なし  
   [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/campaign/s8b_floor_campaign.py:882) の resolver は、現行の `scan_floor_protocol_index`、`IndexedFloorProtocol`、`_FLOOR_PROTOCOL_REL`、`validate_protocol_against_current` の signature・戻り値と整合しています。呼び手の indexed SHA 再照合も維持されています。

4. テストの前提: 問題なし  
   [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/tests/test_campaign.py:4983) の追加 2 テストが使う `build_admission_fixture` の公開属性と signature は両親で一致しています。

編集: なし。指定 2 file に unstaged 差分もありません。

テスト: 次の 2 nodeid を `tools/run_tests.py` で試行しましたが、`qstat -Q` の前処理失敗により rc=16 で停止しました。実装済み・未実走です。

- `test_floor_admission_uses_authority_resolver_not_legacy_literal`
- `test_floor_admission_rejects_disk_bytes_different_from_index_record`

判定: 合成は正しい。