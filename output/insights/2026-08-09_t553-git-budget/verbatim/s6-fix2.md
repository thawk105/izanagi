実装は完了しました。変更は指定2ファイルだけで、commit・docs 編集はありません。pytest は Pegasus の dispatch preflight 障害により未実走です。

### G1 — 重複した実 repo テストを削除

- `test_git_timeout_budget_matches_current_repository_cardinality` を削除し、ファイル冒頭も「実 repository には触れない」契約へ戻しました。[test_s8c_preregistration_core.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:2)
- 削除理由は裁定どおりです。
  - 元所見の誤認を招く `real-invariant-r` は前巡の `not-byte-length` への改名で既に閉じています。[test_s8c_preregistration_core.py:1015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1015)
  - 実 workload は no-touch の invariant test `test_candidate_freeze_matches_contract_and_generation_chain` が検査します。
  - production path 構成の再実装、固定10秒の全履歴 git、xdist group 未登録という負債は、重複検査の検出力に見合いません。
- 予算式の parametrize は残っています。[test_s8c_preregistration_core.py:998](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:998)
- 絶対 CAP と request clamp の検査も残っています。[test_s8c_preregistration_core.py:1025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1025)

### G2 — caller surface を完全一致で固定

[test_s8c_preregistration_core.py:1086](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1086) で以下を exact pin しました。

- `_git(root, args, *, stdin=None)`
- `_git_text(root, args, *, stdin=None)`
- `validate_condition_freeze_at(repo_root, commit="HEAD")`
- `prepare_revision(repo_root, *, ruling_reference=None, revision_reason, commit="HEAD")`

parameter の名前、順序、kind、既定値を列全体で比較するため、1引数でも増減・改名・kind変更があれば赤になります。

CLI は再帰 traversal を維持し、次の両方を固定しました。

- option 集合全体。[test_s8c_preregistration_core.py:1142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1142)
- root／各 subparser の action 列と positional `dest`。[test_s8c_preregistration_core.py:1151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:1151)

変異10を静的に適用すると、別名引数 `wait_seconds` の追加は signature 列の余剰で失敗します。positional 引数の追加も、関数なら signature 列、CLI なら option string が空でも action 列の余剰として失敗します。

### G3 — 実測コメント訂正

[s8c_preregistration.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:95) を訂正版 `MEASUREMENT.md` に合わせました。

- 採用値は during phase 全体の最大 `0.588973秒 / 7,044要求 = 8.3613e-5秒/要求`
- 当該最大サンプルは worker 0
- worker 実在時の最大は `0.445290秒 = 6.3216e-5秒/要求`
- 大きい値の採用は予算を保守側にする意図的選択
- `output/insights/2026-08-09_t553-git-budget/` の参照を維持

定数 `15.0 / 0.0086 / 300.0` は変更していません。

### 変異12件の対応表

| # | 検出先 | 静的確認 |
|---:|---|---|
| 1 | 定数 pin | RATEを1/10にすると`0.0086` assertionで赤 |
| 2 | 定数 pin | BASEを15未満にすると`15.0` assertionで赤 |
| 3 | 定数 pin | CAPを従属式445へ戻すと`300.0`と非従属性が赤 |
| 4 | `above-max-batch-requests`／絶対CAP | CAPの`min`削除で445秒となり赤 |
| 5 | request-clamp test | CAPを1000へ隔離した状態で、clamp削除は875秒対445秒となり赤。構造 sensitivity pin |
| 6 | `not-byte-length` | `len(stdin)`使用なら1要求対1000要求の差で赤 |
| 7 | `no-trailing-lf` | fragmentを数えないと15秒対15.0086秒で赤 |
| 8 | 単一予算 test | 固定15秒ならhelper値123.25秒の伝播 assertionが赤 |
| 9 | 単一予算 test | 100,000行のchunk分割はsubprocess callが2回となり赤 |
| 10 | exact caller surface | 別名引数追加・positional追加ともsignature/action列の余剰で赤 |
| 11 | 既存 timeout fail-closed test | `TimeoutExpired`捕捉削除で`git-timeout` assertionが赤 |
| 12 | input-limit順序 test | budgetを先に呼ぶとmust-not-budgetが発火して赤 |

### 検査結果

- `python3 tools/run_tests.py -q orchestrator/tests/test_s8c_preregistration_core.py`
  - `rc=16`: `qstat -Q preflight rc=1`。pytest未起動。
- exact-pin nodeid単独再試行
  - 同じく`rc=16`。pytest未起動。
- `python3 tools/check_codex_agents.py`: `rc=0`
- `python3 tools/check_docs.py`: `rc=0`
- `git diff --check -- <指定2ファイル>`: `rc=0`
- invariant test file の差分: なし

したがって状態は「実装済み・pytest未実走」です。

### 所有外への波及可能性

- `s8c_preregistration.py` のbytes変更は、下流の`core_module_blob_sha256`へ波及します。ただし段4裁定どおり外部literal golden pinはありません。
- exact pin により、将来4関数またはCLIへ正当な引数を追加する場合も、このテストの明示更新が必要です。
- real-repo unit test削除により、`conftest.py`のreal-repo xdist group登録は不要になりました。
- 実 workload coverageはno-touchのinvariant testへ一本化されています。
- `_git`のsignature、単一`subprocess.run`、input-limit順序、reason code、CR path受理集合には変更ありません。

## 総括

Major 3件を親裁定どおり修正しました。  
重複した実repo cardinality testを削除しました。  
予算式・絶対CAP・request clamp・`not-byte-length`改名は維持しています。  
4関数と全CLI surfaceを完全一致で固定しました。  
変異10は別名・positional追加の双方でkillされます。  
実測コメントを訂正版のworker provenanceへ合わせ、定数は不変です。  
変更は指定2ファイルのみで、invariant・docs・commitには触れていません。  
常設検査はrc=0、pytestはdispatch障害により未実走です。