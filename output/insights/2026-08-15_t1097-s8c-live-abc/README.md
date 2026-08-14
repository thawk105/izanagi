# 2026-08-15 段 8 主経路 (1) — 8c A/B/C live pilot を計算ノードで起動し、受理 gate 2 件で止まった

`docs/phase3.md` 段 8 の「次の主経路は (1) A/B/C を 1 generation だけ single-tenant
live build/legacy+S2/bench で operational pilot」を実走しようとした記録である。

**これは operational evidence であり、workload-conditioned synthesis の科学的主張ではない。**
A=rr50 / B=rr95 は既知点、C=rr100 は read-only の negative control で、
descriptor-on だけの rationale 差は因果証拠にならない。今回は role 呼び出しに 1 件も到達して
いないため、そもそも合成に関する主張は何も生じていない。

## 0. 結論

**live 実走は成立しなかった。** 止めたのは環境でも [T-1094] でもなく、repo 内の受理 gate 2 件である。

1. **D122 の transport 受理条件 (ii) が実機の `PBS_JOBID` を必ず弾く。**
   `--allow-pegasus-compute-transport` は計算ノードで原理的に通らない。
   8c live build の唯一の sanctioned 経路が到達不能である。
2. **完全性検査の閉じた event 集合に producer が書く `transport-admission-error` が無い。**
   その結果 `report.json` が 1 byte も書かれず、失敗の全件記録が失敗経路で失われる。

(1) の修正は D122 が D96 手続で確立した fail-closed 受理集合の変更にあたるため、
**親は緩めずユーザー裁定へ返す** (規律 2、`DW-S04`)。§5 が裁定パッケージである。

## 1. 経路の確定 (実測)

| 問い | 実測 |
|---|---|
| login node で live build できるか | 不可。`_assert_build_site_opted_in` が `8c の build は未受理 site='PEGASUS_LOGIN' では実行できない` |
| campaign を計算ノードへ dispatch できるか | 不可。`tools/pegasus/dispatch_compute.py --task` は `{tests, provenance}` のみ ([T-236] は凍結のまま) |
| 残る経路 | supervisor ごと計算ノードで走らせ、D122 の `--allow-pegasus-compute-transport` を明示する 1 本だけ |
| live build に要る flag | `--allow-coder-derived-build` も必須 (CLI 実測) |

これは archive worklog (102) の [T-276] 裁定
「(a) 維持は live pilot に [T-236] の凍結解除を要求するため実験を遠ざける」という意図と一致する。
`docs/phase3-s8c-autonomous-trial-runbook.md` §3.3 の起動例はこの 2 flag をどちらも欠き、
かつ「[T-276] / [T-277] の裁定済み項目待ち」という 2026-08-02 に解消済みの前提を今も書いている。

## 2. 計算ノードの前提実測 (request 911096 / 911104, bnode021)

| 項目 | 実測値 |
|---|---|
| `buildcache._resolve_site()` | `PEGASUS_COMPUTE` |
| `_site_admits_measurement` | `True` |
| `numactl` | `/bin/numactl` (S2 verify の interleave 前提を満たす) |
| toolchain | gcc/g++ 11.4.0、cmake 3.25.0、`default_build_jobs = 48` |
| ccbench HEAD | `511c9538e4e8efa54b45cda62e72389ed3b706ec` (= PIN `511c953`) |
| 従量経路 env 5 key | すべて不在 |
| proxy | lowercase 2 key のみ (`http_proxy` = `https_proxy` = `http://10.120.96.1:8080`) |
| `claude` CLI | `/home/SFC/tanab/.local/bin/claude` 実在 |

逐語 = `verbatim/preflight-911096.json`、`verbatim/preflight-911104.json`。

## 3. [T-1094] は 8c live build 経路では発火しない (新しい実測事実)

`docs/pegasus-runbook.md` は「git clone / CMake FetchContent / pip が proxy を honor するかは
command・ノード・profile ごとに**未確定**」と明記していた。計算ノードで測った。

- **第 1 走 (911096)**: `dependency_prefix` を空にしたため configure は 0.655 秒で rc=1。
  落ちたのは FetchContent ではなく `find_package(gflags)` (`external/ccbench/CMakeLists.txt:33`)。
  `_deps` は 0 件で、**FetchContent の可否はこの走では測れていない**。
