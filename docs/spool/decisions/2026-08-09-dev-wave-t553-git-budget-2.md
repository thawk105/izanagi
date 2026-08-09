---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-09
wave: dev-wave-t553-git-budget
seq: 2
---

## {{D:git-work-proportional-budget}}. s8c 事前登録の git wall-clock を作業量比例の上限付き予算にする

**決定:** `orchestrator/campaign/s8c_preregistration.py` の `_git` は、固定 15 秒ではなく
次式で算出した予算で git subprocess を待つ。

```
R    = min(stdin の LF 要求行数, MAX_BATCH_REQUESTS)
B(R) = min(GIT_TIMEOUT_SECONDS + R * GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST,
           GIT_TIMEOUT_CAP_SECONDS)
```

`GIT_TIMEOUT_SECONDS = 15.0` (据え置き)、`GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST = 0.0086`、
`GIT_TIMEOUT_CAP_SECONDS = 300.0`。次の 5 条件を必須要件とする。

1. 予算に **caller 引数を持たせない**。`_git` が stdin から一意に算出する。
2. 1 回の `_git` 呼び出し = 1 logical invocation = deadline 1 つ。chunk 分割しない。
3. `MAX_BATCH_REQUESTS` 相当点で**絶対時間 cap** を置く。
4. rate は warm・単独の値から線形外挿せず、競合下の計算ノードでの実測から決める。
5. 実 repo の invariant テストは引数を渡さず production と同じ式を通す。

**理由:**
- 固定値は履歴長に依らないのに、要求数は `commits × paths` で増える。モジュールは
  `MAX_COMMITS = 10_000` / `MAX_BATCH_REQUESTS = 50_000` を受理可能と宣言しているのに、
  15 秒で完走する契約はどこにもなかった。実際に 7,002 要求で 6 回落ちている。
- **CAP は RATE から独立させる。** `CAP = BASE + MAX_BATCH_REQUESTS × RATE` にすると、
  rate の過大推定がそのまま cap の増大になり、絶対上限として機能しない。
  300 秒の根拠は受入全走 1 走の実測 1055〜1408 秒に対して 1/4 未満、かつ計算ノード既定
  walltime 30 分に対して 1/6 未満であること。**この値は RATE を変えても動かない。**
- **`R` に `min` を掛けるのは予算増幅の遮断である。** stdin の行数は command に束縛されないため、
  `MAX_BATCH_REQUESTS` の検査を通らない経路から `_git` へ到達しても予算が CAP を超えないよう、
  算出側で clamp する。
- rate の決定は実測だけでは閉じない。実測は失敗条件を再現できなかった (競合下でも
  最大 0.588973 秒 / 7,044 要求) 一方、production は同じ呼び出しで 15 秒を超えている。
  **実測 (uncensored) と打ち切り観測 (censored) の両方**を使い、後者が示す下界 25.6 倍に
  安全係数 4 を掛けた。導出の正本は `output/insights/2026-08-09_t553-git-budget/MEASUREMENT.md`。

**却下した選択肢:**
- **public API へ timeout 引数を出す** — `timeout=10**9` を止めるものが無い迂回口になり、
  「実 repo で production 既定が効くか」を断言する唯一のテストが無効になる。
- **テスト側で `git-timeout` に限って有限回再試行する** — 規律 2 違反。
  「production 既定での一発成功」という現に成立している断言を「有限回中一成功」へ緩める。
  再試行のたびに OS / git cache が温まるため「恒常的劣化なら全試行が落ちる」分界線も成立しない。
- **git 呼び出しを chunk へ分割し旧 invocation ごとの 15 秒を据え置く** — 総締切が変わらない以上
  赤に無関係で、chunk 境界で reason code が入れ替わる経路が生じる。
- **byte 量を予算に入れる** — `cat-file --batch` の所要は出力 bytes に支配されるが、
  `_git` は実行前に blob size を知らない。caller から渡せば条件 1 に反し、先行の
  `batch-check` を足せば条件 2 に反する。byte 支配の入力は既存の per-blob 16 MiB /
  合計 64 MiB 上限と絶対 CAP で bound する。
- **無 stdin の呼び出しも予算化する** — `rev-list` / `log --name-only` / `ls-tree` は
  実行前に得られる cardinality を持たない。実測では競合下でも 15 秒に対して 6.9〜13.3 倍の
  余裕があるため、本決定の射程外とする。
