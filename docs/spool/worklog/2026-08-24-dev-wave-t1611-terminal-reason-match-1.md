---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1611-terminal-reason-match
seq: 1
title: [T-1611] 8c の理由一致検査を前向き formal 経路 3 本で締め互換 facade を bytes 不変に保った (コード+テスト、branch worktree-dev-wave-t1611-terminal-reason-match、変異matrix = baseline PASSED・7/7 KILLED・SURVIVED0・MISMATCH0)
---

## 本文

- 一次資料は D741 (理由一致検査の版境界での必須化)、D735 (遷移 policy の profile 注入)、
  D672 (互換抽出の受理集合不変)。設計判断は
  {{D:s8c-forward-only-strict-formal-boundary}}。
- **本 wave は 2 つの context にまたがる。** 前半 (段 1〜段 6 第 3 fix 巡) は別 context が進め、
  Codex 利用上限で 14:32 に停止した。後半 (段 6 の変異以降) は別 context が孤児として発見し
  巻き取った。停止時の表示は「再開可能 2026-08-27 22:17」だったが、実際には同日中に上限が解けており、
  巻き取り時点で Codex 子は正常に動いていた。**表示された回復時刻を額面どおり受け取ると
  3 日分の待ちを作る**という点で F411 の supersede と同じ構図である。
- 巻き取りの発見手順は、worktree 53 本に対する (a) 全 PID の cwd と cmdline 走査による占有、
  (b) job dir の最終書込み時刻、(c) branch が main の祖先か、の 3 点分類である。
  同じ利用上限で同時に倒れた wave は本 wave を含め 4 本だった。
- 段 3 の敵対レンズが「terminal 入口だけ strict」案を real な不足として棄却したのが本 wave の
  分岐点である。予約と acceptance が互換のままでは受理集合が変わらず、締めたつもりの恒真ゲートに
  なっていた。段 4 で refuted と裁定した所見は、core の exact 比較不足 (strict profile を渡せば
  null matrix 前に拒否する)、8b profile / retryable 集合 / schema・path の変更要否 (いずれも no-touch)
  の 2 件である。
- **C03 は本 wave の変更で `EVIDENCE_UNDEFINED` から `UNSATISFIED` へ変わった。** 段 4 の裁定に従い、
  evaluator の編集・dead な旧呼び出しの温存・登録の充足化のいずれも行わず、状態報告に留めた。
  最終 commit で判定器を library 経路から再評価し、C03 以外の 11 条件が `EVIDENCE_UNDEFINED`、
  総合が `PREREGISTRATION_NOT_EFFECTIVE` であることを確認した。逐語は
  `output/insights/2026-08-24_t1611-terminal-reason-match.md`。
- 焦点走は `DW-O26` に従い、変更 production 2 module を参照する consumer を grep で引き直して
  24 file へ拡張した (前 context の 7 file より広い)。2321 passed / 3 skipped / 0 failed。
  前 context で赤だった C03 snapshot node も緑になり、第 3 fix 巡の効果を実測で確認した。
- 段 6 の敵対レビュー 2 本と焦点レビュー 1 本、fix 3 巡はすべて前 context の成果である。
  focus1 が採用した must-fix (C03 snapshot の期待 status 1 箇所の同期) を第 3 fix 巡が実装したが、
  その巡の実走は Pegasus の `qstat -Q` 事前確認失敗で `child_started=false` に終わっており、
  **緑の裏取りは巻き取り側の焦点走が初めて行った。**
- 変異は本走を 3 回投入した。**測定は 3 回とも baseline PASSED / 7 KILLED / matching 7 で同一**である。
  1 回目は wrapper の共有木事後検査が `shared_snapshot_matches=false` で abort したが、
  条件を変えない再投入 (2 回目、source = 本 wave の worktree) が検査ごと通り、間欠性が確定した。
  3 回目は source を独立 clone にして観測 root を 1 本へ閉じたもので、こちらも完全緑である。
  親は 2 例の時点で「混雑下では構造的に成立しない」と誤って一般化し、
  並行セッションからの 2 度の指摘で帰属と結論を訂正した。
  経緯は {{F:mutation-wrapper-two-root-shared-check}}。
- 親は停止 wave の候補一覧を 20 分前のスナップショットのままユーザーへ提示し、
  25 分後には 6 件すべてが着地または他セッション確保で空振りになっていた。
  ユーザーは一括起動を明言していたため、指摘が無ければ全件が無駄になっていた。
  経緯は {{F:stopped-wave-inventory-goes-stale}}。
- 待ち手で F32 を再発させた。`pgrep` で外から拾った pid が中間 process で、走行中の変異本走を
  完了と誤報した。2026-08-11 の恒久対応 (producer 自身に pid file を書かせる) に反している。
- 並行 wave との重複は、本 wave の所有 6 file のうち
  `orchestrator/tests/test_attempt_registry_core_s8b_profile.py` だけが T-1601/T-1602 と共有だった。
  同 wave が先に land した後、AST で top-level 定義名を突き合わせて衝突ゼロを確認している
  (base 41 / 本 wave 追加 9 / main 側追加 36、交わりなし、main が消した名で本 wave が触るものもなし)。

## 次の一手差分

### 完了

- [T-1611] 前向き formal 経路 3 本を strict 化し、変異 matrix で裏取りした。受入全走は本記録 commit の後に投入する。
  remaining: none
  base: 6b4169e5b074bb3f2f1ff26d1a4f1fce4d91f4d377d26b005b929a4a663ecbc9

### 新規

- {{T:merge-overlap-diff-base}} **P3・裁定待ち**: main 取り込み前の並行 wave 重複測定について、
  基点を前回の取り込み commit にする旨を `DW-O18` へ入れる。`HEAD` 基準の差分は自分の wave の
  変更も拾うため重複判定に使えない。自然な行き先である `DW-O18` は L2 予算 1000 byte を
  使い切っており、既存の安全義務を削らずには入らない。予算値を上げる変更は独立審査の対象なので、
  実装せず裁定へ返す。事故は伴っておらず、本 wave では測り直して非重複を確定している。
