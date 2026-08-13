---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t1050-s8b-admission
seq: 1
title: S8b binary store の admission receipt 束縛を保存から oracle 実走直前まで通す (コード + docs、branch worktree-dev-wave-t1050-s8b-admission)
---

## 本文

- ユーザー裁定 第 10 回 #2 (起票) と RP-4 に従い実装した。scope 外指定 (schema 世代移行 /
  旧 artifact の互換 loader / 遡及再取得) は実装せず、影響と推奨を insight と本エントリへ返す。
- 親 brief の provisional 案 (P1「raw receipt を exact-key field としてコピーする」) は
  **コードで実装不能と実測して具体化し直した**。raw `build-admission/v1` は絶対パス
  (`source_root`) を含み outer SHA も root 依存で、既存の「異なる root でも production emitter の
  blob/tree/commit が同一」契約と両立しない。`source_root` だけを除いた root 非依存の派生 receipt を採った。
- 権威を経路で分けた設計判断は {{D:s8b-admission-live-historical-split}}。
- 保証名を「発行時に検証した admission の連続束縛」に狭めた。durable artifact 上の receipt は
  整合した JSON を書けば自己発行できるが、信頼根の新設は [T-868] の既裁定 (署名方式と trust root は
  設けない、自己発行可能な性質は明示したまま受容する) に従い行わない。[T-868] が使う機械可読
  limitation 宣言の経路は T-810 preregistration 族の機構で S8b 側には無い
  (`grep -rn "limitations/" --include=*.py orchestrator/campaign/` が 0 件) ため、DW-G04 に従い
  機構を新設せず docstring と insight へ記録した。
- 敵対レビュー 4 本 (段 3 で 2、段 6 で 2) が独立に「恒真な検査」「先取りされる変異」
  「等価変異」の 3 型を検出した。いずれも謳うだけで発火しない保証であり、放置すれば検出力を
  偽装したまま land していた。詳細は insight。
- **変異の事前登録がテストの穴を land 前に暴いた。** 変異 harness の起動前検査で、
  live 経路の ccbench pin / contract 外部照合 gate に負例テストが 1 件も無いことが判明した
  (既存の当該引数使用箇所はすべて正例)。この 2 gate は敵対レビューが blocker と判定した所見の
  実体であるため、負例 2 本を追加してから本走した。
- 単独変異で殺せない型を正直に記録した。receipt 欠落は exact-key 契約と receipt object 契約の
  二重で構造的に拒否され、単独変異でも両層変異でも受理側へ倒せない。冗長 gate として記録し
  kill に数えない。oracle の receipt-subject 対応検査は validator の事後条件から論理的に冗長な
  等価変異で、fix で削除した。
- 実測: 変異 5 本すべて KILLED、期待 node 完全一致 (MISMATCH 0)、baseline 緑。
- セッション異常 3 件。(1) 段 3 レンズ B が既定 `--max-cli-reported-tokens` 1,000,000 に到達して
  SIGTERM、出力 0 bytes で 877 秒を喪失した (evidence_status は complete で、Web 検索や
  evidence 破損ではない)。上限引き上げと行域読み指示を付けて再投入した。(2) 段 6 レビュー投入時に
  `--lane` を付けて rc=2。`--lane` は `--stage consult` 専用で、この制約は `DW-O01` 本文に無い
  (`--help` にはある)。走行ゼロなので損失なし。(3) 親が焦点走の**走行中に** insight 逐語を
  `output/` へコピーし、ツリー前後を比較する副作用テスト 8 件を赤にした。テスト・実装とも正しく、
  親の並行書き込みが原因。
- 焦点走の推移: 赤 12 → 11 → (queue-wait-timeout で計測不能) → 親の書き込み由来 8 → **0**。
  queue-wait-timeout は `run_tests.py` から待ち上限を延ばす経路が無く (dispatch 既定 900 秒)、
  並行 wave 3 本の混雑が原因だった。再投入で回避した。
- 実装子・fix 子は sandbox から計算ノードへ dispatch できず pytest 実走が常に rc=16 になる。
  実測はすべて親が行った。子はいずれも「緑とは申告しない」と正しく報告した。

## 次の一手差分

### 完了

- [T-1050] S8b content-addressed binary store へ admission receipt を束縛した。保存・resume・
  portable projection・floor 測定直前・oracle 実走直前の各層で検証し、receipt 欠落・不一致・
  別 cell 組替え・store bytes 差し替えを fail-closed に拒否する。変異 5 本すべて KILLED。
  scope 外の 5 件は裁定候補として insight へ返した。
  remaining: none
  base: c0f21389677861c7524a4c2932862494da237179c9004ebd265ea65a0cbe26d6

### 新規

- {{T:s8b-post-run-store-reverification}} **P2・ユーザー裁定待ち**: oracle 実走**後**の
  report / judge が store bytes を再読しない。本 wave の境界 (oracle 実走直前まで) の外として
  非接触にした。塞ぐなら report は `output_root` を持つが judge は持たないため、最終 store seal /
  report receipt / judge API のどれを採るかの設計裁定が要る。材料 =
  `output/insights/2026-08-13_t1050-s8b-admission/README.md`。
- {{T:s8b-legacy-portable-artifact-impact}} **P2・新規**: receipt を持たない旧 portable artifact は
  設計どおり拒否される。tracked `output/s8b-freeze` の該当は 0 件で repo 内の影響は無いが、
  repo 外の過去 run directory・計算ノード上の durable store・手元の resume artifact は
  再 build か破棄が必要。対象件数が未確認のため棚卸しする。
