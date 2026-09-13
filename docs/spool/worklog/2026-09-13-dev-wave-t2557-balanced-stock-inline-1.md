---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-13
wave: dev-wave-t2557-balanced-stock-inline
seq: 1
title: [T-2557] balanced の stock-inline 対を正式に測り、consumer 側の 2 欠陥で認証読み出しが止まった (docs のみ、branch worktree-dev-wave-t2557-balanced-stock-inline)
---

## 本文

- D1874 の認可と D1938 の AI 委任に従い、balanced の stock-inline 対を正式に投入・回収・解析した。
  D1936 項48 が残していた人間手番は D1938 が明示的に解除しているので、代行ではない。
- **測定は完走した。** job `995755.nqsv` (gen_S)、Elapse 712 秒、8 genome すべて commit、abort 0 件、
  `.failure.json` なし。投入は 1 回だけで fan-out していない。投入元は記録を書かない専用の
  detached worktree にし、走行中は投入木を 1 bytes も変えていない。
- **consumer は拒否を返した。** code `performance-build-not-trace-disabled`、
  field `wal.bench_done.run_cmd.executable`、arm baseline。原因は測定側ではなく consumer 側にある。
- 実成果物では原理的に成立しない検査が 2 系統あることを一次資料で確定した。
  (1) numactl 前置を `linux-baremetal` 契約の値の literal で固定しており、事前登録が pin する
  `pegasus` 契約 (`numactl=()`、D144 が根拠を実測済み) では満たせない。
  (2) `toolchain_record_sha256` を WAL の縮約 `toolchain` から再導出できる前提だが、producer は
  full version を含む別 manifest から取っており、`version` は成果物に 0 件で復元できない。
  同じ code の腕間比較は実成果物で通る健全な検査であり、欠陥ではない。境界は偵察で確定した。
- (1) の是正方向は D924 が既に裁定している (「env contract の値を計測側へ literal で写す」を却下し
  `env_contract.lookup()` から引くと定めた)。(2) は設計択一を含むので親は裁定せず返す。
- **効果量は本 wave では読んでいない。** 偵察 driver は sample・median・ratio・improvement_percent を
  出力しないよう意図的に作った。未決の設計裁定を、効果量を知らないまま下せる状態に保つためである。
  生値は repo 外の成果物 root に保全してあり失われていない。
- 親が実装まで進めなかった理由を記録する。検査を 1 行外せば自分の計測が読めるようになる圧力が
  現に掛かっている場面であり、受理集合を変える判断は圧力の外の主体が下すべきと判断した (絶対規律 2)。
- 根本原因は F622 と同型 (述語を合成 fixture だけで検証し守る現物と接続しない)。
  違いは恒真の向きで、F622 は決して赤にならない gate、本件は決して緑にならない gate である。
- 実装面の差分はゼロなので変異 matrix を免除した。受入全走は免除していない。
- 詳細・逐語・絶対 path は `output/insights/2026-09-13_t2557-balanced-stock-inline/README.md`。

## 次の一手差分

### 更新

- [T-2557] **P2・ユーザー裁定待ち**: 正式測定は完走し成果物は保全済み。認証された効果量は
  consumer の 2 欠陥のため未取得。裁定が付き次第、同じ成果物を是正済み consumer へ通せばよく、
  再測定は要らない。
  base: 543efbfb8e519befd04e77f152ccd4f63e4cda531b1dbbb5a88af3a6a414c774

### 新規

- {{T:t1998-consumer-real-artifact-repair}} **P1・ユーザー裁定待ち**: T-1998 consumer の
  実成果物非互換 2 件を是正する。(1) numactl 前置を契約由来にする — 方向は D924 が既裁定。
  (2) toolchain digest の腕内再導出 — 案 A 撤去して非保証と明記 / 案 B producer に full manifest を
  記録させる / 案 C producer の hash 対象を揃える、の択一。B と C は再測定を要する。親の推奨は A。
  裁定パッケージは F622 への今回の再発記録と同 insight を参照する。
