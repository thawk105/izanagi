## 総括

指定の 2 ファイルを実装し、worktree に残しました。`git add` / `git commit` は実行していません。**合成入力で検証済み、実データの 12 wave 集計は未実走**です。

- [login_check_receipt_replay.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-login-check-probe/tools/login_check_receipt_replay.py)
- [login_check_event_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-login-check-probe/tools/login_check_event_ledger.py)

**CLI・出力**

```bash
python3.10 tools/login_check_receipt_replay.py \
  --store <dir> --repo <abs> --out-dir <dir> [--waves <jsonl>]

python3.10 tools/login_check_event_ledger.py \
  --jobs-root <dir> --repo <abs> --out-dir <dir> \
  [--receipts <receipts.json>] [--limit 12]
```

B → A → B の順で、wave 同定、受領証帰属、台帳への対応付けを行えます。

| 出力 | field 一覧 |
|---|---|
| `receipts.json` | `captured_at`, `store`, `repo`, `waves_input`, `graph_sha256`, `graph_error`, `partitions`, `receipts`, `balance`, `attribution_balance`, `errors`, `notes` |
| 受領証行 | `file`, `partition`, `mtime_ns`, `mtime_epoch`, `mtime_jst`, `size`, `sha256`, `read_result`, `receipt`, `tip`, `checker`, `schema`, `inherited`, `config_sha256`, `env_kind`, `reachable`, `reconstruction`, `reconstruction_reason`, `correction_check`, `matched_candidate`, `candidate_distance`, `excluded_later_count`, `unavailable_candidates`, `selection_count_reconstructed`, `comparison_diff`, `commit_owner_wave`, `window_waves` |
| `waves.jsonl` | `wave`, `job_dir`, `file`, `line`, mtime・hash、`main_before`, `main_after`, `landing_tip_sha`, `tested_tip_sha`, `window_elapsed_s`, 観測窓、`selection_candidates` |
| `ledger.json` | `captured_at`, `repo`, `jobs_root`, `population`, `wave_selection_inventory`, graph 情報、`check_docs_scope_rules`, `check_docs_explicit_paths`, `check_docs_reference_paths`, `scope_inputs`, `receipt_input`, `waves`, `summary`, `summary_receipts_unique`, `assumed_model`, `notes`, `errors` |
| wave 別台帳 | `commits`, `commit_error`, `inventory`, `evidence`, `acceptance_attempts`, `land_attempts`, `handoff_mentions`, `receipt_matches`, `obligations`, `ancillary_obligations`, `executions_without_matched_obligation`, `counts`, `walls`, `call_gaps`, `unclassified`, `input_balance`, `assumed_full_audit_wall_s`, `unreconstructable_count`, `overwrite_suspect_count`, `errors` |

人向けの同内容を `receipts.md` / `ledger.md` に出します。欠測によって存在しない詳細 field もあります。

**自走結果**

Python 3.10 の `py_compile` と両 CLI の `--help` は成功しました。一時 Git repo・store・job dir による自走では、以下を確認しました。

- 7 受領証の収支＝正常 4、不正 3。warm、cold、到達不能を保持。
- raw correction fallback、不正 records の拒否、未来 mtime の除外、同 tip の距離 0 候補選択。
- 非空 registry の UTF-8 batch 読取。
- land 出力の複製、受入 attempt、full / range / preflight の区別。
- 直接計測 22.5 秒、空 `.err` の区間 4 秒、非空 `.err` の開始時刻不採用。
- JSON は `captured_at` 以外、Markdown / JSONL は全 bytes が再走一致。
- 入力ファイルの hash・mtime 不変。入力不在でもエラー情報付き出力を生成。

合成出力：[receipts.json](/tmp/login-check-synthetic-o_c6aq_m/out/receipts.json)、[ledger.json](/tmp/login-check-synthetic-o_c6aq_m/out/ledger.json)。

**解釈差・不確かさ**

- correction regex は実装から写しました。selection は `_commit_range` に合わせて **`policy` ＋ `policy..HEAD`** を使います。
- `before` 義務は直前 30 分、`after` 義務は直後 30 分で対応します。依頼の一律「直後」からの解釈差を注記しました。
- check_docs の commit 前義務は、優先資料である裁定 #2 に従って完了変更 commit 全件にしています。
- 旧 checker 固有の過去動作、失われた同 tip 受領証、失敗 land の監査到達は確定しません。registry manifest を復元できなければ `unreconstructable` にします。
- 同一 land JSON の複製と同一結果の再実行は区別不能です。`aliases` と `duplicate_ambiguous` を残します。
- 時刻対応は履行候補です。観測下界・受領証・記述件数は加算しません。

**check_docs 走査集合の逐語と根拠**

[check_docs.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-login-check-probe/tools/check_docs.py:129) の `LIVING_DOCS` の path literal：

```text
README.md
AGENTS.md
CLAUDE.md
tools/README.md
.codex/agents/README.md
output/README.md
output/task-runs/README.md
docs/README.md
docs/ai-provenance.md
docs/provenance/correction.md
docs/provenance/audit.md
docs/roadmap.md
docs/related-work/README.md
docs/phase3.md
docs/phase3-main-experiment.md
docs/phase3-8b-descriptor-design.md
docs/phase3-8c-preregistration.md
docs/phase3-b4-reflux-ablation-preregistration.md
docs/glossary.md
docs/agent-architecture.md
docs/orchestrator-design.md
docs/ccbench-anatomy.md
docs/axis-onboarding.md
docs/isolation-phenomena.md
docs/ruleops.md
docs/dev-wave/core.md
docs/dev-wave/workers.md
docs/dev-wave/mutation.md
docs/dev-wave/operations.md
docs/skill-self-improvement.md
```

動的列挙の逐語：

```python
(REPO / "docs").glob("phase3-s*-runbook.md")
directory.glob("*.md")  # docs/spool/decisions
(ARCHIVE_DIR, "docs/archive", "worklog-*.md")
(INSIGHTS_DIR, "output/insights", "*.md")
re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name)
p.name.endswith(".md")
skill_root.rglob("*")
command_dir.glob("*.md")
reference_root.rglob("*")
provenance_root.rglob("*")
ARCHIVE_DIR.iterdir()
HANDOFF_DIR.glob("*.md")
```

根拠は同ファイルの 170、1827、2640–2680、5143、5868、5889、5920、6821、6856 行付近です。skills は `dev-wave` / `rulings` / `next-tasks` / `cleanup-branches`、reference root は `docs/dev-wave` / `docs/provenance`。`COMMAND_LIMITS` は `.claude/commands/` の同名 4 `.md` です。

加えて、`docs/worklog.md`・`docs/decisions.md`、spool の委譲検査、checker が読む実装ファイル、living docs 中の `PATH_REF` による存在検査を反映しました。**任意深さの全 `.md` を走査する実装ではありません。**

**所有外への静的影響**

`test_ccbench_spawn_sites.py` の process 目録は `orchestrator/calibrator`・`orchestrator/campaign`、build 走査はそれらと `tools/pegasus` が対象で、今回の `tools/` 直下 2 本は対象外です。`test_p3_b4_wiring_probe.py` は指定された保護木の比較でした。全 `tools/**/*.py` を読む login-headroom・qdel・receipt-publish の AST 検査も確認しましたが、今回のコードに該当する禁止定義・呼出しは見当たりません。既存テストは実走していません。