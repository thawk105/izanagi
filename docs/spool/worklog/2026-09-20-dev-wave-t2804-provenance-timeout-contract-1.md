---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2804-provenance-timeout-contract
seq: 1
title: [T-2804] land の provenance 監査 timeout (480 秒) と dispatcher の queue 待ち上限 (900 秒) の両立契約 C-2804 を実装した — 外側 480 秒は固定し、land が絶対 monotonic 期限を env で渡して checker が dispatcher の締切を導く (D2148 項 8 の実装ではなく land 固有の限定契約、延長は裁定パッケージへ)。段 1 実測 = 受領証 85 件で queue 待ち中央値 5.2 秒・最大 716.5 秒、RUN 中央値 30.7 秒 (コード + テスト、branch worktree-dev-wave-t2804-provenance-timeout-contract、変異 matrix = baseline PASSED・KILLED 12/12 (期待 node 完全一致)・等価 1 SURVIVED・MISMATCH 0)
---

## 本文

- 起点は entry 1722 の [T-2804] と D2170 の却下項 (延長は scope 外)。一次資料は `output/insights/2026-09-20/t2804-provenance-timeout-contract/README.md`
  (実測表・契約・相談 / レビューの写し・実走・変異台帳・裁定パッケージ)。設計判断は {{D:provenance-outer-deadline-contract}}。専用 handoff は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2804-provenance-timeout-contract/HANDOFF.md`。起点 local main `f94b61fc8`、fresh worktree、開始 gate rc=0。
- 段 1 実測 (provenance 受領証 85 件、残存 worktree に限る): queue 待ち中央値 5.2 秒・p90 7.3 秒・最大 716.5 秒 (本日 20:09、混雑時、land 呼出しではない)、
  監査本体 (RUN 区間) 中央値 30.7 秒・最大 475.9 秒 (旧 checker)、合計 480 秒超 2 件、375〜480 秒の帯 0 件。land の 480 秒 timeout は SIGKILL で、投入後・pending 解除前なら
  dispatcher の回収が走らず job と pending hold が残る構造を確認。
- 段 2 plan 1 本、段 3 相談 2 本 (契約の穴 / 受理集合・fail-closed・過剰)。両者一致の must-fix 5 件を全部採用: 項 8 の実装ではなく限定契約と明記、成功集合の縮小
  (2 帯) の明示、時計起点差 s を絶対 monotonic 期限で吸収、M_pre 180 → 60 秒、投入前拒否の閾値を queue 待ち観測 min × 3 = 16 秒へ、注入 seam の全面改訂を撤回。
- 段 5 author 1 本 (Codex、+299/−9、テスト 10 種 31 case + land pin 改訂)。焦点走 (計算ノード、対象 2 file + consumer 13 file) 3,893 passed / 7 skipped / 0 failed。
  段 6 レビュー 2 本: A GO (should 1)、B NO-GO (must-fix 1 = 終端行の field 名が裁定と不一致、原因は親の prompt の書き誤り)。fix1 (Codex、+5/−3) で field 名を
  裁定の `deadline_margin_s` へ、t2337 テスト 2 本に新 env の隔離。焦点走 再走 3,893 passed / 7 skipped / 0 failed。commit 後の全史監査 2 回 (12,061 / 12,062 件、新規違反なし)。
- Pegasus 実走 (unit 木): L1 正例 (期限 +480 秒、`--force-dispatch`) rc=0、queue 待ち 5.17 秒、Elapse 36 秒、checker 全体 52.6 秒、後段 h ≈ 0.03 秒 (代理値 32 秒に対し
  3 桁小さい、1 走)。L2 負例 (期限 +30 秒) 投入前拒否 rc=16、0.14 秒、新規 job / hold 無し。**L3 負例 (queue 締切 16.9 秒) は queue が空いていて発火せず = 負例未観測**
  (queue-wait-timeout 経路の実走証拠は本 wave に無い)。
- 変異 matrix (独立 clone、fix1 commit、計算ノード dispatch、13 件 = M1〜M12 + 等価 E0): probe (全件 SURVIVED 期待) で観測 node を集め、final は baseline PASSED (47.7 秒)、M1〜M12 = 12/12 KILLED (期待 node 完全一致、matching 13/13)、E0 (min の引数交換) = SURVIVED、MISMATCH 0。1 run 43〜58 秒、M12 だけ queue 待ちで 714 秒。単一理由性はレビュー A / B の静的判定と一致 (M7・M12 は既存テストでも落ちるので新規検出力ではない)。
- 裁定パッケージ (insight §7): 外側予算を D2148 項 8 型へ延ばすか — (a) 480 維持 + 内側導出 (本 wave)、(b) 区間和 5,130 秒、(c) 中間値 1,380 秒、(d) dispatch 時だけ延長。
  親の推奨は (a) を今 land し、(b)〜(d) は改善後 checker の混雑時観測 (T-2805) と queue-wait-timeout 経路の実走証拠が揃ってから。**推奨どおりなら追加の裁定は不要。**
- 言わないこと: 480 秒超の監査が全て救われる (救われない、queue 超過は clean な rc=16 になるだけ)。RUN / collection 中の期限到達で hold が残らない (残る)。
  receipt の永続化を保証する (しない)。85 件で成功集合の縮小がゼロと証明した (母集団の限界)。
- 事故: なし。親の prompt の field 名誤りは段 6 レビューが捕捉 (fix1 1 巡で閉じた)。時刻を推定で書いた箇所を mtime で訂正 (段 3 終了 21:22 を 21:31 と書いていた)。
- 工数: codex 7 本 (plan 1、consult 2、author 1、review 2、fix 1)、計算ノード job = 焦点走 2 + 実走 3 + 変異 28 (probe 14 + final 14)、login 全史監査 2。

## 次の一手差分

### 完了

- [T-2804] 契約 C-2804 (外側 480 秒固定、絶対 monotonic 期限の伝播、dispatcher 締切の導出、qsub 前拒否) を実装し、queue 待ちと監査本体の区間を受領証 85 件で分けて実測した。延長の要否は {{D:provenance-outer-deadline-contract}} の却下項と insight §7 の裁定パッケージ (推奨 = 現状維持)。
  remaining: none
  base: 1c2ba23a73ac3f3d74dc49be315f679cc9130bb14627347413ff47c425860dcd

### 新規

- {{T:provenance-queue-timeout-live-evidence}} **P3・新規**: 改善後 checker で queue が混雑しているときに、契約 C-2804 の queue-wait-timeout 経路 (導出 queue 締切の超過 → cleanup 予算付きの qdel → orphan hold 無し → rc=16) の実走証拠を 1 件取る。本 wave の L3 は queue が空いていて発火しなかった。T-2805 (混雑時の login 全史観測) と同じ機会で取れる。
