---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2779-recovery-codex
seq: 1
title: [T-2779] mocc G2観測条件の中断結果を回収 — 通常5/120・診断0/120・backoff2/120 (docsのみ、branch worktree-dev-wave-t2779-recovery-codex)
---

## 本文

- ユーザー指定の中断回収。B1〜B4の既存done=0を回収し、再計測・補充を投入していない。
  着手時local main b2037abfaから専用Codex worktreeを作り、旧親のdirty差分・未収載commitがないことを確認した。
  旧親cwdのPID 1534820が生存していたため旧worktree・旧HANDOFFは非接触で保全した。
- 既存360走は全件保存済み、failure/indeterminate/未開始/未収載/不明は0。runner・arms・pin・patch・
  define・witness・source・policy・toolchainの束縛を照合した。原結果とrun.jsonの一致、
  7正例336 traceファイル (1,981,789,619 byte) のmanifest SHA一致を確認した。
- 検出数は通常5/120、診断0/120、BACK_OFF=1は2/120。未調整片側Fisherは0.0299507441/0.2230864755。
  family全体の有意性・G2不在・根因同定を主張せず、非certifyingの記録とする。
  witness軽量化は静的設計までで、規律2、certified昇格・pin前進・変異探索の扱いは不変。
- 段2/3/4の既存骨格を継承し、独立read-onlyレビュー2本を実施。双方must-fix 0・GO。
  Aのshould 1 (launcherはround数を引数で受ける) / nit 1 (stamp参照行) は本文で訂正。
  実装子のprobe保存commit 9a2a52550はmergeせず、runnerは逐語資料として保存する。
- 関連テストは正規run_tests経路で602 passed / 3 skipped (既存growth hold)、selftestは21/21。
  check_codex_agents / check_docs、holdout検出語scanはrc=0。
  受入attempt1はqueue-wait-timeoutと同時shard停止で判定なし。既存overrideで待ちを延長したattempt2は
  25,133 passed/69 skipped・child-green (tested tip 69fa71cd3)。
  その後のmain文書mergeでphase先頭追記を手動解消したためlandがnon-clean merge replayを拒否し、mainは動かなかった。
  両項を保持し、T-2779の完了記録を同checkpoint内で移して、解消済みの木を受入し直す。
  製品実装差分ゼロのため段4裁定どおり変異matrix免除。新規gate・台帳・一般化はない。
- 記録は output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md。
  生traceと実走runnerは元job dirに保全し、result JSON・正例判定・manifest・裁定・レビュー逐語はrepoへ保存。
  自己改善は専用handoffへ記録のみとし、改善実装・次waveは追加しない。

## 次の一手差分

### 完了

- [T-2779] 軽量witnessの静的設計と診断・backoffの既存各120走を回収し、束縛・欠測会計を独立レビューした非certifying観測記録として完了。
  remaining: none
  base: 2281ab297ee132a4c2a4a052fec7e5e502533e31ca064c9882a02a7ffae2d542
