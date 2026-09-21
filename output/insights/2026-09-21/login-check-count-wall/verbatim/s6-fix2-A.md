## 総括

所有する 2 ファイルだけを修正しました。`git add` / `git commit` は未実行です。

- [login_check_event_ledger.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-login-check-probe/tools/login_check_event_ledger.py:272)：cutoff 以下の landed 出力から wave を選択。母集団情報と `after_as_of` を追加。
- [login_check_receipt_replay.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-login-check-probe/tools/login_check_receipt_replay.py:373)：渡された wave の cutoff 選別、受領証のフラグ追加。両 CLI が `--as-of` に対応。

前巡の合成入力で確認済みです。

| cutoff（epoch 秒） | 選択 wave | cutoff による除外数 |
|---|---|---:|
| `1800000012` | 12〜01 | 1 |
| `1800000011.999999999` | 11〜00 | 2 |

- Python 3.10 の `py_compile`、両 `--help` が成功。
- 無指定時は旧版と一致。再走も `captured_at` 以外一致。
- cutoff 後の痕跡・commit・受領証を保持し、フラグを確認。
- 不正値・timezone 欠落などは usage エラー、rc=2。
- 入力の hash・mtime は不変。

観測窓は従来どおり「最古 file〜選択された land 出力＋60 秒」で、cutoff では切りません。**受領証候補も as-of で切らず**、cutoff 後の候補を使う再構成結果が維持されることを確認しました。warm/cold・義務対応・wall・枝刈り規則は変更していません。

[合成出力](/tmp/login-check-fix2-hl2cfzbt/observations/ledger.json)。実データでの再実走は未実施です。