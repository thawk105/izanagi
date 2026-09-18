# 親 brief (段 1、2026-09-18 11:25 JST) — [T-1878]

- 依頼 (逐語要約): mocc trace-hook (TRACE=1) pilot の raw verifier 出力 artifact を特定するか、不在を記録する (docs のみ、
  新規実装・計測なし)。探索範囲を pilot の insight (2026-08-22_t755、2026-08-23_t1506、2026-08-24_t1582、2026-08-26_mocc-trace-pair*、
  2026-08-26_mocc-g2-repro/) が名指す job dir・evidence dir (/work/1/SFC/tanab/izanagi-job-evidence/ 配下) と
  tools/pegasus/mocc_trace_pilot.sh の出力先に限定し、見つかれば path と sha256 を claim-evidence の [権威 bytes] 欄の後継記録
  (凍結物は上書きせず新しい日付の記録) と insight に書く。見つからなければ「探索した範囲での未特定」として範囲を明記し、
  全体での不在と断定しない。稼働中の T-2772 / T-2774 の成果物には依存しない。規律 2 を緩めない。本題の所在記録だけ。
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- 研究前進: claim-evidence 表 C14a の `[権威 bytes]`「未特定」を、執筆者が「どこを探して何が無かったか」を辿れる記録にする
- scope: docs のみ (insight 1 件 + `docs/paper-story/README.md` の claim-evidence 系列節へ日付付き後継記録 + worklog fragment)
- 確定済み裁定: D1013 (claim-evidence は append-only、一項目差分改訂を新日付 file として置かない)、D579、D920
- 不変条件: 凍結物 (`claim-evidence/2026-08-26.md`、8 月の insight 5 群、pair receipt) を 1 byte も変えない。規律 2 に触れない。
  全体での不在を断定しない
- 分割: 子ゼロの軽量版 + 段 6 read-only review 1 本 (entry 998 の教訓)。実装面差分ゼロ → 変異 matrix 免除 (DW-S04)
- (P1) 後継記録の置き場 = README の claim-evidence 系列節に日付付き stale 注記。新日付の claim-evidence file は D1013 規則 2 が禁じる。
  稼働 wave t2775 が同 README の版系列 stale 節 (件数行と項目) を編集中なので、その節には触れない

## 段 1 実測 (要点。全文は insight README §1〜§2)

- 出力先 = `$PBS_O_WORKDIR/output/env/pegasus/mocc-trace/job-staging/$PBS_JOBID/verifier.json` (2efe6282 の script)。PBS_O_WORKDIR = 投入 worktree
  `dev-wave-t755-mocc-trace-execution` (当時の handoff)。worktree・branch とも不在。`git log --all -- output/env/pegasus/mocc-trace` 0 件
- evidence dir に `934607.nqsv` 完全表記 0 件。名指し job dir 9 件で `934607.nqsv` 言及 13 file は全て insight 転記・handoff・codex events
- 当時の receipt は `verifier_json: "verifier.json"` 名のみ (sha256 なし)。insight 埋め込み JSON は `trace_dir` 等 3 key を欠き raw の逐語ではない
