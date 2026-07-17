# roadmap.md / CLAUDE.md 明瞭化リファインメント — 相談逐語と裁定 (2026-07-17)

状態: 作業中 (セッション 9b2bec65)。F20 対応: 段階完了ごとに追記。

注記: 本文中 (相談・レビュー逐語内) の `docs/roadmap.md:<N>` 等の行番号リンクは、各節のレビューが
対象にした時点の行番号を指す point-in-time 証拠であり、その後の編集に追従しない (逐語凍結のため
書き換えない)。相談 A/B/C・survey・盲検回帰の節は BASE=60da9b8、「codex 第二系統レビュー」節の
4 リンクは candidate=9997d61 時点。

## プラン v1 (相談前の凍結版、攻撃対象)

# プラン: roadmap.md / CLAUDE.md 明瞭化リファインメント (協議改訂)

## 背景と位置づけ
- ユーザー依頼: 両ファイルの「分かりにくい部分を分かりやすく」。意味の変更・規範の強化/弱化はしない。
- roadmap.md: **協議改訂** (roadmap.md:3 の契約 — in-place、版番号不変、roadmap-history への版凍結なし)。
- CLAUDE.md: 「絶対規律」節とその配下 = 憲法 (変更できるのは人間のみ) → **in-file 編集もコミットもしない**。改善提案 (old→new 対) を output/insights へ凍結し人間裁定に委ねる。それ以外の節 (現在地・起動ゲート・作業の進め方等) は通常編集。
- 昨夜の repo-refinement セッションは裁定 A4 で両ファイルをスコープ外化 (検討なし)。流用材料なし。今回が初の実施。
- 基準: ローカル main 60da9b8 (origin は 0cf9f49 で 3 コミット遅れ = ユーザー push 待ち)。worktree `roadmap-claudemd-clarity` で作業。

## 編集ポリシー (攻撃対象)
1. **意味保存が正しさゲート**。規範文 (「〜してはいけない」「必ず〜」「〜のみ」「〜まで保証しない」) の量化・強度・適用範囲・例外条件を 1 bit も変えない。
2. **見出しテキスト・§ 番号・D 番号・ファイルパスは不変** (他文書からのアンカー参照が多数)。
3. **技術用語の surface form は保持** (glossary 収載語・英語術語の grep 到達性契約、前 wave ac8f3e9 で確立)。日本語化候補は非術語の外来語のみ。
4. 許す操作: 長文の分割 / 入れ子括弧の解消 (箇条書き化・注記の構造化) / 指示語の明示化 / 主語述語の対応修復 / 遡及注記 (太字括弧の「実際は違った」系) の構造化 — ただし歴史的事実・negative result の内容は一切落とさない (roadmap は研究記録でもある)。
5. 許さない操作: 節の統合・分割・並べ替え / 規範の追加・削除 / 数値・実験結果・判断記録 (D 参照) の変更 / 情報の削除 (重複も原則保持、指摘のみ)。
6. check_docs.py 固有ルール順守: 「現在は Phase」現況再掲の禁止 (CLAUDE.md 現在地以外)、CLAUDE/roadmap での「次 =」禁止、LIVING_DOCS 検査。

## 実行設計 (攻撃対象)
- Stage S (survey、sonnet 並列 + opus 統合): 独立レンズで「分かりにくい箇所」を構造化列挙。レンズ: (a) 初見読者の混乱点 (b) 構文密度 = 文長・括弧入れ子 (c) 用語 = glossary 整合・外来語 (d) 規範文の曖昧性 = 誤読リスク。統合時に各所見を safe / normative-care / constitution-proposal-only の 3 分類。
- Stage D (draft、opus): ファイル単位 1 レーン (同一ファイルの並列編集はしない)。roadmap レーンと CLAUDE.md レーン。絶対規律節は編集せず提案の構造化返却のみ。
- Stage R (review、opus 敵対 3 レンズ × 各ファイル): (i) 意味ドリフト狩り — 規範強度の変化を悪魔の代弁者として証明しにいく (ii) 参照整合 — 見出し・§・D・パス・用語到達性 (iii) failures.md 型タグ再発検査。
- Stage V (機械検証、sonnet/親): 見出し diff = 空、§ 列挙一致、check_docs、glossary 語 grep 到達性、D 参照実在。
- 親: 全 diff 目視 → commit (roadmap 改訂 / CLAUDE.md 非規律部 / insights = 相談逐語 + 絶対規律提案) → codex 独立最終レビュー (全 diff) → 残所見修正 → worklog → ローカル main へ ff。push はしない (Pegasus 運用)。

## 自認済みリスク
- 「分かりやすく」が規範を弱める方向に働く (reward hacking の文書版)
- 参照アンカー破壊 (他文書の節名・§ 参照)
- 研究記録の物語性 (negative result の遡及注記) の破壊
- CLAUDE.md は毎セッションロードされる — 明瞭化で行数が膨らむと boot cost 増 (D35 と逆行)。行数純増は roadmap ±10%・CLAUDE.md ±5% を目安に抑える

---

## 相談 A: roadmap 編集方針への攻撃 (codex gpt-5.6-sol reasoning=max) — 逐語

### プロンプト
```
あなたは敵対的レビュアーです。私 (Claude) はこのリポジトリ (izanagi) で docs/roadmap.md の明瞭化リファインメント (意味を変えない文章改善) を計画しています。私のプランを攻撃し、実行前に穴を潰してください。

## まず読むもの (read-only)
- /home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md (私のプラン全文 — 攻撃対象)
- docs/roadmap.md (改訂対象の全文、374 行)
- docs/roadmap-history/README.md (改訂契約 — 協議改訂の定義)
- CLAUDE.md (特に「roadmap の更新 — 三層の可変性」節)
- tools/check_docs.py (機械検査の実装)
- docs/glossary.md の冒頭規約と見出し (用語の grep 到達性契約)
- output/insights/2026-07-17_repo-refinement-consultations.md (昨日の docs リファイン wave の教訓 — 特に相談 B の must-fix)

## 攻撃してほしい論点 (roadmap.md 固有)
1. **協議改訂の分類は正しいか** — 「意味を変えない明瞭化」を協議改訂 (版凍結なし・in-place) として扱う私の解釈に穴はないか。セレモニーを回すべき境界条件は何か
2. **意味保存の破れやすい箇所の特定** — roadmap.md の中で、書き換えると規範・実験記録・判断根拠が壊れやすい具体的な危険地帯を file:line で列挙せよ (例: §3.3 の diff-of-diffs 記述、§3.6(3') の within/between-run 区別、§2 の P2-5 遡及注記、§1 の主張階層)
3. **研究記録の物語性** — 太字括弧の遡及注記 (「実際に起きた移行は違う形だった」等) を構造化して良いか、それとも原文の形が方法論の記録として価値を持つか
4. **アンカー安定性** — 他文書からの § 参照・節名参照で、私の「見出し不変」ポリシーだけでは守れないものはあるか (本文中の語句への参照、行番号参照の残骸等)
5. **編集ポリシーの穴** — プランの「許す操作 / 許さない操作」の列挙に抜けはないか。「分かりやすく」が規範を弱める reward hacking の具体的攻撃シナリオを構成せよ
6. **そもそも直すべきでない可能性** — roadmap の密度は D35 (ブートコスト規律) と両立している。明瞭化による行数増・冗長化が読み込みコストを悪化させる帯はどこか

## 出力形式
所見ごとに: [severity: must-fix / should / nit] タイトル / 攻撃シナリオ (具体的に何がどう壊れるか) / 根拠 (file:line) / 提案 (プランへの修正)。最後に「プラン全体の妥当性」を 3 行で総括。所見が無い論点は「異議なし」と明言せよ。
```

### 回答 (逐語)

結論: このままの実行は危険です。**must-fix 9 件 / should 3 件 / nit 0 件**です。特に「文体修正前の claim 監査」「本文アンカーの固定」「意味保存 oracle」「トークン予算」が不足しています。

### 1. [severity: must-fix] 文体修正前の claim 監査が抜けている

- 攻撃シナリオ: 既存の不正確・矛盾した主張を「分かりやすく」書き直すと、誤りの訂正と文体変更が同じ diff に混ざり、意味保存を判定できなくなる。実例として roadmap は複数 seed を数値的信頼度へ変換しないと明記する一方、consumer はなお `1-εⁿ` を roadmap の主張として引用している。編集者がどちらかへ寄せれば、それは明瞭化ではなく設計・保証の変更になる。
- 根拠: [roadmap.md:158](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:158)、[verifier/cli.py:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/orchestrator/verifier/cli.py:8)、[phase3-main-experiment.md:304](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/phase3-main-experiment.md:304)、[phase3-main-experiment.md:307](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/phase3-main-experiment.md:307)。前 wave も「文体修正より先に read-only claim 台帳を凍結」と裁定している [repo-refinement-consultations.md:197](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/insights/2026-07-17_repo-refinement-consultations.md:197)。現プランは survey から始める [plan-clarity.md:18](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:18)。
- 提案: Stage S の前に `Stage 0: claim audit` を置く。各 roadmap claim について「現在文 / 根拠 D・実装 / consumer / real・stale・ambiguous」を凍結し、stale・ambiguous は今回 no-edit とする。訂正は別の意味変更改訂へ分離する。

### 2. [severity: must-fix] 「協議改訂」は条件付きで正しいが、意味変更への遷移規則がない

- 攻撃シナリオ: 一般的な「分かりやすくして」という依頼を、個々の曖昧性解消や事実訂正まで事前承認されたものとして扱えば、実質的な自律改訂を協議改訂としてセレモニーなしで通せる。
- 根拠: プランは開始時点で無条件に協議改訂と確定している [plan-clarity.md:5](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:5)。契約は「ユーザーと協議して合意した改訂」と「Claude の自律改訂」を分ける [roadmap-history/README.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap-history/README.md:22)、[roadmap-history/README.md:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap-history/README.md:25)。roadmap は戦略層である [CLAUDE.md:99](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:99)。
- 提案: 次の境界を明記する。
  - 純粋な構文・配置変更で意味同値が立証できる hunk → 協議改訂、in-place で異議なし。
  - 曖昧性の一方を選ぶ、保証・因果・状態・閾値・Phase 順序・スコープを変える hunk → clarity diff から除外。
  - その意味変更案をユーザーが具体的に承認 → 協議改訂。
  - Claude 判断で進める → セレモニー 1–3。大改訂案は適用前にユーザー確認。
  
  特に改訂統治そのものを記す [roadmap.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:3) は今回 byte-freeze が安全。

### 3. [severity: must-fix] 見出し不変では本文アンカーを守れない

- 攻撃シナリオ: 見出しを一字も変えなくても、本文の番号・ラベル・引用句を整理すると consumer が着地できなくなる。Stage V の「§ 列挙一致」は、見出しでない `(3')`、`Tier 1`、`§3.4-4`、Phase コードブロック内ラベルを守らない。
- 根拠:
  - `roadmap 冒頭の「読み方」` は見出しでなく太字段落だが、[CLAUDE.md:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:14) と [docs/README.md:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/README.md:15) から参照される。
  - `(3')` と `(4)` は [.claude/agents/calibrator.md:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/.claude/agents/calibrator.md:33) などが直接参照する。
  - `Tier 1` は [verifier/dsg.py:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/orchestrator/verifier/dsg.py:4)、`§3.4-4` は [verifier/model.py:6](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/orchestrator/verifier/model.py:6) のアンカー。
  - `high-abort genome...` は本文を逐語引用される [phase3-main-experiment.md:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/phase3-main-experiment.md:61)。
  - §7 は単なる節でなく、外部文書を指す特殊な転送契約である [roadmap.md:310](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:310)、[related-work/README.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/related-work/README.md:5)。
