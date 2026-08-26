# B-10 balanced workload の機序 profile (2026-08-27, Pegasus)

paper-story `docs/paper-story/2026-08-26.md` §8 B-10 が未取得としていた 4 項目のうち
**「balanced workload の profile」** を取得した。

一次資料:

- `output/env/pegasus/profile/backoff_profile_t48_skew0p9_rr50.json` (rep ごとの生値を含む)
- `output/env/pegasus/profile/backoff_profile_t48_skew0p9_rr50.md`
- job log: `output/insights/2026-08-26_b10-balanced-profile/job-logs/b10bal-20260827-06`
- 再現用 job body: `output/insights/2026-08-26_b10-balanced-profile/job-body.sh`

## 1. 何を測ったか

balanced (`ycsb_zipf_skew=0.9` / `ycsb_rratio=50` / `ycsb_rmw=0`)、48 thread、
1,000,000 records、`extime=3`、`REPS=3`。無 backoff + 静的 backoff 6 値
(2/5/10/25/50/100us) の 7 点。`BACKOFF_NOINLINE=1` の診断 build に
`perf record -e cycles,instructions` を当て、`Backoff::backoff` の cycle% と instruction% を
分離して**有用 IPC = (全命令 - spin 命令) / (全 cycle - spin cycle)** を出した。

実行環境は Pegasus 計算ノード `bnode125`、`clocks_per_us=2100`、
ccbench `511c9538e4e8efa54b45cda62e72389ed3b706ec`、
perf 実体 `/usr/lib/linux-tools-5.15.0-135/perf`。

## 2. 結果

| backoff us | tps (median) | abort% | spin cyc% | spin instr% | total IPC | useful IPC |
|---:|---:|---:|---:|---:|---:|---:|
| 0 (none) | 4,044,953 | 66.9 | 0.0 | 0.0 | 1.933 | 1.933 |
| 2 | 4,510,108 | 54.6 | 22.6 | 2.7 | 1.607 | 2.019 |
| 5 | 4,336,086 | 45.6 | 37.6 | 5.5 | 1.322 | 2.002 |
| 10 | 3,859,665 | 38.5 | 49.6 | 8.7 | 1.085 | 1.967 |
| 25 | 3,022,782 | 29.2 | 63.5 | 15.0 | 0.802 | 1.866 |
| 50 | 2,382,936 | 22.9 | 72.3 | 20.9 | 0.650 | 1.858 |
| 100 | 1,829,445 | 17.5 | 78.8 | 28.6 | 0.520 | 1.748 |

**事前登録した評価帯 (0-10us) で:**

- total_ipc の散布 = **57.0%**
- useful_ipc の散布 = **4.3%** (replication bar 4.4% の内側)

**判定 = condition-met。** balanced でも total IPC の低下は spin 希釈で説明でき、
有用な仕事の per-instruction 効率は sweet-spot 帯でほぼ不変である。

全域 (0-100us) では useful_ipc の散布が 14.2% へ広がる。過抑制域の二次低下を含むため
であり、核命題は sweet-spot 帯に限る (既存 write-heavy 成果物と同じ限定)。

## 3. 事前登録の順序 (事後選択でないことの記録)

評価帯 S = `backoff_us <= 10` は**段 4 で凍結した**。根拠は既存 write-heavy 成果物が同じ帯を
使っていることであり、**balanced の結果を 1 つも見ずに決めた**。散布の定義
`(max-min)/mean` と replication bar 0.044 も同時に凍結した。判定式・帯・bar は
成果物 JSON の `preregistered_decision` に機械可読で入っている。

**後から出てきた独立の裏づけ (帯の根拠ではない):**
`orchestrator/tests/s1_expected_goldens.py` の `EXPECTED_BACKOFF['balanced']` は
`backoff_us: 5` / `reference_fitness_tps: 3106342.0` を凍結している。5us は凍結した帯の内側
である。この一致は corroboration であって帯の選択根拠ではない。順序を混同すると、
事前登録が塞ごうとした事後選択と区別がつかなくなる。

## 4. 言わないこと

**balanced の +11.3% という既報の利得そのものを説明したとは主張しない。** 理由は 3 つあり、
いずれも実走前に確定していた。

1. 既報は別環境 (linux-baremetal) かつ別 source の値である。
2. この走は `BACKOFF_NOINLINE=1` の診断 build であり、D20 により perf 下 throughput を
   headline に使えない。
3. 同一 env / 同一 source の stock-inline 対照をこの wave では取っていない。

成果物には `headline_eligible: false` と `diagnostic_only: true`、固定文言の断り書きが
JSON と MD の両方に条件分岐なしで入る。

## 5. 残る限界 (機械可読 field つき)

- `comparison_confounds: ["environment", "ccbench_commit"]` — 既存 write-heavy との差は
  workload 効果だけに帰属できない。
