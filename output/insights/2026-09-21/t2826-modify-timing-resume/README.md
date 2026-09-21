# [T-2826] 受入 `pre` の worker 側 modify 複合区間の関数別計時 — 最大の区間は `_canonical_item` 内の `Path.resolve()` pass-1 (事前登録の「主因」条件は満たさず、pass-2 とほぼ等分)、resolve 結果の再利用で worker 側 −44.6 秒・`pre` −26〜27 秒 (2026-09-21、再開 wave)

wave `dev-wave-t2826-resume` (前 wave = entry 1800、`output/insights/2026-09-21/t2826-shard-plugin-modify-timing/`)。依頼の逐語は `verbatim/T-2826-resume-origin.md`。
**計測設計と読み方は前 wave の段 4 裁定 §3 / §4 (結果を見る前に確定) を文言を変えずに採り直したもの**で (`verbatim/s4-ruling.md` §A、原文は前 wave の `verbatim/s4-ruling.md`)、本 README の判定はすべてその R1〜R8 に従う。
repo の実装面 (D95 決定 2) の差分はゼロ。probe は wave 専用 dir に置き、逐語を `verbatim/*.txt` に写した。

## 結論 (最初に読む)

1. **計測は完了した。** 計算ノード 1 job (request `15632.nqsv`、bnode003、2026-09-21 20:55:48〜21:06:32 JST、scheduler の `Elapse` 649 秒) で 11 セルすべて rc 0。比較に使う xdist 10 セルは事前登録の有効セル条件 (原裁定 §3) をすべて満たした (warm は温めだけのセルで、集計器は rc だけで判定する)。全セルで他ユーザーの process 0・残留 pytest 0。R8 の外乱は、集計器が作成時刻の代わりに dir の mtime を使っていた (原裁定と異なる) ため、親が原裁定どおり作成時刻 (stat の birth time) で受入共有 root の全 2,207 session を照合し直し、全セルで候補 0 = 重複なしを確かめた (§3)。
2. **R1 閉包:** 関数計時の 6 セル (S2f / S3f / S3cf × a / b) すべてで「閉じた」。worker ごとの |残差| の中央値は 0.258〜0.281 秒 (閾値 2.000〜2.382 秒)。
3. **R2 帰属:** worker の modify 複合区間 (中央値 46.57〜47.65 秒) のうち、`_canonical_item` 実行中の `Path.resolve()` が pass-1 (records_from_items の中) で 22.86〜23.08 秒、pass-2 (選択の by_identity 構築) で 22.01〜22.80 秒 (いずれも worker 中央値、各 27,049 回)。**事前登録の「主因」条件 (1 つの葉の share が有効な f セル 4 つすべてで ≥ 0.5) は満たさない** — 最大の葉 resolve pass-1 の share は 0.483〜0.493。したがって本 README は「主因」と書かず、**最大の区間 = resolve pass-1** と書く。2 つの resolve 葉の worker 中央値の和を modify の worker 中央値で割った値は 0.962〜0.966 (事後の集計で、事前登録の判定ではなく、worker ごとの合計の中央値でもない)。
4. **R5 主比較 (同計器の S3f − S3cf、half a / b):** ΔW = 44.58 / 44.53 秒、Δmodify = 44.79 / 44.68 秒、**Δpre = 27.32 / 26.15 秒**、ΔM = 12.78 / 15.04 秒。worker 側の短縮量 (ΔW) と `pre` の変化 (Δpre) を別々に測るという依頼の量が出た。R4 の集合照合は両 half とも一致 (観測標本の一致であり、一般的同値の証明ではない)。R3 の観測者効果は両 half とも 3 量が |値| ≤ 0.24 秒で判定閾値内。
5. **R6 構造:** 全有効 S2 / S3 セル (8 セル) で `pre` ≈ max(W_w, M) に適合 (符号付き残差 0.017〜0.354 秒)。S3f / S3u / S2f では W_w ≥ M (worker 側が長い、worker の待ち中央値 0.02 秒)。S3cf では W_w (19.49 秒) < M (36.42 / 37.57 秒) になり、`pre` は M に張り付き (36.77 / 37.89 秒)、worker の待ちが中央値 18.94 / 20.24 秒へ伸びた。**事前登録した S3cf の予測 ((i) 適合、(ii) W_w < M 側の「Δpre < ΔW かつ pre ≈ M かつ worker の待ちが伸びる」) は両 half とも的中した。** 集計器の予測判定 (`pass`) は (ii) の「待ちが伸びる」を合否に含めず別列 (`wait_increased`) に出していたので、親が 3 条件すべてで判定し直した (§4.7)。M の変化 (ΔM) の原因は識別しない (事前登録どおり)。
6. **R7 (記述のみ):** process 群の sys は S3f 2,149.32 / 2,137.26 秒 → S3cf 85.13 / 84.29 秒 (shard plugin なしの S1 は 86.43 / 92.09 秒)。Lustre `md_stats:intent_lock` のセル差は S3f 65,444,676 / 65,445,316 → S3cf 6,127,336 / 6,127,957 (S1 5,740,931 / 5,741,103)。
7. **本 wave が言わないこと:** 反実仮想 (resolve 結果の再利用) は probe の中だけの 1 条件の診断で、縮約方式の設計・採否、恒久実装、一般的同値性、実受入の wall の予測には進まない (原裁定 §1・§6)。T-2617 §4 の判定を覆す提案もしない (§5)。

