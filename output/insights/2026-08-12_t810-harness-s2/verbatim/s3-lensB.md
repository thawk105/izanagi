結論: **NO-GO**。`(f)` は T-139 識別未解決のため常時 deny、`(g)` は予算正本・初期値・競合更新の根拠がなく、実効性を証明できない。

### 所見

1. **qsub の凍結入力が実在しない — blocker**  
   位置: `s2-plan.md` §子B（qsub argv）、`t810_prereg_v1.json:569-578,684-698`  
   `<project>`, `<queue>`, `<frozen-walltime>` の供給元がない。prereg は `qsub_argv` を未凍結手順として列挙しているだけ。任意の walltime を manifest に入れても検査できない。  
   修正: project/queue/walltime を承認済み policy の実在 key に追加し、digest で束縛する。

2. **manifest の approval ID・approved host が自己申告になる — blocker**  
   位置: `s2-plan.md:30-35,94-96`、`t810_prereg_v1.json:115-124,570`  
   `prereg_approval_id`、`approved_hostnames`、生死確認 literal の出所がない。呼び出し側が任意 host を approved list に入れると hostname gate が空洞化する。  
   修正: 外部 trust root の approval/host inventory を定義し、無ければ manifest を生成不能にする。

3. **T-139 の識別は機能していない — blocker**  
   位置: `s2-plan.md` §T-139 の識別入力  
   `pilot_patterns=[]`, `main_patterns=[]` で常時 deny。`dispatch_compute.py:429-432` の `izdw-<nonce>` は T-139 を表さず、既存 parser も `Job_Name` の一致しか見ない。  
   修正: T-139 所有側が anchored `Job_Name` 規約を承認し、policy に固定する。

4. **logical ID と PBS ID の境界が未解決 — blocker**  
   位置: `s2-plan.md:32,41,94-95,318`  
   qsub 前の manifest に PBS ID は存在せず、qstat は PBS `Job Id` を返す。PBS ID を logical ID と解釈すると事前 manifest と矛盾し、logical ID を qstat で探すと一致しない。  
   修正: logical ID と PBS ID を別 field と明記し、submission receipt の一方向 mapping に限定する。

5. **qstat fixture の形が二種類の実出力を混同し得る — must-fix**  
   位置: `brief.md:29-32`、`s2-plan.md:178,186-188,270`  
   `mutation_fanout.py:1099-1119` は `qstat -f` 相当の `Job Id/Job_Owner/job_state/Job_Name` しか扱わず、未知 state や重複 field を厳密拒否しない。一方 `queue_state.py:46-122` は `[EXECUTION QUEUE]` と `QueueName ENA STS QUE RUN` の `qstat -Q` 表を読む。両者を同じ fixture/parser 契約にすると、片方の実出力が「0件/deny」になる。  
   修正: `qstat -f <id>` と `qstat -Q` を別 transcript schema・別 parser として固定する。

6. **予算 ledger に genesis・canonical path・trust root がない — blocker**  
   位置: `s2-plan.md:214-264`、`brief.md` P1  
   `total_node_seconds` と estimates の初期値、空 ledger の扱い、共有絶対 path、作成者が未定義。空 ledgerを別 path に置けば `remaining=total` で admission できる。registry 追加は存在確認であり、予算値の承認ではない。  
   修正: 承認済み policy、固定 ledger path、genesis record、所有者、欠落時 deny を定義する。

7. **見積りが実際の N job に束縛されていない — must-fix**  
   位置: `s2-plan.md:226-233,247-262`  
   `jobs_per_attempt=1` の policy と 13-slot manifest の組合せは、式自体は正しくても 1 job 分しか課金しない。  
   修正: `jobs_per_attempt == len(manifest.slots) == prereg node_count` を run kind ごとに検証する。

8. **reservation の idempotency と race が未定義 — must-fix**  
   位置: `s2-plan.md:235-245,268-276`  
   同じ `group_id` を二重 submit して別 `reservation_id` を得ると、同じ attempt が二重予約される。`flock` の対象 pathも caller が選べる。  
   修正: canonical ledger を lock 内で read/validate/check/append し、`(group_id, run_kind, attempt)` の重複予約と finalize replay を拒否する。

9. **qsub失敗・qdel取消・未使用retryの精算がない — blocker**  
   位置: `s2-plan.md:95,106,241,272-275`  
   qsub が timeout したが scheduler では受理済み、または qdel 成功後に `finalize_budget` が呼ばれない場合の扱いがない。main の最大2 attemptを予約して1回で成功した場合の未使用枠も未定義。  
   修正: `unknown scheduler outcome = consumed` 等の状態遷移表を作り、reservation ID付きで取消・retry未使用分を一度だけ精算する。

10. **schema の exact 性が nested/raw JSON まで検証対象になっていない — must-fix**  
    位置: `s2-plan.md:28,52-80,195`  
    root の `set(actual)` は書かれているが、event-specific `payload`、`details`、`a_series_jobs` 等の nested object の unknown/missing field と JSON duplicate key の拒否規約がない。例: `state` 重複 key や `repo_absence` 欠落＋未知 key が parse 後に last-wins になる実装でも通り得る。  
    修正: 全 nested schema の exact 表、raw parser の duplicate-key reject、unknown/missing 双方向 fixture を明記する。

11. **injection seam が本番経路を検査しない — blocker**  
    位置: `s2-plan.md:13,108,119-120,300-305`  
    CLI は dormant seal で scheduler seam より先に停止する。`_coordinate_authorized` を直接呼ぶテストだけなら、production CLI が guard/budget を bypass しても検出できない。  
    修正: dormant 経路と、同一 production orchestration に fake scheduler を注入する authorized 経路を分けて統合検査する。

12. **子A/B/Cの編集集合が素でない — must-fix**  
    位置: `s2-plan.md:16-24,298-307`  
    shared schema、shared scheduler fixture、`SchedulerRun`/`AdmissionEvidence`/`SlotPlan` の所有者が未指定。A/B/Cが同じ schema/fixtureを修正し、API衝突する。  
    修正: Sを単一 owner に割り当てて先に凍結し、fixtureをA/B/C別に分割する。

13. **変異の帰属ができない — must-fix**  
    位置: `s2-plan.md:119,188,207,270-276`  
    `run_authorized=false` のままなら、budget admissionを削除した変異もCLIテストが通る。T-139常時denyは未知state拒否やB取消の失敗を隠す。validator、wrapper、repo absenceの重複拒否も同様。  
    修正: authorized fixtureで各 gate を単独違反にし、`mutant → 必ず失敗するテスト → reason_code` の表を事前登録する。

### 裁定パッケージ候補

- T-139 pilot/main の `Job_Name` 規約と所有者。
- `total_node_seconds`、builder/liveness/main の walltime・job数。
- budget policy と ledger の trust root、初期 genesis、canonical path。
- §3.3 の request ID が logical ID か PBS ID か。
- 開始ばらつきが `max(ack)-release` なのか `max(ack)-min(ack)` なのか。
- `prereg_approval_id` を本 slice で参照だけするのか、T-868 後まで field 化しないのか。

## 総括

実在する入力は N=13、R=10、timeout=1200秒、start spread=5秒、benchmark argv、retry上限2まで。  
qsub仕様、T-139 identity、host approval、budget初期値・ledger正本は未確定。  
fixtureは静的検査に使えるが、本番経路・TOCTOU・精算の保証には不足する。  
したがって現段階の判定は **NO-GO**。