---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t471-restore-bound
seq: 1
title: [T-471] 復元コストを計算ノードで実測した — 数十ミリ秒で 10 s 予算の 3 桁下、しかし T-360 条件 3 は R では閉じないと決着 (コード + docs、受入 6108 passed 19 skipped、branch worktree-dev-wave-t471-restore-bound)
---

## 本文

- **中心結論: `R` を測っても [T-360] 条件 3 は閉じない。** [T-399] の凍結式
  `G_usable_lower ≥ 5 s + 5 s + R` の左辺は凍結代入規則により T-399 attempt の
  `cleanup_elapsed = 5.013 s` に固定される。`R ≥ 0` である以上 `5.013 ≥ 10 + R` は
  **R の値によらず偽**であり、判定は測定精度に一切依存しない。
  「R を測れば条件 3 が前進する」という [T-399] 時点の見通しは成り立たなかった。
  条件 3 は R の精度ではなく「production の cleanup 列が grace 内で実際に完走した attempt が
  1 つも無い」という証拠の問題である。**変異本走を計算ノードへ束ねる安全根拠は成立していない。**
- **凍結記号 `R_restore_bound` は null のままとした。** 同記号は「上限」と定義されているが、
  非定常な Lustre の wall-clock に対し有限標本の max は上限ではない。段 3 の敵対 2 レンズが
  独立に同じ指摘へ到達し、親は real として全面採用した。実測値は別名
  `R_restore_observed` として診断値で公表する (D75 の二義化禁止)。
- **実測 (診断値、計算ノード bnode064、500 trial、失敗 0):** 全 arm の max = **71.79 ms**。
  支配項は `__pycache__` の purge であり bytes はほぼ効かない — `E=0` の p50 2.99 ms に対し
  `E=143` は 34.53 ms、一方 target を 69,659 → 240,600 bytes にしても 34.53 → 33.61 ms。
  cache を冷却した arm は fresh の 1.57 倍 (p50 54.10 ms)。**復元は `_stop_process` の
  10 s 予算に対し 3 桁小さく、予算の支配項ではない。**
- **[T-399] の「warn margin は設計上の障害が残っていない」は射程が広すぎた。** 拡大が構成上
  可能なのは正しいが、`D_delivery` (PBS warn 配送遅延) と `H_head` (`_assert_head` の
  git subprocess) が未計測であり、具体的 warn 値を certify する根拠は無い。凍結文書は
  書き換えず erratum で射程を明示した。
- **段 3 で 22 所見 (レンズ A 12 / レンズ B 10) すべてを real と裁定し、親の provisional 裁定
  P1 (production cleanup 限定) と P4 (certified margin 規約) を撤回した。** P1 は凍結文の字句から
  導けず、P4 は「上限」資格を立証しない。
- **段 6 のレビュー 2 本は受理不可で、must-fix 8 件・should-fix 6 件を全件 real と裁定した。**
  fix で driver を 778 → 293 行へ縮退させ、case を literal 凍結して spec 探索器を削除した。
  焦点再レビューは closed 7 / partial 7 + 新規 6 件を返したが、**親は追加の検出器を実装せず、
  実際に走った attempt の忠実性を生証拠から直接検算する**方針を採った (交互化が exact
  round-robin と完全一致、harness hash が before=after=実ファイル=HEAD blob、E と bytes が
  別々に異なる 3 arm で entry あたり限界コストが 0.2141〜0.2216 ms/entry に一致)。
  残す限界と裁定理由は erratum-1 に記録した。
- **セッション異常 1 件:** 段 6 の fix 巡 1 は編集ゼロで停止した。原因は親の prompt で、
  段 5 が生成した未 land のテストを「変更禁止の既存テスト」と読める書き方をしていた。
  実装子は正しく fail-closed した。権威順序 (凍結事前登録 > 段 4 裁定 > 段 5 実装) を明示して
  巡 2 で全 14 件 closed。