- 提案: pre-edit の incoming-reference manifest を作り、見出しに加えて `(1)…(5)`、`(3')`、`Tier 0…3`、`(a)/(b1)/(b2)`、Phase 名、引用された本文句、「読み方」、§7 の転送意味を固定する。glossary 語だけでなく、全 literal consumer に `rg -F` lookup test を行う。

### 4. [severity: should] 凍結記録の行番号参照は必ずさらにずれる

- 攻撃シナリオ: 長文分割で後続行が移動し、archive・insight 内の `roadmap.md:N` が現在の別内容を指す。これらは凍結物なので、後から追従編集もできない。
- 根拠: 行番号参照は [audit-2026-06-30.md:192](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/archive/audit-2026-06-30.md:192)、[audit-2026-07-04-docs-consistency.json:399](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/archive/audit-2026-07-04-docs-consistency.json:399)、[2026-06-19_invisible-reads-i2-reconciliation.md:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/insights/2026-06-19_invisible-reads-i2-reconciliation.md:56) 等に残る。`check_docs.py` は archive・insight を living docs から除外する [check_docs.py:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/tools/check_docs.py:21)。
- 提案: 「アンカー安定性」の保証対象を living consumer の意味アンカーに限定する。凍結記録の行番号は当時の commit に対する point-in-time 証拠として不変のまま残し、現在 HEAD への着地保証はしないとプランに明記する。凍結物を直して見かけだけ合わせてはいけない。

### 5. [severity: must-fix] 意味保存を判定する oracle が弱すぎる

- 攻撃シナリオ: `check_docs`、見出し diff、D 番号一致をすべて通しながら、規範を弱められる。例えば「決して同一セッションで測らない」を「別々に測る」、「必ず含める」を「含める」、「保証しない」を「対象外」とすると、例外・量化・保証範囲が変わるが機械検査は緑になる。実際に今回も `check_docs: 違反なし` だった。
- 根拠: checker 自身が意味的ずれを検出できないと明記する [check_docs.py:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/tools/check_docs.py:4)。検査実体も行番号、現況、D、パス等に限られる [check_docs.py:133](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/tools/check_docs.py:133)。危険な規範例は [roadmap.md:149](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:149)、[roadmap.md:205](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:205)、[roadmap.md:298](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:298)、[roadmap.md:367](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:367)。
- 提案: 各変更 hunk に次の意味署名を付ける: `主体 / modality / 対象 / 条件 / 例外 / 時制・実装状態 / epistemic status / 根拠 D`。さらに規範語、否定、数量・単位・比較演算子、コード span、リスト順序・個数を pre/post 抽出する。「旧文で許され新文で禁止される入力、またはその逆を一つ作れないか」という反例レビューを独立レビュアに課す。新しい例・因果説明・解釈の追加も禁止操作へ入れる。

### 6. [severity: must-fix] §1・§2・§8・§10 は主張強度を変えやすい semantic-lock 地帯

- 攻撃シナリオ: 読みやすい要約へ置換すると、次の reward hacking が可能になる。
  - 「LLM が機械探索を上回ることは成功条件でない」を落とし、LLM 成功物語へ寄せる。
  - stock/tie と「新しい CC」の達成を混同する。
  - 評価器の成立からシステム・LLM・無人自律を推論する。
  - P2-4 の一事例を LLM の因果的必要性の証明へ格上げする。
  - 禁止事項を「当面やらない」程度へ弱める。
- 根拠: [roadmap.md:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:17)、[roadmap.md:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:30)、[roadmap.md:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:32)、[roadmap.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:38)、[roadmap.md:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:116)、[roadmap.md:120](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:120)、[roadmap.md:317](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:317)、[roadmap.md:360](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:360)。
- 提案: これらを `normative-care` ではなく `semantic-lock` にする。改行・既存語の箇条書き化以外は原則 no-edit。特に「のみ」「含めない」「未実証」「一事例」「主張しない」「スコープ外」の変更を機械的に拒否する。

### 7. [severity: must-fix] §3.1–§3.4 は保証範囲と防壁責務を逆転させやすい

- 攻撃シナリオ:
  - Tier 1 を「serializability verifier」とだけ要約し、point-key/観測 trace 限定、predicate・fairness・未観測実行の非保証を消す。
  - diff-of-diffs を「TRACE 有無の出力 diff」と短縮し、既に棄却された素の diff predicate を復活させる。
  - hooks を「迂回を防ぐ防壁」と総括し、一次防壁と第二防壁の責務分離を失う。
  - auditor の「提案」を「テスト追加」に変え、read-only 境界を消す。
- 根拠: [roadmap.md:149](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:149)、[roadmap.md:158](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:158)、[roadmap.md:169](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:169)、[roadmap.md:180](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:180)、[roadmap.md:181](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:181)、[roadmap.md:182](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:182)。
- 提案: line 169 は `当初案 / 棄却理由 / 現行 predicate / 発火場所 / fails-closed` の五要素を exact に固定する。§3.4 は `primary/secondary`、`read-only/proposal`、`入力側/出力側` の対を機械検査する。ここでは語彙置換をせず、既存句の配置変更だけにする。

### 8. [severity: must-fix] §3.6 と §4 は一つの不可分な意味クラスタ

- 攻撃シナリオ: `(3')` を読みやすく短縮する過程で、within-run を採否 floor に流用した過去の偽 faster 経路が復活する。また MWU を「有意性検定」とだけ要約すると、between-run floor が主防壁、MWU は弱い within-run sanity、near-floor は cross-run 再現必須という順位が逆転する。
- 根拠: [roadmap.md:202](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:202)、[roadmap.md:205](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:205)、[roadmap.md:207](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:207)、[roadmap.md:209](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:209)、[roadmap.md:271](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:271)。consumer も本文の細部に依存する [stability.py:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/orchestrator/calibrator/stability.py:107)、[stability.py:172](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/orchestrator/calibrator/stability.py:172)。
- 提案: §3.6 と §4 を同一レビュー単位にする。`within=品質 / between=採否`、fresh は下限、cross-campaign と比較して最大、high-abort は別 floor、MWU は副防壁、near-floor は再現必須、という七項目を pre/post invariant にする。一方だけ編集して内部不整合を作ることを禁止する。

### 9. [severity: must-fix] 遡及注記は構造化可能だが、一般的な括弧解消ルールでは物語を壊す

- 攻撃シナリオ: 「現在の結論」だけを読みやすい本文に残し、当初仮説・negative result・設計転換を別注へ追いやると、後知恵で一直線に設計したように見える。逆に当初文だけを本文に残し、訂正を離すと古い仮説が現行主張に見える。
- 根拠: 仮説変遷自体が方法論の物語である [roadmap-history/README.md:9](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap-history/README.md:9)。代表例は P2-5 の転回 [roadmap.md:80](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:80)、実際の移行との差 [roadmap.md:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:81)、diff-of-diffs への転換 [roadmap.md:169](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:169)、warmup の意図的非対応 [roadmap.md:196](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:196)、飽和仮説の反証 [roadmap.md:265](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:265)。
- 提案: 原文の「太字括弧」という書式自体は不可触ではない。ただし必ず隣接した `当初仮説 → 実測・反証 → 設計帰結 → D` の四点構造へ写像する。`negative result`、「実際に起きた移行は違う」、「当初案から変更」、「未実装・意図的非対応」等の時系列・評価語を逐語保持する。

### 10. [severity: should] 規範と推奨が同居する帯を「矛盾解消」してはいけない

- 攻撃シナリオ: §3.7 は「方法論として固定」と「必須ゲートではなく推奨」を意図的に併記する。読みやすさのため一方へ統一すると、全小変更に重い監査を強制するか、危険な引き継ぎ監査まで任意化する。§3.8 でも、運用規律が守るのは正しさでなく品質・手戻りだという限界を落とすと保証が膨らむ。
- 根拠: [roadmap.md:220](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:220)、[roadmap.md:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:222)、[roadmap.md:245](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:245)。同様に、正式環境の四条件 [roadmap.md:279](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:279)、CCBench の固定実行順 [roadmap.md:294](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:294)、Phase コードブロック [roadmap.md:325](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:325) も本文アンカー兼契約。
- 提案: この帯は layout-only とする。「推奨だが最小トリガを列挙」「正しさではなく品質を守る」の二軸を保持する。Phase 名・順序、環境採用四条件、CCBench 実行順、否定形のスコープ外項目も exact invariant に加える。

### 11. [severity: must-fix] D35 に対して「行数 ±10%」は無効な指標

- 攻撃シナリオ: 同じ文章を箇条書きに分けただけで行数が増えて失格になる一方、長い一行へ説明を大量追加しても行数は増えない。boot cost を測らず Markdown の物理改行を測っている。
- 根拠: プランは行数比を予算にする [plan-clarity.md:29](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:29)。D35 は実測トークン数と必要率で判断している [decisions.md:813](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/decisions.md:813)、[decisions.md:830](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/decisions.md:830)。roadmap 自身も日常は節単位で読む [roadmap.md:9](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:9)。
- 提案: 物理行数でなく、全文と節別の byte/token 数を pre/post 比較する。特に次は増補禁止またはほぼ net-zero の帯にする。
  - 冒頭の統治・読み方: [roadmap.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:3)
  - 頻出する §1・§2: [roadmap.md:13](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:13)、[roadmap.md:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:67)
  - §3.3・§3.6・§4: [roadmap.md:160](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:160)、[roadmap.md:192](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:192)、[roadmap.md:249](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:249)
  - §3.7–§3.8 の運用規律: [roadmap.md:214](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:214)
  - §7 の薄い転送節: [roadmap.md:304](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:304)
  - §9 の Phase 索引: [roadmap.md:325](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:325)

  長い line 169・205・271・279 は既存語を使った zero-copy 分割なら有益だが、用語解説は glossary、関連研究は §7 の委譲先へ置き、roadmap に再注入しない。

### 12. [severity: should] roadmap と別権限文書を一括 commit する設計が監査性を落とす

- 攻撃シナリオ: roadmap、CLAUDE 非規律部、絶対規律提案 insight を一つの commit にすると、協議改訂の git-log 履歴が曖昧になり、roadmap だけのレビュー・revert・意味保存証明ができない。
- 根拠: 一括 commit が予定されている [plan-clarity.md:23](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:23)。協議改訂は git log が履歴になる [roadmap.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:3)。文書は憲法・戦略・戦術で権限が異なる [CLAUDE.md:97](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:97)。
- 提案: 少なくとも `(1) roadmap clarity-only`、`(2) CLAUDE 非規律部`、`(3) 絶対規律への提案 insight` を別 commit にする。roadmap commit 単独で意味保存レビューと revert が成立するようにする。

