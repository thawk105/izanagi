# 2026-08-11 [T-798] / [T-799] fold transaction の窓 — 実測の逐語

`authority: none` / `default_effect: no-state-change` — 本書は凍結記録であり、可変状態の正本
(worklog 末尾・現行 phase doc) ではない。設計判断の正本は decisions、経緯の正本は worklog の
該当エントリ、裁定待ちの問は `package.md`。

本 wave は**本番コードを 1 行も変えていない。** 依頼は「両方の窓を再現実測し、
各選択肢 (a)/(b)/(c) の実装コストと検出力を添えて裁定パッケージを返す」である。

- `s1-brief.md` — 段 1 brief (scope・不変条件・親の provisional 裁定)
- `findings.md` — 実測結果 (数値と逐語の本体、敵対レンズの指摘による訂正を含む)
- `package.md` — 裁定パッケージ (Q1〜Q6)
- `verbatim/probe-injection-points.md` — probe の注入点
- `verbatim/probe-logs.md` — probe の出力
- `verbatim/consult-sol-lens-a.md` — 敵対レンズ A (実測の妥当性を攻撃)
- `verbatim/consult-luna-lens-b.md` — 敵対レンズ B (裁定と選択肢評価を攻撃)

## 測定環境

- checkout: `.claude/worktrees/dev-wave-t798-t799-fold-window`
- 測定した HEAD: `9abd23daa0dd885a9b1121bddd34b7c44c441428` および
  `974207aea436776db85d83dca04bf36007dd2fcf` (worklog rotation の前後)
- probe の所在: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/` (repo 外)
  — [T-317] 裁定に従い、実行可能な probe は repo へ入れない。逐語は本 `verbatim/` に `.md` で置く。

## 測ったもの・測っていないもの

**測ったもの (本番の制御フロー):** `tools/dev_wave_land.py` と `tools/spool_fold.py` を実体のまま
import し、land の ff-only → `apply_fold` → `check_docs` → staging → commit → postcondition →
`verify_declared_fold_commit` を通した。land 本体へ monkeypatch は当てていない。

**模擬しているもの (3 点):** (i) 台帳の中身 (合成の最小 canonical)、
(ii) `tools/check_docs.py` / `tools/check_ai_provenance.py` の実装 (fixture の stub)、
(iii) repository が tempfile 配下であること。
**窓の幅だけは合成では測れないので、実 repo の実物に対して別途測った。**

## 結論 (要約)

1. [T-798] の窓は実在する。窓の内側で land を SIGKILL すると、canonical・`FOLDED.md`・
   fragment GC が反映済みで fold commit も journal も無い状態が残る。
   **正規の復旧 CLI (`python3 tools/spool_fold.py`) は rc=0 / `status=noop` を返す。**
2. [T-799] の窓も実在し、**核は HEAD ではなく plan 入力 closure の未束縛**だった。
   state が hash で束縛するのは plan の *target* だけなので、採番の入力
   (archive worklog・phase3 見送り台帳・`WORKLOG_ROTATE_BYTES`) は現れない。
   archive を変えてから resume させ、**重複した T 番号を実際に作った**。
3. resume 経路は新規 apply が通る `_git_clean_preflight` を**通らない** — resume の方が弱い。
4. **両者は連結している。** standalone resume は commit を作らないので、成功しても
   [T-798] の残骸と同一の tree になり、次の land を rc=20 で止める。
5. 選択肢 (b) は窓を消さず「commit 済み・state 残存」へ**移す**。その形から land を
   再投入すると rc=10 `stale-main` で止まる (追加実測)。

## 敵対レンズが親の主張を崩した点

段 3 相当の敵対レンズ 2 本 (`consult-sol.md` = 実測の妥当性、`consult-luna.md` = 裁定の妥当性) が
親の主張を複数崩し、親は追加実測 3 本 (`probe_option_b_wedge.py`、`probe_plan_input_closure.py`、
`probe_resume_hard_plan.py`) でそれを裏取りした。撤回・縮小した主張の一覧は `package.md` 冒頭にある。
とくに窓幅の数値と一般化、「(b) は新機構不要」、「C2 は帰属が壊れた欠陥」は撤回・縮小しており、
**代わりに重複 T 番号という値の欠陥が新たに測れた。**
