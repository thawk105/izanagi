# coder 入力仕様 (stage 4 autonomous)

## 1. Template 定義

### 現行 baseline (BACKOFF_FIXED=50)

位置: `external/ccbench/include/backoff.hh:58-74`

```cpp
// EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
// izanagi Phase 3 (D22/phase3.md): この条件コンパイル骨格 (if/else/endif の三枝) だけが
// coder (LLM) の編集面。coder が書くのは合成枝 (BACKOFF_FIXED が 0 以上のとき選ばれる枝) の
// 中身のみ — backoff の量 (now_backoff) を Cicada 適応 hill-climbing の代わりに合成する純
// timing 変異。stock 枝 (適応 Backoff_ を逐語温存) とマーカー・骨格は不可触 (人間が一度入れた)。
// 既定 -1 は stock 枝を選び preprocess 後ソースが原本と同一 → inert (規律2、D18)。
// 閉じた領域制約 (D23 道Y、hook が機械執行): 既存 silo API を呼ぶ straight-line code のみ。
// ヘッダ取り込み・型/関数/マクロ定義の追加、生の条件指令 (if/ifdef/elif 系)、非決定ビルトイン
// (DATE/TIME 系) を禁止 (このコメントは行頭アンカー走査で誤検出しないよう生トークンを避ける)。
#if BACKOFF_FIXED >= 0
    double now_backoff = static_cast<double>(BACKOFF_FIXED);  // <- 合成枝 (hole) / coder がここを編集
#else
    double now_backoff = Backoff_.load(std::memory_order_acquire);  // <- stock 枝 (人間の領域)
#endif
// EVOLVE-BLOCK-END silo-backoff-magnitude
```

**合成枝 (hole)：** `double now_backoff = ...;` のみ。値の表現 (リテラル・計算式・既存 API 呼び出し) は自由。

---

## 2. API Surface (coder が呼んでよい既存関数)

### Backoff class (from include/backoff.hh)

```cpp
class Backoff {
  // Static members
  static std::atomic<double> Backoff_;     // 現在の適応 backoff 値 (microseconds)
  static void update_backoff(double new_backoff);  // Cicada による勾配更新
  static double load();  // 現在値を読む (memory_order_acquire)
  
  // Public constants
  // (なし —定数は define で与えられる)
};
```

### 使用例

- 静的値: `double now_backoff = 50.0;`
- Cicada 適応値の読み: `double now_backoff = Backoff_.load(std::memory_order_acquire);` (stock 枝と同じ)
- 計算式: `double now_backoff = std::ceil(50.0 * 1.5);`
- リテラル以外の式は許可されるが、新しい依存 (ヘッダ・関数) は追加禁止

### 禁止事項

- #include の追加
- 型・関数・マクロの定義
- #if / #ifdef / #ifdef / #else など条件指令
- タイムスタンプ・乱数などの非決定ビルトイン
- Cicada 内部の lock/rwlock の直接参照 (Backoff class public interface のみ)

---

## 3. Leading Indicators (planner が提案する方向の根拠)

> **⚠ 本節も §4/§6/§7 と同じく旧設計 (D39/D45 以前) で superseded。§6 のバナーが述べるとおり、本節の
> leading-indicator 記述・具体値域は現行運用でどこにも渡らない** — 本ドキュメント自体が coder 非提供 (D45)、
> planner (planner-v4) が受け取る leading-indicators は計測層の構造化出力であって本節ではない。経緯記録として残す。

coder が「値をどう変えるか」を提案された時の参考指標：

### Backoff の効果
- **低すぎる (0-10us):** abort 後のスピンタイムが短い → cache line 競合が激化 → abort 率↑
- **中程度 (50-100us):** 競合を軽減しつつ latency penalty が小さい → throughput 最大
- **高すぎる (500us+):** スピン時間が長い → latency ↑、throughput ↓ (Cicada の適応で既に optimal 付近)

### 現行 baseline
- 値: 50 (microseconds)
- 効果: 1m/t48/skew0.9 workload で throughput 最大 (性能が出ている)
- Cicada の勾配: 負 (adaptive は既に high-contention regime)

### 変異の方向性 (planner が提案)
- **「低下」**: contention が低い workload で試す (但し segment 4 では変えない予定)
- **「増加」**: contention leader (abort 率 >10%) の workload で試す (効果実績: +2-5%)
- **「explore_both」**: 軸が未飽和だと判定した場合

---

## 4. Measurement Results (旧設計の現行値記録)

> **⚠ 本節は §7 と同じく旧設計 (D39 以前) で superseded。この throughput/abort/latency 値は現行運用で
> coder に一切渡らない** — 本ドキュメント (coder-spec.md) 自体が coder 非提供 (D45)、coder が受け取るのは
> `coder-leakproof-context.md` の inline 全文 (勝ち筋値・利得を物理削除済み) + planner の抽象方向 +
> 射影済み baseline/whiteboard のみ。具体値を coder が信頼するとリーク経路になるため、本節は経緯記録として残す。

