# [T-2379] test_s8b_approved.py / test_profiler_directive.py の sys.path 暗黙依存を自己完結にした wave — 一次資料 (2026-09-18)

- wave: branch `dev-wave-t2379-syspath-selfcontained`、worktree `.claude/worktrees/dev-wave-t2379-syspath-selfcontained`
- 起点 main: 302b94796 (11:01 JST の local main、fresh worktree)。開始 gate `check_wave_startup.py --mode fresh` rc=0
- 種別: コード (test 2 file、各 1 行) + docs。Codex author 1 本 (D95)、段 2・3・段 6 レビュー子は `DW-C00` の既定軽量版で省略
  (設計択一は割れず、正しさ防壁・受理集合に非接触)
- 裁定の出所: D95 (実装面は Codex author)、D1707 (2 file を自己完結させれば直る技術的欠陥。collection 絞り込みは gate 2 の別裁定で本 wave は触らない)

## §1 欠陥の実測 (段 1、修正前)

対象 2 file だけを選択した走 (`tools/run_tests.py orchestrator/tests/test_s8b_approved.py orchestrator/tests/test_profiler_directive.py`、
login から投入、runner の自動判定で計算ノードへ dispatch):

| request | 結果 | 赤 |
|---|---|---|
| 5493.nqsv (test_s8b_approved.py 単独) | rc=1 | 収集 ERROR |
| 5501.nqsv (2 file) | `1 failed / 58 passed / 1 error` rc=1 | `test_s8b_approved.py` 収集時 `ModuleNotFoundError: No module named 'tests'` / `test_profiler_directive.py::test_derived_directive_is_accepted_by_the_role_policy_check` で `ModuleNotFoundError: No module named 'codex_roles'` (test_profiler_directive.py:341) |

機構: 両 file は先頭で repo root を `sys.path.insert(0, ...)` するが、`from tests.skiputil import` と `from codex_roles import policy` は
`orchestrator/` が sys.path に載っているときだけ解決する。それを載せるのは他の test module の import 副作用
(`test_campaign.py` / `test_campaign_import_invariant.py` / `test_reflux_ir.py` の `sys.path.insert(0, ORCHESTRATOR)`) で、全収集では
これらが先に import されるため隠れ、狭い選択では露出する。`orchestrator/` と `orchestrator/tests/` は `__init__.py` の無い namespace
package なので、repo root だけで `orchestrator.tests.skiputil` / `orchestrator.codex_roles` は解決する (先例:
`test_s8b_protocol_builder.py`、`test_codex_agents.py`)。

login で直接 `python3 -m pytest` は `guard_bash.py` が拒否する (runner 経由が正規経路)。

編集面照合 (job dir の overlap_scan.py、210 branch tip + 208 worktree の作業ツリー): 対象 2 file と `skiputil.py` を触る稼働 wave は 0 件。
`conftest.py` は 2 tip + 5 codex 木が触るが本 wave は非接触。

### 前提訂正

依頼文は「F982 の原因で、entry 1644 の焦点走 f1 でも再発」と書くが、F982 (`test_real_repo_serialization.py` の wrapper が実行中に
`test_p3_s4_loop` を import し conftest の site 中立化 fixture の差し替えを受けない → WAL lock の JSON 不一致) と、entry 1644 の f1
(request 4932.nqsv、同じ WAL lock 不一致) は本欠陥とは別機構である。T-2379 (D1707) の赤は `ModuleNotFoundError`。両者は「狭い選択走の
偽赤」の同族だが、本 wave は T-2379 だけを直し、F982 (wrapper / conftest) は触らない。F982 の「恒久対応: なし」は変わらない。

## §2 修正 (段 4 裁定 → 段 5 Codex author)

| file | 行 | 変更前 | 変更後 |
|---|---|---|---|
| `orchestrator/tests/test_s8b_approved.py` | 31 | `from tests.skiputil import Skip, skip  # noqa: E402` | `from orchestrator.tests.skiputil import Skip, skip  # noqa: E402` |
| `orchestrator/tests/test_profiler_directive.py` | 341 | `    from codex_roles import policy  # noqa: PLC0415` | `    from orchestrator.codex_roles import policy  # noqa: PLC0415` |

(P1) 修正形の選択: `orchestrator.` 接頭の絶対 import。代替の `from skiputil import` (他の約 20 file が使う形) は pytest の prepend
import-mode による rootdir 挿入に依存し、file 自身の bootstrap で閉じない。`Skip` の同一性は各 file 内の `_run()` に閉じており、
どちらでも検査の意味は変わらない。

不変条件: sys.path の挿入を増やさない、検査の意味 (policy の関数・Skip/skip) と受理集合を変えない、他 module の収集順に依存しない。
conftest / skiputil / production / runner / collection 絞り込みは非接触。

実装: Codex author (job-id `s5-author-01`、gpt-6-astra / medium、receipt accepted)。子の自己検査 (pytest なし、fresh process で
sys.path に repo root だけ): IMPORT_PASS ×2、DIRECT_CALL_PASS、旧 import 文の DID_RAISE ×2 (ModuleNotFoundError)、anchor 各 1 件、
所有外差分なし、`grep -rn "from tests\.skiputil\|from codex_roles import" orchestrator tools` は 0 件。起動器の終端 commit 788433a50
(impl 木) から base 302b94796 基準の所有 path 限定 patch を取り出し wave 木へ apply (patch の内容 = 統合 commit b0eea3720 の差分そのもの。`.diff` は所在不問で実装面と判定されるため repo へ複製せず job dir `s5-implementation.diff` に保全)、
blob a19182bb5 / b44a01fae 一致。統合 commit b0eea3720。

