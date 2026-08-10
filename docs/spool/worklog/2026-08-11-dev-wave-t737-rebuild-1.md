---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t737-rebuild
seq: 1
title: 量化縮退の integration pin を 2 層へ入れた — semantic kill は leaf と発行 tool、production loader は到達性 pin に留まる (コード + docs、受入 8245 passed / 20 skipped / rc=0 / 516.07 秒、変異 13/13 事前登録一致、DW-O17 違反を消すため branch を作り直し、branch worktree-dev-wave-t737-rebuild)
---

## 本文

- **裁定の一次資料。** [T-673] 裁定パッケージ §5 の選択肢 G
  (`output/insights/2026-08-09_t673-transition-quantifier-ruling/RULING-PACKAGE.md`)。
  起票は worklog (367) の [T-737]。本 wave の逐語と変異台帳は
  `output/insights/2026-08-10_t737-loader-issuer-pin/`。
- **段 3 の敵対レンズ 2 本が、親 brief の「層 1」を独立に否定した。** 親は当初
  `activation.load_activation_state` を production loader の入口とし、既存の identity test との
  合成で「production loader を通した」と名乗る予定だった。レンズ A / B はともに、
  その合成では `_load_authority_snapshot` 固有の前処理・後処理を通らないと指摘した。
  親がコードを読み直したところ、**`_load_authority_snapshot` は load を先に呼び calibration 検証は
  load 成功後にしか走らない**ため、遷移違反の負例なら合成 registry でも production loader を
  通せると分かった。裁定で入口を `ec.current_activation_state()` へ引き上げた。
- **段 6 のレビュー 2 本が、その引き上げの kill 意味論を独立に否定した。** 縮退を入れると
  遷移 gate は通るが、直後の `_verify_entry_calibration` が存在しない合成 calibration を
  **別理由で**拒否する。よって production loader 層の node が赤くなっても受理集合は反転せず、
  `DW-M03` の semantic kill ではない。**親が段 4 の事前登録で手前の層しか読まず、gate の後続に
  ある別 module の検証層を見なかったことが原因**である。`DW-M01` は既に「前後に無いこと」を
  求めており、破れたのは規則でなく適用である (F28 の再発として追記した)。
  合成 calibration を 65 env × 2 世代ぶん作る案は採らず (pin が calibration schema へ結合する)、
  leaf 入口の負例 2 本を足して semantic kill をそこで取り、production loader の 2 node は
  **到達性 + 診断感度の pin** として残した。この区別を insights と本エントリに書き分ける。
- **段 3 のレンズが予測した並行 wave 衝突が、受入で実際に起きた。** レンズ B は
  「[T-720] が発行 tool の import 経路を変えたら patch が空振りし、実 authority へ publish しうる」
  と予測した。親はこれを採り、issuer node に fail-closed guard (module 同一性 + 実 authority の
  entry 名 sha256 不変) を要求した。受入前に local main を取り込んだところ **[T-720] が
  landed しており**、guard が発火して受入 1 走目が 4 赤になった (原因 1 件)。
  **guard は設計どおり止めた。**壊れていたのは意図ではなく namespace literal に依存した実現手段で、
  fix2 で「patch した seam が実際に呼ばれた証跡」を assert する namespace 非依存の形へ替えた。
  import 例外台帳へ literal を登録して緑にする直し方は採っていない。
- **純増検出力の実測。** 本 wave の追加前 (main `909914ef`) に対する変異 B が **4/4 SURVIVED** で、
  既存テストが N=4 / N=64 を殺せないことを実測した。新 pin に対する変異 A は **8/8 KILLED**。
  実測点は N ∈ {1, 4, 8, 64} であり、`4 ≤ N ≤ 64` は M=65 fixture に対する**静的 envelope**である。
  N ≥ 65 は **fixture-equivalent** であって program-equivalent ではない (関数は任意長 tuple を
  受けるため 66 env なら `[:65]` は非同値)。**族は閉じていない。**
  N ≤ 3 は既存 4 env fixture が既に殺すため純増ゼロである。
- **branch を一度作り直した。親の規律違反を、例外枠を広げずに消すためである。** 最初の branch
  `worktree-dev-wave-t737-loader-issuer-pin` で、受入前に local main を取り込んだ merge commit
  `57c72a66` が `DW-O17` の「実装面 path が両親と異なれば Codex `role=author` へ」に反した。
  並行 wave [T-720] の import 機械書換えと本 wave のテスト追加が同じ file で結合され、結果が
  両親のどちらとも一致しないため checker が実装面の著作と判定する。**原因は親が受入 script の
  merge message を事前に `role=integrator` だけで書き、merge が共有 file を巻き込んだ後に
  `DW-O17` の条件を再評価しなかったことである。** 一度は「[T-720] の同一原因 merge 4 件と同じ
  既知違反枠へ登録してよいか」をユーザーへ諮ったが、**自分の見落としのために gate の例外枠を
  広げる形になるため取り下げた**。現 main に対する正味差分が競合ゼロだったので、merge を一切
  作らない形で積み直した (`c0788404` → 受入前の main 追随で `5c99cfe5`)。
  最初の branch は削除せず残置してある。
