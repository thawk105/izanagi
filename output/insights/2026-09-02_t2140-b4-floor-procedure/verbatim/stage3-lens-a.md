## 所見

所見 1: [起草プラン 42 行目](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/artifacts/t2140-b4-floor-procedure/stage2-plan.md:42) は「ユーザーの採用裁定後」とする一方、将来の値セルには artifact の path/hash だけを書くため、どのユーザー裁定がその artifact を採用したかを永続的に束縛する手順がない。推奨: このまま採用すべきでなく、floor 登録 commit に既存 decisions 等の具体的なユーザー裁定を参照させることを必須にすべきである; 新しい台帳や gate は不要だが、この束縛がなければ後から commit と artifact だけを見て「発効済み」と既成事実化できる。

所見 2: [起草プラン 30 行目](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/artifacts/t2140-b4-floor-procedure/stage2-plan.md:30) が freeze 対象とする protocol・workload・null-pair の作り方・環境条件・provenance・出力命名のうち、[「ユーザーが決める部分」57–60 行目](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/artifacts/t2140-b4-floor-procedure/stage2-plan.md:57) は protocol/workload、共通参照点と null-pair の exact 定義、admission・単独性条件、artifact schema・命名、欠測時の campaign 不採用規則の決定主体を明示していない。推奨: この権限表のまま採用すべきでなく、全 freeze 項目をユーザーが明示承認するか、各項目の決定主体をユーザーが指名すると定めるべきである; そうしないと AI が起草した候補値が無裁定の既定値として procedure-freeze commit に入る。

所見 3: [起草プラン 81 行目](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/artifacts/t2140-b4-floor-procedure/stage2-plan.md:81) の「artifact-bound な正規 consumer が別途実在するまで」という期限は、consumer の実在後なら floor 未発効でも 4 分類を有効化できるように読め、D1383 の「発効するまで `protocol_violation` のみ」と一致しない。推奨: この文言は採用すべきでなく、「floor が発効し、§5 全欄・§6 全条件・発効版 commit・正規 consumer の全てが揃うまで」と直すべきである; consumer の実在は必要条件であって十分条件ではない。

## 見落としていないこと

- §5.1 の既存 floor 条件は「対象動作点で再実測し保守側最大」であり、計画はこれを代替せず、より具体化している。[事前登録 215–216 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/docs/phase3-b4-reflux-ablation-preregistration.md:215)
- 3.0%、D19、48 スレッド calibration の流用は明示的に排除され、既存 `between_run_floor.py` の成果物を権威ある床値へ昇格させる経路もない。[起草プラン 32 行目](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/artifacts/t2140-b4-floor-procedure/stage2-plan.md:32)
- caller の `--floor`、既定値、自由記述の出所は代替経路として明示的に禁止されている。[起草プラン 79 行目](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/artifacts/t2140-b4-floor-procedure/stage2-plan.md:79)
- §11 と pointer は「未裁定」「記入権限・実走許可を与えない」と明示されるため、それ自体を既存解除条件の代替とする文言にはなっていない。[起草プラン 64–65 行目](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/artifacts/t2140-b4-floor-procedure/stage2-plan.md:64)
- 編集位置は pin-safe である。pointer は H4 `5.1.1` より前、§11 は `## 6.` より後であり、consumer が抽出する H4 から次の level 4 以下の見出しまでの raw bytes は変わらない。[consumer 301–321 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-floor-procedure/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301)
- 新しい gate・機械検査・台帳・一般化は要求しておらず、既存測定面で要件を満たせなければ停止してユーザー裁定へ戻すため、コード変更も必須化していない。[起草プラン 58 行目](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2140-b4-floor-procedure/artifacts/t2140-b4-floor-procedure/stage2-plan.md:58)

## 総括

全体判定は条件付き採用であり、現状のままは採用すべきでない。  
既存解除条件、流用禁止、caller 自己申告禁止、pin、scope は維持されている。  
ただし、ユーザー裁定の永続的な束縛、未割当の protocol 項目、4 分類の再開条件を修正する必要がある。  
この 3 点を閉じれば、AI の案が無裁定で床値の権威になる経路を残さず採用できる。  
検査は静的読解のみで、編集、commit、pytest、測定は行っていない。