# 費用と系列数の試算 (段 6 の所見 M1 を反映した v3、親が login の python3 で実行、計算ノードの計算ではない)

v2 (段 4) は本比較の bal を「試走課題の 1 block 合計の最大」で代入し、下側に E_T の再計測を足していなかった。v3 は §8.1 の
c(t, m) の定義どおり、E_T の再計測を全系列に足し、bal を手法ごとの最大値で代入する。

## script (job dir の `cost-model-v3.py` と同じ内容)

```python
# T-2850 試走・本比較の費用と系列数の試算 v2 (段 4 裁定後の規則)
# 単価の出所: B-5 発効束 insight §10 (wh = 実測、rh = 試算、準備 600 s = 試算、親待ち 780 s = 実測 736 s の丸め上げ)
import math

S = {"wh": (499, 510), "rh": (817, 1007)}
PREP, WAIT = 600, 780
B, K, NEVAL, SERIES = 10, 2, 5, 3
PER_SERIES = 1 + K + B + NEVAL          # 18 (試走は E_T の再計測をしない)
BLOCK_SESS = 5 + 5                      # block stock 5 + 参照点 5

def series_cost(lo_hi, llm, extra=0):
    lo, hi = lo_hi
    base = lambda u: (PER_SERIES + extra) * u + PREP + (B * WAIT if llm else 0)
    return base(lo), base(hi)

print("== 試走 (2 課題 × 5 手法 × 3 系列、3 block)")
tot = [0, 0]
cells = {}
for w, u in S.items():
    nl = series_cost(u, False); ll = series_cost(u, True)
    bl = (BLOCK_SESS * u[0] + PREP, BLOCK_SESS * u[1] + PREP)
    t = [4 * SERIES * nl[i] + SERIES * ll[i] + 3 * bl[i] for i in (0, 1)]
    cells[w] = (nl, ll, bl)
    print(w, "非LLM", nl, "LLM", ll, "block", bl, "計 h", [round(x / 3600, 1) for x in t])
    tot = [tot[i] + t[i] for i in (0, 1)]
print("試走 計 h", [round(x / 3600, 1) for x in tot], "論理 session", 2 * (5 * SERIES * PER_SERIES + 3 * BLOCK_SESS))
print("A=30 使い切りの親待ち追加 (LLM 6 系列) h", round(6 * 20 * WAIT / 3600, 1))

print("== 本比較: §8.1 の c(t, m) = 系列 + block job の 1/5 + E_T 再計測 5 session (計画用、常に加算)")
print("   試走していない課題 (bal) は手法ごとに試走課題の c の最大値 (v3 で §8.1 の文言に合わせて明確化)")
def c(u, llm, i, et=True):
    return series_cost(u, llm, NEVAL if et else 0)[i] + (BLOCK_SESS * u[i] + PREP) / 5
methods = [False] * 4 + [True]
for et in (True, False):
    for i, side in ((0, "下側"), (1, "上側")):
        per = {w: [c(u, llm, i, et) for llm in methods] for w, u in S.items()}
        per["bal"] = [max(per[w][k] for w in S) for k in range(5)]
        row = {w: sum(v) for w, v in per.items()}
        label = "計画用 (E_T 再計測を全系列に加算)" if et else "参考 (E_T 再計測が 1 件も要らない場合)"
        print(label, side, {w: round(v) for w, v in row.items()},
              "; ".join(f"n={n}: {n * sum(row.values()) / 3600:.1f}" for n in (5, 8, 10, 12)), "node 時間")


# t 分位点 (標準ライブラリ、正則化不完全ベータの連分数 + 二分法)
def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 300, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > FPMIN else FPMIN); h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > FPMIN else FPMIN)
        c = 1 + aa / c; c = c if abs(c) > FPMIN else FPMIN; h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > FPMIN else FPMIN)
        c = 1 + aa / c; c = c if abs(c) > FPMIN else FPMIN
        de = d * c; h *= de
        if abs(de - 1) < EPS: break
    return h
def betai(a, b, x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    return bt * betacf(a, b, x) / a if x < (a + 1) / (a + b + 2) else 1 - bt * betacf(b, a, 1 - x) / b
def t_cdf(t, df):
    x = df / (df + t * t); p = 0.5 * betai(df / 2, 0.5, x)
    return 1 - p if t > 0 else p
def t_q(p, df):
    lo, hi = 0.0, 1000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2
assert abs(t_q(0.975, 7) - 2.3646) < 1e-3

DELTA = math.log(1.03); H2 = math.log(1.05)
def h(n, s, M): return t_q(1 - 0.025 / M, n - 1) * s / math.sqrt(n)
def nmin(target, s, M):
    n = 5
    while h(n, s, M) > target: n += 1
    return n
print("== 系列数の表 (s = 計画に使う対差の標準偏差、M = 族の大きさ)")
print("delta", round(DELTA, 6), "delta/2", round(DELTA / 2, 6), "ln1.05", round(H2, 6))
for M in (20, 30):
    for s in (0.01, 0.02, 0.03, 0.05, 0.08):
        print(f"M={M} s={s}: n1={nmin(DELTA/2, s, M)} n2={nmin(H2, s, M)} h(5)={h(5, s, M):.4f}")
```

