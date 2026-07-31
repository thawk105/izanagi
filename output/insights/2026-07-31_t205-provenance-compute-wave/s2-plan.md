# 段 2 plan (Claude opus, read-only planner) — [T-205]

親 brief = `output/insights/2026-07-31_t205-provenance-compute-wave/s1-brief.md`。
本ファイルは planner の出力を凍結したものであり、採否は段 4 で親が裁定する。

## 前提の確認

読んだファイル: 段 1 brief / `docs/ai-provenance.md` (全 130 行) / `tools/check_ai_provenance.py` (全 823 行) /
`orchestrator/tests/test_check_ai_provenance.py` (index 全件 + L1–220, L580–1000, L1230–1330, L1540–1600, L2100–2165) /
`tools/pegasus/dispatch_compute.py` (全 1301 行) / `orchestrator/tests/test_pegasus_dispatch_compute.py` (index 全件 + L1–530) /
`tools/run_tests.py` (全 1008 行) / `hooks/guard_bash.py` (全 889 行) / `orchestrator/campaign/site_policy.py` /
`docs/pegasus-runbook.md` §6–§8 (L200–399) / `AGENTS.md` (全 36 行) / insight §11 (L230–265) /
`docs/decisions.md` D95 (L4235–4268)・D96 (L4269–4279)・D103 (L4554–4623) / `docs/worklog.md` L535–594 /
`tools/check_docs.py` (予算表 L140–230, 予算検査 L1690–1760, LIVING_DOCS L30–56, D 見出し検査 L2011–2026) /
`tools/task_run_check.py` / `tools/codex_reasoning_ab.py` L70–160 / `orchestrator/tests/test_hooks.py` L505–845 /
`orchestrator/tests/test_site_policy.py` L220–296 / `orchestrator/tests/test_run_tests_task_run.py` L140–220 /
`orchestrator/tests/test_run_tests_preflight.py` L660–760。

### (P1)〜(P5) への賛否

| | 判定 | 根拠 |
|---|---|---|
| P1 (waiver 形式・最終 block・自身の `role=author` 併記) | **賛成** | `_correction_audit` (`tools/check_ai_provenance.py:237-287`) が raw/canonical/final-block の 3 重照合で既に成立。同じ作法を流用でき、`AI-Agent-Waiver` は `_ai_agent_values` の key 一致判定 (`:218`) にも `RAW_AI_AGENT_CORRECTION` (`:52-56`) にも衝突しない |
| P2 (恒久の正規経路・機械上限なし) | **賛成、ただし 1 点補強** | 免除件数の出力位置は `main()` の `if findings:` (`:791`) の**前**にする。`corrected` の出力 (`:800-804`) と同じ位置に置くと rc=1 のとき免除が sink して「沈黙させない」が破れる |
| P3 (閉じた task enum) | **賛成** | `hooks/guard_bash.py:456` が `tools/pegasus/` の glob 許可を明示的に拒んでいる (D103 決定 5)。任意 command 化はこの裁定と正面衝突する |
| P4 (checker 自身の site 判定を第一層、`guard_bash.py` を第二層) | **賛成、ただし第二層の実効は小さいと明記すべき** | 第一層を入れると `python3 tools/check_ai_provenance.py` は自動 dispatch する正規経路になるので、hook は**それを許可**しなければならない。hook の純増は「同じスクリプトを sanctioned 以外の綴りで呼ぶ形の拒否」だけ。D103 決定 5 の「恒真な保証を謳わない」に従い、この限界を D と runbook に書く |
| P5 (並列度 16 固定・site 由来にしない) | **賛成** | insight §11 (`output/insights/2026-07-30_t200-suite-floor/s7-negative-result.md:245-253`) が 16 で頭打ちと実測。`site_policy.default_test_jobs` 経由にすると非 Pegasus で挙動が変わり D103 決定 6 の「非 Pegasus 挙動不変」を破る |

### brief に無い、プランを縛る 4 つの実測制約 (planner が今回発見)

1. **`docs/ai-provenance.md` の余白は 248 bytes しかない。** 現況 8752 bytes、予算 9000 bytes
   (`tools/check_docs.py:163-165` `PROVENANCE_LIMITS`、超過検出は `:1730-1733`)。waiver 節は最小でも約 458 bytes 必要なので、
   **同一 commit 内で 223 bytes 以上を既存本文から削らないと `check_docs.py` が赤になる**。予算引き上げは T-127 裁定で禁止。
2. **`_audit_history` は 2-tuple を返し、テストが直接 unpack している** (`orchestrator/tests/test_check_ai_provenance.py:1558-1563`)。
   免除件数を外へ出すには戻り値形を変えるしかなく、この 1 テストの機械的更新が必須 (D96 の「境界テストを同じ変更単位で」に該当)。
3. **`test_forward_correction_merge_base_rc128_fails_closed_with_rc2`** (`:2128-2156`) は `_audit_history` 内の
   forward-correction 用 `_is_descendant` (`tools/check_ai_provenance.py:634`) が `git merge-base --is-ancestor` を
   実際に呼ぶことを固定している。→ **D の bitset 置換は per-commit の 2 呼出 (`:573`, `:579`) と
   `_has_co_authored_by_policy` (`:565`) に限り、L634 の 1 呼出は `merge-base` のまま残す**。1 回だけなので性能影響ゼロ。
4. **`test_cab_policy_git_error_fails_closed_with_rc2`** (`:939-963`) は `_git` の argv を
   `args[:4] == ("log", "--full-history", "--no-renames", "--format=%H")` かつ `CO_AUTHORED_BY_POLICY_NEEDLE in args` で
   intercept する。→ **畳んだ pickaxe 呼出はこの argv 前置と needle 位置を保存しなければならない**。

**brief の分割 (U1 = checker(W+D) / U2 = dispatch,hook(A+C)) は素集合ではない** — C の第一層は
`tools/check_ai_provenance.py` を編集する。修正案は「実装順序と依存」に記載。

