"""Human-reviewed role source and projection I/O ledger.

This file is intentionally independent from manifest rendering.  Updating a Claude role source,
description, full manifest role contract, shared developer instruction template, or projected I/O
contract requires an explicit review update here; regenerating an adapter alone cannot bless drift.
"""
from __future__ import annotations


# Claude role / Codex adapter の絶対枚数。set 等号は各 source を相互束縛するが枚数自体は固定しない
# ため、全 source から lockstep で 1 role を削除すると 13 件でも整合してしまう。この floor を
# 人間レビュー ledger に置くことで、role の増減は必ずここの明示更新を伴う review checkpoint になる。
EXPECTED_ROLE_COUNT = 14

SOURCE_FILE_SHA256 = {
    # Reviewed 2026-08-19: T-1356; sort closed-region 残余の gallery型17-21追加、violation type 上限21。
    # Reviewed 2026-08-20: T-1356 fix; 型17-21の具体的な境界条件を削除し、verifier_blind_spot への事後報告へ移管。
    # Reviewed 2026-09-02: T-2145; verified sort IR の監査境界と残余リスクを追記。
    "auditor": "a0912ebbc95e2f3641cfb1cbf0d609cfbe2deb7ba52d1c3057517b1bc69fab35",
    "axis-proposer": "8b33fafbf95d530903f0e56a104147beab98151ed06c7d2fd6b2c3ebb6222be0",
    "calibrator": "dbe696286856738afb79369e772998bfad97bbdaccbcef5a8e0d1773f6c35b62",
    # Reviewed 2026-08-26: T-1690 fix; backoff hole の suffix-free literal 1個・1文制約を汎用 coder に軸限定で追記。
    "coder": "5573a39d611ac519b2a5025e73e0e5585a79292ebf20fafdb02985306031a7e0",
    # Reviewed 2026-08-26: T-1690; suffix-free literal/value一致・1文の producer 契約を追加。
    # Reviewed 2026-09-09: T-2249; 段 4 の delta_pct≡None 不変と食い違う固定例 (-1.2) を入力例から除去。
    # Reviewed 2026-09-11: T-2528; whiteboard 入力例を実射影の 5 field へ訂正。
    "coder-v4-autonomous": "f8916155e8107445a618c6a47a2d0c2ed1a5813352135133457bbaa28314c546",
    # Reviewed 2026-09-02: T-2200; K2 宣言アーム用 sibling role 契約を追加。
    # Reviewed 2026-09-03: T-2246; empty-source と明示 consumer の境界を追記。
    "coder-v4-autonomous-k2": "c149f0955bdeee69edc93d52f2437122e0d533a8737d5bbb3376ef93699d67a6",
    # Reviewed 2026-08-18: T-396 A; enforcement ownership split, prohibition set unchanged.
    # Reviewed 2026-09-02: T-2145; raw C++ 合成を閉じた sort IR proposal へ縮小。
    # Reviewed 2026-09-11: T-2528; whiteboard 入力例を実射影の 5 field へ訂正。
    "coder-v4-autonomous-sort": "27a39534b4248573fccc17ab3120a858ec6bac0436430f3983eb7c154e66a8b3",
    # Reviewed 2026-08-04: stage5-agent-review.md approved the T-428 wire contract.
    # Reviewed 2026-09-11: T-2528; whiteboard 入力例を実射影の 5 field へ訂正。
    "coder-v4-autonomous-trigger-gating": "00405a9639b150372cf0881699090090cf688d4a61fa22651e0aee27e8d5279a",
    "critic": "cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",
    "critic-experiment": "fc20aa7ef1bf9af45eaa2e56313b8b5221a3ff2a2413110fa333ba470ff9456e",
    # Reviewed 2026-08-19: workload-policy-hint-impl; 「## 入力」節へ optional policy_hint
    # フィールドの説明文を追記 (JSON 例本体には含めない — source 入力 shape parity 検査が
    # 例中の全 key を ROLE_IO_CONTRACTS 宣言と exact 照合するため)。ROLE_IO_CONTRACTS の
    # input_required_fields (3 field) は不変 (hint は任意であり「常に必須」の宣言に加えない、
    # dormant Codex adapter parity は対象外)。
    # Reviewed 2026-09-09: T-2249; 段 4 の delta_pct≡None 不変と食い違う固定例 (-1.2) を入力例から除去。
    # Reviewed 2026-09-11: T-2528; whiteboard 入力例を実射影の 5 field へ訂正。 current_perf・whiteboard・任意 policy_hint の入力説明も訂正。
    "planner-v4": "1d6b1603dbbb7c776202cd20a300e60e01b9119b55068ddfcce3e83714f646da",
    "profiler": "8a3f5bc1cba31d366c7ea3f0149e04917c07fe7677aa609ce6f05f5c8decbd6d",
    "selector-8b": "23483aeb871ad7363060a183d85df6dd10b9e74b40337037a6cf6bbcc34c799c",
    "verifier": "80ce00b78832cb18a95d0ee8047124fbb8435cf2ec4d312b9d4ed2e6c7f0300f",
}

