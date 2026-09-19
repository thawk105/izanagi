# [paper-story 2026-09-19 版] docs/paper-story/ の次版を書く (docs-only)
- 目的: 前版 2026-09-17.md 以後に一次資料で確定した事実だけを反映した 2026-09-19 版を README の版規則に従って書く
- 状態: 作業中
- 最終更新: 2026-09-19 22:05 JST
- 基準コミット: a99425b66 (local main、worktree `dev-wave-paper-story-2026-09-19`、branch `worktree-dev-wave-paper-story-2026-09-19`、clean)

## 段 1 brief (2026-09-19 22:05 JST)

- **研究前進:** 論文ストーリーの凍結版を 2026-09-19 の正典 (local main `a99425b66`、worklog entry 1685 まで) へ揃える。
  進む論文の図表・主張: §4 に fig8 (B-10 右 tail 記述図) と fig9 (A-1 attempt-0001 記述図) を登録、§8 の A-1 を
  「attempt-0001 完走・descriptive・非認証 lane」へ、§6 / §8 の状態語を一次資料へ再照合。完了判定 = `docs/paper-story/2026-09-19.md`
  着地 + README の版履歴・訂正・stale 注記の更新 + `check_docs.py` 緑 + 段 6 read-only review 1 本の must-fix 処理 + land。
- **scope:** docs-only。新 file `docs/paper-story/2026-09-19.md`、`docs/paper-story/README.md` の 3 節 (版履歴・訂正一覧・stale 注記)、
  insight README、spool worklog fragment。**scope 外:** 新しい主張の追加、図の再生成、results 稿・claim-evidence 稿・figures/ の改稿、実装面。
- **確定済み裁定:** README 版規則 (append-only・前版不変・冒頭に前版の訂正・全項目再導出)、D1858 (stale 注記は版の要求ではない)、
  D2148 項 11 (一次資料再抽出の docs-only は段 6 read-only review 1 本)、D2120 項 2/3/4/7/14/15/16、D2148 項 2/3/5/13、D2150 項 1/2/4、
  D2114、D2154、D2155、規律 7。
- **不変条件:** 「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」と書かない。数値・日付・判定は一次資料 (権威 bytes・insight・D 本文・
  results 稿) から取り前版を出所にしない。稼働中で未着地の wave の内容は書かない。前版と全凍結物の bytes は不変。
- **成果物の形:** 2026-09-19.md は前版と同じ §0〜§10 構成で全項目再導出。§10 は「段 2・3 は省略 (軽量版)、段 6 は read-only review 1 本」の
  記録にする。README は「最新 = 2026-09-19.md」、訂正一覧を新版のものへ、stale 注記 3 件 (Silo スコープ解除・fig8・A-1 attempt-0001) を
  本文へ移管して 0 件にする。
- **分割方針 (軽量版):** 段 2・3 省略、段 5 = 親の docs 編集 (実装面ゼロ)、段 6 = Codex read-only review 1 本 (2 レンズ = 一次資料照合と
  主張の強さ を 1 本で担う)、変異 matrix 免除、受入は記録 commit 後の tip で 1 走。
- **(P1) 反映集合の範囲 (親の provisional 裁定・攻撃対象):** 引数の 8 事実は必須反映集合。それ以外で §6 / §8 の状態語を変える着地事実
  (B-4 spec 凍結 D2138 と job body D2145 と PerfConfig D2146、T-2731 の F1016 修正 D2108、K2 2 巡目 T-2746 と D2148 項 2、pin 前進の承認
  D2150 項 1 (未実施、pin 511c9538 不変)、Silo スコープ解除 D2114、軸 1 の再開 D2095 と限定閉鎖 D2120 項 14 / D2150 項 4、層3 v3 の
  初適用 D2143、TicToc baseline D2127、mocc 機械実証 設計 D2134 / wave 1 D2147、A-2 nodes=5 裁定 D2148 項 5 (policy は nodes=1 のまま
  未実装)、T-2489 probe、T-1878 C14a、T-2321 B-10 記録値訂正、T-2758 候補表) は**状態語の訂正として反映し、新しい主張は足さない**。
- **(P2) 前版の執筆時点の誤り:** 導出中に見つかれば冒頭の訂正一覧へ。現時点 0 件 (T-2590 の実装 commit `ad83b108b` は前版起点 `fa24e6ea8`
  の祖先でないことを実測 = 前版の「着地済み正典は無い」は当時真)。
- **実測環境:** login node の read-only 検査 (`check_docs.py`、三軸語走査)、受入は計算ノード dispatch。新規計測ゼロ。

## 完了した中間成果

- クラス 3 起動手順、DW-C00/C01/STOP/S01/G01〜G05/O20、skill-self-improvement 読了。worktree 作成・submodule 初期化・開始 gate rc=0。
- 前版 2026-09-17.md 全 10 節 (2819 行) を読了。entry 1582〜1685 の見出しと主要 entry 本文、D2104〜D2155 の見出し、D2120/D2148/D2150/D2154/
  D2155 本文、A-1 results 稿全文、fig8/fig9 節、mocc 3 件の insight 冒頭を読了。引用予定 path 26 件の実在確認済み。

## 未完の作業と次の一手

- 2026-09-19.md を書く: cp 前版 → 冒頭・§0・§2(g)・§9・§10 を全面差替え、他節は箇所ごとに再導出 (job dir の python 置換 script)。
- README 3 節を更新。check_docs.py。段 6 review 1 本 (codex)。段 7 (insight + spool fragment + commit)。段 8。段 9 land。

## 落とし穴・気づき

- 隔離 session の Bash は単文・裸の cd 禁止・repo 外は Write tool・複数 git を 1 行に並べると guard 拒否。

## dev-wave 改善候補

- (なし、随時追記)
