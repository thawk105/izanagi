# [T-2852] P5 の事前登録草稿を S1 版から S3 版へ改版 — 4 cell × n = 4 の向き、T-2867 の LLM が受け取る情報の露出の棚卸し (2026-10-01、計算投入 0)

- 依頼 (逐語): `verbatim/request.md`。段 1 brief `verbatim/s1-brief.md`。開始 gate `verbatim/startup-gate.log` (rc=0、起点 local main `74029b18f`)。
  棚卸しの実測の生出力 `verbatim/inventory-log.md` と、そのコマンド `verbatim/inventory-commands.txt`。履歴の欄の集計 `verbatim/history-fields-log.md`。
  段 6 のレビュー `verbatim/s6-review-a.md`・`verbatim/s6-review-b.md` (焦点再レビューは `verbatim/s6-focus-*.md`)。
- 成果物: 草稿 `docs/workload-description-critic-intervention-preregistration.md` (以下「草稿」、未発効) の全面改版と、`docs/README.md` の地図の 1 項。
- **repo のコード変更なし。計算投入なし。** n の確定・発効・実装・投入はしていない (D2322 項 5、依頼の明示)。

## 0. この文書が主張すること・しないこと

- 主張する: 改版の設計判断の理由 (§4)、露出の棚卸しの実測 (§2)、見積りの計算 (§3)、ユーザーが決める択一 (§5)。
- 主張しない: 見積りは将来の費用の保証ではない。係数 k(n) と s_d の上限は感度の値で、達成される精度の予測ではない。本書も草稿も、実装・本走・計算投入の認可ではない。
- **起草者 (Claude) は T-2867 本走の完了を知っている。** local main の commit 題 (`5b9af2b78` の「48 系列完走、report は 4 比較とも floor 内の同等」) を読んだ。
  本走の score の値・endpoint・方策の本文・report は開いていない。露出の欄を抜き出した 1 機会 (llm-ir-1 の原提案 1) の coder 入力で、critic 診断の文の断片を grep の出力で見た (草稿 §11)。

## 1. 依頼と前提の確認

- 読んだ一次資料と既裁定: D2322 (項 5 と冒頭の相談の採否)、D2256 項 4、S1 版の草稿 (local main `63378acb8` の同じ path)、S1 版の起草 insight §5、
  T-2867 登録 (全節と §16.1 の Erratum)、T-2867 の実装 insight §4、段階 D の insight の射程の節、下書き `p5-s3-draft.md` (repo 外)。
- 依頼の前提は崩れていない。単価 (1 系列 1.23〜1.42、参照 1.74〜2.00) は T-2867 登録 §11.0 の値と一致し、4 cell × n = 4 の換算 21.4〜24.7 node 時間は D2322 項 5 と一致する。
- **wave の途中で前提に関わる新事実が 3 つ出た。** (1) 下書き §1.4 が懸念にとどめた露出の棚卸しで、確認した固定の入力には正しい workload 名を表示する欄が無いと分かった (§2)。
  これで下書きの「T-2867 の C-on 相当の系列」という見方は成り立たず、T-2867 の系列を標本に入れない既定が「既定」から「理由のある規則」になった。
  (2) 再開時 (09:43) に local main が進んでおり、T-2867 本走は完了していた。草稿は「T-2867 本走の後」の前提をそのまま保ち、n の確定は依頼どおりユーザーに残す。
  (3) 段 6 のレビュー (所見 A-1) で、T-2867 の対照の経路では自系列の履歴に評価の結果の verifier の digest と一部の拒否 (schema の拒否と auditor の出力の形式・digest の不一致による拒否) が入っていないと分かった (§2 の 2 つ目の表)。
  段 1 の (P2)「失敗理由は履歴で critic と独立に届く」は schema の上だけの話で、実装では成り立っていなかった。草稿はこの接続を発効の前提にした。
- 中断: 00:4x に land 調整役から利用上限による停止依頼を受けて止め、09:43 のユーザーの「続けて」で再開した。再開時に local main `63378acb8` を `--ff-only` で取り込み、
  対象 3 文書 (草稿・T-2867 登録・S1 版の起草 insight) の差分を確かめた (T-2867 登録に §16.1 の Erratum が増えただけ)。

## 2. 露出の棚卸しの実測 (local main `63378acb8`、生出力は `verbatim/inventory-log.md`)

