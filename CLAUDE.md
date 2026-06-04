# CLAUDE.md — Izanagi 作業指示書

このファイルは Claude Code がセッション開始時に読む。**実装を始める前に、まずこれを読み、次に下記の docs を読むこと。**

---

## このプロジェクトは何か

**ワークロード特化の並行性制御 (CC) を AI が自動合成するシステム。** CCBench を素材コーパスとして使い、入力ワークロードに最適な CC を作る。最終成果物は「新しい CC + なぜ速いかの説明 + 試行錯誤の記録」。

設計の全体像と理由は `docs/roadmap.md` にある。読まずに実装を始めてはいけない。

---

## 現在地

**Phase 1: 評価器の構築。** まだコードは無い。

**Linux 実機は現在未調達 (近日入手予定)。** phase1.md のタスクには [Mac] / [Linux] タグが付いており、[Mac] タスク (0,1,2,3,4a,5a,6) は今の devcontainer だけで完了できる。[Linux] タスク (4b,5b,7) は実機到着後。Mac devcontainer で取った性能数値は env タグ付きで記録し、性能比較には決して使わない (orchestrator-design.md の環境タグ参照)。

次にやるべきことは `docs/phase1.md` に番号付きタスクで分解されている。**タスク0 (CCBench 解剖) から順に進める。** タスク0が終わるまで、後続タスクの詳細は確定しないと明記されている — 推測でコードを書かず、まず CCBench の実物を読んで `docs/ccbench-anatomy.md` を埋めること。

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
└── output/                    ← 全成果物 (variants/runs/reports/insights)
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
