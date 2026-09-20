---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2243-collection-diag
seq: 1
title: [T-2243] 受入 collection の 48 並列を計算ノード 1 job で分解した — bytecode 温なら 48 並列でも 18.4 秒 (Lustre の取り分 4.7 秒)、冷側なら 84.6 秒。受入 pre 61 秒との差 約 43 秒は異条件の差で内訳は未測定 (診断のみ・実装 0 行、branch worktree-dev-wave-t2243-collection-diag)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数の逐語は insight `verbatim/T-2243-origin.md`) の範囲で 1 wave。診断だけで改善実装は 0 行 (D1936 項 35)。
  数値・判定・限界・効果量の見込みはすべて一次資料 `output/insights/2026-09-20/t2243-collection-contention/README.md` (数表 `aggregate.md` / `aggregate.json`、生記録 `raw/`、逐語 `verbatim/`) にあり、ここには再掲しない。
  decisions fragment は無し (新しい設計判断を作らない)。failures fragment も無し。専用 handoff は job dir (repo 外)。
- 起点 local main `f94b61fc8` (EnterWorktree は origin 基準 7baf3f375 で切られたので ff-only で揃えた)。開始 gate rc 0。投入直前に local main `25334c9b7` を ff-only で取り込み (t2766 の conftest pairing 既定 on を含む) その tip で測った。計算ノード bnode008 (単独)、request 13599.nqsv、30 cell、Elapse 744 秒。
- 段構成: 軽量版 (段 1 → 段 3 相談 1 本 → 段 4 → 段 5 author 1 本 → 親の計算ノード実走 → README (親) → 段 6 read-only review 1 本 + 焦点再レビュー → 7 → 8 → 9)。段 2 は省いた。
- **段 3 相談 (gpt-6-astra / medium、11 分) は所見 9 件 (高 3 / 中 6) を出し、全件 real・採用、refuted 0。** 高 3 件: `.git` 除外の node-local 複製は module 直下の `git rev-parse HEAD` (3 file、check=True) で collection に失敗する → `git clone --depth 1` に置換; 3 仮説 (CPU / Lustre metadata / memory 帯域) を一意に数値分解できない → 完了判定を「配置効果・並列度応答・未識別の定量化」へ変更; 全 deselect の xdist 走は受入の上限にならない → 較正に限定。中 6 件のうち 1 件は親の前提実測の一般化 (「同時開始 shard 群は全部 72〜76 秒」) をデータで反証し、撤回した。
- **段 6 レビュー (gpt-6-astra / medium、read-only 1 本) は数表 381 件を照合 (376 一致) し、must-fix 6 / should 5 で NO-GO。** 主因は親の README 初稿が異条件の差 約 43 秒を「受入 regime の追加処理」と帰属し削減余地としたこと (T-2617 §3.3 自身が禁じた同条件でない引き算の成分配分)、初回受入の冷回避を「正・最大 9〜15 秒」と事前登録の条件を満たさずに提示したこと、前提実測の件数・全称の反例 (23 session、66.2 秒、78.8 秒、完了時刻の逆転)。全件 real として README と本 fragment を改め、焦点再レビュー 2 巡目は closed 5 / partial 6 / 新規 3 (must-fix 1 = 本 fragment が再レビュー完了を先取り) で NO-GO、再修正して 3 巡目 (上限) へ提出した。3 巡目は closed 6 / partial 3 / 新規 3 で、残りは親が全件 real として反映し閉じた (README §7)。
- brief 前の前提実測 (login の read-only 観測、受入成果物 23 session) と、その原因の仮説・反例は README §2b にだけ書く (ここに再掲しない)。
- probe (bash 203 行) と集計 (python 305 行) は Codex author の子 branch `author-t2243-probe` (commit `58f95933e`) に実体があり、repo には `.txt` の逐語だけを置いた (land しない)。前提実測の読み取り script と生記録の整形 script は親が repo 外に書いた read-only の整形で、逐語を verbatim に置いた。
- 事故 (自分起因、実害小): (1) 投入前に wave 木の `__pycache__` を消したが、job 開始時刻に wave 木へ 4 pyc が現れ (計算ノード側の dispatcher `_job_run` が書いたと時刻と module 集合から推定、書込みは追跡していない)、R 腕の「冷」判定が機械的には `warm` になった (wave 木に 4 個、有効性未確認)。login で親が tools を走らせた際にも 5 dir の pyc が出来ていた (投入前に削除)。(2) 段 3 所見 3 が「`-k` で hold 検査の経路が変わる」と予告していたのに X 腕の expected_rc=5 を見直さず、較正 2 走が欠測になった。(3) README 初稿の帰属の言い過ぎ (上記)。
- 工数: codex 5 本 (consult 1、author 1、review 1、focus 2)、計算ノード job 1 (12.4 分) + 受入 1 走。

## 次の一手差分

### 完了

- [T-2243] 計算ノード 1 job で腕 R/L/C × N {1,4,12,24,48} の 30 cell を実測し、配置効果 4.7 秒・bytecode 効果 66 秒・未帰属の待ち 4.9 秒を insight に記録した。受入 pre との差 約 43 秒は異条件の差として内訳未測定のまま次の一手へ送った。改善実装は行っていない。
  remaining: none
  base: 461423bbae21a6d0ab963338f92ef56dca117efeaf2310e694948721caf50f90

### 新規

- {{T:acceptance-pre-regime-decomposition}} **P2・新規**: 受入 `pre` 61 秒と、T-2243 が同 checkout の独立 48 process で測った温 collection 18.4 秒との差 (約 43 秒、異条件の差で内訳未測定) を、計算ノード同 job・同 checkout で「独立 48 process → xdist -n 48 (flaky-hold 完全性検査を壊さない全 deselect の形を先に設計) → shard plugin 有り → duration ledger 有り」と段階的に載せて分解する診断。conftest / gate の改変で代用しない。削減可能量は分解が閉じるまで書かない。効果量の見込みだけを記録し実装しない (D1936 項 35)。一次資料 `output/insights/2026-09-20/t2243-collection-contention/README.md` §5 (d)。
- {{T:acceptance-first-run-cold-bytecode}} **P3・新規**: fresh worktree の初回受入で shard の collection が冷 (pyc なし) になりうる件 (T-2243 §2b: login 側 `_collect_login_universe` が並行して pyc を書き、その完了より前に開始した shard は `pre` が約 8〜18 秒高いという仮説、反例 1 件を含む)。観測された関連は初回受入の shard に限られるので、順序の入れ替え (login collection の完了を shard 投入前に置く) で増える待ち時間と、D711 gate 3 の「並行に独立観測」の意味を変えないかを先に判定してから実装可否を決める。実装は本項の裁定後。