- **親の独立検算 (両レンズにない新事実):** `runner_mode=dispatch` では `PYTHONDONTWRITEBYTECODE=1`
  が計算ノードへ伝播しない (allowlist 4 key のみ、`-B` も付かない)。よって [T-360] の実運用経路では
  `__pycache__` が書かれ `E > 0` が主ケースになる。arm 設計をこれに合わせた。
- エージェント工数: codex 6 本 (段 2 プラン 1、段 3 レンズ 2、段 5 author 1、段 6 レビュー 2)
  + fix 2 本 (巡 1 は空振り) + 焦点再レビュー 1 本。claude 子なし。
  計算資源: 実測 job 1 本 (76 s)、テスト dispatch 多数。

## 次の一手差分

### 完了

- [T-471] `_restore_targets` の所要時間を計算ノードで実測し、[T-399] 凍結式への当てはめまで
  完了した。凍結 `R_restore_bound` は上限性を立証できないため null のまま、十分性は `UNKNOWN`。
  同時に判定が R 非依存であることを確定させ、条件 3 が R の測定では閉じないと決着した。
  warn margin は設計メモ (候補・未 certify) に留めた。残る問いは新規 T として起票済み。
  remaining: none
  base: 213d1ce05155ff833ce2fd62bb7bd3e045b0c788f5da2d745bba1d9318aa3987

### 更新

- [T-360] **P1・裁定済み → 前提は残り 2 件 (条件 3 の性質が変わった)**: 択 (a) は不変。
  D130 条件 3 は [T-471] の実測で**前進せず、閉じ方が変わった** — 「捕捉可能構成の実在 =
  実証済み ([T-399])」は不変だが、十分性は `R` の測定では certify できないと確定した
  (`5.013 ≥ 10 + R` は R 非依存で偽)。条件 3 を閉じるには {{T:production-cleanup-leg}} か
  {{T:interruption-safe-restore}} のいずれかが要る。条件 2 (flock 確定) は [T-402] のまま。
  warn margin は「構成上は拡大可能だが、`D_delivery` と `H_head` 未計測のため値を certify
  できない」が正しい射程 ([T-471] `warn-margin.md`)。着手は D131 前提 6 点 + D105 supersede の
  次 wave で、ユーザー裁定に従う
  base: cb222817c98c66d044409dc9b125b46bce7e8235a516cff5e3e4f4ad4e2e3724

### 新規

- {{T:production-cleanup-leg}} **P1・新規・ユーザー裁定待ち**: [T-360] 条件 3 を閉じる probe leg を
  投入するか裁定する。production 相当の cleanup 列 (`_stop_process` の 2 段 wait 10 s +
  復元 0.1 s 相当の仕事) を grace 内で完走させ、`cleanup_elapsed ≥ 10 s + R` を実際に満たす
  attempt を 1 つ作る。現行 nominal grace 60 s に対し時間の余裕はあり、足りないのは証拠である
- {{T:interruption-safe-restore}} **P1・新規・ユーザー裁定待ち**: grace 予算に依存しない復元設計へ
  転換するか裁定する。`_restore_targets` は fsync せず、支えるのは「live node・Lustre client 生存・
  return 後の process kill」までである。journal + fsync + 再開時修復にすれば、
  「間に合うか」を測る問題自体が消える。[T-471] の中心裁定より**こちらが本筋である可能性が高い**
- {{T:warn-delivery-latency}} **P2・新規**: `D_delivery` (PBS が warning を要求した時刻から
  Python parent が受信するまでの遅延) を反復観測する。これが `UNKNOWN` である限り、
  どんな warn 値も certify できない
- {{T:assert-head-cost}} **P3・新規**: `H_head` (`_assert_head` の git subprocess) を Lustre 上で
  計測する。凍結式の `10 s + R` に含まれない項であり、実測の結果 **R より予算への寄与が
  大きい可能性がある**
