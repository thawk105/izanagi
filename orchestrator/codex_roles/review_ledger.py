"""Human-reviewed role source and projection I/O ledger.

This file is intentionally independent from manifest rendering.  Updating a Claude role source,
description, full manifest role contract, shared developer instruction template, or projected I/O
contract requires an explicit review update here; regenerating an adapter alone cannot bless drift.
"""
from __future__ import annotations


# Claude role / Codex adapter の絶対枚数。set 等号は各 source を相互束縛するが枚数自体は固定しない
# ため、全 source から lockstep で 1 role を削除すると 15 件でも整合してしまう。この floor を
# 人間レビュー ledger に置くことで、role の増減は必ずここの明示更新を伴う review checkpoint になる。
EXPECTED_ROLE_COUNT = 16

SOURCE_FILE_SHA256 = {
    # Reviewed 2026-08-19: T-1356; sort closed-region 残余の gallery型17-21追加、violation type 上限21。
    # Reviewed 2026-08-20: T-1356 fix; 型17-21の具体的な境界条件を削除し、verifier_blind_spot への事後報告へ移管。
    # Reviewed 2026-09-02: T-2145; verified sort IR の監査境界と残余リスクを追記。
    # Reviewed 2026-09-26: T-2865; 方策軸の型22〜26と免除範囲を追加。
    # Reviewed 2026-09-30: T-2890; gen-opt の入力 3 つと型27〜30 を追加 (Codex 射影の型上限26・入力 schema は不変)。
    # Reviewed 2026-09-30: T-2890 fix; gen-opt 監査の入力の中身の欠落と source の読めなさを uncertain に追加。
    "auditor": "2664cc8fc93809be25b1961f53a6c9c64a3feb640b2c58a2eeda2b80c66d9e14",
    "axis-proposer": "8b33fafbf95d530903f0e56a104147beab98151ed06c7d2fd6b2c3ebb6222be0",
    "calibrator": "dbe696286856738afb79369e772998bfad97bbdaccbcef5a8e0d1773f6c35b62",
    # Reviewed 2026-08-26: T-1690 fix; backoff hole の suffix-free literal 1個・1文制約を汎用 coder に軸限定で追記。
    "coder": "5573a39d611ac519b2a5025e73e0e5585a79292ebf20fafdb02985306031a7e0",
    # Reviewed 2026-08-26: T-1690; suffix-free literal/value一致・1文の producer 契約を追加。
    # Reviewed 2026-09-09: T-2249; 段 4 の delta_pct≡None 不変と食い違う固定例 (-1.2) を入力例から除去。
    # Reviewed 2026-09-11: T-2528; whiteboard 入力例を実射影の 5 field へ訂正。
    "coder-v4-autonomous": "26024b2ea2684d74a8f747e3169fca69f713e94a1f4648c68d498890e1cd356f",
    # Reviewed 2026-09-02: T-2200; K2 宣言アーム用 sibling role 契約を追加。
    # Reviewed 2026-09-03: T-2246; empty-source と明示 consumer の境界を追記。
    "coder-v4-autonomous-k2": "5d730eeaf09b639ef146157e6a7fe4786e79ace60af3de5c15bb23a16bf9e427",
    # Reviewed 2026-08-18: T-396 A; enforcement ownership split, prohibition set unchanged.
    # Reviewed 2026-09-02: T-2145; raw C++ 合成を閉じた sort IR proposal へ縮小。
    # Reviewed 2026-09-11: T-2528; whiteboard 入力例を実射影の 5 field へ訂正。
    "coder-v4-autonomous-sort": "b34f16a14d4402ef114f37f97090a590de60c2d0d8710a9114cea663e088e84d",
    # Reviewed 2026-08-04: stage5-agent-review.md approved the T-428 wire contract.
    # Reviewed 2026-09-11: T-2528; whiteboard 入力例を実射影の 5 field へ訂正。
    # Reviewed 2026-09-17: T-2703/T-2717/T-2705; baseline の世代間凍結と適用版を明記。
    "coder-v4-autonomous-trigger-gating": "2cc08b30573aef3337740d3e44848d94651d48528d4e1f095b420ceea4807388",
    # Reviewed 2026-09-17: T-2703/T-2717/T-2705; digest の独立指標と適用版を訂正。
    "critic": "fea81c65909aa9026b8fda1bf9b4768b38185dfd9327cff86a8bcef844504c1b",
    # Reviewed 2026-09-17: T-2703/T-2717/T-2705; online digest の独立指標と適用版を訂正。
    "critic-experiment": "95718801d7f2066ec9cbbf68bf1a61c5cfe7775b295330d98a71e08aa488d40c",
    # Reviewed 2026-08-19: workload-policy-hint-impl; 「## 入力」節へ optional policy_hint
    # フィールドの説明文を追記 (JSON 例本体には含めない — source 入力 shape parity 検査が
    # 例中の全 key を ROLE_IO_CONTRACTS 宣言と exact 照合するため)。ROLE_IO_CONTRACTS の
    # input_required_fields (3 field) は不変 (hint は任意であり「常に必須」の宣言に加えない、
    # dormant Codex adapter parity は対象外)。
    # Reviewed 2026-09-09: T-2249; 段 4 の delta_pct≡None 不変と食い違う固定例 (-1.2) を入力例から除去。
    # Reviewed 2026-09-11: T-2528; whiteboard 入力例を実射影の 5 field へ訂正。 current_perf・whiteboard・任意 policy_hint の入力説明も訂正。
    # Reviewed 2026-09-17: T-2703/T-2717/T-2705; current_perf / leading_indicators の凍結と適用版を明記。
    "planner-v4": "a2e01d52bb4d6399c40a5e1ae280ec9e7c64201e79a4a365f00734d006d3eb55",
    "profiler": "8a3f5bc1cba31d366c7ea3f0149e04917c07fe7677aa609ce6f05f5c8decbd6d",
    "selector-8b": "23483aeb871ad7363060a183d85df6dd10b9e74b40337037a6cf6bbcc34c799c",
    "verifier": "80ce00b78832cb18a95d0ee8047124fbb8435cf2ec4d312b9d4ed2e6c7f0300f",
    # Reviewed 2026-09-26: T-2865; 方策 coder role を追加。
    "coder-v4-autonomous-policy": "0a071db46da65a7979952fb68da50b8a8df2b158a5e00a632c7ad1222b16f809",
    # Reviewed 2026-09-26: T-2865; 方策 coder role を追加。
    "coder-v4-autonomous-policy-ir": "6b577e35013273edd5f70811fbc0f1d763e69f705a0a6e17d26cf5176d015e59",
}