# ``manifest.json`` の各 ``roles.<name>`` entry 全体を固定する独立 pin。schema 単体だけでなく
# model、consumer、forbidden classes、capability lowering、projection instructions を含む。
# 値は manifest renderer から自動更新してはならず、契約変更を人間レビューした時だけ更新する。
ROLE_MANIFEST_SHA256 = {
    # Reviewed 2026-08-04: stage6-fix-ruling.md 2 巡目裁定 r1-3。
    # Reviewed 2026-08-19: T-1356; sort closed-region 残余の gallery型17-21追加、violation type 上限21。
    "auditor": "07b097be18a5ca528b5b402746c05a5c1b27ca8e9b3b050b83c7463df445c456",
    "axis-proposer": "57d9bd635e99c5eab2e7fb852043446ffe6c0aff1a1fa48ed5b724c4ae041ad1",
    "calibrator": "775d8e9fa963b6f2d895ffcb7be14a7ce487ea82911fd797f4f6bb840d8e9186",
    "coder": "2af1a88e8f8cae73e251d067ba47ea4b1acd5457083111d3dc719914d199e136",
    # Reviewed 2026-08-26: T-1690; projection に suffix-free literal/value一致・1文制約を追加。
    "coder-v4-autonomous": "5e277d54ad7314807cd2f8c46574c6223e8a87e2b251eb29bdb53e2d02bb8bdd",
    # Reviewed 2026-09-02: T-2200; K2 入力・自己申告出力・境界を固定。
    # Reviewed 2026-09-03: T-2246; empty-source と明示 consumer を固定。
    "coder-v4-autonomous-k2": "c57eafe7b75061b30e956ecd33586f22ac8339d7eba01a7fcb37c122c8e9231c",
    "coder-v4-autonomous-sort": "0516335248dd542372ba4a420835c2451ea816b2aadc78cacaa1c388bd2252fa",
    # Reviewed 2026-08-04: stage5-agent-review.md and stage6-fix-ruling.md r2-7.
    "coder-v4-autonomous-trigger-gating": "c307d820022585bf9f34ffb3f70b10734c8903b5eb0f450698739aa9413d3a8c",
    "critic": "efbb2961dca75c14afa97462b4664065aac90621a184f63d6bc017f1d050cc42",
    "critic-experiment": "69dd9033640393fbde6a51c8f7d606e7780b91393e8d2829d530e5c3d2156b0e",
    "planner-v4": "9e142881783337414af0c8d239541fc8f2b0a2892b160d58940602c93615dd17",
    "profiler": "61a3cc067886a042bcf076fc1b2494bf26bb5e6e64bcd6a6e8bc01a77071ec30",
    "selector-8b": "8d1a101ca21c17dab7cc529ceda263f2ec77dbc09b290a838cfddc88346f8631",
    "verifier": "2d36ee3afec401942fc3e66d521ddbf9d1cc54b81d98090d883f5f49d8f94a8f",
}

