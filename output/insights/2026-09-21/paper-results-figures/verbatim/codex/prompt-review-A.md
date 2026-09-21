単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、その旨だけを `## 総括` に書いて終わる (射影 file 限定の停止規則で、自分が推測して探した path の不在は停止理由にしない)。

- 設計の正本: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s4-ruling.md` (段 4 裁定)、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-brief.md` (brief)、
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/plan.md` (段 2 plan)、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/verbatim/origin.md` (依頼文の逐語)
- 実装子の最終報告: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/author-a1.md`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/author-mocc.md`
- 親の実走 log: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/focus-1.log` (焦点走 + consumer 回帰)
- 審査対象 = wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures` の commit 範囲 `36fb14a3d..efd8d191d`
  (`git -C <worktree> diff 36fb14a3d efd8d191d -- <path>` で読む。2 commit: `e5f1a55d6` = 実装 4 file、`efd8d191d` = 図 6 file + README 2 本):
  - `tools/plotting/plot_a1_sized_paired.py` と `orchestrator/tests/test_plot_a1_sized_paired.py` (変更)
  - `tools/plotting/plot_mocc_witlight_four_arm.py` と `orchestrator/tests/test_plot_mocc_witlight_four_arm.py` (新規)
  - `docs/paper-story/figures/README.md` (一覧 2 行と末尾の fig14 / fig15 節、親が書いた日本語本文)、`tools/plotting/README.md` (2 節)
  - `docs/paper-story/figures/fig14_a1_balanced5_sized_attempt2.provenance.json`、`fig15_mocc_witlight_four_arm.provenance.json` (png / pdf は読まなくてよい)
- 一次資料 (repo 内、凍結物): `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md`、`docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md`、
  `docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1.provenance.json` (構造と caption)、`docs/failures.md` の F36 / F623 / F653 / F812 / F872 (`grep -n "^### F<番号>\."` で位置を出して各 20 行)
