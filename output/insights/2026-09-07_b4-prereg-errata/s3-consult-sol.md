### 所見 1: P1 の列挙は漏れており、§11.2 だけを適用先とする根拠にならない

- 分類: real
- 根拠: 親は [brief.md:21](/home/SFC/tanab/.claude/jobs/71fa9723/tmp/codex/brief.md:21) で「§5 に標本数の行も 59 も無い」として §11.2 だけを直す。しかし現物では、§5 の `n = 201` は B-4 本体の block 数であり、floor window の標本数とは別概念である ([prereg:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:160)、[prereg:398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:398))。floor 標本数概念は §11.1 の「途中の値を見て標本数や campaign 数を変えない」([prereg:941](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:941))、割り当て表の「標本数・campaign 数・時間窓の分離」([prereg:961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:961))、§11.2 の標本数・費用 ([prereg:1001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:1001))、§11.3 の未決一覧 ([prereg:1045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:1045)) にある。§6 には値は無い。数値トークン `59` は 1003、1009、1010 行だけだが、概念上の参照はそれより多い。
- 影響: §11.2 の費用だけ直すと、D1695 の決定値が規範を置く §5/§5.1 に現れず、§11.1・§11.3では未決のまま残る。
- 提案: P1 をそのまま採用しない。§5 表へ行を足さない場合でも、§5.1 の floor 解除条件へ D1695 の dated erratum を追記し、§11.1–11.3を同時に整合させる。

### 所見 2: §5 表への新規行追加は自然な字義解釈だが、現行 admission 契約を壊す

- 分類: real
- 根拠: D1695 は「B-4 事前登録 §5 の『window ごとの標本数』」と明記する ([decisions:51680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:51680))。ところが §5 表にその行は無い。一方、production admission は `_SECTION5_LABELS` を exact 10 項目に固定し ([p3_b4_admission_record.py:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/orchestrator/campaign/p3_b4_admission_record.py:77))、表行数を `len(_SECTION5_LABELS) + 2`、label 集合を exact 一致で検査する ([p3_b4_admission_record.py:645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/orchestrator/campaign/p3_b4_admission_record.py:645)、[p3_b4_admission_record.py:665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/orchestrator/campaign/p3_b4_admission_record.py:665))。本文も「10 欄のうち 1 欄」と自己記述する ([prereg:903](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:903))。
- 影響: §5 に専用行を新設すると、実走前 admission が必ず赤になり、docs-only・実装差分ゼロという所有範囲が崩れる。
- 提案: 推奨は、固定表を変えず §5.1 の floor 項 ([prereg:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:216)) に `n = 62` の規範追記を置くこと。専用行が必要という裁定なら、admission と二つの test fixture を含む別の実装 wave に拡張する必要がある。

### 所見 3: P2 の「必要最小標本数 59」は正しく、62 へ置換してはならない

- 分類: refuted
- 根拠: 現文は「95 パーセンタイルを信頼度 95% で覆うには標本 59 個」と書く ([prereg:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:1002))。標本最大値 \(M_n\) について \(P(M_n \ge q_{0.95})=1-0.95^n\)。したがって \(n\ge\lceil\log(0.05)/\log(0.95)\rceil=59\)。実値は n=58 で 0.948953、n=59 で 0.951505、n=62 で 0.958422 である。D1695 自身も「標本 59 個が要る」と維持している ([decisions:51686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:51686))。
- 影響: 1003 行を「62 個が要る」とすると、必要最小数について偽の統計的主張になる。
- 提案: 1002–1004 行は不変とし、統計上の最小数 59 と、欠測余裕込みの採用計画値 62 を明確に分離する。

### 所見 4: 62 に伴う費用値を旧 session 構造のまま一般化する計画は D1699 と衝突する

- 分類: real
- 根拠: 親は n、合計数、session 数、秒数を更新対象にする ([brief.md:16](/home/SFC/tanab/.claude/jobs/71fa9723/tmp/codex/brief.md:16))。旧文の算数なら n=62、2 campaign 合計124、候補側248 session、3,720秒、別 reference 124 session、1,860秒となる。しかし D1699 は「candidate と reference を 1 つの低水準 session で測る形へ設計を直す」と決定した ([decisions:51763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:51763))。現文1011行の「参照点を対ごとに測るなら、さらに118セッション」は別 session 構造を前提にしている ([prereg:1011](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:1011))。
- 影響: 118→124、1,770→1,860という機械置換をすると、既裁定の新 session 構造に対して偽の費用見積りを固定する。
- 提案: D1699 の adapted spec で「1 session」の測定回数と時間を確定するまで、費用は旧構造に対する条件付き参考値と明記するか、確定不能として数値更新を保留する。

