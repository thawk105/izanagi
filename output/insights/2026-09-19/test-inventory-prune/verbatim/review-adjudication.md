# 段 6 レビュー裁定と fix 対応表 (親、2026-09-19 23:58 JST)

レビュー A (正しさ境界) と B (過剰・削除) はいずれも NO-GO だが、削除実装 (6 node) と登録変異の検出保存は両方が妥当と判定した。阻害点は成果物 (README) の正確さだけ。fix は docs-only (README・mutation-summary) で親が直接編集した (実装面の変更なし)。

| # | 出所 | 所見 | 裁定 | 対応 | 状態 |
|---|---|---|---|---|---|
| 1 | A-1 must-fix | 変異の実行元が裁定 (独立 clone、DW-M07) と違う登録 worktree | real (手順記録)。再走は不採用: harness が固定 HEAD・clean・flock を束縛し `repo_head` を記録しており観測事実は同じ。独立 clone は submodule 供給 URL が非 local で初期化 tool に拒否された (実測) | README §4 と mutation-summary に erratum を明記、§9 に限界として追加。段 8 候補 (DW-M07 の文言と DW-M05 経路の関係) | closed (erratum) |
| 2 | A-2 / B-1 must-fix | 「確認済み (D) 16 関数」に実挙動を含む代表が混入 | real | 冒頭・§2・§5 を「純粋な定数 pin 7 / pin と実挙動の併存 9 / 混在 2 file / D でない 23」に分離し、合算しない旨を明記 | closed |
| 3 | A-3 must-fix | 削除前後の総行数の基底が違う (592,832 は着手時) | real | blob 改行数を親が独立集計: a99425b66 592,832 / 657e1e5a7 592,860 / 0917fc400 592,845。README を 592,860 → 592,845 に訂正、着手時値は時点付きで保持 | closed (再計算済み) |
| 4 | A-4 should | 所要と外側 wall の混同、job 数 4 → 5 | real | 「実行期間 (queue 待ち込み)」に改め、job 5 本 (collection + baseline + 変異 3)、runner 報告時間を併記 | closed |
| 5 | A-5 nit | coverage の増減方向が逆 | real | 「割合はごく僅かに下がるが閾値には遠い」に訂正 | closed |
| 6 | A-6/7/8、B-5/6/7 | 指定外変更・検出集合喪失・母数混同・削除漏れ・要求外機構 | refuted (両レビューとも) | 変更なし | closed |
| 7 | B-2 should | 定数 pin の pin 先が説明名 | real | 7 件に関数名と正確な定数名・literal を記した | closed |
| 8 | B-3 should | suite 全体への結論の拡大 | real | 「今回抽出して意味確認した候補の範囲で」に限定し、取りこぼし型の存在を明記 | closed |
| 9 | B-4 should | DW-G05 の裁定文言が README に無い | real | 冒頭に成果物影響 1 行 (裁定 #13) を追加 | closed |

派生値の再計算 (DW-O16): 台帳合計 17,958.848 s / 削除 33.005 s / 差引 17,925.843 s (両レビューが独立検算)、行数は上記 3 commit を blob から再集計、S_post = S_pre − Del は `check-pre-post.py` で全変異 exact。

## 焦点再レビュー 1 巡目 (focus-1、00:01 JST) の判定と 2 巡目 fix

focus-1: 対応表 9 行のうち 8 closed、#2 partial (README の (D) 説明が「9 関数は実挙動併存」「2 file は pin だけの test と併存」と一括しており、plan の代表確認・test 本文と一致しない)。新規所見 1 (must-fix) = 関数単位で「資料・派生値 pin」「pin と挙動検査の併存」「挙動検査」を分けよ。

親の 2 巡目 fix (docs-only、README §5 と冒頭・§2・§9): 純粋な定数 pin 7 / 資料・派生値 pin 5 (`paper_story_a1_headline:1232` は固定 git 区間の non-touch 検査、`paper_story_a1_paired:903`、`skip_classification:315`、`t1434:409`、`t189:132`) / pin と挙動検査の併存 3 (`b10_backoff_grid_submit:137`、`floor_pair_job_contract:91`、`t2187:4130`) / (D) でない 26 file (`plot_a1_sized_paired`、`plot_b10_static_tail_formal`、`spool_fold` を 23 から移した)。合計 41 file。親が各関数の本文を読んで確認 (`paper_story_a1_headline:1232` は merge-base の祖先判定と diff の exit-code だけで production 関数を呼ばない)。

| # | 所見 | 状態 |
|---|---|---|
| focus-1 新規 1 | (D) の関数単位分類 | closed (2 巡目 fix、focus-2 で再判定) |