| 経路 | 実測 | workload の名前・読み比率 |
|---|---|---|
| coder 入力の key | `make_policy_coder_input` の 5 key (`leakproof_context`・`policy_spec`・`baseline`・`recon_projection`・`self_history`) + 任意の `critic_diagnosis`。T-2867 本走の 1 機会の実物も同じ 6 key | — |
| `leakproof_context` | `src/coder-leakproof-context.md` の生 bytes。Measurement Setup は `100k_records / t4_threads / ... / rr50_readratio / ...` の配線規模。実物の文脈で rr50 を含む行 2、`write-heavy`・`read-heavy`・`rr5 ` は 0 件 | 読み比率 50 (実際の 5 と違う)、名前なし |
| `policy_spec` | workload 語 0 件 | なし |
| `recon_projection` | `projection.json` の `binary` (true)・`scope` と実物が一致。射程文に workload 名なし | なし |
| `baseline` | 実物の abort 率 12.56% (系列開始 stock、write-heavy) | なし (値は write-heavy の実測) |
| `self_history` | schema は結果の分類・`reject_subtype`・`reject_rule_id`・`verifier_digest` (throughput なし)。`workload_tag` は verify pass の tag で、pass の tag 定数は `legacy`・`s2`・`performance`。対照の経路での欄の埋まり方は下の 2 つ目の表 | なし |
| critic prompt | 材料は各 slot の結果・digest・本文・throughput・abort 率・品質と job 1 の stock、系列名。実物の critic prompt で `write-heavy|read-heavy|rratio|rr5` を含む行 0、digest の見出しは `## workload: p3-silo-policy ()` | なし |
| 親指示文・親起動器・起動器・台帳・round tool | workload 語を含む行 0 件 (6 file) | なし |

**自系列の履歴の欄の埋まり方 (段 6 の所見 A-1 の裏取り。コードは `63378acb8`、集計の生出力は `verbatim/history-fields-log.md`):**

| 履歴に入る事象 | 書く場所 | 入る欄 |
|---|---|---|
| 評価の結果 (job 2 以降) | `run_contrast_unit` の中の `_append_history` (`outcome`・`variant`・`logical_slot`・`measurement_campaign_id` だけを渡す) | 結果の分類だけ。`verifier_digest` は入らない |
| 初期点の結果 | `run_contrast_unit` の中の `_append_seed_history` (同上) | 結果の分類だけ |
| 検疫・構文・compile と auditor の通常の判定 (`auditor-violation`・`auditor-uncertain`) による投入前の拒否 | round tool の `_record_preview_reject` → driver の `--record-reject` → `drive_contrast_record_reject` → `_append_history` (`digest` 付き) | `reject_subtype`・`reject_rule_id` |
| coder 出力の schema の拒否と、auditor の出力の形式・digest の不一致による拒否 | round tool の `_schema_reject`・`_record_preview_reject` (subtype が `proposal-schema`・`auditor-gate`・`auditor-digest` のとき driver を呼ばない) | 履歴に入らない (対照の台帳の `opportunity-end` にだけ残る。critic の材料 `_new_results` にも入らない) |

- T-2867 本走の LLM 系列の coder 入力 249 件 (llm-cpp 121・llm-ir 128) の履歴は延べ 1,638 行で、`certified` が 1,626 行 (いずれも `verifier_digest` なし)、
  `rejected` が 12 行 (いずれも `reject_subtype` あり) だった。確認した coder 入力の履歴に現れた評価の結果は全部 certified だった。coder 入力は提案の前の履歴なので、各系列の最後の評価は現れない。評価が失敗したときの情報の欠落の大きさと、本走全体の失敗の有無は、この集計では確かめていない (`verifier_digest` が null であること自体は全行で観測した)。
  これは本走の結果 (score) ではなく入力の欄の集計である。T-2867 登録 §4.1 は「履歴は … verifier の digest を載せ」と書くので、登録と実装の食い違いとして worklog の次の一手に残す。

- **結論:** 段階 D の二値・射程文・baseline の abort 率は、どれも workload の名前や読み比率を示さない。ただし write-heavy で測った情報を運ぶ。運び方は経路で違い、
  段階 D の射影は全 cell に同じ bytes、baseline は系列ごとの系列開始 stock の実測値、critic の材料は critic ありの cell だけに届く。LLM がこれらから競合の強さを推し量れば、
  表示との整合・食い違いを通して記述の効き目は変わりうる (弱めるとは限らない。草稿 §3.4・§12 の U2)。cell 間の差を偏らせないとは言えない。
  read-heavy の同じ構成での stock の abort 率は読んでおらず、12.56% が両者を区別する値かは確かめていない。
