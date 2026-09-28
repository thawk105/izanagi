# 見積りの計算の逐語 (repo 外 job dir で実行、計算投入 0)

- 実行: `python3 estimate_p5.py > estimate_p5.json` (2026-09-28、Pegasus login node、rc=0)。
- 入力: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-v2-followup/section8.json` だけ (score を含まない)。
- 入力の SHA-256: `2cf71e71b3ba57895beae522acbaa0f11db5e43c7f611c0fe285fd6b146e5a16`
- 出力の SHA-256: `7773f617cedc850e0bb9a428cc94265ef2e1f8c2447babee9a6375fbad291330`

## estimate_p5.py

```python
"""[T-2852] P5 の見積り: 試走 v2 (t2850-trial-v2) の実測単価から node 時間・LLM 直列時間・暦・計画半幅を出す。
入力は T-2850 の集計 file のうち score を含まない section8.json だけ (score は読まない)。
t 分位点は T-2850 の section8.py と同じ標準ライブラリの不完全ベータ実装を写した。
"""
import json, math, statistics
from pathlib import Path

SRC = Path('/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-v2-followup/section8.json')
d = json.loads(SRC.read_text())


def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 300, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    cc, dd = 1.0, 1 - qab * x / qap
    dd = 1 / (dd if abs(dd) > FPMIN else FPMIN); h = dd
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        dd = 1 + aa * dd; dd = 1 / (dd if abs(dd) > FPMIN else FPMIN)
        cc = 1 + aa / cc; cc = cc if abs(cc) > FPMIN else FPMIN; h *= dd * cc
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        dd = 1 + aa * dd; dd = 1 / (dd if abs(dd) > FPMIN else FPMIN)
        cc = 1 + aa / cc; cc = cc if abs(cc) > FPMIN else FPMIN
        de = dd * cc; h *= de
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
    lo, hi = 0.0, 1e6
    for _ in range(300):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2


assert abs(t_q(0.975, 7) - 2.3646) < 1e-3
DELTA, H2 = math.log(1.03), math.log(1.05)

# ---- 実測単価 (試走 v2、S1-wh) ----
llm_el = d['cell_elapse_s']['llm']                      # 系列の job Elapse
blk_el = d['block_elapse_s']                            # block job の Elapse
ell = [v['sum_s'] for v in d['llm_serial_s'].values()]  # LLM の待ち (直列時間)
opp = [v['opportunities'] for v in d['llm_serial_s'].values()]
s_llm = d['s_cell']['llm']
s_plan = d['s_plan']

med = statistics.median
unit = {
    'llm_series_elapse_s': {'median': med(llm_el), 'min': min(llm_el), 'max': max(llm_el), 'values': llm_el},
    'block_elapse_s': {'median': med(blk_el), 'min': min(blk_el), 'max': max(blk_el)},
    'llm_wait_s': {'median': med(ell), 'min': min(ell), 'max': max(ell)},
    'opportunities': {'min': min(opp), 'max': max(opp), 'values': opp},
    'llm_nonwait_s': {'values': [e - w for e, w in zip(llm_el, [d['llm_serial_s'][f'llm/series-{i}']['sum_s'] for i in (1, 2, 3)])]},
    's_llm': s_llm, 's_plan': s_plan,
}


def cost(cells, n):
    """cells 本の LLM 系列 + block job 1 本を 1 block とし、n block の node 時間 (h)。"""
    series = cells * n
    lo = (series * min(llm_el) + n * min(blk_el)) / 3600
    mid = (series * med(llm_el) + n * med(blk_el)) / 3600
    hi = (series * max(llm_el) + n * max(blk_el)) / 3600
    wait_mid = series * med(ell) / 3600
    wait_lo = series * min(ell) / 3600
    wait_hi = series * max(ell) / 3600
    return {'series': series, 'evals_B': series * 10, 'node_h': [round(lo, 1), round(mid, 1), round(hi, 1)],
            'llm_serial_h': [round(wait_lo, 1), round(wait_mid, 1), round(wait_hi, 1)],
            'opportunities': [series * min(opp), series * max(opp)],
            'llm_wait_share_of_node_h_mid': round(series * med(ell) / (series * med(llm_el) + n * med(blk_el)), 3)}


