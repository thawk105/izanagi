---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t816-step4-impl
seq: 1
title: trace を v2 専用にし ccbench pin を 511c953 へ前進した — 凍結 v1 証拠は bytes を保ったまま再検証を退役、校正 artifact の再 pin は段 6 が覆して撤回 (コード + docs、変異 8/8 検出、branch worktree-dev-wave-t816-step4-impl)
---

## 本文

2026-08-12 の一括裁定 (粗い provenance 基準) で blocker 2 件が解消されたため、[T-816] 手順 4 を
実装した。裁定の適用先は親が実測で確定した — 「v2 専用 + 赤になる凍結 v1 証拠テストを退役」
「検査で現用の校正 pin だけ機械再 pin、未使用は退役」「乗せ直しを省略して `511c9538` へ直接前進」。

**親の裁定を 1 件、段 6 の敵対レビューが実測で覆した。** 段 4 で親は「生きた driver が verify する
artifact は現用だから機械再 pin」と provisional に裁定したが、`s8b_oracle_driver` は
`known_axes_freeze.json` の**生バイトが移行 receipt の旧 SHA と一致すること**を要求しており、
再 pin は 8b oracle を即座に止める。s8a 頻度実測は TRACE=1 で採った値で、親が根拠にした
TRACE=0 同一性証拠が適用できないうえ、現物は必要 field を欠いて wave 以前から読み込み不能だった。
→ 校正・凍結 artifact 3 件は**旧 pin のまま据置 (退役)** へ戻し、前進を維持するのは
`patches/ledger.json` の base commit とコード・テスト側の現用 pin だけにした。
機序と恒久対応は {{F:consumer-liveness-misjudged}}、設計判断は
{{D:frozen-evidence-historical-binding}}。

段 6 レビューはもう 1 件、**既存の fail-open** を見つけた。parser が record 種別を先頭 1 文字で
判定していたため `End 0` が正規の `E 0` として、`Commit …` が `C …` として受理されていた。
受理集合を縮小する wave で看過できないので同 wave で塞ぎ、変異でも裏取りした。

裁定文の「凍結 v1 証拠テスト 4 本」は、実測では**実 v1 bytes を現行 verifier へ通す経路が 1 本**
だった (凍結 raw trace が 4 本であることに由来する数と解した)。「赤になるものは全部退役」という
趣旨に従い、退役したのは trace 再検証のみで、生バイトからの commit 件数・write witness の再導出と
build / attestation / seal / manifest / commit witness の検査はすべて残した。**凍結 bytes は
1 bit も変えていない。**

実測は `output/insights/2026-08-12_t816-step4-impl/README.md` が正本。焦点 16 file は
`828 passed, 10 skipped` で赤ゼロ。残る 1 error は `test_s8b_approved.py` の収集失敗
(`No module named 'tests'`) で、単一ファイル選択走で import path が確立しない DW-O18 の偽赤である
(wave 前の初回実測でも同じものが出ており、差分と無関係)。`sys.path` に `orchestrator/` を入れれば
`tests.skiputil` が import できることを確認した。

変異は 8 件すべて検出 (SURVIVED 0)。段 4 で登録した M1 (v1 受理) と M8 (校正 pin gate) は
レビュー A が単一理由の不成立を指摘し、M1 は作り直し、M8 は**登録を取り下げた** — 成功 fixture が
常に現行 pin を持つため gate を fail-open にしても挙動が変わらない。MISMATCH 2 件は
{{F:consumer-liveness-misjudged}} とは別型で、F230 の再発として記録した。

**gitlink の前進は Codex `role=author` が物理的に実行できない** (submodule の git dir が
worktree の外にあり workspace-write sandbox から書けない)。`external/` は provenance 監査上の
実装面なので、単独 commit にすると role=author 無しの実装面 commit になる。本 wave は
codex author が書いた実装と同じ統合 commit に含めて回避したが、gitlink だけを進める wave では
回避できない。段 8 の改善候補として送った。

## 次の一手差分

### 完了

- [T-816] 手順 4 を実装した。gitlink `d706650` → `511c9538`、現用 pin 23 箇所、
  trace v2 専用化、framing integrity、負 txid 拒否、record 種別の完全一致、
  凍結 v1 証拠の trace 再検証の退役。凍結 bytes は不変。
  remaining: none
  base: 9f7a085030bd26aa99323a37d6e0b1ae02e5ac75c1e3481a275a8f408f140da0

- [T-838] hard block の実体 (凍結 v1 raw trace と歴史 pin 再現経路) は [T-816] Q1 の裁定へ吸収され、
  本 wave で処理した。凍結 raw bundle は bytes 据置で trace 再検証を退役、歴史再現 driver
  (`s2_verify_calibration.py`) はコードを変えず `docs/phase3.md` へ日付級 1 行を記録した。
  remaining: none
  base: 6585187ae5c157c435e983cd5517f661b956720446efdb795ac69b86c3ac44cf

- [T-879] 負 txid の false-green を塞いだ。`txid >= 0` の構文検査と、負値が `max(txid)+1` の
  欠番計算を相殺する負例を追加し、変異 (検査除去) が期待 node で KILLED になることを確認した。
  remaining: none
  base: 0bda3813ecf73d6fa180f4cadf3b4e7edffcb4704e8f132c2b7ac45a92bdde09

### 新規

- {{T:s1-freeze-family-retired-under-new-pin}} **P1・新規 (ユーザー裁定候補)**: pin 前進の結果、
  S1 freeze 族 (`output/s1-freeze/known_axes_freeze.json` / `measurement_freeze.json`) は
  記録された pin と現行 pin が食い違う状態になった。`s1_measurement_freeze.verify()` と
  `s1_known_axes_freeze.verify()` は実行時に pin 不一致で拒否するため、`s1_report` と
  8b oracle を**新 pin で走らせると refusal が出る**。**受入全走では検出されない**
  (検査が実 artifact を読まないため)。bytes を書き換える再 pin は不可 — 移行 receipt・
  holdout freeze・measurement freeze が旧 bytes を hash で束縛しており、8b oracle が即座に止まる
  ({{F:consumer-liveness-misjudged}})。選択肢は (a) freeze 族を新 pin で再発行 (再測定が要る)、
  (b) 8b を旧 pin の checkout で走らせる運用に固定する、(c) 現状を退役として受け入れ、
  8b が freeze 族を要求しない形へ配線し直す。費用と影響範囲の見積りを添えて裁定へ出す。
  正本 = `output/insights/2026-08-12_t816-step4-impl/README.md`
