## 所見 1

- 主張: 段 4 が指定した「層 3 レポート 0 件」の負例がなく、`if snapshots and len(snapshots) != 6` という空集合だけを通す回帰を現行テストは検出できない。
- 原典: [s4-adjudication.md:31](/work/1/SFC/tanab/dev-wave-jobs/t822-evidence-gaps/s4-adjudication.md:31)、[s4-adjudication.md:112](/work/1/SFC/tanab/dev-wave-jobs/t822-evidence-gaps/s4-adjudication.md:112)、[test_trial_registry.py:1785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/tests/test_trial_registry.py:1785)、[trial_registry.py:5494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/trial_registry.py:5494)
- 判定: must-fix
- 成果物影響: 現実装は 0 件を拒否するため現時点の成果物値は不変だが、この回帰では完全 build 束の受理集合が広がり、層 3 参照を一件も持たない受領証が台帳へ入る。`certifying=False` のため certified 選択値自体は変わらない。

## 所見 2

- 主張: field 型負例は private helper を直接呼ぶため exact 文言だけを固定し、正式受入での受領証不在を固定していない。
- 原典: [test_trial_registry.py:1878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/tests/test_trial_registry.py:1878)、[test_trial_registry.py:1910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/tests/test_trial_registry.py:1910)
- 判定: nit
- 成果物影響: 現実装では helper が receipt 作成前に呼ばれるため影響なし。型不正入力について、将来の呼出し順回帰に対する台帳・受領証不在の検査だけが不足する。

## 所見 3

- 主張: no-build、campaignless failure、またはそれらを一件でも含む束では exactly-6 検査を迂回して受入が完了するが、段 4 が明示的に scope 外とした既存の非 certifying 経路であり、黙った成功ではない。
- 原典: [trial_registry.py:5415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/trial_registry.py:5415)、[trial_registry.py:5432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/trial_registry.py:5432)、[trial_registry.py:5455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/trial_registry.py:5455)、[trial_registry.py:6032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/trial_registry.py:6032)、[s4-adjudication.md:73](/work/1/SFC/tanab/dev-wave-jobs/t822-evidence-gaps/s4-adjudication.md:73)
- 判定: nit（裁定済み scope 制限）
- 成果物影響: 受理集合は従来どおり不完全束を含み、受領証には `no-build` または `layer3-chain-absent` が記録される。`certifying` は false のままで、certified 選択への昇格はない。

## その他の検証結果

- 完全 build 束では 0 件を含む `len(snapshots) != 6` が hard failure になる。空集合の早期 return はなく、例外も握り潰されず、CLI は非ゼロ終了する。
- 正しい同一対象の 6 report 正例は receipt まで到達し、食い違いだけを拒否する。承認外の過剰拒否は静的には見つからなかった。
- `receipt_value`、schema、exact keys、canonical 化、SHA-256、理由コード生成部は無変更で、同一入力の受領証 bytes は不変。
- `git diff --stat` は指定された production/test の2ファイルだけ。禁止された3 production ファイルと `docs/` は無差分で、`git status` 上も変更なし。
- strict JSON は重複キー、非 UTF-8、型不正、空文字、複数または空の `env_tags` を fail-closed にする。揮発する作業ツリー hash は期待値に入っていない。
- 空実装 `return ()` では ccbench、env、5件母数、重複キー、field型の各負例が赤になる。赤にならない新設・変更テストは正例 `test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads` と名前重複検査だけ。
- 統合負例4件は exact 文言と受領証不在を固定する。top-level テスト関数名の実重複はなかった。

## 総括

- must-fix 1件: 段4指定の「0 report」負例を追加し、空集合だけを通す恒真化を固定して防ぐ必要がある。
- nit 2件: 型負例の受領証不在未固定と、裁定どおり残る不完全束の非 certifying 受入経路。
- production gate、受領証不変性、禁止編集面には must-fix を認めなかった。