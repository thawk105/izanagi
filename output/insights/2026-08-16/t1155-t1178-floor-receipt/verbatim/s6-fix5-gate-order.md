## 先取りの診断

1. resume 回帰  
   [s8b_floor_campaign.py:5676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5676) の共有 manifest validator が、既存の `protocol sha256` 検査を先取りしていました。期待 regex は [test_s8b_floor_campaign.py:5267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_campaign.py:5267) です。

2. `binary-cell-binding` 回帰  
   共有 manifest validator が、[s8b_ratified_freeze.py:1663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:1663) の cell identity 検査を先取りしていました。

3. `binaries-cell-set` 回帰  
   同じ共有 validator が、[s8b_ratified_freeze.py:1648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:1648) の binary/cell 集合完全一致検査を先取りしていました。両 cause の期待は [test_s8b_ratified_verify.py:1452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_verify.py:1452) に維持されています。

4. `schema-keys` 回帰  
   [s8b_floor_stats.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_stats.py:637) の共有 result v4 exact-key 検査が先にエラー文字列を返し、[s8b_ratified_freeze.py:3115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3115) で `floor-projection` に変換されていました。そのため既存の `schema-keys` 検査へ到達していませんでした。期待 cause は [test_s8b_ratified_verify.py:1417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_verify.py:1417) のままです。

## 選んだ解決

cause 細分化ではなく、順序入れ替えを選びました。各 validator 間に先行必須のデータ依存はなく、拒否条件の論理積を保ったまま具体診断を先に返せるためです。

canonical authorization は既に、ratified では具体検査後の [s8b_ratified_freeze.py:2107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:2107)、resume では重複・schedule・retry 枠検査後の [s8b_floor_campaign.py:5916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5916) にあり、追加移動は不要でした。

## 直した内容

- [s8b_floor_campaign.py:5671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5671)
  - `protocol_sha256` と `freeze_sha256` の既存検査を共有 manifest validator より前へ配置しました。
  - 共有 validator は [同:5675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5675) に残り、通過入力では必ず実行されます。

- [s8b_ratified_freeze.py:1829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:1829)
  - `_validate_portable_binaries` を共有 manifest validator より前へ移しました。
  - 共有 validator は [同:1833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:1833) に維持しています。

- [s8b_ratified_freeze.py:2208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:2208)
  - ratified 固有の top-level exact-key 検査を helper 化しました。
  - [同:3082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3082) で共有 live verifier より先に実行します。
  - `_validate_result` 内でも [同:2220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:2220) から同 helper を呼び、単体 validator の厳格性も維持しました。

## 受理集合が不変である根拠

各順序変更は同じ必須検査の並び替えであり、通過条件は変更前後とも全検査の論理積です。

- result v4 の余分 key  
  [s8b_ratified_freeze.py:2208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:2208) で依然 `schema-keys` 拒否され、共有側の [s8b_floor_stats.py:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_stats.py:642) も残っています。

- manifest v3 の semantic 不正  
  campaign の [s8b_floor_campaign.py:5675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5675)、ratified の [s8b_ratified_freeze.py:1833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:1833)、holdout freeze の [s8b_holdout_freeze.py:1427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1427) で引き続き拒否されます。

- 正準でない attempt ID  
  planned は [s8b_floor_contract.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_contract.py:159)、retry は [同:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_contract.py:170) で再導出・拒否されます。validator と全 caller は未変更です。

- completed-only fallback  
  [s8b_holdout_admission.py:1841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1841) の completed→start coverage 必須分岐は未変更で、fallback は復活していません。

## positive control 16 件と fix1〜3 への影響

fix4 の16 nodeidはすべて未編集です。

- `test_s8b_holdout_freeze.py`: 4関数、parameterized 5 nodeid  
  1461、1485、1505の `empty` / `v2`、1522。
- `test_s8b_holdout_admission.py`: 6 nodeid  
  836、851、872、910、940、963。
- `test_s8b_floor_contract.py`: 4 nodeid  
  256、268、280、295。
- `test_s8b_floor_stats.py`: 1 nodeid  
  605。

fix1〜3についても、attempt ledger/marker の双方向完全一致分岐 [s8b_holdout_admission.py:1909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1909)、[同:1953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1953)、root 非依存性テスト [test_s8b_floor_campaign.py:6787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_campaign.py:6787)、portable/runtime exact-key 分離 [s8b_binary_admission.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_binary_admission.py:68)・[s8b_floor_campaign.py:3556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:3556) は未変更です。producer の出力 bytes を作る処理にも変更はありません。

静的確認では、変更2ファイルの AST parse、NFC、結合文字不在を確認しました。pytest・`tools/run_tests.py` は指示どおり実行しておらず、緑とは申告しません。テスト、docs、`freeze_verification_hold.py`、`output/` は編集していません。git 操作、commit、Web 検索も行っていません。

## 総括

先取りの構造: 共有 validator が、同じ不正をより具体的に説明する既存検査より先に発火し、cause/message を汎用値へ潰していました。

選んだ解決: validator は削除・条件化せず、既存の具体検査を先行させる順序入れ替えを行いました。

受理集合が不変である根拠: 必須拒否分岐はすべて残り、順序だけが変わっています。余分 key、manifest semantic 不正、非正準 attempt ID、completed-only の全4種は依然拒否されます。