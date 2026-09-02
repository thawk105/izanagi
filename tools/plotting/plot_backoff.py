#!/usr/bin/env python3
"""backoff sweep campaign の WAL/dat から論文品質の図を生成する。

proof-chain: 図は WAL (runs/wal.jsonl, throughput の n 反復生値)、
dat (reports/*.dat, abort%/IPC の集約値)、campaign.lock を入力とし、生成した図の
provenance ヘッダに「どの campaign のどの commit / ファイルから作ったか」を刻む。

使い方:
    python plot_backoff.py [--baselines LIST] OUT_PREFIX CAMPAIGN_DIR [CAMPAIGN_DIR ...]

    OUT_PREFIX      出力ファイルの接頭辞 (例: figures/backoff_sweep)
    CAMPAIGN_DIR    output/campaigns/<id> のパス。複数指定すると
                    その順で 1 枚の図に横並び (workload 比較) される。
    --baselines    no-backoff / stock-adaptive の comma 区切り部分集合。
                    既定は no-backoff のみ。
                    stock-adaptive は CCBench 既定 3 定数 (刻み 100 µs /
                    上限 1000 µs / 更新間隔 10 µs) の adaptive backoff。
                    既定では描かない。明示例: --baselines stock-adaptive
                    D1506 により、これを単独の適応基準線にした比較は機構の
                    優劣を何も言っていないものとして扱う。

出力:
    <OUT_PREFIX>.png / .pdf   図 (上段 throughput+95%CI, 下段 abort%+IPC)
    <OUT_PREFIX>.provenance.json   入力ファイル・campaign id・数値の記録

依存: matplotlib, numpy のみ (figure-style スキル非依存・自己完結)。
実行は計測機の外で (計測機上では走らせない — 図生成に計測は不要)。
"""
import sys, os, json, re, glob, hashlib, datetime, statistics, shlex

# この script を cwd/PYTHONPATH に依存せず直接起動できるよう、repo 内の中央 campaign
# admission 層への import root を __file__ から解決する。独自の WAL reader は持たない。
_REPO_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
if _REPO_ROOT not in sys.path: sys.path.insert(0,_REPO_ROOT)
from orchestrator.campaign import wal
from orchestrator.campaign.artifact_admission import (
    CampaignReadPurpose,
    require_admitted_campaign,
)

np=mpl=plt=FixedLocator=FixedFormatter=NullLocator=None

def _load_plot_deps():
    """WAL consumer の単体利用では作図依存を要求せず、作図時だけ import する。"""
    global np, mpl, plt, FixedLocator, FixedFormatter, NullLocator
    if np is not None:
        return
    import numpy as _np
    import matplotlib as _mpl
    _mpl.use("Agg")
    import matplotlib.pyplot as _plt
    from matplotlib.ticker import (FixedFormatter as _FixedFormatter,
                                   FixedLocator as _FixedLocator,
                                   NullLocator as _NullLocator)
    np, mpl, plt = _np, _mpl, _plt
    FixedLocator, FixedFormatter, NullLocator = _FixedLocator, _FixedFormatter, _NullLocator

# ---- 内蔵スタイル (publication-grade, 自己完結) ----------------------------
def _style():
    mpl.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200,
        "font.family": "sans-serif", "font.size": 9,
        "axes.titlesize": 9, "axes.labelsize": 8.5,
        "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.3, "grid.linewidth": 0.5,
        "legend.frameon": False, "lines.linewidth": 1.6,
        "figure.constrained_layout.use": False,
    })

FOCAL="#1f6fb2"; NONE="#666666"; ADAPT="#d1495b"; ABORT="#e08214"; IPC="#3a923a"

BASELINE_ORDER=("no-backoff", "stock-adaptive")
DEFAULT_BASELINES=("no-backoff",)
BASELINE_SPECS={
    "no-backoff": {
        "label": "no backoff", "data_key": "none", "color": NONE, "linestyle": "--",
        "linewidth": 1.2,
    },
    "stock-adaptive": {
        "label": "stock adaptive", "data_key": "adapt", "color": ADAPT, "linestyle": ":",
        "linewidth": 1.3,
    },
}