**非該当と確認したもの**: `tools/codex_reasoning_ab.py:96-141` の `TRACKED_HASHES` / `CASE_HASHES` は
`BASE_COMMIT` (`:602`) に固定した過去 snapshot の replay 仕様であり、現在の `docs/ai-provenance.md` /
`tools/check_ai_provenance.py` を hash しない。W の編集で赤にならない。

## W — waiver trailer の正規経路

### W-1. `docs/ai-provenance.md` (親が書く。実装子は触らない)

**(a) 挿入位置**: `:67` (空行) と `:68` (`## 記録単位`) の間。`## 実装面の Codex author 契約` (`:51-66`) の直後。

**(b) 挿入する本文 (458 bytes。逐語で凍結し、U1 の production 定数と一致させる)**

    ## Codex author の waiver

    Codex が実行不能な期間は、ユーザー裁定を得て次の物理 1 行を最終 trailer block に置き、同じ
    block の自分の `AI-Agent` に `role=author` を持たせることで前節の要求を免除する。

    ```text
    AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>
    ```

    checker は免除件数と理由を stdout へ出す。件数と経緯は worklog に残し、機械上限は設けない (D105)。

**(c) needle を壊さないための必須条件 (本節の要点)**

- 上記本文は `IMPLEMENTATION_POLICY_NEEDLE` = 「実装面を変更する AI 関与 commit は Codex author を必須」
  (`tools/check_ai_provenance.py:25-27`) を**一度も含まない**。「前節の要求を免除する」と書いて needle の再出現を避ける。
  含めると `_implementation_policy_commit()` (`:361-367`) の pickaxe 対象が増え、不変条件も破れる。
- `CO_AUTHORED_BY_POLICY_NEEDLE` = 「Co-Authored-By 候補行はすべて最終 trailer block に置く」(`:28-30`) も含まない。
  「最終 trailer block に置き」という**部分**は現れるが、needle は完全一致文字列なので
  `policy.count(...) == 1` (`orchestrator/tests/test_check_ai_provenance.py:669`) は 1 のまま。
  **この 2 点をレビューで逐語 grep 確認すること** (`grep -c` で 1 と 1)。

**(d) 予算 223 bytes の捻出 (同一 commit 内)**

| 場所 | 変更 | 削減 |
|---|---|---|
| `docs/ai-provenance.md:107-123` | 3 つの `bash` fence を 1 つに畳む | **93 bytes** |
| `docs/ai-provenance.md:128-130` | 観察データの注意書きを圧縮 (安全義務でなく分析上の注意、内容は保存) | **130 bytes** |

合計 223 bytes 削減 → 余白 471 bytes、追加 458 bytes、**残 13 bytes**。commit 前に `wc -c docs/ai-provenance.md` が
9000 以下であることを必ず確認する。足りなければ `:98-99` の forward correction 運用文 2 行をさらに圧縮する。

### W-2. `docs/decisions.md` に D105 を新設 (親が書く。D96 手続の必須要件)

- 挿入位置: `docs/decisions.md:4624` (D104 の末尾) の後、ファイル末尾。
  見出し `## D105. [T-205] Codex author 契約の waiver を正規経路として新設し、免除は公開と記録で抑止する (2026-07-31)`。
- `tools/check_docs.py:2011-2025` が `^## D(\d+)` の重複を検出。現在の最大は D104。
- 記載必須: 決定 (形式・最終 block・自身 `role=author` 併記・恒久経路・機械上限なし)、却下案 (incident 固定・allowlist・env escape hatch)、
  `AI-Agent-Waiver` は forward correction の受理集合を広げないこと。
- **受理集合を変える改修が 3 つある** (waiver の受理、checker rc に 16 が加わる、dispatch の task enum) ので、最低 1 本の新 D は必須。

### W-3. `tools/check_ai_provenance.py` (U1)

**(a) 定数** — `:51-56` の correction 定数群の直後に追加。

    WAIVER_KEY = "AI-Agent-Waiver"
    RAW_AI_AGENT_WAIVER = re.compile(
        rf"^[ \t]*{re.escape(WAIVER_KEY)}[ \t]*:(?P<value>[^\r\n]*)\r?$",
        re.IGNORECASE | re.MULTILINE,
    )
    WAIVER_VALUE = re.compile(
        rf"^reason=(?P<reason>{IDENT}); ratified=(?P<ratified>\d{{4}}-\d{{2}}-\d{{2}})$"
    )
    WAIVER_POLICY_LITERAL = "AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>"

`IDENT` は `:23` を再利用。`WAIVER_POLICY_LITERAL` は W-1(b) の fence 本文と逐語一致させ、exactly-once メタテストの対象にする。

**(b) dataclass** — `CorrectionAudit` (`:91-106`) の直後に同型で追加。

    @dataclass(frozen=True)
    class WaiverAudit:
        raw_values: tuple[str, ...]
        parsed_values: tuple[str, ...]
        final_values: tuple[str, ...]
        reason: str | None
        ratified: str | None
        findings: tuple[str, ...]

        @property
        def candidate_count(self) -> int: return len(self.raw_values)
        @property
        def exact(self) -> bool: return self.candidate_count == 1 and not self.findings

`ForwardCorrected` (`:116-119`) の隣に `ImplementationWaived(commit: str, reason: str, ratified: str)` を追加。

**(c) `_waiver_audit(label, message) -> WaiverAudit`** — `_correction_audit` (`:237-287`) の直後。作法は `_correction_audit` を踏襲。

