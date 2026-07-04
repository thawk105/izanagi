# Phase 1 — 評価器の構築

**目的:** 評価パイプライン (正しさ + 性能) を信頼できる状態にする。これが Phase 2 以降 (探索の自動化) の土台。

**Phase 1 完了の定義:** verifier が正しい CC を緑、壊れた CC を赤と判定でき、構造化フィードバックを返せる。calibrator がレコード数を決められる。手動移植した最適化の効果が観測者効果なしで測れる。

**サブエージェント:** verifier, calibrator (`.claude/agents/` に定義済み)

**環境の現状 (更新 2026-06-17):** Linux 実機 (計測層) 確保済み — Dell R760, bare-metal x86_64, 96スレ/2NUMA, 247GiB, perf HW カウンタ動作。**開発も計測も本ホストで行える。** [Mac]/[Linux] タグは元々「機能/性能」の区別で、今はどちらも本ホストで実行可能 (タグは履歴として残す)。host-fit の詳細は `docs/ccbench-anatomy.md` §7、進捗は `docs/worklog.md`。

タスクは上から順に。**タスク0 が終わるまで、タスク2以降の詳細は確定しない** — 推測でなく CCBench の実物を読んでから進める。

---

## タスク0 [Mac]: CCBench 解剖 (最優先・他の全タスクの前提)

**✅ 完了 (2026-06-17)。** CCBench を submodule (`33d74a3`) で取得・全ビルド (GCC 11.4, 34バイナリ) し、6軸 + 高リスク2軸の敵対的検証で解剖して `docs/ccbench-anatomy.md` に記録。主要結論: 最適化=ビルド時 `-D` / workload=runtime gflag (全探索が現実的)、protocol 10種 (YCSB 対応 7)、Silo の trace 3点は CC-native (フィールド追加不要)、**`si`=本物の write-skew G2 = タスク3 の positive control**、`#ifdef TRACE` の罠 (→ decisions D14)、スレッドピンニング既定 OFF (→ `-DLinux`/numactl)。以下の原チェックリストは全項目充足 (記録として残す)。

CCBench を clone して構造を調査し、結果を `docs/ccbench-anatomy.md` に記録する。これが終わるまで後続タスクの詳細は確定しない。

- [ ] submodule で CCBench を追加: **`https://github.com/thawk105/ccbench` (v1) を使う** (v2 ではない。v1 が VLDB 論文の実体で 7プロトコル×7最適化のコーパスが揃っているため)。`external/ccbench/` に配置し commit hash を固定
- [ ] 最適化フラグの実装方式を調査:
  - `#define` (ビルド時) か、ランタイムフラグか?
  - これで探索ループが「ビルドし直し型」か「ランタイム切り替え型」か決まる
  - CCBench は性能ベンチなのでおそらくビルド時 `#define` が多いと予想されるが、**必ず実物を確認する**
- [ ] CCBench が実装している CC プロトコルと最適化を列挙:
  - どのプロトコル (Silo, TicToc, MOCC, Cicada, 2PL系, ... ) があるか
  - CCBench 論文の「7最適化」(CPU cache / delay on conflict / version lifetime の3カテゴリ) が実際どう実装されているか
  - 特に invisible reads がどこにあるか (タスク5で使う)
- [ ] YCSB ワークロードのコードを特定:
  - trx がどこで read/write を発行しているか
  - ここが trace-hook を刺す場所になる
- [ ] ビルド方法・実行方法・既存の出力形式を記録
- [ ] **ARM64 (Apple Silicon) でビルドが通るか確認**: x86 intrinsics・PAUSE命令・memory ordering 前提の箇所を洗い出す。通らない場合は該当箇所を記録し、開発層では Rosetta (amd64) で回す方針に切り替える (D10)
- [ ] 調査結果を `docs/ccbench-anatomy.md` に構造化して書く

**完了条件:** ccbench-anatomy.md を読めば、trace-hook をどこに刺すか・パラメータ探索をどの方式でやるかが判断できる。

---

## タスク1 [Mac]: trace-hook の設計と実装 (観測者効果の分離を守る)