_RUN_CONDITION_KEYS=(
    "thread_num", "ycsb_tuple_num", "extime", "clocks_per_us",
    "ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw",
)
_INTEGER_CONDITIONS={
    "thread_num", "ycsb_tuple_num", "extime", "clocks_per_us", "ycsb_rratio",
    "CCBENCH_TRACE",
}

# ---- パース ----------------------------------------------------------------
def _parse_genome(g):
    d={}
    body=g.split("|",1)[1] if "|" in g else g
    for kv in body.split(","):
        if "=" in kv:
            k,v=kv.split("=",1); d[k]=v
    return d

def _condition_scalar(key, value):
    """WAL の command/build payload に記録された scalar だけを型付きで返す。"""
    if key=="ycsb_rmw":
        normalized=str(value).strip().lower()
        if normalized in ("false", "0"):
            return False
        if normalized in ("true", "1"):
            return True
        raise ValueError(f"ycsb_rmw は boolean でなければならない: {value!r}")
    if key in _INTEGER_CONDITIONS:
        return int(value)
    if key == "ycsb_zipf_skew":
        return float(value)
    return value

def _unique_condition(values):
    """1 値は scalar、不一致は集約せず安定順の list で返す。"""
    unique=[]
    for value in values:
        if value not in unique:
            unique.append(value)
    unique.sort(key=lambda value: (type(value).__name__, repr(value)))
    return unique[0] if len(unique)==1 else unique

def _numactl_arguments(run_cmd):
    """run command 内の numactl 引数列を、順序と綴りを保って返す。"""
    try:
        tokens=shlex.split(run_cmd)
    except ValueError:
        return None
    for index,token in enumerate(tokens):
        if os.path.basename(token)!="numactl":
            continue
        arguments=[]
        take_value=False
        for candidate in tokens[index+1:]:
            if take_value:
                arguments.append(candidate)
                take_value=False
                continue
            if not candidate.startswith("-"):
                break
            arguments.append(candidate)
            if candidate in (
                "-i", "--interleave", "-m", "--membind", "-N", "--cpunodebind",
                "-C", "--physcpubind", "-p", "--preferred", "-w", "--weighted-interleave",
            ):
                take_value=True
        return arguments
    return None

def _extract_conditions(records, cdir):
    """campaign 条件を WAL/build payload/campaign.lock の観測値から構成する。"""
    observed={key: [] for key in _RUN_CONDITION_KEYS}
    observed["numactl_args"]=[]
    run_commands=[]
    env_values=[]
    trace_values=[]
    build_done_count=0
    trace_observation_count=0
    for record in records:
        env_tag=getattr(record, "env_tag", None)
        if env_tag:
            env_values.append(str(env_tag))
        payload=record.payload
        run_cmd=payload.get("run_cmd")
        if run_cmd:
            run_commands.append(run_cmd)
            numactl_args=_numactl_arguments(run_cmd)
            if numactl_args is not None:
                observed["numactl_args"].append(numactl_args)
            for key in _RUN_CONDITION_KEYS:
                match=re.search(rf"(?:^|\s)-{re.escape(key)}=([^\s]+)", run_cmd)
                if match:
                    observed[key].append(_condition_scalar(key, match.group(1)))
        if record.stage=="build_done":
            build_done_count+=1
            found=[]
            for value in payload.values():
                if not isinstance(value, str):
                    continue
                found.extend(re.findall(r"(?:^|\s)-DCCBENCH_TRACE=([^\s]+)", value))
            if found:
                trace_observation_count+=1
                trace_values.extend(_condition_scalar("CCBENCH_TRACE", value)
                                    for value in found)

    conditions={}
    unresolved=[]
    incomplete=[]
    for key in _RUN_CONDITION_KEYS+("numactl_args",):
        values=observed[key]
        if values:
            conditions[key]=_unique_condition(values)
            if len(values)<len(run_commands):
                incomplete.append(key)
        else:
            unresolved.append(key)
    if env_values:
        conditions["env"]=_unique_condition(env_values)
    else:
        unresolved.append("env")
    if trace_values:
        conditions["CCBENCH_TRACE"]=_unique_condition(trace_values)
        if trace_observation_count<build_done_count:
            incomplete.append("CCBENCH_TRACE")
    else:
        unresolved.append("CCBENCH_TRACE")

    lock_path=os.path.join(cdir, "campaign.lock")
    try:
        with open(lock_path, encoding="utf-8") as fh:
            ccbench_commit=json.load(fh).get("ccbench_commit")
    except (FileNotFoundError, OSError, ValueError, TypeError):
        ccbench_commit=None
    if ccbench_commit is not None:
        conditions["ccbench_commit"]=ccbench_commit
    else:
        unresolved.append("ccbench_commit")
    conditions["unresolved_fields"]=sorted(unresolved)
    conditions["incomplete_fields"]=sorted(incomplete)
    return conditions

