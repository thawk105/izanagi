# [T-2638] 段 4 裁定 — 所見の real/refuted、plan v2、変異事前登録

裁定: 2026-09-18 06:50 JST (親)。対象 = `s2-plan.md`、`s3-lensA.md` (正しさ境界)、`s3-lensB.md` (過剰・削除)。
main は wave 開始時 (`d2ebef7a4`) から不変、T-2638 に関する新裁定なし (decisions.md 再走査)。

## 1. 所見の裁定

| # | 出所 | 裁定 | 採否 | 理由・実測 |
|---|---|---|---|---|
| A1 | lens A | real | 採用 (局所) | stage/sandbox は投入先が子 worktree であることを証明しない。局所策 = (i) 主 checkout (`--git-dir` == `--git-common-dir`) は `refused reason=primary-worktree`、(ii) 操作進行中 (`MERGE_HEAD` 等) は `deferred` (DW-C01 の merge commit は親)、(iii) docs に「起動器は投入先 worktree 全体の残差を commit する」と明記し、実装子は別 worktree へ (DW-S05-A 既存)。起動時 snapshot・opt-in flag は足さない |
| A2 | lens A + B2 | real | 採用 | 待ち手は `_PidState.DEAD` 確定後にだけ 1 回呼ぶ。done 非空判定・check-only 書込み・done rc の再解釈 (B3) は削除 |
| A3 | lens A + B4 | real | 採用 | index.lock の事前検査・skip 再分類を削る。add/commit の失敗はすべて `failed`。対象外 (read-only・非 author/fix) と保存未達を分け、後者は非 0 (下記 rc 表) |
| A4 | lens A | real | 採用 | 正規化後の `none` は `unknown` に写す (`check_ai_provenance.py:1517-1520` が `none` を拒否、実測)。テストは `tools.check_ai_provenance.AGENT_VALUE` (import に副作用が無ければ) で trailer 行を照合し、`none` 不在を assert する。helper から checker を subprocess で呼ぶことはしない (結合と所要) |
| A5 | lens A | real | nit (記録) | 残差 commit の trailer は「その job の構成」を記す。別構成の未 commit 展開物が混在する運用は前提外 (段 5 は単位ごとに別 worktree、依存は着地後に展開)。子 commit はそのまま land しない。commit 本文に 1 行 `scope: worktree residue at job end` を置く |
| A6 | lens A | real | 採用 | DW-S05-A に `<base>` = 子 worktree 作成時の固定 SHA (現在 HEAD ではない) を明記 |
| A7 | lens A | real | nit (記録) | submodule 内編集・index flag (assume-unchanged) は superproject の `add -A` の対象外。本 wave は再帰 commit を足さず、限界として worklog に記す。実装子は submodule を編集しない (patches/ 経由) |
| A8 | lens A | real | 採用 (統合) | 操作進行中 marker を 1 述語 `operation-in-progress` に統合: `MERGE_HEAD` / `CHERRY_PICK_HEAD` / `REVERT_HEAD` / `rebase-merge` / `rebase-apply` (`rev-parse --git-path` で解決)。テストは merge conflict 1 本 (lens B5 の負担削減) |
| A9 | lens A | nit | 記録 | 同一 worktree への並行投入は DW-C00 (dispatch は全種直列) の前提外。排他は足さない |
| A10 | lens A | nit | 採用 (最小) | helper は `print(..., flush=True)` で独立行を出す。docs の 1 文で「記録であり採用・land・撤去とは別」を示す |
| B1 | lens B | 条件付き | 不採用 (両 tool を保つ) | 依頼文は起動器と待ち手を名指しするので両方を実装する。待ち手は最小配線 (opt-in flag + DEAD 分岐)。opt-in の呼び出し箇所 = DW-S05-A に「待ち手へ `--commit-worktree <abs>`」を書く |
| B2/B3 | lens B | real | 採用 | A2 と同じ |
| B4 | lens B | real | 採用 | A3 と同じ |
| B5 | lens B | 部分 | 部分採用 | marker は 1 述語に統合 (A8)。テストは merge 1 本 |
| B6 | lens B | real | 採用 | テストを統合 (下記 §3)。変異も統合後の集合で登録 |
| B-不足 1 | lens B | real | 採用 | 待ち手 flag の呼び出し箇所を docs (DW-S05-A) に名指す |
| B-不足 2 | lens B | real | 採用 | receipt 欠落時の read-only 不発火は「呼び出し側が対象を正しく指定する」契約に限定 (docs)。待ち手は receipt を読まない (trailer は `unknown`) |
| B-provenance | lens B | real | 一部採用 | brief の矛盾は訂正: 順序は recorded → requested → unknown。`requested_*` は launcher が `codex exec -m` / `model_reasoning_effort` へ実際に渡した確定値 (`codex_worker_launch.py:2067-2070`、実測) であり推測ではない |

