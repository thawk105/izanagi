単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/parent-brief.md — 親 brief (scope・不変条件)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/stage4-ruling.md — 段 4 裁定・plan v2・変異事前登録 (**この文書が plan-out.md より優先**)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/plan-out.md — 段 2 plan (hunk D1〜D7・T1〜T2、test 一覧、sidecar の key 集合)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/ruling-items-14-15.md — ユーザー裁定 (D2104 項 14・15) の逐語。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/D474.md — D474。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/t126_driver.py — 変更対象。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/tests/test_t126_qualification_driver.py — 変更対象 (test)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/artifacts.py — `create_json` / `load_json_strict` / `file_record` / capability の契約。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/collector.py — `_manifest` L228-246 (T5 の consumer)。読めなければ即停止。

## 依頼

[T-2683] を実装せよ。**編集してよい file は次の 2 つだけ** (所有 path):

- `orchestrator/qualification/t126_driver.py`
- `orchestrator/tests/test_t126_qualification_driver.py`

docs・他 file・`execution_guard.py` は編集しない。commit しない。git の状態変更 (add / stash / checkout / reset) をしない。

### 現行の受理・拒否挙動 (scope 前の事実、変えない)

- `_attest` (L449-475): 比較行が空、または 1 行でも `verdict != "pass"` なら `QualificationDriverError("attestation comparison contains a mismatch")`。probe 等の例外は `QualificationDriverError("attestation failed: <type>: <msg>")`。一致時は `status: "accepted"` の payload dict。
- `run()` 内 `attest` closure (L1191-1261): fork した子が `_attest` → `create_json(capability, "{prefix}/attestation/{stage}-{n}.json", payload)` → `os._exit(0)`、例外は `os._exit(RC_ATTESTATION)` (=31) で file を残さない。親は非ゼロ exit で `AttestationError("attestation child rejected")` を上げ、`run_series` が `fsm.reject("attestation", {"stage", "type", "message"})` を書く。
- **受理集合は変えない。** 不一致は依然 reject・rc=31、一致時は accepted payload の bytes 不変で sidecar を書かない。

### 実装 (stage4-ruling.md の plan v2 と plan-out.md の骨格に従う)

1. `AttestationMismatchError(QualificationDriverError)`: 属性 `comparisons`, `expected_profile_sha256`, `observed_profile_sha256`, `observed_profile_projection_schema`。message は現行の全文 `attestation comparison contains a mismatch` を維持。`_attest` の L465 条件式は変えず L466 の raise だけ置換。空 comparisons も同じ型 (`comparisons=[]`)。
2. module-level `_run_attestation_child(*, repo_root, contract, capability, relative, stage, round_index) -> int`: mismatch なら `Path(relative).with_suffix(".mismatch.json").as_posix()` へ `create_json` で診断を 1 つ書き `RC_ATTESTATION` を返す。診断の exact 9 keys と値は plan-out.md §1 のとおり (`schema_version = "t126-qualification-attestation-mismatch/v1"`, `status = "rejected"`, `comparisons` は全行を元の順序で無加工、`failed_fields` は verdict≠pass の field 名)。成功なら payload に stage/round_index を足して accepted path へ `create_json` し `RC_SUCCESS` を返す。全体を `except BaseException: return RC_ATTESTATION` で包む (診断の書込み失敗でも rc 不変、D474)。probe 例外等の非 mismatch 失敗では sidecar を書かない。
3. closure の子分岐を `os._exit(_run_attestation_child(...))` に置換 (`os._exit` は closure に残す)。fork・process group・timeout・親の wait は変えない。
4. module-level `_attestation_rejection_message(*, capability, relative, attempt_dir) -> str`: sidecar 不在なら `attestation child rejected`。実在すれば `load_json_strict` で読み `attestation child rejected; diagnostic=<attempt_dir 相対 path>; failed_fields=<json.dumps(list, ensure_ascii=True)>`。読取り不能・形不正なら `failed_fields=unavailable`。存在確認・読取りの例外を外へ出さない。受理判定に使わない。
5. closure の親側 L1242-1243 を `raise AttestationError(_attestation_rejection_message(capability=capability, relative=relative, attempt_dir=layout.attempt_dir))` に置換。timeout 分岐の message は変えない。`run_series`・`verify()`・`attestation_records`・`evidence_manifest` は非接触。
6. env 名の literal (`pegasus` 等) を driver に足さない。

### test (plan-out.md §5 の 10 本 + stage4-ruling.md の T3・T4・T5)