# t_{0.975, df} (両側 95% = 上側 0.025 臨界値) df=1..28。df>=29 (=n>=30) は正規
# 近似 1.96 を使う。正本: FIGURE_CONVENTIONS.md §2 (小 n は t_{0.975,n-1}·s/√n、
# n>=30 で 1.96·s/√n の近似)。scipy を増やさないための内蔵表。
_T_975 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145,
    15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080,
    22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048,
}

def _t975(df):
    """t_{0.975, df}。df>=29 (n>=30) は正規近似 1.96 (FIGURE_CONVENTIONS.md §2)。"""
    return _T_975.get(df, 1.96)

def _ci95(reps):
    """点推定 = 標本平均、95% CI 半幅 = t_{0.975,n-1}·s/√n。

    正本 FIGURE_CONVENTIONS.md §2: 小 n では t 分布 (t_{0.975,n-1}·s/√n)、n>=30 で
    1.96·s/√n の正規近似。CI 半幅は平均の標準誤差 s/√n なので、中心統計量も標本平均に
    統一する (median 中心に平均 SE を付ける不整合を避ける)。

    n<2 は分散を推定できないので CI は**計算不能**。半幅に 0 を返すと図に幅ゼロの
    誤差棒が「95% CI」として描かれ (実際は不確かさ未知)、査読で崩れる。よって半幅は
    None を返し、描画側 (`_ci95_half_M`) が誤差棒を抑止する。
    """
    a=np.asarray(reps,dtype=float)
    center=_mean_tps(reps)
    if len(a)<2: return center, None
    n=len(a)
    return center, _t975(n-1)*a.std(ddof=1)/np.sqrt(n)

def _mean_tps(reps):
    """baseline の描画値と provenance 値で共有する標本平均。"""
    if not reps:
        raise ValueError("tps repetitions must not be empty")
    return float(statistics.fmean(float(x) for x in reps))

def _ci95_half_M(reps):
    """errorbar 用の 95% CI 半幅 (M tps)。CI 計算不能 (n<2) は NaN を返す。

    matplotlib の errorbar は yerr=NaN の点で誤差棒を描かないので、幅ゼロの棒を
    「95% CI」と偽って描くのを避け、その点だけ誤差棒なし (CI 未知) として表示される。
    """
    half=_ci95(reps)[1]
    return float("nan") if half is None else half/1e6

