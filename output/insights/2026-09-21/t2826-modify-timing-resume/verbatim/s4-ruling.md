# 段 4 裁定 (再開版) — [T-2826] (2026-09-21 20:3x JST、計算ノード job の結果を見る前に確定)

入力: 本 wave の段 1 brief `s1-brief.md` (N1 更新・N5 更新・N6〜N9 新規)、前 wave の段 4 裁定 `output/insights/2026-09-21/t2826-shard-plugin-modify-timing/verbatim/s4-ruling.md` (以下「原裁定」)、前 wave の段 3 相談 `.../verbatim/s3-consult-out.md` (流用)。
裁定 inbox の再走査 (20:3x): `dev-wave-jobs/rulings-inbox/` の最新は `2026-09-21-rulings-full29-verdicts.md` (14:46) で、wave 開始 (20:26) 後の更新なし。稼働中の `rulings-all-20260921d/` は窓の抽出途中 (verdicts file なし)。T-2826 に触れる既裁定は第 28 回 項 7 (T-2382 は schema 外の診断走 T-2826 が先) だけで、本 wave の scope を変えない。

## §A 採り直し (変えない)

- **原裁定 §1 (段 3 所見 9 件の裁定、全件 real・採用、反実仮想は (c) 条件付きで scope 内)、§2 (brief の訂正)、§3 (プラン v2)、§4 (読み方の事前登録 R1〜R8 と比較の限定)、§5 (変異・受入)、§6 (scope 外) を、文言を変えずに本 wave の裁定として採る。** 正本は原裁定の file そのもの (repo 内 `output/insights/2026-09-21/t2826-shard-plugin-modify-timing/verbatim/s4-ruling.md`、本 wave の起点 `36fb14a3d` に含まれる)。
- 原裁定 §7 (追補 1 = Codex 不可用による「実装しない」再裁定) は前 wave 固有の事象への裁定であり、本 wave には引き継がない (N6: Codex 可用)。
- 段 3 相談は前 wave の 1 本を流用する (入口「裁定後に別 context が段 4 から再開する型」、変更面の骨格 = probe 3 file・job dir・repo の実装面差分ゼロが同一)。再検査は段 6 review 1 本へ寄せ、そのレンズに「原裁定 §3 / §4 と probe の実装・集計の一致」を含める。

## §B wave 固有の値の差し替え (設計・判定の変更ではない)

| 原裁定・雛形の値 | 本 wave の値 | 根拠 |
|---|---|---|
| 計測 checkout = wave 木 `d99c556df` | wave 木 `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2826-resume` の `36fb14a3d` (job 完了まで main を取り込まない) | 開始 gate で固定 (brief 冒頭) |
| as-of = 14:08:04 JST | 2026-09-21 20:26:33 JST (`startup-gate.log` mtime) | 同上 |
| §4「比較の限定」の「台帳 +434 行」 | T-2817 tip `2afb39768` → `36fb14a3d` で台帳 +15,645 / −13,419 行 (T-2825 refresh `26387b617` を含む)。T-2817 の S2 / S3 値は引き続き参照に留める | brief N1 |
| 子 worktree `author-t2826-probe` (基点 `d99c556df`) | `/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2826r-probe`、branch `author-t2826r-probe`、基点 `36fb14a3d` | 旧 branch は cleanup 済み (N8)。名前の再利用で rescue bundle の ref と紛れるのを避ける |
| 仕様 file の置き場 = 前 job dir | 原裁定・前 brief・段 3 相談は子 worktree 内の `output/insights/2026-09-21/t2826-shard-plugin-modify-timing/verbatim/` (起点に含まれる)。本 wave の brief・裁定は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-resume/` | F819 (必読 path は子自身の worktree を優先) |
| 既定 `OUT_ROOT` = 前 job dir `/job-out` | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-resume/job-out` | job dir |
| `--job-id t2826-s5-author` | `t2826r-s5-author` | 新しい job-id (起動引数) |
| 行番号 | 変更なし (対象 3 file の差分 0 行、N1) | brief N1 |
| 書きかけ probe | 前 job dir `partial-author/` の 3 file (commit `31894443e` の blob と一致) を**参考資料・未検査**として渡す。完成物として扱わせない | 起動引数、N8 |

## §C 変異・受入 (原裁定 §5 のまま)

repo の実装面 (D95 決定 2) の差分はゼロ → 変異 matrix 免除 (DW-S04)。受入全走は免除せず、記録 commit の後に `tools/dev_wave_wait.py acceptance` で 1 走し child-green を land 条件にする。probe の正しさは段 5 author の合成入力の正例・負例と、親の login 生死確認 (`T2826_WORKERS=2`) で確かめる。
