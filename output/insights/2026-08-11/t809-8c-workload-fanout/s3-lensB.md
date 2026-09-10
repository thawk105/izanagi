## 総括

blocker は5件です。

- **B1:** 「部分成功 = fail-stop」が誤りで、P4・facts の再投入判断が崩れている。
- **B2:** N 本の期待集合・完了・失敗・再投入を機械的に閉じる仕組みがない。
- **B3:** N 個の独立 wall 予算は「1 allocation で完遂する」設計と一致せず、kill 後の group 完了も定義されていない。
- **B4:** build-cache claim 衝突の根拠が標準 CLI の実体と一致せず、代わりに worktree 管理状態と cache 非再利用が未解決。
- **B5:** formal は「fan-out 済み」ではなく、共通 snapshot・launcher・waiter・受理閉包がない。

事実表の誤りは、903110 のノード名、partial の説明、journal-only の説明、campaign identity と cache claim の一般化です。親裁定では P3 の全面禁止が過剰で、P1・P4・P5 も経路ごとの限定が必要です。

全体判定は **NO-GO**。build、formal、one-allocation 置換としての fan-out は採用不可です。ただし、外部 output root・一意 trial/run root・`--no-build`・`scientific_claim=false`・全 N 本の人手照合を条件にした exploratory の独立 singleton 実行だけは条件付き GO です。テスト・build・bench は実行していません。

1. **[blocker] / 「部分成功 = fail-stop」は現行実装全体に当たらない。** / 根拠: 親 brief `:29-30`、facts `:6-9` と古い説明 `:98-108` が矛盾している。`p3_autonomous_workload_trial.py:1727-1733` の `break` は generation loop だけで、通常経路は `:1459-1472` で cell を追加して次 workload へ進む。例外・wall 境界だけが `:1393-1458` で outer loop を止める。 / これを直さないと、P4 が想定する受理集合・partial 件数・後続 workload の有無が変わる。`role-invalid` を含む run は既に後続 cell を持ち得るため、fan-out による変更と現行挙動を区別できない。

2. **[blocker] / N 本のうち2本が落ちた場合の group 完了と registered 再投入が閉じていない。** / 根拠: runbook は N-job verifier を持たないと明記する (`docs/pegasus-runbook.md:999-1021`)。registered acceptance は report 6本を要求する (`trial_registry.py:2178-2189`)。lifecycle は exact token を発行した同一 process 内でしか terminalize できない (`trial_registry.py:1526-1540,1616-1689`)。強制 kill では terminal 行自体が残らない可能性がある。 / これを直さないと、成功した N−2 本だけで group を閉じることはできず、missing report は exact-six acceptance を通らない。clean retry は失敗した2本だけの追加ではなく、新しい manifest・通常は新しい6 trial ID・registry/prereg 束縛を作って6本を再投入する必要がある。旧4本は旧 manifest hash に束縛され再利用できない。

3. **[blocker] / `max_wall_s` を N 本へ複製すると、1 allocation の総予算ではなく N 個の独立予算になる。** / 根拠: wall の起点は process ごとの `started_monotonic` (`p3_autonomous_workload_trial.py:2083-2086`)。検査は workload/generation 境界だけ (`:1361-1371,1682-1694`)で、role 呼び出し・build・bench・finalize 中には止めない。設計メモは role 4回×1200秒、build/verify/bench、finalize reserve を一 allocation に積む前提 (`output/insights/2026-08-01_8c-one-allocation-budget-design.md:36-61,154-167`)。 / これを直さないと、N process を同一 PBS allocation に入れた場合は共通 deadline がなく、別 job にした場合は総作業量が N 倍になる。PBS kill 後に journal が残っても、group が incomplete であることを示す集約証拠はない。Gmax、完遂保証、採用可能な値の集合が変わる。

