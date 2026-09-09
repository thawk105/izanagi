# [T-2418] 静的 backoff の右側 3 点を探索走として測れるようにし、3 workload へ投入した

**これは探索であって正式系列ではない。** D1813 が定めた 2 段構成の第 1 段であり、値は正式標本へ
混ぜない。本格格子と停止基準 (飽和判定) は、本走の結果を見た後・本格 cohort の投入前に別途
事前登録する。本 wave では凍結していない。

## 0. 依頼と、実際に起きたこと

依頼は「2000 / 4000 / 9999 マイクロ秒の 3 点を、既存 sweep と同じ反復数・walltime 枠で探索走として
実測する。機構は `orchestrator/campaign/backoff_sweep.py` が実在する」だった。

- **引数が名指しした機構の所在は正確でなかった (訂正)。** `backoff_sweep.py` の格子 `SWEEP_US` は
  `[2, 5, 10, 25, 50, 100]` で、生の `BACKOFF_FIXED` を genome へ渡す。1000 以上を表現する符号化
  `encode_static_backoff_us` と拡張格子 `EXTENDED_SWEEP_US` は隣の
  `orchestrator/campaign/backoff_extended_sweep.py` にある。本 wave の機構はこちらである。
  `backoff_sweep.py` からは `_BASE` / `_official_durable_root_policy` /
  `_require_backoff_condition_gate` を輸入するだけで、同 file は変更していない。
- **凍結格子へ点を足す形は採らなかった。** `EXTENDED_SWEEP_US` は事前登録された認証格子で、
  `test_backoff_extended_sweep.py` が上端 `== 1000` を pin し、`backoff_extended_sweep_report.py` が
  長さ・集合・index・隣接関係を意味に使う。ここへ探索値を入れることは D1813 の
  「探索値を正式標本へ混ぜない」にも反する。先例 `t2266-tail` と同型の**第 3 の RUN_KIND**
  `t2418-explore` を足し、campaign identity・report schema・成果物 stem を分離した。

## 1. 符号化の高域枝は、認証済みの正式格子が既に発火させている (実測)

`patches/silo-backoff-fixed.patch` の合成枝は `BACKOFF_FIXED / 1000` で 4 分岐し、
`>= 3000` の枝だけが `BACKOFF_FIXED - 2000` を物理値にする。

- `encode_static_backoff_us`: 2000→4000、4000→6000、9999→11999。`decode` で往復一致 (worktree で実測)。
- **`EXTENDED_SWEEP_US` の上端 1000 は encode で 3000 になるため、この高域枝は認証済みの
  正式格子が既に通っている。** 探索の 3 点は同じ枝を通る。
- 正値の runtime meaning witness は `unestablished` のままだが、これは探索走に固有ではなく
  **既存 sweep 全体と同一の境界**である。探索走にだけ pointwise meaning gate を課すのは
  正式系列より厳しくする scope 外の追加であり、その不在は正しさ検査の弱体化ではない。
  この限定を機械可読 field `meaning_witness_status` として成果物の 3 か所へ載せた。
- 本 wave が実測したのは **Python 側の codec と wire 値の構成まで**である。gate 通過・build・
  runtime の物理量は投入した job の結果で確かめる。

## 2. 先例 t2266-tail の実走記録から取った 3 つの事実

本 wave の裁定は、`output/insights/2026-09-07_t2266-tail-measurement/README.md` の実走記録に基づく。

- **初回投入は 3 job とも 90 秒で条件関門に落ちていた** ([T-2320] 第 2 層欠陥、関門文脈での
  masstree `config.h` 不在)。修正済み (`2177b85aa`)、3 回目が完走。現行 main はこの修正を含む。
- **`_T2266RepCapture.reps_for` に恒真テスト由来の欠陥があった。** 凍結 view が list を tuple に、
  dict を `MappingProxyType` に変えるのに突合が `list == tuple` で書かれ、必ず不一致になった。
  単体テストが view を list / dict で手組みしていたため実経路を一度も通しておらず、8 genome 分の
  計測が終わった直後に 3 job とも report 生成で停止した。**本 wave はこの型の再発を殺す変異
  (m13) を事前登録し、report のテストを凍結 view の実通しで書かせた。**
