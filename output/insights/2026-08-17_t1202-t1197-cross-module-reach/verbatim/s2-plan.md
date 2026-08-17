# 段 2 実装プラン

結論は、契約で宣言された root module からのみ開始し、実際の import 束縛を canonical な `(blob path, function name)` として辿る設計を採ることです。宣言外 module は import closure として commit blob から読み、その blob を `EvidenceRef` に追加します。`SATISFIED` 終端や契約 JSON、規範文書、freeze record は変更しません。

静的検査だけを行いました。pytest は実行しておらず、緑とは報告しません。

## 0. brief のアンカー訂正

brief の「`run_trial` の既定引数 `drive=trigger.drive_iteration` が 2402 行」という記述は不正確です。

- [p3_autonomous_workload_trial.py:2398-2403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:2398) は `_run_workload` の定義です。
- `run_trial` は [同:2845-2860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:2845) で sentinel を既定値にします。
- 標準 delegate は [同:2893-2894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:2893) で代入され、3172、2121、2755 行を経て `_drive_s8c_generation` へ渡ります。

したがって、2402 行の既定値を辿る案は「実際の引数伝播を証明する解析」ではなく、静的 may-reach の近似です。この区別を段 4 裁定に残す必要があります。

## 1. traversal の設計

### 1.1 編集箇所と内部表現

[s8c_preregistration_evidence.py:280-359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:280) の `_functions`、`_called_names`、`_reachable_functions`、`_reachable_calls` 周辺を、path-aware な graph に置き換えます。

- callable の identity は bare name ではなく `(repo-relative Python path, top-level function name)`。
- module graph の開始点は、その条件の `required_evidence` で指定された root module だけ。
- 到達関数、解決済み call target、未解決 call を別集合にする。述語判定に使うのは解決済み target だけ。
- top-level 名が複数回定義または再束縛される場合は曖昧として解決しない。最後の同名定義を暗黙採用しない。
- wildcard import、`getattr`、`importlib`、lambda、`functools.partial`、instance method は本 wave では追わず、到達なしへ倒す。
- C01/C12 の attribute 集合は root module 内の到達関数だけから集める。[現行 C01:427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:427) と [C12:573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:573) を cross-module 全体の attribute union にしない。無関係な module の `.sha256` や `.single_process` で gate を満たす拡大を防ぎます。

### 1.2 module 名から commit 内 path への解決

現在の module path から package 名を機械的に導出します。通常の `x.py` は末尾を除いた部分が package、`x/__init__.py` は `x` 自身が packageです。

module `a.b.c` の候補は次の 2 つに限定します。

- `a/b/c.py`
- `a/b/c/__init__.py`

exact 1 blob のときだけ解決し、両方存在または両方不在なら未解決です。path component は Python identifier に限定し、絶対 path、`..`、制御文字を受理しません。

| 構文 | 束縛規則 |
|---|---|
| `from . import X` | 現 package の `X.py` または `X/__init__.py` を解決し、local `X` を module に束縛する。`as Z` なら `Z`。 |
| `from .X import y` | 現 package の `X` module を解決し、local `y` をその module の canonical symbol `y` に束縛する。 |
| `from .X import y as z` | local `z` だけを canonical symbol `X:y` に束縛する。bare `y` は束縛しない。 |
| `import a.b.c` | Python と同じく local root `a` を束縛し、call expression が exact `a.b.c.<name>` のときだけ `a/b/c.py:<name>` へ解決する。 |
| `import a.b.c as z` | local `z` を exact module `a.b.c` へ束縛する。 |

relative import の `level` が package root を越えるもの、repo に blob がない absolute import、stdlib・third-party import は未解決 edge として無視します。実際の Python import は実行しません。

### 1.3 module-level alias

[p3_s4_loop_trigger_gating.py:101-102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_s4_loop_trigger_gating.py:101) の `_lookup = env_contract.lookup` を次の限定規則で解決します。

- module top-level の単純な `Assign` または `AnnAssign` だけ。
- target は単一 `Name`、RHS は `Name` または静的 `Attribute` chain。
- RHS が実 import bindingを経て一意な top-level function に解決できる場合だけ alias edge を作る。
- alias の再代入、computed attribute、call result、instance attribute は解決しない。
- `_admit_env_contract` の `_lookup(...)` [同:325-331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_s4_loop_trigger_gating.py:325) は canonical target `env_contract.py:lookup` として数える。

### 1.4 callable の既定値

