# 段 1 brief — dev-wave 1 本が login で回す検査の回数と wall (直近 landed 12 wave、診断のみ)

起点 local main `5efd69367` (開始 gate rc 0、`startup-gate.log` 2026-09-21 07:4x JST)。branch `worktree-diag-login-check-wall`。job dir `J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-login-check-wall/`。台帳 ID 未起票 (依頼文に ID なし、主題 slug)。

## 研究前進 (土台)
dev-wave が論文の実験・図表・記録を運ぶ唯一の経路で、1 wave 平均 154 分 (entry 1776、insight `dev-wave-wall-decomp`) が研究の回転を律速する。entry 1776 は login 走を「union 7.2 分 / wave」と 1 成分で置いた。本 wave はその内訳 — 5 種の login 検査 (check_docs / 三軸語 CLI / 全史 provenance 監査 / fold dry-run / find-fold-owned) の回数と wall — を wave ごとに再構成し、「契約で必須の回数」と「習慣で増えた回数」を分け、cold 監査の回数と原因を数え、効果見積り付きの裁定パッケージを出す。完了判定 = insight に 12 wave の表 (検査種別 × 回数 × wall × 契約/習慣) + cold 表 + 裁定パッケージが載り、数値の出所が verbatim で追える。

## scope と確定済みユーザー裁定 (依頼文 = 逐語は `verbatim/origin.md`)
- 対象: 直近 landed 12 wave (`land*.json` / `land-*.stdout` / `land*.log` の status=landed、mtime 順) = t2797 / branch-residue / t2817 / t2810 / t2814 / wall-decomp / paper-story-20260921 / paper-abstract / t2344 / t2803 / t2804 / t2243 (着地 09-20 23:13 〜 09-21 05:26 JST)。fig9b は未 land、fig13 は 13 番目で外す。
- 診断のみ・実装 0 行 (repo)。検査の受理集合・判定・5 分上限 (D690) は変えない。規律 2 不変。gate・検査・台帳・一般化の追加は scope 外 (裁定パッケージへ)。
- 全史監査の wall は T-2803 (entry 1769) の warm 22 秒 / cold 58 秒を前提値とし、実測値があればその出所付きで併記する。
- 一次資料 = job dir (log の mtime、HANDOFF.md の時刻) + 全史監査の受領証 store (`<common git dir>/provenance-audit-receipts/`、D2045/D2192) + commit 日時。session transcript は 12 wave とも撤去済みで使えない (実測)。
- 並走 wave との境界: `dev-wave-provenance-cold-diag` (同時刻起動) が「実 land 連鎖での監査 warm/cold」を扱う。本 wave は **wave 内で親と受入 tool が login で回した走**を主対象にし、land の監査は回数 (1/land) と warm/cold の結果だけ書き、land 内部の分類・局所修正はそちらへ譲る。