- `matches = tuple(RAW_AI_AGENT_WAIVER.finditer(message))`。空なら空 audit を即返す (**canonical parser を呼ばない** — `:239-241` と同じ遅延。専用テストで固定)。
- 物理 1 行性: `len(raw_values) != 1` → 「raw candidate cardinality 違反」。
- 文法: 各 raw value が `" " + payload` の形で `WAIVER_VALUE.fullmatch(payload)` を満たすこと。
  `_correction_audit:258` と同じく先頭 1 空白を要求し、trailer 継続行 (folded line) を弾く。
- canonical: `_parsed_trailers(message).get(WAIVER_KEY.casefold(), [])` が exact 1 かつ文法一致。
- final block: `_parsed_final_trailers(message)` から取り、(i) `len(final_values) == 1`、
  (ii) 同 block の `AI-Agent` に `AGENT_VALUE.fullmatch` が成立し `role == "author"` の行が 1 本以上あること (P1)。
- `reason` / `ratified` は canonical 値が exact なときだけ設定する。
- **`_correction_audit` から踏襲しないもの**: incident 固定値との逐語一致 (`:258`, `:267`, `:276`)。
  waiver は payload が可変なので固定値照合の代わりに `WAIVER_VALUE` 文法照合を置く。この 1 点が唯一の作法差でありコメントで明示する。

**(d) `validate_implementation_author` の免除** — `:414-437`。

- signature を `(label, message, paths, *, waived: bool = False)` にする (既定 False。既存 4 呼出は無改修で通る)。
- `:431` の codex author 発見 `return []` の直後、`:432` の `sample = ...` の直前に `if waived: return []` を挿入。
  → **免除は「codex author が居ない」と判定した後にだけ効く**。codex author が居る commit で waiver を付けても受理集合は 1 bit も動かない。

**(e) history 経路** — `_normal_commit_audit` (`:556-589`)。`:577-583` の実装面ブロックを置換。

    waiver = WaiverAudit((), (), (), None, None, ())
    if (
        implementation_epoch is not None
        and ancestry.is_descendant(implementation_epoch, commit)   # D で置換
    ):
        waiver = _waiver_audit(label, message)
        findings.extend(waiver.findings)
        findings.extend(validate_implementation_author(
            label, message, _commit_paths(commit), waived=waiver.exact,
        ))

- **非遡及**: waiver の形式検査も免除も `implementation_epoch` の子孫でだけ動く。D95 決定 3 と整合。
- `CommitAudit` (`:108-113`) に `waiver: WaiverAudit` フィールドを追加。

**(f) `_audit_history` の戻り値** — `:592-675`。`HistoryAudit` dataclass
(`findings`, `corrected`, `waived`) にする。`waived` は findings 収集ループと同じ入力順で構築。
実装は単に `if a.waiver.exact` とし、「実装面 path が無い commit の waiver も件数に数える」ことを D105 に明記する
(数え漏らしより過大申告のほうが安全側)。
**waiver は forward correction の受理集合を広げない**: `:657-666` の `suppressed_missing` / `corrected` 判定に
`waiver` を一切参照させない。専用テストで固定する。

**(g) `--message-file` 経路** — `main()` `:765-782`。`:772-774` を置換し、
`waived=waiver.exact` を渡す。`findings = [*base, *scoped, *cab, *waiver.findings, *implementation]`。
message-file では epoch 判定をしない (現行の `validate_implementation_author` も無条件適用なので一貫する)。

**(h) 免除件数の stdout 出力** — `main()` `:791` の `if findings:` の**直前**。

    for record in waived:
        print(
            "check_ai_provenance: implementation-author-waived "
            f"commit={record.commit} reason={record.reason} "
            f"ratified={record.ratified}"
        )
    if waived:
        print(f"check_ai_provenance: implementation-author-waived={len(waived)}")

`findings` があっても (rc=1) 免除は必ず表示される。`waived` が空なら 1 行も出さないので、
既存の `captured.out` 逐語一致テスト (`:2106`, `:2124`) は無傷。

**(i) 起点コミット問題 (chicken-and-egg) の解消**

`_audit_history` は**現在の checker で全履歴を再判定する**ので、waiver 実装を入れた commit 自身が
waiver trailer を持っていても受理される。commit 時の `--message-file` preflight も staged/working tree の
新 checker が走る。よって **W の commit を本 wave の最初の実装 commit にすれば、それ自身から waiver で成立する**。

### W-4. 新規テスト (すべて `orchestrator/tests/test_check_ai_provenance.py`)

| nodeid | 検査 vector |
|---|---|
| `test_waiver_literal_matches_production_and_repo_policy_exactly_once` | `WAIVER_POLICY_LITERAL` の逐語、`policy.count(...) == 1`、かつ **既存 needle の count 不変**を同 node で再確認 |
| `test_waiver_exact_line_exempts_implementation_author_gate` | `waived=True` で `[]`、`waived=False` は従来 finding |
| `test_waiver_requires_own_role_author_ai_agent_line` | 同 block の `AI-Agent` が `role=reviewer` のみ → `exact` False + 専用 finding |
| `test_waiver_boundary_rejects_malformed_and_out_of_block[case]` | 2 行、継続行 (folded)、body 内配置 + 正常 1 行、`reason=` 大文字、`ratified=2026-7-31`、`ratified` 欠落、`;` 区切りの空白違い、divider 越え |
| `test_waiver_parser_is_lazy_without_raw_candidate` | `_parsed_trailers` を例外注入し、waiver 無し message で空 audit |
| `test_waiver_does_not_widen_forward_correction_acceptance` | correction 受理条件が変わらないこと |
| `test_waiver_is_nonretroactive_before_implementation_policy_epoch` | epoch 前は findings に出ない / epoch 後は出る |
| `test_waiver_count_is_reported_on_stdout_on_both_green_and_red` | 免除 1 件 + 別 commit に finding → rc=1 かつ stdout に `implementation-author-waived=1` |
| `test_waiver_message_file_gate_exempts_staged_implementation_paths` | staged-path テストの waiver 版 |

## A — `dispatch_compute.py` の request 一般化

