判定は **NO-GO** です。plan 自身の停止判断は正しいものの、再 brief で閉じるべき穴がさらにあります。

### A-1

- 主張: 候補生成後に初めて `BatchCommitted` する順序では、kill／process 分割／run-root 変更により query 予算を消費せず候補 batch を無限に引き直せる。
- 根拠: plan は N 回の coder 完了後に commit する（[s2-plan.md:116](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:116)、[s2-plan.md:120](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:120)）。ledger が `iterations_used` / `queries_used` を増やすのは `BatchCommitted` 適用時だけである（[reflux_origin_ledger.py:900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:900)、[reflux_origin_ledger.py:913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:913)）。`run_trial` は既存 root の resume を拒否するだけで、新しい root での再起動は可能である（[p3_autonomous_workload_trial.py:1786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1786)）。
- 具体的な失敗シナリオ: 同じ `origin_id` で N 件の coder 出力を得て raw wire を読む。気に入らなければ commit 直前に process を殺し、新しい `trial_id` / run-root で再実行する。ledger は常に `queries_used == 0` のままで、気に入った候補集合だけを最終的に commit できる。
- 成果物影響: 試行台帳の query 数が実呼出し数より小さくなり、certified 候補集合が無課金の rejection sampling で偏る。

### A-2

- 主張: plan の「live cell 比較」は origin manifest 全体を実行 sink に束縛せず、別 spec・scale・CCBench・role bundle を同じ origin として走らせられる。
- 根拠: origin manifest は 13 field を含む（[reflux_origin_ledger.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:216)）一方、`derive_cell_key` は descriptor SHA、axis、verifier、environment の 4 値しか覆わず、`records` / `threads` すら含まない（[reflux_origin_ledger.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:434)）。plan の手順も full manifest ではなく cell の比較で終わる（[s2-plan.md:74](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:74)）。さらに提案 API は `campaign`、`descriptor_binding`、`ccbench_root`、`environment_contract` を caller から受ける（[s2-plan.md:15](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:15)）が、実 drive は environment と layout を独立に再解決する（[p3_s4_loop_trigger_gating.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:701)）。
- 具体的な失敗シナリオ: caller は authority と一致する descriptor/environment object を `bind_origin` に渡す一方、実 drive には別 CCBench checkout、変更済み spec、別 role bundle を渡す。4 digest が一致すれば plan の cell gate は通る。
- 成果物影響: origin の予算・constraint class が別の科学的条件へ混入し、材料レポートと proof chain が誤った実行を同一 origin として参照する。

### A-3

- 主張: plan は authoritative な Layer-3/admission 検査より先に不可逆な `BatchSealed` を作るため、未検証または caller 合成の outcome を ledger に確定できる。
- 根拠: plan は各 `drive` の後、全候補を prepare/seal する（[s2-plan.md:120](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:120)、[s2-plan.md:123](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:123)）。現行 Layer-3 admission は `_run_workload` が戻った後に実行される（[p3_autonomous_workload_trial.py:1278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1278)）。fixture path では caller の `drive` / `preview` 注入が許され（[p3_autonomous_workload_trial.py:1698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1698)、拒否は claude-headless だけ: [p3_autonomous_workload_trial.py:1713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1713)）、no-build completeness は admission を `not-applicable` として受理する（[autonomous_trial_completeness.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/autonomous_trial_completeness.py:883)）。
- 具体的な失敗シナリオ: `provider_kind="fixture"`, `do_build=False`, `drive=fake_drive` で `outcome="certified"` を返す。producer がこれを `"accepted"` に写せば、verifier・build・artifact admission が一度も動かないまま seal できる。実 build でも、seal 後に Layer-3 が赤くなる窓が残る。
- 成果物影響: 試行台帳に未検証の accepted/rejected 値が入り、後続 P7 consumer がそれを要求するようになると certified 受理集合まで汚染される。

### A-4

