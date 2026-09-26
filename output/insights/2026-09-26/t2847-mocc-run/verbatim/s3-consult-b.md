## 所見

- **B-01｜must-fix｜[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:39)、[s3_mocc_lock_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/campaign/s3_mocc_lock_coverage.py:139)、[mocc_trace_v1_policy.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/tools/pegasus/mocc_trace_v1_policy.json:18)**  
  plan は `_load_policy()` の流用を前提にするが、同関数は policy の `new_oid` が旧 pin `e9e477ca…` と一致することを要求する。policy を pin C に変えず、driver 定数も変えない方針のままでは起動器は依存物準備前に停止する。**提案:** repo 外起動器で旧 policy のコンパイラ・依存物の束縛を保持しつつ、mocc commit の束縛を pin C と照合する局所 policy 読込経路を明記する。`_load_policy()` の無検査流用は不可。

- **B-02｜must-fix｜[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:37)、[s3_mocc_mutation_proof.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/campaign/s3_mocc_mutation_proof.py:320)**  
  `_variant_run()` は timeout 時に verifier を呼ばず、`finally` で trace directory を削除する。plan の「停止 run の部分 trace を別欄で verify」と「raw を job dir に保存」は、この関数をそのまま呼ぶだけでは実現しない。通常 run でも `_run_trace()` は一時 directory を作り、stdout/stderr を結果へ保存しない。**提案:** 起動器側で trace の寿命と受動保存を管理する経路を設計し、通常 run の判定は既存 `_verify()` と同じ argv・rc 規則で行う。部分 trace の結果は本判定から隔離する。

- **B-03｜must-fix｜[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:63)、[brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/brief.md:5)**  
  brief の完了判定は 6 行を五分類で実測記入することだが、plan は V25 の主 cell に「停止、verdict なし」を期待し、既存 4 本の発火未確認 S も五分類への算入を保留する。これは科学的には慎重だが、現在の完了判定とは両立しない。**提案:** 事前に「停止／発火未確認」を判定不能として表に残す条件と、その場合に 6 行をどう完了扱いするかを明文化する。証拠のない S を未発生や盲点へ押し込まない。

- **B-04｜must-fix｜[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:42)、[test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_ccbench_spawn_sites.py:3553)**  
  plan が挙げる `:2912` の在庫照合だけでは足りない。新 macro 2 件で patch 由来 interface が 57→59 件になるため、`test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` の `proven-unreachable: 53` と `covered: 57`、`test_define_sink_cross_product_t2520_certify_entry_removal` の `proven-unreachable: 43` も赤になる。**提案:** 分類の根拠を確認して両 test の固定件数を更新する。[T-2849] の `t2849-unit-a` は**同じファイルのこの件数行**を既に変更しており、取り込み時に直接競合する。

- **B-05｜should｜[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:69)、[mutation-run README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/output/insights/2026-09-23/t2847-mutation-run/README.md:58)**  
  139～194 秒は前回の *silo* で 4～5 build を含む job の Elapse であり、pin C の mocc 10 build、condition gate、依存物準備、V25 の停止を測った単価ではない。通常実走 800～1,200 秒の根拠は弱い。一方、plan の内訳をそのまま足すと最大約 1.47 node 時間で、直ちに 2 時間超とは言えない。**提案:** J1 の焦点走で mocc の build・gate・run の実時間を分けて取得し、J2～J4 と受入再試行分を投入前に再計算する。J3 の 20 分 walltime は停止 4 本で 480 秒を使うため、準備・build の実測を含めて再確認する。

- **B-06｜should｜[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:16)、[s3_mocc_mutation_proof.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/campaign/s3_mocc_mutation_proof.py:418)**  
  `compute_checks()` は旧計装 patch を touch set に必須とし、trace0 の三 check も旧 pin の「計装前後」比較に結び付く。plan はこの問題を認識している。ただし「既存 checks の述語を再計算」と書く範囲には、`_matrix_complete()` が全 36 run と全 verifier 完了を要求する点も含まれる。J1/J2 分割や V25 timeout に流用できない。**提案:** 旧 check 名を全体の `all_pass` に流用せず、job ごとの観測・完走条件と pin C 用 touch set を明示した結果欄にする。

- **B-07｜should｜[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:8)、[brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/brief.md:20)**  
  plan が brief の「発火証拠のない S＝未発生」を退けた点は妥当。source で示せるのは V16 cold の hot 分岐未到達であり、default や他の S の発火・不発火は証明できない。また brief の `git apply --check rc=0` は適用可能性の証拠に限られ、pin C 上での変異機構の発火や結果の帰属を保証しない。**提案:** 先行実測を一般化せず、発火未確認を独立して記録する。