- **副次の発見:** 確認した固定の入力 (driver・round tool・親が組む部分) には、正しい workload 名と読み比率を表示する欄が無い。coder の文脈は読み比率 50 の配線規模を表示し、
  critic の digest の見出しは workload 欄が空である。critic 診断は自由文なので workload に触れることはありえ、確認したのは本走の 1 機会の critic prompt と coder 入力の固定部分だけで、そこでは該当語 0 件だった。同じ機会の critic 診断 (自由文) には「未測定の workload (ほかの skew や read-heavy など) へは一般化しません」の文があり、自由文の部分は 0 件ではない。
  文脈が backoff 軸用の旧文書のままであること自体は既知で (段階 F の insight `output/insights/2026-09-27/t2865-silo-policy-stage-f/README.md` §3.4、
  方策軸用へ替える方向は D2272 項 5 = [T-2870] で了承済み、具体差分のユーザー承認待ち)、本 wave の純増は「その旧文書が実際と違う読み比率を表示する」という露出の観点である。
  この表示は LLM の構成の一部として T-2867 の LLM の 2 arm に共通で、非 LLM の arm は使わない。実際と違う読み比率の表示が LLM の探索に不利に働いたか
  (LLM 対 非 LLM の比較への影響) は、本 wave では評価していない。T-2867 の報告で LLM の構成を書くときに開示が要る事実として、worklog の次の一手に残す。
  本 wave は T-2867 の文書・コードを変えない。

## 3. 見積りの計算

- node 時間 = 系列数 × 1.23〜1.42 + 1.74〜2.00 (T-2867 登録 §11.0 の 1 系列と参照 3 本)。4 cell × n = 4 = 16 系列で 19.68〜22.72 + 1.74〜2.00 = 21.42〜24.72。
- 契約上限 = 系列数 × (0.5 + 10 × 0.25 + 0.75) h + 参照 3 × 1.0 h (T-2867 登録 §11.0 の walltime の案)。16 系列で 63。
- 原提案機会 = 系列数 × 10〜30。LLM の直列時間 = 機会 × 5.7〜8.0 分。16 系列で 160〜480 機会、15.2〜64.0 h。
- 係数 k(n) = t(1 − 0.025/3, n − 1) / √n。t 分布の分位点は scipy が無いので Simpson 則の数値積分と二分法で求めた (検算: 自由度 2 の t(0.975) = 4.303)。
  t(0.99167, 2) = 7.649、t(0.99167, 3) = 4.857、t(0.99167, 4) = 3.961、k(3) = 4.416、k(4) = 2.428、k(5) = 1.771。
  δ = ln 1.03 = 0.0296 に半幅が収まる s_d の上限 δ / k(n) は 0.0067・0.0122・0.0167。
- 符号反転の片側 exact 検定の最小 p は 1/2^n で、n = 4 で 0.0625。
- 参照 job の単価の出所 (T-2867 の実装 insight §5) の算式 `3 × (5 × 166〜203 + 5 × 255〜265 + 33)` 秒を再計算すると 6,414〜7,119 秒 = 1.78〜1.98 h で、
  同じ行の 6,264〜7,194 秒 (1.74〜2.00 h) と一致しない (段 6 の所見 A-5)。草稿は依頼どおり登録の値 1.74〜2.00 h を使い、独立に導いた値とは扱わない (再計算値は幅の内側)。

## 4. 設計判断 (段 1 の provisional 裁定と、その後の扱い)

- **(P1) critic なしは critic を呼ばないだけ。** 推定対象は「解釈 + 性能の還流」と明記した。性能を機械的に写す別 key は D2256 項 4 の firewall を変える追加の介入なので、
  段 6 の所見 B-3 を受けて確認事項から外し、射程外として草稿 §15 に記した。
- **(P2) S1 版の「失敗理由の写し」は作らない — ただし履歴の欄の接続を発効の前提にする。** 段 1 では「履歴が verifier の digest を critic と独立に届ける」と置いたが、
  段 6 の所見 A-1 で対照の経路では欄が埋まっていないと分かった (§2)。既存の欄を対照の経路でも埋める修復を草稿 §13 の 2 に置き、それが満たされれば両水準で同じ経路で届く。
- **(P3) 記述の表示は coder の Measurement Setup の塊の置換と critic prompt の動作点の節。** 共有 file は書き換えず driver が cell に束縛して置き換える (実装は後続)。
  系列名に cell を入れない (critic prompt が系列名を載せるため)。
- **(P4) 統計は S1 版の Bonferroni の同時区間 (δ = ln 1.03 固定) を保つ。** n = 4 では符号反転の exact 検定が使えないため。T-2867 の `max(0.03, CV_stock)` は使わない。
  固定の δ は両方向に効く (雑音から決める δ より同等には分類されにくく、優越・退行には分類されやすい。段 6 の所見 B-4)。分類は fallback 込みの運用 score についてで、
  全組が fallback の対比は区間 [0, 0] で「同等」になりうるので、生成の力の同等とは読まないと草稿に書いた。
- 人手分類は IR の本文と骨格 (整数定数を型付きの placeholder に置き換えた木) の同一性で (i) を機械的に 4 分類し、人は付記と (ii) を担う形にした。
  K は本文照合用 (C++ を含む全 arm) と骨格照合用 (IR を持つ方策だけ) に分けた (段 6 の所見 A-2・B-1)。