- **時間予算は実績で言える。** 8 genome の build・verify・bench (5 rep)・commit が 11 分で完走
  (02:36→02:47)。本探索は 5 genome で、かつ backoff を大きくすると 3 秒枠あたりの transaction 数が
  減るため、律速である直列性検査はむしろ短くなる。`SWEEP_CAP_S=11700` に対して余裕は大きい。

## 3. 正しさ防壁を先例と同じ強さに揃えた

`_require_distinct_static_binary_hashes` は、静的でない `BuildResult` を無条件に読み飛ばし、
確認できた amount が 2 未満なら成功する。先例 `t2266-tail` はこの穴を
`_require_distinct_t2266_binary_hashes` (8 genome の完全性を要求) で塞いでいた。
**探索走をその防壁なしで走らせることは先例に対する弱体化であり、規律 2 に反する。**

新設した `_require_distinct_t2418_binary_hashes` は、ちょうど 5 genome、全 trace-disabled
`BuildResult` の実在、genome 束縛、完全 sha256、5 つの相異を fail-closed で要求する。
`_prebuild_backoff_binaries` へ `require_all_t2418_binary_hashes` を足して呼ぶ。
**既存 `require_all_binary_hashes` の式と t2266 の呼び方は変えていない。**

## 4. 「同じ反復数」を共有定数に追随させない

`p2_2.REPS` から期待値を作るテストでは、共有定数が 4 に変わったときに生産側・capture・loader・
テストがすべて追随し、D1813 の literal 5 に反したまま緑になる。
`p2_2.REPS == 5`、`p2_2.EXTIME == 3`、捕捉した `PerfConfig.reps == 5` / `extime == 3`、
各 report point の rep 数 5 を、**テスト側に直接書いた数字**で pin した。変異 m07 が発火する。

## 5. 探索の開示

`search_config` / JSON report top level / `.dat` provenance の 3 か所へ同値で載せる。

- `run_kind` = `t2418-explore`、`claim_scope` = `exploratory_backoff_tail_only_not_formal_series`
- `exploratory` = true、`formal_series` = false、`exploration_values_us` = [2000, 4000, 9999]
- `formal_grid_status` = `not_selected_in_this_wave`
- `formal_stopping_criterion_status` = `not_defined_in_this_wave`
- `meaning_witness_status` = `unestablished_for_positive_backoff_fixed_as_in_existing_sweep`
- `declared_use_class` = `official` / `reps` / `extime_s` / `records` / `threads`

`declared_use_class` を載せたのは、**D1813 の「探索」と runbook の
`IZANAGI_EXPLORATION_OUTPUT_ROOT` が指す「exploration campaign」が別語だから**である。前者は
標本への帰属、後者は campaign layout の use class を指す。探索走を exploration root へ移すと
durability policy と declared use class が変わり、「既存 sweep と同じ枠」から外れる。移していない。

## 6. 敵対レビューが見つけた 2 件と、その裏取り

- **変異 m12 が生存していた。** report が返す `.dat` / `.json` の basename をどのテストも独立
  literal と照合しておらず、成果物 stem を t2266 のものに書き換えても赤にならなかった。
  名前が入れ替わると計測は完走するのに CLI と PBS finalizer が成果物を見つけられず投入が
  失敗扱いになる。fix で basename の照合を 2 件足し、**変異本走で KILLED を確認した**。
- **裁定した「限定」が成果物側に無かった。** §1 の meaning witness の限定を文書側にしか
  持っておらず、成果物単体を受け取った人が誤読できた。3 か所へ同値で載せ、
  1 か所を落とす変異 (m15) が赤になることを確認した。

親が不採用にした nit 3 件 (m13 の登録位置・positive assert の冗長・共有 helper の例外文言) は
焦点再レビューで「親裁定どおり未変更」を確認した。**m13 は親が変異 spec 側で狙いを付け直した** —
当初の登録は比較の片側だけを戻すもので、凍結入力上は両側とも tuple になり等価変異だった。
もう片方 (`tuple(item["throughput_tps"])`) を戻す形へ差し替えて KILLED になった。

## 7. 変異 matrix (事前登録 m01〜m15)

`tools/mutation_harness.py --runner-mode dispatch --detached` を直接使用。
probe (全件 SURVIVED 期待で観測 node 収集) → 本走 (期待 node 完全一致) の 2 段。

