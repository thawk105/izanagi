判定: **NO-GO**。静的検査のみ。blocker が複数あり、1 本の実 attempt は結線されていません。

1. **blocker — guard/budget admission を偽造できる。**  
   [t810_coordinator.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:225)、[t810_coordinator.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:255)、[t810_guard.py:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_guard.py:59)、[t810_budget.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_budget.py:53)  
   具体入力 → `approved_hostnames` だけ ratified、`qsub`/`budget` は unratified、guard identity は unresolved の policy に、`{"launch_intent_sha256": 正値, "decision":"allow"}` と `{"launch_intent_sha256": 正値, "admitted":true}` を渡すと `prepare_group()` が受理する。schema_version、policy_sha256、guard phase、ledger digest は未検査。  
   成果物影響: 未承認の scheduler 投入が、allow/admitted receipt の digest を持つ正規 manifest として残る。  
   修正: GuardDecision/BudgetReceipt の exact validator を追加し、policy digest・phase=`pre-release`・ledger after digest・decision literal を照合する。

2. **blocker — unratified は全経路 deny ではない。**  
   [t810_coordinator.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:244)、[t810_coordinator.py:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:260)、[t810_pbs_wrapper.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:132)  
   具体入力 → 現行の全-unratified policy は hostname gate で止まるが、hostname だけ ratify すれば、unratified qsub/budget と unresolved guard を前項の receipt で迂回できる。coordinator は canonical qsub generator を呼ばない。  
   成果物影響: 個別裁定されていない project/queue/walltime・予算・T-139 identity で submission receipt が生成される。  
   修正: coordinator の最上流で admission policy 全体を exact load し、全 ratifiable status が ratified でなければ receipt 評価前に deny する。

3. **blocker — wrapper/coordinator は実運用上結線されていない。**  
   [t810_coordinator.py:775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:775)、[t810_coordinator.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:801)、[t810_coordinator.py:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:831)、[t810_pbs_wrapper.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:425)  
   具体入力 → `ready_events`、`ack_events`、`completion_receipts` を qsub 前から config に埋め込める。coordinator は node JSONL を待機・読取せず、wrapper request/PBS script の producer も存在しない。  
   成果物影響: 実ジョブと無関係な事前合成 event から `valid` terminal-state を生成できる。  
   修正: intent から request/script を生成し、submission receipt で束縛した各 slot の create-only JSONL を監視・安定読取する実 consumer を実装する。

4. **blocker — canonical_benchmark_argv の照合が自己参照。**  
   [t810_prereg_v1.json:607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json:607)、[t810_pbs_wrapper.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:464)、[t810_pbs_wrapper.py:712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:712)、[t810_runner_policy.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_runner_policy.py:70)  
   具体入力 → WrapperRequest に `canonical_benchmark_argv=["-thread_num=1"]` を入れると、その値から runner policy が作られ、同じ値との exact 比較を通って実行される。prereg の7引数は参照されない。  
   成果物影響: 凍結条件外の測定値が正規 measurements/terminal に入る。  
   修正: argv は VerifiedT810Preregistration の projection からのみ導出し、その digest を intent/request/runner policy 間で束縛する。

5. **blocker — node receipt の chain と digest が検証されない。**  
   [t810_coordinator.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:349)、[t810_coordinator.py:585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:585)、[t810_coordinator.py:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:593)、[t810_pbs_wrapper.py:427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:427)  
   具体入力 → preflight/start_ack/measurement/terminal をすべて `sequence=0, previous_event_sha256=null` の独立 object とし、`node_receipt_sha256="a"*64` を渡しても受理される。  
   成果物影響: terminal proof が、実在しない／別内容の node-receipt JSONL を参照できる。  
   修正: node JSONL 全体を読み、sequence・previous digest・event 順序を連鎖検証し、receipt field は実ファイル bytes の SHA-256 と照合する。

6. **blocker — post-release failure が terminal_reduced に昇格する。**  
   [t810_pbs_wrapper.py:673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:673)、[t810_pbs_wrapper.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:692)、[t810_pbs_wrapper.py:702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:702)、[t810_coordinator.py:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:601)、[t810_coordinator.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:626)  
   具体入力 → release 後に dependency/module/trace/NUMA が不一致だと、wrapper は start_ack を書いてから測定せず state 2 で終了する。残り12 job が完了すると coordinator は terminal payload を無視して `terminal_reduced` とする。  
   成果物影響: estimator 禁止の state 2 が、estimate 許可の terminal_reduced に変わる。  
   修正: 全 post-release 再検査成功後だけ ack を書き、completion verifier は各 terminal state/reason を ordered-first-match で集約する。