## 1. 依頼と scope

- 依頼 (起動引数): 前 wave (entry 1800) の段 4 裁定 §3 / §4 を変えずに採り直し、段 5 へ進む再開 wave。標本の時点は新 wave の開始 gate で固定、T-2825 の台帳更新の land を段 1 で確かめて前提 N1 に反映、F818 は他 wave が記録済みなら足さない、本題の計測だけ (`verbatim/T-2826-resume-origin.md`)。
- 本題 (前 wave 起票時の依頼): 受入 `pre` の worker 側 約 45 秒 (shard plugin を載せた段の modify 複合区間) を関数別に計時し、`pre` ≈ max(worker 側, 早期 memo prewarm) の構造を事前登録し、worker 側の短縮量と `pre` の変化を別々に測る。短縮の実装は含めない (D1936 項 35)。
- **標本の時点:** 計測 tip = `36fb14a3d131d516dc57b02ec69f56c711927c2e` (開始 gate の時点の local main)、as-of = 2026-09-21 20:26:33 JST (`verbatim/startup-gate.log` の mtime。gate command の起動は 20:26:20、`verbatim/startup-gate.started.txt`)。job の実行時刻 (20:55:48〜21:06:32) は as-of と別。job 中の wave 木は `36fb14a3d` のまま clean (`verbatim/run-probe.tip.txt`。投入 launcher が job の前後に取った `git status --porcelain` は `verbatim/run-probe.status-before.txt` / `run-probe.status-after.txt` でいずれも 0 byte、job 内の開始時も `raw/job-out/env.txt` で 0 行)。

## 2. brief 前の前提実測 (段 1 brief `verbatim/s1-brief.md` の N1〜N9 から抜粋)

- N1. 対象 3 file (`tools/acceptance_shards.py`・`orchestrator/tests/conftest.py`・`tools/run_tests.py`) は T-2817 の計測 tip `2afb39768` からも前 wave の基点 `d99c556df` からも `36fb14a3d` まで差分 0 行。所要台帳 `orchestrator/tests/acceptance_duration_ledger.json` は T-2825 の refresh 再生成 (`26387b617`、entry 1803 で land 済み) を含み、`d99c556df` → `36fb14a3d` で +15,645 / −13,852 行、`2afb39768` → で +15,645 / −13,419 行。`allocate` は台帳の値を重みに使うので shard-0 の選択集合は T-2817 と同じとは限らない (本 job の shard-0 は 27,049 件中 4,204 件を選択、両 half・S2 / S3 の全 8 セルで同じ digest)。
- N1b. `d99c556df` → `36fb14a3d` で test file 4 本が変わった (追加・削除 0)。本 tip の collection は 27,049 件 (login の pyc 温め 48.36 秒、本 job の全 worker でも 27,049 件)。
- N5. T-2825 は land 済み (entry 1803)。比較測定の区間の重なりは生じない。
- N6. Codex は使える状態だった (本 wave の段 5 author は model call 30 回・767 秒で完了、`codex_exit_code=0`。`verbatim/s5-author-receipt.json` の `actuals.model_calls` / `actuals.wall_clock_s`)。
- N7. F818 には 2026-09-21 の再発追記が既に 2 件あるため、前 wave の漏れは追記しない。
- N8. 書きかけ probe の branch `author-t2826-probe` は cleanup-branches が 20:26:54 に削除した (peer 通知)。commit `31894443e` の 3 blob と前 wave の `partial-author/` の 3 file の `git hash-object` が一致することを本 wave で確かめ、参考資料 (未検査) として author へ渡した。

## 3. 計測の実施

