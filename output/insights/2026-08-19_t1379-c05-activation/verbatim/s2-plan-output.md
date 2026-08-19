以下は静的読解のみの段2プランです。pytest・編集・再実測は未実施です。

```text
【1. 契約 JSON】
orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:190-228
C05 の condition_number、required_evidence、negative_control_id は維持し、
:227 の machine_checkable だけを false → true にする。

【2. evaluator 登録】
orchestrator/campaign/s8c_preregistration_evidence.py:2607-2615
辞書を番号順に保ち、4 と 9 の間へ `5: _evaluate_c05,` を 1 行追加する。
_evaluate_c05(:1631-1740)、_evaluate_undefined(:2622-2650) の C05 分岐、
PredicateRegistry.evaluate(:2718-2735) は変更しない。
SATISFIABLE_CONDITION_IDS(:2619) に C05 は追加しない。登録後も現行
p3 の run_trial に schedule 呼出しがないため、結果は
UNSATISFIED / schedule-consumer-unreachable のままとする。

【3. DECIDER_VERSION】
orchestrator/campaign/s8c_preregistration.py:41-51
`DECIDER_VERSION = "s8c-decider/v3"` を v4 にする。SOURCE_PATH、
EVIDENCE_CONTRACT_PATH は変更しない。
prepare_revision の契約は :1957-2037、CLI は :2091-2129 を使用する。

【4. C05 負対照 fixture】
orchestrator/tests/test_s8c_preregistration_predicates.py:488-638 に、
C05 用の token-only consumer / workload source を追加する。

_evaluate_c05(:1647-1698) が要求する関数集合は次の 9 個である。
`validate_authority`, `search_space_digest`, `initial_state_digest`,
`regenerate`, `load_schedule`, `verify_exact_schedule_bytes`,
`verify_shared_search_space_and_initial_state`, `verify_schedule`,
`consume_schedule`

token-only schedule consumer は上記 9 関数をすべてトップレベルに定義し、
次の呼出し関係を実際の live body に置く。

- verify_schedule → validate_authority,
  verify_exact_schedule_bytes,
  verify_shared_search_space_and_initial_state
- consume_schedule → verify_schedule
- verify_exact_schedule_bytes → regenerate

同じ fixture の関数 body に、field_literals(:1683-1703) が要求する
次の 8 文字列を実際の AST Constant として置く。
`schema_version`, `master_seed`, `cells`, `schedule_index`, `arm`,
`holdout`, `search_space_sha256`, `initial_state_sha256`

workload fixture は相対 import で load_schedule / consume_schedule を取り、
run_trial から次を到達可能にする。

    artifact = load_schedule("output/s8c-preregistration/schedule.v1.json")
    return consume_schedule(
        artifact, master_seed="fixture-seed", authority={}
    )

main は `return run_trial()` とする。_negative_control_case(:824-915) の
C05 分岐では、p3、schedule consumer、schedule artifact の 3 source を返す。
artifact は `_c05_authority()`(:37-95) と `S.regenerate()` で fixture 内に作る。

mutation は上記 workload の `return consume_schedule(...)` を
`return artifact` に 1 箇所だけ置換する。token-only 版は
EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable、mutated 版は
UNSATISFIED / schedule-consumer-unreachable になる。

:918-926 へ `nc_c05_initial_state_hash_bitflip: C05` を移し、
:929-931 から削除する。:2433-2441 の expected_reasons に
`"C05": "schedule-consumer-unreachable"` を追加する。

machine-checkable 件数の追加波及として :2397-2408 の集合と exercised を
7 → 8 にし、:3012 の `len(...) == 7` も 8 にする必要がある。
これは C05 登録に伴う既存 tripwire の機械的追随である。

なお、:2697-2738 の旧 bitflip test は NON_MACHINE... が空になるため
収集されなくなる。専用 test を残すか、旧 coverage を移すかは brief が
指定しておらず、段3で裁定する（未確定）。

【5. schedule authority (P1)】
orchestrator/campaign/s8c_schedule.py:57-114 が定義する厳密な集合は次の通り。

search-space:
`arms`, `designated_source_context`, `descriptor_bindings`, `gating_spec`,
`holdout_bindings`, `holdouts`, `role_contracts`, `role_files`,
`role_payload_allowlist`, `workloads`

initial-state:
`attempt_policy`, `baseline`, `descriptor_binding`, `gating_snapshot`,
`initial_role_metrics`, `leakproof_context`, `stop_policy`, `whiteboard`

validate_authority(:210-249) は key 集合の完全一致、mapping/list/string 型、
入れ子を含む空値禁止を要求する。regenerate(:317-349) はこの authority の
digest を schedule bytes に埋める。

実値からの候補写像は以下である。

- arms / holdouts → S.ARMS / S.HOLDOUTS
- gating_spec / designated_source_context → p3 の GATING_SPEC /
  DESIGNATED_SOURCE_CONTEXT
- role_contracts → p3.ROLE_CONTRACTS の値を role ごとに canonicalize
- role_files → ROLE_FILES の Path を repo-relative path、role 名、bytes hash
  を持つ mapping へ正規化
- role_payload_allowlist → ROLE_PAYLOAD_KEY_SPEC
- workloads → p3.WORKLOADS の各 WorkloadEntry を通常 dict へ正規化
- attempt_policy / stop_policy / leakproof_context →
  s8c_generation_projection の定数を dict/string 化
- initial_role_metrics → p3._INITIAL_ROLE_METRICS

ただし descriptor_bindings / holdout_bindings は WORKLOADS ではなく
FORMAL_WORKLOADS / s8b_holdout_freeze.HOLDOUTS 側の H1/H2 値を要する。
baseline、descriptor_binding、whiteboard は run_trial 内の runtime 値
（:3195-3237、:3316-3340）で、gating_snapshot も
snapshot_gating_spec(:3767) の runtime snapshot である。
さらに p3 の _load_s8c_schedule_authority(:1555-1560) は現在明示的に
unavailable を送出する。したがって、意味が定義された「本物の authority」
をこの scope 内だけで構築するのは不可能であり、canonical projection の
新設は T-1380 相当の過大拡張となる。

代替案は、親が一度だけ test helper と同型の暫定 18-key mapping
(:37-95) を生成用に inline し、S.validate_authority → S.regenerate を
通すこと。ただしこれは将来 consumer が実 authority から再生成すると
bytes が変わり、実質再抽選になる。暫定値を commit してよいかは未確定で、
段3の最重要攻撃対象とする。p3 や schedule.py に builder を追加せず、
T-1380 の配線も先取りしない。

【6. g8、§5、schedule artifact】
output/s8c-preregistration/condition-freeze/condition-freeze.v1.g8.json は
新規生成物（行番号なし）。既存 g7 の次世代であることを確認する。
docs/phase3-8c-preregistration.md:145-165 の規約に従い、
:192 の master_seed 欄へ `secrets.token_hex(32)` で一度だけ生成した
64 hex 文字列を単一 code span 内の canonical JSON string として記入する。
結果や cell order を見て seed を選び直さない。

output/s8c-preregistration/schedule.v1.json も新規生成物（行番号なし）。
固定した同じ seed と authority で
`orchestrator.campaign.s8c_schedule.regenerate(master_seed, authority=...)`
を呼び、bytes をそのまま保存する。保存後は同じ引数で
validate_authority、verify_exact_schedule_bytes、
verify_shared_search_space_and_initial_state を確認する。

【7. F393 に従う統合順序】
親が最初に変更前 HEAD を保存する。

    OLD_HEAD="$(git rev-parse HEAD)"

実装子の契約・registry・DECIDER_VERSION・test 変更は commit せず作業 tree
へ集める。もし子が commit 済みなら、対象を確認したうえで F393 の代替手順
として `git reset --soft "$OLD_HEAD"` を使い、契約変更 commit を祖先に残さない。

その後、次の順で実行する。

    python3 -m orchestrator.campaign.s8c_preregistration prepare-revision \
      --repo-root "$PWD" \
      --commit "$OLD_HEAD" \
      --ruling-reference D529 \
      --revision-reason \
      "T-1379: C05 の machine-checkable activation と decider v4 への改訂"

→ g8 の exclusive-create 成功を確認する。
→ cryptographic seed を 1 回生成し :192 を記入する。
→ P1 の裁定済み authority（暫定ならその旨を記録）で schedule.v1.json を生成する。
→ CLI check は evaluator bytes 比較の罠があるため診断根拠にせず、
  library の core.activation_report_at を使って C05 の
  UNSATISFIED / schedule-consumer-unreachable を確認する。
→ 以下を全て同じ一回の commit に入れる。

- contract JSON
- s8c_preregistration_evidence.py
- s8c_preregistration.py
- test_s8c_preregistration_predicates.py
- docs/phase3-8c-preregistration.md
- condition-freeze.v1.g8.json
- schedule.v1.json

commit 前に staged path と diff を確認し、AI-Agent trailer を付ける。
pytest、check_docs、provenance 監査は親の実行面で行い、この段2では実走済みと
報告しない。
```

## 総括

変更対象は契約・evaluator registry・decider・メタテスト・§5・g8・schedule artifact。`_evaluate_c05`、`_evaluate_undefined`、`PredicateRegistry`、p3 の schedule 配線は変更しない。

最大の未確定事項は P1 の authority projection と、旧 bitflip test の扱い。段3では、暫定 authority による将来再生成 drift、C05 負対照の一変異性、F393 の一 commit 境界、T-1355 との v4 競合を攻撃する。