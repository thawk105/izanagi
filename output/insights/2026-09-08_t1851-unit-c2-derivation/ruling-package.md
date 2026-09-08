# [T-1851] 単位 C2 — ユーザー裁定へ返す 2 件

本 wave は land しない (D1341)。したがって下の 2 件はどちらも成果物の値を今すぐ変えない。
**返答を待たずに実装は完了させてある。**

---

## 裁定 1 — 診断 counter が厳しくなったとき `FORMULA_ID` を改版するか

### 何が起きたか (実測)

契約 v3.1 の 3 節に従って `exec_failures` を自然文 notes の regex から構造化 field へ移し、
rep 証跡を 6 key から 7 key にした。その結果、**1 つの入力 class だけで診断 counter が変わる**。

対象は「subprocess は rc=0 で終了したが、その後の stdout 解析で例外を捕捉した rep」
(`post_spawn_execution_exception`)。実装子が実 `measure_point()` を通した probe で生成した。

| 量 | 改訂前 | 改訂後 |
|---|---:|---:|
| `exec_failures` | 1 | **1 (変わらない)** |
| qualified throughputs | (100.0, 101.0) | **同一 (変わらない)** |
| `rep_integrity_failures` | 0 | **1 (変わる)** |
| session の有効性 | — | **変わらない** |
| session median | — | **変わらない** |

旧実装は、rc=0 と counter 完備だけでこの rep を complete と数えていた
(throughput が `None` でも complete)。改訂後は `execution_failure is False` を要求するので
integrity failure に数える。**受理集合が狭まる向きの訂正である。**

### なぜ裁定が要るか

`orchestrator/campaign/s8b_floor_stats.py:16-19` は
「算出式はセルの有効性契約・floor 合成・scalar 代替・**診断まで含めて**本モジュールが正本である。
**式を変えるときは FORMULA_ID を改版する**」と書いている。
`rep_integrity_failures` は診断に当たるので、字義どおりなら改版が要る。

しかし改版すると凍結成果物の bytes が変わる。

- `FORMULA_ID = "s8b-floor-stats/v2"` は `s8b_floor_stats.py:51` と
  `s8b_floor_contract.py:44` にあり、`:476` が一致を要求する。
- `s8b_floor_campaign.py:1310` が protocol へ `"formula": FORMULA_ID` を書く。
- その protocol は `output/s8b-freeze/floor_protocol.json` として凍結され、
  `orchestrator/tests/test_frozen_artifacts.py:44-49` の `FROZEN_MANIFEST` が sha256 を pin する。
- 同じ値は `output/s8b-freeze/floor-protocols/` 配下の版にも入っている。

### 判断材料

- **certified 成果物への到達経路は現時点で 0 件である** (契約 v3.1 の 0 節)。
  よって改版してもしなくても、既存の成果物の値・受理集合・参照は 1 つも変わらない。
- 変わるのは診断 counter 1 つだけで、向きは厳しくなる方向のみ。
  有効性・median・floor 合成は不変であることを test で固定した。
- 旧 journal は resume 経路で fail-closed になる。これは D1660
  (「旧世代の受理を前向きに廃止する。受理集合は狭まる方向にしか動かない」) と同じ向きである。

### 択一

- **(a) 改版しない。** 診断 counter の訂正は「式を変える」に当たらないと読む。
  凍結成果物に触れない。差分は characterization test で明示的に固定済みなので、
  黙った drift にはならない。**親の推奨はこれ。**
- **(b) 改版する。** `FORMULA_ID` を `s8b-floor-stats/v3` にし、
  `floor_protocol.json` と `FROZEN_MANIFEST` の pin を再発行する。
  字義には忠実だが、値が 1 つも変わらない成果物のために凍結面を動かすことになる。
- **(c) 判断を後続単位へ持ち越す。** 6 単位が揃って land する直前に、
  その時点の到達経路を見て決める。

**親が実装で担保したこと (どの択でも成り立つ):**
`exec_failures` と qualified throughputs と session median が改訂前後で一致し、
`rep_integrity_failures` が `execution_failure is True` の rep の本数だけ増えることを、
producer の全 outcome class の直積で exact に固定した。

---

## 裁定 2 — 契約 9 節「実値域は C2 が供給する」を満たす単位分割

### 実測

- `launch_floor_attempt()` の production 呼び手は **0 件**。
- launcher module の import 元は repo 全体で **1 件、自分の test file だけ**。
- campaign から `attempt_registry` への参照は **0 件**。
- **実 campaign の値域を記録した成果物は repo に 0 件** (親が `output/` 全体を走査)。
- 配線の見積りは **5 file / 350-550 行** (段 2 plan)。
- 配線は 7-key schema が先に無いと組めない (launcher の terminal evidence が
  `exec_failures` を束縛するため)。依存順が固定されている。

### 択一

- **(a) 単位を割る。** C2 は producer 側 (契約 1〜3) を持ち、
  配線と実値域の実測を新しい単位 C3 へ分ける。6 単位が 7 単位になる。
  D1341 は同じ branch で揃えば満たされるので違反しない。**親の推奨はこれ。**
- **(b) C2 を延長する。** 1 wave では収まらず、7-key の受入と配線の受入が混ざる。
- **(c) 契約 9 節の「供給」を「producer schema の準備」へ弱める erratum を出す。**
  契約は AI が敵対検査で v3 から v3.1 へ訂正した先例があるが、
  **単位分割はユーザー裁定の対象なので親の独断では変えない。**

**本 wave の成果物には「実環境の値域を供給した」と書いていない。**
書いたのは「producer 側が実値を構造化して産出する状態にした。launcher の gate へ通してはいない」である。
