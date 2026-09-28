## 判定

**NO-GO** — 草稿は未発効のまま、以下の must-fix を直してから再レビューするのが妥当です。

## 所見

1. **must-fix｜レンズ 1｜[草稿 §11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/workload-description-critic-intervention-preregistration.md:358)、[起草 insight §3.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md:52)**
   **主張:** 試走 v2 の「15 系列・300 session で anomaly 0 件」。**根拠:** 引用先の[試走 v2 分析 §1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-27/t2850-trial-v2-analysis/README.md:12)と `section8.json` に anomaly 件数はない。完走・品質欠測 0 は記載されているが、anomaly 0 の直接の値ではない。**推奨:** 件数を裏付ける一次記録を引用するか、0 件の断定と「写しに中身が入る機会は少ない」という推論を削る。
   **放置時の誤り:** 確認できない 0 件を実測値として示し、失敗理由の写しの有用性の見込みまで低く見積もる。

2. **must-fix｜レンズ 2｜[草稿 §10・§13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/workload-description-critic-intervention-preregistration.md:327)、[起草 insight §5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md:88)、[docs/README.md の項](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/README.md:100)**
   **主張:** 追加の予備段を先に行い、結果を見て本走の要否・規模を決める。**根拠:** [逐語依頼](/work/1/SFC/tanab/tmp/t2852-p5-prereg-20260928/verbatim/request.md:3)は本題の草稿と見積りを求める。[段 4 裁定](/work/1/SFC/tanab/tmp/t2852-p5-prereg-20260928/s4-ruling.md:27)も予備段を未検査の親の追加と明記する。草稿 §10:340–341 は予備段の値で本走の規則を変えないとする一方、本走を行うか・規模をどうするかは値を見て決めるため、その選択規則が固定されていない。**推奨:** 今回の草稿・見積りから予備段と推奨を外す。残すなら別の探索的提案に分け、選択後の本走を無条件に計画した確認的実験として扱わない。D2272 項 2 は T-2850 の停止判断であり P5 を直接禁じないが、予備段はそこで挙がった S1 の分類力と node 費用を解消しない。
   **放置時の誤り:** 予備結果に応じた実施・規模の選択を、固定済みの事前登録による本走と誤認させる。

3. **should｜レンズ 2｜[起草 insight §3.4・§5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md:70)**
   **主張:** 予備段 45 回の「上限の目安」は直列約 10.9 時間、4 並列約 2.7 時間。**根拠:** [試走 v2 の `section8.json`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-v2-followup/section8.json)の 9,594.9 秒は系列全体の待ちの中央値であり、11 機会で割った値は coder 単独呼び出しの上限ではない。並列時の所要も未測定。**推奨:** 予備段を残す場合も「未測定の単純換算例」とし、「上限」と 4 並列の暦見込みを外す。

4. **should｜レンズ 2｜[草稿 §7.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/workload-description-critic-intervention-preregistration.md:207)**
   **主張:** 計画半幅が `ln(1.05)` を超えると、優越・退行・同等の分類は「ほとんど得られない」。**根拠:** [見積り JSON](/work/1/SFC/tanab/tmp/t2852-p5-prereg-20260928/estimate_p5.json)の半幅は効果の中心値を含まない感度計算である。半幅が大きくても十分大きな効果なら優越・退行に分類できる。**推奨:** 同等分類や小さい効果の識別が難しい、という範囲に表現を絞る。

5. **nit｜レンズ 1｜[起草 insight §2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md:30)**
   **主張:** `t2849_comparison_harness.py:444-446` が「評価 2 以降に critic 診断が無いと例外」を示す。**根拠:** 必須条件は[同ファイル 439–442 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/orchestrator/campaign/t2849_comparison_harness.py:439)。また、機構変更を拒否する文法の実行箇所は `p3_s4_loop.py:765-772,834-840` で、引用中の 879–906 行は拒否結果の組立てである。**推奨:** file:line を実際の判定箇所へ直す。

## 総括

§7.2 の費用・機会・半幅、69.9%・60.8%・約 2.8 倍、h(5) の差と暦の算術に不一致は見つかりませんでした。D2265・D2272・D2273・D2259・D2212 の項番号を伴う参照にも、結論を覆す食い違いはありません。critic 診断だけが現行の構造化失敗理由の返却経路であることと、S1 の受理候補で機構変更ができないことはコードと整合します。verifier・anomaly 即 reject・失敗理由返却を外す記述、留保条件を生成・選択に使う記述も見つかりませんでした。今回は指定資料の静的検査のみです。