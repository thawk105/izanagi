---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-stranded-branch-audit-20260825
seq: 1
title: main へ未マージのまま残る branch 6 本を内容照合で着地判定し、回収対象ゼロを確定した (docs、branch worktree-dev-wave-stranded-branch-audit-20260825)
---

## 本文

- 対象 6 本を実測したところ **実質 5 本**だった。`worktree-workload-policy-hint-impl-unitB` と
  `unitC` は「内容が同一に見える」のではなく **同一 commit `500f47a6` を指す別名**である。
  `worktree-roadmap-workload-hint` (`15b5c389`) は unitB/C の祖先であり、独立した成果を持たない。
- **5 本すべて着地済みで、回収する成果はゼロだった。** 判定は ancestry と行数ではなく
  blob 同一性・`FOLDED.md` の receipt・pin 閉包の実値で行った。
- 判定の内訳。
  - `worktree-dev-wave-t1484-floor-restart-registry`: spool fragment 5 本は全て
    `content_sha256` が `FOLDED.md` の receipt と一致。insights 13 ファイルと
    `trial_registry.py` などは main と blob 一致。残る実装 3 ファイルと
    `docs/phase3-8b-restart-runbook.md` は **main が先行**しており、branch 側は
    後継 wave (`worktree-dev-wave-t1578-t1579-t1431-floor-restart`、エントリ 906) が
    置き換えた段階 5-A の旧状態だった。branch は `RecoveryPolicy`・`recovery` event・
    D740 の閉集合を**持たない**側であり、main はその上位である。
  - `worktree-workload-policy-hint-impl-unitB` / `unitC` ([T-1419]): `docs/roadmap.md`、
    `s8b_descriptor.py`、`s8b_descriptor_schema.json`、`test_s8b_descriptor.py` が
    main と blob 一致。残る 5 ファイルの差分は schema pin 閉包のみで、**新値が main に在り
    旧値は main から消えている**。`D:workload-policy-hint` → D568、
    `T:workload-policy-hint-impl` → `[T-1419]` がいずれも採番済み。
  - `worktree-rulings-20260818-floor-measurement`: decisions 側 fragment は
    `content_sha256` が receipt と一致。worklog 側 fragment は byte が一致しないが、
    同題のエントリが `docs/archive/worklog-phase3-0819-670.md` に着地しており、
    そちらは base 不一致の照合注記を持つ **carry 解決済みの上位互換**である。
  - `worktree-t1458-side-ccbench-provenance-fix`: 唯一の fragment が receipt と一致。
- **正しさ防壁の取り残しは無い。** `attempt_registry_core.py` の guard 5 種
  (`forbid_retry_after_observation`、`cannot authorize a retry`、
  `non-retryable outcome cannot be consumed`、`observation_start_event_sha256`、
  `attempt-slot-order`) を両側で数え、main は全て同数以上
  (`attempt-slot-order` は main 6 / branch 5) だった。branch 固有の 18 行 / 12 行は
  同じ検査の旧表現で、main が落とした検査ではない。
- **判定手順の落とし穴 2 件。** (a) `git diff main <branch>` の二点比較は main 自身の前進を
  全部拾うため着地判定に使えない (本件では 2821 files・85 万行規模のノイズになった)。
  branch の成果は merge-base からの三点側で取り、各 path を main の blob と個別照合する。
  三点側の行数をそのまま未着地量として読む型は F270 の 3 例目に既出。
  (b) 最初に書いた照合器が全 fragment を「main に別内容で存在」と誤って読み、
  作り直した。原因と恒久対応は {{F:sentinel-concatenated-with-failed-command-stdout}}。
- **fragment の byte 不一致は未着地の証拠にならない。** `FOLDED.md` の receipt は
  fold した実体の hash であり、carry 解決や wave 名の付け替えで byte が変わる。
  本件の 3 本は receipt と hash が合わなかったが、いずれも採番済み ID か
  着地済みエントリで実体が確認できた。hash 不一致で止まったら、次に ID の採番状況と
  canonical 側の同題エントリを見る。
- branch と worktree は削除していない (ユーザー指示があるときのみ)。
- **受入 attempt 1 は F136 の同日 3 例目で 11 件赤になった** (11 failed / 15,284 passed /
  60 skipped、差分は 11 件とも `('dir', 'task-runs/reports')`)。帰属は 3 点で否定した —
  差分 2 file が `launch_cert` / `certificate` を 1 箇所も参照しない、同 file の焦点走が
  451 passed / 2 skipped で緑、junit 差分が実装でなく `output/task-runs/` の dir 増加を指す。
  直前の docs-only wave (2 例目) と赤の件数・assertion 本文・焦点走の内訳が完全に一致しており、
  この赤の決定性を F136 へ追記した。attempt 2 を本 commit を含む tip へ投入した
  (走行結果の正本は受入 receipt)。

## 次の一手差分

### 新規

- {{T:stranded-branch-6-deletion}} **P3・新規**: 本エントリで着地済みと確定した branch 5 本
  (`worktree-dev-wave-t1484-floor-restart-registry`、
  `worktree-workload-policy-hint-impl-unitB`、`worktree-workload-policy-hint-impl-unitC`、
  `worktree-rulings-20260818-floor-measurement`、
  `worktree-t1458-side-ccbench-provenance-fix`、
  および祖先の `worktree-roadmap-workload-hint`) の削除可否をユーザーが判断する。
  内容は全て main に在り、失われる成果は無いことを確認済み。AI 側からは削除しない。
