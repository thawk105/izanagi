---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2744-writer-priority-closure
seq: 1
title: [T-2744] 実 repo ロックの writer 優先は 2026-09-17 (1611) が実装・land 済みだった — 依頼の局所修正は二重に届けず、[T-2744] [T-2745] の carry を終端して F428 再発を記録した (docs のみ、branch worktree-dev-wave-t2744-writer-priority-closure、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2744] (D2104 項 33、ユーザー裁定) 実 repo ロック (`orchestrator/tests/conftest.py` の real-repo lock、read = LOCK_SH / write = LOCK_EX) に writer 優先 (待機 writer がいる間は新規 reader を待たせる) を局所修正として入れる (F976 の機構側対処)。既存 lock 契約と deadline の意味は変えない。Codex author (D95)、変異 matrix (writer 待機中の reader 拒否の負例) と焦点走。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の局所修正だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **着手前実測 (`DW-S01`) で前提が覆った。実装しない (段 4 → 7 → 8 → 9)。** 依頼の局所修正は 2026-09-17 の entry 1611 (branch `worktree-dev-wave-f976-f977-lock-notify`) が Codex author ×2 で実装し、変異 matrix (負例 11/11 KILLED・等価 1 SURVIVED) と受入全走 (child-green、tested main `48e3ff9e5` / tip `be21eb0b5`) を通して land 済み (実装 commit `df2da88ee`、記録 `3b160bb31`、land receipt `land-once-3.json` = landed、landing tip `5aec51501`)。設計判断は D2112、F976 には supersede 追記 (2026-09-17) が既に入っている。現行 main `d2ebef7a4` の `orchestrator/tests/conftest.py` に `.gate` flock (fresh 取得と昇格で writer が保持し、reader は実 repo lock を 1 つも持たないときだけ検査) が在り、正例・負例は `orchestrator/tests/test_real_repo_serialization.py`。
- **閉じ損ねの機序は F428 の 2026-09-09 再発と同型 (実装 wave 自身が 完了 節を書かなかった)。** entry 1611 の本文は「閉じた」「D2104 項 33 / 34 を実装した」と書いたが、次の一手差分は [T-2744] [T-2745] を carry stub のまま残し、1612〜1635 まで運ばれた。本 wave はその carry 本文を写した依頼で起動した。新しい面 (本文が T 番号でなく裁定の項番号で実装を書いた / 兄弟項の片方だけが依頼になった) は F428 の再発追記に書いた。
- [T-2745] (D2104 項 34、`tools/wave_land_window.py message --kind rolled-back`) も同 wave・同 commit・同 D2112 で済 (現行 main の同 file に `rolled-back` kind が在る) なので同時に閉じる。
- 段 2・3・5・6 は省略 (docs-only、設計択一なし、正しさ防壁・受理集合に触れない)。F428 の lint 化 (closing commit と carry の機械照合) は依頼が仮想リスク向け検査の追加を scope 外としているので実装せず、再発の事象だけ台帳へ追記した。
- 実走 (runner が計算ノードへ dispatch): 焦点走 f1 (`test_real_repo_serialization.py` + `test_spool_fold.py` + `test_dev_wave_land.py`、request 4932.nqsv) は 633 passed / 1 failed / 2 skipped で、赤は `test_real_repo_writers_do_not_materialize_oracle_environment_candidates` の WAL lock 不一致 = F982 (狭い file 選択の wrapper 偽赤) の署名。F982 の手順どおり `test_p3_s4_loop.py` を足した f2 (request 4944.nqsv) は **1048 passed / 2 skipped / rc=0** で、writer 優先 gate の正例・負例は現行 main でも緑。受入全走は land の receipt 要件として 1 回 (対象の再検証ではない。結果は land の受領証)。
- 工数: codex 子 0 本 (docs-only、`DW-C00` の既定軽量版)。親の実測: 済照合 (conftest grep、`merge-base --is-ancestor`、1611 wave の job dir の receipt / land log / wave-usage)、`check_docs.py`、`spool_fold.py --dry-run`、三軸語走査、焦点走 2 本 (F982 の再測を含む)。

## 次の一手差分

### 完了

- [T-2744] 実 repo ロックの writer 優先 (D2104 項 33) は 2026-09-17 (1611) が実装・land 済み (commit `df2da88ee`、D2112)。本 wave は二重に実装せず終端した。
  remaining: none
  base: f6bb52dbd6158c740fe5506fb01bf7c4fba0310ddac4e7b4cc441c9e801b6425
- [T-2745] fold 失敗の巻き戻し通知 (D2104 項 34) は 2026-09-17 (1611) が `wave_land_window.py message --kind rolled-back` として実装・land 済み (commit `df2da88ee`、D2112)。同 wave の兄弟項として本 wave が終端した。
  remaining: none
  base: 3b99b8eb82feea6215f082f058d09a3d03e4c1d6383d818be8d1bac2114d766c