# ``spec.DEVELOPER_INSTRUCTION_TEMPLATE`` exact UTF-8 bytes の独立 pin。
DEVELOPER_INSTRUCTION_TEMPLATE_SHA256 = (
    "78efa4db37b471081ea9d29c880c9e34ec86d9845f68f213ba6a00a2b69ece8a"
)

DESCRIPTION_SHA256 = {
    "auditor": "3c49b2bb687ce732af79bd94b542d2272536783e5c720d51c67b46a39e2edae2",
    "axis-proposer": "adb272294d98a10aa7e0160c35609c94d03cc472a14699284d572600fd2d67f3",
    "calibrator": "89ff12f68058d1fb1f0e8fbced10b04d34909c1c903f3140d6736b0a9c0df6ed",
    "coder": "e69da61c8d99ce72ddd9888d275cba9b9a31e5c8457d68696a7e00e9e5d94602",
    "coder-v4-autonomous": "c40c7e9d9a0ef4957c02957088331377186ffd2f23443236e05c4f231f0faa1b",
    "coder-v4-autonomous-k2": "0674e6b541ac09d51b19f93708f5119d6470486a16ec2ebe477d8d44e09f6bfe",
    # Reviewed 2026-09-02: T-2145; verified IR producer を明記した description へ追随。
    "coder-v4-autonomous-sort": "c65ecb4ef49ab1cf6b91aada5fcf7f401ed5f50e4540c0bdeab37cb2ab114a86",
    # Reviewed 2026-08-04: stage5-agent-review.md approved the T-428 wire contract.
    "coder-v4-autonomous-trigger-gating": "fdbb6a5501d78b693546b3dd78885576a0c0de558931971d87e50244ee404a2a",
    "critic": "b029016d0d8ca4b3ccf8f1ca3ab719d611f312d9a2ad7f88a361ba6d399b3fa1",
    "critic-experiment": "cc698590354ca22332f54ccb965ff67f8f093eca9a3c46063d3a8779e9956761",
    "planner-v4": "e1c82ce9410df83eb54db2dd491a11e3e303e43a83fefe44ce249a2e287e03e8",
    "profiler": "208aa13e1acb0b281dc0de3e811c2ec4c9483217d9ec63a2ed9c69fa5fd16347",
    "selector-8b": "144f5f9b20ab953dfb2e1f5c8622f1db2b74a9be3f3ac4cf821f7c0752b11632",
    "verifier": "21906b5078651cf0b99b831b8be96aeca064a45c4a45ad42c6417238c129bdc3",
}

