# CLAUDE.md — Izanagi 作業指示書

このファイルは Claude Code がセッション開始時に読む。**実装を始める前に、まずこれを読み、次に下記の docs を読むこと。**

---

## このプロジェクトは何か

**ワークロード特化の並行性制御 (CC) を AI が自動合成するシステム。** CCBench を素材コーパスとして使い、入力ワークロードに最適な CC を作る。最終成果物は「新しい CC + なぜ速いかの説明 + 試行錯誤の記録」。

設計の全体像と理由は `docs/roadmap.md` にある。読まずに実装を始めてはいけない。

---

## 現在地

**Phase 1: 評価器の構築。タスク0-4 完了。** CCBench を submodule で取得・全ビルド (34バイナリ)、構造を `docs/ccbench-anatomy.md` に記録。trace-hook (タスク1)、mini trace verifier (タスク2, `orchestrator/verifier/`、Adya DSG で G2 cycle 検出・敵対的検証済み)、verifier の赤検出証明 (タスク3) を2つの ablation で実装: (A) わざと壊した Silo `patches/broken-silo-norw-validation.patch` で 1310 G2 検出 vs 素 Silo 緑、(B) 本物の `si`=Snapshot Isolation の trace-hook で 3576 G2 検出 vs 同一 workload の Silo 緑 (real-CC discrimination)。タスク4 (calibrator, `orchestrator/calibrator/`) 完了: TSC 実測 (1800MHz)・perf+numactl runner・倍々スイープ。**実機で miss 率が飽和しない発見 → D15 下限基準 (working set が L3×K 超の最小 N)**、確定 records=1m (skew0.9/48thread, noise floor CV 2.28%)。**submodule 改変は D16 で行き先を分岐**: pinning バグ修正→`master` 還元、trace-hook→`izanagi-trace` ブランチ (submodule が pin)、broken-silo のみ `patches/` (push は人間)。次はタスク5 (invisible reads の正しさ/性能サニティ)。任意増分: `ermia` cross-check (版 cstamp が `cstamp<<1` の罠あり、worklog 参照)。

**Linux 実機 (計測層) 確保済み。** 開発・計測ともこの Linux サーバ (Dell R760, bare-metal x86_64, 96スレ/2NUMA, 247GiB, perf HW カウンタ動作) で行う。D10 の「Mac devcontainer=開発層 / Linux=計測層」の二層は、実機がこのホストに集約されたことで開発層も Linux 実機側に寄った (devcontainer 経路は維持するが必須でない)。性能数値は env=linux-baremetal タグ付きで記録する (orchestrator-design.md の環境タグ)。phase1.md の [Mac]/[Linux] タグは「機能/性能」の区別として読み替える (どちらも本ホストで実行可能)。

実装の進め方は `docs/phase1.md` の番号付きタスク。**設計が動いた点・実機の現状・各セッションの作業は `docs/worklog.md` に時系列で記録する** (索引兼日誌)。

---

## 絶対規律 (違反してはいけない)

これらは Jitskit/IDS 論文が実証した失敗モードへの対策であり、本プロジェクトの根幹。**性能や利便性のためにこれらを緩めてはいけない。**

### 1. 観測者効果の分離
正しさ検証用のトレース取得は、性能計測用ビルドから完全に除去する。
- トレース処理は `#ifdef TRACE` でコンパイル時に消す。ランタイム分岐 (`if(tracing)`) にしてはいけない
- 正しさ検証 = trace-enabled build、性能計測 = trace-disabled build。**別ビルド・別run**
- 性能比較は variant も baseline も trace-disabled で揃える
- メタデータは「CC本来のもの」と「検証専用のもの」を区別し、後者だけ `#ifdef TRACE` に隔離する
- perf プロファイリングは trace-disabled build に対して行う

### 2. 正しさゲートを緩める変異を許さない
これは最優先の規律。性能が出ても正しさを破る variant は無価値。
- verifier が anomaly を検出したら、その variant は即 reject (fitness = 失格)
- LLM に variant を作らせるとき「検証を甘くして性能を稼ぐ」方向の変異を絶対に採用しない
- これは reward hacking (Jitskit §3.2) への対策。最適化圧力は必ず正しさを攻撃しに来るという前提で動く

### 3. 正しさシグナルを後付けにしない (IDS の教訓)
verifier は「最後にまとめて回すゲート」ではなく「毎 iteration 回して、結果を次の一手のシグナルにする」もの。
- verifier は単なる pass/fail を返してはいけない。**なぜ壊れたか** (どの trx 間のどの依存で G2 anomaly が出たか等) を構造化して返す
- これを LLM の次の variant 生成の入力にする

### 4. レコード数・実験スケールは無造作に大きくしない
- 探索時は cache miss 率が飽和する最小のレコード数を使う (calibrator が決める)
- 大きすぎるスケールは時間を食うだけで測定値を変えない。それは「バカ」
- ただし小さすぎると many-core での cache 競合が再現されず測定が楽観的に歪む。両方の罠を避ける

### 5. 段階導入 / 盛らない
- Phase ごとに必要なコンポーネント・サブエージェントだけを足す。最初から全部並べない
- 各コンポーネントの効果は ablation (足す/抜くの比較) で測れるようにする
- ECC のような巨大な汎用ツール化を目指さない。CC 合成という単一目的に必要なものだけ持つ

---

## roadmap の更新 — 設計を進化させる権限と規律

roadmap は read-only の聖書ではなく **living document**。試行錯誤から「全体の絵をこう描き直した方がいい」という発見があったら、改訂に挑戦してよい。むしろ歓迎される。設計仮説の変遷記録は、そのまま論文の方法論 narrative になる。