プラン全体の妥当性 1/3: 協議改訂・in-place という分類自体は、全 hunk が本当に意味同値なら妥当です。  
プラン全体の妥当性 2/3: 現状は claim 監査、本文アンカー、意味保存 oracle、D35 の計測指標が不足しており、そのまま実行すべきではありません。  
プラン全体の妥当性 3/3: 上記 must-fix を反映し、semantic-lock 帯を layout-only に絞れば、安全に実行可能な計画になります。
---

## 相談 B: CLAUDE.md 編集方針への攻撃 (codex gpt-5.6-sol reasoning=max) — 逐語

### プロンプト
```
あなたは敵対的レビュアーです。私 (Claude) はこのリポジトリ (izanagi) で CLAUDE.md の明瞭化リファインメント (意味を変えない文章改善) を計画しています。私のプランを攻撃し、実行前に穴を潰してください。

## まず読むもの (read-only)
- /home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md (私のプラン全文 — 攻撃対象)
- CLAUDE.md (改訂対象の全文、159 行)
- AGENTS.md (製品別入口 — CLAUDE.md への委譲構造)
- docs/roadmap-history/README.md と docs/roadmap.md 冒頭 (三層可変性の対応関係)
- tools/check_docs.py (CLAUDE.md への機械検査)
- hooks/README.md の冒頭 (CLAUDE.md が委譲する機械防壁の正本)
- docs/failures.md (過去の失敗型 — 文書改変での再発リスク)

## 攻撃してほしい論点 (CLAUDE.md 固有)
1. **憲法境界の定義** — 私は「## 絶対規律 とその配下 ### 1〜6」を人間専管とし in-file 編集もコミットもしない方針。この境界定義は十分か? 「roadmap の更新 — 三層の可変性」節の「絶対規律 = 憲法。変更できるのは人間のみ」の文自体、あるいは task-class gate (現在地節) など、規律と同等の効力を持つ他の節はどれか。それらを「通常編集可」と扱う私の分類の危険性を攻撃せよ
2. **ゲート弱体化の検出** — CLAUDE.md はすべての AI セッションの挙動を規定する。明瞭化を装った書き換えが起動ゲート・監査発火条件・信頼境界を弱める具体的シナリオを構成せよ (例: クラス分類の「迷った場合は重い方」の条件を「読みやすく」削る等)
3. **boot cost との緊張** — CLAUDE.md は毎セッション全文ロードされる。明瞭化による行数増は D35 に逆行する。行数純増の許容幅、または「明瞭化 = 圧縮」とすべき箇所を特定せよ
4. **提案止まり運用の妥当性** — 絶対規律節の改善提案を output/insights に凍結して人間裁定に委ねる、という運用に穴はあるか (提案自体が誘導的になる危険、裁定なしで放置された場合の扱い等)
5. **他文書との結合** — CLAUDE.md の文言を参照・引用している他文書 (AGENTS.md、hooks/README、agent role 定義等) があれば、どの文言が壊れやすいか列挙せよ
6. **編集ポリシーの穴** — プランの「許す操作 / 許さない操作」に CLAUDE.md 固有の抜けはないか

## 出力形式
所見ごとに: [severity: must-fix / should / nit] タイトル / 攻撃シナリオ (具体的に何がどう壊れるか) / 根拠 (file:line) / 提案 (プランへの修正)。最後に「プラン全体の妥当性」を 3 行で総括。所見が無い論点は「異議なし」と明言せよ。
```

### 回答 (逐語)

結論から言うと、現状のままの実行には反対です。6 論点すべてに異議があります。

## 1. 憲法境界

[severity: must-fix] 人間専有境界そのものが保護範囲外

攻撃シナリオ — プランは `## 絶対規律` 配下だけを凍結しますが、「絶対規律を変更できるのは人間のみ」という権限規則は節外です。AI がこれを「人間の承認がある場合のみ」などと明瞭化すれば、後続セッションが自己承認や暗黙承認を主張して憲法を編集できます。同様に roadmap/phase docs の編集権限・凍結契約も書き換えられます。

根拠 — [plan-clarity.md:6](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:6)、[CLAUDE.md:99](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:99)、[docs/decisions.md:130](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/decisions.md:130)、[docs/decisions.md:2231](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/decisions.md:2231)。

提案 — byte-frozen 範囲を「絶対規律ブロック」に加えて `絶対規律 = 憲法。変更できるのは人間のみ` の全文まで広げ、見出し単位ではなく抽出ブロックの SHA-256 で検査してください。残る三層可変性の文も `normative-care` とし、通常編集扱いをやめます。

[severity: must-fix] 「非憲法 = 通常編集可」の二分法が粗すぎる

攻撃シナリオ — 起動ゲート、generic child の禁止、hook 非迂回、provenance、計測値の資格、push 人間判断を「普通の文章」として整理すると、絶対規律本文を一字も触らず実効性だけ落とせます。たとえば「hook が守る」と短縮すれば、Codex では未配線なのに手動防護を省略できます。

根拠 — [CLAUDE.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:22)、[CLAUDE.md:104](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:104)、[CLAUDE.md:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:112)、[CLAUDE.md:135](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:135)、[AGENTS.md:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/AGENTS.md:17)。

提案 — 三分類にしてください。

- `byte-frozen`: 絶対規律と人間専有境界
- `semantic-invariant`: ファイルの正本性、task-class gate、三層可変性、subagent/hook/provenance、作業手順
- `safe prose`: 非規範的な背景説明のみ

`normative-care` の採用条件も Stage D に明記し、曖昧なら編集せず proposal-only に落としてください。

[severity: must-fix] 監査発火条件には既存の規範矛盾がある

攻撃シナリオ — `CLAUDE.md` は「取り込み時・Phase 境界・overnight 後には監査を行う」という義務形ですが、roadmap と D27 は「推奨、必須ゲートではなく小さい増分では省略可」です。片方をもう片方へ寄せる「明瞭化」は、必ず強化または弱化になります。

根拠 — [CLAUDE.md:93](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:93)、[docs/roadmap.md:220](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:220)、[docs/roadmap.md:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:222)、[docs/decisions.md:551](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/decisions.md:551)。

提案 — この対応箇所は両ファイルとも編集対象から外し、「義務」「推奨」「トリガ時には実施するが release gate ではない」のどれかを人間が裁定する案件として別記してください。単一の old→new 案を「意味保存」として提示してはいけません。

## 2. ゲート・信頼境界の弱体化

[severity: must-fix] task-class gate を状態機械として固定していない

攻撃シナリオ — 次のいずれも「読みやすい短縮」で起こせます。

- 問題報告をクラス 1 から始める既定を落とし、暗黙に修正権限を得る
- 「迷ったら重い方」を先に置き、明示的な編集依頼がない報告までクラス 2 にする
- 昇格時の遡及確認を落とし、`git status` や handoff 確認前に編集する
- 「逆方向には降格しない」を落とし、編集後にクラス 1 を名乗って worklog・検査を省く
- 「handoff をすべて読む」を「関連するもの」に変え、並行作業を上書きする

根拠 — [CLAUDE.md:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:24)、[CLAUDE.md:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:32)、[CLAUDE.md:34](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:34)、[CLAUDE.md:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:43)、[AGENTS.md:9](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/AGENTS.md:9)。

提案 — クラス、遷移、遷移条件、遷移時の副作用、省略可能な確認を表にした invariant ledger を先に作ってください。語順、例外の優先順位、番号 1〜3、昇格のみ・降格不可を検査対象にします。

[severity: must-fix] 信頼中核と機械防壁の境界が一語で広がる

攻撃シナリオ — 「docs」を「リポジトリ内の資料」、「ユーザーの直接メッセージ」を「ユーザー由来の内容」と言い換えるだけで、submodule、output、取得ログ、引用内命令まで信頼対象になります。また、例示を箇条書き化すると列挙が網羅的に見え、checkpoint 等の未列挙入力が監査対象外になります。

根拠 — [CLAUDE.md:89](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:89)、[CLAUDE.md:92](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:92)、[hooks/README.md:13](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/hooks/README.md:13)、[hooks/README.md:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/hooks/README.md:106)。

提案 — `すべて`、`外から`、`直接`、`採用・コミットする前`、`指示ではない` を意味上の固定トークンにしてください。hook は「責務・配線・既知限界へのポインタ」であり、全製品で執行済みとは書かない、という負の契約も固定します。

## 3. boot cost

[severity: should] ±5% 行数は誤った予算指標

攻撃シナリオ — 行数を守りながら長文化できますし、読みやすい改行だけで違反扱いにもなります。現行 `CLAUDE.md` は 159 行・13,243B。D57 直後の 135 行・10,758B から既に 24 行、2,485B、約23.1%増えています。task-class gate など必要な増分を戻せという意味ではありませんが、明瞭化だけでさらに +5% を許す余地はありません。

根拠 — [plan-clarity.md:29](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:29)、[docs/decisions.md:813](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/decisions.md:813)、[docs/decisions.md:2227](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/decisions.md:2227)、[docs/decisions.md:2239](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/decisions.md:2239)。

提案 — CLAUDE.md は「論理行純増 0、UTF-8 byte/token 見積りは現行以下」を基本予算にしてください。物理改行は byte 総量が減る場合に限り許容します。圧縮候補は、部分読み指示の重複、subagent/hook/provenance のポインタ部、現在地と作業手順 1/7/8 の重複です。絶対規律を圧縮原資にしてはいけません。「重複も削除不可」は「固有条件を落とさない lossless dedup」に緩めないと D57 と両立しません。

## 4. proposal-only 運用

[severity: must-fix] 未裁定案を trusted docs へ洗浄できる

攻撃シナリオ — proposal を `output/insights` に置くこと自体は妥当ですが、worklog に候補文を逐語転載すると、untrusted な output から信頼中核である docs へ昇格します。コミット済みという事実も、次セッションに「承認済み」と誤認させます。

根拠 — [plan-clarity.md:23](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:23)、[CLAUDE.md:89](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:89)、[output/README.md:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/README.md:47)、[output/README.md:58](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/README.md:58)。

提案 — artifact に最低限 `status: unadjudicated`、`authority: none`、`default: do-not-apply`、基準 commit、旧文 hash、候補、反対解釈、`human_decision: pending` を持たせてください。worklog/handoff には path・hash・未裁定状態だけを書き、候補文を再掲しない。裁定が来なければ永久に非採用です。採用は人間の直接指示を受けた別変更・別 commit にします。

[severity: must-fix] 最終 commit まで相談原文が揮発領域に残る

攻撃シナリオ — Stage S/R の出力を job tmp に置き、最後にまとめて insights 化する間にセッションが落ちれば、F20 と同じ「唯一コピー消失」が再発します。逐語出力だけを保存すると F13 の巨大全文読みにも戻ります。

根拠 — [plan-clarity.md:19](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:19)、[docs/failures.md:231](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/failures.md:231)、[docs/failures.md:239](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/failures.md:239)、[docs/handoff/README.md:18](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/handoff/README.md:18)。

提案 — 各 survey/review 終了直後に repo 配下へ raw + digest + hash を保存してください。統合側は digest を読み、衝突・must-fix・反証時だけ raw に上がります。「最後に凍結」では遅すぎます。

