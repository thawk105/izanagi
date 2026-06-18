# 発見: phantom / 述語異常はトレース形式の構造上 verifier に見えない

- **発見日:** 2026-06-18 (Phase 1 タスク2 の敵対的検証 workflow `verify-the-verifier`)
- **種別:** Izanagi 側の **trace-hook の設計限界** (CCBench のバグではない)
- **重大度:** 中 (現 Phase のワークロード=YCSB では無害。将来 range/predicate を含む
  ワークロードを扱うときに効く)

## 何が見えないか

verifier (`orchestrator/verifier/`) は key 粒度の Direct Serialization Graph で
serializability を判定する。トレース形式 (`patches/README.md`) は **存在する版の
read しか記録しない** — 範囲スキャンが「この範囲にキーが無い」ことを観測する
**述語読み (predicate read)** は、読む版が無いので R イベントを一切生まない。

その結果、典型的な **phantom write-skew** が verifier には serializable に見える:

```
T1: 「範囲 A は空か?」→ yes (R イベント0個) → 範囲 B にキー a1 を INSERT
T2: 「範囲 B は空か?」→ yes (R イベント0個) → 範囲 A にキー b2 を INSERT
```

述語意味論では両者が互いの前提を覆す非直列 (述語 anti-dependency の cycle)。だが
key 粒度では共有キーゼロ・read イベントゼロ → DSG の辺が 0 本 → 自明に非巡回 →
verifier は **serializable** と答える (`output/runs/adversarial/insert-delete/phantom-skew`
で実測。committed fixture は `orchestrator/tests/fixtures/p1_phantom_skew`)。

## なぜ「バグではない」か

verifier の入力契約は「key×版の read/write 競合」。述語の被覆範囲がトレースに無い
以上、見えないのは dsg.py の論理欠陥ではなく**入力 (trace-hook) が落としている情報**。
レッドチームの独立検証でも「key 粒度では verifier は正しく serializable」と一致。

INSERT/DELETE 自体は正しく扱える (op フィールドは記録のみで graph では不使用、
tombstone も通常の版として ww/wr/rw に乗る — `delete-rw-cycle`/`tombstone-read` で実証)。
見えないのは **述語 (範囲) の被覆だけ**。

## 対策 (将来、述語ワークロードを扱うとき)

trace-hook に**述語読みの被覆範囲 (gap/next-key/range)** を吐く口を足す必要がある:
- 範囲スキャンが観測した範囲境界 (lo, hi) または next-key を R とは別の `P` レコードで記録
- verifier 側に predicate anti-dependency (述語 rw) の検出を足す
- これは MySQL/PostgreSQL の gap-lock / next-key-lock 相当の情報

現 Phase は YCSB (点アクセスのみ・範囲なし) なので**実装しない** (絶対規律5: 段階導入)。
本ノートは「green verdict を range-heavy ワークロードで過信しない」ための記録。

## 還元判断

**不要。** これは Izanagi のトレース形式の限界であり CCBench への還元対象ではない。
将来 Izanagi 側で述語対応する際の設計メモとして残す。
