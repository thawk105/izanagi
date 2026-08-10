# [T-675] whole-file SHA-256 pin の意味欠落 — 設計択一を裁定へ返した (2026-08-10)

authority: none / default_effect: no-state-change

wave = `dev-wave-t675-pin-semantic-gap` /
branch = `worktree-dev-wave-t675-pin-semantic-gap` / 起点 main = `7c3ac3e9`。
親の裁定要約は worklog の該当エントリ。

## 射程 (これを越える引用を禁じる)

本 wave は **実装差分ゼロの設計 wave** である。land したのは裁定パッケージと逐語だけで、
**意味検査を 1 行も実装していない。**

- 「[T-675] が解決した」と書いてはならない。したのは**択一の整理と前提事実の実測**だけである。
- 段 2 プランの推奨 (専用関数 + 全 path / 全 F ID / Skill 側まで含む検査) は**親が採らなかった**。
  段 3 の敵対 2 レンズが**両方とも NO-GO** を返し、親が実測で裏取りして縮めた。
- 親自身の当初案 (必須 literal の token 分解) も**取り下げた** — 実測 (M11 状態 iii) で
  token 移動により迂回できることを確認したためである。
- 本 wave が測ったのは `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` の
  2 gate だけである。**land 経路・hooks・provenance は測っていない** (段 3 レンズ A の指摘で縮めた)。
- `.agents/skills/cleanup-branches/SKILL.md` 側の攻撃は**実測していない** (静的に同型と推定しただけ)。

## 構成

- `package.md` — 裁定パッケージ本体 (R1〜R4)
- `verbatim/measurements.md` — 親が実 repo で測った M1〜M12
- `verbatim/s1-brief.md` — 段 1 brief (訂正前。M1/M6/M7 の誤りを含む歴史記録)
- `verbatim/s2b-plan.md` — 段 2 プラン (read-only codex sol / max)
- `verbatim/s3-lensA2.md` — 段 3 レンズ A (sol / max、NO-GO)
- `verbatim/s3-lensB2.md` — 段 3 レンズ B (luna / max、NO-GO)

## 親の誤りで敵対検証が訂正したもの (歴史として残す)

1. **M6「pin と意味検査は交差ゼロ」は誤り**だった。段 2 プランが反例を出し、親が
   `tools/check_docs.py:4104-4107` を読んで確認した — pin 済み command は既に
   `docs/skill-self-improvement.md` への到達性を検査されている。
2. **M1 の pin 閉包は command 3 箇所ではなく族全体で 6 箇所**だった (Skill 側 3 箇所)。
3. **必須 literal の token 分解案は迂回可能**だった (レンズ A、M11 で実測確定)。
4. **段 2 プランの「実質上限 24 bytes は checker が強制する値ではない」は不正確**だった。
   親が `_assert_cleanup_digest_violation` の `_violation_count(res) == 1` を読んで反証した
   (レンズ B も独立に real と判定)。
