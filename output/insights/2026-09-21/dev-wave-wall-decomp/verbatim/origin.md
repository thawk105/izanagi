# 依頼の逐語 (/dev-wave の引数、2026-09-21 00:52 JST 起動)

dev-wave 1 本の所要の分解と短縮 (台帳 ID 未起票、着手直前の local main から fresh worktree)。段 1 で直近 landed wave 12 本
  (/work/1/SFC/tanab/dev-wave-jobs/<wave>/ の HANDOFF.md の時刻・startup-gate.log・codex/ の receipt・dispatch job log の
  queue/RUN・acceptance-receipt-*.json・land-*.json。時刻は file の mtime と commit 日時で採り推定しない、読んだ値は verbatim/ へ写す) から段別
  wall を再構成する — 起動〜段 1 brief、codex 子 (author / review / fix) の各 wall と親の待ち、焦点走の queue と RUN、変異 probe + final、受入
  (lease 待ちと走)、land (監査と fold)、段 7 記録。合計に対する上位 3 成分と wave 間のばらつきを出す。受入全走の短縮は [T-2273]+[T-2817] の
  wave が持つので測るだけで触らない。実装は 2 件に限る: (a) 変異 probe の dispatch 走を login の self-run (各変異を生成器に注入 → 新 test file
  の __main__ harness で自走 → 原 bytes へ復元して sha256 一致を assert → 観測 node で final を 1 回) に置き換える手順を DW-M08 に収容する
  (2026-09-20 fig13 wave の実測 = 20 変異 1 分、final 20/20 一致。self-run と pytest で node が食い違いうる parametrize / skip のある test は
  dispatch probe に戻す条件を残す。docs/dev-wave/ の byte 予算は D782 手順 1 段目 (既存記述の削減) で収容し上限は動かさない、check_docs / test
  の pin literal 追随は Codex author = D95)。(b) 段 1 の上位 3
  成分のうち既存機構の局所修正か手順変更で効くものを、効果を同じ資料で見積もってから 1 件だけ Codex author で実装する (受理集合・正しさ
  gate・受入要件・5 分上限 D690 は変えない、hooks の拒否を迂回しない)。残る成分は効果見積り付きで裁定パッケージへ。規律 1・2
  を緩めない。並列化のための新 framework・自動 sweep・台帳・gate の追加は scope 外。
