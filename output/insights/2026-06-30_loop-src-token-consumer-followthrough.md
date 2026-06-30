# loop の src_token 追従 ([HIGH]) + consumer 完遂 + 敵対検証結果

- **日付:** 2026-06-30
- **発端:** `docs/audit-2026-06-30.md` (別セッションの全体監査) の **[HIGH]** — D23 で identity を「コードの差」
  (src_token) まで覆ったのに、消費側の `loop.run_campaign` が追従せず skip/abort キーが stock id のまま。
- **方法:** 独立裏取り → 修正 → 3 レンズ敵対検証 (TOCTOU偽hit / リカバリ正しさ / 後方互換、13 エージェント /
  約 64 万トークン) → confirmed 8 / refuted 2 を反映。
- **位置づけ:** Phase 3 タスク3 着手前の割り込み対応 (audit の [HIGH] をユーザー指示で優先)。decisions D25。

---

## 裏取りした [HIGH] (実コードで確認)
- `loop.py` (HEAD): skip 判定 `v = variant_id(g)` と例外 abort が **常に stock id**。
- `pipeline.py:evaluate`: `v = variant_id(genome, src_tok)` で **src_token id** で WAL を書く。
- `done = set(terminal)` の terminal は WAL 由来 = src_token id。
→ coder variant (src_token != "stock") で skip キー (stock id) と WAL/terminal (src_token id) が乖離し、
(D) 評価済み coder variant の再評価 = リカバリ冪等性破綻、(A) 例外 abort が別 id に付き孤児化。Phase 2 は
全 genome stock 正規化ゆえ潜伏。

## 修正
- `source_digest.resolve(genome, ccbench_commit)` = allowlist 検査 + src_token の単一窓口 (WAL は書かない、
  fails-closed)。loop と evaluate が同じ計算を共有し id 確定点を二重化しない。
- `pipeline.evaluate(src_token=None)` 引数: None なら自己計算 (直接 caller 用、fails-closed)、loop は確定済みを渡す。
- `loop.run_campaign`: `resolve` → `variant_id(g, src_tok)` で skip/dedup → evaluate に渡す。例外 abort も
  src_token id、identity-error は stock id で隔離。
- 回帰テスト3本 + pipeline self-compute テスト。後方互換 (silo 8 golden、stock src_token='stock'→旧 id) 不変。

---

## 敵対検証 confirmed (8)

### [medium] backoff_repro._bench_tps が stale consumer (同時修正済)
`backoff_repro.py:_bench_tps` が `variant_id(genome)` = stock id で WAL を引くが、その genome は
`BACKOFF_FIXED=10/5` (非 stock src_token)。template patch 適用済み working-tree で run_campaign が src_token id
で WAL を書くため lookup が None → **P2 backoff の cross-run 再現 ([P0] の +38%/+11%) が silently「判定不能」**。
loop と同じバグクラス (D23 で取り残された consumer) → 同時修正: `run_campaign` が返す `EvalResult.variant`
(src_token まで確定済み) から引くようにし、consumer 側で identity を再計算しない (確定点の単一化, D24 と同型)。

### [medium] identity-error poison stock id (既存問題として繰延)
`source_digest.resolve` が transient 失敗 (g++ 一時不在 / git 一時失敗) すると loop は stock id
(`v0=variant_id(g)`) で terminal abort → 環境修復後も `variant_id(g, "stock")==v0` ゆえ **stock genome が
永久 skip**。検証は「fix が ACID-D を再導入」と裁定したが、**HEAD でも同一挙動** (修正前は evaluate が stock id
で identity-error abort、loop が stock id で skip 判定 → 修復後も永久 skip) を `git show HEAD` で確認。私の修正は
この挙動を変えていない (検証の「newly creates」は誤帰属)。**既存の terminal-abort 設計限界** = transient infra
失敗を genome-intrinsic 失敗 (verifier-red/build-error) と同じ permanent skip に誤分類している。fails-closed
(false-green ではない、規律2 不変、害は genome の silent drop)。**対処 = identity-error abort を retryable に
マークし recovery で再評価**は別タスクに繰延 (terminal-abort の overnight 耐性とのトレードオフ設計が要る)。

### [low] dedup テストが skip-key スキームを区別しない (docstring 正直化済)
`test_loop_dedup_uses_src_token_id` は同一 genome 2 本ゆえ stock id でも src_token id でも単一キーに潰れ、
skip キーのスキームを区別しない (buggy stock-id loop でも pass)。docstring を正直化し、skip キーが src_token id
であることの load-bearing 検査は `test_loop_recovery_skips_committed_src_token_variant` (WAL の src_token id
terminal で skip = 旧 stock-id 判定なら fail、検証で確認) が担うと明記。

### nit 群
- pipeline.evaluate の self-compute identity-error 枝が未テスト → テスト追加済。
- loop と evaluate に identity-error 処理が二重 (DRY) → production では排他 (loop が src_token を渡すので evaluate
  の自己計算枝は通らない)、correctness 欠陥なし。将来発散リスクのみ。
- loop.resolve → build 間の TOCTOU 窓 → D23 から同じ性質・単一テナント直列で非現実的、worktree 隔離 (phase3.md
  繰延) で塞がる。

## refuted (2)
- allowlist 検査が loop 経路で 3 回 (resolve 1 + build trace/perf 2) → 冪等・安全側で not-a-bug。
- silo 8 後方互換が実 loop 経路 (resolve→variant_id) でも golden 不変 → positive 確認 (not-a-bug)。
