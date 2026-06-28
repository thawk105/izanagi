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
build で動くか** (P2-0 で trace timeout した3構成) を最初に確認 → 動けば 12、動かねば genome.py に除外制約。
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

### 次の一手

1. **[P0] cross-run 再現性** — no-backoff/fix5/fix10 を別系列・rounds≥3 で再測し +38% の再現を確認 (最優先)。
2. **[P1] 機序純度・適応収束値・正しさ実測化** — スピン命令分離 / `Backoff_` dump / 実 perf 構成 trace verify。
3. **P2-4 (profiler)** はこの「スピン命令分離」と地続き。**P2-5 (LLM 誘導 vs 全探索)** でこの合成例を「空間外」実例に。
