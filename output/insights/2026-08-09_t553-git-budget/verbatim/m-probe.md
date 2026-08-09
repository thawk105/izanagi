作成しました。

- ファイル: [probe_git_batch_budget.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py)
- 行数: 765 行
- Python 3.10 の構文・CLI 起動確認済み
- JSON 必須フィールドと `returncode` 非 `None` を確認済み

動作確認はログインノード `pegasus02` で軽量な 1 回のみです。

- `cat-file --batch-check`: 7,002要求、並列度1、0.136293秒、rc=0
- `cat-file --batch`: 重複排除後4要求、並列度1、0.007711秒、rc=0
- contended な本測定は未実走です。

production から解決した既定 path は次の3本です。

- `docs/phase3-8c-preregistration.md`
- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`
- `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json`

この probe では、受入全走の混合負荷、真の cold cache、他ユーザー由来の外乱は再現・分離できません。cache は落とさず、初回と2回目以降を別記録します。

repo 書込確認として、作業前後の `git status --porcelain=v1 --untracked-files=all` が空、最終 `git diff --exit-code` が rc=0 であることを確認しました。docs 更新・commit・git 状態変更は行っていません。

## 総括

計測専用 probe 1本を job directory に作成しました。  
4系統、競合実行、hard cap、失敗除外集計を実装済みです。  
ログインノードでは軽量な動作確認だけを実施しました。  
予算係数や安全性の結論は probe 内に実装していません。