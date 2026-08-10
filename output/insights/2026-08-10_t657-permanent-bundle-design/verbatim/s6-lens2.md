# 敵対レビュー結果

**判定: NO-GO。** 固定裁定 3 件は守られているが、上位設計が承認済みの下位 topology を破壊し、未裁定分岐を本文で先に固定している。

対象略称:

- 本体 = [calibration-freeze-authority-bundle-design.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md)
- 第1正本 = [freeze-permanent-design.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md)
- exact正本 = [freeze-permanent-design-s2.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design-s2.md)
- 一次資料 = [joint-generation design](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/calibration-freeze-joint-generation-design.md)
- 親裁定 = [s4-ruling.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s4-ruling.md)

## real

### REAL-1 — 下位 A と X を再結合しており、承認済み topology と機械的に両立しない

- **主張:** 本体 §5 の `A_f = 凍結側の承認 + 下位 pointer` は虚偽である。
- **根拠:** 本体 §5 は直前に「導入・承認・発効は別 commit」と認めながら、図では A と X を `A_f` に結合している。第1正本 §7-A/§7-X と exact正本 §S2-1.14 は、A を approval 1 ファイル、X を pointer 1 ファイルの別 commit と固定する。親裁定 J2 は G/A 分離だけを処理し、X_f を落としている。
- **壊れ方:** 本体どおりの A_f は `approval.commit-diff` と `pointer.x-commit` の双方に拒否される。下位正本どおり X_f を追加すると、本体の parent chain と「上位 X まで active pointer は不変」という説明が崩れる。
- **判定:** **real / must-fix**
- **成果物影響:** 下位 approval/pointer commit の受理集合が食い違い、正当な凍結 bundle から certified 選択へ到達する経路が空になる。

### REAL-2 — §12 Q2 を本文が既に裁定している

- **主張:** 上位 A/X の主体は未裁定ではない。本文が「人間」に固定済みである。
- **根拠:** 本体 §5 は A/X を「人間、`AI-Agent: none`、各1ファイル」と断定し、§10 段6も「人間による発効 X」とする。一方 §12 Q2 と親裁定 Q2 は、主体と A の意味を未確認としている。
- **壊れ方:** ユーザーが AI による X、または異なる承認形状を選んでも、既に書かれた topology と trailer 規則がそれを拒否する。親の「推奨」が実質的な裁定になっている。
- **判定:** **real / must-fix**
- **成果物影響:** 上位 approval と active pointer の受理 commit 集合、provenance 値、発効主体がユーザー裁定前に変わる。

### REAL-3 — 推奨される E-1 分岐は §5 により不可能

- **主張:** E-1 を開いた択一とする記述は虚偽である。
- **根拠:** 本体 §5 は上位 X を「1ファイル追加のみ」と固定するが、§6 E-1 は X に公式 activation record、literal 更新、上位 pointer の exact 3-path diff を要求する。親裁定 J12 は E-1/E-2 の双方を開くよう命じている。
- **壊れ方:** 1-path X では literal と公式 record が進まず、3-path X では §5 の形状規則に拒否される。両方を満たす X は存在しない。
- **判定:** **real / must-fix**
- **成果物影響:** E-1 の上位 X 受理集合が空になり、activation serial/state と authority pointer が同じ certified bundleを指せない。

### REAL-4 — `unresolved` profile が S2 分岐を閉じる

- **主張:** seal slot 自体ではなく、保証境界を無条件に profile 解決事項とした箇所が S2 を不可能にする。
- **根拠:** 一次資料 §6 と本体 §12 は G-a/G-b/G-c を「S1 の場合」に限る。本体 §8.2 は unresolved profile の X を拒否し、§10 段5は S1/S2 と G-a/G-b/G-c の双方を無条件に裁定済みにする。
- **壊れ方:** S2 を選ぶと、本来不要な G 選択が未解決のまま残って X が拒否されるか、意味のない G 値を捏造して profile を resolved にするしかない。
- **判定:** **real / must-fix**
- **成果物影響:** 正当な S2 seal を持つ権限束が X の受理集合から消え、対応する campaign・report が公式化できない。

### REAL-5 — 「下位 active pointer のみ」は親裁定 J3 の過剰一般化

- **主張:** raw generation record の直参照が危険であることから、「active pointer しか参照できない」は導けない。
- **根拠:** 本体 §7.2-1 と親裁定 J3。exact正本 §S2-4.2 と §S2-1.8 には、人間承認済みだが未発効の `ApprovedInactiveArtifact` が実在する。
- **壊れ方:** 人間承認を通った approved-inactive bundle まで拒否され、上位 B を作る前に下位 X_f を先行発効させることになる。その結果、下位権限だけが変わる中間 HEAD が必ず生じる。
- **判定:** **real / must-fix**
- **成果物影響:** 上位束が受理する freeze 成分の集合から approved-inactive bundle が除外され、active pointer の遷移順と certified authority の組が変わる。

