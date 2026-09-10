### 所見

1. **検査 1 — 不整合あり**

   - **対象:** plan、文書
   - **不整合の内容:** 残る義務は「適合確認の責任」だけだが、確認の時点、照合行為、確認結果の記録を要求していない。同一人物が記入者・レビュー者の名前を書くだけでも、確認を行った場合と文書上区別できない。plan 自身も「独立した証拠や別主体の視点は得られない」と認めている。
   - **根拠:** plan は「レビュー者は、記入内容が事前登録の要求を満たすことを確認する責任を負う」とする一方、観測可能な行為を定めていない（[s2-plan.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s2-plan.md:29)）。また「同一 identity による確認なので、責任は定義される一方、独立した証拠や別主体の視点は得られない」（[s2-plan.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s2-plan.md:51)）。D1266 の問題意識は「定義せずに兼任だけ書くと、後から恒真な保証と読まれる」である（[verbatim-d1266.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/verbatim-d1266.md:9)）が、現在案は役割の履行について同じ問題を残す。
   - **放置した場合の影響:** レビュー行為の記録がない先行 freeze commit まで受理集合に入りうる。「対象 driver と軸」を後で埋められる commit の集合が広がる。直ちに数値は変わらないが、実験を事前登録済みとして受理する集合が変わる。

2. **検査 2 — 不整合あり**

   - **対象:** plan、文書
   - **不整合の内容:** 「記入内容」は直前の 6 項目と読めるが、「事前登録の要求」の指し先は一意でない。§5.1 (i) の先行 freeze 要求だけなのか、§0 の記入規約、§1 の発効条件、§5.1 全体、または文書全体なのかを文面から確定できない。
   - **根拠:** plan は「責任対象は一意」と断定する（[s2-plan.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s2-plan.md:33)）。しかし文書には、例えば「本書が定める規範は §5.1 と §7 に置き」（[phase3-b4-reflux-ablation-preregistration.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/docs/phase3-b4-reflux-ablation-preregistration.md:42)）や、全欄を実走前に commit する要求（[同文書](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/docs/phase3-b4-reflux-ablation-preregistration.md:52)）など多数の「事前登録の要求」がある。
   - **放置した場合の影響:** 6 項目の存在だけを確認した commitと、形式・時点・先行 freeze まで照合した commitのどちらを受理するかが読み手ごとに変わる。受理集合に直接影響する。

3. **検査 3 — 不整合あり**

   - **対象:** 文書、plan
   - **不整合の内容:** §0、§1、§5.1 の「実行責任者」「env_tag」とは衝突しない。しかし §10 は指名後に事実上古くなる。
   - **根拠:** §10 は現在形で「残るのは §5.1 (i) の先行 freeze — …記入者とレビュー者 — であり、人間の指名を含むため AI が確定できない」とする（[同文書](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/docs/phase3-b4-reflux-ablation-preregistration.md:759)）。両者を `thawk105` と固定した後は、両者は残件でも指名不能事項でもない。plan も「部分的に古く見える」と認識しながら変更しない（[s2-plan.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s2-plan.md:46)）。
   - **扱い:** §10 の残件列挙を未固定の 4 項目だけにし、「人間の指名を含むため」という原因節を削る必要がある。scope がそれを許さないなら、文書内不整合を残す plan は採らない。
   - **放置した場合の影響:** §10 を正本として読む後続作業が、指名を未了と判定したり再指名を要求したりする。残件参照と発効可否の判断が変わる。

4. **検査 4 — 不整合なし**

   - **対象:** plan、文書
   - **根拠:** §5 の値は引き続き「対象 driver と軸｜未記入」である（[同文書](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/docs/phase3-b4-reflux-ablation-preregistration.md:158)）。また後続文は「CLI の実在は (i) を充足せず」「候補集合・各 exact command・証拠 path と hash・0 件／複数件の決定規則・記入者・レビュー者を…freeze しない限り、対象 driver と軸を記入しない」と明記する（[同文書](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/docs/phase3-b4-reflux-ablation-preregistration.md:184)）。plan も残り 4 項目を未固定と明記している（[s2-plan.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s2-plan.md:41)）。
   - **放置した場合の影響:** なし。末尾 2 項目の指名だけで、(i) の充足や対象欄の記入権限を先取りする読みにはならない。

