## Blocker 1: inventory 判定不能が orphan-stop を迂回する

**主張:** timeout 後の inventory 取得が例外になると `result` が返らず、local mutation は latch も sidecar も作らず source を復元する。実際には qsub 済みでも、孤児 job が復元後の bytes を読む経路が残る。inventory が空または差分なしならさらに悪く、通常の terminal `TIMEOUT` になる。

**根拠 file:line:** `tools/mutation_harness.py:1640-1645`, `tools/mutation_harness.py:1838-1848`, `tools/mutation_harness.py:1895-1937`, `tools/mutation_harness.py:1662-1666`, `tools/mutation_harness.py:2805-2808`

**深刻度:** blocker

**成果物影響:** 実際に投入済みの変異が復元後 bytes で走るか、未実行扱いの `TIMEOUT` として `completed` に入り、KILLED / SURVIVED と分母が誤る。

## Blocker 2: submission directory は qsub の証拠ではなく、追加テスト自身が偽の赤を固定する

**主張:** 正規 dispatcher は submission directory を作った後に `qstat -Q` preflight を行い、そのさらに後で qsub する。したがって preflight 停滞でも `new_dispatch_submission=True` になり、未投入なのに violation と latch を作る。追加 fixture はまさに directory を作るだけで scheduler を一度も呼ばず、その偽陽性を正解として固定している。

**根拠 file:line:** `tools/pegasus/dispatch_compute.py:1532-1536`, `tools/pegasus/dispatch_compute.py:1662-1676`, `tools/mutation_harness.py:277-304`, `orchestrator/tests/test_mutation_harness.py:72-78`, `orchestrator/tests/test_mutation_harness.py:90-91`, `orchestrator/tests/test_mutation_harness.py:936-947`

**深刻度:** blocker

**成果物影響:** 未投入の変異が terminal 台帳に入らないまま wave 全体を rc=2 で止め、検出力台帳を永久に未完了へ倒す。

## Blocker 3: inventory が共有 namespace 全体を数えるため、並行 acceptance dispatch を自分の投入と誤認する

**主張:** inventory は `output/pegasus-dispatch/` 直下の全 directory を列挙し、所有 token、PID、attempt、command identity の束縛なしに集合差を bool 化する。同じ checkout の別 acceptance process が snapshot 間に directory を作れば、local timeout 側が自分の dispatch と誤認する。mutation harness の flock は同 repo の別 harness は直列化するが、直接 `run_tests.py` を使う acceptance process はこの lock を共有しない。

**根拠 file:line:** `tools/mutation_harness.py:1490-1503`, `tools/mutation_harness.py:1601`, `tools/mutation_harness.py:1640-1645`, `tools/mutation_harness.py:2508-2515`, `tools/run_tests.py:940-950`, `tools/pegasus/dispatch_compute.py:1489-1492`, `tools/pegasus/dispatch_compute.py:1535-1536`

**深刻度:** blocker

**成果物影響:** 無関係な走行が一件 directory を作るだけで対象変異の terminal record が消え、検出力台帳と acceptance の双方が偽の赤で停止する。

## Blocker 4: local violation が作った hold を次回 local run が無視する

**主張:** local で `result` のない入口では hold の存在確認より先に return する。また mutation の finally も既存 hold を保全理由にするのは dispatch mode だけである。hold 作成後に orphan-stop sidecar の書込みが失敗した場合、次回 local run は唯一残った create-only latch を無視して source を再変異できる。

**根拠 file:line:** `tools/mutation_harness.py:282-283`, `tools/mutation_harness.py:297-317`, `tools/mutation_harness.py:1895-1899`, `tools/mutation_harness.py:2819-2828`

**深刻度:** blocker

**成果物影響:** 生存中の孤児 job と次の変異が同じ checkout bytes を共有し、各 mutation record の injection evidence と実行 bytes が食い違う。

## Local latch の解除手順が非束縛で、人間の復旧コストが過大

**主張:** local timeout は receipt recovery を行わず `request=None` にするため、hold の `submission_dir` と `request_id` は null になる。それでも復旧文言は対象を qstat で確認して手動削除するよう要求する。さらに worktree wrapper は local sidecar を orphan hold と分類せず、実際には sidecar gate で失敗する `--resume` を案内する。

**根拠 file:line:** `tools/mutation_harness.py:1643-1650`, `tools/mutation_harness.py:226-254`, `tools/mutation_harness.py:2448-2455`, `tools/mutation_worktree.py:1173-1179`, `tools/mutation_worktree.py:1213-1215`, `tools/mutation_harness.py:2613-2615`

**深刻度:** must-fix

**成果物影響:** 人間が全 submission を手作業で照合し、source 復元、hold と sidecar 削除まで行う間、次回投入、source 復元、worktree 廃棄、acceptance probe 掃除が止まり、台帳の完了値を確定できない。

D454 が定める停止範囲は `docs/decisions.md:18987-19003`、実際の acceptance cleanup 拒否は `tools/check_acceptance_reds.py:404-409` と `tools/check_acceptance_reds.py:845-858` にある。

## Dispatch mode と既存 consumer の確認

dispatch mode の timeout、rc=2、terminal 0 件という制御フロー自体は維持されている。ただし before inventory の常時取得と `active_record.new_dispatch_submission` の追加により、sidecar bytes は同一ではない (`tools/mutation_harness.py:1601`, `tools/mutation_harness.py:1640-1649`, `tools/mutation_harness.py:2490-2493`)。production consumer は sidecar または hold の存在だけを見ており、`reason.code == "orphan-hold"` を要求する consumer は見つからなかった (`tools/mutation_harness.py:2613-2615`, `tools/mutation_worktree.py:626-631`)。

既存テスト期待値の反転、緩和、skip、削除はなかった。既存 local `TIMEOUT` 期待も維持されている (`orchestrator/tests/test_mutation_harness.py:879-905`)。既存 submission の再利用も正規 dispatcher では `mkdir` が create-only のため成立しない (`tools/pegasus/dispatch_compute.py:1532-1536`)。runner mode は production CLI 上 local / dispatch の二択で、dispatch timeout は従来の停止側へ入る (`tools/mutation_harness.py:2559`, `tools/mutation_harness.py:282-316`)。

## 総括

blocker は 4 件。  
最優先は、directory 作成を qsub の証拠と見なす判定と、それを正解として固定した fixture の撤回。  
現在の実装は fail-closed の穴と実運用上の偽陽性を同時に持つため、変異台帳と検出力の主張を受理できない。