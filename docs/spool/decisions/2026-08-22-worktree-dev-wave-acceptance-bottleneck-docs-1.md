---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: worktree-dev-wave-acceptance-bottleneck-docs
seq: 1
---

## {{D:dw-o12-sequencing-note-placement}}. 受入投入と記録commitの順序注記はDW-S07/DW-C00でなくDW-O12へ置く

**決定:** T-1451 (「land対象tipへの最終受入投入は段7記録commit完了後に行う」旨の注記) を、
提案元が候補地として挙げていた `docs/dev-wave/core.md` の `DW-S07`/`DW-C00` (いずれもL1、
wave開始時・段7で無条件に読む) ではなく、`docs/dev-wave/operations.md` の `DW-O12`
(「裁定手順と実行手順の差」、L2、段4裁定手順と実行手順が食い違った時点にだけ読む) へ置く。
同時に着地させた T-1468 (checker自身のPegasus infra失敗の扱い) は提案どおり `DW-O18`
(L2) へ置く。

**理由:**
- `docs/dev-wave/**` のL1 unique footprint予算は10,625 bytesで固定 (`tools/check_docs.py`
  の `DEV_WAVE_L1_BYTES_MAX`)。本wave着手時点で実測すると、T-1451 の注記文を `DW-S07`
  または `DW-C00` (いずれもL1) へ追記しただけで合計11,038 bytesとなり budget を413 bytes
  超過した。既存L1文の圧縮だけでこの幅を埋めるのは、複数節にまたがる大規模な書き直しを
  要し規律5 (段階導入・盛らない) に反するため見送った。
- `DW-O12` は「裁定手順(想定)と実行手順(実際)が食い違った時点」という発火条件そのものが
  T-1451 の症状 (`DW-S06-C` の文面が段6内の受入投入を示唆する一方、実際land対象となる
  受入は段7の記録commit後でなければならない、という想定と実際の食い違い) と一致する。
  追記前実測611 bytes空きがあり、圧縮なしで収まった (追記後 `python3 tools/check_docs.py`
  が違反なしを返した)。
- `DW-O18` (「親のテストcwd」、L2、追記前995/1000 bytes) は T-1468 の症状 (checker自身の
  rc非0の扱い) と直接同じ話題領域であり、提案どおりの設置が最も自然だった。既存文を圧縮
  (F41 引用文を `DW-S07` 案から `DW-O12` 側へ retarget、細部の言い回し圧縮) して
  997/1000 bytesに収めた。

**却下した選択肢:**
- `DW-S07`/`DW-C00` への直接追記 (提案時の候補地のまま) — L1総予算超過で `check_docs.py`
  が違反を返す。既存L1文の広範な圧縮とセットでなければ成立せず、本wave (対象2件の着地) の
  scopeを超える。
- `DEV_WAVE_L1_BYTES_MAX`/`DEV_WAVE_L2_SECTION_BYTES_MAX` 等の予算定数自体を引き上げる —
  D271近辺で予算の運用契約 (L2節の新設・削除は裁定を要する) が既に定められており、定数の
  見直しはそれ自体が独立の設計判断でありユーザー裁定を要する。本waveのscope外として着手
  しなかった。3層とも逼迫している実態はworklog fragment (exploratory-run-worktree-isolation
  候補が未着地のまま残る記録) に残し、次に予算へ触れるwaveへ引き継ぐ。