4. **[blocker] / build-cache claim 衝突という facts の主張は、標準 CLI の N process 経路ではそのまま成立しないが、build の read/write 集合は未解決である。** / 根拠: CLI は build ごとに `checkout()` で一意 worktree を作る (`p3_autonomous_workload_trial.py:2327-2328`, `patchharness.py:288-306`)。しかし `SourceEvidence` の `source_root` は receipt に入り (`source_digest.py:149-160,850-876`)、admission 全体が cache preimage に入る (`build_admission.py:470-482`, `buildcache.py:246-266`)。したがって標準 CLI の各 process は source root が異なり、同じ Genome でも cache digest は異なる。逆に、cache 再利用のため同じ worktree を共有すれば create-only claim (`buildcache.py:658-702`) が競合し得る。worktree add/remove は共通 base の登録簿を触るが、fan-out 用の明示 lock はない (`patchharness.py:291-306`)。 / これを直さないと、facts `:73-94` と s2-plan `:31` の「同じ cache key で後着が必ず落ちる」という理由は修正対象になる。実際の標準経路の問題は claim 衝突より cache 非再利用と共有 git metadata であり、build fan-out の可否・コスト・stale claim の頻度を誤って裁定する。

5. **[blocker] / formal は leaf のデータモデルがあるだけで、運用上「既に fan-out 済み」ではない。** / 根拠: registered は singleton workload (`trial_registry.py:1018-1041`)で、manifest は exact six (`:322-357`)。一方、現 repository は正式 H1/H2 の12前提が未充足で、起動を期待してはならない (`docs/phase3-s8c-autonomous-trial-runbook.md:61-70`)。各 process は個別に `measurement_head` を解決する (`trial_registry.py:1044-1055`)が、acceptance は6 report間の head 一致を検査しない (`:2266-2325,2384-2397`)。 / これを直さないと、P1 の「formal は既に fan-out 済み」は、exact-six の受理器があることと、N 本を同一 protocol snapshot として投入・待機・閉じることを混同する。異なる measurement HEAD を含む6本が受理され得るため、accepted values と参照 commit の集合が変わる。

6. **[must-fix] / P3 の「workload-conditioned claim だから cross-node fan-out 全面禁止」は過剰である。** / 根拠: 親 brief `:26-28` は全面禁止だが、実 report は `scientific_claim=false` (`p3_autonomous_workload_trial.py:1523-1531`)。runbook は job 内比較を無条件に許し、job間性能比較だけに node block/randomization を要求する (`docs/pegasus-runbook.md:968-978`)。 / これを直さないと、性能を比較しない no-build operational fan-out まで禁止し、worklog 418 で撤回された「未測定量を理由に広く禁止する」誤りを再発させる。P2 の same-node build/bench 排除は維持できるが、P3 は exploratory wiring と将来の性能 protocol に分けるべきである。

7. **[must-fix] / 「一意な run root なら既存 CLI だけで独立」は外部 output root 条件を欠いている。** / 根拠: CLI の既定 root は repo 内 `output/exploration/autonomous-trials/<trial-id>` (`p3_autonomous_workload_trial.py:2269-2298`)。`--run-root` 明示時は external-root resolver を経ず、namespace marker の検査も repo 外必須ではない (`layout.py:375-387`)。`.gitignore` は `output/exploration` を無視しない (`.gitignore:17-25`)。runbook は job script に `IZANAGI_EXPLORATION_OUTPUT_ROOT` を設定するよう要求している (`docs/pegasus-runbook.md:1082-1086`)。 / これを直さないと、デフォルト実行は repo tree を汚し、clean gate や output parent を走査する consumer と干渉し得る。探索 namespace を読む具体的 consumer の衝突は静的には断定しないが、現状は「機械保証」ではなく運用者依存である。

8. **[must-fix] / campaign ID を `(trial_id, workload, policy, contract)` と説明する facts/s2 の記述は誤り。** / 根拠: `CampaignConfig` は execution contract を identity から除外すると明記する (`model.py:67-84`)。canonical preimage は spec content、commit、search config、trial のみ (`ident.py:151-178`)。p3 が workload・descriptor・generation を search config に入れることは確認できる (`p3_autonomous_workload_trial.py:512-541`)が、bound contract 自体は入らない。 / これを直さないと、contract/node 環境が違えば campaign root も別になるという前提で freshness、lock、WAL、consumer の分離を判断してしまう。build cache の contract namespace と campaign root の分離を混同し、成果物参照が同じ root を指す可能性を見落とす。

