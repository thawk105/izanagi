# 受入前 merge 段の全史 provenance 監査を merge commit の作成後へ移した — 取り込んだ main の commit と merge 自身を初めて選択集合に入れ、赤でも merge commit を保持する契約に定めた

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- 起票: [T-2670] (P1、D2044 項 5 でユーザー裁定済み → 実装手番)
- wave branch: `dev-wave-t2670-merge-provenance-position`
- 基準 commit: `38353207f719acb0871cfe3d9bbe3a02490282bb` (local main = origin/main、wave 開始時、fresh worktree)
- 実装 commit: `21e0bdc6b478cc3ced1d2b929baf558326316ec9` (Codex `role=author` 1 単位、2 file、+170/−68)。
  fix commit: `7562001c45722b4b8e9480264198ae913dc190a0` (Codex fix 1 巡、test 1 行: 受入 1 回目の赤の是正、下記)
- 設計判断: 本 wave の decisions fragment (slug `merge-history-provenance-after-commit`)。失敗の型: failures fragment
  (slug `merge-audit-before-commit-saw-nothing-new`、F206 / F365 へ supersede 追記)
- job dir (prompt・log・patch・probe script・変異 spec/台帳の原本):
  `/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2670-merge-provenance-position/`
  (codex 子の起動 log と artifact は `/home/SFC/tanab/.claude/jobs/844e52e7/tmp/t2670/` から同 dir へ写した)

## 何をしたか

`tools/dev_wave_wait.py acceptance` の受入前 merge 段は、`git merge --no-ff --no-commit main` の直後・`git commit` の前に
全史 provenance 監査 (stage `merge-history-provenance`、`check_ai_provenance.py` の既定 authoritative 監査) を走らせていた。
`--no-commit` 中の HEAD は wave tip のままなので、checker の選択集合 `{policy} ∪ rev-list(policy..HEAD)` は claim 前の監査と
同一で、取り込んだ main の commit と merge commit 自身は入らない。F365 の恒久対応が「その merge 自身が新しく作る違反を
捕まえる」と書いた監査は、導入以来それを一度も見ていなかった (D908 の前提も不成立)。

`tools/dev_wave_wait.py`: 監査呼び出しを `git commit` 後、HEAD の pin 取得 (`commit-rev-parse`) の直後・commit message の
事後検査の前へ移した。argv・stage 名・診断理由・失敗出力の捕捉は不変。`merge_pending` (未完了 merge の abort 権限) の窓は
merge 開始〜commit 成功のまま。commit 後の監査赤では `git merge --abort` を呼ばず merge commit を保持し、所有する lease
(ACQUIRED / UNKNOWN) を解放し、受入 command を投入せず、receipt を書かず、理由本文を返す (rc=70)。cleanup の実処理は変えない。

`orchestrator/tests/test_dev_wave_wait.py`: 段順序の期待列を新位置へ更新 (主張は維持)。監査赤で abort を期待していた 2 本
(`test_nonzero_stage_blocks_submission_and_releases[merge-history-provenance]`、
`test_merge_history_provenance_failure_blocks_submission_releases_and_returns_reason`) は commit 済み・abort 不在・release 1 回へ。
実 git の負例 `test_real_git_main_only_history_violation_blocks_acceptance_after_commit` を追加: main にだけ存在する違反 commit を
temp repo の偽 checker (`git merge-base --is-ancestor <sha> HEAD`) が赤にし、受入 command 0 回・lease の監査時存在と終了時不在
(checker の trace 3 行)・HEAD が開始時 tip と main tip を親に持つ 2 親 merge commit・違反 SHA の到達性・MERGE_HEAD 不在・
tracked clean・receipt/log 不在を主張する (subprocess `timeout=120`)。

## 受理集合の変化 (段 6 レビュー A4、親の実 checker probe で実測)

