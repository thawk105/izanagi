---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-branch-residue-cleanup
seq: 3
title: 残骸 branch/worktree が溜まらない構造にした — 段 9 の自己撤去が統合証明済みの Codex 子 branch を履歴 bundle 後に -D し、/cleanup-branches に裁定条件つきの -D 経路を足し、損失 commit 248 件を台帳へ転記 (コード + docs、branch worktree-dev-wave-branch-residue-cleanup)
---

## 本文

- ユーザー裁定 (2026-09-21 00:40 頃「`/cleanup-branches` は branch の `-D` をしてよい / 残骸 155 本は消す / 自己改善 wave で再発を防ぐ」) を受けた
  自己改善 wave。起動引数の成果物 1〜6 (D 化・command §0/§2・段 9 の子 branch 削除・F・台帳転記・lock 再検査) をすべて実装した。裁定は
  {{D:cleanup-force-delete-and-child-branch}}、失敗型は {{F:cleanup-allowlist-structural-residue}}。一次資料は
  `output/insights/2026-09-21/branch-residue-cleanup/README.md` (brief・plan・相談 2・裁定・author 3 巡・レビュー 2・変異台帳の逐語)。
- 起点 local main `285477c00` (fresh worktree、01:17 JST gate rc 0)。最初に切った worktree 名に未採番の T 番号を使い (spool/worklog/README.md の規則違反)、
  主題 slug で作り直した (旧木は commit 0 で撤去)。段 4 直前に `2afb39768` (第 27 回 rulings) を ff-only 取り込み。
- **段 1 の実測で前提を更新:** `cleanup-branches.md` は 6,181 / 6,204 bytes (引数の 5,900 / 5,888 は旧値) で T-2814 が並走編集中、cleanup session の
  事前 report (rescue2.json) は job dir 削除で消失、**D2163 (前日) が「子 branch は削除しない」を明示的に却下済み** (今回の 155 本の摩擦が未見事実)。
- 段 3 (2 レンズ、real 14 / refuted 9) の主な採用: 所有 path 一致で通った子の中間 commit は branch 削除で保全根を失う (→ `-D` 前に `history.bundle`)、
  監査非通知 161 件は「報告対象外」であって着地証拠ではない (親の追加実測の誤りを訂正)、cleanup 実行内で台帳へ書く案は台帳契約・land・F747 と衝突
  (→ 転記は別 wave)、pending の note を広げる schema 改訂は不要、author A/B の file 所有を素集合に、同木の旧 fix branch は manifest に無く
  段 9 の対象外 (→ 次の一手)。
- 段 5: author A (実装済み・未実走、login では pytest 不可) → fix1 (HEAD が main 祖先の子で bundle 範囲が空) → 焦点走 f1 で cleanup test 10 node が
  同根で赤 (`git bundle create` は ref 名を要求し bare sha では "Refusing to create empty bundle") → fix2 (`refs/heads/<name>` を渡す、detached は
  bundle なし) → f2 = 1011 passed / 5 skipped / 0 failed。f1 の setup error 群は test でない契約 module `orchestrator/test_selection_contract.py` を
  pytest に渡した親の誤り。fix は同木・同 branch に積んだ (fix ごとに新 branch を切ると B-1 の残骸を自分で作る)。
- T-2814 land (03:19、main `e07c220a0`) を非 ff merge で取り込み、その版 (6,201 bytes、§2 に「非施錠を再確認」が入っていた) を base に親が
  `cleanup-branches.md` §0/§2/§3/§5 を改訂 (7,055 bytes、非施錠の再確認を `.git/worktrees/<name>/locked` 不在の検査として具体化)。author B が
  `check_docs.py` (SHA・予算・DW-O28 literal) と `test_check_docs.py` (fixture・literal・len・padding) を追随 → 焦点走 f3 で 2 件赤 (fixture 変異の
  anchor が旧文言 / 予算余白 0 で 1 byte 追加負例が 2 件違反) → fix1 (anchor 追随、予算 7,058 = 余白 3) → f4 = 2438 passed / 10 skipped / 0 failed。
  SKILL.md は変えない (Codex overlay は既存の縮退で足りる)。
- 段 6: レビュー 2 本 (正しさ境界 / 過剰・削除) は共に NO-GO だが実装 must-fix なし。must-fix = DW-O28 本文の 3 限定 (撤去前の拒否・HEAD 祖先なら
  bundle 省略・manifest 現行 branch) → 994 bytes へ改訂、変異評価の再照準 (M7/create は mask、M8 は診断 pin、削除失敗の fail-open は 4 層が独立に
  守るので累積 4 置換 M8b で登録)、fragment の対応表と母集団表現。bundle の実行順は段 4 案 (撤去後) より安全側の backup phase (撤去前、
  退避失敗時は木・admin・branch を保持) に変わったことを記録する。