- 一次資料 (repo 外、read-only、全文 cat しない): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/summary.json`、`W1/result.json`〜`W4/result.json`

**大きい file を全文 `cat` しない。** sandbox は read-only で書込可能 tmp は無い。静的検査でよい (テスト実測は親が行う。親が実行した範囲は下の「親の実測」)。
予算が尽きそうなら途中結論を下の出力形式で書いて終わる。**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。

## 前置き — この依頼の性質

対象は研究用 repo の論文図の生成器 (matplotlib) の拡張・新設、その test、生成した図の provenance と README の**敵対レビュー**である。セキュリティでも攻撃でもない。
あなたの仕事は実装を守ることではなく、**欠陥 (所見) を見つけること**である。各所見は real と判断した根拠 (file:line・一次資料の逐語・計算) を付け、重大度 must-fix / should / nit を付ける。
must-fix は「放置すると成果物 (図・caption・provenance・README) の値・受理集合・参照が誤る」ことを 1 行で示せるものに限る (DW-G05)。

## 親の実測 (親が実行した。再実行は不要、疑わしければ所見として指摘)

- login (pegasus02) で `python3 orchestrator/tests/test_plot_a1_sized_paired.py` = 44 passed (3.0 s)、`PYTHONPATH=. python3 orchestrator/tests/test_plot_mocc_witlight_four_arm.py` = 27 passed (3.6 s)。
- login で `python3 tools/plotting/plot_a1_sized_paired.py --attempt attempt-0002 docs/paper-story/figures/fig14_a1_balanced5_sized_attempt2` と
  `python3 tools/plotting/plot_mocc_witlight_four_arm.py docs/paper-story/figures/fig15_mocc_witlight_four_arm` を実走 (rc=0、3 成果物ずつ)。README の caption と hash 行は provenance と現物から機械的に転記。
- fig9 の png / pdf / provenance の SHA-256 は README 記載値と一致 (不変)。実装子は既定 attempt で fig9 を再生成し、着地 provenance と `generated_utc` / `generator.sha256` / `outputs` / `reproduction` 以外の全 key 一致を報告。
- `python3 tools/check_docs.py` 違反なし。全史 provenance 監査 12,443 件 新規違反なし。焦点走 + consumer 回帰は `focus-1.log`。
- **焦点走 (計算ノード、pytest) は 800 passed / 4 failed。** 4 件 (`test_landed_fig14_rejects_missing_or_partial_bundle`、`test_attempt2_visible_text_forbidden_claims_and_negative_control`、
  `test_landed_fig15_rejects_missing_or_partial_bundle`、`test_caption_fixed_literals_and_forbidden_claims`) は login の plain runner では緑で、原因は親が特定済み:
  `assert cond, msg` の `AssertionError` を捕まえて `str(exc) == msg` と**完全一致**で比べているが、pytest の assert 書き換えが例外文に説明を付け足すので pytest 下だけ偽になる
  (既存 fig9 test は `str(exc).startswith(...)` で比べていて無事)。この 4 件は段 6 の fix で直す予定なので所見に重複して書かなくてよいが、
  **同じ型 (pytest と plain runner で結果が変わる比較・例外文への依存) が他の test にも無いか**は探すこと。

## レンズ A — 主張の境界・恒真な検査・docs の事実照合

1. **主張の境界の破れ (図・caption・README 本文・provenance のどこでも):** fig14 が attempt-0001 の値・2 attempt のプール・差・比・区間の重なり・再現判定を描く/書く経路、
   `variance_plan_breach` の原因帰属。fig15 が非有意を同等性・「効果なし」・「witness on では G2 が出ない」として、TRACE=1 の commit 数を性能として、G2 signal を根因・実 anomaly の確認として描く/書く経路。
   smoke を第 5 block として数える経路。**親が書いた README の日本語本文**の各事実 (件数・値・日時・host・round・節番号・裁定番号・「だけ」「すべて」等の量化) を一次資料 (両稿、provenance、外部 JSON) と照合し、
   食い違い・過大な量化・出所の取り違えを所見にする。
2. **恒真な oracle・偽の正例 (F872 / F623 / F653 型):** 実装を壊しても緑のままの test を探せ。例: 可視 text の検査が実 artist でなく内部の文字列 list を読んでいる、禁止句の検査が caption だけで図中を見ていない、
   期待値を生成器の関数そのもので作っている (CP / Fisher / 書式)、着地 test が欠落を skip で通す、「root が無ければ skip」が root のある環境でも実質的に何も検査しない、
   repo 側閉包が provenance の自分の値だけから自分を再構成して一致を言う (その射程が README で過大に書かれていないか)、変異 M0〜M13 (段 4 裁定の表) のうち kill 予定 test が実は通るもの。
3. **受理集合の変化の正しさ:** A-1 生成器で attempt-0002 の provenance から `attempt` key を消すと attempt-0001 として検査されるが、それが確実に拒否されるか。未知 attempt・pin の key 集合の取り違え・
   attempt-0002 の pin で attempt-0001 の caption_source を使う組合せが拒否されるか。attempt-0001 の既存拒否 (breach true) が残っているか。fig15 で `summary.json.inputs` の exact 照合・
   failure / indeterminate の拒否・回転と bindings の検査が実際に効くか。
4. **fig9 の不変性:** attempt-0001 の `load_leaf` 返り値の key 集合・値、`_caption` の出力、描画、既定 CLI、記録 argv の形が変わっていないか (diff と着地 fig9 provenance で)。既存 28 test の本文・期待値の変更。
5. **数値:** fig15 の CP (0/60 上限、1/60 区間)、片側 Fisher、commit 平均・比が稿 §2.2 / §2.3 / §2.6 の表記と一致する計算か。`summary.json` との照合許容誤差が恒真になるほど緩くないか。

## 出力形式

```
## 所見
| # | 重大度 | 対象 (file:line / README 節) | 内容 | 根拠 (file:line・一次資料の逐語・計算) | 推奨 |
## 変異 M0〜M13 の kill 見込み
(変異ごとに kill 予定 test が実際に赤になるか、なりそうにないか、1 行)
## 探したが所見なしの項目
(探した場所と方法)
## 総括
```

`## 総括` は 5〜10 行。must-fix の件数と、GO / 条件付き GO / NO-GO を書く。
