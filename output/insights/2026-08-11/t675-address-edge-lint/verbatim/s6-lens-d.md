静的検査のみ実施した。pytest・受入走行は実施していない。

1. R2 置換 — `refuted`

削除語は他文書の義務への唯一の到達手段ではない。

- byte・最長行: `docs/skill-self-improvement.md:46`、`tools/check_docs.py:4024-4029`
- 義務本文の意味保存: `docs/skill-self-improvement.md:49-50`、`docs/decisions.md:10646-10648`
- lint に固定せず: `docs/decisions.md:10646-10648`

2. D 本文

- `real`: `docs/spool/decisions/2026-08-11-dev-wave-t675-address-edge-lint-1.md:14-15` は trust root を「人間レビューと敵対監査」としている。正本の指定は trust root = 人間レビューである (`plan-v2.md:121-123`、`package.md:86-87`)。敵対監査は根拠形成手順であり、trust root と並記しない方が正確。
- `refuted`: 「協調改変を防ぐ防壁」と主張してはいない。明示的に禁止しており、package.md 3.3 と整合する (`...-1.md:15`、`package.md:86-87`)。
- `refuted`: SHA-256 は bytes だけを検査する、同時再 pin で通る、という主張は package.md:12-23 で裏付く。
- `refuted`: 既存の到達性・typed edge の存在は `tools/check_docs.py:3322-3325`、`4072-4084`、`4697-4723` で裏付く。
- `refuted`: raw HTML block と inline hidden HTML の限界は `tools/check_docs.py:1009-1027`、`...:1100-1106` で裏付く。
- `refuted`: D30/D45/D227 との衝突はない。自然文 lint を防壁化しない方針は `docs/decisions.md:646-655`、`1558-1567`、`10628-10643` にある。
- `speculative`: 「段 3 の敵対レンズ 2 本のうち 1 本が独立に一次資料へ当たった」は、提示された code/package だけでは裏付けられない (`...-1.md:19`)。根拠を追加できなければ削除すべき。

3. F1 への再発帰属 — `refuted`

F1 は日付誤記だが、既存の再発追記が「機構の実在状態の転写」まで型を拡張している (`docs/failures.md:22-26,36-42`)。今回の誤った F173 恒久対応も同型であり、F165（見積り再導出、`docs/failures.md:4231-4240`）や F188（承認外 gate の上乗せ、`docs/failures.md:4684-4690`）より F1 が適切。形式も `docs/spool/failures/README.md:5,38-40` に適合する。

4. fragment 形式 — `refuted`

両 fragment とも frontmatter は `schema/ledger/authored/wave/seq` のみで、禁止された `title` はない (`docs/spool/README.md:35-49`)。ファイル名と authored/wave/seq は一致し、decision の H2・slug、failure の `## 再発` → `### F1` の順序も適合する (`...-1.md:1-9`、`...-2.md:1-11`)。

5. 記録の不足 — `real`（段 7 待ち）

現 diff に明示的な R4 worklog fragment がないため、次が未記録または不十分。

- s1: 完全に未記録。
- s2: 限界自体は `...-1.md:27-28` にあるが、「scope 外の裁定候補」として未記録。
- c1: 親 brief の SHA-256 定数数の誤りの具体的訂正がない。
- c2: 内容は `...-1.md:24-26` にあるが、R4 の訂正記録として明示されていない。
- c3: `check_docs` と AI 作業手順だけが変わる、という限定がない。
- `DW-G05` backlog と B-057 発火の明記がない。

6. 受理集合 — `refuted`

diff 内に「受理集合は変わらない」という無限定表現はない。package.md:152-154 の表現は無限定だが、diff 対象ではない。正しい限定は plan-v2.md:37-39 のとおりである。

7. scope 逸脱 — `refuted`

実装は cleanup command の 1 分岐と 6 テストに限定されている (`tools/check_docs.py:4076-4084`、`orchestrator/tests/test_check_docs.py:6745-6837`)。F51、helper path、Skill 側、path 実在性、全 F 番号到達性は decision fragment に「却下対象」として列挙されただけで、実装されていない (`...-1.md:41-42`)。F173 訂正は plan-v2.md:133-135 で明示された R4 拡張内である。

8. DW-G05 — 限定主張は `refuted`

未実装・放置時に変わるのは `check_docs` と AI 作業手順の受理集合であり、certified 選択・レポート・試行台帳の値や参照を変えるコードは diff にない (`tools/check_docs.py:4072-4084`、`docs/dev-wave/core.md:65-70`)。ただし、その判断の記録自体は上記 5 のとおり段 7 で必要。

最小修正案: decision fragment の `trust root` を「人間レビュー」に限定し、未根拠の provenance 文を削除または一次資料で裏付ける。段 7 で R4 の不足項目と B-057 を worklog に明記する。

## 総括

D 本文に trust root の過剰表現と未裏付け provenance がある。  
R4/DW-G05/B-057 の記録も現 diff では未完了である。  
実装 scope、F1 帰属、fragment 形式、受理集合限定は問題ない。  
上記を直すまで land 不可。  
NO-GO