**三層の可変性:**
- **絶対規律 (このファイルの上記セクション) = 憲法。Claude は変更してはいけない。** 変更できるのは人間のみ。roadmap がどう進化しても、正しさゲート・観測者効果の分離などの規律は不変
- **roadmap = 戦略。Claude が改訂できる。** ただし下記の版管理規律に従う
- **phase docs / ccbench-anatomy / insights = 戦術。自由に更新してよい**

**roadmap 改訂の規律 (必須手順):**
1. 現行の docs/roadmap.md を docs/roadmap-history/vN.md にコピーして凍結する (Nは現行版数)。**過去の版は絶対に消さない・書き換えない**
2. roadmap.md を改訂し、冒頭の版数を上げる
3. 改訂理由 (何を試して何が分かったから設計をどう変えたか) を docs/decisions.md に D エントリとして追記する
4. **設計判断の変更を伴う大改訂** (Phase 構成の組み替え、粒度方針の転換、スコープ外項目の取り込み等) は、改訂案を作った段階でユーザーに提示して確認を取る。軽微な改訂 (学んだ事実の反映、見積もりの修正、関連研究の追加) は確認不要で進めてよい

**版管理セレモニーの適用範囲 (上記 1-3):** 版上げ・history への凍結・decisions.md への改訂理由記録は、**Claude が自律的に改訂したものを追跡するための仕組み**。その目的は「Claude が独断で設計を動かしたら後から追える」こと。

- **Claude の自律改訂** (ユーザーと相談せず Claude の判断で roadmap を改訂する場合) → 手順 1-3 をフル実行する
- **ユーザーと協議して合意した改訂** → セレモニー (1-3) は不要。通常の編集として content だけ入れる。版番号は上げない・history に凍結しない・decisions.md への「改訂理由」記録もしない。ただし、独立した設計判断として将来の読み手に価値があるなら decisions.md に D エントリを書いてよい (これは「改訂の追跡」ではなく「設計判断の記録」として)
- どちらの場合も手順 4 (大改訂はユーザー確認) は、協議改訂なら定義上すでに満たされている

## サブエージェント

`.claude/agents/` にロール定義がある。各エージェントは独立コンテキストを持ち、`tools` で権限を絞ってある。

**Phase 1 で実体化済み:**
- `verifier` — trace を読んで serializability を検査。**書き込み系ツールを持たない** (検証役が実装を勝手に直す事故を構造的に防ぐため)。anomaly を構造化して返す
- `calibrator` — cache miss 率を見てレコード数を決める

**後続 Phase で足す (仕様は `docs/agent-architecture.md` に予約):**
- `critic`, `profiler` (Phase 2)
- `planner`, `coder`, `auditor` (Phase 3)

これらの `.md` は、該当 Phase に来たとき `docs/agent-architecture.md` の仕様に従って生成する。今は作らない。

---

## hooks

`hooks/` に最小限の機械的防壁を置く (Python で実装)。目的は絶対規律1・2の自動執行:
- variant コードが `#ifdef TRACE` の外に検証専用メタデータを書こうとしたら警告 (規律1)
- verifier を迂回して性能数値だけ更新しようとしたら止める (規律2)

ECC のように大量の hook を入れない。この2つの防壁だけ。詳細は `docs/agent-architecture.md`。

---

## リポジトリ構成

```
izanagi/
├── CLAUDE.md                  ← このファイル
├── README.md
├── docs/
│   ├── roadmap.md             ← 全設計と理由 (まず読む)
│   ├── decisions.md           ← 個別の設計判断と却下した選択肢
│   ├── phase1.md              ← Phase 1 タスク分解 (タスク0から)
│   ├── agent-architecture.md  ← サブエージェント構成と段階導入計画
│   ├── orchestrator-design.md ← orchestrator の設計原則 (ACID/WAL/排他制御)
│   └── ccbench-anatomy.md     ← タスク0で作る。CCBench の構造調査結果
├── .claude/agents/            ← サブエージェント定義
│   ├── verifier.md
│   └── calibrator.md
├── hooks/                     ← Python の機械的防壁
├── orchestrator/              ← 探索ループの中枢 (Python)。Phase進行で実装
├── external/ccbench/          ← submodule (タスク0で追加)
└── output/                    ← 全成果物。campaigns/<id>/ (入力ごと) と env/<tag>/ (calibration) の二軸 (D13)
```

---

## 環境の二層戦略 (D10)

- **開発層 = この devcontainer (Mac 上)**: CCBench のビルド・trace 検証・verifier・orchestrator 開発。Phase 1 タスク0-3 はここで完結する
- **計測層 = Linux 実機**: 性能ベンチと calibration。**Mac 上の Docker では HW PMU が取れず perf の cache miss 計測が動かない。性能数値も VM 越しで歪むため、計測層で取った数値以外を性能比較に使ってはいけない**
- devcontainer の構成は `.devcontainer/` にある。CCBench submodule 追加後は post-create.sh が ubuntu.deps を読んで依存を入れる
- submodule は **thawk105/ccbench (v1)** を使う。v2 ではない (7プロトコル×7最適化のコーパスが揃うのは v1)

## 言語方針

- ドキュメント: 日本語
- オーケストレーション層・hooks・verifier・calibrator: Python
- CCBench 本体および variant: C++ (CCBench に準拠)
- 将来、国際公開が必要になったら英語ドキュメントを追加する (今はやらない)

---

## 作業の進め方

1. このファイルと `docs/roadmap.md` を読む
2. `docs/phase1.md` のタスクを上から順に潰す
3. 設計判断で迷ったら `docs/decisions.md` を引く (なぜその選択をしたか・何を却下したかが書いてある)
4. CCBench 自体のバグ等を見つけたら `output/insights/` に構造化レポートを吐き、「還元判断: ユーザー確認待ち」を付ける。勝手に上流へ PR を出さない
