## 総括

blocker は **6 件**。

1. exploratory の 1 multi-workload trial を N leaf に割ると、期待集合・共通 run envelope・group lifecycle が消える。
2. `CrossRoleSessionTracker` の検出範囲が trial 全体から各 workload に縮み、`valid child_id` の集約だけでは旧検出力を再現できない。
3. singleton 化で「全 build cell が同じ campaign output root」を検査できなくなり、既存 exact-six acceptance も Layer-3・実 arm を認証しない。
4. build fan-out は shared cache claim により逐次時と異なる `build-error` を生み、同一ノードでは compiler が bench を汚染できる。
5. node fan-out は exploratory no-build と正式性能比較で結論が逆になる。正式 6 trial の一処置一ノード配置は現 protocol では許可できない。
6. 新 exact-six manifest を作れば formal retry できる、という案は「crash 後再走なし」を迂回し、repeat-until-success を許す。

事実表には、訂正欄と本文の矛盾、成功 node、fail-stop、campaign identity、build claim の後処理、workload 独立性について誤りが残る。親裁定は **P2 のみ維持**、P1/P3/P4/P5 は限定修正が必要。

全体判定は、**workload 単位 fan-out の実装は NO-GO**。`s2-plan.md` の択 (a)「実装しない」は条件付き GO だが、「既存 CLI を N 回呼ぶ」ことを旧 multi-workload trial と同値な一成果物として扱ってはならない。no-build exploratory を独立運転するだけなら、起動前 exact 集合・全 request の terminal/rc/hash・欠落時の incomplete を明示し、性能・正式・同値性の主張へ流入させない場合に限り許せる。

## 所見

### 1. [blocker] N leaf 化は「投入時刻だけ」の変更ではない

- **主張:** `brief.md:15` の不変条件と、`s2-plan.md:20-33` の一意な trial ID / run root を持つ N process 案は両立しない。旧 trial の代替には group-level の start-once、terminal-once、exact workload 集合、共通 execution contract が必要だが、現択 (a) には存在しない。
- **根拠:** 旧検査は一つの report/journal 上で、共通 provider・generation budget・`do_build`・wall を束縛し、workload を一意な requested prefix として検査する（`autonomous_trial_completeness.py:459-554,892-949`）。一方 campaign ID は trial ID、workload、generation、descriptor、policy 等を含む config から導出される（`p3_autonomous_workload_trial.py:504-541`; `ident.py:151-178`）。trial ID を leaf ごとに変えれば campaign ID/root も変わる。
- **影響:** 一つの `status`・journal hash・shared wall が、N 個の status/hash/wall に変わる。欠落 workload、異なる generation budget、成功 leaf のみの選択が各 leaf 内では通るため、受理集合、wall 値、campaign/report 参照が変わる。`s2-plan.md:78-84` の将来 group 定義は方向として正しいが未実装であり、手動 fan-out の保証にはならない。

registered では `assert_trial_registry_acceptance` が exact 6 report と manifest trial set の一致を要求する（`trial_registry.py:2178-2189,2232-2243`）。これは「6 successes」ではなく、partial を含む **全 6 report** の構造受理であり、receipt も `certifying=false` である（`:2344-2347,2419-2421`）。exploratory group にも同じ「成功集合ではなく期待集合」の原則が必要である。

### 2. [blocker] session 相異検査が縮み、plan の `valid child_id` 検査では不足する

- **主張:** `s2-plan.md:25,61` は report 間の valid `child_id` 相異を「同値性を主張する場合」に置くが、旧 multi-workload trial の代替なら必須である。さらに valid records だけでは旧 tracker と同じ検出力にならない。
- **根拠:** 一つの `CrossRoleSessionTracker` が全 role provider に共有される（`p3_autonomous_workload_trial.py:1082-1105`）一方、tracker 自身は明示的に process-local である（`role_session_isolation.py:2-8,53-66`）。provider は session ID を tracker へ登録してから応答を返し（`claude_projected_provider.py:340-371`）、role parser はその後に走る（`p3_autonomous_workload_trial.py:943-961`）。したがって parser-invalid attempt の session ID も旧 tracker の集合には入るが、journal では invalid event となり valid provenance の `child_id` には現れない（`:961-985`）。
- **影響:** 同じ session が workload A の parser-invalid attempt と workload B で再利用された場合、旧 process は B を `role-invalid` にするが、fan-out leaf は双方を通し得る。leaf `status`、exact-six の受理内容、fresh-context の証拠が変わる。全 provider envelope を hash 束縛して再検査する cross-process tracker が必要である。

### 3. [blocker] Layer-3 と実 arm は既存 exact-six acceptance では閉じない

