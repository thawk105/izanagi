## 実測

- 指定された `brief.md`、`rulings-verbatim.md`、`prior-closure-consult-b.md` は全文確認した。
- 当 worktree は clean、`HEAD=2bf9cf387643bf7ac087c31f5c38cfcc5539de68`。一方、現在の local `main=1d2706f9eaad4fc87fa7a4ea5f8c53f8bfb9a210` なので、brief の「base = local main 2bf9cf387」は「branch 作成時の base」としては正しいが、現在の local main という表現は古い。
- 競合 wave `worktree-dev-wave-t1999-define-gate-family` は現在 37 file が未 commit。除外指定の 3 file はすべて変更中で、`s8b_oracle_manifest.py` は非接触。この点は brief を支持するが、「3 file 程度」という読みは現在では過小。
- loader は `s8b_ratified_freeze.py:1399-1418`、g1 投影 equality は `:1054-1085` のみ。current selection は `launch_validate` → `_launch_validate` の `:3303-3321`、historical reverify は `:3558-3568` でこの分岐を通らない。`test_s8b_ratified_verify.py:890-895` が historical 不変を固定している。
- load-only 3 群は再測一致:
  - oracle manifest: `s8b_oracle_manifest.py:1198-1260`、静的 load は `:1205`、公開直前は `:1259`。
  - s8c verifier/publish: `s8c_result_judge.py:2103-2163` と `:2166-2209`。静的 load は `:2108`、`:2188`。
  - C06: `p3_autonomous_workload_trial.py:4639-4657`、静的 load は `:4640`。
- C06 の「経路全体が到達不能」は過大。`_load_s8c_schedule_authority` の常時拒否 `p3_autonomous_workload_trial.py:1799-1804` は `_prepare_s8c_budget_inputs:1837` で呼ばれ、`:4640` の freeze 読込より後である。予算予約 `:4647` は未到達だが、`:4640` に置く selection gate は先に発火できる。
- official floor `result.json` / `launch_certificate.json`、active v2 generation、approval、active pointer はいずれも 0 件。`BUDGET_APPROVAL_SHA256` は `s8b_holdout_freeze.py:52` で `None`。`output/s8c-preregistration/schedule.v1.json` も不在。
- 起動証明書:
  - 選択側は非 strict validator を使用: `s8b_holdout_freeze.py:1654-1686`、呼出し `:1674`。
  - strict 版は `s8b_launch_cert.py:129-144`。発行側だけが独立 2 回 scan と strict 比較を行う: `s8b_floor_campaign.py:5368-5393,7330-7336`。
  - `clean_scan_digest` の preimage は tracked・untracked file 列挙と freeze allowlist: `s8b_holdout_freeze.py:370-385`、`s8b_floor_campaign.py:5272-5314`。preimage 自体は保存されず、証明書には digest だけが残る。
  - 現行 full validator が証明するのは path/cert 秒一致、cert/journal hash・時刻束縛、cert 導入 commit の一意性と `C<G`: `s8b_ratified_freeze.py:3331-3391,3420-3428,3448-3467`。同 module 自身も `:3085-3088` で実時間順を保証しないと明記する。
- `s8c_result_judge` の production caller は依然 0。公開関数は `judge:1947`、`verify_floor_bytes:2103`、`publish_result_table:2384`。
- s8c の production aggregate final claim 点は単一 trial の `_finish_trial` ではなく、6 report を集約する `trial_registry.assert_trial_registry_acceptance:5675-6267`。receipt は `:6233-6255` で組み立て、`:6251` が常に `certifying: False`、`:6256` で発行する。CLI callsite は `:6348-6354`。
- judge は exact 6 cell、`n>=2`、`6×n` schedule・観測、correctness/trace/外部 attestation を要求する: `s8c_result_judge.py:281-303,330-431,493-561`。production attempt は `p3_autonomous_workload_trial.py:1330-1338` で `replicate_index==0` の slot だけを選び、acceptance の初期集合も `trial_registry.py:3496-3509` で同じく replicate 0 に固定される。

## 設計 (残件 1)

強制点は loader ではなく、各 current consumer の「公開・予約へ進む直前」とする。`_verify_generation_semantics` と `reverify_published_freeze` は変更しない。

### Oracle manifest

変更候補は `orchestrator/campaign/s8b_oracle_manifest.py:1259`。`build_approved_manifest` の公開署名は変更しない。

```python
validated = s8b_ratified_freeze.launch_validate(ratified, root)
assert validated.ratified is ratified
_write_approved_manifest(...)
```

manifest の純粋な構築後、create-only write の直前に置く。これなら spec 自体の拒否優先順は保ち、公開だけを current admission に束縛できる。

拒否理由は `RatifiedFreezeError.reason` を既存 `ManifestCliError` に翻訳し、少なくとも次を保持する。