## 5. ユーザー確認の束 (発効の前、草稿 §14)

1. n の確定。向きは 4 cell × n = 4 (D2322 項 5。4 cell × n = 3 と 6 cell × n = 4 は同項で却下済み)。資料は T-2867 本走の分散と週上限の実測 (本 wave では読んでいない)。
2. 評定者 (人 2 名)。

## 6. 段 6 の経緯

- 軽量版で段 2・3 を省き、段 6 に read-only の Codex レビュー 2 本 (gpt-6-astra) を同じ worktree で直列に回した (同じ worktree の dispatch は直列、DW-C00)。
  レンズ A = 事実と一次資料の照合、レンズ B = 過剰・削除と推定対象・統計。逐語は `verbatim/s6-review-a.md`・`verbatim/s6-review-b.md`。どちらも NO-GO (must-fix 各 2、うち 1 件は共通)。
- 親の裁定 (refuted 0):

| 所見 | 重さ | 裁定 | 処置 |
|---|---|---|---|
| A-1 対照の経路で失敗理由が履歴に入らない | must-fix | real (親がコードと本走の入力の欄で裏取り、§2) | 草稿 §3.2 を書き直し、§13 の 2 に履歴の欄の接続を発効の前提として追加 |
| A-2・B-1 K の C++ 方策に骨格が無い | must-fix | real | K_本文と K_骨格に分け、骨格の規則 (整数定数だけを placeholder) を固定 (§9.2・§9.3・U8) |
| B-2・A-3 露出を「全 cell 同じ bytes・値」とした | must-fix / should | real | 経路ごとに運び方を分け、偏らないという断定を外し、効き目が強まる向きもあると限定 (§3.4・U2) |
| A-4 「一度も表示されていない」 | should | real | 確認した固定の入力と 1 機会に限定 (草稿 §3.1、本書 §2) |
| A-5 参照 job の換算式の不一致 | should | real (出所の T-2867 実装 insight の問題) | 草稿 §7.2 と本書 §3 に注記、値は登録どおり |
| A-6 0.0276 | nit | real | 0.0275 に訂正 |
| B-3 却下済みの 6 cell・追加の介入を確認事項に戻した | should | real (D2322 項 5 の却下案) | 6 cell の対比と確認事項を外し、表は参考に縮め、追加の介入 2 つは §15 の射程外へ |
| B-4 fallback と固定 δ の意味 | should | real | §6 に運用 score である旨と固定 δ の両方向を追記 |
| B-5 最初の提案の (i)/(ii) と欠測 | should | real | §8 の 1 を直した |
| B-6 docs 地図の「族 3」 | nit | real | 「3 対比の Bonferroni 同時区間」に訂正 |

- 焦点再レビュー 1 巡目 (`verbatim/s6-focus-1.md`): closed 9・partial 3・regressed 0、派生値 (249 件・1,638 行・費用表・k(n)・0.0275・[0, 0]) はすべて再計算で一致。NO-GO (must-fix 1)。
  F1 (must-fix、real): 履歴に入らない拒否を「schema・auditor」と一括りにしていた。auditor の通常の判定 (`auditor-violation`・`auditor-uncertain`) は `--record-reject` を通って履歴に入り、
  入らないのは coder 出力の schema の拒否と auditor の出力の形式・digest の不一致 (`proposal-schema`・`auditor-gate`・`auditor-digest`) だけ。評価の転記は `run_contrast_unit` の中。親がコードで確かめて草稿 §3.2・§13 の 2、本書 §2、fragment を直した。
  F2 (should、real): 履歴の集計から本走全体の失敗の不在を導いていた → 集計の範囲に限定。F3 (should、real): 1 機会の critic 診断の自由文に `read-heavy` の語がある → 「0 件」を固定部分に限定。
  F4 (should、real): 発効束に 6 cell が残っていた → 「4 cell、確定した n」に。
- 焦点再レビュー 2 巡目の結果は下に追記する。

## 7. 本 wave が閉じないもの

- n の確定・発効・実装・投入。T-2867 本走の score・分散・週上限の読取。
- T-2867 の報告に「LLM の coder 文脈は実際と違う読み比率 (50) の配線規模を表示し、確認した固定の入力には正しい workload 名・読み比率の明示欄が無い」事実を開示すること、
  その影響の評価 (T-2867 の文書は変えていない)。
- T-2867 登録 §4.1 (履歴は verifier の digest を載せる) と対照の経路の実装の食い違いの記録・修復 (草稿 §13 の 2 は P5 の発効の前提として置いただけで、実装していない)。
- 2026-11-02 の S1 縮小案の再提示 (D2283 (ii))。
