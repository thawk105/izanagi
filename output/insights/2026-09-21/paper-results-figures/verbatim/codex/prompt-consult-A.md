単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、その旨だけを `## 総括` に書いて終わる (射影 file 限定の停止規則で、自分が推測して探した path の不在は停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-brief.md` — 親の段 1 brief。**これ自体も攻撃対象**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-pin-closure.md` — 親がまとめた pin 閉包 (**攻撃対象**)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/plan.md` — 段 2 の codex plan。**攻撃対象**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/verbatim/` 配下の全 file (依頼文の逐語 `origin.md`、裁定の逐語、両 results 稿の該当節、README 2 本の現行節、先行 wave の終端記録)
- repo 内 (worktree の path、read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures/` の
  `tools/plotting/plot_a1_sized_paired.py` (全文)、`orchestrator/tests/test_plot_a1_sized_paired.py` (全文)、`tools/plotting/FIGURE_CONVENTIONS.md` (全文)、
  `tools/plotting/plot_b10_waiting_grid_forest.py` と `orchestrator/tests/test_plot_b10_waiting_grid_forest.py` (部分読み)、
  `docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1.provenance.json` (構造だけ)、`docs/failures.md` の F623 / F653 / F812 / F872 (`grep -n "^### F623\|^### F653\|^### F812\|^### F872"` で位置を出して各 20 行)
- repo 外 (read-only): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/summary.json`、`W1/result.json`〜`W4/result.json` (全文 cat しない。`python3 -c` / `jq` で見る)

**大きい file を全文 `cat` しない。** sandbox は read-only で書込可能 tmp は無い。静的検査でよい (テスト実測は親が行う)。予算が尽きそうなら途中結論を下の出力形式で書いて終わる。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。

## 前置き — この依頼の性質

対象は研究用 repo の論文図の生成器 (matplotlib) の拡張・新設と、その図・provenance・test の**計画の敵対レビュー**である。セキュリティでも攻撃でもない。
あなたの仕事は plan と brief を守ることではなく、**欠陥を見つけること**である。所見は real と判断した根拠 (file:line・実測値・一次資料の逐語) を付ける。

## レンズ A — 正しさ境界・整合・実効性

次を探せ。見つからなければ「探した場所と方法」を書いて「所見なし」とする (推測で「無い」と書かない)。

1. **主張の境界の破れ:** fig14 が 2 attempt のプール・差・比・区間の重なり・再現判定・attempt-0001 の値を描く/書く経路、`variance_plan_breach` の原因を帰属する文言、
   fig15 が非有意を同等性・「効果なし」・「on では出ない」として、TRACE=1 の commit 数を性能 (throughput) として、G2 signal を根因・実 anomaly の確認として描く/書く経路
   (軸 label・panel 題・凡例・注記・caption のどこでも)。禁止すべき語の一覧が plan に欠けていないか
2. **fig9 の不変性:** plan の変更で attempt-0001 の `load_leaf` 返り値・caption・provenance の形・CLI の再現 argv・既存 test のどれかが変わらないか。
   着地 fig9 の `validate_repo_closure` (現行生成器で作り直した値と着地 provenance の全 key 一致) が通り続けるか。既存 test を弱める変更 (削除・条件緩和・skip 化) が無いか
3. **束縛の実効性:** pin 表 (D1752) を CLI から迂回できないか、attempt の取り違え (attempt-0002 の pin で attempt-0001 の caption_source を使う等) を拒否できるか、
   fig15 の 5 file の SHA-256 束縛・`summary.json.inputs` の W1〜W4 exact 照合で smoke 混入や block 欠落を拒否できるか、着地閉包の repo 内 / repo 外の分離で
   repo 外証拠が不在のとき何も検査しない恒真 test が生まれないか
4. **開示の現物検査 (F872 / F623 / F653):** fig14 の breach 表示と fig15 の「TRACE=1 exposure, not performance」等が PNG/PDF に実際に描かれることを、
   内部値でなく `fig.findobj(Text)` の実 artist で検査する計画になっているか。provenance の artist 系列が描画と別経路で作られていないか
5. **数値の一致:** fig15 の CP 両側 95% (scipy 無し)・片側 Fisher・commit 数平均・on/off 比が稿 §2.2 / §2.3 / §2.6 の表記 (`[0%, 5.963%]`、`[0.042%, 8.940%]`、`0.500`、
   `613,741.5`、`0.8636` 等) と丸め込みで一致する計算になっているか。`summary.json` の `cp95` との照合許容誤差、`k` の定義 (`verifier.status == "g2"` か `anomaly_count` か) の一義性
6. **実寸 fixture (F812 / D1546):** fig14 は 3 workload × 30 対 × 2 arm、fig15 は 4 block × 60 走 (15 round × 4 arm・回転・G2 2 走) を production の形で作るか。
   fixture が小さくて layout 検査が恒真に通る箇所が無いか
7. **変異候補の単一理由性:** plan §7 の各変異について、同じ入力を拒否する層が前後・内側に別にあって赤理由が 2 つ以上になるもの、kill 予定 test が実は通るもの
8. **親 brief 自身の誤り:** brief の実測値 (図番号の未使用、`summary.json` の key、verbatim 写しの SHA-256 一致、attempt-0002 の field 値) とその一般化、P1〜P8 の前提の誤り

## 出力形式

```
## 所見
| # | 重大度 (must-fix / should / nit) | 対象 (plan §x / brief / 既存 file:line) | 内容 | 根拠 (file:line・実測・逐語) | 推奨 |
## P1〜P8 の判定
(P ごとに 同意 / 反対 / 根拠不足 と 1〜2 行)
## 探したが所見なしの項目
## 総括
```

`## 総括` は 5〜10 行。must-fix の件数と、plan を実装へ進めてよいか (GO / 条件付き GO / NO-GO) を書く。
