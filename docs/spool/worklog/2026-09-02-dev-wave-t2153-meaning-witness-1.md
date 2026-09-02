---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2153-meaning-witness
seq: 1
title: [T-2153] 意味 witness を 8 macro へ広げた — 断片ではなく所有 TU 全体の枝選択で観測する (コード + テスト、branch worktree-dev-wave-t2153-meaning-witness、変異 TBD)
---

## 本文

- 実行側の意味 (runtime-meaning) の節が witness を 1 件しか持たず、残り 21 macro が
  `unestablished` として成果物へ持ち越されていた。本 wave は**単一の `#if <MACRO>` を
  1 箇所だけ持つ positive control 8 件**を green へ動かした。意味の対応は 1/22 から 9/22 になる。
  設計は {{D:compile-time-branch-witness}}、{{D:meaning-supported-set-does-not-widen-legacy}}、
  {{D:witness-wiring-only-where-artifacts-shrink}}。

- **段 2 のプランは 13 件を提案したが、親は 8 件へ絞った。** 段 3 のレンズ B が
  「平坦な no-else 8 件、入れ子 2 件、selector、attribute、compound companion を同時に実装するのは
  依頼の『一括で扱わない』に当たる」と指摘し、親が採用した。絞ったことで
  `s1_direct_comparison.py` を触らずに済み、その bytes を pin する golden 2 箇所と
  受入台帳の S1 suite pin への追随がすべて不要になった。

- **段 3 と段 6 の敵対レビューが、独立に同じ穴を 2 度指摘した。** 対応 macro 集合を広げると
  旧 BACKOFF 復号器の受理面も一緒に広がる (旧宣言型の検査が集合所属しか見ていなかった)。
  段 3 で親が採用し実装子へ渡したが、段 6 でも再度挙がった。実装は入っていたので確認で閉じた。

- **段 6 のレビュー A が、実装の witness が意味を確立していないことを具体的な入力で示した。**
  条件指令の断片だけを切り出して単体で前処理していたため、所有 TU の手前に `#undef` が
  1 行あるだけで false-green になる。fix で所有 TU 全体の前処理へ変えた。この変更により
  自前の深さ計算が不要になり、行継続・コメント・raw string の誤判定 (両向き) も同時に消えた。

- **段 6 のレビュー B が、配線先 4 面のうち 1 面が無効であることを見つけた。** 対象 8 macro は
  `CCBENCH_` 名前空間外の裸マクロで、汎用 pipeline が作る define の route と一致しない。
  `screening_driver` へ配線しても admission 前に拒否され、成果物は 1 件も縮まない。
  fix で差し戻し、実効 driver は S3・S5・T152 の 3 面と確定した。

- **親の brief が 3 点で誤っていた。** (a) 第一群 11 件のうち `IZANAGI_BREAK_TRIGGER_MISATTR` は
  `#ifdef` かつ `#if BACKOFF_TRIGGER_GATING` の内側で、要求値 1 / 既定値 0 では枝が変わらない。
  (b) driver 側は 1 関数では足りず、意味の節を呼ぶ生産側は 21 箇所あった。
  (c) `capture_define_inputs` が patch 適用済み source を保証するという一般化は誤りで、
  保証しているのは各 driver 側である。

- **計算資源の混雑で投入が 6 回中断した。** すべて `queue-wait-timeout` か、それが残した保留
  ファイルによるもので、実装の欠陥ではない。1 回は変異が適用されたまま止まったが、
  残った差分が登録済み変異そのものであることを照合してから復元した。詳細は
  {{F:mutation-dispatch-orphan-hold-two-kinds}}。

- 実装は Codex `role=author` が書き、fix も同じ契約で Codex が行った。親は裁定・統合・
  commit・実測・記録だけを担った。

## 次の一手差分

### 更新

- [T-2153] **P2**: 意味 witness を持つ macro を 1 件から 9 件へ増やした。残る 13 件は
  (a) `#else` + 入れ子を持つ 2 件、(b) 条件指令が別の条件指令の内側にある 1 件、
  (c) 条件指令が複数箇所に散る 3 件、(d) selector / template / 診断が混在する 4 件、
  (e) 枝は単一だが成果物へ届く driver の配線が編集面を大きく超える 2 件、
  (f) 同伴 define を gate 側が再注入するため実 build と乖離しうる 1 件。
  base: 57050103bee0298953e965d0de8f01d781d1cf721a4f4ab561f058f78ef39df6
