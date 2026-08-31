# T-1933 受入 wall を決めている単体処理は存在しない — 10〜11 unit の frontier である (2026-08-29)

- wave: `dev-wave-t1933-wall-unit` / branch `worktree-dev-wave-t1933-wall-unit`
- base main: `d03855e92`
- authority: none
- default_effect: no-state-change
- 実装面の差分: なし (docs-only)

本書は可変状態の正本ではない。タスク状態は worklog、設計判断は decisions を正本とする。

## 依頼と結論

依頼は「fixed-tip full artifact の critical worker で wall を実際に決める単体処理を先に同定し、
その処理自体の安全な短縮だけを検討する。同定結果が具体的な処理を 1 つ指し示した場合にだけ
その処理に閉じて実装する」であった。

**結論は負である。現行 tip・hold 有効の状態で、受入 wall を決めている単体処理は存在しない。**
条件が成立しないので短縮は実装していない。

## 素材と方法 — 新しい受入走行は 1 本も投入していない

`/work/1/SFC/tanab/.izanagi-acceptance-shards/<group>/shard-N/` に残る、
他 wave が過去に流した受入の生 artifact を事後解析した。

- `report.json` (`izanagi-acceptance-shard-report/v1`): `worker_occupancy` (worker → items と duration_s)、
  `group_to_workers`、`worker_collection_digests`、`observed_universe`、`terminal_counts`。
- `junit.xml`: `testsuite@time` (pytest session の wall)、`@timestamp`、`@hostname`、
  `testcase@time` (node 所要)。loadgroup 所属 node は `testcase@name` 末尾に `@<group>` が付く。
- `dispatch/shard-N/request.json`: `runner_binding.tested_main` と `repo_root`。

548 group を走査し、全 shard の report が揃い `terminal_counts.passed` の合計が 15,000 以上のものを
full 走として **484 走**を採った。K=2 が 293 走、K=3 が 191 走。scheduler は全走 `loadgroup`、
worker は全走 48。

解析 script は repo 外の job directory `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-wall-unit/`
(`corpus_scan.py`、`analyze2.py`〜`analyze15.py`、`analyze_prof.py`) に置いた。
probe を repo へ入れないため、生出力だけを `measurements/` に保存している。
各 script が何を計算したかは本書と `verbatim/parent-findings.md` に記述してある。

これに加えて login node `pegasus02` で read-only の計測を 2 種だけ行った
(`measurements/collect-timing.txt`、`measurements/analyze_prof.txt`)。
テストは 1 本も実行していない。

## 確定した結論 — scheduling model に依存しない

`makespan >= 最長 unit の所要` は任意の schedule について成立する定理である。ここでの unit は
「1 つの xdist_group、または group を持たない 1 node」を指す。group は不可分に 1 worker へ載る。

hold 有効の 4 走 (critical shard はすべて shard-0)。tested_main は `analyze15.txt` から引いた。

| 走 | tested_main | shard0 wall | max_occ | 97 秒以上の unit | 77 秒以上の unit | 上位 5 unit |
|---|---|---:|---:|---:|---:|---|
| `9c62f3e9` (08-29 02:36) | `93fcb4663` | 204.769 | 127.6 | 11 | 11 | 126.6 107.3 104.7 100.7 99.5 |
| `6fbbc43d` (08-29 02:24) | `93fcb4663` | 200.246 | 122.6 | 10 | 12 | 111.8 109.1 105.5 104.9 103.8 |
| `96dd3976` (08-29 02:05) | `c9f868ba` | 224.276 | 145.3 | 10 | 20 | 120.5 118.3 113.5 113.0 112.7 |
| `ef85f4f2` (08-29 01:52) | `c9f868ba` | 216.451 | 141.1 | 10 | 22 | 116.0 112.2 108.9 107.4 107.2 |

4 走は**同一 tip の 2 組**であって、同一 tip の 4 走ではない。
D357 の 3 走要件は満たしていない。4 走とも growth hold の解除環境変数は未設定である。

1. **最長 unit を無料にしても、makespan は次の unit の所要を下回れない。**
   その差は 2.7 / 19.3 秒であり、上位が入れ替わるだけである。