### 所見 5: P3 の canonical decisions を直接編集しない判断は妥当である

- 分類: refuted
- 根拠: DW-S07 は「worklog / decisions / failures の3台帳は直接編集せず」fragment と fold を要求する ([core.md:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/dev-wave/core.md:102))。spool 契約も「canonical の既存 bytes は不変」とする ([spool/README.md:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/spool/README.md:116))。D1646 は D1593/D1618の本文を編集せず、新しい D1646 内で「本決定をもって D1593 / D1618 へ追記で訂正する」とした ([decisions:50508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:50508))。D1694も同じ方式を明記する ([decisions:51663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:51663))。
- 影響: D1641 を直接変えると、裁定時点の記録を遡及改変し、規律7と spool 不変条件を破る。
- 提案: D1694/D1695が既に canonical へ land 済みなので、今回 decisions.md は触らない。新しい設計択一が生じた場合だけ別 D を裁定へ返す。

### 所見 6: 「pin は §5.1.1 の2 hash だけ」という pin 閉包は不完全である

- 分類: real
- 根拠: §5.1.1 の raw/semantic hash pin は実在する ([consumer:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47)、[consumer:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:404))。それに加えて、§5 表の exact 10行・label集合 pin がある。また admission 発行後は、宣言した commit の全文 document sha256を検査し、HEAD の document bytes と完全一致させる ([p3_b4_admission_record.py:770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/orchestrator/campaign/p3_b4_admission_record.py:770))。現時点では3つの admission record はすべて不存在だったため、現在の旧 bytes を束縛する発行済み全文 pin は無い。現 blob `f2ac31d0…` と sha256 `cf8a3d0f…` の静的 repo hit 0 は確認できた。
- 影響: §11.2だけの編集は現在の pin を壊さないが、§5表の新規行は即 admission 赤、admission 発行後の文書編集は全文 binding 赤になる。
- 提案: pin 閉包を「現行静的全文hashなし／§5.1.1 hash pinあり／§5 exact表形状あり／将来のadmission全文bindingあり」と訂正する。

### 所見 7: n=62 は受理集合を広げるが、その変化自体は D1695 の明示範囲内である

- 分類: refuted
- 根拠: driver は campaign ごとに `planned = sample_count * pair_count` を作り、欠測率が `max_dropped_fraction` 以下なら受理する ([floor_pair_driver.py:2489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/orchestrator/campaign/floor_pair_driver.py:2489))。1 pairなら n=59 は2件まで、n=62は3件までを受理する。これは受理集合の実変化であるが、D1695 は n=62と5%規則の維持を同時に明示し、3件欠測を意図している ([decisions:51680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:51680)、[decisions:51689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:51689))。
- 影響: raw dropout pattern の受理集合は広がるが、5%という割合ゲートは緩まず、ユーザー裁定を超えた変更ではない。
- 提案: 「ゲート不変」だけでなく「離散境界は2件から3件へ変わる」と記録する。driver は spec の `sample_count` を読むため、固定数を書き換える実装変更は不要。

### 所見 8: 親の「3件落ちても59残る」という一般化は複数 pair の campaign では成立しない

- 分類: real
- 根拠: 親は [brief.md:50](/home/SFC/tanab/.claude/jobs/71fa9723/tmp/codex/brief.md:50) で「3件落ちても59残る」を設計意図とする。しかし5%判定は window 内の pair 合算であり、pair別には閾値を掛けない ([decisions:51727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:51727))。driver も campaign 合算後、pair別には retained 件数を報告するだけである ([floor_pair_driver.py:2490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/orchestrator/campaign/floor_pair_driver.py:2490)、[floor_pair_driver.py:2498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/orchestrator/campaign/floor_pair_driver.py:2498))。3 pairなら planned=186、9件欠測まで通り、9件が1 pairへ偏ればその stratum は53件しか残らない。driver自身も「残存標本で95%被覆を保つことを証明しない」と明記する ([floor_pair_driver.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/orchestrator/campaign/floor_pair_driver.py:74))。
- 影響: n=62を「各 stratum が59件残る」「全セルで95%被覆」と一般化すると偽になる。
- 提案: D1695の理由を保証として再掲せず、1 pairの場合の算数または campaign合算の動機に限定する。D1696/D1697に反する pair別 gate は追加しない。

