---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-08
wave: dev-wave-t627-noop-binding
seq: 1
---

## {{D:activation-transition-bound-pair}}. activation の世代遷移は (generation, contract hash) の対を同一入力として検査する

**決定:** activation record chain の連続 record 間の遷移検査を、次の形で実装する。

- 述語の入力は各 env の `(generation, contract_sha256)` の**対**であり、番号だけの射影ではない。
- 変化した env すべてについて `successor.generation == predecessor.generation + 1` を要求する。
  **env ごとに評価し、総和・最大・個数などの集約量で判定しない。**
- 変化した env すべてについて、その対を registry の `GenerationEntry` へ exact 解決したうえで
  `is_valid_successor` が真であることを要求する。最初の 1 件で打ち切らない。
- 全 env の対が据置なら no-op として拒否する。据置 env の混在は許す。
- successor 判定は loader の**既定値なし keyword-only 引数**として注入し、
  production 側 adapter が `GENERATIONS` を**呼出し時に**読んで解決する。
  activation record の schema leaf は環境契約 module を import しない (stdlib-only を維持)。
- 発行 tool は同じ adapter を loader へ渡すだけとし、独自の遷移判定を持たない (実効 gate は 1 箇所)。

D228 の遷移規則そのものは変えない。本決定はその**実装形**を固定するものである。

**射程 (この決定が保証しないこと):** 束縛するのは「検証済み production generation snapshot に対する
record-level edge」だけである。contract 実体の rollback、世代列の再定義、module 属性の再束縛、
逆引き index の再束縛、較正の新旧は D228 と同じく射程外であり、塞いだと読める記述を置かない。

**理由:**
- 番号だけを見る述語は、後継世代が旧較正を指す再束縛を素通しする (D176 が「逆引き index を
  authority として扱ってはならない」と定めたのと同じ理由)。対を同一入力にすることで、
  番号の前進と contract 同一性の検査が同じ判断の中で閉じる。
- 集約量による判定は、複数 env の相殺を受理する。実測でも、変化 env ごとに見ない実装は
  `(+2, −1)` や `(+1, −1)` を受理し、提案されたテスト表を全部通った。
- registry catalog の隣接だけに頼る案は、loader が受け取る catalog を呼び出し側が任意に構成できる
  以上、loader の契約上は `is_valid_successor` との合成が現れない。必須注入にすると、
  合成が公開署名の上に現れ、省略が型エラーになる。
- adapter が import 時 snapshot を closure で捕捉すると、registry を差し替える既存の試験経路と
  分裂する。既存 consumer も load 後に module-global を読み直しており、呼出し時参照が整合する。
- 発行 tool 側に独自判定を置くと、同じ入力を拒否する層が 2 つになり、変異の単一理由性が失われる。

**却下した選択肢:**
- env→generation の数値 mapping を受ける純述語 — contract の rollback を素通しする。
- 世代 entry の mapping を loader へ直接渡す — schema leaf から環境契約 module への逆 import が生じ、
  stdlib-only を構造的に強制している既存検査を壊す。
- 検証済み registry snapshot から catalog と adapter closure を同時生成する — 片方の分裂を
  別の分裂に置き換えるだけで、registry を差し替える試験経路から adapter が見えなくなる。
- 許可 edge の data catalog を別に渡す — loader には再び投影結果しか残らず、二重 catalog の
  不整合面が増える。
