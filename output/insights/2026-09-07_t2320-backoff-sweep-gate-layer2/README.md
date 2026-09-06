# [T-2320] backoff_sweep 経路の条件関門 第 2 層 (masstree `config.h` 不在) を A-2 と同じ形で直し、A-5 と T-2266 tail を実測した

- 日付: 2026-09-07 (wave 開始 2026-09-05)
- wave: `worktree-dev-wave-t2320-backoff-sweep-gate-layer2`
- 実装 commit: `0ade09d5e` (第 2 層の修正、Codex author、8 file) と `2177b85aa`
  (T-2266 report 生成の欠陥、Codex author、2 file)。main 取り込み `28c60d344` (固定 SHA `46b387dc2`)
- authority: **A-5 の性能値は含むが、A-5 は D1525 に従い未充足のままである。** T-2266 tail の
  rep 単位値の正本は `output/insights/2026-09-04_t2266-backoff-static-tail/README.md` §8 (本 wave が追記)。
- 一次資料: `output/insights/2026-09-04_t2211-a5-second-boot-resubmit/README.md`、
  `output/insights/2026-09-02_a2-condition-gate-patched-root/README.md`

## 0. 要点

1. **修正は効いた。** 修正前は A-5 6 job + T-2266 tail 3 job が全件 `BACKOFF_FIXED=red/preprocess-failed`
   (第 2 層) で止まっていた。修正後は生死確認 (計算ノード) と実 job 5 本 (A-5 2 + T-2266 3) の全部で
   関門を通過し、build → 検証 (全 genome serializable) → 計測まで進んだ。
2. **第 3 層 (D1611 の差分分類) が backoff_sweep 経路で初めて実測された。** inert 比較 (`BACKOFF_FIXED=-1`)
   は `stock-inert-preprocess-root-location-only` の緑、他 6 値は `requested-default-preprocess-different`
   の緑。両 driver (A-5 の 7 値、T-2266 の 7 値) とも `admission.admitted = true`。
3. **A-5 は 2 job とも 8 genome 全部を計測したが、balanced job の rc は 1 である。** 理由は関門でも計測でも
   なく、同じ checkout から走らせた write-heavy job の終了処理 (`git worktree prune --expire now`) が、
   共有 submodule gitdir 上の他 job の worktree 登録を別ノードから消したこと (§5、F251 の再発)。
4. **T-2266 tail は 3 回投入して 3 回目で完走した。** 1 回目は上記 prune 衝突で 8 点中 6/6/4 点、
   2 回目は 8 点全部を計測したあと report 生成が driver 側の型不一致で必ず落ちる欠陥に当たり、
   3 回目 (修正 commit `2177b85aa` から投入) で 3 workload とも `status: complete` になった (§6)。
   **750 と 999 µs は初測定である。** rep 単位値の正本は
   `output/insights/2026-09-04_t2266-backoff-static-tail/README.md` §8 に追記した。
5. **A-5 は未充足のまま (D1525)。** 値が取れたことを充足と読み替えない。

## 1. 修正の内容 (commit `0ade09d5e`)

`orchestrator/campaign/backoff_sweep.py` の `_require_backoff_condition_gate` は
`capture_define_inputs(source_root, stock_root=stock_root)` を configure_args なしで呼んでいた。
関門の supply arm は configure だけを行い、CCBench が build 時 custom target (`masstree_build`) で
生成する masstree `config.h` が build tree に無いので、owner TU (`cc/silo/transaction.cc`) の preprocess が
落ちていた。

- helper に keyword-only `configure_args: Sequence[str] = ()` を足し `capture_define_inputs` へ素通しする。
  判定式・受理集合・既定値・stock 比較・meaning arm は不変。
- `backoff_sweep.run_workload` と `backoff_extended_sweep.run_workload` (A-5 job と B-10 job
  `--run-kind t2266-tail` の 2 経路) で、patched root を canonical 化し、一時 base
  (`tempfile.TemporaryDirectory(prefix="izanagi-backoff-condition-gate-")`) で
  `buildcache.prepare_masstree_fetchcontent(ccbench_dir=<canonical root>, fetchcontent_base_dir=<base>,
  expected_toolchain_manifest, configure_timeout_s=900, target_timeout_s=900, site)` を 1 度呼び、
  同じ base を `-DFETCHCONTENT_BASE_DIR=<base>` として関門へ渡す。一時 base は関門の直後に閉じる。
  **検査する木と build する木は同じ patched root** (A-2 の不変条件)。
