# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。**何をやって・何が分かって・次に何をするか。**
git 履歴より粗く、roadmap / decisions より具体的な「作業の物語」。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

---

## 2026-06-17 — Phase 1 タスク0 着手 + Linux 計測層の確保

### 環境: Linux 実機が手に入った (D10 の「計測層」)

- ホスト `cygnus`: **Dell PowerEdge R760、ベアメタル** (`systemd-detect-virt=none`)、x86_64
- **96 論理CPU** (48 物理コア × 2SMT、2ソケット / 2 NUMA ノード)、247 GiB RAM、L3 約45 MiB/socket
- **perf が HW カウンタを取れる** (`LLC-load-misses` 実値、`perf_event_paranoid=-1`)
- toolchain: GCC 11.4 / clang 15、cmake 3.22、numactl、libnuma、jemalloc、boost 一式
- **意味:** CLAUDE.md / phase1.md が前提にしていた「Linux 未調達・Mac devcontainer のみ」が解消。
  [Linux] タスク (4b/5b/7) が解禁、calibrator の核心 (cache miss 飽和点) と性能計測がこのホストで動く。
  phase1 タスク0 の ARM / Apple Silicon 懸念は消滅 (ネイティブ x86_64)。
- **未反映 (要対応):** CLAUDE.md「現在地」と phase1.md の環境注記はまだ旧前提のまま。
  更新はユーザー確認の上で行う (CLAUDE.md は作業指示書なので慎重に)。

### タスク0: CCBench 解剖 (進行中)

- submodule 追加: `thawk105/ccbench @ 33d74a3` (tag `v1.1.0-117`)。**CMake 再構成版の v1 fork**
  (オリジナル CCBench を @jnmt の vldb-paper ブランチ等とマージしたもの)
- **ビルド成功** (`cmake -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF` + `make -j48`, GCC 11.4):
  **34 バイナリ**。docs が警告していた #44 (GCC11 vs CI の GCC13 で `-Werror=maybe-uninitialized` 不一致)
  は現 HEAD では修正済みで、GCC 11 でも警告ゼロで通った
- 初見の重要事実:
  - プロトコルは **10種** (`cicada d2pl ermia mocc mvto oze si silo ss2pl tictoc`)。roadmap の「7」は要更新
  - YCSB 対応は **7種** (`silo mocc cicada ermia tictoc oze si`)。`ss2pl/mvto` は TPC-C/BoMB のみ、`d2pl` は BoMB のみ
  - **フラグ二層構造:** ワークロードパラメータ = **ランタイム gflags** (`thread_num, ycsb_rratio, ycsb_tuple_num, ycsb_zipf_skew, ...`)、
    最適化 = **ビルド時 `-D` define** (`cmake/Options.cmake`: `NO_WAIT_LOCKING_IN_VALIDATION, INLINE_VERSION_PROMOTION,
    REUSE_VERSION, PREEMPTIVE_ABORTS, TEMPERATURE_RESET_OPT, WAL, ...`)。
    → パラメータ探索は roadmap §6 の予想どおり「ビルドし直し型」。ただし ccache で warm rebuild 約3秒
  - コンパイラ注記: 内部の variant↔baseline 比較は同一コンパイラ (GCC 11) で揃うので妥当。
    GCC 13 (CI) と揃える必要が出るのは CCBench 上流への還元時のみ
  - `silo/replay_test.exe` という再生テスト用バイナリあり (後で中身確認 — verifier 設計の参考になりうる)
- 詳細解剖を多エージェント・ワークフロー (6軸 + 高リスク2軸の敵対的検証、8エージェント/521k tok) で実施 →
  **`docs/ccbench-anatomy.md` を作成 (タスク0 完了条件を充足)。** YCSB `-help` スモークも実施。

### タスク0 で判明した「設計に効く」事実 (詳細は ccbench-anatomy.md)

- **protocol×workload ごとに別バイナリ (CMake)。最適化=ビルド時 `-D` (Options.cmake)、workload=runtime gflag。** パラメータ探索は全探索が現実的 (生フラグの boolean 超立方体 ≈ 258 binaries)
- **`si` = `ermia` から SSN を剥がした SI = 本物の write-skew (G2) を出す** → **タスク3「verifier が赤を出せる証明」の positive control。** `ermia`/`oze` は anti-dep を実体化する cross-check oracle
- **Silo の trace 3点 (read tidword / write / commit maxtid) は全て CC-native** → trace 専用フィールド不要。例外は `ss2pl` (producer-id が要る)
- **`#ifdef TRACE` の罠:** cmake が常に `-DTRACE=0` を出すと `#ifdef` 常真でコンパイルアウトされない → 観測者効果漏れ (絶対規律1違反)。**`#if TRACE` 方式 or 0 のとき `-D` を落とす** (`INSERT_*_DELAY_MS` に先例)。既存 `ADD_ANALYSIS` がほぼ完全な先例
- **スレッドピンニングが既定 OFF** (`-DLinux` 未定義) → 96スレ/2NUMA で scheduler 依存に。**`-DLinux` 追加 or `numactl` 必須 (絶対規律4)**
- **`clocks_per_us` は runtime gflag (default 2100、自動校正なし)。** tps は非依存だが backoff/epoch 実挙動は依存 → calibrator が TSC 実測して毎回渡す
- 死にフラグ (`NO_WAIT_OF_TICTOC`/`PARTITION_TABLE`/`PROCEDURE_SORT`) は探索から除外。CCBench doc 不整合 (protocols_en.md の YCSB 表) を `output/insights/` に記録 (還元待ち)

### 未コミット (git identity 設定後にまとめる)

`docs/ccbench-anatomy.md` / `output/insights/ccbench-protocols-doc-ycsb-mismatch.md` / 本 worklog 更新。
+ 既に保留中の commit A (submodule) / B (worklog 初版) も identity 設定後に切る。

### 進捗更新 (同日, タスク1 まで完了)

- ✅ doc 更新 (roadmap/CLAUDE.md/phase1/decisions D14) 適用・コミット済み
- ✅ ccache + gcc-13 (13.4.0) 導入、その toolchain で全ビルド確認 (CI=GCC13 一致)
- ✅ **タスク1 (trace-hook) 完了** — `patches/trace-hook.patch` で Silo に `#if TRACE` トレース。
  実証: trace の C 行数 = `commit_counts_` (327918)、非 genesis read の 100% が producer に matchable・ORPHAN 0・版重複 0、
  trace-disabled build に trace シンボル 0 (compile-out)、CC-native でフィールド追加なし。形式は `patches/README.md`。
  CCBench submodule は active dev 中は patch 適用状態 (gitlink は `33d74a3` のまま、parent には未ステージ)。

### 次の一手

1. **タスク2 (mini trace verifier, Python)** — trace から ww/wr/rw 辺の serialization graph を構築し G2 cycle 検出。
   構造化フィードバックを返す (絶対規律3)。`patches/README.md` の trace 形式が入力
2. タスク3 — `si` (SI=本物の write-skew G2) を verifier の positive control、`ermia` を negative にして検出力を実証
3. タスク4/5b 系 (計測) — calibrator で `clocks_per_us` 実測 + `-DLinux`/`numactl` ピンニング patch + cache miss 飽和点

---

## 2026-06-18 — Phase 1 タスク2 完了 (mini trace verifier + 敵対的検証)

### やったこと

- **verifier 実装** (`orchestrator/verifier/`, Python): `parse.py` (trace_*.log を txid で束ねる) →
  `dsg.py` (Adya DSG 構築 ww/wr/rw + iterative Tarjan SCC で cycle 検出 + G0/G1c/G2 分類 +
  witness 再構成) → `report.py` (構造化 JSON + 人間可読、絶対規律3) → `cli.py`/`verify.py` (複数 run=確率的検証)。
- **実トレース生成**: trace-enabled build (`build-trace`) で `ycsb_silo` を回し `output/runs/silo-sample`
  (184k txn / 1.63M 辺 / 66MB)。Silo なので**緑の地面**。verifier は 10.4s/950MB で certified serializable。
- **手製フィクスチャ + 単体テスト** (`orchestrator/tests/`): 緑4・赤3(G2)から開始 → 後述の昇格で計13、テスト15/15。
- **敵対的検証 workflow** (`verify-the-verifier`, 10 エージェント = 監査4レンズ + レッドチーム6班, 444k tok):
  最悪モード=false-green (本物の anomaly を serializable と誤認=絶対規律2 崩壊) を集中攻撃。

### workflow の結論 (極めて良好)

- **33 フィクスチャで verdict mismatch 0 / false-red 0。** コア DSG は正しい。
- Tarjan SCC を 2万+4万ランダムグラフで参照実装・独立 3-color DFS と照合 → 不一致ゼロ。
  6万トレース差分 fuzz で独立 Adya DSG 参照と照合 → false-green/red ゼロ。
  辺の向き・bisect_right・immediate-successor+ww 推移性・自己ループ抑制・深さ1万非再帰、全確認。
- **発見1 (定理):** realizable trace では ww/wr は必ず commit 順方向、逆走できるのは rw だけ →
  **全 cycle は必ず G2**。G0/G1c は構造的に出ない (`docs/isolation-phenomena.md` 新設、ユーザー質問に対応)。
- **発見2 (スコープ限界):** phantom/述語異常は trace 形式が述語読みを記録できず不可視。
  trace-hook の限界で dsg.py のバグではない (`output/insights/2026-06-18_phantom-predicate-out-of-scope.md`、還元不要)。

### 指摘 → 絶対規律2 の硬化 (実装済み)

指摘6件は全て単一テーマ: 判定が integrity を無視し、**malformed トレース** (実 Silo は出さない) で
辺が落ちて real cycle を隠す false-green が可能だった。修正:
- **FIX1:** integrity 不良 (orphan read / version dup / 重複 txid / 番兵 commit) なら `serializable` を
  主張せず **`indeterminate`** を返す。verdict を3値化、`certified` を「ゲート通過」の唯一信号に。
  CLI exit: 0=certified / 1=anomaly / 3=indeterminate / 2=parse error。`--lenient` で 3 を降格。
- **FIX2:** genesis を値 (1,0) でなく **producer 不在**で判定 → (1,0) commit の wr 辺を落とさない +
  (1,0) commit を非物理として integrity 違反に。
- 高価値の敵対トレース5本を committed fixture に昇格 (`r4_mixed`/`r5_nonlatest`/`m1_commit_at_genesis`/
  `m2_version_dup`/`p1_phantom_skew`) + 回帰テスト追加。

### 次の一手

1. **タスク3** — `si` (本物の write-skew G2) を positive control にして verifier の検出力を実機トレースで実証。
   現状 trace-hook は Silo のみ instrumented → `si` への trace-hook 拡張 (patch) が要る。`ermia`/`oze` を cross-check。
2. タスク4/5b 系 (計測) — calibrator (`clocks_per_us` 実測 + `-DLinux`/`numactl` ピンニング + cache miss 飽和点)。

---

## 2026-06-18 (続き) — Phase 1 タスク3 Approach A 完了 (verifier の赤検出を実証)

### やったこと: わざと壊した Silo で verifier が赤を出すことを実トレースで証明

- **壊し方:** Silo `validationPhase()` 条件#1 (read-set tidword 再検証 = anti-dependency / stale-read
  チェック) を macro `IZANAGI_BREAK_NOREAD_VALIDATION` で抜く。stale read が abort されず commit →
  lost-update / write-skew の G2 が trace に出る。`patches/broken-silo-norw-validation.patch` (既定 OFF、
  `#else` で元の abort が残る inert 設計。trace-hook patch の上に重ねる)。
- **clean ablation** (同一ワークロード `rmw,skew0.9,tuple50,ope5,thread4,extime1`、差は read validation のみ):
  - 壊し ON: 293,803 commit → **1310 G2 cycle** → verifier **NON-SERIALIZABLE (exit 1)**
  - 壊し OFF: 285,047 commit → verifier **certified SERIALIZABLE (exit 0)**
- witness は ww+wr+rw 混在の 2-cycle (lost-update)。**タスク3 完了条件「意図的なバグを verifier が
  捕まえられる・検出力の証拠が残る」を達成。** verifier が「常に緑のザル」でないことを実証。
- 壊しは macro-guard かつ patch 化済みなので submodule working tree は trace-hook のみのクリーン状態に復帰。

### Approach B (si=本物の write-skew G2) 完了 — real-CC positive control

より強い positive control = 無改変の `si` (SI、write-skew を admit) を赤にする real CC 実証。scout で
3 点を解決して実装した:
- **commit 点:** `cc/si/transaction.cc::si_commit()`。`cstamp = ++Lsn`、各 write 版に `ver_->cstamp_` を刻む。
- **版ID写像:** si 版ID = `cstamp` (単 uint) → `(epoch=1, tid=cstamp)` と emit。**初期版 cstamp=0** (`tuple.hh`)、
  実 txn は `++Lsn≥1` → 初期版 read が `(1,0)`=genesis に**自然一致** (衝突なし)。`patches/trace-hook-si.patch`。
- **workload:** `rmw=true` は read set=write set で ww 衝突 abort になり write-skew が出にくい →
  **`rmw=false`** で read/write を別キーに分離 + 高 contention で write-skew を誘発。
- **結果 (real-CC discrimination):** 同一 workload `rmw=false,rratio50,skew0.9,tuple30,ope10,thread8`:
  - `si` (SI): 171,037 commit → **3576 G2 cycle → NON-SERIALIZABLE**、integrity clean (版写像が正しい証拠)
  - `silo` (serializable OCC): 208,904 commit → **certified SERIALIZABLE**
  - 差は分離レベルのみ → verifier は workload や計装の副作用でなく**正しさそのもの**を見ている。
- **ermia cross-check の罠 (将来増分):** `ermia` (SSN on=green oracle) は版 cstamp が **`cstamp<<1`**
  (低ビット=SSN flag, `ssn_commit:561`) で si と違い、commit 経路も `ssn_commit`/`ssn_parallel_commit` の2系統。
  version id 写像をこの shift に合わせないと全 read が orphan 化する。si trace-hook はそのままでは流用不可。

タスク3 は2つの独立 ablation で実証完了: (A) 壊し Silo 赤 / 素 Silo 緑、(B) 本物 si 赤 / Silo 緑。

### 次の一手

1. (任意・強化) **ermia/oze の trace-hook** (`cstamp<<1` に注意) → `si`赤 / `ermia`緑 の同一エンジン ablation。
2. **タスク4/5b 系 (計測)** — calibrator (`clocks_per_us` 実測 + `-DLinux`/`numactl` ピンニング + cache miss 飽和点)。

---

## 2026-06-18 (続き) — Phase 1 タスク4 (calibrator) 実装 + 実機 calibration

### タスク4a: calibrator 純ロジック + モックテスト (機械非依存)

`orchestrator/calibrator/` を verifier と同型で実装。純ロジック (machine 非依存・
モックでテスト可): `perfparse` (perf stat CSV/人間可読/`<not counted>` → PerfCounters)、
`benchparse` (ccbench `label:\tvalue` → throughput[tps]/maxrss/actual_extime)、
`analyze` (飽和判定 / scale 感度 / noise floor CV)、`model`/`report` (env スコープ
文書化用 dataclass + text/JSON)。**飽和判定は tail-flat 要求で非単調系列に頑健**
(途中の noise dip で早すぎる plateau を誤採用しない、最終点は飽和確認不能なので除外)。
モック単体テスト (perf 3形式・飽和 早/遅/非単調/下限割れ/退化・下限基準・scale・noise)。

### タスク4b: 実機ドライバ + calibration (env=linux-baremetal)

- **`-DLinux` ピンニング patch** (`patches/linux-thread-pinning.patch`): `ccbench_add_protocol`
  が protocol target に `-DLinux` を渡さず**ワーカーが unpinned** だった (anatomy §7) のを
  microbench 先例どおり修正。実機で各ワーカーが CPU 単一ピンを確認 (絶対規律4)。D6 通り
  submodule に commit せず patches/ で保持。
- **実機ドライバ**: `tsc` (rdtscp×CLOCK_MONOTONIC で TSC 実測 = **1800 MHz**。Xeon 5418N の
  base。/proc の動的 2600 や CCBench default 2100 は誤り)、`runner` (perf stat -x, +
  numactl interleave で 1点を反復測定、maxrss 捕捉)、`sweep`/`cli` (倍々→飽和/下限→
  noise floor→scale を env スコープに書く)。
- **初回タイムアウトを診断・修正**: settle() が連続 run 間で毎回 30s 待ち空費 + 重い makeDB。
  → settle は campaign 冒頭1回のみ・閾値緩和、飽和/下限確定で**早期打ち切り**。孤児プロセス無し確認。

### 実機の発見 → D15 (飽和点が無い → 下限基準 / 飽和点は skew 依存)

**LLC miss 率が uniform も skew0.9 も飽和しなかった** (単調上昇)。原因は index=**masstree**:
N増で木が深化し内部ノードの cold miss が増え続け「膝」が出ない。含意2つ: ①飽和点は
skew (局所性) 依存 → calibration を (env, thread, **代表 workload**) でキー (D13 改訂)、
②「飽和せず→最大点」は規律4 と逆 (最も遅い run を選ぶ)。

→ **D15: 下限基準を追加**。飽和点が無ければ「working set (実測 maxrss) が L3 を K 倍
(既定4) 超える最小 N」を採る。詳細 `output/insights/2026-06-18_calibration-no-cache-miss-saturation.md`。

**確定 calibration (linux-baremetal, 48 thread, numactl interleave):**
- **skew=0.9 (contention, タスク1-3 と同帯)**: 下限基準で **records=1,000,000** (1m で
  maxrss 597MB = L3(90MB) の 6.6×、miss 20.4% で cache-bound)。**noise floor CV 2.28%**。
