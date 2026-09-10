# [T-989] worker_id/nodeid/start/finish 一時診断 — 実装・検証・revert (2026-08-20)

## 経緯

[T-989] real-repo グループ部分除外 NO-GO (2026-08-19、worklog entry 686) の
insight package が「次に着手するなら worker_id/nodeid/start/finish の一時診断
実装から」としつつ「本 wave ではこの診断の実装を推奨しない (投資対効果不明)」
という留保を明記していた。ユーザーはこの留保を読んだ上で、一時診断の実装と、
価値が低ければ revert して insight のみ記録することを明示的に許可し、本 wave
(dev-wave-t989-realrepo-worker-diag) を起動した。

## 実装した内容 (revert 済み、commit 履歴に残る)

`orchestrator/tests/conftest.py` の既存 `pytest_runtest_logreport` hook を、環境変数
`IZANAGI_T989_WORKER_SPAN_LOG` (未設定なら完全 no-op) でゲートした診断で拡張した。
setup/call/teardown 各 report の worker_id (`PYTEST_XDIST_WORKER`)・nodeid・start・stop
を JSONL 1行として O_APPEND 追記する。fail-open、repo tree 内への書き込み拒否、
xdist crash 合成 report (`when="???"`) 除外を実装した。

- 段2 codex plan → 段3 敵対相談2レンズ (正しさ境界・実効性/一般化) → 段4 親裁定
  (plan v2 確定) → 段5 実装 → 段6 敵対レビュー2レンズ → fix2回 → 焦点再レビュー →
  変異matrix、の全段を完走した。
- **変異matrix: baseline PASSED (15/15)、登録4件全て KILLED、期待node完全一致、
  SURVIVED 0・MISMATCH 0。** 診断コード自体の技術的健全性は証明された。
- 統合commit: `0296a5f92373f76f510a3ccb7adea622a1647cb0` (revert前)。
- 詳細プロセス記録は wave の handoff/job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t989-realrepo-worker-diag/`) に残る
  (`stage1-brief.md`〜`stage4-ruling.md` が段階裁定の一次資料)。

## revert した理由 (二重)

### 理由1: 測定基盤の構造的な壁 (今回新たに判明)

段6測定手順どおり `IZANAGI_T989_WORKER_SPAN_LOG` を指定した全テストスイート実測
(`tools/run_tests.py --force-dispatch`、13,881 items) を実行したが、**診断出力
ファイルは作成されなかった。**

原因を `tools/pegasus/dispatch_compute.py` の実物で特定した。`"tests"` task の
`env_allowlist` (89-103行) は `PYTEST_ADDOPTS`・`IZANAGI_TEST_NPROC`・
`IZANAGI_TEST_TRIGGER`・`IZANAGI_TASK_RUN_SIDECAR`・`IZANAGI_TASK_RUN_AUTO_RECORD`・
`PYTHONDONTWRITEBYTECODE`・`IZANAGI_T080_E2E`・`IZANAGI_RUN_GROWTH_HELD_TESTS` だけの
**閉じた集合**であり、1536-1540行の
`request_env = {key: command_env[key] for key in spec.env_allowlist if key in command_env}`
が qsub へ渡す環境をこの集合だけに厳密に絞る。コメント (84-85行) が明記する通り
「任意 command 化はしない」(D103 決定5) を根拠とする意図的設計であり bug ではない。

**含意**: 受入全走はほぼ確実に計算ノードへ dispatch される規模 (13,000+ test) なので、
このアーキテクチャ上の壁を回避して worker span を実測するには、
`tools/pegasus/dispatch_compute.py` の env allowlist という**20以上の並行稼働
セッションが共有する dispatch のセキュリティ境界**を拡張する必要がある。一時診断
のためだけにこれを行うのは対象の重さと著しく不釣り合いであり、本 wave では
見送った。

### 理由2: worker span は因果的指標ではない (段3 レンズBが指摘)

段3 敵対相談レンズB (実効性・一般化) が、たとえ測定に成功しても次の理由で
decision-relevant でない可能性が高いと指摘した。

- **worker span (occupied interval の union) は、除外時の wall 短縮量を意味する
  因果的指標ではない。** real-repo group が wall の 100% を占有していても、他
  worker の仕事が同じ時間を埋めていれば除外効果はゼロになり得る。逆に短い末尾
  区間でもwallを決める場合がある。
- D258 (2026-08-10、real-repo group 直列和が critical path 下界) と D358
  (2026-08-13、排他機構を丸ごと無効化しても予測利得に届かない) は**下界の実測**と
  **過去の反実仮想結果**であり、今回の観測値から因果効果を導く根拠にはならない。
- レンズBが提示した「測定結果 → T-989処遇」の決定表 (詳細は本 wave の
  `stage4-ruling.md`) では、**5行中4行が診断コードのrevertへ帰着し、唯一
  revert以外の結果 (real-repo groupがwall終端付近まで占有) でも「D358は覆らない」
  という条件付き継続にしかならない。** すなわちこの診断が生み出しうるどの結果も、
  部分除外の実装を正当化する根拠には到達し得ない。

## 結論

**[T-989] は本 wave で調査を完了し、これ以上の再訪を推奨しない。** D258・D358・
2026-08-19 wave (n=1測定の限界)・本 wave (診断の技術的実現性と測定基盤の壁、
worker span の非因果性) の4波にわたる独立した調査が、いずれも「real-repo group
の排他機構を変更して受入を速くする路線」を閉じる方向で収束した。今後この路線を
再訪する場合の前提条件:

1. `tools/pegasus/dispatch_compute.py` の env allowlist 拡張が正当化される
   **別の**明確な用途が先に生まれていること (一時診断単独の正当化では足りない)。
2. worker span 相当の観測から**因果的な** wall 短縮効果を推定する方法論
   (例: 実際に対象を除外した A/B 比較、複数run のペア比較) を用意すること —
   単発の occupied span 観測では原理的に不十分。

受入全走時間そのものの伸び (2026-08-15: 128〜149s → 2026-08-19: 183〜274s →
2026-08-20実測: 202s、テスト数増加との交絡が未分離) は本 wave の scope 外のまま
残っており、[[test-time-regression-rule]] の監視対象として別途フォローが要る。

## 一次資料

- 段階裁定・敵対相談・レビューの全文:
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t989-realrepo-worker-diag/`
  (`stage1-brief.md`, `stage2-plan-attempt2.md`, `stage3-lensA.md`, `stage3-lensB.md`,
  `stage4-ruling.md`, `stage6-reviewA.md`, `stage6-reviewB.md`, `stage6-focus.md`,
  `mutation-spec.json`, `mut-main-out.json`, `measurement-run1.log`)
- 実装 commit (revert 済み): `0296a5f92373f76f510a3ccb7adea622a1647cb0`
- revert commit: `e893bbc9` (amend 後、AI-Agent trailer 修正はユーザー明示許可済み)
- D258: `docs/decisions.md` 該当節、D358: 同上
- 前回 wave insight: `output/insights/2026-08-19_test-bottleneck-real-repo-group/package.md`