- **probe:** 段 5 の Codex author 子 (gpt-6-astra / medium / workspace-write、job-id `t2826r-s5-author`、子 worktree `author-t2826r-probe`、基点 `36fb14a3d`) が runner / plugin / 集計器の 3 file (計 1,392 行) を書き、起動器が終端 commit `1df428f40` にした (所有 3 file の追加だけ)。子の検査は構文・import・関数単位・合成入力の正例 / 負例で、本物の shard plugin / conftest では未検証 (`verbatim/s5-author-out.md`)。親が wave 専用 dir へ複製し (blob 一致、`verbatim/probe-sha256.txt`)、以下で走らせた。逐語は `verbatim/t2826_*.txt`。
- **login の生死確認 (親、比較に使わない):** 2026-09-21 20:48:55〜20:54:23、`T2826_WORKERS=2`、セル S1-a / S2f-a / S3u-a / S3f-a / S3cf-a、全 rc 0、wave 木 clean。A / B / C の計時点、S3cf の memo (pass-1 miss 369 / hit 26,680、pass-2 hit 27,049)、R4 の digest 一致、集計器の R1〜R8 出力を実データで確かめた (`raw/login-out/`)。login の値は負荷で揺れた (load 1 分値 4.57 → 36.14) ので数値は比較に使わない。
- **計算ノード job:** `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:40:00 --queue-wait-timeout 5400 --overall-grace 5400 -- bash <job dir>/probe/t2826_modify_timing_probe.sh` (`verbatim/run-probe.sh.txt`)。セル順は原裁定 §3 のとおり `warm S1-a S2f-a S3u-a S3f-a S3cf-a S3cf-b S3f-b S3u-b S2f-b S1-b`、`-n 48`。環境は `raw/job-out/env.txt` (bnode003、kernel 5.15.0-173、48 core、Lustre stats 読取り可)。
- **有効性:** 比較に使う xdist 10 セルは原裁定 §3 の有効セル条件 (rc 0、48 worker の payload 回収、必須計時点、collection 不一致なし、probe / node の error 0、report あり、S3cf は R4 成功) をすべて満たした (`job-out-aggregate.md` §有効性、無効理由 0 件)。warm は単独の `--collect-only` で、集計器は rc だけを見る (rc 0)。
- **外乱 (R8):** 原裁定 §4 R8 は受入共有 root の session のうち**作成時刻**が [セル開始 − 900 秒, セル終了] のものを候補にする。集計器は作成時刻の代わりに dir の mtime を使っていた (author 契約が近似を許していた。mtime は作成後に進みうるので、区間内に作られ後で更新された session を落としうる) — 集計器の出力は「mtime による代替抽出で全セル候補 0」である。そこで親が原裁定どおり作成時刻 (`stat -c %W` の birth time) で受入共有 root `/work/1/SFC/tanab/.izanagi-acceptance-shards` の全 2,207 session を照合し直した (採取は 2026-09-21 21:27:27 JST 以前 = 採取直後に記録した `verbatim/acceptance-root-stat.taken.txt` の時刻、birth time 不明 0 件、最新の作成時刻 17:16:52、最新の mtime 17:38:58): **全 11 セルで候補 0 件 → 重複なし** (`verbatim/acceptance-root-stat.txt`、`verbatim/r8-birth-recheck.md`、script は `verbatim/r8_birth_recheck.py.txt`)。採取時点で残っている session だけを見ている。他 node・他ユーザーの MDS 負荷は検知できない。取り直しは不要だった。

## 4. 判定 (原裁定 §4 の R1〜R8)

数値の出所は `job-out-aggregate.json` (集計器の出力)。表は `summary-tables.md` (同 JSON から `verbatim/extract_summary.py.txt` で機械的に抜いたもの) の抜粋。時間は秒、worker 分布は 48 worker の中央値。

### 4.1 セル表

