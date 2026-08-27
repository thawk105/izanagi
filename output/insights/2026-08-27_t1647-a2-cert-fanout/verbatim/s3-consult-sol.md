静的検査の結論は「現計画のまま実装へ進めない」です。gate 配置に重大な scope 漏れがあり、2-request 合流の意味論も未裁定です。pytest・実走・Web 検索は行っていません。

### 1. 重大 — D1070 が要求する dispatch / artifact gate が計画から漏れている

該当 file:line: [rulings.md:171](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/refs/rulings.md:171)、[s2/out.md:142](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:142)、[ident.py:427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/ident.py:427)、[paper_story_a2_certification.py:1862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1862)

何が起きるか: D1070 は批准検査を dispatch と artifact 受入でも発火させると裁定している。しかし計画は closure が未批准と知りながら 2 件を `qsub` し、compute 内の「新規 lock 作成」まで到達させる実測を成功条件にしている。さらに既存 lock 経路は live binding だけを再検査し、新規 lock 用の批准検査を通らない。A-2 collector も lock を decode するだけで批准を再検査しないため、正しい形の未批准 v2 lock を先置きすれば dispatch/受入 gate を通らない経路が残る。

成果物影響: 未批准 closure の scheduler request が投入記録へ入り、先置き lock 経路では未批准 campaign の値が `certification.json` の受理集合へ入りうる。

推奨: **裁定・依存へ返す。** T-1629 側の dispatch/artifact gate API 着地を先行条件にし、新 submitter と collector の双方から呼ぶ。gate 閉鎖中の実測成功条件は「login 側で批准エラー、qsub 0 件」へ変更する。compute 到達を維持する非認証経路は A-2 certification ではなく、D1028/D1038 型の別成果物裁定が必要。

### 2. 重大 — 1 request から 2 request への変更は受理集合を広げるが、policy を変えない計画になっている

該当 file:line: [s2/out.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:14)、[s2/out.md:92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:92)、[paper_story_a2_certification.sh:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:243)、[paper_story_a2_certification.py:1727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1727)、[fanout-independence.md:58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/refs/fanout-independence.md:58)

何が起きるか: 現行は 1 PBS request が rr5、rr50 を同一ノード・連続時刻で実行する。分割後は異なるノード・時刻の 2 campaign を、各 workload の effect の論理積として `observed-positive` にする。数式は workload 内比較だけだが、「Pegasus contract が同じなら異なる実ノード・時刻を一証明へ合流してよい」という規則は policy にない。CC throughput のノード差は明示的に未測定であり、同値性を実測から一般化できない。

成果物影響: `certification.json` の受理集合が「単一 request の4 cell」から「任意の2 request・2 host・2時刻の workload 対」へ広がり、report の `effects/status` と台帳参照が混成観測を表すようになる。

推奨: **裁定へ返す。** 採るなら policy に「各 workload は独立に環境契約された campaignであり、outer certification はその conjunction」と明記し、protocol SHA/schema を更新する。`policy は変更しない` は落とす。

### 3. 重大 — 「失うのは1 workloadだけ」は no-resume 契約では成立しない

該当 file:line: [s1-brief.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/refs/s1-brief.md:50)、[s2/out.md:126](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:126)、[paper_story_a2_certification.py:631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:631)、[同:2185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2185)、[同:1603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1603)

何が起きるか: rr50 が preflight 後に切れると、その workload の raw leaf・campaign claim/WAL は既存になる。計画は resume を scope 外とし、attempt は `automatic_retry: false`、raw は create-only である。同じ attempt へ再投入できず、新 attempt の rr50 と旧 attempt の rr5 を collector が cross-attempt として拒否する。正式 certification を得るには新 attempt で4 cellすべて再走が必要になる。

成果物影響: 成功した2 cellは診断用には残るが certified 選択へ再利用できず、`certification.json` は欠落または indeterminate のままになる。

推奨: **親の「損失は2 cell」主張は落とす。** この wave を待ち時間短縮だけと位置付けるなら実装可能。成功 workload の再利用まで求めるなら、D1059 の束縛付き resume または workload-fragment 集約を別裁定へ返す。

### 4. 高 — preregister と compute-preflight が同じ raw leaf の作成者になっている

該当 file:line: [s2/out.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:17)、[同:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:33)、[同:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:68)、[paper_story_a2_certification.py:2537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2537)

何が起きるか: 計画は preregister 時に `raw/$workload` を作る一方、compute-preflight でも同じ leaf を create-only 作成すると記す。文字どおり実装すると両 job が preflight で既存 path を拒否する。安易に freshness 検査を緩めれば、逆に stale/他 job の raw を受け入れる。

成果物影響: 厳密実装では raw 4 cell・manifest・certification が一切作られず、緩和実装では raw の受理集合が広がる。

推奨: **採る。** preregister は `raw/` 親だけを作り、`raw/$workload` の唯一の create-only owner を各 compute-preflight にする。`jobs/$workload` と `scheduler/$workload` は preregister 所有でよい。