- 変異 (DW-M01〜M08): probe (M0〜M9、全件 SURVIVED 期待で観測) + probe2 (M8b) → final = **KILLED 10 / SURVIVED 1 (M0) / MISMATCH 0、期待 node 完全一致 11/11** (baseline 201 passed 27 秒/run、head `cdc5ddb59`、runner = test_dev_wave_cleanup.py の dispatch)。kill に数えるのは 9 件 (M1〜M7・M9・M8b)。文書 pin の変異 (runner = test_check_docs.py): probe → final = **KILLED 2/2** (M10 = DW-O28 literal の ASCII 1 byte: 337 node、M10b = CLEANUP_COMMAND_SHA256 の 1 hex: 321 node、合成 fixture 依存 test が連鎖する型で期待 node 完全一致)、対照 M0d SURVIVED、head `1972bd33f`。手動 probe (DW-O19): command の 1 byte 置換 → check_docs rc 1 (SHA 不一致 1 件)、DW-O28 の 1 byte 置換 → rc 1 (exact 契約不一致 1 件)、復元後 clean・rc 0。M7 は `[verify]` が主証拠 (`[create]` は
  後続の directory 読込みに mask)、M8 は diagnostic sensitivity pin (kill 数に入れない)、M5 は正常受理の縮小の検出。
- 台帳: 損失 227 件 (全件 fsck 到達不能、削除 branch 1〜8 本から到達可能だった) + 監査のみ 21 件 (2026-08-23〜09-09 の commit、削除閉包外) = 248 entry を
  既存 schema のまま pending で追記。追記後の `--ledger-check` は rc 3 (pending 通知)、parse 完全、未記帳 0、entry 278。
- **D2194 項 10 (T-2821) の前提は既に偽だった:** 候補 2 の 6 本と `impl-t2766-pairing-optin` は裁定 (00:5x) の前 00:46 の cleanup で worktree 撤去 +
  branch を bundle 退避後 `-D` 済み (retire-worktrees.json / deleted-branches.tsv で照合)。DW-O12 に従い実行済み手順として記録し完了に置く。
- 言わないこと: 段 9 改訂で残骸が「溜まらなくなった」(証明不能な子・同木の旧 fix branch・中断 wave・dev-wave 外の branch は経路 2 の回収対象、
  被覆割合は未確定)。「40 wave 分」「1 wave 2〜8 本」は名前からの概算。監査非通知 161 件が main に着地したとは言わない。bundle は Git object を延命しない。
- 受入・検査: 焦点走 f2 (実装面、1011 passed / 5 skipped) と f4 (check_docs 側を含む 14 file、2438 passed / 10 skipped / 0 failed)、親の `check_docs.py` rc 0、
  全史 provenance 監査 (段 7 前 12,220 件) 違反なし、変異 KILLED 10 + 2 / MISMATCH 0。受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し、
  受領証は job dir (`acceptance-receipt-*.json`) と land の記録が持つ (件数は本文へ書かない)。
- 工数: codex 10 本 (plan 1・consult 2・author 2・fix 3・review 2、gpt-6-astra / medium)、計算ノード job = 焦点走 4 (f1 赤 → fix2 → f2 緑、f3 赤 → fixB1 → f4 緑) +
  変異 33 run (tool 系 probe 11 + probe2 2 + final 12、文書系 probe 4 + final 4) + 受入。login = 台帳照合 2、fsck 1、台帳生成 31 秒、手動 probe 2。wave 開始 00:59 JST。

## 次の一手差分

### 完了

- [T-2821] 候補 2 の 6 本 (`witlight-author` / `t2153-author` / `t2629-unit-probe` / `t2709-unit-probe` / `t2766-unit-impl` / `t2802-unit-probe`) と
  `impl-t2766-pairing-optin` は、D2194 項 10 の裁定 (00:5x) より前、2026-09-21 00:46 JST の `/cleanup-branches` で worktree を撤去し branch を
  bundle 退避後 `-D` した (実行済みの手順。裁定の「branch は残す」とは異なるが、内容は `deleted-branches.bundle` に 140 heads で退避済み、損失 commit は
  台帳に pending で転記済み)。本 wave が一次資料 (retire-worktrees.json / deleted-branches.tsv) で照合した。
  remaining: none
  base: d274b0b2616059833f7981d9aa6ebafd6505f8f1b2e74b5bdb3e09732d08d634

### 新規

- {{T:child-manifest-retired-branches}} **P3・新規**: 同じ木で fix 巡ごとに切り替えた旧 branch は manifest に 1 本しか無く段 9 の自己撤去で残る
  (今回削除した 140 本のうち名前に fix を含むものが 55 本)。fix 巡の再登録時に manifest へ `retired_branches` を記録し、tool が統合証明の
  下で消す設計を裁定パッケージ (manifest schema と `DW-S05-A` の改訂) として提示する。それまでは `/cleanup-branches` の `-D` 経路が回収する。
- {{T:ledger-pending-248-resolution}} **P3・新規 (ユーザー裁定待ち)**: 到達不能 object 台帳に pending で転記した 248 entry (損失 227 + 監査のみ 21) の
  解決 — bundle (`dev-wave-jobs/cleanup-branches-20260921-rescue/deleted-branches.bundle`) からの救出 ref 作成 (`rescued`) か喪失の明示受容
  (`accepted-loss`、人間のみ)。監査のみ 21 件 (2026-08-23〜09-09) は削除 report が無く個別 triage が要る。`--ledger-check` は解決まで rc 3 のまま。