# ``manifest.json`` から生成してはならない独立 review pin。required field だけでなく
# nested type/minimum/additionalProperties まで含む canonical JSON 全体を固定するため、
# manifest と generated adapter を同時に弱めても checker はここで fail-closed になる。
SCHEMA_SHA256 = {
    "auditor": {
        "input": "1b74afcd7a4100722d600004e3dba20245e548750937b87506c1a6fe55f68094",
        # Reviewed 2026-08-04: stage6-fix-ruling.md 2 巡目裁定 r1-3。
        # Reviewed 2026-08-19: T-1356; sort closed-region 残余の gallery型17-21追加、violation type 上限21。
        "output": "c3de7a421aee251c533a2bd65e9a4c0b7445665072d7902d42a9c947dcf078a8",
    },
    "axis-proposer": {
        "input": "3da4142a4dda56f7c88296cb1ea6f540cd7577a9a49fa8fa25a44b0a7e4c8c10",
        "output": "854068c96a8b3abdbb80d12a709b9307106ae9f8a4a7448324dc533146c8d718",
    },
    "calibrator": {
        "input": "291d2cabe23d3a69654ea2c715e7fd843aa4d470b76e58456d9af0b3bc2b8d97",
        "output": "6b9c628240cb26c01eac611b498e4aa4011597cd99da74af0bc9b4b00e83c202",
    },
    "coder": {
        "input": "169552e41b63f3daf041e809c86421e050def732fa7d0e6f1914d4fc064fe8bf",
        "output": "e356562a68e691103a97bc641aef49a690a05dc670266b7a6d83b7cfd32d3fc3",
    },
    "coder-v4-autonomous": {
        "input": "6412c89cf8d32b8071967cb6726791bc77e542a49b579790151136cddae5c361",
        "output": "bdede09e28ba864440cce8e055460370126ce8c230268abfbc61e976229da1ef",
    },
    "coder-v4-autonomous-k2": {
        "input": "eb27a6e93e0abd7ddc276105b43b43f8c1e44a86841d862c84e42e1b8d80235c",
        "output": "fb318c56fdaeeb61ebff284939d6386268c5d793e6d13210e22d5adc021ce24a",
    },
    "coder-v4-autonomous-sort": {
        "input": "7a1946e72e7b57e1888af72a0f2c30c4e204a42556dbbd4ea60b4e9053f1d510",
        "output": "680f2ed894f9df0d836c22750ea5e5506580dcfc4104b7b176d65425ec96cf06",
    },
    "coder-v4-autonomous-trigger-gating": {
        "input": "7f274f740ee0a94e8176d9a3be408b935600f4ffe1ee256339eb43ebe395ac0d",
        # Reviewed 2026-08-04: stage5-agent-review.md approved the T-428 wire contract.
        "output": "175db0210f85ffd219b65ca5b69410989f3fc7bfefa233a068d0309ac6c5d199",
    },
    "critic": {
        "input": "049e7b20460d5a9039f78160ec51409a6e22c4700dbde92cdd3f07f6774470b9",
        "output": "d03f4a295732859975e45db18271459981e0aaeef415119e58d1c7fe1c5e7e65",
    },
    "critic-experiment": {
        "input": "050411d0459b81a5485ab854c91cefc176c141349409f04832d22d5a274b165d",
        "output": "bb7ed153ace477c3b023ec8d4d906c0320a168357d52cb3323eadde363f72276",
    },
    "planner-v4": {
        "input": "b00309b29b14771cbc3e3100f11cb32478a1439e27a70f8945498b474d3cb0f7",
        "output": "f5ed98fea602c926de03c2d2f68e3280b03e9463808cb4775ee0b233fb70022c",
    },
    "profiler": {
        "input": "464c5c4d556d311bd002804b8dc5979ffa400acea16ae6f1695975b1f913a744",
        "output": "afdcede422f9dbd77995c34865e754dfe316a2271c1e558928155131240edeb0",
    },
    "selector-8b": {
        "input": "2960dfeb3933f68cd57097ef40bd96e30c63fa934f6a41d29c0a5f04f6c8c404",
        "output": "a2fc5431ca3bf7d5932499e7f968b0fbc8210f94c4bef6aa35716926d2b310e4",
    },
    "verifier": {
        "input": "e3df4ec4dee7c5fa3c024ab4543f4f26180d953b2f82466164994140b2090789",
        "output": "1b9803e741452465e08073580992818a4cb57afe5134583ae196083ee200c7ce",
    },
}


def _direct(inputs: tuple[str, ...], outputs: tuple[str, ...]):
    return {
        "mode": "direct-json-example",
        "input_required_fields": inputs,
        "output_required_fields": outputs,
        "source_obligations": {},
    }


def _mediated(inputs: tuple[str, ...], outputs: tuple[str, ...], obligations: dict[str, str]):
    return {
        "mode": "mediated-override",
        "input_required_fields": inputs,
        "output_required_fields": outputs,
        "source_obligations": obligations,
    }


