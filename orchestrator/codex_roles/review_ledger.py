"""Human-reviewed role source and projection I/O ledger.

This file is intentionally independent from manifest rendering.  Updating a Claude role source,
description, full manifest role contract, shared developer instruction template, or projected I/O
contract requires an explicit review update here; regenerating an adapter alone cannot bless drift.
"""
from __future__ import annotations


SOURCE_FILE_SHA256 = {
    "auditor": "324ff727b78935f5915fe7c685ad93ae3f3b3df74de2056990060266858f53f8",
    "axis-proposer": "8b33fafbf95d530903f0e56a104147beab98151ed06c7d2fd6b2c3ebb6222be0",
    "calibrator": "dbe696286856738afb79369e772998bfad97bbdaccbcef5a8e0d1773f6c35b62",
    "coder": "2781f8831766e2e4242b06878351979464767fc6a1c766bcf663dbaaf13f5ab2",
    "coder-v4-autonomous": "9e42f26503d63b92edb664a8d45875e10a05018f7bf469b1833bafcfa917771a",
    "coder-v4-autonomous-sort": "b6eeb4909c9022dc94e9aa0f6a6156a716cd384fe5898302bef7a15485801480",
    "coder-v4-autonomous-trigger-gating": "ff6deb8ce4a4888b22c93d876ae41e6f3709f6c18848866360976aefcc001949",
    "critic": "cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",
    "critic-experiment": "fc20aa7ef1bf9af45eaa2e56313b8b5221a3ff2a2413110fa333ba470ff9456e",
    "planner-v4": "0a52dd4feada41167aa62711cc8cf1ad81e306ad706e99825b9709595b412ef2",
    "profiler": "8a3f5bc1cba31d366c7ea3f0149e04917c07fe7677aa609ce6f05f5c8decbd6d",
    "verifier": "e244dff1273053878dd34fc26f6b96acc3faff466e3b2bdbf9a80920820ba8e0",
}

# ``manifest.json`` の各 ``roles.<name>`` entry 全体を固定する独立 pin。schema 単体だけでなく
# model、consumer、forbidden classes、capability lowering、projection instructions を含む。
# 値は manifest renderer から自動更新してはならず、契約変更を人間レビューした時だけ更新する。
ROLE_MANIFEST_SHA256 = {
    "auditor": "8110e01edc701803d2c5565d537ba9eceffe488fd44ef47eb76d5bc97307f4f9",
    "axis-proposer": "57d9bd635e99c5eab2e7fb852043446ffe6c0aff1a1fa48ed5b724c4ae041ad1",
    "calibrator": "775d8e9fa963b6f2d895ffcb7be14a7ce487ea82911fd797f4f6bb840d8e9186",
    "coder": "2af1a88e8f8cae73e251d067ba47ea4b1acd5457083111d3dc719914d199e136",
    "coder-v4-autonomous": "1c1611da8e9d30146155c36dd0c90ad371ec4611076ac39f24f74a8f48322017",
    "coder-v4-autonomous-sort": "0516335248dd542372ba4a420835c2451ea816b2aadc78cacaa1c388bd2252fa",
    "coder-v4-autonomous-trigger-gating": "6c6f17d7397969f0902ee34929f65e3e53281f98ec97071963647ce7f990f4dc",
    "critic": "efbb2961dca75c14afa97462b4664065aac90621a184f63d6bc017f1d050cc42",
    "critic-experiment": "69dd9033640393fbde6a51c8f7d606e7780b91393e8d2829d530e5c3d2156b0e",
    "planner-v4": "9e142881783337414af0c8d239541fc8f2b0a2892b160d58940602c93615dd17",
    "profiler": "61a3cc067886a042bcf076fc1b2494bf26bb5e6e64bcd6a6e8bc01a77071ec30",
    "verifier": "18216687be26dbb5de59d4cf84691c85f50820fbd4af33edef18ad947493884e",
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
    "coder-v4-autonomous-sort": "c0e5855da78d3f07fe24485c1e2c4324a2fb454c0d8c2748a3e86b156f13df00",
    "coder-v4-autonomous-trigger-gating": "b79ff4897751172ceabf135875bcde34057680531cacea19f2de1779c9260d0c",
    "critic": "b029016d0d8ca4b3ccf8f1ca3ab719d611f312d9a2ad7f88a361ba6d399b3fa1",
    "critic-experiment": "cc698590354ca22332f54ccb965ff67f8f093eca9a3c46063d3a8779e9956761",
    "planner-v4": "e1c82ce9410df83eb54db2dd491a11e3e303e43a83fefe44ce249a2e287e03e8",
    "profiler": "208aa13e1acb0b281dc0de3e811c2ec4c9483217d9ec63a2ed9c69fa5fd16347",
    "verifier": "21906b5078651cf0b99b831b8be96aeca064a45c4a45ad42c6417238c129bdc3",
}

# ``manifest.json`` から生成してはならない独立 review pin。required field だけでなく
# nested type/minimum/additionalProperties まで含む canonical JSON 全体を固定するため、
# manifest と generated adapter を同時に弱めても checker はここで fail-closed になる。
SCHEMA_SHA256 = {
    "auditor": {
        "input": "1b74afcd7a4100722d600004e3dba20245e548750937b87506c1a6fe55f68094",
        "output": "9e066eb0fb92df9fb87e512bce30499becd51b9a2142b81c078cc66016957b57",
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
    "coder-v4-autonomous-sort": {
        "input": "7a1946e72e7b57e1888af72a0f2c30c4e204a42556dbbd4ea60b4e9053f1d510",
        "output": "680f2ed894f9df0d836c22750ea5e5506580dcfc4104b7b176d65425ec96cf06",
    },
    "coder-v4-autonomous-trigger-gating": {
        "input": "7f274f740ee0a94e8176d9a3be408b935600f4ffe1ee256339eb43ebe395ac0d",
        "output": "bcbb348cc0d42e14ae435d7155904fae31cac224e17083c218b1f0a6dd7cc8b0",
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
    "DEVELOPER_INSTRUCTION_TEMPLATE_SHA256",
    "DESCRIPTION_SHA256",
    "ROLE_MANIFEST_SHA256",
    "ROLE_IO_CONTRACTS",
    "SCHEMA_SHA256",
    "SOURCE_FILE_SHA256",
]