| cell | wall | pre_junit | W_w | M | modify | worker の待ち (cf_exit − cf_entry) | process 群 user | process 群 sys | intent_lock 差 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1-a | 69.88 | 16.06 | 15.58 | n/a | 0.45 | 0.32 | 717.56 | 86.43 | 5,740,931 |
| S2f-a | 68.08 | 62.73 | 62.71 | 48.56 | 47.62 | 0.02 | 868.78 | 2,193.64 | 65,416,689 |
| S3u-a | 69.22 | 64.18 | 64.16 | 52.34 | 46.53 | 0.02 | 878.48 | 2,158.99 | 65,445,267 |
| S3f-a | 69.32 | 64.09 | 64.07 | 49.20 | 46.70 | 0.02 | 897.35 | 2,149.32 | 65,444,676 |
| S3cf-a | 42.20 | 36.77 | 19.49 | 36.42 | 1.91 | 18.94 | 816.90 | 85.13 | 6,127,336 |
| S3cf-b | 43.38 | 37.89 | 19.49 | 37.57 | 1.90 | 20.24 | 815.69 | 84.29 | 6,127,957 |
| S3f-b | 69.27 | 64.04 | 64.02 | 52.61 | 46.57 | 0.02 | 892.33 | 2,137.26 | 65,445,316 |
| S3u-b | 68.85 | 63.80 | 63.78 | 50.36 | 46.68 | 0.02 | 866.89 | 2,164.03 | 65,444,900 |
| S2f-b | 68.19 | 62.94 | 62.93 | 48.66 | 47.65 | 0.02 | 881.09 | 2,193.85 | 65,416,539 |
| S1-b | 55.33 | 15.59 | 15.09 | n/a | 0.45 | 0.31 | 716.24 | 92.09 | 5,741,103 |

- pre_junit = max_w(cf_exit) − junit timestamp、W_w = max_w(cf_entry) − junit timestamp、M = max(早期 receipt prewarm の正常復帰, 早期 oracle prewarm の正常復帰) − junit timestamp (原裁定 §4 R5)。S1 は shard plugin も早期 memo も無い形で、memo は collection 通知後の barrier で走るため M は定義しない。
- `warm` は温めだけのセル (11.19 秒) で比較に使わない。

### 4.2 R1 閉包

| cell | 判定 | median(\|残差\|) | 閾値 | 残差 min / median / max | W_w を決めた worker (その残差) |
| --- | --- | --- | --- | --- | --- |
| S2f-a | 閉じた | 0.261 | 2.381 | 0.231 / 0.261 / 0.286 | gw42 (0.258) |
| S3f-a | 閉じた | 0.258 | 2.335 | 0.230 / 0.258 / 0.293 | gw46 (0.242) |
| S3cf-a | 閉じた | 0.281 | 2.000 | 0.249 / 0.281 / 0.344 | gw47 (0.254) |
| S3cf-b | 閉じた | 0.272 | 2.000 | 0.246 / 0.272 / 0.312 | gw46 (0.257) |
| S3f-b | 閉じた | 0.260 | 2.329 | 0.224 / 0.260 / 0.380 | gw47 (0.224) |
| S2f-b | 閉じた | 0.260 | 2.382 | 0.223 / 0.260 / 0.302 | gw47 (0.237) |

閾値 max(2 秒, 0.05 × modify 中央値) は診断上の許容値で、精度保証ではない。残差は全 worker で正 (葉の和が modify より約 0.22〜0.38 秒短い) で、葉に入らない区間 (委譲 wrapper 自身・葉の境界の間の処理) が残っている。

### 4.3 R2 帰属 (葉の wall の worker 中央値、括弧は share = 葉の中央値 / modify の中央値)

| 葉 | S2f-a | S3f-a | S3f-b | S2f-b | S3cf-a | S3cf-b |
| --- | --- | --- | --- | --- | --- | --- |
| resolve pass-1 | 23.077 (0.485) | 22.862 (0.490) | 22.980 (0.493) | 23.036 (0.483) | 0.108 (0.056) | 0.110 (0.058) |
| resolve pass-2 | 22.795 (0.479) | 22.069 (0.473) | 22.013 (0.473) | 22.780 (0.478) | 0.057 (0.030) | 0.056 (0.030) |
| canonical 残り pass-1 | 0.600 (0.013) | 0.595 (0.013) | 0.597 (0.013) | 0.601 (0.013) | 0.502 (0.263) | 0.500 (0.263) |
| canonical 残り pass-2 | 0.595 (0.012) | 0.593 (0.013) | 0.594 (0.013) | 0.597 (0.013) | 0.495 (0.260) | 0.494 (0.260) |
| records 残り | 0.070 | 0.070 | 0.070 | 0.070 | 0.062 | 0.061 |
| allocate | 0.060 | 0.060 | 0.059 | 0.060 | 0.066 | 0.069 |
| 選択 loop 残り | 0.046 | 0.047 | 0.047 | 0.046 | 0.035 | 0.035 |
| `pytest_deselected` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| state | 0.054 | 0.054 | 0.054 | 0.055 | 0.057 | 0.057 |
| shard impl 残り | 0.004 | 0.004 | 0.004 | 0.004 | 0.004 | 0.005 |
| conftest 前段 | 0.141 | 0.146 | 0.142 | 0.145 | 0.120 | 0.118 |
| conftest validate / strip / reorder / 残り | 0.027 / 0.011 / 0.000 / 0.002 | 0.028 / 0.011 / 0.036 / 0.002 | 0.028 / 0.011 / 0.037 / 0.002 | 0.027 / 0.011 / 0.000 / 0.002 | 0.028 / 0.011 / 0.030 / 0.002 | 0.028 / 0.011 / 0.030 / 0.002 |
| xdist WorkerInteractor の modifyitems | 0.035 | 0.035 | 0.035 | 0.035 | 0.037 | 0.036 |
| E0 / E4 | 0.000 / 0.001 | 0.000 / 0.001 | 0.000 / 0.001 | 0.000 / 0.001 | 0.000 / 0.001 | 0.000 / 0.001 |

