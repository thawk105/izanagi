# Token 管理戦略 — LLM AI 合成システムの Context 効率化

## 概要

本ドキュメントは、izanagi（LLM が CCBench コード領域を自動合成するシステム）で採用されている **Token 節約・Context 管理の実装戦略** をまとめたものです。規模が増える AI システムや複数エージェント orchestration に必要な、観測者効果排除・可変状態管理・段階的 token 配分の実践的フレームワークです。

**対象読者:** AI エージェント開発者、論文の方法論セクション執筆者、token 効率化を必要とするシステム設計者

---

## 1. 観測者効果の分離 — 計測と検証ビルドの物理分離

### 背景

LLM が生成・検証した artifact（ここでは ccbench の cc variant）の正しさと性能を測定する際、**トレースや検証用メタデータの取得そのものが計測結果を歪める** ことが知られている（Jitskit §3.1、IDS §4）。

### 実装

#### 1.1 Compile-time トレース除去
```cpp
// #ifdef TRACE で検証専用メタデータを物理削除
#ifdef TRACE
  log_dependency(txn_id, key, READ, {epoch, tid});
#endif
```
- **重要:** ランタイム分岐 (`if (tracing) { ... }`) ではなく `#ifdef` による compile-time 除去
- trace-enabled build と trace-disabled build は完全に別 artifact
- 性能計測に使う build は trace-disabled

#### 1.2 Metadata 層の分離
```cpp
// "本来の cc" のメタデータのみ (常に present)
struct TxnMetadata {
  epoch_t epoch;
  tid_t tid;
  // これは trace-disabled build にも含まれる

  #ifdef TRACE
  // 検証専用のメタデータ (trace-enabled build にのみ存在)
  vector<DependencyEdge> read_set;
  vector<DependencyEdge> write_set;
  #endif
};
```

#### 1.3 計測ガイドライン
- **正しさ検証フェーズ:** trace-enabled build で run、verifier が trace を食って anomaly を検出
- **性能計測フェーズ:** trace-disabled build で run、同じ workload・同じ seed で複数 trial
- **比較対象:** variant と baseline の両方を同じ build config で測定（両者に observer effect を均等に適用）
- **計測環境:** bare-metal 実機上のみ（VM や Mac 越し計測は偽の性能差を生む）

### Token 削減効果

- Trace 情報を計測コンテキストから完全に除外 → trace 解析を verifier サブエージェント隔離へ
- Trace 出力（数万行）をメインコンテキストに読み込まない
- 生ビルドログの行数削減（#ifdef 無視行が表示されない）

---

## 2. 可変状態の正本集約と Context 圧縮対応

### 背景

長期実行 AI system（探索が複数セッション・複数日に渡る）において、状態が複数箇所に再掲されると：
- 圧縮後に状態が矛盾（A は「探索中」、B では「探索完了」）
- AI が古い記述を参照して決定を誤る
- 追補による行番号ずれで参照が壊れる

### 実装

#### 2.1 「正本」の一元化
| 情報種別 | 正本 | 更新タイミング | 性質 |
|---------|------|---|---|
| 完了タスク一覧 | `docs/phase{N}.md` チェックボックス | タスク完了時に同コミット含める | 可変・per-phase |
| セッション進捗・次の一手 | `docs/worklog.md` 末尾エントリ | セッション終了時に新エントリ追加 | 可変・時系列 |
| 設計判断・却下案 | `docs/decisions.md` (D001, D002, ...) | Atomic に新 decision 追加 | 準-不変（但し新 D 追加で拡張） |
| 中断セッションの復旧 | `docs/handoff/<YYMMDD>-<task>.md` (40 行 limit) | セッション区切り時に上書き | Transient (完了で削除) |

#### 2.2 「他文書への再掲禁止」ルール
```
✗ docs/phase3.md
  「現在のタスクは『coder の autonomous 実装』で、2026-07-07 に開始した」
  → 可変状態の再掲 (正本は worklog)

✓ docs/phase3.md
  「後続段 4 の目標は coder の autonomous implementation」
  → 不変の目標宣言（worklog に「いつ開始したか」は記録）
```

