# 段 4 裁定 — 救出材料 7 file の要否

段 3 相当の独立レビュー 1 本 (`consult-sol.md`、read-only codex、gpt-5.6-sol、xhigh) を受けた裁定。
レビューは 7 件を親の処遇表を見る前に独立導出し、**7/7 で親と一致**した。
一致したので処遇は動かさない。**採用した補正は 3 件、却下は 0 件。**

## 所見の real / refuted と採否

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A | 項目 1 は「実時間を含む生の受入集合」は広げる。親の (P3) の書き方は不正確 | **real** | 採用 | scope 内 (記録の訂正) |
| B | 撤去は `root_snapshot.complete=false` のままでは損失ゼロ未証明。closure の complete と root inventory の complete は別契約 | **real** | 採用 | scope 内 (撤去の前提条件) |
| C | 項目 7 は D1298 が無くても着地不可。高速路の誤判定は**偽緑**を出しうる | **real** | 採用 | scope 内 (破棄理由の補強) |
| D | 項目 1 と同じ patch は既に commit `aaffa71a6` として存在し、二重実装を避けるべき | **real** | 採用 | scope 内 (実装方針の変更) |
| E | 5 worktree の untracked / ignored / staged / stash を棚卸ししていない | **real** | 採用 | scope 内 (実施済み) |
| F | 破棄しても D1179 の明記義務は残る。T-2032 を完了にしてはならない | **real** | 採用 | scope 内 (次の一手へ送る) |
| G | flaky hold の「直接証拠は無い」という自認は、それ単独では破棄根拠として不十分 | **real** | 採用 | scope 内 (破棄根拠の差し替え) |

## 確定した処遇 (7 件)

| # | file | 処遇 | 確定根拠 |
|---|---|---|---|
| 1 | `orchestrator/tests/test_growth_test_holds_contract.py` | **着地** | 別 session root の受入全走 2 走が、18382 件中この 1 node だけの赤だった (一次 log で検証済み) |
| 2 | `orchestrator/tests/flaky_test_holds.py` | 破棄 | root fix `42c62e4dd` の後、`5254ac6ed` で hold を外して受入母集団へ戻し、baseline rc=0 と m03 の両 node KILLED を記録済み |
| 3 | `orchestrator/tests/test_flaky_test_holds_contract.py` | 破棄 | 項目 2 の row・digest・逐語 field の鏡。row を捨てれば独立した検出力がない |
| 4 | `tools/check_wave_startup.py` | 破棄 | 「段 5 専用」を否定被引用文へ入れており D1179 の決定より意味が後退する |
| 5 | `orchestrator/tests/test_check_wave_startup.py` | 破棄 | docstring / help / NOTE に列挙文字列が在ることだけを固定する 73 行。midflight の 6 検査と除外集合は既存 test が既に固定済み |
| 6 | `orchestrator/tests/test_codex_worker_launch.py` | 着地済み (no-op) | worktree の blob `95c2f0080` が main の blob と同一 |
| 7 | `orchestrator/tests/test_s8c_preregistration_invariant.py` | 破棄 | main が `ce99cc7d4` で exact 5 node を growth hold 済み。D1298 が現 regime の単一 loadgroup 短縮を退ける。加えて高速路の誤判定は偽緑を出し絶対規律 2 に反する |

**着地させる 1 件の一行:** これが無いと、受入全走が偽の timeout 赤を出し続け、
その走が唯一の根拠として与えるはずの tested_tip の緑 — land の前提そのもの — が捨てられる。

## 実装方針の変更 (所見 D)

**再実装しない。既存 commit `aaffa71a6` を cherry-pick で回収する。** D720 の 2 条件を両方満たす。

1. **未着地:** `git cherry` で main に無いことを確認。`git merge-base --is-ancestor aaffa71a6 main` は偽。
   到達可能なのは `worktree-dev-wave-t2027-t2043-external-input` だけ。
2. **現況で妥当:** 主張を 1 つずつ検証した。
   - 「12 caller のうちこの 1 本だけが実 conftest を読む」— main で caller 数 12 を実測、一致。
   - 「両方の受入全走で予算が切れた」— 一次 log 2 本で検証済み。
   - 「assert は経過時間を見ていない」— 現物を読んで確認。
   - AI-Agent trailer が 1 block で 2 行 (codex author + claude manager)。provenance は完全。