- **uniform (skew=0, 対照)**: 同じく下限基準で 1m (miss 14.9%)。**noise floor CV 0.47%**。
  (skew0.9 より低いのは hot key 競合の abort 揺らぎが無いため。両者とも専有機ゆえ <5%)
- 出力は workload 署名付き `output/env/linux-baremetal/calibration/calibration_t48_skew*.{json,md}`。

### submodule 改変の整理 (D16) — patch 一律運用をやめ性質ごとに分岐

calibration を機に「ccbench 改変の行き先」を再検討し、D6 (全て out-of-tree patch) を改訂:
- **pinning バグ修正** → submodule `master` に還元 (`7e268f2`)。Izanagi 非依存の本物の修正で、
  全 34 binary が gcc-13+`-Werror` クリーンビルド確認。`patches/linux-thread-pinning.patch` は削除。
- **trace-hook (Silo/si)** → submodule `izanagi-trace` ブランチ (`8b82d3e` Silo, `fee622f` si)。
  検証計装は protocol 横断で増えるので patch でなくブランチで持つ。`#if TRACE` ゆえ perf ビルドは
  観測者効果セーフ。`patches/trace-hook*.patch` は削除。
- **broken-silo** → `patches/` 死守 (わざと壊した CC は baseline 誤ビルド回避のため inert patch)。
  izanagi-trace 上にクリーン適用できることを確認。
- parent: gitlink を `fee622f` に前進、`.gitmodules` に `branch = izanagi-trace`、patches/README 全面改稿。
- **push は人間が行う** (この環境に ccbench への push 認証が無い + CLAUDE.md「勝手に上流 PR 出さない」)。
  要 push: `git -C external/ccbench push origin master` + `... push origin izanagi-trace`。

### 次の一手

1. **(直近) ccbench の master / izanagi-trace を push** (上記)。push 後 parent gitlink が他者にも解決可能に。
2. **タスク5a** — invisible reads on/off の正しさサニティ (両 trace 緑 + DB 状態一致)。
3. **タスク5b** — invisible reads の性能差を実機計測し論文 I2 と整合確認 + baseline 取得
   (確定した 1m/48thread/skew0.9 を使用)。
4. (任意) thread 数を変えた再 calibration / 下限基準 K の感度。

---

## 2026-06-19 — submodule push 反映 + Phase 1 タスク5 完了 (ultracode 開始)

### ccbench push 反映

ユーザーが ccbench master + izanagi-trace を push し、izanagi-trace の CI (clang-format) 修正
(`977e194`) を上に積んでくれた。submodule gitlink を `fee622f→977e194` に FF で前進
(修正は trace 出力の整形のみ・挙動不変・perf ビルドに影響なし)。**以降 ultracode を有効化**:
実質タスクは多エージェント workflow + 敵対的検証を既定にする。ただし**性能計測は単一テナント
直列が鉄則** (絶対規律4) なので、並列化するのは解析/検証/合成のみ、ベンチ実行は直列。

### タスク5a (正しさ側) 完了

既知最適化の on/off で正しさパイプラインが期待通り動くことを実トレースで実証。invisible reads は
silo 内在で toggle 不可・mocc は trace-hook 未実装のため、代表として **silo `BACK_OFF` (意味論保存)
を on/off** → 両方とも verifier が **certified SERIALIZABLE** (BACK_OFF=1: 277,391 txn / =0: 571,816 txn)。
観測者効果分離はタスク1 の symbol 不在が最強の構造的証明で、977e194 で再確認 (trace build に
izanagi_trace 6 / perf build に 0)。DB-dump semantic 等価性は symbol 不在より弱いので冗長と判断・未実装。

### タスク5b (性能側) 完了 — invisible reads の I2 を実測で裁定 (workflow)

invisible reads の効果を MOCC `temp_threshold` で実機計測 (1m/48thread/skew0.9, reps5)。
**3レンズ調査 + 敵対的裁定 workflow** (MOCC ソース / 論文 / データ, 4 エージェント 229k tok) +
perf カウンタで機構確認:
- **交絡を発見・確定:** `temp_threshold` は read だけでなく write/delete の lock() も gate する
  (`transaction.cc:361,468`)。`rratio=0` の最大倍率 1.733x は read op が0 で read-lock 不発 →
  invisible reads でなく **temperature-gated 悲観 write-locking** の効果。
- **クリーン点 = `rratio=100` (read-only):** invisible **1.28x** (9.32M vs 7.28M tps, CV 0.1%)。
  perf で visible が **+32% cache-misses/txn** = read-lock 語の cacheline bouncing 回避が機構と確認
  (dissent「帯域節約では?」を perf で解消)。
- **I2 訂正:** roadmap「read-heavy で効く」が正、**phase1「write-intensive」は誤帰属で訂正**。
  docs/phase1.md・anatomy §3 を訂正、`output/insights/2026-06-19_invisible-reads-i2-reconciliation.md`。

### baseline (Phase 2 用) + oze 病理

確定 calibration で YCSB 7 protocol の baseline 取得 (CV<1.5%):
**tictoc 1.05M / silo 902K / mocc 661K / cicada 605K / si 351K / ermia 327K tps**。
**oze だけ 81 tps / CV 53% = 病理。** skew0.9 で thread=1 でも 244 tps・thread48 で abort 99% livelock、
uniform は 122K で正常。機構 = read ごとの依存グラフ DFS (`is_invisible_dfs`) が密競合グラフで爆発
(`output/insights/2026-06-19_oze-skew-pathology.md`)。Phase 2 baseline で oze は uniform か除外。

### Phase 1 完了

タスク0-5 完了。**評価パイプライン (正しさ + 性能) が信頼できる状態に到達** = Phase 1 完了条件充足。
verifier が正しい CC を緑・壊れた CC を赤と判定し構造化フィードバックを返せ、calibrator がレコード数を
決められ、手動最適化の効果が観測者効果なしで測れる (invisible reads の I2 を実測で裁定し誤記まで訂正)。

### 次の一手

1. **Phase 2 着手** — `docs/phase2.md` を作りパラメータ探索へ。最初の実験候補 = CCBench 最適化フラグの
   全探索 (有限空間)。critic / profiler サブエージェントを `agent-architecture.md` 仕様で実体化。
2. タスク6 (orchestrator 骨格: campaign-id/WAL/リカバリ/排他) も Phase 2 の前提として配線。
3. (任意増分) mocc trace-hook (visible-reads の trace 検証 + verifier 2nd エンジン化)、ermia cross-check。

---

## 2026-06-19 (続き) — タスク6 (orchestrator 骨格) STAGE2 + 敵対レビュー硬化

### STAGE1 (前段, commit `6daf1a6`)

orchestrator を DB トランザクション実行エンジンの原理で設計 (orchestrator-design.md)。machine 非依存の
骨格: `model` (Genome/CampaignConfig/CampaignId/WalRecord/EvalState)、`genome` (最適化フラグ超立方体 +
制約付き列挙、silo 2^4=16→no-wait 相互排他で 12 有効)、`ident` (campaign 同一性=内容ハッシュ、D13)、
`layout` (出力二軸)、`wal` (追記+fsync+リプレイ+atomicity+末尾切れトレラント)、`lock` (machine-wide
fcntl ベンチ排他)。モックテスト 15。

### STAGE2 — 評価パイプライン統合 (build→verify→[bench]→commit)

`buildcache` (genome→バイナリ。内容キーで trace/perf **別ビルド** 規律1、ccache warm)、`pipeline`
(評価状態機械)、`loop` (同一性確定→リカバリ→未評価 genome 評価)、`demo` (end-to-end 配線テスト)。
**demo を実機で完走**: silo 2 variant (BACK_OFF on/off) が build→verify→bench→commit、両 **certified
SERIALIZABLE** (タスク5a と一致: BACK_OFF=1 で 272K txn / =0 で 571K txn)、run2 で recovery が両 skip。
規律1 を buildcache 経路で再確認 (perf build に izanagi_trace symbol **0** / trace build に **6**、`nm`)。

### 敵対レビュー (workflow 32 agent / 1.36M tok) → 規律2/A の穴を発見・硬化

STAGE2 は規律1・2 を engine が自動執行する統合点。5次元 review → 各 finding を敵対検証する workflow で
**confirmed 20**。本質クラスタ:
- **規律2 (false-green):** `_run_trace` が trace バイナリの returncode を無視 + 空トレース (commit 0) を
  verify に渡すと空 DSG が `serializable=True` に化け **certified**。異常終了/部分実行/空実行が「正しさ
  ゲート通過」になっていた。trace なし (ParseError) は campaign ごとクラッシュ。
- **A (atomicity):** bench 測定失敗 (median=None) を fitness 無しの STAGE_COMMIT で terminal 化 →
  リカバリで永久 skip。半端な評価を採用済みにしていた。
- **overnight 耐性:** 1 genome の評価例外が campaign 全体を停止 + abort 記録なし → 再起動で同地点再クラッシュ。
- 防御: 偽キャッシュヒット (commit 未照合)、settle を genome ごと呼ぶ (calibrator 契約違反・規律4 の時間浪費)、
  records 二重指定、path traversal、WAL 親 dir 未 fsync、high_variance 落とし。

**硬化 (実装済み):**
- pipeline: **正しさを確証できない全経路を abort に倒す** — verifier red だけでなく build 失敗・trace 異常
  終了 (rc≠0)・空トレース (commit 0)・パース不能・timeout・bench 測定失敗。`_run_trace` は `(ncommit, rc)`
  を返し呼び手が rc を必ず検査。bench 失敗は fitness 無し COMMIT を書かず abort (A)。high_variance を WAL 記録。
- loop: per-variant 例外隔離 (例外も abort 記録で terminal 化し campaign 継続)、run 内 dedup、settle を
  最初の実 bench の前 1 回のみ (calibrator 契約)。
- buildcache: 宣言 ccbench_commit を submodule 実 HEAD と照合 (偽ヒット防止)。layout: campaign-id の
  path traversal 関所。wal: 初回作成時に親 dir も fsync (D)。

テスト **15→28** (規律2 の abort 自動執行を全 reject 経路で回帰テスト化、loop 例外隔離/dedup、commit 照合、
path 防御)。硬化後の green-path を実機で再確認 (build cache hit→実 trace 272808 commit→certified)。
verifier 15 / calibrator 23 回帰なし。

### 次の一手

1. **Phase 2 着手** — `docs/phase2.md` + critic/profiler 実体化。タスク6 ループを実 fitness (確定
   calibration 1m/48thread/skew0.9) に切り替え、silo 12 genome の全探索を最初の実験に。
2. (任意) do_bench 同一性の構造化 (現状は trial 隔離が前提・呼び手契約)、bench 失敗を terminal-abort と
   するか retry とするかの方針確定。

---

## 2026-06-20 — Phase 2 着手 (P2-0 verifier 大規模 sanity + CCBench 隠れ前提3つを露呈)

### Phase 2 設計 (`docs/phase2.md`)

roadmap §9 (パラメータ探索) + 層2(a) 全探索 + §3.5 leading indicators + §3.6 測定安定性 +
agent-architecture (critic/profiler) に基づきタスク分解。**初手は silo フラグ空間の全探索**
(有限・ground truth) → LLM 誘導探索と比較 (論文の図)。P2-0(verifier大規模sanity)→P2-1(測定安定性)
→P2-2(実fitness全探索)→P2-3(leading indicators+critic)→P2-4(profiler)→P2-5(LLM誘導vs全探索)。

### P2-0: silo verifier 大規模 sanity = 「緑を取りこぼさない」実証

パラメータ variant は CCBench 由来で理屈上全緑のはず。silo 全 genome を build(trace+perf)→verify
→commit (do_bench=False, 計測なし) で回す。**全探索が網羅的だからこそ、普段コンパイル/実行されない
経路の隠れた前提を3つ露呈** (roadmap §2(a) の狙い通り):

1. **WAL `10^9` XOR バグ** (build-error): `ftruncate(10 ^ 9)` は XOR で 3 (意図は 1e9=1GB)。
   gcc-13 -Werror で fail。silo/ss2pl の WAL 経路 5箇所。WAL=0 default では未コンパイルで潜伏。
   → ユーザー判断で **izanagi-trace `6656e93`** に修正 (10^9→1000000000)。gitlink 前進。
   master 還元用 fix ブランチ `fix/silo-wal-ftruncate-xor` を用意 (push 認証なし→人間が PR)。
   `output/insights/2026-06-19_ccbench-silo-wal-ftruncate-xor-bug.md`。
2. **WAL log/ 前提** (SIGABRT rc=-6): WAL の log は `<cwd>/log/log<thid>` (fileio.hh genLogFileName)。
   log/ 不在で open 失敗 → LibcError → uncaught → terminate。CCBench バグでなく運用前提
   (genLogFileName が mkdir しない)。→ `_run_trace` を cwd=trace_dir + log/ 用意に修正
   (trace_dir 使い捨てで log も消える)。trace/perf 両 build で SIGABRT = WAL 全般の前提。
3. **両 no-wait=0 ハング** (trace-timeout): wait validation の silo は high/mid/low(uniform) 全
   contention で trace 取得 timeout (構成自体のハング、livelock 疑い)。P2-0 から除外 (sanity_silo.py)。
   **perf build で動くか = 構成病理か trace 特有かは P2-2 で確認** (動けば探索空間に残す)。

### 硬化が2回機能 (敵対レビュー硬化の実機実証)

build-error と SIGABRT を `evaluate` が abort 隔離し campaign は完走 (クラッシュなし)。特に
SIGABRT 後の部分トレースは、硬化前なら空 DSG 経由で false-green certified になっていた
(規律2 の自動執行が `_run_trace` の rc 検査で防いだ)。STAGE2 敵対レビュー硬化の価値を実機で実証。

### 結果: P2-0 PASS

両 no-wait=0 除外 + WAL 修正後、**WAL=0/1 各 4 = silo 8 genome 全て certified serializable**
(false-red ゼロ)。verifier が大量の正しい variant を緑と判定できる実証 = タスク3「赤を出せる」と
対の「緑を取りこぼさない」を達成。テスト 28/15/23 回帰なし。

### 次の一手

1. **P2-1 (測定安定性 §3.6 (2)(4))** — 純ロジック (calibrator と同型、モックテスト)。
2. **P2-2 (実 fitness 全探索)** — 確定 calibration で silo を計測 (直列)。**両 no-wait=0 が perf で
   動くか**を最初に確認 (動けば 12 genome、動かねば genome.py に除外制約)。runner も WAL log/ 対応要。
3. master PR (`fix/silo-wal-ftruncate-xor`) は人間が push (push 認証なし)。

---

## 2026-06-20 (続き) — CCBench PR 還元 + 材料レポート射影器 (gnuplot + 再現性)

### WAL バグ master 還元完了

ユーザーが fix ブランチを push し **PR #116 を master にマージ** (origin/master `2574412`、
`10^9`→`1000000000` が5箇所反映)。P2-0 で掘り当てた CCBench バグが上流還元された。izanagi-trace
`6656e93` (探索用) と master の修正は同一内容。izanagi-trace の push と master 完全追従 (rebase)
は後日 (探索は 6656e93 で問題なし)。

### 材料レポート射影器 (再現性が一級市民)

ユーザー要望: .dat に生成コマンドをコメントで埋め手打ち再現可能にし、報告レポートに gnuplot
グラフを入れ人間可読にする → forensic binding (roadmap §3.6(4)/§7) の前倒し実装。

`orchestrator/reports/`:
- `plot.py` — gnuplot ラッパ。`DatFile` がヘッダに provenance + **手打ち再現コマンド**を `#`
  コメントで埋める。`make_plot` が .dat/.plt/.png 3点セット + gnuplot 描画 (noenhanced で `_` を
  リテラル表示)。
- `calibration_report.py` — calibration json → .dat/.plt/.png + report.md (最初の実例)。
  records 掃引の miss率/maxrss を 2軸グラフ + 数値表 + 再現コマンドに射影。
- 実機 calibration (skew0.9 / uniform) を材料レポート化 (png 検証済み)。テスト 6。
- 出力規約を orchestrator-design.md に明記 (各図 = .dat[再現コマンド]+.plt+.png+md、性能比較図は
  trace-disabled のみ = 規律1)。

**残**: runner が組み立てる実行コマンドを WAL/calibration に記録する配線 (今は reports 射影器が
workload から再構成・binary placeholder = 近似再現)。実コマンド記録で provenance を完全化するのは
次の改善。

---

## 2026-06-21 — forensic binding 完成 (実コマンド記録) + 別セッション injection を受けた監査

### セッション再開の経緯 (プロンプトインジェクション対応)

隣で並行していたセッションが激しいプロンプトインジェクションを受けたため、ユーザーがセッションを
作り直して再開。未コミットの作業 (12ファイル) が残っていた → **素性の信頼できない作業物**として扱い、
コミット前に **3視点の敵対的監査** (security/injection・規律 compliance・correctness/completeness) を
並列ワークフローで実施。全視点 **clean**:

- footprint は宣言された12ファイルに限局 (untracked なし、hooks/・CLAUDE.md・.claude/ 改変なし)
- 記録されるコマンド文字列は eval/exec/subprocess に一切流れない**不活性データ** (`#` コメント描画のみ、
  shell=True 不在)
- 計測数値 (miss率/tps/noise floor) は byte-identical = **改竄・捏造なし** (規律4)
- 規律1: WAL に記録されるビルドコマンドは **perf=trace-disabled build のものに限定** (trace build と
  非混同)、run_cmd は実計測 binary を忠実再現 (差分は再現無関係な perf `-o/-x` のみ)
- 規律2/3: verifier・正しさゲートのロジックは無改変 (diff 全体 grep で確認)

→ 監査結果を信頼し、検証済みクリーンな論理単位としてコミット。

### forensic binding の完成 (前回「残」の解消)

calibration/WAL に **実ビルド/実行コマンド**を記録し、近似再構成を実コマンド記録に置換 (roadmap §3.6(4)/§7):

