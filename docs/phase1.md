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

verifier が「常に緑を出すザル」でないことを証明する。**ここを飛ばすと、後で壊れた variant を正しいと誤認する地獄になる。**

**有力な近道 (タスク0 で判明):** `si` は `ermia` から SSN (anti-dependency 認証) を剥がした Snapshot Isolation で、**本物の write-skew (G2) を admit する**。`ermia`(SSN on=serializable) と `si`(SSN off=SI) は同一エンジンの ablation ペアなので、`si` を **positive control** (verifier が G2 を検出せねばならない)、`ermia`/`oze` (明示的に anti-dep を実体化) を cross-check oracle にできる。「わざと壊した CC」に加えて、この CCBench 内蔵の本物の anomaly を検出力の証拠に使う (詳細 `ccbench-anatomy.md` §2)。

- [ ] わざと壊した CC を作る (例: Silo の validation を抜く、版チェックを省く)
- [ ] その壊れた CC の trace に対して verifier が anomaly を検出することを確認
- [ ] 複数種類の壊し方 (ww / wr / rw それぞれの違反) で検出できることを確認

**完了条件:** 意図的なバグを verifier が捕まえられる。検出力の証拠が残る。

---

## タスク4a [Mac]: calibrator の実装とモック検証

cache miss 率の飽和点でレコード数を決めるロジックを実装する。**calibrator サブエージェントの定義に従う。** 実機実行はタスク4b。

- [ ] perf stat の出力 (LLC-load-misses 等) をパースする仕組み
- [ ] 飽和判定ロジック: 倍々系列の miss率データから「次に倍にしても +Δ% 未満」の最小レコード数を返す
- [ ] **モックの perf 出力データで単体テスト** (飽和が早いケース / 遅いケース / 単調でないケース)
- [ ] スケール感度検出の枠組み (small/medium 2点の伸び方を特徴量として記録)
- [ ] 判断と妥当性を env スコープ (`output/env/<env-tag>/`) に文書化する出力部 (calibration は入力非依存なので campaign スコープに置かない、D13)

**完了条件:** モックデータに対して正しい飽和点と根拠文書を返す。

## タスク4b [Linux]: calibration の実機実行

- [ ] Linux 実機で perf stat が HW カウンタを取れることを確認
- [ ] 1m → 2m → 4m → 8m... の実キャリブレーションを実行し、探索用レコード数を確定
- [ ] thread 数を固定して実施 (飽和点は thread 数依存)

---

## タスク5a [Mac]: 手動移植のサニティチェック (正しさ側)

- [ ] CCBench の invisible reads を手動で on/off する (タスク0で場所は特定済み)
- [ ] 両方の trace に対して verifier が緑を出すことを確認
- [ ] (採用済みの機械検証) trace-enabled と trace-disabled で最終 DB 状態が一致することを確認 (ビルド等価性)

**完了条件:** 正しさパイプラインが既知の最適化の on/off に対して期待通り動く。

## タスク5b [Linux]: 手動移植のサニティチェック (性能側)

- [ ] trace-disabled build で invisible reads on/off の性能を実機計測し、性能差が CCBench 論文の insight I2 (invisible reads は write-intensive で効く) と整合することを確認
- [ ] Phase 2 で使う baseline 性能 (素の各プロトコル) を実機で取得

**完了条件:** 評価パイプライン (正しさ + 性能) が信頼できる状態。invisible reads の効果が論文と整合し、観測者効果が排除されている。

---

## タスク6 [Mac]: Phase 2 の前倒し (Linux 待ちの間に積めるもの)

Linux 実機が届くまでの待ち時間で、Phase 2 の機能面を先行実装する。**性能数値が要らない仕事は全部ここでできる。**

- [ ] orchestrator の骨格: 出力レイアウトと campaign-id の確定 (`output/campaigns/<id>/` と `output/env/<tag>/` の二軸、campaign-id = spec+config の内容ハッシュ、D13/orchestrator-design.md)、WAL スキーマ (環境タグ必須・campaign スコープ)、リカバリループ (入力から campaign-id を再計算して WAL を特定)、評価パイプラインの atomicity、ベンチ排他ロックの構造
- [ ] パラメータ全組み合わせの列挙器と、**全 variant のビルド通過確認** (コンパイルが通るかは正しさ仕事、Mac でできる)
- [ ] ビルドキャッシュ (同じ最適化組み合わせを再ビルドしない)
- [ ] 探索ループの end-to-end 配線テスト: Mac 上の throughput を**ダミー fitness** として使い、ループが回ることを確認。**この数値は env=mac-devcontainer タグ付きで記録し、性能比較には決して使わない**
- [ ] 全組み合わせ variant に対する verifier 一括実行 (パラメータ粒度 variant は理屈上全部緑のはず = verifier の大規模 sanity check)

**完了条件:** Linux が届いた時点で「実機で回すだけ」の状態になっている。

## タスク7 [Linux]: Linux 実機到着日のチェックリスト

- [ ] リポジトリを clone し、devcontainer ではなくネイティブでセットアップ (ubuntu.deps)
- [ ] perf の動作確認 (HW カウンタが取れること)
- [ ] タスク4b (実機 calibration)
- [ ] タスク5b (性能側サニティチェック + baseline 取得)
- [ ] タスク6 の探索ループを実 fitness (env=linux タグ) に切り替えて Phase 2 開始

## Phase 1 が終わったら

`docs/phase2.md` を作り、Phase 2 (パラメータ探索) に進む。Phase 2 では critic と profiler サブエージェントを `docs/agent-architecture.md` の仕様に従って実体化する。

Phase 2 の最初の実験候補: **CCBench の最適化フラグの全探索** (有限空間なので可能) → その結果を「LLM 誘導探索」のベースラインにする。
