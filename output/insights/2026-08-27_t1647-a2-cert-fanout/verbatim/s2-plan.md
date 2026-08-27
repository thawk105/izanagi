結論は、(P1)〜(P4) をすべて採用します。ただし P4 は成果物名だけでなく、現在 1 job 固定になっている submission/completion/acquisition receipt 全体を「2 workload の group receipt」へ拡張する必要があります。ここが親案で最も大きく不足していた点です。

```text
login
  preregister attempt を1回
  ├─ qsub rr5  ── compute body ── raw/rr5 + jobs/rr5
  └─ qsub rr50 ── compute body ── raw/rr50 + jobs/rr50
                         ↓ 2 job 終端後
login: finalize-raw を1回 → group completion/acquisition → collect
```

## (P1)〜(P4) の裁定

- P1 — 採る。policy の単一 `scheduler.job_body` pin は維持し、同じ body に `IZANAGI_A2_WORKLOAD=rr5|rr50` を渡す。body を2本に分けるより、hash/path 閉包が小さい。
- P2 — 採る。各 workload は [campaign_preimage:507-530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:507) と [run_workload:2182-2184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2182) が stock → adopted の1 campaignを要求する。最大同時数は2 workload。
- P3 — 採る。compute body から `finalize-raw` を除去し、2 job の `driver_rc==0` と4 cellの存在を確認した後、loginで1回だけ実行する。walltime は今回は `06:00:00` のままにする。短縮は正式 full-chain の実時間を未測定のまま timeout 受理集合を狭めるため、別計測後に扱う。
- P4 — 採るが強化する。attempt root は共有し、`raw/$workload`、`jobs/$workload`、`scheduler/$workload` を preregister 時に作る。submission/completion/acquisition は jobごとに別ファイルを競合生成せず、workload順の exact 2-entry group receipt とする。

`campaign_lock.py`、`contract_loader_binding.py`、`artifact_admission.py` は変更しない。批准検査の条件分岐や迂回も追加しない。

## 現在、直列化・単一 job を強制している場所

| 現行箇所 | 現在の強制・2本目の失敗 | 分割後 |
|---|---|---|
| [job body:243-259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:243) | `rr5`、`rr50` を固定順で直列実行 | `--workload "$IZANAGI_A2_WORKLOAD"` を1回だけ |
| [job body:261-264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:261) | 同一 job の末尾で manifest を確定 | body から削除し login へ移す |
| [job body:37-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:37) | `$attempt/compute-result.json` が存在すると2本目を必ず拒否 | `$attempt/jobs/$workload/compute-result.json` |
| [job body:46-55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:46) | trap の hard-link publish先も単一 | workload別 job rootへ publish |
| [job body:89-95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:89) | allocation qstat 2ファイルが単一で、2本目を拒否 | `scheduler/$workload/allocation-qstat.*` |
| [job body:152-156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:152) | `$attempt/reservation.json` が単一 | `jobs/$workload/reservation.json` |
| [job body:217-220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:217) | `$attempt/raw` が存在すると2本目を必ず拒否 | fresh対象を `$attempt/raw/$workload` に限定 |
| [job body:222-230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:222) | scratch fresh検査 | PBS job ID別なので変更不要 |
| [compute_preflight:2537-2546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2537) | `attempt/raw` 全体が未作成であることを要求 | workload引数を追加し、`attempt/raw/$workload` だけを create-only作成 |
| [run_workload:2163-2165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2163) | raw rootを `attempt/raw` に固定 | `attempt/raw/$workload` に固定 |
| [run_workload:2182-2187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2182) | stock/adopted 2 cellを同じ実行へ束縛 | 維持。自身の2 cellだけfresh検査 |
| [submission validator:738-898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:738) | qsub argv、request ID、stdout/stderrが各1件 | policy順のexact 2 job entryを反復検証 |
| [receipt writers:1174-1233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1174) | `receipts/submission.json`、`completion.json` と単一request ID | 各ファイルは1つのまま、内部をexact 2-job group化 |
| [completion validator:997-1055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:997) | compute/reservationのcanonical pathがattempt直下の単一名 | workload別pathと対応request IDを反復照合 |
| [completion validator:1065-1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1065) | 単一 `driver_rc` だけでmanifest有無を決定 | 2件すべて0の場合だけmanifestを許可 |
| [raw finalizer:2253-2307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2253) | `raw/`直下のexact 4 fileを要求し、job内で即finalize | `raw/rr5`、`raw/rr50`の各exact pairを確認後、loginから1回 |
| [manifest loader:2329-2344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2329) | raw member名を直下4件に固定 | workloadを含むnested pathへ変更 |
| [collector:1579-1585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1579)、[result:1749-1758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1749) | certificationが単一 `request_id` | exact `{rr5,rr50}` の `request_ids` |
| [materialize:2414-2447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2414) | reportと単一requestを照合 | workload→request mappingを照合 |

