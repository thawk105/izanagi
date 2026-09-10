静的レビュー結果です。pytest・受入走は未実施です。

1. **real / blocker — 実際の cleanup 呼び出しでは新機能が発火しない**

   プランは CLI/env 未指定時に探索を完全に省略します（[s2-plan.md:238](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:238)、[s2-plan.md:242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:242)）。しかし実際の呼び出し元は env も `--offrepo-root` も渡していません（[cleanup-branches.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/.claude/commands/cleanup-branches.md:17)）。§7.2 も所在を示すだけで export しません（[pegasus-runbook.md:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/docs/pegasus-runbook.md:733)）。既存 command は 3,983 bytes、上限は 4,000 bytes です（[check_docs.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/check_docs.py:168)）。

   **失われるもの:** `/cleanup-branches` の通常系列では (b) が一度も効かず、既知の偽陽性が残り続ける。

2. **real / must-fix — P5 の祖先 root 拒否が未確定**

   worktree 内 root の拒否は書かれていますが、worktree を内包する祖先 root の拒否は「推奨」に留まり（[s2-plan.md:123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:123)、[s2-plan.md:124](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:124)）、テストも採用時だけです（[s2-plan.md:347](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:347)）。祖先 root は repo/worktree 内の untracked copy まで走査できます。

   **失われるもの:** repo 内の自作コピーが repo 外正本に見えて、真正な dangling path を masking できる。

3. **real / must-fix — `--include-fold-trees` の CLI 回帰を検出できない**

   現行 CLI は `excluded` を計算して `audit()` に渡します（[audit_dangling_commits.py:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:175)）。プランは wrapper 置換を指示しますが、`excluded` の引き継ぎを明示していません（[s2-plan.md:245](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:245)）。既存テストは直接 `audit()` を呼ぶだけで、CLI option を通りません（[test_audit_dangling_commits.py:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/orchestrator/tests/test_audit_dangling_commits.py:209)）。

   **失われるもの:** 明示した `--include-fold-trees` が無視され、spool/archive の調査契約が静かに退行する。

4. **real / must-fix — 環境変数のテスト隔離が実装定数依存**

   既存 CLI テストの隔離案は `monkeypatch.delenv(ADC.OFFREPO_ROOT_ENV)` です（[s2-plan.md:299](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:299)）。これでは定数自体を誤記した実装を検出できず、実際の公開名を独立に固定できません（[s2-plan.md:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:19)）。

   **失われるもの:** CI や実行環境に本物の env が残っていると、既存 negative control が偶然の bytes 一致で変質する。

5. **real / must-fix — CLI precedence の positive test が弱い**

   テスト案は env root と 2 番目の CLI root に同じ一致物を置くだけです（[s2-plan.md:315](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:315)）。これでは「CLI root だけを使う」実装と、env を混ぜてから sort する誤実装を区別できず、1 番目の CLI root も検証していません（[s2-plan.md:317](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:317)）。

   **失われるもの:** CLI 指定時に env 側の不要な実体を探索・抑止しても、テストが緑になる。

6. **real / must-fix — スケールとメモリの受入根拠が一点測定だけ**

   親の 1,946 directory / 20,544 file / 2 秒という値から、プランは `+2〜3 秒`を見積もっています（[s1-brief.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/output/insights/2026-08-08_dangling-audit-offrepo-authority/s1-brief.md:31)、[s2-plan.md:375](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:375)）。一方、全 root を `os.walk` し、候補 blob の全 bytes をメモリへ保持する設計です（[s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:24)、[s2-plan.md:163](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:163)、[s2-plan.md:213](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:213)）。10 倍規模・巨大 checkout・巨大 blob の試験や上限がありません。

   **失われるもの:** 掃除の安全 gate が長時間化またはメモリ逼迫し、運用者が監査を迂回する誘因になる。

7. **real / must-fix — root error と FIFO のテストが安全に赤くなる保証がない**

   プランは directory `onerror` を `scan_failures` に数える契約ですが（[s2-plan.md:125](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:125)）、テスト案は file read failure の注入に偏っています（[s2-plan.md:356](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:356)）。FIFO の negative control は、壊れた実装が通常の `open()` を使うと pytest 自体が block し得ます（[s2-plan.md:351](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:351)）。

   **失われるもの:** root が読めない場合の透明な fail-closed 表示を検証できず、回帰が赤ではなくハングまたは無言の skip になる。

### scope 外の real 所見

8. **real / nit — `authority` / `正本` の語が既存の trust semantics と衝突する**

   プランは外部ファイルを `authority absolute path` と呼び、出力も「正本」とします（[s2-plan.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:21)、[s2-plan.md:258](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:258)）。しかし既存文書では repo 外 root は certified material / proof chain の正本ではないと明記されています（[output/README.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/output/README.md:57)、[output/README.md:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/output/README.md:60)）。D75 も入力識別子の二義化を禁じています（[operations.md:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/docs/dev-wave/operations.md:77)）。

   **失われるもの:** 監査上の「同一 bytes の外部証拠」が、正式な provenance authority と誤認される。

9. **疑い / nit — lease env と jobs root env の関係が曖昧**

   既存の `IZANAGI_WAVE_LEASE_DIR` は `dev-wave-jobs/land-lease` を指します（[pegasus-runbook.md:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/docs/pegasus-runbook.md:743)、[pegasus-runbook.md:747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/docs/pegasus-runbook.md:747)）。新 env は親の `dev-wave-jobs` 全体を指す想定です（[s2-plan.md:241](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:241)）。指定例上は別 directory ですが、両者の関係・誤設定時の扱いが定義されていません。

   **失われるもの:** operator が lease directory を探索 root と誤設定し、必要な正本を見落とすか、誤った外部成果物を走査する。

裁定 (b) 以外の ack 台帳 (a) や即時 prune (d) の混入は、静的には見当たりません（[s2-plan.md:391](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dangling-audit-offrepo-authority/s2-plan.md:391)、[ruling.md:57](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-07-dangling-audit-alarm-fatigue.md:57)）。ただし (b) は所見 1 のため実運用では未接続です。

## 総括

1. blocker は **1 件**（所見 1）。
2. 最も危険なのは、実際の `/cleanup-branches` 呼び出しが探索 root を渡さず、新機能が恒真な no-op になることです。
3. 段 5 へは **NO-GO**。まず caller の発火経路と P5・CLI 回帰・テスト検出力を確定すべきです。