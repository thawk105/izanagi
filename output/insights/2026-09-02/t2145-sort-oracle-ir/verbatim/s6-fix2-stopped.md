## 停止理由

指定どおり、期待値側の誤りを確認したため実装を変更せず停止しました。

- [test_p3_s4_loop_sort.py:960](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix2/orchestrator/tests/test_p3_s4_loop_sort.py:960) は comparator を使う前に旧 campaign ID `081dd46f` を要求します。
- 現行 ID は実走ログどおり `42c83ea9` です。
- [p3_s4_loop_sort.py:317](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix2/orchestrator/campaign/p3_s4_loop_sort.py:317) は段 4 R4 に従い、新実験の `spec_content` と oracle contract を設定しています。
- [ident.py:196](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix2/orchestrator/campaign/ident.py:196) はそれらを campaign ID の preimage に含めます。
- comparator fixture の差し替えでは、この先行 assertion は変化しません。

## 変更

変更なしです。commit も実行していません。

既存の 16 staged file は維持され、unstaged の追加差分はありません。禁止対象の `docs/`、authority、freeze、effect gate、`CANDIDATES` も触れていません。

## 検査

指定された 2 本の pytest は未実走です。期待値誤りを判断した場合は実装を変えず停止する、という指示を優先しました。

したがって既知の状態は親の実走結果のままです。

- `test_sort_swo_oracle.py`: 104 passed
- production 検査側 6 file: 8 failed / 597 passed / 2 skipped

## 波及可能性

未修正の G1/G2 は `quarantine`、sort driver、S1 caller、s6 sweep、receipt、dependency material、critic consumer に波及します。

G3 は role adapter、role collection、real-repository serialization、originless baseline に波及します。campaign ID の期待値については、R4 と identity consumer 全体のどちらを正本とするか親裁定が必要です。

## 総括

(1) 旧 campaign ID の assertion は段 4 R4 と両立せず、fixture 差し替えでも直らないため停止しました。  
(2) 新たな検査は未実走です。既知値は 104 passed、および 8 failed / 597 passed / 2 skipped です。  
(3) G1からG4は未修正で、残赤 8 件です。作業差分と commit はありません。  
(4) sort admission/materialization consumers と role pin/adapter/serialization/originless が波及候補です。