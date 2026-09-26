## 変更アンカー表

行番号は現行 worktree の変更起点。新設ファイルの行番号は作成時に固定する位置を示す。所有 path は単位間で重ねない。

| 所有 | file:line | 変更内容 | 依存 |
|---|---|---|---|
| A | `orchestrator/campaign/silo_policy_ir.py:24–125,172,237` | 既存 dataclass を正本に、閉じた JSON codec `parse_policy_ir` / `serialize_policy_ir` を追加する。未知 key、重複 key、型違反、範囲外を拒否し、最後に `validate_ir` を呼ぶ。 | 既存 IR 型と `validate_ir` |
| A | `orchestrator/tests/test_silo_policy_ir.py` 新設行 | codec の往復と全 node 種の負例。既存偵察の候補 ID や結果は fixture に入れない。 | A |
| B | `orchestrator/campaign/p3_s4_loop.py:737–875` | `silo-function-policy` marker だけ、構造検疫→effect gate→`check_policy_body` の構文検査・単独 TU compile を追加する。全 pass 後にのみ `write=True` を実行する。 | `axis_silo_function_policy.py:4–9`、既存 C 段検査器 |
| B | `orchestrator/campaign/diff_quarantine.py:41–49` | 方策専用の `POLICY_GRAMMAR`、`POLICY_COMPILE` subtype を追加する。 | B の reject 射影 |
| B | `orchestrator/campaign/projection_guard.py:28–56,291–363` | planner 不在の C++ / IR 専用契約を追加。既存契約の required/optional 集合は維持する。 | C の proposal loader |
| B | `orchestrator/critic/digest.py:924–957,1477–1585` | 方策 subtype の固定 rule id と検査段を WAL から critic 表示へ通す。候補由来の診断全文は表示しない。 | B の reject |
| B | `orchestrator/campaign/auditor_gate.py:29,54–94` | violation type 上限を 21 から 26 に広げる。verdict・digest の既存意味は維持。 | D の auditor 目録 |
| B | `orchestrator/tests/test_p3_s4_loop.py`、`test_projection_guard.py`、`test_auditor_gate.py:139–160` | marker 限定、検査順、subtype、閉じた schema、型 22–26 の受理と 27 の拒否。 | B |
| C | `orchestrator/campaign/p3_s4_loop_policy.py` 新設行、型 `p3_s4_loop_sort.py:103–116,179–278,285–332,358–439,439–524,524–655,659–806` | 軸定数、2 形の proposal、preview、auditor 照合、1 iteration、checkpoint、CLI。B-4・sort oracle・trigger wire は持ち込まない。 | A、B |
| C | `orchestrator/tests/test_p3_s4_loop_policy.py` 新設行、型 `test_p3_s4_loop_sort.py:203–215,577–787,881–960` | §7.4 の入口・schema・cfg・継続と、この軸の gate・firewall。 | C |
| C | `orchestrator/campaign/materializer_admission.py:103–107`、`orchestrator/tests/test_ccbench_spawn_sites.py:42,79,102,2940–2965` | 新 driver の登録・新たな process/build site が実際に生じた場合だけ台帳を exact に更新。既存診断 site の行番号 pin を差分に合わせて更新。 | C の実装後の AST 棚卸し |
| D | `.claude/agents/coder-v4-autonomous-policy.md`、`coder-v4-autonomous-policy-ir.md` 新設行 | fresh・tools `[]`、固定仕様と閉じた出力。戦略例や偵察結果は書かない。 | C の入力・出力契約 |
| D | `.claude/agents/auditor.md:68–73,88–91` | 型 22–26 とチェック項目を追加。型 17–21 の免除は sort IR と**機械生成 IR 候補**に限定し、LLM×C++ へ一般化しない。 | D2214、C の auditor 入力 |
| D | `orchestrator/codex_roles/manifest.json` の `roles`、`review_ledger.py:13,15,60,88,110,191`、`policy.py:30–85`、`spec.py:538–673`、`.codex/role-adapters/`、`tools/check_codex_agents.py:2,45–59`、`orchestrator/tests/test_codex_agents.py:138–207,552–612,1484–1497` | 2 role と auditor 改訂に登録簿を追随。詳細は P7。 | D の role 本文をレビュー後 |
| 親 | `docs/phase3-s9-policy-runbook.md` 新設行、型 `docs/phase3-s5-sort-runbook.md:14–187` | 実走前ゲート、planner なしの駆動、firewall、停止、限界。phase 完了チェックと記録は実装 commit に含める。 | A–D の確定 interface |

