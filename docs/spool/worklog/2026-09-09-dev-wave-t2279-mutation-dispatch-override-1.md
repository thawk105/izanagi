---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2279-mutation-dispatch-override
seq: 1
title: [T-2279] 変異 harness へ D612 の上書きが届かない食い違いを特定した — 2026-09-07 に別 wave の副産物で解消済みで、今日残るのは外側 watchdog と dispatcher 締切の不一致という別の欠陥 (コード変更ゼロ、branch worktree-dev-wave-t2279-mutation-dispatch-override)
---

## 本文

- 依頼は「食い違いを特定し、特定できた分だけを直す」。特定は完了し、**修理対象は残らなかった**。
  2026-09-03 の 904 秒は当時の収集経路が dispatcher を上書きなしで直呼びしていたためで、
  その経路は 2026-09-07 の commit 1e22c4cbd (T-2337 wave の副産物) が既に塞いでいた。
  今日の HEAD で上書きが届かない経路は 0 件である。一次資料は
  `output/insights/2026-09-09_t2279-mutation-dispatch-override/README.md`。
- 段 2 プラン 1 本と段 3 敵対レンズ 2 本 (いずれも read-only codex) を独立に走らせ、
  「伝播は全経路で成立」「904 秒は当時の収集経路」の 2 点で結論が一致した。
- **親 brief の誤り 4 件を段 3 が名指しし、段 4 で訂正した。** (1) watchdog の timeout が mutant の
  TIMEOUT として台帳へ帰属するという読みは誤りで、実際は orphan hold へ変換され rc=2 で全走が
  止まる。(2) fresh baseline と非 hang 変異を欠陥に含めたのは過大。(3) F762 の「本走も dispatcher
  直呼び」は誤り。(4) 「1800+300 = 待ち 2100 秒」は dispatcher の締切構造と違う。
- **段 2 が出した早期拒否 gate は不採用にした。** 主題外であること、式 `outer < Q + G` が
  dispatcher の締切構造 (queue は Q 単独、G は RUN 後、cleanup は別予算) を表していないこと、
  現在完走しうる設定を起動前 rc=2 に変えて受理集合を縮めることの 3 点による。両レンズが独立に
  不採用を支持した。
- 新規に特定した欠陥は {{T:mutation-watchdog-dispatch-deadline-contract}} として登録し、
  実装せずユーザー裁定へ返す。式を決めずに実装すると、不採用にしたのと同じ誤りを別の場所で犯す。
- F762 の記述が stale であったことが本 wave の brief を誤らせた。supersede 追記で訂正した。
- 受入全走は 4 回投入した。1 回目は緑 (child-green、22078 passed) だが land が全史 provenance 監査中の
  main 進行で rc=29、2 回目も緑で land が stale-main (rc=10)。3 回目は 2 回目の lease が自分名義で
  残っていたため `claim-self-unverified` で terminal 停止した。land 経路は lease を解放できない
  (`--lease-dir` を受け取らない) ので、`tools/wave_land_window.py release` で明示解放してから
  投げ直した。4 回目は
  `orchestrator/tests/test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed` の 1 件が
  赤 (22078 passed)。本 wave の差分は docs だけで、この test は codex launcher の SIGTERM 処理を
  見るものなので差分から到達できない。単独再走は緑で非再現だったため、DW-O18 に従い受入を投げ直した。

## 次の一手差分

### 完了

- [T-2279] 変異 harness 経由で D612 の上書きが効かない食い違いを特定した。904 秒の層は当時の
  収集経路の queue-wait 既定 900 秒で、その経路は 2026-09-07 に解消済み。今日の伝播欠落は 0 件で
  修理対象なし。新規に見つけた別欠陥は {{T:mutation-watchdog-dispatch-deadline-contract}} へ分離した。
  remaining: none
  base: ddb420e61a305fecc25fb59cba01d20fb52bae462b88470c5949c1c187430cb9

### 新規

- {{T:mutation-watchdog-dispatch-deadline-contract}} **P2・ユーザー裁定待ち**: 変異 harness の外側
  watchdog (`spec.timeout_seconds` / `hang_timeout_seconds`) が dispatcher の締切構造のどの区間を
  覆う契約かを決める。dispatcher は queue 待ちを `queue_wait_timeout_s` 単独で、RUN 後を
  `walltime + overall_grace`、cleanup を別予算で判定するので、既存の collection gate が使う
  `outer < Q + G` は過剰拒否と取りこぼしの両方を作る。発火する実在 artifact は
  `output/insights/2026-09-07_t2195-policy-binding/mutation-spec-final.json` (timeout 3600 /
  hang 900、hang_risk 変異 5 件) で、上書きを設定して混雑時に走らせると最初の該当変異で外側
  watchdog が先に発火し orphan hold と rc=2 になる。裁定すべきは (a) 契約の定義、(b) 既存
  collection gate の式を合わせるか (受理集合が緩む方向)、(c) 拒否でなく理由付きの早期診断に
  留めるか (受理集合を動かさない)。根拠は
  `output/insights/2026-09-09_t2279-mutation-dispatch-override/README.md` 第 3・4 節。