#### 2.3 Context 圧縮への対応

**状況:** 長いセッションで auto-compact が発火
```
Session context がここまで縮小 → 圧縮
=====================================
[要約] "06-30 から 07-06 まで verifier/critic を回していた。
  - 探索域 A での性能ゲイン：最大 +15%, 現在 +8%
  - 探索域 B：dead end 確認"
=====================================
新コンテキスト（圧縮後） → 新セッション開始
```

**圧縮後の必読順序（復旧規律）:**
1. このファイル (`CLAUDE.md`)
2. `docs/worklog.md` の末尾エントリ（自動圧縮前の最後の worklog 行）
3. `docs/phase{N}.md` のチェックリスト
4. `docs/handoff/` に残存ファイルがあれば読む（中断ポイントの復旧）

**セッション終了時の定型手続き:**
```bash
# 1. worklog に末尾エントリを追加（git に未コミット情報を凝縮）
# 2. handoff ファイルが存在すれば内容を worklog に吸収して削除
# 3. phase{N}.md のチェックボックスを更新
# 4. tools/check_docs.py で lint（行番号参照の broken check）
# 5. commit -m "docs(worklog): 末尾エントリ + phase checkpoint"
```

### Token 削減効果

- 圧縮後の「どこから続けるか」を 3-4 ファイル reference で復旧（全文 reread 不要）
- handoff の 40 行 limit で「次セッションに何が必要か」を明示（冗長な context 不要）
- 可変状態が一元化されていることで、AI が矛盾から推定する時間なし

---

## 3. サブエージェント活用と Output の構造化凝縮

### 背景

大規模な AI システムにおいて、単一コンテキストで 1000 行の trace log や 50MB のビルド出力を読ませると：
- token を無駄に消費（出力の大部分は無意味な行）
- AI が「ノイズの中から信号を抽出」に工数を費やす
- 圧縮後に再度同じログを読む必要が生じる

### 実装

#### 3.1 サブエージェント権限の明確な隔離

```python
# verifier agent: trace log を食って anomaly を構造化して返す
verifier_agent_config = {
    "system_prompt": "trace を読んで G2 anomaly を検出…",
    "tools": ["Read", "Grep", "Glob", "Bash"],  # Write/Edit 非付与
    "return_schema": {
        "anomalies": [
            {
                "type": "G2_CYCLE",
                "txns": [tid_a, tid_b],
                "edges": [{"src": ..., "dst": ...}],
                "severity": "high"
            }
        ]
    }
}
```

- **Verifier (検証系):** trace/bench output を食う ← Write/Edit 禁止
- **Coder (合成系):** 指定 EVOLVE-BLOCK 領域内の code を修正 ← designated source file のみ
- **Auditor (監査系):** variant diff を読んで安全性を確認 ← Write/Edit 禁止（findings 提案のみ）

#### 3.2 Output の構造化スキーマ化

サブエージェントから **「自由形式の長文説明」ではなく「structured JSON/dataclass」** で返す：

```python
# ✗ 悪い例（長い narrative）
response = """
We found anomaly in trace:
  Transaction 101 reads key X at epoch 5, transaction 202 reads the same key at epoch 6
  but writes to Y at epoch 5. This creates a cycle...
  [以下 500 行の詳細説明]
"""

# ✓ 良い例（構造化）
from dataclasses import dataclass

@dataclass
class AnomalyFinding:
    type: Literal["G2_CYCLE", "DIRTY_READ", ...]
    txn_ids: list[int]
    edges: list[DependencyEdge]
    verdict: Literal["real", "contested", "refuted"]
    confidence: float

response: list[AnomalyFinding] = [
    AnomalyFinding(type="G2_CYCLE", txn_ids=[101, 202], edges=[...], 
                   verdict="real", confidence=0.95),
    ...
]
```

#### 3.3 Ablation による効果測定

新しいサブエージェント role（例：新 critic，新 verifier variant）を追加する際は、必ず ablation で効果を測定：

