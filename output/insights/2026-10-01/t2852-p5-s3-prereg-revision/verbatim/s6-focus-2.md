静的読取と再集計によるレビューです。書込み・テスト実行・委任・禁止された本走結果の閲覧は行っていません。

## 1. F1〜F4 の対応表

参照：[草稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/workload-description-critic-intervention-preregistration.md)、[改版 insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/output/insights/2026-10-01/t2852-p5-s3-prereg-revision/README.md)。

| 所見 | 判定 | 根拠 |
|---|---|---|
| F1 履歴への拒否・digest の接続範囲 | **closed** | 草稿 §3.2 が「auditor の通常の判定…分類つきで履歴に入る」と区別。§13(2) は「初期点を含む評価の結果」と不足する拒否分類を修復対象に限定。元の must-fix は解消。subtype の列挙には後述の nit が残る。 |
| F2 集計から本走全体への過大な推論 | **partial** | insight §2 の「本走全体の失敗の有無は、この集計では確かめていない」は適切。ただし新しい説明「各系列の最後の評価は現れない」に反例がある。後述 N1。 |
| F3 「0件」の範囲 | **closed** | insight §2 は「critic prompt と coder 入力の固定部分だけ」に限定し、診断の自由文は「0 件ではない」と明記。§7 も「確認した固定の入力」に限定。 |
| F4 発効束の6 cell | **closed** | 草稿 §14 は「規模 (4 cell、確定した n)」。§3.3 の「本書の対比・確認事項には入れない」と一致。 |

**closed 3、partial 1、regressed・not-addressed 0。**

前巡で closed だった9件も維持されています。

| 前巡の所見 | 判定 | 現行の根拠 |
|---|---|---|
| A-2・B-1：K と骨格の定義 | closed ×2 | §9.3「K_本文」「K_骨格」、「整数型…の定数」、§12 U8 の C++ 方策に関する限界。 |
| A-3・B-2：露出の同一性 | closed ×2 | §3.4「baseline…系列ごとに測る値」「critic…ありの cell だけ」「偏らせないとは言えない」。 |
| A-5：参照 job の換算 | closed | §7.2「独立に導いた値とは扱わない」。 |
| A-6：丸め | closed | §7.2「0.0275」。再計算も一致。 |
| B-4：fallback・固定 δ | closed | §6「fallback を含む運用 score」「生成の力が同等だという意味ではない」。 |
| B-5：最初の提案・欠測 | closed | §8(1)「(i) または (ii)」「読み取れる IR が無ければ欠測」。 |
| B-6：地図の「族3」 | closed | [docs 地図](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/README.md:103) は「3 対比の Bonferroni 同時区間」。 |

## 2. 拒否経路・量化・fragment の照合

**F1 の意味上の分類は一致します。** 履歴に入らない拒否の subtype をコード上で列挙すると、次の **5種類**です。

| 経路 | subtype | 自系列履歴 |
|---|---|---|
| `check`・`finalize` → `_schema_reject` | `coder-schema`（`invalid-json`／`invalid-schema`） | 入らない |
| `finalize` → `_schema_reject` | `auditor-schema`（同上） | 入らない |
| driver の proposal 読込失敗 → `_record_preview_reject` | `proposal-schema` | 入らない |
| auditor の機械的整合性エラー → 同上 | `auditor-gate`・`auditor-digest` | 入らない |
| preview の検疫・描画後の構文・compile 拒否 → `--record-reject` | 検疫の subtype・`policy-grammar`・`policy-compile` | 分類つきで入る |
| auditor の通常の veto → 同上 | `auditor-violation`・`auditor-uncertain` | 分類つきで入る |

根拠は [round tool](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/tools/silo_policy_contrast_round.py:51) の全拒否分岐と、[driver の記録経路](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/orchestrator/campaign/p3_s4_loop_policy.py:665)です。[auditor gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/orchestrator/campaign/auditor_gate.py:194) が通常判定から生成する subtype は上記2種類で、`pass` は拒否を生成しません。

補足：

- `reject_rule_id` は常に非nullではありません。通常の auditor 拒否でも、`reject_subtype` による分類は残ります。
- IR の parse・`validate_ir` 不合格は `coder-schema` に含まれます。「履歴に入る構文拒否」は描画後の `policy-grammar` を指します。
- `_new_results` は stock・seed・eval の `slot-result` だけを選ぶため、上記の履歴に入らない `opportunity-end` は critic の材料にも入りません。

**初期点・評価結果の digest 欠落も一致します。** [_append_seed_history](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/orchestrator/campaign/p3_s4_loop_policy.py:832) と `run_contrast_unit` の評価転記は `verifier_digest` を渡さず、`_append_history` の `out.get('verifier_digest')` は `None` になります。

草稿・insight・両 fragment は、この意味上の分類と修復対象について一致しています。ただし subtype の説明は N4、恒久対応として参照する memory は N3 のとおりです。