- **第 2 走 (911104)**: production の `dependency_prefix` seam へ gflags/glog の install prefix を
  渡して再測。**configure rc=0、8.357 秒**。`_deps` に `masstree-{src,build,subbuild}` /
  `mimalloc-*` / `googletest-*` の 9 entry が生成され、`masstree-src` の HEAD は pin と同じ
  `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`、実体は 3.3M / 11M / 20M。

結論: **計算ノードの FetchContent は proxy 経由で通る。** [T-1094] が床値経路を止めているかは
本 wave の scope 外であり、ここで反証したのは「計算ノードでは FetchContent が原理的に通らない」
という一般化の方だけである。

模擬と実の差 (F29): probe は `buildcache._v2_commands` が組み立てる production の configure argv を
そのまま実行したが、`build_v2` の cache / staging / admission / identity 機構は通していない。
また stock tree に対して測ったため `CCBENCH_BACKOFF_TRIGGER_GATING` は「未使用変数」警告になる
(本走では patchharness が骨格 patch を当ててから build する)。FetchContent の発火は configure 時
かつ genome define と独立なのでこの差は上の結論に影響しないが、**「build 全体が通る」証拠には
ならない** — 本走が role 呼び出し前に止まったため、build leg は今も未実証である。

## 4. 本走 (request 911106, bnode021, 2026-08-15 07:53 JST)

job script は計測前に fail-closed で次を確かめてから supervisor を起動した — 競合 `ycsb_*.exe` の
不在 (`NONE`)、`numactl` 実在、`claude` CLI 実在、`policy.json` の
`gflags_expected_head` / `glog_expected_head` と source HEAD の一致、そして
`tools/pegasus/floor_campaign.sh:810-925` を逐語再利用した gflags/glog の build/install と
`CMAKE_PREFIX_PATH` の export。単独性は tanab 7 process + system daemon のみで、競合 bench は無い。

依存 staging は全段 rc=0 で通り、supervisor は起動した。journal (`verbatim/attempts.jsonl`) は
3 event で終わっている。

```
seq=1  transport-admission-error  pbs-jobid-invalid: PBS_JOBID witness の syntax が不正
seq=2  run-start                  do_build=true, workloads=[ycsb-a,ycsb-b,ycsb-c],
                                  generation_budget_per_workload=1, performance_early_stop=false,
                                  scientific_claim=false, certifying=false
seq=3  run-finish                 status=partial, report=<run-root>/report.json
```

**role attempt は 0 件。** よって planner / coder / auditor / critic は 1 度も呼ばれておらず、
LLM 費用も descriptor 射影も発生していない。

### 4.1 欠陥 1 — D122 受理条件 (ii) は実機で充足不能

```
orchestrator/campaign/claude_transport.py:61
    PBS_JOBID_PATTERN = r"[A-Za-z0-9][A-Za-z0-9._-]*"     # ':' を含まない
実機 (bnode021)
    PBS_JOBID = 0:911106.nqsv                              # 先頭に job index "0:"
```

この pattern は `orchestrator/qualification/qsub_binding.py:14` の `_JOB_ID_TEXT` と
byte 一致で pin されている。しかし `_JOB_ID_TEXT` は **qsub が印字する request ID**
(`911106.nqsv`) の文法であって、**環境変数 `PBS_JOBID`** の文法ではない。NQSV は
`<job index>:<request id>` を渡す。

**repo 自身がこの差を既に知っている**のが決め手である。
`orchestrator/tests/test_claude_transport.py:335` は
`COLLECTOR._JOB_ID.pattern == rf"(?:0:)?{T.PBS_JOBID_PATTERN}"` を pin し、
同じテストの負例集合が `"job:id"` を invalid と主張している。
collector 側は `0:` 接頭辞を明示的に許し、transport 側は許さない。
**受理条件 (ii) は、実機で満たせる値が存在しない gate になっている。**

D122 段 1 の前提実測 (request `877155`、bnode009) は proxy key の集合と `claude -p` の rc を
測ったが、**`is_valid_pbs_jobid` を実機の `PBS_JOBID` へ通す end-to-end は測っていない**。
これが裁定時の未見事実である。

### 4.2 欠陥 2 — 完全性検査が失敗経路の記録を落とす

```
producer:  orchestrator/campaign/p3_autonomous_workload_trial.py:2442
           journal へ {"event": "transport-admission-error", ...} を書く
consumer:  orchestrator/campaign/autonomous_trial_completeness.py:34-42
           _EVENTS = {transport-admission, run-start, role-attempt, supervisor-error,
                      supervisor-wall-budget, provider-init-error, run-finish}
```