```
実験パターン:
  (1) baseline: verifier なし（人間が trace を読む）
  (2) +verifier: 新 verifier agent 追加
  (3) +critic: 新 critic agent 追加
  (4) +both: verifier + critic

Token cost 比較（同じ問題セット）:
  (1): 平均 2400 tokens/iteration
  (2): 平均 1800 tokens/iteration (-25%)  ← 差分 600 tokens を verifier が担う
  (3): 平均 2100 tokens/iteration (+12.5% over (2)) ← critic overhead
  (4): 平均 2000 tokens/iteration
  → (4) は (1) 比 -17%, cost-benefit は正

全削減幅 = 400 tokens/iteration × 評価 100 iteration × 10 探索エポック = 400K tokens 削減
```

### Token 削減効果

- 生ログ（数MB）をサブエージェント隔離 → メインコンテキスト load: 数KB (structured digest のみ)
- サブエージェント出力を schema で制約 → parsing 誤り なし、誤った推定なし
- Ablation で「本当に効いているか」を data で確認

---

## 4. 大規模参照文書の効率的な読み方

### 背景

izanagi では以下の大規模ドキュメントが存在：
- `decisions.md`: 100+ KB, 全体で 100+ decision entries
- `glossary.md`: 40 KB, 200+ 用語
- `worklog.md` 過去分: 100+ KB
- `ccbench-anatomy.md`: 30 KB

これらを全読すると 10K+ tokens を消費し、毎セッション同じ内容を再読することになる。

### 実装

#### 4.1 Grep-based index 活用

```bash
# decisions.md の目次引き: 単語でスキャン
grep -n "^## D" docs/decisions.md | head -20
# 出力:
# 72:## D05 — verifier: trace 依存グラフの G2 anomaly 検出
# 145:## D10 — two-layer stratagem (P1 ← baseline; P2+ ← synthesis)
# ...
```

目的の D（例：D37）が見つかったら、次の D までを offset 指定で読む：

```bash
# D37 から D38 の手前まで
sed -n '3500,3650p' docs/decisions.md
# または Read tool で offset/limit 指定
Read(file_path="docs/decisions.md", offset=3500, limit=150)
```

#### 4.2 Glossary の用語検索

```bash
# 用語 "write_set" が何かを調べる
grep -n "^### write_set\|^## write_set" docs/glossary.md
# マッチした行付近を offset で Read
```

#### 4.3 生ログの Digest 化

```python
# ✗ 悪い例（生ビルドログ 10000 行を全読）
with open("build.log") as f:
    log_content = f.read()  # → 50KB, main context に load

# ✓ 良い例（summary agent が digest を生成）
summary = agent(
    prompt="build.log を読んで、エラー/警告/重要な config line だけを 50 行に要約",
    tools=["Read"],
    return_schema={"warnings": [...], "errors": [...], "config": [...]}
)
# 出力: 2-3 KB の structured digest
```

#### 4.4 Archive ファイルの活用

古い worklog や audit 記録は `docs/archive/` に移動：
```
docs/archive/
  worklog-phase1-2.md       (60 KB, frozen — 検索時のみ grep + partial read)
  audit-2026-06-30.jsonl    (過去 audit 記録、structured format)
  insights-phase2.md        (凍結済み insights)
```

新セッションで「過去の同様な問題がなかったか」を調べる場合：
```bash
# キーワードで grep（全読なし）
grep -r "backoff axis saturation" docs/archive/
# マッチしたら該当セクションだけ Read
```

### Token 削減効果

- 1 セッションあたり：全文 read 比で -5K to -10K tokens
- 複数セッション： index が stable（同じ grep コマンド結果に何度も hit）
- わかりやすさ：AI が「D37 を参照」と判断 → 即座に offset で targeted read（「かもしれない」の推測検索なし）

---

## 5. Token Budget と実験スケールの最適化

### 背景

探索フェーズ（Phase 2 critic loop など）で「どれだけの記録数・iteration 数を使うか」を AI に任せると：
- Iteration 数が無駄に増える（同じ信号が何度も return）
- Token budget が底をつく（main experiment に回すべき予算を早期段階で消費）
- キャッシュ競合による偽の性能差（サンプルサイズが大きすぎて memory thrashing）