- **主張:** `s2-plan.md:39` の「`assert_trial_registry_acceptance` をそのまま上位集約として再利用」は formal build 経路には危険である。
- **根拠:**
  - 旧 multi-cell producer は、全 build cell の `campaign_root.parent.parent` が一つであることを明示検査する（`p3_autonomous_workload_trial.py:1564-1573`）。singleton report では集合要素が常に一つなので恒真になる。
  - `assert_campaign_layer3_chain` の campaign ID 重複検査と共通 `output_root/campaigns/<id>` 検査も report 内だけである（`autonomous_trial_completeness.py:1123-1174`）。
  - `trial_registry.py` は `assert_autonomous_trial_completeness` しか import せず（`:30-33`）、acceptance は `_assert_snapshot_completeness` だけを呼ぶ（`:1801-1856,2253`）。C9 の証拠契約は formal acceptance 自身から Layer-3 を呼ぶことを要求している（`s8c_preregistration_evidence_contract.v1.json:303-333`）。
  - registry は「declared arm が実際に走った arm だとは認証しない」と明記する（`trial_registry.py:2-6`）。
- **影響:** N leaf が異なる campaign output root を使っても、また producer 後に campaign WAL/Layer-3 bytes が変わっても、report/journal/lifecycle hash が不変なら exact-six receipt が発行され得る。さらに descriptor-on 相当の実行を manifest 上 on/off/swapped と宣言できる。材料値、arm ラベル、proof-chain 参照が実体から分離する。

group validator には、起動前に固定した **一つの campaign output root** を全 leaf の `assert_campaign_layer3_chain` へ渡し、formal acceptance の必須経路で再実行する必要がある。

### 4. [blocker] build fan-out は結果を変え、同一ノードの計測単独性も守れない

- **主張:** build を含む fan-out は、同一ノード・別ノードの双方で現状 NO-GO。P2 は維持すべきである。
- **根拠:**
  - CLI は全 process の cache root を `<ccbench-dir>/build-variants` に固定する（`p3_autonomous_workload_trial.py:2327-2328`）。
  - 同じ完全 preimage では create-only claim が競合する（`buildcache.py:246-266,538-547,658-679`）。逐次なら先行 publish 後に後続は cache hit になるが、並行時の後着は `BuildCacheError` となり、pipeline は当該 variant の `build-error` abort に変換する（`pipeline.py:748-804`）。
  - build は bench lock の外で先に走る（同上）。`bench_lock` が排除するのは同じ lock を取得する bench/重い verify だけ（`lock.py:41-64`）。
  - `competing_bench_pids()` は `ycsb_*.exe` だけを検索し、compiler を見ない（`calibrator/runner.py:171-203`）。
  - `settle()` は load average が下がらなくても timeout 時点で `settled=false` を返すだけ（`:60-79`）。通常 8c path では `require_settled=false` なので計測自体は進む（`pipeline.py:392-409,1055-1059`）。また settle 後に別 process が build を開始することも防げない。
- **影響:** fan-out の投入時刻だけで、逐次なら cache hit だった arm が `build-error` になり、fitness が欠落する。同一ノードでは compiler 負荷により throughput、CV、最終 fitness/選択値が変わる。別ノードでも shared cache claim 問題は残る。

なお claim の恒久残留は kill 限定ではない。claim 取得後の通常の configure/build/validation/publish 失敗も、成功時の `_release_v2_claim` に到達せず claim を残す（`buildcache.py:701-793`）。

### 5. [blocker] P3 は広すぎるが、正式 6 本の一処置一ノード配置も許可できない

- **主張:** no-build wiring pilot と正式性能比較を分ける必要がある。
- **根拠:** §7.5 は、job 内で閉じる性能比較を許し、job 間の性能比較には投入前の node block/randomization、node 内対照または node 間反復、推定量・集約手順を要求する（`docs/pegasus-runbook.md:968-978`）。
  - **job 内で閉じるもの:** 一つの leaf 内の correctness verdict、bench rep の median/CV。将来、一つの job が stock/variant の対を同じ node で測るならその差。
  - **job を跨ぐもの:** formal on/off/swapped の性能・fitness 差。凍結設計は arm を対照として比較し、oracle performance 差も判定に使う（`phase3-8b-descriptor-design.md:158-170,220-230`）。
  - 現 manifest は `{trial_id, arm, holdout, campaign_id}` しか持たず、node block/randomization 因子がない（`trial_registry.py:322-357`）。prereg は schedule・seed・arm 順を事前固定することを要求する（`phase3-8c-preregistration.md:108-118`）が、現 exact-six acceptance は配置を検査しない。
- **影響:** H1/H2 × 3 arm を一 arm 一 node に置くと treatment と node が完全交絡し、on/off 差や floor 超過判定が変わり得る。6 process であることは 6 node へ散らす許可ではない。

したがって P3 の「8c 全体を禁止」は撤回する。fixture/no-build の operational fan-out は性能値を比較しない限り node 交絡の対象外。一方、正式 6 本の性能値を別 job 間で比較する配置は、protocol 改訂前は NO-GO である。

