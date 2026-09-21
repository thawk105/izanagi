# 段 4 裁定 (2026-09-21 08:1x JST、相談 A `codex/s3-consult-A.md` の 18 所見)

裁定の原則: 相談の所見は一次資料 (log / land 記録 / git diff) で親が再確認したものだけ採用する。実装・docs 改訂・gate・台帳の追加はしない (診断のみ)。

| # | 裁定 | 採否 | 処置 |
|---|---|---|---|
| 1 | real must-fix | 採用 | `dev-wave-t2243-collection-diag/land-.stdout` は `status=landed`、mtime 09-20 23:13:14 (親が実測)。母集合を t2243 入り・t2807 外しに訂正。t2243 は焦点走 0 本 (同条件の検索で 0 件) なので 27 本・秒数は不変。script の固定リストは残し README に選択規則との対応を明記 |
| 2 | refuted (算術) + 出所説明の訂正 | 採用 | 27 本中 18 本 (t2344 / walldecomp / t2814 / t2810 / residue / t2797) は start / end 行が無く `.pid` / `.done` の mtime。README §2 の出所説明を訂正 |
| 3 | real should | 採用 | RUN = Started→Ended であり footer の Elapse (t2803 f1 76 秒、residue f2 131 秒) と 4 秒違う。「= Elapse」の括弧書きを削除 |
| 4 | real should | 採用 | walldecomp の投入前 21 / 29 秒は bounded local の失敗試行 (cap-oom → dispatch 退避) を含む。通常の投入固定費 (1〜2 秒) と分けて書く |
| 5 | real should | 採用 | queue の名称を「Created→Started = ノード開始前の待ち (QUE・PRR 等を含む)」にする。「厳密な QUE+PRR」「receipt は全件消失」は書かない (walldecomp focus-2 の receipt は同 wave の insight verbatim に現存) |
| 6 | refuted (結論は維持) | 採用 | t2817 の 2 本の母数外の根拠を「login の bounded local 予算予約の行が log にある」肯定証拠に替える |
| 7 | real must-fix | 採用 | 「契約最小 17〜19 本」「契約内 19 / 契約外 8」を撤回。契約は job 数でなく充足条件 (集合・単独 process・tip・新規 file のメタテスト・改訂追随) を定める。表を「目的別内訳」と「充足状況」に分ける |
| 8 | real must-fix | 採用 | (P1) は (b): D325 の「別 process の単独走」「全走の緑はその file 単独の緑を含意しない」は多 file 走への包含で満たされない。#4 / #9 は単独確認走 (契約内)。同一 pytest process への統合は D325 を変える案 = 契約変更として択一へ |
| 9 | real must-fix | 採用 | t2810 の 10 / 17 file 集合は inventory 4 群のうち 1 群のみ。ただし実行 (09-20 20:08〜20:51) は T-2813 land (22:49) の前で当時契約には適合。「改訂前実行」と現行契約適用時の不足を分けて記す。同様に t2804 / t2803 / t2344 f1・f2 / t2797 focus-1・2 も改訂前実行 |
| 10 | real must-fix | 採用 | #12 (t2344 f3) は改訂追随走として妥当 (land 22:49:08 → f3 Created 23:15:31)。#27 は「merge 後の再確認走、義務充足への寄与未確定」— commit 5 の login 実走の集合・単独性の証拠が README に無い |
| 11 | real must-fix | 採用 | residue f1 の赤は log どおり 92 failed / 65 errors = 157 件 (FAILED 列挙 cleanup 10、campaign 81、wiring_probe 1)。insight の「10 + 33 + 1」は原因の帰属であって件数でない。表を訂正 |
| 12 | real should | 採用 | walldecomp の 2 本は DW-O26 でなく DW-S07「docs commit 後に … 影響テストを再走して閉じる (F34)」に根拠がある「docs 影響確認走」。C5 の感度分析は削除 |
| 13 | real must-fix | 採用 | held 走の「同 job 化不可」は process と job の混同。同 job 内で env を分けた別 process は runner 次第 (実装案件)。固定費の比較値 735 秒 (6 + 715 + 14)、対象は 2 file・9 node に訂正 |
| 14 | refuted (合計) + real should (分布) | 採用 | 長待ち帯は 337〜1,020 秒 (12 本)、平均 632 秒 / 中央値 623 秒。短待ち帯 14 本平均 8.9 秒。「混雑時 ≈ 5 分」を撤回し帯別の値で書く。帯分けは事後で、将来の混雑予測ではないと明記 |
| 15 | real must-fix | 採用 | 効果は候補ごとに固定費 (投入前 + queue + collection) の実測比較値で書き、job 廃止 / 同 job 化 (RUN 不変) / 重複実行削除を分ける。#4 = 27 秒、#9 = 22 秒 (HEAD が違うので順序の組み直しが前提)、E3 の 158 / 524 秒は別の反実仮想で足さない |
| 16 | real should | 採用 | 別 worktree (同 SHA) からの並行投入は D289 の例外に当たらなければ可能 (T-2817 の実測)。job 数と queue 合計は減らず経過時間の重なりを作る策として別枠に書く |
| 17 | 判定不能 | 採用 | 1,007〜1,020 秒の 3 例は観察として記録、原因帰属はしない |
| 18 | real should | 採用 | 「契約外 = 削減可能」「job wall 合計 = wave 短縮」を切り離す。t2803 の赤 2 本は依存 fix の入力、t2810 は review と並走済み (251 秒の重なり) |

brief への指摘: (P6) と 19 / 8 を撤回 (採用)。scope 文の「decisions / failures fragment は新事実があれば」は通常の記録 (spool fragment) の意味で台帳新設ではない — README で明記 (採用)。研究前進は「必須 / 任意 / 未確定の区別と条件付き削減候補の提示」に限定 (採用)。既存策 (F558、DW-O20 の untracked 禁止、memory) の再記載を新規改善と数えない (採用)。T-2813 前後を分ける (採用)。

## 裁定後の新事実 (親の実測、`verbatim/changed_files.txt`)

各 wave が main へ入れた test file (land 記録の main_before..landing_tip の `git diff --name-only`): t2804 3、t2803 1、t2344 6、t2814 1、t2810 2、residue 2、t2797 7 = 22 file。このうち D325 の字面 (別 process の単独走) で走ったのは **t2803 の 1 file (#4 統合 tip、#9 fix commit 後) と t2344 の 1 file (#13、受入赤 fix2 後) の 2 file**。残り 20 file は多 file 焦点走 (と受入全走) だけで受入へ進んだ。単独走 3 本はいずれも緑 (この標本では単独走だけが検出した赤は無い、n = 3)。

→ 依頼文の「単独走と inventory 群の同 job 化」は、同一 pytest process への統合なら D325 を変える (契約変更)。契約を変えない形は「1 job 内で集合 process と単独 process を分けて走らせる」で、現行 `run_tests.py --force-dispatch` は 1 argv = 1 pytest invocation なので runner 側の対応が要る (実装案件、本 wave では実装しない)。

## プラン v2 (診断成果物の形)

insight README を次の構成にする: §3 本数と wall (訂正: 母集合、出所、RUN、queue の名称、帯別)、§4 契約の充足条件 (job 数でなく条件)、§5 27 本の目的別内訳 (表 A) と充足状況 (表 B: 集合走 / 単独走 / 改訂前後)、§6 契約を変えずに減らせる候補 (候補ごとの固定費比較値、頻度、前提)、§7 裁定パッケージ (択一、契約を変える / 変えない)、§8 判定不能・言わないこと、§9 段 6 レビュー、§10 検査・受入。変異は免除 (実装面 0 行)。