採る案は、import binding から一意に解決できる callable default を may-reach edge として辿る設計です。ただし、この edge は「必ず呼ばれる」証明ではなく、既存 AST traversal と同じ存在到達性です。

対象は `ast.Name` または `ast.Attribute` から一意に解決できる default だけとし、任意式や caller 注入値は解決しません。`SATISFIABLE_CONDITION_IDS` は空集合のまま [evidence.py:607-610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:607) に保ち、この近似を充足証明へ昇格させません。

#### 既定値を辿る場合

C12 は第 1 gate を通過すると予測します。

- `run_trial` → `_finish_trial`: [p3 autonomous:3194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:3194)
- `_finish_trial` → `_run_workload`: [同:2109-2131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:2109)
- `_run_workload` の callable default: [同:2398-2403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:2398)
- `_drive_s8c_generation` の `drive(...)`: [同:1202-1229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:1202)
- `drive_iteration` → `_run_one_iteration_resolved`: [trigger:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_s4_loop_trigger_gating.py:764)、[同:837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_s4_loop_trigger_gating.py:837)
- `from .loop import run_campaign`: [同:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_s4_loop_trigger_gating.py:70)
- `run_campaign` → `_authorize_measurement`: [loop.py:123-170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/loop.py:123)
- `_authorize_measurement` → `execution_guard.attest_and_build_receipt`: [loop.py:92-109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/loop.py:92)、定義は [execution_guard.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/execution_guard.py:576)
- `lookup` は default と独立に `_run_workload` 2461 → `_admit_env_contract` 325 → `_lookup` 331 → [env_contract.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/env_contract.py:820) へ届く。

結果として `lookup` と `attest_and_build_receipt` は exact target として到達し、第 2 gate の `single_process_required` 不在で止まります。

#### 既定値を辿らない場合

higher-order callable を一切伝播しない最小案では、`lookup` は上記 alias 経路で届きますが、`_drive_s8c_generation` の `drive(...)` [p3 autonomous:1229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:1229) で停止します。

したがって `attest_and_build_receipt` に届かず、C12 は引き続き `UNSATISFIED / environment-contract-consumer-absent` です。

より精密に 2893-2894 行の sentinel assignment、3172・2121 行の `dict(**kwargs)`、2755 行の明示 keyword を追うデータフローなら default を使わず到達可能ですが、本 wave の小さな import traversal を大きく越えます。段 4 では「限定 may-edge を採る」か「高階解析なしで誤診断を残す」かを選ぶべきで、前者を推奨します。

### 1.5 commit blob の読み方と EvidenceRef

現行 `_ConditionProbe.read_kind` は [evidence.py:370-390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:370) のとおり契約 kind しか読めません。trigger と loop は C12 の `required_evidence` に無いため、既存経路だけでは裁定を実現できません。

[evidence.py:361-397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:361) に次を追加します。

- `read_path(path)`：`core.read_blob_at(repo_root, commit, path, required=False)` を使う commit-blob 専用経路。
- `python_path(path)`：path 単位の AST cache。
- `read_kind` / `python_kind` は上記を呼ぶ薄い wrapper にする。
- 実際に読んだ宣言外 blob も `refs[path]` に登録する。

その結果、C12 の `PredicateResult.evidence` には少なくとも trigger と loop が増えます。これは次の影響を持ちます。

- `EvidenceRef` は [core:148-159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration.py:148) の report 本体であり、隠れた判定入力を残さず監査可能になる。
- `evidence()` の path sort [evidence.py:394-396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:394) により順序は決定的。
- `ActivationReport` digest は dataclass 全体から導出される [core:1932-1936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration.py:1932) ため、EvidenceRef 増加でも digest は変わる。
- 契約 JSON の `required_evidence` を増やす変更ではなく、宣言 root から導出した dependency closure の記録である。JSON hashと freeze pin は変えない。
- 宣言外 blob を読んでおきながら EvidenceRef に載せない案は、判定に効いた bytes が report から消えるため採らない。

### 1.6 循環、上限、解決不能

提案する固定上限は次です。

- call depth: 64
- 読み込む Python module: 64
- canonical callable state: 2048
- traversal で保持する raw blob 合計: 16 MiB

実 C12 の必要 chain は 5 module 程度なので十分な余裕があります。

