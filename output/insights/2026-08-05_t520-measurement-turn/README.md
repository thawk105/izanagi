# [T-520] 資源分類の実測をユーザー端末の手番として明文化する — 逐語

dev-wave `worktree-dev-wave-t520-measurement-turn` (2026-08-05) の敵対レビュー逐語。
台帳側の正本は worklog エントリと D180 で、本ディレクトリは**子の出力そのもの**を凍結する。

| ファイル | 中身 |
|---|---|
| `s6-revA.md` | 1 巡目 敵対レビュー (codex read-only)。NO-GO / must-fix 3 |
| `s6-refocus-1.md` | 2 巡目 焦点再レビュー (`DW-O16` の対応表付き)。NO-GO / must-fix 3 |
| `s6-refocus-2.md` | 3 巡目 焦点再レビュー。NO-GO / must-fix 2 |

## この wave の形

docs-only (`docs/pegasus-runbook.md` §7.0 / `tools/README.md` / spool fragment 2 本)。
`DW-C00` の軽量版で段 2・3 と実装子を省き、親が編集して codex read-only の敵対レビューだけを
回した。受入全走は計算ノードで 4 回、いずれも 6453 passed / 20 skipped (rc=0)。
実装差分が無いため変異 matrix は対象外で、変異事前登録も行っていない。

## レビューが実際に止めたもの

3 巡とも NO-GO で、**2・3 巡目の must-fix には前巡の fix が生んだ欠陥が含まれた**。

1. 1 巡目: `tools/README.md` が「分類 registry も gate も存在しない」と書いていた
   ([T-481] 以後の事実と食い違う) / D175 決定 2・4 と F123 の「裁定待ち」を supersede した
   記録が無い / 未閉鎖の実行面を規範本文へ再列挙している。
2. 2 巡目: 親の 1 巡目 fix が「機械強制は `tools/pegasus/` 配下だけ」という逆向きの過大限定を
   作り、テストと provenance 監査の login 拒否を不存在扱いしていた / decisions fragment の
   測定依頼項目が不足 / worklog fragment 自身が「`tools/README.md` には触っていない」と虚偽を
   書いていた。
3. 3 巡目: 限定の掛け方がまだ狭い / worklog fragment が未実施の commit 後検査を完了事実として
   書いていた。

`DW-O16` の 3 巡上限に達したため、3 巡目の 2 件は親が real と裁定して是正し、4 巡目は回していない。

## 部分不採用 1 件

1 巡目の `BYPASS-01` は、worklog の「迂回 4 系統」の列挙も抜け道目録として抽象化せよと求めた。
規範本文 (runbook) 側は抽象化したが、**台帳側は保持した** — 既存 item の本文であり、削ると
閉鎖対象の同一性が失われる。2・3 巡目のレビューもこの境界を妥当と判定している。

## この wave が主張しないこと

- 循環そのものの解消。ユーザー端末が唯一の正規測定面であるという状態は変えていない。
- 測定専用 bounded surface の設計。裁定どおり admission registry の族再設計へ残した。
- registry の machine-readable 化 ([T-522])。§7.0 の「admission registry が正本」という記述は
  現状 (`hooks/guard_bash.py` 内) のまま残してある。
- レビュー子は sandbox が read-only のため pytest を実行していない。テスト実測はすべて親が
  計算ノードへ dispatch して行った値である。