- 他 4 呼び手 (`backoff_overthrottle` / `backoff_profile` / `backoff_requested_us` / `backoff_repro`) は
  既定値で従来どおり。第 2 層は未修正のまま (本 wave の実測経路でない、裁定パッケージ §9)。
- test: 実 fixture で requested/control 両 configure argv に渡した引数が現れることを必須検査 (段 3 B MF-2)、
  prepare 1 回、exact 1 要素 tuple、prepare / 関門 / 後続 build / campaign の resolved root 一致、
  T-2266 経路の exact 7 値、event 順序。`run_workload` を end-to-end で走らせる consumer test は
  prepare だけ記録 stub にし本物の関門は維持。共有 fixture `supplied/CMakeLists.txt` は
  `FETCHCONTENT_BASE_DIR` を無害に参照する (未使用変数の CMake 警告が関門の `configure-failed` になるため)。

### 1.1 段 3 相談・段 6 レビューの裁定 (要旨。全文は job dir の `ruling.md` / `review-a.md` / `review-b.md`)

- A MF-1 (real、不採用・scope 外): 関門の一時 base の masstree `config.h` と後続 build の `config.h` は別物で、
  **compiler 入力の閉包までは一致しない。** 不変条件が指すのは patched **source 木**の一致であり、
  第三者生成 header の閉包 hash 束縛は新規 gate に当たる。A-2 経路も同じ限界を持つ。裁定パッケージへ。
- A SH-1 / SH-2 (real、記述): 関門 predicate の受理集合 (不変) と driver の実行前提 (prebuild 成功が加わる) を
  区別する。一時 base を含む record は再生不能な実行時観測である。
- B MF-1〜MF-3 (real、採用): login node は site gate で prepare を拒否するので生死確認は generic dispatch で
  計算ノードへ送る。生死確認は supply evaluator を直接呼び全 record を JSON で保存し、件数・`reason_code`・
  両 configure argv の `-DFETCHCONTENT_BASE_DIR` 一致 (exact 1 個、prepare の base と同一) を機械検査する。
- B MF-4 (real、運用で閉じる): B-10 job は投入元 tree の live tree で driver を走らせ HEAD を束縛しない。
  本 wave は固定 SHA の detached `submit-tree` から投入し、全 job 終了まで不変に保った (§7)。
  恒久修正 (expected HEAD + detached JOB_REPO) は裁定パッケージへ。
- 段 6 レビュー A = GO (should 2 件 → fix で closed)、B = NO-GO (must-fix は生死確認 script の検査強度、
  v2 で closed。production の指摘なし)。
- 焦点走 1 回目 682 緑 / 1 赤 (`test_screening_opt_in.py`、帰属 real: fixture が変数を消費せず CMake 警告)、
  fix 後 2 回目 1243 緑 / 12 skip / 赤 0 (23 file)。

## 2. 変異 matrix (事前登録 M1〜M7、`mutation/`)

`tools/mutation_harness.py` を直接使用 (`--runner-mode dispatch --detached`)。probe (全件 SURVIVED 期待で
観測 node 収集、2026-09-07 02:20〜02:25 JST) → 本走 (期待 node 完全一致、02:27〜02:31 JST)。

- baseline PASSED、**7/7 KILLED**、MISMATCH 0、SURVIVED 0、TIMEOUT 0、期待 node 10 件完全一致
- `repo_head` = `0ade09d5e3d1cde388876ce3b7c82351ae082344`
- 本走 spec sha256 = `e1efd6a08489c76cd260a29fd48d5abfa0150d5301bbecb1edcd323cf877e64f`
  (probe spec `9da91020c710a84961726795ae81ff078130e727c350d5e70e5dd6fa4488648f`)
- runner sha256 = `e2c8b34cfb8698501f5854037f1ab38766631f19f7611ea56960be18fae2a465`、
  tool sha256 = `c4b7f3cf951280f3633807228646fe8460d5fc99f172fc108e8d6c62d459f669`
