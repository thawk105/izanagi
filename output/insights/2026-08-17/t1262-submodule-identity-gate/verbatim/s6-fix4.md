## 変更内容

- [test_codex_reasoning_ab.py:1859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:1859)
  - `copy_with_absolute_worktree` を `shutil.copytree` と同じ 7 parameter に変更。
  - 位置引数・キーワード引数の双方を受理可能。
  - 再帰 copy では注入せず、最上位 copy 完了後だけ絶対 `core.worktree` を設定。
- [test_codex_reasoning_ab.py:1903](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:1903)
  - 期待理由 `absolute submodule core.worktree` と未拒否時の fail sentinel は変更なし。
- production file は変更しておらず、検査を緩めていない。

## 同種不整合の走査結果

test file 全体の `shutil.copytree` 使用箇所と、35 個の local-function monkeypatch helper を走査した。

直前 fix 由来の `counted`、`injected_walk`、`counted_inventory`、`recording_run` も各呼出形と照合し、未対応の位置引数はなかった。`copytree` の差し替えは今回の 1 箇所だけだった。

AST 検査では wrapper と標準 API の parameter 名が完全一致した。

## 実走結果

`tools/run_tests.py` で対象 node を実行したが、Pegasus の `qstat -Q` preflight が失敗して `rc=16` となった。

したがって対象 node は「実装済み・未実走」。緑とは判定していない。AST parse、signature 照合、`git diff --check` は成功した。

## 総括

残る TypeError の原因だった wrapper signature を修正した。  
再帰 copy を考慮し、絶対 `core.worktree` の注入は最上位 copy 後だけに限定した。  
期待する拒否理由と production の検査は変更していない。  
対象 node の実測は基盤失敗のため親の計算ノード走行に委ねる。