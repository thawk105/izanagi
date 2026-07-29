authority: none
default_effect: no-state-change

# [T-126] 逐次停止 v2 実装前審査の逐語束

このディレクトリは、2026-07-29 の dev-wave で実施した実装前審査の入力・最終出力を凍結する。
一時的な実行ログ、prompt、終了コードは、各最終出力を `tools/check_codex_output.py` で検査した後に
除外した。

- `parent-brief.md`: 親が固定した依頼、scope、既知前提
- `plan.md`: 読取専用 planner の最終提案
- `consult-stat.md`: 統計・測定・実行環境レンズの敵対相談
- `consult-proof.md`: proof chain・consumer・promotion authority レンズの敵対相談
- `adjudication.md`: 親の独立再現と段 4 裁定

実装判断の公開正本は
`output/insights/2026-07-29_t126-implementation-preflight.md` とする。
