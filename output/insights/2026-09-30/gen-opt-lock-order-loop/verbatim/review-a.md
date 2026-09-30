## 総括

**NO-GO。** 要求つき build は出口再照合で常に不一致となる。さらに、その不一致を直しても、成功した campaign の `verify_result` は driver に渡らず、certified 行を作れない。実装子の試験は未実走で、親の焦点走結果も未受領。

## 所見

1. **must-fix — 要求つき build の出口再照合が必ず失敗する。** [source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/source_digest.py:2479) は要求時に D5 証拠束を capture するが、[buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/buildcache.py:3679) の再取得は要求を渡さず、3692 行で証拠束を含む snapshot と比較する。新規 build と cache hit の両方で不一致になる。**影響:** 適格な候補も build 出口で停止し、certified の受理集合が空になる。**修正:** 出口再照合にも入口と同じ要求条件を渡し、証拠束を含む snapshot を比較する。要求ありの新規 build と cache hit を試す。

2. **must-fix — 成功結果から driver の certified 行へ到達できない。** [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/pipeline.py:2235) は各反復で `res.verify_result` を `None` に戻し、成功時の `_project_repetition_outcome` は値を戻さない。設定するのは abort 時の 2254 行だけ。[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/p3_s4_loop_lock_order.py:302) は `None` を `verifier-result-missing` にする。**影響:** campaign が certified でも専用 history は拒否行となり、成果物の参照が食い違う。**修正:** 成功した全 workload・全反復の検証結果を、既存呼出しの bytes を変えない要求時限定の経路で driver に渡す。

3. **should-fix — certified 行の条件を全反復に照合できていない。** [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/p3_s4_loop_lock_order.py:142) は単一の結果だけで `required`・版・D5・`certified` を判定する。[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/pipeline.py:712) の反復 payload にも gate 節はない。**影響:** 所見 2 を単一結果の保持だけで直すと、別 workload・別反復の要求漏れを確認せず certified 行を作りうる。**修正:** 要求時の各 verify 結果に閉じた gate 判定を保持し、期待反復数と全件の四条件を確認してから行を確定する。

4. **should-fix — history の証拠種別が実態を表さない。** [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/p3_s4_loop_lock_order.py:129) は登録簿 digest が `None` なら、結果の出所に関係なく `fixture` と書く。逆に試験で fixture 登録簿を差し込むと `registered` になる。**影響:** 拒否行や coder 入力の証拠種別が誤り、台帳上で fixture と本番登録の参照を取り違える。**修正:** 証拠種別を呼出し経路から明示して閉じた値で記録する。未登録は fixture と呼ばない。

静的確認では、flag 強制は Silo の非ゼロ `SILO_ORDER_VARIANT` に限定され、他 protocol や flag のない既存 genome へ波及しない。要求なしの snapshot serialization は旧 key 集合を保ち、capability・receipt・lock の通常経路に新 field を加える変更も見当たらない。D5 の snapshot 評価は disk を再読せず、証拠束欠落時は `unavailable` で certified にならない。小モデル関門は登録簿 `None`、digest、場面、完了理由、構成数、witness、反例を拒否し、反復関数に登録簿の差替え引数はない。拒否時には `run_campaign` を呼ばない。inventory の追加 call site 数は実装各 1 件と一致し、`materializer_admission` の追記も 1 項目。これらは静的確認であり、試験結果ではない。

## 変異 M1〜M12 の単一理由性

| 変異 | 外す箇所と赤になる test | 単一理由性 |
|---|---|---|
| M1 | pipeline の flag 強制 → `test_m1_flag_forces_required_evaluate` | 明示要求なし・flag=1。driver の明示要求は遮らない |
| M2 | loop の要求転送 → `test_m2_explicit_requirement_passes_run_campaign` | flag=0・明示 True。flag 強制は遮らない |
| M3 | capability の要求転送 → `test_m3_required_capability_rejects_absent_gate_file` | gate file 欠落が単独の差 |
| M4 | snapshot D5 を disk 読みに戻す → `test_m4_required_d5_uses_snapshot_not_disk` | capture 後に disk を変更して差を作る |
| M5 | 要求なしにも証拠束を serialize → `test_m5_unrequested_snapshot_legacy_bytes` | 旧 JSON の key/bytes 比較で検出 |
| M6 | 登録簿 `None` の拒否 → `test_m6_unregistered_registry_rejected` | 他の結果条件は正常 |
| M7 | 独立 digest 照合 → `test_m7_result_digest_cannot_supply_expectation` | digest だけを変更 |
| M8 | `stop_reason` 照合 → `test_m8_complete_max_states_is_incomplete` | `complete=True` を維持 |
| M9 | 必須場面照合 → `test_m9_required_scenario_missing` | 場面欠落だけを入力 |
| M10 | 反例拒否 → `test_m10_counterexample_rejected` | schema 有効な反例を使用 |
| M11 | 閉じた反例投影 → `test_m11_counterexample_projection_has_exact_keys` | validated 入力を使い投影だけを検査 |
| M12 | driver の `required` 照合 → `test_m12_required_false_cannot_certify` | 他の認証 field は正例 |

この表は試験入力の静的評価である。**M1〜M5 を含め、赤の実走と変異 matrix は未確認。** また M1 の通常 build 経路は所見 1 が先に遮るため、その経路全体の生存証明にはならない。

## 裁定との食い違い

- 段 4 U-A の「同じ条件で build 出口まで snapshot を再照合」は、所見 1 のとおり未達。
- 段 4 A3 の「各 verify 結果で四条件を確認して certified 行を作る」は、所見 2・3 のとおり未達。
- 追補裁定の登録簿差替え禁止と `materializer_admission` の 1 項目追加は満たす。現行 pin と本番 digest 未登録のため本番 certified を主張できない、という裁定上の限界も残る。