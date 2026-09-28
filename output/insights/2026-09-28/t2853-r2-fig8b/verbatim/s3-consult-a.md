## 所見

**F1 — must-fix：R2 の役割表示と生成器の整合検査が両立していない。**
根拠: [s2-plan.md](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/codex/s2-plan.md:63)、[plot_b10_static_tail_formal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/tools/plotting/plot_b10_static_tail_formal.py:544)、同ファイル [445 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/tools/plotting/plot_b10_static_tail_formal.py:445)。プランは `COHORTS` の `role` を R2 用に変えるが、既存の provenance 検査は `(1, "primary"), (2, "reproduction")` を固定要求する。一方、元の役割を残せば図中では R2 が主結果と独立再現に見える。さらに `main` の描画経路は生成後に `validate_repo_closure` を呼ばない（同ファイル [648–679 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/tools/plotting/plot_b10_static_tail_formal.py:648)）。
**放置時の影響:** R2 図の地位が誤表示されるか、生成した provenance が既存検査で不合格になる。
**推奨:** wrapper で「R2 の別 attempt」という表示と対応する役割の照合を明示し、出力後に既存の入力・出力 closure 検査を通す。verdict、`gate_passed`、`failures`、stock pin など測定値の受理条件は維持する。

**F2 — should-fix：完走照合で `completion.json` に存在しない項目を要求している。**
根拠: [s2-plan.md](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/codex/s2-plan.md:40)、8737 版 `b10_backoff_grid.sh:410–437,712–725`。元の [cohort 1・2 の reservation と completion](/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/b10-backoff-grid-20260919T131526Z-2235286-write-heavy/completion.json) でも確認した。`completion.json` に source commit と nonce はなく、これらは `reservation.json` の `source_binding` と `binding` にある。
**放置時の影響:** 正常な 6 job を照合不能と誤判定するか、source commit・nonce の照合が抜ける。
**推奨:** request ID・workload・run kind・status は completion と receipt、source commit・gitlink・nonce・script SHA は reservation と receipt の対応する欄で照合する。

**F3 — should-fix：P2 の「同じ条件」の射程を限定する。**
根拠: [s1-brief.md](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/s1-brief.md:16)、[事前登録の追記](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/docs/b10-backoff-static-tail-preregistration.md:1109)。元 cohort 1 の repository commit は `0600887d9…`、cohort 2 は `8737cacb4…`。追記は両者の事前登録文書 blob が異なり、§5 の spec SHA は同じと明記する。R2 の両 group を 8737 で走らせる選択は cohort 2 の経路の再測として整合するが、cohort 1 の checkout の厳密な再実行ではない。
**放置時の影響:** 対照表が R2 group 1 を元 cohort 1 の同一 source・同一事前登録 blob による再測と誤記しうる。
**推奨:** 対照表に各 group の source commit、事前登録 commit・blob SHA、spec SHA を別欄で載せ、R2 は両 group とも cohort 2 の投入版を用いた別 attempt と記す。

## 総括

- **P1：支持。** 手順書の投入経路は `submit_b10_backoff_grid.sh --run-kind t2500-tail-formal`。
- **P2：修正。** 8737 の選択は整合する。`511c9538..6810666` の CCBench 差分は実際に `cc/mocc/transaction.cc` のみ、8737 以後の job script 差分は freeze digest 定数のみ。ただし元 cohort 1 の source・事前登録 blob まで同一とは記さない。
- **P3：支持。** `qsub -v` の固定列挙に trace 保全の opt-in はない。
- **P4：修正。** bytes を保つ wrapper 案は可能性があるが、役割表示と closure の整合を先に解決する必要がある。測定値の固定検査を緩める根拠はない。
- **P5：支持。** D2050 に沿い、別 attempt・非合成の地位を結果と投入より前に固定する計画である。

静的検査のみ実施し、job・テストは実行していない。