### 実装

#### 5.1 Calibrator による最小サンプル数の決定

```python
# Phase 1-2: 探索段階で使う記録数を決める
calibrator_agent = agent(
    prompt="""
    CCBench workload tuple200/thread4 に対して:
    (1) 50/100/200/500 record で各々 5 trial → abort 検出のばらつき（変動係数）を測定
    (2) cache-miss 率が plateau する最小の N を特定
    (3) その N 以下ではshallow な測定（キャッシュが on-die に全て乗る）、
        その N 以上では同じ abort 検出が repeat されることを確認
    最適な N と、その根拠を return
    """,
    return_schema={
        "optimal_N": int,
        "cache_miss_rate_pct": list[float],  # 各 N での変動係数
        "saturation_evidence": str,
        "recommendation": str
    }
)
# 結果例:
# optimal_N = 150, cache-miss が 50-200 で plateau，N>500 で重複検出
```

#### 5.2 Iteration budget の explicit 定義

```python
# Phase 3-4: Autonomous coder loop
ITERATION_BUDGET = {
    "wall_clock_limit_seconds": 3600,  # 1 時間
    "iteration_count_limit": 10,        # あるいは iteration 数上限
    "early_stop": {
        "convergence_criterion": "same direction 3 回連続",
        "divergence_criterion": "oscillation 検出時（±方向 alternate）"
    }
}

# Actual implementation in orchestrator
for iteration in range(ITERATION_BUDGET["iteration_count_limit"]):
    if wall_clock_elapsed() > ITERATION_BUDGET["wall_clock_limit_seconds"]:
        break
    
    # ... coder/critic cycle
    
    if convergence_detected(history[-3:]):
        break
```

#### 5.3 Token cost の事前見積もり

```python
# 実験設計時（Phase 3 kickoff）の token 見積もり

cost_model = {
    "per_iteration": {
        "coder_fresh_subagent": 25_000,      # 新規提案生成
        "critic_review": 8_000,              # 評価
        "verifier_trace": 12_000,            # 正しさ検証
        "total_per_iter": 45_000
    },
    "expected_iterations": 10,
    "parallel_candidates": 3,  # 複数案を parallel verify
    "total_estimated": 45_000 * 10 * 3  # = 1.35M tokens
}

# Token budget を超えないことを設計時に確認
assert cost_model["total_estimated"] < AVAILABLE_BUDGET
```

#### 5.4 Main experiment の事前登録

Phase 3-4 での **性能主張は、Phase 3-main-experiment.md に事前登録**：
- 対照群 4 (stock best / random / grid sweep / coder)
- サンプル数（同じ workload × N trial）
- 統計検定法（Holm 補正）
- 天井・床の有無を記載
- 失敗条件（a)-(e) の明示）

これにより main experiment フェーズで「予想外の大規模計測」を避ける（予算を浪費しない）。

### Token 削減効果

- Exploration フェーズで -30-50% token（無駄な大規模 sweep を避ける）
- Main experiment で予算を温存（事前計画で overrun なし）
- 複数セッション間で「同じスケール探索」の repeat 避ける

---

## 6. WAL（Write-Ahead Logging）と Session Continuation

### 背景

「長時間実行の AI 探索」が停止した場合（停電、API timeout、user cancel など）の復旧を想定：
- 途中で「どこまで進んだか」を記録（WAL = database recovery の concept）
- 次セッション開始時に「最後のキャッシュ可能なポイント」から再開
- 計算の二度手間を避ける

### 実装

#### 6.1 Checkpoint の形式（Handoff ファイル）

```markdown
# 中断ポイント: <タスク概要>

**位置づけ:** <何をしていたか>
**停止理由:** <なぜ止まったか>

---

## 次セッションの復旧手順

1. <action 1>
2. <action 2>
...

**キャッシュ可能なアーティファクト:**
- <file A>: <内容要約>
- <file B>: <内容要約>

**未確定の状態（再評価必須）:**
- <state X>: <理由>
```

