## 観点 1 — 既定 branch の無傷性

- 分類: must-fix なし、nit なし、backlog なし。
- 既定値は `extended` で、既定 qsub 環境には `B10_RUN_KIND` が追加されません。T-2266 時だけ追加されます。[submit_b10_backoff_grid.sh:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/submit_b10_backoff_grid.sh:12) [submit_b10_backoff_grid.sh:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/submit_b10_backoff_grid.sh:184)
- `extended` は従来と同じ driver argv、overthrottle、report の順で実行されます。[b10_backoff_grid.sh:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:579) [b10_backoff_grid.sh:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:594)
- executing bytes、submit 時 SHA、committed blob の三者照合は維持されています。[b10_backoff_grid.sh:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:369)
- PBS の 5 時間 envelope、各 timeout cap、freeze 前後検査に変更はありません。[b10_backoff_grid.sh:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:4) [b10_backoff_grid.sh:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:13) [b10_backoff_grid.sh:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:576) [b10_backoff_grid.sh:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:611)

## 観点 2 — 凍結物と登録簿

- 分類: must-fix なし、nit なし、backlog なし。
- 統合差分の対象は driver、同テスト、既存 job body、既存 submitter の 4 ファイルだけです。[s5-integrated.diff:1](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s5-integrated.diff:1) [s5-integrated.diff:585](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s5-integrated.diff:585) [s5-integrated.diff:756](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s5-integrated.diff:756) [s5-integrated.diff:909](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s5-integrated.diff:909)
- `EXTENDED_SWEEP_US` は変更されず、既定 branch は既存 `config_for`、`genomes`、`measurement_order` を選択します。[s5-integrated.diff:50](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s5-integrated.diff:50) [backoff_extended_sweep.py:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:752)
- 指定された freeze、図、patch、registry、runbook、registry golden に差分はなく、`GeneratorId` の追加もありません。

## 観点 3 — run kind の provenance

- 分類: must-fix なし、nit なし、backlog なし。
- submit event は manifest、submitted、failed のすべてに保存されます。[submit_b10_backoff_grid.sh:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/submit_b10_backoff_grid.sh:117)
- reservation は `run_kind` を引数で受け、文書へ保存します。[b10_backoff_grid.sh:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:394) [b10_backoff_grid.sh:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:409)
- failure receipt と completion にも保存されます。[b10_backoff_grid.sh:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:114) [b10_backoff_grid.sh:645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:645)
- submitter、job body、driver の各境界で `extended|t2266-tail` に閉じています。[submit_b10_backoff_grid.sh:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/submit_b10_backoff_grid.sh:36) [b10_backoff_grid.sh:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:186) [backoff_extended_sweep.py:739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:739)

## 観点 4 — 要求集合と実現集合

- 分類: must-fix なし、nit なし、backlog なし。
- `requested_us` は 1000 を含み 999 を含まず、`realized_us` は 999 を含み、1000 は F718 の未実現理由へ分離されています。[backoff_extended_sweep.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:64)
- 三集合は campaign identity の `search_config` に束縛されています。[backoff_extended_sweep.py:446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:446)
- JSON 成果物にも同じ三集合と run kind が保存されます。[backoff_extended_sweep.py:661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:661)
- `.dat` の provenance 行にも campaign、run kind、要求・実現・未実現が入るため、成果物単体から「1000 は未測定」と判定できます。[backoff_extended_sweep.py:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:690)

## 観点 5 — 申告と実物の照合

- 分類: must-fix なし、nit なし、backlog なし。
- `s5-author.md` の受理集合の申告は、両 shell と driver の閉じた run-kind 分岐、8 commit と 2 report の完了検査、create-only 書込みと一致します。[s5-author.md:51](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s5-author.md:51) [b10_backoff_grid.sh:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:624) [backoff_extended_sweep.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:686)
- 波及可能性の申告も差分と一致します。receipt の追加 field は明示され、registry、既存 report、plotter、freeze、docs を「変更していない」範囲に含めた隠れた変更はありません。[s5-author.md:60](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s5-author.md:60)
- 申告と実物の食い違いは検出しませんでした。

## 総括

- must-fix: 0 件。内容なし。
- nit: 0 件。
- backlog: 0 件。
- 既定 `extended` の driver argv、段順序、qsub 環境、PBS envelope、timeout、freeze 検査は維持されています。
- 凍結物、登録簿、既存 campaign identity、`GeneratorId` に変更はありません。
- run kind は四種の receipt すべてに保存され、入力も二値へ閉じています。
- 要求 1000 と実測 999 の区別は campaign identity、JSON、`.dat` まで到達しています。
- 指示どおり静的検査のみ行い、テストは実行していません。