### stock (BACKOFF_FIXED=-1・Cicada 適応)
```json
{
  "workload": "1m/t48/skew0.9/rr50/rmw0/max_ope10/extime3",
  "throughput_ops_sec": 87432.5,
  "abort_rate_pct": 8.2,
  "avg_latency_us": 547.3
}
```

### baseline 50 (BACKOFF_FIXED=50)
```json
{
  "workload": "1m/t48/skew0.9/rr50/rmw0/max_ope10/extime3",
  "throughput_ops_sec": 88124.1,
  "abort_rate_pct": 7.9,
  "avg_latency_us": 543.7
}
```

**diff:** +692 ops/sec (+0.79%), abort -0.3 ppt, latency -3.6us

---

## 5. Coder の提案形式 (structured output)

> **⚠ 本節も旧設計の記録で superseded。現行の出力スキーマの正本は agent 定義
> (`.claude/agents/coder-v4-autonomous.md`。軸派生の `-sort` / `-trigger-gating` はスキーマが異なる —
> value フィールドなし)。本節は段 4 backoff 軸の旧記述であり、経緯記録として残す。**

```json
{
  "proposal": {
    "axis": "silo-backoff-magnitude",
    "value": 65,
    "justification": "<planner の方向を受けて、なぜこの値を選んだか。数字はなし>",
    "implementation": "double now_backoff = 65.0;",
    "confidence": "high" | "medium" | "low"
  }
}
```

---

## 6. Coder の制約 (リーク制御)

> **⚠ 本節も §7 と同じく superseded (D45/D39)。下記「許可」は本ドキュメントを coder に渡していた旧設計の
> 記述であり、現行運用では coder-spec.md 自体が coder 非提供。coder が実際に受け取るのは
> `coder-leakproof-context.md` の inline 全文のみで、§3/§4 の leading-indicator・現行値はどこにも渡らない。**

### 許可 (旧設計)
- CCBench API surface (Backoff class public interface)
- 値 (リテラル・計算式)

### 禁止
- output/insights/2026-06-22_p2-case-study-* (sweet-spot value や利得情報)
- backoff-sweep campaign の WAL・reports・profile JSON
- main-experiment §24/§59 の「ここまで試した値」リスト
- decisions.md の具体値・機序・利得 (§319, §338)
- phase3.md 残存リスク節 (「勝ち筋は X us」の具体値)

これらの情報は **planner が方向のみを提案するメカニズム** で遮断される。

---

## 7. Coder の入力 context 構成

> **⚠ 本節は旧設計 (D39 以前の予約) で superseded。現行運用では本ドキュメント (coder-spec.md) を
> coder に渡さない** (sweet-spot 漏れリスク — 段4b runbook §1(b) が明示禁止)。coder が受け取るのは
> `coder-leakproof-context.md` の inline 全文 + planner の抽象方向 + 射影済み baseline/whiteboard のみ
> (D45)。本節は経緯記録として残す。

**用意するファイル:**
1. 本ドキュメント (`coder-spec.md`)
2. `coder-leakproof-context.md` — curated contextファイル (下記参照)

**coder.md agent は以下を受け取る:**
- spec: `coder-spec.md` の 1-3 節 (template + API)
- leading-indicators: 本ドキュメント 3 節
- current-baseline: 本ドキュメント 4 節
- planner-proposal: planner agent からの構造化出力 (方向 + magnitude only)
- whiteboard: 評価済み提案 (値なし、「なぜ棄却」のみ)

**受け取らないもの:**
- 4節以下の文書 (4節の measurement は aggregate のみ、詳細 profile/WAL/grid fitness なし)
- output/ 以下のファイル

---

## 8. 段 5 への引き継ぎ

> **⚠ 本節は履行済みの旧計画で superseded。段 5 (sort 軸) は完了済み** (記録 =
> `docs/archive/phase3-kickoff-stages1-5.md`、2026-07-10 凍結)。sort 軸の template は
> `external/ccbench/cc/silo/transaction.cc` の EVOLVE-BLOCK として実装されたが、下記の
> 「coder-spec.md を拡張」する予定は採られず、現行の正本は `docs/phase3-s5-sort-runbook.md` と
> agent 定義 (`.claude/agents/coder-v4-autonomous-sort.md`)。経緯記録として残す。

段 4 で backoff 軸を合成したら、段 5 で lock-sort 軸が追加される予定。その時：
- 新軸の template を同じパターンで `external/ccbench/cc/silo/transaction.cc` に追加
- coder-spec.md を拡張 (section 1-3 に新軸の API を追加)
- planner に新軸の leading-indicator を教示

但し段 4 では lock 編集面が許可されていないため (D38)、実装順序は本 spec のままとする。
