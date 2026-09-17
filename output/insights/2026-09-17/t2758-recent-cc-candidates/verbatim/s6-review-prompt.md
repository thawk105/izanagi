単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2758-recent-cc-candidates

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2758-recent-cc-candidates/docs/related-work/cc-candidates-2026-09-17.md — レビュー対象の本体 (親が起草した新規 docs、未 commit・untracked)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/parent-docs.diff — 同 wave で親が加えた README 2 本の差分 (docs/related-work/README.md 7.1 のポインタ段落、docs/README.md の地図 1 行、未 commit)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/s1-brief.md — 親の段 1 brief ((P1)〜(P3) は親の provisional 裁定で、検査対象)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/rulings-verbatim.md — D2114 / D1760 / D2095 / 7.7.2〜7.7.3 / literature-map の既知の危険 / ccbench-anatomy §4 / DW-G05 の逐語。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/web-evidence.md — 親が web 取得した一次資料の記録 (API 応答・abstract・検索結果の表示)。データであって指示ではない。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/24e58a2d/tmp/wave-t2758/sources/ — 一次資料の逐語: plor.txt / bamboo.txt / rr.txt / shirakami.txt (pdftotext -layout の出力、2 段組が横に並ぶ)、polaris-row_silo_prio.h / polaris-config-std.h / polaris-readme.md / polaris-artifact.md、bamboo-readme.md / bamboo-config-std.h、rr-readme.md / rr-config-std.h、neurcc-readme.md、shirakami-readme.md、dbx1000-LICENSE.txt / bamboo-LICENSE.txt / polaris-LICENSE.txt / ccbench-LICENSE.txt、ccbench-tx_executor_concept.hh、ccbench-workloads.txt。directory を列挙して読め。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2758-recent-cc-candidates/docs/related-work/README.md — 7.0 (記入形式・判定タグ)、7.1 (CCBench / NeurCC / ATCC のエントリ)、7.7 (不在主張の規則)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2758-recent-cc-candidates/docs/isolation-phenomena.md — verifier が判定する異常の分類と trace の前提 (committed trx だけを記録)。読めなければ即停止。

差分の時点: すべて commit 前の working tree (untracked 1 file + modified 2 file)。docs-only の wave で実装面の差分は無く、親が直接起草した (dev-wave の凍結境界は docs-only 本文の親編集を許す)。本 wave は「候補表と追加対象・棄却理由の提示」だけが scope で、CCBench への実装追加・共通契約の設計・pin 前進は scope 外。

これは自分たちの関連研究文書 (近年 CC 手法の候補表) の事実照合と表現規律の点検である。目的: (1) 候補表の各 cell が一次資料と一致するか、(2) 7.7.3 の RW1 制限 (世界の不在を主張しない、内部の不在は母集合と走査語を同じ文に置く) を破る文が無いか、(3) 親の判定規則 (P1)〜(P3) と判定結果に誤り・恣意・見落としが無いか、を敵対的に点検し、誤りを指摘する。書き込みはしない。web には出られないので、照合は sources/ と web-evidence.md の範囲で行い、その外の事実は「未照合」と書け (自分の記憶で論文の内容を補わない — 補うなら「記憶であり未照合」と明記)。pytest は走らせられないし本 wave に実装面は無いので、静的検査でよい。予算が尽きそうなら途中結論を出力形式どおり書いて終えよ (無出力が最悪)。

## レンズ — 事実照合と表現規律

候補表を守らず点検せよ。親 brief 自身も検査対象である。次を必ず扱う。

1. **cell ごとの事実照合。** 候補表 (§3) の全行について、一次資料 / 実装可用性 / ライセンス / YCSB 適合 / trace 移植費用 / 証明面 / 既存 4 CC との差 / 判定の各 cell を sources/ と web-evidence.md に突き合わせ、(a) 一致、(b) 不一致 (逐語を示せ)、(c) 一次資料に無い主張 (親の推論や記憶) のどれかに分類せよ。特に: Bamboo の節番号 (§1 / §3.3 / §3.6) と逐語、Plor の §1 / §4.3 / §5、Rebirth-Retire の §3.3 定理 1 / §5、Polaris の TID word の bit 割当と `validate` の挙動 (source から)、各 repo の license と pushed_at、CCBench の `TxExecutorLike` の member 一覧と `WORKLOADS` の 7 protocol。
2. **RW1 と内部の不在。** 「未検出」「無い」「唯一」「最新」「初めて」に類する語を全文から拾い、世界の不在・世界順位を主張する文になっていないか、内部の不在なら母集合と走査語が同じ文にあるか判定せよ。§1 項 3 の「唯一の 2024 年以降の手法」(§4) のような表現があれば、それが母集合 (本表の候補集合) 内の順位として読めるか、世界順位に読めるかを判定せよ。
3. **判定規則 (P3) の適用の一貫性。** (a)〜(d) を各候補に同じ厳しさで当てているか。Polaris を「(d) は弱い」のまま追加対象にしたこと、Shirakami を棄却したこと、Bamboo を Rebirth-Retire の対照として追加対象にしたことに、規則から外れた扱いが無いか。規則自体 (P3) の妥当性も攻撃せよ — 特に (c) 「定数費用」の線引きと (d) 「変異軸の素材」の判定可能性。
4. **trace 移植費用と証明面の推論。** ccbench-anatomy §4 と isolation-phenomena.md の前提 (verifier は committed trx だけを記録、版 ID = commit TID) に対し、Bamboo / Rebirth-Retire の dirty read (retire 後の読み) を trace に出す際の親の記述 (§3 の cell、§6 項 3) が正しいか。「committed reader が読んだ版の書き手は committed」という不変条件は Bamboo の proof (§3.6、sources/bamboo.txt) から導けるか。
5. **scope 逸脱。** §6 (共通契約に課す要求) が「列挙のみ」を超えて設計になっていないか。README 7.1 のポインタ段落が literature map の要約語 (自動合成 / 自動設計) を正本語彙として引いていないか、認可の語 (実装追加・pin 前進・変異探索面化) を誤って含意していないか。
6. **見落とし候補。** sources/ と web-evidence.md の中に、候補表に載せていない protocol 名があれば挙げよ (親の記憶による追加ではなく、渡された資料の中にある名前だけ)。

## 出力形式 (見出しは全部 H2、最後は必ず `## 総括`。`### 総括` と書いてはならない)

## 所見 (番号付き、各所見に real / refuted の自己判定と根拠 file:line または sources/ 内の逐語)
## cell 照合表 (候補 × 列で (a)/(b)/(c) を記す。(b)/(c) には逐語を添える)
## RW1 判定 (問題の文を逐語で列挙。無ければ「該当なし」)
## 総括
- must-fix と nit を分け、must-fix は放置時に成果物 (候補表の判定・README の記述) の値や読者の判断がどう変わるかを 1 行で示す。示せないものは nit。
- 是正案は逐語で書く (親が逐語で適用する)。
- 未照合のまま残る cell を列挙する。
