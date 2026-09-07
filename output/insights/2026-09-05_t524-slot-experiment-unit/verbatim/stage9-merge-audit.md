## 合成監査の結果

**健全。**

- `test_layer3_report.py`: wave 側は実物の legacy receipt を downstream gate で拒否します（[test_layer3_report.py:2319](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/tests/test_layer3_report.py:2319)）。main 側の accepted-report テストは current-schema gate を明示的に mock し、E1・commit・出力契約だけを検査しているため、旧 schema の通過を前提にしていません（[test_layer3_report.py:2406](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/tests/test_layer3_report.py:2406)、[test_layer3_report.py:2439](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/tests/test_layer3_report.py:2439)）。
- `test_p3_autonomous_workload_trial.py`: wave 側が共通 fixture の slot identity と genesis 作成器へ同じ `prereg_generation=13` を渡し（[test_p3_autonomous_workload_trial.py:7020](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/tests/test_p3_autonomous_workload_trial.py:7020)）、main 側の formal-profile 正例もその強化済み fixture を使用します（[test_p3_autonomous_workload_trial.py:8064](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/tests/test_p3_autonomous_workload_trial.py:8064)）。負例は launch admission より前で停止し、拒否分岐を迂回しません。
- `test_reflux_originless_compatibility.py`: wave 側の揮発化は attempt prefix の digest と byte count に限定されています（[test_reflux_originless_compatibility.py:205](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/tests/test_reflux_originless_compatibility.py:205)）。main 側は別パスの auditor role-source digest を固定値として更新しており（[test_reflux_originless_compatibility.py:574](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/tests/test_reflux_originless_compatibility.py:574)）、分類は衝突していません。

3 ファイルすべてで、各親の patch-id と反対親から probe merge への patch-id が一致し、片側の変更欠落もありません。

## 旧 schema 契約との整合

main 側の新しいテストが、旧 schema receipt の downstream 到達を前提にする箇所はありません。

旧 receipt は参照整合性を検証して読み取れますが、続く capability 要求では拒否されます（[test_s8c_acceptance_receipt.py:162](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/tests/test_s8c_acceptance_receipt.py:162)、[test_s8c_acceptance_receipt_v2.py:1052](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:1052)）。production gate は schema v5 を必須化してから再検証します（[s8c_acceptance_receipt.py:2039](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/campaign/s8c_acceptance_receipt.py:2039)）。

production の downstream 経路は `render_accepted` から `build_accepted_report` を経てこの gate に到達する一系統です（[layer3_report.py:904](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/campaign/layer3_report.py:904)、[layer3_report.py:1035](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/campaign/layer3_report.py:1035)）。main 側から別入口は追加されていません。

## 揮発分類との整合

main 側の追加と wave 側の揮発 leaf 分類は整合しています。

wave 側の 2 leaf は runtime の時刻・process identity・report digest を含む attempt prefix に由来する値だけです。完全一致させる receipt 検証自体は維持されます（[s8c_acceptance_receipt.py:1571](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/campaign/s8c_acceptance_receipt.py:1571)）。

一方、main 側が更新した role-source digest は揮発集合に含まれず、非揮発 leaf の比較で引き続き exact に検査されます（[test_reflux_originless_compatibility.py:598](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-merge-audit/orchestrator/tests/test_reflux_originless_compatibility.py:598)）。

## merge message

```text
[T-524] local main を取り込む — 旧 schema の下流拒否と slot 消費契約を保つ

両親がともに触った 3 ファイルの意味的な合成を監査した。

- test_layer3_report.py では、旧 schema の receipt を current verified capability に昇格させない拒否期待を維持した。main 側の accepted-report テストは current-schema gate を明示的に代役化して後段の E1・commit・出力契約だけを検査するため、旧 schema の下流到達を前提にしない。
- test_p3_autonomous_workload_trial.py では、main 側の formal-profile テストが使う共通 fixture に prereg_generation を slot identity と genesis 引数の両方で exact に与えた。正例は強化済み registry binding を通り、負例は launch admission 前で閉じる。
- test_reflux_originless_compatibility.py では、attempt registry prefix の digest と byte count だけを runtime 由来の揮発 leaf とし、main 側が更新した auditor role-source digest は別の非揮発 path で exact に保持した。

監査で次を確認した。

- 共有 3 ファイルについて両親の patch が merge tree に欠落なく残っている。
- 旧 schema は履歴読取に限って検証可能だが、require_current_verified_receipt から downstream capability へ到達しない。
- v5 は attempt registry の全 ref 履歴、genesis-only の初期 blob、slot projection、全 predeclared unit の final terminal を再照合する。
- render_accepted は build_accepted_report を経由し、current-schema gate を迂回する production 経路がない。
- 揮発分類は attempt prefix の派生値だけに限定され、slot・unit・role-source の意味束縛を隠さない。

AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=xhigh; role=author
AI-Agent: product=claude; model=claude-opus-5-1m; reasoning=xhigh; role=manager
Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

## 総括

- probe `cfd24bf4c` の実際の両親 `5dddb9f80` と `e6f3a8c3e` を監査し、意味的な破れや拒否分岐の迂回は認めませんでした。
- 依頼記載の `e1850cf3c` は `e6f3a8c3e` の祖先で、共有面の追加 127 行は knowledge provenance テストに限られ、本契約と衝突しません。
- 758 passed は補助事実とし、健全判定は差分、call path、schema gate、揮発 path の現物照合に基づきます。
- worktree と index は無変更です。commit、merge、rebase、reset、push は行っていません。