- runner argv: `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_backoff_sweep.py
  orchestrator/tests/test_backoff_extended_sweep.py -q -rf -p no:cacheprovider`

| ID | 変異 | 事前登録の検出 test | 観測 (赤 node 数) |
|---|---|---|---|
| M1 | helper が `configure_args=` を落とす | `test_real_family_helper_admits_effective_define_and_recomputes_file_digest` | 1 (登録どおり) |
| M2 | sweep の prepare 呼び出し削除 | `test_run_workload_prepares_masstree_once_before_condition_gate` | 3 (登録 + 同一木 test + 順序 test、冗長 gate) |
| M3 | sweep の関門を `configure_args=()` に戻す | `test_run_workload_gates_the_prepared_patched_tree_with_fetchcontent_base` | 1 |
| M4 | sweep の関門第 1 引数を stock root へ | 同上 | 1 |
| M5 | extended wrapper の転送削除 | `test_extended_gate_wrapper_forwards_configure_args` | 1 |
| M6 | extended で関門を prepare の前へ | `test_mu13_run_path_uses_the_calibration_bound_records` | 1 |
| M7 | extended の prepare 呼び出し削除 | `test_extended_run_path_prepares_and_gates_the_same_patched_tree` | 2 (登録 + MU13 順序、冗長 gate) |

`DW-M03` に従い M2 / M7 の追加 node は冗長 gate として記録する (赤理由はそれぞれ 1 つ)。

## 3. 生死確認 (計算ノード、`liveness/`)

login node は `require_heavy_work_site` が prepare を拒否するので、`tools/pegasus/dispatch_compute.py --task generic`
で repo 外 script (`liveness/t2320_gate_liveness.py.txt`) を計算ノードへ送った。

| 回 | request | 結果 |
|---|---|---|
| 1 | 978710 | rc=16 `queue-wait-timeout` (infra、混雑)。`--queue-wait-timeout 3600 --overall-grace 600` を付けて再投入 |
| 2 | 978783 | bnode039、2026-09-05 22:34:36〜22:37:59 JST (208 秒)、`job_ready = true` |

2 回目の検査結果 (`liveness/liveness.json` の `check`):

- record 14 件 (A-5 の 7 値 + T-2266 の 7 値)、`preprocess-failed` 0 件、全件 green、driver_id 一致 14
- 両 configure argv (requested / control) に `-DFETCHCONTENT_BASE_DIR=<prepare の base>` が exact 1 個ずつ
- prepare 所要 20.2 秒 (B SH-1 の実測)。base 配下 `masstree-src/config.h` の sha256
  `e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a` は prepare 後と関門後で同一
- helper 本体 (`_require_backoff_condition_gate`) を A-5 値集合と T-2266 値集合で 1 回ずつ呼び、
  両方 `admitted = true`
- **第 3 層の初実測**: inert 比較 (`-1`) の supply arm は `stock-inert-preprocess-root-location-only` の緑
  (D1611 の「置き場所由来だけ」判定が backoff_sweep 経路で初めて発火した)。他 6 値は
  `requested-default-preprocess-different` の緑
- 一時 base を含む record は再生不能な実行時観測 (A SH-2)。`CMAKE_PREFIX_PATH=/work/1/SFC/tanab/izanagi-a2-deps`、
  proxy `http://10.120.96.1:8080` を script が自分で設定した

## 4. A-5 (D1100) の再投入 — 関門通過、8 genome 全部を計測、balanced は終了処理で rc=1

```
bash tools/pegasus/submit_a5_second_boot_backoff_sweep.sh \
  --output-parent /work/1/SFC/tanab/a5-second-boot-runs
```

投入 2026-09-07 02:19:22 JST、group `a5-second-boot-backoff-sweep-20260906T171922Z-31812`、投入元は
detached `submit-tree` (`0ade09d5e`、clean)。job が照合した repository commit = `0ade09d5e…`、
CCBench gitlink = `511c9538e4e8efa54b45cda62e72389ed3b706ec`。

