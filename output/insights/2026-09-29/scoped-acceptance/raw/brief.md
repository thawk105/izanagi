# 段 1 brief — scoped-acceptance (縮小受入)

依頼: /work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/md_1.txt (ユーザー発言の逐語を含む)。全 9 段。

研究前進 (土台): docs・知見・台帳 fragment だけの wave の land を、計算ノード混雑に左右される全受入
(2026-09-29 VHash の docs-only land で約 5 時間) から外し、論文向け知見 wave の回転を上げる。
完了判定: 知識面だけの変更を持つ tip が縮小受領証で land を通り、実装面を 1 file 混ぜた tip の縮小受領証は
land が拒否し、同じ tip の縮小受入と全受入の所要を同時刻で比べた値が insight にある。

確定済みユーザー裁定: (U1) 2026-09-29 夜の発言 (md_1.txt 逐語) — 知識蓄積だけの wave は land を速くしてよい、
dev-wave にそれを分からせる。(U2) D747 テスト削除は採らない。(U3) D237/D301 旧射程 (docs-only も受入全走) は
U1 が前向きに上書きする対象 (D237 自身が「機械 gate 化は範囲外、ユーザー裁定へ返した」と書く)。
(U4) D95 決定 2 実装面は path と拡張子で決まる。(U5) D662/D987 受入後の main 取込は runner blob 差だけ再受入。

不変条件: 規律 2/3 (正しさの門 = 検査器・trace・受領証・事前登録・凍結に触れる path は全受入)。fail-closed
(分類不能・迷いは全受入)。既存 v5 受領証経路は弱めない・変えない。テストは 1 件も削らず hold も足さない。
分類は wave の自己申告でなく tested_main..tested_tip の git 差分から land が lock 内で再導出する。

暫定裁定 (親の provisional、段 3 の攻撃対象):
(P1) allowlist は閉じた列挙で最小に始める: `docs/**/*.md` と `output/insights/**` の非実装拡張子 (md/txt/json/jsonl/csv/tsv/svg/png/pdf?) と
  `docs/spool/**` fragment。除外 (全受入): D95 実装面すべて、`docs/dev-wave/**`、`.claude/**`、`.agents/**`、`AGENTS.md`、
  `CLAUDE.md`、`docs/skill-self-improvement.md`、canonical 3 台帳 (`docs/worklog.md`/`decisions.md`/`failures.md` の直接編集)、
  事前登録・erratum・freeze 系 docs、`patches/**`、`external/**`、`output/` の insights 以外、gitlink・symlink・mode 変更・非 UTF-8 path。
(P2) 「正しさの門に触れる doc」は production code (orchestrator/ tools/ hooks/ の非 test) が path literal で参照する path として
  機械で数え、全受入側へ倒す (手書き列挙だけに頼らない)。
(P3) 縮小集合 = `_REAL_REPO_NODE_INVENTORY` ∪ 変更 path を literal (full path / basename) で参照する test file ∪ docs 検査の固定集合
  (test_check_docs.py・spool 系・provenance 系・inventory 4 群) + 直接実行 3 本 (`tools/check_docs.py`、`tools/spool_fold.py --dry-run`、
  `tools/check_ai_provenance.py`)。growth hold 3 件 (docs_bytes) は現行全受入でも skip なので、直接実行が検出力を補う。
(P4) 受領証は新 schema (v5 と別名)。分類結果・変更 path 列の digest・選択集合 digest・分類器/選択器の blob を束縛し、land は lock 内で
  分類と選択を再導出して一致しなければ拒否。取込後の main 差で分類器・選択器・runner の blob が変われば再受入。
(P5) 縮小受入は login admission 内で走ることを目標にし (run_tests.py の既存 login 判定を再利用)、dispatch に落ちても可。

成果物: 分類器・縮小受入 launcher・land 受理の実装と test (Codex author)、DW-S04 と runbook §7.3 の改訂、
insight `output/insights/2026-09-29/scoped-acceptance/README.md`、decisions fragment (U1 の記録 + 設計)、worklog fragment。
DW-G05: 放置すると land の受理集合は変わらず知見の land が混雑に律速される。実装を誤ると実装面の変更が全受入なしで main へ入る
(受理集合の拡大) — 負例 test と変異で必ず殺す。
DW-G04 発火: md_1.txt と worklog (1949) 行の受入経緯 (VHash job dir) が既存の発火実例。

分割方針: 実装子 2 本 (所有を分ける)。A = 分類器・選択器の新 module と test。B = 受入 launcher/待ち手の縮小形と
dev_wave_land.py の受理、その test。docs は親。段 3 レンズ: (a) 縮小で見逃す赤 (b) 受理集合の漏れ・偽造 (c) 運用・予算・D747/D237 整合。
受入・実測環境: Pegasus login (縮小受入)、計算ノード dispatch (本 wave 自身の全受入)。所在は runbook §7。
