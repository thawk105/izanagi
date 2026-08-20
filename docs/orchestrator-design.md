# Orchestrator 設計原則 — トランザクション実行エンジンとしてのオーケストレーション

Izanagi の orchestrator (探索ループの中枢) は、**DB のトランザクション実行エンジンの原理で設計する**。これは作者 (Takayuki) の着想: Claude Code のサブエージェント運用をトランザクション処理として捉える視点を、orchestrator の設計原則に落としたもの。

「CC を合成するシステム自体が、CC の原理で設計されている」という自己言及的な一貫性を持つ。

同じ思想の先行例: VibeServe (arXiv 2605.06068) の outer loop は、永続的な計画状態 (issues / long-term memory file / git commit graph) の上で探索を計画する。本ドキュメントの D (durability) はこれと同じ思想。

---

## 基本対応表

| DB の概念 | orchestrator での対応物 |
|---|---|
| トランザクション | サブエージェント呼び出し / variant 評価パイプライン |
| Atomicity | variant 評価の all-or-nothing (コミットポイント通過のみ採用) |
| Consistency | CLAUDE.md の絶対規律 + hooks による機械執行 |
| Isolation | ベンチ実行の排他制御 / worktree 分離 |
| Durability | 評価ログの先行書き込み + クラッシュリカバリ |
| WAL | output/campaigns/<id>/runs/ への逐次追記ログ |
| ロックマネージャ | ジョブスケジューラ (ベンチ=排他、ビルド/検証=並列) |
| Admission control | ロードアベレージによる並列度調整 |
| Task partitioning | island model (Phase 3) |

---

## D: Durability — 評価ログとクラッシュリカバリ (最重要)

探索は計算環境上で一晩回しっぱなしにする (どのマシンかは時期で変わる。専有ノードを確保できる環境ではジョブスケジューラ経由で投入し、共有ノード上で走らせるしかない環境では load average による admission control で外乱を避けながら常駐させる — 手順は環境別 runbook)。途中クラッシュ (OOM・ビルド暴走・電源) は必ず起きる前提で設計する。「失敗したらゼロからやり直し」は数千回の評価のループでは許容できない。

設計:
- 各 variant の評価をログ先行書き込みで進める。`variant X: ビルド開始 → ビルド完了(バイナリhash) → 検証完了(結果) → ベンチ完了(数値) → コミット` を output/campaigns/<id>/runs/ に逐次追記する
- orchestrator は再起動時にログをリプレイし、「どこまで評価済みか」を復元して途中から再開する
- 評価済み variant は再評価しない (ビルドキャッシュと同じ思想で、評価結果もキャッシュ)
- whiteboard memory (却下した設計の蓄積) も durable log の一種として統一的に扱う

サブエージェントは「中間状態を観測できないトランザクション」である。この観測不能性を補うため、**全サブエージェントに構造化ログを書かせ、再試行時は前回ログから作業を引き継ぐ**。verifier の「構造化フィードバックを返す」規律は、この一般原則の一例。

## A: Atomicity — variant 評価の all-or-nothing

評価パイプライン (ビルド → 正しさ検証 → 性能ベンチ → 記録) の途中で死んだ variant を「半分評価済み」として population に混ぜない。

- コミットポイントは「全段通過して記録された瞬間」のみ
- ログに「コミット」レコードがない variant は、リカバリ時に破棄する (= rollback)
- 「半分評価済み」を許すと、進化ループが「ビルドだけ通った variant」を誤って親に選ぶ等の腐敗が起きる

## C: Consistency — 絶対規律と hooks

CLAUDE.md の絶対規律 = 整合性制約。hooks = その機械執行。既に雛形で実装方針が確立している (docs/agent-architecture.md 参照)。

制約は人間 (作者) が CLAUDE.md / memory に育てていく。variant がどう進化しても破ってはいけない不変条件 (正しさゲート・観測者効果の分離) がここに固まる。

## I: Isolation — ベンチ実行の排他制御

**性能ベンチは同一マシンで並列実行すると互いに干渉する** (CPU・cache・メモリ帯域の競合)。これは観測者効果 (絶対規律1) の延長: trace を #ifdef で消しても、隣で別 variant のビルドが走っていれば測定は歪む。