合成の余地はゼロだった。cherry-pick 後の blob `5fdd36cac` は `aaffa71a6` の blob と byte 同一で、
main の blob は commit の親 blob `d60083028` と同一である。よって**合成監査の対象となる合成が存在しない**。
`python3 tools/check_ai_provenance.py --range main..HEAD` は「1 件、違反なし」。

段 5 の Codex 実装子は起動しない。実装面の author は `aaffa71a6` の trailer が記録する
codex `role=author` であり、その成果物を逐語で回収したからである。
親は実装面を 1 byte も書いていない。

## commit message の erratum (所見 A)

回収する commit message は「its accept and reject sets are unchanged」と書く。
**厳密には正しくない。** 変わらないのは assert が固定する機能的な正しさ集合であり、
実時間を含む生の実行受入集合は 10 秒から 120 秒へ広がる。

message は原著者の記録なので**書き換えず逐語で回収し**、訂正は台帳側へ erratum として置く
(D720 の (a) 群)。絶対規律 2 には触れない — 4 つの assert は 1 つも飛ばず、
120 秒を超える hang は引き続き赤である。

## 変異事前登録 (DW-M01)

| id | 変異 | 期待 | 単一理由性の確認 |
|---|---|---|---|
| `M1-ANTI-HANG-BUDGET-NOT-WIRED` | `], timeout=120.0)` -> `], timeout=0.001)` | KILLED = {`test_regular_pytest_path_keeps_single_hold_skip`} | 前後に同じ入力を拒否する層が無い。`_run_subprocess` は `TimeoutExpired` を捕捉せず伝播させる。repo に pytest 全体へ掛かる timeout plugin の設定は無い。よって赤理由は 1 つに絞れる |

anchor は対象 file 内で 1 箇所 (`grep -c` で確認)。
DW-M08 の「新旧両走」は**適用外**である — 本 wave はテストを新設も改名もせず、
既存 test の基盤上界を変えるだけで、検出力を示すべき新テストが存在しない。

## 段 6 の縮約

DW-C00 の軽量版に従い、段 6 の敵対レビュー子は起動しない。理由は次の 3 つ。

- 実装面の差分は 4 行で、その 4 行に対する敵対レビューは段 3 相当の consult が
  問い 2 で既に実施済みである (固定される 4 性質の列挙、規律 2 への抵触判定、
  repo 内の代替機構 3 種の検討まで到達している)。
- 合成が恒等なので、合成に起因する新しい攻撃面が無い。
- fix 子は fix すべき所見が無い。採用した補正 A・C・G は台帳の文面へ、B・E は撤去手順へ、
  D は実装方針へ入り、いずれもコード変更を要求しない。F は次の一手へ送る。

変異 matrix と受入全走は縮約しない。

## 撤去の前提条件 (所見 B・E)

次を**すべて**満たすまで撤去しない。

1. `check_branch_rescue.py` を 4 branch + 4 worktree の 1 操作で再走し、
   rc=0、`root_snapshot.complete=true`、`deletion_loss_closure` が complete かつ count 0。
2. 5 worktree に untracked / staged-only の未着地 bytes が無いこと。**実施済み** —
   untracked はゼロ、ignored は `__pycache__` と `output/pegasus-dispatch/` だけ。
   stash 2 本はどちらも対象外 branch (`t1563-acceptance-nproc`、`t816-step4-impl`) のもので、
   worktree 撤去でも失われない。
3. `check_worktree_occupancy.py` が対象ごとに rc=0。
4. 変異 harness が主 checkout を観測していないこと。**実施済み** —
   稼働中 2 本の `--repo` は `/proc/<pid>/cwd` で t2033 と t2061 の worktree と確認。

`fix-dev-wave-t2027-timeout` は撤去しない。未着地の S8B commit 2 本を持ち、
稼働 branch `worktree-dev-wave-t2027-t2043-external-input` からも到達可能である。

## ユーザーへ返す設計択一

無し。7 件とも判定基準が一意に決めた。
D1179 の未履行分だけは新規 T として次の一手へ送る (所見 F)。
