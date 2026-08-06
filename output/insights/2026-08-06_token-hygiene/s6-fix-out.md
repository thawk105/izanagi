## 総括

### (a) 変更ファイル

- [tools/claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/tools/claude_session_ledger.py)
  - root/sidechain の均衡配分と未使用枠再配分
  - file provenance 単位の ID alias 解決、衝突時 fatal
  - timestamp 順序・terminal usage 完全性検査
  - bytes、行長、record、request、tool、issue、discovery の hard limit
  - `os.walk(onerror=...)`、regular-file・root containment 検査
  - 配分・安全上限を JSON/テキストへ追加

- [orchestrator/tests/test_claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-hygiene/orchestrator/tests/test_claude_session_ledger.py)
  - 既定テキスト出力の全文 exact 比較
  - root 優勢時の sidechain 配分 fixture
  - alias、file/side collision、timestamp、terminal usage fixture
  - tree 全体の read-only・import bytecode 抑止検査
  - hard-limit、walk error、symlink containment 検査
  - descending final usage と全 `STRICT_ISSUES` matrix

docs 編集・commit はしていません。変更は指定された未追跡 2 ファイルだけです。

### (b) 対応表

| 項目 | 状態 | 理由 |
|---|---|---|
| A1 | partial | 均衡予約＋未使用枠再配分と配分報告を実装。既定 25 で root 21 / sidechain 4 になる root 優勢 fixture を追加。pytest 未実走 |
| A2 | partial | `requestId` / `message.id` を resolved file provenance 内で alias 化。file・root/sidechain 衝突と alias graph の曖昧性は除外＋fatal。pytest 未実走 |
| A3 | partial | timestamp 逆転、部分欠損、terminal usage 欠損を分類。時系列 terminal を採用し、欠損 request は集計しない。pytest 未実走 |
| B1 | partial | root/sidechain、unreadable、root/filter、時間根拠、token 値を含むテキスト全文 exact test を追加。M8/M10/M12 の kill は未実走 |
| B2 | partial | ledger import 前に bytecode を抑止。隔離 tree 全体の bytes・mtime・entry 増減と CLI 引数集合を検査。pytest 未実走 |
| B3 | partial | total bytes、行長、record/request/tool、discovery、issue detail を固定上限化。既定 `25` と `~/.claude/projects` を独立 literal で固定。pytest 未実走 |
| B4 | partial | `os.walk(onerror=...)`、`lstat()` regular-file 検査、resolve 後 containment と読み取り直前の再検査を実装。pytest 未実走 |
| B5 | partial | 降順 terminal usage が fieldwise max にならない fixture と `STRICT_ISSUES` 全分類 matrix を追加。pytest 未実走 |

### (c) 検査結果

実走済み:

- `python3 -m py_compile`（bytecode は `/tmp` へ隔離）: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: `違反なし`
- 99 文字超行の静的検査: 該当なし
- `git status`: 指定 2 ファイルのみ未追跡

未実走:

- `orchestrator/tests/test_claude_session_ledger.py`
- `orchestrator/tests/test_plain_runner_coverage.py`
- M1〜M12 変異 matrix
- 実データ走査

`pegasus02` ログインノード規律に従い、pytest・変異・実データ走査は行っていません。したがって緑や closed とは主張しません。

### (d) 波及可能性

- 静的検索では既存 caller/consumer は見つかりませんでした。
- JSON schema は `2` になり、population と hard-limit field が増えています。将来 schema `1` 固定の consumer が追加されていれば追従が必要です。
- `--max-files` は安全上限 `1000` を超える値を拒否します。
- ID・discovery・資源上限の曖昧入力は新たに fatal になります。これは A2/B3/B4 の fail-closed 要件による受理集合縮小です。
- fixture はすべて `tmp_path` 内で完結し、共有 fixture や実セッション tree には依存しません。
- `pytest.main` harness は維持しており、plain-runner meta-test の静的要件を満たしますが、meta-test 自体は未実走です。