## 所見ごとの対応表 (P1〜P5)

pytest は実行していない。差分と HEAD の静的検査に加え、P2 の純粋述語だけ副作用なしで評価した。

| 所見 ID | 判定 | 根拠 file:line | 判定理由・成果物影響 |
|---|---|---|---|
| P1 | closed | [loop.py:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:643)、[loop.py:673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:673)、[loop.py:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:690)、[loop.py:814](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:814)、[test_reflux_campaign_issuer.py:754](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/tests/test_reflux_campaign_issuer.py:754) | 元の4点中、skip 2点は issuer 呼出し自体を削除して直接拒否、残る2点は call-site guard 内でのみ引数を評価する。番人 `EvalResult` は line 814 の guard を外せば `build_attempt_id` 参照で確実に落ちる。originless の record、WAL、受理集合を増やさない。 |
| P2 | partial | [reflux_result_evidence.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/reflux_result_evidence.py:238)、[reflux_result_evidence.py:1223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/reflux_result_evidence.py:1223)、[execution_guard.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/execution_guard.py:242)、[execution_guard.py:265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/execution_guard.py:265)、[test_reflux_campaign_issuer.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/tests/test_reflux_campaign_issuer.py:319) | issuer は実 `receipt_matches_contract()` を通し、中心正例も実 `_authorize_measurement()` と v2 builder を通る。probe seam は observed 値だけを置換し、verified profile/hash と expected/observed 再検算は残る。しかし issuer が mode と calibration を未束縛の context から受け取るため、required 契約から作った v1 receiptを `context.attestation_mode="none"` として渡すと検証が `True` になる。required attestation を欠く recordと provenance が発行可能で、issuer の受理集合と後続参照の真正性が広いまま。 |
| P3 | closed | [loop.py:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:643)、[loop.py:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:689)、[test_reflux_campaign_issuer.py:931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/tests/test_reflux_campaign_issuer.py:931) | identity 解決失敗側と通常 recovery 側の両 skip は context ありで無条件拒否し、`_result_evidence_attempt_id()` は削除済みかつ参照0件。過去 WAL と現在 receipt を混ぜた record は発行されず、台帳候補 member が増えない。 |
| P4 | closed | [test_reflux_campaign_issuer.py:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/tests/test_reflux_campaign_issuer.py:688)、[test_reflux_campaign_issuer.py:710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/tests/test_reflux_campaign_issuer.py:710) | file、stage、payload-key の期待値は test 内の具体的 literal であり、context ありの出力や実装定数から生成していない。同じ frame を両経路へ足す回帰を検出し、originless の成果物集合を固定する。 |
| P5 | closed | [test_reflux_campaign_issuer.py:931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/tests/test_reflux_campaign_issuer.py:931)、[test_reflux_campaign_issuer.py:1006](/work/1/SFC/tanab/izanги/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/tests/test_reflux_campaign_issuer.py:1006)、[test_reflux_campaign_issuer.py:1127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/tests/test_reflux_campaign_issuer.py:1127)、[test_reflux_campaign_issuer.py:1219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/tests/test_reflux_campaign_issuer.py:1219) | terminal skip 2形、identity-error、eval-exception の attempt ID あり・なしを context ありで駆動し、拒否前後の evidence file 集合を比較する。拒否経路から record、projection、source が残らないことを固定する。 |

P2 の具体的な残存反例は次の通り。

- `build_receipt(required_contract)` は v1 receipt を生成できる。[execution_guard.py:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/execution_guard.py:204)
- issuer は契約本体ではなく context の `attestation_mode` を verifier へ渡す。[reflux_result_evidence.py:1223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/reflux_result_evidence.py:1223)
- `receipt_matches_contract(required-contract-hash付きv1, attestation_mode="none")` の純粋評価結果は `True` だった。
- production `run_campaign()` 自体は required 時に v2 receipt を作るため、この組合せを自然生成しない。[loop.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:185) 残る穴は公開 issuer の直接呼出し面である。

## fix が新たに作った破れ

新規 regression の反例なし。

既存期待値の弱体化も見当たらない。任意 schema receipt は既存 verifier が受理する receipt へ強化され、originless の自己比較は literal baseline へ置換されている。

ただし P2 は「新たな受理拡大」ではなく、fix 前から存在した広い受理集合を完全には閉じていない partial である。

## 変異事前登録 v2 の最終判定