- `runner.repro_command()` — 計測点を手で再現するコマンド (perf の `-o`/`-x` は再現無関係なので外す)。
  `ScalePoint.run_cmd` に載せ、pipeline が `STAGE_BENCH_DONE` で WAL に記録。
- `buildcache.BuildResult.configure_cmd/build_cmd` — **cache hit でも記録** (provenance 完全化)。
  pipeline は perf (trace-disabled) build のコマンドだけを `STAGE_BUILD_DONE` で WAL に記録 (規律1)。
- `calibration_report._build_command` + `DatFile.build_command` — .dat/report.md に「**ビルド → 実行**」
  二段の再現コマンドを埋める。実機 calibration 2件 (skew0/skew0.9) を再生成 (数値不変)。
- テスト: `test_reports` に build+run コマンド埋め込みテスト追加。**73 passed** (verifier15/calib23/campaign28/reports7)。

### 次の一手

**P2-1 (測定安定性 §3.6 (2)(4))** — 純ロジック・機械非依存・モックテスト。(1)(3) (noise floor + 反復
中央値・CV) の上に (2) 外れ値→自動再測定 + (4) 分布比較 (noise floor 以下は「差なし」、超えは
Mann-Whitney U) + unstable 除外を積む。計測を伴わないので直列規律 (規律4) に抵触しない。

---

## 2026-06-21 (続き) — P2-1 完了: 測定安定性 (2)(4)

(1)(3) (noise floor + 反復中央値・CV) の上に (2)(4) を積んだ。**純ロジック + callable 注入**で machine に
触れずモックテスト (実走は pipeline が bench_lock 下=直列、絶対規律4 不変)。

新規 `calibrator/stability.py`:

- **(2) 外れ値→自動再測定** `remeasure_until_stable(measure_fn, settle_fn, cv_threshold=5%, max_rounds=3)`:
  反復内 CV が閾値超なら静定して測り直し、規定ラウンドで収束しなければ `unstable`。採用は最も CV が
  低かったラウンド (収束したらその点)。2 ラウンド目以降のみ静定 (1 回目は campaign 冒頭で済)。
- **(4) 採否は分布比較** `compare(baseline, variant, noise_cv, alpha=0.05)`: ① noise floor 以下の中央値差は
  「差なし」に丸める (信用してよい差の下限) → ② 超える差にだけ `mann_whitney_u` を当て有意なら
  faster/slower。MWU は正規近似 + tie/連続補正の自前実装 (scipy 非依存 = 「重い統計機構不要」、erf のみ)。
  **unstable variant は呼び手が比較から除外する** (沈黙して 1 点を採用しない)。

pipeline.py 配線:

- bench 段を単発 `measure_point` → `remeasure_until_stable` に置換 (実走は bench_lock 内のまま=直列)。
- `EvalResult.unstable` 追加。WAL `STAGE_BENCH_DONE` に rounds/cv_history/unstable、`STAGE_COMMIT` に
  unstable を記録 → 採否の分布比較 (P2-2) が除外判断に使える。
- unstable でも reject しない (正しさは通過済み)。「沈黙して 1 点を採用しない」は分布比較からの除外で担保。

テスト: `test_stability.py` 12 (remeasure 収束/後続収束/unstable最小CV採用/単点除外、MWU 同分布/完全分離/空、
compare 床下/有意faster/slower/床上非有意/空) + `test_campaign` に unstable 伝播 1。**86 passed**
(verifier15/calib23/campaign29/reports7/stability12)。

### 次の一手

**P2-2 (silo 全探索)** — ここから実機計測 (直列)。確定 calibration で silo 12 genome を実 fitness 評価し、
`compare` で workload 別の最速構成を**分布比較**で特定 → D12 材料レポートに射影。**両 no-wait=0 が perf
build で動くか** (P2-0 で trace timeout した3構成) *(注 2026-07-03: 最終的な除外は両 no-wait=0 の
4 構成 = 12−8。「3構成」は当時の記録の揺れで、P2-0 の sanity WAL が未保存のため原記録での確定は
不能 — 2026-06-22 エントリの 12→8 敵対監査参照)* を最初に確認 → 動けば 12、動かねば genome.py に除外制約。
runner も WAL log/ 対応要 (P2-0 で _run_trace は対応済、perf 経路も同様に要確認)。

---

## 2026-06-22 — P2-2 着手: 両 no-wait=0 の livelock を監査・確定 → silo genome 空間を 12→8 に訂正

### セッション再開時の監査 (規律6)

未コミットの untracked insight (`output/insights/2026-06-22_silo-both-no-wait-zero-livelock.md`) が残って
いた。worklog に当日の記録は無く素性が完全には追えない作業物のため、**採用前に独立監査**した:

- **核心 (両 no-wait=0 livelock) を実ソースで再検証:** `cc/silo/transaction.cc:145-178 lockWriteSet()`。
  write set 各 tuple の tidword を内側 `for(;;)` の**外**で 1 回だけ読み (`expected`, :151)、競合時の分岐は
  `#if NO_WAIT_LOCKING_IN_VALIDATION` / `#elif NO_WAIT_OF_TICTOC` のみで **`#else` 句が無い**。両 0 のとき
  `if (expected.lock)` の本体が空 → 他者ロック保持を観測すると expected を再読みせず永久スピン (busy
  livelock)。thread=1 のみ完走 (競合せず) で thread≥2 は必ず hang。**機構は insight の主張どおりと確認。**
- **「実装済み」の主張は事実と相違:** insight は「genome.py を XOR 制約に強化済み」と書くが、`git diff` は空・
  genome.py は HEAD から無改変 (依然 `_no_wait_mutual_exclusion` = 両 1 のみ禁止 = 12 genome)。記述が実装に
  先行していた → **記述に合わせて実装し、説明と中身を一致させた** (規律6「差異を表に出す」)。
- injection 性なし (純粋な技術 finding + 「上流 PR は出さず insight に留める」は CLAUDE.md と整合)。

### silo 有効遺伝子空間: 12 → 8 (no-wait XOR)

`(NO_WAIT_LOCKING_IN_VALIDATION, NO_WAIT_OF_TICTOC)` の素性: (1,0)=競合で即 abort / (0,1)=解放して retry /
(1,1)=`#elif` が dead code で (1,0) と挙動同一 (冗長) / (0,0)=競合分岐が空で livelock。**有効なのは XOR
(ちょうど一方が 1) の 2 組のみ。** silo の live 空間 = `BACK_OFF[2]×WAL[2]×{(1,0),(0,1)}[2] = 8`。
これまでの「12」は両 1 だけ除いた生の数で、縮退 (両 0) を含んでいた。

実装 (テスト 86 passed, 回帰なし):
- `genome.py`: `_no_wait_mutual_exclusion` (両 1 禁止) → `_no_wait_xor` (ちょうど一方が 1)。enumerate() が 8 を返す。
- `test_campaign.py`: size 12→8、制約テストを XOR (両 1 も両 0 も 1 個も無い) に強化。
- `sanity_silo.py`: P2-0 当時の手動除外 `_trace_evaluable` を撤去 (genome.py の制約に昇格して不要)。
- `phase2.md`: P2-0/P2-2 の genome 数を 8 に、P2-0 を done に。
- insight を committed 化。**上流 PR は出さない** (XOR 除外で探索には足り、CCBench 本体の `#else` 補完は別判断)。

### 次の一手

**P2-2 本体 (実 fitness 全探索)** — 確定 calibration (1m/48thread/skew0.9) で silo 8 genome を実機計測
(直列・規律4)。代表 workload (read-heavy / write-heavy / high-contention) ごとに `compare` で最速構成を
分布比較で特定 → D12 材料レポートに射影。

---

## 2026-06-22 (続き) — P2-2 完了 (silo 全探索) + 規律4 インシデント (孤児 livelock 汚染) 対処

### runner の WAL log/ 対応 (P2-2 の前提解消)

`run_once` は cwd を変えず `log/` も作らなかったため、WAL=1 genome は `<cwd>/log/` 不在で SIGABRT し
「no metrics」abort になっていた (worklog 前回フラグ済み)。`_run_trace` と同様に使い捨て tmp 内に log/ を
作り cwd=tmp で実行するよう修正。実機 smoke で WAL=1 silo が throughput を出すことを確認。

### 🔴 規律4 インシデント: 前セッションの孤児 livelock が計測を汚染

P2-2 起動直後、素性不明の `ycsb_silo` (rratio=50/rmw=false) が動いているのに気づき調査 → **PPID=1・約7時間・
%CPU 4793% (≈48 コア占有) の孤児**。両 no-wait=0 の livelock ([[2026-06-22_silo-both-no-wait-zero-livelock]])
で、insight を書いた前セッションが kill し損ねたもの。孤児が半機を食う中で read-heavy が 3 genome を commit
済みになっていた (汚染。genome1 が汚染時 3.86M → クリーン時 **8.47M tps = 2.2x 差**)。対処:
- 孤児を kill、私の P2-2 run を停止、汚染した read-heavy campaign dir を削除して再測定。
- **競合検知ガード** `p2_2.py._assert_single_tenant()` 追加: `pgrep` で競合ベンチを直接確認 (load average は
  1 分 EMA で laggy)、居たら PID を表に出して計測拒否 (自動 kill しない = 規律6)。
- admission control の **fails-open ギャップ** (`settle` が quiesce できなくても進む) を含め
  `output/insights/2026-06-22_orphan-livelock-contaminated-measurement.md` に記録 (深い修正は P2-3 以降に延期)。

### P2-2 結果 (クリーン機・単一テナント直列、全 24 評価 certified・abort 0)

*(注 2026-07-03: 下表の数値は初回計測のもの。P2-3 で leading indicators 捕捉のため同一 campaign-id で
再計測しており (2026-06-22 P2-3 エントリ参照)、現存 WAL / p2-2-summary.md の数値は再計測値
(read-heavy 8,487,844 / balanced 2,752,621 / write-heavy 1,872,376、2位差 +7.6%/+13.0%)。
差は floor 内で最速構成・結論は不変。現 WAL から下表は再現できない点に注意)*

silo 8 genome × 3 workload (skew0.9, rratio 95/50/5)。workload 別最速構成を `compare` (noise floor 2.28%
以下は差なし + Mann-Whitney U) で特定:

| workload | 最速 | median tps | 2位との差 |
|---|---|---:|---|
| read-heavy  | B0-T-W0 | 8,466,239 | 上位3つ noise floor 内で同点 |
| balanced    | B0-L-W0 | 2,722,529 | +6.1% (有意) |
| write-heavy | B0-L-W0 | 1,883,017 | +13.2% (有意) |

(B=BACK_OFF, L=no-wait-locking/即abort, T=tictoc-no-wait/retry, W=WAL)。知見: **(1) BACK_OFF=0 が全 workload で
支配** (read-heavy で BACK_OFF=1 比 ~4.3x。task5a の BACK_OFF 遅延と整合)。**(2) no-wait は workload 依存** —
read-heavy は無差、contention 域 (balanced/write-heavy) は即abort (L) が retry (T) より速い。**(3) B0-L-W0 が
2/3 で1位・read-heavy で同点1位 = 全体最強** → P2-5 (LLM 誘導探索) の ground truth。

成果物: 各 campaign の `reports/` (.dat[再現コマンド]+.plt+.png+report.md) + `runs/wal.jsonl` (生 tps + 実行
コマンドの proof chain) + 横断 `output/campaigns/p2-2-summary.md`。テスト 87 passed (reports に棒グラフ 1 追加)。

### 次の一手

1. **P2-3 (leading indicators + critic)** — perf カウンタ (lock contention / cache / allocator) を fitness と
   一緒に WAL 記録し critic に渡す。critic.md を agent-architecture 仕様で実体化。
2. (検討) admission control を fails-closed 化 (settle が quiesce できなければ計測中断) — 孤児汚染の根治。
3. (任意) cicada/oze 等へ protocol を広げ genome 空間を拡大 (P2-5 比較の強化)。

---

## 2026-06-22 (続き) — P2-3 完了 (leading indicators の WAL 記録 + critic 実体化)

### leading indicators の WAL 配線

throughput スカラーだけでは探索が停滞する (Jitskit §3.5)。fitness を設計選択に帰属させる先行指標を
毎評価 WAL (STAGE_BENCH_DONE) に記録:
- `benchparse`: abort_rate() (ccbench `abort_rate:` 優先、欠損/-nan は生カウントから再計算) + latency_ns()。
  **abort_rate は no-wait の即abort/retry や backoff の効果が直接出る CC-native な最重要指標。**
- `model`: PerfCounters.ipc、ScalePoint に abort_rate/latency_ns + `leading_indicators()`
  (throughput/abort/latency/llc_miss/ipc を束ねる)。`runner.measure_point` が代表 rep (throughput 中央値)
  の ccbench メトリクスから取り込む (perf counters と同一 run の断面)。`pipeline` が WAL に記録。

### critic 実体化 (digest 機械準備 + agent)

- `orchestrator/critic/digest.py`: campaign WAL の leading_indicators を **genome 別表 + フラグ軸の限界効果**
  (BACK_OFF / no-wait L|T / WAL をフリップしたときの各指標の水準別平均、他フラグで周辺化) に構造化。
  no-wait は XOR なので L/T の categorical 軸に畳む。`python critic/digest.py` で 3 workload digest を出力。
- `.claude/agents/critic.md`: 帰属→次手の LLM 推論エージェント (model opus、読み取りのみ)。出力は
  attribution/recommend/avoid/uncertainty。digest をデータ扱い (規律6)・正しさ前提 (規律2)・noise floor 尊重。

### LI 付き再計測 + critic 実走

LI 記録前の P2-2 commit は loop recovery で skip されるため、3 campaign dir を削除して**同一 campaign-id で
再計測** (LI 捕捉)。fitness は元 P2-2 と再現一致 (最速構成不変・差は noise floor 内 = 再現性の裏付け)。
全 24 commit に LI が入った。critic エージェントを実 LI に実走させ帰属を取得:
- **BACK_OFF=1 はなぜ遅いか:** abort は減らせている (balanced 65→18%) のに throughput 半減 = **ipc 崩壊
  (1.4-1.6→0.4-0.5)+latency 増の over-throttling** (待ちで命令を発行できない)。損は abort baseline が高いほど
  小さい (機序の裏付け) → 全 workload で avoid。
- **no-wait は workload で L↔T 反転:** read 無差 (noise内) / balanced=L 優位 (+19.6%, ipc で稼ぐ) /
  write=T 優位 (+12.7%, abort+latency 同時減)。critic 無しの「全 workload で 1 構成」探索はこの反転を取りこぼす
  (= critic の ablation 価値)。
- **WAL は write 比率比例の純損** (abort 不変・latency/miss 増)。
- **次手:** BACK_OFF=0/WAL=0 固定・no-wait 出し分け・**新軸「中間/適応 backoff」** (ipc を殺さず abort を
  下げる未探索帯) を提案。uncertainty (read top2 は noise 内で順位不可・1round・限界効果は交互作用未分離・
  中間 backoff 未測定) も honest に明示。`output/insights/2026-06-22_p2-3-critic-leading-indicator-attribution.md`。

テスト 96 passed (benchparse abort/latency・ipc・leading_indicators・WAL 記録・critic digest 4 = 計9追加)。
途中、test_campaign の一時 dir leak (257個) を atexit 後始末で解消。

### 次の一手

1. **P2-4 (profiler 実体化)** — screening 通過した上位 variant にだけ perf/FlameGraph を回し many-core
   スケール懸念を診断 (二段構え、trace-disabled build=規律1)。critic の「中間 backoff」提案の検証にも使える。
2. **P2-5 (LLM 誘導探索 vs 全探索)** — critic フィードバックで次 genome を選ぶループ。silo 8 は全探索済み
   なので、critic 提案の新軸 (中間 backoff) や cicada/oze へ空間を広げて到達 iter を比較。
3. (検討) admission control の fails-closed 化 (孤児汚染の根治)。

---

## 2026-06-22 (続き) — P2 ケーススタディ: 静的 backoff variant の合成がフラグ空間外で stock を上回る

critic の「中間/適応 backoff」提案 (P2-3) をユーザー合意のもと実験 (「論文ネタになるなら」)。

### 評価 (論文上の位置づけ)

「中間 backoff」自体は CC 手法として新規でない (contention management は数十年の蓄積)。**単体の貢献として
主張しない。** 価値は **Izanagi 方法論のケーススタディ**: システムが leading indicators で機序を特定し、
定義済みフラグ空間の外へ出て新軸を開き、正しさゲートを保ち、stock を上回るか正直に測る。ソース確認で
**CCBench の backoff は既に Cicada 適応 backoff** (leader が throughput 勾配で global 値を hill-climbing)
で、critic が提案した「適応化」は既存 = それが BACK_OFF=1 の正体と判明。よって実験は「適応の収束が悪い」
仮説の検証に焦点化。

### 合成 variant + 実験 (D18, patches/silo-backoff-fixed.patch)

backoff の*量*を静的固定する `CCBENCH_BACKOFF_FIXED` (default -1=stock 適応で inert) を導入。L-W0 base で
無 backoff / stock 適応 / 静的 {2,5,10,25,50,100}us を高 abort workload (write-heavy/balanced) で計測
(`backoff_sweep.py`)。全 16 (8×2) が **certified serializable・abort 0** (backoff は timing のみ→CC 論理
不変、verifier が毎回ゲート)。inert は stock genome の cache hit で実証。

### 結果 — 合成 variant が stock 最良を明確に上回る (sweet spot あり)

| workload | 無 backoff | stock 適応 | 静的最良 | 無比 |
|---|---:|---:|---:|---|
| write-heavy | 1,882,125 | 1,052,528 | **10us = 2,603,521** | **+38.3%** |
| balanced | 2,791,760 | 916,149 | **5us = 3,106,342** | **+11.3%** |