- 既存 `_attest_fixture` (L261) と `_fsm(tmp_path)` (L521) を再利用。stub は較正 loader と probe だけ (比較・parser・hash・`create_json`・`load_json_strict` は実物)。
- 正例 `test_t2683_mismatch_preserves_all_comparison_rows`: governor を `powersave` にし、実 `_attest` の typed 例外と属性、次に `_run_attestation_child` の rc=31・sidecar 1 個・accepted 不在・21 行中当該 1 行だけ非 pass・残り 20 行 pass・9 keys・両 hash・projection・`failed_fields == ["effective_clock.governor"]`。
- 負例 `test_t2683_match_preserves_accepted_bytes_without_sidecar`: 一致入力。期待 bytes は **旧契約 (現行の accepted payload 構成) から独立に組み立てた canonical JSON + 改行** と比較 (helper の出力をそのまま期待値にしない)。rc=0、`.mismatch.json` 不在、attestation dir に追加 file なし。pre-round / post-series を parametrize。
- 空 comparisons、書込み失敗 (`OSError` / `QualificationArtifactError` を parametrize、mismatch path だけ例外にする)、probe 失敗で sidecar なし、既存 sidecar の先置きで create-only 拒否かつ先置き bytes 不変、親 message 3 本 (names / legacy / unreadable を parametrize)、台帳契約 (`run_series` に実 helper を通す `attestation_fn`、pre-round / post-series を parametrize、evidence keys `stage/type/message` と外側 `reason/evidence_canonical_json/evidence_sha256` の exact 一致、rc=31・rejected)。
- **T3** `test_t2683_run_attest_closure_wires_child_helper_and_rejection_message`: `ast` で driver source を parse し、`run` 内の nested `attest` に (a) `os._exit(...)` の引数が `_run_attestation_child` の Call である箇所が 1 つ、(b) `raise AttestationError(...)` の引数が `_attestation_rejection_message` の Call である箇所が 1 つあることを固定 (同 file の `test_m10_driver_binds_prologue_observation_at_every_member_callsite` と同型)。
- **T4** `test_t2683_forked_child_writes_sidecar_visible_to_parent`: governor 不一致で `os.fork()`、子は `os._exit(_run_attestation_child(...))`、親は `os.waitpid` で `os.waitstatus_to_exitcode == 31`、sidecar 実在、`_attestation_rejection_message` が相対 path と `effective_clock.governor` を含む文字列を返す。子は例外で親の pytest を汚さないよう `try/except BaseException: os._exit(99)` で囲む。
- **T5** `test_t2683_mismatch_sidecar_is_listed_in_collector_closure`: 実 helper で sidecar を作った attempt_dir に対し `orchestrator.qualification.collector._manifest(layout.attempt_dir, exclude=set())` を呼び、`attestation/pre-round-1.mismatch.json` の record が含まれることを確認。
- 期待値に揮発 payload (working tree hash 等) を焼き込まない。fixture へ現行 hash を差し込んで緑にしない。既存 test の assertion を弱めない。

### 検査と報告

- 実走: `cd` 先は worktree root。`python3 -m pytest orchestrator/tests/test_t126_qualification_driver.py -q -p no:cacheprovider` を走らせ、緑には実走 nodeid・件数を併記する。sandbox 由来で走らない/赤になる node は「実装済み・未実走」または「sandbox 由来の疑い」と分類し、`closed` と申告しない。
- テスト新設の単位は、親の名指しを網羅と見なさず、test 名・fork・`ast` 利用に制約を課す meta-test (`orchestrator/tests/` で `test_t126_qualification_driver` や `os.fork` を grep) を自ら洗い出して走らせる。
- 完了報告に、所有外 caller (`_attest` / `AttestationError` / RC 定数の他 file 参照)、共有 fixture、consumer test (`test_t126_pegasus_tools.py`、`test_t126_qualification_artifacts.py`、`test_campaign.py`、`test_official_perf_closure.py`、`test_artifact_admission.py`) への波及可能性を静的に列挙する。
- 完了報告に、変異事前登録 M1〜M11・E1 の各位置を実装後の行番号で対応づける (anchor 表)。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: 変更 hunk 数、新規 test 数、実走結果 (passed/failed/未実走)、scope 逸脱の有無)。続けて `## 変更一覧` (file:line)、`## 実走`、`## 変異 anchor 表`、`## 波及可能性`、`## 未実走・懸念`。
