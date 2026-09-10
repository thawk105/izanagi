# [T-1239] 取り残し branch の着地判定を機械検査にする — 逐語と実測

wave: `dev-wave-t1239-branch-landing-check`
base main: `c83b5b2c` (依頼文の `003c0499` から前進済み。wave 中に何度も前進した)

## 何を作ったか

`tools/check_branch_landed.py` — local branch 名または commit-ish を 1 つ受け取り、
D720 条件 1 (未着地であること) を機械判定して JSON を返す。
条件 2 (現況で妥当であること) は機械化せず、出力に未検査であることを明示する。
判定は `landed` / `not-landed` / `indeterminate` の 3 値で、exit code は 0 / 1 / 2。

設計の正本は同 wave の decisions fragment (fold 後に採番)。

## 逐語

| file | 中身 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief |
| `verbatim/s1-measurements.md` | 親の実測 (branch 20 本、3 層の食い違い、worktree 占有) |
| `verbatim/s1-measurements-addendum.md` | 親の追加実測 (receipt 不在が偽の未着地を出す実例) |
| `verbatim/s2-plan.md` | 段 2 プラン |
| `verbatim/s3-lens-sol.md` | 段 3 敵対相談 (正しさ境界) |
| `verbatim/s3-lens-luna.md` | 段 3 敵対相談 (整合と実効性) |
| `verbatim/s4-adjudication.md` | 段 4 裁定と変異事前登録 |
| `verbatim/s5-author.md` | 段 5 実装子の報告 |
| `verbatim/s6-review-a.md` | 段 6 敵対レビュー (偽の landed) |
| `verbatim/s6-review-b.md` | 段 6 敵対レビュー (実データ) |
| `verbatim/s6-parent-dogfood-1.md` | 親の実データ実走 1 回目と診断 5 件 |
| `verbatim/s6-fix-1.md` | fix 第 1 巡 (F1〜F17、M2'/M4'/M8') |
| `verbatim/s6-parent-dogfood-2.md` | 親の実測 2 回目 (branch 8 本の消失を検出) |
| `verbatim/s6-fix-2.md` | fix 第 2 巡 (赤 1 件、commit-ish 対応、M11) |
| `verbatim/s6-parent-dogfood-3.md` | 親の実測 3 回目 (probe の識別力不足) |
| `verbatim/s6-fix-3.md` | fix 第 3 巡 (identity 単位、M12) |

## 実データの判定結果 (fix 第 3 巡後、親が実走)

対象 9 本のうち 8 本は wave 実行中に別経路で削除されたため、
生存 1 本は branch 名で、削除済み 7 件は tip commit の SHA で判定した。

| 対象 | 入力 | verdict | 証明単位 | 所要 |
|---|---|---|---|---|
| `worktree-cleanup-branches-20260825` | branch 名 | `indeterminate` | 2 | 4s |
| `39407cfd` (t1484-backup) | commit-ish | `landed` | 6 | 4s |
| `b3611129` (agent-ab4539) | commit-ish | `landed` | 2 | 1s |
| `15b5c389` (roadmap-workload-hint) | commit-ish | `indeterminate` | 3 | 4s |
| `fe56f5f7` (rulings-0818-floor) | commit-ish | `indeterminate` | 2 | 3s |
| `a6a9f2b7` (rulings-0818-second) | commit-ish | `landed` | 1 | 0s |
| `028a5e2d` (t1458-side) | commit-ish | `landed` | 1 | 1s |
| `500f47a6` (workload-unitB/C) | commit-ish | `indeterminate` | 11 | 14s |

`indeterminate` 4 件はいずれも spool fragment の fold receipt 不在によるもので、
設計どおりの保守側の判定である。`not-landed` は 0 件。

## 実装初版と最終版の差 (親の実走が出した)

| 対象 | 初版 | 最終版 |
|---|---|---|
| `t1458-side` の証明義務 | 18 file → `indeterminate` | 1 file → `landed` |
| `t1484-backup` の証明義務 | merge base 非一意で判定不能 | 6 unit → `landed` |
| 実データ 9 本の `landed` | 1 件 | 4 件 |
| 1 件あたりの所要 | 13〜57 秒 | 0〜14 秒 |

初版は合成テスト 26 件が全緑だった。**実データへ当てるまで、判定器が実質使えないことは
分からなかった。**

## 未 fold fragment の識別 (非決定の観測層)

`unresolved_fragment_candidates` は verdict を動かさないが、回収対象を選ぶ手掛かりを出す。
fragment の frontmatter の `title:` を identity 単位として使う。

| fragment | identity | 本文単位 | 実際 |
|---|---|---|---|
| `2026-08-19-roadmap-workload-hint-1.md` (worklog) | `matched` (archive-710) | 1/5 | 着地済み |
| `2026-08-18-rulings-20260818-floor-measurement-1.md` (worklog) | `matched` (archive-670) | 4/31 | 着地済み |
| `2026-08-25-cleanup-branches-20260825-2.md` (worklog) | `not-matched` | 1/5 | 未着地 |
| `2026-08-19-roadmap-workload-hint-2.md` (decisions) | `not-matched` | 5/6 (docs/decisions.md) | 着地済み |
| `2026-08-25-cleanup-branches-20260825-1.md` (failures) | `not-applicable` | 1/5 | 未着地 |

worklog fragment では identity 単位が決め手になる。
decisions fragment は placeholder 見出しに採番と日付が後から付くため identity が一致せず、
本文単位の集中 (単一 file が 6 分の 5 を覆う) が手掛かりになる。
failures fragment は使える見出しが無く `not-applicable` を返す。

## 検査

- `orchestrator/tests/test_check_branch_landed.py` 54 node 緑 (dispatch、gen_S)。
- `test_plain_runner_coverage.py` + `test_pytest_collection_config.py` 79 node 緑。
- `python3 tools/check_docs.py` rc=0。
- `python3 tools/spool_fold.py --dry-run` `status=planned`。

## erratum — 逐語の可逆最小正規化 (D88)

`verbatim/s2-plan.md` は markdown の強制改行として行末に半角空白 2 個を持つ行が 5 行あり、
`git diff --check` に抵触した。可視文字を変えない可逆最小正規化として、
`sed -i 's/[[:space:]]*$//'` で行末空白だけを除去した。

- 原文 sha256: `be591b6e2e566a4771282f7098ada4347050d60f02d278f772cb1f35edc3ce94` (21,851 bytes)
- 正規化後 sha256: `8c33eedf7c968c174a2f84512155c4d1cd13999fcf0e8344bd2b815973748e28` (21,841 bytes)
- 差分は 5 行 x 2 bytes = 10 bytes の行末空白のみ。復元は該当 5 行 (271 / 274 / 277 / 280 / 283 行目)
  の行末へ半角空白 2 個を戻す。原文は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1239-branch-landing-check/s2-plan.md` に無変更で残る。