ロック設計:
```
ビルド:      並列OK (admission control 下で)
trace検証:   並列OK
性能ベンチ:  排他ロック。実行中は他のジョブを全部静止させる
```

ベンチ = 排他ロックが要る critical section。orchestrator はロックマネージャとして振る舞う。

## Admission Control — 並列度の動的調整

ロードアベレージ・CPU 使用率を監視し、ビルド/検証ジョブの並列度を絞る。

特に I と組み合わせて: **ベンチ開始前に load average が静定するまで待つ**。直前のビルドの余熱 (ページキャッシュ書き戻し・温度スロットリング) がベンチに漏れるのを防ぐ。この「ベンチ前の静定確認」は calibrator の責務に含める。

## Task Partitioning — island model との接続 (Phase 3)

抽象度の高い探索タスクを分割するほど並列数を増やせる。Phase 3 の island model (複数シードからの並列進化) はこの語彙で設計する: 島 = パーティション、島間マイグレーション = 再パーティショニング。Phase 3 設計時に具体化する。

---

## 環境タグ — 性能数値の汚染防止

run ログ (WAL) の全レコードに**環境タグを必須フィールド**として持たせる: `env=mac-devcontainer` / `env=linux-baremetal` など。

- 性能比較・Pareto 選択・レポート生成は **linux 実機タグの数値しか受け付けない**
- Mac devcontainer の throughput は探索ループの配線テスト (ダミー fitness) 専用。VM 上の数値は VM オーバーヘッドと PMU 非対応で信用できない (D10)
- これは観測者効果の分離 (絶対規律1) と同じ構造の第三の汚染防止: trace の有無 / 並列実行の干渉 / **実行環境の違い**、のどれも性能比較を汚染しうる

## 出力レイアウトと campaign 同一性

orchestrator が書く全アーティファクトの置き場。本システムは入力ワークロードごとに特化 CC を作る (roadmap §1) ので、出力は**入力ごと**に分離する。ただし全部を入力で割るのは誤り — calibration / noise floor / profile は (env, thread数) ごとで入力に依存しない (roadmap §4、絶対規律4)。したがって**二軸**に分ける。

### 二軸レイアウト

```
output/
  env/<env-tag>/            ← 環境スコープ (campaign 横断で共有)
    calibration/             飽和レコード数 + noise floor (within-run / between-run, §3.6(3)/A2)
    profile/                 perf 機序プロファイル (spin 分離・有用 IPC, P2-4)
  campaigns/<campaign-id>/  ← 入力スコープ (1 campaign = D12 射影の単位)
    campaign.lock            同一性を決める正準 config (下記)。改竄不能な同一性の源
    spec/                    凍結した入力 spec cards (レポートを自己完結にする)
    runs/                    この campaign の WAL (env-tag 必須フィールド)
    variants/                variant ソース/patch とビルドキャッシュキー
    reports/                 D12 材料レポートの射影先
    insights/                campaign 固有の insight / whiteboard
  insights/                 ← CCBench 還元レポート等のグローバル知見 (D6)
  whiteboard/               ← campaign 横断で転用可能な教訓 (任意。SkillOpt の転用性)
  campaign-locks/           ← campaign 実行所有権の advisory flock ([T-565], 下記)
```

ドキュメント中で `output/runs/` `output/insights/` と書いてある箇所は、特記なき限りそれぞれ `output/campaigns/<id>/runs/` の campaign スコープ、ルート直下 `output/insights/` のグローバルスコープを指す短縮表記とする。calibration/noise floor/profile の書き込み先は `output/env/<env-tag>/`。

`campaign.lock` (同一性を決める正準 config) とは別に、`output/campaign-locks/<sha256(realpath(layout.root))[:20]>.flock` が run 全体の実行所有権を advisory flock (`LOCK_EX|LOCK_NB`) で保持する。campaign root 外に置くのは、campaign root 配下を exact-set 比較する `layer3_report.py`/`autonomous_trial_completeness.py` の completeness 判定を摂動させないため。保護対象は `run_campaign()` 呼び出しに限り、`run_campaign()` を経由しない producer は対象外 (D528 決定 9 と同型の境界)。設計判断の詳細は `docs/decisions.md` の [T-565] 実装 wave の決定を参照。