def load_campaign(cdir):
    """1 campaign を読み、workload ラベル・sweep 点・baseline を返す。"""
    historical_view=require_admitted_campaign(
        cdir, purpose=CampaignReadPurpose.HISTORICAL_RAW)
    wal_path=historical_view.wal_file
    # Historical admission may preserve a crash-prefix tail for forensic reads.
    # Plot inputs must be complete: validate every physical frame before using
    # the immutable partial projection returned by the historical view.
    for _ in wal.iter_lines(wal_path):
        pass
    dat_paths=glob.glob(os.path.join(cdir,"reports","*.dat"))
    if not dat_paths:
        raise FileNotFoundError(f"dat がない: {cdir}/reports/*.dat")
    dat_path=dat_paths[0]

    recs=historical_view.records
    genome={x.variant:_parse_genome(x.payload["genome"])
            for x in recs if x.stage=="build_start"}
    thread_nums=set()
    for x in recs:
        rc=x.payload.get("run_cmd","")
        m=re.search(r"thread_num=(\d+)", rc or "")
        if m: thread_nums.add(int(m.group(1)))

    pending_bench={}; committed_bench={}
    for x in recs:
        variant=x.variant
        if x.stage=="bench_done":
            pending_bench[variant]=x
        elif x.stage=="commit" and variant in pending_bench:
            committed_bench[variant]=pending_bench.pop(variant)
    excluded_uncertified=sorted(pending_bench)
    pts=[]; none=None; adapt=None; baseline_genomes={}
    for x in committed_bench.values():
        g=genome.get(x.variant,{}); p=x.payload
        reps=p.get("tps",[]); bf=g.get("BACKOFF_FIXED","-1"); bo=g.get("BACK_OFF","0")
        if bo=="1" and bf not in ("-1",None):
            if not reps:
                raise ValueError(
                    f"{cdir}: static backoff {bf}us の tps repetitions が空")
            pts.append((int(bf),reps))
        elif bo=="0":
            none=reps
            baseline_genomes["no-backoff"]=dict(sorted({
                **g, "BACK_OFF": bo, "BACKOFF_FIXED": bf,
            }.items()))
        if bo=="1" and bf=="-1":
            adapt=reps
            baseline_genomes["stock-adaptive"]=dict(sorted({
                **g, "BACK_OFF": bo, "BACKOFF_FIXED": bf,
            }.items()))
    pts.sort()

    # dat から abort%/IPC (集約値) と workload メタを読む
    abort_ipc={}; meta={}
    with open(dat_path) as fh:
        for line in fh:
            s=line.strip()
            if s.startswith("# workload:"): meta["workload"]=s.split(":",1)[1].strip()
            if s.startswith("# env:"): meta["env"]=s.split(":",1)[1].strip()
            if s.startswith("# campaign:"): meta["campaign"]=s.split(":",1)[1].strip()
            if not s or s.startswith("#"): continue
            parts=re.split(r"\s+",s)
            if len(parts)>=4 and parts[0].lstrip("-").isdigit():
                abort_ipc[int(parts[0])]=(float(parts[2]),float(parts[3]))

    lock_path=os.path.join(cdir, "campaign.lock")
    return {
        "dir":cdir, "wal":wal_path, "dat":dat_path,
        "wal_sha256":_sha256(wal_path), "dat_sha256":_sha256(dat_path),
        "lock":lock_path,
        "lock_sha256":_sha256(lock_path) if os.path.isfile(lock_path) else None,
        "workload":meta.get("workload","?"), "env":meta.get("env","?"),
        "campaign":meta.get("campaign",os.path.basename(cdir)),
        "threads":sorted(thread_nums), "pts":pts, "none":none, "adapt":adapt,
        "baseline_genomes":baseline_genomes,
        "conditions":_extract_conditions(recs, cdir),
        "abort_ipc":abort_ipc,
        "excluded_uncertified":excluded_uncertified,
        "read_purpose":historical_view.read_purpose.value,
        "campaign_verifier_epoch":{
            "campaign_verifier_epoch":(
                historical_view.campaign_verifier_epoch.campaign_verifier_epoch),
            "state":historical_view.campaign_verifier_epoch.state,
            "reason_code":historical_view.campaign_verifier_epoch.reason_code,
            "identity_scope":historical_view.campaign_verifier_epoch.identity_scope,
            "excluded_scope":historical_view.campaign_verifier_epoch.excluded_scope,
            "verifier_assessment_basis":(
                historical_view.verifier_assessment_basis),
        },
    }

def _sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as fh:
        for b in iter(lambda: fh.read(65536), b""): h.update(b)
    return h.hexdigest()

def _provenance_path(path):
    """repo 内 path は provenance gate が要求する repo-relative 表記へ正規化する。"""
    value=os.fspath(path)
    resolved=os.path.abspath(value)
    try:
        if os.path.commonpath((_REPO_ROOT, resolved))==_REPO_ROOT:
            return os.path.relpath(resolved, _REPO_ROOT)
    except ValueError:
        pass
    # repo 外は standalone consumer の互換 seam。着地成果物 gate はこれを拒否する。
    return value

# ---- 作図 ------------------------------------------------------------------
def _short_wl(wl):
    # "read-heavy (ycsb_rmw=0, ...)" -> "read-heavy"
    return wl.split("(")[0].strip() if wl else "?"

