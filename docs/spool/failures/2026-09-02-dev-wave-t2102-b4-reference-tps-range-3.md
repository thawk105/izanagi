---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2102-b4-reference-tps-range
seq: 3
---

## 再発

### F103

- **再発: 2026-09-02** — detach は正しく行ったが、**Write tool で作った runner `.sh` に
  実行権が付かない**ため、`bash -c "\"$JOB/run-s2-plan.sh\"; echo $? > ...done"` の
  直接 exec が `許可がありません` で落ち、段 2 の plan 子が 1 度も起動しなかった。
  `.done` には wrapper が書いた `126` だけが残り、log は 0 byte、artifact dir も空。
  子が消えたのではなく最初から生まれていない点が F103 本体と違うが、
  **背景投入の手順が必要条件を全部書いていないために子が起動しない**という型は同じである。
  `DW-C01` は「隔離 worktree の detach は runner/launcher の `.sh` へ外出し」を義務づけるが、
  その `.sh` の**呼び方**を規定していない。恒久対応は launcher から
  `bash "<path>"` で呼ぶこと (本 wave の `launch-s2-plan2.sh` /`launch-s3.sh` /
  `launch-s3b.sh` / `launch-acceptance*.sh` はすべてこの形)。再投入では
  `--job-id` と `.done` / `.pid` / `.log` の名前を変えて既存 `.done` を消さない。
  `DW-C01` への 1 行追記は単節予算 1000 bytes に対し現行 996 bytes で入らず、
  節全体が exact pin されているため見送った。検知は `.done` が `126` で
  log が 0 byte のときに実行権を最初に疑う。