def h(n, s, M):
    return t_q(1 - 0.025 / M, n - 1) * s / math.sqrt(n)


def nmin(target, s, M, lo=2):
    n = lo
    while h(n, s, M) > target:
        n += 1
        if n > 2000: return None
    return n


# 対比の SD: 2 系列の対差 s_pair。6 cell 要因配置では記述の主効果が critic 2 水準の平均 (s_pair/√2)、
# critic の主効果が記述 3 水準の平均 (s_pair/√3)。4 cell 案は各対比が単一の対 (s_pair)。
designs = {
    'six-cell-factorial': {'cells': 6, 'M': 3, 'sd_factor': {'D_hide': 1 / math.sqrt(2), 'D_swap': 1 / math.sqrt(2), 'C': 1 / math.sqrt(3)}},
    'four-cell': {'cells': 4, 'M': 3, 'sd_factor': {'D_hide': 1.0, 'D_swap': 1.0, 'C': 1.0}},
}
s_pair_opts = {'s_plan (P3 の登録値、random-sweep)': s_plan, 'sqrt2*s_llm (LLM cell のみ、自由度 2)': math.sqrt(2) * s_llm}

out = {'source': str(SRC), 'unit': unit, 'delta': DELTA, 'ln105': H2, 'designs': {}}
for name, ds in designs.items():
    res = {'cost_by_n': {n: cost(ds['cells'], n) for n in (2, 3, 4, 5, 6, 8, 10)}, 'precision': {}}
    for sname, sp in s_pair_opts.items():
        pr = {}
        for c, f in ds['sd_factor'].items():
            s_eff = sp * f
            pr[c] = {'s_eff': round(s_eff, 5),
                     'h': {n: round(h(n, s_eff, ds['M']), 4) for n in (2, 3, 4, 5, 6, 8, 10)},
                     'n1_(h<=delta/2)': nmin(DELTA / 2, s_eff, ds['M']),
                     'n2_(h<=ln1.05)': nmin(H2, s_eff, ds['M'])}
        res['precision'][sname] = pr
    out['designs'][name] = res