def _figure_epoch_label(camps):
    """Return the exact recorded epoch label shown on the figure."""
    epochs=sorted({
        c["campaign_verifier_epoch"]["campaign_verifier_epoch"] for c in camps
    })
    return epochs[0] if len(epochs)==1 else ", ".join(epochs)

def _draw_baseline(axis, reps, spec):
    """baseline を描き、実際に渡した line y / text label / CI 半幅を返す。"""
    if not reps:
        return None
    center,half=_ci95(reps)
    center_m=center/1e6
    if half is not None:
        axis.axhspan((center-half)/1e6, (center+half)/1e6,
                     color=spec["color"], alpha=0.10, lw=0, zorder=1)
    axis.axhline(center_m,color=spec["color"],ls=spec["linestyle"],
                 lw=spec["linewidth"],zorder=2)
    label=spec["label"]
    axis.text(0.58,center_m,label,transform=axis.get_yaxis_transform(),
              color=spec["color"],va="bottom",ha="left",fontsize=6)
    return {
        "label": label,
        "value_tps": center_m*1e6,
        "ci95_half_tps": None if half is None else float(half),
    }

def make_figure(camps, out_prefix, baselines=DEFAULT_BASELINES):
    _load_plot_deps()
    _style()
    baselines=_validated_baselines(baselines)
    n=len(camps)
    fig,axes=plt.subplots(2,n,figsize=(3.9*n,6.6),squeeze=False)
    twins=[]
    facts={}
    rendered_baselines=[]
    for j,c in enumerate(camps):
        wl=_short_wl(c["workload"]); pts=c["pts"]
        if not pts:
            raise ValueError(
                f"{c['campaign']}: historical committed static-backoff pointが無い "
                f"(excluded uncertified BENCH_DONE={len(c['excluded_uncertified'])})")
        if any(not reps for _,reps in pts):
            raise ValueError(f"{c['campaign']}: static backoff の tps repetitions が空")
        xs=[bf for bf,_ in pts]
        ms=[_ci95(r)[0]/1e6 for _,r in pts]; cis=[_ci95_half_M(r) for _,r in pts]
        none_m=_ci95(c["none"])[0]/1e6 if c["none"] else None
        adapt_m=_ci95(c["adapt"])[0]/1e6 if c["adapt"] else None
        # top: throughput
        axt=axes[0,j]
        panel_baselines=[]
        for baseline in baselines:
            spec=BASELINE_SPECS[baseline]
            record=_draw_baseline(axt, c.get(spec["data_key"]), spec)
            if record is not None:
                genome=c.get("baseline_genomes", {}).get(baseline)
                if not genome:
                    raise ValueError(
                        f"{c['campaign']}: {baseline} の描画 genome が無い")
                panel_baselines.append({**record, "genome": dict(genome)})
        rendered_baselines.append(panel_baselines)
        axt.errorbar(xs,ms,yerr=cis,fmt="o-",color=FOCAL,capsize=3,ms=5.5,zorder=3)
        pk=int(np.argmax(ms))
        if 0<pk<len(ms)-1:
            axt.annotate(f"peak {ms[pk]:.2f}M @ {xs[pk]}\u00b5s",(xs[pk],ms[pk]),
                         textcoords="offset points",xytext=(6,9),ha="left",
                         fontsize=6.5,color=FOCAL,fontweight="bold")
        _logx(axt,xs); axt.set_ylim(0,None); axt.margins(y=0.20)
        axt.set_title(wl,pad=14)
        # bottom: abort% + IPC
        axb=axes[1,j]
        ab=[c["abort_ipc"].get(bf,(np.nan,np.nan))[0] for bf in xs]
        ip=[c["abort_ipc"].get(bf,(np.nan,np.nan))[1] for bf in xs]
        axb.plot(xs,ab,"s-",color=ABORT,lw=1.5,ms=4.5,zorder=3)
        axb.set_ylim(0,100); _logx(axb,xs)
        axb.set_xlabel("static backoff (\u00b5s)"); axb.tick_params(axis="y",colors=ABORT)
        axr=axb.twinx(); twins.append((axb,axr))
        axr.plot(xs,ip,"^:",color=IPC,lw=1.5,ms=4.8,zorder=3)
        axr.set_ylim(0,2.0); axr.tick_params(axis="y",colors=IPC)
        axr.set_xscale("log"); axr.xaxis.set_minor_locator(NullLocator())
        axr.tick_params(axis="x",which="both",labelbottom=False)
        if j<n-1: axr.set_yticklabels([])
        if j>0: axb.set_yticklabels([])
        if j==0:
            axb.text(0.05,0.92,"abort rate",transform=axb.transAxes,color=ABORT,fontsize=6.8,fontweight="bold")
            axb.text(0.05,0.83,"IPC",transform=axb.transAxes,color=IPC,fontsize=6.8,fontweight="bold")
        facts[wl]={"best_bf":xs[pk],"best_M":ms[pk],
                   "none_M":none_m,"adapt_M":adapt_m,
                   "n_reps":len(pts[0][1]) if pts else 0,
                   "campaign_verifier_epoch":c["campaign_verifier_epoch"][
                       "campaign_verifier_epoch"],
                   "read_purpose":c["read_purpose"]}
    axes[0,0].set_ylabel("throughput (M tps)")
    axes[1,0].set_ylabel("abort rate (%)",color=ABORT)
    twins[-1][1].set_ylabel("IPC",color=IPC)
    axes[0,0].text(0.04,0.06,"static backoff",transform=axes[0,0].transAxes,
                   color=FOCAL,ha="left",va="bottom",fontsize=7,fontweight="bold")
    # 共通条件をサブタイトルに
    thr=sorted({t for c in camps for t in c["threads"]})
    env=camps[0]["env"]
    thr_s = f"{thr[0]} threads" if len(thr)==1 else f"threads={thr}"
    nrep = facts[list(facts)[0]]["n_reps"]
    epoch_label=_figure_epoch_label(camps)
    fig.suptitle(f"Silo static backoff sweep — {thr_s}, {env}  "
                 f"(n={nrep} reps; top error bars = 95% CI; epoch={epoch_label})",
                 fontsize=9, y=1.00)
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_prefix) or ".", exist_ok=True)
    # bottom x軸ラベルを twin 上書き後に再適用
    for j in range(n):
        _logx(axes[1,j], [bf for bf,_ in camps[j]["pts"]])
    fig.savefig(out_prefix+".png", bbox_inches="tight")
    fig.savefig(out_prefix+".pdf", bbox_inches="tight")
    _overlap_check(fig)
    return facts,rendered_baselines

