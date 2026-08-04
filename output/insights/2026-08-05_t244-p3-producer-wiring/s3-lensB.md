現行 brief / 段2プランに対する判定は **NO-GO（実装しない）** である。authority と runtime genesis が存在せず、正の producer 経路は発火不能である。拒否専用 CLI を land すれば、D147 が禁じた「未結線 leaf を実装済みと数える」再演になる。

### B-1

**主張:** 現プランを land しても P3 の観測可能な成果物は一つも前進せず、「production producer wiring」という wave 名が会計上虚偽になる。

**根拠:**

- 親 brief 自身が、authority が空のため受理・予算消費経路は発火しないと認めている。[brief.md:80–83](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:80)
- 段2プランも、正の producer wiring は不可能で、拒否専用 CLI は未結線 prototype の再演だとして NO-GO を出している。[s2-plan.md:1–3](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:1) [s2-plan.md:270–277](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:270)
- D147 は「leaf だけ land して P3 実装済みと記録する」案を明示的に却下している。[decisions.md:7202–7217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/decisions.md:7202)
- D159 の現行会計は “P3 origin-ledger prototype” までで、producer と P7 が入るまで P3 は FAIL のままである。[decisions.md:7890–7901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/decisions.md:7890)

**具体的な失敗シナリオ:** opt-in CLI と adapter を追加し、テストでは空 authority に対する拒否だけを確認する。コードレビュー上は「8c に結線」と記録されるが、実行時には全入力が genesis 前に拒否され、production candidate は一件も ledger に入らない。

**成果物影響 1 行:** certified 選択＝不変、材料レポート＝origin 参照なし、試行台帳＝新規受理なし、proof chain＝新しい辺なし。

**処置区分:** scope 内の改名では救えない。実装を止め、成果物を「設計メモ」として返すべき裁定事項である。

---

### B-2

**主張:** 成果に必要な11層のうち、本 wave が実装対象にしているのは producer と caller の2層だけで、しかも前提層が欠けるため実効上は0層である。

| 層 | 現状 | 本 wave |
|---|---|---|
| 1. authority 値の裁定・発行 | registry は空配列。値の復元にもユーザー裁定が必要。[reflux_origin_authority_v1.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_authority_v1.json:1) [s2-plan.md:90–110](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:90) | 外 |
| 2. public authority reader / live-cell binding | 公開 reader がなく `OriginSnapshot` からも必要値を復元できない。[brief.md:53–57](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:53) | 外 |
| 3. runtime bootstrap・storage・migration | production 初期化は禁止、公開 API は `create=False`。[reflux_origin_ledger.py:2265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2265) [reflux_origin_ledger.py:2737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2737) | 外 |
| 4. producer translator / batch journal | API、journal、error taxonomy を計画。[s2-plan.md:15–70](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:15) | 内 |
| 5. production caller | 8c opt-in 結線を計画。[s2-plan.md:149–166](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:149) | 内 |
| 6. durable origin-proof 発行 | brief が本 wave から除外。[brief.md:77–79](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:77) | 外 |
| 7. report schema / 現 consumer の任意 proof 検査 | report v3 と D96 を明示的に先送り。[s2-plan.md:141–147](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:141) | 外 |
| 8. trial registry の origin binding | `TrialBinding` に origin 欄がなく、受理も declaration-only。[trial_registry.py:103–129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/trial_registry.py:103) | 外 |
| 9. P7 formal consumer | D121 が別要件としている。[decisions.md:5842–5854](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/decisions.md:5842) | 外 |
| 10. Layer 3 / WAL / 材料レポート | brief が明示的に除外。[brief.md:77–79](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:77) | 外 |
| 11. positive runbook・監査・crash recovery | 単体テスト案はあるが、現 driver は resume を拒否し E2E replay 不可能。[s2-plan.md:168–189](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:168) | 部分のみ |

**具体的な失敗シナリオ:** 4・5層だけ完成させても、1〜3層で必ず停止する。fixture で通したとしても6〜10層へ参照が渡らず、production artifact から到達不能な leaf になる。

**成果物影響 1 行:** production の4成果物はすべて不変で、変わるのは source tree と fixture 内 ledger だけである。

