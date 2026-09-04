## 問 1 — 事実確認

(P1-a) から (P1-d) は概ね正しい。ただし「1 job 内」は、3 workload 全体が 1 job ではなく、**各 workload の全格子が 1 job、合計 3 job**である。

- submit receipt は write-heavy=951689、balanced=951690、read-heavy=951691 の 3 job を記録している (`/work/1/SFC/tanab/b10-backoff-grid-runs5/b10-backoff-grid-20260826T234647Z-783837.submit.jsonl:1-4`)。
- 3 件とも `status: complete` である。各 `completion.json:16-21` が campaign、job id、workload、完了状態を束縛する。
- 各 job は job-local の単一 build cache を作る (`tools/pegasus/b10_backoff_grid.sh:252-256`)。
- dat は `source_measurement: trace_disabled` と記録する。3 workload とも依頼済み 4 点は次の行に存在する。

| workload | 150 | 200 | 300 | 500 |
|---|---:|---:|---:|---:|
| write-heavy | dat:23 | dat:24 | dat:26 | dat:28 |
| balanced | dat:23 | dat:24 | dat:26 | dat:28 |
| read-heavy | dat:23 | dat:24 | dat:26 | dat:28 |

ここで dat は各 workload の `/work/1/SFC/tanab/b10-backoff-grid-runs5/.../reports/b10-backoff-grid-<workload>.dat` である。

**999 の読解は正しい。** 符号化の実体は `patches/silo-backoff-fixed.patch:69-73`、特に同 `:70` の次の分岐である。

```cpp
(BACKOFF_FIXED / 1000ULL == 0ULL)
    ? static_cast<double>(BACKOFF_FIXED)
    : ((BACKOFF_FIXED / 1000ULL == 1ULL)
       ? ... (BACKOFF_FIXED % 1000ULL) ...
```

したがって、

- 999 は商 0 なので第 1 枝に入り、`now_backoff = 999.0`。
- 1000 は商 1・剰余 0。mode 1 の式では振幅に使う項がすべて 0 となり、`now_backoff = 0.0`。
- 独立な逐語 model も 0 から 999 の両 uint64 端で入力値と完全一致することを全点検査している (`orchestrator/campaign/b10_backoff_shape_sweep.py:650-663`, `orchestrator/tests/test_b10_backoff_shape_sweep.py:1920-1923`)。
- F718 の台帳も同じ結論である (`docs/failures.md:19467-19483`)。1000 行が 0 行と一致する実測裏付けは同 `:19493` にある。

**依頼の有効な既測点は本当に 4 点である。**

- `EXTENDED_SWEEP_US` の全列挙は 150、200、300、500 を含むが、750 と 999 を含まない (`orchestrator/campaign/backoff_extended_sweep.py:37-40`)。
- write-heavy の 700/800 は dat `:31-32`、900 は `:33`。750 はない。
- `1000` と表示された dat `:34` は固定 1000 ではなく固定 0 の独立反復なので、6 点目に数えられない。
- tracked `output/campaigns`、`output/insights`、外部 B-10 root、`izanagi-job-evidence/thread-scaling` を `BACKOFF_FIXED=750/999` と dat の行頭値で検索したが、測定 artifact はなかった。見つかった 999 は明示的な synthetic fixture (`orchestrator/campaign/p3_s4_red.py:167-180`) とテスト fixture だけである。
- よって未測定は、依頼そのものでは 750 と「表現不能な真の 1000」。999 を代替端点として採るなら 750 と 999 の 2 点である。

**凍結 pin は親の列挙より広い。**

