# Phase 1 — 評価器の構築

**目的:** 評価パイプライン (正しさ + 性能) を信頼できる状態にする。これが Phase 2 以降 (探索の自動化) の土台。

**Phase 1 完了の定義:** verifier が正しい CC を緑、壊れた CC を赤と判定でき、構造化フィードバックを返せる。calibrator がレコード数を決められる。手動移植した最適化の効果が観測者効果なしで測れる。

**サブエージェント:** verifier, calibrator (`.claude/agents/` に定義済み)

**環境の現状 (D10):** 現在 Linux 実機は未調達 (近日入手予定)。それまでは Mac devcontainer (開発層) で進められる範囲を最大化する。原則: **「機能の正しさ」は全部 Mac でできる。「信用できる性能数値」だけが Linux。** 各タスクに [Mac] / [Linux] のタグを付けてある。[Mac] タスクは Linux 無しで完了できる。

タスクは上から順に。**タスク0 が終わるまで、タスク2以降の詳細は確定しない** — 推測でなく CCBench の実物を読んでから進める。

---

## タスク0 [Mac]: CCBench 解剖 (最優先・他の全タスクの前提)

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

CCBench に trace を吐く口を `#ifdef TRACE` で足す。**絶対規律1 (観測者効果の分離) を厳守。**

- [ ] trace-enabled build と trace-disabled build を分けるビルド設定を作る
- [ ] trace-hook を `#ifdef TRACE` で囲む。ランタイム分岐にしない
- [ ] hook が吐く情報: 各 trx が「どの trx が書いた値を読んだか / どの版を読んだか / 何を書いたか / commit順」。rw依存 (anti-dependency) 検出のため、読んだ版のバージョン番号も記録する (G2 を見るため)
- [ ] 改変は直接コミットせず `patches/trace-hook.patch` として保持
- [ ] orchestrator が patch 適用 → ビルド → 実験 → git checkout でクリーン化、の流れを作る

**完了条件:** trace-enabled build が trace を出力し、trace-disabled build にはトレース処理が一切残らない (バイナリに含まれない)。

---

## タスク2 [Mac]: mini trace verifier の実装 (Tier 1)

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
- [ ] 判断と妥当性を `output/insights/` に文書化する出力部

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

- [ ] orchestrator の骨格: WAL スキーマ (環境タグ必須、orchestrator-design.md 参照)、リカバリループ、評価パイプラインの atomicity、ベンチ排他ロックの構造
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