### brief (P1)〜(P6) の再裁定

- (P1) 訂正。起動器の最終 rc: launcher rc≠0 → そのまま。launcher rc=0 かつ helper が `committed` / `clean` / `deferred` → 0。
  launcher rc=0 かつ `refused` / `failed` → **3** (新規、終端契約未達。2 = 起動失敗と区別し、親が「再投入」でなく「手動 commit」へ進めるため)。
  stderr に `NG: worktree-commit ...` 1 行。
- (P2) 反証を採用。発火 = `--sandbox workspace-write` ∧ stage ∈ {author, fix}。それ以外の workspace-write は `worktree-commit: skipped reason=stage` (rc 影響なし、対象外)。
- (P3) 訂正。待ち手は `--commit-worktree <abs>` のみ (receipt flag は足さない)。DEAD 確定後に 1 回。既存 outcome が成功で helper が `refused`/`failed` なら `_Outcome(RC_FAIL_CLOSED, "producer-commit", detail=...)` (receipt は公開しない = fail-closed)。flag 無しは 1 byte も変えない。
- (P4) 支持。`<base>` の定義を docs に足す (A6)。
- (P5) 支持 (scope 外、記録のみ)。
- (P6) 時点観測。段 5 統合直前に再走査する。

## 2. plan v2 (実装単位 1 つ、Codex author)

### 2.1 helper — `tools/dev_waves/git_state.py`

```python
def commit_worker_worktree(
    repo_root, *, wave, job_id, stage, launcher_rc, receipt_path=None, actor="launcher"
) -> tuple[str, str | None]:
    # 返値 (status, detail): ("committed", sha) / ("clean", None) / ("deferred", reason)
    #                        / ("refused", reason) / ("failed", reason)
```

順序 (すべて `_run` の allowlist 経由。追加する `GIT_COMMANDS`: `git-dir` (`rev-parse --path-format=absolute --git-dir`)、
`git-path` (`rev-parse --path-format=absolute --git-path`)、`add-all` (`add -A`)、`staged-quiet` (`diff --cached --quiet`、rc 0/1 許可)、
`commit-file` (`-c commit.gpgSign=false commit -F`)):

1. `toplevel` の resolve ≠ `repo_root` の resolve → `refused root-mismatch`
2. `git-dir` == `common-dir` (主 checkout) → `refused primary-worktree`
3. `branch` (symbolic-ref) rc=1 → `refused detached-head`; branch ∈ {`main`, `master`} → `refused protected-branch`
4. `git-path` で `MERGE_HEAD` / `CHERRY_PICK_HEAD` / `REVERT_HEAD` / `rebase-merge` / `rebase-apply` のいずれか実在 → `deferred operation-in-progress`
5. `add-all` → `staged-quiet`: rc 0 → `clean`; rc 1 → message file を `tempfile` (repo 外、`NamedTemporaryFile(dir=None)`) に書き `commit-file` → `head` → `committed <sha>`
6. Git の失敗 (timeout・非 0・非 UTF-8) は `failed <固定識別子>`。reset / checkout / clean / lock 削除 / 再試行はしない。

stdout: `worktree-commit: committed <sha>` / `worktree-commit: clean` / `worktree-commit: deferred reason=<r>` /
`worktree-commit: refused reason=<r>` / `worktree-commit: failed reason=<r>` (1 行、`flush=True`)。
`refused`/`failed` は stderr に `NG: worktree-commit <status> reason=<r>` も出す。

commit message (固定):