- `floor-selection-rule-mismatch`
- `floor-selection-eligibility-underivable`
- `floor-selection-unverifiable`

通る正例は、static load、current full validation、earliest eligible identity がすべて成立する active g1。拒否される負例は、static loader には通るが同 namespace により早い derived-eligible run が存在する active g1で、candidate file は作られない。

変わる受理集合は「`load_ratified_freeze` だけ通る active freeze」から「`launch_validate` も通る current active freeze」への縮小。selection mismatch に加え、既存 current gate が拒否する activation HEAD drift、current contract/admission mismatch、closure drift、既存 `certificate-generation-scope` も新たに manifest 公開を止める。新しい g2 述語は作らず、既存 gate の挙動だけを再利用する。

ただし現制約では実装を直ちに land できない。編集禁止の `test_s8b_oracle_manifest.py:1346-1407` にある 2 正例が static-only synthetic `RatifiedFreeze` を注入し、`launch_validate` を patch しないため必ず赤になる。期待値変更ではなく fixture の current-admission 注入追加で直せるが、同 file は編集禁止である。赤を受容せず、unit B は所有解除または当該 wave 側の fixture 追随が確認できるまで停止すべきである。

### s8c verifier / publish

`orchestrator/campaign/s8c_result_judge.py:26` に既存 `launch_validate` を追加 importし、`:2020` 手前に次の private helper を追加する。

```python
def _load_current_launch_validated_freeze() -> RatifiedFreeze:
    ...
```

実装は `load_ratified_freeze()` → `launch_validate(ratified)` → `validated.ratified`。`verify_floor_bytes:2108` と `_validate_verified_floor:2188` の静的 load をこの helper に置換する。

拒否理由:

- verifier: `current ratified freeze launch validation failed: <RatifiedFreezeError.reason>`
- publish: `current ratified floor binding is unavailable: <上記理由>`

通る正例は、current selection を満たす g1 の floor protocol/source bytes と一致する 2 refs。負例は static load と bytes hash は通るが earlier eligible run が存在する receiptで、verifier または publish が table 作成前に拒否する。

変わる受理集合:

- 現在通る「static load-valid・bytes 一致・selection mismatch」の refs。
- verify 後に namespace が変わり、publish 時点では selected が earliest でなくなった古い receipt。
- static loader は通るが current full admission が失敗する freeze。

いずれも実装後は拒否される。`judge` 自体の入力・結論集合は変えない。

### C06 budget

`orchestrator/campaign/p3_autonomous_workload_trial.py:1807` 手前に追加する。

```python
def _load_s8c_budget_ratified_freeze(
    *, root: Path,
) -> s8b_ratified_freeze.RatifiedFreeze:
    ...
```

`load_ratified_freeze(root)` → `launch_validate(..., root)` → `.ratified` とし、`:4640` をこの helper 呼出しへ置換する。拒否理由は既存 `RatifiedFreezeError` の `[floor-selection-…]` をそのまま伝播させ、新しい成功状態や certification 文言は作らない。

通る正例は selection-valid g1。gate 通過後は従来どおり `8c schedule authority is unavailable; schedule_sha256 を推測できない` で止まる。負例は selection mismatch g1で、C05 authority を呼ぶ前に `[floor-selection-rule-mismatch]` で止まる。

変わる受理集合は「C05 authority 呼出しまで進める freeze」の集合である。現在は static load-validなら進むが、実装後は current launch-valid なものだけになる。予算 ledger を生成できる集合は C05 未実装のため現在も実装後も空だが、gate 自体は到達可能であり無意味ではない。

## 設計 (残件 2)

実装しない。新しい関数・述語・拒否理由は追加しない。

`expected_clean_scan_digest` は凍結時に再計算できない。発行時 preimage にはその時点の untracked file と freeze namespace の path/hash 集合が入るが、その preimage は certificate、journal、manifest、receipt、Git tree のいずれにも保存されない。後の Git commit には untracked 状態がなく、result/certificate 等の追加によって列挙集合も変わる。

同 namespace の他 run の digest 比較も採らない。値が一致しても複数 certificate を同じ偽 digest で整合的に再構成でき、不一致は正当な worktree 変化でも生じるため、実時間性の証明にも安全な拒否境界にもならない。

測った値域は次のとおり。

- production official certificate: 0 件、従って観測済み `clean_scan_digest` 集合も空。
- non-strict validator が受ける digest の型域: 任意の 64 lower-hex (`s8b_launch_cert.py:67-72`)。
- strict validator の拒否文字列: `launch certificate.clean_scan_digest が expected と不一致`。ただし freeze/selection 時点に独立 expected が存在しない。