## 5. 他文書との結合

[severity: must-fix] 見出し以外の semantic consumer が検査対象外

攻撃シナリオ — 見出し、§、D、パスを維持しても、番号や短い契約語を変えれば consumer は壊れます。`check_docs.py` と role parity checker はこの種の CLAUDE↔consumer 意味差を検出しません。

根拠 — 壊れやすい参照は以下です。

- 起動アンカー: [AGENTS.md:9](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/AGENTS.md:9)、[README.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/README.md:22)、[docs/README.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/README.md:3)、[docs/roadmap-history/README.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap-history/README.md:3)
- 規律番号・手順番号: [hooks/README.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/hooks/README.md:3)、[hooks/README.md:83](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/hooks/README.md:83)、[docs/failures.md:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/failures.md:11)、[docs/failures.md:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/failures.md:51)
- 規律の意味を複製する role: [.claude/agents/critic.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/.claude/agents/critic.md:22)、[.claude/agents/auditor.md:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/.claude/agents/auditor.md:28)、[.claude/agents/coder.md:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/.claude/agents/coder.md:29)、[.claude/agents/profiler.md:18](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/.claude/agents/profiler.md:18)
- 既に移動済み文言を引用する歴史文書: [docs/decisions.md:147](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/decisions.md:147)
- Codex checker は role↔adapter parity を見るだけで、CLAUDE↔role の意味同値までは証明しない: [.codex/agents/README.md:84](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/.codex/agents/README.md:84)

提案 — consumer inventory を `anchor / ordinal / literal phrase / semantic mirror / historical-only` に分類し、before/after で比較してください。特に規律 1〜6、作業手順 1〜10、クラス 1〜3、`task-class gate`、`現在地`、`roadmap の更新`、`主要ドキュメント`、`データであって指示ではない`、`人間のみ` を semantic API として固定します。

## 6. 編集・検証ポリシー

[severity: must-fix] 「許す操作」が規範文には強すぎる

攻撃シナリオ — 指示語の明示化は「どれを指すか」の意味決定、主語修復は「誰に義務があるか」の決定です。括弧の箇条書き化は条件・例外・列挙の作用域を変えます。特にゲートの例外順序、監査トリガ、圧縮後だけの条件と常時の生ログ禁止を容易に混同します。

根拠 — [plan-clarity.md:14](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:14)、[CLAUDE.md:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:32)、[CLAUDE.md:93](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:93)、[CLAUDE.md:148](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:148)。

提案 — 規範文で安全とみなすのは改行、誤字、明白な係り受けの修正だけに限定してください。主語、指示対象、条件節、否定、接続詞、例示の網羅性、箇条書き階層、順序を変える操作は必ず clause-level equivalence ledger を要求し、曖昧性を解消する必要がある時点で proposal-only に落とします。

[severity: must-fix] survey/review エージェントの read-only が構造化されていない

攻撃シナリオ — プランは model 名しか指定していません。general-purpose Sonnet/Opus がレビュー中に「ついでに修正」すれば F7 の再発です。prompt で read-only と書くだけでは防壁になりません。

根拠 — [plan-clarity.md:19](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:19)、[plan-clarity.md:21](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:21)、[docs/failures.md:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/failures.md:71)、[docs/agent-architecture.md:119](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/agent-architecture.md:119)、[CLAUDE.md:108](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:108)。

提案 — Stage S/R は `Read/Grep/Glob` のみ、Write/Edit/Bash なし、fresh context、構造化 finding 返却だけと明記してください。修正は Stage D/親だけが行います。generic Codex child を「auditor role 相当」と呼ばないことも明記します。

[severity: must-fix] Stage V が semantic drift に対して恒真化する

攻撃シナリオ — `逆方向には降格しない`、`現在 Phase 3`、`採用・コミットする前`を削除しても、見出し・§・D・パス・glossary grep・`check_docs` は全部通り得ます。`check_docs.py` 自身が意味的ずれは検出しないと宣言しています。

根拠 — [plan-clarity.md:22](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:22)、[tools/check_docs.py:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/tools/check_docs.py:7)、[tools/check_docs.py:140](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/tools/check_docs.py:140)、[docs/failures.md:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/failures.md:88)。

提案 — Stage V に、凍結ブロック hash、Markdown heading level/order、番号集合と順序、list nesting、規範語・条件語 inventory、consumer inventory、byte/token budget、clause ledger を追加してください。新しい検査には「凍結文を1字変える」「降格禁止を削る」「番号を交換する」positive control を通します。機械検査は意味同値を証明せず、独立レビューの前提確認に留めます。

[severity: must-fix] commit 後レビューの終了条件が閉じていない

攻撃シナリオ — 現行順序は commit → Codex review → 修正 → worklog です。レビュー修正、worklog、handoff 削除が未 commit・未検査で残るか、最初の commit だけを provenance 監査して終了できます。roadmap・CLAUDE・未裁定 proposal を一つの commit にすると、CLAUDE の危険差分も埋もれます。

根拠 — [plan-clarity.md:23](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:23)、[CLAUDE.md:151](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:151)、[CLAUDE.md:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:153)、[AGENTS.md:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/AGENTS.md:26)、[docs/ai-provenance.md:97](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/ai-provenance.md:97)。

提案 — 最終修正後の working-tree diff を独立レビューし、その後に全検査を再実行して commit してください。commit 後は provenance 監査を行い、失敗や追加修正があれば review→検査→commit→監査を再ループします。roadmap、CLAUDE 非憲法部、未裁定 proposal は分離 commit を推奨します。worklog 吸収・handoff 削除も commit 済みであることを確認してから ff します。

## プラン全体の妥当性

現状判定: 実行不可。憲法の自己保護、既存規範矛盾、検証・終了条件が未閉鎖です。  
良い部分: 見出し固定、単一編集レーン、複数レンズ、絶対規律 proposal-only の方向性は妥当です。  
再判定条件: 上記 must-fix をプランへ反映し、最終候補 diff をもう一度 read-only で敵対レビューすることです。
---

## 相談 C: 検証設計への攻撃 (codex gpt-5.6-sol reasoning=max) — 逐語

### プロンプト
```
あなたは敵対的レビュアーです。私 (Claude) はこのリポジトリ (izanagi) で docs/roadmap.md と CLAUDE.md の明瞭化リファインメント (意味を変えない文章改善) を計画しています。あなたには**検証設計と実行プロセス**を攻撃してほしい (編集対象そのものの危険地帯は別の相談で攻撃済み)。

## まず読むもの (read-only)
- /home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md (私のプラン全文 — 特に「実行設計」と「Stage V (機械検証)」)
- docs/roadmap.md と CLAUDE.md (対象ファイル)
- tools/check_docs.py (既存の機械検査が何を見て何を見ないか)
- docs/failures.md (過去の失敗型 — 特に恒真ゲート・説明と実装の食い違い・consumer 取り残しの型)
- output/insights/2026-07-17_repo-refinement-consultations.md (昨日の docs wave の検証設計と教訓 — 「オラクル天井」意味反転をレビュー段が捕まえた事例を含む)
- docs/ai-provenance.md (commit 規約)

## 攻撃してほしい論点 (検証とプロセス)
1. **意味ドリフトの機械検出の不足** — 私の機械検証は「見出し diff 空・§ 列挙一致・check_docs・glossary 語 grep・D 参照実在」。これで捕まらない意味ドリフトの具体例を構成せよ。追加すべき機械検査 (例: 規範文 (「してはいけない」「必ず」「のみ」等) の抽出リスト差分、否定語の数の一致、数値 literal の集合一致) を提案せよ
2. **敵対レビューのレンズ設計** — opus 3 レンズ (意味ドリフト狩り / 参照整合 / failures 型タグ) で足りるか。昨日の wave では編集エージェント自身の自己申告漏れ・レビュアーの古い根拠による誤復元 (C2 競合) が起きた。同型の事故を防ぐレーン設計を提案せよ
3. **サンプルサイズと独立性** — survey レンズ 4 本 (sonnet) の見逃し率、draft を opus 1 レーン/ファイルに集約するリスク、レビューの独立性 (draft と同じ worktree を見る = 原文をどう参照するか)。diff だけ見るレビューと全文再読レビューの使い分けを設計せよ
4. **プロセス事故** — 同一ファイルへのレーン競合、handoff/worklog 契約、commit 粒度 (roadmap / CLAUDE.md 非規律部 / insights の 3 コミット案)、AI-Agent trailer、check_ai_provenance、ローカル main ff のタイミング (ユーザーが並行で push/merge した場合)。穴を突け
5. **モデル配分** — survey=sonnet / draft=opus / review=opus / 機械検証=sonnet という配分の弱点。どの段が最も知能を要するか
6. **最終ゲートの設計** — codex 独立最終レビュー (全 diff) の後に残所見をサブエージェントで修正するループの終了条件。「レビューが clean になるまで」は無限ループしうるか

## 出力形式
所見ごとに: [severity: must-fix / should / nit] タイトル / 攻撃シナリオ (具体的に何がどう壊れるか) / 根拠 (file:line) / 提案 (プラン・検証設計への修正)。最後に「検証設計全体の妥当性」を 3 行で総括。所見が無い論点は「異議なし」と明言せよ。
```

### 回答 (逐語)

結論から言うと、現行案のまま実行するのは危険です。must-fix 10 件、should 3 件、nit 0 件です。

## 1. 意味ドリフトの機械検出

### [severity: must-fix] Stage V は構造保存ゲートであって意味保存ゲートではない

**攻撃シナリオ:** 次の変異は、現行 Stage V の全項目を通り得ます。

- roadmap の「noise floor **以下**なら差なし」を「**以上**なら差なし」にする。否定語数・数値・見出し・§・D・用語は不変ですが、採否が反転します。[roadmap.md:208](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:208)
- `within-run` と `between-run` の役割を入れ替える。surface form の全集合は不変ですが、偽 faster を防ぐ主防壁が壊れます。[roadmap.md:203](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:203)
- 「build-cache key からは外してよい／campaign identity には必ず含める」の述語を交換する。`よい` と `必ず` の個数も用語も不変です。[roadmap.md:298](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:298)
- provenance の「commit **前**に読む／commit **後**に監査」を交換する。語と参照は全て残ります。[CLAUDE.md:119](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:119)
- 「**短い** read-only 作業では handoff 不要」から「短い」だけ落とす。規範語・否定語・数値は変わりませんが、例外範囲が全 read-only 作業へ拡大します。[CLAUDE.md:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/CLAUDE.md:24)
- オラクル天井の「評価回数の**下限**」を「上限」にする。同じ用語・式・数値を保ったまま意味が反転します。前 wave の事故と同型です。[glossary.md:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/glossary.md:17)

既存 checker 自身も、意味的なずれは検出不能と明記しています。[check_docs.py:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/tools/check_docs.py:7) Stage V はその上に見出し・参照・語の存在検査を足しただけです。[plan-clarity.md:22](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:22)

**提案:** Stage V の合格条件に、Git から自動生成する「全変更 hunk 台帳」を加えてください。各変更単位について旧文と新文を対応づけ、少なくとも次を記録します。