**機序が量の関数として明瞭 (write-heavy 曲線):** backoff を増やすと abort 単調減 (82→17%)・ipc 単調減
(1.62→0.59)、throughput は両者の積が最大の **10us でピーク**の逆U字。stock 適応はピークを越えた低 ipc 域
(≈100us 相当, ipc 0.59) に収束 = **Cicada の hill-climbing が sweet spot を逃している**ことの直接証拠
(critic の P2-3 帰属「適応は sweet spot を逃す/over-throttling」を実 sweep で裏付け)。最適量は workload 依存
(write 10us / balanced 5us)。

**フラグ空間 (binary BACK_OFF) は {無, 適応} しか提供せず、適応は病理・無が勝者だった。量という新軸を開いて
初めて +11〜38% の sweet spot が見つかった** = 方法論ケーススタディの核 (システムが空間外を合成して stock 超え)。

成果物: 各 sweep campaign の `reports/` (throughput vs backoff 量の曲線 .dat/.plt/.png + report.md) +
`runs/wal.jsonl`。射影器 `backoff_sweep_report.py`。critic の締めの解釈 (ループ閉じ) は中断、後続で再実行可。

### 次の一手

1. (締め) critic に sweep を解釈させ「適応をやめ静的小 backoff/workload 依存量」を最終推奨として記録。
   read-heavy でも測って「低 abort では backoff 不要」を確認 (現在は high-abort 2 workload のみ)。
2. **P2-4 / P2-5** は上記のまま。この合成 variant は P2-5 (LLM 誘導 vs 全探索) の「空間外合成」の実例にもなる。
3. (検討) admission control の fails-closed 化。

---

## 2026-06-22 (続き) — backoff ケーススタディの締め: read-heavy 対照 + 敵対的検証 workflow

### read-heavy 対照 (機序の完全性)

backoff が効くのは abort が高い時だけ、を対照で確認。read-heavy (rratio95, abort 16%): no-backoff=8,450,806 が
最良で、backoff 量↑につれ throughput **単調減** (2us=7.89M … 100us=3.63M、適応=1.92M)。**sweet spot は
no-backoff(0)に潰れ純損** (-6.6%)。高 abort (write 10us+38%/balanced 5us+11% で内点ピーク) と対をなす =
合成した静的 backoff は **workload-aware** (abort が高い時のみ latency/ipc コストを上回る利得)。全 certified・abort 0。

### 敵対的検証 workflow (8 agent / 357k tok) — fatal ゼロ・headline 生存

計測 (直列) は完了済みなので解析のみ workflow 化 (規律4 抵触なし)。critic 解釈 → 5 レンズ敵対的反証
(measurement/fairness/mechanism/correctness/generalization) → 完全性 → 合成。**fatal 反証ゼロ、中核主張は
5 レンズを生存**。`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md` に paper-ready 評価を記録。

**生存した主張:** 合成 variant が contention 域で stock 最良を +38.3%/+11.3% 上回る (5-rep 完全非重複, MWU
p=0.012, 差は floor の 5-17 倍)・全 certified (規律2)・patch は inert で apples-to-apples (規律6 監査)・逆U字と
read-heavy 対照は実在。

**敵対的検証が削った over-claim (paper を正直にする発見):**
- **機序「throughput = abort×ipc の積でピーク」は看板 write-heavy で破綻** (積ピーク 25us vs throughput ピーク
  10us)。残差は backoff() の `_mm_pause` スピン命令が perf instructions を希釈する第三因子。正しい定性は
  「abort 減 × (ipc 減 + 純待ち latency) のトレードオフ」。latency[ns] は ccbench で tps の恒等再記述で独立情報ゼロ。
- 勝利は **high-abort に条件付き** (3 workload 中 2 勝 1 敗) → 主張を「contention 域で」と狭める。
- **+38% は単一 back-to-back 系列** (rounds=1) で別 boot 再現は未確認。
- certified は機序論証依存で実 perf 構成の trace を直接検証していない (backoff が correctness-inert ゆえ堅固だが外挿)。

**最致命の穴 [P0]:** (1) cross-run 再現性が未確認、(2) 機序「なぜ速いか」が看板例で破綻。安価な [P1]: 正しさ実測化・
適応収束値の実測・base 一般性。

### 方法論的含意

「leading indicators の帰属が**フラグ空間外への合成**を駆動 → 正しさゲートが空間外でも機能 → certified なまま
stock 最良超え」のループが回った = **本プロジェクト中核仮説 (AI が正しさを保ったまま既存最良を超える CC を合成)
の限定スコープでの最初の成立例**。ただし critic ablation の定量 (有/無の探索効率比較) は未実施 = P2-5。

### cross-run 再現性 [P0] を解消 (`backoff_repro.py`)

勝者と参照を別 campaign・逆順 (fix10→fix5→none) で再測 → **headline 再現確認**:
- balanced クリーン再現 (+11.3%→+11.7%, drift +0.4%)
- write-heavy は勝者 fix10 が完全再現 (2,603,521→2,599,032 = -0.17%)。"乖離"は no-backoff 参照が -2.9%
  (CV 2.19%, floor 2.28% 近傍) ドリフトし比が +42.2% に動いたため。win は両系列で +38%超・頑健。
- 含意: no-backoff (abort 82%) が最大の run 間分散源で backoff variant の方が安定、順序は勝者を偏らせない
  (後置の none が低い=warmup 人工物と逆)。**残: 別 boot / rounds≥3** (本 repro は同一 boot・別系列)。

### [P1] over-throttling 直接測定を試行 → CCBench の新バグを露呈 (ADD_ANALYSIS+BACK_OFF segfault)

「stock 適応の backoff スピン占有率」を既存フラグ `ADD_ANALYSIS=1` の `backoff_latency_rate` で外挿でなく実測
しようとしたら、**BACK_OFF=1 + ADD_ANALYSIS=1 が segfault** (thread=1/4/48・適応/静的 全て、gdb で
`TxExecutor::leaderWork()` に限局)。BACK_OFF=1 単体 (sweep 全点) と BACK_OFF=0+ADD_ANALYSIS (none) は完走
→ 交互作用固有。**フラグ超立方体探索が露呈した CCBench 潜在バグの 3 例目** (WAL XOR #116 / 両no-wait livelock
に続く)。`output/insights/2026-06-22_ccbench-backoff-add-analysis-segfault.md`。over-throttling は当面 ipc/latency
からの**外挿のまま** (敵対的検証で「独立に頑健」裁定済み)。直接実測は ASan で bug 特定 or `Backoff_` dump の小 patch が要る。

### 次の一手

1. **[P0] 機序純度 (スピン命令分離)** — backoff() の `_mm_pause` 命令を perf instructions から分離し「有用 ipc」で
   残差 K が定数化するか。看板 write で積モデルが破綻 = 「なぜ速いか」の最大の穴。**P2-4 profiler と地続き** (perf record)。
2. **[P1] over-throttling 実測** — 上記 segfault を ASan 特定して迂回 or `Backoff_` 収束値 dump の小 patch。正しさ
   実測化 (実 perf 構成 trace verify) / base 一般性。
3. **P2-4 (profiler)** / **P2-5 (LLM 誘導 vs 全探索, この合成例を「空間外」実例に)**。(検討) 別 boot 再現・admission fails-closed 化。

---

## 2026-06-28 — ADD_ANALYSIS+BACK_OFF の ODR バグを ASan で特定・修正・上流還元 + izanagi-trace 前進

(注: これ以前の本セッションのエントリは作業日を 2026-06-22 と誤記している。実日付は 6/28。以降は実日付で記録する。)

backoff over-throttling を `ADD_ANALYSIS` の `backoff_latency_rate` で直接実測しようとして露呈した
segfault ([[2026-06-22_ccbench-backoff-add-analysis-segfault]]) を ASan で根本特定:
- **ODR 違反**: `ccbench_common` (= `CCBenchResults` を確保) が universal definitions を受けずビルドされ、
  `Result` を ADD_ANALYSIS=0 の小レイアウトで `resize`。プロトコル側 (ADD_ANALYSIS=1, 大レイアウト) の
  `leaderBackoffWork` の range-for が大 stride で走査し buffer 末尾を越える heap-overflow。BACK_OFF=1 で
  leaderBackoffWork が走るときだけ顕在化。
- **修正** (2 ファイル): `CMakeLists.txt` で `ccbench_common` に `ccbench_universal_definitions()` を適用 +
  `result.cc` の dead 変数 `num_txns` を `[[maybe_unused]]`。gcc-13 で検証 (ASan clean / Release -Werror /
  default build 無回帰 / `backoff_latency_rate` 出力)。
- **上流還元**: ssh push (HTTPS は token 必須でこの環境に無し) → `gh api` で PR 作成 → **ccbench master に
  PR #118 でマージ** (`50c7946`)。WAL XOR #116 に続く Izanagi 探索由来の上流還元 2 件目。

**izanagi-trace 前進**: ODR fix (`ad33940`) を izanagi-trace に cherry-pick (→ `dff0f1e`) して push、parent の
gitlink を `6656e93 → dff0f1e` に前進。fix は ADD_ANALYSIS=0 の perf build に対し inert (default build 無回帰を
実測確認) なので、過去の calibration/sweep 結果は新 pin でも再現可能。これで Izanagi 側でも `backoff_latency_rate`
が使え、ケーススタディの [P1]「over-throttling を外挿でなく直接実測」が実施可能になった (ASan 確認で thread8
適応が 76.5% スピンを実測済み、本実測は確定 calibration での sweep で裏取り予定)。

### [P1] over-throttling 直接実測 — 完了 (`backoff_overthrottle.py`, 3レンズ敵対的検証済み)

新 pin で ADD_ANALYSIS=1 build を作り sweep 各点の `backoff_latency_rate` を 1m/48thread/skew0.9 で実測:
**stock 適応は write 87.3% / read 78.0% のスレッド時間を backoff スピンに浪費**。3レンズ検証で:
- **[強化] over-throttling は計装固有でない**: 検証者が Backoff_ 収束値を AA=0/AA=1 両 build で probe 実測 →
  **実 fitness build でも適応は ~560us(write)/~600us(read) に駐車 = sweet spot 5-10us の 56-80倍**。前回「外挿」
  だった穴を実測に置換。**構造的決定打**: grid が kIncrBackoff=100us 刻みで適応は 5-10us に物理的に到達不能。
- **[縮約] eff_tps=tps/(1-spin) 機序は over-claim を削る**: 恒等式で `eff_tps/(1-abort)` 平坦 = eff_tps 単調増は
  「abort 単調減」の再表現にすぎず新機序でない。**[P0] 核心 (有用 IPC 分離) は perf record = P2-4 待ち**。
詳細は `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md` の追記 (2026-06-28)。

### 次の一手 (この時点)

1. **[P0] 機序純度 (スピン命令分離) = P2-4 profiler** — `perf record` で backoff() スピン命令を instructions から
   分離し「有用 ipc」を直接計測 (eff_tps 代理でなく)。これが backoff ケーススタディの最後の穴。
2. **P2-4 (profiler 実体化) / P2-5 (LLM 誘導 vs 全探索)**。

---

## 2026-06-28 (続き) — Phase 1 完了監査 (B) + 評価パイプライン硬化 (A1/A3/A4/A5、A2 は未着手)

ユーザー質問「Phase 1 は完璧に終わっているか」に対し **B→A** (網羅監査 → 修正) で対応。

### B: Phase 1 完了監査 (4軸 workflow, 5 agent / 355k tok)

verifier / calibrator+admission / 観測者効果+hooks / pipeline 正しさゲート を各エージェントが Phase 1
完了条件 + Phase 2 インシデントに照らして突いた。**結論: 完了条件は満たす (blocks-phase1 = 0) が「完璧」ではない。**
hardening 9 / scope-limit 5。正しさゲートは fails-closed (6 abort 経路 + positive/negative control で版写像実証)、
性能計測も within-run・単一テナント・確定動作点では信頼できるが、未硬化あり。

### A: 修正 (手堅い順、テスト 100 passed)

- **A1 [済] admission を fails-closed (最重要・実害 near-miss 根治)** — `runner.competing_bench_pids()` (pgrep で
  競合/孤児ベンチをラグなし検知) を `pipeline.evaluate` の bench 直前に呼び、居たら `bench-competing-tenant`
  で abort (汚染計測を不採用)。driver=campaign 冒頭 / pipeline=genome ごとの二段。孤児は規律6 で自動 kill せず
  PID を WAL に出す。settle の settled を forensic 記録。
- **A3 [済] zero-txn ガードを verifier 最下層へ + digest committed フィルタ** — 空トレースが certified に化ける
  false-green (verify.py 直叩き経路) を VerifyResult.verdict/certified に n_txns==0→indeterminate を置いて封鎖。
  critic digest は STAGE_COMMIT のある genome のみ拾う (A の漏れ窓)。
- **A4 [済] perf build の trace シンボル不在を buildcache で継続 assert (規律1)** — `_assert_no_trace_symbols`
  (nm -C に izanagi_trace があれば RuntimeError)。実機: perf=0個/trace=6個 で誤検知なし・検知が効く。
- **A5 [済] hooks 未実装を明示 + Phase 3 着手前 must を phase2.md に** — hooks/ は placeholder で CLAUDE.md と
  乖離 → README 冒頭に明示 (規律6)。実装は Phase 3 (LLM が C++ を書く瞬間に load-bearing) に繰り延べ。
- **A2 [未着手] between-run noise floor** — within-run CV (2.28%) は between-run (~3%, repro 実測) を過小評価し
  compare が数% flag 差で偽 faster を出しうる。capability (stability に between_run_noise_floor) + baseline 反復
  計測 + compare/report への配線が残り。+38% の大効果は無影響。

### Phase 3 着手前 must (今やると過剰修正 = 繰り延べ。phase2.md に記載)

S4 規律3 配線 (verifier の構造化 anomaly を次手に流す) / H3 hooks 実体化 / S2 certify=perf workload 一致 /
S1 trace-hook 別 protocol 拡張。**いずれも Phase 2 (silo・列挙) では無害、Phase 3 (別 protocol/コード合成) で
初めて load-bearing。**

### セッション所見 (引き継ぎ用)

長セッションでコンテキスト増大。最終 commit の質は安全装置 (敵対的検証 workflow・テスト・規律) で維持できたが、
一次ミスは増えた (**日付を 6/28→6/22 と誤記**したのが典型 = [[use-actual-current-date]] に記録)。次セッションは
worklog/insights/decisions/memory が最新でクリーンに引き継げる。**日付は session の実 currentDate を使うこと。**

### 次の一手 (次セッションの起点)

1. **A2 (between-run noise floor)** を仕上げる — capability 実装 + baseline 反復計測 + compare 配線。手堅い小仕事。
2. **P2-4 (profiler 実体化)** — `perf record` で backoff スピン命令分離 = backoff ケーススタディの最後の穴 [P0]。
3. **P2-5 (LLM 誘導探索 vs 全探索)** — Phase 2 主実験。critic の帰属で次 genome を選ぶループ。
4. **Phase 3 着手前 must** (上記 S1/S2/S4/H3) は Phase 3 直前に。
- 計測は直列・単一テナント (規律4)。submodule は izanagi-trace @ dff0f1e (ODR fix 入り) を pin、working tree に
  backoff patch (patches/silo-backoff-fixed.patch) 適用済み。CCBENCH_COMMIT="dff0f1e"。

---

## 2026-06-28 (続き) — A2 完了 (between-run noise floor の分離・実測・配線)

Phase 1 完了監査の残件 A2 を完了。設計→実装の前に **ultracode で 4 レンズの敵対的設計批評** (concept/統計/scope/wiring、4 agent / 326k tok) を回し、その収束所見で設計を絞ってから実装した。

### 塞いだ穴
`compare` (variant vs baseline の採否の材料) の丸め閾値に **within-run noise floor (2.28%)** を流用していた。variant と baseline は別 run/別ビルドで測るので、信用できる差の下限は run 間ドリフトを含む **between-run** であるべき。within-run を流用すると 2.28%〜3% 帯の差を「有意」と誤判定し**偽 faster** を出す (reward hacking の鏡像)。

### 実装 (最小 honest 版, 設計批評で 6→4 成果物に削減)
- **capability** `calibrator.stability.between_run_noise_floor` (callable 注入でテスト可) + `BetweenRunNoiseFloor` model。独立セッション (各 = measure_point = reps+median) の session-median の CV を出す。settle は admission であって独立性でない旨を docstring 明記。
- **compare** に `near_floor` フラグ追加。Gate2 (reps=5 の MWU) は完全分離で常に p≈0.012 を返し between-run artifact を弁別できない弱い sanity と判明 → 主防壁は Gate1 (between floor 丸め)。floor〜1.5×floor の faster/slower は near_floor を立て「cross-run 再現で裏取り要」(verdict は変えない・hard margin は規律5 で却下)。docstring を正直に書き直し。
- **独立ドライバ** `campaign/between_run_floor.py` で実機実測 (直列・pgrep gate)。
- **配線**: 3 ファイルのハードコード 0.0228 を `p2_2.BETWEEN_RUN_CV` (=0.030) に集約 (JSON 動的 loader は data が 1 点しか無く scope creep と批評 → named const + 測定ファイル参照)。

### 実測の発見 (なぜ floor=0.030 か)
B0-L-W0 baseline を確定動作点で 8 独立セッション実測 → **write-heavy で within 2.19%→between 0.67%、balanced で within 1.07%≈between 1.07%** (back-to-back では下がりこそすれ within を上回らない)。median 集約 + 熱/周波数/cache 共有で、back-to-back セッションは真の run 間ドリフトを捉えない**楽観的下限**と実測で裏付け (設計批評 concept レンズの予言どおり。high-abort の write でのみ顕著に低下)。よって floor は fresh 値でなく**時間分離 cross-campaign の genuine データ** (no-backoff CV(n=2, sweep vs repro) = 2.09%/1.53%、high-abort within ≤2.91%) に錨を打ち、最悪 run 間分散 ~2.91% をカバーする保守値 **0.030** に確定。fresh 測定は `between_run_noise_t48_*.json` に provenance 保存 (既存 calibration JSON は不可侵)。