probe (`verbatim/s6-probe-real-checker-positions.json`、script は job dir の `probe_real_checker_positions.py`) は temp repo に
実 `check_ai_provenance.py`・実 `tools/known_violations/`・site を OTHER に固定した site_policy を置き、旧位置 (`--no-commit` 中)
と新位置 (commit 後) で同じ checker を走らせた。

| 場面 | 旧位置 | 新位置 |
|---|---|---|
| main にだけ trailer 無し commit A | rc=0「1 件、違反なし」(wave tip の 1 commit しか見ない) | rc=1「3 件中 1 違反」A を名指し |
| さらに main が A の既知違反 entry を追加 | rc=2「実行不能: index-only member does not match HEAD」(F206 再発 2026-09-01 の型) | rc=0「4 件、新規違反なし」(main の full 監査と同じ判定) |

(1) は縮小 (main-only 違反を受入投入前に拒否)、(2) は旧位置の偶発的拒否の解消 (台帳規則と append-only 履歴検査は新位置で
そのまま適用。従来は親が `--ff-only` で main を揃えてから再投入するしかなかった)。checker と台帳の規則は変えていない。

## 段 3 / 段 6 の所見と裁定

- 段 3 consult A (裁定・契約整合) / B (実効性): real 所見は docs・裁定文の是正 (D518 の誤引用 → D689/D731/D732、選択集合に
  policy 自身を含める表記、監査赤後の復旧手順 3 行、fake の順序 pin と意味的 kill の分離、M4 の追加、M5 は診断 pin、
  subprocess の timeout)。設計 (P1 巻き戻さない / P2 commit-rev-parse 直後) は両レンズとも支持。`verbatim/s4-ruling.md`。
- 段 6 レビュー A (NO-GO → A4 を意図した帰結として記録、code 変更 0) / B (GO)。`verbatim/s6-ruling.md`。
- 巻き戻し (`git reset --merge <premerge>`) を採らない理由: 捨てた merge commit が branch / HEAD reflog に残り、
  `tools/dev_wave_cleanup.py` の reflog 到達性検査 (D1233 の喪失閉包) が自己撤去を拒む。reflog を消す手は掃除側の防壁の迂回。
  保持される終端状態は、変更前でも受入全走の後に land の監査で止まったときと同じ。

## 実走

- 焦点走 f1 (login 自動判定 → 計算ノード 4004.nqsv、7 file: test_dev_wave_wait / test_dev_wave_wait_compute /
  test_run_tests_shards / test_dev_wave_land / test_resume_gate_acceptance_boundary / test_check_docs / test_check_wave_startup):
  1713 passed / 4 skipped (check_docs 実 repo 走の growth hold 3 + flaky hold 1、既存) / 68.9 秒 / rc=0。
- 実装 commit の full 監査: 計算ノード 4049.nqsv、11,076 件、新規違反なし、rc=0。
- Codex author の直接呼び出し検査 (子の自己申告、`verbatim/s5-author-report.md`): 27 件 PASS、M2 (監査削除) の反実仮想で
  runner 計数 1 → 主張が赤化 → 復元確認。
- **受入 1 回目 (docs commit `7cfd5d4b7` の tip、23:35 投入) は赤 1 件**: 24,759 passed / 1 failed / 67 skipped、
  `test_check_subprocess_bytecode_guard.py::test_real_repo_clean` — 自 wave 帰属。新規負例の
  `subprocess.run([sys.executable, ...], env=env)` の env が `_real_waiter_repo` の tuple 返り値で、bytecode guard の P2
  が静的に辿れず `test_dev_wave_wait.py:8703:14:run` を違反とした (既存の同型 test は `env["PYTHONDONTWRITEBYTECODE"] = "1"` を
  関数内で代入)。Codex fix 1 巡で同じ 1 行を足した (`7562001c4`、`verbatim/s6-fix1-report.md`)。fix 後: checker rc=0、
  焦点走 f2 (test_dev_wave_wait + test_check_subprocess_bytecode_guard) 385 passed / 33.9 秒、焦点再レビュー 1 本
  (`verbatim/s6-focus-review.md`)、変異 matrix を fix commit で再走 (下記 final2)。