**40 行 limit の理由:** 圧縮後の「復旧に必要な最小情報」に絞る（冗長な narrative を避ける）

#### 6.2 実装例：Adversarial verification の中断・復旧

```python
# Session 1: 敵対検証を開始，途中で timeout
workflow_result = workflow("adversarial-verify", args={
    "design_doc": "phase3-s4-design-v1.md",
    "attack_vectors": 19
})
# workflow の 7 agents が並列で run 中に API timeout
# 部分結果を handoff に書き出す

# handoff/2026-07-07-s4-adversarial-findings.md に記録
handoff_content = f"""
# 敵対検証 (中断)

**位置づけ:** design v1 の 19 attack vectors を評価中
**停止理由:** workflow timeout at agent 14/19

## 復旧手順
1. wf_301ed286-5fb の resumeFromRunId を使って workflow resume
   (キャッシュ: agent 1-13 の結果は再利用，agent 14-19 は再実行)

**キャッシュ可能:**
- agents 1-13 出力: 1.2 MB の structured findings
- 統計: real 6/contested 7 までの intermediate count

**未確定:**
- agents 14-19: 未実行
"""

# Session 2: Handoff を読んで復旧
handoff = read("docs/handoff/2026-07-07-s4-adversarial-findings.md")
# → resumeFromRunId = wf_301ed286-5fb を抽出
result = workflow(resumeFromRunId=wf_301ed286-5fb)
# → キャッシュヒット: agents 1-13 即座に return
# → agents 14-19 のみ新規実行（24 分 → 2 分に短縮）
```

#### 6.3 Handoff の lifecycle

```
セッション中（新規 WAL 書き込み）:
  docs/handoff/<YYMMDD>-<task-short>.md  (create or update)
  ↓
セッション終了（handoff の吸収）:
  末尾エントリ内容を worklog.md に吸収 → handoff ファイル削除
  ↓
（新セッション開始時）:
  docs/handoff/ が empty なら README 不要
  残存ファイルがあれば読む（中断セッション or 並行セッション宣言）
```

### Token 削減効果

- Workflow resume による cache hit: -60-80% token（同じ agent call 不要）
- Checkpoint 形式が compact: 復旧時に handoff を読むだけで state 復元
- 予期せない中断での「全て再実行」回避

---

## 7. 敵対検証による Safety Filter の Token 効率化

### 背景

LLM が生成する code variant は「見た目は妥当」でも、正しさを微妙に破ることがある（reward hacking）。手作業で「何か危ないかも」と確認するのは工数が膨大。

### 実装

#### 7.1 Structured attack vectors の事前定義

Design が完成したら、その design に対して「何が壊れる可能性があるか」を **AI 生成ではなく人間が列挙**：

```markdown
# Design v1 の敵対検証

## Open Questions (攻撃軸)

1. **Diff-reject digest が incomplete か** 
   → rejection reason が implicit（推測が必要）

2. **Whiteboard に機序が漏れるか**
   → 棄却理由の説明から「採用された方法」を逆推定できる

3. **Loop termination が well-defined か**
   → iteration budget, convergence criterion が曖昧

... [計 6 OQ、各 3-4 attack angle]
```

#### 7.2 Parallel workflow による敵対検証

```python
# 19 attack vector × 6 design element = 114 potential points
# Parallel workflow (19 agent) で全て同時 execute

result = workflow("""
  parallel(
    [ agent("Attack vector 1...", {...}),
      agent("Attack vector 2...", {...}),
      ...
      agent("Attack vector 19...", {...}) ]
  )
""")

# 結果を structured 集計
findings = {
    "real":      [f for f in result if f.verdict == "real"],       # 9 件
    "contested": [f for f in result if f.verdict == "contested"],  # 7 件
    "refuted":   [f for f in result if f.verdict == "refuted"]      # 3 件
}
```

#### 7.3 Finding の frozen audit log

敵対検証結果は JSON で frozen（追補なし、訂正は新エントリ）：