- 主張: 現 8c の artifact topology は preview／drive の結果を seal 前に少なくとも 1 bit 漏らし、plan の call-trace test では検出できない。
- 根拠: preview の pass/fail で auditor が「skip event」になるか実 provider 呼出しになるかが分岐する（[p3_autonomous_workload_trial.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1533)、[p3_autonomous_workload_trial.py:1541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1541)）。実呼出しは `raw_<invocation_id>.txt` と timestamp 付き journal を即時 fsync する（[p3_autonomous_workload_trial.py:935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:935)、[p3_autonomous_workload_trial.py:494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:494)）。drive 後は critic に outcome/metrics を直接渡す（[p3_autonomous_workload_trial.py:1647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1647)）が、plan の期待 trace には critic が存在しない（[s2-plan.md:126](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:126)）。
- 具体的な失敗シナリオ: candidate 0 の preview 後、auditor raw file の有無または skip event を監視して pass/fail bit を得る。悪い bit なら意図的に crash し、plan の再開規則で batch を tombstone する。candidate 0 の rejected constraint は公開 class に入らない。
- 成果物影響: sealed constraint class から不都合な結果を選択的に落とせるため、材料レポートと proof chain の「全結果非公開・非適応」前提が偽になる。

### A-5

- 主張: producer journal は seal plaintext を ledger より先に漏らす一方、削除されると prepared operation を公開 API から復元できず origin を永久停止させる。
- 根拠: plan は event 全 bytes・salts・openings を各副作用前に fsync するとする（[s2-plan.md:56](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:56)、[s2-plan.md:177](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:177)）。ledger はこの漏洩を避けるため、durable pre-event では seal plaintext を commitment に射影している（[reflux_origin_ledger.py:2355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2355)）が、raw seal event 自体の未 commit 漏洩は既知である（[reflux_origin_ledger.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:13)）。`OriginSnapshot` は prepared `operation_id` や open batch を返さず（[reflux_origin_ledger.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:496)）、`run_trial` は既存 root の resume を拒否する。
- 具体的な失敗シナリオ: `BatchSealed` の全 opening を producer journal に保存後、ledger の head commit 前に crash する。journal 観測者は plaintext を読める。journal を消すと再開側は operation ID を取得できず、新 operation は `"another operation is durably prepared"` で拒否される（[reflux_origin_ledger.py:2621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2621)）。
- 成果物影響: seal 前結果が漏れるか、origin の試行台帳が prepared 状態で永久欠落し、proof chain を完結できなくなる。

### A-6

- 主張: git-common-dir store は lock だけでなく CAS と authority version まで全 worktree・全 origin で共有し、独立 campaign 同士を不必要に衝突させる。
- 根拠: runtime root は common-dir の固定 `v1`（[reflux_origin_ledger.py:1160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1160)）。state commitment は authority 内の全 origin head を含む（[reflux_origin_ledger.py:1858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1858)）ため、別 origin の event でも CAS base が変わる（[reflux_origin_ledger.py:2559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2559)）。さらに各 worktree の `HEAD` authority と runtime genesis の blob SHA が一致しなければ全 replay が拒否される（[reflux_origin_ledger.py:1963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1963)）。
- 具体的な失敗シナリオ: origin A と B が同じ global base を読み、双方 N 件の coder 呼出しを行う。A が先に commit すると、B は自身の origin が不変でも CAS loser になる。別 worktree が異なる authority commit を持てば、同じ runtime は authority mismatch で起動不能になる。
- 成果物影響: 正当な並行 trial が partial/reject へ反転し、B の実 coder query は ledger に一件も計上されず、試行台帳と proof chain が欠落する。

### A-7

