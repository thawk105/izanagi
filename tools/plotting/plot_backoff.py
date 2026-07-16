#!/usr/bin/env python3
"""backoff sweep campaign の WAL/dat から論文品質の図を生成する。

proof-chain: 図は WAL (runs/wal.jsonl, throughput の n 反復生値) と
dat (reports/*.dat, abort%/IPC の集約値) だけを入力とし、生成した図の
provenance ヘッダに「どの campaign のどの commit / ファイルから作ったか」を刻む。

使い方:
    python plot_backoff.py OUT_PREFIX CAMPAIGN_DIR [CAMPAIGN_DIR ...]

    OUT_PREFIX      出力ファイルの接頭辞 (例: figures/backoff_sweep)
    CAMPAIGN_DIR    output/campaigns/<id> のパス。複数指定すると
                    その順で 1 枚の図に横並び (workload 比較) される。

出力:
    <OUT_PREFIX>.png / .pdf   図 (上段 throughput+95%CI, 下段 abort%+IPC)
    <OUT_PREFIX>.provenance.json   入力ファイル・campaign id・数値の記録

依存: matplotlib, numpy のみ (figure-style スキル非依存・自己完結)。
実行は計測機の外で (計測機上では走らせない — 図生成に計測は不要)。
"""
import sys, os, json, re, glob, hashlib, datetime

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