現行で通る正例は、任意の 64 lower-hex digestを持ち、v1/protocol/run ID/path 秒が一致する証明書。現行で拒否される負例は `started_utc` と path run ID の秒が異なる証明書。問題の「全証拠を整合的に再構成した証明書」は現在も実装後も拒否できない。

変わる受理集合は 0。値域を狭める根拠がなく、任意の digest equality を足す実装は過剰拒否か恒真束縛になるため採らない。証明可能な上限は既存の path/cert 秒一致、raw hash chain、`C<G` までであり、実時間順は締められない。

## 設計 (残件 3)

実装しない。production final claim の正しい配線位置は `orchestrator/campaign/trial_registry.py:6104-6256`、すなわち6 report、attempt snapshot、lifecycle、cross-binding を固定した後、acceptance receipt を作る直前である。単一 trial の `_finish_trial:3523-3659` では6 cellを持てないため不適切。

安全な呼出順は概念上、

```text
verify_floor_bytes → judge → publish_result_table → acceptance receipt
```

だが、現 production schema から以下を構成できない。

- `n>=2` の exact `6×n` schedule/observations。
- raw throughput と correctness/trace 状態に独立束縛された attestation。
- judge の単一 `_ContrastParams` に渡す正当な H1/H2 params authority。
- repository 外3表と repository 内 receipt の failure-atomic な束縛。

C05 が常時拒否するため production report 集合も作れず、実在する発火 artifact path は 0。関数名だけを呼ぶ配線、report値からconsumer自身がattestationを発行する配線、G1/G2を replicate に転用する配線は作らない。

通る production 正例は現状 0。テスト fixture だけが exact 6×n 入力を構成できる。現行の負の対照は、6 report acceptance が `s8c_result_judge` を一度も呼ばず `certifying:false` receipt を発行できる入力である。

DW-G05 の成果物影響は非ゼロで書けない。正確な1行は「放置しても receipt は既に `certifying:false` のままで、certified 選択・report・台帳の値、受理集合、参照は変わらず、未使用3関数の production 参照数だけが0のまま」である。従って must-fix 実装ではなく、C05と入力 authority が実在するまで backlog とする。変わる受理集合は 0。

## テスト計画

実装可能な s8c unit:

- `orchestrator/tests/test_s8c_result_judge.py`
  - `test_floor_verification_requires_launch_validated_current_freeze`
  - `test_floor_verification_rejects_selection_mismatch_before_reading_floor_bytes`
  - `test_publish_rejects_when_current_floor_selection_changed_before_writes`
  - 既存 `load_ratified_freeze` patch 4 箇所へ、同じ loaded object を `.ratified` に返す `launch_validate` patchを追加。assert/期待値は変更しない。
- `orchestrator/tests/test_p3_autonomous_workload_trial.py`
  - `test_c06_budget_uses_launch_validated_ratified_freeze`
  - `test_c06_selection_failure_precedes_unavailable_schedule_authority`
  - 既存 `:8445`、`:9203` の bare loader patchを新 helper patchへ追随。期待値は変更しない。
- 既存回帰:
  - `test_s8b_ratified_verify.py::test_launch_validate_rejects_floor_selection_rule_mismatch`
  - `test_s8b_ratified_verify.py::test_historical_reverify_does_not_apply_current_floor_selection`

oracle unit は条件解除後:

- 新規 `orchestrator/tests/test_s8b_oracle_manifest_selection.py`
  - `test_approved_manifest_calls_current_launch_validation_before_create`
  - `test_approved_manifest_selection_mismatch_leaves_no_candidate`
- pytest fixture依存なので `orchestrator/tests/README.md` の `PYTEST_ONLY_ALLOWLIST` に登録する。`test_plain_runner_coverage.py:44-86` は `test_*.py` を動的列挙するため、別の file 集合への手動登録は不要。
- ただし編集禁止の既存正例2 nodeも launch validator fixtureへの追随が必要。これを解消できない間は production変更を入れない。

production module名の lexical grep 結果:

- `s8c_result_judge`: `test_s8c_preregistration_invariant.py`、`test_s8c_preregistration_predicates.py`、`test_s8c_result_judge.py`。
- `p3_autonomous_workload_trial`: `test_attempt_registry_core_s8b_profile.py`、`test_autonomous_trial_completeness.py`、`test_campaign.py`、`test_claude_transport.py`、`test_layer3_admission_diagnosis.py`、`test_layer3_report.py`、`test_p3_autonomous_workload_trial.py`、`test_p3_build_authority_cli.py`、`test_p3_exploration_namespace.py`、`test_p3_s4_loop.py`、`test_p3_s4_loop_trigger_gating.py`、`test_reflux_formal_consumer.py`、`test_reflux_origin_binding.py`、`test_reflux_originless_compatibility.py`、`test_role_session_isolation.py`、`test_s8c_arm_inputs.py`、`test_s8c_budget.py`、`test_s8c_preregistration_invariant.py`、`test_s8c_preregistration_predicates.py`、`test_trial_registry.py`。
- `s8b_oracle_manifest`: fixture 2本に加え、`test_s8b_binding_driftguards.py`、`test_s8b_experiment_numbers.py`、`test_s8b_holdout_admission.py`、`test_s8b_materialization.py`、`test_s8b_oracle_artifacts.py`、`test_s8b_oracle_driver.py`、`test_s8b_oracle_judge.py`、`test_s8b_oracle_manifest.py`、`test_s8b_oracle_manifest_contract.py`、`test_s8b_oracle_n_pilot.py`、`test_s8b_oracle_report.py`、`test_s8b_ratified_freeze.py`、`test_s8b_verdict.py`。

