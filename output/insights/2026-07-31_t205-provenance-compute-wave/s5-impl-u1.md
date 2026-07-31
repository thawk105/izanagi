# 段 5 実装子 U1 (checker) 完了報告 — Claude opus

**pytest は 1 度も走らせていない** (ログインノード `pegasus02`)。静的検査と軽い import probe のみ。

## 変更 (`tools/check_ai_provenance.py` +373/-34、`orchestrator/tests/test_check_ai_provenance.py` +870)

| 箇所 | 変更 | 理由 |
|---|---|---|
| import 部 | `REPO` を `sys.path` へ挿入し `site_policy` を import、`PEGASUS_DISPATCH_RC=16`、`AUDIT_WORKERS_CAP=32` | C-2(a)(b)。RC は `run_tests.py:110` と同値契約 |
| 定数 | `WAIVER_KEY` / `RAW_AI_AGENT_WAIVER` / `WAIVER_VALUE` / `WAIVER_POLICY_LITERAL` | W-3(a) |
| dataclass | `WaiverAudit` + `EMPTY_WAIVER`、`CommitAudit` に `waiver` / `waived_applied`、`ImplementationWaived(label, reason, ratified)`、`HistoryAudit(findings, corrected, waived)` | W-3(b)(f) |
| `_waiver_audit` | raw/canonical/final-block の 3 重照合。raw 候補ゼロなら parser を呼ばず即 `EMPTY_WAIVER` | `_correction_audit` 踏襲。唯一の作法差 (固定値照合→文法照合) は docstring に明記 |
| `validate_implementation_author` | 戻り値 `(findings, waived_applied)`、`waived` は codex author 判定の**後**に評価 | **W-3 改訂 2**。`waived_applied` は実発火時のみ True |
| `AUDIT_WORKERS()` | `max(1, min(site_policy.available_cpus(), 32))` を返す module 属性。env 上書きなし | **D 改訂 1** |
| `_Ancestry` / `_build_ancestry` | `rev-list --topo-order --parents --stdin` 1 本 + pickaxe 1 本。pickaxe rev は `*commits` をそのまま渡し argv 前置を保存 | **D 改訂 2**。intercept テストの契約 |
| `_normal_commit_audit` | `ancestry: _Ancestry \| None = None`。`None` で**逐次 oracle を production に残す** | **D-3**。等価性テストの oracle |
| `_audit_history` | 冒頭に空集合 guard、`ThreadPoolExecutor` + `pool.map`、`HistoryAudit` を返す | D 改訂 2 / D-4 |
| 前方訂正の連言 | `and not correction.waiver.exact` を追加 | **W-3 改訂 1 = A-R1 対策** |
| `main()` | `(argv=None, *, site=None, dispatch_fn=None)`。site gate を `parse_args()` の**後**に置き `args.message_file is not None` だけで免除。`waived` を分岐前に初期化し message-file 分岐でも積む。出力ループは両分岐共通で `if findings:` の**前** | **C-2 改訂 (A-R9)** / **W-3 改訂 3 (A-R2)** |
| `_default_dispatch` / `_invoke_dispatch` | `dispatch(argv, task="provenance", repo_root=REPO)`、想定外例外を rc=16 へ一義化 | C-2(e) |

`_is_descendant` の前方訂正呼出は `merge-base` のまま据え置き、`_has_co_authored_by_policy` / `_is_descendant` も削除せず残した。

## 静的検査と probe の実測 (pytest は未実行)

- `python3 -m py_compile` — checker / テスト両方 OK
- **waiver boundary probe 11 形** (module import + 実 git parser): `valid` のみ `exact=True`、他 10 形はすべて
  `exact=False` で期待どおりの finding (two-lines→cardinality、continuation→raw のみ、across-divider→final=0、
  split-blocks→role=author 不在、body-only→canonical=0)
- **`_build_ancestry` vs `merge-base` oracle** (実 repo、git 読み取りのみ): closure **948**、
  pairwise mismatch **0**、cab mask mismatch **0**、反射性 OK
- `_implementation_policy_commit()` → `8c6d3f3bdc716c1ede8febb83ced1b0351a99118` (非 None、親の実測と一致)
- AST 走査で test 内の `provenance.*` / `site_policy.*` 参照の実在確認 → missing なし
- `git status --short` → 変更は所有 2 ファイルのみ

## 新規テストと KILL する変異 (抜粋)

M1 `test_waiver_exact_line_exempts_implementation_author_gate` / M2 `test_waiver_boundary_rejects_malformed_and_out_of_block[10 形]` /
M3 `test_waiver_requires_own_role_author_ai_agent_line` / **M4 `test_waiver_does_not_widen_forward_correction_acceptance`** /
正例 `test_forward_correction_without_waiver_is_still_accepted` / M14 `test_waived_count_excludes_docs_only_commits` /
M5 `test_audit_history_empty_range_returns_zero_findings` / M6・M7 `test_ancestry_bitset_matches_merge_base_oracle_for_every_pair` /
M8 `test_audit_history_is_identical_across_worker_counts_and_ancestry` / M9 `test_suspect_history_audit_refuses_with_infra_rc_without_dispatch` /
M10 + A-R9 `test_login_message_file_is_dispatch_exempt[--message-file|--message-f]` /
A-R8 是正 `test_audit_history_concurrency_high_water_follows_audit_workers` (grep でなく**同時実行高水位**。1→peak 1、4→peak ≥2) /
positive control `test_implementation_policy_epoch_is_pinned_in_this_repo` /
`test_waiver_literal_matches_production_and_repo_policy_exactly_once` / `test_waived_count_is_reported_on_stdout_on_both_green_and_red` /
`test_ancestry_pickaxe_mask_matches_per_commit_oracle` / `test_audit_history_propagates_first_exception_in_input_order` /
`test_forward_correction_ancestry_still_uses_merge_base`。