# ``manifest.json`` の各 ``roles.<name>`` entry 全体を固定する独立 pin。schema 単体だけでなく
# model、consumer、forbidden classes、capability lowering、projection instructions を含む。
# 値は manifest renderer から自動更新してはならず、契約変更を人間レビューした時だけ更新する。
ROLE_MANIFEST_SHA256 = {
    # Reviewed 2026-08-04: stage6-fix-ruling.md 2 巡目裁定 r1-3。
    # Reviewed 2026-08-19: T-1356; sort closed-region 残余の gallery型17-21追加、violation type 上限21。
    # Reviewed 2026-09-26: T-2865; auditor 出力型上限26に追随。
    "auditor": "1e1967d1922c616af122be6ae29042bab94d41ad1e6e8c1067b1a91e06790e96",
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
    # Reviewed 2026-09-26: T-2865; 方策 coder role を追加。
    "coder-v4-autonomous-policy": "d16cd0214a038917693eb61bd58fce6aa4b1b445375e857ff4cbb8f3271cece3",
    # Reviewed 2026-09-26: T-2865; 方策 coder role を追加。
    "coder-v4-autonomous-policy-ir": "50ef6280b9357fd31b3c0451d92aa10dd636706e5c62169bea4d8b0282025845",
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
    "planner-v4": "80f3f634d672a12d985329f5d6e932e4c07b56465a4840f447393b490cff121a",
    "profiler": "208aa13e1acb0b281dc0de3e811c2ec4c9483217d9ec63a2ed9c69fa5fd16347",
    "selector-8b": "144f5f9b20ab953dfb2e1f5c8622f1db2b74a9be3f3ac4cf821f7c0752b11632",
    "verifier": "21906b5078651cf0b99b831b8be96aeca064a45c4a45ad42c6417238c129bdc3",
    # Reviewed 2026-09-26: T-2865; 方策 coder role を追加。
    "coder-v4-autonomous-policy": "bb106ed03285eeaa5c2e2d7e20034847f8f4f1de456170333b491fa3c39b1680",
    # Reviewed 2026-09-26: T-2865; 方策 coder role を追加。
    "coder-v4-autonomous-policy-ir": "e31783ab621f3837c5e207d806af29f80e4798a581d2ec7bfd40bffd7b18e733",
}

# ``manifest.json`` から生成してはならない独立 review pin。required field だけでなく
# nested type/minimum/additionalProperties まで含む canonical JSON 全体を固定するため、
# manifest と generated adapter を同時に弱めても checker はここで fail-closed になる。
SCHEMA_SHA256 = {
    "auditor": {
        "input": "1b74afcd7a4100722d600004e3dba20245e548750937b87506c1a6fe55f68094",
        # Reviewed 2026-08-04: stage6-fix-ruling.md 2 巡目裁定 r1-3。
        # Reviewed 2026-08-19: T-1356; sort closed-region 残余の gallery型17-21追加、violation type 上限21。
        # Reviewed 2026-09-26: T-2865; auditor violation type の最大値を26へ。
        "output": "dc17b6811bff118ef189394f8062497ba9f185bb5f12d58aea966acf2ca27101",
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
    # Reviewed 2026-09-26: T-2865; 方策 coder の入出力 schema を固定。
    "coder-v4-autonomous-policy": {"input": "8d0570f36e2a742e5346c93df34ac4aac42aacbebba07a52e11d7c3b804c2357", "output": "701d1969d53ec2ff3a2f955ed6118d2760dbb0a94772f4cfeb86cd54fe6df9f2"},
    # Reviewed 2026-09-26: T-2865; 方策 coder の入出力 schema を固定。
    "coder-v4-autonomous-policy-ir": {"input": "8d0570f36e2a742e5346c93df34ac4aac42aacbebba07a52e11d7c3b804c2357", "output": "c7d77ac06a6f27108c70e20a3e9d2252e2af17143ea1280985fc737d9a9b7e7a"},
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
    "coder-v4-autonomous-policy": _direct(
        ("leakproof_context", "policy_spec", "baseline", "recon_projection", "self_history"),
        ("proposal",),
    ),
    "coder-v4-autonomous-policy-ir": _direct(
        ("leakproof_context", "policy_spec", "baseline", "recon_projection", "self_history"),
        ("proposal",),
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
