実装は指定された 2 ファイルだけに反映しました。

- [p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/campaign/p3_b4_closed_critic.py:291)
- [test_p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/tests/test_p3_b4_closed_critic.py:929)

主な変更は以下です。

- pair 検査を dataclass 受理から terminal receipt path 再読へ変更。
- start、payload、envelope、argv、WAL、loop state、prompt、executable、neutral root、closure の hash を bytes から再検証。
- factory 固有 `pair_id` を start/terminal receipt に記録。
- certified executable は固定名 `claude` の PATH 解決に限定。CLI の executable 指定を削除。
- query 前に terminal file descriptor を排他予約。
- closure manifest に admission、prediction runner、session isolation、identity projection を追加。
- JSON escape の二重 decode を廃止し、空白を含む引用 path を正規化。
- CLI の factory seam と実駆動テストを追加。
- M6/M7/M8/M9/M11 を登録名から外し、M16〜M20を追加。
- 非採用 2 件は実装せず、同一 process 改変、WAL/state 論理世代、storage failure などを非保証 field に明記。

所有外への波及を `rg` で静的確認した結果、対象 2 ファイル外からの直接 caller、共有 fixture、consumer test はありません。動的 caller が存在する場合、`assert_b4_arm_pair` の path API 化と CLI の `--claude-executable` 削除が互換性影響になります。既存の `orchestrator/tests/test_p3_s4_loop.py` の変更は作業開始前から存在し、今回は触れていません。commit、add、stash、branch 操作も行っていません。

## 総括

### R1〜R12

|裁定|状態|対応|
|---|---|---|
|R1|closed|terminal path を再読し、exact schema/status、start/payload/envelope/argv/snapshot等を bytes 再検証。昇格 dataclass と terminal 書換えを負例化。|
|R2|closed|certified は固定名 `claude` を解決。caller executable は無視し、CLI option を削除。|
|R3|closed|[M16テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/tests/test_p3_b4_closed_critic.py:968)で実送信 payload を捕捉し、各 admitted view から独立計算した on/off digest と byte 比較。marker の on 出現/off 不出現も固定。|
|R4|closed|num_turns、permission_denials、server_tool_use を各 1 field の正負対へ分離し、理由を exact 検査。|
|R5|closed|WAL、loop state、argv、送信 digest、payload、start receipt の期待 hash をテスト側で独立再計算。|
|R6|closed|実 invocation 前後の loop-state bytes と campaign tree を比較。artifact root の proposal/checkpoint 不在も確認。|
|R7|closed|main を fake factory で駆動し、2 invoke、pair gate、stdout receipt path、成功/失敗 rc を検査。|
|R8|closed|closure へ最低 3 依存と identity renderer を追加。全 entry の path/contract bytes 対応表をテスト側に独立定義。|
|R9|closed|JSON decode を一度だけにし、引用された空白 path を処理。実 JSON escape alias の負例と説明用 escape の正例を追加。|
|R10|closed|各応答文字列、exact bool、空 digest、未知/non-str result を 1 field ずつ検査。|
|R11|closed|terminal slot を query 前に予約し、start 書込みを try 内へ移動。start failure terminal と storage 非保証を追加。|
|R12|closed|module/fixture 表示を縮小し、tool、trust、snapshot、storage の非保証を receipt に明記。|

### 改訂後の変異 15 件

|変異|状態|単一理由性の静的確認|
|---|---|---|
|M1|closed|campaign_id literal gate のみ。|
|M2|closed|repository root literal gate のみ。|
|M3|closed|campaign path literal gate のみ。|
|M4|closed|artifact 作成前の module-root equality のみ。|
|M5|closed|runner identity gate のみ。後段 resolver は正例化して隔離。|
|M10|closed|response exact-key gate のみ。dataclass は明示 field 構築とし、余剰 key の後段拒否を除去。|
|M12|closed|raw/decoded view に exact root が無い parent aliasを normalized view のみが拒否。|
|M13|closed|receipt raw-envelope evidence field/hash 検査のみ。|
|M14|closed|failure terminal writer の必須性のみ。|
|M15|closed|独立 closure 対応表の provider entry のみ。|
|M16|closed|実送信 off payload と独立 off digest の byte 比較のみ。|
|M17|closed|個別 receipt 検証後、pair_id equality を最初の pair 混成理由として検査。|
|M18|closed|caller decoy executable が evidence/argv に影響しないことのみ。|
|M19|closed|terminal path 必須性。test-only dataclass の文字列昇格は受理不能。|
|M20|closed|独立 closure 対応表の artifact_admission entry のみ。|

M6/M7/M8/M9/M11 は登録名から除外済みです。関連する防御確認は `test_unregistered_*` として残しています。

テスト実行状況:

- 対象範囲: `orchestrator/tests/test_p3_b4_closed_critic.py` 全体
- 試行 1: `python3 tools/run_tests.py orchestrator/tests/test_p3_b4_closed_critic.py -q`
- 試行 2: 同範囲を `--force-dispatch`
- 両方とも `qstat -Q preflight rc=1`、wrapper rc=16、`child_started=false`
- 実際に走った pytest nodeid: なし
- 静的に確認した test 関数数: 37
- 静的検査: 両 Python ファイルの `compile()` 成功、diff whitespace 検査成功、登録集合と外部 caller 検索済み

残した赤は pytest assertion ではなく、計算ノード dispatch infrastructure の rc=16 です。全 37 nodeid、関連全走、docs/Codex checker は未実走であり、緑とは報告しません。