- `SWEEP_US` は定義 (`backoff_sweep.py:59`) から genome (`:191-200`) と campaign identity (`:203-218`) へ入る。S1 generator は候補集合完全一致と source hash を取る (`s1_known_axes_freeze.py:384-423`)。golden と直接検査は `s1_expected_goldens.py:30-31`、`test_s1_known_axes_freeze.py:546-549`。
- その source SHA は `output/s1-freeze/known_axes_freeze.json:145-155` と `measurement_freeze.json:164-174` に実在し、さらに `output/s8b-freeze/holdout_freeze.json:148-160` へ伝播している。
- A-5 finalizer も `backoff_sweep.genomes()` の正確な 8 genome を要求する (`a5_second_boot_backoff_sweep.sh:615-619,649-662`)。
- B-10 job は `output/s1-freeze` と `output/s8b-freeze` の合同 SHA を前後 2 回検査する (`b10_backoff_grid.sh:552-595`)。
- `EXTENDED_SWEEP_US` は genome 順 (`backoff_extended_sweep.py:282-306`) と `search_config.sweep_us`、測定順を通じ identity に入る (`:327-355`)。テストは格子、上端、重複なし、順序を pin する (`test_backoff_extended_sweep.py:152-172,371-382`)。
- report は 31 点と静的集合の完全一致を要求する (`backoff_extended_sweep_report.py:83-96`)。
- T-1941 consumer も独立な `EXPECTED_FIXED_GRID` を持ち、reference lock の格子を完全一致させる (`backoff_requested_us.py:69-72,451-475,597-607`)。
- 作図器は raw 29 点と有効 28 点を literal 化し (`tools/plotting/plot_b10_extended_backoff.py:34-40`)、3 campaign identity と入力 SHA を固定する (`:75-154`)。provenance テストにも独立コピーがある (`test_b10_extended_figure_provenance.py:43-117`)。

したがって、両既存定数は変更不可という (P1-d) は正しい。

## 問 2 — 新規測定なしで閉じる範囲

既存 28 点で、依頼の科学的目的である「未測定 tail に説明を依存している状態」はほぼ閉じる。

- write-heavy の静的 throughput は 150 µs の 2.048 M から 560 µs の 1.252 M、600 µs の 1.218 M、900 µs の 1.035 M まで実測されている。適応側の観測谷 1.242 M (`2026-09-02_t2216...md:157-164`) は、静的曲線の 560〜600 µs 付近に実在する。
- よって旧文書 `:46-48,206-207` の「谷より低い値には未測定 b>100 が必要」「b>100 は 1 点もない」は誤りである。
- 700 と 800 が 750 を挟み、tail は 900 まで滑らかに低下しているため、750 の欠測は「低い tail が存在する」という結論を左右しない。
- 一方、750 の正確な `T` と abort 率、真の固定 1000、依頼 6 点を同一の新規 job 割付けで測ったという literal な達成は残る。
- 静的 tail は動的 `Backoff_` の滞在分布を示さない。遷移損失、同期、履歴依存、leader 固有の abort、窓内 commit 分布も未観測のままである (`2026-09-02_t2216...md:180-193`)。機序確定には直接計装が必要であり (`:240-243`)、T-2266 だけでは閉じない。

歩行 model への影響は重要である。

- 現行 model の静的入力は 0、2、5、10、25、50、100 の 7 点だけ (`tools/t2216_backoff_walk_model.py:52,279-324`)。
- 100 を超える領域は、50→100 の末尾 2 点から指数外挿する (`:327-361`)。
- その式では write-heavy の予測は約 0.429 M at 500、0.078 M at 900 だが、実測は 1.305 M と 1.035 M。現行 model は大 backoff の損失を大幅に過大評価している。
- 実測 tail を入れると、大 b での期待 throughput は上がり、abort 率も実測値になり、leader 試行周期と遷移確率の両方が変わる。非線形なので順位や滞在率の向きは再計算なしには断定できない。
- ただし現行 model は、tail を過度に悪く仮定しても観測谷より高い値しか出せなかった (`2026-09-02_t2216...md:159-178`)。実測 tail はより高性能なので、同じ滞在分布なら谷の再現はさらに難しくなる。単純な静的混合では足りないという否定的結論は、弱まるより強まる可能性が高い。

## 問 3 — 最小実装プラン

**`tools/pegasus/admission_registry.json` を触らずに済む経路は存在する。** 推奨経路は、既存 B-10 job body と submitter に T-2266 固有の opt-in mode を足し、既存 driver file 内に別 grid を追加する方法である。新しい `tools/pegasus/*` path は作らない。

実装案は次のとおり。