# ---- パース ----------------------------------------------------------------
def _parse_genome(g):
    d={}
    body=g.split("|",1)[1] if "|" in g else g
    for kv in body.split(","):
        if "=" in kv:
            k,v=kv.split("=",1); d[k]=v
    return d

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
    統一する (median 中心に平均 SE を付ける不整合を避ける)。n<2 は CI 幅 0。
    """
    a=np.asarray(reps,dtype=float)
    if len(a)<2: return float(np.mean(a)), 0.0
    n=len(a)
    return float(np.mean(a)), _t975(n-1)*a.std(ddof=1)/np.sqrt(n)

def load_campaign(cdir):
    """1 campaign を読み、workload ラベル・sweep 点・baseline を返す。"""
    wal_path=os.path.join(cdir,"runs","wal.jsonl")
    dat_paths=glob.glob(os.path.join(cdir,"reports","*.dat"))
    if not os.path.exists(wal_path):
        raise FileNotFoundError(f"WAL がない: {wal_path}")
    if not dat_paths:
        raise FileNotFoundError(f"dat がない: {cdir}/reports/*.dat")
    dat_path=dat_paths[0]

    recs=[]
    with open(wal_path) as fh:
        for line in fh:
            line=line.strip()
            if line.startswith("{"): recs.append(json.loads(line))
    genome={x["variant"]:_parse_genome(x["payload"]["genome"])
            for x in recs if x.get("stage")=="build_start"}
    thread_nums=set()
    for x in recs:
        rc=x.get("payload",{}).get("run_cmd","")
        m=re.search(r"thread_num=(\d+)", rc or "")
        if m: thread_nums.add(int(m.group(1)))

    pending_bench={}; certified_bench={}
    for x in recs:
        variant=x.get("variant")
        if x.get("stage")=="bench_done":
            pending_bench[variant]=x
        elif x.get("stage")=="commit" and variant in pending_bench:
            certified_bench[variant]=pending_bench.pop(variant)
    excluded_uncertified=sorted(pending_bench)
    pts=[]; none=None; adapt=None
    for x in certified_bench.values():
        g=genome.get(x["variant"],{}); p=x["payload"]
        reps=p.get("tps",[]); bf=g.get("BACKOFF_FIXED","-1"); bo=g.get("BACK_OFF","0")
        if bo=="1" and bf not in ("-1",None): pts.append((int(bf),reps))
        elif bo=="0": none=reps
        if bo=="1" and bf=="-1": adapt=reps
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

    return {
        "dir":cdir, "wal":wal_path, "dat":dat_path,
        "wal_sha256":_sha256(wal_path), "dat_sha256":_sha256(dat_path),
        "workload":meta.get("workload","?"), "env":meta.get("env","?"),
        "campaign":meta.get("campaign",os.path.basename(cdir)),
        "threads":sorted(thread_nums), "pts":pts, "none":none, "adapt":adapt,
        "abort_ipc":abort_ipc,
        "excluded_uncertified":excluded_uncertified,
    }

def _sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as fh:
        for b in iter(lambda: fh.read(65536), b""): h.update(b)
    return h.hexdigest()[:16]

# ---- 作図 ------------------------------------------------------------------
def _short_wl(wl):
    # "read-heavy (ycsb_rmw=0, ...)" -> "read-heavy"
    return wl.split("(")[0].strip() if wl else "?"

def make_figure(camps, out_prefix):
    _load_plot_deps()
    _style()
    n=len(camps)
    fig,axes=plt.subplots(2,n,figsize=(3.9*n,6.6),squeeze=False)
    twins=[]
    facts={}
    for j,c in enumerate(camps):
        wl=_short_wl(c["workload"]); pts=c["pts"]
        if not pts:
            raise ValueError(
                f"{c['campaign']}: certified static-backoff pointが無い "
                f"(excluded uncertified BENCH_DONE={len(c['excluded_uncertified'])})")
        xs=[bf for bf,_ in pts]
        ms=[_ci95(r)[0]/1e6 for _,r in pts]; cis=[_ci95(r)[1]/1e6 for _,r in pts]
        none_m=_ci95(c["none"])[0]/1e6 if c["none"] else None
        adapt_m=_ci95(c["adapt"])[0]/1e6 if c["adapt"] else None
        # top: throughput
        axt=axes[0,j]
        if none_m is not None: axt.axhline(none_m,color=NONE,ls="--",lw=1.2)
        if adapt_m is not None: axt.axhline(adapt_m,color=ADAPT,ls=":",lw=1.3)
        axt.errorbar(xs,ms,yerr=cis,fmt="o-",color=FOCAL,capsize=3,ms=5.5,zorder=3)
        pk=int(np.argmax(ms))
        if 0<pk<len(ms)-1:
            axt.annotate(f"peak {ms[pk]:.2f}M @ {xs[pk]}\u00b5s",(xs[pk],ms[pk]),
                         textcoords="offset points",xytext=(6,9),ha="left",
                         fontsize=6.5,color=FOCAL,fontweight="bold")
        _logx(axt,xs); axt.set_ylim(0,None); axt.margins(y=0.20)
        axt.set_title(wl,pad=14)
        if none_m is not None:
            axt.text(0.58,none_m,"no backoff",transform=axt.get_yaxis_transform(),
                     color=NONE,va="bottom",ha="left",fontsize=6)
        if adapt_m is not None:
            axt.text(0.58,adapt_m,"stock adaptive",transform=axt.get_yaxis_transform(),
                     color=ADAPT,va="bottom",ha="left",fontsize=6)
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
                   "n_reps":len(pts[0][1]) if pts else 0}
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
    fig.suptitle(f"Silo static backoff sweep — {thr_s}, {env}  "
                 f"(n={nrep} reps; top error bars = 95% CI)", fontsize=9, y=1.00)
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_prefix) or ".", exist_ok=True)
    # bottom x軸ラベルを twin 上書き後に再適用
    for j in range(n):
        _logx(axes[1,j], [bf for bf,_ in camps[j]["pts"]])
    fig.savefig(out_prefix+".png", bbox_inches="tight")
    fig.savefig(out_prefix+".pdf", bbox_inches="tight")
    _overlap_check(fig)
    return facts

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
def main(argv):
    if len(argv)<3:
        sys.stderr.write(__doc__); return 2
    out_prefix=argv[1]; cdirs=argv[2:]
    camps=[load_campaign(d) for d in cdirs]
    facts=make_figure(camps, out_prefix)
    prov={
        "generated_utc": datetime.datetime.utcnow().isoformat()+"Z",
        "generator": os.path.basename(__file__),
        "inputs": [{"campaign":c["campaign"],"dir":c["dir"],
                    "wal":c["wal"],"wal_sha256":c["wal_sha256"],
                    "dat":c["dat"],"dat_sha256":c["dat_sha256"],
                    "threads":c["threads"],"env":c["env"],
                    "excluded_uncertified_bench_done":c["excluded_uncertified"]}
                   for c in camps],
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
        print(f"  {wl}: best {f['best_M']:.2f}M @ {f['best_bf']}\u00b5s "
              f"(none={f['none_M']:.2f}M adapt={f['adapt_M']:.2f}M n={f['n_reps']})")
    return 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv))
