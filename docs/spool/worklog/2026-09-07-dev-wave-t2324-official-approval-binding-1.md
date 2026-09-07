---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2324-official-approval-binding
seq: 1
title: [T-2324] 床値 official の §8 承認束縛を D926 の submission nonce 束縛で実装し、投入手順を固定 official へ入れ替えた (コード + テスト + docs、branch worktree-dev-wave-t2324-official-approval-binding、変異 11/11 KILLED)
---

## 本文

- **方式は既裁定なので再裁定していない。** D926 (D461 型の submission nonce 束縛、official 専用の
  別系統) が方式を確定しており、D1396 が実装を見送った前提 (staged transport で発火経路が書けない) は
  D1562 / D1628 の着地で消えていた。本 wave は実装だけを行った。
  **実装の着地は測定認可 (D1641) を兼ねない** — 実投入はしていない。
- **段 3 の敵対 2 レンズが親 brief の記述を 5 件反証した。** (1) 不変条件「副作用より前」は誤りで、
  診断 env の取り込みが承認 gate より前にある。(2) 成果物影響の書き方 (起動と API の受理集合は
  変わるが、実投入していないので測定値と選択結果は変わらない)。(3) DW-G04 の witness に
  予算承認文書を数えていた (投入器・job・driver のどこからも読まれない)。(4) 変更面表の件数と位置。
  (5) 床値の走行間ばらつきの producer 同定の根拠が結論より弱かった。すべて段 4 で訂正した。
- **親が段 3 の合意を 1 件反証した。** 段 2 plan が承認 gate の前倒しを提案し、段 3 の 2 レンズが
  どちらも妥当と認めたが、**3 者とも親 brief の誤った不変条件を基準に判定していた。** 前倒しは
  無条件の観測者効果隔離テストを条件付きへ割る対価を要求し、得られるものが無い。gate は動かさず、
  不変条件の書き方を直した ({{D:floor-official-approval-gate-keeps-its-position}})。
- **段 3 の 2 レンズが逆向きの主張を出したので層で分けた。** 未承認投入の扱いについて alpha は
  「強めろ」、beta は「brief を弱めろ」だった。投入器で実投入を必須化し、job script は D926 の形を
  literal に保つ形で両立させた ({{D:floor-official-submitter-requires-approval-argument}})。
- **段 5 の実装子は model call 上限 (100) で SIGTERM され、報告を 1 行も書かなかった。**
  出力 0 byte・rc=1 だが、**所有 9 file すべての編集は完全に残っていた** (親が blob hash 照合で確認)。
  「報告が無い」は「作業が無い」ではない。親は成果を回収し、完成度の確定を段 6 のレビュー 2 本の
  仕事に含めた。走行は 1587 秒・model call 100・cached 15,383,296 token。
  途中の stderr には `apply_patch verification failed` 3 件と、`python3 -I -B - <<'PY'` で
  `tools/pegasus/floor_campaign.sh` を読もうとして guard に拒否された 1 件が残っている。
- **段 6 のレビュー 2 本は私の argv の誤りで 1 度落ちた** (`--reasoning` は review 段では
  指定できない。rc=2)。名前を変えて投げ直した。実装や検査の問題ではない。
- **段 6 レビュー B の must-fix 4 件のうち 2 件を採用し、2 件を nit へ降格した。** 降格の根拠は実走。
  受入台帳の陳腐化と自走 harness の不在はどちらも関門を落とさない (該当 meta-test 82 passed)。
  受入台帳の正しい更新方法は実受入の記録から再生成することだが、それは受入の後になり
  「検査済み tip 以降は編集不可」の land 契約と衝突するので次の一手へ回した。
- **変異は挙動 kill 8 件と診断感度 pin 3 件に分けて記録した。** 本走は 11/11 KILLED だが、
  受理集合か fail-closed 挙動が期待方向へ変わったのは 8 件である。とくに空文字分岐の変異は、
  承認値が 32 桁 hex の nonce と一致しない以上、不一致分岐が同じ入力を必ず拒否するので
  冗長 gate である。段 3 が求めた「`-z` の歯」は診断上だけ閉じた — 正直にそう記録する。
- **一次資料**: `output/insights/2026-09-07_t2324-official-approval-binding/`
  (README、段 1 brief、段 4 裁定、子 5 本の逐語、変異 spec 2 本と台帳 2 本)。

## 次の一手差分

### 完了

- [T-2324] 床値 official の §8 承認束縛を実装し、投入手順を固定 official + 明示承認へ入れ替えた。
  変異 11/11 KILLED。実投入はしていない (測定認可は D1641 が別に扱う)。
  remaining: none
  base: 635b6735d8ed712a808d644a7eca0593fbe8330bb777778d6ea3d63fbc1ab14c

### 新規

- {{T:floor-official-result-repo-relative-vs-evacuation}} **P2・新規**: official 床値 result の
  repo 相対読取りと、走行直後の repo 外退避の順序を決める。`s8b_holdout_freeze._validate_floor_inputs`
  は repo 相対に解決して official run path を要求する一方、holdout clean-scan の除外は
  `output/s8b-freeze/` だけなので、result を repo に置いたまま次の official job を起動すると
  起動証明が止まる。**clean-scan は緩めない。** candidate 生成を実際に走らせる wave で決める。
- {{T:acceptance-duration-ledger-nodeid-regeneration}} **P3・新規**: 受入所要時間台帳の nodeid を
  実受入の記録から正規の updater で再生成する。旧 nodeid 7 件が残り、新 nodeid 17 件が欠落している。
  網羅を強制する検査は無いので関門ではないが、shard 割当の根拠が実際の suite と食い違う。
  推測時間を手書きしない。
- {{T:restart-runbook-w3-candidate-producer-exists}} **P3・新規**:
  `docs/phase3-8b-restart-runbook.md` W-3 の「candidate producer が存在しない」を現況へ直す。
  `generate-v2-candidate` は既に実在する。[T-2324] の変更が原因ではないので当時は scope 外とした。