- **変異は作り直しの前後で 3 度走らせた。** 作り直し後の本走は A / C が `c0788404`、
  B が base main `909914ef`。作り直し前の 2 走 (`3a5a76d7` と `f9b44c4c`) も同じ結果で、
  うち 1 つを `mutation-ledger-{A,C}-superseded.json` として insights に残した。
  **同じテスト内容を別 SHA・別 base で 3 度測って一致している。**
- **手順の逸脱を 1 件記録する。** `DW-S06-A` はレビューを `reasoning=high` と定めるが、
  本 wave は段 3・段 6 とも `max` で走らせた。過小でなく過剰方向の逸脱であり検査赤には
  していないが、実際に実行した値を書く (`DW-O12`)。
- **子の内訳。** codex 子 7 本 (plan 1 / 段 3 レンズ 2 / 実装 1 / 段 6 レビュー 2 + 焦点再 1) と
  fix 2 本。段 3・段 6 の 2 本目はいずれも `gpt-5.6-luna`、他は `gpt-5.6-sol`。
  実装子・fix 子はいずれも Pegasus の dispatch を sandbox から使えず **1 度も pytest を走らせていない**。
  実走はすべて親が計算ノードへ dispatch した。
- **受入。** 作り直し後の tip `5c99cfe5` で **8245 passed / 20 skipped / rc=0 / 516.07 秒**。
  受入 lease は計 3 度取得した。作り直し前の 1 走目は下記の namespace 変更で 4 赤、2 走目は
  `de46bdc3` で 8020 passed / rc=0 だったが、base main が動いたため land 対象への受入結果ではない。
  **land 対象 tip は受入 tip と異なる** — 差分は本記録 commit だけで、実 repo を読む検査の対象は
  1 byte も動いていない。
- **段 8 で足した規律が同じ wave 内で発火した。** 「並行 wave が自分の編集 file を所有すると
  判明している wave では、受入全走の前に main を取り込んだ木で焦点 node を 1 度走らせる」を
  `DW-O18` へ統合し、作り直し後の受入 script に実装した。lease 取得後の main 追随で実際に発火し、
  焦点 115 passed を確認してから全走へ入っている。

## 次の一手差分

### 完了

- [T-737] 65 env の合成 registry で量化縮退の integration pin を 8 本入れ、変異 13/13 が
  事前登録と一致した。semantic kill は leaf 入口と発行 tool で成立し、production loader 層は
  到達性 + 診断感度に留まる。この限定は insights と本エントリに書き分けた。
  remaining: none
  base: 9c175c002be6a7d120bde464ad6f93388e5f8d6fc3fd2b79fa21a368c74d8c37

### 新規

- {{T:ident-activation-transition-pin}} **P2・新規 ([T-737] の段 3 レンズ B が検出、scope 外)**:
  `orchestrator/campaign/ident.py:211` の `_load_current_activation_state` と `:292` の
  `verify_recorded_activation_tuple` は、`env_contract` の wrapper を経ずに
  `load_activation_state` / `validate_activation_records` を直接呼ぶ第 3 の production 経路である。
  前者は certified campaign lock の新規作成、後者は既存 lock の再検証に使う。[T-737] が塞いだのは
  裁定が名指した 2 層だけで、この経路は未被覆のまま残る。放置すると、遷移述語の量化縮退が
  この経路を素通りしたとき `campaign.lock` の activation tuple が承認外の transition へ束縛され、
  `admission_status="admitted"` の受理集合へ入りうる。
  正本 = `output/insights/2026-08-10_t737-loader-issuer-pin/README.md`。
- {{T:loader-layer-semantic-kill}} **P3・新規 ([T-737] の段 6 レビュー 2 本が検出)**:
  production loader 層 (`ec.current_activation_state()`) の M>N 負例は、縮退が遷移 gate を
  通ったあと `_verify_entry_calibration` が別理由で拒否するため受理集合の反転を示せない。
  同層で semantic kill と正例を取るには、65 env × 2 世代の合成 calibration 成果物を作るか、
  `_verify_entry_calibration` を patch して correctness gate を迂回するかの択一になる。
  後者は採らないと [T-737] で裁定済みで、前者の要否がユーザー裁定である。
- {{T:issuer-test-syspath-restore}} **P3・新規 ([T-737] の焦点再レビューが検出、本 wave 以前からの欠落)**:
  既存の発行 tool test 4 本が `issuer.__file__` を tmp へ patch して `main()` を呼ぶが、
  `main()` が `sys.path` へ挿入した tmp path を復元しない。`monkeypatch` は list の直接変更を
  undo しない。放置すると worker 内に stale な import path が溜まり、後続 node の module 解決が
  実行順依存になりうる。[T-737] の新 3 node は復元済み。