**許可された履歴欄の再集計：保存ログと全値一致。**

| 項目 | 再集計値 |
|---|---:|
| coder 入力 | 249件＝cpp 121＋ir 128 |
| 延べ履歴行 | 1,638行 |
| certified・digest 非nullなし・subtype 非nullなし | 1,626行 |
| rejected・digest 非nullなし・subtype 非nullあり | 12行 |
| verifier_digest が非nullの行 | 0行 |

対象3 key は全1,638行に存在します。「なし」は key の欠落ではなく **null** です。一意な候補数ではなく、累積履歴の延べ数です。

F3 も再確認できました。指定 a1 の文脈には rr50 の行が2行、critic prompt の指定検索語は0行。同じ coder 入力の診断自由文には `read-heavy` があり、修正後の開示と一致します。

**派生値も一致。**

- 4 cell・n＝4：**21.42〜24.72 node h、契約上限63 h、160〜480機会、LLM直列15.2〜64.0 h**。他の費用表3行も一致。
- k(3〜5)：**4.416039013、2.428328636、1.771317564**。
- `ln(1.05)/k(5)`＝**0.027544561 → 0.0275**。
- 参照 job の算式：**6,414〜7,119秒＝1.7816667〜1.9775 h**。登録単価との不一致を開示した現行注記と一致。
- 全対が同じ fallback なら対差・標準偏差が0となり、登録式の区間は **[0,0]**。

fragment は未発効・実装未了を保持しています。新規 worklog 項目は、実際に判明した入力の開示・修復を既存台帳へ残すものです。機械 gate・新規台帳・汎用機構の追加はありません。再発検知も今回の欠落を確認する範囲です。

## 3. 新しい／残った所見

**N1 — should：F2 の「最後の評価は現れない」が無条件になっている。**

場所：[insight §2、52行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/output/insights/2026-10-01/t2852-p5-s3-prereg-revision/README.md:52)。

「各系列の最後の評価は現れない」には、最後の評価後に拒否された提案が続き、A＝30で終わる系列が反例になります。その評価は後続の coder 入力に入ります。これは登録のA/B停止規則とコードから導ける反例で、本走で発生したという主張ではありません。

**直し方：**「評価後に次の coder 入力が生成されなければ、その評価は集計に現れない」と条件付きにする。

**N2 — should：worklog が T-2870 を必須の先行依存に変えている。**

場所：[worklog fragment、33行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/spool/worklog/2026-10-01-dev-wave-p5-s3-prereg-1.md:33)。

「表示の切替は [T-2870] の文脈の差し替えの上で行う」に対し、草稿 §13(1) は「先に着地していれば」、§3.1 は「どちらの文脈であっても」です。

**直し方：** 草稿と同じ条件付きの文にする。現状のままだと、台帳だけが新しい着手条件を課します。

**N3 — should：恒久対応の memory は実在するが、F1・F2 の旧説明が残っている。**

場所：[failures fragment、22行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/spool/failures/2026-10-01-dev-wave-p5-s3-prereg-2.md:22) が参照する [memory](/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/memory/consumer-schema-is-not-producer-evidence.md:13)。

memory は索引にも登録されています。しかし本文に、次が残っています。

- 「`_contrast_unit` → `_append_history`」
- 「schema・auditor の拒否は台帳にだけ残っていた」
- 「全部 certified の標本では欄の欠落は表に出ない」

修正後の草稿・insight と一致しません。

**直し方：** `run_contrast_unit`、通常の auditor 拒否との区別、null 自体は観測済みという説明へ更新する。草稿の節と worklog の新規項目への参照は実在し、対応しています。

**N4 — nit：履歴に入らない subtype の括弧内列挙が不完全。**

場所：草稿 §3.2、insight §6。

`proposal-schema`・`auditor-gate`・`auditor-digest` は `_record_preview_reject` の除外集合です。別経路の `_schema_reject` は `coder-schema` と **`auditor-schema`** を記録します。自然言語の「auditor の出力の形式」には含まれるため、修復範囲の実質的な欠落とは判定しません。

**直し方：** 上の5種類を経路別に書き、「構文」は描画後の構文検査と明示する。

**N5 — nit：failures の根本原因が、登録の起草過程まで断定している。**

場所：[failures fragment、19行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-p5-s3-prereg/docs/spool/failures/2026-10-01-dev-wave-p5-s3-prereg-2.md:19)。

「登録の文も同じ schema から書かれており」は、今回の資料で確認できる範囲を超えます。確認できるのは登録の記述と対照経路の不一致、およびP5草稿の誤前提です。

**直し方：**「登録にも同じ情報の返却が記載されていたが、対照経路では実現されていなかった」とする。

## 総括

**GO — must-fix 0件。**

元の F1 の重大な誤分類は解消しています。残件は **should 3件・nit 2件**。既に closed だった9件に後退はありません。