等価性テストは合成 repo に **root 2 (orphan merge)・merge 2・correction 1・CAB 違反・実装面 path 有無・scope 複数行 (計 11 commit)** を含み、
`findings` を順序込みで 4 arm (逐次 oracle / bitset×1,2,16) 比較する。恒真化防止に `findings`/`corrected`/`waived` の非空を先に固定した。

D96 の同一変更単位更新: `test_claude_only_author_is_rejected_for_implementation_positive_control` /
`test_codex_author_and_nonimplementation_changes_are_accepted` / `test_human_only_implementation_is_not_misattributed_to_codex` /
`test_forward_correction_acceptance_is_commit_order_invariant`。

## 所有外への波及 (静的列挙)

- `tools/task_run_check.py:18` — `provenance-check` が rc を素通しするので、login では rc=16 が台帳 `exit_status` に入りうる (A-R10)
- `tools/dev_waves/cli.py:193` — dev-wave の provenance check が同経路。login では queue 依存になる
- `tools/codex_reasoning_ab.py:89-156` — `git show BASE_COMMIT:<path>` で読む凍結 snapshot の replay。作業ツリーを hash しないので**赤にならない**
- 共有 fixture は既存のまま。新規に `_commit_dated` / `_waiver_history` / `_mixed_history` を**追加のみ**
- `_normal_commit_audit` の既存直接呼出 3 箇所は keyword 呼びで `ancestry=None` 既定に落ち、逐次 oracle 経路を通る
- 他 module からの `validate_implementation_author` / `_audit_history` の caller は存在しない (repo 全 grep)

## 期待して赤くなる finding — **0 件** (親 docs と U2 の land を実測して確認)

指示時点の前提と異なり、親の waiver bullet も U2 の `task` 引数・sanctioned 追加も既に tree にある。
よって**赤はすべて回帰として扱われるべき**。ただし未実走なので、以下は「未検証の想定」として残る:

1. `_mixed_history` の `git switch --orphan` + `merge --allow-unrelated-histories` (git 2.34.1 で構文は有効だが未実行)
2. bitset oracle テストの date 逆転による rev-list 出力順の仮定 (推論のみ)
3. 高水位テストの `measure(4) >= 2` (sleep 0.05s × 11 commit なので余裕はある想定)
4. `test_provenance_dispatch_rc_matches_run_tests_contract` は `run_tests.py` の exec_module で `packaging` を要求する

**重要 (login node 全般)**: site gate 導入により、`--range`/既定 range の全既存テスト約 100 本は
`current_site()` が `PEGASUS_LOGIN`/`PEGASUS_SUSPECT` の機械では dispatch/rc=16 に化ける。
計算ノード (`bnodeNNN` → `PEGASUS_COMPUTE`) では従来どおり local 監査になるため、
**受入は必ず計算ノードで走らせる必要がある**。

## 受理・拒否挙動の差分

| 入力 | 変更前 | 変更後 |
|---|---|---|
| 実装面 + claude-only author + **正規 waiver** (epoch 子孫) | rc=1 (finding) | **rc=0** + stdout に免除行と件数 |
| 同上 + **不正な waiver** (2 行 / 折返し / block 外 / 文法違反 / role=author 不在) | waiver 行は無視 | **waiver 固有 finding が追加**され免除は発火しない (fail-closed) |
| docs-only + waiver | 無視 | 無視 (**件数に計上しない**) |
| codex author 済み + waiver | 受理 | 受理 (**計上しない** = 1 bit も動かない) |
| epoch より前の waiver | 無視 | 無視 (非遡及を維持) |
| 前方訂正の担い手が waiver を持つ | (概念なし) | **担い手資格を失う** = 受理集合は現行と同じか狭くなる方向のみ |
| waiver 無しの正常な前方訂正 | 受理 | 受理 (不変) |
| `PEGASUS_LOGIN` で履歴監査 | local 実行 (130–150 秒) | **計算ノードへ dispatch** し子 rc を返す (例外は rc=16) |
| `PEGASUS_SUSPECT` で履歴監査 | local 実行 | **rc=16** + 拒否メッセージ、dispatch しない |
| `--message-file` (接頭辞省略 `--message-f` を含む) | local 実行 | **local 実行 (免除)** — site を問わない |
| `PEGASUS_COMPUTE` / `OTHER` | local 実行 | local 実行 (不変) |
| 空の selected set | rc=0 | rc=0 (guard で保存) |

## 親裁定を要した点と親の裁定

- `ImplementationWaived` の第 1 フィールドを `commit` でなく **`label`** にし出力を `label=<値>` にした。
  裁定 W-3 改訂 3 が message-file 経路の label を `args.message_file` と定めたため、SHA と path の両方を
  1 フィールドで担う必要があったから。→ **親裁定: 可。** 出力書式のみの選択で受理集合に影響しない。
- 実装できなかった項目: **なし**。