`axis_silo_function_policy.py`、`silo_policy_grammar.py`、`silo_policy_compile.py`、`silo_policy_coverage.py` は本計画では変更しない前提である。変更が必要になれば所有単位を明示して再配分する。設計上も骨格 patch、API header、pin の受理契約は固定されている（brief:15–20、段階 C:160–167）。

## interface

**A：IR codec。** `parse_policy_ir(document: object) -> PolicyIR` と `serialize_policy_ir(ir: PolicyIR) -> dict[str, object]`。parser は JSON object を受け、文字列から読む入口では `json.loads(..., object_pairs_hook=重複拒否)` を使う。root は `fields`、`after_abort`、`on_lock_conflict`、`on_commit` の完全一致。各式は `kind` 識別子を持つ tagged object とし、`Const{kind,type,value}`、`Reason{kind}`、`Attempt{kind}`、`StateRef{kind,index}`、二項 `{kind,left,right}`、`Select{kind,condition,yes,no}`、`Shift{kind,direction,value,amount}` を閉じる。hook は現行 dataclass の field 名に一致させる。`serialize_policy_ir` は `validate_ir` 後、JSON 値だけを返す。最終 identity は IR JSON でなく `render_policy(ir)` の C++ 本文の `source_digest` とする（`silo_policy_ir.py:24–125,172–228,237–317`、D2214:35–38）。

**B：検疫。** `quarantine(sub: str, implementation: str, marker_id: str=..., source_rel: str=..., write: bool=True, *, policy_compiler: str|None=None, policy_scratch_dir: str|None=None) -> tuple[DiffQuarantineResult,str,str,str]` とする。policy marker の場合だけ compiler と scratch を要求し、欠落・利用不能・timeout は pass にしない。構文拒否は `subtype="policy-grammar"`、`rule_id=PolicyDecision.rule_id`、compile 拒否は `subtype="policy-compile"`、固定 `rule_id="policy-tu.compile"` とする。いずれも `rejection_type="diff-quarantine"`、`diff_region`、`template_diff_id`、固定した `reason/evidence` を載せ、compiler 診断全文は載せない。既存 `record_diff_reject(...):982–1020` の WAL 経路を使う。

**B：proposal gate。** 新契約名は `CODER_CONTRACT_POLICY_CPP="policy-cpp"` と `CODER_CONTRACT_POLICY_IR="policy-ir"`。既存 `assert_closed_proposal_schema(document, *, require_auditor, require_coder_value, coder_contract=...)` にこの二値を追加し、この二値だけ top required を `{coder,auditor}`、optional を `{prior_critic_reverse}` にする。`planner` と `value` は未知 key として拒否する。IR 値は key closure 後に A の parser で検証する。既存 3 軸の契約分岐はそのまま残す（`projection_guard.py:28–56,291–363`）。

**C：coder 入力。** `make_policy_coder_input(*, contract_spec: str, baseline: dict, projection_path: Path, history_path: Path, critic_diagnosis: dict|None) -> dict[str, object]`。出力 key は必須 `{leakproof_context,policy_spec,baseline,recon_projection,self_history}`、診断がある時だけ `critic_diagnosis`。`recon_projection` は厳密に `{binary: bool, scope: str}`。`projection.json` の top は `{binary,scope,excluded}` の完全一致を検査し、`excluded` の値には触れず、出力しない。履歴各件は `{iteration,implementation,outcome,reject_code,verifier_digest,critic_diagnosis}` に閉じる。`justification` は別台帳にだけ書く。既存 K2 の兄弟 key の実体は `p3_s4_loop.py:1266–1311` の `k2_critic_diagnosis_from_bytes` / `k2_next_generation_inputs` と `:1314–1353` の payload 射影である。新軸には K2 knowledge 条件を流用せず、診断の固定 field と source hash の作法だけを使う。

