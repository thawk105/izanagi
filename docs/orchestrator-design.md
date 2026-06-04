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
| Consistency | CLAUDE.md の絶対規律 + hooks による enforcement |
| Isolation | ベンチ実行の排他制御 / worktree 分離 |
| Durability | 評価ログの先行書き込み + クラッシュリカバリ |
| WAL | output/runs/ への逐次追記ログ |
| ロックマネージャ | ジョブスケジューラ (ベンチ=排他、ビルド/検証=並列) |
| Admission control | ロードアベレージによる並列度調整 |
| Task partitioning | island model (Phase 3) |

---

## D: Durability — 評価ログとクラッシュリカバリ (最重要)

探索はローカルラップトップで一晩回しっぱなしにする。途中クラッシュ (OOM・ビルド暴走・電源) は必ず起きる前提で設計する。「失敗したらゼロからやり直し」は数千 evaluation のループでは許容できない。

設計:
- 各 variant の評価をログ先行書き込みで進める。`variant X: ビルド開始 → ビルド完了(バイナリhash) → 検証完了(結果) → ベンチ完了(数値) → コミット` を output/runs/ に逐次追記する
- orchestrator は再起動時にログをリプレイし、「どこまで評価済みか」を復元して途中から再開する
- 評価済み variant は再評価しない (ビルドキャッシュと同じ思想で、評価結果もキャッシュ)
- whiteboard memory (却下した設計の蓄積) も durable log の一種として統一的に扱う

サブエージェントは「中間状態を観測できないトランザクション」である。この観測不能性を補うため、**全サブエージェントに構造化ログを書かせ、リトライ時は前回ログから作業を引き継ぐ**。verifier の「構造化フィードバックを返す」規律は、この一般原則の一例。

## A: Atomicity — variant 評価の all-or-nothing

評価パイプライン (ビルド → 正しさ検証 → 性能ベンチ → 記録) の途中で死んだ variant を「半分評価済み」として population に混ぜない。

- コミットポイントは「全段通過して記録された瞬間」のみ
- ログに「コミット」レコードがない variant は、リカバリ時に破棄する (= rollback)
- half-evaluated を許すと、進化ループが「ビルドだけ通った variant」を誤って親に選ぶ等の腐敗が起きる

## C: Consistency — 絶対規律と hooks

CLAUDE.md の絶対規律 = 整合性制約。hooks = その機械的 enforcement。既に雛形で実装方針が確立している (docs/agent-architecture.md 参照)。

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

## Phase 1 への反映

orchestrator/ の実装は、最初から以下を骨格に持つ:

1. **評価ログのスキーマ** (D) — どの段がいつ終わったかを追記する形式を最初に決める。**環境タグを必須フィールドに含める**
2. **リカバリループ** (D, A) — 起動時にログをリプレイし、コミット済み variant をスキップ、未コミットを破棄
3. **ベンチの排他実行** (I) — Phase 1 は直列実行なので自明に満たされるが、Phase 2 で並列化する際にロックを入れる前提でコードを構造化する
4. **静定確認** (Admission) — ベンチ前に load average を確認する処理を calibrator に持たせる
