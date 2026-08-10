修正は実装済みです。既存 tracked ファイル・docs・台帳・`orchestrator/campaign/` は変更していません。

## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| B-1 exact-13 専用入口 | `closed` | caller が集合を指定できない `require_approved_addendum_a_fields()` を追加し、承認 blob の既定経路正例を追加。 |
| B-2 digest oracle | `partial` | actual digest の例外漏洩は除去。approval manifest 由来でない caller-supplied trust root は scope 外のまま残る。 |
| B-5 Git hardening | `closed` | 環境 allowlist、config 無効化、top-level exact、literal pathspec、16 MiB 上限、サイズ比例 timeout、shallow/replace refs/grafts 拒否を追加。 |
| A2-5 resolver fallback mutation | `partial` | resolver が存在しないため、単一理由帰属する fallback 変異は引き続き定義不能。 |
| B-6 resolver 経由証明 | `partial` | 公開 resolver 自体が scope 外で未実装。低水準 fail-closed の検査のみ。 |
| M12 過剰決定 | `closed` | commit 型の `M12a` と symlink mode の `M12b`、対応 test node を分離。 |
| P1 / M13 / M14 / M15 | `closed` | 指定された4変異と対応 node を登録。全 `old` は exact 1 件。 |
| 回帰 | `regressed` なし | 承認済み追補は a01〜a13、合成 digest は指定値のまま。 |

## 総括

1. 変更ファイルと行数（現在行数／開始時からの純増）:

   - [__init__.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/orchestrator/preregistration/__init__.py): 28行／+2
   - [addendum_envelope.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/orchestrator/preregistration/addendum_envelope.py): 186行／+10
   - [blobref.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/orchestrator/preregistration/blobref.py): 266行／+100
   - [erratum.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/orchestrator/preregistration/erratum.py): 401行／±0
   - [test_t139_preregistration_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/orchestrator/tests/test_t139_preregistration_binding.py): 527行／+96
   - [mutation spec](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-10_t139-producer-slice-mutation-spec.json): 318行／+85

2. pytest 実走結果:

   - file 全体（31 node）、M15 node 単体、collect-only を `tools/run_tests.py` 経由で試行。
   - すべて実行開始前に `qstat -Q preflight rc=1`、runner `rc=16` で停止。
   - したがってテストは「実装済み・未実走」であり、緑は主張しません。
   - production API の直接確認では、承認済み追補を専用入口が受理し、合成 digest は `d1782b04…de82` と一致しました。
   - JSON schema load、全19変異の anchor exact-1、期待 node 実在、全 mutant の AST parse は成功しています。

3. 登録できなかった変異:

   - A2-5/B-6 の resolver fallback 変異。`resolve_effective_preregistration` が存在せず、代用品では `DW-M01` の単一理由帰属を満たさないため未登録です。

4. 残した既知の穴:

   - `expected_composed_sha256` の trust root は caller supplied のままです。
   - approval manifest／公開 resolver が未実装のため、resolver 経由の fallback mutation 証明はありません。
   - pytest と mutant pytest は Pegasus dispatch infrastructure failure により未実走です。