**proposal JSON の完全 schema。** 形ごとに別契約を指定し、top は両形とも required `{coder,auditor}`、optional `{prior_critic_reverse}`、他は拒否。`prior_critic_reverse` は `bool|null` で、coder の自己申告からは採らず、実 critic 結果を親が与える。C++ の `coder` は required `{axis:"silo-function-policy",implementation:string}`、optional `{justification:string,confidence:"high"|"medium"|"low"}`。IR の `coder` は required `{axis:"silo-function-policy",ir:<A の閉じた object>}`、optional は同じ。両形とも `value`、`planner`、`strategy_summary` は不可。`auditor` は required `{verdict:"pass"|"reject"|"uncertain",diff_digest:非空の小文字 SHA-256}`、optional `{violations,nits,proposed_tests,uncertainty}` で、既存 `parse_auditor_dict` の各 list と verdict 整合規則を適用する（`auditor_gate.py:270–295`）。

**auditor digest の対象。** C++ 形は入力本文を検疫して得る、骨格適用後の `base_text` から `edited_text` への `working_diff` の UTF-8 bytes。IR 形は *parse→validate→render 後の C++ 本文*を同じ検疫に入れ、その `working_diff` の UTF-8 bytes。双方 `compute_diff_digest(working_diff)` と auditor の返却値を実走時に再照合する（`p3_s4_loop.py:727–735,737–875`、`auditor_gate.py:171–187`）。IR JSON 自体の hash や repo の HEAD diff ではない。

## P1〜P8 の判定

