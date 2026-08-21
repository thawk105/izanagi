# T-1142 R33 n-pilot 投入手順

この手順は人間が login node で実行するためのもの。Codex/AI は qsub を実行しない。
reserve の receipt と3 allocation の result/manifest が揃った後に、aggregate は qsub
を使わず login node の driver を直接実行する。

作業対象の repo、protocol、外部 output/cache root は次の固定値とする。

```bash
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1142-n-pilot-admission-redesign
mkdir -m 0700 /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output
mkdir -m 0700 /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-cache
```

campaign は `t1142-r33-run-1` に固定する。まず reserve を1回だけ投入する。

```bash
bash tools/pegasus/submit_oracle_n_pilot.sh \
  --mode reserve \
  --protocol /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1142-n-pilot-admission-redesign/output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json \
  --output-root /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output \
  --campaign-run-id t1142-r33-run-1 \
  --admission-manifest /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/admission.json \
  --confirm-irreversible-pilot-holdout
```

reserve job の完了と admission manifest の作成を確認してから、allocation 0, 1, 2 を
それぞれ1回投入する。cache root は各 allocation で異なる create-only path にする。

```bash
bash tools/pegasus/submit_oracle_n_pilot.sh \
  --mode consume \
  --protocol /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1142-n-pilot-admission-redesign/output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json \
  --output-root /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output \
  --campaign-run-id t1142-r33-run-1 \
  --allocation-index 0 \
  --admission-manifest /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/admission.json \
  --cache-root /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-cache/t1142-r33-run-1-allocation-0 \
  --confirm-irreversible-pilot-holdout

bash tools/pegasus/submit_oracle_n_pilot.sh \
  --mode consume \
  --protocol /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1142-n-pilot-admission-redesign/output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json \
  --output-root /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output \
  --campaign-run-id t1142-r33-run-1 \
  --allocation-index 1 \
  --admission-manifest /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/admission.json \
  --cache-root /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-cache/t1142-r33-run-1-allocation-1 \
  --confirm-irreversible-pilot-holdout

bash tools/pegasus/submit_oracle_n_pilot.sh \
  --mode consume \
  --protocol /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1142-n-pilot-admission-redesign/output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json \
  --output-root /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output \
  --campaign-run-id t1142-r33-run-1 \
  --allocation-index 2 \
  --admission-manifest /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/admission.json \
  --cache-root /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-cache/t1142-r33-run-1-allocation-2 \
  --confirm-irreversible-pilot-holdout
```

3 allocation の `result.json` と admission manifest が揃ったことを確認した後、aggregate
は次の1回を login node で直接実行する。

```bash
python3 -I -B orchestrator/campaign/s8b_oracle_n_pilot.py \
  --protocol /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1142-n-pilot-admission-redesign/output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json \
  --output /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/aggregate.json \
  --aggregate \
    /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/allocation-0/result.json \
    /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/allocation-1/result.json \
    /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/allocation-2/result.json \
  --admission-manifest \
    /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/admission.json \
    /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/admission.json \
    /work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/r33-output/t1142-r33-run-1/admission.json
```

aggregate の driver CLI は allocation identity を result 側から検証する。3つの manifest
引数は driver の exact cardinality 契約を満たすために同じ receipt file を3回指定する。