submissionの `-o/-e` も workload別にしないと、2 jobが同じscheduler logへ書くため証拠が混線します。新validatorでは `scheduler/$workload/job.stdout|stderr` をcanonical pathとして固定します。

## 変更ファイルと行

### 新規

- [tools/pegasus/submit_paper_story_a2_certification.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/submit_paper_story_a2_certification.sh)（予定 `:1-240`）
  - `:1-65`: 引数、login/queue/quota、repo・CCBench・依存prefix・clean HEAD検査。
  - `:66-105`: preregisterを1回実行し、job body SHA-256とcanonical環境を固定。
  - `:106-190`: `WORKLOADS=(rr5 rr50)` をpolicyと照合し、各1回 `qsub -v "...IZANAGI_A2_WORKLOAD=$workload..."`。stdout/stderr/qstat観測はworkload別。
  - `:191-240`: exact 2-job submission payloadを生成して `record-submission`。部分投入失敗はappend-only diagnostic eventを残すが、certifying group receiptは作らない。
- `output/insights/2026-08-27_t1647-a2-cert-fanout/measurement.md:1-…`
  - 実request IDs、qsub argv、body hash、workload別artifact、両jobの批准終端を逐語記録。

### 改修

- [paper_story_a2_certification.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:9)
  - `:9-41`: workload必須・exact enum、job/raw/scheduler root導出。
  - `:43-58`: workloadを含むcompute-result v2。
  - `:88-193`: qstat/reservationをworkload別pathへ。
  - `:217-264`: workload raw fresh、1 workloadだけ実行、compute側finalize削除。
- [paper_story_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:40)
  - `:40-50,122-143`: receipt/result schema bump、`IZANAGI_A2_WORKLOAD`追加。
  - `:615-636`: shared attemptの `raw/`、`jobs/{rr5,rr50}`、`scheduler/{rr5,rr50}` をpreregister時に作成。
  - `:738-1233`: submission/completion/acquisitionをexact 2-job groupへ変更。各reservationのscript hashを共通submission `job_body_sha256`へ独立照合。
  - `:1579-1777`: `request_id` を `request_ids` mappingへ。
  - `:2148-2385`: workload別raw layout、exact pair、group manifest。
  - `:2414-2464`: materialized group receiptとの照合。
  - `:2485-2547`: compute-preflightへworkload引数。
  - `:2550-2723`:複数driver rc、CLI引数、acquisition記録を追随。
- [admission_registry.json:268-310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/admission_registry.json:268)
  - 新submitterを `local-ok` / `static login-side submitter classification` として追加。
- [tools/pegasus/README.md:20-53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/README.md:20)
  - admission site表へ新submitterを追加。A-2のsubmit/finalize手順を新節で記載。
- [docs/pegasus-runbook.md:484-544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/docs/pegasus-runbook.md:484)
  - registry投影表にlogin-side submitter行を追加。
- [test_paper_story_a2_job_contract.py:15-327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_paper_story_a2_job_contract.py:15)
  - bodyが1 workloadだけ実行すること、新submitterがexact 2 qsubすること、2番目のpreflightが1番目のraw/job成果物と共存することを検査。
- [test_paper_story_a2_certification.py:246-397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_paper_story_a2_certification.py:246)
  - receipt fixtureを2-job groupへ改修。workload/request/pathのswap・重複・欠落、片側nonzero、nested raw inventoryを負例化。
- [test_hooks.py:2572-2635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_hooks.py:2572)、[同:2901-2948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_hooks.py:2901)、[同:3423-3444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_hooks.py:3423)
  - class、entry全field、local evidenceの3 literal goldenへ新submitterを追加。
- [docs/failures.md:13864-13876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/docs/failures.md:13864)
  - 実測後に2-request fan-out終端を追記し、解除条件を「D905実行主体のlandと、その主体による現行closureの批准」に訂正。人間転記案は再掲しない。

## policyとschema

[policy:119-125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.v1.json:119) は変更しません。job body path、1 node、6時間を維持します。

wire contractは互換性のない変更なので、少なくとも次をbumpします。

- submission v3 → v4
- completion v2 → v3
- acquisition v2 → v3
- certification result v2 → v3
- compute result v1 → v2
- raw manifest v2 → v3

reservationのfield shapeは変えずv1を維持します。canonical pathとrequest IDによってworkload entryへ束縛します。

## pin閉包の取り直し結果

親が挙げた5 file以外で、変更が必要なのは [tools/pegasus/README.md:20-53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/README.md:20) です。新しい実行体を本文で案内する場合、admission site表にも載せないと `check_docs` が落とします。

以下はpath以外のpinですが、設計どおりなら変更不要です。