### REAL-6 — bundle ID 必須化と「挙動保存」は同時に成立しない

- **主張:** §10 の受理集合不変条件は §7.2-3/§11 と矛盾する。
- **根拠:** 本体 §7.2-3 と §11 は bundle ID を持たない claim/report/receipt を公式拒否する。一方 §8.3、§9、一次資料 §8 は現行 receipt、campaign lock、verdict/report がその ID を持たないと認める。§10 段1/3は移行前後の受理・拒否集合の完全一致を要求する。
- **壊れ方:** 既存の bundle-less 成果物を拒否すれば受理集合が変わり、grandfathering や後付け推測で通せば §11 が偽になる。どちらの政策も §12 にない。
- **判定:** **real / must-fix**
- **成果物影響:** 既存 report・claim・投入 receipt・試行台帳の受理集合が移行境界で変わる。

### REAL-7 — 「freeze 四型を継承」は虚偽

- **主張:** 本体 §3 の状態型は下位正本を継承していない。
- **根拠:** 第1正本 §4 と exact正本 §S2-4.2 の四型は `candidate → registered-inactive → approved-inactive → active-official`。本体 §3 は `candidate` を落とし、代わりに `revoked/cancelled` を四つ目へ入れている。
- **壊れ方:** 未登録候補を表す型がなくなり、候補を registered として早期昇格させるか、候補 bundle を表現不能にする。revocation/cancellation も lifecycle 型と governance record のどちらか不明になる。
- **判定:** **real / must-fix**
- **成果物影響:** resolver の返却型、bundle registry の受理状態、revocation/cancellation 台帳の状態値が変わる。

### REAL-8 — 既存の U-A1 未裁定を「全問裁定済み」条件から落としている

- **主張:** 本体 §10 段0だけでは実装開始条件を満たさない。
- **根拠:** exact正本冒頭と §S2-11 は、approval の activation-window/lease をユーザー裁定 U-A1 として未解決にしている。本体 §10 は §12 の問いだけで段0完了とし、§5では下位 A_f/X_f を消費する。
- **壊れ方:** activation-window と lease では、発効後 expiry、use-time 再検査、19 consumer の伝播 schema が異なる。下位 active pointer の有効性を確定できないまま上位 A/X を設計したことになる。
- **判定:** **real / must-fix**
- **成果物影響:** 期限後の campaign/report の受理集合と、台帳の `validated_at` / `expires_at` 相当値が分岐する。

### REAL-9 — B の digest 束縛が §5 と §7.3 で食い違う

- **主張:** 権限束 identity の preimage が一意に定義されていない。
- **根拠:** 本体 §5 は「B と Q を digest preimage に入れる」と断定するが、§7.3 の「必ず入れるもの」には Q raw hash はあっても B の raw hash、path、commit identity のいずれもない。
- **壊れ方:** §5を読む実装は B を hash 成分にし、§7.3を読む実装は省く。同じ record 群から異なる bundle ID が生じるか、B の一部を差し替えても同じ ID が残る。
- **判定:** **real / must-fix**
- **成果物影響:** approval、claim、report、計算ノード receipt に記録される authority-bundle digest が実装ごとに変わる。

### REAL-10 — precedence が可変状態の文章に依存する

- **主張:** 第1正本の追記は安定した precedence 規則ではない。
- **根拠:** 追記は「上位層は起票済み・裁定待ち」「それまでは本書が現行契約」とする。`CLAUDE.md`「作業の進め方」6(a) は可変状態を worklog 末尾と現行 phase doc 以外へ再掲することを禁じる。上位 X の実在を判定する安定した path/schema は追記にない。
- **壊れ方:** 上位 X 後も凍結 design 文書が「裁定待ち」のままなら、直接読者は下位 resolver を production authority として使い続ける。
- **判定:** **real / must-fix**
- **成果物影響:** report が参照する authority が上位 bundle ID ではなく下位 pointer になり、未承認の環境×凍結直積が受理集合へ戻る。

### REAL-11 — 可変な現状説明を設計文書へ再掲している

- **主張:** 「可変状態を書かない」という本体冒頭の宣言は守られていない。
- **根拠:** 本体の状態行、§6 の「現在の head は literal」、§8.3/8.4 の現行 receipt/権限 object、§9 の現行 campaign lock・投入 script・job script の説明、docs/README の「裁定待ち」はすべて実装後に変わる。
- **壊れ方:** 移行後も「bundle ID がない」「固定 path を直接実行する」と読み取られ、完了済み層を未実装として再起票するか、逆に新 consumer の追加を見落とす。
- **判定:** **real / nit**