### 帰結 (既存結論の是正・headline 不変)
floor 2.28%→3.0% で **P2-2 read-heavy rank3 (B0-T-W1, +2.4%) / rank4 (B0-L-W1, +2.6%) が faster(有意)→no-difference に反転** = 過大主張の是正 (read-heavy の no-wait/WAL 差は P2-3 で既に「無差」裁定済みと整合)。レポート再生成済み。**headline は全て不変**: 最速構成・backoff sweet spot (+38.3/+11.3/-6.6%)・repro 判定 (write drift +3.93% は 3% でも乖離) は floor 両側で変わらない。テスト 107 passed (between_run 4 + near_floor 3 追加)。詳細 [[decisions]] D19。

### 露呈した既存 issue (A2 と独立, follow-up)
レポート再生成時、**6/28 の ODR-fix gitlink 前進で CCBENCH_COMMIT が 6656e93→dff0f1e に上がり、content-addressed campaign-id が移動して歴史的 p2-2/backoff campaign の report が現 config では孤立**することが判明 (ODR fix は ADD_ANALYSIS=0 perf build に inert なので 6/22 測定は意味的に有効)。今回は測定時 commit (6656e93) を供給して忠実に再生成した。恒久対応 (生成器が既存 dir を discover する / inert な submodule fix では campaign-id を据え置く) は phase2.md に follow-up 記録。

### 次の一手
1. **P2-4 (profiler 実体化)** — `perf record` で backoff スピン命令分離 = backoff ケーススタディの最後の穴 [P0]。
2. **P2-5 (LLM 誘導探索 vs 全探索)** — Phase 2 主実験。critic の帰属で次 genome を選ぶループ。near_floor フラグが close call の裏取りに効く。
3. **Phase 3 着手前 must** (S1/S2/S4/H3) + campaign-id drift の恒久対応は Phase 3 直前に。

---

## 2026-06-28 (続き) — P2-4 profiler 実体化 + backoff [P0] 機序純度を解消

backoff ケーススタディの最大の穴 [P0]「なぜ速いか」(看板 write-heavy で「throughput=(1-abort)×ipc の積」が
peak 位置を外す) を **perf record で spin 命令を分離**して解消。profiler サブエージェントを実体化 (Phase 2 deliverable)。

### 手法の実機 de-risk → BACKOFF_NOINLINE 診断パッチ
- `backoff()` の `_mm_pause`+`rdtscp` busy-wait は -O2 で `TxExecutor::abort` に inline され perf で独立シンボルに
  ならない (fix50 で rdtscp 単体が全 cycle の 42.49% = smoking gun だが abort に溶ける)。
- **`BACKOFF_NOINLINE` inert 診断ノブ**を patch に追加 (Options.cmake + backoff.hh の `#if`)。1 で `__attribute__((noinline))`
  → `Backoff::backoff` を独立シンボル化。既定 0=inert (stock 命令列・挙動不変、cache hit で実証)。観測者効果も実測:
  noinline fix10 = 2,623,221 vs stock 2,603,521 = **+0.76% (floor 3.0% 内、inert)** → 機序分析が stock に転移する。

### ドライバ + 実測 (`backoff_profile.py`, 直列・pgrep gate)
write-heavy で backoff {none,2,5,10,25,50,100us} を `perf record -e cycles,instructions` → `Backoff::backoff` の
cycle%/instruction% を分離 → **有用 IPC = (全命令−spin命令)/(全cycle−spin cycle)**。

### 結果 — [P0] 解消 (sweet-spot) + 正直な留保 + 新発見
- **sweet-spot 域 (0-10us, ピーク帯) で有用 IPC 一定** (1.92/1.96/2.01/1.94, 散布 4.4%)。total IPC は 1.92→1.09 崩壊
  (全域 117.7%) = **純 spin 希釈** (fix10 で cyc 48.7%/instr 8.5%)。**「なぜ fix10 が速いか」= abort 半減 (82→49%) が
  有用 IPC 不変のまま効いた**。元の積モデルが peak を 25us に外したのは ipc 項に spin 混入の total_ipc を使ったから。
- **正直な留保**: K_useful は一定でない (5.24M→1.47M, -72%) → 「有用 IPC で積モデルが定数 K で救われる」は**不成立**。
  言えるのは「sweet-spot の total IPC 低下 = spin 希釈」まで。predictive な積モデルは主張しない。
- **新発見 (第二次効果)**: over-throttle 域 (25-100us) で有用 IPC **自体**が低下 (1.94→1.47) = 待ちすぎは spin 税だけ
  でなく有用仕事効率も削る → stock 適応 ~560us 駐車の敗因 (最悪点) を裏付け。
- profiler.md (agent-architecture 仕様) を実体化し実データで実走 → hotspot/scale-risk/mechanism/uncertainty を構造化で返した
  (critic の P2-3「ipc 崩壊」帰属を「sweet-spot の崩壊は有用効率でなく spin 希釈」と精緻化)。critic.md の noise floor を
  A2 の between-run 3.0% に更新 (A2 配線漏れの修正)。

詳細 insight 追記 [[2026-06-22_p2-case-study-backoff-synthesis]] / decisions D20。データ
`output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.{json,md}`。

### 次の一手
1. **P2-5 (LLM 誘導探索 vs 全探索)** — Phase 2 主実験 (critic ablation の定量化が残る最大項目)。near_floor が close call 裏取り。
2. (任意) backoff profile を balanced でも取る (write-heavy で [P0] は閉じたが対照として)。over-throttle 有用 IPC 低下の機序
   (MLP 低下 vs cache 余熱) の分離。
3. **Phase 3 着手前 must** (S1/S2/S4/H3) + campaign-id drift (C1) 恒久対応は Phase 3 直前に。

## 2026-06-29 — P2-5 着手: 設計を敵対的検証で固め、replay 基盤 + ベースラインで negative result を精密化

P2-5 (LLM 誘導探索 vs 全探索) に着手。多エージェント workflow (Map6→Design→Critique3→Finalize) で設計を組み、
敵対的妥当性検証 (リーク/小N/ベースライン公平性) にかけた結果、**silo 8 では「誘導が速い」を headline にできない**
ことが判明 → ユーザー承認のもと **negative result + critic ablation** に枠組みを確定。

### 実測値の直接検証 (P2-2 WAL から再計算)
silo 8 genome は実質 **BACK_OFF=0 の1ビットでほぼ決まる自明空間**。winner-tied set (between-run floor 3.0% 内の
equivalence class) = read-heavy **k=4** (空間の半分、上位4=全BACK_OFF=0 が2.57%以内→その下77%崖) /
balanced・write-heavy **k=1** (B0-L-W0、2位が7.08%/11.49%下)。手動 python 再計算と replay.py が完全一致。

### replay 基盤 + ベースライン (新規直列計測ゼロ = 規律4 コスト0)
- `orchestrator/campaign/replay.py` — P2-2 の 3 campaign WAL を **dir 名 prefix で discover** (C1 campaign-id drift
  回避: 現 config の id 再計算は e2e2d91e 等で既存 dir 5ffcabad 等と食い違うと実測確認) し、{canonical genome →
  fitness/tps5/LI/certified} の landscape を構築。replay_evaluate で配る。winner_tied_set = compare の no-difference
  連結成分。committed のみ採用 (A: atomicity)。8 genome 全 certified を assert。自己テストで手動検証と一致。
- `orchestrator/campaign/search_baselines.py` — random (解析 P(j)=C(N-j,k-1)/C(N,k)・期待 (N+1)/(k+1) + 経験) /
  **critic 無し貪欲** (digest.axis_effects の勾配のみ、LLM なし) / オラクル天井 (初手ランダム制約下 E=2-k/N) /
  確率優越 P(戦略<random)。

### 結果 — negative result が「空間に余地なし」でなく「機械的勾配は余地を取れない」に精密化
| workload | k | random | critic無し貪欲 | オラクル天井 | P(貪欲<random) |
|---|---|---|---|---|---|
| read-heavy | 4 | 1.80 | 1.76 | 1.50 | 0.326 |
| balanced | 1 | 4.50 | 4.23 | **1.88** | 0.471 |
| write-heavy | 1 | 4.50 | 4.36 | **1.88** | 0.455 |

read-heavy (k=4) はどの戦略にも余地なし=到達判定が情報を持たない (主張対象外)。**k=1 は完璧なオラクルなら
2.6本削減の余地が構造的にあるが、digest の機械的貪欲はゼロしか取れない** (P(貪欲<random) 全て 0.5 未満)。
(※2026-07-02 D29 で撤回: この P 列 = p_lt は同分布でも 0.5 を下回る系統バイアスを持ち、確率優越 a への
再校正後は貪欲は balanced で random より有意に速い (a=0.533, exact p≈0.005)。同日エントリ参照。)
→ 残る唯一の鋭い問い: **LLM critic の帰属知能は機械的貪欲を超えてオラクル天井 (1.9) に近づくか?** 効果量が大きい
(貪欲4.3 vs オラクル1.9) ので小Kで判別可能。誘導アームが確認作業でなく本実験になった。

### 誘導 LLM アーム実走 → P2-5 完了 (negative result 確定)
誘導ハーネス (guided.py = critic に評価済み digest と未評価候補だけ見せ fitness/到達は伏せる + online_digest の
実行時 assert + 検疫) と中立プロンプト critic-experiment.md (critic.md から最適解の literal を物理削除) を実装。
headless claude CLI が無いため、各試行を fresh エージェント (本会話=答えを知っている を見ない) が guided.py を
Bash で駆動する形に。中立 critic を **30 試行** (balanced/write-heavy 各12 + read-heavy 6) workflow で並列実走。

結果 (到達本数、未到達=予算上限 N=8 算入):
| workload | k | random | オラクル天井 | 貪欲(LLMなし) | 誘導(LLM) | P(誘導<random) | 誤収束 |
|---|---|---|---|---|---|---|---|
| read-heavy | 4 | 1.80 | 1.50 | 1.76 | 1.67 | 0.357 | 0/6 |
| balanced | 1 | 4.50 | 1.88 | 4.23 | 3.75 | 0.531 | 0/12 |
| write-heavy | 1 | 4.50 | 1.88 | 4.36 | **6.33** | 0.208 | **8/12** |

- balanced (clean な BACK_OFF=0 支配): 誘導が僅かに有利だが P=0.531 で有意でなく、オラクル余地 2.62 本の 1/4 のみ。
  (※2026-07-02 D29 で再校正: この表の P 列 = p_lt は系統バイアス込み。a 基準の正確な読みは同日エントリと
  insight 追記参照 — 総合結論は不変、支柱は「vs 貪欲 無優位 + deceptive で貪欲比有意に有害」へ。)
- **write-heavy (deceptive、BACK_OFF=1 の B1-T-W0 が実2位 −11%)**: 誘導が random/貪欲より**遅い**。誤収束 8/12 で
  critic が BACK_OFF=1 genome 等に確信停止し winner B0-L-W0 を評価しない。clean な balanced で校正された自信ある帰属が
  誤誘導 + 早期停止 → **critic の知能が deceptive 帯で負債**。random/貪欲は早期停止しないので必ず当てる。
- 結論: silo 8 では誘導の価値は実証できず空間拡大が前提 = negative result。P2-4 backoff 合成 (空間外で勝つ positive) と
  対比し「フラグ探索は自明→価値は合成にある→Phase 3」が Phase 2 の物語。

成果物: insight 2026-06-29_p2-5-guided-vs-enumeration.md / decisions D21 / phase2.md P2-5 完了。集計は
`output/campaigns/p2-5-summary.json` (per-trial 軌跡で永続化、raw 試行 WAL は軌跡を summary に取り込み削除し
fitness は P2-2 WAL = 証拠連鎖保持)。テスト 8 追加 (test_guided、リーク assert/到達/random期待値1.80/連結成分)。

### 次の一手
- **Phase 2 完了**。残るは任意項 (空間拡大 cicada/oze = critic 価値実証の前提だが S1 trace-hook 拡張を要す) と
  **Phase 3 着手前 must** (S1/S2/S4/H3) + campaign-id drift (C1) 恒久対応。Phase 3 (LLM が別 protocol/コードを合成) で
  これらが load-bearing になる。critic の確信度校正 (deceptive 帯で早期停止を抑える) も Phase 3 設計教訓。

## 2026-06-29 (続き) — S4: 規律3 の構造化 anomaly 配線 (Phase 3 着手前 must の最重要)

Phase 3 着手前 must のうち最も規律中核の S4 を消化。**問題を実コードで裏取り** (規律6): verifier は既に豊かな
構造化 anomaly (cycle/edge/EdgeReason/integrity) を `result_to_dict` で持つが、`pipeline.py` の境界で
STAGE_VERIFY_DONE は `anomalies: len(...)` = 件数に潰し、verify-red の `_abort` payload は `{"reason": verdict}`
のみ = **「なぜ壊れたか」を完全に捨てていた**。Phase 2 (全緑) で無害、赤を出す Phase 3 で規律3 が死ぬ箇所。

- **生産側** (`pipeline.py`): verify-red 時に `result_to_dict(vr)` (使い捨て trace_dir は除く) を abort payload の
  `{"verify": ...}` に載せる。
- **読み出し経路** (`critic/digest.py`): `load_rejections(layout)` = abort の verify 構造を拾い `Rejection`
  (genome/verdict/anomalies/integrity) で返す (`load_workload` の緑読みと対をなす赤読み)。build-error 等
  verify を持たない abort は除外。consumer (critic/planner が読んで依存を断つ variant を作る) は Phase 3 = 規律5。
- **テスト**: mock を実 VerifyResult に差し替え (result_to_dict 経路を忠実化)、生産側 (abort payload に cycle/edge/
  reason が載る、test_campaign +1) と読み出し側 (load_rejections が構造化を拾い build-error を除外、test_critic +1)
  を回帰。broken-silo end-to-end は Phase 1 確立済 + buildcache が genome キーで patch 状態と衝突する罠ゆえ
  mock/fixture で回帰 (全テスト緑: campaign34/critic6/verifier16/guided8/stability20/reports8)。

## 2026-06-29 (続き) — Phase 3 (LLM コード合成) kickoff 設計確定 (ユーザー承認)

Phase 2 完了 + S4 を受け、ユーザー判断で Phase 3 (合成 = 本丸) に着手。多エージェント workflow
(Map5→Design→Critique3[reward-hack/スコープ過剰/正しさゲート]→Finalize) で kickoff を設計し敵対検証。
**設計を提示しユーザー合意 → 実装へ** (phase3.md / decisions D22)。

**敵対的検証が draft を大きく改善:**
- **first target を sort-strategy → 純 timing (静的 backoff) へ撤回** (3 批判全員 high severity 一致)。実コード裏取り:
  verifier は lock 獲得順を emit しない (transaction.cc:517-540) → lock 経路は certify 不能 (規律2 の穴) / silo は
  no-wait 即 abort ゆえ「sort=デッドロック回避」は誤診断で動かすのは liveness / 現 CorrectnessWorkload は lock 競合を
  踏まない。純 timing は abort-path タイミングのみ = 正しさ攻撃面が構造的に最小・P2-4 で certified 実証済。
- **EVOLVE-BLOCK 機構** = P2-4 inert-patch (D18) の一般化 (マーカー + #if coder枝/#else stock逐語、coder は #if のみ、
  型/header 追加禁止 = data-structure 観測者効果対策)。
- **identity の穴を塞ぐ**: cache_key を preprocess 後 (cpp -E) ハッシュにし variant_id (WAL キー) にも織り込む
  (生 sha256 だとマーカー挿入で全 miss=D18 inert 継承が破れる / variant_id は canonical() のみ hash ゆえ同フラグ別 diff が alias)。
- **COMMIT を書く唯一の経路は pipeline.evaluate** (guided.py の replay-fake certified は live variant に再利用しない)。
- **観測者効果二重検査** (trace/perf object diff、nm name-based の穴を埋める)。

**blocking must** = H3 hooks / cache_key+variant_id 拡張 / 観測者効果二重検査。S2/S1/C1 は純 timing kickoff では
non-blocking (S2 は sort 段で gate 条件に昇格)。**新規実体化は coder のみ** (critic/profiler 再利用、auditor/planner 後続)。

