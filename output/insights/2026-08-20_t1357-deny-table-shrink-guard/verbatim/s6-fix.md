`orchestrator/tests/test_coder_effect_gate.py:146-195` の関数内部のみを修正しました。

- 全 `Assign` / `AnnAssign` を収集し、対象代入が1件 בלבדであることを検証。
- RHS を allowlist 化し、別名参照・属性・comprehension・非文字列定数・不正な呼び出しを拒否。
- 現行 frozen 定義の直接チェックは通過。
- pytest 全体は Pegasus dispatch の `qstat -Q` rc=1 により未実走（子プロセス未開始）。

## 総括

後続再代入は件数 assert で検出します。  
別名迂回は `frozenset` 以外の Name 拒否で封じました。  
変更対象は指定テストファイルのみです。