| job | workload | ノード | boot ID | 開始 | 終了 | Elapse | rc | committed |
|---|---|---|---|---|---|---:|---:|---|
| 979578 | write-heavy | bnode059 | f7ef6917-4ab2-4197-b582-a45b20d1a4d4 | 02:19:30 | 02:31:24 | 718 秒 | 0 | 8/8 |
| 979579 | balanced | bnode061 | f954c43c-4400-4845-9321-6f318b6fc3a3 | 02:19:30 | 02:31:26 | 721 秒 | 1 | 8/8 |

- 関門通過の証拠: 両 job の campaign WAL の先頭 `build_start` が 02:20:30 JST にある (関門は build の前で
  raise するので、WAL に build が現れた時点で関門は通過している)。前回までの 6 job は WAL が空だった。
  driver は成功時に関門 record を stdout へ出さないので、record の逐語は §3 の生死確認が担う。
- 全 genome の verify は serializable (anomaly 0)。
- balanced の rc=1 は 8 genome の commit 後、`patchharness.checkout` の終了処理で
  `git checkout -- .` / `git worktree list` が rc=128 (`fatal: not a git repository:
  …/.git/worktrees/submit-tree2/modules/external/ccbench/worktrees/ccbench`) になったもの (§5)。
  `failure.json` は `stage=backoff_sweep`, `returncode=1`, `campaign_wals[0].last_terminal = commit`。
- WAL sha256: write-heavy `6b8000a33b78d3eed8c4f43f9f3c678e49c5ba971ab29621ddc2632397e500d1`
  (`campaigns/backoff-sweep-silo-write-heavy-sweep-8e82cd3f/runs/wal.jsonl`)、
  balanced `12c02f4b5145af766cd78fbfd6aca8e4db8c8b680673b79c7b5cf9ffdc7931d6`
  (`campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/runs/wal.jsonl`)。原本は repo 外、
  stdout / stderr / failure.json / reservation.json / submit receipt の写しを `a5/` に置いた。

### 4.1 取れた値 (median tps、5 rep、48 thread)

| backoff | write-heavy | balanced |
|---|---:|---:|
| none (`-1`, BACK_OFF=0) | 2,368,703 (CV 2.83%) | 3,803,883 (CV 3.30%) |
| adaptive (`-1`, BACK_OFF=1) | 1,377,645 (CV 0.92%) | 1,255,276 (CV 1.80%) |
| fixed 2 µs | 3,436,569 (CV 2.98%) | 4,394,479 (CV 1.42%) |
| fixed 5 µs | 3,949,653 (CV 1.98%) | 4,294,095 (CV 1.19%) |
| fixed 10 µs | 3,925,215 (CV 1.03%) | 3,893,392 (CV 0.35%) |
| fixed 25 µs | 3,453,760 (CV 0.46%) | 3,082,384 (CV 0.27%) |
| fixed 50 µs | 2,914,145 (CV 0.26%) | 2,424,693 (CV 0.44%) |
| fixed 100 µs | 2,357,575 (CV 0.29%) | 1,862,067 (CV 0.34%) |

**充足の判定はしない。** D1525 (2026-09-03 ユーザー裁定) により、Pegasus で取れた結果を D1100 の
「別 boot の再現」と読み替えず、**A-5 は未充足のまま残す。** 上の値は「関門を通り切った後に driver が
出した値」であり、比較の相手 (D1100 の元 boot) との対応づけは本書の主張に含めない。

## 5. 失敗: 共有 gitdir への別ノードからの `git worktree prune` が並走 job を落とした (F251 の再発)

- 事象: 02:31:24 に A-5 write-heavy (979578) が正常終了し、終了処理
  (`tools/pegasus/a5_second_boot_backoff_sweep.sh` の cleanup) が `git -C "$CCBENCH_BASE" worktree prune
  --expire now` を打った (`env/worktree-remove.rc`: remove 0 / prune_rc=0)。02:31:26〜02:31:29 に、同じ
  `submit-tree` から走っていた A-5 balanced (979579) と T-2266 tail 3 job (979596 / 979598 / 979599) が
  同時に `git status` / `git worktree list` rc=128 で落ちた。