## 段 1 前提実測 (親 script = 仮説。確定は段 5 の Codex author probe で再導出する — T-317 未裁定・重い側、memory `probe-must-not-enter-repo-without-codex-author`)
1. 受領証 store 495 件 / 19 partition (partition = checker sha + config + 継承 env (GIT_*/LC_*/LANG) + schema)。12 wave へ帰属 58 件 = login-env 46 / land-env 12。login cold 11 = T-2803 着地 (00:12) 前の 10 (attributes 指紋 5、checker sha 変更 5) + t2797 の 1 (wave 木の checker が旧版のまま → 旧 partition)。land cold 3 (T-2803 前)、後は 9/9 warm (前 wave の land 受領証を継承)。現行 checker の login partition は 35 件で剪定なし、旧 partition は 64 件で剪定済み (T-2803 前 5 wave の件数は下界)。
2. 受領証は同 tip の再走で上書きされ (path = `<tip>.json`)、`--range` は受領証を残さない (`/run/user/<uid>/izanagi-admission/peak-provenance-range.peak` mtime 02:56 = 親が range 監査も使う)。→ 親の走は受入 tool の claim 前監査に上書きされ、受領証だけでは下界。
3. 受入 tool (`dev_wave_wait.py acceptance`) は attempt ごとに claim 前 1 + post-claim merge 後 1 の全史監査を内蔵 (`preclaim-history-provenance` / `merge-history-provenance`、親 env 継承 = 同 partition)。t2817 (4 attempt) の login 受領証 7 は全部これ。started.txt → 受領証 mtime = 13〜19 秒 (warm)。
4. job dir log (親が残した分): branch-residue = 全史 5 / `--message-file` 10 / check_docs 5 / 三軸語 2 / dry-run 0 log、11 commit。t2814 = check_docs 5 / 全史 4 / dry-run 3 / 三軸語 1 (check_docs → dry-run → 全史を 1 call に束ね、fold 4 秒・warm 監査 12 秒)。t2810 = check_docs 5 / dry-run 5 / 三軸語 1 / range 1。wall-decomp = 全史 3 / dry-run 1 / 三軸語 1 (check_docs 「4 commit」は記述のみ)。t2804 = 全史 3 (75 / 63 / 46 秒、cold) / 三軸語 1。t2803 = 全史 3 (112 / 47 / 54 秒、cold) / 三軸語 1 / dry-run 2。t2243 = 全史 1 (50 秒)。t2344 = 全史 1 / check_docs 2 / 三軸語 1。paper-abstract = 全史 1。t2817 / paper-story = log なし (handoff の記述のみ)。find-fold-owned は 12 wave で 0 (script は t2724 / t2796 の job dir にだけ実在)。
5. 検査 1 回ごとに親の手番が挟まる: branch-residue の記録 commit 前後で check_docs → 三軸語 → preflight の log 間隔 95 / 83 秒、t2814 は 1 call に束ねて間隔 4〜12 秒。並走負荷下の warm 監査は log 間隔で 36〜47 秒 (受入 tool 内は 13〜19 秒、T-2803 実測 21.9 秒)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- (P1) 契約必須回数の定義: 全史監査 = 親の commit ごと 1 (DW-O17・`docs/ai-provenance.md` 通常列・PR-A02) + tool 内蔵 (受入 attempt ごと claim 前 1 + merge 後 1、land 1 = D254)。check_docs = docs を触る commit ごと 1 (CLAUDE.md 作業の進め方 6(c)、spool README「fragment を書いたら」) + land 内蔵 1。三軸語 = wave 1 回 (DW-S07「凍結前」; 凍結 commit が複数なら各 1 を許容)。fold dry-run = land 前 1 (spool README、rc=0 まで) + fragment commit ごと 1 (同「dry-run で確かめる」)。find-fold-owned = 0 (docs に無し、memory 習慣)。これを超える分を「習慣で増えた回数」とする。
- (P2) 効果の主成分は検査 wall (warm 22 秒 × 5〜8 = 2〜3 分 / wave) より、検査呼び出しごとの親手番 (80〜95 秒 × 10〜15 回 = 15〜20 分 / wave、entry 1776 の未分類残差 28% の一部) — 減らせるのは回数でなく**呼び出し回数 (束ね)** が主。
- (P3) cold の原因は「checker sha 変更 (partition)」「attributes 指紋 (T-2803 前)」「partition (land env / LC_CTYPE=C.UTF-8 の別 shell)」の 3 分類で尽きる。剪定 (64 件) による偽 cold は現行 partition では 0。
- (P4) 親の走のうち受領証で見えない分 (上書き・range) は handoff の記述で補い、「観測下界」と「記述」を別列にする。推定で埋めない。

## 不変条件・成果物・段構成
- 実装面 0 行 (repo)。probe (受領証 replay / job dir 台帳 / 手番 gap) は Codex `role=author` が worktree 内 `probe/` (untracked) に書き、親が J へ退避して login で実走 (read-only、数秒〜数十秒)。親 script 6 本 (`J/*.py`) は仮説で、insight には author probe の出力だけを確定値として載せ、親 script は sha256 と「仮説」の印で verbatim に残す。
- 成果物: `output/insights/2026-09-21/login-check-count-wall/README.md` + `verbatim/` (受領証の写し (tip / partition / mtime / bindings 差分)、job dir log の mtime 表、handoff 逐語、probe の出力、scripts.sha256) + worklog fragment (`docs/spool/worklog/`)。decisions fragment は「実装しない」なら不要 (裁定パッケージは insight)。
- 段構成: 軽量版 + 診断 wave の最小 = 段 3 相談 1 本 (read-only codex、P1〜P4 を攻撃) → 段 4 → 段 5 author 1 本 (probe) + 親の実走 + 親の insight 起草 → 段 6 review 1 本 (read-only) + 焦点再レビュー ≤ 3 巡 → 段 7 → 段 8 → 段 9。変異 matrix = 実装面差分ゼロで免除 (DW-S04)。受入全走は免除しない (計算ノード、門番付き chain、先例 t2797 `run-acceptance-gated.sh`)。焦点走 = docs-only なので `test_check_docs.py` (insight README は `output/insights/**/*.md` として check_docs の走査対象)。
- DW-O08/O09/O10: 凍結成果物に触れない (新規 insight dir のみ)。DW-O13: gate 新設なし。DW-O11: 削除なし。
- 受入・実測環境: 受入 = Pegasus 計算ノード dispatch (所在 = worklog 直近、機体 = runbook)。probe 実走 = login (read-only)。login は現在 13 job 並走で高負荷 — 本 wave は wall を新たに計測しない (log の mtime と前提値で書く)。
- 既存被覆 (純増だけ書く): D2045 / D2192 (受領証と warm 条件)、D254 / DW-O25 (land 監査 480 秒)、D690 (5 分)、entry 1776 (login 成分 7.2 分)、T-2803 §11 (候補列挙 memo 化)、F975 (land 監査の timeout)。純増 = 検査種別ごとの回数・契約/習慣の分離・受入 tool 内蔵走の可視化・同 tip 上書きによる観測限界・検査ごとの親手番。
