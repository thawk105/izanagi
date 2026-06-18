# Isolation phenomena (G0/G1/G2) — verifier が見るもの

verifier (`orchestrator/verifier/`) が判定する serializability 異常の分類。出典は
**Adya の一般化 isolation level 定義** (Adya-Liskov-O'Neil, "Generalized Isolation
Level Definitions", ICDE 2000 / Adya PhD thesis 1999)。roadmap §3.1 が「Serializable
狙いなら G2 まで見る」と書いている、その G2 の正体がこれ。

## 依存グラフ DSG の辺 (3種)

committed trx を節点、同一キーへの競合アクセスを辺とする有向グラフ (Direct
Serialization Graph)。辺はすべて「a が直列順序で b より前」を意味する (a → b):

| 辺 | 名前 | 条件 |
|---|---|---|
| **ww** | write-depends | a が版 V を書き、b が同キーの**次版**を書いた |
| **wr** | read-depends | a が版 V を書き、b がその V を**読んだ** |
| **rw** | anti-depends | a が版 V を**読み**、b が同キーで V の**直後版を書いた** (読み手→上書き手) |

**DSG が非巡回 ⇔ serializable。** cycle が 1 本でもあれば non-serializable。

## phenomena (どんな辺の cycle か)

| 現象 | 中身 | 防ぐ isolation level |
|---|---|---|
| **G0** | **ww だけ**で閉じた cycle (dirty write) | PL-1 ≈ Read Uncommitted 以上 |
| **G1a** | abort する trx の値を読む (dirty read) | PL-2 ≈ Read Committed 以上 |
| **G1b** | 中間 (非最終) 値を読む (intermediate read) | 同上 |
| **G1c** | **ww+wr** から成り **rw を含まない** cycle (circular info flow) | 同上 |
| **G2-item** | **rw を 1 本以上含む** cycle (単一アイテムの anti-dependency) | PL-2.99 ≈ Repeatable Read 以上 |
| **G2** | 述語 (phantom) 込みの rw cycle | **PL-3 = Serializable のみ** |

要点:
- **番号が大きいほど検出が難しく、より強い isolation でしか防げない。**
- **Serializable = G1 も G2 も全部禁止。** だから serializability 判定は G2 まで見る。
- **Snapshot Isolation は G0/G1 を防ぐが G2 を許す** (= write-skew)。これが
  タスク3 で `si` を verifier の positive control にする根拠 (`si` は本物の G2 を出す。
  `ccbench-anatomy.md` §2)。

## 本プロジェクトでの実態 — 実質 G2 のみ

CCBench Silo の trace は **(1) committed trx だけ**を記録し、**(2) 版ID = commit
(epoch,tid) の単一スタンプ**を使う。この2つから:

- **G1a / G1b は観測不能** — abort trx も中間版もトレースに出ない。
- **G0 / G1c は realizable trace では構造的に出現しない** — ww は版順=commit 順、
  wr も「書かれた後に読む」ので、どちらも commit 順を**前向き**にしか進めない。
  commit 順を**逆走**できるのは rw だけ。cycle は始点へ戻る以上、逆走辺 (=rw) を
  最低 1 本含む ⇒ **必ず G2**。
- したがって verifier が realizable trace で出す赤は**全部 G2**。

(verifier の `_classify` は G0/G1c 枝も持つが、それは**非 realizable な手製/破損
trace** でのみ到達する。verdict は cycle の有無だけで決まり分類に依存しないので無害。
証明スケッチは `orchestrator/verifier/dsg.py` の `_classify` docstring。)

## スコープ外: phantom / 述語異常

トレース形式は **key 粒度**で、存在する版の read しか記録しない。範囲スキャンが
「キーが無いこと」を観測する述語読み (phantom の素) は R イベントを生まないため、
**phantom write-skew (G2-item でなく述語 G2) は verifier に見えない**。これは
trace-hook の限界であって dsg.py のバグではない。詳細と対策は
`output/insights/2026-06-18_phantom-predicate-out-of-scope.md`。
