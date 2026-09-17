---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2744-writer-priority-closure
seq: 2
---

## 再発

### F428

- **再発: 2026-09-18** — 2026-09-09 の再発 (実装 wave 自身が carry を閉じ損ねた型) と同型。
  [T-2744] (D2104 項 33、実 repo ロックの writer 優先) と [T-2745] (D2104 項 34、fold 失敗の巻き戻し通知 kind) は
  2026-09-17 の worklog entry 1611 (branch `worktree-dev-wave-f976-f977-lock-notify`、実装 commit `df2da88ee`、
  設計判断 D2112) が 1 wave で実装・land し、本文に「閉じた」「D2104 項 33 / 34 を実装した」と書いたが、
  次の一手差分は両 ID を carry stub のまま残した。fold は保存則どおり 1612〜1635 まで運び、2026-09-18 に
  [T-2744] の carry 本文 (「裁定済み → 実装手番」) を写した依頼で wave が起動した。着手前実測 (`DW-S01`) が段 1 で
  覆し、実害は実装子を 1 本も起動しないまま docs-only の終端記録へ切り替えたことで止まった。
  **新しい面は 2 つ。** (1) entry 1611 の本文は実装した項を T 番号でなく**裁定の項番号 (D2104 項 33 / 34)** で
  書いており、2026-09-09 の再発が「最も安く効く」と挙げた「同一 fragment 内で本文が閉じたと書いた ID が 完了 節に
  無い」検査は ID 一致では当たらない — carry 本文が引く D 番号と項番号から T へ写す対応表が要る。
  (2) 閉じ損ねた 2 ID は同一 wave の兄弟項 (同 D・同 commit) で、片方の依頼だけが起動した。一方を閉じるときは
  同 entry が同時に実装したと書く兄弟項を同じ fragment で照合する。lint は未実装のまま (本 wave の依頼が
  仮想リスク向け検査の追加を scope 外と明示)。局所修復として本 wave が [T-2744] [T-2745] を 完了 にし、
  段 8 で `docs/spool/worklog/README.md` の `完了` 規則へ「どの ID を置くか」(依頼が名指す T + 本文が実装した
  と書く作業の T、項番号で書いた作業は carry の T へ写す、兄弟項も同時) を 1 項足した。`DW-S07` (L1) は
  予算 10,625 bytes が満杯で 139 bytes 入らず (D782 の手順で spool 正本側へ収容)。

### F982

- **再発: 2026-09-18** — docs-only wave の焦点走 (`test_real_repo_serialization.py` + `test_spool_fold.py` +
  `test_dev_wave_land.py`、計算ノード request 4932.nqsv) で
  `test_real_repo_writers_do_not_materialize_oracle_environment_candidates` が既報と同じ WAL lock の JSON 不一致
  (`test_p3_s4_loop.py:7080`) で赤になった (633 passed / 1 failed)。変更面は spool fragment 2 本だけで
  wrapper・site 中立化 fixture・WAL・ident は触っていない。既報どおり `test_p3_s4_loop.py` を選択へ足した再走
  (request 4944.nqsv) は 1048 passed / 2 skipped / rc=0 で、選択形固有の偽赤と確定した。恒久対応は未実施のまま。
