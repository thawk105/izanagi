---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t758-docs-corrections
seq: 1
title: [T-758] 既存 docs の誤り 3 件を現物で裏取りして訂正した (docs のみ、branch worktree-dev-wave-t758-docs-corrections)
---

## 本文

- 3 件とも 2026-08-10 の指摘に頼らず、`external/ccbench` の現物と `orchestrator/campaign/genome.py`
  から独立に数え直してから直した。逐語と根拠は
  `output/insights/2026-09-14/t758-docs-corrections.md`。
- **carry の字面は一次資料と 1 か所ずれていた。** carry と一次資料 V3 は「mocc の自由軸は 2 つ」だが、
  V3 の 2 つは protocol 固有 option だけの数で、全 protocol 共通の `BACK_OFF` を含めていない。
  同じ insight の s2-plan と `MOCC_SPACE` の実装はどちらも 3 軸である。anatomy の探索空間の列は
  他 protocol でも `BACK_OFF` を数えている (ermia 4 = `KEY_SORT` × `BACK_OFF`) ため、
  doc へ書いた数は 2^3=8 とした。carry の数字をそのまま写していたら誤りを別の誤りに置き換えていた。
- **自分の探索でも一度同じ型の誤りを踏んだ。** `grep ... | head -20` で ccbench を数えて
  `KEY_SORT` の live site を取り逃し、死にフラグと誤判定した。切らずに数え直して是正した。
- 子エージェントは起動していない (docs のみ・実装面の差分ゼロ)。DW-S04 により変異 matrix は免除、
  受入全走は実施した。
- 設計択一は生じなかったため decisions への追記はない。

## 次の一手差分

### 完了

- [T-758] 3 件を現物で裏取りして訂正した。ermia は active な `ssn_parallel_commit()` が raw cstamp を
  書くので si の写像がそのまま流用でき、`cstamp<<1` は呼ばれない `ssn_commit()` と sstamp 側だけである。
  mocc の探索空間は 2^3=8 (`RWLOCK` は bare define で軸に数えない)。trace-hook は silo と si の
  2 protocol に既存で、si は 2026-06-19 追加である。
  remaining: none
  base: 8c6fb83ae0fc52fc6b76f3934056b98e4ee3793860698ec5b5686055a22cf39f

### 新規

- {{T:anatomy-search-space-tictoc-cicada}} **P2・新規**: anatomy の探索空間サイズのうち tictoc
  (doc 2^4=16 / `TICTOC_SPACE` は 5 軸) と cicada (doc 2^6=64 / `CICADA_SPACE` は 5 軸) の項を
  現物で数え直して訂正する。あわせて `orchestrator/campaign/genome.py` の module docstring が
  引く旧合計 (≈ 258 binaries) を直す — こちらは実装面なので Codex author が要る。
  T-758 は 3 件を名指しした課題だったため本 wave では触らず、doc 側へ未検証と明記して送った。
