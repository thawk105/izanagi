修正完了（commitなし）。

- `validate_message` の docstringを authoritative / 非 authoritative の適用差分を明記する内容へ更新。
- drift テストへ synthetic finding と出力抑止 assertion を追加。
- `git diff --check`：成功。
- 指定テスト：Pegasus dispatch infrastructure failure（`qstat -Q preflight rc=1`、child未起動、rc=16）。
  - 実走 nodeid：なし
  - pass/fail：0 / 0（未実行）

`docs/` の既存変更は触れていません。

## 総括