campaign スコープの実際の root は namespace で 2 つある (D65/D123)。official は `output/campaigns/<id>/`、s4 driver 族 (`p3_s4_loop` / `_sort` / `_trigger_gating` / `p3_s4_red` / `p3_kickoff` / 8c build) の**新規** campaign は `output/exploration/campaigns/<id>/` である。**構造・WAL・lock は同一**で、違うのは official consumer が marker で後者を拒否する点だけである。歴史成果物は移していないので、既存の `output/campaigns/` 参照は過去の所在としてそのまま正しい。

exploration 側だけは base root を差し替えられる ([T-422] / F98)。優先順位は**明示 `output_root` 引数 > `IZANAGI_EXPLORATION_OUTPUT_ROOT` > repo 既定**で、env 値は非空・絶対 path・repository 外・symlink component なし・実効 uid 所有を要求し、process 内で最初の解決値に pin される。使い捨て worktree (`.claude/worktrees` / `.codex/worktrees`) 配下への materialize は `ensure()` が拒否する。**repo hooks の campaign tree 防護は repo 内の path にだけ効く** — 外部 root は防護外の使い捨て領域であり、certified 材料・proof chain 素材を置かない。official `CampaignLayout` と `output/env/` は env を参照しない。

### 材料レポートの出力規約 (再現性が一級市民)

`reports/` (および env スコープの `calibration/`) の各図は **3点セット + md** で残す。グラフを画像だけにせず**生成手段とデータを必ず添える** (roadmap §3.6(4)・§7 forensic binding = claim→code→evidence の proof chain):

- `<name>.dat` — gnuplot 用データ。**ヘッダに provenance (env / ccbench-commit / clocks_per_us / workload) と「手打ち再現コマンド」を `#` コメントで埋める**。.dat 単体で「どの実行コマンドからこの数値が出たか」を辿れ、後で手打ち実行でも近似結果を再現できる。
- `<name>.plt` — gnuplot スクリプト。人間が `gnuplot <name>.plt` で図を再生成できる。
- `<name>.png` — 描画結果。`report.md` に埋め込む (人間が読みやすい)。
- `report.md` — グラフ + 数値表 + provenance + 再現コマンドを束ねた人間可読レポート (D12)。

射影器は `orchestrator/reports/` (`plot.py` = gnuplot ラッパ + `DatFile`、`calibration_report.py` が最初の実例)。throughput 等の生値を WAL に残すのと同じ anti-fabrication の思想で、「グラフは綺麗だが何から作ったか不明」という静かな汚染を断つ。**性能数値の比較に使う図は trace-disabled build の計測値のみ**から作る (絶対規律1)。

### campaign とは何か

1回の合成パイプライン起動を、**(入力 spec, 探索 config) を固定したもの**として定義する。2つの起動が「同じ campaign (=リカバリで再開する)」であるのは (spec, 探索 config) が一致するときだけ。ablation (全探索 vs LLM誘導、OEE on/off、有効 Tier 集合) や CCBench commit、scale protocol が違えば**別 campaign** になる — roadmap が随所で要求する「足す/抜く比較」がこれで素直に並ぶ。実測値 (calibration が決めるレコード数など) は同一性の入力ではなく、campaign 内に記録される派生値。

### campaign-id の決め方

要件: (1) **クラッシュ/再起動を跨いで安定** — 同じ (spec, config) は同じ id に決まり、リカバリが同じディレクトリへリプレイできる (D)。(2) **人間が読める** — manifest を開かずに「read-heavy・full探索・linux」を見つけられる。(3) **衝突しない・決定論的** — 入力から純粋に導ける。

**方式: 可読プレフィクス + 内容ハッシュ。** git の `main@a3f9c2d`、docker の `name:tag@sha256` と同じパターン。

```
<spec-slug>-<search-tag>-<cfg-hash8>
   例: readheavy-locont-llmguided-9f3a1c0b
```