- `backoff_time_live_verified: false` — 要求 us は contract-calibrated だが実効 TSC は未検証。
- `dependency_prefix_cache_identity_bound: false` — legacy build 経路は dependency prefix を
  cache identity へ束縛しない。job 専用 cache root で既存 cache の継承を避ける緩和に留まる。
- 同一 env / 同一 source の stock-inline 対照は未取得。

## 6. 途中で確定した環境の事実 (この wave の副産物)

いずれも `--task generic` で計算ノードへ投げた実測。受領証は `output/pegasus-dispatch/`。

- **perf は計算ノードで動く。** kernel は `5.15.0-173-generic` だが導入 linux-tools は 100 と 135
  だけで、`/usr/bin/perf` の dispatcher は必ず失敗する。一方
  `/usr/lib/linux-tools/5.15.0-135-generic/perf` は `stat` / `record` / `report --stdio` の
  すべてで rc=0 (request 950749 系)。`perf_event_paranoid=0`。
  `tools/pegasus/policy.json` の候補一覧は先頭が 135 で修正不要。
  過去の `output/env/pegasus/t293-perf-site/` の probe が候補ゼロを返していたのは、
  toolchain 解決で先に落ちて perf の機能 smoke に到達していなかったためである。
- **汎用投入の子は proxy 変数を持たない。** 素の `git ls-remote` は
  `Could not resolve host: github.com` (request 951179)。
  `http_proxy` / `https_proxy` を `http://10.120.96.1:8080` に設定すると rc=0 で、
  返る SHA が policy の pin と一致する (request 951181)。
  **環境 runbook がこの節を「git clone / CMake FetchContent / pip が proxy を honor するかは
  未確認」と記していた点のうち、git については honor すると実測できた。**
  FetchContent 経由でも通ることを本走で確認した。
- **計算ノードに gflags / glog は無い。** pinned source と gcc/g++/cmake と `/scr` は在る
  (request 950299)。`/scr/$USER` は書ける (空き 5.4TB)。`/usr/bin/python3.10` 実在。
  `TMPDIR` は未設定。
- **汎用投入の子に `PBS_JOBID` は渡らない。** `USER` は渡る。cwd は repo root。
- **legacy build 経路は offline では通らない。** `buildcache.build()` の configure argv は
  `FETCHCONTENT_SOURCE_DIR_*` を渡さない。渡せるのは `build_v2` だけで、その docstring は
  legacy caller を従来 namespace に隔離する境界を明示している。境界を跨ぐ移行は設計判断なので
  この wave では行わず、proxy 経由で通した。

## 7. 参考値 (最終成果物ではない)

本走 2 回目 (request 951195、patch 未適用の build) で無 backoff 点だけが測れている。

```
backoff=0us  tps=4,034,148  abort=66.8%  spin_cyc=0.0%  total_ipc=1.946  useful_ipc=1.946
```

最終成果物の同点 (4,044,953 / 66.9% / 1.933) と近いが、**診断ノブが効いていない build の値**
なので成果物には採らない。参考として残す。生 log は wave の job dir に退避してある。

## 8. 計測に到達するまでに塞いだ欠陥

本走は 6 回投入し、5 回は値が出る前に検査が止めた。**5 時間枠は 1 度も浪費していない**
(最長 241 秒)。止まった理由と、それぞれが防いだもの:

1. 依存ライブラリの取得が offline で失敗 → proxy 経由で解決。
2. **要求した build define が黙って無視されていた** (下記 9)。
3. 正例検査が存在しない場所を見に行っていた (build cache は binary だけを publish し、
   CMake の中間ツリーは残らない) → 実在する成果物を見る形へ張り直し。
4. symbol 検査の適用範囲が広すぎた (無 backoff 点では呼び出しが消え、静的メンバ関数が
   未参照になるため emit されない。`noinline` は未参照の emit を強制しない) → 適用範囲を
   backoff 有効点だけに限定。
5. job token をスケジューラ変数から取っていたが、汎用投入の子には渡らない → argv 経由へ。

## 9. 最大の発見: 要求した build define が黙って無視されうる

`BACKOFF_FIXED` と `BACKOFF_NOINLINE` は ccbench 本体に存在せず、template patch が供給する。
この driver は patch を適用していなかった。**CMake は未定義の define を黙って無視する**ので、
backoff 有効点では要求した静的量が無視され、`BACK_OFF=1` だけが効いて stock の適応 backoff で
測ることになる。6 点すべてが同じ条件になる。

gate (perf report に対象 symbol が出ることの要求) が偽の成果物を止めた。詳細と、
異なる producer での独立再現、族一般化の裁定案は failures 台帳の該当 F に書いた。

対処は 2 つで、**後者が本体**である。

- 計測全体を `patchharness.applied()` の内側で行う。
- **要求した define が実際に効いたことを build 側の実体で確かめる。**
  この走では 7 点の binary hash が 7/7 相異なることを、計測を 1 点も始める前に検査した。
  無視されていれば静的量を持つ全点が同一 binary になる。