**処置区分:** D159 に従えば、仮に land しても名乗れるのは「fixture-only producer adapter prototype、P3 FAIL 継続」までだが、DW-G04 のため本 wave では設計メモに留めるべきである。

---

### B-3

**主張:** authority registry が空で bootstrap も禁止されている以上、拒否経路を実装しても DW-G04 の発火 gate は満たさない。

**根拠:**

- DW-G04 は、発火条件を満たす既存 artifact path または measurement ID を brief に書けない機能を設計メモに限定する。[core.md:57–60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/dev-wave/core.md:57)
- brief は正の受理・予算消費経路が発火しないことを自認している。[brief.md:80–83](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:80)
- public API から runtime genesis を作れず、fixture seam だけが `create=True` を使う。[reflux_origin_ledger.py:2317–2333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2317)

**具体的な失敗シナリオ:** 「空 authority を正しく拒否した」という measurement ID を発火証拠として採用する。しかしそれが証明するのは fail-closed だけで、機能の条件節である「候補を受理し、予算を消費し、seal する」は一度も実行されていない。

**成果物影響 1 行:** ledger の受理件数・iteration/query 消費量は0のままなので、試行台帳・材料レポート・proof chain への参照も0のままである。

**処置区分:** ユーザー裁定が必要。違反しない最小形は、先行 wave で「実在する authority entry、公開 reader、production bootstrap、`commit_batch → seal` と予算減算を示す既存 artifact path/measurement ID」を成立させることである。

---

### B-4

**主張:** P1 の「8c 一点へ結線」は現状では誤りであり、E は安い生死実験候補だが production 結線先としては未だ不適格なので、今はどちらにも結線すべきでない。

**根拠:**

- production 8c driver が扱える workload は `ycsb-a/b/c` のみ。[p3_autonomous_workload_trial.py:171–175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:171)
- trial registry の formal arms は `rr80/rr20` である。[trial_registry.py:41–58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/trial_registry.py:41)
- runbook は A/B/C を pilot であって formal trial ではないとし、H1/H2 を後段に置いている。[phase3-s8c-autonomous-trial-runbook.md:9–12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/phase3-s8c-autonomous-trial-runbook.md:9) [phase3-s8c-autonomous-trial-runbook.md:238–240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/phase3-s8c-autonomous-trial-runbook.md:238)
- E driver は既存の一提案単位 producer だが、drive 後に provenance と checkpoint を公開するため、複数 iteration を一 ledger batch に後付けする構造になっている。[p3_s4_loop_trigger_gating.py:649–681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:649) [p3_s4_loop_trigger_gating.py:729–746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:729)

**具体的な失敗シナリオ:** 8c の A/B/C に結線すると pilot report しか得られず、formal rr80/rr20 を指定すると production driver が workload を拒否する。一方Eをそのまま使うと、第一提案の drive/publication 後に第二候補を集めるため、D121 の「全候補を先に commit・seal」を破る。

**成果物影響 1 行:** 8c案では pilot report だけ増えて formal trial registry の受理は増えず、E案では E checkpoint/provenance だけが ledger seal より先行し、certified 選択と proof chain は増えない。

**処置区分:** P1 を撤回するユーザー裁定が必要。authority/bootstrap 後、Eを「事前に2提案を用意して seal 後に drive する使い捨て生死実験」にだけ使い、その後に formal 8c を別 wave で結線するのが最小である。

---

### B-5

**主張:** P2 の複数 coder invocation は現 consumer の受理集合を必ず変えるため、D96 なしには実装できない。

**根拠:**

- completeness consumer は `attempt == 1` かつ `retry == false` を要求する。[autonomous_trial_completeness.py:175–195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/autonomous_trial_completeness.py:175)
- attempt 2 の拒否は境界テストで固定されている。[test_autonomous_trial_completeness.py:678–693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/tests/test_autonomous_trial_completeness.py:678)
- 段2案はこれを避けるため全 coder を `attempt=1` のまま `candidate_index` で分けるが、現 report は role ごとに単一 object である。[s2-plan.md:112–124](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:112) [autonomous_trial_completeness.py:633–690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/autonomous_trial_completeness.py:633)
- journal と report の role tuple は Counter の全単射検査を受ける。[autonomous_trial_completeness.py:916–924](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/autonomous_trial_completeness.py:916)
- D96 は受理集合変更と新D・境界テストを同一変更単位に要求する。[decisions.md:4269–4289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/decisions.md:4269)