### 5. 高 — stock/adopted の実行順は機械化されるが、campaign と request/node の事後束縛が閉じていない

該当 file:line: [paper_story_a2_certification.py:2148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2148)、[同:2182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2182)、[loop.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/loop.py:212)、[paper_story_a2_certification.py:2277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2277)

何が起きるか: `run_workload` は exact 2 cell を stock→adopted 順で同じ `run_campaign()` に渡すため、pair 分割の懸念自体は反証できる。ただし campaign preimage/lock/WAL は request ID・hostを持たない。campaign claim には `job_id/host/boot_id/campaign_identity` が既にあるのに、raw manifest は lock/WAL だけを凍結する計画である。このため materialized proof から「この workload campaign は group receipt のこの request/node が生成した」と再検証できない。

成果物影響: `request_ids[workload]` と raw campaign の直接束縛がない証拠も受理でき、レポート・台帳の request 参照が実 producer を証明しない。

推奨: **採る。** raw manifest v3 に exact 2 campaign claim を含め、campaign ID、workload、reservation の request ID・host・boot ID と交差照合する。stock/adopted は同一 binary ではなく別 genome の別 buildなので、「同じ build」ではなく「同一 campaign・source pin・toolchain・node」と定義する。

### 6. 反証 — 5反復と elapstim は段2計画では緩められていない

該当 file:line: [s2/out.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:16)、[policy:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.v1.json:17)、[pipeline.py:1340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/pipeline.py:1340)、[paper_story_a2_certification.py:1538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1538)、[walltime-cost.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/output/insights/2026-08-26_a2-4cell-walltime-cost.md:72)

何が起きるか: 段2は walltime を6時間のまま維持しており、pass は5回をループし、positive/certified は exact 5 pass の場合だけ成立する。途中切れは nonzero/missing result または indeterminate になり、部分5反復が positive 側へ流れる経路は見つからない。したがって「今回縮める」という懸念は反証。ただし n=1 の線形換算から将来の短縮を正当化することはできない。

成果物影響: 現計画では certified 受理集合への影響なし。将来短縮した場合も主な影響は false-positive ではなく indeterminate/欠落の増加。

推奨: **6時間維持を採る。** 短縮は複数回の正式 full-chain 観測後に別判断とする。RSS 20.29 GB/32 GB は分割しても rr50 job 内のピークとして残り、時間枠では解決しない。分割の効用は別ノードへの隔離まで。

### 7. 代案「workloadごとに別attempt、既存単一job機構は無変更」はそのままでは壊れる

該当 file:line: [paper_story_a2_certification.sh:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:243)、[paper_story_a2_certification.py:1587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1587)、[同:2253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2253)、[同:2414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2414)

何が起きるか: 現行 job body は常に両 workload を実行するため、「1 attempt = 1 workload」は機構無変更では作れない。さらに raw finalizer は1 attempt内の exact 4 cell、collector は同一 attempt ID、materializer は単一 attempt reportを要求する。2 attempt を束ねるには workload-fragment 成果物型と外側 aggregation authority が必要になる。

成果物影響: 無変更案では workload分割にならないか、cross-attempt拒否で単一 certification が作れない。

推奨: **「より小さい代案」としては落とす。** 有効化には結局 submission/completion/raw/result の意味変更に加えて新しい fragment→outer certification 契約が要り、6 schema bump案より小さいとはいえない。ただし成功 workload の再利用性は高いので、それを要件化するなら別の裁定候補にはなる。

### 8. 反証 — 共有 build cache の同一 stock build 衝突は起きない

該当 file:line: [paper_story_a2_certification.sh:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:222)、[buildcache.py:1271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/buildcache.py:1271)、[同:1659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/buildcache.py:1659)

何が起きるか: rr5-stock と rr50-stock の genome は同じだが、各 PBS job の scratch dependency prefix は request別で、その正準 path が build identity に含まれる。したがって build digest/claim は分離される。

成果物影響: なし。共有 cache を理由に片側が build-error になる懸念は反証。

推奨: **現方式を採る。** request別 dependency prefix が identity に入ることを契約テストで固定する。

## 裁定パッケージ候補

- D1070 準拠の dispatch/artifact gate が T-1629 所有なので、着地順と新 submitter/collector の呼出し契約を確定する。
- 「2 workload certification は別ノード・別時刻の独立 campaign の conjunction でよいか」を policy 層で裁定する。
- 成功 workload の再利用を要件にするかを決める。要件化するなら no-resume group attempt ではなく、fragment/outer aggregation 設計が必要。

## 総括

- 最重は D1070 違反で、未批准中に qsub して compute gateを観測する成功条件そのものを変更する必要がある。
- 次に、単一 request から2 request合流への受理集合拡大は policy不変のまま扱えず、意味論裁定が要る。
- no-resume のため片側失敗時も正式 certification では4 cell全再走となり、親の「損失2 cell」主張は成立しない。