1. `orchestrator/campaign/backoff_extended_sweep.py:37-40` の `EXTENDED_SWEEP_US` は一切変更せず、隣接する別定数として `T2266_REQUESTED_US = (150, 200, 300, 500, 750, 999)` と、同一 job 内の静的 baseline を含む `T2266_SWEEP_US = (0, 150, 200, 300, 500, 750, 999)` を追加する。999 は必ず「1000 の測定値」ではなく「現符号化で表現できる最大固定値」と記録する。

2. 同 `:282-355` に T-2266 専用の順序、genome、config builder を追加する。slug は `t2266-backoff-static-tail-silo-<workload>`、identity には grid、測定順、`requested_endpoint=1000`、`realized_endpoint=999`、`reason=F718` を入れる。既存 `genomes()`、`measurement_order()`、`config_for()` の戻り値は変えない。

3. 同 `:358-444` の実行本体を point/config を受け取る private helper へ切り出し、既存 `run_workload()` は従来値を渡す薄い wrapper として保持する。T-2266 wrapper も同じ `_require_backoff_condition_gate`、`_prebuild_backoff_binaries`、`run_campaign` を使う。これにより新しい正しさ gate や build authority は増やさない。

4. trace/perf の build pair は既存のまま使う。pipeline は同じ genome、toolchain、source evidence から `trace=True` と `trace=False` を作り (`pipeline.py:1236-1263`)、bench には `trace=False` 側を渡す (`:1679-1705`)。T-2266 report は WAL の committed attempt から `median_tps`、全 rep、abort rate、latency、CV を読み、create-only の `.dat` と JSON を出す。新たな判定規則は足さない。

5. `tools/pegasus/b10_backoff_grid.sh:183-196` に exact な `B10_RUN_KIND={extended,t2266-tail}` を追加する。`extended` を既定にして現行挙動を保つ。同 `:570-587` では共通 driver argv に T-2266 時だけ opt-in flag を追加し、T-2266 時は scope 外の `backoff_overthrottle.py` と B-10 shape report を実行しない。isolated CCBench worktree、job-local cache、reservation、freeze 前後検査 (`:421-575,589-623`) は共有する。

6. `tools/pegasus/submit_b10_backoff_grid.sh:6-27` に T-2266 専用 opt-in を追加し、同 `:80-87,163-170` で mode を qsub 環境へ束縛する。既存の `WORKLOADS=(write-heavy balanced read-heavy)` と 1 workload=1 job の fan-out は変更せず、3 job を同じ loop から連続投入する。既存 05:00:00 envelope を流用すれば、実装上の walltime 再設計も不要である。

7. `orchestrator/tests/test_backoff_extended_sweep.py:152-172,371-396` に、既存格子と既存 campaign identity が不変である検査、T-2266 格子が exact 7 点で 1000 を含まない検査を追加する。同 `:528-589,683-723` では、extended branch の既存 3 job、freeze、AA/report、script SHA contract が残り、T-2266 branch は同じ 3 workload で tail driver だけを起動することを検査する。

8. 新規測定の有無にかかわらず、`output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md:39-48,151-190,200-217,238-246` を訂正し、`output/insights/2026-09-03_t2266-backoff-static-tail/` に既存 dat の逐語表、SHA/provenance、F718、model への影響を置く。

候補ごとの判定は次のとおり。

- **(i) A-5 流用は不採用。** job は write-heavy/balanced しか受けず (`a5_second_boot_backoff_sweep.sh:188-206`)、driver は `backoff_sweep.py` に固定 (`:589-592`)、finalizer は既存 8 genome と workload 別 5/10 µs target を要求する (`:615-619,649-662,745-748`)。契約テストも exact 2 workload、`read-heavy` 不在、既存 driver の一意呼出しを pin する (`test_a5_second_boot_job_contract.py:177-187,273-300`)。tail mode を足すと A-5 正式測定の意味を壊す。

- **(ii) B-10 流用は採用。** 既に 3 workload fan-out、isolated worktree、build cache、reservation、trace/perf pair が揃う。ただし現状の argv/env だけでは格子は変わらないため、上記の T-2266 固有 opt-in を実装する。default branch は B-10 の exact grid/report contract を保持する。

