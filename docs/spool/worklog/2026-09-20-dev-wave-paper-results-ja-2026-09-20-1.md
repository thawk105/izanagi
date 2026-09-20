---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-paper-results-ja-2026-09-20
seq: 1
title: 本体論文 (日本語) の結果・考察草稿を 2026-09-20 版として再導出し、09-10 の前稿 (entry 1436) を supersede した — 09-10 以後の results 稿 15 本と図 fig4〜fig12・fig8b を主張ごとの 12 節・表 15 に束ね、数値は稿の表の逐語、言えること / 言えないことは稿の限定と story §6 + stale 注記に揃えた (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-paper-results-ja-2026-09-20)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数、台帳 ID 未起票の新規執筆依頼) の範囲で 1 wave。成果物は `output/insights/2026-09-20/paper-results-ja/results-discussion.md`
  (12 節・表 15・出所 25) と同 dir README (段 1 実測・機械照合・前稿との対応・段 6 の逐次記録)、前稿 dir `output/insights/2026-09-10/paper-results-ja/README.md`
  (新規、前方 pointer。前稿本文は不変)、`docs/phase3.md` のチェック 1 項。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-ja-2026-09-20/HANDOFF.md`。
  軽量版 (docs-only、一次資料の再抽出) で段 2・3 を省き、段 6 は read-only レビュー 1 本 + 焦点再レビュー 2 本。実装差分 0、新規測定 0、変異 matrix は免除、受入全走は免除しない。
- 起点 local main `fec4a8187`、採用時点 `482f19b88`。段 6 の前に peer 通知を契機に main を読み直し、[T-2304] (ccbench pin `511c9538` → `e9e477ca`) の着地を実測 →
  採用時点を更新して稿の pin の記述 (§10 / §12: 観測当時の pin と採用時点の main の pin を分け、既存測定は無効にならない = 規律 7) を直し、main を固定 SHA で
  `--no-ff --no-commit` merge (競合なし、main に対する差分は自 wave の 3 file のみ) → submodule 初期化 → integrator commit → 全史 provenance 12,012 件新規違反なし。
- 入力: results 稿 19 本の §0 / §2 / 限定、story 2026-09-20 版 §3 / §6 / §8、paper-story README の stale 注記 3 件 (fig10 着地、**D2174 項 3 の B-7 限定付き充足** =
  版 §8 の「昇格させない」を supersede、fig12 着地)、figures README の一覧と fig10 追補、凍結 JSON 2 本 (P2-5、S-2 / S-3 は前稿から値不変)。裁定 D2172 項 2 / 項 3
  (T-2792 / T-2795) は「裁定済み・実装着地済み (entry 1736 / 1746)・測定は未」と状態で分けて書いた。
- 親の機械照合 (job dir `artifacts/numcheck.py`): 本文の数値 token 355 件 (fix 後 360 件) を一次資料の本文へ桁区切りの有無を両方で逐語照合、未検出 4 件は稿側の表記差
  (`%` 無し列・空白入り) のみ。量化語は稿の該当文を引用し、cohort 2 の `L ≥ 0.27` は同稿 §2.2 で確認。
- **段 6 review-1 (gpt-6-astra / medium、28 call、507 秒、NO-GO): 所見 12 = must-fix 4 / should-fix 7 / nit 1、全件 real・採用 (refuted 0)。数表 15 の転記違いは 0 で、
  所見はすべて条件・採用時点の状態語・説明の帰属** — (1) 凍結 v2 g1 は entry 1742 で承認 A / active pointer X により批准済み (loader 成功、P3 の launch validation は未達)
  なのに「未発効」と書いた、(2) 検証相の 10 s 未完走の原因は entry 1744 で同定済み (fixed-5 の trace 2 本、当時の記録は不変) なのに「未確定」と書いた、(3) S-1a の
  324 verify を全部 `legacy` に帰属した (実は legacy 306 + s2 18)、(4) 旧 A-2 の訂正の根拠を `src_token` 単独に帰属した (稿は 4 field の連言)、(5) B-5 を「必要性を示す
  対照」と呼んだ (D1067 は条件付き優越へ)、(6) 「12 本」の母集合違い (15 本 = 単独 13 + B-7 併記 2)、(7) 採用時点が本文に 2 つ、(8) 右 tail の事前登録 §0 の限定の脱落、
  (9) mocc の CP / Fisher の仮定の脱落、(10) 待ち方 grid の 36 = 18 + 18 の明示、(11) 前稿にあった S-3 の非有意の限定の脱落、(12) 出所 path の短縮規約。(1)(2) は
  起草起点に含まれる entry を親が見落としたもので稼働中 wave の先取りではない。fix commit `27df019b1`。
- 段 6 focus-1 (11 call、218 秒): closed 11 / partial 1 (所見 9 の追記文が witlight 稿の「4 node で同時刻」と不整合) / regressed 0、親の量化 5 件は再計数で一致。
  範囲外走査で新規 2 件 = (13) §3.6 の certified の射程が T-1998 (legacy 各 arm 1 回) へ広がって読める (must-fix)、(14) abort 率の集約方法を「代表 rep 1 点」に一律化
  (右 tail は 5 反復平均) (should-fix)。3 件 real・採用、fix commit `62c9f887b`。focus-2 (3 call、63 秒): 3 件とも closed、GO。
- 検査: `check_docs` 違反なし、`git diff --check` 緑、全史 provenance 新規違反なし、三軸語走査 (`s8b_holdout_freeze search`) の hit は既存 (official floor 成果物 3 file +
  g1 候補 1 file、2 holdout) のみで本 wave の file は 0。受入: 記録 commit の tip で待ち手経由の全走 (`dev_wave_wait.py acceptance`、3 shard) を門番 loop から投入する。
  結果は本 fragment には書かず受領証 (job dir) と land の記録が持つ。child-green でなければ land しない。
- 限界・言わないこと: 本稿は執筆者向けの統制稿であり投稿本文ではない。数値の権威は各 results 稿とその権威 bytes にあり、本稿は転記の検算 (逐語存在) まで。
  採用時点より後に着地する事実 (A-1 attempt-0002 の投入、K2 4 巡目、story 次版) は反映せず、次に正典が動いたら新しい日付の稿で再導出する。英訳・図の生成・
  版や claim-evidence の改訂は行っていない。
- 気づき (記録のみ、gate は足さない): 数表の転記は機械照合で守れたが、採用時点より前に着地した worklog entry の状態語と、稿の限定の条件 (検査条件の内訳・集約方法・
  実行時刻) は機械照合の射程外で、独立レビュー 3 巡がすべてそこを突いた。次の再導出では起草前に当日の worklog entry 見出しを全部読み、「未発効」「未確定」型の
  状態語は grep で反証してから書く。
- 工数: codex 3 本 (review 1、focus 2)、計算ノード job = 受入のみ。

## 次の一手差分
