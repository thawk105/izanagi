## 総括

指定の 2 ファイルだけを修正しました。`git add` / `git commit` は未実行です。

- [login_check_event_ledger.py:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-login-check-probe/tools/login_check_event_ledger.py:233)：land 出力の最大 mtime で先に選別し、選ばれた wave だけ観測窓を走査。
- [同ファイル:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-login-check-probe/tools/login_check_event_ledger.py:97)：`.git` entry・指定ディレクトリ名による枝刈りと `pruned_dirs`／`notes` を追加。
- [login_check_receipt_replay.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-login-check-probe/tools/login_check_receipt_replay.py:334)：観測窓欠測時の再帰走査にも同じ枝刈りを適用。受領証の判定規則は変更していません。

両 CLI に `--prune-dir NAME`（複数指定時は既定一覧を置換）、`--no-prune`、`--progress on|off`（既定 on）を追加しました。

合成入力で以下を確認済みです。

- Python 3.10 の `py_compile`、両 `--help` が成功。
- 14 wave 中、刈り有り／無しで同じ最新 12 本を選択。対象外は再帰走査なし。
- `.git` がファイル／ディレクトリの場合と `rate-source` の除外記録を確認。
- `--progress off` の stderr は空。
- 前巡入力の既存 JSON 値、および `--no-prune` の既存値が旧版と一致。
- 再走の全出力 bytes が `captured_at` 以外一致。入力 hash・mtime は不変。

[合成出力](/tmp/login-check-fix-wrtrpd0u/tight/ledger.json)

刈った木により古いファイルがあると `window_start` が新しくなり、観測窓は全走査時の窓の下界になります。この条件を `notes` に記載しました。

計算量は、選別段が全 wave の直下 entry 列挙・land 名ファイル読取と landed wave のソート、走査段が選択された `--limit` 本の残存木の総量です。**実データ 527 wave の再実走・性能測定は未実施**です。