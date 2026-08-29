# 親の追加実測 — 反実仮想、regime 交代、床の分解

`measurements.md` の続き。すべて既存 artifact の事後解析と、login node 上の read-only 計測だけ。
新しい full 受入は 1 本も投入していない。

## A. 反実仮想シミュレーション — 「その処理を無料にしたら壁は動くか」

critical shard の実測 node 所要を 48 worker へ LPT (longest-processing-time first) で詰め直し、
xdist_group は 1 単位として不可分に扱った。特定の単位の所要を 0 にして詰め直し、
makespan がどれだけ縮むかを見る。script は `analyze5.py` / `analyze6.py` / `analyze7.py`、
生出力は同名 `.txt`。

観測された makespan の観測下界として使う。LPT は最適 makespan の 4/3 近似の一種であり、
実 scheduler の makespan はこれ以上になる。したがって
**「LPT でも縮まない」は「実 scheduler でも縮まない」を含意する向きで使う。**

### A-1. 2026-08-29 01:52 を境に、wall を決めるものが入れ替わった

K=3 の直近 30 走 (`analyze7.txt` に全行)。

| regime | n | shard0 wall 中央 | LPT makespan 中央 | 床 (wall − LPT) 中央 | 最重単位を無料にした短縮 中央 |
|---|---:|---:|---:|---:|---:|
| s8c group 稼働 (〜08-29 01:43) | 26 | 374.4 | 198.0 | 175.0 | **+57.9 秒** |
| s8c group hold (08-29 01:52〜) | 4 | 210.6 | 118.3 | 94.5 | **+3.2 秒** |

- 旧 regime: `s8c-preregistration-candidate` loadgroup (5 node が 1 worker へ直列、
  実測 118〜267 秒) が単独で makespan を決めていた。これを無料にすると中央 58 秒縮む。
  **この時期なら「wall を決める単体処理」は存在した。**
- 現 regime: その 5 node は `orchestrator/tests/growth_test_holds.py` の
  `IZANAGI_GROWTH_HOLD_V1` で hold (skip) され、group の所要は 0 になった。
  **単一の単位が wall を決めなくなった。**

### A-2. 現 regime では最重単位を消しても壁はほとんど動かない

直近走 `9c62f3e9` (08-29 02:36、bnode003、shard-0 wall 204.769 秒、6,299 item、
総 occupancy 4,859 秒、48 worker):

| 消す単位 | 消えた仕事量 | LPT makespan | 短縮 |
|---|---:|---:|---:|
| なし | 0 | 126.6 | — |
| 最重 1 | 126.6 秒 | 107.3 | +19.3 |
| 最重 2 | 233.9 秒 | 104.7 | +21.9 |
| 最重 3 | 338.6 秒 | 100.7 | +25.9 |
| 最重 5 | 538.8 秒 | 99.2 | +27.4 |
| 最重 8 | 835.8 秒 | 98.6 | +28.0 |
| 最重 12 | 1,201.6 秒 | 76.2 | +50.4 |
| T-080 oracle-driver 系 21 単位すべて | 1,072 秒 | 126.6 | +0.0 |

**835 秒分の仕事を消しても makespan は 28 秒しか縮まない。**
同じ長さの単位が次々に代わりを務めるためである。
直近 4 走で最重単位を無料にしたときの短縮は +19.3 / +2.7 / +2.3 / +3.8 秒、中央 3.2 秒。

### A-3. 山を作っているのは 2 つの test file

現 regime の 100〜127 秒帯:

