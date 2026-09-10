実装済み・未実走です。指定 2 ファイルのみ変更し、親所有の docs 差分・manifest・no-touch 定数・段 0 算出経路には触れていません。`git add` / `git commit` も未実施です。

変更点:

- [fence helper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:348) を新設。tab stop 4 で indent column を計算し、opener/closer を一括判定します。
- 旧文字数判定だけが fence と誤認した行は fence 扱いせず、受理集合拡大を防ぐため fail-closed にしました。
- [F3 node](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:975) は無効 opener と唯一の canonical 表だけに変更。invalid-info 検査を外すと表が一意に抽出され、全検査を通って受理されます。
- [tab-indent node](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:999) を追加。旧文字数 mutant は緩和表を隠して canonical 表を受理しますが、修正版は invalid indentation で拒否します。
- `git diff --check` は成功しました。

指定 test run は `qstat -Q preflight rc=1` による dispatch infrastructure failure、rc=16 で、pytest node は一件も実行されませんでした。

## 総括

- G1: 対応済み — column ベース判定と単調な fail-closed guard を実装。
- G2: 対応済み — F3 node を真の受理集合差へ更新し、tab-indent の真 KILL node を追加。
- G1 の CommonMark 根拠: indent 0〜3 column、backtick/tilde 同種 marker 3 個以上、backtick opener の info に backtick なし、closer は同種・opener 以上の長さ・後続空白のみを一 helper で判定。
- 新たに受理される入力: なし。
- 追加・更新 nodeid: 更新 `test_design_invalid_backtick_info_decoy_is_rejected`、追加 `test_design_tab_indented_fence_decoy_is_rejected`。
- 走らせた nodeid と結果: 未実走 — 指定 2-file run は dispatch preflight rc=16 で投入前に失敗。