**✅ 完了 (2026-06-17)。** `patches/trace-hook.patch` で Silo に `#if TRACE` トレースを実装。実証: trace の C 行数 = ベンチ `commit_counts_` 完全一致 (327918)、非 genesis read の 100% が producer に matchable・ORPHAN 0・版重複 0、trace-disabled build に `izanagi_trace` シンボル 0 (compile-out)、3点とも CC-native でフィールド追加なし。トレース形式と適用フローは `patches/README.md`。`-DLinux` ピンニングは別 patch (task4) に分離。

CCBench に trace を吐く口を足す。**絶対規律1 (観測者効果の分離) を厳守。** 実装は **`#if TRACE`** で行う (naive な `#ifdef TRACE` + cmake `-DTRACE=0` は常真化して消えず観測者効果が漏れる → `decisions.md` D14)。既存 `ADD_ANALYSIS` が同型の完全コンパイルアウト先例 (`ccbench-anatomy.md` §5)。Silo から着手 — read-version=`expected` Tidword (`cc/silo/transaction.cc:261`)、write-value=WriteElement body (`:479/:525`)、commit-order=`maxtid` (`:511`)、**3点とも CC-native でフィールド追加不要** (§4)。`-DLinux` 未定義でスレッドピンニングが死んでいる件 (§7) も、この patch で併せて直すか別 patch にするか判断する。

- [ ] trace-enabled build と trace-disabled build を分けるビルド設定を作る
- [ ] trace-hook を `#ifdef TRACE` で囲む。ランタイム分岐にしない
- [ ] hook が吐く情報: 各 trx が「どの trx が書いた値を読んだか / どの版を読んだか / 何を書いたか / commit順」。rw依存 (anti-dependency) 検出のため、読んだ版のバージョン番号も記録する (G2 を見るため)
- [ ] 改変は直接コミットせず `patches/trace-hook.patch` として保持
- [ ] orchestrator が patch 適用 → ビルド → 実験 → git checkout でクリーン化、の流れを作る

**完了条件:** trace-enabled build が trace を出力し、trace-disabled build にはトレース処理が一切残らない (バイナリに含まれない)。

---

## タスク2 [Mac]: mini trace verifier の実装 (Tier 1)

**✅ 完了 (2026-06-18)。** `orchestrator/verifier/` に実装 (parse → DSG 構築 ww/wr/rw →
iterative Tarjan SCC で cycle 検出 → G0/G1c/G2 分類 → 構造化 report)。実 Silo トレース
(184k txn / 1.63M 辺) を certified serializable、手製赤フィクスチャ (write-skew/lost-update/
3-cycle/mixed) を G2 検出。**敵対的検証 workflow (4 監査 + 6 レッドチーム, 33 フィクスチャ)
で verdict mismatch 0 / false-red 0**: Tarjan を 6万グラフで参照実装と照合 (一致)、判定を
独立 3-color DFS と照合 (一致)、6万トレース差分 fuzz で独立 Adya DSG と照合 (false-green/red
ゼロ)。指摘から**絶対規律2 の硬化**を実装: integrity 不良 (orphan/version dup/重複 txid/
番兵 (1,0) commit) の trace は serializable を主張せず **indeterminate** を返す (落ちた辺が
real cycle を隠す false-green を防ぐ)。genesis は値 (1,0) でなく **producer 不在**で判定
(FIX2)。**発見:** realizable trace では全 cycle が G2 (G0/G1c は構造的に出ない、定義は
`docs/isolation-phenomena.md`)。phantom/述語異常は trace 形式の限界でスコープ外
(`output/insights/2026-06-18_phantom-predicate-out-of-scope.md`)。単体テスト 15/15。

trace を読んで serializability を検査する自前 verifier を Python で書く。**verifier サブエージェントの定義に従う。**

- [ ] trace ログのパーサ
- [ ] read/write 依存グラフの構築 (ww / wr / rw の3種の辺。Adya の serialization graph)
- [ ] cycle 検出。**G2 (anti-dependency cycle) まで見る** (Serializable 狙いのため)
- [ ] anomaly を検出したら、**構造化フィードバックを返す** (絶対規律3): どの trx 間のどの依存で cycle ができたか。単なる pass/fail にしない
- [ ] ランダム seed を変えて N回回す確率的検証の枠組み (Jitskit の reward hack 対策と合致)