### 所見 9: §11.2 の2箇所だけでは、D1694/D1695後も文書が「未裁定」と「未決」を主張し続ける

- 分類: real
- 根拠: §11冒頭は「本節は裁定されていない」と断言する ([prereg:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:877))。§11.2も「実際の数はユーザーが決める」とする ([prereg:1005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:1005))。§11.3は標本数をユーザー手番、driver新設を未決として残す ([prereg:1045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:1045))。対してD1641は12項目を採用済み ([decisions:50331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:50331))、D1694は新設を適合と読む ([decisions:51664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:51664))、D1695は標本数を決定済みである。
- 影響: 読み手は n=62とdriver適合を未決と誤認し、再裁定や重複実装を始めうる。
- 提案: 過去の案を消さず、§11冒頭に D1641/D1694/D1695 の dated status overlay を追記する。§11.1表の標本数行、§11.2の採用値、§11.3の未決一覧も同じ追記に整合させる。

### 所見 10: doc 冒頭と §6 の変更は不要である

- 分類: refuted
- 根拠: 冒頭状態は「§5の数値欄が埋まり、§6の前提条件がすべて充足し、その版がcommitされるまで発効しない」とする ([prereg:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:34))。§5にはなお複数の `未記入` がある ([prereg:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:159))。§6は全欄記入とfloor成果物を要求するだけで、window標本数の値を持たない ([prereg:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:593)、[prereg:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:643))。
- 影響: 冒頭状態を進めると、未発効の文書を発効に近い状態と誤表示する。§6へ数値を重複すると正本が増える。
- 提案: 冒頭の発効前状態と§6は変更しない。

### 所見 11: §10 には実在する別の stale 現在地があるが、D1694/D1695の適用とは分けて扱うべきである

- 分類: real
- 根拠: §10は「§5.1 (i) の先行 freeze と人間の指名」が残り、「対象 driver と軸」の欄は埋められないとする ([prereg:804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:804)、[prereg:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:813))。しかし§5の現物は base を選択・記入済みである ([prereg:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:158))。§10末尾も「対象driverと軸の選定そのもの」を未了に残す ([prereg:855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/phase3-b4-reflux-ablation-preregistration.md:855))。
- 影響: 発効条件の現在地を誤って1段階後退させるが、n=62やD1694の意味自体は変えない。
- 提案: 仮想リスクではなく具体的な stale fact なので、段4で「同じ局所docs訂正に含める」か「別の最小erratumへ送る」かを明示裁定する。gate・台帳の一般化へ広げない。

### 所見 12: 新しい validator・pair別 gate・台帳を足さない親の制約は正しい

- 分類: refuted
- 根拠: D1696は exact 2 window・標本数などの未検査項目を人手レビュー責任のまま置き、「validatorを拡張する案は採らない」と決定する ([decisions:51702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:51702))。D1697もpair別閾値を明示的に不採用としている ([decisions:51739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-prereg-errata-20260907/docs/decisions.md:51739))。
- 影響: 補助gateを足すと受理集合を狭め、確定済み裁定と「書きすぎ禁止」を破る。
- 提案: 今 wave は文書上の規範・現在地・参照整合だけに留め、実装・検査・台帳は増やさない。

## 総括

P2とP3は成立する。1003行の統計的最小数59は維持し、D1641本文も直接編集してはならない。

一方、P1とpin閉包、費用値の一般化は成立しない。特に次の3点が plan v2 の必須修正である。

- D1695を§11.2の費用だけに閉じず、規範側の§5.1と§11.1–11.3へ dated erratum として反映する。
- §5表への新規行は exact表形状pinを壊すため、行追加を避けるか、実装scope拡張を改めて裁定する。
- D1699後のsession構造が確定するまで、旧構造由来のsession数・秒数を新しい「事実」として固定しない。

n=62は5%ゲートの離散受理境界を広げるが、これはD1695の明示範囲内である。ただし複数pairでは「3件落ちても各stratumに59件残る」は成り立たず、95%被覆の一般保証を追記してはならない。ファイル変更・テスト実行・git状態変更は行っていない。