5. **検査 5 — 不整合なし**

   - **対象:** plan、文書
   - **根拠:** 変更案は確認責任を定義するだけで、免除・承認による代替・規範変更の権限をレビュー者へ与えていない。§4 の「アームによって verifier policy・受理集合・再試行・校正値を変えた block は protocol violation」（[同文書](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/docs/phase3-b4-reflux-ablation-preregistration.md:143)）、§5.1 (ii) の outcome 非生成 probe 制約（[同文書](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/docs/phase3-b4-reflux-ablation-preregistration.md:174)）、§7 の全件報告（[同文書](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1769-b4-reviewer-role/docs/phase3-b4-reflux-ablation-preregistration.md:603)）はいずれも残る。
   - **放置した場合の影響:** これらのゲートの値・受理集合は変わらない。ただし所見 2 の曖昧さは別途解消すべきである。

6. **検査 6・P1 — 不整合なし**

   - **対象:** brief
   - **根拠:** P1 の「同じ bullet 内に置く」という配置判断（[s1-brief.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s1-brief.md:56)）は、役割が §5.1 (i) のレビュー者だけに適用されることを示す最小配置として妥当である。
   - **放置した場合の影響:** 配置自体による値・受理集合・参照の変化はない。ただし配置だけでは所見 1、2 の意味上の欠陥を解消しない。

7. **検査 6・P2 と scope — 不整合あり**

   - **対象:** brief、plan
   - **不整合の内容:** P2 は、歴史的に「AI が指名したのではない」ことと、§10 が現在の未了事項を正しく列挙していることを混同している。また scope の切り方が、変更によって必然的に古くなる §10 の同期を落としている。
   - **根拠:** brief は「『人間の指名を含むため AI が確定できない』は本変更後も真のまま残せる」とする（[s1-brief.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s1-brief.md:58)）。しかし §10 は由来の説明ではなく、「本書が閉じないこと」の現在地である。brief の「本題の記入と役割定義文だけ」という scope（[s1-brief.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s1-brief.md:16)）を機械的に適用すると、この矛盾を意図的に残す。
   - **放置した場合の影響:** §10 の残件集合と実際の残件集合が食い違い、後続作業の発効判定・再指名判断が変わる。

8. **検査 6・実測節 — 不整合あり。ただし事実が偽とまでは判定不能**

   - **対象:** brief
   - **不整合の内容:** 「only」「1 件も存在しない」「D1266 以外の裁定は無い」という全称・不存在の結論に対し、指定資料には exact command、探索範囲、出力がない。特に「記入者」「レビュー者」だけの主題検索では、「独立検査者」「確認責任者」「同一 identity」「兼任」など別語の裁定を排除できない。
   - **根拠:** brief は「bytes を機械が pin しているのは §5.1.1 だけ」（[s1-brief.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s1-brief.md:65)）、「admission record は repo に 1 件も存在しない」（[s1-brief.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s1-brief.md:70)）、「D1266 以外の裁定は無く」（[s1-brief.md](/home/SFC/tanab/.claude/jobs/e76c0c8f/tmp/wave-artifacts/t1769-b4-reviewer-role/s1-brief.md:72)）とするが、再検証可能な実測記録を示していない。
   - **放置した場合の影響:** 未列挙 consumer があれば hash・参照整合性の受理が変わり、見落とした裁定があればレビュー者の受理集合が変わる。これは nit ではなく、brief の根拠強度に関する material な所見である。

### 文面の対案

所見 1、2を同時に解消する、役割定義文だけの置換案は次のとおり。

```text
レビュー者は独立検査者ではない。記入者としての記入とは別に、(i) に列挙した 6 項目を本項の先行 freeze 要求と照合し、全項目を満たすと確認した事実を当該先行 freeze commit に記録する責任者である。記入者との同一 identity を許し、独立性を要求しない。
```

### 総括

現 plan はそのまま採らない。  
役割定義を上の文面へ直し、確認対象と観測可能な履行を明記する必要がある。  
さらに §10 の残件列挙から記入者・レビュー者と、古くなる原因節を同期して除く。  
末尾 2 項目だけの固定は (i) の充足を先取りせず、正しさゲートも緩めない。  
brief の全称的な実測結論は、再検証可能な根拠がないため確定事実として扱わない。  
検査は指定 4 ファイルの静的読解のみで、テストは実走していない。