def _logx(ax,xs):
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator(xs))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(FixedFormatter([str(x) for x in xs]))

def _overlap_check(fig):
    r=fig.canvas.get_renderer()
    texts=[(t,t.get_window_extent(r)) for t in fig.findobj(mpl.text.Text)
           if t.get_text().strip() and t.get_visible()]
    tickset=set()
    for ax in fig.axes: tickset|=set(ax.get_xticklabels()+ax.get_yticklabels())
    ov=[(a.get_text(),b.get_text()) for i,(a,ba) in enumerate(texts)
        for b,bb in texts[i+1:]
        if ba.overlaps(bb) and not (a in tickset and b in tickset)]
    if ov: sys.stderr.write(f"[warn] text overlaps: {ov}\n")

# ---- main ------------------------------------------------------------------
def _validated_baselines(values):
    values=tuple(values)
    unknown=[value for value in values if value not in BASELINE_SPECS]
    if unknown:
        raise ValueError(f"未知の baseline: {', '.join(unknown)}")
    if not values:
        raise ValueError("--baselines は空にできない")
    if len(set(values))!=len(values):
        raise ValueError("--baselines に同じ値を重複指定できない")
    return tuple(value for value in BASELINE_ORDER if value in values)

def _parse_cli(argv):
    positional=[]
    baseline_arg=None
    index=1
    while index<len(argv):
        arg=argv[index]
        if arg in ("-h", "--help"):
            return None
        if arg=="--baselines":
            if baseline_arg is not None:
                raise ValueError("--baselines は 1 回だけ指定する")
            index+=1
            if index>=len(argv):
                raise ValueError("--baselines に LIST が必要")
            baseline_arg=argv[index]
        elif arg.startswith("--baselines="):
            if baseline_arg is not None:
                raise ValueError("--baselines は 1 回だけ指定する")
            baseline_arg=arg.split("=",1)[1]
        elif arg.startswith("-"):
            raise ValueError(f"未知の option: {arg}")
        else:
            positional.append(arg)
        index+=1
    if len(positional)<2:
        raise ValueError("OUT_PREFIX と 1 件以上の CAMPAIGN_DIR が必要")
    if baseline_arg is None:
        baselines=DEFAULT_BASELINES
    else:
        baselines=_validated_baselines(baseline_arg.split(","))
    return positional[0], positional[1:], baselines