### 次の一手 (実装、blocking 順)
cache_key+variant_id honest 拡張 → EVOLVE-BLOCK template patch → H3 hooks 2本+settings.json → 観測者二重検査 →
coder.md + 純 timing variant 1本で 1周 (まず #else 逐語複写の no-op で stock cache-hit 実証) → broken-silo 回帰。

## 2026-06-30 — Phase 3 kickoff タスク1: source_digest (identity を「コードの差」まで覆う) を敵対レビュー駆動で実装

kickoff の blocking タスク1 (cache_key + variant_id の honest 拡張) を、**設計を多エージェント 3 レンズ
(honest / 列挙漏れ / 最小性) 敵対レビューで固めてから**実装。レビューは 3 レンズとも実機で**偽 cache hit を
構築**して設計の急所を炙り出した (例: レンズC が `#ifdef Linux` で枝の中身だけ違う 2 variant を同一 digest に
化けさせた)。設計判断は decisions D23。

### 方式 E を実機実証 (preprocess 後ハッシュ)
backoff.hh から `#include` を除去し `g++ -E -P -undef -nostdinc -Werror=undef -D<flags>` で preprocess
(= #if/#else 解決 + コメント除去) した出力を sha256。include 展開ゼロ (84 行)・環境非依存。
- **(a) inert** (`BACKOFF_FIXED=-1`) の出力は HEAD (patch 前) と**同一 sha256** `7664020a` → D18 inert 実証を継承。
- **(b)** `BACKOFF_FIXED=50`/`10` で別 digest (alias 防止)、`-1` は #else = stock。
- defines = `Options.cmake` の `set(CCBENCH_<NAME> <v> CACHE ...)` 既定 (CCBENCH_ 剥がし・クォート剥がし・
  空値 unset) を base に `genome.flags` で上書き。未定義マクロ 0 扱い穴を base が塞ぐ。

### 設計の急所と対策 (D23)
- **道Y (digest==実枝を構造保証):** `-undef` cpp 環境は実ビルドのマクロ環境 (-DLinux/-DNDEBUG/builtin/TU の
  GLOBAL_VALUE_DEFINE) と乖離する。digest を実ビルド環境で取る (道X) と builtin `__DATE__` が非決定 + compile_
  commands は configure 後で cache_key と鶏卵。→ EVOLVE-BLOCK 内の生 #if/builtin を **hook (タスク3) で禁止**し
  骨格 #if の既知マクロだけが枝を決める設計に倒す。digest 側の防壁は `-Werror=undef` (#if/#elif の供給漏れを fails-closed)。
- **TOCTOU:** 旧 build() は cache_key と無関係に working-tree を素でコンパイルしていた。cache_key/variant_id に
  **working-tree 由来 src_token を織り込む**ことで materialization と identity を構造結合 (working-tree が変われば
  key が変わる)。
- **後方互換:** stock (working-tree==HEAD baseline) は src を `"stock"` に正規化し pre-image から省く → silo 8
  genome の vid (`b971a1d9f80a` 等) / ck (`silo_24dd2f7509_t0` 等) は不変 = 既存 P2-2 WAL/build-variants と整合。
- **fails-closed:** g++/git 失敗・供給漏れ・**allowlist 外改変** (template patch の touch 集合 `{Options.cmake,
  backoff.hh}` を超える transaction.cc 等の M) は停止 (identity 核に best-effort skip を持ち込まない)。

### 実装
- `orchestrator/campaign/source_digest.py` 新規 (parse_options_defaults / _cpp_normalize / compute / baseline /
  src_token / assert_worktree_within_allowlist)。`buildcache.cache_key`+`build()` と `pipeline.variant_id`+`evaluate`
  に src_token を織り込み (evaluate は build 前に 1 回計算し trace/perf で共有、identity-error は fails-closed abort)。
- テスト 7 追加 (test_campaign 34→41、全 126 緑): 後方互換 golden / Options パース / stock roundtrip / FIXED 別 id /
  供給漏れ fails-closed / コメント不感・挙動敏感 / allowlist。source_digest は実 g++/git に依存するので段階遷移
  テスト (`_mock_pipeline`) では mock し、source_digest 自体は専用テストで実機検証。

### 次の一手
タスク2 (EVOLVE-BLOCK template patch: backoff.hh の BACKOFF_FIXED 周辺にマーカー骨格 + #if coder枝/#else stock逐語)。
既存 silo-backoff-fixed.patch が #if/#else を既に持つので、`// EVOLVE-BLOCK-BEGIN/END` マーカーを足し inert が
preprocess 後同一 digest であることを再確認する。blocking 順で H3 hooks (道Y の機械執行) → 観測者二重検査 → 配線 1 周。

## 2026-06-30 (続き) — Phase 3 kickoff タスク2: EVOLVE-BLOCK マーカー画定 + 敵対レビュー

kickoff の blocking タスク2 (EVOLVE-BLOCK template patch) を実装し、3 レンズ敵対レビューで固めた。

### 実装 (マーカー骨格 = coder の編集面)
- `backoff.hh` の `backoff()` 内 `now_backoff` 計算 (`BACKOFF_FIXED` の `#if/#else/#endif`) を
  `// EVOLVE-BLOCK-BEGIN silo-backoff-magnitude` 〜 `END` で画定。既存コード行は **byte 不変**、説明コメントを
  折り込んだだけ。`#if` 枝=coder 合成枝 / `#else` 枝=stock 逐語温存 / マーカー・骨格=不可触 (P2-4 inert-patch
  D18 の一般化)。`BACKOFF_NOINLINE` の診断計器は EVOLVE-BLOCK 外に保持 (coder 不可触)。
- **inert を preprocess 後ハッシュで実証:** マーカーは `//` コメントゆえ `cpp -E -P` で除去 + 既定
  `BACKOFF_FIXED=-1` が `#else`=stock を選ぶ → working-tree の preprocess 出力が HEAD 原本と **byte-identical**
  (sha256 `7664020a`、D23 と不変) → stock genome は cache-hit (規律2・観測者効果なし)。`BACKOFF_FIXED=50`/`10`
  は別 digest (alias なし)、silo 8 golden variant_id/cache_key 不変 (後方互換)。
- `silo-backoff-fixed.patch` をマーカー込みで再生成 (reverse-check OK = clean stock から再現可)、
  `patches/README.md` に EVOLVE-BLOCK 節、`test_evolve_block_markers_structure_and_inert` 追加 (127 passed)。

### 敵対レビュー (workflow 3 レンズ = 観測者効果 / 偽 cache hit / scope·規律、10 エージェント) → confirmed 4 / refuted 3
- **F1 (medium) `Options.cmake` digest 被覆ギャップ:** digest 対象 `EVOLVE_BLOCK_SOURCES`=backoff.hh のみ vs
  編集許可 `ALLOWLIST`={Options.cmake, backoff.hh} の不一致。`VAL_SIZE` 等を変えると別バイナリなのに
  src_token/cache_key/variant_id 不変 = 偽 hit (実機 exploit 済・revert 済)。**タスク2 由来でなく source_digest
  (タスク1/D23) の既存ギャップ。** identity 側で塞ぐと template patch の sentinel で後方互換が壊れる →
  **タスク3 (H3 hook) で coder の編集面を `#if` 枝に絞り Options を coder 不可触にして塞ぐ** (D24)。発火経路は
  coder 未実装ゆえ現状人間 template のみで潜在。
- **F2 (low) `-undef` cpp が `#if` 枝内の build 時マクロ/builtin の「値」を素通し:** D23 道Y が既知の hook 執行面 →
  タスク3 scope。
- **F3 (nit) phase3.md の `#if <AXIS> > 0` 文言誤り** (実装は `>= 0`/sentinel=-1) → phase3.md を整合修正。
- **F4 (nit) 説明コメント内の生プリプロセッサトークン** (`#if`/`__DATE__` 等) が hook substring 走査の誤検出罠 →
  コメント散文化 + hook は行頭アンカー走査と phase3.md に明記。
- **refuted 3 (設計通り):** `#else` 改変は digest 不感 (canonical に FIXED が入り衝突不能) / `#else` 不可触は
  hook 待ち (非ブロッキング繰延) / signed 比較は cmake default + `-Werror=undef` の二重ガードで到達不能。

成果物: insight `2026-06-30_phase3-task2-evolve-block-adversarial-review.md` / decisions D24 / phase3.md
(EVOLVE-BLOCK 機構の極性整合 + タスク3 に F1/F2 取り込み + 残存リスク追記)。

### 次の一手
タスク3 (H3 hooks 2 本 + `.claude/settings.json`): (hook1) EVOLVE-BLOCK 外 / `#ifdef TRACE` 外への検証専用
フィールド書き込み阻止 (規律1)、(hook2) coder の Write を EVOLVE-BLOCK の `#if` 枝に限定 (F1: Options を coder
不可触に) + 領域内の生条件指令・非決定 builtin 禁止 (F2/D23 道Y、行頭アンカー走査) + Bash リダイレクト穴対策。
盛らない (この 2 本)。blocking 順で 観測者二重検査 → coder.md + 純 timing variant 配線 1 周 → broken-silo 回帰。

## 2026-06-30 (続き) — audit [HIGH] 割り込み: D23 src_token の consumer 追従を完遂 (loop + backoff_repro)

Phase 3 タスク3 着手前に、別セッションの全体監査 `docs/audit-2026-06-30.md` が挙げた [HIGH] をユーザー指示で
優先対応。素性が別セッションゆえ独立裏取り (規律6) + 敵対検証で固めた。

### 裏取り + 修正
- **[HIGH] loop が D23 src_token を消費側で追従していない:** loop の skip/abort キーが stock id、pipeline.
  evaluate は src_token id で WAL を書く → coder variant で乖離しリカバリ冪等性 D / 例外 abort 整合 A が破綻
  (Phase 2 は全 stock で潜伏)。`git show HEAD` で裏取り。
- 修正: `source_digest.resolve` (allowlist 検査 + src_token の単一窓口、WAL なし、fails-closed) を新設。
  `pipeline.evaluate` に src_token 引数 (loop が確定済みを渡す / 直接 caller は自己計算、後方互換)。loop が
  resolve → `variant_id(g, src_tok)` で skip/dedup → evaluate に渡す。回帰テスト3本。

### 敵対検証 (3 レンズ / 13 エージェント) → confirmed 8 / refuted 2
- **[medium] backoff_repro が同類 stale consumer (新発見):** `_bench_tps` が stock id で WAL を引き
  BACKOFF_FIXED genome を取りこぼし P2 backoff 再現 ([P0] +38%/+11%) が silently 判定不能。`run_campaign` の
  EvalResult.variant から引くよう同時修正 (確定点を再計算しない)。
- **[medium] identity-error poison stock id:** transient 失敗で stock id terminal abort → 修復後永久 skip。
  **HEAD でも同一挙動** (私の修正は不変、検証の「newly creates」は誤帰属) = 既存の terminal-abort 設計限界。
  fails-closed (規律2 不変)。恒久対処 (retryable マーク) は別タスクに繰延。
- [low] dedup テストが skip-key を区別しない → docstring 正直化 (load-bearing は recovery テストが担う)。
- nit: pipeline self-compute identity-error テスト追加 / DRY (production 排他) / TOCTOU (既存・worktree 隔離繰延)。
- refuted: allowlist 3 回チェック (冪等)、silo 8 後方互換 (resolve→variant_id でも golden 不変)。

成果物: insight 2026-06-30_loop-src-token-consumer-followthrough.md / decisions D25 / 全 131 passed。

### 次の一手
- **Phase 3 タスク3 (H3 hooks)** に戻る (本来の blocking 順)。
- **identity-error poison (medium, 既存)** の恒久対処 (identity-error abort を retryable にマーク) は別タスクで
  検討 (ユーザー判断)。`docs/audit-2026-06-30.md` の残り (online_digest assert 恒真 [MED] 等) も別セッション成果
  として要確認。

## 2026-06-30 (続き) — identity-error poison を retryable で解消 (D25 の繰延項を前倒し)

ユーザー「保守的に進めるなら」の判断で、D25 で繰延した identity-error poison (medium) を前倒し解消。transient
infra 失敗 (g++ 一時不在等) で identity-error abort になった stock genome が環境修復後も永久 skip され stock
baseline を silently drop する穴 (HEAD でも同一挙動の既存の terminal-abort 設計限界、fails-closed)。loop の
recovery seed で `reason="identity-error"` の abort を permanent-skip から外し再評価 (genome-intrinsic な失敗とは
区別、commit 済みは除外)。overnight 耐性は不変 (永続エラーは abort 隔離でクラッシュループにならない)。回帰テスト
`test_loop_identity_error_is_retryable_after_repair` (run1 abort → run2 修復で再評価)。132 passed。D25 更新。

### 次の一手
- **Phase 3 タスク3 (H3 hooks)** に戻る (本来の blocking 順)。`docs/audit-2026-06-30.md` の残り ([MED]
  online_digest assert 恒真 等) は別セッション成果として要確認。

## 2026-06-30 (続き) — audit 全体監査の独立裏取り + 規律直結の軽量掃除

別セッションの全体監査 `docs/audit-2026-06-30.md` (10 次元・57 エージェント・43 項目) のうち本セッション未対応の
MED 以上 + 規律直結 LOW + 再現性/ドキュメント代表 11 件を、ワークフロー (11 エージェント並列・約 100 秒) で
**実コードに当てて独立裏取り** (規律6: 素性が別セッション)。

### 裏取り: real 10 / refuted 1、**Phase 3 blocker 0**
audit の機序記述は概ね正確 (誇張は副次主張レベル: online_digest のコメント誤記主張・backoff-if の「sha256 不変」・
phase3 の worklog 筆頭残存は誤り/誇張)。
- **refuted:** parser が W 行版を無検証破棄 — verifier は W 版を DSG 入力に使わず (版は C 行 commit のみ)
  false-green 不能。hardening nit であって正しさゲートの穴ではない。

### 軽量掃除 (自律可・低リスク、4 コミット)
1. **verifier genesis_commits を JSON payload に** (規律3): `result_to_dict` の integrity 4 カウンタのうち
   genesis_commits だけ機械可読経路 (→WAL→`load_rejections`→planner) から欠けていた穴を 1 行 + テストで塞ぐ。
2. **online_digest 二重防壁の honest 化** (D26): 「二重の関所」が同一 WAL 由来で恒真と判明 → 偽装で取り繕わず
   docstring を実態 (配線 sanity) に正す。コードロジック不変。
3. **calibrator rep 失敗の握り** (規律3): rep ループに try/except、1 rep 失敗で測定点全体を捨てず残りで median、
   握り潰さず notes に構造化記録、全 rep 失敗のみ原因集約して fail-closed + テスト 2 本。
4. **docs 鮮度**: README 現在地を Phase 2 完了/Phase 3 着手へ + 必読を phase3.md へ、phase3.md タスク1/2 を [x]。

テスト 134 全緑 (calibrator +2)。

### 人間判断に委ねた項目 (Claude 自律不可)
- **backoff-if (`#if BACKOFF_FIXED >= 0` 未定義時 backoff=0)**: EVOLVE-BLOCK 内の coder 不可触骨格 #if
  (D22 で人間専管)。`defined()` ガード追加は inert digest を変えるため source_digest baseline (7664020a) 再固定も
  要る。off-path のみ (正規 CMake は常に `-DBACKOFF_FIXED=-1` 供給) で Phase 3 を塞がない → 人間判断待ち。

### 残り backlog
- allowlist untracked #include 抜け穴・verifier-bash 機械執行 → Phase 3 タスク3 (hooks) と同時 (coder 起動の直前防壁)。
- c1-drift reports (replay で読める)・p2_2 records assert (値一致) → 実害ゼロで繰延。

### 次の一手
- **Phase 3 タスク3 (H3 hooks)** に着手 (本来の blocking 順)。allowlist #include reject + designated patch 以外
  Write 拒否を同梱 (上記 backlog の編集面ギャップを塞ぐ)。

## 2026-06-30 (続き) — 「Phase 完了監査と引き継ぎ監査」を方法論として明文化 (D27)

ユーザーの設計相談「性能の低い AI 作業が入った時の是正監査ステップを roadmap/CLAUDE.md に追加すべきか」を、
証拠 (過去 13 劣化事例の棚卸し + 既存防壁のカバレッジ + 文書の収まり所) と 3 立場 panel (賛成/慎重/折衷) の
ワークフロー (7 エージェント) で検討。

**結論 = lightweight-trigger (D27):** 新しい監査フェーズ/エージェントは作らない (規律5 盛らない)。過去 13 劣化
事例のうち 12 は既に systematic に捕まっており (敵対検証 / 規律6 独立裏取り / Phase 完了監査)、穴は「捕まえる手段」
でなく「回す契機」の規律化欠如だけ (計測汚染が pgrep 目視で偶然検出・audit 43 項目が別セッションで偶発蓄積)。既存
運用の発火条件を明文化するのが規律5 と両立する唯一の解。

ユーザー「両方一緒にいれる」指示で実施:
- **roadmap §3.7** 新設「Phase 完了監査と引き継ぎ監査 (劣化の遡及検出)」。前向き層 (§3.4 reward hacking 対策 /
  §3.6 測定安定性) と対をなす遡及層。推奨手順 (必須ゲートでない)、Phase3 auditor との直交、監査者自身の劣化という
  限界まで記載。
- **CLAUDE.md 規律6** に発火条件 1 文を追記 (別セッション/別 AI 作業物の取り込み・Phase 境界・overnight 後に独立
  敵対裏取り)。憲法だがユーザー直接指示で実施。詳細は roadmap §3.7 に委譲し 1 文に留める (二重管理回避)。
- **協議合意した改訂ゆえ版管理セレモニー不要** (CLAUDE.md 改訂規律の協議改訂パス: 版数据え置き・history 凍結なし)、
  設計判断は D27 に記録。

コミット前に改訂自体を独立エージェントで敵対レビュー (§3.7 の「採用・コミット前に監査」を自身に適用 = ドッグフーディング)。
real 2 件を指摘され反映: (1) [HIGH] 本 worklog エントリの記録漏れ (Edit が未適用のまま放置) を追加、(2) [MED]
roadmap §3.7 の「audit を real 10/refuted 1 で裏取り」は監査全体 43 項目でなく裏取りサブセット 11 件の結果である
旨を明示。事実誤り (D 番号・参照・事例引用)・規律矛盾・セレモニー判断・閉じ込めリスクは問題なしと確認。

### 次の一手
- **Phase 3 タスク3 (H3 hooks)** に着手 (本来の blocking 順、変わらず)。

## 2026-07-02 — Phase 3 着手前 引き継ぎ監査 (workflow 再監査) を audit バックログに反映

新セッションでの再開に備え、リポジトリ全体を独立 workflow (8観点 × 21 エージェント、各 finding を敵対検証) で
再監査した (roadmap §3.7 / D27 の引き継ぎ監査を発火 = Phase 境界トリガ)。**結論は 6/30 audit と一致: 致命バグ・
false-green・規律1-3 破りゼロ。** 11 精査 → 10 REAL / 1 refuted、全件が `docs/audit-2026-06-30.md` に既出 or 追記で
カバー。10 件は「doc 鮮度・over-claim」と「歴史的 campaign の材料レポート射影器が沈黙して空を返す C1 drift」で、
計測データ・正しさ判定には波及しない。

`docs/audit-2026-06-30.md` に反映 (新規ファイルは作らず living なバックログを差分更新、規律5):
- 冒頭に「2026-07-02 再監査」差分サマリ (結論・優先順・未検証領域の完全性クリティック)。
- §2 の C1 drift 項目に `critic/digest.py:215`(`load_p2_2_digests`)を 3 本目として追記、`worklog.md:596`「digest.py で
  3 workload 出力」が現状偽 (空を返す) を明記、severity [LOW→MED]、6/30 の「exit 1」を 7/2 実測 exit 0 に訂正。
- §5 に新規3件: `CLAUDE.md:19` 現在地 stale [MED]・`roadmap.md:231` §6 submodule 運用 D16 未追従・`guided.py:12`
  docstring D26 未追従 (consumer 取り残し)。既存の §5/§8 項目 (roadmap §8・decisions:256・phase2:54・ロスター) も 7/2 REAL 再確認。

**未検証で残した領域 (次の監査候補、完全性クリティック):** 規律1 の `#ifdef TRACE` 別ビルド分離の実挙動、verifier
DSG/G2 検出の偽陰性、hooks 発火 (H3 未実体化)、Phase 3 EVOLVE-BLOCK/source_digest のコード裏取り、
fitness/admission/median の数値正当性。submodule gitlink pin (dff0f1e) と patch 完全一致は前タスクで確認済み。

### 次の一手 (新セッション開始点)
1. **`CLAUDE.md:19` 現在地の更新** (audit §5 🔁 [MED]): Phase 3 kickoff タスク1/2 (source_digest/EVOLVE-BLOCK,
   D22-D27) 完了を反映し C1 を「消化すべき残 must」から外す。次セッションの誤誘導を断つ最優先。**憲法側ゆえ人間確認。**
2. **Phase 3 タスク3 (H3 hooks)** に着手 (本来の blocking 順)。
3. C1 drift 恒久対応 (phase2.md:154-159 選択肢a): report/critic 3 本を `replay.discover_p2_2_dir` 方式に統一。

## 2026-07-02 (続き) — 「現状の洗練」検査: audit 台帳の全項目裏取り + 未検証領域の新規検査

ユーザー指示「進捗とコードを検査して改善 (前進でなく洗練)」を受け、ultracode workflow (~80 エージェント) で
(a) audit バックログ全項目の実態突合 (8 グループ)、(b) 7/2 再監査が「未検証」と残した領域の新規検査 (6 観点:
規律1 TRACE 分離実挙動 / verifier DSG 偽陰性 / source_digest・EVOLVE-BLOCK 裏取り / fitness・統計の数値正当性 /
直近修正コミット群のレビュー / 簡素化・重複)、(c) 新規 finding の敵対検証 (誤検出疑い + 再現性の 2 名投票) を実施。

**backlog 裏取りの結論**: 台帳が実態より古かった — §1 HIGH loop src_token (19e0915)・§1 MED 回帰テスト (同)・
§2 MED rep 失敗 (1e2c01c)・§2 LOW genesis_commits (835ed9b)・§5 root README・§5 phase3 タスク1 は修正済みなのに
`[ ]` のままだった → 台帳を [x] 化 (本コミット)。残りは未対応で自律修正可 ~28 件 / 人間判断 3 件
(§6 submodule dirty の checkout・§2 backoff-if 骨格 #if=D22 人間専管 (6/30 判断を維持)・CLAUDE.md:154 の 7x7 旧表現)。

**新規 finding 36 件 (敵対検証で大半 REAL、UnicodeDecodeError 素通りの実害主張 1 件は棄却)。主要どころ:**
- [HIGH] verifier 偽陰性 (実証済み): trace 形式に完全性情報 (R/W 件数・終端マーカー) が無く、(a) txid 欠番 =
  trx 丸ごと欠落も (b) trx 尾部欠落 = C 行だけ残り R/W 消失も integrity に乗らず certified serializable になる —
  `verifier/parse.py`。部分 trace への防壁ゼロ。
- [HIGH] source_digest の盲領域: 対象ファイル内 `#ifdef GLOBAL_VALUE_DEFINE` ブロックが digest 前処理で
  剥がされ、挙動変更が同 digest = 偽 stock / 偽 cache hit — `campaign/source_digest.py:90`
- [HIGH/MED] D25 retryable の破れ: retryable 判定が `st.last` 依存のため、identity-error → 修復 → 再評価が
  in-flight クラッシュすると permanent skip が復活 (2 finder が独立指摘、実 run_campaign 3-run 再現済み) — `loop.py:60`
- [MED] calibrator CLI `--binary` に trace シンボル検査が無い (buildcache 経路のみ防壁あり) + buildcache の
  nm 不在/失敗が silent pass — 規律1 の防壁が経路依存
- [MED] pipeline: CV 算出不能 (nf.cv=None) が BENCH_DONE 後の log f-string で TypeError → 意図しない
  eval-exception abort + permanent skip — `pipeline.py:258`
- [MED] S4 consumer: `load_rejections` の Rejection が variant id / src_token を落とし、同 canonical 別コードの
  RED variant が planner 視点で alias する — `critic/digest.py:151`
- [MED] prob_superiority の離散 tie 校正: 同一分布でも p_lt≈0.41 (<0.5) となり、P2-5 の「誘導は勝たない」を
  実態より強く見せる方向のバイアス — `search_baselines.py:169`。P2-5 結論への波及は要精査
- [MED] 1e2c01c の rep 失敗 notes が calibration JSON/MD に出ずインメモリ止まり (「沈黙させない」が半分)
- [LOW 群] W 行 (epoch,tid) 無照合 / key 形式無検証 / genesis 番兵未満の版無検査 / between_run_floor None ガード /
  Gate1 の差分散 √2 補正漏れ / cache_key に cc・cxx 不含 / loop silent skip の WAL 痕跡ゼロ 等
- [簡素化] WAL リーダ 4 重実装・canonical パーサ 3 重・dead import 8 件・env_scope_dir 未使用・分位計算 2 実装・
  sys.path 汚染書法不一致 等 (大物の統合は規律5 と凍結スクリプト尊重で見送り、台帳追記に留める)

**修正計画 (コミット単位、上から順に実施。本エントリはセッション引き継ぎ用スナップショット):**
1. docs 鮮度一括 (roadmap §6 D16 相互参照 / §8 7x7→10 プロトコル / phase2:54 テスト数 / decisions:256 patch 名 /
   agent-arch critic-experiment 注記 / patches README broken-silo 手順)
2. コード内 docstring 鮮度 (guided.py D26 追従 / genome.py 行参照→シンボル / calibrator cli.py 出力名 /
   buildcache 補記 / fixtures README 凡例 / orchestrator README 実構成化)
3. agent spec 整合 (python→python3 ×4 / critic.md digest 引数 / 書き込み隔離文言の honest 化 §4 段1)
4. テスト品質 (_skip ヘルパで return 疑似スキップ可視化 / test_critic・test_guided の except Exception 枝 / tests/README)
5. calibrator 小修正 (clocks_per_us fallback を result に記録 / max_records 16m 統一)
6. verifier 硬化: 部分 trace の偽陰性を integrity で塞ぐ (txid 欠番 / W 行版照合 / key 正規化 / genesis 番兵) + テスト
7. campaign 硬化 (D25 retryable を last 履歴でなく reason 履歴で判定 / CV=None ガード / Rejection に id 追加 /
   records assert→例外 / cli --binary trace 検査 / nm fails-closed 化)
8. C1 drift: discover_p2_2_dir 方式を p2_2_report / backoff_sweep_report / critic digest の 3 本に統一 +
   p2_2 RECORDS/THREADS の calibration JSON 照合
9. rep 失敗 notes の永続化 (calibrator report の _point_to_dict に notes)
10. 統計系 (prob_superiority tie / Gate1 √2) — 数値結論に触るため修正内容を精査してから
11. simplify 低リスク分 (dead import 削除・env_scope_dir 整理)
12. CLAUDE.md 現在地更新 (独立コミット・報告で明示。絶対規律セクションは不触)
13. 台帳・worklog 最終同期 + テスト全緑確認 (ベースライン 134 passed 取得済み)

**人間判断待ち (実施しない):** submodule dirty の checkout (destructive、計測時の patch 再適用運用と絡む) /
backoff-if `#if defined()` ガード (D22 人間専管 + inert digest 再固定要、6/30 判断を維持) / CLAUDE.md:154 7x7 表現。

## 2026-07-02 (続き2) — 洗練セッション完了: 15 コミットで backlog + 新規 finding を消化

冒頭エントリ (「現状の洗練」検査) の修正計画を完遂した。テストは 134 → **143 全緑** (+9)、
bare runner 5 本 OK。コミット系列 (54aa6ec 引き継ぎ〜):

1. **docs/spec 鮮度** (d16f7dc, 8e06a37, a1661d2): roadmap §6/§8・phase2・decisions・agent-arch・
   patches README・guided/genome/cli/buildcache docstring・orchestrator README 実構成化・
   agent spec python3 + 書き込み隔離宣言の honest 化 (§4 段1)。
2. **テスト品質** (d96264f): skiputil で return 疑似スキップを両 runner とも SKIP 可視化、
   except Exception 枝、tests/README 新設。
3. **calibrator** (4d1f25f): clocks_per_us フォールバックの成果物記録 + max_records 16m 統一。
4. **verifier 硬化** (36a1193): 部分 trace / 整合破れの偽陰性 4 種を integrity で遮断 —
   [HIGH] txid 欠番 (trx 丸ごと欠落が certified になる実証済み偽陰性)・W 行版照合・key 形式・
   genesis 番兵未満 + UnicodeDecodeError の ParseError 化。手製フィクスチャ p1 の txid を実仕様
   (0 始まり) に追従。実 Silo 184k txn で誤発火なし。
5. **campaign 硬化** (02b08eb, 9cde781, ec5aaaf, a649fe7): [HIGH] D25 retryable の破れ
   (last→last_terminal 基準化、in-flight クラッシュで permanent skip が復活する穴)・identity skip
   可視化・CV=None admission・records assert→例外・TRACE 予約名 reject・規律1 防壁 fails-closed 化
   (calibrator CLI 入口 nm 検査新設 / buildcache nm silent pass 廃止)・cache_key に cc/cxx・
   S4 Rejection にコード軸 id (variant/src_token)・backoff_repro の resume 耐性。
6. **C1 drift 恒久対応** (065593a): discover_campaign_dir 統一で report/critic 3 本が歴史的
   campaign を再出力 (+38.3%/+11.3% の根拠 sweet spot 復活、再生成物は既存とバイト一致 =
   決定的再現の証明)。p2_2 に calibration 実行時照合。
7. **統計/可視性** (cf62e81): rep 失敗 notes の永続化 (JSON + WAL)・確率優越 a (tie 半加算) 追加・
   Gate1 √2 の統計的意味を docstring 化・between_run_floor None ガード。
8. **simplify** (f8f423a): dead import 6 件・repro_command 誤記 (reps=3→5) + .dat 再生成・
   env_scope_dir 集約。大物統合 (WAL リーダ 4 重等) は規律5 で見送り、台帳に方針記録。
9. **CLAUDE.md 現在地** (608a72b、独立コミット・人間レビュー用) + **D28** (warmup 意図的非対応,
   39a607e) + 台帳・worklog 同期 (本コミット)。

**人間判断待ち (実施していない):** (1) submodule dirty の checkout 戻し (destructive)、
(2) backoff-if `#if defined()` ガード (D22 人間専管 + inert digest 再固定)、(3) patches フォーマット
統一 (broken-silo 再生成 = 規律2 positive control の byte 一致検証を伴う)、(4) **P2-5 の主指標を
p_lt→a に置換 + p2-5-summary 再生成 + D21 結論文の再解釈** — p_lt の 0.5 基準は同分布でも 0.4375 と
出る系統バイアスで negative result を強める方向だった。a への置換で「誘導は有意に上回らず」の一部
(balanced) が変わる可能性があり、主張に触るため人間の指示で行う。

**持ち越し (台帳「2026-07-02 洗練検査」§参照):** trx 尾部欠落 (trace 形式拡張 = S1 と同時)、
build-error retryable 非対称 (Phase 3 abort payload 設計と同時)、digest への unstable 伝搬、
Gate1 √2 の閾値意味論 (Phase 3 設計判断)。

### 次の一手 (変わらず)
- **Phase 3 タスク3 (H3 hooks 実体化)** — §1 残り 2 項目 (allowlist untracked / hooks) を同梱。

## 2026-07-02 (続き3) — 人間判断待ち 4 件をユーザー承認のもと消化 (P2-5 再校正 D29 / backoff #error / patches 統一 / submodule clean)

ユーザー「その4件は対応した方が良さそうだよね?」の承認を受け、洗練セッションで人間判断待ちと
した 4 件を全て対応した。

1. **P2-5 指標再校正 (D29、39c44cc)** — 最重要。p_lt の系統バイアス (同分布 null=0.4375) を
   確率優越 a に置換。**敵対検証が機能した**: 当初解釈「balanced では誘導も random より有意に速い
   (t p=0.016)」を独立統計検証が exact 検定 (p=0.144)・Holm 補正・分散縮小 (大外れ回避) の指摘で
   棄却。確定した再解釈 =「貪欲は balanced で有意に速い (a=0.533, exact p≈0.005、旧『ゼロしか
   取れない』を撤回)。誘導は貪欲を超えず (A=0.581 有意差なし)、deceptive では貪欲より有意に有害
   (A=0.230, permutation p<10⁻⁴、打ち切り感度に頑健。機序 = 自信ある早期停止の負債)」。
   *(訂正 2026-07-03: 「p<10⁻⁴」は方式未記録の過大表示 — 厳密 permutation で p=2.52×10⁻⁴。
   Holm ×6 でも有意で結論不変。summary.json `correction_2026_07_03` / D29 末尾の訂正注記参照)*
   **D21 総合結論は不変・むしろ強化** (支柱が vs random から vs 貪欲 ablation へ移動)。
   成果物: p2-5-summary.json に recalibration 追記 (既存キー不変・再実行で消えないマージ保持) /
   insight 追記 / p2_5・search_baselines の a 主指標化 + null 校正テスト / D21 へのポインタ /
   phase2・README・CLAUDE.md の文言更新 / 本 worklog 過去 2 エントリに撤回・再校正の注記。
2. **backoff.hh 骨格に #ifndef+#error (4f7bb3c)** — audit 案の defined() ガードは実測で「gcc が
   短絡し -Werror=undef が発火しない = source_digest の fails-closed が黙って stock 縮退に弱まる」
   トレードオフが判明、より強い #error (全経路コンパイル停止) を採用。inert digest 7664020a /
   variant digest とも byte 一致を実測 (audit が懸念した baseline 再固定は不要)。round-trip 検証済み。
3. **patches フォーマット統一 (92e1cd8)** — broken-silo を git diff 形式に再生成。clean checkout に
   新旧 patch を適用した transaction.cc の byte 一致で規律2 positive control の不変を証明。
4. **submodule clean 戻し (d6bc750 で test 追従)** — dirty が silo-backoff-fixed.patch と完全一致
   (逆適用成功) を確認して checkout。gitlink dff0f1e 不変。patch 適用前提のテスト 3 本は skip として
   可視化される (140 passed + 3 skipped)。次回計測/Phase 3 ビルド時は patch を再適用する。

### 次の一手 (変わらず)
- **Phase 3 タスク3 (H3 hooks 実体化)**。

## 2026-07-03 — セッション運用ルールの明文化 (roadmap §3.8 新設 + CLAUDE.md 手順5、D31)

ユーザー問題提起「仕事を投げて一定時間経つとコンテキストが膨れ上がって質が低下する」を受け、
D27 が明示的に残した穴 (「同一セッション内の緩やかな劣化は前向き層に委ねる → 本質的に未解決」) を
運用ルールとして埋めた。協議合意の改訂ゆえ版数据え置き (版管理セレモニー不要)。

- **roadmap §3.8 新設 (§3.7 遡及層と対をなす前向き層)**: 劣化メカニズム 3 つを名指し
  (ロッシーな自動圧縮 / 自己一貫性バイアス = P2-5「自信ある早期停止の負債」と同型 / 読んだつもり
  ドリフト)。対策 4 ルール = 粘らず捨てる (自動圧縮が入ったら新サブタスクを始めず handoff を書いて
  セッションを終える) / handoff 自己完結基準 (fresh セッションが handoff + 現在地 + worklog 末尾
  だけで再開できる品質) / コンテキスト衛生 (生 trace・生ログ・WAL 全文を main context に入れず
  サブエージェント・digest 経由) / 圧縮跨ぎ再読。加えて **Phase 3 ループ主導権の原則**: 反復ループは
  orchestrator (Python) が回し LLM は iteration 単位で fresh に呼ぶ (品質がセッション寿命に依存しない。
  orchestrator-design.md 既存原則の適用)。設計原理 =「セッションの延命でなく、短命でも仕事が
  途切れない構造」。新機構は足さない (規律5)。§3.7 末尾の委譲文に §3.8 を配線。
- **CLAUDE.md 作業の進め方に項目 5** (短い配線のみ、詳細は §3.8 へ委譲 — D27 と同じパターン)。
- **decisions.md D31** (D30 は H3 hooks の別セッションが予約済みのため番号を跨いで追記)。
  却下した代替 = hook による機械的強制 (コンテキスト残量は hook から観測不能・proxy は誤発火、
  規律5)、対策不要 (圧縮はロッシー)。残るトレードオフ = 自己申告ベースの自己言及 (劣化した Claude
  自身が気づく必要)。下支えは既存の機械ゲート (規律2) + §3.7 遡及監査。

### 次の一手 (変わらず)
- **Phase 3 タスク3 (H3 hooks) の未コミット成果物の取り込み** — 別セッション進行中 (guard_write /
  guard_bash / settings.json / D30 記入待ち)。以後の残り blocking は観測者効果二重検査 → coder.md 全配線 1 周。

## 2026-07-03 — docs 全体の敵対検査 + H3 hooks の over-claim 撤回 + 方針 A 確定 (D30)

ユーザー指示「docs を検査し方向性・設計が優れているか検討して改善」を受け、docs 11 ファイルを 7 視点で
並列敵対検査 (Workflow) + 独立裏取り。**最重要検出 = H3 hooks の over-claim** (5 ファインダーが独立に検出)。

**規律6 の独立裏取りで確定した over-claim (git 履歴には未固定 = working tree のみ):** 前 2 セッション
(**2026-07-02 = hooks 実装 + 1 巡目敵対検証 15 finding / 2026-07-03 = 2 巡目敵対検証**、いずれも worklog 未記録
だったのを本エントリで補足。記録は insight `2026-07-02_...adversarial-review.md` / `2026-07-03_...round2-handoff.md`)
が phase3.md を「H3 hooks 完了・2 巡で硬化」・hooks/README を「配線済み」とマークしたが、実態は
(1) `.claude/settings.json = {}` で**未配線 = 第二防壁ゼロ**、(2) 2 巡目で **real 13 件 (critical 1 = コメント行連結で
コメント除去器を騙し `#define TRACE`/`__DATE__` を素通しさせる GW2R-1)**、(3) 参照先 **D30 が decisions.md に不在**
(宙吊り)、(4) 配線検査テスト `test_settings_json_wires_both_hooks` が赤 (実機確認: 18 passed / 1 skipped / 1 failed)。

**方針確定 = A (ユーザー承認):** 2 巡目 real の質が「テキスト検査で C++ 翻訳フェーズ・shell の完全性を負うのは
原理的に無理」を実証。→ hook を最小第二防壁に軽量化し、identity の honest さは source_digest の preprocess 後ハッシュ、
観測者効果の分離は観測者効果二重検査へ委譲 (「payload 検査が唯一の防壁」の単一障害点を放棄)。B (hook 強化続行 =
軍拡競争・規律5 と衝突) / C (記録のみ) を却下。

**docs 整合 (協議合意ゆえ版管理セレモニー不要):**
- **over-claim 撤回** — phase3.md タスク3 を `[ ]` (進行中・方針 A で再設計) に、must 分類表を「進行中」に、
  hooks/README.md を「実装済・未配線」に訂正。
- **D30 記入** (方針 A の設計判断、却下 B/C 込み)。D24 末尾に部分 supersede ポインタ、D31 冒頭の予約注記を実態化。
- **roadmap 反映** — §3.4-3 (hook = 最小第二防壁、identity/観測者効果は一次防壁)、§3.3 (ビルド等価性の「採用済み」
  stale を実態=symbol 不在 + Phase 3 で preprocess 二重検査に修正)、§2/§3.5 (P2-5 negative result の未反映 stale を
  「誘導は貪欲を超えず deceptive で有害・価値は空間外合成」に更新)。
- **Phase 3 主実験の評価設計を新設** (最大の設計欠落) — 完了定義が kickoff 配線実証しか無かったので、反証可能な主張・
  headline ベースライン集合 (silo stock / クロスプロトコル stock / ランダム変異 / 機械 sweep)・LLM 価値の ablation・
  統計計画 (確率優越 a + between-run floor)・失敗条件を phase3.md 冒頭に事前登録。backoff +38%/+11% が silo 内比較に
  閉じている弱点への対策も配線。
- **残存リスク追記** — S2 空振り認証 (abort≈0 で合成枝が verify 未実行のまま緑)、coder リーク制御未設計 (BACKOFF_FIXED
  勝ち筋がリポジトリ内既知)、観測者効果二重検査の述語が #ifdef TRACE 内側の挙動差を素通しする点、ハーネス自己保護の
  欠落 (orchestrator/hooks 自身が防護対象外)。agent-architecture.md coder 節に kickoff 制約の前進ポインタ。

**用語集 `docs/glossary.md` を新設 (ユーザー指示):** docs が説明なしに使う非自明用語を、専門外の査読者・将来の自分
向けに平易に定義。5 領域 (探索最適化 / 並行性制御DB / 評価測定統計 / 合成機構 / エージェント運用) を並列ファインダーで
横断収集 (142 用語→重複統合 118→執筆時に近接統合) し、私が一貫文体で 5 分類に整理。各項目は「教科書レベルの定義 +
izanagi での使われ方 + 参照先」の 2 段。roadmap 冒頭に発見ポインタを配線。動機 = ユーザーが「貪欲ベースライン・
オラクル天井・deceptive 構造」の意味を尋ね、docs には数値・結論はあるが用語の一般定義が無い (専門家前提で圧縮) と
判明したこと。定義は執筆時点のもので正典は各 docs 本文。

**コミットはしていない (ユーザー未指示)。** working tree に docs 変更 + 用語集 + 前セッションの hooks 実装/テストが
未コミットで併存。テストの唯一の赤 = `test_settings_json_wires_both_hooks` は未配線という実態と整合 (方針 A の配線 step で緑化)。

### 次の一手
- **本 docs 変更 + hooks 実装のコミット** (論理単位ごと、ユーザー承認後)。撤回は済んだので over-claim を履歴に入れない。
- 方針 A の実装順: (1) 一次防壁 (source_digest preprocess ハッシュ + 観測者効果二重検査) を先に load-bearing に →
  (2) hook を最小化 + false-positive 4 件除去 → (3) settings.json 配線 (matcher = `Write|Edit|MultiEdit|NotebookEdit` / `Bash`)。
- 未消化の docs 課題 (本セッションで flag のみ): C1 campaign-id drift の状態が 4 文書で食い違う / 「WAL proof chain」の
  実体定義が無い / 外的妥当性 (Threats to Validity) の集約が無い / coder 自律期の停止条件・fitness 採否・再試行方針が未予約。

## 2026-07-03 — Phase 2 完了監査 (実態突合) + 検出事項の修正

ユーザー指示「docs を調査し phase2 までの仕事がちゃんとできているか検査」。同日の docs 敵対検査
(前エントリ、設計・方向性が対象) と軸を変え、**完了主張 vs 実態 (成果物・数値の一次データ・規律遵守)
の突合**として実施。7 視点 (P2-0/1・P2-2・P2-3/4・P2-5・規律1/2・規律3/4/6・docs 整合) の並列
ファインダー → 重複統合 → 敵対検証 (severity 高は 3 票制) の 23 エージェント構成 (新規計測ゼロ・
読み取りのみ)。

**総合判定: Phase 2 までの仕事は実態が伴い健全。完了主張の虚偽・絶対規律違反は 0 件 (critical/high 0)。**
裏取り済み 78 件の主要な柱: P2-2 の 24 評価 WAL から最速構成を独立再計算で一致 / backoff headline
+38.33%/+11.27% と cross-run 再現を WAL 生データから復元 / P2-5 の全統計量 (A・a・null・誤収束 8/12・
exact p 2 件) を独立再計算で一致、凍結値は決定論 replay で byte 一致 / critic-experiment.md に答え
literal 不在 (critic.md には現存 = 物理削除の主張どおり) / 全 perf build 46 個の nm 走査で trace
シンボル漏れ 0 (trace build は 6 件 = 検査の弁別力確認)・計測に使われた build 16 種すべて trace 無効 /
全 8 WAL で「verify 赤なのに commit」0 件・fails-closed 経路網羅 / D1〜D31 連番欠番なし・主要数値の
文書間一致。検出は real_new 10 (medium 1 + low 9)・既知管理済み 4・refuted 1。監査の完全な結果
(全 finding の証拠と判定理由) はセッション成果物として保持、要点は以下の修正コミットに反映。

**唯一の medium = write-heavy「permutation p<10⁻⁴」の過大表示 → 訂正 (9c9d144):** 旧記録は方式・
反復数が未記録の Monte Carlo 由来で as-stated 再現不能。厳密 permutation (pooled 512 から 12 本の
多変量超幾何・全 50268 構成列挙、整数統計量で境界厳密) を `search_baselines.exact_perm_pvalue_A` に
コード化し (手計算校正 + 凍結度数分布の回帰テスト付き)、監査エージェントと本セッションの独立 2 系統で
**p=2.52×10⁻⁴** 一致を確認して確定。Holm ×6 でも <0.05 で「誘導は貪欲より有意に有害」・A=0.230 は
不変。伝播 5 箇所 (phase2 / D29 末尾訂正注記 / 本 worklog 過去エントリ注記 / insight 追記表 /
summary.json `correction_2026_07_03` 節 — recalibration 節は 07-02 の記録として原文保持) を訂正。

**low の消化 (7ea7cb4 / acdfece / 32e0f57):** phase2.md の P2-0 完了表記取り残し (実態は A4 の
buildcache 継続 assert に吸収済み) + sanity WAL 未保存の注記 + 「abort 0」の多義性明確化 (STAGE_ABORT
0 件 ≠ tx abort_rate) + C1 節を「解消済み (選択肢 a、065593a)」に更新 (前エントリ flag「4 文書の
食い違い」の phase2.md 側を消化) / calibrator 2 ファイルの削除済み pinning patch 参照 +
test_verifier の「4 カウンタ」ハードコードを修正 / insight に D26 恒真注記・per_step 証拠連鎖の範囲
注記、audit C1 の理由付け訂正、本 worklog 過去 2 箇所に前方注記 (P2-2 初回テーブルは再計測で置換済み /
「3構成」は 4 構成との揺れ)。

**対応せず記録のみ (既知管理済みと確認):** H3 hooks 未配線 (方針 A 進行中、テストは条件付き skip で
可視) / critic・profiler の「書き込みなし」が Bash 残存で規律ベース (agent 定義自身が開示済み) /
bench_lock の排他が pipeline 外計測スクリプトを覆わない (pgrep admission のみ)。監査 finding の
1 件「suite 全緑主張 vs 1 failed」は実測 (160→162 passed + 5 skipped) で現に全緑のため非成立と裁定。

### 次の一手 (変わらず)
- **Phase 3 タスク3 (H3 hooks 方針 A の実装)** — 順序: 一次防壁 → hook 最小化 → settings.json 配線。
- 未消化の docs 課題 (残り): 「WAL proof chain」の実体定義 / 外的妥当性の集約 / coder 自律期の
  停止条件・fitness 採否・再試行方針の予約。

## 2026-07-03 — Phase 3 計画の多視点敵対検査 + 検出 30 件のうち計画欠陥系を phase3.md に反映

ユーザー指示「phase3 と roadmap を検査して phase3 の計画を練る (問題・改善点)」。6 視点 (内部整合 /
roadmap・規律整合 / 実装実態との突合 / 実験設計・統計 / 規律突破面の残穴 / 運用・段取り) の並列
ファインダー → 指摘ごとの独立裁定 (real/refuted/known) の 38 エージェント構成 (読み取りのみ・新規計測ゼロ)。
**裁定 = real 30 (high 11 / medium 16 / low 3)・refuted 2・既知重複 0**。全指摘の証拠付き裁定はセッション
成果物として保持、構造的欠陥はユーザー承認のもと phase3.md に反映済み (下記)。

**検出した構造的欠陥 3 つ (いずれも複数ファインダーが独立検出):**
1. **主実験に到達する道が計画に無い** — 事前登録した headline 4 対照 + LLM ablation を実行する段が
   後続段 1-5 に不在。特に headline 2 (クロスプロトコル stock 最良) は trace-hook が silo/si にしか無く
   pipeline.evaluate (verify 必須) では COMMIT 不能 = S1 が前提なのに、must 表の S1 発火条件が主実験を
   数えていなかった。「sort 段以降の主張は従う」の文言も段 4 (coder 自律期、sort より前) を拘束できず。
2. **kickoff 完了条件が検査不能かつ自己矛盾** — abort>0 確認が 2 箇所で「完了条件に追加」と宣言され
   ながら本文未反映、かつ WAL に abort 数が記録されておらず (STAGE_VERIFY_DONE payload は 4 項のみ・
   _run_trace は stdout を捨てる) 確認自体が実行不能。「純 timing (or inert no-op) が stock cache-hit で
   commit」は選言で no-op 単独完了を許し、「純 timing が cache-hit」は identity 設計の故障状態を合格と
   読める。apply/revert 駆動部 (機構節が約束する pinned-clean assert 込み) も未実装・タスク無所属。
3. **一次防壁の穴 (方針 A の実効性)** — (i) 観測者効果二重検査 (blocking) の旧述語「両ビルドの
   preprocess 出力を diff」は成立しない (TRACE ガード領域で正当に食い違う)。(ii) source_digest は
   #include 行を digest 前に無条件除去 (`_INCLUDE_RE`) するため、coder の #include 追加はバイナリが
   変わるのに identity 不変 = stock と alias → 既存バイナリ cache hit で変更が一度もコンパイルされない
   まま certified 記録。防壁は道Y の hook 禁止のみ = 未配線で、方針 A が消したはずの単一障害点が復活。
   (iii) resolve→build 間の TOCTOU: 共有 working-tree に排他が無く、汚染が campaign 非依存の共有
   ビルドキャッシュに永続。

**phase3.md への反映 (修正 1-4、ユーザー指示):**
- **完了条件を 2 項に分離** (identity 後方互換 = no-op stock cache-hit / 合成枝 1 周 = 純 timing
  cache-miss 新規ビルド + **verify abort>0 の WAL 確認**)。「純 timing が cache-hit = 一次防壁の故障」と明記。
- **blocking タスク 4 本追加**: verify abort 数の WAL 記録 (ccbench stdout `abort_counts_:` パース) /
  apply-revert ハーネス (順序 = apply→resolve→build→revert 固定) / build 後 digest 再照合 (TOCTOU 遮断、
  worktree 隔離 = 段 5 までの最小防壁) / #include 死角の identity 核での閉塞。
- **観測者効果二重検査を「述語仕様の確定が先」に書き直し** — 候補述語 = **diff-of-diffs** (variant の
  TRACE=1/TRACE=0 preprocess 差分が pinned HEAD の同差分と一致)。旧残存リスク「#ifdef TRACE 内側に
  挙動差を隠す攻撃を素通し」もこの述語で D_variant≠D_stock として捕える (残存リスク節を更新)。保証しない
  こと (両ビルド共通の常駐メタデータは機械判定不能 = fitness 自己ペナルティ + auditor 領域) を明記。
- **主実験の実行を後続段 6 として新設** (gate = headline 候補 + S2 gate + auditor live。前提タスク (a)-(g):
  S1 or stock 専用計測経路の設計判断 / SPACES 拡張 + protocol 別 calibration + floor 対象別再実測 /
  ランダム変異生成器 / 機械 sweep 軸命名手順 / リーク制御実体化 / 検証相 (seed×N) / サンプル設計数値確定)。
  must 表 S1 行に主実験発火を追記。評価設計の拘束範囲を「coder が性能主張を生む段 (段 4 以降) すべて」に明確化。
- **統計計画の補完**: floor 流用禁止 (3.0% は stock silo 実測値、対象ごとに再実測) / サンプル設計 4 点
  (系列数・検定単位=系列・検定力・総予算。P2-5 は replay だったが Phase 3 は直列実計測 — 検定力不足由来の
  偽 negative を「LLM に価値なし」と誤読させない) / Holm 補正 / 天井の不在の明示と代替天井 (機械 sweep
  漸近 = 経験的天井、BACKOFF_FIXED grid = 局所天井) / deceptive 相当の検証 / 検証相の配線。
- **失敗条件 (e) 追加**: workload 過適合は退行込みで全 workload 報告 (選択的報告の禁止)。
- ベースライン 3/4 の操作的定義の最低要件 (Tier0 通過変異のみ・通過率報告 / 軸命名は coder 出力を見る前に
  固定し情報源を記録)。文言修正: 「Write hook で強制」→ 配線後に機械強制 (現在形の保証ではない) /
  coder.md タスクに前提 gate (hooks 配線 = `test_settings_json_wires_both_hooks` 緑を機械確認)。

**協議の決着 = a' (折衷、ユーザー承認):** roadmap §2 層2(b) の本丸「他 CC の最適化移植 + カタログ化」が
Phase 3 計画に不在という乖離は、**移植を拡張予約に降格**して解消 (D32) — 層2(b) の内側を b1 (空間外合成、
P2-4 で実証済み) / b2 (移植、未検証仮説) に分節し、主実験は b1 で行い、b2 + カタログ化は phase3.md
後続段 7 に予約 (一歩目 = カタログ化試作 1 枚、本格投資はその結果で判断)。roadmap は軽微改訂 (層2 名称を
「最適化合成ループ」に・粒度節 b1/b2・§8 コーパス駆動の再定義・§9 実態一致。協議合意ゆえ版管理セレモニー
不要)。README 三層図も追従。refuted 2 件 (変異軸順序の自己矛盾疑い / リーク制御と CLAUDE.md 自動ロードの
非両立疑い) は蒸し返さない。**コミット 3 件** (441a50b 検査反映 / f9fa80a a'+D32 / 本 worklog)。

### 次の一手
- kickoff 残り blocking の実装順 (phase3.md タスクリスト順): abort 数 WAL 記録 → apply/revert ハーネス →
  digest 再照合 → #include 閉塞 → hook 最小化 + 配線 → 観測者効果二重検査 (述語 = diff-of-diffs 確定) →
  coder.md + 全配線 1 周。
- 未消化の docs 課題 (残り、変わらず): 「WAL proof chain」の実体定義 / 外的妥当性の集約 / coder 自律期の
  停止条件・fitness 採否・再試行方針の予約。