- **(iii) 新 driver + 新 job body + 新 submitter は不採用。** 新しい `tools/pegasus/*` は runtime guard が未登録実行体として拒否する (`hooks/guard_bash.py:609-623,1200-1210`)。さらに `test_hooks.py:2572-2640,2641-3044,3445-3456` が registry の path と 4 field を literal golden で固定するため、registry と test golden の双方の編集が必須になる。これは稼働 wave との重複面を避ける条件に反する。

- **(iv) `dispatch_compute.py --task generic` は不採用。** generic は非空 argv を shell=False で実行できる (`dispatch_compute.py:154-160,1311-1321,1623-1637`) が、child 環境は HOME/PATH 等だけの clean 集合 (`:335-345,1406-1417`) で PBS/reservation 変数を落とす。一方 campaign authorization は reservation binding を必須にする (`orchestrator/campaign/loop.py:198-207`)。既存 B-10/A-5 job bodyも PBS 変数を要求する。generic の環境契約を拡張するのは本題外の一般化になる。

- **(v) 新規測定なしの既存 artifact 再解析は採用可能。** 科学的な tail の空白は既存 28 点で閉じており、実装は insight 訂正と既存 tail の model 突合せだけで済む。

registry を変更しない理由は、新しい login/compute entry pathを作らず、既登録の job body (`admission_registry.json:22-26`) と submitter (`:292-296`) の site class、primary gate、evidence を変えないためである。`test_official_perf_closure.py:44-52,807-823,888-905` の exact inventory に対しても、新しい perf predicate fileや tracked callを追加せず、既存 reviewed driver 内の実行面を再利用する。

pytest は実行していない。以上は source、台帳、外部一次成果物の静的検査結果である。

## 問 4 — 推奨

択一は次の 3 つでよい。

1. **新規測定なし、既存 28 点の再解析と文書訂正だけを行う。推奨。** 0 job。実装は T-2216 訂正と T-2266 insight が中心。tail が谷以下まで低下するという目的は既に実測で閉じる。750 の exact 値と真の 1000 は残るが、機序の残課題は直接観測であり、この 2 点ではない。

2. **B-10 の T-2266 mode で 7 静的点を再測定する。** `[0,150,200,300,500,750,999]` を workload ごとの 3 job へ同時投入する。3 job、既存 envelope では最大 5 時間/job、最大 15 node-hour、外部 wall clock は最大約 5 時間。既存 4 点を含めた同一 job 座標、750、最大表現可能値 999 が得られる。真の 1000 は得られない。

3. **専用 job body/submitter を新設する。非推奨。** job 数と得られる測定は 2 と同じだが、新規 Pegasus path、registry、`test_hooks` golden、追加契約テストが必要になる。科学的な上積みがなく、編集中 wave と `admission_registry.json` で衝突する。

依頼の「目的」を優先するなら 1、依頼の「指定点を同一の新規割付けで測る形」を優先するなら 2 である。1000 については、どちらを選んでも「未測定」ではなく「現符号化では測定不能」と明記する必要がある。

## 総括

- 既存 B-10 は各 workload 1 job、合計 3 job で完走した trace-disabled 29 行、F718 除外後 28 有効点である。
- 依頼 6 点のうち有効な既測は 150、200、300、500 の 4 点。
- 750 は未測定。1000 行は mode 1・振幅 0で、真の固定 1000 ではない。
- 999 は商 0 の固定値として正確に表現できるが、測定 artifact はない。
- `SWEEP_US` と `EXTENDED_SWEEP_US` は freeze、consumer、report、plot、provenance test の複数経路に pin されており変更不可。
- 既存 28 点は、静的 tail が観測谷まで低下する事実を既に実測で閉じる。
- model の 100 µs 超は指数外挿であり、実測 tail を入れると単純混合の不成立はむしろ強まる可能性が高い。
- 推奨は 0 job の再解析・文書訂正。
- 測る裁定なら、既存 B-10 path の T-2266 固有 modeで 3 job を同時投入し、registry は変更しない。
- 新規 Pegasus job body/submitter と generic dispatch は採らない。