**具体的な失敗シナリオ:** metadata を `attempts_per_role_generation=2` にすれば即拒否される。全呼出しを attempt 1 と偽装すれば、複数 journal event の一つしか `roles.coder` に表現できず、Counter 不一致で拒否されるか、一候補が黙って report から消える。

事前登録文書は現在も draft で freeze mechanism 未実装なので、「既存の凍結 bytes」はまだ存在しない。[phase3-8c-preregistration.md:1–7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/phase3-8c-preregistration.md:1) [phase3-8c-preregistration.md:34–35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/phase3-8c-preregistration.md:34) ただし、これは無手続で schema/cardinality を変えてよい理由ではなく、正式 activation 前に再事前登録が必要である。

**成果物影響 1 行:** 現状では複数 attempt report の受理数は0、consumer を黙って緩めれば completeness と trial registry の受理集合、role cardinality、report bytes が同時に拡張される一方、certifying 値は false のままである。

**処置区分:** current scope 内では修正不能。report v3、completeness、trial registry、新D、旧拒否・新受理の境界テストを同一変更単位にする裁定が必要である。

---

### B-6

**主張:** 「本 wave は origin proof を許すだけ、P7 が後で要求する」という P4 境界は、durable な横断参照を今発行しない限り成立しない。

**根拠:**

- brief は formal report、proof chain、Layer 3、WAL を本 wave から外している。[brief.md:77–79](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:77)
- `SealedBatch` は origin/batch と候補・結果 hash を持つが、trial、campaign、report への参照を持たない。[reflux_origin_ledger.py:509–516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:509)
- 現 trial report の公開 payload に origin proof はなく、trial registry 参照も任意の既存参照だけである。[p3_autonomous_workload_trial.py:1283–1321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1283)

**具体的な失敗シナリオ:** producer は batch A を seal するが、trial report R は A の `origin_id/batch_id` を保持しない。P7 が後から R を検査しても、Rの採用候補が評価前にAへ拘束されたのか、別の seal 済み batch を後付けしたのか区別できない。

**成果物影響 1 行:** ledger 内の sealed batch 数だけ増えても、材料レポート・trial registry・proof chain の参照集合にはその batch への辺が追加されず、certified 選択は origin に根拠付けられない。

**処置区分:** scope 境界の裁定が必要。少なくとも `origin_id`、authority blob hash、batch ID、seal commitment、候補・結果 artifact hash を report/WAL に残し、現 consumer が「存在する場合は検証」するところまで同時に入れる必要があり、これはD96変更単位となる。

---

### B-7

**主張:** trial registry は成功時でも明示的に non-certifying なので、これへの結線を certified 選択の前進として数えることはできない。

**根拠:**

- モジュール冒頭が registry を declaration-only とし、arm の実実行を certify しないと宣言している。[trial_registry.py:2–6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/trial_registry.py:2)
- `AcceptanceSummary` の値は `certifying=False`、`arm_binding="declared-only"` である。[trial_registry.py:124–129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/trial_registry.py:124)
- 六 report の構造受理後も同じ non-certifying summary を返す。[trial_registry.py:1298–1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/trial_registry.py:1298)

**具体的な失敗シナリオ:** 六件が registry acceptance を通った事実を「certified selection 完了」と誤記するが、実際には arm binding は申告値の比較に過ぎず、実行候補・origin・formal proof の一致を証明していない。

**成果物影響 1 行:** 試行台帳の構造受理件数だけは増え得るが `certifying=false` は不変で、certified 選択・材料レポート・proof chain は前進しない。

**処置区分:** producer scope では直さない。ただし brief と完了会計では必ず「declaration-only acceptance」と記録し、certification はP7側の裁定へ返す。

---

### B-8

**主張:** M1〜M6 は実装可能性の証拠ではなく blocker の実測であり、M7の grep 推論とM8の cold-start 成功も production liveness を一切証明していない。