- `orchestrator/tests/test_s8b_oracle_driver.py` の T-080 系 **10 本** (中央 103.8〜114.3 秒)。
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module` **1 本** (83〜127 秒)。

その下に `orchestrator/tests/test_s8b_floor_campaign.py` の official / pilot 系が
**約 10 本、77〜81 秒**で続く。最重 12 単位を消すと makespan が 76.2 秒まで落ちるのはこの層に当たるためである。

T-080 の 10 本は走間で完全に連動する (最重 node との相関 r = +0.999、
比の中央値 0.910〜1.000、範囲 [0.901, 0.964])。同種の費用に支配されている。
ただし `test_s8b_floor_campaign` 系も r = 0.96〜0.98 で連動しており、
この連動だけでは「同一処理の共有」の証拠にならない (計算ノード混雑で全 node が一斉に膨らむため)。
一方 `test_repository_candidate_uses_real_s8c_budget_module` は r = +0.053 で連動しない。

## B. 床 (テストを 1 本も走らせていない時間) の同定

### B-1. 床は 3 shard 共通で約 55 秒、混雑にほぼ影響されない

K=3 の直近 60 走で `wall − max_occ` (`analyze9.txt`):

| shard | n | 最小 | p25 | 中央 | p75 |
|---|---:|---:|---:|---:|---:|
| shard-0 | 60 | 65.6 | 76.0 | 86.2 | 162.3 |
| shard-1 | 60 | 52.7 | 54.6 | **55.1** | 56.2 |
| shard-2 | 60 | 53.1 | 54.4 | **54.9** | 55.6 |

hold 後の 4 走に限ると shard-0 が 77.2 / 77.7 / 78.9 / 75.4、
shard-1 が 55.5 / 55.1 / 55.5 / 54.6、shard-2 が 55.4 / 56.1 / 55.4 / 54.9。

shard-1 と shard-2 は重い山を持たないので、その 55 秒は **scheduling slack をほぼ含まない**。
shard-0 の 75〜79 秒は「55 秒の床 + 約 21〜24 秒の scheduling slack」と分解できる。
60 走・9 台の計算ノードにまたがって 54.4〜56.2 秒に収まる。混雑で node 所要が 1.7 倍になる走でも
床は動かない。

### B-2. 床の内訳 — 全件 collection 1 回が 11〜43 秒

login node `pegasus02` (96 core、load 6.55) で、この worktree に対し
`python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider` を 3 回連続で実測した
(`logs/collect.time`、テストは 1 本も実行していない):

| 走 | wall | maxrss |
|---|---:|---:|
| 1 回目 (page cache 冷) | **42.78 秒** | 265,984 KB |
| 2 回目 | 16.16 秒 | 240,188 KB |
| 3 回目 | 11.37 秒 | 240,052 KB |

比較のため `python3 -c "import pytest"` 単独は 0.16 秒。
つまり 11〜43 秒は **`orchestrator/tests` 配下の全 test module の import と 18,954 item の収集**である。

受入の 1 shard は 48 worker を立てる。xdist の各 worker は独立の process で、
それぞれがこの import と収集を最初から行う。

**artifact による直接の裏取り**: `shard-0/report.json` の `worker_collection_digests` は
長さ **48 の list** で、48 要素すべてが同一の digest
`7564777aec72e47ab068236eb1089f211db3bbc394152bb41e8f6b8d160ce51a` である。
すなわち 48 worker が**それぞれ独立に全 18,954 item を収集し、同じ universe に到達した**。
その後 shard-0 分の 6,299 item へ deselect する。K=3 なので 1 走あたり収集は **144 回**行われる。
1 process あたり 240 MB を使う。

**約 55 秒の床は、この「全件 collection を 48 回」でほぼ説明できる。**

### B-2b. 収集 1 回の内訳 (cProfile、login node、read-only probe)

同じ collection を cProfile 下で 1 回走らせた (`logs/collect.prof`、解析は `analyze_prof.py`)。
cProfile は所要を膨らませるので絶対値でなく**比率**として読む。全体 18.85 秒。

| 項目 | 値 | 全体比 |
|---|---:|---:|
| `_pytest/main.py:789 perform_collect` (cumulative) | 17.93 秒 | 95% |
| module import `importlib._bootstrap:1022 _find_and_load` (cumulative) | 10.84 秒 | 58% |
| `builtins.compile` (self、471 呼) | 2.36 秒 | 13% |
| `posix.stat` (self、41,602 呼) | 1.52 秒 | 8% |
| `io.open` + `io.open_code` (self) | 1.40 秒 | 7% |
| `marshal.load` (self、409 呼) | 0.55 秒 | 3% |
| `_pytest/python.py:1606 Function.__init__` (cumulative、31,623 呼) | 3.12 秒 | 17% |
| `_pytest/fixtures.py:1853 getfixtureclosure` (cumulative、12,728 呼) | 1.37 秒 | 7% |
| `orchestrator/tests/test_p3_exploration_namespace.py:63` の setcomp (cumulative、180 呼) | 2.70 秒 | 14% |

最後の 1 項だけが repo 側のコードである。`_call_names` が `ast.walk` を回しており
(`ast.walk` は 1,153,351 呼で cumulative 2.66 秒)、これが collection 時に 180 回走っている。
残りは pytest と Python の import・item 構築・fixture closure であり、
**件数と module 数に比例して増える構造的な費用**である。

`builtins.compile` が 471 回発火しているのは `__pycache__` が無い状態で
source から bytecode を作っているためで、48 worker が同時に立つ初回はこれを重複して払う。
先の 3 連続実測で 1 回目 42.78 秒・2 回目 16.16 秒・3 回目 11.37 秒と落ちたのはこの効果を含む。

### B-3. 床は 11 日で 26 秒から 55 秒へ、収集 1 回は 4.08 秒から 11.37 秒へ増えた

先行知見 `output/insights/2026-08-18_acceptance-wall-cost-structure/README.md` は
同じ量を測っている (逐語):

> **wall = `real-repo` 直列鎖 + 約 26 秒の固定費**が 14 走すべてで成立する。
> 固定費は worker 48 本の起動と、全 worker が 12951 件を各自 collection する費用
> (単一 process の collection 実測 4.08 秒) と最終集約である。

| 日付 | universe 件数 | 単一 process の collection | 固定床 |
|---|---:|---:|---:|
| 2026-08-18 | 12,951 | 4.08 秒 | 約 26 秒 |
| 2026-08-29 | **18,895** | **11.37 秒 (warm) / 42.78 秒 (cold)** | **約 55 秒** |

件数は 1.46 倍だが、収集は 2.79 倍、床は 2.1 倍になっている。
**床は件数に線形ではなく、それより速く伸びている。**
床は受入 wall の中で最も速く伸びている項である。

### B-4. 2026-08-18 に wall を決めていた鎖は、いま 0 秒になっている

直近 4 走の shard-0 の loadgroup 鎖 (`analyze10.txt`):

| loadgroup | items | 2026-08-18 の鎖長 | 2026-08-29 の鎖長 |
|---|---:|---:|---:|
| `real-repo` | 4 | 77.53〜94.86 秒 | **0.0 秒** |
| `s8c-preregistration-candidate` | 5 | 71.65〜77.54 秒 | **0.0 秒** |
| `campaign-repository-scan` | 6 | — | **0.0 秒** |
| `s8c-predicate-snapshot` | 3 | — | 36.0〜38.2 秒 |

0 秒の 15 node は skip されている。直近走の skip は 3 shard 合計 67 件で、
うち 51 件が `growth_test_holds` の hold である (`analyze11.txt`):
`output_artifacts` 23、`tracked_files` 18、`commits` 7、`docs_bytes` 3。
残る 16 件は環境依存の条件付き未実走 (Codex/bwrap、masstree root、template patch、gnuplot 等)。

**受入は既に、repository の成長に比例する検査を hold して wall を抑えている。**
同定結論は「これらの hold が効いている状態」に対する主張である。

## C. 現時点での親の結論 (provisional、段4 で裁定する)

現行 tip (hold 有効) では、受入 wall を決めている単体処理は**1 つではなく 2 つ**である。

1. **48 worker それぞれが行う全件 collection**。3 shard すべてが約 55 秒払う。
   shard-0 の wall 205 秒の 27%。混雑に依らず一定。
2. **`test_s8b_oracle_driver.py` の T-080 e2e 10 本が 1 本あたり払う約 100 秒**。
   1 本消しても壁は 3 秒しか動かない。10 本同時に効く短縮でなければ動かない。

hold が解除されると 1 位は `s8c-preregistration-candidate` loadgroup に戻る。

D1260 の「+0.37% で変化なし」はこの構造の帰結として説明できる。
6 本を 1 worker へ寄せて memo を共有させても、100 秒級の山が他に 5 本以上残るため
makespan は動かなかった。