### A-1. `pytest_args` 固定箇所の全列挙

| 行 | 現況 | 変更 |
|---|---|---|
| `:39-44` `_REQUEST_ENV_ALLOWLIST` | pytest 専用 4 変数 | task 別 dict へ |
| `:266-280` `_interpreter_probe_source()` | 引数なし。`pytest`/`xdist`/`packaging` を無条件 import | `_interpreter_probe_source(task: str = "tests")`。task の `probe_imports` だけ |
| `:289-360` `_job_script(...)` | task 非依存 | **変更不要** |
| `:376-440` `_job_run()` | `:388-390` 無条件 import、`:394` `request["pytest_args"]`、`:416` `tools/run_tests.py` 固定 | task 解決 → 該当 import のみ → `request["args"]` → `spec.child_script` |
| `:718-735` `_dispatch_impl` signature | `pytest_args` | `args, *, task: str = "tests"` |
| `:759-763` request_env 構築 | `_REQUEST_ENV_ALLOWLIST` 直参照 | `spec.env_allowlist` |
| `:780-793` receipt `request` | `"pytest_args"` (`:789`) | `"task"` + `"args"`、`schema_version` を `pegasus-dispatch-receipt/v2` へ |
| `:797-802` `request.json` | `pegasus-dispatch-request/v1` | `/v2` + `"task"` + `"args"` |
| `:803` probe 書き出し | `_interpreter_probe_source()` | `_interpreter_probe_source(task)` |
| `:1166-1183` `dispatch()` signature | `pytest_args` | `args, *, task: str = "tests"` |
| `:1232-1240` setup receipt | `{"pytest_args": ...}` | `{"task": ..., "args": ...}` + `receipt/v2` |
| `:1284` argparse | `pytest_args` positional | `--task` (choices) + positional を `args` へ改名 |

### A-2. task enum の設計 (P3)

`:44` の直後に `_TaskSpec` frozen dataclass (`child_script`, `env_allowlist`, `probe_imports`) と
`TASKS = {"tests": ..., "provenance": ...}`、`DEFAULT_TASK = "tests"` を置く。

- `tests`: `("tools", "run_tests.py")` / 既存 4 変数 / `("pytest", "xdist", "packaging")`
- `provenance`: `("tools", "check_ai_provenance.py")` / **空 allowlist** / `()`
  (checker は stdlib + git だけで動き、`GIT_*` は `_canonical_trailer_env` が隔離するので親の環境値は不要)
- 既存の `_REQUEST_ENV_ALLOWLIST` は削除し `TASKS["tests"].env_allowlist` へ移す。
  既存テストは `request["environment"]` の値だけを見るので無改修。
- **不正 task の fail-closed 二層**: 親は `_dispatch_impl` 冒頭で `ValueError` → setup receipt + rc=16。
  子は `_job_run` で照合し `DispatchError` → `stage="bootstrap"` / rc=16。argparse は `choices=tuple(TASKS)`。

### A-3. `_job_run` の書き換え (`:376-440`)

`schema_version != "pegasus-dispatch-request/v2"` を拒否し、`task` を `TASKS` に照合、
`spec.probe_imports` だけを `__import__`、`repo_root.joinpath(*spec.child_script)` を起動する。

- `:386-387` の `sys.version_info < (3, 10)` 検査は**そのまま残す** (M5 二層冗長 gate が固定)。
  ただし同テストの fixture request JSON (`:426-431`) は `pytest_args` / `v1` なので
  **`/v2` + `task` + `args` へ更新が要る** (D96 の同一変更単位更新)。
- `:396` の型検査メッセージを `args は string list でなければなりません` へ。

### A-4. 後方互換

- **`tools/run_tests.py` (唯一の production caller)**: `:829-835` `_default_dispatch` の呼出に `task="tests"` を明示追加するだけ。
  **`main()` (`:938-949`) の `dispatch_fn(args, environ=environ)` seam は変えない** —
  既存 fake が `def dispatch(args, *, environ)` 署名なので `task=` を通すと 4 テストが壊れる。
- `hooks/guard_bash.py:163` の sanctioned path は不変。`_job_script` (`:289-360`) も不変
  (ただし `:329-332` が `_interpreter_probe_source()` を無引数で呼ぶので**既定引数が必須**)。

### A-5. 新規テスト (`orchestrator/tests/test_pegasus_dispatch_compute.py`)

| nodeid | 検査 vector |
|---|---|
| `test_task_kind_enum_is_closed_and_unknown_task_is_setup_infra_rc` | `set(TASKS) == {"tests","provenance"}`、未知 task で rc=16 + setup receipt、scheduler 未呼出 |
| `test_provenance_task_binds_child_script_and_empty_env_allowlist` | request.json が `/v2` + `task=provenance` + `environment == {}`。`PYTEST_ADDOPTS` を environ に入れても出ない |
| `test_provenance_probe_omits_pytest_and_xdist_imports` | probe に `import pytest`/`xdist` が無く、version reject が在る |
| `test_job_run_rejects_unknown_request_schema_version_and_task` | v1 schema / 未知 task で `INFRA_RC`、`stage == "bootstrap"` |
| `test_job_run_launches_task_specific_child_script[tests\|provenance]` | argv[1] が `run_tests.py` / `check_ai_provenance.py` |
| `test_tests_task_remains_default_and_receipt_records_task` | 既定が `tests`、receipt に task、`receipt/v2` |

## B — docs 編集の挿入位置 (親が書く)

### B-1. `docs/pegasus-runbook.md` §7

1. **`:256-258`** の重い処理列挙へ `provenance 履歴監査 (tools/check_ai_provenance.py)` を追加。
2. **`:262-263`** の「ログインノードに残してよいのは編集・静的検査・docs 検査・スケジューラ操作だけ」を書き換える。
   ここが worklog `:546-547` の「親が過大解釈した」当該文である。`--message-file` の commit 前 preflight を明示的に許し、
   **履歴監査は「静的検査」ではない**と書く (1 回で git subprocess 約 3000 本・130〜150 秒)。
