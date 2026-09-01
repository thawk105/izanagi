## 所見

1. [orchestrator/tests/test_p3_b4_admission_record.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/tests/test_p3_b4_admission_record.py:226)、[同:765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/tests/test_p3_b4_admission_record.py:765) — enforcement テストが mapping 変異から独立していない。production 定数との直接の equality assertion は持たないが、正例 fixture の配置をテスト側の独立 mapping で決めている。production の `base` mapping を事前登録 M2 の `"admission.json"` へ変異させると、最初の正例が path 関門で落ち、負例へ到達しない。したがって M2 は mapping literal テストだけでなく enforcement テストも落とす。
   
   成果物への影響: M2 の kill が過剰決定となり、変異記録で enforcement テストの単一理由性を主張できない。

## 弱体化の有無

なし。diff header を除く削除行21行を全件確認した。

拒否入力、exact な拒否署名、assertion、skip の削除・緩和はない。sort の projection 不一致は required path に置いた別 fixture へ移して同じ exact 署名を維持している。`admission.json` の期待値変更は配置移動に対応するもので、manifest は既存の完全一致 assertion に加えて新しい3本すべての不在を確認しており、実質的な緩和ではない。

## 総括

- 最大の所見は、enforcement テストと production mapping の間に残った間接依存である。
- 関門自体は実効位置にあり、別 path の regular file は前段を通り、関門を除けば後段も通る。
- 負例追加後と最終正例は同一 repository・同一 HEAD で両立している。
- 命名は required path に限定され、docstring の指定された非保証5項目にも抜けはない。
- 受理集合は狭まるだけで、fixture の `mkdir`、`git add`、`git rm` の path に取り違えはない。
- 単一理由性を直すまで記録段へ進めない。静的検査のみで、テストは実走していない。