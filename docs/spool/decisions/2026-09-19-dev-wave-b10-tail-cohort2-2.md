---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-19
wave: dev-wave-b10-tail-cohort2
seq: 2
---

## {{D:b10-tail-cohort2-independent-reproduction}}. B-10 静的右 tail の第 2 cohort は独立再現とし、cohort 1 の verdict を主として保持して再現欄に併記し、合成しない

**決定 (ユーザー裁定、2026-09-19):** 事前登録 `docs/b10-backoff-static-tail-preregistration.md` に対する第 2 cohort を
走らせる。地位は次のとおりで、**結果を見る前に**事前登録の末尾追記 (日付付き append-only、commit `cad6f46d8` の bytes は
不変、§5 spec の bytes も不変) として commit してから投入する。

- 第 2 cohort は cohort 1 (group `b10-backoff-grid-20260915T061814Z-545445`、verdict `not-observed-in-any-workload`) の
  **独立再現**であり、置換ではない。
- cohort 1 の verdict を主として保持する。第 2 cohort の verdict は、第 2 cohort の稿と fig8 の再現欄に併記する。
  cohort 1 の既存の稿・図は凍結物のまま改めない。
- 2 つの cohort を合成しない (統合 verdict・プール推定・またぐ有意水準の保証を作らない)。
- 結果にかかわらず 1 本を報告する。未完走・報告生成失敗も §7 に従い開示する。第 3 cohort の実施・地位は定めない。
- 格子・反復・判定は既存の事前登録どおり。機構は `tools/pegasus/b10_backoff_grid.sh` の `B10_RUN_KIND=t2500-tail-formal`、
  3 workload を 3 job に割って別ノードで走らせる。`performance_certified: false` を維持し、正しさは trace 有効の別走行。
- scope 外: 901〜998 マイクロ秒の帯 (D2044 項 14)、v2 consumer 移行 (D1936 項 36)、追加 gate。

これは D2050 (2 本目は地位を結果より前に明記してから投入) の充足であり、D2104 項 7 / D2120 項 16 が
「走らせる場合は D2050 を満たす別 wave として新規に起票する」と留保した保留を、**この 1 cohort についてだけ**解く。

**理由:**
- 独立な再現走行は科学的に望ましい (D2050 の却下案の理由)。事前登録は 2 本目を禁じていない。
- 地位を先に固定すれば、結果後に「どちらの verdict を採るか」を選ぶ余地が消える (絶対規律 3)。
- fig8 (cohort 1 の記述図) が成立し、結果を使う下流が存在する (D2120 項 16 が挙げた理由の一部の変化)。

**却下した選択肢:**
- 第 2 cohort で cohort 1 を置換する — 結果後の選択を残すため採らない。
- 2 つの cohort を合成して 1 つの verdict にする — 事前登録に合成規則が無く、新しい統計的主張になるため採らない。
- §0 本文へ変更理由の 1 項目を挿入する — ユーザー指定の「末尾 append-only」と一致しないため、§0 が求める記載は
  追記の冒頭に置く (段 3 相当の consult の real 所見を採用)。