3. **`:267-273`** の強制の層 3 bullet: 一次強制へ checker の自動 dispatch (`--message-file` は免除)、
   二次防壁へ sanctioned exact path と「hook が閉じるのは綴り差だけ」を追記。
4. **`:275` 以降の実測ブロック直後**に実測 1 段落 (request `874712`、bnode041、596 commit、
   130〜150 秒 → 25.24 秒 → 4.58 秒、全 arm で findings と forward-correction が baseline と完全一致)。

### B-2. `docs/pegasus-runbook.md` §8

- **`:374-375`** の bullet 列挙末尾へ `provenance 履歴監査 (§7)` を追加。
- **`:376` の直前**へ新 bullet: 自動 dispatch の receipt の所在と「`rc=16` は dispatch の infra 失敗であり監査結果ではない」。

### B-3. `AGENTS.md`

- **`:28`** の直後に「Pegasus ログインノードでは自動 dispatch されるのでこの行を打つこと自体は禁止されない (`rc=16` は監査結果ではない)」。
- **`:30-31`** の列挙へ `provenance 履歴監査` を追加。
- **`:32`** の直後に「`check_ai_provenance.py` の履歴監査は静的読み取りではない (git subprocess 約 3000 本)」。
- `AGENTS.md` は `LIVING_DOCS` (`tools/check_docs.py:32`)。可変状態の再掲と行番号参照を持ち込まない。予算表の対象外。

### B-4. 任意

`hooks/README.md` は現状 `run_tests` / sanctioned / 重い処理を一言も含まない (grep 実測 0 hit)。
guard_bash の Pegasus 層自体が未記載なので C の追加は**新たな不整合を作らない**。書くなら sanctioned path 一覧節を新設。**親所有**。

## C — fail-closed 強制

### C-0. 2 層の責務分界 (D105 と runbook §7 に逐語で書く)

| 層 | 実体 | 何を保証するか | 何を保証しないか |
|---|---|---|---|
| **第一層 (checker 自身)** | `tools/check_ai_provenance.py` の `main()` | **sanctioned entry point を通る全経路** — Claude Bash、Codex subprocess、ユーザー端末、IDE、cron、`task_run_check.py provenance-check`。LOGIN なら計算ノードへ投げ、SUSPECT なら rc=16 で止まる | checker を経由しない同等処理 (`python3 -c` で module を import する等) |
| **第二層 (hook)** | `hooks/guard_bash.py` の `decide()` | **Claude の Bash 面だけ**で、sanctioned exact path 以外の綴りを拒否する | Codex subprocess (hook 未配線)、script file 越し、変数展開、`eval`、`python3 -c`、ユーザー端末 |

D103 決定 5 と同じ書きぶりで「sanctioned 経路では機械強制し、それ以外は規律で塞ぐ」に主張を狭める。
**第二層が新規に閉じるのは「綴り差」だけであり、第一層が入った時点で `python3 tools/check_ai_provenance.py` は
hook が許可すべき正規経路になる** — この反転を明示しないと実装子が hook で拒否してしまう。

### C-1. 手本 = `tools/run_tests.py` の構造

- site 判定の解決点: `:927` `resolved_site = site_policy.current_site() if site is None else site`。
  seam は `main(argv=None, *, site=None, dispatch_fn=None)` (`:910-915`)。
- 免除の閉集合: `:111-114` `_PEGASUS_DISPATCH_EXEMPT_FLAGS`、判定は `:381-396`。
- SUSPECT = 拒否: `:929-937`、`heavy_work_refusal` を stderr、`return _PEGASUS_DISPATCH_RC` (=16, `:110`)。
- LOGIN = 自動 dispatch: `:938-949`。`_dispatch_environment()` (`:816-823`) → `_invoke_dispatch` (`:838-855`) が
  想定外例外も rc=16 へ一義化 → 子 rc をそのまま返す。
- 遅延 import: `:829`。repo root の sys.path bootstrap: `:46-51`。

### C-2. `tools/check_ai_provenance.py` への同型移植 (U1)

- **(a)** `:20` の `REPO` 直後に `sys.path` 挿入 + `from orchestrator.campaign import site_policy`。
  既存テスト `:13` の `sys.path.insert(0, str(REPO / "tools"))` と衝突しない。
- **(b)** `:24` の隣に `PEGASUS_DISPATCH_RC = 16` (`run_tests.py:110` と同値。meta-test で固定)。
- **(c)** `main()` `:751` を `(argv=None, *, site=None, dispatch_fn=None)` へ。
  `values = list(sys.argv[1:] if argv is None else argv)` を **parse の前に**取る (dispatch 時に子へ渡す argv になる)。
- **(d)** `:759` と `:761` の間に site gate を挿入。**履歴監査だけが重い (唯一の免除は `--message-file`)**。
  SUSPECT → `heavy_work_refusal` + rc=16。LOGIN → `_invoke_dispatch`。
- **(e)** `main()` の直前に `_default_dispatch(argv)` (`dispatch_compute.dispatch(argv, task="provenance", repo_root=REPO)`) と
  `_invoke_dispatch(dispatch_fn, argv)` を `run_tests.py:826-855` と同型で置く。
- **(f) 意図的に移植しない 3 点**: (1) task_run 台帳記録 (`task_run_check.py:17-19,43-47` が既に `provenance-check` として記録、二重計上になる)、
  (2) `environ=` の受け渡し (allowlist が空)、(3) env escape hatch (D103 却下項目。site 上書きは keyword-only の `site=` だけ)。
- **(g) 無ループの根拠**: 計算ノードでは `site_policy.classify_site` が `bnode\d+` を `PEGASUS_COMPUTE` にするので
  `refuses_heavy_work` が False。加えて `_job_run:404-405` が `bnode` hostname を独立に assert する二層。