- **「主因」の判定 (事前登録):** 該当なし (`job-out-aggregate.json` の `principal_leaves` は空)。最大の葉は 4 つの f セルすべてで resolve pass-1 (share 0.483〜0.493)。**最大の区間 = resolve pass-1** と書く。
- 事後の集計 (事前登録の判定ではない): 2 つの resolve 葉の share (葉の worker 中央値 ÷ modify の worker 中央値) の和は S2f-a 0.963 / S3f-a 0.962 / S3f-b 0.966 / S2f-b 0.962。別々の葉の中央値を足した値で、worker ごとの 2 葉の合計の中央値ではない。resolve 1 回あたりの wall は葉の worker 中央値 ÷ 27,049 回で pass-1 0.845〜0.853 ms、pass-2 0.814〜0.843 ms (派生値)。
- reorder は `--no-loadscope-reorder` の S2f で 0 秒 (呼ばれない)、S3 系で 0.030〜0.037 秒。
- `pytest_deselected` は選択区間の中で呼ばれるが、worker 上の impl の実行時間は 0.000 秒 (中央値)。
- **CPU (大区間、thread の値は `RUSAGE_THREAD`):** shard impl 全体の thread sys は worker 中央値で S2f-a 43.48 / S3f-a 42.61 / S3f-b 42.36 / S2f-b 43.74 秒 (48 worker 合計 2,080.1 / 2,033.7 / 2,025.3 / 2,083.4 秒)、thread user は 3.03〜3.12 秒。S3cf では thread sys 0.07 / 0.06 秒 (合計 3.9 / 3.7 秒)、thread user 1.34 / 1.33 秒。records_from_items と選択区間がそれぞれ thread sys の約半分ずつを持つ (`summary-tables.md` §R2 大区間の CPU)。**process 群の sys (§4.1、`/usr/bin/time` の値) と thread sys の合計は同じ量ではない** (前者は controller と全 process を含み、後者は計時した区間の worker thread だけ)。

### 4.4 R3 観測者効果 (S3f − S3u、half ごと)

| half | Δmodify 中央値 | ΔW_w | Δpre | 判定 |
| --- | --- | --- | --- | --- |
| a | +0.169 | −0.091 | −0.090 | 閾値内 |
| b | −0.108 | +0.240 | +0.237 | 閾値内 |

3 量とも |値| ≤ 2 秒で「計器の影響は判定閾値内」。

### 4.5 R4 反実仮想の集合同値 (S3cf の有効条件)

両 half とも一致: 全 48 worker の `records_digest` / `selected_digest` がセル内で一意かつ S3cf・S3f・S3u の間で一致 (`3fdca6e6…` / `f43d3301…`)、gw0 の records (27,049 件) / selected (4,204 件) の canonical JSON sha256 が一致、report の `observed_universe` / `selected` の sha256 が一致。これは観測標本の一致であり、一般的同値の証明ではない。

### 4.6 R5 主比較 (S3f − S3cf、half ごと)

| half | ΔW | Δmodify | Δpre | ΔM |
| --- | --- | --- | --- | --- |
| a | 44.575 | 44.794 | 27.323 | 12.785 |
| b | 44.528 | 44.675 | 26.146 | 15.038 |

worker 側 (ΔW) は約 44.5 秒縮み、`pre` (Δpre) は約 26〜27 秒縮んだ。差は `pre` が M に張り付いたことによる (§4.7)。

### 4.7 R6 `pre` の構造

