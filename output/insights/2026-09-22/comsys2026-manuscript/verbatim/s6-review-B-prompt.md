単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-comsys2026-manuscript

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 依頼文の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-comsys2026-manuscript/verbatim-request.md
- 親 brief (P1〜P6 は親の provisional 裁定で攻撃対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-comsys2026-manuscript/s1-brief.md
- 原稿の骨格と下書きの規則: 同 job dir の `manuscript-plan.md`・`drafter-rules.md`
- レビュー対象 (投入先 worktree の path、read-only、commit `d18b073abe2d8957c26827cd062d2e4a5e6cbcec`): `output/insights/2026-09-22/comsys2026-manuscript/manuscript.tex`
  (本文に内部 ID を出さず、出所は各段落直後の LaTeX コメント `% 出所: …` にある)。組版済み PDF は同 dir の `manuscript.pdf` (14 頁) — PDF は読めなくてよい、tex で判定せよ。
- 正本 (版): `docs/paper-story/2026-09-22.md` の §6 (言えること / 言えないこと)・§7 (過大主張チェックリスト、133 項)・§3 (新規性の主張)・§4 (図の使用条件)。
  §7 の原稿向け要約 (索引、正本ではない): job dir の `checklist-condensed.md` (統合規則 40 条・必ず書く限定 39 項)。
- 素材の草稿 (原稿はこれらを圧縮・統合した): `output/insights/2026-09-20/paper-intro-ja/{intro,contributions}.md`、`output/insights/2026-09-21/paper-methods-ja/{methods,implementation,README}.md`、
  `output/insights/2026-09-21/paper-results-ja-b/results-discussion.md`、`output/insights/2026-09-21/paper-abstract-conclusion-ja-b/{abstract,conclusion}.md`、`output/insights/2026-09-20/paper-related-work-ja/related-work.md`、
  `output/insights/2026-09-21/paper-intro-ja/limitations.md`。
- 図のキャプションの正本: `docs/paper-story/figures/README.md` の fig2b・fig4・fig9・fig14・fig15 節の「キャプション正文」(英文または和文)。
- 書誌の出所 (job dir の `bibsrc/`): `arxiv-summary.tsv` (arXiv API の取得結果)、`nonarxiv-summary.txt`・`venue-summary.txt` と `crossref-*.json` (Crossref)。
- 数値照合の親の実測: job dir の `numcheck-1.log` (本文の数値 118 token が草稿・一次資料に逐語で存在)。

## 前置き — これは自分たちの研究論文原稿のレビューである

研究用 repo (トランザクションの並行性制御を LLM で合成する研究) の、国内シンポジウム ComSys 2026 (情報処理学会の研究報告の書式、査読なし) へ出す日本語原稿を、書いた後に敵対的に点検してもらう。
セキュリティ製品でも攻撃ツールでもない。あなたは read-only のレビュー役で、書込可能な tmp は無いので静的な読解と grep でよい。組版やテストは走らせない。
**親の brief・原稿の骨格・親の実測 (数値照合・書誌取得) も点検対象である。** 攻撃が成立しなかった項目は正直に「不成立」と書け。全項目を無理に成立させるな。

## レンズ — 過大主張・限定の脱落・事実の取り違え・読者への誤導

所見ごとに real / refuted の見込み・重大度 (must-fix / should / nit)・根拠 (原稿の行番号と、正本・草稿・一次資料の file と見出し)・放置時に読者が何を誤って信じるかを 1 行で書く。

1. **過大主張:** 原稿の各主張が版の §6「言えること」の範囲に収まるか。§7 の禁止句・禁止された言い換え (例: 再現した、勝った / 有意 を status や記述的な札に使う、認可を実施と書く、設計を実装と書く、certified を性能の認証と読める文、
   位置づけの 1 文の 3 条件を落とした短縮形、優先権・世界初・系譜の序数、backoff の機構の新しさ) に当たる文が無いか。否定文・逐語引用の中の語は違反ではない。
2. **限定の脱落:** 要約で主張だけが残り、同じ文か直後の文にあるべき限定 (certified の保証範囲、非認証 lane の地位、旧環境の記述性と分母、3 走行の独立、同一候補測定の 4 語、B-8 型の 30 枠の内訳 (本走 24 + 校正の完走 6)、
   S-1a の不成立と S-1b の結果既知の追試、MOCC の非 certifying・非有意は同等性でない、TPC-C / 関数単位の軸 / 生成器対照 / 同一 job 対照が未実施) が落ちていないか。
3. **事実の取り違え:** 草稿・一次資料と比べて、数値・条件・母集合・帰属 (どの実験のどの値か)・時点 (「本稿の時点」と起点) を取り違えていないか。特に、採用した静的 backoff の検証相と、合成軸の最終候補の長時間検証の対象の取り違え、
   +55.5〜+98.4% (S-1a の対 sort 最良) と S-1b の値の取り違え、A-1 の 2 attempt の値と breach の取り違え。
4. **図:** 各図のキャプションが英文キャプション正文の限定を落としていないか。fig9 と fig14 を並べて比較させる書き方になっていないか。fig4 の画像に焼き込まれた内部名の扱い。旧 fig2・fig5 を使っていないか。
5. **関連研究と書誌:** 書誌 27 件の著者・題目・会場・巻号・頁・年が bibsrc の取得値と一致するか。Polyjuice §4.5 と ADRS の書き方が出所 (`output/insights/2026-09-21/vldb-direction/gap-analysis.md` §2、`docs/decisions.md` D2212 の理由欄) を超えていないか。
   位置づけの 1 文が関連研究草稿 §2.1 の逐語 (括弧書き・句点まで) か。
6. **brief の P1〜P5:** 頁数 (本文 13 + 参考文献 1 = 14 頁で、P1 の目標 13 頁を 1 頁超えた)、枠組み (VLDB 方針を書かず今後の課題に TPC-C・関数単位の軸)、原稿の正本を tex 1 本にしてスタイルを repo に入れない判断、
   図の選択、著者欄の差し込み、は妥当か。原稿として読者 (システム系の研究者) に通じない内部語 (lane、attempt、campaign、protocol の status 名など) が説明なしに残っていないか。

## 出力形式

- 見出しは `#` 1 段だけを使い、`##` は最後の `## 総括` のみ。`### 総括` と書いてはならない。
- 実行できない検査は「未実走・静的読解」と明記する。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- **出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。
- 末尾に `## 総括`: GO / NO-GO、must-fix / should / nit の一覧 (各 1 行、根拠は原稿の行番号と正本・一次資料)、各 must-fix の最小修正案 (置き換え後の文面を 1 つ添える)。