| 案 | 判定 | 根拠と修正 |
|---|---|---|
| P1 | **要修正** | `quarantine` の既存順序は構造→effect→軸文法（`p3_s4_loop.py:813–875`）。追加位置は適切。ただし `check_policy_body` は compiler/scratch 必須（`silo_policy_compile.py:114–117`）なので引数契約が要る。`prepare_policy` は直後に同じ検査を呼ぶ（`silo_policy_coverage.py:279–305`）。診断経路では同じ本文を二度 compile するため、当面は両方の pass を要求し、二度目の結果を既存診断 receipt に残す。失敗位置が前へ移ることを test に固定する。既存 3 marker には分岐しないので受理集合は不変。C/D の最終受理集合も同じ検査条件なら不変だが、診断文面・実行時間は変わる。`test_ccbench_spawn_sites.py:2940–2965` の build sink 行番号 pin は行移動で更新が必要。新 driver が直接 build/process を起動しない構成なら、新しい raw spawn site は増えない。 |
| P2 | **要修正** | `check_stop` は空 whiteboard なら `evaluated=[]` となり収束しない（`p3_s4_loop.py:1386–1398`）。iteration・walltime と、`reverse_recommendations` が閾値に達した場合だけ停止（`:1371–1406`）。`LoopState` は `whiteboard=[]` のまま、`start_wall`・`iteration`・reverse 回数だけを既存 `loop_state.json` に保存できる（`:1408–1450`）。履歴本文は WAL から再導出できない。reject WAL は digest と variant ID を保存するだけ（`:982–1020`）。campaign dir の `policy_history.jsonl` に本文と結果の自系列記録を追加し、`policy_justifications.jsonl` は coder 入力から隔離する。WAL は outcome/reject の照合元、history は本文の保存元として variant/iteration を照合する。critic の逆方向結果が無いなら reverse は 0 のままにし、予算だけで止める。 |
| P3 | **real** | IR dataclass と `validate_ir`、renderer は既存（`silo_policy_ir.py:24–125,172–317`）。codec を足せば IR JSON→同じ C++ admission へ接続できる。未知 key・重複 key・`bool` を整数として受ける型混同まで fail-closed にする。 |
| P4 | **要修正** | planner なしは D2214:39–43 と手順書 §3-E:187–207 に一致。ただし現行 `projection_guard` は planner を必須とする（`:28–33,291–331`）。新契約を明示選択した時だけ top 集合を切り替える。`prior_critic_reverse` を JSON に置く場合も、coder からの値を信用しない。 |
| P5 | **要修正** | `projection.json` の実 key 型は `{binary:bool,scope:str,excluded:...}`。P5 の入力 key/justification 不在だけでは、禁止情報が `scope` や履歴本文へ混ざる経路を否定できない。trusted producer の allowlist、参照 path の固定、`excluded` 非読取、履歴の自系列由来の照合を加える。字面 tripwire は追加しない。既存 policy も opaque string は検査しないと明記（`codex_roles/policy.py:1–11`）。 |
| P6 | **real** | B-5 動作点は `p2_2.py:54–57,74–77`、`p3_s4_loop.py:1873–1883` の `calibrated_perf("write-heavy")` から取る。1M/48/skew .9/rratio 5/extime 3/reps 5、`ycsb_max_ope` は同関数の `S2_FLAGS` 由来。`default_perf()` は 100k/4/1秒/2 rep なので使わない。`SEARCH_CONFIG_VERIFY_KEY=VERIFY_LEGACY_PLUS_PERFORMANCE` は `pipeline.py:170–175`、`loop.py:315–324`、CLI 前例 `p3_s4_loop.py:3749–3764`。 |
| P7 | **要修正** | 2 role の追加で `EXPECTED_ROLE_COUNT` は 14→16（`review_ledger.py:13`）。新 2 件の `SOURCE_FILE_SHA256`、`DESCRIPTION_SHA256`、`ROLE_MANIFEST_SHA256`、`SCHEMA_SHA256` 入出力、`ROLE_IO_CONTRACTS` が必要（`:15,60,88,110,191`）。auditor 本文改訂は同 ledger の auditor source pin、manifest entry を改訂するなら manifest pin、schema を変えるなら schema pin、adapter の期待 bytes に波及する。型 22–26 のため `auditor_gate.py:29` と `test_auditor_gate.py:139–160` の「22 拒否」pin を 27 拒否へ更新。`policy.py:30–85` の新 role 別 forbidden key token、manifest の `forbidden_key_tokens` を一致させる。`spec.py:538–673` は集合・枚数・各 hash を検査し、`test_codex_agents.py:138–207,552–612,1484–1497` に 16 件と新契約を固定。`tools/check_codex_agents.py:2,45–59` と `.codex/agents/README.md:1–14` の 14 件表記・JSON 例 parity 対象を更新する。manifest entry は手レビューで記述し、adapter JSON は `spec.render_adapter`（`:803`、`expected_adapters`:876）の期待 bytes を生成してレビュー後に反映する。`check_codex_agents.py --write` は拒否される（`:349–355`）。全 adapter は static/dormant のまま。 |
| P8 | **要修正** | 非 LLM 手書き 2 形での配線確認は有効。ただし「auditor 実 spawn」は D2214 の LLM 由来必須 gate を試すため、手書きでも既存登録 auditor を通す試験例として明記する。既存 `--no-build` fixture の自己生成 verdict は live auditor の証拠にならない（`p3_s4_loop_sort.py:832–838`）。実計算投入は D2243 項 1 の node 時間提示・事前確認が要る（`D2243-item1.md:11–13`）。 |

**build admission の選択。** `BuildProvenance.CODER_AUTHORED` は `build_admission.py:92–116`、CLI の `--allow-coder-derived-build` は `:444–468`。sort driver は `GeneratorId.BACKOFF_SWEEP` で `BuildRunContext` を作る（`p3_s4_loop_sort.py:385–390,735–748`）。新 driver も登録済み coder entrypoint と parser 発行 authority を使い、LLM×C++、LLM×IR、手書き live 候補を `CODER_AUTHORED` にする。`silo_policy_coverage._build_variant` は `NON_ADMISSIBLE` 診断経路（`materializer_admission.py:103–107`）なので流用しない。新 GeneratorId の追加は、この driver が generator receipt を発行しない限り不要。`HUMAN_REVIEWED` に分類しない。

## test と変異の事前登録候補

最小 test 名は提案名。各 test は正例と、単一の契約を壊す負例を持つ。

