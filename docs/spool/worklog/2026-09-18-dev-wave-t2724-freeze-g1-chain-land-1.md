---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2724-freeze-g1-chain-land
seq: 1
title: [T-2724] 凍結 v2 g1 の chain を main へ運ぶ wave — merge を準備し検証したが land せず、非 hold 5 node (並行 wave の実測を検算すると 45 node) が chain の hit で受入赤になり production の oracle gate も閉じる新事実を記録して再裁定へ戻した。退避 (e) は完了、T-1851 worktree は cleanup rc=20 で残置 (docs のみ、branch worktree-dev-wave-t2724-freeze-g1-chain-land、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2724] (D2120 項 2 (a)(d)(e)) 凍結 v2 g1 の chain を main へ運ぶ — (a) 保存 branch `freeze-g1-chain-t2724`
  (X1' cc82edc8c、X2 4d8fb93b7) を wave branch へ merge して land する。(d) growth hold 2 本が解除時に赤になる帰結を記録し
  hold は現行のまま。(e) `dev-wave-t1851-c3c-official-floor` worktree の失敗 run 3 件を固定退避先へ evacuate して worktree を
  撤去する (cleanup が rc=20 なら迂回せず残して報告)。(b) G は別 wave、A / X は人間 commit。本題の取り込み・記録・退避だけ」。
- 一次資料は `output/insights/2026-09-18/t2724-freeze-g1-chain-land/README.md` (裁定パッケージは同 §5)。decisions fragment は
  無し (新しい設計判断なし。D2120 (a) は有効のまま履行保留)。failures fragment は F370 の再発追記 1 本。
- **(a) は land しなかった。** merge commit `b227d0d91` (main `d2ebef7a4` + X2、X1'/X2 の SHA・7 blob 不変、provenance 3 件
  違反なし) を作って検証したが、段 3 相談 A-4 の指摘を親が焦点走で実測すると、**growth hold に載っていない 5 node
  (`test_s8b_floor_campaign.py` の E2E 1 + public preflight 4) が production `clean_scan_digest` の正しい拒否
  (`clean scan 拒否: rr80 / rr20 holdout hit 4 件` = chain の journal.jsonl / manifest.json / result.json / 候補) で赤**になった
  (計算ノード request 4968.nqsv、5 failed / 23.7 秒)。これらは通常の受入全走で走るため、land すると main の受入が恒久的に
  赤になり以後の全 wave の land が止まる。裁定 D2120 (d) が挙げた帰結は hold 下 2 node だけで、この 5 node は裁定文・
  worklog・package.md に未記録 (裁定時に未提示の受入上の波及) → DW-S04 に従い不採用にせず新事実を添えて再裁定へ戻す。
  merge commit は branch `freeze-g1-chain-t2724-merge-prepared` に保存 (G の親にはしない。削除はユーザー指示時)。
- **並行 wave (G 作成側 `dev-wave-t2724-freeze-g1-gen`) の実測を親が job dir の生 log で検算した (insight §3.1):** X1' を含む木で
  非 hold の赤は **45 node** (`test_s8b_oracle_driver.py` 40 + `test_s8b_floor_campaign.py` 5、request 5001.nqsv、45 failed /
  967 passed) で、**production の P3 gate-check も同じ holdout hit (`holdout.unknownness_layer2`) で refuse** する。T-080 receipt の
  live scan が zero-hit を要求し v2 closure が hit を期待集合に持つ矛盾が共通原因で、test fixture の是正 (択 1) では解けない
  → 上流は production 側の整合設計 (peer の裁定パッケージ 択 A)、択 1 はその下流。G = `32ba8cae4` (親 = X1'、branch
  `freeze-g1-gen-t2724`) は peer が保全して正式停止。両 wave は旧 main から独立に merge しているため後発の land は再受入が要る。
- **(d) は実測で記録した。** 権威 CLI 三軸走査: 対照 main hit 0 / 0 (positive 188、27,691 file、rc=0)、merge 済み木 hit 4 / 4
  (rc=1)。hold 下で解除時に赤になるのは D2120 の 2 node に加え第 3 の held node
  `test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null` (live scan → `unknownness_layer2` で拒否理由が
  増え完全一致検査が破れる、相談 B-3)。hold・test・除外集合は不変。
- **(e) は退避まで完了、撤去は未完了。** main 版 `s8b_floor_evacuation evacuate` (T-1851 の tip に module 無し) で固定 bundle は
  1 run → 4 run / 11 file (既存 5 file の sha 保持、追加 3 run は journal + cert のみ)。`dev_wave_cleanup.py` は
  rc=20 `wave worktree is dirty` (claims 3 件 + submissions 3 dir 約 123MB の untracked、裁定の名指し外) で残置。dirty が解けても
  admin 配下 hardlink 31 本で nlink 検査が rc=20 になる見込み。`/cleanup-branches` へ引き渡す。
- 段 3 / 4 相談 5 本 (A は親の射影 file 名誤りで fail-closed 停止 → A2 再投入、B、C = 是正の設計と規律 2 の射程判定、D = 攻撃)。
  C の判定: 択 1 (fixture を起動可能 base から作り chain 有り拒否を負例に足す test 変更) = c、hold 追加 = a、除外拡大 = a、
  main に載せない = b (D2120 が却下済み)。D は親方針に同意 (yes 0 / partial 3 / no 3)。推奨は択 1 を別 wave で実証してから
  chain を land。
- 実走: 三軸走査 3、焦点走 1 (計算ノード)、evacuate 1、cleanup 1、provenance range 監査 1、`check_docs.py`、
  `spool_fold.py --dry-run`、受入全走 3 回 (docs のみの木。1 回目は `test_t1259_qsub_env_delivery_probe.py` の setup で git 30 秒
  timeout 26 error = F945 型の非帰属赤、2 回目は child-green 24,824 passed だが並行 wave の検算を docs に反映するため lease を
  release して 3 回目を改訂後の木で投入、結果は land の受領証)。
- 工数: codex 子 5 本 (consult 5、全段 `gpt-6-astra` / `medium`)。実装子・review 子なし。

## 次の一手差分

### 更新

- [T-2724] **P1・ユーザー裁定待ち (D2120 項 2 (a) の履行形、裁定パッケージ = `output/insights/2026-09-18/t2724-freeze-g1-chain-land/README.md` §5)**:
  (a) は有効・履行保留 — chain を main に載せると非 hold で少なくとも 45 node (`test_s8b_oracle_driver.py` 40 +
  `test_s8b_floor_campaign.py` 5) が production gate の正しい拒否で赤になり main の受入が恒久赤になる上、X1' を含む checkout では
  production の oracle gate (P3 gate-check) も同じ holdout hit で refuse する (2026-09-18、親の実測 5 node + 並行 wave の実測を
  親が検算)。**上流の裁定 = T-080 receipt live scan の zero-hit 要求と v2 closure の整合を production 側でどう設計するか**
  (並行 wave `dev-wave-t2724-freeze-g1-gen` の裁定パッケージ 択 A と同じ問い、受理集合を変えるため規律 2 の射程)。下流の推奨 =
  択 1: floor_campaign 5 node の fixture を「official 成果物を持たない起動可能 base」から作り chain 有り tree の拒否を負例に足す
  test 変更 ({{T:floor-campaign-fixture-launchable-base}}) を land し、上流が閉じた後に chain (保存 branch
  `freeze-g1-chain-t2724`、参考 merge `freeze-g1-chain-t2724-merge-prepared`) を land。hold 追加・除外拡大は規律 2 の射程で
  推奨しない。(b) G = `32ba8cae4` (親 = X1') は並行 wave が branch `freeze-g1-gen-t2724` に保全済み、A / X はユーザー commit。
  (d) 記録済み (hold 下は 2 + 1 node)。(e) 退避済み (bundle 4 run)、T-1851 worktree は cleanup rc=20 dirty で残置 →
  `/cleanup-branches` (ユーザー指示)。(f) T-750 の P-1 / P-3 は別管理のまま。
  base: 0e9776de69cc561e014b042bc484d76a6f318f3d12c66fee2e3dd86b59bdbeaa

### 新規

- {{T:floor-campaign-fixture-launchable-base}} **P1・AI 手番 (設計・実装・実証は裁定前に着手可、land は [T-2724] の裁定後)**:
  `orchestrator/tests/test_s8b_floor_campaign.py` の実 HEAD clone fixture (`_clone_committed_head_with_ccbench` :2291、
  `_protocol_binding_public_preflight` :15609) を、committed HEAD から official namespace 全体と候補の exact path だけを外した
  起動可能 base に置き換え、chain 有り tree (official 成果物だけ / 候補だけ / 両方) の `clean_scan_digest` 拒否を負例として
  同 test に足す。production gate・走査除外・allowlist・hold は 0 byte。変更前後の tree 差分が宣言した削除集合だけであることを
  独立検査し、既存の正例・hash drift 負例・`bypass_drift_gate` 対照を残す。変異 matrix で search 拒否を外すと負例が失敗することを
  確認。chain 無し / 有りの両 tree で焦点走。Codex author。`test_s8b_oracle_driver.py` の 40 node (T-080 receipt live scan 経由) は
  production 側の整合設計 (上流裁定) に依存するため本 wave の scope に入れない。根拠は
  `output/insights/2026-09-18/t2724-freeze-g1-chain-land/README.md` §3 / §3.1 / §5。