- 全有効 S2 / S3 セル 8 つで残差_pre = pre_junit − max(W_w, M) は +0.017〜+0.354 秒 (|残差_pre| ≤ 2 秒で「max 式に適合」)。
- S2f / S3u / S3f の 6 セルは W_w > M (W_w − M = 11.41〜14.86 秒、json の原精度で差を取ってから丸めた派生値) で、worker の待ち (cf_exit − cf_entry) の中央値は 0.023〜0.024 秒。`pre` は worker 側で決まっている。
- S3cf の 2 セルは W_w (19.49 秒) < M (36.42 / 37.57 秒) で、`pre` (36.77 / 37.89 秒) は M との差 0.35 / 0.32 秒。worker の待ちの中央値は 18.94 / 20.24 秒 (C の `_wait_early_memo_job` の出入りでは 18.88 / 20.15 秒)。
- **事前登録した S3cf の予測:** (i) 適合 — 的中 (両 half)。(ii) W_w(S3cf) < M(S3cf) の分岐で「Δpre < ΔW かつ pre(S3cf) ≈ M(S3cf)、worker の待ち (cf_exit − cf_entry) が伸びる」— 3 条件とも成立して的中 (両 half): Δpre 27.32 / 26.15 < ΔW 44.58 / 44.53、|pre − M| 0.354 / 0.321 秒 ≤ 2、待ちの中央値 0.023 → 18.94 秒 (a)・0.024 → 20.24 秒 (b)、増分 18.92 / 20.22 秒。
- **集計器の予測判定の限定:** 集計器の `R6.prediction-*.pass` は (ii) のうち「Δpre < ΔW かつ |pre − M| ≤ 2」だけで合否を決め、「待ちが伸びる」は別列 `wait_increased` に出していた (author 契約の予測式から待ちの条件が落ちていた)。上の判定は親が json の `timing_pass` と `wait_increased` (いずれも true) を合わせて 3 条件で出し直したもので、結論は変わらない。
- M は S3f 49.20 / 52.61 秒 → S3cf 36.42 / 37.57 秒と縮んだ (ΔM 12.78 / 15.04 秒)。**原因は識別しない** (早着 worker の CPU / local IO、resolve 削減による Lustre 負荷の変化などは候補にとどまる)。

### 4.8 R7 Lustre・CPU (記述のみ、閾値なし)

§4.1 の process 群 user / sys と `intent_lock` 差のとおり。S3cf の sys (85.13 / 84.29 秒) と `intent_lock` (6,127,336 / 6,127,957) は shard plugin なしの S1 (sys 86.43 / 92.09 秒、`intent_lock` 5,740,931 / 5,741,103) に近い。

### 4.9 R8 外乱

§3 のとおり、原裁定どおりの作成時刻による親の再照合で全セル候補 0 = 重複なし (集計器の mtime による代替抽出も全セル候補 0)。取り直しは発生しない。

## 5. 既存観測・既裁定との関係 (条件が異なる既存観測として並べる。食い違いとは呼ばない)

- **T-2817 (計算ノード 48 worker、tip `2afb39768`):** S2 worker modify 中央値 45.66 / 45.55 秒、S3 44.68 / 44.79 秒、process 群 sys 80 → 2,108 秒、`intent_lock` 5.2 M → 60.9 M。本 job の同形の値 (S3u modify 46.53 / 46.68 秒、S1 → S3u の sys 86.43 → 2,158.99 秒) は同じ桁だが、tip と台帳 (+15,645 / −13,419 行) が違うので参照に留める (原裁定 §4「比較の限定」)。T-2817 が「読み」とした `Path.resolve()` への帰属は、本 wave で関数別計時 (R1 閉包・R2) と反実仮想 (R5) により測られた。
- **T-2617 §3.2 / §4 (login 単独 process):** plugin あり − なし = user CPU +1.74 秒 (sys 1.37 → 3.09 秒)。§4 は「`_canonical_item` の 2 回目の呼び出しを 1 回目の結果で置き換える」案を「1 worker あたり 0.9 秒未満。48 worker でも wall 1 秒級」と見積もって採らないと判定し、`Path.resolve()` の字句処理への置換は不可と判定した。**本 job (計算ノード 48 worker 同時) では pass-2 の resolve だけで worker 中央値 22.01〜22.80 秒、shard impl の thread sys は worker 中央値 42.4〜43.7 秒だった。** 本 wave の反実仮想は字句化ではなく「固定した collection 中の、成功した実 resolve 結果の再利用」であり、T-2617 §4 の判定の撤回・再判定は提案しない (原裁定 §1・§6)。値を記録するだけで、T-2617 の測定値も無効化しない (規律 7)。
- **T-2825 (entry 1803、実受入の隣接対):** shard-0 の `pre` は台帳 refresh 後の B 有効 3 走で 63.0 / 63.5 / 64.4 秒 (refresh 前の A を含む有効 6 走では 62.6〜64.4 秒、`output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md` の走表)。本 job の S3u (受入の argv 形 + 共通計時) の `pre_junit` 64.18 / 63.80 秒は B の範囲にあるが、実受入 (test を走らせる) と collection-only の probe は条件が違う参照値である。
- **D2200 項 4 (受入門番の閾値の据え置き):** 再提示の条件は「門番待ちの実測 wave と受入律速の診断 (T-2273 / T-2817 / T-2825 / T-2826) の結果が揃ったとき」。本 wave で T-2826 の結果が出た。再提示するかは裁定側の手番で、本 wave は判断しない。
- **T-2273 (entry 1803 の項):** 「固定費 F_0 の pre の内訳は [T-2826]」— 本 README §4 がその内訳である。