**完了条件:** 正しい CC の trace に対して「serializable」を返し、anomaly のある trace に対して「どこがどう壊れているか」を構造化して返す。

---

## タスク3 [Mac]: verifier が「赤を出せる」ことの証明 (絶対に飛ばさない)

**✅ 完了 (2026-06-18, Approach A)。** Silo の read-set 検証 (validationPhase 条件#1 = anti-dependency
チェック) を macro-guard で抜いた**わざと壊した variant** (`patches/broken-silo-norw-validation.patch`,
既定 OFF) をビルドし、高 contention YCSB (rmw, skew 0.9, 50 tuples, 4 thread) で実行 → trace に
**1310 個の G2 cycle** が出現し verifier は **NON-SERIALIZABLE (exit 1)** を返した (witness は
ww+wr+rw 混在の lost-update/write-skew)。**同一ワークロードで壊していない Silo は certified
SERIALIZABLE (exit 0)** = clean ablation (差は read validation の有無のみ)。verifier が「常に緑のザル」
でないことを実トレースで実証。なお realizable trace では全 cycle が G2 なので「ww/wr/rw それぞれの
違反」は G2 の中で辺構成が違う形として現れる (`docs/isolation-phenomena.md`)。

**✅ Approach B も完了 (2026-06-18)。** **本物の (無改変の) `si`=Snapshot Isolation を positive control に。**
si エンジンに trace-hook 拡張 (`patches/trace-hook-si.patch`、版ID=`(1, cstamp)`、初期版 cstamp=0→genesis に自然一致)。
write-skew が出る workload (`rmw=false` で read/write set を分離、高 contention) で `ycsb_si` を実行 →
**3576 個の G2 cycle → NON-SERIALIZABLE**、integrity clean (版写像が正しい証拠)。**同一 workload で Silo
(serializable OCC) は certified SERIALIZABLE** → verifier は workload でなく**分離レベルそのもの**を見ている
real-CC discrimination。`ermia` (SSN on=serializable) cross-check は版 cstamp が `cstamp<<1` (低ビット=SSN flag)
で commit 経路も2系統あり計装が繊細なため次の増分に回す (worklog に罠を記録)。

verifier が「常に緑を出すザル」でないことを証明する。**ここを飛ばすと、後で壊れた variant を正しいと誤認する地獄になる。**

**有力な近道 (タスク0 で判明):** `si` は `ermia` から SSN (anti-dependency 認証) を剥がした Snapshot Isolation で、**本物の write-skew (G2) を admit する**。`ermia`(SSN on=serializable) と `si`(SSN off=SI) は同一エンジンの ablation ペアなので、`si` を **positive control** (verifier が G2 を検出せねばならない)、`ermia`/`oze` (明示的に anti-dep を実体化) を cross-check oracle にできる。「わざと壊した CC」に加えて、この CCBench 内蔵の本物の anomaly を検出力の証拠に使う (詳細 `ccbench-anatomy.md` §2)。

- [ ] わざと壊した CC を作る (例: Silo の validation を抜く、版チェックを省く)
- [ ] その壊れた CC の trace に対して verifier が anomaly を検出することを確認
- [ ] 複数種類の壊し方 (ww / wr / rw それぞれの違反) で検出できることを確認

**完了条件:** 意図的なバグを verifier が捕まえられる。検出力の証拠が残る。

---

## タスク4a [Mac]: calibrator の実装とモック検証

**✅ 完了 (2026-06-18)。** `orchestrator/calibrator/` に純ロジック (perf/bench パース → 飽和判定 → scale 感度 → noise floor → env スコープ文書化) + モックテストを実装。飽和判定は tail-flat 要求で非単調系列に頑健。一次記録は worklog 2026-06-18。

cache miss 率の飽和点でレコード数を決めるロジックを実装する。**calibrator サブエージェントの定義に従う。** 実機実行はタスク4b。

- [x] perf stat の出力 (LLC-load-misses 等) をパースする仕組み
- [x] 飽和判定ロジック: 倍々系列の miss率データから「次に倍にしても +Δ% 未満」の最小レコード数を返す
- [x] **モックの perf 出力データで単体テスト** (飽和が早いケース / 遅いケース / 単調でないケース)
- [x] スケール感度検出の枠組み (small/medium 2点の伸び方を特徴量として記録)
- [x] 判断と妥当性を env スコープ (`output/env/<env-tag>/`) に文書化する出力部 (calibration は入力非依存なので campaign スコープに置かない、D13)