print(json.dumps(out, ensure_ascii=False, indent=1))
```

## estimate_p5.json (出力の逐語)

```json
{
 "source": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-v2-followup/section8.json",
 "unit": {
  "llm_series_elapse_s": {
   "median": 14095,
   "min": 12198,
   "max": 18376,
   "values": [
    18376,
    12198,
    14095
   ]
  },
  "block_elapse_s": {
   "median": 2177,
   "min": 2151,
   "max": 2359
  },
  "llm_wait_s": {
   "median": 9594.934874604456,
   "min": 7703.191797491396,
   "max": 13904.400821075891
  },
  "opportunities": {
   "min": 11,
   "max": 14,
   "values": [
    11,
    14,
    11
   ]
  },
  "llm_nonwait_s": {
   "values": [
    4471.599178924109,
    4494.808202508604,
    4500.065125395544
   ]
  },
  "s_llm": 0.00707879816692679,
  "s_plan": 0.03894115049688376
 },
 "delta": 0.02955880224154443,
 "ln105": 0.04879016416943205,
 "designs": {
  "six-cell-factorial": {
   "cost_by_n": {
    "2": {
     "series": 12,
     "evals_B": 120,
     "node_h": [
      41.9,
      48.2,
      62.6
     ],
     "llm_serial_h": [
      25.7,
      32.0,
      46.3
     ],
     "opportunities": [
      132,
      168
     ],
     "llm_wait_share_of_node_h_mid": 0.664
    },
    "3": {
     "series": 18,
     "evals_B": 180,
     "node_h": [
      62.8,
      72.3,
      93.8
     ],
     "llm_serial_h": [
      38.5,
      48.0,
      69.5
     ],
     "opportunities": [
      198,
      252
     ],
     "llm_wait_share_of_node_h_mid": 0.664
    },
    "4": {
     "series": 24,
     "evals_B": 240,
     "node_h": [
      83.7,
      96.4,
      125.1
     ],
     "llm_serial_h": [
      51.4,
      64.0,
      92.7
     ],
     "opportunities": [
      264,
      336
     ],
     "llm_wait_share_of_node_h_mid": 0.664
    },
    "5": {
     "series": 30,
     "evals_B": 300,
     "node_h": [
      104.6,
      120.5,
      156.4
     ],
     "llm_serial_h": [
      64.2,
      80.0,
      115.9
     ],
     "opportunities": [
      330,
      420
     ],
     "llm_wait_share_of_node_h_mid": 0.664
    },
    "6": {
     "series": 36,
     "evals_B": 360,
     "node_h": [
      125.6,
      144.6,
      187.7
     ],
     "llm_serial_h": [
      77.0,
      95.9,
      139.0
     ],
     "opportunities": [
      396,
      504
     ],
     "llm_wait_share_of_node_h_mid": 0.664
    },
    "8": {
     "series": 48,
     "evals_B": 480,
     "node_h": [
      167.4,
      192.8,
      250.3
     ],
     "llm_serial_h": [
      102.7,
      127.9,
      185.4
     ],
     "opportunities": [
      528,
      672
     ],
     "llm_wait_share_of_node_h_mid": 0.664
    },
    "10": {
     "series": 60,
     "evals_B": 600,
     "node_h": [
      209.3,
      241.0,
      312.8
     ],
     "llm_serial_h": [
      128.4,
      159.9,
      231.7
     ],
     "opportunities": [
      660,
      840
     ],
     "llm_wait_share_of_node_h_mid": 0.664
    }
   },
   "precision": {
    "s_plan (P3 の登録値、random-sweep)": {
     "D_hide": {
      "s_eff": 0.02754,
      "h": {
       "2": 0.7436,
       "3": 0.1216,
       "4": 0.0669,
       "5": 0.0488,
       "6": 0.0397,
       "8": 0.0304,
       "10": 0.0255
      },
      "n1_(h<=delta/2)": 24,
      "n2_(h<=ln1.05)": 5
     },
     "D_swap": {
      "s_eff": 0.02754,
      "h": {
       "2": 0.7436,
       "3": 0.1216,
       "4": 0.0669,
       "5": 0.0488,
       "6": 0.0397,
       "8": 0.0304,
       "10": 0.0255
      },
      "n1_(h<=delta/2)": 24,
      "n2_(h<=ln1.05)": 5
     },
     "C": {
      "s_eff": 0.02248,
      "h": {
       "2": 0.6071,
       "3": 0.0993,
       "4": 0.0546,
       "5": 0.0398,
       "6": 0.0324,
       "8": 0.0249,
       "10": 0.0209
      },
      "n1_(h<=delta/2)": 17,
      "n2_(h<=ln1.05)": 5
     }
    },
    "sqrt2*s_llm (LLM cell のみ、自由度 2)": {
     "D_hide": {
      "s_eff": 0.00708,
      "h": {
       "2": 0.1912,
       "3": 0.0313,
       "4": 0.0172,
       "5": 0.0125,
       "6": 0.0102,
       "8": 0.0078,
       "10": 0.0066
      },
      "n1_(h<=delta/2)": 5,
      "n2_(h<=ln1.05)": 3
     },
     "D_swap": {
      "s_eff": 0.00708,
      "h": {
       "2": 0.1912,
       "3": 0.0313,
       "4": 0.0172,
       "5": 0.0125,
       "6": 0.0102,
       "8": 0.0078,
       "10": 0.0066
      },
      "n1_(h<=delta/2)": 5,
      "n2_(h<=ln1.05)": 3
     },
     "C": {
      "s_eff": 0.00578,
      "h": {
       "2": 0.1561,
       "3": 0.0255,
       "4": 0.014,
       "5": 0.0102,
       "6": 0.0083,
       "8": 0.0064,
       "10": 0.0054
      },
      "n1_(h<=delta/2)": 4,
      "n2_(h<=ln1.05)": 3
     }
    }
   }
  },
  "four-cell": {
   "cost_by_n": {
    "2": {
     "series": 8,
     "evals_B": 80,
     "node_h": [
      28.3,
      32.5,
      42.1
     ],
     "llm_serial_h": [
      17.1,
      21.3,
      30.9
     ],
     "opportunities": [
      88,
      112
     ],
     "llm_wait_share_of_node_h_mid": 0.655
    },
    "3": {
     "series": 12,
     "evals_B": 120,
     "node_h": [
      42.5,
      48.8,
      63.2
     ],
     "llm_serial_h": [
      25.7,
      32.0,
      46.3
     ],
     "opportunities": [
      132,
      168
     ],
     "llm_wait_share_of_node_h_mid": 0.655
    },
    "4": {
     "series": 16,
     "evals_B": 160,
     "node_h": [
      56.6,
      65.1,
      84.3
     ],
     "llm_serial_h": [
      34.2,
      42.6,
      61.8
     ],
     "opportunities": [
      176,
      224
     ],
     "llm_wait_share_of_node_h_mid": 0.655
    },
    "5": {
     "series": 20,
     "evals_B": 200,
     "node_h": [
      70.8,
      81.3,
      105.4
     ],
     "llm_serial_h": [
      42.8,
      53.3,
      77.2
     ],
     "opportunities": [
      220,
      280
     ],
     "llm_wait_share_of_node_h_mid": 0.655
    },
    "6": {
     "series": 24,
     "evals_B": 240,
     "node_h": [
      84.9,
      97.6,
      126.4
     ],
     "llm_serial_h": [
      51.4,
      64.0,
      92.7
     ],
     "opportunities": [
      264,
      336
     ],
     "llm_wait_share_of_node_h_mid": 0.655
    },
    "8": {
     "series": 32,
     "evals_B": 320,
     "node_h": [
      113.2,
      130.1,
      168.6
     ],
     "llm_serial_h": [
      68.5,
      85.3,
      123.6
     ],
     "opportunities": [
      352,
      448
     ],
     "llm_wait_share_of_node_h_mid": 0.655
    },
    "10": {
     "series": 40,
     "evals_B": 400,
     "node_h": [
      141.5,
      162.7,
      210.7
     ],
     "llm_serial_h": [
      85.6,
      106.6,
      154.5
     ],
     "opportunities": [
      440,
      560
     ],
     "llm_wait_share_of_node_h_mid": 0.655
    }
   },
   "precision": {
    "s_plan (P3 の登録値、random-sweep)": {
     "D_hide": {
      "s_eff": 0.03894,
      "h": {
       "2": 1.0515,
       "3": 0.172,
       "4": 0.0946,
       "5": 0.069,
       "6": 0.0562,
       "8": 0.0431,
       "10": 0.0361
      },
      "n1_(h<=delta/2)": 44,
      "n2_(h<=ln1.05)": 7
     },
     "D_swap": {
      "s_eff": 0.03894,
      "h": {
       "2": 1.0515,
       "3": 0.172,
       "4": 0.0946,
       "5": 0.069,
       "6": 0.0562,
       "8": 0.0431,
       "10": 0.0361
      },
      "n1_(h<=delta/2)": 44,
      "n2_(h<=ln1.05)": 7
     },
     "C": {
      "s_eff": 0.03894,
      "h": {
       "2": 1.0515,
       "3": 0.172,
       "4": 0.0946,
       "5": 0.069,
       "6": 0.0562,
       "8": 0.0431,
       "10": 0.0361
      },
      "n1_(h<=delta/2)": 44,
      "n2_(h<=ln1.05)": 7
     }
    },
    "sqrt2*s_llm (LLM cell のみ、自由度 2)": {
     "D_hide": {
      "s_eff": 0.01001,
      "h": {
       "2": 0.2703,
       "3": 0.0442,
       "4": 0.0243,
       "5": 0.0177,
       "6": 0.0144,
       "8": 0.0111,
       "10": 0.0093
      },
      "n1_(h<=delta/2)": 6,
      "n2_(h<=ln1.05)": 3
     },
     "D_swap": {
      "s_eff": 0.01001,
      "h": {
       "2": 0.2703,
       "3": 0.0442,
       "4": 0.0243,
       "5": 0.0177,
       "6": 0.0144,
       "8": 0.0111,
       "10": 0.0093
      },
      "n1_(h<=delta/2)": 6,
      "n2_(h<=ln1.05)": 3
     },
     "C": {
      "s_eff": 0.01001,
      "h": {
       "2": 0.2703,
       "3": 0.0442,
       "4": 0.0243,
       "5": 0.0177,
       "6": 0.0144,
       "8": 0.0111,
       "10": 0.0093
      },
      "n1_(h<=delta/2)": 6,
      "n2_(h<=ln1.05)": 3
     }
    }
   }
  }
 }
}
```
