実装は完了しました。編集は指定された2ファイルのみです。docs・commit・stage・stash・branch操作は行っていません。

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1796)
  - 非 backtick の `.md` path を拒否。
  - self 以外の `の全節` を拒否。
  - range delimiter を空白付き exact `〜` のみに限定。
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:2638)
  - grammar 負例2本。
  - range 負例2本、exact range 正例1本。
  - 無名可視 H2 による coverage 専用負例。
  - O20 +154 正例を operations 8,401 bytes、旧 cap 8,400超過に強化。padding は他のL2節へ分散し、各節1,000 bytes以下を独立 assert。

検査結果:

- `python3 -B tools/check_docs.py` — rc=0、違反なし
- AST parse — rc=0
- `python3 tools/check_codex_agents.py` — rc=0
- `git diff --check` — rc=0
- grammar/range in-memory assert — rc=0
- pytest — **未実走**
  - force dispatch: `qstat -Q preflight rc=1`、runner rc=16
  - 通常 runner: 同じく rc=16
  - どちらも pytest 本体開始前に停止したため、緑は主張しません。

## 総括

- must-fix 1: **partial（実装済み・pytest未実走）**。受理集合は狭まる。dev-wave 段/条件参照 cell のみへ作用。
- must-fix 2: **partial（実装済み・pytest未実走）**。受理集合は狭まる。正規の `DW-O01`〜`DW-O06` は維持。共有 parser のため provenance 側にも静的波及可能性はあるが、現行 provenance 契約に range はない。
- must-fix 3: **partial（テスト強化済み・pytest未実走）**。production受理集合は不変。旧 file cap 残存変異への検出力を追加。
- must-fix 4: **partial（テスト追加済み・pytest未実走）**。production受理集合は不変。coverage比較のKILL nodeを追加。
- 未着手項目はありません。親所有の既存 docs 差分は保持し、1 byteも編集していません。