- 機構: 各 job は ccbench の scratch worktree を **ノードローカル `/scr/<jobid>-…/`** に作り、その管理 dir は
  投入元 checkout の submodule gitdir (`…/.git/worktrees/submit-tree2/modules/external/ccbench/worktrees/`)
  に置かれる (5 job が共有)。別ノードから見ると他 job の `/scr` path は存在しないので、prune は
  他 job の登録を「消えた worktree」として削除する。以後、その job の git 呼び出しは
  `fatal: not a git repository` になる。
- 型: F251 (走行中の worktree が掃除の生存判定をすり抜けて削除される) の再発。掃除主体が並行 session でなく
  **兄弟 job の終了処理**である点と、消えたのが worktree 本体でなく**別ノードにある worktree の登録**である
  点が新しい。A-5 job 本体の prune は `output/insights/2026-09-02_t2205-a5-second-boot-measurement-job/README.md`
  の「失敗・強制 timeout 時に prune が無かった。追加」に由来し、**同じ checkout から 2 job を出す投入器と
  組み合わさると、後に終わる job が必ず落ちる構造**になっている (09-02 / 09-04 は関門で先に落ちたので顕在化
  しなかった)。
- 本 wave の対処: T-2266 tail は A-5 job が無い状態で同じ submit-tree から再投入 (§6、先例 runs5 と同じ
  3 job 構成。B-10 job の終了処理は自 path への `worktree remove --force` だけで prune を打たない)。
  A-5 は再投入しない — 8 genome の計測と検証は 2 job とも完了しており、再投入しても同じ構造で後着 job が
  落ち、D1525 により充足の判定も変わらない。
- 恒久対応は裁定パッケージ (§9): A-5 投入器を workload ごとの checkout に分けるか、job 本体の prune を
  自 path の `worktree remove` に限定するか。いずれも `tools/pegasus/admission_registry.json` の登録簿と
  F660 に触れる。

## 6. T-2266 tail (8 点格子 x 3 workload) の再投入

```
bash tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2266-tail \
  --output-parent /work/1/SFC/tanab/b10-backoff-grid-runs6
```

### 6.1 1 回目 (02:21:51 JST 投入、group `b10-backoff-grid-20260906T172151Z-81318`) — §5 の prune に巻き込まれた

| job | workload | 終了 | Elapse | committed / aborted | 落ちた点 |
|---|---|---|---:|---|---|
| 979596 | write-heavy | 02:31:29 | 574 秒 | 6 / 2 | 500, 750 (order の末尾 2 点) |
| 979598 | balanced | 02:31:29 | — | 6 / 2 | order の末尾 2 点 |
| 979599 | read-heavy | 02:31:28 | 506 秒 | 4 / 4 | order の末尾 4 点 |

abort 理由はすべて `identity-error` (`source_digest: git status 失敗 rc=128`)。関門は 3 job とも通過し、
commit 済みの点は全部 serializable。`reports/` は空、`completion.json` 無し。**この回の値は正本に使わない**
(不完全な格子であり、2 回目が同一 job 内で 8 点を揃える)。

### 6.2 2 回目 (02:36:02 JST 投入、group `b10-backoff-grid-20260906T173602Z-433694`) — 8 点計測後に report 生成が落ちた

投入元は同じ `submit-tree` (`0ade09d5e`、clean)。この tree から他の job は走らせていない。
job は 979703 (write-heavy) / 979704 (balanced) / 979705 (read-heavy)、02:36:55〜02:47:09 JST、Elapse 638〜639 秒。

**3 job とも 8 点全部を build → verify (serializable) → bench → commit した** (`done: 8 committed / 0 aborted`)。
その直後の `materialize_t2266_report` が `RuntimeError: T-2266 adopted bench round lacks rep capture` を上げ、
rc=1、`reports/` は空、`completion.json` 無し。3 job で同一の決定的失敗である。
**`t2266-tail` mode が report 段へ到達した実走はこれが初めてだった** (09-04 の 3 job は関門で止まっていた)。

原因は driver 側の型不一致である。

- `_load_t2266_report_points` は `require_certified_campaign_view` で campaign を読み戻す。
  `artifact_admission._deep_immutable` が WAL payload の `list` を `tuple`、`dict` を `MappingProxyType`
  に変換する。
- `_T2266RepCapture.reps_for` は capture 側の `list` と view 側の `tuple` を `==` で突合していた。
  Python では `[1, 2] == (1, 2)` は False なので**必ず**不一致になる。
