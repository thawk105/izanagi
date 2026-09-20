# 段 1 brief — dev-wave 1 本の所要の分解と短縮 (2026-09-21、brief.md の mtime が起草時刻、起点 local main 285477c00)

**研究前進:** 土台。dev-wave が論文の実験・図表・記録を運ぶ唯一の経路で、1 wave の平均 154 分 (impl 170 分) が研究の回転を律速している。本 wave は (1) 直近 landed 12 wave の一次資料から段別 wall を再構成し上位成分とばらつきを出す、(2) 変異 probe を login self-run へ置き換える手順を DW-M08 に収容 (実測 = fig13 wave: 20 変異 2 分、final 20/20 一致)、(3) 上位成分のうち手順変更 1 件を実装、残りを効果見積り付きで裁定パッケージへ。完了判定 = 12 wave の表 (verbatim/stage_walls.md)、DW-M08 / DW-M05 の改訂が check_docs 緑で land、insight に上位 3 成分・ばらつき・裁定パッケージ。

**scope (純増):** 一次資料は `/work/1/SFC/tanab/dev-wave-jobs/<wave>/` の file mtime (verbatim/<wave>.mtimes.txt に写した)、mutation attempts json の started/finished、dispatch receipt (state_history / queue_wait_s)、land-*.json、acceptance chain log。既存被覆: F42 (自走 harness の二択)、D805 (pre-running → RUN の正規化)、記憶 mutation-expected-nodes-via-login-selfrun (fig13)。所要分解の先行記録は無し。

**段 1 実測 (verbatim/stage_walls.md、成分は wall で重なりうる):**
- 合計: 全 12 中央値 162 分 / 平均 154 分 (65〜215)、impl 7 本 平均 170 分 (119〜215)、docs 5 本 平均 131 分 (65〜194)。
- 上位 3 成分 (平均合計に対する比): (1) 親だけが動いている時間 (合計 − 子・走・land・撤去の union) 42.5 分 = 28% (impl 47.8、うち起動→段 1 は impl 11.7 分、段 7 記録の直列区間 impl 10.7 分)。(2) 受入 = 門番/claim 待ち 23.0 分 + 走 20.6 分 = 44 分 = 28% (docs wave は門番待ち平均 48 分・最大 99 分が支配、impl は走 19.4 分)。(3) 変異 probe + final 23.6 分 = 15% (impl 40.4 分 = 24% で impl の第 2 位)。次点: codex 子 union 20.7 分 = 13.5% (impl 28.9)、焦点走 10.8 分 (impl 17.3)、land 8.8 分、撤去 5.1 分。
- 変異の内訳 (t2804 final、attempt 台帳 + receipt): 1 変異 53 秒 = qsub→ノード開始 20 秒 + ノード上 27 秒 (pytest 21 秒) + END 後処理 6 秒 + 次 attempt まで 7.5 秒。pytest は final 29 分の 18%、固定費 28%、**PRR 外れ値 (qsub→ノード開始 5〜17 分、5 wave 84 job 中 8 件、計 60 分超) 39%**。receipt は D805 の正規化で pre-running を RUN に写し queue_wait_s は常に約 5 秒 — peer session の観測と一致 (prr_check.txt)。probe は impl 平均 17.8 分 (13.6〜26.4) で、fig13 の login self-run 実測は 2 分。
- 受入の再走: terminal-postcheck rc=70 (main が動いた) が 4 wave 5 回、門番 (leaders ≤ 1 ∧ load ≤ 60) 待ちは docs wave で 11〜99 分。land のやり直し (stale-main / another land running / fold-gate-failed / incoming 変更) は 7 wave で計 25 分。
- 撤去は worktree 1 本あたり約 1 分 (占有走査 2 回)。land 成功走の window ≈ 300 秒は全史 provenance 監査 (T-2803 が 00:12 に着地、以後の wave で短縮見込み)。