`_check_closed_events` が `unknown kind: 'transport-admission-error'` で
`AutonomousTrialCompletenessError` を投げるのは `_finish_trial` の中である。
そのため **`report.json` は書かれない** (実在しないことを確認済み)。
journal は `run-finish status=partial` と report path を既に記録しているので、
台帳と実 FS が食い違う。terminal report を出す機構が、それが最も要る失敗経路で自分を止めている。

これは「説明と実装の食い違い」ではなく **consumer 取り残し**である —
D122 決定 (5) は receipt を invalid attempt / provider-init 失敗 / supervisor-error /
wall-budget / run-finish へ載せると定めたが、admission が**失敗した**ときの event kind を
consumer の閉集合へ足す作業が抜けている。

## 5. 裁定パッケージ (ユーザー手番)

### 問 1 — `PBS_JOBID` 受理文法をどうするか

D122 決定 (2)(ii) の受理集合を変える。親は緩めない。

- **択 (a)**: transport 側の文法を `(?:0:)?<request-id>` (= collector と同形) へ拡げる。
  実機で唯一通る形。`is_valid_pbs_jobid` の負例集合 (`"job:id"` を invalid とする現行テスト) の
  更新を伴う。**colon を一般に許すのではなく、先頭 `0:` の job-index 接頭辞だけを許す**形にすれば
  受理集合の純増は 1 形だけに留まる。
- **択 (b)**: job script が `PBS_JOBID` から request ID を切り出して渡す。
  **これは gate を通すために gate が検査する env を書き換える行為であり、親は迂回と判定して推奨しない。**
- **択 (c)**: witness を `PBS_JOBID` から別の実在証拠 (例: `PBS_O_WORKDIR` + `qstat` 照合) へ替える。
  D122 決定 (7) は `PBS_JOBID` を「env 由来なので偽装可能な cheap witness であって attestation
  ではない」と既に明記しているので、強度は元から主張されていない。設計変更としては最も大きい。

**親の推奨は択 (a)。** 理由は 3 つ。(i) repo 内に既に `(?:0:)?` を許す consumer があり、
実機形はそちらが正しいと repo 自身が記録している。(ii) D122 決定 (7) が witness の強度を
attestation でないと明言しているので、`0:` を許しても防護の主張は 1 bit も減らない。
(iii) 択 (b) は規律違反、択 (c) は本 pilot と独立に大きい。

### 問 2 — 完全性検査の閉集合に `transport-admission-error` を足すか

- **択 (a)**: 足す。journal と report が失敗経路でも整合し、partial report が書かれるようになる。
  完全性検査の受理集合は「これまで拒否していた journal を受理する」方向へ広がるので D96 手続に乗る。
- **択 (b)**: producer 側を直し、admission 失敗を既存 kind (`provider-init-error`) で書く。
  event 語彙を増やさないが、診断語が丸められる。

**親の推奨は択 (a)。** 規律 3 (正しさシグナルを構造化して返す) に照らすと、
`transport-admission-error` は `provider-init-error` より具体的で、
なぜ止まったかを次の一手へ運べる。丸めると規律 3 の還流が狭くなる。

### 問 3 — 問 1 が解けた後、本 pilot をこの wave の外で走らせるか

問 1・問 2 の実装は受理集合の変更を含むため、実装子・変異 matrix・受入を伴う別 wave が要る。
その wave が終わってから live pilot を再投入する形を親は推奨する。
本 wave の job script (`live.pbs`) は repo 外の
`/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1097-s8c-live-abc/live/` に保全してあり、
依存 staging と単独性検査はそのまま再利用できる。

## 6. 本 wave が残さなかったもの (正直な会計)

- **build leg は未実証。** configure が通ることは測ったが、masstree の bootstrap/make を含む
  `ycsb_silo.exe` の完成、legacy+S2 verify、bench はいずれも走っていない。
- **role provenance は 0 件。** headless Claude の呼び出し、descriptor 射影、
  auditor gate、diff quarantine のいずれも今回は発火していない。
- **`report.json` が無いため、完全性検査の CLI 独立再検査も実行できていない。**
- 単独性は本走の起動時点で確認したが、**計測が無いので単独性は結果に効いていない。**