- M1: 成立。`verify_result=outcome.verify_result` の除去だけで typed 保持が失われ、他層に復元経路はない。予測 node:

  - `orchestrator/tests/test_pipeline_verify_result_retention.py::test_local_rejected_repetition_retains_exact_verify_result_and_wal_binding`
  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_real_run_campaign_issues_rejected_record_and_originless_is_inert`

- M2: 成立。`_abort()` の exact-type gate だけが dict/subclass を拒否する。予測 node:

  - `orchestrator/tests/test_pipeline_verify_result_retention.py::test_abort_rejects_non_exact_verify_result`

- M3': 不成立。要求された「projection 前に `_admit_verify_fanout_result()` の戻り値を直接見る専用 node」がなく、現 node は pipeline 終端だけを見る。非 exact 値を入れる変異は M2 に拒否され、wire から exact `VerifyResult` を作る変異は一意に定義できない。予測 nodeなし。再照準先:

  - 新設 `test_admitted_remote_fanout_abort_has_no_typed_verify_result_before_projection`
  - `_admit_verify_fanout_result()` の abort return 直後を直接検査する。

- M4': 成立。source ref path だけを live WAL にすると snapshot writeは残り、単独で path不変性を破る。予測 node:

  - `orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_issues_real_wal_projection_and_resolves_interval`
  - `orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_snapshot_survives_append_while_live_ref_breaks`

- M5: 成立。`byte_start=0` は2番目 attempt だけで非等価となり、resolver の interval対projection照合が落とす。予測 node:

  - `orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_preserves_nonzero_offset_for_second_attempt`

- M6a: 成立。derive を最初の content write より後へ移すと、非 exact typed 拒否時の file snapshot が単独で変わる。予測 node:

  - `orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_nonexact_verify_result_before_writes`

- M6b: 不成立。不正 `expected_record_path` と file 0件を組み合わせる node が現物に存在しない。予測 nodeなし。再照準先:

  - 新設 `test_campaign_producer_refuses_wrong_expected_record_path_before_writes`
  - `dataclasses.replace(context, expected_record_path=...)` を渡し、前後 snapshot 完全一致を検査する。

- M7': 成立。mode-none producer 正例と同じ有効 WALへ、`None` の代わりに自己申告 v1 dict を置くと issuer が進むため、receipt absent負例だけが落ちる。予測 node:

  - `orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_absent_execution_receipt_before_writes`

- M8': 不成立。context-none branch が複数あり、helper側 `context is None` を変えても call-site guard に mask される。予測 nodeを一意化できない。再照準先:

  - [loop.py:814](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:814) の normal-result guard の `else` だけに marker write を置く exact 変異。
  - 予測 nodeは `orchestrator/tests/test_reflux_campaign_issuer.py::test_originless_campaign_has_legacy_literal_artifact_and_wal_shape`。

- M9a: 成立。fresh identity-error の context 分岐から issuer 判断を除去すると、後続拒否はない。予測 node:

  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_identity_error_terminal_is_explicitly_refused`

- M9b: 成立。identity 解決失敗後の accepted stock terminal拒否は独立した直接 raise である。予測 node:

  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_accepted_terminal_recovery_is_refused_without_new_evidence[True]`

- M9c: 成立。通常 accepted terminal recovery の拒否も独立した直接 raise である。予測 node:

  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_accepted_terminal_recovery_is_refused_without_new_evidence[False]`

- M10a: 不成立。`len(genomes)` gateを外しても、現在の mode-none context は後段の receipt gateで同じ入力を拒否する。現 nodeは例外 message差で赤になるだけで、受理集合上は過剰決定。予測 node:

  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_context_shape_rejects_multiple_genomes_and_balanced_before_writes`

  再照準先は `_validate_result_evidence_context()` を直接呼ぶ multiple-genome専用 node。

- M10b: 不成立。balanced gateを外しても同じ mode-none receipt gateが後段で拒否し、M10aと同一 node内に埋め込まれている。予測 node:

  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_context_shape_rejects_multiple_genomes_and_balanced_before_writes`

  再照準先は `_validate_result_evidence_context()` を直接呼ぶ balanced専用 node。

- M11: 成立。[_issue_campaign_result_evidence()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:309) 内の public issuer callだけを catchして returnすれば、外側に同じ拒否層はない。予測 node:

  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_real_run_campaign_issues_rejected_record_and_originless_is_inert`
  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_identity_error_terminal_is_explicitly_refused`
  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_context_eval_exception_is_refused_without_result_evidence[False]`
  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_context_eval_exception_is_refused_without_result_evidence[True]`

- M12: 不成立。現物には guard が [loop.py:673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:673) と [loop.py:814](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2437-record-issuer/orchestrator/campaign/loop.py:814) の2つあり、前者だけを外しても番人 nodeは通る。再照準先は line 814 の guard除去へ exact化する。その場合の予測 node:

  - `orchestrator/tests/test_reflux_campaign_issuer.py::test_originless_campaign_does_not_evaluate_issuer_only_attributes`
  - `orchestrator/tests/test_paper_story_a2_certification.py::test_official_run_observes_dependency_receipt_after_condition_prebuild`
  - `orchestrator/tests/test_paper_story_a1_paired.py::test_a1_exact_marker_routes_loop_to_dedicated_replay_and_append`
  - `orchestrator/tests/test_t1416_backoff_compiler_binding.py::test_run_campaign_forwards_expected_toolchain_to_evaluate_for_each_genome`

登録から外すべき現行変異は M3'、M6b、M8'、M10a、M10b、M12。各再照準を実装・node化してから再登録が必要。

## 裁定パッケージ候補 (scope 外の real な所見)

新規候補なし。P2 は本 wave scope 内の未閉塞 blocker であり、scope 外へ送るべき所見ではない。

## 総括 (NO-GO と 1 行の理由)

**NO-GO** — P1、P3、P4、P5 は閉じたが、P2 の required契約と context指定modeの束縛が未閉塞で、さらに16変異中6件が現物上の単一理由変異として成立していない。