- 続く `leading_indicators` の `type(indicators) is not dict` 検査も `MappingProxyType` を拒否する
  (突合だけ直しても次でここに落ちる)。
- unit test は `ImmutableWalRecord` を list / dict の payload のまま手組みしており `_deep_immutable` を
  通らないので、この欠陥が見えなかった。

これは仮想リスクではなく、依頼 (b) の rep 単位値がこの report 経由でしか得られない
(rep ごとの abort 率は driver process の memory にしかなく WAL に残らない) ため、修正を scope 内と裁定した
(裁定の全文は job dir の `ruling-addendum-1.md`)。

### 6.3 修正 (commit `2177b85aa`、Codex author)

- `reps_for` の突合は exact `list` / `tuple` だけを tuple 化して比較する。`run_cmd` の完全一致、
  5 rep の throughput 列の完全一致、複数一致時の ambiguity 検査は不変。
- `leading_indicators` は exact `dict` と `MappingProxyType` を受理する。他の型は拒否のまま。
- **受理集合は広げていない。** 全 8 点・全 5 rep・正で有限な throughput・0 以上 1 以下の abort 率・
  correctness verified・create-only・`allow_nan=False` はいずれも不変。`MappingProxyType` は report
  document に残さず、取り出した scalar だけを書くので JSON 直列化にも影響しない。
- test は fixture の WAL record を `_immutable_records` に通して実走と同じ凍結型にし、tuple と
  `MappingProxyType` であること、`materialize_t2266_report` が JSON / `.dat` を生成して
  `throughput_tps_reps` / `abort_rate_reps` が capture 値と一致することを検査する。
- 敵対レビュー 2 本 (受理集合の不変性 / 実効性) はいずれも **GO、must-fix なし**。焦点走 74 緑 (rc=0)。
- レビュー A の should: 負例を parametrized test で固定すると将来の受理集合拡大を直接検出できる
  (現状も `run_cmd` 不一致・順序変更・4 rep・非有限値・abort 率範囲外・未検証点・7 点は行番号付きで
  拒否経路が確認されている)。本 wave の依頼は仮想リスク向けの gate 追加を scope 外としているので入れない。
- レビュー B の should: 再測定ラウンドが複数になる入力の代表 test と、`p2_2.REPS == 5` の literal gate。
  同上の理由で入れない。**注意点として記録**: rep 値は driver process の memory にしかないので、
  既存 commit を skip する resume 入力では capture が空になり同じ失敗が再現する。新しい output root で
  8 点を実測し直す限り該当しない。

### 6.4 3 回目 (03:17:18 JST 投入、group `b10-backoff-grid-20260906T181718Z-1158057`) — 完走

投入元は修正 commit `2177b85aa8cf1877f11be3e0adf6e4c8751646c6` の新しい detached worktree
(`submit-tree-fix`、clean、submodule 初期化済み)。この tree からは他の job を走らせていない。

| job | workload | 開始 | 終了 | Elapse | 結果 |
|---|---|---|---|---:|---|
| 979843 | write-heavy | 03:17:26 | 03:27:54 | 632 秒 | complete、8 点 |
| 979844 | balanced | 03:17:26 | 03:27:53 | 631 秒 | complete、8 点 |
| 979845 | read-heavy | 03:17:26 | 03:27:50 | 629 秒 | complete、8 点 |

3 job とも `completion.json` が `status: complete`。report JSON の sha256 は write-heavy
`d462e146b8b5d1fa804556225facd27f0d49975c81622c9922766f92170caada`、balanced
`5ad6f095cfca3477d5668f582deec9e240ad1c69b0b760f46a758e1e8e3d9ecf`、read-heavy
`66bc31956766b030e54add0788b50d9409647b7454a7d79557abc7affef40da0`。
**rep 単位の throughput と abort 率を含む値の正本は
`output/insights/2026-09-04_t2266-backoff-static-tail/README.md` §8** で、本 wave がそこへ追記した。
写しは本 directory の `t2266-tail/` に置いた。

要点だけ再掲する。750 と 999 µs は本測定が初出で、静的 tail は 3 workload とも 150 → 999 で
throughput・abort 率ともに単調に下がり、谷は無い。既測 4 点は §1 の値と 0.5% 以内で一致する。
1000 µs は F718 により依然測定不能で、999 は代替であって 6 点目ではない。