- 主体・行為・対象
- MUST / MUST NOT / MAY / ONLY / 推奨
- 肯定・否定
- 量化・適用範囲
- 条件・例外
- 前後関係
- 数値と単位
- D / § / パスと、その主張への結び付き

レビュアーは「旧文⇒新文」「新文⇒旧文」の双方向含意を個別に判定し、片方向だけなら drift とします。絶対規律節は見出し境界で抽出し、候補との byte 完全一致を別ゲートにしてください。

### [severity: must-fix] 否定語数・数値集合・規範文抽出も、そのままでは恒真化する

**攻撃シナリオ:** `N=5` と「初期 3 ラウンド」を交換すれば数値集合は同じです。[roadmap.md:196](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:196) 否定語は、重要な節から一つ消して別の無害な節へ一つ追加すれば総数を維持できます。規範文は分割・結合が許されるため、文数一致を要求すると正当な明瞭化を拒否し、数だけ合わせる方向へ最適化されます。

D 参照も、現行 checker が見るのは「その番号が実在するか」だけです。[check_docs.py:156](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/tools/check_docs.py:156) D29 と D32 を別の主張間で交換すれば、全参照が実在し、集合も同じまま provenance だけ壊れます。

**提案:** 追加検査は次の位置づけにします。

- 数値は集合でなく `(literal, unit, hunk-id, 係る述語)` の多重集合で比較する。
- D / § / glossary 語は全文の集合でなく、変更前後の同一 claim 単位で比較する。
- 規範語は `必須・必ず・してはいけない・禁止・のみ・だけ・限り・任意・推奨・省略・保証しない・以上・以下・前・後・ただし` 等を抽出するが、差分ゼロを合格条件にせず「全差分に人手の対応判定があること」を条件にする。
- 新規 checker は `以下→以上`、D 交換、条件削除などを故意に入れて赤になる positive control を持たせる。これは F9 の明示的な再発防止契約です。[failures.md:94](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/failures.md:94)

### [severity: should] 「参照整合」は存在検査でなく claim–根拠の結合検査にする必要がある

**攻撃シナリオ:** glossary 語が文書内の別の場所に一度残っていれば、重要な用例の日本語化・誤用を「到達性あり」と判定できます。パス検査も拡張子付きの限定パターンであり、ディレクトリ参照や削除された参照そのものは検出しません。[check_docs.py:83](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/tools/check_docs.py:83)

**提案:** 変更前の各 hunk から D / § / path / code span / glossary surface form を取り出し、新 hunk との対応を検査してください。削除された参照・引用句については repo 全体の consumer 検索も行います。Markdown のリンク先・anchor 解決と、Markdown AST の見出し順・リスト階層・コードフェンス構造の一致も別検査にします。

## 2. 敵対レビューのレンズ設計

### [severity: must-fix] 3 レンズでは「申告漏れ」と「根拠の時点競合」を担当する者がいない

**攻撃シナリオ:** 編集者が変更 hunk を一つ自己申告し忘れると、3 レンズとも提示された変更一覧だけを見て終了できます。また、レビュアーが古い decision や旧実装を根拠に「復元」すると、原文より古い状態へ戻すことがあります。これはレビューが善意でも起き、C2 型の競合を再現します。

同じ親が発見・修正・裁定・checker 合格を握る自己承認は、昨日の相談でも明示的に危険とされています。[consultations.md:267](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/insights/2026-07-17_repo-refinement-consultations.md:267) 実際、既存 checker 成功後の独立最終レビューが複数の重大所見を発見しています。[consultations.md:364](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/insights/2026-07-17_repo-refinement-consultations.md:364)

**提案:** Stage R を次のレーンへ変更します。

1. **R0 coverage auditor:** Git が列挙した全 path・hunk・削除行を台帳化し、エージェント自己申告と照合する。未割当 hunk は即失格。
2. **R1 diff-only semantic:** draft の理由を見ず、旧・新 hunk と包含節だけから双方向含意を判定する。高リスク hunk は独立 2 名。
3. **R2 full-text:** diff を先に見ず、base と candidate の全文から規範・歴史・因果関係をそれぞれ要約して比較する。
4. **R3 authority/reference:** 数値、negative result、D / §、手順順序、consumer を検査する。
5. **R4 process/provenance:** 禁止節 hash、変更 allowlist、レビュー coverage、trailers、handoff を監査する。

意味保存タスクでは、意味の正本は固定 base の原文です。外部資料との矛盾は「既存文書の別問題」として insight に出し、このタスク内で原文を修理しない、という裁定規則を明記してください。根拠には path だけでなく commit SHA と authority owner を要求します。

### [severity: should] failures 型タグは独立レンズではなく、全所見へ掛ける横断チェックである

**攻撃シナリオ:** 「failures 型タグを確認した」とだけ報告し、意味ドリフト担当が見つけた所見へ `[ドリフト]` と付ければ、このレーンは独自の検出を一件も行わず完了できます。型タグは索引でありテスト手順ではありません。[failures.md:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/failures.md:17)

**提案:** 型ごとに具体的な負例へ展開してください。

- `[恒真ゲート]`: checker を故意に壊して発火確認
- `[手順漏れ]`: Git 実 diff と編集者申告の差
- `[捏造/幻覚]`: 数値・歴史的主張を base と一次 authority に照合
- `[ドリフト]`: 主体・述語・条件・例外・時系列の双方向含意
- `[権限逸脱]`: reviewer の write surface 不在を確認

タグは R1〜R4 の各 finding に付与し、「タグ専用 reviewer」は廃止する方が明確です。

## 3. サンプルサイズと独立性

### [severity: must-fix] survey 4 本は見逃し率を推定できるサンプルではない

**攻撃シナリオ:** 同じ Sonnet、同じ system prompt、同じ原文を使う 4 呼出しは独立な Bernoulli 試行ではありません。レンズを分割すると、むしろ一つの規範文を意味面から見るのは一レーンだけになります。したがって「4 本通したから見逃し率が下がった」という解釈は成立しません。監査者の限界は roadmap 自身も「確率的に下げるだけ」としています。[roadmap.md:224](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:224)

F15 も、テスト本数ではなく実際の失敗分布を含むかが問題だったと記録しています。[failures.md:141](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/failures.md:141)

**提案:** survey は編集候補発見専用とし、安全性の証拠に数えないでください。安全性は全 paragraph/hunk の census で担保します。さらに、本番候補とは別のコピーに次の blind mutation を注入してレビュー系の回帰試験にします。

- MUST↔MAY、禁止↔許可
- のみ↔少なくとも
- 条件・例外の削除
- 以下↔以上、前↔後
- 主体交換
- within/between の交換
- 数値の claim 間交換
- D / § の交換
- negative result の勝者・敗者交換
- 申告されない隠し hunk
- 古い根拠による誤復元
- オラクル天井の下限↔上限

ensemble が全ての critical mutation を捕捉することを機能ゲートにします。ただし、この結果から実文書上の統計的な見逃し率は推定しないでください。

### [severity: must-fix] 同じ worktree を見ること自体より「可変な原文を読む」ことが独立性を壊す

**攻撃シナリオ:** reviewer 実行中に draft や親が編集を続けると、同じ path が別内容になります。`main` を比較元にすると、並行 merge により base 自体も動きます。reviewer が記憶上の原文や dirty file と比較すれば、古い根拠による復元事故が起きます。

handoff 契約も、監査対象を dirty worktree でなく固定 commit にするよう要求しています。[handoff/README.md:40](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/handoff/README.md:40) また prompt 上の read-only は構造的権限遮断の代用になりません。[failures.md:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/failures.md:71)

**提案:** 最初に full SHA の `BASE` と対象 blob hash を固定し、draft 後に clean な `CANDIDATE` commit を作ります。レビュー入力は必ず `git show BASE:path` と `git show CANDIDATE:path` から取り、作業ツリーや可動 branch 名を読ませません。レビュー中の書込みを止め、reviewer には構造的に write surface を与えないでください。

diff-only と全文再読は次のように使い分けます。

- diff-only: 微小な極性・量化・数値変更を捕らえる。draft rationale は渡さない。
- 全文再読: 変更 hunk と未変更段落のスコープ、negative-result の物語、CLAUDE/roadmap 間の整合を捕らえる。
- 修正後: delta review に加え、規範・歴史 hunkなら包含節を全文再読する。

### [severity: should] 1 draft lane/file は競合回避には有効だが、系統的な一括ドリフトを作る

**攻撃シナリオ:** 一人の Opus が 374 行を同じ簡略化方針で書き換えると、同じ誤った規範解釈が全節へ一貫して展開されます。ファイル単位所有は競合を防いでも、semantic monoculture は防ぎません。行数 ±10% / ±5% も、情報削減を暗黙の報酬にします。[plan-clarity.md:29](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:29)

**提案:** 同一ファイルを一レーンにする判断自体は維持して構いません。ただし draft は直接 commit せず、survey で承認された hunk だけの patch と変更台帳を返させます。親だけが順次適用し、機会的な追加修正を禁止します。行数目標は合否ゲートでなく報告指標に格下げしてください。

## 4. プロセス事故

### [severity: must-fix] handoff・worklog・共有ファイルの single-writer 契約が実行設計にない

**攻撃シナリオ:** 長い survey/draft/review 中にセッションが死ぬと、計画と commit だけ残り、どの hunk がレビュー済みか復元できません。複数レーンが insight・worklog・handoff を直接更新すれば、対象ファイルを分離していても共有面で競合します。現行案は末尾に `worklog` とだけ書き、handoff 作成・10 分更新・吸収削除を落としています。[plan-clarity.md:23](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:23)

正本は、作業中は handoff に集約し、正常終了時に一度だけ worklog へ吸収すると定めています。[handoff/README.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/handoff/README.md:10) 相談全文を一時領域だけに置くことも禁止されています。[handoff/README.md:18](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/handoff/README.md:18)

**提案:** 実行順へ明記します。

1. クラス 2 起動確認、残 handoff、`git status`、BASE 固定
2. 親専用 handoff 作成
3. 子は patch/findings のみ返し、親だけが repo 内共有物を書く
4. 節目・10 分ごとに hunk coverage、候補 SHA、未解決 finding を更新
5. consultation 全文は同じセッションで insight へ永続化
6. 正常終了時に worklog へ一度吸収し、handoff 削除
7. 削除後の最終 status/checker を確認

### [severity: must-fix] 固定の「3 コミット案」と final review の順序が、未レビュー差分を必ず生む

**攻撃シナリオ:** roadmap / CLAUDE / insight の 3 commit 後に Codex が finding を出すと、修正 commit と worklog commit は最初の「全 diff review」の対象外です。review 結果を insight に逐語保存すれば、その保存自体も reviewer が見ていない新差分になります。逆に既存 commit を amend すると、レビュー済み SHA が変わります。

また、ファイル単位の固定分割では、roadmap と CLAUDE の対応する表現が一時的に不整合な commit を履歴へ残し得ます。commit はファイルでなく invariant 単位にすべきです。

**提案:** 次の二層に分けてください。

- **content candidate:** 対象文書と、レビュー前に存在する相談・提案を atomic commit 化。各 commit 単独で green。
- **closure metadata:** 最終レビュー逐語、親裁定、worklog、handoff 削除だけの最後の commit。

