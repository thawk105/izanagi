# date: 2026-10-01 09:49:37 JST  HEAD: 63378acb8ff8ce76e9973dec0735f2a2c12d7c9b
## [1] make_policy_coder_input の key と入力源 (p3_s4_loop_policy.py)
40:PROJECTION_PATH = ROOT / 'output/env/pegasus/calibration/silo_function_policy_recon/projection.json'
41:CONTEXT_PATH = ROOT / 'src/coder-leakproof-context.md'
42:SPEC_PATH = Path(__file__).with_name('silo_function_policy_coder_spec.md')
311:        digest['workload_tag'] = workload['tag']
352:                    'iteration', 'implementation', 'ir', 'outcome',
353:                    'reject_subtype', 'reject_rule_id', 'verifier_digest')})
354:    payload = {'leakproof_context': CONTEXT_PATH.read_text(encoding='utf-8'),
355:               'policy_spec': SPEC_PATH.read_text(encoding='utf-8'),
356:               'baseline': baseline,
357:               'recon_projection': {'binary': projection['binary'], 'scope': projection['scope']},
358:               'self_history': history}
363:        payload['critic_diagnosis'] = critic_diagnosis
## [2] projection.json
{
  "binary": true,
  "scope": "固定 16 点のテンプレート部分空間で、両 verify certified・非 high-abort の点が、同 job の abort0 に対して 5 rep 中央値で 3% 超を示し、それが別 job の再測でも再現したか",
  "excluded": {}
}
## [3] leakproof context の Measurement Setup の標準 workload 塊
59:### Standard Contention Workload (bench、配線規模)
61:100k_records / t4_threads / skew0.9_zipfian_access / rr50_readratio /
69:- `rr50`: 操作の 50% が read、50% が write
75:これは kickoff と同じ配線規模であり、性能比較用に calibrator が決めた規模ではない。性能比較に
76:入る段では、calibrator が決めた records / threads / reps に差し替えられる。
## [4] 仕様 file と親指示文・起動器・台帳・round tool の workload 語 (行数)
orchestrator/campaign/silo_function_policy_coder_spec.md: 0
tools/pegasus/silo_policy_contrast_parent.md: 0
tools/pegasus/silo_policy_contrast_parent.py: 0
tools/pegasus/silo_policy_contrast_launch.py: 0
orchestrator/campaign/silo_policy_contrast.py: 0
tools/silo_policy_contrast_round.py: 0
## [5] critic prompt の材料 (round tool _critic_prompt)
106:    materials = [{"logical_slot": e["logical_slot"], "critic_digest": e.get("critic_digest"),
108:                  "fitness_tps": e.get("fitness_tps"), "abort_rate_pct": e.get("abort_rate_pct"),
111:    return (f"silo-function-policy 系列 {ledger.header['series']} の原提案 {a} の前に、"
116:            "```json\n" + json.dumps({"results": materials, "job1_stock": _stock(ledger)},
## [6] critic digest の見出しと verify pass の tag
1207:    green = render_text([build_digest(tag, {}, view)])
1260:        L.append(f"## workload: {d.tag} ({wl})")
170:LEGACY_TAG = "legacy"
171:S2_TAG = "s2"
176:PERFORMANCE_TAG = "performance"
## [7] T-2867 本走 (v1) の llm-ir-1 原提案 1 の入力から、露出に関わる欄だけ
coder-input keys: ['baseline', 'critic_diagnosis', 'leakproof_context', 'policy_spec', 'recon_projection', 'self_history']
baseline.abort_rate_pct: 12.559999999999999
recon_projection == projection.json の binary/scope: True
leakproof_context: rr50 を含む行 2 / write-heavy 0 / read-heavy 0 / 'rr5 ' 0
policy_spec の workload 語: 0
critic-prompt.md の write-heavy|read-heavy|rratio|rr5 を含む行: 0
critic-prompt.md の digest 見出し: ## workload: p3-silo-policy ()