## 出力

```
== 試走 (2 課題 × 5 手法 × 3 系列、3 block)
wh 非LLM (9582, 9780) LLM (17382, 17580) block (5590, 5700) 計 h [51.1, 52.0]
rh 非LLM (15306, 18726) LLM (23106, 26526) block (8770, 10670) 計 h [77.6, 93.4]
試走 計 h [128.7, 145.4] 論理 session 600
A=30 使い切りの親待ち追加 (LLM 6 系列) h 26.0
== 本比較: §8.1 の c(t, m) = 系列 + block job の 1/5 + E_T 再計測 5 session (計画用、常に加算)
   試走していない課題 (bal) は手法ごとに試走課題の c の最大値 (v3 で §8.1 の文言に合わせて明確化)
計画用 (E_T 再計測を全系列に加算) 下側 {'wh': 73775, 'rh': 113525, 'bal': 113525} n=5: 417.8; n=8: 668.5; n=10: 835.6; n=12: 1002.8 node 時間
計画用 (E_T 再計測を全系列に加算) 上側 {'wh': 75150, 'rh': 137275, 'bal': 137275} n=5: 485.7; n=8: 777.1; n=10: 971.4; n=12: 1165.7 node 時間
参考 (E_T 再計測が 1 件も要らない場合) 下側 {'wh': 61300, 'rh': 93100, 'bal': 93100} n=5: 343.8; n=8: 550.0; n=10: 687.5; n=12: 825.0 node 時間
参考 (E_T 再計測が 1 件も要らない場合) 上側 {'wh': 62400, 'rh': 112100, 'bal': 112100} n=5: 398.1; n=8: 636.9; n=10: 796.1; n=12: 955.3 node 時間
== 系列数の表 (s = 計画に使う対差の標準偏差、M = 族の大きさ)
delta 0.029559 delta/2 0.014779 ln1.05 0.04879
M=20 s=0.01: n1=9 n2=5 h(5)=0.0302
M=20 s=0.02: n1=22 n2=6 h(5)=0.0604
M=20 s=0.03: n1=43 n2=8 h(5)=0.0907
M=20 s=0.05: n1=110 n2=15 h(5)=0.1511
M=20 s=0.08: n1=273 n2=30 h(5)=0.2418
M=30 s=0.01: n1=10 n2=5 h(5)=0.0337
M=30 s=0.02: n1=24 n2=7 h(5)=0.0673
M=30 s=0.03: n1=47 n2=9 h(5)=0.1010
M=30 s=0.05: n1=119 n2=16 h(5)=0.1683
M=30 s=0.08: n1=296 n2=32 h(5)=0.2694
```