### REAL-12 — 参照と登録行に小さいが実在する破損がある

- **主張:** 全参照が一意という主張は成立しない。
- **根拠:** 第1正本追記の `§7-X` は実在する Markdown 見出しではなく、§7 内の太字ラベルである。本体の「2026-08-10 §58」は一次資料 path を示さない。docs/README の「freeze 族内部の設計は下2件」は、登録行より下に freeze 文書が1件しかない。
- **壊れ方:** `§7-X` の自動索引は失敗し、「下2件」を字義通り読むと無関係な次項まで freeze 正本に見える。
- **判定:** **real / nit**

## refuted

### REFUTED-1 — seal slot 自体は S1/S2 のどちらも排除しない

- **主張:** 「slot 自体を必須にしただけで S1 または S2 が不可能になる」は反証される。
- **根拠:** 一次資料 §6 は、S1 に旧予測 bytes への binding record、S2 に新 seal を要求する。本体 §8.1 はその二型を明示している。
- **壊れ方:** slot だけを理由にした破壊構成は作れない。実在する破損は REAL-4 の profile/G 条件である。
- **判定:** **refuted / nit（修正要求なし）**

### REFUTED-2 — 確定裁定 3 件の直接違反はない

- **主張:** pegasus G2、旧 branch、floor 復元についての直接違反は構成できない。
- **根拠:** 本体 §3 は G2 を `registered-inactive` に維持し、§14 は merge/cherry-pick を禁じ再導出だけを許し、§15 は repo 書き戻し不要・ユーザー確認のみとする。一次資料 §7/§11、restore protocol §§4–5、ユーザー裁定 §58 と一致する。
- **壊れ方:** 設計段だけで G2 を活性化する、旧 commit を main に運ぶ、AI が floor を書き戻す経路はいずれも本文にない。
- **判定:** **refuted / nit（修正要求なし）**

### REFUTED-3 — R1..R16 本文は物理的には変更されていない

- **主張:** 追記が既存条文を直接編集したという疑いは反証される。
- **根拠:** 差分は冒頭の「適用範囲」7行追加だけで、R1..R16 本文に変更はない。
- **壊れ方:** 条文 bytes の変更構成は存在しない。ただし意味上の上書きは REAL-1、REAL-7、REAL-10 に残る。
- **判定:** **refuted / nit（修正要求なし）**

### REFUTED-4 — 現 serial/hash/commit literal と docs 間の行番号参照はない

- **主張:** 本体が現在値を literal 再掲したという強い疑いは反証される。
- **根拠:** 本体は activation serial、artifact hash、現 commit OID を値として記載していない。docs 間参照も節名であり、source line number は使っていない。
- **壊れ方:** literal 値の陳腐化や行挿入による直接参照ずれは構成できない。REAL-11 の一般的な現状記述は別問題である。
- **判定:** **refuted / nit（修正要求なし）**

### REFUTED-5 — 明示された path と主要節名は実在する

- **主張:** 本体が参照する文書 path の不存在は反証される。
- **根拠:** worklog、orchestrator design、両 freeze 正本、二つの insight はすべて実在する。exact正本の bundle digest は §S2-2、W-d consumer registry は §S2-8.2、restore protocol §§4–5 も一意に存在する。
- **壊れ方:** path-not-found や同名見出しの複数一致は構成できない。REAL-12 の `§7-X` と無 path の §58 は例外である。
- **判定:** **refuted / nit（修正要求なし）**

### REFUTED-6 — 下位 R13/R14/R15 は上位 Q2/Q3 を既に裁定していない

- **主張:** 上位 A/X と上位 lockstep が既存承認済みだから Q2/Q3 は不要、という反論は成立しない。
- **根拠:** 第1正本 §11 の R13/R14 は freeze-family の X/A、R15 は3 freeze family内部の lockstep に限定される。上位の環境×凍結 bundle は別 authority domain である。
- **壊れ方:** 下位裁定だけから上位の実行主体、承認意味、rollback/revocation を一意に導出できない。
- **判定:** **refuted / nit（修正要求なし）**

## 総括

最も重い指摘は次の3件である。

1. **REAL-1:** 下位 approval A と発効 X の再結合。承認済み exact checker が本体の A_f を必ず拒否する。
2. **REAL-2/3:** 上位 X は「未裁定」でありながら人間・1ファイルに固定され、推奨 E-1 の3-path X と両立しない。
3. **REAL-4:** S2 に不要な G-a/G-b/G-c を resolved profile の条件にし、S2 の発効集合を空にする。

**NO-GO。** このままでは「裁定待ちの第1設計段」としても択一を正しく保存しておらず、下位正本どおりに実装しても本体どおりに実装しても、approval・active pointer・bundle digest・report の少なくとも一つが異なる。