## 6. 限界・言わないこと

- **1 job・1 node (bnode003)・順序反転 2 half の記述的診断**であり、外乱除去・効果確立の証明ではない (原裁定 §4「比較の限定」)。
- 反実仮想 S3cf は probe の中だけの 1 条件で、**実受入の wall の予測・短縮策の効果の見込み・恒久実装の可否には使わない。** R4 は観測標本の一致で、一般的同値性の証明ではない。memo は process 内・`_canonical_item` 実行中だけに限定した (conftest の resolve・`Path.cwd().resolve()`・spec 解決には触れていない)。
- S3cf の値は計装下 (f の計器を載せた) の値である。R3 は無計装 S3u と計装 S3f の差が閾値内であることを示すが、S3cf 自体の無計装値は測っていない。
- M の縮み (ΔM) の原因は識別していない。
- R8 は受入共有 root の session だけを見る。作成時刻による親の再照合は採取時点 (21:27:27 JST 以前、`verbatim/acceptance-root-stat.taken.txt`) に残っていた session だけを対象にし、削除済みの session や外乱一般の不在は示さない。他 node・他ユーザーの MDS 負荷は検知できない。集計器の R8 は mtime による代替抽出で、原裁定の作成時刻とは異なる (§3)。
- 集計器の R6 予測判定 (`pass`) は事前登録の条件のうち「待ちが伸びる」を含まない。本 README の予測判定は親が 3 条件で出し直したもの (§4.7)。
- warm は温めだけのセルで、有効セル条件の検査対象ではない (集計器は rc だけを見る)。
- R4 の集合照合について、段 6 review が独立に確かめたのは保存された hash (全 worker の digest、gw0 の records / selected の canonical sha256、集計器が report から取った hash) の一致と照合実装までである。report 本体と gw0 の配列そのものは repo に置いていない (`raw/job-out/report-json-sha256.txt` は report 全体の hash で、配列の canonical hash を再計算する代替にはならない)。report の中身からの独立な再計算は行っていない。
- R1 の「閉じた」は、残り (canonical 残り・records 残り・選択 loop 残り・shard impl 残り・conftest 残り) を差で定義する分解なので、閉包だけでは帰属の独立な証明にならない。帰属の裏付けは S3cf の反実仮想 (R5) が担う。
- 集計器・plugin・runner は Codex author が書き、子の検査は偽 module による関数単位と合成入力までである。本物の shard plugin / conftest での配線は親の login 生死確認 (2 worker) と本 job で確かめたが、それ以上の独立検査は段 6 の review に委ねた (§8)。
- 本 job の後の最終受入 (記録 commit の後) の shard-0 `pre` は、別 tip の参考観測としてだけ worklog に書く。

## 7. 再現

1. 計測 tip `36fb14a3d` の worktree を投入元にし、`verbatim/t2826_*.txt` の 3 file を拡張子を戻して 1 dir に置く。
2. `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:40:00 --queue-wait-timeout 5400 --overall-grace 5400 -- bash <dir>/t2826_modify_timing_probe.sh` (出力先は env `T2826_OUT` か runner 既定。空 dir 必須)。
3. `python3.10 <dir>/t2826_modify_timing_aggregate.py <OUT_ROOT> --markdown <md> --json <json> --acceptance-root /work/1/SFC/tanab/.izanagi-acceptance-shards`。
4. 要約表は `python3.10 verbatim/extract_summary.py.txt <json>` (拡張子を戻して)。

## 8. 段 6 review

