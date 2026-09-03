---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2067-bcd-selection-closure
seq: 1
title: [T-2067] 床値選択の公開迂回口を塞ぎ、実導出を launch / consumer 経路へ通した — 親の probe は「repo 全体で未検査」でなく「2 経路だけ未検査」を示した (コード + テスト + insight、branch worktree-dev-wave-t2067-bcd-selection-closure、変異は静的追跡のみで実走せず)
---

## 本文

- **ユーザー裁定により (b)(c)(d) だけを実装し、(a)(e)(f) は scope 外とした。**
  (a) は凍結成果物の bytes が変わるためユーザー裁定送り、(e) は T-2159 着地後の再評価、
  (f) は D1241 が機構を禁じている。
- **親の変異 probe が (d) の前提を実測で狭めた。** 正本 (archive worklog 1202) は
  「実導出を走らせて rule-mismatch を出す test が repo に無い」としていたが、
  `test_s8b_holdout_freeze.py::test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility`
  が 2026-08-29 (commit `31426fb9a`) から存在していた。
  `_derive_floor_selection_eligibility` を無条件 `False` へ一時変異させると
  (`-k "selection or eligib"` の 4 file で) baseline 25 passed → 6 failed / 19 passed となり、
  **赤 6 件はすべて v2 candidate 経路**で、launch 経路と consumer 経路は全緑だった。
  穴は「repo 全体で未検査」ではなく **「launch 経路と consumer 経路が実導出を一度も通らない」**である。
- **この「6 failed」は `-k` filter 内の値であり、repo 全体の kill 数ではない。**
  段 3 の 2 レンズが独立に filter 外の
  `test_s8b_holdout_freeze.py::test_v2_candidate_enumerates_and_reads_earlier_run_through_bound_dirfds`
  を指摘し、親が現物を読んで追認した。親の一般化を狭めた。
- **段 2 プランの `sys.setprofile` による code frame 観測は採用しなかった。**
  段 3 のレンズ A が「実導出の冒頭を `return True` に変える故障では同じ code frame と引数が
  観測されてしまい殺せない」と反証した。代わりに D1504 が既に定めていた
  「実 loader と実 callee を通す genuine な正例と負例」を対で張った。**この 2 件は scope 逸脱ではなく、
  着地済み裁定の履行である。**
- **段 2 プランの caller 列挙が親 brief の漏れを 6 件訂正した。**
  `test_s8b_oracle_manifest.py` の 4 件と、親が file ごと落としていた
  `test_s8b_oracle_driver.py` の 2 件。改名対象は合計 25 箇所。
- **(c) の private 化は命名規約であって機構的閉包ではない。** in-process の caller は
  underscore 名を直接呼べる。ユーザーの依頼は「**公開**迂回口を塞ぐ」であり seal token は
  scope 外の新機構なので採らなかった。絶対規律 7 に従い、閉じていない範囲を主張せず明記する。
  `verify_manifest` が選択 token を要求しない点は (a) の裁定対象と重なるため裁定パッケージへ送る。
- **敵対レビュー 2 本とも must-fix 0 件だった。** レンズ C は変異 X (常に False) が拒否側 2 node を、
  変異 Y (冒頭 return True) が受理側 2 node を赤にすることを静的に追跡し、正負の対が両方向の
  故障を殺すことを確認した。レンズ D は旧 3 名の実行参照 0 件と 25 caller の過不足なしを独立に数え直した。
- **焦点走の file 集合を大きくすると、単独では全緑の file 群が集合走でだけ大量に赤になった。**
  `test_s8b_ratified_verify.py` 単独 189 passed、`test_s8b_oracle_manifest.py` 単独 107 passed、
  `test_s8b_oracle_report.py` + `test_s8b_oracle_driver.py` 395 passed / 6 skipped。
  ところが 4 file を 1 集合に載せると 10% 到達時点で赤 20 件超。scheduler は両方 `loadgroup` で同一。
  **全走 (正規の走行構成) では再現せず、実装起因の赤は 0 件だった。**詳細は {{F:focus-set-only-red}}。
- **実装子と両レビュー子はいずれも codex sandbox の制約で pytest を開始できず、正しく
  「実装済み・未実走」と申告した。**実測はすべて親が行った。
- **前セッションが段 6 の途中で落ち、背景 3 本 (焦点走 + レビュー 2 本) が成果物を残さず died した。**
  レビューは `--job-id` を変えて再投入した。worktree と実装差分は無事だった。

## 次の一手差分

### 更新

- [T-2067] **P1・一部完了 (設計択一 2 件は D1325 で終端、強制は s8c 床値 verifier / publish と
  oracle manifest まで実装済み、(c) 公開迂回口と (d) launch / consumer 経路の実導出被覆は本 wave で完了)**:
  残るのは
  (a) oracle report / verdict / oracle judge への選択強制 — report と judge は manifest の
  `_GENERATOR_SOURCES` に含まれるため、編集すると凍結成果物の bytes が変わる。実装するかは
  ユーザー裁定に送る。`verify_manifest` が選択 token を要求しない点も同じ裁定対象、
  (e) s8c C06 予算群 — C05 schedule authority の着地後に再評価 (D1371)、
  (f) 起動証明書の実時間性 — 独立した外部 commitment 無しには閉じられず必要な機構は D1241 が禁じている、
  (g) s8c production final claim 配線 — 前提が連言で不在 (D1371)。
  **(b) の母集合は 4 群で確定した** (report / judge / verdict と C06 予算群)。
  `s8b_oracle_driver.py:496` は選択強制点ではなく、強制点は `:664` と `:1351` である。
  **いずれも D1241 / D1313 の advisory / non-certifying 上限を解除しない。**
  base: 6cbf443d5fc37ab428348edd8e4ecbc76d0448cf96d7f57e5a63cefff133b229
