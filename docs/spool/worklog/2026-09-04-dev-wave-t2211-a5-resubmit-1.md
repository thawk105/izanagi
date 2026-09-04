---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2211-a5-resubmit
seq: 1
title: [T-2211] A-5 (D1100) の再投入 — T-2226 着地後も 2 job とも同じ関門 preprocess-failed で止まり、理由の本体を masstree config.h 不在 (第 2 層) と実測で確定した (insight + docs のみ、branch worktree-dev-wave-t2211-a5-resubmit、実装面の差分 0)
---

## 本文

- **同じ投入器を local main `1b7822110` からもう 1 回走らせ、2 job (977066 write-heavy / bnode026、
  977067 balanced / bnode027) とも 09-02 と同一の条件関門 `BACKOFF_FIXED=red/preprocess-failed` ×7 で
  止まった。** 測定値は 1 つも取れていない (`campaign_wals=[]`)。Elapse は 137 / 138 秒。
  一次資料は `output/insights/2026-09-04_t2211-a5-second-boot-resubmit/README.md`。
- **理由の本体を login node での再現で確定した。** `backoff_sweep.py` の拒否文は `evidence.detail` を
  捨てるので、同じ形の supply arm を 1 request 分だけ再現し、detail = `masstree_wrapper.hh:20: fatal
  error: config.h` を得た。A-2 の解剖 (2026-09-02) が第 2 層と呼んだ赤と同一で、masstree の `config.h`
  は build 時 custom command で生成されるため configure しかしない関門の木には無い。
- **段 1 の実測が引数の前提を 1 つ覆した。** 「[T-2226] 着地で原因側が直った」は関門 3 層のうち
  第 3 層 (inert 比較) にしか当たらない。第 2 層を A-2 経路で直した修正
  (`buildcache.prepare_masstree_fetchcontent` + `-DFETCHCONTENT_BASE_DIR`) は
  `paper_story_a2_certification.py` にだけ入っており、`backoff_sweep.py` の関門呼び出しは
  configure_args なしのままである。段 4 で (P1) real と裁定し、それでも投入した — 依頼が失敗枝を
  明示していて費用が 2 job × 約 2 分であり、「予測」を backoff_sweep 経路の「実測」へ変える価値が
  あるため。[T-2226] は必要条件であって十分条件ではなかった。
- **実装には手を入れていない。** 投入と記録だけの依頼で、関門を通すための修正は規律 2 の対象であり
  Codex 実装子と敵対レビューを要する。変異 matrix は実装面ゼロのため免除。
- **A-5 は未充足のまま** (D1525)。今回は値が無いが、値が取れても充足と書かない前提を insight に明記した。
- 副産物 (scope 外、記録のみ): 受領証の `job_id` field に qsub 出力全文が入る (09-02 も同じ)。
  balanced job の後片付けで superproject 側 `git worktree remove` が rc=128 (09-02 の主 checkout 投入でも同じ)、
  prune は rc=0 で login node に `/scr/` の残骸は無い。
- 軽量版、子ゼロ。段 2/3/5/6 の子は実装面ゼロのため省略。dev-wave 改善候補はゼロ。

## 次の一手差分

### 更新

- [T-2211] **P1・順序待ち (再)**: A-5 の別 boot 再取得は、[T-2226] 着地後の再投入 (2026-09-04、
  2 job) でも同じ関門 `preprocess-failed` で止まった。理由は第 2 層 (masstree `config.h` 不在) が
  `backoff_sweep` 経路に残っているためで、{{T:backoff-sweep-gate-masstree-config}} の着地を待つ。
  着地後に同じ投入器をもう 1 回走らせる。そこで初めて第 3 層 (D1611) が backoff_sweep 経路で
  実測される。充足の判定は D1525 に従い「未充足のまま残す」。
  base: 37e008a9785851de9e370772c5722774b7fd5fc7a8451cf5498c2f7de8aeaf04

### 新規

- {{T:backoff-sweep-gate-masstree-config}} **P1・新規**: `backoff_sweep.py` の
  `_require_backoff_condition_gate` へ第 2 層の修正を入れる (Codex 実装子)。A-2 経路と同じ形
  (関門文脈で `buildcache.prepare_masstree_fetchcontent` を 1 度呼び、`-DFETCHCONTENT_BASE_DIR` を
  `capture_define_inputs` の configure_args で渡す) が最短。不変条件は A-2 の教訓「検査した木と
  build する木を一致させる」。関門を通すためだけの修正で偽の緑を作らない (規律 2)。
  一次資料: `output/insights/2026-09-04_t2211-a5-second-boot-resubmit/README.md`、
  `output/insights/2026-09-02_a2-condition-gate-patched-root/README.md`。
