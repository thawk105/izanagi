## 所見

**F1 · must-fix — P2 の A 案では cohort 1 を測り直したことにならない。**
根拠: [brief:16–21](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/s1-brief.md:16)、[plan:7](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/codex/s2-plan.md:7)。元の reservation は cohort 1 が `0600887d9`、cohort 2 が `8737cacb4` を記録する。両版の B-10 job body は依存元の取得経路が異なり、元の依存元 directory は現在も存在して pin と一致する。
**放置時の影響:** R2 の２本はどちらも cohort 2 の条件での再走となり、「元の２ cohort と並べた」比較の意味が変わる。
**推奨:** **A′** を採る。各 group を元の source commit と事前登録 commit（cohort 1 は `0600887d9`／`cad6f46d8`、cohort 2 は `8737cacb4`）で走らせ、どちらも原 cohort の置換ではない別 attempt と表示する。A と A′ の測定費用はいずれも６ job、約 1.40 node 時間。A′ は旧依存元の起動前確認が増えるが、driver 改修は要らない。B は `pin.CURRENT_PIN = 6810666` となり、[生成器:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/tools/plotting/plot_b10_static_tail_formal.py:229) の固定検査を通らないため、生成器改修とその受入が必要で、成果物も現行 pin での新条件の測定になる。元の２条件を再現パッケージに並べる目的には A′ が最も合う。

**F2 · should-fix — 対照表の必須項目が過大。**
根拠: [plan:71–76](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/codex/s2-plan.md:71)、[生成器:361–372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/tools/plotting/plot_b10_static_tail_formal.py:361)。plan は全反復の整数カウンタ、SD、CV、全区間の各境界まで insight 表への転記を要求する。
**放置時の影響:** 原値と R2 の主要な値が大量の転記に埋もれ、転記誤りも図との比較結果に混入しうる。
**推奨:** 表は４ attempt ×３ workload について、group・source／事前登録・verdict、８点の throughput／abort rate の平均と 95% CI、６区間の state、必要な代表量（1250→9999 µs 比など）に絞る。反復値と全境界は元の report、DAT、provenance の参照とハッシュで辿れるようにする。

**F3 · should-fix — 図が出ない場合の成果物を結果前に明記する。**
根拠: [brief:24–26](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/s1-brief.md:24)、[plan:67](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/codex/s2-plan.md:67)、[生成器:204–206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/tools/plotting/plot_b10_static_tail_formal.py:204)。verdict が固定値と異なる場合や group report が invalid の場合、同じ生成器は図を拒否する。
**放置時の影響:** 図の欠落が測定失敗なのか、得られた異なる判定なのかを成果物から区別できない。
**推奨:** 投入前の地位記録に、完走・invalid・未完走・描画拒否をいずれも掲載し、図が出ないときは各 group の report／得られた値／拒否理由を表で並記すると一文加える。生成器の verdict 検査は緩めない。

**F4 · nit — 描画 wrapper の検査と記録を局所化する。**
根拠: [plan:59–69](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/codex/s2-plan.md:59)、[生成器:314–345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/tools/plotting/plot_b10_static_tail_formal.py:314)、[生成器:439–460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/tools/plotting/plot_b10_static_tail_formal.py:439)。原生成器の cohort 名と役割表示は固定されているため、R2 用の差し替えと実行 argv の開示は必要。一方、原図の全 artist series を再照合する陽性対照や、wrapper の細かな定数ごとの記録は依頼の追加検査に当たる。
**放置時の影響:** 対照する値・図・判定自体は変わらず、作業と記録だけが増える。
**推奨:** wrapper の内容、実行 argv、入力ハッシュ、出力 provenance を残し、図中で R2 を原 cohort の「主結果／独立再現」と誤表示しないことを確認する範囲に絞る。

## 総括

- **P1：支持。** [投入手順:35–48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/docs/b10-backoff-static-tail-submission.md:35) は `submit_b10_backoff_grid.sh --run-kind t2500-tail-formal` を指定する。
- **P2：修正。** CCBench の `511c953..6810666` の差分が `cc/mocc/transaction.cc` だけという観察と、`8737` 以後の *job script* の差分が freeze digest だけという観察は支持できる。ただし後者を実行条件全体へ一般化できず、両 group を `8737` に固定する案は元の cohort 1 の再走を失う。A′を推奨する。
- **P3：支持。** [submit script:239–252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/tools/pegasus/submit_b10_backoff_grid.sh:239) の `qsub -v` に trace 保全 opt-in はない。
- **P4：修正。** 入力定数と図中表示に加え、caption と provenance の固定された cohort 役割・group 束縛も R2 と整合させる必要がある。想定外 verdict では図を出さず結果を記録する方針は支持する。
- **P5：支持。** [D2050](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/docs/decisions.md:62781) に沿い、別 attempt としての地位と報告方法を結果前に固定する。