| test | 赤にする変更 |
|---|---|
| `test_policy_quarantine_gate_order_and_no_write` | effect より前に grammar を呼ぶ、または拒否本文を書き込む |
| `test_policy_grammar_reject_precedes_tu_and_auditor` | 構文拒否後に TU/auditor を呼ぶ |
| `test_policy_tu_reject_precedes_auditor_and_build` | grammar pass・TU fail を通す |
| `test_policy_reject_subtypes_roundtrip_wal_critic` | grammar/compile の subtype・rule id を落とす |
| `test_policy_proposal_cpp_and_ir_closed_schema` | planner/value/未知 key、auditor 欠落、未知 verdict、空 digest を許す |
| `test_policy_default_cfg_verify_axis_pin_perf` | legacy+performance、axis、`axis.PIN`、write-heavy のいずれかを変える |
| `test_policy_drive_stops_before_iteration_and_resumes_checkpoint` | 入口停止で iteration を消費する、または `loop_state.json` を無視する |
| `test_policy_ir_codec_roundtrip_and_fail_closed` | 未知 key、重複 key、bool/int 混同、範囲外を許す |
| `test_policy_firewall_projection_positive_negative` | 実 `projection.json` の binary/scope は通し、`excluded` を入力に混ぜるか他 file を開けば落とす |
| `test_policy_firewall_history_and_source_paths` | 自系列 `policy_history.jsonl` は通し、justification、段階 D の aggregate/initial/compare、禁止された小比較 path を入力源にすれば落とす |

P5 の test は恒真にならないよう、`make_policy_coder_input` が返した bytes と、差し替えた producer fixture の bytes を比較する。正例は実 projection の許可 field と自系列 1 件。負例は `excluded` への混入、`policy_justifications.jsonl` からの混入、禁止ディレクトリを読みに行く monkeypatch、履歴の他 campaign ID。段階 D の禁止 file を改変しても入力 bytes が同じ、という試験は「そもそも開かなかった」open 記録も確認する。

変異の事前登録候補は次の 8 本。変異を当てる前に、先行 gate を通る fixture かを確かめ、期待失敗 node の完全一致を記録する。

| 変異 | 壊す行・単一理由性 | 期待する赤 |
|---|---|---|
| M-E1 | 新 `quarantine` の `marker_id == axis.MARKER_ID` を常時偽。構造/effect pass、grammar fail 本文を使用 | `test_policy_grammar_reject_precedes_tu_and_auditor` |
| M-E2 | 新 grammar `accepted` 判定を pass 固定。grammar のみ拒否し TU が通る fixture を使用 | 同 test、`test_policy_quarantine_gate_order_and_no_write` |
| M-E3 | 新 compile `accepted/returncode` 判定を pass 固定。grammar pass、TU fail の本文を使用 | `test_policy_tu_reject_precedes_auditor_and_build` |
| M-E4 | 新 reject 射影の `POLICY_GRAMMAR` を `HOST_EFFECT` に変更。前段 grammar で止める | `test_policy_reject_subtypes_roundtrip_wal_critic` |
| M-E5 | IR parser の未知 key 拒否を削除。IR は他の型・範囲を満たす | `test_policy_ir_codec_roundtrip_and_fail_closed` |
| M-E6 | IR parser で `type(x) is int` を `isinstance(x,int)` に変更。`true` だけを index に使用 | 同 test |
| M-E7 | projection の `excluded` を coder 入力へ加える。履歴・auditor は正常 | `test_policy_firewall_projection_positive_negative` |
| M-E8 | 履歴射影へ `justification` を追加。WAL・本文・診断は正常 | `test_policy_firewall_history_and_source_paths` |

`test_ccbench_spawn_sites.py` の行番号 pin が変異に伴って赤になる場合、それは副次的な赤として区別する（段階 C 記録:129–130）。gate の非恒真性は上記の機能 test が担う。

## live 確認と見積りの材料