2. **97 秒以上の unit が 10〜11 本ある。** makespan を 97 秒未満にするには
   10〜11 本を同時に短くする必要がある。77 秒まで含めると 11〜22 本になる。
3. したがって**単一処理は wall を決めていない**。これは定理からの帰結で、
   xdist の scheduler の挙動にも、親が別に行った LPT 詰め直しにも依存しない。

## D1260 の +0.37% はこの構造の帰結である

D1260 は「同じ immutable base を使う T-080 の 6 node を同一 worker へ寄せる配線は、
paired full K=3 中央値が 10% 未満の差なら採用しない」と定め、pre 244.810 秒 / post 245.707 秒 /
差 +0.37% を根拠にした。上の frontier がその理由を説明する。
6 本を 1 worker へ寄せて memo を共有させても、97 秒以上の unit が他に 4〜5 本残るため
makespan は動かない。**局所の cache hit は full wall の critical path の下に隠れる**という
D1260 の記述は、frontier の幅として定量化された。

## wall のうちテスト実行でない部分

`wall − max_occ` は**全 worker が非実行である時間の上界**である。下限ではない。
`tools/acceptance_shards.py:862-872` は phase の `report.duration` を node ごとに加算するだけで、
`orchestrator/tests/conftest.py:2083-2085` の real-repo lock 待ちは `yield` の外側にあり
phase duration に入らない。worker の idle、scheduler、session suffix も同じ差分に入る。

K=3 の直近 60 走 (`measurements/analyze14.txt`):

| shard | n | min | p25 | median | p75 | max |
|---|---:|---:|---:|---:|---:|---:|
| shard-1 | 60 | 52.7 | 54.6 | 55.1 | 56.2 | 78.7 |
| shard-2 | 60 | 53.1 | 54.4 | 54.9 | 55.6 | 67.0 |

hold 後の 4 走では shard-0 が 77.2 / 77.7 / 78.9 / 75.4 秒、
shard-1 が 55.5 / 55.1 / 55.5 / 54.6 秒、shard-2 が 55.4 / 56.1 / 55.4 / 54.9 秒である。
安定しているのは中央域であり、全走ではない。

### この残差は universe 件数に対し 1,000 件あたり 2.45 秒で伸びる

critical でない shard 675 本 (universe 15,063〜18,895 件、K=2 と K=3 の両方) で
`wall − max_occ` を universe 件数へ回帰すると、
**傾き 0.00245 秒/件、切片 10.5 秒、r 0.490** である (`measurements/analyze13.txt`)。

| universe | K | n | 残差の中央値 |
|---:|---:|---:|---:|
| 約 15,000 | 2 | 62 | 46.1 |
| 約 16,000 | 2 | 85 | 48.5 |
| 約 17,000 | 2 | 134 | 52.0 |
| 約 18,000 | 2 | 11 | 53.0 |
| 約 18,000 | 3 | 212 | 52.3 |
| 約 19,000 | 3 | 166 | 54.7 |

この範囲では概ね線形である。**超線形であるとは言えない。**

### 内訳は現 artifact では分解できないが、collection の絶対値は測れた

`report.json` の `worker_collection_digests` は長さ 48 の list で、48 要素すべてが同一の digest
`7564777aec72e47ab068236eb1089f211db3bbc394152bb41e8f6b8d160ce51a` である。
すなわち 48 worker が**それぞれ独立に全 18,895 item を収集し、同じ universe に到達した**。
その後 shard-0 分の 6,299 item へ deselect する。
K=3 の 1 走の collection は worker 144 回 + login collection 1 回 = **145 回**である。

login node `pegasus02` (96 core、load 6.55) でこの worktree に対し
`python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider` を 3 連続で測った
(`measurements/collect-timing.txt`):

| 走 | wall | maxrss |
|---|---:|---:|
| 1 回目 (page cache 冷) | 42.78 秒 | 265,984 KB |
| 2 回目 | 16.16 秒 | 240,188 KB |
| 3 回目 | 11.37 秒 | 240,052 KB |

`python3 -c "import pytest"` 単独は 0.16 秒である。

cProfile 下の 1 回 (18.85 秒、`measurements/analyze_prof.txt`) の内訳。
cProfile は所要を膨らませるので比率として読む。

