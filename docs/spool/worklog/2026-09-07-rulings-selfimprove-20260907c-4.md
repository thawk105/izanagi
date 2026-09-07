---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: rulings-selfimprove-20260907c
seq: 4
title: /rulings 全件 第 13 回の裁定 — 索引 8 件を推奨どおり裁定した。うち 3 件は相談が覆した側の推奨で、射程を広げる案が退けられた (docs のみ、branch worktree-rulings-selfimprove-20260907c)
---

## 本文

- **ユーザー裁定は「推奨通りで。過剰実装・過剰ガードレールは無しで。main land までよろしく」。**
  索引 14 件のうち、/rulings が推奨を書いた **8 件 (索引 1〜8) を推奨どおり裁定**した。
- **推奨を書いていない 3 件は裁定として記録しなかった。** 索引 9 (正式系列を開始する production
  genesis producer)、索引 10 (排他権の世代の導出方式の最終採用)、索引 11 (見送り 7 件の同時発火) は、
  索引にのみ載せて推奨を付けていない。**ユーザーが見ていない文面へ「推奨どおり」を適用するのは
  裁定の捏造になる**ため、次回へ持ち越した。索引 12〜14 はユーザーの実行手番のまま。
- **裁定のうち 3 件は、起草時の親推奨が相談で覆った側である。** いずれも**射程を広げる案が
  退けられた**方向で、ユーザーの付言 (過剰実装・過剰ガードレールは無し) と同じ向きだった。
  - 受入 collection の絞り込み — 起草時は「絞り込みを採り割付一致検査を代替に置く」だったが、
    自己証明になるため {{D:acceptance-collection-scoping-stays-forbidden}} で不採用。
  - D906 の実効層 — 起草時は「作らず限界明記」だったが、D1197 の却下欄が逐語で退けていたため
    {{D:d906-effective-layer-is-separate-os-principal}} で別 OS principal を採用。
  - 条件関門の赤 — 起草時は 3 箇所すべてだったが、一次資料が到達不能と書いていたため
    {{D:driver-gate-supply-limited-to-screening}} で screening 1 箇所に限定。
- **横断の制約を 1 件立てた。** {{D:rulings-13-implementation-scope-rider}} — 実装段で射程が戻る
  経路を塞ぐため、名指し外の gate・検査・台帳・一般化は同じ wave で実装せず裁定パッケージへ送る。
- **[T-1851] の項本文は書き換えていない。** 稼働 wave が所有しているため、第 11 回・第 12 回の
  先例に従った。裁定は {{D:unit-c-two-rulings-decided-ahead-of-land}} に置いた。
- **本 wave は裁定の記録だけで、実装面の差分はゼロ。** 各裁定の実装は別 wave が持つ。

## 次の一手差分

### 更新

- [T-2377] **P1・裁定済み ({{D:acceptance-collection-scoping-stays-forbidden}}、2026-09-07 /rulings 全件
  第 13 回、相談で推奨が逆転) → 実施しない**: 自 shard 絞り込みは採らず D711 の禁止を維持する。
  **起草時の親推奨「絞り込みを採り割付一致検査を代替に置く」は、同じ縮小集合による自己証明であり
  gate 2 と同等でないため退けた。** 再訪条件 = 受入 wall が再び実害として観測され、かつ独立な
  全体集合から導いた期待割付を供給する設計が具体的に示されたとき。費用の増加だけでは再訪しない。
  base: f6a22919cac6bb3e558a5308d125435f16ac1b4555f95dc5ddd92e7c9739e3a9
- [T-2382] **P1・裁定済み ({{D:acceptance-observation-fields-deferred}}、2026-09-07 /rulings 全件
  第 13 回、推奨どおり) → 実施しない**: 観測 field の拡張も closed schema の v2 移行も行わない。
  D1706 が計装なしで残差を分解しており、[T-2377] が現状維持となった以上、内訳を確定しても
  次の一手は変わらない。再訪条件 = 受入 wall が再び実害として観測され、かつ内訳の確定なしには
  次の一手が決まらないことを示せたとき。
  base: b33c39b7b8ecad91b0ce41d35d3cf372c4aee1ddfc03033515e0e2f98c5188f7