def _output_provenance(out_prefix):
    paths=[out_prefix+".png", out_prefix+".pdf"]
    if not all(os.path.isfile(path) for path in paths):
        return []
    return [{"path": _provenance_path(path), "sha256": _sha256(path)} for path in paths]

def main(argv):
    try:
        parsed=_parse_cli(argv)
    except ValueError as exc:
        sys.stderr.write(f"[error] {exc}\n")
        sys.stderr.write(__doc__)
        return 2
    if parsed is None:
        sys.stdout.write(__doc__)
        return 0
    out_prefix,cdirs,baselines=parsed
    camps=[load_campaign(d) for d in cdirs]
    # 既存 consumer は 2 引数の make_figure を差し替える。既定時はその seam を保つ。
    if baselines==DEFAULT_BASELINES:
        facts,rendered_baselines=make_figure(camps, out_prefix)
    else:
        facts,rendered_baselines=make_figure(camps, out_prefix, baselines=baselines)
    if len(rendered_baselines)!=len(camps):
        raise ValueError("make_figure の baseline 描画記録数が campaign 数と一致しない")
    for c in camps:
        wl=_short_wl(c["workload"])
        if wl in facts:
            facts[wl].setdefault(
                "campaign_verifier_epoch",
                c["campaign_verifier_epoch"]["campaign_verifier_epoch"],
            )
            facts[wl].setdefault("read_purpose", c["read_purpose"])
    prov={
        "schema": "izanagi-backoff-figure-provenance/v2",
        "generated_utc": datetime.datetime.utcnow().isoformat()+"Z",
        "generator": os.path.basename(__file__),
        "generator_source": {
            "path": os.path.relpath(os.path.abspath(__file__), _REPO_ROOT),
            "sha256": _sha256(os.path.abspath(__file__)),
        },
        "outputs": _output_provenance(out_prefix),
        "inputs": [{"campaign":c["campaign"],"dir":_provenance_path(c["dir"]),
                    "wal":_provenance_path(c["wal"]),"wal_sha256":c["wal_sha256"],
                    "dat":_provenance_path(c["dat"]),"dat_sha256":c["dat_sha256"],
                    "lock":_provenance_path(c["lock"]),"lock_sha256":c["lock_sha256"],
                    "threads":c["threads"],"env":c["env"],
                    "baselines":rendered_baselines[index],
                    "conditions":c["conditions"],
                    "read_purpose":c["read_purpose"],
                    "campaign_verifier_epoch":c["campaign_verifier_epoch"],
                    "excluded_uncertified_bench_done":c["excluded_uncertified"]}
                   for index,c in enumerate(camps)],
        "facts": facts,
    }
    with open(out_prefix+".provenance.json","w") as fh:
        json.dump(prov, fh, ensure_ascii=False, indent=2)
    print(f"wrote {out_prefix}.png / .pdf / .provenance.json")
    for c in camps:
        excluded=c["excluded_uncertified"]
        if excluded:
            print(f"  {c['campaign']}: excluded {len(excluded)} uncertified BENCH_DONE "
                  f"(後続COMMITなし): {', '.join(excluded)}")
    for wl,f in facts.items():
        print(f"  {wl}: historical best {f['best_M']:.2f}M @ {f['best_bf']}\u00b5s "
              f"(epoch={f['campaign_verifier_epoch']}; "
              f"none={f['none_M']:.2f}M adapt={f['adapt_M']:.2f}M n={f['n_reps']})")
    return 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv))
