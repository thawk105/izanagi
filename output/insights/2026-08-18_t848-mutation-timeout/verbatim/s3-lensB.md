```text
### 所見 1: local 申告から実 dispatch へ到達し、現行案では偽の TIMEOUT を止められない

主張: 到達可能。`--runner-mode local` は `tools/run_tests.py` の dispatch を禁止しない。S2案も local timeout を無条件に TIMEOUT とするため、穴が残る。

根拠となる file:line:
- `tools/mutation_harness.py:703-724` は固定 `tools/run_tests.py` を local/dispatch 共通で許可する。
- `tools/run_tests.py:1028-1040,1063-1077` は headroom 不明・不足時に dispatch へ倒し、`tools/run_tests.py:1856-1862` が実際に dispatch を起動する。
- `tools/mutation_harness.py:1589-1593` は local では submission 前 snapshot を取らず、`:1618-1634,1646-1650` は外側 timeout を無条件に TIMEOUT 化する。
- `_dispatch_orphan_stop` は `tools/mutation_harness.py:274-304` で dispatch mode にしか効かない。S2案も `s2-plan.md:17-27,46-57` で local を TIMEOUT としている。
- 実際に観測できるのは `output/pegasus-dispatch/<nonce>/` と request 等 (`tools/pegasus/dispatch_compute.py:1516-1555`)、harness が捕捉する console (`tools/mutation_harness.py:1625-1634`)、`[Pegasus dispatch] ... QUE` 等 (`tools/pegasus/dispatch_compute.py:404-405,1814-1816`)。
- scheduler の job stdout は RUN 後の receipt log に依存し、queue-only 経路では保証されない (`tools/mutation_harness.py:1527-1536,1439-1457`)。local artifact には receipt/job stdout path を保存できない (`tools/mutation_harness.py:1187-1222`)。
- local の `before=set()` は既存 submission と新規 submission を区別できず、複数なら recovery 自体が失敗する (`tools/mutation_harness.py:1499-1503,1589-1593`)。
- なお dispatch mode 自体は orphan stop が先に働く (`tools/mutation_harness.py:1822-1832,2803-2812`)。生きている経路は local 宣言と実体の乖離である。

深刻度: blocker

成果物影響: queue で一度も RUN していない変異が TIMEOUT、completed、resume keep となり、検出力と `completed == registered` の主張が偽る。

### 所見 2: status の閉包は「TERMINAL 2 箇所・summary 3 箇所」ではない

主張: 実行時 status の束縛点が複数残る。特に baseline の別 classifier、fan-out の Counter、current/history の逐語 gate を個別に裁定しないと、追加 status の漏れまたは過剰許可になる。

根拠となる file:line:
- mutation の期待 status 検査: `tools/mutation_harness.py:506-526`
- mutation classifier: `tools/mutation_harness.py:1646-1662`
- baseline classifier と再検証: `tools/mutation_harness.py:1716-1727,2087-2103`
- summary と completed 判定: `tools/mutation_harness.py:1924-1945`
- resume の current/history routing: `tools/mutation_harness.py:2346-2369`
- 保存後の停止条件: `tools/mutation_harness.py:2793-2797`
- wrapper の exact summary/status count: `tools/mutation_worktree.py:841-889`
- fan-out の observed status と expected status: `tools/mutation_fanout_contract.py:335-352,475-489`
- fan-out の `Counter` と current/history gate: `tools/mutation_fanout_contract.py:949-1006,1011-1049`
- docs の exact schema 参照は `docs/pegasus-runbook.md:1361-1363`。`docs/worklog.md:662-663` と `docs/failures.md:5378` は逐語を含むが、実行 consumer ではなく履歴記述である。

深刻度: must-fix

成果物影響: 漏れれば QUEUE_TIMEOUT が unknown/PARSE_ERROR で止まり、逆に広げ過ぎれば queue 待ちを terminal として summary、resume、fan-out が受理する。

### 所見 3: v5 は妥当だが、v4 互換性を失う相手を明記しないと P4 の結論が過小評価になる

主張: v4 据え置きでは新 evidence 欄と QUEUE_TIMEOUT の exact 契約を表現できない。一方 v5 では TIMEOUT 0 の旧台帳だけでなく、全ての旧 v4 resume/remerge が拒否される。

根拠となる file:line:
- mutation record は exact key: `tools/mutation_harness.py:79-105,2121-2123`
- 旧 consumer の schema exact check: `tools/mutation_harness.py:2246-2257`
- wrapper の schema/summary exact check: `tools/mutation_worktree.py:827-855`
- fan-out の schema、summary、record exact check: `tools/mutation_fanout_contract.py:813-815,935-954`
- fan-out の未知 status 拒否: `tools/mutation_fanout_contract.py:965-968`
- S2案自身も全 v4 resume/remerge 拒否を認めている (`s2-plan.md:96-114`)。

深刻度: must-fix

成果物影響: `TIMEOUT` 過去件数が 0 でも既存 v4 台帳と shard は継続利用できず、v4 を読む旧 harness/wrapper/merger も新 v5 record を exact 検査で拒否する。

### 所見 4: テストの逐語 status と v5 fixture の監査範囲が不足している

主張: S2案は主要 fixture の更新を挙げるが、status を逐語で持つ test site を全て分類していない。既存期待値として残すものと、新 schema に合わせるものを分けて固定すべきである。

根拠となる file:line:
- harness の local TIMEOUT と dispatch orphan fixture: `orchestrator/tests/test_mutation_harness.py:881-894,900-970`
- harness の resume history status: `orchestrator/tests/test_mutation_harness.py:617-631`
- worktree の exact summary と v4 literal: `orchestrator/tests/test_mutation_worktree.py:116-146`
- worktree の KILLED assertions: `orchestrator/tests/test_mutation_worktree.py:293,1029-1033`
- fan-out の expected status、record、summary、TIMEOUT reject、SURVIVED 再集計: `orchestrator/tests/test_mutation_fanout_contract.py:75-85,241-275,536-563,773-787`
- S2案が明示する更新範囲は `s2-plan.md:201-209` に留まる。
- 新規 test file は作らない方針 (`s2-plan.md:164-166`) なので、作る場合だけ `orchestrator/tests/test_plain_runner_coverage.py:44-74` の自走/allowlist gate が追加で必要になる。

深刻度: must-fix

成果物影響: stale な v4/summary fixture は実装を拒否し、逆に既存 local TIMEOUT や D289 の TIMEOUT reject を一括変更すると、旧防壁を緩めた緑を作る。

### 所見 5: M6 は現状の fixture を再利用すると後段 gate に mask される

主張: `history の QUEUE_TIMEOUT を許す` 変異は、通常の artifact fixture を使うと対象行ではなく後段の evidence 検査で落ちる。

根拠となる file:line:
- M6 の対象と期待 node: `s2-plan.md:207-220`
- history の対象 gate: `tools/mutation_fanout_contract.py:1011-1017`
- 対象 gateを通過すると artifact 検査へ進み、receipt path があれば observed status を再計算する: `tools/mutation_fanout_contract.py:1018-1035`
- 既存 fixture は receipt/job stdout path が常に非 null: `orchestrator/tests/test_mutation_fanout_contract.py:35-72,233-239`
- receipt path がある通常 record では `timed_out=False` から KILLED 等を再導出するため、`observed_status != PARSE_ERROR` で後段 reject される。

深刻度: must-fix

成果物影響: M6 の KILLED が history gate の検出力ではなく後段 artifact gate の検出力になり、層別の検出力主張を誤る。

### 所見 6: M1-M4 の expected node は DW-M08 の完全集合になっていない可能性がある

主張: S2案は同一 test を pytest parameterize すると書く一方、matrix には関数名だけを expected node として登録している。parameterized node suffix を含む実赤集合を列挙する設計が必要である。

根拠となる file:line:
- parameterize の記述: `s2-plan.md:168-187`
- M1-M4 の expected node 記述: `s2-plan.md:211-220`
- DW-M08 は実赤 node との完全一致だけを KILLED とする: `docs/dev-wave/mutation.md:56-60`
- harness も `expected_nodes` と failed node の完全一致を前提にする: `tools/mutation_harness.py:514-526,1659-1662`

深刻度: must-fix

成果物影響: parameterized case の一部を落とすと MISMATCH、関数名へ丸めると期待 node の過少列挙となり、M1-M4 の kill 帰属と検出力値が無効になる。

補足: wave 前の無条件 TIMEOUT は M1 として明示登録済み (`s2-plan.md:213-216`) であり、この点の omission はない。

### 所見 7: DW-M06 と v5 schema のため docs は無変更では済まない

主張: docs への新規行追加は避けられるが、既存行の置換は必要。v5 にする以上、runbook の v4 逐語を残せない。さらに DW-M06 は queue timeout と実行 timeout を区別していない。

根拠となる file:line:
- v5 採用と runbook 更新: `s2-plan.md:96-107`
- DW-M06 の「timeout は fail-open の証拠」: `docs/dev-wave/mutation.md:37-40`
- DW-M07 の local/dispatch 契約: `docs/dev-wave/mutation.md:42-48`
- runbook の旧 v4 参照: `docs/pegasus-runbook.md:1361-1363`
- docs 予算に収まらなければ統合・停止する規律: `docs/skill-self-improvement.md:46-51`

深刻度: must-fix

成果物影響: v4 のままの運用説明は既存台帳の resume/remerge を誤誘導し、DW-M06 の逐語は QUEUE_TIMEOUT を fail-open の実行証拠と誤読させる。

### 所見 8: dispatch 自身へ queue 待ち上限を渡す対案は成立するが、現在の argv 経路には未接続

主張: dispatch 側分類は実装可能。ただし `--queue-wait-timeout` は dispatch_compute の CLI にしか存在せず、run_tests/harness/wrapper の runner argv から自動転送されない。S2案はこの対案を検討していない。

根拠となる file:line:
- dispatch の CLI option と API 伝播: `tools/pegasus/dispatch_compute.py:2195-2232`
- queue timeout の判定: `tools/pegasus/dispatch_compute.py:1838-1852`
- infra rc=16 と receipt 保存: `tools/pegasus/dispatch_compute.py:188-222,2002-2083`
- run_tests は child args だけを dispatch API へ渡す: `tools/run_tests.py:940-950`
- run_tests が runner option として除去するのは force のみ: `tools/run_tests.py:158-165`
- harness は command をそのまま Popen する: `tools/mutation_harness.py:1595-1604`
- wrapper/fan-out が runner argv を組み立てる: `tools/mutation_worktree.py:674-705`, `tools/mutation_fanout.py:656-688`
- S2案の分類案は `s2-plan.md:7-67` にあるが、queue option の forwarding seam がない。

深刻度: must-fix

成果物影響: flag を run_tests argv に誤って足すと pytest 側の parse error になり、足さなければ harness outer timeout が先に発火して、queue-specific 分類も receipt 生成も得られない。

### 所見 9: D289 は緩めてはならないが、fan-out の v5 consumer 更新自体は scope 内

主張: `_MERGEABLE_STATUSES`、TIMEOUT current gate、history gate、`TIMEOUT: 0` を変更するのは scope 外。schema、summary、record exact shape の更新と QUEUE_TIMEOUT 明示拒否だけは v5 consumer closure として必要である。

根拠となる file:line:
- D289/D300 の TIMEOUT 全面拒否: `docs/decisions.md:13911-13918`
- 現行の TIMEOUT reject と mergeable gate: `tools/mutation_fanout_contract.py:31-33,965-968`
- history reject と再集計: `tools/mutation_fanout_contract.py:1011-1017,1037-1049`
- S2案も mergeable set を維持している: `s2-plan.md:69-94,155-162`

深刻度: nit

成果物影響: 現行の拒否を維持すれば値は変わらない。緩めれば queue timeout shard が併合され、fan-out の検出力と D289 の fail-closed 保証が壊れる。
```

## 総括

blocker は 1 件。最優先は local 宣言と実体 dispatch の乖離である。  
次に、queue option の伝播、v5 の互換性、M6 の mask、expected node 完全集合を段 4 で固定すべきである。  
D289 の TIMEOUT 全面拒否は維持し、fan-out は v5 consumer 更新に限定する。  
pytest は未実走で、判定は静的検査のみ。