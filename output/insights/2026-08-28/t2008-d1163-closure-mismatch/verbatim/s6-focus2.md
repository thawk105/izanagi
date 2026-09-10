## 対応表

| 所見 | 裁定 | 根拠 file:line / call-return | 受理例 / 拒否例 | 成果物影響 | 残余 |
|---|---|---|---|---|---|
| FR-01 | `closed` | 新 test は [test_plot_backoff_ci.py:375](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_plot_backoff_ci.py:375) で `plot.main(...) == 0` を要求。production の通常成功経路は provenance を [plot_backoff.py:614](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/tools/plotting/plot_backoff.py:614) で書き、[同:626](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/tools/plotting/plot_backoff.py:626) で `0` を返す。`git show HEAD:...` でも変更前から成功戻り値は `0`。 | 受理: fixture call が `0` を返し、後続 SHA 検査へ進む。拒否: 旧 `is None` は正常な `0` を拒否していた。CLI error の `2` も現 assertion で拒否される。 | fig2b の新生成 provenance が現行 generator SHA を記録することを検査可能になった。production・既存成果物 bytes は変更しない。 | 対象 node 未実走。緑の receipt はない。 |

実際の到達経路は次のとおりです。

1. test が load/make を fixture に差し替える（[test_plot_backoff_ci.py:354](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_plot_backoff_ci.py:354)、[同:357](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_plot_backoff_ci.py:357)）。
2. `main()` を呼び `== 0` を確認する（[同:375](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_plot_backoff_ci.py:375)）。
3. production は同じ `__file__` の SHA を provenance に格納する（[plot_backoff.py:596](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/tools/plotting/plot_backoff.py:596)）。
4. `0` の return 後、test は JSON を読み（[test_plot_backoff_ci.py:376](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_plot_backoff_ci.py:376)）、同じ module file を hash して [同:385](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-closure-mismatch-codex-resume/orchestrator/tests/test_plot_backoff_ci.py:385) の assertion に到達する。

## 追加所見

追加 must-fix はありません。

fix2 の隔離差分は [s6-fix2.patch:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s6-fix2.patch:9)–[同:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s6-fix2.patch:10) の `is None` → `== 0` のみで、reverse-check も成功しました。

したがって fix2 自体は以下を変更していません。

- production code
- artifact の accepted/rejected 例
- historical SHA
- marker
- fixture

唯一変わる受理判定は、FR-01 当該 assertion 自身の「成功値 `0` を受理し、`None` を拒否する」という意図した訂正です。

なお対象 resume worktree全体には既存 wave の14 path分の変更があります。現在は全14 pathが unstagedで、[s6-fix2.md:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s6-fix2.md:10) に記録された author worktreeの staging 状態とは異なります。これは成果物契約への追加回帰ではありません。

## 実走残余

read-only 再レビューのため pytest は実走していません。

既往の対象 node 実行も `rc=16`、`child_started=false` であり、実際には開始されていません（[s6-fix2.md:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s6-fix2.md:6)–[同:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s6-fix2.md:8)）。

残る実走対象は少なくとも次です。

`orchestrator/tests/test_plot_backoff_ci.py::test_production_provenance_records_current_generator_source_sha`

## 総括

FR-01 は静的再レビュー上 `closed` です。従来からの成功戻り値 `0` と新 test の `== 0` が一致し、current generator SHA assertion への call/return 経路も到達可能です。

fix2 は当該1 assertion以外を変更しておらず、DW-G05 の成果物影響を伴う追加 must-fix はありません。ただし対象 node は未実走なので、テストが緑とは報告しません。