この段では pytest・acceptance・checker は実走しておらず、緑とは記録しない。親は実装後に指定 acceptance 全走を行う。

## 変異事前登録の候補

1. `s8c_result_judge.py:2108` 付近  
   `_load_current_launch_validated_freeze()` を bare `load_ratified_freeze()` へ戻す。  
   殺す node: `test_s8c_result_judge.py::test_floor_verification_rejects_selection_mismatch_before_reading_floor_bytes`

2. `s8c_result_judge.py:2188` 付近  
   publish の current bindingだけ static loaderへ戻す。  
   殺す node: `test_s8c_result_judge.py::test_publish_rejects_when_current_floor_selection_changed_before_writes`

3. `p3_autonomous_workload_trial.py:4640` 付近  
   `_load_s8c_budget_ratified_freeze` を bare loaderへ置換する。  
   殺す node: `test_p3_autonomous_workload_trial.py::test_c06_selection_failure_precedes_unavailable_schedule_authority`

4. `p3_autonomous_workload_trial.py` の新 helper  
   `launch_validate(...).ratified` を入力 `ratified` の直接 return に変える。  
   殺す node: `test_p3_autonomous_workload_trial.py::test_c06_budget_uses_launch_validated_ratified_freeze`

5. `s8b_oracle_manifest.py:1259` 直前  
   `launch_validate` 呼出しを削除する。  
   殺す node: `test_s8b_oracle_manifest_selection.py::test_approved_manifest_selection_mismatch_leaves_no_candidate`

残件2・3は実装しないため、効いていない検査を装う変異は登録しない。

## 分割

### Unit A — s8c、実装可能

排他所有 path:

- `orchestrator/campaign/s8c_result_judge.py`
- `orchestrator/campaign/p3_autonomous_workload_trial.py`
- `orchestrator/tests/test_s8c_result_judge.py`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py`

### Unit B — s8b oracle、条件付き停止

排他所有 path:

- `orchestrator/campaign/s8b_oracle_manifest.py`
- `orchestrator/tests/test_s8b_oracle_manifest_selection.py`（新規）
- `orchestrator/tests/README.md`

両 unit が共有して触る file はない。`s8b_holdout_freeze.py` は編集しないため、future candidate の `generator.sha256` も変わらない。Unit B は編集禁止 test の fixture追随問題が解消するまで開始しない。

## リスクと不確実性

- read-only 静的調査のみで、pytest、acceptance、`check_codex_agents.py`、`check_docs.py` は未実走。
- local main が branch base より進んでおり、実装前 rebase/merge 後に行番号と競合面の再測が必要。
- `launch_validate` は selection だけでなく current contract・closure・generation gate 全体を再利用するため、受理集合の縮小は selection mismatch より広い。これは current consumer としては fail-closed だが、焦点走で波及を確認する必要がある。
- oracle production変更と編集禁止 test の synthetic fixture は現状両立しない。回避のため production に test-only bypass を入れてはならない。
- official run が0件なので、残件2の不能性は保存形式と call graphからの証明であり、実 artifact 値の比較ではない。
- C05、effective schedule、production 6×n observations が実在しないため、残件3の到達性は実走確認不能。
- repo外 backup、人手による時刻記録、外部監査ログの存在は調査対象外。ただし現在の production validator が参照しない材料は証明根拠に数えていない。

## 総括

残件1の s8c verifier/publish と C06 は、loaderを変えず current consumerから既存 `launch_validate` を呼ぶ形で実装できる。  
C06 selection gate は C05 の常時拒否より先に発火できるため、到達不能という親の一般化は訂正が必要である。  
oracle manifestも同じ設計が正しいが、編集禁止 test の static fixtureと衝突するため、現制約のままでは赤なしに land できない。  
残件2は clean-scan preimage が保存されず、既存材料だけでは実時間性を締められない。  
残件3は production aggregate点を特定できるが、6×n観測 authorityがなく、成果物影響も0なので実装しない。  
D1241/D1313 の non-certifying 上限、D1312 の loader/historical境界、D1325 の既存 g2 gate はいずれも維持する。