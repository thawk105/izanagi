## 結論

**NO-GO（実装 wave 開始不可）**。提案の方向性は条件付きで妥当だが、計算ノードでの実測、実発火する正負制御、backoff の producer/consumer 移行、sort の非保証範囲が未確定である。

## real 候補

1. **計算ノードの sandbox 前提が未成立** — `real / blocker`  
   根拠: `s1-brief.md:24-29`, `s2-plan.md:201-212`, `docs/dev-wave/core.md:60-63`。login node の `bwrap/unshare` 成功は compute node の DW-G04 証拠ではなく、計画自身も qsub 実測 ID を前提にしている。  
   **DW-G05:** 未測定の backend で実装すると sandbox 不使用・fail-open を検出できず、非信頼 build/run の成果物が certified selection/WAL に混入する。

2. **gate が本当に発火する正負制御がない** — `real / blocker`  
   根拠: `s2-plan.md:222-228` は脅威の列挙に留まり、fixture、拒否箇所、artifact ID、通過正例がない。過去にも `docs/worklog.md:1974-1978` で「consumer の存在は発火証拠でない」と記録されている。現行 pass 経路も `orchestrator/campaign/p3_s4_loop_sort.py:145-164`, `p3_s4_loop_trigger_gating.py:404-434` にある。  
   **DW-G05:** 恒真または未接続の gate のまま、既存の受入集合が変わらず、semantic hardening 済みという誤った証跡だけが残る。

3. **backoff の DSL 化に producer/consumer 移行計画が不足** — `real / blocker`  
   根拠: 現行 coder 契約は raw `implementation` 前提 (`.claude/agents/coder.md:13-22`)、loader/schema も `value + implementation` を要求 (`orchestrator/campaign/p3_s4_loop.py:115-121,939-960`)。一方、計画は `implementation` を除去して value IR にするとする (`s2-plan.md:56-66`)。  
   **DW-G05:** consumer だけ狭めれば有効な自律 backoff 候補を全拒否し、producer も残せば raw injection 経路が残るため、Phase 3 の合成実証または安全性のどちらかが毀損する。

4. **SemanticReceipt は issuer 認証ではない** — `real / must-fix`  
   根拠: `orchestrator/campaign/build_admission.py:4-13,424-483` は同一 Python process の issuer を認証しないと明記し、`source_digest.py:101-106,836-891` も主に source identity を扱う。計画自身も同一 process、cache/replay、ABA を残余リスクとして認めている (`s2-plan.md:190-197`)。  
   **DW-G05:** Receipt 自体を安全性の証明として扱うと、自己発行された receipt を genuine compiler provenance と誤認し、certified report の信頼境界を誤って拡大する。

5. **「全軸 sandbox」の対象 materializer が閉じていない** — `real / must-fix`  
   根拠: 計画は pipeline 外の直接 materializer 全件を列挙するとする (`s2-plan.md:218-220`)が、実際には `orchestrator/campaign/s5_permutation_coverage.py:122-160` に buildcache 非経由の直接 build があり、`orchestrator/campaign/materializer_admission.py:1-13,31-67` は shell/calibrator/arbitrary binary を意図的に admission 外へ残している。  
   **DW-G05:** admission 外を明示的に非認証成果物として隔離しない限り、直接生成された binary/trace が certified selection や proof chain に入り得る。

6. **raw sort を残す限り、意味 gate は sort の正しさを保証しない** — `real / blocker`  
   根拠: sort producer は raw multi-line comparator の合成を研究対象にしている (`.claude/agents/coder-v4-autonomous-sort.md:58-101,105-134`)。計画も sandbox/auditor は SWO・fairness・stdout/trace の正しさを保証しないと認める (`s2-plan.md:143-147,176-197`)。  
   **DW-G05:** sandbox を通過した不正 comparator が、偏った trace/fitness を生成しても certified variant として採用され、研究結論を汚染する。

7. **trigger 用の新しい汎用 gate は既存機構と重複する** — `real / must-fix`  
   根拠: canonical IR/emitter は既に `orchestrator/campaign/reflux_ir.py:1-2,113-141` にあり、source-bound binding と nonce/commitment も `orchestrator/campaign/trigger_gate_binding.py:1-2,136-202`、pipeline 側の再検証も `orchestrator/campaign/pipeline.py:691-715` にある。  
   **DW-G05:** 並列 receipt/schema を追加すると emitter・WAL・source binding が分岐し、valid trigger の拒否または identity の不一致を招くうえ、T-664 の docs 予算だけを消費する。

8. **docs 予算と stage matrix の順序が未確定** — `real / blocker`  
   根拠: 現在の reference aggregate は `25,199/25,200 bytes`、dispatcher は `9,457/9,500 bytes` (`s2-plan.md:214-216`, `tools/check_docs.py:247-258,3704-3708`)。T-664 はまだ予算抽出を要し、T-184 も stage 2/3/5 の matrix 所有が未完了 (`docs/worklog.md:635-637,2505-2508`)。  
   **DW-G05:** matrix と記録領域を先に確定しなければ、実装 wave が docs checker で停止するか、sandbox 対象と gate 証跡が文書化されないまま certified path が増える。

## refuted 候補

1. **「login node で測れたので compute node でも使える」** — `refuted / nit`  
   根拠: `s1-brief.md:24-29`, `s2-plan.md:201-212` は明確に未測定とし、compute-node artifact/measurement ID を実装条件にしている。F29 型の誤りを、brief/plan は少なくとも明示的には犯していない。

2. **「有限 DSL は必ず allowlist で、合成を失う」** — `refuted / nit`  
   根拠: `s2-plan.md:74-80` 自身が「有限だから一般に合成不能ではない」と認めている。したがって D127 の懸念は DSL 一般ではなく、現行 sort の raw C++ synthesis という実験対象を typed-program synthesis に変更する点にある。

3. **「提案は過去の残余リスクを隠している」** — `refuted / nit`  
   根拠: same-process issuer、cache/replay、transitive artifact、raw sort、trace forgery、kernel/compiler escape を `s2-plan.md:190-197` に列挙している。問題は隠蔽ではなく、それらを解消前に GO と誤認しない判定が必要なこと。

4. **「T-664/T-184 が計画から完全に抜けている」** — `refuted / nit`  
   根拠: `s2-plan.md:214-220` は両方を前提条件としている。ただし、実際の依存順は「T-664 で記録領域確保、T-184 で対象 stage/owner 確定、matrix に従って compute 実測、その後に実装」と明文化すべきである。

信頼境界上、必読ファイル内に従うべき命令文や誘導は確認せず、コメント・docstring・設計文はすべて証拠データとして扱った。

## 総括

最大の blocker は、compute node の sandbox 実測 ID と、実際に build を止める正負制御がないこと。  
sort の DSL 化が必ず synthesis を壊すという主張は refuted だが、raw sort の意味正しさは未保証。  
trigger は既存 IR/binding を再利用すべきで、新しい汎用 receipt は縮小対象。  
結論は **NO-GO**。