- `<spec-slug>`: 入力ワークロードの短い人間名 (例 `readheavy-locont`)。可読性 (要件2)
- `<search-tag>`: ablation/探索軸 (例 `fullsearch` / `llmguided` / `llmguided-oee`)。意図的な ablation 再実行を区別 (要件3)
- `<cfg-hash8>`: campaign を決める入力の**正準シリアライズ**を取ったハッシュ先頭 8 hex。決定論・無衝突を保証 (要件1,3)

ハッシュ対象 (= `campaign.lock` の正準 pre-image): spec **の内容** (名前でなく中身) + ccbench-commit + 探索 config (ablation フラグ / Tier 集合 / scale protocol)。再起動時は orchestrator が要求された spec+config を正準化して再ハッシュ → 同じ id → ディレクトリを見つけて WAL をリプレイ。状態を保存せず入力だけから id を再現できる (D が要求する「再起動を跨ぐ安定同一性」)。

**なぜ slug とハッシュの両方か:**
- slug 単独: 無衝突でない。名前が同じで中身の違う 2 spec が黙って衝突 → 2 campaign の WAL が混ざる (致命的)
- ハッシュ単独: 安定・無衝突だが `output/campaigns/a3f9c2d1/` は何も語らず、たどるのに毎回 manifest を開く羽目になる
- 両方: 人間に可読 + ハッシュが同一性を保証。git/docker が `name@digest` を採るのと同じ理由

**ハッシュは spec の「名前」でなく「内容」を覆うこと (正直さの担保).** ワークロード spec を編集して名前を据え置くと、ハッシュが変わり**新しい campaign ディレクトリ**になる → 古い spec の WAL に新しい spec の run を黙って追記しない。spec のずれが自動的に新しい同一性を生む。これは §3.4 の reward-hack 対策 (改竄を識別する / 再構成不可能なエントロピー) を campaign 同一性に適用したもので、「ワークロードを弄ったのに orchestrator が古い campaign を再開して比較不能な run を混ぜた」という静かな汚染を断つ。D12 の honest-by-construction (完全・決定論的射影) の前提でもある。

**意図的な再実行の表現.** 入力が完全に同一なまま別 campaign を切りたい (seed study 等) ときは config に `trial` フィールドを足す → ハッシュが変わる → 別ディレクトリ。「意図的な新規」は config フィールドで表現し、事故では起きない。再開時はハッシュ一致に加えて格納済み正準 config と現在の config を照合し、万一ハッシュ一致で中身相違なら**黙って統合せずエラー**にする。

**env は campaign 同一性に含めない.** env-tag は WAL の per-record フィールドで、性能比較は linux タグの record だけ読む (上の環境タグ節)。1 campaign は Mac (配線テスト用ダミー fitness, phase1 タスク6) と Linux (実 fitness, タスク7) の record を正当に併存させ、射影時に env でフィルタする。env は同一性キーでなく読み出しフィルタ。

**date は同一性キーにしない.** 起動時刻をパスのキーにするとクラッシュ後に別時刻で再開した際に空の新ディレクトリができ、リプレイ対象が見つからず最初からやり直しになる (D 破綻)。created-at は `campaign.lock` 内の provenance として持ち、必要なら slug にソート用プレフィクスとして添えてよいが、**パーティションのルートにはしない**。

---

## Phase 1 への反映

orchestrator/ の実装は、最初から以下を骨格に持つ:

1. **評価ログのスキーマ** (D) — どの段がいつ終わったかを追記する形式を最初に決める。**環境タグを必須フィールドに含める**。書き込み先は campaign スコープ (`output/campaigns/<id>/runs/`) なので、**WAL を開く前に campaign-id を確定する** (上の「出力レイアウトと campaign 同一性」)。リカバリは「どの campaign の WAL か」を入力から再計算して特定する
2. **リカバリループ** (D, A) — 起動時にログをリプレイし、コミット済み variant をスキップ、未コミットを破棄
3. **ベンチの排他実行** (I) — Phase 1 は直列実行なので自明に満たされるが、Phase 2 で並列化する際にロックを入れる前提でコードを構造化する
4. **静定確認** (Admission) — ベンチ前に load average を確認する処理を calibrator に持たせる
