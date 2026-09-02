---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t941-p6-mechanization
seq: 1
title: [T-941] P6 の機械実装は始められなかった — 順序依存は 1 本ではなく 2 本だった (docs のみ、branch worktree-dev-wave-t941-p6-mechanization、実装面の差分 0)
---

## 本文

- **ユーザー依頼:** [T-941] が所有する P6 (意味的充足契約 v1、D156 発効済み) の機械実装と認定を進め、
  同 wave へ材料レポート renderer の結線 (V-12、[T-942]) を同梱する。裁定の根拠は entry 1184 の
  「8c 結線の裁定パッケージに残っていた『P6 の実装と認定をどの wave が所有するか』の停止項は閉じた。
  二段束縛の唯一の順序依存が解けた」。
- **実装しなかった。** 段 3 の敵対 2 レンズがともに NO-GO を返し、親がその決定的な主張を 1 件ずつ
  現物で検算した結果、実装へ進むと `DW-G04`・`DW-STOP`・2026-08-12 の承認済み裁定のいずれにも
  抵触することが確定した。詳細は `output/insights/2026-09-03_t941-p6-second-ordering-dependency/`。
- **本 wave が確定させた新事実:** entry 1184 の「二段束縛の**唯一の**順序依存が解けた」は誤りである。
  1184 が閉じたのは「どの wave が所有するか」という所有の停止項だけで、**第 2 の、より手前にある
  順序依存が開いたまま**である。V-8 (未裁定) → V-7 (V-8 の後と順序づけ済み、未裁定) →
  本番 runtime provisioning → 本番 authority entry (現在 0 件) → 本番 origin → P6 の発火条件。
- **親が現物で検算した事実 (レンズの報告を鵜呑みにしていない):**
  (M1) `reflux_origin_authority_v2.json` の `origins` は空配列で本番 origin は 0 件。
  (M2) `reflux_origin_ledger.py:2914-2915` の `_initialize_locked` は fixture でなければ
  `production runtime initialization is forbidden` で停止し、本番 runtime は構造的に作れない。
  (M3) `reflux_formal_consumer.py:722-729` の `_wal_trigger()` は root の `kind`/`trigger_binding` を
  要求する一方、`wal.py:1354-1359` の producer は `stage` + `payload` で書く。**着地済みの 8c formal
  consumer は本番形状の WAL record を 1 件も読めない。**
  (M4) `evaluate_formal_origin()` の非 test caller は 1 件だけで、origin 入力を渡す本番経路が無い。
  (M5) 2026-08-12 の裁定が「V-6〜V-10 の裁定まで結線実装 wave を起票しない原則、発行 3 条件 0/3、
  本番 authority entry 0 は不変」と定め、V-6/V-7/V-9 は V-8 の後と順序づけている。
  (M6) V-8 は今も未裁定で、2026-09-02 の一括裁定 374 件にも 2026-09-03 に着地した /rulings 第 4 回
  31 件 (`9efeacd69`) にも含まれない。
  (M7) `verify_done` payload には `build_attempt_id` が**存在する** (`pipeline.py:1485`)。
  P6 設計 §3.2.1 の「無い (実測)」は 2026-08-03 時点の測定で、現行コードと一致しない。
  親 brief はこれを現在の事実として転記していた — 親の誤りであり、レンズ A / B が独立に指摘した。
- **段 3 の 2 レンズは互いを見ずに A1 ≡ B4 へ到達した** — 「P6 が `NOT_IMPLEMENTED` のまま V-12 を
  繋ぐことは、[T-942] の裁定理由 (P6 不在のまま繋ぐと完全性を主張できない中間状態を読む結線になる) に
  反する」。合議ではない。
- 段 2 のプランは witness 正規化器と自己申告 3 field の出所移動を `file:line` 粒度まで設計し、
  受理集合の変化を 10 群、変異事前登録を 31 点まで具体化していた。それでも実装しなかったのは、
  発火条件を満たす artifact path も計測 ID も 1 件も書けず (`DW-G04`)、受理集合の変化が fixture 上の
  仮想差分にとどまるためである (`DW-G05`)。2026-09-02 の [T-434] wave が同じ理由で撤退したのと同型。
- プランと 2 レンズの逐語は insight の `verbatim/` へ凍結した。provisioning が裁定された後に同じ設計から
  再開でき、閉じるべき前提条件 10 件 (A3〜A11、B3、B5、B7) を表にした。
- **本 wave は「P6 の機械実装を進めた」「production 受理集合を狭めた」「V-12 を結線した」の
  いずれも名乗らない。** P6 の状態は `NOT_IMPLEMENTED` のままで、cap-lift・認定・`NOT_CLAIMED` の
  いずれも生じていない。
- 設計判断は {{D:p6-second-ordering-dependency}}。
- 実装面の差分は 0 のため変異 matrix は `DW-S04` により免除。受入全走は免除せず実走した。

## 次の一手差分

### 更新

- [T-941] **P2・ユーザー再裁定待ち (新事実あり)**: P6 の機械実装。entry 1184 の「起動可」は所有の
  停止項だけを閉じており、より手前の順序依存 (V-8 → V-7 → 本番 provisioning → 本番 origin) が
  開いたままである。本番 origin 0 件・本番 runtime 初期化禁止・結線実装 wave の起票制限のいずれも
  現行であり、`DW-G04` を満たせない。裁定パッケージ U1〜U5 は
  `output/insights/2026-09-03_t941-p6-second-ordering-dependency/README.md`。親推奨 = V-8 → V-7 の
  裁定まで保留へ戻す。
  base: 540a70476f625bef3b164147a95bdabb36417084e61c6859d43411a72b0f7e11

### 新規

- {{T:formal-consumer-production-wal-shape}} **P2・新規**: 8c formal consumer の
  `_wal_trigger()` が root の `kind`/`trigger_binding` を要求し、production producer が書く
  `stage` + `payload` 形状の WAL record を読めない
  (`reflux_formal_consumer.py:722-729` と `wal.py:1354-1359`)。provisioning の裁定と独立に必要で、
  P6 本体より小さい修理である。段 3 レンズ B の B3 が発見し親が検算した。

### 見送り追記

- [T-942] 2026-09-03 の [T-941] wave で V-12 の同梱を見送った。段 3 の 2 レンズが独立に「P6 が `NOT_IMPLEMENTED` のまま繋ぐことは本項の裁定理由に反する」と判定し、親が採用した。裁定候補 U3 (延期するか、P6 不在でも診断専用の非完全 projection を許すか) をユーザーへ返す。親推奨 = 延期。
