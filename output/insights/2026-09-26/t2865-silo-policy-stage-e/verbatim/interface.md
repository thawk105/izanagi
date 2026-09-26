# 単位間 interface (段 4 裁定で固定、2026-09-26、親)

正本は同 dir の `s4-ruling.md`。ここは実装子 core と role の両方が守る契約だけを書く。変える必要が出たら実装せずに報告して止まること。

## 1. proposal file (driver の `--run-iteration` / `--preview-diff` が読む JSON)

- top: required `{"coder", "auditor"}` だけ。optional なし。`planner`・`value`・`prior_critic_reverse`・`strategy_summary` を含む file は拒否。
- 全階層の重複 key は最外層の読込 (`object_pairs_hook`) で拒否。
- `coder` (C++ 形、契約名 `policy-cpp`): required `{"axis": "silo-function-policy", "implementation": str}`、optional `{"justification": str, "confidence": "high"|"medium"|"low"}`。他 key は拒否。
- `coder` (IR 形、契約名 `policy-ir`): required `{"axis": "silo-function-policy", "ir": object}`、optional は C++ 形と同じ。`ir` は `silo_policy_ir.parse_policy_ir` が受ける tagged object。
- `auditor`: 既存 `auditor_gate.parse_auditor_dict` の形 (required `{"verdict", "diff_digest"}`、optional `{"violations", "nits", "proposed_tests", "uncertainty"}`)。violation type の上限は本 driver だけ 26 (既定 21 は不変)。
- 形は CLI (`--form cpp|ir`) で選び、search_config に焼く (形ごとに別 campaign)。proposal の形と CLI の形が違えば拒否。
- auditor digest の対象: C++ 形は `implementation`、IR 形は `render_policy(parse_policy_ir(ir))` の本文を、骨格 patch 適用後の source に入れた `working_diff` (既存 `L.quarantine` の返す diff) の UTF-8 bytes の sha256 (`compute_diff_digest`)。

## 2. IR の tagged object (`parse_policy_ir(document: object) -> PolicyIR`)

- 既存 dataclass (`silo_policy_ir.py` の `Const`・`Reason`・`Attempt`・`StateRef`・`Compare`・`Select`・`Min`・`Max`・`SatAdd`・`SatSub`・`Shift`・`StateField`・`AbortHook`・`LockHook`・`CommitHook`・`PolicyIR`) と 1 対 1。各式 object は `"kind"` に dataclass 名を持ち、他の key は dataclass の field 名と完全一致。
- root・hook・状態 field を含む**全 object** が `"kind"` (dataclass 名、例 `"PolicyIR"`・`"AbortHook"`・`"StateField"`・`"Const"`) を持ち、残りの key は dataclass の field 名と完全一致。tuple 型の field は JSON 配列。
- 数値 field (`StateRef.index`・`Shift.amount`) は exact `int` (bool は拒否)。`Const.value` は `Const.type` に一致する exact 型だけ (`u32`/`u64` は bool でない int、`bool` は bool、`reason`/`action` は既存値域の str)。`next_state` は key 必須で値は `null` か配列 (省略は拒否)。文字列 enum は既存の値域だけ。未知 kind・未知 key・欠落 key・範囲外は `ValueError`。最後に `validate_ir` を必ず呼ぶ。
- serializer は作らない。

## 3. coder role の入力 (driver の `make_policy_coder_input(layout, *, baseline, critic_diagnosis=None)` が出す JSON)

必須 key (role の入力例はこの 5 key と完全一致):

```
{
  "leakproof_context": str   (src/coder-leakproof-context.md の内容),
  "policy_spec": str         (固定の接続仕様: 3 hook の署名・状態型・観測・上限・受理契約 policy-C++ v1 の要約。driver が固定 file から読む。偵察・小比較の情報を含まない),
  "baseline": {"throughput_tps": number, "abort_rate_pct": number},
  "recon_projection": {"binary": bool, "scope": str},
  "self_history": [ {"iteration": int, "implementation": str, "ir": object|null,
                     "outcome": str, "reject_subtype": str|null, "reject_rule_id": str|null,
                     "verifier_digest": object|null} ]
}
```

任意 key: `"critic_diagnosis"` = 既存 `p3_s4_loop.k2_critic_diagnosis_from_bytes` と同じ 6 文字列 field (`data_boundary`・`source_sha256`・`attribution`・`recommend`・`avoid`・`uncertainty`)。無い回は key ごと出さない。role の入力例には書かず、本文で説明する。

- `recon_projection` は `output/env/pegasus/calibration/silo_function_policy_recon/projection.json` (module 定数の固定 path) から、top key `{binary, scope, excluded}` の完全一致・`binary` exact bool・`scope` str を検査して 2 field だけ出す。
- `self_history` は当該 campaign layout 内の履歴 file だけから作り、justification を含めない。
- `policy_spec` の文面は core 実装子が固定 file `orchestrator/campaign/silo_function_policy_coder_spec.md` として作る。

## 4. coder role の出力

- C++ 形 role: `{"proposal": {"axis": "silo-function-policy", "implementation": "<namespace izanagi_silo_policy の本体 = marker 内の C++>", "justification": "...", "confidence": "high|medium|low"}}`
- IR 形 role: `{"proposal": {"axis": "silo-function-policy", "ir": {<§2 の tagged object>}, "justification": "...", "confidence": "high|medium|low"}}`
- 親は `proposal` を proposal file の `coder` に写し、auditor の出力を `auditor` に置く。justification は履歴 file に残るが coder 入力と critic には渡らない。