- **(h)** 既存 100 超のテストへの影響なし (`OTHER` / `PEGASUS_COMPUTE` では dispatch しない)。
  ログインノードで直接 pytest を打った場合だけ大量 dispatch が起きるが、それは `run_tests.py:938-949` が既に禁じている経路。

### C-3. `hooks/guard_bash.py` (U2)

1. **`:161-167` `_SANCTIONED_PATHS` に `"tools/check_ai_provenance.py"` を追加** (第一層を有効にする前提)。
2. **`:178` 直後**に `_PROVENANCE_SCRIPT_BASENAME` と `_PROVENANCE_EXEMPT_FLAGS = {"--message-file", "--help", "-h"}`。
3. **`_heavy_segment_violation` (`:497-552`) の `:505-507`** の直後に、basename 一致 かつ 免除 flag 無しなら
   「非 sanctioned provenance 履歴監査実行体」を返す分岐を挿入。到達条件は `_is_sanctioned` が False の綴り
   (repo 外 copy、cwd 相対、`~/…`)。sanctioned exact path と `python3 -m tools.check_ai_provenance` は `:502` で先に許可される。
4. `decide()` (`:791-800`) は無改修。

### C-4. 新規テスト

**`orchestrator/tests/test_check_ai_provenance.py` (U1)**

| nodeid | 検査 vector |
|---|---|
| `test_login_history_audit_dispatches_to_compute_and_returns_child_rc` | fake の rc を返し `_audit_history` が呼ばれない、fake が受け取る argv が逐語一致 |
| `test_login_message_file_is_dispatch_exempt` | `--message-file` は dispatch せず通常 rc |
| `test_suspect_history_audit_refuses_with_infra_rc_without_dispatch` | rc=16、stderr、dispatch_fn 未呼出 |
| `test_compute_and_other_sites_audit_locally` | `PEGASUS_COMPUTE` / `OTHER` で未呼出 |
| `test_dispatch_exception_is_folded_into_infra_rc` | `OSError` → rc=16 |
| `test_provenance_dispatch_rc_matches_run_tests_contract` | `PEGASUS_DISPATCH_RC == 16` かつ `run_tests._PEGASUS_DISPATCH_RC` と一致 |

**`orchestrator/tests/test_hooks.py` (U2)**

| nodeid | 検査 vector |
|---|---|
| `test_bash_login_sanctioned_entries_are_exact` (`:743` 拡張) | `python3 tools/check_ai_provenance.py`、`./tools/...`、`-m tools.check_ai_provenance` を許可側へ |
| `test_bash_login_blocks_nonsanctioned_provenance_entrypoints` | `/tmp/copy/...`、cwd 相対、`bash -lc '... ../...'` を拒否。同綴り + `--help` / `--message-file` は許可 |
| `test_bash_compute_allows_provenance_forms` | `PEGASUS_COMPUTE` で全形許可 |

## D — `_audit_history` の並列化と祖先 bitset

### D-1. 祖先集合の構築 (`_audit_history:592` の直前に新設)

`AUDIT_WORKERS = 16` (module 定数。site 由来にしない = P5)。

    @dataclass(frozen=True)
    class _Ancestry:
        index: dict[str, int]
        bits: tuple[int, ...]          # bits[i] = i の祖先集合 (自身を含む) の bitset
        cab_policy_mask: int

        def is_descendant(self, ancestor: str, commit: str) -> bool:
            i = self.index.get(commit)
            j = self.index.get(ancestor)
            if i is None or j is None:
                return False
            return bool(self.bits[i] >> j & 1)

        def has_cab_policy(self, commit: str) -> bool:
            i = self.index.get(commit)
            return False if i is None else bool(self.bits[i] & self.cab_policy_mask)

構築 `_build_ancestry(commits)`:

    raw = _git("rev-list", "--topo-order", "--parents", "--stdin",
               input_text="".join(f"{c}\n" for c in commits))
    rows = [line.split() for line in raw.splitlines()]
    index = {row[0]: n for n, row in enumerate(reversed(rows))}
    bits = [0] * len(rows)
    for row in reversed(rows):                    # parent が必ず先に確定する順
        i = index[row[0]]
        acc = 1 << i
        for parent in row[1:]:
            j = index.get(parent)                 # shallow/graft 境界は None
            if j is not None:
                acc |= bits[j]
        bits[i] = acc
    # tips = 選択集合のうち他の要素の祖先になっていないもの
    policy_hits = _git(
        "log", "--full-history", "--no-renames", "--format=%H",
        "-S", CO_AUTHORED_BY_POLICY_NEEDLE, *tips, "--", POLICY_PATH,
    ).splitlines()
    mask = OR of (1 << index[sha]) for sha in policy_hits if sha in index

**選んだ構築方法と等価条件の根拠**

- **`git rev-list --parents` を選び `--ancestry-path` は使わない。** `--ancestry-path` は「2 端点の間の経路上」に絞る演算であり、
  `merge-base --is-ancestor` の到達可能性と意味が違う。必要なのは選択集合の**祖先閉包全体**。
- **`--topo-order` が必須。** 既定は commit-date 順で位相順の保証がなく、逆順走査で親が未確定になりうる。
- **`--stdin`** は argv 長を選択集合サイズに依存させないため。
- **反射性**: `git merge-base --is-ancestor A A` は rc=0 (真)。`acc = 1 << i` で自身を含めて一致させる。
- **index 外の扱い**: 閉包に無い ancestor はいかなる選択 commit の祖先でもありえない → False。
  separate lineage テスト (`:772-803`) の現行 `merge-base` の False と一致。
