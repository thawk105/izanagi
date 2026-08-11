F1〜F3 を指定の 2 ファイルだけで実装しました。親の docs 差分は保持し、manifest・git index・commit には触れていません。`git diff --check` は成功しています。

F1 では `check_docs.py` と同じ判定を採用し、backtick info 内の backtick を無効として fail-closed にしました。無効 opener 周辺は本文候補になりますが、`_read_design()` が extractor へ返す前に拒否するため、余分な表や anchor が権威内容として読まれる経路はありません。tilde info 内の backtick は引き続き許可します。

F2 では空行 terminator を closer より前に保持しました。静的確認上、現実装では表全体が fence 除去されて `missing or duplicated`、raw-text mutant では空行で表抽出が終了して closer が row に混入せず、canonical 表が正常受理されます。

指定テストは `qstat -Q` preflight の dispatch infrastructure failure（rc=16）で pytest 起動前に停止しました。

## 総括

- F1: 対応済み — 無効な backtick info opener を fail-closed で拒否
- F2: 対応済み — §7.5 の削除型 2 node を受理集合差による真の KILL へ修正
- F3: 対応済み — 無効 opener の陰性 node と tilde info の陽性 node を追加
- この 2 巡目の修正で新たに受理されるようになる入力: なし
- 追加 nodeid: `test_design_invalid_backtick_info_decoy_is_rejected`、`test_design_tilde_fence_info_may_contain_backtick`
- 更新 nodeid: `test_design_revocation_table_only_in_tilde_fence_is_rejected`、`test_design_revocation_table_only_in_long_backtick_fence_is_rejected`
- 走らせた nodeid と結果: 2 ファイル全体を指定したが dispatch preflight rc=16 のため 0 node 実行、実装済み・未実走