7. **blocker — 凍結 artifact 集合を作らず、presence は自己申告。**  
   [t810_prereg_v1.json:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json:42)、[t810_prereg_v1.json:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json:53)、[t810_pbs_wrapper.py:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:438)、[t810_coordinator.py:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:597)  
   具体入力 → filesystem に `measurements.jsonl` と `estimate.json` が無くても、completion receipt の `actual_presence` に期待 path 文字列を並べれば `presence_valid=true` になる。wrapper は全 event を node receipt 一本へ書く。  
   成果物影響: prereg の exact file set を満たさない output が valid/reduced と記録される。  
   修正: measurements を専用 JSONL へ直列化し、root/slot tree を lstat して expected set と比較し、valid/reduced では estimate.json も必須化する。

8. **must-fix — coordinator の raw evidence 再計算が欠落。**  
   [t810_coordinator.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:394)、[t810_pbs_wrapper.py:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:611)  
   具体入力 → `trace_symbols=["trace_enabled"]`、dependency/module digest 不一致、NUMA 不一致でも、hostname/hash/quiet/argv が正常なら ready barrier は release を返す。  
   成果物影響: trace-enabled または環境 drift した測定を release 後の台帳へ混入できる。  
   修正: 必要な期待値を intent に束縛し、coordinator が全 raw evidence を再計算する。

9. **must-fix — (d2) の肯定証拠が実検査を超える。**  
   [t810_pbs_wrapper.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:118)、[t810_pbs_wrapper.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:227)、[t810_pbs_wrapper.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:518)  
   具体入力 → production は `repo_root=None` で検査するため、`.git` を除いた repository copy 内の絶対 path に対し `roots_repo_external=true` を記録する。  
   成果物影響: receipt が §9.1(d2) を肯定したように読める偽陽性を作る。  
   修正: frozen repository identity/forbidden root を package に渡して照合するか、証明不能な boolean を false に固定して limitation とする。

10. **must-fix — CLI の validator 結線が成立しない。**  
    [t810_coordinator.py:755](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:755)、[t810_coordinator.py:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:901)、[t810_validator.py:1340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:1340)  
    具体入力 → JSON config の既定 `validator_kwargs={}` は必須引数不足で TypeError、全 field を JSON 化しても `approved_git_identity` は GitIdentity dataclass に復元されず不一致になる。TypeError は CLI の catch 対象外。  
    成果物影響: production CLI は正規 attempt terminal を生成できず、テスト seam のみが緑になる。  
    修正: exact JSON config schema と Path/GitIdentity decoder を実装し、validator 呼出し前に完全検証する。

11. **must-fix — limitations の語彙と実限界が一致しない。**  
    [t810_admission_v1.json:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_admission_v1.json:70)、[t810_guard.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_guard.py:15)、[t810_pbs_wrapper.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_pbs_wrapper.py:37)  
    具体入力 → policy は `guard-snapshot-to-release-race-not-eliminated`、guard receipt は別名 `snapshot-to-release-race-not-eliminated`。`execution_mediation_incomplete` は node event にだけ存在し、artifact自己申告・consumer未結線・root外部性未証明は未宣言。  
    成果物影響: report consumer が残存限界を同一事項として集約できず、valid の意味を過大評価する。  
    修正: limitation ID を一つの closed schema に統一し、実装済み検査と未保証事項を policy・receipt・terminal に同じ ID で伝播する。

12. **nit — 規律5に反する未使用面。**  
    [t810_harness_schema.py:544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_harness_schema.py:544)、[t810_harness_schema.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_harness_schema.py:357)、[t810_coordinator.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/t810_coordinator.py:471)  
    具体入力 → `ready` event schema は wrapper が生成せず coordinator も受けず、任意 `expected_node_count` 汎用化と `release_is_still_active()` は production caller がない。  
    成果物影響: 現時点では直接なし。未結線面を実装済みと誤認させ、監査面だけ増やす。  
    修正: 13-node 専用契約へ縮約し、必要な経路は production orchestration へ結線、不要なら削除する。

既存境界については、prereg bytes は main と同一で SHA-256 は `3052af...e404`、terminal state 名も凍結5語と一致しています。registry の追加は sorted closed set 内で、既存 consumer import も増えていません。ただし「既存 consumer がない」こと自体が上記の未結線を裏付けます。

## 総括

- **NO-GO**。blocker 7件。
- guard/budget/qsub の unratified 個別 gate は coordinator から迂回できる。
- coordinator・wrapper・validator を通る実 attempt 経路は存在しない。
- prereg argv、node receipt digest、event chain、artifact presence が実体へ束縛されていない。
- state 2 を terminal_reduced に誤分類でき、禁止 estimator を許可する。
- limitations は実限界を網羅せず、(d2) の肯定証拠は検査能力を超える。
- prereg bytes と registry 追加自体には回帰所見なし。
