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

**受入全走で構造的 blocker が出たため、本 wave は land していない。** 実装は緑だったが、
焦点走の範囲が狭すぎた — 前 wave は 5 file、本 wave の焦点走も 16 file しか測っておらず、
`test_s8b_oracle_driver.py` 等が入っていなかった。前 wave の記録にある
「S1 freeze の破れは受入では検出されない」は**誤り**である。詳細は [T-816] の項。

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

- [T-879] 負 txid の false-green を塞いだ。`txid >= 0` の構文検査と、負値が `max(txid)+1` の
  欠番計算を相殺する負例を追加し、変異 (検査除去) が期待 node で KILLED になることを確認した。
  remaining: none
  base: 0bda3813ecf73d6fa180f4cadf3b4e7edffcb4704e8f132c2b7ac45a92bdde09

### 更新

- [T-816] **P1・手順 4 は実装完了・受入で構造的 blocker → ユーザー裁定待ち
  (2026-08-12 dev-wave-t816-step4-impl)**: 実装は緑になった (焦点 16 file が `828 passed`、
  変異 8/8 検出・SURVIVED 0) が、**受入全走が `44 failed, 9357 passed`** になった。
  うち 12 件 (pin 由来 campaign identity golden と、段 2 の A/B 分類を 1 件誤って据置にした
  fixture pin) は本 wave で修正し、**残る 32 件はすべて 1 つの構造的事実に帰着する** —
  `s1_known_axes_freeze.verify()` が `ccbench_pin` を**submodule の現 HEAD**と比較するため、
  **gitlink を進める限りどの実装でも通らない**。これが T-080 移行受領証 → holdout freeze →
  8b oracle → 床値 protocol の連鎖を fail-closed にする。機械的再 pin は 1 field で閉じず、
  受領証と seal の bytes 書き換えに波及するため無裁定では実施しない。
  **4 択を裁定へ返す** (機械的再発行 / 再測定して再発行 / freeze の検証条件を変える /
  手順 4 の撤回。親推奨 = 機械的再発行、根拠 = TRACE=0 同一性の機械証明)。
  正本 = `output/insights/2026-08-12_t816-step4-impl/README.md`、
  一次控え = `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-t816-step4-freeze-chain-blocks-pin-advance.md`
  base: 9f7a085030bd26aa99323a37d6e0b1ae02e5ac75c1e3481a275a8f408f140da0

- [T-838] **P1・[T-816] の裁定へ吸収済み、実装も同 wave が保持**: hard block の実体
  (凍結 v1 raw trace と歴史 pin 再現経路) は処理した — 凍結 raw bundle は bytes 据置で
  trace 再検証を退役し、歴史再現 driver (`s2_verify_calibration.py`) はコードを変えず
  `docs/phase3.md` へ日付級 1 行を記録した。**本項の終端は [T-816] の裁定に従属する。**
  base: 6585187ae5c157c435e983cd5517f661b956720446efdb795ac69b86c3ac44cf
