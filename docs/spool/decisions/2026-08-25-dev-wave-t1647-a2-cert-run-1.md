---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1647-a2-cert-run
seq: 1
---

## {{D:nqsv-state-vocabulary-single-source}}. NQSV の状態語彙は共有 leaf 1 箇所に置き、campaign と dispatcher の双方が使う

**決定:** `qstat -f` の状態 field 正規化と target-bound parser を stdlib-only の
`orchestrator/scheduler_nqsv.py` に置き、`tools/pegasus/dispatch_compute.py` と
paper-story A-2 の投入時可視性検査が同じ実装を使う。A-2 が受理するのは正規化後の
`QUE` / `RUN` だけで、receipt の `state` field と submission receipt の schema version は
変えない。`orchestrator/campaign/` から `tools/` を import しない。

**理由:**
- A-2 は `Request State = QUE|RUN` の行を要求していたが、実 NQSV はその行を出さない。
  投入直後は `Current State = Staging`、実行中は `Current State = Running` である。
  実装は実環境で一度も満たせない述語を持っていた。
- 受理集合を新規に発明する必要が無かった。dispatcher 側に `Request State` /
  `Current State` / `State` の 3 形式を正規化する land 済みの語彙が既にあり、
  `staging` と `queued` を `QUE`、`running` と `pre-running` を `RUN` へ写す。
- 実測値だけを受理集合にする案 (`Current State ∈ {Staging, Running}`) は過学習だった。
  本 wave の本走 2 回目は投入後 `Current State = Queued` で待機しており、
  その案なら**正常運用で fail-closed していた**。
- 語彙を 2 箇所に置くと二重の真実になる。dispatcher の destructive gate が持つ
  「request ID ちょうど 1 つ」「state field 各々高々 1 つ」「併存時に正規化後が一致」
  「対象 ID より前に state が無い」の 4 条件も、A-2 の投入時可視性が必要とする性質と同じである。

**却下した選択肢:**
- `Current State` 専用の case-sensitive parser を A-2 に新設する — dispatcher と語彙が
  食い違い、request ID の `:` / `=` 両形式の扱いもずれる。
- `orchestrator/campaign/` から `tools/pegasus/dispatch_compute.py` を直接 import する —
  層の逆転であり、executable tool を library として扱うことになる。
- 到達不能になった `Request State` 枝を残す — 実形式の証拠を持たない受理枝が生き続ける。
  ただし終端側は `Current State` 形式を既に受理しており、そちらは触らない。

## {{D:pbs-jobid-not-a-path-component}}. `PBS_JOBID` を path 要素にしない

**決定:** NQSV の `PBS_JOBID` から path を作るときはコロンを取り除く。
証拠として記録・照合する `PBS_JOBID` の逐語利用は変えない。

**理由:**
- `PBS_JOBID` は `0:945411.nqsv` の形で必ずコロンを含む。make は依存 path のコロンを
  rule 区切りと解釈するため、`find_package` が返す archive の絶対 path や
  FetchContent の source path がコロンを含むと build が
  `target pattern contains no '%'` で必ず落ちる。
- 計算ノードで 4 arm の対照実験を行い、依存 prefix と FetchContent base のコロンが致命で
  build dir 自身のコロンは無害であることを確定した。
- 一方 `PBS_JOBID` は予約証拠・completion 照合・qstat 照会の束縛に使われる。
  path のために正規化した値をそちらへ流用すると証拠鎖が切れる。
  **正規化の適用面は path 生成に限る。**

**却下した選択肢:**
- scratch を `PBS_JOBID` 以外の識別子にする — 同一ノードで複数 job が走る場合の
  一意性を失う。コロンだけを置換すれば一意性は保たれる。
- build dir だけを避ける — 実測では依存 prefix と FetchContent base が致命であり、
  build dir は無害だった。避ける場所を取り違える。