Codex review は content candidate SHA を固定して実施します。finding 修正は追記 commit とし、全機械検査、delta review、必要な節全文 review を行った後、最後に content 全 diff を一度再レビューします。最終レビュー自身の逐語は自己包含できないため、「全 diff」の射程を content paths と明示し、closure commit は allowlist と append-only 検査で閉じます。

### [severity: must-fix] 必須 checker と provenance の「実質的寄与」確認が抜けている

**攻撃シナリオ:** Stage V は `check_codex_agents.py` と commit 後の `check_ai_provenance.py` を列挙していません。しかし AGENTS はクラス 2/3 の完了条件として両方を要求しています。[AGENTS.md:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/AGENTS.md:26)

さらに `check_ai_provenance.py` が確認するのは trailer の有無・形式・重複だけです。[check_ai_provenance.py:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/tools/check_ai_provenance.py:56) 編集者が survey/reviewer 一名を申告し忘れても構文上は green です。規約は UI・CLI・設定による独立確認を求めています。[ai-provenance.md:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/ai-provenance.md:81)

**提案:** orchestration 側で `agent-id / product / model / reasoning / role / 採用された finding / 影響 commit` の寄与台帳を自動生成し、自己申告でなく実呼出し記録と親の採否から trailer を作ります。各 commit で次を実行してください。

1. 最新 status・変更 allowlist・`git diff --check`
2. 意味保存 checker と mutation positive controls
3. 関連テスト
4. `check_codex_agents.py`
5. `check_docs.py`
6. commit message を `check_ai_provenance.py --message-file` で事前検査
7. commit
8. `check_ai_provenance.py` を HEAD まで実行

final-review 後の修正にも同じ一式を再実行します。

### [severity: must-fix] ローカル main への自動 ff は並行ユーザー作業と両立しない

**攻撃シナリオ:** 計画は base を local main `60da9b8` に固定する一方、origin は遅れており、最後に local main を ff するとしています。[plan-clarity.md:8](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:8) 途中でユーザーが別 worktree から main を進める、merge する、push する場合、比較基準が移動します。そこで rebase/merge すればレビュー済み tree が変わり、main worktree が dirty ならユーザー差分にも触れます。

**提案:** デフォルトでは ff せず、最終 feature SHA・BASE・検査結果をユーザーへ渡してください。明示的に local ff まで委任された場合だけ、main の現在 SHA と対象 worktree の clean 状態を再確認し、開始時 SHA と違えば停止します。許されるのは、main が想定した祖先である場合の `--ff-only` だけです。rebase、競合解消、moving main に対する再統合は、新しい candidate と全レビューを必要とします。

## 5. モデル配分

### [severity: should] 最も知能を要するのは draft でなく意味同値性と根拠競合の裁定である

**攻撃シナリオ:** draft と review を同じ Opus 系に置くと、文章を改善したときの解釈をレビューでも自己整合的に再採用しやすくなります。一方、「機械検証=Sonnet」とすると、決定的であるべき検査にモデル判断を混ぜ、機械検証の外観だけが残ります。昨日も checker green 後に独立モデルが重大所見を発見しています。[consultations.md:306](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/insights/2026-07-17_repo-refinement-consultations.md:306)

**提案:** 配分を次のように変えます。

- survey Sonnet: 読みづらさの候補発見だけ
- draft Opus: 承認 hunk の限定編集
- 機械検証: モデルではなく決定的スクリプトを親が実行。Sonnet がスクリプトを作るなら別モデルの監査と mutation test 必須
- semantic diff review: Opus と異製品モデルの二系統
- full-text / authority adjudication: 最高知能モデル
- 最終統合・real/refuted/accepted-risk 裁定: 最高知能の親
- Codex 独立レビュー: commit 後の飾りでなく、candidate 採用前の意味ゲートに含める

## 6. 最終ゲート

### [severity: must-fix] 「clean になるまで」は停止条件でなく、無限修正器になる

**攻撃シナリオ:** reviewer は常に新しい should/nit を作れます。各修正が新しい意味ドリフトを導入し、次の reviewer がそれを直すと往復します。前 wave も最終レビュー後に wave 2 修正を要しています。[consultations.md:368](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/insights/2026-07-17_repo-refinement-consultations.md:368) 現行案には、どの severity が blocker か、修正後に何を再レビューするか、何巡で諦めるかがありません。[plan-clarity.md:23](/home/SFC/tanab/.claude/jobs/9b2bec65/tmp/plan-clarity.md:23)

**提案:** 次の有限状態機械を事前登録してください。

1. `C0` を全 diff review。
2. finding を `real / refuted / accepted-risk` に裁定。
3. open must-fix だけを修正。should は修正または理由付き accepted-risk、nit は非 blocker。
4. 全機械検査、修正 delta review、規範・歴史 hunk の包含節再読。
5. repair round は最大 2 回。
6. 同じ hunk が再度 must-fix、または根拠競合が解けない場合、その hunk を BASE 原文へ戻す。広域なら対象ファイルを戻す。
7. 原文自体の誤りが露呈した場合は clarity task から分離し、人間裁定付きの別変更にする。

終了条件は「open must-fix 0、全 hunk に必要なレビュー記録あり、全 should に disposition あり、機械検査 green、最後にレビューした content SHA が不変」です。「所見ゼロ」や「nit ゼロ」は要求しません。意味保存タスクでは、改善を諦めて原文へ戻すことが安全で有限な fallback です。

## 検証設計全体の妥当性

現状: 参照・構造の保存には有効ですが、意味保存を合格判定できず、実行開始には不十分です。  
修正後: immutable な BASE/CANDIDATE、hunk 全数台帳、双方向含意、異種レビュー、mutation control を入れれば妥当になります。  
最終判定: handoff・provenance・必須 checker・有限終了条件・main 統合境界をプランへ明記するまで着手不可です。
---

## プラン v2 (相談 A/B/C + 参照インベントリ裁定後の事前登録、実行前凍結)

# プラン v2: roadmap.md / CLAUDE.md 明瞭化リファインメント (相談 A/B/C 反映後の事前登録)

相談 A (must-fix 9 / should 3)・B (must-fix 11 / should 1)・C (must-fix 10 / should 3) + 参照インベントリを裁定。
全 33 所見 real (裁定差分は §裁定注記)。以下を実行前に凍結する。

## 1. 不変量 (機械検査、決定的スクリプト + positive control 必須)

- **byte-frozen**: (1) CLAUDE.md「## 絶対規律」ブロック全体 (見出し境界で抽出、SHA-256 一致)、
  (2) CLAUDE.md「絶対規律 = 憲法。変更できるのは人間のみ」を含む三層可変性の権限規則行、
  (3) roadmap.md 冒頭の統治段落 (行 3)