1 iteration の成功経路は、構造検疫・effect・grammar・単独 TU compile・auditor digest 照合の後、`run_campaign` が trace 有効 build と性能用 trace 無効 build を扱う。verify は legacy **1 rep** と、`performance_correctness_workload(perf)` の **5 rep**、計 6 trace/verifier 判定。bench は **5 rep**。build cache hit や preflight の追加作業があるため、実 build 起動回数・Elapse は job 記録から確認する（`pipeline.py:149–154,186–224,2225–2227`、`loop.py:315–324`）。拒否候補は後段へ進まない。

段階 C smoke は 5 case・793 秒、単純平均 **158.6 秒/case**（`t2857…/README.md:89–101`）。ただし smoke は性能構成 verify と bench が各 1 走であり、新 1 iteration は各 5 rep なので、この平均をそのまま単価にしない。見積りは「2 形 × 実測 job Elapse」を基礎に、compile、6 verify、5 bench、依存物準備、受入 test の時間を別に積む。図 1 枚当たりの node 時間とタスク合計を親が示し、2 node 時間以上なら投入前に確認する（D2243 項 1）。

計算ノード投入は `tools/pegasus/README.md:335–405` と既存 `tools/pegasus/p3_s4_loop_pegasus.sh` の **qsub job body** 方式を型にする。ただし同 script は `p3_s4_loop` 固定なので、新 driver 用 job body と契約 test を作るか、親の既存許可経路で同等の固定 argv・scratch・prebuild receipt・reservation 束縛を用意する。worktree path をそのまま同 job body へ渡す案は同文書の拒否条件に反する。E の静的計画では投入しない。実 role spawn は承認済み定義が fresh session に登録されてから行う。

## runbook 節立て

`docs/phase3-s5-sort-runbook.md:14–187` の 5 節を踏襲する。

- `## 0. 実走前ゲート`：fresh session に coder 2 role と auditor が見えること、single tenant、`policy.PIN` の pinned clean、test 緑、calibration、計算見積りと承認。
- `## 1. 1 iteration`：coder 入力を trusted 関数で作成→C++ または IR coder→IR は parse/render→`--preview-diff`→auditor spawn→proposal JSON→`--run-iteration`→WAL/履歴/critic digest。sort の planner 段 `(a)` を削り、両 coder 形を分岐として示す。
- `## 2. リーク制御`：projection の binary/scope、自系列履歴、justification の隔離、禁止 file の非読取、auditor への性能値非送付。
- `## 3. 停止と継承`：空 whiteboard の予算・reverse 判定、`loop_state.json` と `policy_history.jsonl`、F は別 session。
- `## 4. 既知の限界`：有限 trace の認証範囲、fairness は目視、verify/perf の分岐一致は保証しない、IR 部分空間と C++ 全空間を混同しない。設計判断は D2214 と設計正本を参照する。

## 未確定点 (親の裁定が要るもの)

1. **P1 の二重 compile を E では許容するか。** 私の推奨は許容し、`prepare_policy` の既存診断 receipt を維持する案。後で性能上の理由から一回化するなら、C/D 診断経路の変更として別に扱う。
2. **role 差分の承認。** `.claude/agents/` の 2 新設と auditor 改訂は D2214:43 と依頼逐語:9 の明示承認が必要。具体差分を D 単位が作り、レビュー可能な形で親が提示する。
3. **live 計算の投入承認。** 見積りを job Elapse で積んでから、D2243 項 1 の条件に従い親が確認する。現段階では実測単価が足りず、2 node 時間未満とは判定できない。

## 総括

- 実装順は A codec → B 検疫と schema → C driver → D role/登録簿 → 親 runbook。
- P1 は compiler/scratch の契約と `prepare_policy` の二重検査を明示すれば採用可能。
- planner なしでは whiteboard を空に保ち、既存 `LoopState` の予算・reverse 判定を使える。
- 履歴本文は WAL から復元できないため campaign 専用 file に保存し、justification を射影しない。
- verify は legacy 1 rep＋性能構成 5 rep、bench 5 rep。C smoke の 158.6 秒/case は直接の単価ではない。
- 親への裁定依頼は、二重 compile の許容、具体 role 差分の承認、見積り後の計算投入確認。
- 本段は read-only の静的計画であり、build・pytest・live 計測は実行していない。