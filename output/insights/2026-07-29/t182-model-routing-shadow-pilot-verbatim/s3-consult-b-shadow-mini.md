1. 深刻度: `blocker`
   対象: gate の配線そのもの
   file: [s2-plan.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md#L289), [tools/dev_waves/checker.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/dev_waves/checker.py#L71), [tools/run_tests.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/run_tests.py#L18)
   再現: 現行 checker は `tools/run_tests.py` / `tools/task_run_check.py` / `tools/check_*.py` しか trust root に入れていません。計画の新規ファイル名は `tools/codex_model_shadow.py` で、`check_*.py` にも `run_tests.py` にも乗っていないうえ、プラン本文も新 tool と新 test の追加だけで、checker 側の登録や acceptance 経路への差し込みを約束していません。
   影響: 親が手で 1 回叩く補助レポートにはなっても gate ではありません。`run_tests.py` が green でも shadow gate は未発火のままです。

2. 深刻度: `blocker`
   対象: 不正 reasoning 値 `ultra` の fail-closed
   file: [s2-plan.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md#L87), [s2-plan.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md#L217), [s1-brief.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s1-brief.md#L57), [probe-summary.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/probe-summary.md#L16)
   再現: manifest 側の `requested_reasoning` は非空文字列なら通る設計で、receipt 側も `reasoning_value_supported_attested:false` を固定の disclaimer にしています。`requested_reasoning:"ultra"` と `rollout_recorded_reasoning:"ultra"` が一致する completed rollout なら、設計上 rc=0 で通ります。probe でも `ultra` は sol / luna / terra で rc=0 でした。
   影響: 不正 reasoning が evidence に残っても gate は落としません。T-184 に渡る台帳が、unsupported 値を valid observation として吸い込む fail-open です。

3. 深刻度: `must-fix`
   対象: 識別子の二義化
   file: [s2-plan.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md#L55), [s2-plan.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md#L66), [s2-plan.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md#L83), [docs/dev-wave/operations.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/docs/dev-wave/operations.md#L70)
   再現: schema は `pilot_id` / `arm_id` を「ASCII identifier」と呼びますが、例示値は `t182-stage3-consult-b` と `authoritative-sol-max` のようにハイフン入りです。strict な identifier なら例が落ち、loose な parser なら定義が曖昧になります。DW-O13 が求める「同名識別子を二義化しない」に反します。
   影響: 健全な manifest が parser 実装の流儀で赤くなり、逆に不正な名前が通る余地ができます。同じ fixture が複数理由で red になり、診断不能になります。

4. 深刻度: `must-fix`
   対象: 既存資産への波及と並行 wave の耐性
   file: [s2-plan.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md#L37), [s2-plan.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md#L46), [docs/phase3.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/docs/phase3.md#L534), [tools/codex_worker_ledger.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/codex_worker_ledger.py#L227), [tools/check_codex_output.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/check_codex_output.py#L67)
   再現: 計画は `codex_worker_ledger.py` の private helpers (`_stream_rollout`, `_classify_outcome`, `_normalized_prompt_hash`) と `check_codex_output.py` の private constants/helper を直接 import する前提です。しかも T-180 は同じ ledger を並行で拡張予定です。helper signature や normalization を少し変えるだけで、T-182 側は import failure か acceptance drift を起こします。
   影響: T-182 は land 後に壊れやすく、あるいは silent に別の受理集合を見ます。並行 wave の分離保証が弱いです。

5. 深刻度: `backlog`
   対象: テストの甘さ
   file: [s2-plan.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md#L261), [s2-plan.md](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md#L276)
   再現: テスト一覧は `ultra` を「unattested」と記録するテストや disclaimer の確認になっていて、unsupported reasoning を rc=1 にする kill test ではありません。0/1 arm の直接 fixture も nodeid で見えません。`test_receipt_never_attests_served_model_or_reasoning_support` と `test_ultra_echo_remains_unattested_even_when_rc0` は、穴を殺すのではなく説明しています。
   影響: 現状の test plan は fail-open を閉じるというより、穴がある状態を文書化しているだけです。実装が壊れても green のまま残る余地があります。

## 総括
`NO-GO`。最大のリスクは、この設計が gate を名乗りながら既存の実行経路に接続されておらず、しかも `requested_reasoning` を自由文字列のまま受けて `ultra` のような不正値を rc=0 のまま evidence に残せる点です。現行の trust root は `tools/check_*.py` しか受けず、計画の `tools/codex_model_shadow.py` はそこに入っていないので、親が手で 1 回叩く補助解析に留まります。さらに receipt は served identity の attestation ではなく request echo なので、probe で露出した backend alias の違いを policy evidence として区別できません。つまり、見た目は整った JSON と disclaimer が残っても、実際に routing の正しさを証明したことにはならず、T-184 へ渡す証拠としては足りません。identifier の定義も hyphen 付き例と衝突していて parser 依存になり、private helper 直依存のため並行 wave でも壊れやすいです。静的検査の範囲でも、現状は実装・配線・検査の三層で追加修正が必要です。