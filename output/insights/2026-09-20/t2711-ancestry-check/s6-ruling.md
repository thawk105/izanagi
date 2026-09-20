# [T-2711] 段 6 裁定 — レビュー 2 本の所見と採否

- 日時: 2026-09-20 07:46 JST。レビュー A (正しさ境界・帰属) = `verbatim/s6-review-A.md`、レビュー B (過剰・削除・記録) = `verbatim/s6-review-B.md` (codex gpt-6-astra / read-only、`check_codex_output` rc=0 ×2)。対象 = 実装 commit `d24ec35ea` + 焦点走 log + 変異 spec 2 本 + 段 4 裁定。
- 初回投入 (tag A/B) は親が `--reasoning medium` を review 段に付けて rc=2 (DW-C01 に記載済みの禁止形、親の投入ミス)。tag A2/B2 で再投入し、以後 A/B と呼ぶ。

| # | 所見 | 裁定 | 採否 | 反映 |
|---|---|---|---|---|
| A-must | なし | — | — | patch GO |
| A-should A1 / B-should S1 | 実 repo test (`test_real_freeze_gate_lists_floor_and_budget_null`) を S から外す理由の「差分が消える」は不正確。node 集合で見れば e2e が加わる差分は残り、消えるのは M3 の集約 status (SURVIVED→KILLED) の差だけ。かつ実 repo test は growth hold で焦点走でも未実行 (`focus1.log` の hold 6 件に含まれる) なので、その検出は「hold 解除・比較到達時の静的予測」と書く | real | 採用 (docs) | README §5・§6 と fragment の文言: 「S = 既存 unit と対象 e2e で追加検出の帰属を示せる最小集合」「実 repo test の検出は静的予測 (hold 中)」 |
| B-should S2 | 先行裁定 (entry 1554 §2-2) を「訂正」と呼ぶのは強い。先行文は「alternates 経由で見えると…変わりうる」の条件付きで、入口の拒否経路を否定していない | real | 採用 (docs) | README §7 を「現行 `verify_receipt` の入口では alternates が拒否されるため、先行裁定の条件付き観測変化をそのまま現行 e2e の実行経路の説明には使えない」に限定。案 B の再裁定なし |
| B-nit N1 | comment 2 行目 (report との一致は同一 source) は 2090 行付近の既存 comment と説明が重なる。削除は任意 | real | 不採用 | 検出力不変。新版の変異走が `d24ec35ea` で既に走行中であり、コード再変更は焦点走・変異の再走を要して費用に見合わない。裁定 §3 が comment 1〜2 行を許容済み |
| B-nit N2 | M2 は M1 と同一分岐・同一比較で失敗するので削除可能。ancestor / not-ancestor 両方を明示する目的なら 3 件維持も妥当 | real | 不採用 | 事前登録どおり 3 件を維持 (両走とも投入済み)。両状態を明示する目的 |
| A (患部の補足) | 追加後の e2e で最初に赤になるのは追加 assert (2058 行) — 他の既存 assert (`refusals == ()`、`active-valid`、fixture 子プロセス検査) は 3 変異で変わらない (M 143〜147、2381〜2383、2426〜2434) | 静的予測 | 記録 | 変異の実測で失敗行を確認して帰属を確定する (README §5) |
| A (焦点走) | 348 passed / 7 skipped は緑。skip 7 のうち 6 は log に列挙された growth hold、1 件は非 verbose log から node を特定できない。追加 assert に skip 経路は無い | real | 記録 | README §4 に「4 file 全 node 実行済み」とは書かない |
| B (記録) | brief 実測 2 の「実 repo test は 17 件全部を `_independent_ancestry_item` で比較」は末尾 2 件だけ (先頭 15 は golden tuple)。成果は「17 件すべてに独立比較がある」であり「全 field を独立検算」ではない (先頭 15 件は 4 field 比較のまま) | real | 採用 (docs) | README §1・§7 |

fix 子: 起動しない (コード変更なし)。焦点再レビュー: 不要 (DW-O16 は fix 後に適用)。