- baseline PASSED (47 passed)、**14 KILLED / 1 SURVIVED / MISMATCH 0 / TIMEOUT 0**、期待 node 完全一致
- `repo_head` = `db67738af9ff443de3f8dde62c8141fd88a43abe`
- probe spec sha256 = `21990a38e4f7de5323c8147c74b8734d94ae97ae3bd72b15563cc966e3e26cc3`
- 本走 spec sha256 = `c5536a85626ed4245c01fffd14c4713bb9cb5077ade12727fdb66f5686133e8e`
- runner argv: `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_backoff_extended_sweep.py -q -rf -p no:cacheprovider`
- 台帳は `mutation/` (probe-spec / probe-report / main-spec / main-report)

| ID | 変異 | 観測 (赤 node 数) |
|---|---|---|
| m01 | `T2418_REQUESTED_US` の 1 点を 9998 へ | 2 |
| m02 | 静的点を `encode_static_backoff_us` を通さず生値へ | 3 |
| m03 | `T2418_CLAIM_SCOPE` を t2266 と同値へ | 2 |
| m04 | `formal_stopping_criterion_status` を search_config から落とす | 1 |
| m05 | T2418 分岐で `t2266_config_for` を選ぶ | 1 |
| m06 | `_require_distinct_t2418_binary_hashes` を即 return | 2 |
| m07 | `PerfConfig(reps=p2_2.REPS - 1)` | 1 |
| m08 | PBS `case` から `t2418-explore` を落とす | 1 |
| m09 | PBS finalize の commit 数を 8 へ | 1 |
| m10 | submit script の run kind 転送から T2418 を外す | 1 |
| m11 | 未完走でも report materializer を呼ぶ | 2 |
| m12 | report stem を t2266 の stem へ | 1 |
| m13 | 凍結 view 突合の `tuple()` 正規化を片側外す (再照準後) | 2 |
| m14 | `len(canonical_by_sha256)` → `.keys()` (等価変異・正例) | SURVIVED |
| m15 | `meaning_witness_status` を `.dat` provenance から落とす | 1 |

`DW-M03` に従い m11 の追加 node
(`test_extended_run_path_prepares_and_gates_the_same_patched_tree`) は冗長 gate として記録する
— 完走条件は run kind 共通の 1 か所なので、赤理由自体は 1 つである。
m14 は harness が SURVIVED を報告する能力の正例であり、kill には数えない。

## 8. 受入全走 — 4 回目で緑

- **1 回目: 1 failed / 22086 passed / 68 skipped。** 赤は
  `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
  の 1 件だけで、覆い 19935 / 収集 22155 = **89.979689%** が閾値 90% をわずかに割った。
  **帰属は本 wave である** — 本 wave が足した 8 node を分母から外した反実仮想は
  19935 / 22147 = 90.012191% で緑になる。F902 の同型再発 (ただし新規 test file ではなく
  既存 file への追加で起きた)。
- **2 回目: `stage=owned-path-overlap` で走行前に停止。** 台帳を正本 producer で更新して
  commit した直後、**別 wave が同一の台帳更新 (2081 node) を main へ着地させていた** (`2fd1679dd`)。
  merge guard が正しく発火した。
- **台帳 commit は取り下げた。** main 側の台帳は 22123 node で網羅率は約 99.9% あり、
  本 wave の 8 node が未登録でも閾値を大きく上回る。一方、自分の台帳更新を残したまま
  main を取り込むと 3-way merge で 56 か所衝突する (`git merge-file` で実測)。
  **閾値は下げていない。** 8 node は次に台帳を更新する wave が自動的に拾う。
- **3 回目: `stage=postcheck` で走行前に停止。** main を取り込んだ直後に main が 11 commit
  進み、「取り込みが最新でない」と判定された。混雑帯の競走である。
- **4 回目: `child-green`、22116 passed / 68 skipped、rc=0。** claimed main = `7befabf44`。

## 9. 焦点走 (`DW-O26`)

変更した production を参照する consumer test を参照関係で引いた 11 file。

- fix 前: 変更 test file 単独 47 passed、consumer 集合 1103 passed / 13 skipped
- fix 後: 同じく 47 passed、1103 passed / 13 skipped

## 10. scope 外として実装せず裁定へ返した 4 件

いずれも既存の正式系列と共通の性質であり、探索走に固有の弱体化ではない。

1. 正値の pointwise meaning gate の新設 (既存 sweep 全体と同じ境界。§1)。
2. job 本体への working-tree 拘束。job は自身の script の sha256 しか HEAD に束縛せず、
   driver・patch・`pin.py`・condition gate の working bytes は拘束しない。全 run kind 共通の性質で、
   共有 job 本体への gate 追加になる。**運用で閉じた** — 専用の detached submit-tree を
   wave commit から作り、投入から job 終端まで編集しない。
3. 既存の正式 consumer へ `completion["run_kind"] == "extended"` を必須化する案。
   正式系列の受理集合を変える変更で、本 wave の編集面の外。現状 T2418 成果物が正式 consumer に
   最終的に拒否されることは相談が経路つきで確認した。
4. runbook の exploration-root 語の整理 (§5 の語の衝突)。

## 11. 投入

固定 SHA `c49cdca1d40454ad006a6b583c61703b14dedd56` の detached submit-tree
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2418-static-backoff-explore/submit-tree`、
tracked clean) を cwd にして投入した。job 本体は `PBS_O_WORKDIR` を repo root として使うため、
cwd が submit-tree root であることが必要である。

