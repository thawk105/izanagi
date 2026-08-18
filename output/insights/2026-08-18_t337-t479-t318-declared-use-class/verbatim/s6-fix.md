## 総括

F1 は closed。閉包判定を fixture と実検査で共有しました。  
F2 は closed。module attribute 呼出しも検出します。  
F3 は closed。producer ごとの layout/run 個数 assertion を復活しました。  
F4 と N1 は closed。consumer 移行と例外型・効果判定を修正しました。  
pytest は Pegasus dispatch infra red のため、実装済み・未実走です。  
docs・`layout.py`・`s1_known_axes_freeze.py` は変更せず、commit もしていません。

### 所見対応表

| 所見 | 状況 | 対応 |
|---|---|---|
| A1 | closed | 動的 AST 走査を維持 |
| A2 | closed | attribute 形を追加検出 |
| A3 | partial | D162 の scope 外残余として未変更 |
| A4 | closed | 既存の fail-closed を維持 |
| A5 | closed | wave 前からの pin 不一致、追加変更なし |
| A6 | closed | campaign-id 不変を維持 |
| A7 | closed | 8c を動的閉包へ含有 |
| A8 | closed | 個数表を現 producer に固定 |
| A9 | closed | production caller は既移行済み |
| A10 | partial | 報告文の誤記のみ、コード変更なし |
| B1 | closed | `test_trigger_gate_binding.py` を移行 |
| B2 | closed | 例外 message 依存を除去 |
| B3 | closed | scope 外との裁定を維持 |
| B4 | closed | 宣言を path selector として維持 |
| B5 | partial | DW-G03 の制度 scope 外残余 |
| B6 | closed | hooks・test 集合への影響なし |
| F1/F2/F3/F4/N1 | closed | 下記 3 file に反映 |
| regressed | なし | 静的検査で確認 |

### 変更 file

- [test_p3_exploration_namespace.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/tests/test_p3_exploration_namespace.py:40)
  - Name/attribute 共通 AST 走査、共有閉包判定、動的 fixture、個数固定を追加。
- [test_trigger_gate_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/tests/test_trigger_gate_binding.py:400)
  - `declared_use_class="official"` を signature consumer に追加。
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t337-t479-t318-use-class/orchestrator/tests/test_campaign.py:8424)
  - `match=` を除去し、型・cid 未計算・output 未生成で判定。

個数表は族の外延ではなく、各 producer の内部呼出し回数を pin するためテスト内に保持しました。

### 実走結果

pytest の実走 nodeid はありません。すべて「実装済み・未実走」です。`tools/run_tests.py` は通常実行・`--force-dispatch`・`--collect-only` とも Pegasus `qstat -Q preflight rc=1` で rc=16 でした。

非 pytest probe は以下を通過しました。

- 閉包の負例・正例 fixture
- module attribute 検出
- signature consumer
- 動的 inventory と producer 個数
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- `git diff --check`

### 波及可能性

- production の `loop.run_campaign` は 15 call、13 file（backoff 系、demo、P2-2、P3 kickoff/s4 系、s6/s8a、sanity）で、全て宣言付きです。
- `s8b_floor_campaign.py` の `run_campaign` は別 API であり、今回の consumer ではありません。
- 共有 fixture wrapper は `conftest.py` にありません。`test_p3_s4_loop_trigger_gating.py` と `test_dev_wave_land.py` は既移行済みです。
- `test_campaign.py` の selector 省略呼出しは拒否挙動を固定する意図的負例として残しています。