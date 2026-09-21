# 段 1 brief — 受入全走を 2 回以上投入した wave の原因分類 (直近 landed 20 wave、診断のみ)

- 研究前進: 土台。dev-wave の受入段が 1 wave あたり平均 43.6 分 (entry 1774: 待ち 23.0 + 走 20.6) を占め、その一部は「再投入」で、原因ごとに防げたかが未分類。本 wave は直近 landed 20 wave の job dir の一次資料 (chain log / attempt log / child log / receipt / land 記録) から再投入の原因を分類し件数と追加 wall を出す。完了判定 = 20 wave × 全投入の分類表と、防げた分類ごとの「守られなかった既存手順」の名指し。最小差分 = 0 行 (診断のみ)。
- scope: 20 wave = worklog entry 1758〜1779 のうち dev-wave 20 本 (rulings 1751/1771 を除外、1760 [T-2501] は job dir 消失のため除外し 1758 を繰り入れ)。一次資料は `/work/1/SFC/tanab/dev-wave-jobs/<wave>/acceptance-*.{chain.log,log,started.txt,finished.txt}`、`acceptance-child-*.log`、`acceptance-receipt-*.json`、land 記録 (`land*.json`/`*.log`) は再投入の原因が land 側にある場合だけ引く。帰属判定 (自分起因/非帰属) は当該 wave の worklog entry / handoff の記録を採り、本 wave は再判定しない。
- scope 外 (依頼どおり): gate・台帳・一般化の追加、受入の受理集合・門番・hold の意味論の変更、rc=23 以外の land 往復の分析 (隣接 wave [551d12] の主題)。
- 確定済みユーザー裁定: 依頼文の 6 分類 (A 自分起因の赤 / B 非帰属の既知間欠赤 hold 未登録 / C F1013 同型 / D post-claim merge の terminal-merge / E 記録 commit 後の tip 変更 rc=23 / F lease 失効)。6 分類に入らない投入は「分類外」として名指しし、6 分類へ無理に寄せない。
- 不変条件: 規律 2 (正しさゲートを緩めない) — 非帰属赤の hold 登録・門番緩和・postcheck 省略は提案しない。規律 7 — 当時の判定を現行コードで覆さない。実装 0 行、repo へ書くのは insight (README + verbatim の派生形) と spool fragment だけ。三軸語走査の生出力を insight に写さない (F1013)。
- (P1) 「投入」の単位 = `dev_wave_wait.py acceptance` の起動 1 回 (attempt log 1 本)。chain 内の自動再試行 (attempt 2) も 1 投入と数える。走なし (postcheck / terminal-merge / preflight / 中止) も投入に数えるが「全走」ではないので、件数は「投入」と「走あり」を分けて書く。
- (P2) 追加 wall = (最終緑の finished − 最初の投入の開始) − (最終緑 1 走の門番待ち + 走 wall)。再投入分の走 (門番待ち + 走 wall) と親の処理間隙に分ける。門番待ちは原因ではないので分類表では走 wall と分けて示す。
- (P3) postcheck (`_behind_count != 0`、tools/dev_wave_wait.py) は post-claim merge の commit 後・child 起動前の検査であり「走行中に main が動いた」(entry 1774 の記述) ではない。実測 4 件の失敗 attempt は 0.8〜2.6 分。1774 の「各 8〜23 分の再走」は再走側 (必要な走) を数えており、無駄は 1〜3 分 + 門番待ちだけ。
- 成果物: `output/insights/2026-09-21/acceptance-resubmit-causes/README.md` (分類表・件数・追加 wall・防げた分類ごとの守られなかった手順・裁定パッケージ) + `verbatim/` (抽出表の派生形、生 log は job dir に残し sha256 で引用)。spool fragment (worklog 1 本)。decisions fragment は無し (設計判断なし)。
- 段構成: 軽量版 + 診断 wave の型: 段 1 → 段 3 相談 1 本 (codex read-only、分類と wall 会計を攻撃) → 段 4 → 段 5 親起草 (docs のみ) → 段 6 read-only review 1 本 → 7 → 8 → 9。段 2 は省く (file:line の実装 plan が無い)。
- 条件表: DW-O08/09/10 不成立 (凍結・oracle・proof chain に触れない)、DW-O13 不成立 (gate 新設なし、依頼が明示除外)。
- 受入・実測環境: login (読み取りのみ)。受入全走は記録 commit を含む最終 tip で land 前に 1 回 (門番付き chain)。
