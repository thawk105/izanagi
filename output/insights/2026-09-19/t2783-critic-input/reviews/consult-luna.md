## 総括

**NO-GO（現planの実装引渡し）。** P1の「K2限定・明示入力・兄弟key」は妥当です。ただし、consumerの所有分割と、手動組立てをどの成果物で検証するかを先に確定してください。static input schemaの修復は本waveから外せます。

指定4資料と関連コードを静的に確認しました。編集・pytest・checker・role起動・評価実走は行っていません。以下のreal/refutedは静的所見の候補判定です。

### must

**M1 — consumerをauthor単位から外しており、両roleへの接続が受入単位からこぼれる〔real候補〕**

所在: [brief.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/brief.md:14)、[plan.md:102](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/plan.md:102)、[plan.md:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/plan.md:108)。

- **反例:** authorのCLIとbuilderは診断を正しく出すが、manager側のcoder入力組立てから代入1行が抜ける。builderの回帰は通っても、T2746と同じ未送達が残る。現planでは「coder側コピーを削除」の変異対象が、手順本文なのかテスト内の模擬コピーなのか未確定です。
- **実影響:** briefが結合するとした型・CLI・consumerの変更が分離し、「両role入力へ届く」という成果物の中心を検証できません。テスト内のコピーを壊して赤にしても、実手順の欠落を検出したことにはなりません。
- **最小修正:** role契約と両入力の組立て例をauthorの結合レビュー対象に戻す。既存runbookのK2追補に、同一contextから両JSONを組み立て、保存・inline送付する具体例を置き、その**実際の手順例**を回帰対象として指定する。managerは文書統合と親受入を担当する。新CLI・launcher・送達gateは不要です。

### should

**S1 — static schema修復の条件分岐を削除する〔real候補〕**

所在: [plan.md:127](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/plan.md:127)。現物は `orchestrator/codex_roles/manifest.json:1490`、`tools/check_codex_agents.py:196`、`orchestrator/codex_roles/review_ledger.py:45`。

- **反例:** 登録Claude roleへ完全なJSONをinline送付する現行経路は、dormant adapterのplanner入力schemaを通しません。既存`policy_hint`もsource本文では許可され、台帳にはdormant parityを対象外とする扱いがあります。
- **実影響:** 「static schemaでも扱うなら」を残すと、既存`knowledge_input`不一致の修復、schema pin、manifest pinまで変更が広がります。それでも手動コピー欠落は検出できません。
- **最小修正:** 本waveではstatic入力schemaによる完全入力検証を受入条件にしないと確定する。role本文変更に必要なsource pin・埋込みadapterの追従は残し、schema・manifest pinは実際に変更したものだけ追従する。runtime blockedを維持する。

**S2 — 変異の赤を、今回追加した経路の検出力へ一括帰属しない〔real候補〕**

所在: [plan.md:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/plan.md:108)、[plan.md:112](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/plan.md:112)、[t2746-readme.md:163](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/t2746-readme.md:163)。

- **反例:** 共通節抽出器のfence処理を壊せば既存AOテストが赤になり得ます。AO読取り挿入も既存隔離テストが検出します。これは両roleの新入力経路を通した証拠にはなりません。
- **実影響:** 親のmatrixが全件KILLEDでも、本waveの未接続部分を覆ったように読めます。
- **最小修正:** 既存matrixの結果説明で、壊した箇所と実際に赤になったnodeを対応づける。共有抽出器・旧防壁による検出と、新CLI・両入力組立てによる検出を区別する。新しい台帳やgateは不要です。

**S3 — P1の動機を「未送達が20再提案の原因」と一般化しない〔real候補〕**

所在: [brief.md:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/brief.md:2)、[t2746-readme.md:78](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/t2746-readme.md:78)。

- **反例:** 診断を受け取ってもcoderは留保を踏まえて20を選べます。また当時の入力には、20が評価済みという履歴もありませんでした。
- **実影響:** 経路整備を、再提案防止や探索改善の実証へ読み替える余地が残ります。
- **最小修正:** 親の結論は「診断未送達と20再提案を観測した。因果は未検証」に限定する。plan:21の「10を受入条件にしない」は維持し、既知値禁止・履歴統合・再抽選を追加しない。

### nit

**N1 — 「4節全部が最小」は断定が強い〔real候補〕**

所在: [plan.md:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2783-critic-input/plan.md:51)。

4節にはstock運用要望も含まれ、生成だけに必要な最小情報集合とは未証明です。ただし削るための意味抽出器を新設する方が大きな変更になります。**「留保を落とさず、既存抽出器を使える最小実装」**への言い換えで十分です。

### refuted候補

- **「4節を渡すならwhiteboard防壁を緩める必要がある」:** 不要。兄弟keyで成立します。
- **「K2・emit限定の引数検査はすべて過剰gate」:** 不成立。今回の入力口の適用範囲を限定する検査には根拠があります。評価受理・停止判定への拡張は不要です。
- **「static schemaを直さなければ両roleの手動入力経路は閉じない」:** 不成立。必要なのは局所入力型、role本文の許可、具体的な組立て・送付手順です。実送達と採用・改善効果の確認は、今回の静的確認とは別に残ります。