```text
[T-2638] 起動器/待ち手の終端契約 (D2044 項 16): 実装子の作業木残差を記録

wave: <wave>
job-id: <job_id>
stage: <stage>
actor: <launcher|waiter>
launcher rc: <int|unknown>
receipt outcome: <outcome|unknown>
scope: worktree residue at job end

AI-Agent: product=codex; model=<m>; reasoning=<r>; role=author
```

`<m>` / `<r>` は receipt (あれば) の `recorded_*` → `requested_*` → `unknown`。正規化: 小文字化 → `[a-z0-9._-]` 外を `-` に →
連続 `-` を畳む → 先頭が `[a-z0-9]` になるまで先頭記号を落とす → 末尾 `-` を落とす → 空 or fullmatch 不成立 or `none` → `unknown`。
本文の値は 1 行に escape (改行・`;` を除去) して trailer 混入を防ぐ。timeout は `_run` の既定でなく本 helper 用に `add-all` 120 秒、
`commit-file` 120 秒 (26k file の実測余裕。既定 30 秒は観測用)。

### 2.2 起動器 — `tools/dev_wave_codex.py`

`main()`: dry-run は従来どおり helper を呼ばず return。launcher の `subprocess.run` 復帰後、
`args.sandbox == "workspace-write" and args.stage in ("author", "fix")` のとき helper を呼ぶ (`receipt_path` = 生成した receipt path)。
それ以外の workspace-write は `worktree-commit: skipped reason=stage` を出して helper を呼ばない。read-only は何も出さない。
最終 rc は §1 (P1) の表。`_launcher_argv` は receipt path と stage を `args` に保持する (argv 不変)。

### 2.3 待ち手 — `tools/dev_wave_wait.py producer`

`_producer_parser` に `--commit-worktree <Path>` (既定 None、指定時は絶対 path 必須、相対は rc=2)。
`wait_for_producer(..., commit_worktree=None)`: DEAD 確定 (既存 `break`) の直後、`commit_worktree` が非 None なら helper を 1 回呼ぶ
(`actor="waiter"`, `receipt_path=None`, `launcher_rc=None`, `job_id`/`wave`/`stage` = `unknown`)。その後は既存のファイル待ちへ。
既存 outcome が成功で helper が `refused`/`failed` → `_Outcome(RC_FAIL_CLOSED, "producer-commit", detail=...)`。
check-only 経路は触らない。flag 無しは stdout/stderr/rc/receipt bytes 不変 (テストで固定)。
`main` の配線 (`_parse_cli` → 通常待機) は実装時に確認して最小で通す。

### 2.4 docs (親) — `docs/dev-wave/workers.md` DW-S05-A

`<base>` 化 (= 子 worktree 作成時の固定 SHA)、終端 commit の 1 文 (起動器と待ち手 `--commit-worktree <abs>`、記録であり採用・land・撤去とは別)、
同層の縮約で相殺。pin 行不変。編集後 `check_docs.py` で確定。

### 2.5 テスト (統合後)

| file | test | 実体 |
|---|---|---|
| `test_dev_waves_git_state.py` | `test_commit_worker_worktree_records_residue_then_noop` | 実 repo (tmp) の topic branch に tracked 編集・削除・untracked を作り helper → commit +1、tree に全残差、trailer 1 行 (AGENT_VALUE 照合)、repo-local identity、2 回目 `clean` で HEAD 不変、`git diff --cached <base> -- <path>` の bytes が commit 前後で一致 |
| 同 | `test_commit_worker_worktree_provenance_values` | receipt: recorded 優先 / requested fallback / 欠落 / `NONE` → `unknown` / 改行・`;` 混入の escape を実 commit message で確認 |
| 同 | `test_commit_worker_worktree_refuses_detached_protected_primary_root` | parametrize: 実 `checkout --detach`、`main`、主 checkout、sub-directory 指定 → `refused` + HEAD/index/作業 file 不変 |
| 同 | `test_commit_worker_worktree_defers_merge_in_progress` | 実 merge conflict (`MERGE_HEAD` あり) → `deferred`、index の unmerged 保持 |
| 同 | `test_commit_worker_worktree_failed_keeps_residue` | commit を失敗させる (identity 無し repo) → `failed`、HEAD 不変、staged 内容保持 |
| `test_dev_wave_codex.py` | `test_workspace_write_author_commits_after_launcher` | fake launcher が編集後 rc=0 / rc=7 (parametrize) → commit +1、dispatcher rc = 0 / 7、stdout 行 |
| 同 | `test_terminal_commit_failure_rc` | launcher rc=0 × helper failed → 3 + `NG:`; launcher rc=7 × failed → 7 |
| 同 | `test_read_only_and_non_author_never_commit` | dirty topic branch、read-only (author) / workspace-write (plan) → commit 0、HEAD/index 不変 (後者は `skipped reason=stage`) |
| 同 | `test_dry_run_never_commits` | workspace-write author dry-run → HEAD 不変 |
| `test_dev_wave_wait.py` | `test_producer_commit_worktree_after_death` | 実 producer (短命 process) の死後に residue を commit、既存 files 判定は維持 |
| 同 | `test_producer_without_commit_flag_preserves_bytes` | flag 無し: stdout/stderr/rc/receipt raw bytes が residue の有無で不変 |
| 同 | `test_producer_commit_worktree_requires_absolute_path` + `:5090` option 集合更新 | 相対 path rc=2、Git 不実行 |