- 投入 2026-09-09 04:36 JST、`tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2418-explore`
- request 986597 (write-heavy) / 986598 (balanced) / 986599 (read-heavy)、queue `gen_S`
- 出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/`、
  受領証 `b10-backoff-grid-20260908T193601Z-2540578.submit.jsonl`
- 完了判定は 3 本すべての `completion.json` の照合まで行う。submitter の rc=0 は
  qsub 受理しか意味しない (fan-in は submitter に無い)。

## 12. 探索の結果 — 9999 マイクロ秒まで abort 抑制は飽和しない

3 job とも `status=complete` で完走した (2026-09-09 04:36 投入、04:54 までに 3 本とも完了)。
`run_kind` は 3 本とも `t2418-explore`、campaign id は workload ごとに別、
`freeze_trees_sha256` は投入前後で `c405c742…` のまま不変。各点 5 rep、
`correctness_verified=true` / `performance_certified=false`。

静的 3 点 (median throughput [tps] / abort 率):

| workload | 2000 µs | 4000 µs | 9999 µs |
|---|---|---|---|
| write-heavy | 746465 / 0.0293 | 565390 / 0.0198 | 402820 / 0.0114 |
| balanced | 542511 / 0.0404 | 420293 / 0.0268 | 317205 / 0.0145 |
| read-heavy | 1251217 / 0.0170 | 921117 / 0.0119 | 616015 / 0.0074 |

文脈 2 点 (median throughput / abort 率):

| workload | none | adaptive |
|---|---|---|
| write-heavy | 2488679 / 0.7821 | 1363579 / 0.1240 |
| balanced | 3727702 / 0.6869 | 1265715 / 0.2110 |
| read-heavy | 10082696 / 0.1549 | 2328817 / 0.0405 |

**観察 (探索であり、判定ではない):**

- **3 workload すべてで、abort 率は 9999 µs まで単調に下がり続け、飽和の兆候が無い。**
  2000→9999 で write-heavy 0.0293→0.0114、balanced 0.0404→0.0145、read-heavy 0.0170→0.0074。
  倍率はいずれも 2.3〜2.8 倍で、workload 間で近い。
- **throughput も同じ区間で単調に下がる** (2000→9999 でおおむね 0.49〜0.58 倍)。
  つまりこの領域では、abort 抑制の追加分を throughput の低下がそのまま買っている。
- 変動係数は全点で 0.7% 未満 (最大 0.0065)。
- **D1813 の第 1 段が問うた「飽和する領域」は、9999 µs までの範囲には現れなかった。**
  第 2 段の本格格子と停止基準は、この事実を踏まえて別途事前登録する。
  本 wave は格子も停止基準も凍結していない。

出力は `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/` の 3 job dir。
report は各 campaign の `reports/t2418-backoff-static-explore-<workload>.{dat,json}`。

## 13. エージェント工数

Codex 子 9 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1・ledger author 1)。
model call は順に 16 / 34・16 / 33 / 12・8 / 16 / 16 / 14 の計 165、
wall-clock 合計は約 5773 秒。すべて `gpt-5.6-sol` @ `reasoning=xhigh`。