**完了条件:** モックデータに対して正しい飽和点と根拠文書を返す。

## タスク4b [Linux]: calibration の実機実行

**✅ 完了 (2026-06-18, env=linux-baremetal)。** cache-miss は倍々スイープで飽和せず (index=masstree の木深化で「膝」が出ない)、D15 の下限基準に転換し、**records=1m / 48thread / skew0.9** で確定 (within-run noise floor CV 2.28% も実測)。一次記録は worklog 2026-06-18。

- [x] Linux 実機で perf stat が HW カウンタを取れることを確認
- [x] 1m → 2m → 4m → 8m... の実キャリブレーションを実行し、探索用レコード数を確定
- [x] thread 数を固定して実施 (飽和点は thread 数依存)

---

## タスク5a [Mac]: 手動移植のサニティチェック (正しさ側)

**✅ 完了 (2026-06-19)。** 既知最適化の on/off で正しさパイプラインが期待通り動くことを実トレースで確認。invisible reads は silo に内在し silo で toggle 不可・mocc は trace-hook 未実装のため、**代表として silo の `BACK_OFF` (delay-on-conflict, 意味論保存) を on/off** して両方とも verifier が **certified SERIALIZABLE** を返すことを実証 (BACK_OFF=1: 277,391 txn / =0: 571,816 txn、高 contention `tuple200,skew0.9,rmw,thread4`)。観測者効果分離はタスク1 の symbol 不在 (perf build に izanagi_trace 0 個) が構造的に最強の証明で、ここでも trace build に 6 シンボル・perf build に 0 を再確認。

- [x] 既知最適化を on/off (silo BACK_OFF。invisible reads 自体は silo で toggle 不可なため代表最適化を使用。invisible reads の正しさは silo=invisible が tasks 2/3 で certified 済み・broken silo が red で担保)
- [x] 両方の trace に対して verifier が緑を出すことを確認 (BACK_OFF on/off とも certified serializable)
- [x] ビルド等価性: trace-enabled と trace-disabled の意味論一致は**タスク1 の symbol 不在で構造的に担保**済み (perf binary に trace コードが 1 byte も無い)。DB 状態ダンプによる semantic 等価性は symbol 不在の方が強い証明なので冗長と判断 (DB-dump 計装は未実装)。**残増分:** mocc trace-hook (visible-reads 側の trace 検証 + verifier を 2nd エンジンに拡張) は低価値・高コスト (mocc は shipped の serializable protocol) なので Phase 2 任意増分に回す。

**完了条件:** 正しさパイプラインが既知の最適化の on/off に対して期待通り動く (達成: BACK_OFF on/off 両緑 + tasks 2/3 の green-for-correct/red-for-broken)。

## タスク5b [Linux]: 手動移植のサニティチェック (性能側)

**✅ 完了 (2026-06-19, env=linux-baremetal)。** invisible reads の効果を MOCC `temp_threshold` で実機計測。**訂正:** I2 は「invisible reads は **read-heavy** で効く」が正しい (roadmap.md §層3 の narrative 例示 (「read-heavy phase での cache 汚染削減」) が論文に忠実、当初ここに書いた「write-intensive」は誤帰属)。クリーン点 = `rratio=100` (read-only) で **invisible 1.28x** (9.32M vs 7.28M tps, CV 0.1%)、perf で visible が +32% cache-misses/txn = read-lock の cacheline bouncing 回避が機構と確認。baseline は YCSB 7 protocol 取得 (silo 902K / tictoc 1.05M / mocc 661K / cicada 605K / si 351K / ermia 327K tps、oze は skew0.9 で病理=別 insight)。詳細 `output/insights/2026-06-19_invisible-reads-i2-reconciliation.md`。