- 主張: `origin_id` / `batch_id` / `operation_id` / `campaign_id` / `trial_id` の namespace と相互参照が未定義で、D75 の同名識別子防止を満たしていない。
- 根拠: `batch_id` の reuse 検査は origin 内の `seen_batches` に限定される（[reflux_origin_ledger.py:911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:911)）一方、`operation_id` は全 origin で一つの集合として重複拒否される（[reflux_origin_ledger.py:2005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2005)）。sealed batch の参照には `(origin_id, batch_id)` の両方が必要である（[reflux_origin_ledger.py:2760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2760)）。対して `campaign_id` は caller 可変の `trial_id` を含む config から導出される（[p3_autonomous_workload_trial.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:528)、[p3_autonomous_workload_trial.py:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:557)）。plan は各 ID の生成規則を定義せず、保持するとだけ書く（[s2-plan.md:51](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:51)）。
- 具体的な失敗シナリオ: origin A/B がともに `batch_id="b0"` を合法に使う。producer が `operation_id="seal:b0"` とすれば B は global collision で拒否され、report が `batch_id` だけを持てば A/B のどちらを指すか決められない。
- 成果物影響: 正当 batch が誤拒否されるか、材料レポート／proof chain が別 origin の sealed batch を参照する。

### A-8

- 主張: 提案された positive opt-in 統合テストには production store を避けて実 ledger を通す injection seam がなく、恒真 mock か共有 store 接触の二択になる。
- 根拠: 公開 API 3 本は無条件に `_production_store()` を使う（[reflux_origin_ledger.py:2777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2777)、[reflux_origin_ledger.py:2784](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2784)）。temp repo seam は private `_fixture_store_for_test` だけである（[reflux_origin_ledger.py:2317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2317)）。plan の trial 結線は `reflux_origin: str` しか追加せず（[s2-plan.md:153](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:153)）、それでも positive trial テストを列挙している（[s2-plan.md:220](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:220)）。
- 具体的な失敗シナリオ: `test_reflux_opt_in_invokes_n_coders...` が実 `run_trial` を呼ぶと shared common-dir を読む／commit する。producer を monkeypatch すれば call count は緑になるが、authority、CAS、seal、store path の実配線は一度も検査されない。
- 成果物影響: suite が緑でも production の ledger 順序・予算・proof 参照が壊れたまま land しうる。

### A-9

- 主張: 親 P1′ の E 段代案は「proposal file」を候補だけと誤認しており、実 file は auditor 結果を既に含むため commit-before-preview を満たさない。
- 根拠: P1′ は 2 本以上の proposal file を先に用意して commit できるとする（[brief.md:85](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:85)）。実 schema は planner/coder に加え `auditor.verdict` と `diff_digest` を必須にする（[p3_s4_loop_trigger_gating.py:649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:649)、[p3_s4_loop_trigger_gating.py:655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:655)、[p3_s4_loop_trigger_gating.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:674)）。
- 具体的な失敗シナリオ: 正当な proposal file を作るため各 candidate を preview して working diff を auditor に渡し、pass file だけ batch commit する。preview をしないなら auditor verdict/digest を捏造するしかない。どちらでも P1′ の前提が壊れる。
- 成果物影響: batch が評価後に選ばれ、certified 選択と材料レポートが post-selection 済み候補だけを数える。

### A-10

- 主張: M7 の「pin 0 件」は path grep で見えない authority blob trust root を落としており、bootstrap 後の authority 更新・runtime 削除で予算を reset または全拒否にできる。
- 根拠: M7 は path/role 名検索の 0 hit から durable 再発行不要とする（[brief.md:29](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:29)）が、DW-O09 は path hit 0 を pin 無しと結論してはならないと明記する（[operations.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/dev-wave/operations.md:48)、[operations.md:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/dev-wave/operations.md:53)）。origin genesis と runtime genesis は authority 全 bytes の SHA を pin し（[reflux_origin_ledger.py:1838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1838)、[reflux_origin_ledger.py:1963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1963)）、duplicate cell 検査は現在の authority list 内だけである（[reflux_origin_ledger.py:1261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1261)）。
- 具体的な失敗シナリオ: authority v1 で予算を消費後、別 origin 追加または同 cell entry を差し替えて authority v2 を commit する。既存 runtime は blob mismatch で全拒否になる。runtime を削除して新 bootstrap すれば旧 counter を失った新品 ledgerになる。
- 成果物影響: 試行台帳の query/iteration counter が reset するか全 trial が拒否され、旧 proof chain の authority 参照が孤立する。

### A-11

