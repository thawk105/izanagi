## 直した fixture

- [test_backoff_counterfactual_analysis.py:433](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-a/orchestrator/tests/test_backoff_counterfactual_analysis.py:433)
  - 12成果物すべてのtop-levelをv2へ変更。
  - 全rowは既定のv1を維持。
  - 診断は`top-level counterfactual contract mismatch`。
- [test_backoff_counterfactual_analysis.py:445](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-a/orchestrator/tests/test_backoff_counterfactual_analysis.py:445)
  - 12成果物すべての全18 rowをv2へ変更。
  - top-levelは既定のv1を維持。
  - 診断は`row preregistration SHA-256 mismatch`。
- 既存3形態はいずれもv2固定変異を分離できなかったため、上記2形態へ置換した。

## 帰属の裏取り

- M7a、top pinをv2固定:
  - 対象node 1件を実走しrc=1。
  - top側の`pytest.raises`が`DID NOT RAISE ValueError`となり赤。
- M7b、row pinをv2固定:
  - 対象node 1件を実走しrc=1。
  - row側の`pytest.raises`が`DID NOT RAISE ValueError`となり赤。
- 対象node:
  - `orchestrator/tests/test_backoff_counterfactual_analysis.py::test_artifacts_remain_bound_to_literal_v1_preregistration_sha`
- productionのSHA-256は変異前後とも`9883892bae84e8f4dc9206d8635f02bbec8cb420313df8ea5f3ba6b8277a745a`。
- 復元後の`git diff --exit-code -- orchestrator/campaign/backoff_counterfactual_analysis.py`はrc=0。

## 変えていないもの

- productionコードは最終的にbyte不変。
- literal SHA-256値は不変。
- `_write_artifacts`の既定v1束縛は不変。
- 対象test以外のassertion、比較方向、許容範囲は不変。
- `git status --short`には対象testだけが表示された。
- docs、commit、index、branchは変更していない。

## 実走

- `python3 tools/run_tests.py orchestrator/tests/test_backoff_counterfactual_analysis.py`
  - rc=16
  - `qstat -Q` preflightによるdispatch infrastructure failure。
- `PYTHONPATH=. python3 /work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-a/orchestrator/tests/test_backoff_counterfactual_analysis.py`
  - 最終実走rc=0。
  - nodeid選択: `orchestrator/tests/test_backoff_counterfactual_analysis.py`
  - 25件収集、25件成功。
- 変異実走:
  - M7a: 1件収集、1件失敗、rc=1。
  - M7b: 1件収集、1件失敗、rc=1。
- runnerが生成した一時receipt一式は除去済み。

## 総括

- must-fix: 解消。
- M7aとM7bは、それぞれ対応するgateだけを通過させた場合に対象nodeが赤になる。
- 未解決点: なし。