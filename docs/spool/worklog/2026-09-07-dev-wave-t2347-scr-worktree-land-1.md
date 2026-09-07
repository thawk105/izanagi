---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2347-scr-worktree-land
seq: 1
title: [T-2347] 計算ノード job の scratch worktree 登録で land が rc=31 になる経路を直す — 判定を「解決できたか」から「path が不在か」へ変え、登録は 1 件も捨てない (コード + テスト + docs、branch worktree-dev-wave-t2347-scr-worktree-land、変異 8/8 KILLED)
---

## 本文

- ユーザー指示 (dev-wave 引数): F851 が挙げた 2 案 — (a) `tools/dev_wave_land.py` の
  `_registered_worktree_paths` が prunable (path 不在) の登録を非接触検査から除く、
  (b) job script が job 専用 clone を使う — の**どちらかを入れる**。正例 (login 上の登録は従来どおり
  検査される) と負例 (`/scr/` 登録があっても land が進む、ただし実在する他 worktree の dirt は
  今までどおり拒否) を test に固定する。Codex author (D95) 必須。本題の実装だけで、
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- **案 (a) を採ったが、ユーザー引数の「prunable の登録を除く」という形は採らなかった。**
  段 3 の敵対相談が穴を挙げ、親が使い捨て repo で実測して却下した (逐語は insight の
  `git-worktree-porcelain-probe.txt`)。(1) `worktree list --porcelain -z` はこの機体の git 2.34.1 に
  無く (`rc=129`) record 境界を一意にできない。(2) `prunable` は path 不在を意味せず、directory が
  実在し `.git` file だけ壊れた登録にも出る。(3) path に改行を含む**実在**の worktree は
  `prunable <後半>` 行を偽装できる。代わりに `Path.resolve(strict=True)` の `FileNotFoundError`
  だけで分岐し、**登録を 1 件も捨てない**形にした。詳細は {{D:fold-gate-absent-registration}}。
  この形は marker 方式が取り逃す「locked かつ path 不在」も同じ経路で通す。
- **段 2 プランは却下した。** 段 2 が起草した `prunable` marker 方式は上の実測で穴が確定したため、
  段 4 で親が plan v2 へ置き換えた。段 2 の成果物自体は無駄ではなく、テスト設計と変異候補は採用した。
- **段 6 の敵対レビュー 2 本はどちらも must-fix ゼロ。** nit 3 件 (T5 が `NotADirectoryError` /
  `ELOOP` / `RuntimeError` を直接固定していない、T9 が不在登録 1 本で F851 逐語の 2 本を再現して
  いない、追加テストが `worktree add` を延べ 20 回行う) はいずれも「放置しても land 判定の値は
  変わらない」と自認しており、`DW-G05` により backlog とした。fix 巡は回していない。
- **セッション異常が 2 回あった。** どちらも process 異常終了による自動再起動で、作業物の損失は
  無かった (branch・worktree・子の成果物はいずれも保たれていた)。
- **道具の実測。** (i) `tools/dev_wave_codex.py` は author / review / fix / focus 段で
  `--reasoning` を受け付けず rc=2 になる (`DW-C01` の既記載を実測で確認した)。1 回目の実装子投入が
  これで落ち、実装は 1 行も走っていない。`--job-id` を変えて再投入した。
  (ii) `tools/run_tests.py` の 1 回目が `rc=16 orphan-hold` で戻ったが、job (980096.nqsv) は実際に
  投入されており、job 終端とともに hold は自動的に消えて `child_rc=0` の result.json が残った。
  hold の `phase=pending-qsub` / `request_id=null` は qsub 窓の一時 file であり、手動削除は不要だった。
- **エージェント工数**: codex 子 6 本 (plan 1、consult 2、author 1、review 2。すべて
  `gpt-5.6-sol` / `xhigh` / `accepted`)。author は 1 回失敗して再投入したので投入は 7 回。
  計算ノード job は焦点走 2 本 + 変異 2 走 (probe 9 run / final 9 run)。
- 実測の一覧と逐語は `output/insights/2026-09-07_t2347-scr-worktree-land/`。

## 次の一手差分

### 完了

- [T-2347] `_registered_worktree_paths` を `FileNotFoundError` 分岐へ変え、path 不在の登録を捨てずに
  残す形で F851 を閉じた。T1〜T10 で正例・負例・end-to-end を固定し、変異 8/8 KILLED。
  remaining: none
  base: 7c55c8fc43b55e8c12adb561d25d8883e11248793a4ccd2aaa72d2232bc40f9e

### 新規

- {{T:a5-superproject-worktree-residue}} **P3・新規**: `tools/pegasus/a5_second_boot_backoff_sweep.sh` の
  終了 cleanup は CCBench 側しか `worktree prune` せず、superproject 側の scratch 登録は job が
  SIGKILL された場合などに共有 repo へ残りうる。land は {{D:fold-gate-absent-registration}} で
  塞がれなくなったので緊急性は無いが、登録簿が伸び続ける。job script 側で superproject も
  prune するか、F851 案 (b) の job 専用 clone へ寄せるかを決める。Codex author。
- {{T:worktree-registry-consumers-scr-audit}} **P3・新規**: worktree 一覧を引く他 tool
  (`tools/mutation_worktree.py`、`tools/mutation_fanout.py`、`tools/check_acceptance_reds.py`) が
  `/scr` の path 不在登録で同型に壊れるかを検査する。本 wave では scope 外として**検査していない**
  ため、緑とも赤とも判定できていない。壊れる箇所があれば同じ `FileNotFoundError` 分岐へ揃える。
  Codex author。
- {{T:fold-gate-registry-test-widening}} **P3・新規**: 段 6 レビューの nit を閉じる。T5 の
  fail-closed 検査を `NotADirectoryError` / `OSError(ELOOP)` / `RuntimeError` へ広げ、T9 の
  end-to-end を F851 逐語どおり不在登録 2 本へ増やす。どちらも現行の land 判定の値は変えず、
  回帰検知の幅だけを広げる。Codex author。