## 3. 変異事前登録 (B-057、実装後に anchor を確定し spec 化。すべて負例 = KILLED 期待、M0 は対照 SURVIVED)

| id | 位置 (実装後に逐語 anchor) | 反転内容 | 殺すテスト (期待 node は probe 走で確定) |
|---|---|---|---|
| M0 | helper の docstring/comment 1 語 | 対照 (等価) | SURVIVED (expected_nodes 空) |
| M1 | `dev_wave_codex.main` の発火条件 | `sandbox == "workspace-write"` を反転 | `test_read_only_and_non_author_never_commit` |
| M2 | 同 | stage ∈ {author, fix} 判定を削除 (常に真) | 同 (plan+workspace-write が commit する) |
| M3 | helper の detached 判定 | rc=1 でも続行 | `test_commit_worker_worktree_refuses_detached_protected_primary_root` |
| M4 | helper の protected-branch 判定 | 集合を空に | 同 |
| M5 | helper の primary-worktree 判定 | 反転 | 同 |
| M6 | helper の operation-in-progress 判定 | marker 集合を空に | `test_commit_worker_worktree_defers_merge_in_progress` |
| M7 | helper の staged-quiet 分岐 | rc 0/1 を入れ替え | `..._records_residue_then_noop` |
| M8 | `dev_wave_codex.main` の rc 合成 | launcher rc≠0 を 0 に上書き | `test_workspace_write_author_commits_after_launcher` (rc=7 側) |
| M9 | 同 | failed + rc=0 を 0 にする | `test_terminal_commit_failure_rc` |
| M10 | helper の trailer 生成 | `AI-Agent` 行を削除 | `..._records_residue_then_noop` |
| M11 | helper の provenance 順序 | requested を recorded より優先 / `none` 写像を外す | `test_commit_worker_worktree_provenance_values` |
| M12 | waiter の opt-in 判定 | `commit_worktree is None` を無視して常に呼ぶ | `test_producer_without_commit_flag_preserves_bytes` |
| M13 | waiter の呼び出し位置 | DEAD 確定前 (loop 先頭) で呼ぶ | `test_producer_commit_worktree_after_death` (生存中に commit されれば不一致) — 実装後に単一理由性を確認、無理なら再照準 |
| M14 | `dev_wave_codex.main` の dry-run 経路 | dry-run でも helper を呼ぶ | `test_dry_run_never_commits` |

単一理由性 (DW-M01) は実装後・spec 化前に各 anchor で確認する。冗長 gate (HEAD blob drift 群) は較正走で `--deselect` 集合を実測する。
runner = `tools/run_tests.py <3 test file> -k "<node 集合>" -q -rf --force-dispatch`、
repo = 変異 container (`.codex/worktrees/t2638-mutcontainer`、統合 commit で detach)、spec/out は job dir。

## 4. scope 外として記録するもの

- cleanup-si-routing (DW-O28 改訂) との相互作用: commit 済み子 branch は main 非到達 commit を持ち、
  `dev_wave_cleanup.py` の撤去は reflog/HEAD 到達性で拒否される (rc=20 系)。D2044 項 16 の限定どおり別裁定。
- submodule 内編集・index flag (A7)、同一 worktree 並行投入 (A9)、別構成の展開物混在 (A5)。
