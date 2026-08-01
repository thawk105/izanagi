# AI provenance — 一回限りの forward correction

入口の `correction` または `history` 条件が成立したときだけ読む (`history` からは `PR-C03`)。

## PR-C01 — 固定 target と一回性

共有済み `6b64d21753d2cfc790f80caba29df7a40fef3072` はrewriteせず、strict descendant 1件で補記する。

```text
AI-Agent-Correction: target=6b64d21753d2cfc790f80caba29df7a40fef3072; product=claude; model=claude-opus-5; reasoning=xhigh; role=integrator
```

一般allowlist・設定・CLI免除へ拡張しない。この枠は `6d7141dc8a174384f3b9be689d3516a8a3a31bbf` で
消費済みであり、新しい担い手を追加してはならない。

## PR-C02 — 担い手の成立条件

自身の `AI-Agent` と上記物理1行は同じ最終blockに置く。checkerはraw/canonical/final-block exact、
selected set内の両commit、strict lineage、target実欠落、candidate 1件、自身の通常greenを連言する。
有効な `AI-Agent-Waiver` を持つ commit は担い手になれない。相殺するのはtargetの欠落findingだけで、
他のfindingは保存する。

## PR-C03 — 権威ある監査範囲

両commitを含むrangeか既定full-historyだけを権威とする。target抜き`OLD_HEAD..HEAD`は補助で、初回伝播も
免除しない。green時は両SHAを`forward-corrected=1`で示す。
