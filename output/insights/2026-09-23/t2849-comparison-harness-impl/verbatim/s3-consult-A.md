**現プランは要修正です。must-fix 2件、should 3件。** 静的検査のみ実施し、テスト実測はしていません。

以下、`plan` は [段2プラン](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2849-comparison-harness-impl/s2/plan.md)、`brief` は [親 brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2849-comparison-harness-impl/s1/brief.md)、`設計` は [設計正本](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2849-comparison-harness/output/insights/2026-09-22/t2849-comparison-harness-design/README.md) を指します。

## 所見

### 1. must-fix — P2 は D2220 の LLM 構成を変更する

**根拠:** brief:35–36、plan:289–294・355・477、設計:104・130・154–156、`docs/decisions.md:71385`。

既存役割契約が K0 の診断入力を許さないという調査結果は正しいです。しかし、それは D2220 が要求する改訂を省略する理由にはなりません。設計:90 は既に K2 限定を指摘し、適用範囲の拡張を実装事項にしています。「裁定時に未見」という brief の説明は、少なくともこの制約について不正確です。

P2 では、LLM は初期点2件の対応つき観測・投入前拒否一覧・critic 診断を受け取れません。最新 baseline だけでは代替できず、critic を呼んでも診断が次の生成へ戻りません。規律3の構造化した失敗情報の還流にも穴が残ります。「部分実装」と文書に書くだけでは、依頼された単位4の完了にはなりません。

本依頼を完了させる選択は **(a) 必要な役割契約と射影を改訂する**ことです。役割変更を今回扱えないなら **(c) 単位4を未完として送る**方が正確で、5手法比較を投入可能とは扱えません。

なお brief:35 の「両 file が B-5 束に束縛」も過大です。束:222–223 が列挙するのは planner と **coder-v4-autonomous-k2** であり、通常版 coder ではありません。

**放置時の影響:** LLM の生成候補列と費用が D2220 の構成から変わり、レポートが別構成の比較を予定した5手法比較として扱う。

### 2. must-fix — 役割費用の producer–consumer 接続が未確定

**根拠:** plan:100–101・132–138・345・407、`tools/b5_llm_round.py:358–364`、`orchestrator/campaign/b5_generator_contrast.py:692–701`。

成功提案の既存 handshake は、入力文書から planner/coder 入力を照合した後、返却 provenance を `inputs_path`・SHA・current_perf の出所から組み立て直します。追加した費用を自動で透過転送する契約ではありません。

さらに plan は critic 費用を「実行後の materials に残し、集約で取り込む」としますが、materials root は巡 tool の独立した引数です。aggregate の入力にはその場所も、台帳からの参照規則もありません。現状では U-C が保存できても U-B が読める保証がありません。

並列投入前に、成功／拒否それぞれの費用 field の保存位置、driver の読み取りと event への転記、critic materials の参照と集約時の結合単位を固定してください。実際の巡 tool の publish → driver の consume → aggregate を通す試験が必要です。

**放置時の影響:** 記録済みの役割呼出し・介入費用が台帳やレポートで欠落し、LLM 構成の費用比較が不完全になる。

### 3. should — `N_eval` と session 内の5 rep を明示的に分離する

**根拠:** plan:89・104–106・218・240、`orchestrator/campaign/b5_generator_contrast.py:635`・829、同:418–424。

既存 B-5 は `N_EVAL` を endpoint の session 数にも、`classify_slot(..., expected_reps, ...)` にも使っています。ともに5なので成立していますが、新 driver は N を可変にします。一方、共通評価口の correctness／bench は5 rep 固定です。

プランにはこの結合を外す指定がありません。`N_eval=2` でも、各 session は legacy＋performance 5回を要求し、endpoint だけ2 session 測る、と明記してください。この条件を実 WAL 分類を通して検査すれば、混同を検出できます。

**放置時の影響:** 素直な移植で N≠5 を指定すると正常な WAL が欠測扱いになり、score と参照比が消える。

### 4. should — cohort root と ledger root の配置契約が抜けている

**根拠:** plan:85–101・298–302・365。

driver は cohort root と ledger root を別々に受け、集約は cohort root 配下だけを読みます。ledger をその配下へ必ず配置する規則も、配下でない場合の参照方法も定義されていません。

追加台帳は不要です。既存 header と配置規約で「どの探索・共有対照台帳を発見できるか」を固定し、実ディレクトリ配置から他系列 anomaly と block controls を拾う試験を入れてください。

**放置時の影響:** 探索時には記録された他系列 anomaly が集約から漏れ、失格値が endpoint として報告される、または共有対照が欠測になる。

### 5. should — 新しい参照分類の負例と保全例外の試験が不足する

**根拠:** plan:182・187–190・222・322・433–436、`orchestrator/campaign/b5_generator_contrast.py:380–435`、`orchestrator/campaign/pipeline.py:2176–2178`。

参照分類は既存分類を複製する新しい実装面ですが、試験指定は exact flags と実 WAL 分類が中心です。正常 fixture だけでは、identity 照合・verify 回数・anomaly 条件を落としても赤になりません。

少なくとも正常な参照 WAL を起点に、genome 不一致、performance verify 欠落、anomaly 混入で certified にならないことを確認してください。また保全は `finally` 内なので、zstd の非ゼロ終了に加え、起動失敗や inventory 書込み失敗が元の評価結果を例外で置き換えないことも対象です。

**放置時の影響:** 参照の不完全な証拠を受理する弱体化、または保全障害による正常評価の欠測化を、正例中心の試験が見逃す。

## 攻撃が不成立だった観点

- **P1：条件付きで不成立。** 束の4ファイルの SHA は、この静的検査でも現行と一致しました。束:18 は指定 land と、束の status／effective section だけを変える発効 commit を対象にします。その land を親にして本 wave を含めなければ整合します。ただし「その子なら何でもよい」「SHA 一致なら別 commit でも承認内」ではありません。
- **P3：不成立。** prebuild 後の排他的な job body 分岐と、driver 直前の lock 設定は既存:652–670 と整合します。「置き場が無い」は言い過ぎですが、採用案自体は妥当です。
- **規律1・2の直接迂回：不成立。** プランは共通 verify／bench を維持し、参照に偽の `BACKOFF_FIXED=-1` を足しません。接頭辞拡張も既存の必須 flag 条件を残しています。既存 B-5・非 B-5・保全 opt-in なしの受理集合を変える指定は見つかりませんでした。
- **A/B、初期点、重複、R0、欠測優先：意味の改変は不成立。** plan:242–251・298–304 は設計と整合します。全系列 anomaly も意図は正しく、問題は所見4の発見経路です。
- **所有 path の重複：不成立。** plan:403–405 は素集合です。依存順も妥当ですが、所見2の受け渡し仕様を先に埋める必要があります。
- **数値試験の恒真性：不成立。** 解析解と独立した2×2逆行列による照合は有効な方針です。未実装のため、変異が実際に kill されるとはまだ判定できません。

## 総括

- **所見5件：must-fix 2、should 3、nit 0。**
- **P1：条件付き賛成。** 親の4 SHA 一致は再確認できた。指定 land と発効差分の条件を維持する。
- **P2：反対。** 既定の比較構成を変えるため、(a) が依頼完了に適合する。(c) は明示的な未完扱いの場合の代案。
- **P3：賛成。** 最小の排他的 job body 分岐でよい。
- テスト実測・ファイル変更・計算投入は行っていません。