---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: worktree-dev-wave-b5-generator-contrast-prereg
seq: 1
title: B-5 生成器対照 (K2 loop / ランダム変異 / 機械 sweep) の事前登録 v1 を作った (docs のみ、branch worktree-dev-wave-b5-generator-contrast-prereg)
---

## 本文

- ユーザー決定 (2026-09-19) の範囲だけで 1 wave: 固定 backoff hole の内で 3 生成器を同一評価数で比べる事前登録の作成。
  本走・生成器の実装・追加 gate・D1409 の条件変更は認可されておらず、行っていない。着手時 local main `a99425b66`
  から fresh worktree、記録前に `657e1e5a7` を ff-only で取り込み。実装面差分ゼロ。
- 成果物 = `docs/b5-generator-contrast-preregistration.md` (v1、未発効) と `docs/README.md` の 1 bullet。設計判断は
  {{D:b5-generator-contrast-prereg-v1}}。一次資料・裁定・逐語は `output/insights/2026-09-19/b5-generator-contrast-prereg/README.md`。
- 段 1 実測: hole の受理域は整数 µs 1..1000 (Tier 1 文法 + 値域 + 帰属整合) で完全列挙可能。K2 手動 loop の性能構成は
  `default_perf()` の配線規模に固定、拡張 sweep は 29 点全走 driver で B 点 mode なし、ランダム変異は不在。
- plan 1・相談 2・独立レビュー 1・焦点 2 (全段 gpt-6-astra / medium、計 61 model call)。plan が brief を 3 点訂正
  (単一 layout では入口停止、同一 genome は WAL 復元、支持集合は共通でない)。相談は must 6 / should 6、独立レビューは
  must 3 / should 2、焦点 1 は新規 must 1 / should 1、焦点 2 は新規 must 1。全所見 real・採用。親が docs を直した。
  親の統計の誤り 2 件 (Holm の段階閾値、(iii) の防壁効能) は焦点再レビューが倒し、本文から外した。
- 段 4 裁定からの変更 3 点 (主副の向き不一致の廃止、片 arm の生成不成立、精度不足の判定順) は段 6 の親裁定として
  記録した (`rulings-stage6.md`)。DW-O16 の 3 巡上限に達したので fix 巡はここで止めた。
- 費用は 1773 論理 session (前回設計の 3330 から縮小)、百時間級の推定。総実行 wall の上限は試走後に本走認可で決める。
- 検査: `check_docs` 緑、三軸語走査 rc 0、`git diff --check` 空、NFC OK。変異 matrix は実装面ゼロで免除。
  受入全走は記録 commit の tip に対して投入し、結果は専用 handoff と land の receipt に残す (受入後の commit は
  tested tip を外すので作らない)。
- 専用 handoff は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/HANDOFF.md`。
  dev-wave 改善候補はゼロ。次 wave・push は行わない。

## 次の一手差分

### 更新

- [T-1872] **P3・裁定待ち → 実装待ち**: B-5 対照の実装対象は事前登録 §10 の「実装が要る」部品
  (較正動作点の CLI、session 契約の束縛、B/A 台帳と停止の不適用、重複の fresh 評価、exact correctness 経路、
  系列開始 stock、random 生成器、sweep の hash 順 B 点、解析 consumer)。実装の認可は本走認可 (事前登録 §12 の
  7 項) と同じ裁定パッケージで諮る。
  base: 9bed5f418c8f5795e29bbb4b288fa2cd67d8154de5fb1684e4f3450af1a698c3

### 新規

- {{T:b5-contrast-activation}} **P2・ユーザー裁定待ち**: `docs/b5-generator-contrast-preregistration.md` §12 の
  本走認可時の確認 7 項 (D39 決定 2 の実質改訂、凍結する実験構成、score と失敗処理、費用、未閉鎖の主張、
  本走の対象 commit、D52 / D1409 との境界) と、較正動作点・exact correctness 経路での所要の試走の認可。
  裁定が出るまで発効 commit を作らない。