- [x] trace-disabled build で invisible reads on/off の性能を実機計測し、論文 insight I2 と整合確認。**⚠ 計測の罠 (実測で判明):** `temp_threshold` は read 経路だけでなく **write/delete の lock() も gate する** (`cc/mocc/transaction.cc:361,468`)。よって `rratio=0` (write-only) の差 (1.733x) は invisible reads でなく temperature-gated 悲観 write-locking の効果。**invisible reads の計測には `rratio=100` (read-only) のみを使う** (rratio 0/25/50/75 は read/write lock 混線で off-mechanism)。anatomy §3:117 の「mocc は read 可視性以外も異なる」の同一バイナリ gflag 内版。
- [x] Phase 2 で使う baseline 性能 (素の各プロトコル) を実機で取得 (上記。oze は skew 病理を `output/insights/2026-06-19_oze-skew-pathology.md` に記録)

**完了条件:** 評価パイプライン (正しさ + 性能) が信頼できる状態。invisible reads の効果が論文 (read-heavy) と整合し、観測者効果が排除されている (タスク1 の symbol 不在 + タスク5a の BACK_OFF on/off 両緑で再確認)。

---

## タスク6 [Mac]: Phase 2 の前倒し (Linux 待ちの間に積めるもの)

**✅ 完了 (2026-06-19)。** orchestrator 骨格 (STAGE2) の評価パイプライン統合まで実装 (model/genome/ident/layout/wal/lock + buildcache/pipeline/loop、敵対レビューで規律2/atomicity を硬化)。残り (全 variant ビルド通過確認 + verifier 一括実行) は Phase 2 の P2-0 (2026-06-20) で消化 — `docs/phase2.md` P2-0 参照。一次記録は worklog 2026-06-19 (続き)。なお end-to-end 配線テストは下記の「Mac ダミー fitness」経路でなく実機 demo (build→verify→bench→commit 完走、env=linux-baremetal) で消化した — 実機集約 (D10) により Mac 経路は不要化し、mac-devcontainer タグの計測記録は存在しない。

Linux 実機が届くまでの待ち時間で、Phase 2 の機能面を先行実装する。**性能数値が要らない仕事は全部ここでできる。**

- [x] orchestrator の骨格: 出力レイアウトと campaign-id の確定 (`output/campaigns/<id>/` と `output/env/<tag>/` の二軸、campaign-id = spec+config の内容ハッシュ、D13/orchestrator-design.md)、WAL スキーマ (環境タグ必須・campaign スコープ)、リカバリループ (入力から campaign-id を再計算して WAL を特定)、評価パイプラインの atomicity、ベンチ排他ロックの構造
- [x] パラメータ全組み合わせの列挙器と、**全 variant のビルド通過確認** (コンパイルが通るかは正しさ仕事、Mac でできる)
- [x] ビルドキャッシュ (同じ最適化組み合わせを再ビルドしない)
- [x] 探索ループの end-to-end 配線テスト: Mac 上の throughput を**ダミー fitness** として使い、ループが回ることを確認。**この数値は env=mac-devcontainer タグ付きで記録し、性能比較には決して使わない**
- [x] 全組み合わせ variant に対する verifier 一括実行 (パラメータ粒度 variant は理屈上全部緑のはず = verifier の大規模 sanity check)

**完了条件:** Linux が届いた時点で「実機で回すだけ」の状態になっている。

## タスク7 [Linux]: Linux 実機到着日のチェックリスト

**✅ 完了。** 子項目は全て消化済み (タスク4b/5b は本文書の各節で完了宣言済み。実 fitness への切り替えは Phase 2 の P2-2 で実施)。

- [x] リポジトリを clone し、devcontainer ではなくネイティブでセットアップ (ubuntu.deps)
- [x] perf の動作確認 (HW カウンタが取れること)
- [x] タスク4b (実機 calibration)
- [x] タスク5b (性能側サニティチェック + baseline 取得)
- [x] タスク6 の探索ループを実 fitness (env=linux タグ) に切り替えて Phase 2 開始

## Phase 1 が終わったら

`docs/phase2.md` を作り、Phase 2 (パラメータ探索) に進む。Phase 2 では critic と profiler サブエージェントを `docs/agent-architecture.md` の仕様に従って実体化する。

Phase 2 の最初の実験候補: **CCBench の最適化フラグの全探索** (有限空間なので可能) → その結果を「LLM 誘導探索」のベースラインにする。
