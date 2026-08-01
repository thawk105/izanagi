対象の 2 テスト欠陥だけを [test_claude_transport.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:119) で修正しました。production・docs・Git index は変更していません。

- PBS_JOBID テスト:
  - 根本原因は、拒否値 `":"` を構造的な `code: message` 区切りを含む全文に対して検査していたことです。
  - code prefix を exact 検査後、開示検査を message 本体だけに限定しました。
  - bad 値は削減していません。`credential-sentinel@host` 等が本文へ漏れれば引き続き失敗します。

- P1 flag-off テスト:
  - 根本原因は、run_root 由来の campaign hash と、その値を含む journal digest が run ごとに異なることです。
  - 正規化後の journal/report bytes parity は維持しています。
  - 列挙外の field 値が異なれば bytes 比較は失敗します。
  - `attempt_journal_sha256` は単に削除せず、正規化後 journal bytes の SHA-256 に再計算し、digest 束縛を維持しました。
  - transport field 不在検査、transport I/O 0 回検査、固定 clock は維持しています。

正規化対象は次の field だけです。

- `attempts[].raw_response_path`: run_root 配下の role 出力先
- `attempts[run-finish].report`: run_root 配下の report 出力先
- `report.attempt_journal`: run_root 配下の journal 出力先
- `report.cells[].campaign_id`: run_root 由来の 8-hex hash 接尾辞
- `report.cells[].campaign_root`: run_root と campaign ID を含む
- `report.cells[].generations[].roles.*.raw_response_path`: journal から複製された run 固有 path
- `report.attempt_journal_sha256`: run 固有 path を含む journal bytes の digest

変異 spec は non-positive 24 entry の anchor がすべて `count=1`、全 27 entry の nodeid も一意に実在しました。anchor 更新は不要です。

静的検査は構文 compile、`git diff --check` とも成功しました。pytest は指示どおり実行しておらず、緑は主張しません。共有 helper `_expect_transport_error` の disclosure 判定面だけが影響対象で、production caller・fixture・consumer の挙動変更はありません。

## 総括

親実測の赤 2 本について、構造的区切りの誤検出と未列挙の run 固有値をそれぞれ限定修正しました。検出力と正規化後の byte parity を保ち、production・受理集合・変異 anchor は変更していません。