## 7. B MF-4 の運用制約の記録

- 投入元は 2 本の detached worktree。`submit-tree` =
  `0ade09d5e3d1cde388876ce3b7c82351ae082344` (A-5 と T-2266 の 1・2 回目)、`submit-tree-fix` =
  `2177b85aa8cf1877f11be3e0adf6e4c8751646c6` (T-2266 3 回目)。いずれも submodule 初期化済み。
- 投入時 (A-5 02:19、T-2266 02:21 / 02:36 / 03:17) の `git rev-parse HEAD` は各 tree の上記 SHA と一致し、
  `git status --porcelain --untracked-files=no` は空 (job dir の `submit-*.head` / `submit-*.status`)。
- wave worktree 側の記録 commit と main 取り込み (`28c60d344`) は submit-tree に影響しない (別 checkout)。

## 8. 確定していないこと・限界

- A MF-1: 関門が見た masstree `config.h` (一時 base) と計測 build が使う `config.h` (buildcache) は
  同じ pin・同じ toolchain から生成されるが、bytes の同一性は束縛していない。A-2 経路も同じ。
- 関門 record は driver の成功経路では保存されない。実 job での第 3 層通過は「関門が raise せず build が
  始まった」ことからの帰結であり、record の逐語は生死確認 (§3) にしかない。
- A-5 の値は 2 boot (bnode059 / bnode061) で取れたが、D1525 により充足と読まない。
- すべて単一環境 (Pegasus、48 物理コア)。

## 9. 裁定パッケージ (ユーザーへ返す、本 wave では実装しない)

1. (A MF-1) 条件関門と測定 build の compiler 入力閉包 (第三者生成 header) を束縛するか。A-2 経路も同じ限界。
2. (B MF-4) B-10 job body に expected HEAD の照合と detached JOB_REPO を入れるか (A-5 と同形。登録簿と F660)。
3. 他 4 呼び手 (`backoff_overthrottle` / `backoff_profile` / `backoff_requested_us` / `backoff_repro`) に
   同じ prebuild を入れるか (実測経路になった時点で)。
4. (§5) A-5 投入器の 2 job を checkout ごとに分けるか、job 本体の `worktree prune` を自 path の remove に
   限定するか。B-10 3 job も同じ gitdir を共有しており、remove が失敗した job が prune へ落ちれば同型が起きる。

## 10. 時系列と工数

- 09-05: brief 12:49、plan 13:04、相談 A/B 13:14 / 13:17 (B は必読 refs 不在で 1 回やり直し)、
  ユーザー go 待ち → author 20:31→20:42 (642 秒)、review A/B 20:54 / 20:55、焦点走 1 回目 21:00、
  fix 21:05〜、焦点走 2 回目、統合 commit、生死確認 1 回目 (rc=16) → 2 回目 22:34〜22:38。
- 09-07 (session 再開 02:17): A-5 投入 02:19、変異 probe 02:20〜02:25、T-2266 1 回目 02:21、
  変異本走 02:27〜02:31、A-5 / T-2266 1 回目終了 02:31、main 取り込み 02:32、T-2266 2 回目 02:36〜02:47、
  補遺 1 裁定 03:00、author-2 03:01〜03:08、レビュー 2 本 03:08〜03:12、焦点走 3 (74 緑)、
  commit `2177b85aa` 03:15、T-2266 3 回目 03:17〜03:28、M8 / M9 変異走。
- 裁定した実行順 (変異 → 生死確認 → A-5 → T-2266) からの逸脱 (DW-O12 の記録): (1) 生死確認を変異より先に、
  (2) A-5 と変異 probe を並行に、(3) T-2266 1 回目を A-5 走行中に投入した。(3) が §5 の衝突を招いた。
  (4) 段 6 を終えた後に段 5・6 をもう 1 巡した (補遺 1 の裁定 → author → レビュー 2 本 → 焦点走 → commit)。
  実走で初めて露出した決定的欠陥が依頼 (b) の成果物を塞いでいたためで、裁定と経緯は job dir の
  `ruling-addendum-1.md` にある。