9. **[must-fix] / probe 903110 のノード provenance が事実表内で修正され切っていない。** / 根拠: facts 冒頭は `bnode019` と訂正している (`facts.md:3-5`)が、同じ表の一次資料説明 `:24-25` と実測見出し `:110` は依然 `bnode033`。原票は `probe/job-0-903110.nqsv/env.txt:1` が `bnode019`、wall は `walls.txt:1-7`。 / これを直さないと、1.69倍の値自体は同じでも、node block/randomization やノード一般化に使う provenance と参照が不一致になる。

10. **[must-fix] / 1.69倍の実測範囲を、未測定の production path と混同しない明示が必要。** / 根拠: 実測は fixture・`--no-build`・generation 1 のみ (`facts.md:110-124`)で、LLM role、build、verify、bench、scheduler receipt を含まない。facts 自身が role 実時間を未測定と認める (`:127-130`)。runbook は固定費が未測定なら測ってから判断するよう要求する (`docs/pegasus-runbook.md:923-932`)。 / これを直さないと、1.69倍を role timeout、build/bench、PBS prologue の速度根拠として使えるように読める。少なくとも role wall、job prologue、build/cache 再利用を unknown として裁定 package に残し、Gmax や break-even の数値へ流入させてはならない。

11. **[must-fix] / 「実装しなければ成果物の値・受理集合・参照は変わらない」は条件付きでしか正しくない。** / 根拠: brief `:36-42` は no implementation なら不変とするが、s2-plan `:101` は手動で N 回起動すれば exploratory が1 multi-cell reportから N leaf reportへ変わると認めている。 / これを直さないと、「コード差分ゼロ」と「fan-out運用を実行しない」を混同する。実際に N 回実行すれば report、journal、run root、trial ID、hash 参照が変わる。certifying input にはならなくても、成果物と参照集合は変化する。

12. **[must-fix] / 選択肢に「fan-out しないで律速を解く」軸が抜けている。** / 根拠: s2-plan の択は `:97-106` に集中しているが、budget 設計は worst-case envelope の77%が role timeoutで、最短経路は role cap低減とする (`output/insights/2026-08-01_8c-one-allocation-budget-design.md:141-150`)。また Pegasus transport と build/bench の同居自体が未解決 (`:169-199`)。planner→coder→auditor→drive→critic は世代内で順序依存する (`p3_autonomous_workload_trial.py:1682-1907`)。 / これを直さないと、workload fan-out が律速を縮めるという前提で択を比較してしまう。「role cap/transport を解く」「formal arm/trial 軸で分ける」「generation/role fan-out は意味変更として退ける」「そもそも fan-out の利益なし」を明示した受理集合が必要である。

13. **[must-fix] / P5 の「新 trial_id 必須」は registered と exploratory で分ける必要がある。** / 根拠: registered は lifecycle start-once (`trial_registry.py:1578-1583`)だが、exploratory は registry に登録済みでないことだけを確認する (`:1126-1188`)。no-build exploratory は新 run root なら同じ IDでも技術上は動き得る一方、build は同じ trial/workload の campaign freshness で拒否される (`p3_autonomous_workload_trial.py:1652-1658`)。 / これを直さないと、再投入手順の「誰が、いつ、何を旧 attempt と照合するか」が曖昧なままになる。registered は新 exact-six 系列、exploratory は新 ID・新 root を運用規則として固定し、旧 request と新 request の対応を group ledger に残す必要がある。

**条件付き GO の境界:** `--no-build`、非 holdout exploratory、1 process 1 workload、外部専用 output root、一意 trial ID/run root、期待 N 本の事前 ledger、全 N 本の rc・report・journal hash 照合、成功部分集合だけの集計禁止、性能比較をしない、をすべて明記できる場合に限ります。これを超える fan-out は、上記 blocker を解消するまで NO-GO です。