- **アンカー**: 見出し集合・順序・レベル完全一致 / roadmap § トークン多重集合一致 ((3')・§3.4-4 等の
  副番号含む) / Tier 0-3・(a)(b1)(b2)(c)・Phase 名 / CLAUDE.md 作業の進め方の番号項目 1〜10 の個数・
  順序 / クラス 1〜3 / 参照インベントリ確定リストの逐語アンカー (「読み方」「Phase 完了監査と
  引き継ぎ監査 (劣化の遡及検出)」「観測者効果の分離」(CLAUDE↔roadmap 二重アンカー、両側同文言を維持)・
  「盛らない」「バカ」等) の rg -F 照合
- **内容**: D 参照集合一致 / 数値 literal 多重集合一致 (単位付き) / glossary 語 surface form 保持 /
  コードブロック数・内容一致 / check_docs.py green
- **予算**: CLAUDE.md は総 byte 現行以下・論理行純増 0。roadmap は節別 byte 計測し、冒頭統治・§1・§2・
  §3.3・§3.6・§3.7-3.8・§4・§7・§9 は net-zero 帯 (増補禁止)。行数は報告指標であり合否ゲートにしない
- **報告型検査** (ゼロ差分を要求しないが全差分に人手 disposition 必須): 規範語 inventory 差分
  (必須・必ず・してはいけない・のみ・だけ・限り・推奨・省略・保証しない・以上・以下・前・後・ただし)、
  否定構造の差分
- positive control: 凍結 byte 改変 / 以下↔以上 / D 交換 / 項目番号交換 / アンカー削除 → checker が
  各々赤になることを実証してから使う (F9 契約)

## 2. 編集ポリシー (三分類 + hunk 規則)

- **byte-frozen**: 上記。編集もコミットも不可。改善案は提案台帳のみ
- **semantic-lock (layout-only)**: roadmap §1/§2/§8/§10、§3.1〜3.4 の保証・防壁記述 (line 169 は五要素
  exact)、§3.6+§4 (不可分クラスタ、七項目 invariant、同一レビュー単位)、§3.7 の規範/推奨併記、
  CLAUDE.md の task-class gate・信頼境界・hooks/provenance/サブエージェント節。許すのは改行・
  誤字・明白な係り受け修正・既存語のみの箇条書き化。語彙置換・条件節/例外/主体/指示対象の変更禁止
- **normative-care**: 上記以外の規範文。長文分割・括弧解消可。ただし hunk ごとに意味署名
  (主体/modality/対象/条件/例外/時制/epistemic status/根拠) を台帳化し双方向含意レビューを通す
- **safe-prose**: 非規範の背景説明。通常の明瞭化可
- 共通禁止: 新しい例・因果説明・解釈の追加 / 曖昧性の一方を選ぶ書き換え (→提案台帳へ) / 凍結記録の
  行番号参照の追従修正 / glossary 解説の roadmap への再注入 / 遡及注記の時系列・評価語
  (「negative result」「実際に起きた移行は違う」等) の非逐語化。重複は lossless dedup のみ検討し
  normative-care 扱い
- 既知の規範矛盾 (CLAUDE.md:93 監査義務形 vs roadmap §3.7 推奨) は両側とも不可触。提案台帳へ
  人間裁定案件として記載
- 意味の正本は BASE 原文。外部文書との矛盾を発見しても本タスク内で「修理」しない (insight へ報告のみ)

## 3. 実行順 (BASE/CANDIDATE 固定、single-writer)

0. BASE = 60da9b8 (worktree clean 確認済)。対象 blob hash 記録。checker + mutation control を先に整備
1. Survey census (読み取り専用レーン、sonnet ×4 + opus 統合): 全段落を分類し、編集候補 hunk と
   risk class を列挙。survey は候補発見専用で安全性の証拠に数えない
2. 親が編集 worklist を承認 (approved hunk list)。proposal-only 項目を分離
3. Draft (opus、1 ファイル 1 レーン、approved hunk のみ、hunk 台帳返却必須)。親が R0 coverage audit
   (git 実 diff の全 hunk vs 承認リスト、未承認 hunk は revert) → CANDIDATE を一時 commit
4. Review 系は全て BASE/CANDIDATE の git show 読みで固定 (作業ツリーを読ませない。レビュー中は書込停止):
   - 先に blind mutation 回帰: 変異注入コピーに同一レビュープロンプトを当て、critical mutation 全捕捉を
     機能ゲートにする (統計的見逃し率は主張しない)
   - R1 意味 diff (opus ×2 独立、rationale 非開示、双方向含意、片方向のみ = drift)
   - R2 全文 (opus、BASE/CANDIDATE を独立要約して比較)
   - R3 参照/権威 (sonnet + checker 出力、変更 hunk の consumer 照合)
   - 異製品第二系統: codex による意味 diff レビュー (SHA 固定)
   - failures 型タグは各 finding への横断付与 (専用レーンにしない)
5. Repair FSM (事前登録): blocker = must-fix のみ / should は修正または理由付き accepted-risk / nit 非
   blocker。修正ラウンド最大 2。同一 hunk が再 must-fix なら BASE 原文へ戻す。終了条件 = open must-fix 0 +
   全 hunk にレビュー記録 + 全 should に disposition + 機械検査 green + 最終レビュー済み content SHA 不変
6. Commit 二層: content candidate (roadmap 単独 / CLAUDE.md 非規律部 / 提案+相談 insight の 3 commit、
   各 commit 単独 green、AI-Agent trailer は実呼出し記録から生成) → 全 diff 最終レビュー (codex) →
   残 must-fix 修正 (追記 commit + delta review) → closure commit (worklog 吸収・handoff 削除・最終
   レビュー逐語)。commit ごとに: git diff --check / checker / check_docs / check_codex_agents /
   commit / check_ai_provenance to HEAD
7. main 統合: ユーザー既定 (「ローカル main に入れて、push は自分でやる」2026-07-17 指示) に従い
   --ff-only 限定で ff。ただし main が開始時 SHA (60da9b8) から動いていたら停止してブランチ引き渡し。
   push はしない (Pegasus 運用)

## 4. 提案台帳 (byte-frozen / 曖昧性解消の改善案)

output/insights/2026-07-17_claudemd-discipline-proposals.md に凍結。各項目:
status: unadjudicated / authority: none / default: do-not-apply / 基準 commit / 旧文 sha256 / 候補 /
反対解釈 / human_decision: pending。worklog・handoff には path と状態のみ書き、候補文を転載しない。
採用は人間の直接指示による別 commit

## 5. 裁定注記 (相談所見との差分)

- C の「draft は patch 返却、親が適用」→ draft レーンの直接編集を許すが、R0 coverage audit (承認外
  hunk の機械検出 + revert) で同じ保証を得る (worktree 分離と hooks が既にあるため)
- C の「ff はデフォルトでしない」→ ユーザーの明示既定 (前夜の指示) があるため --ff-only + SHA 不動
  確認付きで実施。動いていたら停止
- B の「CLAUDE.md 圧縮候補」→ 本タスクは明瞭化であり圧縮 wave ではない。lossless dedup のみ、
  byte 純増ゼロを守る範囲で実施

---

## survey census の親裁定 (2026-07-17)

6 レーン 66 所見 (生出力は output/insights/2026-07-17_clarity-survey-findings.json に凍結) を重複統合し裁定:
- 承認 21 hunk (roadmap layout-only) + 条件付き 3 hunk (CLAUDE.md、byte/行中立を lossless dedup で自弁できる場合のみ)
- proposal 台帳行き 8 件 (byte-frozen 帯 3・真の曖昧性 3・語順再構成 1・記号意味確定 1)
- 却下 11 件 (Markdown 段落内改行は再結合され効果が出ない / 分割が係り受けを変える / benefit low)
- checker の net-zero 帯を「総 byte 不増」から「内容文字 (非空白・非マーカー) 不増 + 総 byte +10% 上限」に修正 (相談 A#11 の趣旨に整合)。positive control m11 (語の増補=RED)・negative control m12 (正当な箇条書き化=GREEN) を追加し 12 変異で再実証

### 承認済み worklist (逐語)

```
# 承認済み編集 worklist (親裁定 2026-07-17、BASE=60da9b8)

行番号は BASE 時点。編集は必ず逐語 quote で位置特定せよ (自分の編集で行がずれるため)。
承認 hunk 以外への変更は R0 coverage audit で機械検出され revert される。

## 共通の絶対制約
- 語彙置換禁止。既存の語だけを使う。新しい例・説明・解釈・言い換えの追加禁止
- 見出し・§ 番号・D 番号・数値・コードブロック・技術用語 surface form・太字強調の範囲は不変
- 遡及注記の時系列・評価語 (「negative result」「実際に起きた移行は違う形だった」「当初案から変更」「意図的非対応」等) は一字も変えない
- 許す操作: 改行 / 箇条書き化 (子箇条含む) / 段落分割 / ダッシュ・括弧を句点や箇条に置き換える記号調整 / 番号マーカー付与
- net-zero 帯 (roadmap 冒頭・§1・§2・§3.3・§3.6・§3.7・§3.8・§4・§7・§9): 内容文字 (非空白・非マーカー) を 1 字も増やさない。マーカー・改行の追加は可

## roadmap.md (21 hunk)

- [R-9] L9 読み方段落: 「...節名 (§) で引く — 全文を...」のダッシュを句点にし 2 文へ分割。語追加なし
- [R-73] L73 (b) 項目: (b) 総論 / (b1) 定義 / (b2) 定義 / Phase 3 の着手順 をそれぞれ子箇条 (インデント) に分割。
  括弧注記 ((P2-4 backoff が成立例) / (未検証仮説) / (順序は D32 で確定) / (phase3.md 後続段 7)) は対応する項目に残す
- [R-80] L80: 太字括弧の遡及注記 (**この比較は P2-5 で実施済み...物語に転じた**) を、括弧を外して独立の子行
  (例: 改行 + インデント + 「→ **この比較は...**」) に切り出す。内容逐語保持
- [R-81] L81: 同型。(**実際に起きた移行は違う形だった** — ...) を独立の子行へ
- [R-149] L149 Tier 1 箇条: 手法 (トレース取得〜cycle 検出) / YCSB の辺の種類と G2 / 保証範囲の限定 (自前 mini-verifier が担保するのは...保証しない) / TPC-C 拡張条件 を子箇条に分割
- [R-165] L165: 括弧内 2 文 (`TRACE=0` でも...使わない。ランタイム分岐は...汚しうる) を子箇条 2 行に分離
- [R-169] L169 ビルド等価性: 原理 (機械確認する) / 当初案からの変更 (実装は当初案...参照) / Phase 3 での一次防壁昇格と diff-of-diffs 定義 / 発火場所と fails-closed を子箇条に分割。
  五要素 (当初案 / 棄却理由 / 現行 predicate / 発火場所 / fails-closed) の文言は exact 保持
- [R-181] L181: identity の担当 / 観測者効果の分離の担当 / hook の責務 の 3 者を子箇条に分割
- [R-182] L182 §3.4-4: 入力側隔離の定義文と、出力側隔離との対比 (括弧内の限定含む) を分離
- [R-196] L196: WAL の括弧内説明 (campaign スコープ...D13) を分離し、主語述語 (WAL には...残し) を連続させる。語順不変で括弧を後置の文または子行にする
- [R-205] L205 §3.6(3') 太字段落: 前提 (決して同一セッションで測らない) / 結論 (採否の floor は between-run であるべき) / 機序 (within-run は...偽 faster を出す) / fresh 下限と保守側採用 / high-abort の分散 を文・子箇条単位に分割
- [R-209] L209 §3.6(4) MWU 帯: 主防壁 = between-run floor 丸め / MWU = 弱い sanity / near-floor 帯 = cross-run 再現 の役割が並列に見えるよう子箇条化。「上記第1項」の語句は変えない
- [R-216] L216 §3.7: 4 つの劣化事例 (reward hacking の鏡像 / consumer 取り残し / 恒真な空証文 / 計測汚染) を箇条書き化。各括弧内は逐語保持
- [R-220] L220: 監査テンプレの 3 段階 (集中攻撃 / 別エージェント再検証 / git show 照合) を番号箇条化
- [R-235] L235 §3.8: 4 つの再開手段 (CLAUDE.md「現在地」/ worklog / WAL リプレイ / handoff insight) を箇条書き化。WAL の括弧内説明は当該項目の子行へ
- [R-243] L243 ループ主導権段落: 原則 / 現状の部分実装 / 劣化機序 / orchestrator 主導の利点 / 8c 移行の根拠 の論点ごとに改段落のみ (箇条書き化不要、語追加なし)
- [R-271] L271 §4 太字ただし書き: 「のみ使う」/「使わない」/「採否 floor は between-run で別ドライバが確定」の 3 論理単位をダッシュ位置で文分割。太字範囲は分割後も同じ文言に付く形を保つ
- [R-279] L279 §5: 前段の規範文群と「別環境を正式計測へ採用する条件は...」を段落分割し、(1)〜(4) を番号箇条に展開。(3) の括弧注記は (3) の行に残す
- [R-289] L289 §6: 括弧内 (解剖時点のスナップショットは...D38) を独立文として括弧の外 (直前または直後) に出し、「実物は 10 プロトコル...を持つ」の主語述語を連続させる。情報は一切削らない
- [R-294] L294 §6: (a) 実行手順の矢印連鎖 (orchestrator が...clean assert、の順に固定する) を番号箇条化。
  (b) 「改変の所在は D16 の三分岐に従う」を段落分割し、三分岐 (上流還元 / izanagi-trace / patches 行き) を箇条書き化
- [R-296] L296 §6: protocol→build target / 最適化軸・trace 有無→CMake define / read 比率等→gflags の 3 対応を箇条書き化

## CLAUDE.md (条件付き 3 hunk — 予算を守れる場合のみ)

**予算 (機械検査で強制): 総 byte ≤ BASE、論理行 (非空白行) ≤ BASE、絶対規律ブロック byte 不変。**
予算を守るための削除は「完全に同義の重複の統合 (lossless dedup)」のみ許す。1 bit でも情報・条件が
落ちる統合は不可。予算内に収まらない hunk は編集せず、proposal として構造化返却せよ。

- [C-32] L32-36 task-class gate 段落: (a) 既定分類 / (b) 迷った場合 / (c) 昇格と遡及確認 / (d) 降格禁止 /
  (e) prompt 規律の注記 が読み分けられる構造化。行増は dedup で自弁
- [C-139] L139-141: em-dash 列挙 (重い処理を流してよい場所 / ノードの確保と単独性の確認 / 外乱の回避・検知・再計測) の整理。byte 中立なら
- [C-150] L150-152 作業の進め方 6: 3 規則の視認性 (byte 中立でできる範囲)

## proposal 起草依頼 (ファイル編集はしない。old→new + 反対解釈を構造化返却)

roadmap レーン:
- [P-3] roadmap L3 統治段落 (byte-frozen) の構造化案
- [P-19] roadmap L19 入力定義文の語順再構成案 (語の追加を伴うため)
- [P-118] roadmap L118-119 「human-supervised loop」前半の述語省略の解消案 (真の曖昧性 — 両解釈を明記)
- [P-209] roadmap L209 「上記第1項」の指示対象明示案

CLAUDE.md レーン:
- [P-89] L89 絶対規律 6 中核文 (byte-frozen) の構造化案
- [P-93] L93 監査発火条件 (byte-frozen) の構造化案。注意: CLAUDE.md L93 の義務形と roadmap §3.7 の
  「推奨・省略可」は既存の規範矛盾であり、どちらに寄せるかは人間裁定 — 案は「両解釈を併記」せよ
- [P-100] L100-101 自律改訂 / 大改訂 / 協議改訂の三語関係の明確化案 (roadmap L3 との整合表)
- [P-155] L155 「節目ごと + 10 分おき」の「+」の意味確定案 (両解釈を明記)
```

---

## 盲検変異回帰の結果 (2026-07-17、レビュー系の機能ゲート)

- 対象: 変異版 34e076a = 実 candidate 9997d61 + checker 不可視の意味反転 7 箇所 (within/between 役割交換・D21/D29⇔D32 クロススワップ×2・条件節削除・主防壁/sanity 交換・隠し hunk 一事例→事例・trace-enabled/disabled ラベル交換)。決定的 checker は変異版で green (=意味レビューでしか捕まらないことを事前確認)
- 結果: **R1 opus ×2 が独立に 7/7 全捕捉、偽陽性ゼロ** (実編集 19 hunk は全て preserved と正しく弁別)。D スワップは「参照集合保存のまま紐づけ交換」、within/between 反転は「トップ結論と矛盾」まで診断
- 判定: レビュー系の弁別力を実証。本番レビュー (R1×2 + R2 全文 + R3 参照、candidate=9997d61) へ進む
- 生出力: output/insights/2026-07-17_clarity-blind-regression.json。変異版 34e076a は回帰専用であり絶対に merge しない

---

## codex 第二系統レビュー (candidate 9997d61、gpt-5.6-sol reasoning=max) — 逐語

結論は不合格です。「layout-only」とは認定できず、must-fix が 2 件あります。

### 所見

- [severity: must-fix] [docs/roadmap.md 新 L73](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:73)（旧 L73、R-73） / 旧版は「(b) の内側に 2 形態」と述べ、b1・b2 の定義後に Phase 3 の着手順を別の文として置いていた。新版はコロン直下に b1・b2・Phase 3 の3つを同格の子 bullet としたため、Phase 3 の着手順が「2形態」の第3項に見える。旧版はこの分類関係を含意せず、旧⇒新が破れる / 子 bullet は b1・b2 の2つだけにし、Phase 3 文は空行を挟んだ `(b)` 項目内の continuation paragraph に戻す。

- [severity: should] [docs/roadmap.md 新 L194](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:194)（旧 L181、R-181） / 旧版では、source digest と diff-of-diffs が一次防壁を担い、hook が第二防壁という共有述語を持つ連続文だった。新版では source digest の bullet が「後ハッシュ、」で終わり、`一次防壁として担い` が次の diff-of-diffs bullet にだけ入る。source digest も一次防壁であるという D30 の分類が視覚・構文上弱まり、一次/第二防壁の対応を「diff-of-diffs のみ一次」と読める / R-181 を原文へ戻すか、各項目に述語を明記する semantic edit として再承認する。

- [severity: must-fix] [docs/roadmap.md 新 L249](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:249)（旧 L220、R-220） / 旧版末尾の `(Phase1 完了監査…D19、audit-2026-06-30…)` は、集中攻撃・別エージェント再検証・`git show` 照合からなる監査テンプレ全体の実績だった。新版では括弧全体が番号項目3の内部に入り、D19 と real/refuted 実績が `git show` 照合だけの根拠・成果に見える。主張と D/実績の紐づけが狭まり、双方向含意を満たさない / 括弧を番号リスト終了後の独立段落へ移し、3段階全体に掛ける。

- [severity: should] [docs/roadmap.md 新 L83](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:83)（旧 L80–81、R-80/R-81） / `  →` 行は Markdown 上の子要素ではなく、直前 paragraph の soft/lazy continuation である。通常レンダリングでは改行が空白へ畳まれるため、worklist が求める「独立行化」にならない。意味語は保たれるが、明瞭化の主張と Markdown 構造が不一致 / 矢印行の前に空行を入れ、同じ2空白インデントで同一 list item 内の第2段落にする。

- [severity: should] [consultations.md L141](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/insights/2026-07-17_roadmap-claudemd-clarity-consultations.md:141) ほか / 設計文書には、この mutable worktree の `docs/roadmap.md:<line>` を指すリンクが55個あり、今回の行増加後は45個（旧36行）が意図した箇所からずれた。例として旧 L80 の negative result は新 L83–84、旧 L169 の diff-of-diffs は新 L179–182、旧 L220 の監査テンプレは新 L249–252だが、リンク先は旧番号のまま別内容を指す / `BASE=60da9b8` の commit 固定参照へ置換するか、§・見出し参照にする。逐語凍結を維持するなら訂正表を追記する。

### 観点別判定

1. 双方向含意: 異議あり（R-73、R-181、R-220）。
2. 対概念: within/between-run、trace-enabled/disabled、主防壁/MWU sanity は異議なし。一次/第二防壁のみ上記 R-181。
3. D・§ の紐づけ: D参照42件、§参照25件の順序・個数は不変。ただし R-220 の実績/D19の構造的スコープに異議あり。
4. 条件・例外・限定・時系列評価語: **異議なし**。`negative result`、`実際に起きた移行は違う形だった`、`当初案`、`意図的非対応`、否定・限定語の欠落なし。
5. 列挙の網羅性: R-73 に異議あり。他の四条件・三分岐・四事例・再開手段は旧版も明示列挙であり異議なし。
6. Markdown: R-80/R-81 に異議あり。見出し26件、コードフェンス4ブロック、太字 delimiter、リストの他のネストには異議なし。
7. 外部アンカー: §番号・見出し文字列・確認した逐語引用には異議なし。設計文書の可変行番号リンクには上記の異議あり。

worklist 範囲については異議なしです。実 diff の18 unified hunkは承認済み19論理編集に収まり、R-294a/R-296もコミット説明どおり原文復元されています。

総括 1/3: must-fix 2件が残るため、9997d61 の layout-only 主張は現状では成立しない。  
総括 2/3: 語彙・限定・D/§・時系列評価語は保存されたが、リスト階層が分類と根拠スコープを変えた。  
総括 3/3: R-73 と R-220 を修復し、R-181・softbreak・固定アンカーを処置後に再レビューすべきである。
### 親裁定 (全 5 所見 real)
- must-fix R-73 (着手順が第 3 形態に見える) → 修復: 着手順を (b) の継続段落へ
- must-fix R-220 (実績括弧のスコープ狭窄) → BASE 復元
- should R-181 (共有述語の分断で source_digest の一次防壁性が弱まる) → BASE 復元
- should R-80/81 (lazy continuation) → 修復: 空行挿入
- should (本 insight 内の行番号リンク) → 冒頭に point-in-time 注記追加 (逐語は不変)
- 特記: 回帰で 7/7 だった R1 (語レベル双方向含意) はこの構造スコープ型を preserved と誤判定しており、異製品レンズの補完性が実証された

---

## 本番レビューと修復の記録 (closure、2026-07-17)

- R1 意味 diff ×2 (opus、回帰実証済みプロンプト、candidate 9997d61): 全 20 hunk preserved・scope 外 0 件。正規化比較で「日本語・技術語・D 番号・§参照・数値・太字範囲は 1 トークンも増減なし」
- R2 全文比較 (opus xhigh、diff 非依存、初回レーンは空返答のため再実行 / candidate 5ab330a): 規範 41・役割 10・歴史 13・D 紐づけ 20 の計 84 項目で相違ゼロ
- R3 参照整合 (sonnet): § 番号・見出し・逐語アンカー・コードフェンス 4 ブロック byte 一致・Markdown 構造すべて異常なし
- codex 第二系統 (gpt-5.6-sol max): must-fix 2 + should 3 を検出 (R1 が preserved と判定した構造スコープ型 — 異製品レンズの補完性を実証)。修復 wave 1 (5ab330a) で R-73 継続段落化・R-220/R-181 BASE 復元・R-80/81 空行挿入。delta 再レビューで全所見 resolved・「60da9b8→5ab330a は layout-only として合格」
- 修復ラウンド消費: 1/2。未裁定提案 11 本は output/insights/2026-07-17_clarity-proposals-unadjudicated.md へ (どれも発効していない)

### codex delta 再レビュー (逐語)

結論として、`docs/roadmap.md` の4件は解消され、修復 commit に新たな意味ドリフトや Markdown 構造破壊はありません。ただし、行番号注記には should 相当の新しいスコープ問題があります。

| 所見 | 判定 | 根拠 |
|---|---|---|
| R-73 Phase 3 が第3形態に見える | resolved | [(b) 項目](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:73) の子 bullet は b1・b2 の2件だけ。空行後の L77 は2空白インデントなので `(b)` 内の継続段落、L78 の `(c)` は列0から始まる外側リストの次 sibling。分類は「2形態」のまま。 |
| R-220 実績括弧のスコープ狭窄 | resolved | [L249](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:249) は BASE L220 と完全一致。集中攻撃・再検証・`git show` 照合の三動作と実績括弧が同一段落に戻り、括弧は監査テンプレ全体に掛かる。 |
| R-181 共有述語の分断 | resolved | [L197](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:197) は BASE L181 と完全一致。source digest と diff-of-diffs が一次防壁、hook が第二防壁という対応が復元された。 |
| R-80/R-81 lazy continuation | resolved | [L84–89](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/docs/roadmap.md:84) は矢印段落の前に空行があり、矢印行は2空白インデント。同一 list item 内の第2段落として独立し、soft/lazy continuation ではない。 |
| 設計文書の行番号リンク | resolved（元の55件） / new-issue（後段4件） | [冒頭注記](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/insights/2026-07-17_roadmap-claudemd-clarity-consultations.md:5) により、元の55件は BASE=60da9b8 の point-in-time 証拠として明示された。一方、[Codexレビュー節](/home/SFC/tanab/github/izanagi/.claude/worktrees/roadmap-claudemd-clarity/output/insights/2026-07-17_roadmap-claudemd-clarity-consultations.md:781) 内の4リンク（新 L73/L194/L249/L83）は candidate=9997d61 の行番号。冒頭注記を広く読めば誤って BASE 扱いし、狭く読めばこの4件は未処置になる。candidate 節を例外として明記する必要がある。加えて、この文書は未追跡で5ab330aには含まれていない。 |

前回の観点別判定は次のとおり更新できます。

1. 双方向含意: 合格。R-73/R-181/R-220 を解消。
2. 対概念: 合格。一次/第二防壁を含め対応関係を保存。
3. D・§ の紐づけ: 合格。BASE/最終とも D参照42件、§参照25件で出現順も一致。
4. 条件・例外・限定・時系列評価語: 合格。前回の異議なしを維持。
5. 列挙の網羅性: 合格。b1/b2 の2形態と Phase 3 の着手順を正しく分離。
6. Markdown: 合格。見出し26件、コードフェンス4ブロックを保存。`git diff --check` も問題なし。
7. 外部アンカー: roadmap 本体は合格。ただし上記 candidate 行番号4件の注記スコープは要修正。

`python3 tools/check_docs.py` も「違反なし」です。

**明言すると、`docs/roadmap.md` の 60da9b8→5ab330a は layout-only として合格です。** ただし、レビュー成果物全体を完全合格とするには、未追跡の consultation 文書で candidate=9997d61 の4リンクを注記の例外として明示する必要があります。