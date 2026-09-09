---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2419-meaning-decl
seq: 1
---

## {{D:backoff-meaning-intent-from-driver}}. 非負 BACKOFF_FIXED の意味宣言は driver が渡し、判定器は符号を変換しない

**決定:** `orchestrator/campaign/backoff_sweep.py` の `_require_backoff_condition_gate` は、
必須 keyword `backoff_fixed_physical_us: Mapping[int, int]` を取る。生値から、その driver が
意図した物理 µs への写像である。判定器は宣言 bits を `float(physical)` から作り、
**符号の変換 (codec) を一切呼ばない。** 写像の key 集合は要求された非負 `BACKOFF_FIXED` の
集合と完全一致しなければならず、欠け・余りは source capture の前に拒否する。

`BACKOFF_FIXED = -1` の stock branch witness と、他 macro の扱いは変えない。
生値の範囲による一律拒否 (wire domain 制約) は設けない。宣言と観測が食い違えば red になるので、
新しい拒否面を作る必要がない。

**理由:**

- 生値から codec で期待値を逆算する設計は、driver が何を要求したかを証明しない。
  literal-µs driver の格子へ「物理 3000 µs のつもりで 3000」を足すと、宣言も観測も 1000.0 に
  なって素通りする。F718 と同型の事故がそのまま通る。段 3 の 2 レンズが独立に同じ結論へ収束した。
- driver が物理 µs を渡すと、期待値は Python 側の driver intent、観測値は捕捉した合成枝を
  独立 TU へ埋めて実 C++ compiler で評価した値になり、経路が分かれる。恒真ゲートにならない。
- 変異 M2 (宣言 bits を物理でなく生値から作る) が、生値と物理が一致する点では死なず
  符号化点だけで死ぬことを実測した。テストがこの区別を実際に持っていることの証拠である。
- 判定器から codec を外すと、codec を module 間で移す必要が消え、循環 import の論点も消える。
  実装面が当初案より小さくなった。

**却下した選択肢:**

- 生値を静的 codec で逆算して宣言する — 上記のとおり driver intent を証明しない。
- 生値 1000〜2999 (合成枝の乱択モード帯) と上限外を wire domain 外として一律拒否する —
  新しい拒否面を作るわりに、宣言と観測の照合で足りる。将来 乱択モードを使う driver を
  塞ぐ副作用もある。
- 意味の節を `unestablished` のまま残す — F718 型が production 経路で捕まらない。