- cycle は canonical callable の visited 集合で停止する。
- target を全件発見したら探索を終了し、無関係な import closure を広げない。
- module/path 不在、外部 import、曖昧 alias は edge 不在として扱う。
- Python parse error は既存の `evidence-python-parse-error`。
- depth/module/bytes/callable 上限到達は新しい閉じた reason `reachability-limit-exceeded` の `ERROR` にする。[現行 catch:700-712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:700) で `commit-blob-read-error` に潰さない。
- 未解決や上限を到達済みとみなす fallback は設けない。

## 2. 受理集合を不当に広げない設計

### canonical target の比較

bare name の集合比較を、条件が要求する exact path と name の比較へ変更します。

- C01: `ratified_generation_reference` の contract path と `load_ratified_freeze`。
- C04: workload supervisor 内の `mark_experiment_indeterminate` と、contract の `trial_registry.py:forbid_trial_restart`。
- C12: contract kind `environment_contract`、`execution_guard`、`allocation_consumer` の各 path と関数名。
- C09 は target module path が契約に宣言されていないため、少なくとも実 import から解決された canonical callable であることを要求する。repo 全体の同名検索はしない。
- C10/C11 の直接 AST shape gate は変更しない。

`SATISFIABLE_CONDITION_IDS`、各 evaluator の終端 `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` は維持します。

### 最短の細工と封鎖

危険な最短細工は、`reservation.py` または未 import の decoy module に top-level の `single_process_required` を 1 定義だけ追加し、repo 全 module の同名定義を到達と数える実装を通すことです。runtime の import edgeも call edgeもないのに C12 の allocation gate が前進します。

封鎖は二重です。

1. traversal は到達済み関数の lexical import binding からしか別 module を開かない。
2. C12 は canonical target `(reservation.py, single_process_required)` が call graph に存在することを要求する。

したがって、別 module の同名定義、required module に置いただけで未配線の定義、bare unresolved call のいずれも到達にはなりません。

残る限界は `if False` などの control-flow 非実行性です。既存 traversal 自体が may-reach であり、本 wave では dominance 証明へ拡張しません。終端を `SATISFIED` にしないことで、その限界を充足証明に使わせません。

## 3. 6 条件への影響予測

| 条件 | 予測 status / reason | 根拠 |
|---|---|---|
| C01 | `UNSATISFIED / workload-projection-mismatch` | traversal より手前の [evaluator:418-421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:418) で停止する。実 sink は records=100,000、threads=4 [p3 autonomous:637-695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:637) で、要求される 1,000,000 と 48 を含まない。 |
| C04 | `UNSATISFIED / crash-policy-cell-partial` | 第 1 gate [evaluator:442-448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:442) の要求名が実 tree にない。現実装は `_record_indeterminate_terminal` → `trial_registry.record_trial_terminal` [p3 autonomous:2813-2835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:2813)、registry 側も `record_trial_start_once` / `record_trial_terminal` [trial_registry.py:1687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/trial_registry.py:1687) であり、要求された 2 名ではない。 |
| C09 | `UNSATISFIED / formal-acceptance-layer3-consumer-absent` | producer 側は import [p3 autonomous:50-51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:50)、call [同:2380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:2380)、定義 [completeness.py:2225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/autonomous_trial_completeness.py:2225) で通る。しかし evaluator の第 2 gate [459-470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:459) が要求する `accept_trial` はなく、実入口は `assert_trial_registry_acceptance` [trial_registry.py:2408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/trial_registry.py:2408)。 |
| C10 | `UNSATISFIED / cross-binding-verifier-incomplete` | traversal を使う前の verifier shape gate [evaluator:496-505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:496) で止まる。`autonomous_trial_completeness.py` に `verify_s8c_cross_binding` / `read_and_verify_bytes` はなく、現有の全体検査入口は [completeness.py:1971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/autonomous_trial_completeness.py:1971)。 |
| C11 | `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` | cap=2 [p3 autonomous:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:124)、3入口 validator は 2451、2897、3352 行、critic consumer は2555行。projection の定数は [projection.py:74-82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_generation_projection.py:74)、関数は458、511、734行にある。traversal 非使用のまま [evaluator:557-561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:557) の終端へ達する。 |
| C12 | `UNSATISFIED / allocation-enforcement-consumer-absent` | default may-edge を採れば lookup と attestation の exact target が届き、第 1 gate [evaluator:577-584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:577) を通る。`reservation.py` にある top-level API は `read_binding` [159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/reservation.py:159)、`check_reservation` [218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/reservation.py:218)、`is_reservation_required` [273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/reservation.py:273) で、`single_process_required` はないため第 2 gate [585-591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:585) で止まる。 |

## 4. テスト計画

