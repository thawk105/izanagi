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

**受入全走で構造的 blocker が出た。** 実装は緑だったが、焦点走の範囲が狭すぎた — 前 wave は
5 file、本 wave の焦点走も 16 file しか測っておらず、`test_s8b_oracle_driver.py` 等が
入っていなかった。前 wave の記録にある「S1 freeze の破れは受入では検出されない」は**誤り**である。

blocker はユーザー裁定 D328 (凍結検証の保留) で解けた。**本 wave が [T-917] の保留執行も担った**
(並行 wave と調整のうえ、赤を実証できるのが本 tip だけであるため)。保留の設計で 3 回直している。

1. **関数まるごとの保留は不可**。保留対象の同一性検査と、保留してはならない測定公正・admission・
   防壁が同じ関数に同居していた (F240)。行単位へ切り直した。
2. **可視性を process 内状態に依存させない**。in-process registry だけだと CLI subprocess と
   48 worker で親に届かず、「保留しているのに何も保留していないと見える」最悪の不可視化になる。
   発火時に stderr へ機械可読 1 行を出す形にした。**ただし pytest は通過テストの出力を捕獲するため、
   緑の走行では marker が log に現れない** (実測)。production の CLI 経路では見える。
3. **保留対象の同定を機構名でなく赤の実体から逆引きする**。`_verify_ccbench_current` を
   「live ccbench identity」という名前から対象外と分類していたが、実体は
   「現在の ccbench HEAD == 記録 pin」で D328 が名指しする検査そのものだった (赤 31 件の主因)。
   逆に `protocol-pre-oracle-head-bytes` は名前が似ているだけの盲検保護で、pin と無関係だった
   (保留対象から外した)。

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

- [T-816] **P1・手順 4 完了。D328 の保留執行 ([T-917]) を同 wave で実施して閂を外した
  (2026-08-12 dev-wave-t816-step4-impl)**: 実装は緑だったが**受入全走が
  `44 failed, 9357 passed`** になった。うち 12 件 (pin 由来 campaign identity golden と、
  段 2 の A/B 分類を 1 件誤って据置にした fixture pin) を修正し、**残る 32 件は 1 つの
  構造的事実**に帰着した — 凍結チェーンが「現在の ccbench HEAD == 記録 pin」を要求するため、
  **gitlink を進める限りどの実装でも通らない**。
  再発行パッケージの (a)〜(d) は D328 が supersede し、**検証側の保留**で解いた。
  保留は削除でなく可視な held 印で、凍結 bytes は 1 bit も変えていない。
  実測: 当該 6 file が `32 failed` → **`612 passed, 14 skipped` (赤ゼロ)**。
  正しさゲート (holdout 漏洩検出と rr50 陽性対照、未承認世代 admission、variant_binding、
  T-080 の陽性対照と schema、盲検封印 19 件、盲検保護、verifier / admission / 変異検査) は
  すべて保留対象外で無傷。
  正本 = `output/insights/2026-08-12_t816-step4-impl/README.md`、
  一次控え = `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-t816-step4-freeze-chain-blocks-pin-advance.md`
  base: 2d35747e2a8cbd078600bcdb35de2f26eb589038c448b3f32832ffaa40159b7a

- [T-838] **P1・[T-816] の裁定へ吸収済み、実装も同 wave が保持**: hard block の実体
  (凍結 v1 raw trace と歴史 pin 再現経路) は処理した — 凍結 raw bundle は bytes 据置で
  trace 再検証を退役し、歴史再現 driver (`s2_verify_calibration.py`) はコードを変えず
  `docs/phase3.md` へ日付級 1 行を記録した。**本項の終端は [T-816] の裁定に従属する。**
  base: 6585187ae5c157c435e983cd5517f661b956720446efdb795ac69b86c3ac44cf