## §3 段 6 検証 (修正後 b0eea3720、計算ノード gen_S、同一 worktree の dispatch を 1 本の chain に直列化)

段 2・3・段 6 の敵対レビュー子は `DW-C00` の既定軽量版で省略した (設計択一は (P1) のみで割れず、正しさ防壁・受理集合に非接触)。
chain (`verbatim/chain-verify-1.log`): 11:35:31 開始 → 11:50:34 完了 (JST、date 実測)。

### 焦点走 (対象 2 file だけの選択走 = 修正後緑の主張)

| request | 選択 | 結果 |
|---|---|---|
| 5521.nqsv (11:46:56〜11:47:03) | `test_s8b_approved.py` + `test_profiler_directive.py`、`-q -rf --force-dispatch` | **69 passed** rc=0 (修正前の同選択 5501.nqsv は 1 failed / 58 passed / 1 error) |

### 変異 matrix (段 4 の事前登録どおり、runner 選択は同じ 2 file)

| 変異 | 内容 | 期待 | 実測 | request |
|---|---|---|---|---|
| M-A (negative、手動) | `test_s8b_approved.py:31` を `from tests.skiputil import Skip, skip  # noqa: E402` へ戻す | 収集 ERROR 1 件 (`No module named 'tests'`) | **59 passed, 1 error**、赤は `IZANAGI_FAILURE rank=1 category=error when=collect nodeid="orchestrator/tests/test_s8b_approved.py"` の 1 件、`ModuleNotFoundError: No module named 'tests'` (単一理由) | 5544.nqsv |
| M-B (negative、harness) | `test_profiler_directive.py:341` を `    from codex_roles import policy  # noqa: PLC0415` へ戻す | KILLED、node = `test_profiler_directive.py::test_derived_directive_is_accepted_by_the_role_policy_check` | **KILLED**、`1 failed, 68 passed`、failed_nodes は期待 node と完全一致、`ModuleNotFoundError: No module named 'codex_roles'` | 5548.nqsv |
| M-C (positive、等価、harness) | 同行末に `  # equivalent-mutation` を足す | SURVIVED (expected_nodes 空) | **SURVIVED**、69 passed (harness の SURVIVED 検出の正例) | 5547.nqsv |

harness (`tools/mutation_harness.py --runner-mode dispatch --detached`、spec `verbatim/mutation-spec-main.json`
sha256 `dd48ba86928699840a7202dd763589873287d54d609dbfcd187ae4fd3753c491`、台帳 `verbatim/mutation-main.json`): collection 5545.nqsv PASSED、
baseline 5546.nqsv PASSED (69 passed)、repo_head b0eea3720、rc=0。M-A は形状が pytest collection error (file 単位、`FAILED ` 行なし) で
harness の `_failed_nodes` (tools/mutation_harness.py:1253、`FAILED ` 行のみ抽出) に登録できないため、段 4 で事前登録した独自手順で
実測した (`DW-M05` の「独自 harness は同等検査を備えると段 4 で事前登録」に該当):

1. `git status --porcelain` 空・作業 blob == `HEAD:<file>` を確認 (a19182bb5)
2. 旧行を 1 箇所だけ置換 (出現 1 回でなければ中止)、`git diff --stat` が対象 1 file +1/-1 であること (mutated blob fee703dfb = 修正前 main の blob と同一)
3. 同じ 2 file 選択で `tools/run_tests.py … -q -rf --force-dispatch`
4. `git checkout -- <file>` で復元、`git hash-object` == HEAD blob (a19182bb5)、`git status --porcelain` 空を確認 (`restore-verified`)
5. signal (INT/TERM/HUP) でも復元する trap

手順の逐語は `verbatim/ma-manual-1.log`。script 本体 (`run-ma-manual.sh`、`ma_mutate.py`) は実行可能資材なので repo へは入れず、job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2379-syspath-selfcontained/` に保全した (D95 の実装面判定を避けるため)。

### 単一理由性 (F820)

M-A / M-B の赤はそれぞれ 1 つの `ModuleNotFoundError` だけで、同じ入力を拒否する層は前後・内側に無い (digest の
`failures=1` と一致)。修正前の 5501.nqsv も同じ 2 署名だった。

### provenance

実装 commit b0eea3720 後の `tools/check_ai_provenance.py` 全史監査: 11,315 件、新規違反なし、rc=0 (login bounded local、11:52:16〜11:53:24)。

## §4 受入・land

(受入全走と land は本 README の commit 後に行う。結果は worklog エントリと land の受領証が正本。ここには書かない)

## §5 scope 外として残るもの

- F982 (wrapper `test_real_repo_serialization.py` + conftest site 中立化 fixture の順序) — 別機構、本 wave 非接触。恒久対応は引き続き「なし」。
- collection 絞り込み (D711 gate 2 の弱体化可否) — D1707 のユーザー裁定待ちのまま。本 wave はその技術的前提 (2 file の自己完結) だけを満たした。
- `DW-O18` の「file選択走は`from tests import`確立後に限り未確立赤も偽赤」— 本 wave 後、test file に `from tests.` 形は残らない
  (author の grep 0 件) ので、この句の対象は消えた。節は exact literal pin (`check_docs`) と予算満杯のため本 wave では触らない (段 8 で候補として記録のみ)。
