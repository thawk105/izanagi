---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2067a-oracle-selection
seq: 1
title: [T-2067] (a) oracle report / verdict / judge へ床値選択規則の再強制を入れた — 払った凍結 pin は test 側 1 か所だけで成果物の再発行は起きない (コード + テスト + docs、branch worktree-dev-wave-t2067a-oracle-selection、変異 matrix = baseline PASSED・KILLED 11・SURVIVED 0・MISMATCH 0・期待 node 完全一致 11/11)
---

## 本文

- **D1526 (ユーザー裁定) の実装。** 3 経路の `main()` で `load_ratified_freeze` の直後・
  historical reverify の前に選択強制を呼ぶ。詳細と実測は
  `output/insights/2026-09-08_t2067a-oracle-selection-enforcement/README.md`。
- **worklog の項本文は台帳より古かった。** 項は「実装するかはユーザー裁定に送る」のままだったが、
  D1526 が既に「実装する」と裁定していた。entry 1333 が現物で確認済みと記していたのと同じ型 (D1335)。
- **段 4 で採用した must-fix 3 件のうち 2 件は、既存先例をそのまま写すと壊れる型だった。**
  (i) 負例の earlier result を走査中立にする — 既存先例 (manifest の real-g1 テスト) は
  reverify を呼ばない経路なので全 repo 走査に当たらないが、本 wave の 3 経路は当たる。
  複製すると強制を消しても `closure-hit-mismatch` が同じ入力を弾き、単一帰属が成立しない。
  (ii) verdict の既存 2 テストは D1504 が名指しで却下した「loader と選択 assert の両方を stub」に
  倒れかけていた。記録 stub へ寄せた。
- **この 2 件は変異走で効き目が実測できた。** `V1-REMOVED` は記録 stub にした既存 2 テスト
  (計 5 node) も赤にしており、純 no-op なら gate 削除を検出できなかった。
  `R1/J1/V1-REMOVED` が各経路の負例を赤にしたことで、MF-1 の単一帰属も実測で成立した。
- **段 3 の 2 レンズが独立に同じ非対称を指摘した。** `verify_manifest` は選択未強制の freeze から
  封印 token を発行でき、library core を直接呼べば 3 CLI の gate を通らずに同種の official artifact へ
  到達できる。D1526 の理由 (防壁の非対称を残さない) に対し、**3 経路は閉じたが library 経路の
  非対称は残る**と正直に記録する。実装しないのは残件 (c) の主題だからで、
  repo 内の production caller は現に 3 CLI に閉じている。
- **段 3 レンズ B の「新規 node を real-repo 登録簿へ登録せよ」は却下した。** ヘルパを持つ suite 自身も
  既存先例も未登録で、登録簿は独立 golden と exact 一致で緑である。静的読解での却下だったので
  焦点走に `test_real_repo_serialization.py` を入れて実測し、緑を確認した。
- **実装子 4 本とも計算ノード投入が rc=16 (infra 失敗) でテストを 1 件も走らせられなかった。**
  4 本とも「実装済み・未実走」と正直に申告し、緑と偽らなかった。親が実走したところ赤は 1 件だけで、
  judge のテストの `assert type(x) is Path` が恒偽 (`Path()` は `PosixPath` を返す) だった。
  同じ経路の親側投入は通っており、rc=16 は子側の環境要因である。
- 段 1 で親が引いた凍結 pin の閉包は byte hash 型しか見ておらず不完全だった。独立の走査で
  構造 pin (呼び手集合・呼出し回数・guard 式・行番号 literal) を回収し、今回の追加行では
  発火しないことを 1 件ずつ現物で検算してから着手した。

## 次の一手差分

### 更新

- [T-2067] **P1・(a) 完了、(b) (c) (d) が残件**: (a) は D1526 のとおり実装し着地した。
  残るのは (b) 「load-only consumer 3 群」という母集合の再確定、
  (c) `build_manifest` / `write_manifest` の公開迂回口 — 段 3 の 2 レンズが独立に指摘した
  `verify_manifest` → `build_observations` / `judge_oracle` / `verify_oracle_verdict` →
  `judge_combined` の library 経路が具体的な到達経路として使える、
  (d) 床値選択 eligibility 導出の被覆の穴、
  (e) s8c C06 予算群 (D1371)、(f) 起動証明書の実時間性 (D1241 が機構を禁じている)、
  (g) s8c production final claim 配線 (D1371)。
  **いずれも D1241 / D1313 の advisory / non-certifying 上限を解除しない。**
  base: 557e27cc6889618bcf955e016f83e30300101b62ace5eeb19aa1c5b9bcc2a333
