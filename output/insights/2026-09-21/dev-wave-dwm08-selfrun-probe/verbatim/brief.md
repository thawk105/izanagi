## 段 1 brief (2026-09-21 07:50 JST)

1. **新事実 (承認前提を覆す):** 依頼の中核は着地済み。entry 1774 (archive `docs/archive/worklog-phase3-0921-1774.md`)・D2195 (2026-09-21)、
   commit 993d2fc5f / 6d600f0a6 / 618fb8501 (docs のみ)・記録 33de1a3ea、fold 済み (FOLDED.md 5133–5134、tested_tip 4566c64b4)。
   この job の依頼文は着地前に起票された写しと判断 (依頼の実測値 fig13 = D2195 理由と同一)。
2. **研究前進:** 土台 (dev-wave 所要)。所要分解 (entry 1774) で変異 probe+final は impl wave wall の 19〜24%、self-run で probe 20.7 分 → 2 分。
   本 wave の最小差分 = self-run 適用外の条件に「skip」を名指しし、skip 持ち file を self-run へ投入して final MISMATCH (1 final 分の空振り) を招く経路を閉じる。
3. **既存被覆 (純増ゼロ、収容しない):** 注入→自走→復元 sha256 照合→dispatch final (DW-M08 第 3 文 + DW-O19)、`--collect-only` 同形式照合 (DW-M08 第 4 文)、
   git status clean (DW-O19 の `--porcelain` 空確認 + 復元 bytes の commit 照合)、node 抽出規約 (F71 参照)、実測値 (D2195 理由)、
   parametrize・fixture・環境変数・import 副作用・対応不明の fallback (DW-M08 第 4 文)、完全一致 / KILLED 判定 (不変)。
4. **純増 (P1、親の provisional 裁定・攻撃対象):** DW-M08 第 4 文の列挙に `skip` を足す (+7 bytes、L1.5 残 15 内、削減不要、上限不変)。
   根拠: skip は `--collect-only` の一致で検出できない乖離型 — `test_check_docs.py::_run` は `except Exception` で `Skipped` (BaseException) を捕まえず、
   `skipif` 付き test は mark を無視して実行される。
5. **収容しない (P2):** 抽出 regex `\S+?::[A-Za-z0-9_]+` と `orchestrator/tests/` 前置。harness ごとに FAIL 行の形が違う (`test_check_docs.py` は
   file 前置なし `FAIL <fn>[label]`) ので leaf に固定せず「正規化 → `--collect-only` と同形式」で足りる。誤りは final の MISMATCH で fail-closed。
6. **pin 追随:** 不要。`check_docs.py` / `test_check_docs.py` は mutation.md を節 ID 在庫と層予算でしか束縛せず、本文 literal pin なし (3_750 等は合成 fixture 用)。
   → 実装面差分ゼロ、Codex author なし (D95 docs-only 例外)、変異 matrix 免除 (DW-S04)、受入全走は免除しない。
7. **不変条件:** 完全一致要件 (DW-M08 / F33)・KILLED 判定・規律 2 を変えない。gate・台帳・一般化を足さない。予算上限を動かさない。
8. **成果物:** DW-M08 の 1 語追加 (docs commit 1)、insight (依頼逐語・brief・レビュー逐語・被覆表)、worklog fragment。decisions は D2195 の適用条件の
   明確化に留まり新 D は起票しない (段 6 レビューで反証があれば再裁定)。
9. **分割方針:** 軽量版。段 2・3 省略 (設計択一なし・受理集合を広げない)。段 6 は一次資料の再抽出を含むので独立 read-only レビュー 1 本 (codex) を残す。
10. **条件表:** O08/O09/O10 不成立 (凍結・oracle・proof chain 非接触)、O13 不成立 (gate 新設なし)、O11 不成立、O19 不成立 (一時変異なし)。
