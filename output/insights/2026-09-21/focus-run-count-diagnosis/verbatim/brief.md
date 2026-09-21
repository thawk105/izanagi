# 段 1 brief — 焦点走 (計算ノード) の本数と wall を契約回数と照合する (診断のみ、2026-09-21)

- 研究前進 (土台): 1 wave 平均 154 分 (所要分解 wave、entry 1774) のうち計算ノード焦点走の分を「契約が要求する本数」と「契約外の増分」に分け、契約を変えずに減らせる分を効果見積り付きで裁定に渡す。8c 無人ループの wave 回転数に直結する土台。最小差分 = 0 (診断のみ、実装面 0 行、docs 改訂なし)。
- scope: 直近 landed 12 wave (land 記録の mtime 順、worklog entry 1766〜1779 と対応) の job dir 一次資料 (`focus*.log` 等の run_tests 非受入走 log、NQSV footer、pid/done mtime、insight README の走行表) から、計算ノード焦点走の本数・投入前/queue/RUN/collection の wall・合否を機械抽出し、DW-S05-C / DW-O26 (+D325) / DW-S06-C / DW-M07 / DW-O20 の契約回数と照合する。裁定パッケージは insight に置き、起票・gate・台帳・docs 改訂・一般化はしない。
- 確定済みユーザー裁定 (引数): 焦点走を login へ移す案は採らない (run_tests.py の login admission / rc=16 の設計どおり)。受理集合・inventory 4 群・変異の完全一致要件 (DW-M08 / F33) は変えない。規律 2 を緩めない。診断だけ。
- 不変条件: 時刻は log の date 行 / NQSV footer / mtime だけから取り推定しない (verbatim へ写す)。契約の文言は現行 docs の逐語で引く。receipt 消失 (wave worktree 撤去済み) により queue の QUE / PRR 内訳は分離しない。
- 成果物: `output/insights/2026-09-21/focus-run-count-diagnosis/README.md` + `verbatim/` (抽出 jsonl、表、時系列、集計、script の sha256)、spool fragment (worklog 1 件)。decisions / failures fragment は新事実があれば。
- 分割方針: 軽量版 + 診断 wave の最小 = 段 3 相談 1 本 (read-only codex、レンズ = 契約解釈の攻撃 + 効果算術の検算)、段 5 なし (実装 0 行、D95 docs-only 例外)、段 6 独立 read-only レビュー 1 本 (一次資料からの再抽出)、変異免除 (DW-S04: 実装面差分ゼロ)、受入全走は免除しない。
- 実測環境: 抽出・集計は login (read-only、job dir の file を読むだけ)。計算ノード job は投げない。受入は `tools/dev_wave_wait.py acceptance` (gen_S)。

## 段 1 実測 (`verbatim/focus_runs_table.md`、`verbatim/aggregate.txt`、`verbatim/timeline.txt`)

- 計算ノード焦点走 27 本 / 12 wave (t2804 2、t2803 7、t2344 4、walldecomp 2、t2814 2、t2810 3、residue 4、t2797 3、t2807 / abstract / story21 / t2817 は 0)。t2817 の `rerun-single*.log` 2 本は login の bounded local 走 (母数外)。依頼文の実測例 t2803 7 本 / t2344 4 本と一致。
- wall 合計 10,602 秒 (176.7 分) = queue (QUE+PRR) 7,861 秒 **74.1 %** + RUN 2,306 秒 21.8 % (pytest 2,269 秒、job 内 overhead 平均 1.4 秒) + collection 345 秒 3.3 % (1 本 10〜15 秒) + 投入前 90 秒 0.8 %。queue は二峰 (< 30 秒 14 本、≥ 300 秒 12 本、375〜1020 秒)。
- 赤の走 8 本 (t2803 focus-3 / 5 / 7、t2344 f1、t2814 focus-1、t2810 focus-impl-1、residue f1 / f3)。うち親の手順起因の赤 = t2803 focus-7 (走行中 commit、F558 型)、t2814 focus-1 (untracked fragment)、residue f1 の 34 件 (契約 module 混入 33 + docs dirty 1、実赤 10 と同居)。
- NQSV footer の Started Request Time はノード上 script 開始 (= compute-visible、wall-decomp focus-2 で 02:16:25 一致) なので queue = QUE + PRR。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 「変更 test file は受入前に単独走で確認する」(DW-O26) は D325 の決定文どおり「既に回す走行のうち 1 本を単独走にする、追加 dispatch は原則 0 本」であり、変更 test file を含む焦点走 1 本で満たされる。別 job の単独走 (t2803 focus-2 / focus-8) は契約が要求する本数の外。
- (P2) main 取込後の焦点走は契約に無い (DW-O20: 取込は受入の post-claim merge)。t2797 focus-3 は commit 5 (fix3、test 変更) の受入前走を merge 後の tip で兼ねたものとして契約内 1 本に数え、t2344 f3 は wave 中に land した DW-O26 改訂 (T-2813、inventory 4 群) の追随として契約内に数える。
- (P3) fix 巡ごとの焦点走は、赤を出した走 (t2803 focus-3 / 5) は次の fix の入力 (規律 3) で必要、緑で後続 fix が続いた走 (t2797 focus-2) だけが事後的な重複。事前には判別できないので「契約外だが削減対象にしない」。
- (P4) 削減の効果は job 1 本あたり queue (平均 291 秒 / 中央値 23 秒、≥ 300 秒が 12/27) + collection 13 秒 + 投入前 2 秒で見積り、同 job 化なら RUN は不変 (単独走の file は既に集合内)。同一 worktree の並行 dispatch は orphan hold で rc=16 (DW-C00) なので、D289 の並行投入は焦点走どうしには使えず、同 job 化だけが queue 1 回分を消す手段。
- (P5) docs-only wave (walldecomp) の `test_check_docs.py` 走は DW-O26 の文言 (production file) の外だが、exact pin を持つ consumer test として契約内相当に数える (別枠で明記)。
- (P6) 契約最小本数 = 統合 tip 1 + 最終 fix tip 1 (fix が test / production を変えた場合) + 受入赤の fix 後 1 (DW-O18 の単独再走) + 契約改訂追随 1 (該当時) で、unit が複数なら unit ごと。観測 27 に対し最小 17〜19 (P5 の扱いで 2 増減)、契約外 8 = 中間 fix 再走 3 + 別 job 単独走 2 + 手順起因赤の再走 2 + held 診断走 1 (t2810、ユーザー明示 env の診断)。

## DW-G05 (成果物影響)

診断のみ。放置時に certified 選択・レポート・台帳の値・受理集合・参照は変わらない。効果は wave の wall (焦点走 14.7 分/wave のうち契約外 ≈ 2〜2.5 分/wave、うち契約を変えずに減らせる分 ≈ 0.3〜0.9 分/wave 実測、混雑時の期待値は job 1 本 ≈ 5 分)。