- review 1 本 (Codex gpt-6-astra / medium / read-only、2 レンズを 1 本、job-id `t2826r-s6-review-1`、21:19〜21:26 JST、`check_codex_output.py` rc 0)。prompt と出力の逐語は `verbatim/s6-review-prompt.md` / `s6-review-out.md`。数表照合は 315 件中 313 件一致・不一致 2 件 (W_w − M の上端の二重丸め、T-2825 の引用範囲)、生記録との照合は 159 項目すべて一致、`job-out-aggregate.md` は保存 json と集計器から完全に再生成できたと報告した。判定は NO-GO (must-fix 2)。
- 所見 8 件 (must-fix 2・should 5・nit 1) を**全件 real・採用**と裁定し、本 README を直した: (1) R8 が作成時刻でなく mtime を使っていた → 親が作成時刻で全 session を再照合 (§3); (2) R6 予測判定の合否が「待ちが伸びる」を含まない → 3 条件で出し直し (§4.7); (3) 「11 セルすべて有効」の量化 → xdist 10 セルと warm を分けた; (4) 題の「96 %」→ 題は最大の区間を中心にし、事後集計の定義を明記; (5) T-2825 の `pre` の引用範囲 → refresh 後 B と A を分けた; (6) 出所の不足 → author receipt・投入前後の status・受入 root の stat を `verbatim/` に添付し、649 秒を scheduler の `Elapse` と明記; (7) W_w − M の上端 14.87 → 14.86; (8) R4 の独立確認の範囲と R1 閉包の限界を §6 に追記。refuted 0 件。
- 焦点再レビュー 1 本 (Codex gpt-6-astra / medium / read-only、job-id `t2826r-s6-focus-1`、21:32〜21:36 JST、`check_codex_output.py` rc 0、逐語 `verbatim/s6-focus-1-prompt.md` / `s6-focus-1-out.md`): 所見 1〜8 は **closed 8・partial 0・regressed 0**。R8 の全 2,207 行 × 11 セル、R6 の 3 条件、W_w − M の範囲、share の和、T-2825 の引用、正規化記録 (18 file・41 行・除去 65 byte) を独立に再計算して一致。新規所見は nit 1 件 (R8 の採取時刻を 21:27:18 と書いたが添付記録は 21:27:27。21:27:18 は直前の下見の表示時刻だった) で、real と裁定して添付記録の時刻へ直した。判定 **GO**。

## 9. この dir の中身

- `README.md` — 本文。
- `job-out-aggregate.md` / `job-out-aggregate.json` — 集計器の出力 (本文の数値の出所)。
- `summary-tables.md` — 同 JSON から機械的に抜いた要約表。
- `raw/job-out/` — 計算ノード job の各セルの `cell.txt`・`time.txt`・`probe.json`・`junit.xml`・`out`・`err`・loadavg・MemAvailable・Lustre stats、job の `env.txt` ほか。各セルの process 一覧 (他ユーザーの process を含む) は入れず、`cell.txt` の `others=` / `stale_pytest=` に数え上げだけ残る。S2 / S3 の `session/shard-0/report.json` (計 46.7 MB) は入れず、sha256 を `raw/job-out/report-json-sha256.txt` に置く (R4 は集計器がその中身を照合済み)。
- `raw/login-out/` — login 生死確認の各セルの `cell.txt`・`time.txt` と集計 (`login-aggregate.md`)。比較には使わない。
- `verbatim/` — 依頼 (`T-2826-resume-origin.md`)、段 1 brief (`s1-brief.md`)、段 4 裁定 (再開版、`s4-ruling.md`)、段 5 の prompt / 報告 / dry-run / midflight gate、probe 3 file と要約 script と運転 script の逐語 (`*.txt`)、開始 gate の出力、子 worktree 作成・pyc 温め・生死確認・本走の時刻と dispatch log。
- `verbatim/s5-author-receipt.json` (author 子の receipt)、`verbatim/run-probe.status-before.txt` / `run-probe.status-after.txt` (投入前後の `git status --porcelain`、いずれも 0 byte)、`verbatim/acceptance-root-stat.txt` / `acceptance-root-stat.taken.txt` (受入共有 root の全 session の `stat -c '%W %Y %n'` と採取時刻)、`verbatim/r8-birth-recheck.md` / `r8_birth_recheck.py.txt` (作成時刻による R8 の再照合とその script)、`verbatim/s6-review-prompt.md` / `s6-review-out.md` (段 6 review)、`verbatim/s6-focus-1-prompt.md` / `s6-focus-1-out.md` (焦点再レビュー)。
- `verbatim/trailing-whitespace-normalization.md` — `raw/` の `cell.txt` 16 本と `verbatim/run-probe.log` の行末空白 (各 1 行・1 byte)、`verbatim/s6-review-out.md` / `s6-focus-1-out.md` の行末空白 (24 行 / 6 行・各 2 byte) の可逆最小正規化の記録 (DW-S07。原文 sha256・byte 数・復元法)。
