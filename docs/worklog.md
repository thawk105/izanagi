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

### Approach B (si=本物の write-skew G2) の feasibility メモ (未実装)

より強い positive control = `si`(SI、write-skew を admit)を赤・`ermia`(SSN on)を緑にする real CC ablation。
着手前に si エンジンを scout した結果:
- **commit 点:** `cc/si/transaction.cc::si_commit()` (470行)。`cstamp = ++Lsn` (大域単調 uint32) で
  版スタンプ確定、各 write 版に `ver_->cstamp_` を刻む (508行)。read 版も `cstamp_` を持つ。
- **版ID写像:** si の版ID = `cstamp` (単 uint) → trace 形式 (epoch,tid) に `(1, cstamp)` 等で写せる見込み。
- **未解決 (実装前に要確認):** ① 初期ロード版の cstamp が何か (genesis=(1,0) 写像と衝突しないか)。
  ② ycsb_si が write-skew を観測可能に出すか (rmw=true は read set=write set で ww 衝突 abort になり
  write-skew が出にくい → **rmw=false で read/write を別キーにする**必要)。③ read_set_/write_set_ の構造。
- **判断:** タスク3 完了条件は Approach A で満たした。B は si/ermia への trace-hook 拡張という別エンジン
  instrumentation (絶対規律5: 別増分) なので、上記3点を詰めてから着手する。

### 次の一手

1. (任意・強化) **Approach B**: si/ermia trace-hook → `si`赤 / `ermia`緑 の real ablation。
2. **タスク4/5b 系 (計測)** — calibrator (`clocks_per_us` 実測 + `-DLinux`/`numactl` ピンニング + cache miss 飽和点)。