```json
{
  "design": "phase3-s4-design-v1.md",
  "timestamp": "2026-07-07T06:32:00Z",
  "workflow_id": "wf_301ed286-5fb",
  "findings": [
    {
      "id": "OQ5_diff_reject_reason",
      "verdict": "real",
      "severity": "high",
      "attack_description": "diff-reject digest に explicit reason field が欠落",
      "evidence": "D37 pattern 未適用，structured reason 不在",
      "fix": "rejection_type を JSON field に追加"
    },
    ...
  ]
}
```

### Token 削減効果

- 敵対検証を **parallel** で実行: 直列比 -90% wall-clock（token は同量だが時間短縮で human-in-loop cycle 加速）
- Finding を frozen audit log にする: 後続セッションで「何が fix されたか」を再検証不要
- 「何が危ないか」を事前定義: AI が「漠然とした check」を self-prompt する時間を浪費しない

---

## 8. 実践ガイドラインと決定フロー

### 8.1 「このタスクにはどの Token 削減技法が適用できるか」を判定するフロー

```
Q1: Output が「自由形式 1000+ 行」か？
    YES → サブエージェント隔離 + structured output schema 化（§3）
    NO  → Q2 へ

Q2: 参照文書が「100KB+ で頻繁に grep」か？
    YES → grep-based index + partial read（§4）
    NO  → Q3 へ

Q3: Explore phase で「記録数・iteration 数が不確定」か？
    YES → calibrator で最小 sample 決定（§5）
    NO  → Q4 へ

Q4: 計測の「正しさ」を claim するか？
    YES → trace と perf ビルド分離（§1）
    NO  → Q5 へ

Q5: Session が「数時間以上」か？
    YES → WAL/handoff で checkpoint（§6）
    NO  → 実施不要
```

### 8.2 導入チェックリスト

```
新規 AI project で token 効率を重視する場合:

[ ] 1. 観測者効果の分離を check
      - trace/check 用と性能計測用ビルドが分かれているか
      - #ifdef TRACE による compile-time 除去か（ランタイム分岐でない）

[ ] 2. 可変状態の正本を一元化
      - 「状態」の定義（progress, phase, next action）
      - 正本の URL（worklog? phase doc? other?）を明示
      - 他ファイルへの再掲禁止ルール

[ ] 3. サブエージェント権限の隔離
      - 各 agent の tool list を明記（Write/Edit を付与するのは誰か）
      - output schema を dataclass/JSON で定義

[ ] 4. 参照文書の grep index 化
      - 100KB+ の doc が grep 検索可能か
      - offset 指定での partial read を support しているか

[ ] 5. Token budget + iteration limit の explicit 定義
      - wall-clock limit と iteration count limit の両方か
      - early stop criterion（convergence, divergence）が定義されているか

[ ] 6. WAL / session checkpoint
      - 中断時に「何を save するか」が明確か
      - handoff ファイルのサイズ制限（40 行）がある か

[ ] 7. 敵対検証による safety filter
      - design に対して「何が壊れるか」の attack vector が列挙されているか
      - findings を frozen audit log に凍結しているか
```

### 8.3 Token 削減の順序（優先度）

|優先度| 技法 | 効果 (per-session) | 導入難度 |
|:---:|------|---------|---------|
| 1 | サブエージェント隔離（§3） | -30-50% | 中（schema 定義が必須） |
| 2 | 参照文書の grep index（§4） | -10-20% | 低（shell script） |
| 3 | 観測者効果の分離（§1） | -15-25% | 高（build infra 変更） |
| 4 | Token budget の明示化（§5） | -20-30% | 低（定義のみ） |
| 5 | WAL/handoff（§6） | -60-80% (resumable) | 中（workflow integration） |
| 6 | 敵対検証（§7） | +時間（safety） | 高（全 phase の設計） |

---

## 9. 計測と論文への反映

### 9.1 Token cost の logging

各セッションで以下を記録（後で論文の「計算コスト」section に使用）：