| 項目 | 値 | 比 |
|---|---:|---:|
| `_pytest/main.py:789 perform_collect` (cumulative) | 17.93 秒 | 95% |
| module import `importlib._bootstrap:1022` (cumulative) | 10.84 秒 | 58% |
| `builtins.compile` (self、471 呼) | 2.36 秒 | 13% |
| `posix.stat` (self、41,602 呼) | 1.52 秒 | 8% |
| `io.open` + `io.open_code` (self) | 1.40 秒 | 7% |
| `_pytest/python.py:1606 Function.__init__` (cumulative、31,623 呼) | 3.12 秒 | 17% |
| `_pytest/fixtures.py:1853 getfixtureclosure` (cumulative、12,728 呼) | 1.37 秒 | 7% |
| `orchestrator/tests/test_p3_exploration_namespace.py:63` の setcomp (cumulative、180 呼) | 2.70 秒 | 14% |

repo 側のコードは最後の 1 項だけで、`_call_names` が `ast.walk` を回している
(`ast.walk` は 1,153,351 呼、cumulative 2.66 秒)。
**これらは collection 単体の内訳であって、55 秒の残差の内訳ではない。**
残差を collection へ帰属させるには worker 側の phase timeline が要る (下記「観測の穴」)。

## 上位 unit の中身は 3 機構である。2 系統ではない

1. `orchestrator/tests/test_s8c_preregistration_invariant.py:362-385` の module fixture。
   fresh index、`read-tree HEAD`、pathspec なしの `git add -A` (同:205)、`write-tree`、
   `commit-tree -p HEAD`。5 node が `s8c-preregistration-candidate` loadgroup で 1 worker に載る。
2. `orchestrator/tests/test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module`。
   function fixture の `git add` は 4 path 限定で、費用は C06 evaluator の到達可能性探索
   (`orchestrator/campaign/s8c_preregistration_evidence.py:1341-1468`) と blob 読み取りにある。
   1 とは別機構である。
3. `orchestrator/tests/test_s8b_oracle_driver.py:1022-1254` の T-080 stub-free e2e。
   `orchestrator/` と Git-visible `output/` の実体コピー、historical source closure の復元、
   ccbench submodule add/checkout、`git add -A`、basis commit、isolated child Python での
   blob 照合、draft/validate/finalize/commit/receipt verify/public gate。

3 は**共有された 1 回の処理ではない**。同:895-903 は「各テストへは独立した実体コピーを渡す」
「コピーは共有しない実体でなければならない」と明記し、同:909-927 は process-local cache を
引いた後も毎回 `shutil.copytree(base_root, root, symlinks=True)` を実行する。
正しくは**同じコード経路を 10 本が独立に実行している**。
したがって短縮は 10 本すべてへ効く形でなければ makespan を動かさない。

## 結論は hold 有効という条件付きである

`orchestrator/tests/conftest.py:1668-1680` の環境変数で growth hold は opt-in 解除できる。
直近走の skip は 3 shard 合計 67 件で、うち 51 件が `growth_test_holds` の hold である
(`measurements/analyze11.txt`): `output_artifacts` 23、`tracked_files` 18、`commits` 7、
`docs_bytes` 3。残る 16 件は環境依存の条件付き未実走である。

hold により、直近走では次の loadgroup 鎖が 0.0 秒になっている (`measurements/analyze10.txt`)。

| loadgroup | items | 2026-08-18 の鎖長 | 2026-08-29 の鎖長 |
|---|---:|---:|---:|
| `real-repo` | 4 | 77.53〜94.86 秒 | 0.0 秒 |
| `s8c-preregistration-candidate` | 5 | 71.65〜77.54 秒 | 0.0 秒 |
| `campaign-repository-scan` | 6 | 記録なし | 0.0 秒 |
| `s8c-predicate-snapshot` | 3 | 記録なし | 36.0〜38.2 秒 |

(2026-08-18 の値は `output/insights/2026-08-18_acceptance-wall-cost-structure/README.md`。)

hold を解除すると `s8c-preregistration-candidate` が単独で makespan を決める regime へ戻る。
2026-08-29 01:52 より前の 26 走では、この group を無料にすると LPT makespan が
中央値 57.9 秒縮んだ (`measurements/analyze7.txt`)。
**受入は既に、repository の成長に比例する検査を hold して wall を抑えている。**