## 変異 matrix (事前登録 = `verbatim/s4-ruling.md` §5、DW-M01)

container worktree `.codex/worktrees/t2670-mutcontainer` (実装 commit `21e0bdc6b` の使い捨て worktree) で
`tools/mutation_harness.py` を直接当て、runner は `run_tests.py` 3 file (test_dev_wave_wait / test_dev_wave_wait_compute /
test_run_tests_shards)、計算ノード dispatch (D612 の queue 待ち 1800 / grace 600 上書き)。probe 走で観測 node を集めてから本走。

| ID | 変異 | 期待 | 結果 (本走) |
|---|---|---|---|
| M0 | 移設 block の comment だけ変更 | SURVIVED (対照) | SURVIVED (rc=0、注入実在は spec の old/new 差で確認) |
| M1 | 監査を `git commit` 前 (旧位置) へ戻す | KILLED | KILLED、19 node 完全一致。実 git 負例の赤理由 = `assert ['run'] == []` (受入 command が投入された)。他 18 は順序 pin (補助) |
| M2 | 監査呼び出しを削除 | KILLED | KILLED、14 node 完全一致。実 git 負例の赤理由 = runner 計数 (同上) |
| M3 | 監査の非 0 を無視 (`effects.run` で結果を捨てる) | KILLED | KILLED、4 node 完全一致 (実 git 負例 = runner 計数、fake の history 赤 2 本、stage param 1 本) |
| M4 | `merge_pending = False` を監査成功後へ遅らせる | KILLED | KILLED、5 node 完全一致。実 git 負例の赤理由 = `stage=merge-abort rc=74 source_rc=128` (MERGE_HEAD 不在で abort が失敗する cleanup 契約の赤)、fake 2 本 = `git merge --abort` の出現、`nonzero_stage[commit-rev-parse]` = pin 段の赤で abort が走る期待列差 |
| M5 | 監査の stage 名だけ変更 | 診断 pin (KILL に数えない) | 4 node 赤 (stage 名文字列のみ、受理集合は不変)。診断感度 pin として別枠記録、KILL 数に含めない |

probe 走 (22:21 投入、8 request、全件 SURVIVED 登録で観測 node を収集) → 本走 (22:38〜23:08、baseline PASSED 88.5 秒、
KILLED 5 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0、matching 6/6、m3 / m4 の所要 469 / 755 秒は queue 待ち込み)。
意味的 kill (負例が受理集合の変化で赤) は M1〜M4 の 4 件で、いずれも実 git 負例が専属 killer。順序 pin だけの赤と M5 は
補助・診断として分けた (DW-M03 / M08)。
**fix 後の再走 (final2、DW-S06-C):** container を fix commit `7562001c4` へ切り替え、同じ spec (anchor を fix 後の現物で再検証、
内容同一で sha256 も同一) で 23:56〜00:08 に再走。baseline PASSED (89.4 秒)、KILLED 5 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0、
matching 6/6 で本走と同一。land の受領証が指す tip はこの commit 以降の前進 merge だけを含む。
spec: `mutation-spec-probe.json` / `mutation-spec-final.json` / `mutation-spec-final2.json`、台帳: `mutation-ledger-probe.json` /
`mutation-ledger-final.json` / `mutation-ledger-final2.json`。

## scope 外で残るもの

- checker に HEAD 以外を pin する `--head` を足して commit 前に dangling merge commit を監査する設計 (受領証・registry の
  HEAD 束縛の見直しを伴う別単位)。
- 保持した merge commit の違反が既存の是正契約 (前進訂正 commit / 既知違反登録のユーザー裁定) で解消できない事例が出た
  場合の裁定パッケージ (現時点で該当なし)。