- **pickaxe を畳む正確な等価条件**: 現行は commit ごとに `log --full-history --no-renames -S NEEDLE <commit> -- POLICY_PATH` が非空か。
  `--full-history` は履歴簡約を無効化するので**走査集合は `ancestors(commit)` そのもの**であり、`-S` は各 commit を親との diff で
  独立に判定する **tip 非依存の filter**。したがってヒット集合 = `P ∩ ancestors(commit)` (`P` = repo 全体のヒット集合)。
  tips 群から 1 回歩けば `P ∩ closure` が得られ、`bits[commit] & mask != 0` が元の非空判定と同値になる。
  merge commit は `-m`/`-c` 無しで diff されないが、これも tip 非依存なので両側で同じ扱い。
- **argv 前置の保存**: 畳んだ呼出は `("log","--full-history","--no-renames","--format=%H","-S",NEEDLE,*tips,"--",POLICY_PATH)` であり、
  `test_cab_policy_git_error_fails_closed_with_rc2` の intercept 条件 (`args[:4]` と `NEEDLE in args`) を両方満たす。git 障害は rc=2 のまま。
- **メモリ**: 948 commit で 948 個の 948-bit int ≈ 114 KB。insight §11 の「数百 KB」と一致。

### D-2. `_has_co_authored_by_policy` / `_is_descendant` の扱い

- **`:370-376` と `:379-395` は削除せず残す。** (i) 既存テスト 4 箇所が直接呼ぶ、(ii) bitset の等価性を検証する oracle になる、
  (iii) `_message_file_correction_findings:726` は選択集合を持たないので `merge-base` のまま使う。
- **置換するのは 3 箇所だけ**: `:565` (cab)、`:573` (scope epoch)、`:579` (implementation epoch)。
  commit あたり git subprocess 3 本 × 596 = 1788 本が消える。
- **`:634` の forward-correction `_is_descendant` は据え置く**。1 run につき最大 1 呼出。

### D-3. `_normal_commit_audit` の signature (`:556-561`)

`ancestry: _Ancestry | None = None` を追加。`None` のときは従来どおり `_has_co_authored_by_policy` / `_is_descendant` を呼ぶ。
これで既存の直接呼出 (`:1249-1253`) が無改修で通り、同時に **「逐次 oracle 実装が production に残る」**ので等価性テストが自己参照にならない。

### D-4. thread pool (`_audit_history:598-605`)

`ThreadPoolExecutor(max_workers=max(1, min(AUDIT_WORKERS, len(commits))))` で `pool.map(...)` を `list()` 消費。

| 論点 | 保証 |
|---|---|
| **順序安定性** | `Executor.map` は**入力順**で結果を返す。`audits` の順序 = 現行 list comprehension と同一。findings list が逐語一致する |
| **例外伝播** | `list()` 消費で**入力順で最初の例外**が送出される。現行の逐次実装も入力順の最初で止まるので `main():787-789` が受ける例外の同一性が保たれる。`parser_calls == 1` を assert するテストは 1 commit range なので並列でも 1 |
| **`with` 抜けの待機** | 例外時 `__exit__` が `shutdown(wait=True)`。監査は数秒なので許容。`cancel_futures` は 3.9+ 依存を避け使わない |
| **スレッド安全性** | (a) `_git` は `subprocess.run` のみ、`cwd=REPO` は読み取り専用。(b) `_isolated_parsed_trailers:157-160` は呼出ごとに専用 `TemporaryDirectory`。(c) `_canonical_trailer_env:139` の `os.environ.items()` は読み取りのみ。(d) `os.chdir` を使わない。(e) frozen dataclass を返し共有可変状態を持たない |
| **`TRAILER_PARSE_TEMP_ROOT`** (`:57`) | **読み取り専用のまま扱う。** 全 worker が同じ値を読み、`TemporaryDirectory(dir=...)` が atomic に一意な子 dir を作る。テストは pool 起動**前**に monkeypatch する。**worker 内でこの global を書き換える実装を作ってはならない** |
| **並列度** | `AUDIT_WORKERS = 16` の module 定数。`site_policy` を参照しない。テストは monkeypatch で 1 と 16 を切り替える |

### D-5. 新規テスト

| nodeid | 検査 vector |
|---|---|
| `test_audit_history_is_identical_across_worker_counts_and_ancestry` | 合成 repo (root 2、merge 2、correction 1、CAB 違反 1、implementation path 有無、scope 複数行、約 30 commit) を 1/2/16 並列 + 逐次 oracle の 4 arm で `findings` (順序込み)・`corrected`・`waived` が完全一致 |
| `test_ancestry_bitset_matches_merge_base_oracle_for_every_pair` | 全 (ancestor, commit) 対で `_Ancestry.is_descendant == _is_descendant`。自己反射・別系統・root を含む |
| `test_ancestry_pickaxe_mask_matches_per_commit_oracle` | 全 commit で `has_cab_policy == _has_co_authored_by_policy`。needle 0→2→1、rename in/out、merge が policy を保持/破棄 の 3 状況 |
| `test_audit_history_propagates_first_exception_in_input_order` | 特定 commit で `RuntimeError` → 常に入力順最初のメッセージ、rc=2 |
| `test_audit_workers_is_fixed_and_not_site_derived` | `AUDIT_WORKERS == 16`、module ソースに `site_policy.default_test_jobs` / `available_cpus` が現れない |
| `test_forward_correction_ancestry_still_uses_merge_base` | `merge-base --is-ancestor` が correction 経路で**呼ばれる**ことを確認 (`:2128` の fail-closed が空洞化していない証拠) |

**既存テストの必須更新 (D96)**: `:1558-1565` を `HistoryAudit` へ追随 (2 行の unpack → 属性参照)。

### D-6. wave レベルの「完全一致」受入 (段 7)

計算ノードで 1 job だけ流す。
1. `git show <wave 開始点>:tools/check_ai_provenance.py > $TMP/baseline_checker.py`
2. baseline と現行を同一 range で走らせ stdout/stderr を byte 比較 (waiver の新出力行だけが差分として許される — 差分行の集合を事前宣言)
3. wall を両方記録し insight §11 の 25.24 → 4.58 秒に整合するか確認する