ROLE_IO_CONTRACTS = {
    "auditor": _mediated(
        ("working_diff", "diff_digest", "designated_sources", "abort_digest"),
        ("verdict", "diff_digest", "violations", "nits", "proposed_tests", "uncertainty"),
        {field: f"adapter-field:{field}" for field in
         ("verdict", "diff_digest", "violations", "nits", "proposed_tests", "uncertainty")},
    ),
    "axis-proposer": _direct(
        ("diagnostics", "stock_excerpts", "edit_surface_map"),
        ("proposals", "global_unknowns"),
    ),
    "calibrator": _mediated(
        ("request", "measurements"),
        ("selected_records", "decision_basis", "within_run_noise", "scale_risk", "uncertainty"),
        {
            "record-count-selection": "adapter-field:selected_records",
            "documented-basis": "adapter-field:decision_basis",
            "within-run-noise-floor": "adapter-field:within_run_noise",
            "scale-sensitivity": "adapter-field:scale_risk",
            "unresolved-measurement-limits": "adapter-field:uncertainty",
        },
    ),
    "coder": _mediated(
        ("instruction", "marker_id", "designated_source", "api_excerpts"),
        ("implementation", "summary", "constraint_check", "uncertainty"),
        {
            "edited-branch": "adapter-field:implementation",
            "edited-surface-summary": "adapter-field:summary",
            "constraint-self-check": "adapter-field:constraint_check",
            "deviation-or-doubt": "adapter-field:uncertainty",
        },
    ),
    "coder-v4-autonomous": _direct(
        ("leakproof_context", "baseline", "planner_direction", "whiteboard"),
        ("proposal",),
    ),
    "coder-v4-autonomous-k2": _direct(
        ("leakproof_context", "knowledge_input", "baseline", "planner_direction", "whiteboard"),
        ("proposal", "knowledge_use", "classification", "data_boundary_report"),
    ),
    "coder-v4-autonomous-sort": _direct(
        ("leakproof_context", "sort_spec", "baseline", "planner_direction", "whiteboard"),
        ("proposal",),
    ),
    "coder-v4-autonomous-trigger-gating": _direct(
        ("leakproof_context", "gating_spec", "baseline", "planner_direction", "whiteboard"),
        ("proposal",),
    ),
    "critic": _mediated(
        ("digest",),
        ("attribution", "recommend", "avoid", "uncertainty"),
        {field: f"adapter-field:{field}" for field in
         ("attribution", "recommend", "avoid", "uncertainty")},
    ),
    "critic-experiment": _mediated(
        ("trial", "workload", "seed", "online_digest", "unevaluated_candidates", "trajectory"),
        ("action", "genome", "reason", "uncertainty"),
        {
            "next-step-decision": "adapter-fields:action,genome,reason,uncertainty",
            "trajectory": "trusted-driver-owned:trajectory",
            "final_pick": "trusted-driver-owned:final_pick",
            "per_step": "trusted-driver-owned:per_step",
            "stopped_reason": "trusted-driver-owned:stopped_reason",
        },
    ),
    "planner-v4": _direct(
        ("current_perf", "leading_indicators", "whiteboard"),
        ("proposal",),
    ),
    "profiler": _mediated(
        ("certified", "screening", "profile_data"),
        ("hotspot_attribution", "scale_risk", "mechanism", "uncertainty"),
        {
            "hotspot-attribution": "adapter-field:hotspot_attribution",
            "scale-risk": "adapter-field:scale_risk",
            "mechanism": "adapter-field:mechanism",
            "uncertainty": "adapter-field:uncertainty",
        },
    ),
    "selector-8b": _direct(
        ("schema_version", "descriptor", "candidates"),
        ("schema_version", "choice_id", "rationale"),
    ),
    "verifier": _mediated(
        ("verification_result",),
        ("serializable", "verdict", "certified", "stats", "total_cycles", "anomalies", "integrity", "uncertainty"),
        {
            "serializable-graph-fact": "adapter-field:serializable",
            "three-valued-verdict": "adapter-fields:verdict,certified",
            "structured-cycle-witness": "adapter-field:anomalies",
            "trace-integrity": "adapter-field:integrity",
            "trusted-verifier-counts": "adapter-fields:stats,total_cycles",
            "uncertainty": "adapter-field:uncertainty",
        },
    ),
}


__all__ = [
    "EXPECTED_ROLE_COUNT",
    "DEVELOPER_INSTRUCTION_TEMPLATE_SHA256",
    "DESCRIPTION_SHA256",
    "ROLE_MANIFEST_SHA256",
    "ROLE_IO_CONTRACTS",
    "SCHEMA_SHA256",
    "SOURCE_FILE_SHA256",
]