- 主張: 複数 coder slot は現 completeness の閉じた role/report 状態機械では表現不能であり、P4 を維持したまま P2 を実装する道はない。
- 根拠: 現 consumer は role 順を `planner,coder,auditor,critic` の一意な mapping に固定する（[autonomous_trial_completeness.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/autonomous_trial_completeness.py:52)、[autonomous_trial_completeness.py:566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/autonomous_trial_completeness.py:566)）うえ、journal/report の role-attempt multiset 完全一致を要求する（[autonomous_trial_completeness.py:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/autonomous_trial_completeness.py:916)）。brief P4 は formal report/completeness 面を外す（[brief.md:77](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:77)）一方、plan は report v3 と consumer 改訂が必要だと認めている（[s2-plan.md:143](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:143)）。
- 具体的な失敗シナリオ: N 件の coder event を journal に書いて report の既存 `roles.coder` に1件だけ置けば multiset gate が拒否する。extra event を隠せば試行欠落、consumer を緩めれば D96 の受理集合変更になる。
- 成果物影響: opt-in trial の受理集合が全拒否になるか、複数候補の一部を欠いた試行台帳が正当と誤受理される。

### A-12

- 主張: P5 の「空 authority による拒否側だけの発火」は DW-G04 の発火証拠にならず、実装ではなく設計メモに留める条件である。
- 根拠: P5 は正側 artifact が存在しないと認める（[brief.md:80](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:80)）。DW-G04 は発火条件を満たす既存 artifact path または計測 ID が書けなければ設計メモに留めると明記する（[core.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/dev-wave/core.md:57)）。現 authority は空で、production bootstrap も禁止されている（[reflux_origin_authority_v1.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_authority_v1.json:1)、[reflux_origin_ledger.py:2265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2265)）。
- 具体的な失敗シナリオ: `--reflux-origin` を追加して empty-authority rejection test だけ通し、「producer 結線済み」と記録する。実際には全入力が lock 不在または unknown origin で止まり、commit/budget/seal は一度も発火しない。
- 成果物影響: trial の正側受理集合は空のまま、origin receipt も proof 参照も生成されず、P3 の進捗会計だけが誤って前進する。

### A-13

- 主張: M3〜M6 は既存 8c/E-loop の proposal 数しか測っておらず、「合法 batch を作れない」という一般化も、batch が実 coder query に由来するという前提も成立しない。
- 根拠: brief の一般化は [brief.md:59](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:59)。ledger の公開 `BatchCommitted` は caller が任意の commitment tuple を渡せ（[reflux_origin_ledger.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:445)）、FSM は cardinality・distinct・budget だけを検査する（[reflux_origin_ledger.py:900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:900)）。公開 `commit_event` に role receipt や provider invocation の引数はない（[reflux_origin_ledger.py:2784](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2784)）。
- 具体的な失敗シナリオ: authority/bootstrap 後、任意 Python caller が coder を一度も呼ばず、2個の salted commitment を `BatchCommitted` として直接送る。ledger 上は「2 query 消費の合法 batch」になる。逆に A-1 では実 query を何度呼んでも 0 のままにできる。
- 成果物影響: 試行台帳の `queries_used` が実 provider query 数を表さず、材料レポートの予算遵守主張と proof chain の会計が偽になる。

## 総括

最重要の 3 件は次です。

1. A-1: commit 前 kill だけで無課金の候補引き直しができ、予算束縛そのものが成立しない。
2. A-3: verifier／Layer-3 admission 前に不可逆な seal を作れ、偽 outcome を台帳へ入れられる。
3. A-4: raw artifact、auditor skip、WAL、critic 経由で seal 前結果が漏れ、commit-reveal が実効化されない。

判定は **実装停止**です。段 4 は plan の「実装しない」を採用し、少なくとも pre-query reservation、full-manifest の sink-side binding、admission 後 seal、artifact 非干渉、authority 世代移行、global CAS、resume/operation-ID schema、production-path を通す隔離テスト seam を含む新 brief へ戻すべきです。

これは read-only の静的レビューであり、pytest は実行していません。現 production authority は空、runtime store も未作成だったため、現時点の certified 選択・材料レポート・試行台帳・proof chain の bytes はまだ汚染されていません。