### 6. [blocker] 新 exact-six manifest は formal retry の自動許可ではない

- **主張:** `s2-plan.md:92-95` の「clean な再実験なら新 exact-six manifest・新 6 ID」は registry の構造説明としては正しいが、現 protocol 上の許可ではない。
- **根拠:** 8b の裁定は crash 後の再走なし、実験全体を判定不能とする（`phase3-8b-descriptor-design.md:275-280`）。8c prereg もその整合を前提条件にする（`phase3-8c-preregistration.md:70-72,108-110`）。lifecycle は同一 ID の start/terminal を一度に閉じる（`trial_registry.py:1578-1584,1667-1686`）。
- **影響:** 新 manifest/new IDs を単なる retry として許すと、失敗した exact-six を残したまま成功するまで新系列を作り、成功系列だけを結果にできる。受理集合と結論が repeat-until-success で変わる。新しい正式系列には再凍結・ユーザー裁定と、旧失敗系列を含む全件報告が必要である。

### 7. [must-fix] 事実表の訂正が本文へ反映されていない

- **主張:** `facts.md:3-22` の訂正だけでは足りず、後段の相反する本文を直す必要がある。
- **根拠と影響:**

| 残る誤り | 原典 | 直さない場合の影響 |
|---|---|---|
| `facts.md:110` は 903110 を bnode033 とする | 原票 `probe/job-0-903110.nqsv/env.txt:1-2` は bnode019 | node provenance が誤る |
| `facts.md:98-101` は partial 全般を fail-stop とする | `p3_autonomous_workload_trial.py:1459-1472,1727-1733` では role-invalid 後も次 workload へ進む | P4 の現受理集合を誤る |
| `facts.md:43-45` は workload 間依存なしと断定 | provider/session tracker、shared wall/fatal semantics が跨る（`:1082-1105,1361-1490`） | fan-out で縮む防壁を見落とす |
| `facts.md:65` は campaign identity を単純 tuple 化 | 実 preimage は spec/search config/trial 等で、execution contract 自体は除外（`model.py:66-84`; `ident.py:151-178`） | campaign root 衝突・分離の推論が誤る |
| `facts.md:85-86` は claim 衝突で process が落ち手動回収とする | loser は pipeline の `build-error` へ隔離。owner 成功なら claim 除去（`pipeline.py:799-804`; `buildcache.py:674-699,788`） | failure/status の意味を誤る |
| 訂正欄は stale claim を kill 限定とする | claim 取得後の通常 build/validation 失敗でも残る（`buildcache.py:701-793`） | build fan-out の恒久障害リスクを過小評価する |

### 8. [must-fix] 1.69× は N-job fan-out も本番利得も測っていない

- **主張:** 1.69× は「同一 node の fixture/no-build 3 process を一度重ねた観測値」に限定する。
- **根拠:** probe は PBS 1 job・1 node 内で（`t809_fanout_probe.sh:2-12`）、3 background process を起動している（`:102-115`）。provider は fixture、build/bench なし（`:81-88`）。成功原票は bnode019、C は一回だけである（`env.txt:1-8`; `walls.txt:1-7`）。
- **影響:** queue 待ち、job prologue、cross-node 配置、実 LLM latency、build cache、compiler、verify、bench のいずれの wall も推定できない。`facts.md:125-126` の「固定費 0.68 秒・限界費 0.44 秒」は A/B 二点へ線形モデルを当てた推定で、独立な実測量ではない。本番 speedup、投入本数、wall budget の根拠にすると値が変わる。

ただし、P2 の拒否は未測定の速度差ではなく静的に確認できる isolation 欠落、正式 node 配置の拒否は未測定の node 差ではなく識別不能性に基づく。この二つは有効である。

### 9. [must-fix] P1〜P5 の最終文言

| 裁定 | 必要な修正 |
|---|---|
| P1 | 「formal は leaf が 6 process に分解済み」は可。「fan-out 済み・追加機構不要」は不可。launcher/waiter はなく、現 prereg は未発効、acceptance は arm/Layer-3 を認証しない。 |
| P2 | 維持。同一ノード build+bench fan-out は拒否。cross-node でも shared build-cache 問題を別途閉じる。 |
| P3 | 全面撤回ではなく分岐。no-build operational は node 交絡を理由に禁止しない。正式な job 間性能比較は node 因子を protocol 化するまで禁止。 |
| P4 | 旧 multi-workload report を独立完走 group に置換する場合は受理集合変更。role-invalid は既に後続 workload を続行するため「現状すべて fail-stop」は削除する。 |
| P5 | registered の同一 ID retry 禁止は維持。ただし新 exact-six は自動的な retry 許可ではなく、現 no-rerun protocol の再裁定が必要。 |

静的読解のみで、テスト・build・性能測定は実行していない。pytest 緑は主張しない。