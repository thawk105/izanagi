---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-10
wave: dev-wave-t2533-t1998-prereg-digest
seq: 1
---

## {{D:t1998-prereg-binds-consumer}}. 事前登録は文書を置くだけでなく consumer の受理条件へ束縛する

**決定:** T-1998 の事前登録は、canonical 文書を置いて呼び手に渡すだけの形にしない。
consumer は既存の成果物比較をすべて通した後、`ratio` 計算の直前に次の 3 つを要求する。

1. 作業木の事前登録文書 bytes の sha256 が `CURRENT_PREREGISTRATION_SHA256` と一致する。
2. 成果物が記録する `repository_commit` における文書 blob の sha256 が
   `MEASUREMENT_TIME_PREREGISTRATION_SHA256` と一致する。
3. その measurement blob から導いた identity が、渡された identity と
   `repository_commit` を除いて完全一致する。

**理由:**

- 文書を置くだけでは、呼び手が結果を見た後に成果物から identity を写して手組みでき、
  canonical 文書を 1 度も読まずに受理へ到達できる。段 3 の 2 レンズが独立にこの経路を突いた。
- 呼び手が渡す `repository_commit` を成果物と突き合わせるだけの検査は恒真である。
  measurement blob の sha を要求すると、受理される commit が「その版の文書を含む commit」に
  限られ、事前登録の着地前も改訂後も受理されなくなる。
- 3 gate を既存比較の**後**に置くのは、先行させると既存負例の拒否 code と field が動くためである。
  受理集合は狭まる方向にしか変わらない (絶対規律 2)。

**却下した選択肢:**

- 文書だけを置き、loader を任意呼び出しにする — 上記の手組み経路が残る。
- 3 gate を既存比較より前に置く — 既存負例の拒否 provenance が動く。
- producer schema を拡張して成果物へ事前登録 sha を書く — 束縛は強くなるが D1244 の最小 3 部品の外。

## {{D:t1998-two-pins-equal-in-v1}}. D1790 の 2 定数は初版で同値でよく、不等性を要求しない

**決定:** D1790 が要求する「測定時点の版」と「現行の解析規則の版」の 2 定数は、独立した
scalar として別々に置く。**初版では両者が同じ値になるのが正しい状態であり、
「値が異なること」を要求する検査を置かない。**

**理由:**

- D1790 が禁じるのは、2 つを 1 つの定数へ統合すること、複数版を受理する allowlist を作ること、
  任意値を受理する形へ緩めることである。初版で値が一致することは禁じていない。
- 不等性を要求すると、規則を改訂していない正当な初版 cohort を理由なく拒否する。
- 帰結として、2 定数を同一定数へ統合する変異はテストでは殺せない。これは等価変異であり、
  変異台帳へ SURVIVED として登録して限界を明記する。静的な統合検出を足すことはしない。

**却下した選択肢:**

- 2 定数の値が異なることをテストで要求する — 正当な初版を拒否する。
- 統合を静的に検出する gate を足す — 依頼の外にある要求外の検査である。

## {{D:prereg-source-digest-under-patch}}. 事前登録の arm 別 source digest は patch 適用下で導く

**決定:** T-1998 の事前登録が固定する arm 別 `source_bytes_sha256` は、
`patches/silo-backoff-fixed.patch` を作業木へ適用した状態で `resolve_evidence` を呼んで導く。
patch 未適用の作業木で計算した値は使わない。

**理由:**

- 正式 producer は campaign 全体を `patchharness.applied(...)` の内側で走らせ、build 証拠は
  その状態から解決される。事前登録が固定すべきは producer が実際に記録する値である。
- `BACKOFF_FIXED` が負の arm では patch が inert なので値は変わらないが、静的 backoff を選ぶ arm
  では前処理後のソースが変わり digest も変わる。**片方だけ一致するので、
  baseline の一致を根拠に target も正しいと推定してはならない。**
- 誤った値のまま正式測定を打つと `source-identity-unbound` で全件拒否され、
  適格な成果物が 1 本も得られない。

**却下した選択肢:**

- patch 未適用の作業木で計算した値を使う — producer が記録する値と食い違う。
- 過去の測定成果物から digest を写す — 事前登録の前向き性を損なう疑いを残す。