主な編集面は [test_s8c_preregistration_predicates.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1) です。

| 追加・更新 test | 期待値 | 殺す欠陥 |
|---|---|---|
| `test_cross_module_import_forms_resolve_exact_bound_target` | 4 parameter: `from . import X`、`from .X import y`、`from .X import y as z`、`import a.b.c` が同じ canonical target を返す | 各 import AST branch の削除、`as` 名を無視する実装、absolute import を bare root 名だけで比較する実装 |
| `test_c12_cross_module_consumers_advance_past_environment_gate` | 全 consumer を正しく import した synthetic tree は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`。dynamic module path が EvidenceRef の subset に入る | cross-module traversal 全体の除去、宣言外 blob を読めない実装、dependency EvidenceRef の記録漏れ |
| `test_c12_module_level_callable_alias_is_reachable` | `_lookup = env_contract.lookup` 経由でも environment gate を通る | module-level alias resolver の削除 |
| `test_c12_callable_default_is_reachable` | `_run_workload(drive=trigger.drive_iteration)` から `drive_iteration` を経て attestation target に届く | callable-default edge の削除 |
| `test_c12_missing_definition_stays_unsatisfied`（B1） | call spelling があっても、どの module にも target 定義がなければ `UNSATISFIED / environment-contract-consumer-absent` | call の字面だけで target を成立させる変更、定義存在 gate の削除 |
| `test_c12_unimported_same_name_definition_stays_unsatisfied`（B2） | 別 module に同名定義があっても import binding がなければ同じ `environment-contract-consumer-absent` | repo 全体の同名 scan、canonical identity を bare name へ戻す変更 |
| `test_reachability_cycle_terminates_and_limit_fails_closed` | cycle は有限終了。上限到達は `ERROR / reachability-limit-exceeded` | visited 削除、上限を無視、上限到達を reachable 扱いする変更 |
| `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` | C12 だけ `allocation-enforcement-consumer-absent` へ更新 | wave 前の module-local traversal への復帰、実 tree default/alias/import closure の欠落 |
| 既存 `test_noop_and_token_only_fixtures_never_satisfy` | mutation 後 reason 表は C01/C04/C09/C10/C11/C12 とも現行値を維持。C12 は `allocation-enforcement-consumer-absent` | 各条件の既存負の対照を無効化する変更 |

### 既存 fixture の更新

[test predicates:313-425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:313) の single-module fixture は identity-aware traversal と不整合になるため、次を直します。

- C01: `load_ratified_freeze` を対応 module から実 import する。
- C04: `forbid_trial_restart` を registry module から実 import する。workload module の同名 local def は除く。
- C09: producer verifier を実 import binding で呼ぶ形にする。
- C12: 現在の local `lookup` / `attest_and_build_receipt` / `single_process_required` 定義を positive fixture から除き、対応 module の import 経由にする。
- 現在の unbound C12 fixture [406-425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:406) は B2 の負例へ転用できる。

### 実 tree snapshot と golden

現行 snapshot helper [test predicates:66-87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:66) は contract 宣言 path しか複製しません。宣言外の中継 module が synthetic commit に存在しなくなるため、少なくとも次も HEAD blob から複製します。

- `orchestrator/campaign/p3_s4_loop_trigger_gating.py`
- `orchestrator/campaign/loop.py`

golden 表 [118-132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:118) は C12 の reason だけ `allocation-enforcement-consumer-absent` へ変更します。

負の対照表 [534-543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:534) の reason 値は変更しません。ただし baseline fixture を実 import 束縛へ直し、mutation 前が terminal `EVIDENCE_UNDEFINED`、mutation 後が表の `UNSATISFIED` になることを保ちます。

## 5. `DECIDER_VERSION` bump の閉包

D458 決定 (1) は、拒否理由の意味変更でも bump を要求します。C12 が `environment-contract-consumer-absent` から `allocation-enforcement-consumer-absent` へ変わるため、[s8c_preregistration.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration.py:50) を `s8c-decider/v2` へ bump します。

契約 JSON、規範 doc、freeze record は変更しません。現 tip g3 は [condition-freeze.v1.g3.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g3.json:1) の legacy v1 で `decider_version` がなく、[core:1741-1743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration.py:1741) により既に `decider-version-unbound` です。現用の effective capability を bump が失効させる状況ではありません。

### core test 内の literal `"s8c-decider/v2"` 全 5 件

| 現行行 | 用途 | bump 後の修正 |
|---|---|---|
| [core test:1535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_core.py:1535) | generation record の版改変 | current と異なる版を返す test helper を使う。bump 後なら v3 相当。v2 のままでは bytes mutation にならない。 |
| [同:2014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_core.py:2014) | mismatched record fixture | current と異なる版変数へ置換する。 |
| [同:2022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_core.py:2022) | 上記 fixture の report assertion | 2014 行で作った mismatch 版変数との一致を検査する。 |
| [同:2075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_core.py:2075) | hostile `str` subclass | `HostileRuntimeDecider(M.DECIDER_VERSION)` にする。文字列値は current と同じだが exact type が違う、という本来の検出力になる。 |
| [同:2094](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_core.py:2094) | report digest mutation | current と異なる版 helper を使う。v2 のままでは replace が no-op になり digest が変わらない。 |

併せて literal v1 assertion の [2057](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_core.py:2057) と [2080](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_core.py:2080) は、record 作成時に保存した current version または `M.DECIDER_VERSION` 由来の変数へ変えます。1499 行の malformed `v0`、`v01`、`v1/extra` は形式負例なので維持します。

### 他 consumer

- `trial_registry` は literal 版を持たず、[1343-1347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/trial_registry.py:1343) と [2435-2439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/trial_registry.py:2435) で core の再導出結果を検証します。変更不要。
- `reflux_origin_binding` は activation report digest を写すだけ [220-268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/reflux_origin_binding.py:220)。変更不要。
- `p3_autonomous_workload_trial.py` に版 literal・直接参照はありません。対応 test の [5254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_p3_autonomous_workload_trial.py:5254) は既に定数参照です。
- trial registry tests の 1211、1604 行、reflux test の112行も定数参照なので追従します。

## 6. 変異事前登録候補

| 変異点 | 変異 | 期待 kill node |
|---|---|---|
| [evidence.py:341-358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:341) | 新 graph を wave 前の module-local `_reachable_functions` / `_reachable_calls` へ戻す | 実 tree golden、`test_c12_cross_module_consumers_advance_past_environment_gate` |
| 新 import resolver、現アンカー [280-340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:280) | `ImportFrom` の `asname` を無視する | `test_cross_module_import_forms_resolve_exact_bound_target[from-symbol-as]` |
| 同 resolver | module-level `_lookup = env_contract.lookup` の alias edge を除去する | `test_c12_module_level_callable_alias_is_reachable`、実 tree golden |
| callable-default edge、現アンカー [p3:2402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/p3_autonomous_workload_trial.py:2402) | default callable を reached set に入れない | `test_c12_callable_default_is_reachable`、実 tree golden |
| canonical call comparison、現アンカー [evaluator:577-589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:577) | `(path, name)` を bare `name` 比較へ戻す | `test_c12_unimported_same_name_definition_stays_unsatisfied` |
| 同 C12 gate | exact target definition 検査を除く、または unresolved call spelling を reached と数える | `test_c12_missing_definition_stays_unsatisfied` |

## 7. 段 5 実装単位

編集ファイル所有が素集合になる 2 分割は可能です。brief の「単一実装子しかない」は訂正できます。

- 単位 A: `s8c_preregistration_evidence.py` と `test_s8c_preregistration_predicates.py`。cross-module graph、EvidenceRef、A/B、alias/default、golden、変異対象を一体で所有。
- 単位 B: `s8c_preregistration.py` と `test_s8c_preregistration_core.py`。version bump と literal fixture 閉包を所有。

4 ファイルの所有は完全に disjoint で、B は A の内部 API に依存しません。並列実装後に親が統合し、実 tree golden と関連 suite をまとめて実測できます。JSON、`docs/phase3-8c-preregistration.md`、freeze record はどちらにも所有させません。

## 総括

- 採るべき設計は、契約 root から actual import binding だけを辿る canonical `(path, function)` graph である。
- 宣言外の中継 module は commit blob から読み、判定に使った全 blob を EvidenceRef に追加する。
- callable default は限定した may-reach edge として辿る案を推奨する。これで C12 は真の allocation 不在まで進む。
- 最大のリスクは、default edge が実引数の上書きを無視する過大近似になることである。
- bare name、repo 全体走査、未 import の同名定義は B1/B2 と canonical identity で拒否する。
- D458 により `DECIDER_VERSION` は v2 へ bump し、core test の衝突 literal 5 件を全件是正する。
- 段 4 の択一は「限定 default may-edge を採る」対「高階 callable を追わず C12 の誤診断を残す」であり、前者を採るべきである。