この 3 手順を `--task provenance` の dispatch で実行することが、**A・C・D の統合動作証拠**を同時に取ることになる。

## 実装順序と依存

### owner 分割の修正 (brief の U1/U2 は素集合でない)

| owner | 所有ファイル | 担当 |
|---|---|---|
| **U1 (checker)** | `tools/check_ai_provenance.py`、`orchestrator/tests/test_check_ai_provenance.py` | **W-3/W-4 + C-2/C-4(前半) + D 全部** |
| **U2 (dispatch/hook)** | `tools/pegasus/dispatch_compute.py`、`orchestrator/tests/test_pegasus_dispatch_compute.py`、`hooks/guard_bash.py`、`orchestrator/tests/test_hooks.py`、`tools/run_tests.py` (`:831` の 1 行のみ) | **A 全部 + C-3/C-4(後半)** |
| **親 (docs)** | `docs/ai-provenance.md`、`docs/decisions.md`、`docs/pegasus-runbook.md`、`AGENTS.md`、`docs/worklog.md`、(任意) `hooks/README.md` | **W-1/W-2 + B 全部** |

**これで素集合になる。** 交差ファイルはゼロ。

### 依存と凍結すべき界面

1. **`dispatch()` 署名を段 4 brief で凍結する** —
   `dispatch_compute.dispatch(args: Sequence[str], *, task: str = "tests", repo_root=None, environ=None, ...) -> int`。
   U1 はこの署名に対してコードを書き、テストは `dispatch_fn` seam に fake を注入するので **U2 の完了を待たずに並行できる**。
2. **waiver の逐語文字列を段 4 brief で凍結する** — `AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>`。
   親 (docs) と U1 (production 定数) の両方が書き、exactly-once メタテストが結合を機械照合する。

### commit 順序

1. **W (親 docs 部 + U1 の W-3/W-4)** を**最初の実装 commit**にする。message 自身に `AI-Agent-Waiver` を載せ、
   staged の新 checker が `--message-file` で自己受理する。D105 も同 commit (D96)。docs 予算検査をここで通す。
2. **A + C-3 (U2)**。3. **C-2 (U1)**。4. **D (U1)**。5. **B (親、docs-only)**。6. worklog + phase チェック。

依存グラフ: W → (A ∥ C-2) → C-3 → D → B。

## リスクと未確定事項

1. **`docs/ai-provenance.md` の残 margin 13 bytes (高)。** 段 4 で waiver 本文を逐語凍結し、commit 前に `wc -c` を必須検査にする。**予算引き上げは提案しない** (T-127)。
2. **`git rev-list --topo-order --parents --stdin` の実挙動未検証 (中)。** read-only のため未実行。実装子は小 range で 1 回だけ形を確認すること。`--stdin` が使えない場合は argv に直接置く (948 SHA ≈ 39 KB、ARG_MAX 内)。
3. **shallow clone / graft 境界 (低)。** 本 repo は shallow でない。等価性テストは通常 clone のみ対象。
4. **`Executor.map` の shutdown 待ち (低)。**
5. **request/receipt schema bump の波及 (中)。** 既存 receipt を読む consumer は grep 上不在。queue 待ち中に repo が更新されると古い request を新 `_job_run` が読む可能性 — 現行も tree snapshot を持たない既知ギャップであり、新設の schema_version 検査は**この場合に fail-closed で止める**ので silent failure から明示失敗への格上げになる。
6. **checker rc に 16 が加わる (中)。** `task_run_check.py:64` は rc を素通しするので台帳に 16 が入る。「16 は監査結果ではない」を docs に書く。
7. **hook 第二層の marginal value が小さい (中、正直に書く)。** C-0 の表で射程を明記し「全経路の機械保証は主張しない」と結ぶ。
8. **waiver の乱用抑止が人手依存 (中)。** 機械上限を設けない以上、件数の stdout 公開と worklog 記録が唯一の抑止であることを D105 に明記する。
9. **ログインノードで直接 pytest を打つと ~100 の provenance テストが dispatch を試みる (低)。** `run_tests.py:938-949` が既に禁じている経路。残余リスクとして D105 に記録。
10. **未確定 (親の裁定が要る)**: (a) `hooks/README.md` を今回更新するか。(b) D を 1 本にまとめるか分けるか。(c) `provenance` task の walltime 既定 (実測 5 秒、queue 待ちが支配的なので据え置きを推奨)。

## 総括

- 5 単位すべてを file:line で起草した。(P1)〜(P5) は全面賛成、ただし **P2 の出力位置は `main():791` の前**でなければ
  rc=1 時に免除が沈黙する、**P4 の第二層は「非 sanctioned な綴りの拒否」だけが純増**で第一層導入後は hook が
  `check_ai_provenance.py` を**許可**側に回す必要がある、の 2 点を補正した。
- **最大のリスクは技術ではなく docs 予算である。** 8752/9000 bytes、余白 248、waiver 節は最小 458 bytes。
  `:107-123` の fence 統合 (93) と `:128-130` の圧縮 (130) で 223 bytes を捻出する。残 margin 13 bytes。
- **needle exactly-once は「waiver 本文に 2 つの needle 文字列を一字も含めない」ことで壊さない。**
- **D の完全一致は 4 つの機構で担保する**: `Executor.map` の入力順保証、逐次 oracle を production に残す、
  `--topo-order --parents` による正しい祖先閉包、計算ノードでの baseline byte 比較。
- **既存テスト 3 本が設計を縛る**: `:2128`、`:939`、`:1558`。いずれも回避策を本文に書いた。
- **brief の U1/U2 分割は素集合でない**。C を第一層=U1 / 第二層=U2 に割り直せば素集合になる。
