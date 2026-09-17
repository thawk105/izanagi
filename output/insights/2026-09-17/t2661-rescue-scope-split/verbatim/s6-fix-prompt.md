単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2661-impl

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2661-rescue-scope-split/s5-author-prompt.md` — 段 5 実装子の契約 (権限、所有 7 file、テスト弱体化禁止、受理集合、報告義務、規模上限)。**本 fix 子はこの契約を全文継承する**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2661-rescue-scope-split/artifacts/dev-wave-t2661-rescue-scope-split/s6-a.md` — 段 6 レビュー U1 (must-fix 0、nit 2 件が本 fix の対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2661-rescue-scope-split/artifacts/dev-wave-t2661-rescue-scope-split/s6-b.md` — 段 6 レビュー U2 (must-fix 0、fix 対象なし。参考)
- 所有 file (repo root `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2661-impl`、HEAD `0f7b6b73e` = 段 5 の実装 commit):
  - `tools/audit_dangling_commits.py`: `_print_offrepo_report` 1922〜1930 (off の開示行)
  - `orchestrator/tests/test_audit_dangling_commits.py`: `test_explicit_off_disclosure_is_distinct_from_missing_root` 4231〜4247、`test_explicit_full_without_root_is_execution_failure` 4305〜4317

**大きい file を全文 `cat` しない。** `grep -n` と `sed -n` の範囲指定で読む。

## この段の仕事 (nit 2 件の fix、他は触らない)

1. **開示行の記号を半角へ (U1 所見 1)。** `_print_offrepo_report` の off 行で全角の `（` `）` `；` を半角の `(` `)` `;` に替える。文言 (「repo 外走査は明示 off」「の指定も無視」「repo 外の同一実体は未確認」「findings は full なら抑止されうる (commit, path) 対を含みうる」「救出 triage は --offrepo-scan full --offrepo-root <root> を指定して単独実行する」) は変えない。`test_explicit_off_disclosure_is_distinct_from_missing_root` の assert 文字列がこの行の部分文字列を検査しているので、半角化で assert が壊れないか確認し、壊れるなら **assert 側を同じ半角へ揃える** (期待の緩和ではなく表記の追随。緩和・削除はしない)。`check_branch_rescue.py` の parse (行頭空白 + `commit <oid> (`、`要確認の到達不能変更 N commit`、`要確認 0 件`、terminal 行) に当たらないことを目視で確認する。
2. **M3 の帰属を単一理由に (U1 所見 2)。** `test_explicit_full_without_root_is_execution_failure` は `tmp_path` (git repo でない) を `--repo` に渡すため、full + root 無しの拒否を除去する変異 (M3) では `_checked_git` の git 失敗が先に rc 2 を返し、`_audit_snapshot` の trap に届かない。`_checked_git` にも `_forbid_offrepo_io` の trap を置く (`monkeypatch.setattr(ADC, "_checked_git", _forbid_offrepo_io)`) ことで、拒否が消えたら trap の AssertionError で赤になる形にする。既存の専用文言 assert (`--offrepo-scan full には ...`) は残す。

## 守る点 (段 5 契約の再掲)

- **既存 test の期待値を変えない。** 反転・緩和・skip・削除で緑にしない。上記 1 の assert 文字列の半角追随だけを例外とし、それ以外の変更を混ぜない。赤なら実装側が誤り。期待値が誤りなら実装を変えず報告して止める (この「止める」は当該項目の作業を止めて報告することであり、他の項目は続ける)。
- 所有 2 file 以外を触らない。docs 編集・`git add`・`git commit` をしない。
- 受理集合を変えない。開示行の文言と test の trap 追加だけ。

## test の実走

`PYTHONPATH=. python3 orchestrator/tests/test_audit_dangling_commits.py` (自走 harness) を走らせ、緑には実走 nodeid・件数を併記する。加えて、項目 2 の効果を **反実仮想で確かめる**: `audit_with_offrepo` の full + roots 空の `RuntimeError` ブロック (1702〜1706) を一時的に除去し、`test_explicit_full_without_root_is_execution_failure` が **trap の AssertionError** (git 失敗の rc 2 ではなく) で赤になることを確認し、必ず戻す (戻したことを `git diff --stat` で示す)。

## 完了報告に必ず含める

- 所見ごとの closed / partial / regressed の対応表 (U1 所見 1、U1 所見 2)。
- 変更 file:line と old → new。
- 実走 nodeid と結果。反実仮想の結果 (赤理由の逐語 1 行)。
- 既存 test の期待値を変えていないことの明示 (半角追随の assert があればその行)。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2)、最後の節は必ず `## 総括`。

節の順:

## 所見対応表
## 変更一覧
## 実走結果
## 反実仮想
## 期待値変更
## 総括