- [T-2384] **P2・裁定済み ({{D:formal-consumer-terminal-outer-shape-closes}}、2026-09-07 /rulings 全件
  第 13 回、推奨どおり) → 実装待ち**: terminal record の外枠を D1665 が FC05C へ入れたのと同じ形の
  exact gate で閉じる。変異 B-057-M5 の生存が実在欠陥の実測である。他の gate・reason code・判定式は
  変えない。`P6Unavailable` により certified 選択集合は動かない。
  base: 1176b84f237b1b0ff4fda96f796de5a55ef8640748190974ab927ace802aa927
- [T-2389] **P1・裁定済み ({{D:d906-effective-layer-is-separate-os-principal}}、2026-09-07 /rulings
  全件 第 13 回、相談で推奨が逆転) → ユーザー手番 (配置)**: 実効層は別 OS principal を採る。
  **起草時の親推奨「いずれも作らず限界明記」は、D1197 の却下欄が「限界の明記だけで足りるとする」を
  逐語で退けていたため撤回した。** 配置と権限設定は D1436 によりユーザーの手番で、AI は代行せず
  代行案も作らない。閉じるまでは D1197 のとおり未閉鎖と明記する。
  base: c57c65ca5147e50919a12237cdb4a1d8a985fa42c65f51e0f5afe3f723b54f64
- [T-2396] **P1・裁定済み ({{D:a1-group-receipt-publishes-via-os-link}}、2026-09-07 /rulings 全件
  第 13 回、推奨どおり) → 実装待ち**: group submission receipt の公開を `os.link()` へ改める。
  既存先に `EEXIST` を返すので create-only の排他性を落とさない。`complete` の completion receipt と
  materialize 側も同族として棚卸しする。Codex `role=author`、正例・負例を同じ commit へ。
  base: ac7081398df2ea569199c734f90fe8376ee1b2d99b7453418a0eb64f87da02ee
- [T-2228] **P2・裁定済み ({{D:driver-gate-supply-limited-to-screening}}、2026-09-07 /rulings 全件
  第 13 回、相談で推奨が逆転) → 実装待ち (1 箇所のみ)**: FetchContent base の供給は
  `screening_driver._run_condition_gate_for_genome` にだけ入れる。**起草時の親推奨「赤 3 箇所すべて」は、
  一次資料 1.3 節が「現状のまま `backoff_repro` を起動すると関門に触れる前に止まる」と書いており、
  測った赤が歴史 pin の木のものだったため退けた。** pin の整合と freeze の再生成も行わない。
  再訪条件 = `backoff_repro` または `s1_direct_comparison` が現行の正規入口から関門へ到達したことを
  実測で示せたとき。
  base: 3fa0b8e325f1da06673d0047dc8d3bb818286fea1b795da6588c2e12c8d7453f
- [T-2381] **P2・裁定済み ({{D:prebuilt-receipt-nonconsumption-stays}}、2026-09-07 /rulings 全件
  第 13 回、推奨どおり) → 実施しない**: 現行挙動 (terminal variant を `evaluate` 前に skip し
  事前構築 receipt を消費しない) を維持する。receipt transport の追加も duplicate の意味論の変更も
  採らない。既存の test pin と `tools/pegasus/README.md` 7 節の運用注記で閉じる。
  base: d80be3552eee6208aa71b5ee720434e641906d0d591dd580581585dfdb6be166

### 新規

- {{T:rulings-13-unranked-carryover}} **P2・新規・ユーザー裁定待ち (3 件)**: /rulings 第 13 回の索引に
  載せたが**推奨を付けなかった**ため裁定として記録しなかった 3 件を、次回に推奨つきで再提示する。
  (1) 正式系列を開始する production genesis producer が 0 件 ([T-2392] が実体)、
  (2) 排他権の世代の導出方式の最終採用 — D1528 の再提示条件 (鍵と発行権限の配置) は 2026-09-05 に
  成立済み ([T-2148] / [T-2184] が実体)、(3) 見送り台帳 7 件の同時発火の扱い ([T-281] / [T-436] /
  [T-982] / [T-993] / [T-1007] / [T-1008] / [T-1015])。**「推奨通りで」は推奨のある項にしか及ばない。**