## 同定が止まっている 1 点

`report.json` に **nodeid → worker の対応が無い**。あるのは `group_to_workers` と
`worker_occupancy` だけである。したがって group を持たない node について
「critical worker に何が載っていたか」は現 artifact では確定できない。
`tools/acceptance_shards.py:800` の `_REPORT_WORKERS` は既に nodeid → worker を計算しているが、
report へ出力されていない。

この観測を足すかどうかは本 wave では実装せず、裁定パッケージとしてユーザーへ返す。
最小形は `node_to_worker` の 1 field 追加 (`tools/acceptance_shards.py:999-1022` と
closed field 集合 `同:61-66`) である。段 2 プランが提案した全 phase timeline と
session milestone は、本 wave の負結論を変えないので過剰実装として不採用にした。

## 撤回した親の主張

段 3 の 2 レンズが検出し、親が実測で確認して撤回した。詳細は `verbatim/s4-adjudication.md`。

1. `wall − max_occ` を「テストを走らせていない時間の下限」と書いていた。**上界**である。
2. 「LPT でも縮まないなら実 scheduler でも縮まない」と書いていた。LPT は実 scheduler の
   makespan の下界ではない。定理 `makespan >= 最長 unit` へ置き換えた。
3. shard-1 / shard-2 の床を「60 走が 54.4〜56.2 秒に収まる」と書いていた。IQR を範囲と誤記した。
4. universe を 18,954 件、collection を 144 回と書いていた。正しくは 18,895 件、145 回。
   18,954 は `login-collection.log` の行数である。
5. 最 busy worker の item 数を「2〜5」と書いていた。全 484 走の中央値は 72 で二峰性である。
   2〜5 が成り立つのは K=3 の直近 117 走に限られる (2 が 26、3 が 41、5 が 50、合計 117/117)。
   道具の出力を切り詰めたまま母集合を明示せずに引用していた (F473 の再発)。
6. 床の伸びを 2 点だけで「非線形」としていた。675 観測の回帰で概ね線形と確認し、撤回した。
7. 上位 unit を「2 系統」と書いていた。3 機構である。
8. T-080 を「10 本が共有する 1 本あたり約 100 秒の処理」と書いていた。共有ではない。
9. 「受入 wall は総仕事量律速ではない」と一般化していた。host slowdown の交絡があるので
   「この corpus では最 busy worker の occupancy の方が平均 occupancy より wall をよく説明する」
   に弱めた。主結論はこの相関に依存しない。

## 実行しない方がよいこと

- 現 regime で `s8c-preregistration-candidate` の `git add -A` を短縮すること。
  その group は現在 0.0 秒なので wall は動かない。
- T-080 の一部だけを同一 worker へ寄せる grouping。D1260 が不採用を確定している。
- 段 2 プランが定義した `0.9 <= ΔW/ΔU <= 1.1` の x-for-x 条件を同定の必要条件にすること。
  D357 の逐語は 3 走・中央値・10% 未満は変化なし、しか要求していない。
  full wall を 10% 以上短縮する処理を「単一支配でない」という理由で捨てる gate は過剰である。

## 次に測るなら

同定を positive に閉じるには、同一 tested tip・同一 K・同一 worker 数・同一 collection digest・
**同一 hold opt-in 状態**で 3 走以上を逐次に取り、worker ごとの phase timeline を残す必要がある。
hold opt-in 状態は現在どの同値キーにも入っていない。

## 一次資料

- `verbatim/s1-brief.md` — 段 1 brief。
- `verbatim/parent-measurements.md`、`verbatim/parent-findings.md` — 親の実測 (撤回前の記述を含む)。
- `verbatim/s2-plan.md` — 段 2 プラン。
- `verbatim/s3-correctness.md` — 段 3 正しさ・整合レンズ、18 所見。
- `verbatim/s3-effectiveness.md` — 段 3 実効性レンズ、10 所見。
- `verbatim/s4-adjudication.md` — 段 4 裁定。
- `verbatim/rulings-projected.md` — 子へ逐語射影した既裁定。
- `verbatim/NORMALIZATION.md` — 逐語 5 file に適用した可逆最小正規化の原文 hash と byte 数 (DW-S07)。
- `measurements/` — 解析の生出力。