- **B-08｜should｜[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:6)、[request.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/request.md:5)**  
  V25 の SIGTERM handler、停止 trace の追加 verify、TRACE=0 の新しい照合は、依頼の「本題の実装だけ」より広い。特に signal handler は発火証拠のための新しい実行経路を patch に足す。**提案:** 停止時の証拠欠落はそのまま判定不能と記録し、追加診断を採る場合だけ、その必要性と判定への不使用を事前に限定する。TRACE=0 確認も既存の規律確認に必要な最小範囲へ絞る。

- **B-09｜should｜[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:77)、[test_screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_screening_driver.py:659)**  
  変異候補 5 の「既定値を 0 以外にする」は、現行の exact set test では殺せない。test は `_CONDITION_DEFAULTS` の**キー集合**を照合し、新 macro の値は同じ辞書から読み出して request を作るため、値の誤りと期待値が一緒に動く。候補 1・2・3 も複数の赤 node を生むため、赤 node 単位では帰属が一つに絞れない。**提案:** 候補 5 は独立した「既定値 0」の期待を既存表 test に足した後で採用する。変異結果は node ではなく変更した誤り単位で帰属させる。

## 赤になる test の一覧

新 patch と macro を追加し、plan 記載の表を未更新のままにした場合の静的予測である。テストはこの段では実行していない。

| test・検査 | 赤になる条件／必要な対応 |
|---|---|
| [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_condition_meaning_gate.py:45) `test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches`、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_condition_meaning_gate.py:3448) `test_v1_domain_and_claim_boundaries_are_exact` | witness 順序・site 数・supply domain の固定表。plan 記載あり。 |
| [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_p3_s4_loop.py:8463) `test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted` | `patches/*.patch` の `IZANAGI_` token を path ごとの表と照合。plan 記載あり。 |
| [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_ccbench_spawn_sites.py:2912) `test_patch_define_inventory_matches_condition_gate_registry` | patch glob で新 macro を発見する。gate 登録が欠けると赤。plan 記載あり。 |
| [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_ccbench_spawn_sites.py:3553) `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_ccbench_spawn_sites.py:3580) `test_define_sink_cross_product_t2520_certify_entry_removal` | interface 件数の固定値が 2 増分ずれる。**plan の具体的列挙から漏れ**、かつ `t2849-unit-a` の変更箇所と重なる。 |
| [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_screening_driver.py:659) `test_screening_condition_requests_cover_exact_define_specs` | screening の既定値表にキーがなければ赤。値が非 0 でも、この test だけでは赤にならない。 |
| [patches/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/README.md:14) | test ではないが、冒頭の「broken-mocc 3 本」と旧 preimage 説明、既存節の旧 pin 前提を、新規 2 本を説明する際に混同しない対応が必要。 |
| [check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/tools/check_docs.py:125) | `patches/README.md` の mocc patch 件数・macro 集合を照合する検査ではない。新 patch の追加だけで赤になる根拠は見つからなかった。 |
| [test_mocc_mutation_proof.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_mocc_mutation_proof.py:347)、[test_mocc_proof_surface.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_mocc_proof_surface.py:31) | 旧 driver・旧 JSON の固定 patch 集合を検査する。plan どおり旧 driver を変更しなければ、新 patch 追加だけでは赤にならない。 |
| [test_mocc_template_proof.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/tests/test_mocc_template_proof.py:94) | patch glob は mocc の EVOLVE marker を探す条件付き検査。予定する V25/V34 patch に marker を加えない限り、新 patch 追加だけでは赤にならない。 |

## 未確認点

- pin C 上で V25 の限定 gate が発火する頻度、停止の相手が別 worker か、V34 の境界値が評価されるかは静的には決まらない。
- `_resolve_toolchain()` のコンパイラ digest と `_prepare_dependencies()` の外部 cache・依存物 HEAD が実行先で一致するかは未実測。policy の **pin 不一致は静的に確定**している。
- job ごとの実 Elapse、J3 の 20 分内完了、受入再試行を含む総 node 時間は実測後に再見積りが必要。
- `t2849-unit-a` との同一行の最終的な統合値は、両 branch の取り込み順とその時点の patch 集合で確定する。

## 総括

現 plan のままでは旧 pin に束縛された policy で起動器が止まり、`_variant_run()` の流用では停止 trace と raw を保存できない。登録 test には `test_ccbench_spawn_sites.py` の固定件数 2 箇所の漏れがある。これらを直した上で、停止・発火未確認を五分類へ無理に算入しない完了条件を先に定める必要がある。