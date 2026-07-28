"""全 campaign WAL の abort reason 分布と、S2/bench の段別コスト分布を読むだけの集計。"""
import json, glob, collections, os

os.chdir("/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate")
reasons = collections.Counter()
stages = collections.Counter()
per_campaign = collections.defaultdict(collections.Counter)
s2_durations = []
n_files = 0
for path in glob.glob("output/campaigns/*/runs/wal.jsonl"):
    n_files += 1
    camp = path.split("/")[2]
    last_ts = {}
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        stages[r.get("stage")] += 1
        v = r.get("variant")
        ts = r.get("ts")
        p = r.get("payload", {})
        if r.get("stage") == "verify_done" and p.get("workload", {}).get("tag") == "s2":
            prev = last_ts.get(v)
            if prev is not None and ts is not None:
                s2_durations.append(ts - prev)
        if ts is not None and v is not None:
            last_ts[v] = ts
        if r.get("stage") == "abort":
            reason = p.get("reason", "?").split(":")[0]
            reasons[reason] += 1
            per_campaign[camp][reason] += 1
print("files:", n_files)
print("stages:", dict(stages))
print("abort reasons (all campaigns):")
for k, v in reasons.most_common():
    print(f"  {k}: {v}")
print("\nper-campaign (p3 loop 系のみ):")
for c, cnt in sorted(per_campaign.items()):
    if "loop" in c:
        print(f"  {c}: {dict(cnt)}")
if s2_durations:
    s2_durations.sort()
    n = len(s2_durations)
    print(f"\nS2 verify duration (直前 record からの差分, n={n}): "
          f"min={s2_durations[0]:.1f}s median={s2_durations[n//2]:.1f}s max={s2_durations[-1]:.1f}s")
