# [T-189] wave の逐語

`worktree-dev-wave-t189-reasoning-allowlist` の各段の子出力と親の裁定を、そのまま凍結したもの。
分析と結論は `../2026-08-03_t189-reasoning-effort-allowlist/README.md` が正本。

## 実行構成

- 段 2 プラン起草 / 段 3 敵対相談 / 段 6 敵対レビュー / 焦点再レビュー:
  `codex exec -m gpt-5.6-sol -c model_reasoning_effort="max" -s read-only`
- 段 5 実装 / 段 6 fix:
  `codex exec -m gpt-5.6-sol -c model_reasoning_effort="high" -s workspace-write`
- 採用条件は `tools/check_codex_output.py` の rc=0。全 12 本とも rc=0。
- 子はいずれも pytest を実行していない (Pegasus ログインノードのため)。テストの実測は親が
  計算ノードへ dispatch して行った。

## 一覧

| ファイル | 段 | 内容 |
|---|---|---|
| `s1-brief.md` | 1 | 親 brief。実測 M1〜M10、provisional 裁定 P1改 / P2 / P3 |
| `s2-plan.md` | 2 | codex プラン起草 (file:line 粒度) |
| `s3a-review-correctness.md` | 3 | 敵対相談 レンズ A (正しさ境界・受理集合・fail-closed) NO-GO |
| `s3b-review-effectiveness.md` | 3 | 敵対相談 レンズ B (実効性・整合・変異帰属) NO-GO |
| `s4-adjudication.md` | 4 | 親の裁定。所見 13 件の real/refuted、plan v2、変異事前登録 V1〜V11 |
| `s5a-impl-canonical.md` | 5 | 実装子 単位 A (許可リストの正本) |
| `s5b-impl-face1.md` | 5 | 実装子 単位 B (面 1 = codex worker launcher) |
| `s5c-impl-face23.md` | 5 | 実装子 単位 C (面 2・3 = dev-waves CLI / schema) |
| `s6a-review-contract.md` | 6 | 敵対レビュー R1 (契約遵守とテスト検出力) NO-GO |
| `s6b-review-attribution.md` | 6 | 敵対レビュー R2 (統合整合・波及・変異帰属) NO-GO |
| `s6fix-report.md` | 6 | fix 実装子 (FX1〜FX6、全件 closed) |
| `s6re-focused-rereview.md` | 6 | 焦点再レビュー (closed 14 / partial 2 / regressed 0) |

## 正規化の erratum (D88 / DW-S07)

`s5a-impl-canonical.md` は原文のまま置くと `git diff --check` の行末空白に抵触したため、
**可視文字を変えない可逆最小正規化**を 1 回だけ適用した。

- 対象: 行末の半角空白 2 個 (Markdown の hard line break) を持つ **2 行**
- 原文: sha256 `c4f40fa282ae4d60de4eb929f96c93c51412545cac9741d4406334ca990c06ab`、5715 bytes
- 凍結版: sha256 `af35fcc39c8d00f4e3e286f9a1a1a9ecdcb57ea92331dc9f5e18f33b409be89f`、5711 bytes
- 復元法: 「編集ファイル: 指定された 4 ファイルのみ。」と
  「波及: 既存 caller・fixture・consumer test の受理結果や診断への変更なし。」の 2 行の行末へ
  半角空白 2 個を戻すと原文 sha256 に一致する
- 他の 11 本には正規化を適用していない