**確定済みユーザー裁定 / 引数の制約:** 受入全走の短縮は [T-2273]+[T-2817] の領分 (測るだけ)。実装は (a) DW-M08 の self-run 手順収容、(b) 上位 3 成分のうち 1 件、の 2 件だけ。受理集合・正しさ gate・受入要件・D690 5 分上限は不変、hooks 拒否の迂回なし。docs/dev-wave の byte 予算は D782 手順 1 段目 (既存記述の削減) で収容し上限は動かさない。pin literal の追随は Codex author (D95)。並列化の新 framework・自動 sweep・台帳・gate の追加は scope 外。規律 1・2 不変。

**(b) の選択 (P1、親の provisional 裁定・攻撃対象):** 変異 final の走行中 (impl 平均 22.6 分、親は待つだけ) に段 7 の草稿 (insight README・fragment 本文・check_docs / fold dry-run / 三軸走査の準備) を job dir で進め、final 後は結果値の記入と commit だけにする手順変更。効果見積り: final 終了→受入投入の直列区間 impl 5 本 (t2803 9.5 / t2804 5.7 / t2813 9.9 / fig13 14.4 / t2153 11.4、t2344 は focus-f3 12 分を除き 7.2) 平均 9.7 分 → 約 3 分、**約 6.7 分 / impl wave (impl 平均の 4%)**。収容先は DW-M05 (変異 final 起動時に読む L1.5 節)。却下候補と見積り: 変異 job の batching (final 29 → 約 8 分だが harness の構造変更 = scope 外)、dispatcher poll 5 秒の短縮 (final あたり 2 分、qstat 負荷増)、fix 用 unit worktree の再利用 (1.5 分/wave)、撤去の占有走査 (4 分/wave だが上位 3 外)、受入門番の緩和 (docs wave 48 分だが裁定事項)。

**(P2) 実装面ゼロの見込み:** DW-M08 / DW-M05 の本文は check_docs / test に literal pin されていない (exact pin は DW-O18/O25/O26/O28/C01 と入口節のみ)。docs-only なら D95 により親が編集し Codex author は不要 — 引数の「Codex author で実装」は pin 追随が発生した場合に発火する。段構成は軽量版 + 診断 wave の最小 (段 3 相談 1 本、段 6 独立 read-only レビュー 1 本)、変異 matrix は実装面差分ゼロなら免除 (DW-S04)、受入全走は免除しない。

**(P3) byte 予算:** L1 残 2 bytes、L1.5 残 3 bytes (layer_bytes.py)。(a)(b) の追記 (約 400 bytes) は mutation.md 内の L1.5 節 (DW-M08 の F71 詳細の括弧書き、DW-M05 の重複語) の削減で等量以上を確保し、安全義務は落とさない (check_docs の DW-S07 注記の趣旨)。収容できなければ D782 の 2 段目 (独立 3 例) を判定し、上限は動かさない。

**不変条件:** 規律 1・2・6。時刻は mtime / commit 日時 / json field のみ (推定なし)。docs-only の変更は正しさ gate・受理集合・受入要件に触れない。self-run は期待 node の観測法であり、KILLED 判定は従来どおり dispatch final の完全一致 (DW-M08) が担う — 観測誤りは final の MISMATCH (fail-closed) に落ちる。

**成果物:** insight `output/insights/2026-09-21/dev-wave-wall-decomp/README.md` (+ verbatim: stage_walls.md/json、prr_check.txt、attempt_gaps_t2804_final.txt、12 wave の mtimes)、`docs/dev-wave/mutation.md` の改訂、spool fragment (worklog 1、decisions 0〜1)、裁定パッケージ (insight §)。

**並列分割方針:** 段 3 相談 1 本 (read-only、分解の妥当性と (a)(b) の攻撃)、段 5 親 docs 編集、段 6 レビュー 1 本 (read-only、一次資料との照合)。