- [test_campaign.py:5198-5212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_campaign.py:5198): `run_campaign` call-site数は1のまま。
- [test_ccbench_spawn_sites.py:110-117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_ccbench_spawn_sites.py:110): driver内git subprocess数は増やさない。
- [test_official_perf_closure.py:44-59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_official_perf_closure.py:44): driver path/roleは不変。
- [qstat fixture:1-4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/fixtures/paper_story_a2/qstat-visibility-945411.stdout:1): job role名 `paper-a2-cert` は維持する。
- [acceptance_duration_ledger.json:9031-9116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/acceptance_duration_ledger.json:9031): test名pinがある。旧test名を変えた場合だけ、親の実測後に正規toolで再生成する。推測値を手書きしない。
- [t1683 cost probe:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/probes/t1683_rr5_cost_probe.py:20): policy pathは不変。
- executable inventoryは [test_hooks.py:3849-3866](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_hooks.py:3849) が動的に拾うため、registry追加が必須。

A-2 driver/job/policyはいずれも `CONTRACT_LOADER_RELATIVE_PATHS` 25件には含まれません。この変更自身は批准closure digestを動かしません。

## 並列度を2より上げる余地

技術的にはjob数を増やせますが、現proof chainを保った同時並列度は2が上限です。

- cell単位4 job: [run_workload:2182-2184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2182) のstock→adopted対を破るため不採用。
- 5反復の分割: repetitionごとのcampaign/WAL/reservationをfan-inする新しい証明が必要。D1059の「回数を減らさない」は守れても、既存の1 campaign・1 WALという束縛を変更するため不採用。
- probe/build/verify/perf相分割: job数は増やせるが相間依存があるため、各workloadで同時実行はできない。最大同時数は結局2。さらにresume契約が必要で、本waveの所有外。
- stock/adoptedを別jobにしてscheduler依存で順次実行: job数4、同時数2に留まり、証拠鎖だけ複雑になるため利点がない。

反復数、full-scale correctness、cell集合は一切変更しません。

## 新設検査と実環境値

新しい外部入力は `IZANAGI_A2_WORKLOAD` だけです。値はexact `rr5|rr50` とし、次の3層で交差束縛します。

1. loginで記録した実 `qsub -v` argv。
2. compute bodyが書く `compute-result/v2.workload`。
3. canonical path `jobs/$workload` / `raw/$workload`。

gate確認の実投入で両値を実測できるため採用できます。新しいNQSV field、PBS array ID、`qsub -W depend=...`、qstatの`Variable_List`検査は、現環境で形式を実測していないため採用しません。可視性stateは既存の実fixtureと共有parserをそのまま使います。

## gateが閉じている今の実測手順

1. login nodeでqueue active、repo/CCBench clean、重複A-2 jobなしを確認する。
2. 新submitterを1回だけ実行する。

```bash
# admission-site: login-direct
tools/pegasus/submit_paper_story_a2_certification.sh \
  --attempt-id t1647-fanout-wiring-YYYYMMDDTHHMMSSZ \
  --ccbench-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/external/ccbench \
  --dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps
```

3. submitterが異なる2 request IDを返し、group submission receiptにexact `rr5,rr50` が入ることを確認する。
4. 2 requestの終端を待ち、次を確認する。
   - 両方に workload別 `allocation-qstat.*` と `reservation.json` がある。
   - 両方に workloadと各PBS IDを持つ `compute-result/v2` がある。
   - 両stderrが `enforcement-source-closure-unratified` で終端する。
   - `compute result already exists`、`reservation result is not fresh`、`allocation qstat evidence is not fresh`、`raw result root is not fresh` がどちらにも出ない。
   - `raw/rr5` と `raw/rr50` は互いに共存し、批准gate手前で止まったためcell resultは作られていない。
   - 各reservationのscript SHAがsubmissionの `job_body_sha256` と一致し、各qsub argv末尾がpolicyのcanonical bodyである。
5. gate閉鎖中は `finalize-raw` と `collect` を実行しない。raw 4 cellが無いため、finalize成功を装ってはならない。
6. request IDs、host、各artifact SHA、期待終端をmeasurement文書とF498追記へ記録する。

これで「2本とも独立にcompute nodeへ入り、単一attemptのfresh検査で片方が殺されず、同じ批准gateまで到達した」ことを配線成功の判定にできます。gate通過後の正式走では、両jobが0で終端してからloginで `finalize-raw` を1回だけ実行します。

静的読解のみで、pytest・shell実走・docs checkerは実行していません。緑とは報告しません。

## 総括

- 1 bodyをworkload径数化し、rr5/rr50の2独立qsubへ分割する。
- raw・compute・reservation・scheduler証拠はworkload別、receiptはexact 2-job groupとする。
- cell対と5反復は維持し、並列度2を上限とする。
- 最大リスクは、単一request前提のreceipt/collector閉包を一部だけ直して片側のscheduler証拠を失うこと。