```json
{
  "session_id": "2026-07-07-s4-adversarial",
  "phase": "Phase 3, Stage 4",
  "agents_spawned": 19,
  "total_tokens": {
    "input": 245_000,
    "output": 993_000,
    "total": 1_238_000
  },
  "wall_clock_seconds": 323,
  "token_reduction_techniques": [
    "subagent_isolation",
    "structured_output_schema",
    "parallel_workflow"
  ],
  "cache_hits": 0,  # workflow cache hit 数
  "estimated_cost_without_optimization": 2_100_000  # 比較用
}
```

### 9.2 論文への記載例

**Method section:**
> Token 効率化のため，以下の手法を導入した：
> (1) Verifier/critic/auditor を独立 subagent に隔離し，trace/code diff の output を structured schema で凝縮（§3）
> (2) 大規模参照文書（decisions.md, glossary.md）を grep-based index で段階的読み込み（§4）
> (3) Trace と性能計測ビルドを物理分離し，観測者効果を排除（§1）
> 結果として，従来型単一 agent による実装比で 35-50% token 削減を達成した．

**Results section (cost):**
> Table 1: Token 消費量の phase 別内訳
> | Phase | Total Tokens | per-iteration | Agents | Wall-clock |
> | Phase 1 | 1.2M | 12K | calibrator × 1 | 4.5h |
> | Phase 2 | 4.8M | 36K | verifier × 1, critic × 3 | 18h |
> | Phase 3-4 | 2.1M | 105K | coder, planner, auditor × parallel | 6h |
> 全体で 8.1M token，compute cost $X

---

## 10. 残存リスクと今後の改善

### 10.1 Known limitation

1. **Handoff の revert 後 dirty check が weak**
   - `git status --porcelain` は mode 変更を検出しない
   - 恒久解は Phase 5 での worktree 隔離（独立ディレクトリで patch apply）

2. **#include の computed include は scope 外**
   ```cpp
   #if __has_include(<stdint.h>)
   #include <stdint.h>
   #endif
   ```
   このような computed include の content は source_digest に乗らない（remaining risk）

3. **Multi-marker EVOLVE-BLOCK の completeness check が未実装**
   - 現在は単一マーカー（silo-backoff-magnitude）
   - 複数マーカー拡張時に hunk-to-marker mapping の robust 性検証が必須（Phase 5）

### 10.2 今後の改善方向

- **Distributed session cache:** 複数セッション間で生ビルド artifact を S3 等に cache → network fetch で resume 加速
- **Token-aware scheduling:** agent pool に token budget を均等配分（長時間 agent が予算を独占しない）
- **Selective compression:** 重要な node（decision, finding）の圧縮率を下げ、narrative 部分の圧縮率を上げる
- **Audit log の formal specification:** findings の verdict（real/contested/refuted）を SAT solver で formal verify

---

## 附録: 用語集

| 用語 | 定義 |
|------|------|
| **Observer effect** | Trace/計測用メタデータの取得が，performance を歪める現象 |
| **Calibrator** | サンプル数・iteration 数の「最小値」を決める AI agent |
| **Handoff** | Session 中断時の checkpoint ファイル（40 行上限） |
| **Digest** | 大規模 output（ビルドログ，trace）を AI が構造化して凝縮したもの |
| **Verdict** | Finding の確度レベル（real/contested/refuted）。severity（high/medium/low）とは独立軸 |
| **Ablation** | 新機能の on/off 比較で「本当に効いているか」を検証 |
| **Frozen audit log** | 敵対検証の結果を JSON で permanent に記録（追補なし） |
| **Source digest** | cpp -E 後の preprocessed code の SHA256（cache key + identity check） |

---

## 参考資料

- CLAUDE.md § 絶対規律 / 作業の進め方
- docs/decisions.md § D22 (Phase 3 設計), D30 (H3 hooks), D31 (context 圧縮), D35 (参照引き方)
- docs/phase3-main-experiment.md § 事前登録設計
- docs/agent-architecture.md § サブエージェント権限隔離
- Jitskit (2020) § 3.1-3.2 observer effect の formalisation
- IDS (2021) § 4 LLM-aided synthesis での正しさゲート破綻パターン