**根拠:**

- M1〜M6 は空 authority、runtime 不在、batch 最小2、8c attempt 1、E一提案、coder schema の不整合を列挙している。[brief.md:15–28](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:15)
- M7 は「参照が見つからない」ことから durable manifest 再発行不要と推論し、M8 は単なる cold-start 結果である。[brief.md:29–33](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/brief.md:29)
- ledger は live authority を committed `HEAD` の bytes と照合し、runtime genesis の authority hash/origin 集合とも一致を要求する。[reflux_origin_ledger.py:1306–1324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1306) [reflux_origin_ledger.py:1952–1972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1952)

**具体的な失敗シナリオ:** unrelated startup が緑だったため ready と判断するが、最初の ledger API 呼出しで runtime genesis 不在により停止する。後に authority bytes を追加した場合も、bootstrap/migration 契約がなければ既存 epoch との不一致で停止する。

**成果物影響 1 行:** startup status だけが緑でも ledger 受理・予算値・report refs・registry refs・proof refs はすべて不変である。

**処置区分:** M7/M8 を発火証拠から外す修正は brief 内で行うべきで、authority epoch/bootstrap 方針はユーザー裁定へ返す。

---

### B-9

**主張:** 生死実験前に generic producer、journal、error taxonomy、14 mutation を一括設計する規模は DW-G01〜G03/G05 に反し、1 wave で安全に閉じない。

**根拠:**

- DW-G01 は既存 driver または100行以下の使い捨て実験を先行させる。[core.md:42–45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/dev-wave/core.md:42)
- DW-G02 は初回 cycle 前 blocker を成果物の正しさ・受理・proof reference 等が実際に変わるものへ限定する。[core.md:47–50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/dev-wave/core.md:47)
- DW-G03 は族一般化に独立した producer/consumer 二例を要求する。[core.md:52–55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/dev-wave/core.md:52)
- 現プランは生きた一例がない段階で generic API・journal・error taxonomy と14 mutation を計画している。[s2-plan.md:15–70](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:15) [s2-plan.md:234–253](/home/SFC/tanab/.claude/jobs/bcfdcde4/tmp/t244-p3-producer-wiring/s2-plan.md:234)

**具体的な失敗シナリオ:** 8c の単一 role object を前提に generic producer を固めた後、E の「複数 iteration・各回即 publication」境界が一致しないと判明し、generic 層を破棄するか、seal 前 publication を許す例外を追加する。

**成果物影響 1 行:** 初期実装単位では4成果物の値が変わらず、source surface とテスト数だけが増えるため、DW-G05上も独立成果として数えられない。

**処置区分:** 次の単位へ分割すべきである。

1. 裁定のみ：authority manifest/preimage、issuer、bootstrap、target、proof-ref schema、attempt cardinalityを確定する。
2. authority wave：実在 entry、public reader、runtime bootstrap/migration、positive measurement ID、runbookを作る。
3. 生死実験：Eに事前生成済み2提案を渡し、batch commit/seal 後だけ drive する使い捨て経路を測る。
4. production 8c単位：target-specific producer、report v3、origin proof ref、completeness/registry、新D96と境界テストを同一変更単位にする。
5. P7単位：Layer 3/WAL/材料レポート/formal consumer/監査を結び、この時点で初めてP3 PASSを検討する。
6. Eと8cの独立二例が成立した後にだけ共通 producer API を抽出する。

## 総括

最重要の3件は次のとおりである。

1. **DW-G04違反:** 空 authority と bootstrap 不在により、正の受理・予算消費経路は発火不能である。
2. **D96未充足:** 複数 coder invocation は現 consumer と report の受理集合を必ず変えるが、新D・report v3・境界テストがscope外である。
3. **P4境界の破綻:** producer と report/proof chain の durable cross-referenceを今残さなければ、P7は後からその試行を信用できない。

したがって、この wave は **実装へ進めず「実装しない」と裁定すべき** である。許される現成果は設計メモと裁定パッケージまでであり、拒否専用 adapter や fixture-only leaf を production wiring/P3前進として land してはならない。

なお、これは Pegasus ログインノード上での静的レビューであり、pytest等の実測は行っていない。