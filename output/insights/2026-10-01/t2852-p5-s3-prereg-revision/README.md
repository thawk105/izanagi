# [T-2852] P5 の事前登録草稿を S1 版から S3 版へ改版 — 4 cell × n = 4 の向き、T-2867 の LLM が受け取る情報の露出の棚卸し (2026-10-01、計算投入 0)

- 依頼 (逐語): `verbatim/request.md`。段 1 brief `verbatim/s1-brief.md`。開始 gate `verbatim/startup-gate.log` (rc=0、起点 local main `74029b18f`)。
  棚卸しの実測の生出力 `verbatim/inventory-log.md` と、そのコマンド `verbatim/inventory-commands.txt`。
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
- **wave の途中で前提に関わる新事実が 2 つ出た。** (1) 下書き §1.4 が懸念にとどめた露出の棚卸しで、現行の S3 の構成には正しい workload 名を表示する経路が無いと分かった (§2)。
  これで下書きの「T-2867 の C-on 相当の系列」という見方は成り立たず、T-2867 の系列を標本に入れない既定が「既定」から「理由のある規則」になった。
  (2) 再開時 (09:43) に local main が進んでおり、T-2867 本走は完了していた。草稿は「T-2867 本走の後」の前提をそのまま保ち、n の確定は依頼どおりユーザーに残す。
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
| `self_history` | 結果の分類・`reject_subtype`・`reject_rule_id`・`verifier_digest` (throughput なし)。`workload_tag` は verify pass の tag で、pass の tag 定数は `legacy`・`s2`・`performance` | なし |
| critic prompt | 材料は各 slot の結果・digest・本文・throughput・abort 率・品質と job 1 の stock、系列名。実物の critic prompt で `write-heavy|read-heavy|rratio|rr5` を含む行 0、digest の見出しは `## workload: p3-silo-policy ()` | なし |
| 親指示文・親起動器・起動器・台帳・round tool | workload 語を含む行 0 件 (6 file) | なし |

- **結論:** 段階 D の二値・射程文・baseline の abort 率は、どれも workload の名前や読み比率を示さない。ただし write-heavy で測った情報を全 cell に同じ bytes で運ぶので、
  LLM がそこから競合の強さを推し量れば記述の介入は弱まる (草稿 §3.4・§12 の U2)。read-heavy の同じ構成での stock の abort 率は読んでおらず、
  12.56% が両者を区別する値かは確かめていない。
- **副次の発見:** 現行の S3 の LLM×IR は、正しい workload 名を一度も表示されていない。coder は読み比率 50 の配線規模の表示を、critic は workload 欄が空の見出しを受けていた。
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

## 4. 設計判断 (段 1 の provisional 裁定と、その後の扱い)

- **(P1) critic なしは critic を呼ばないだけ。** 性能を機械的に写す別 key は D2256 項 4 の firewall を変えるので既定にせず、確認事項にした。推定対象は「解釈 + 性能の還流」と明記した。
- **(P2) S1 版の「失敗理由の写し」は作らない。** S3 の自系列の履歴が verifier の digest を critic と独立に coder へ届けるので、規律 3 は両水準で保たれる。
- **(P3) 記述の表示は coder の Measurement Setup の塊の置換と critic prompt の動作点の節。** 共有 file は書き換えず driver が cell に束縛して置き換える (実装は後続)。
  系列名に cell を入れない (critic prompt が系列名を載せるため)。
- **(P4) 統計は S1 版の Bonferroni の同時区間 (δ = ln 1.03 固定) を保つ。** n = 4 では符号反転の exact 検定が使えないため。T-2867 の `max(0.03, CV_stock)` は使わない
  (等価域を広げると同等に分類されやすくなるので、結果に依存しない固定値を保つ)。
- 人手分類は IR の本文と骨格 (定数を型付きの placeholder に置き換えた木) の同一性で (i) を機械的に 4 分類し、人は付記と (ii) を担う形にした。

## 5. ユーザー確認の束 (発効の前、草稿 §14)

1. n (3〜5) と cell 数。向きは 4 cell × n = 4。資料は T-2867 本走の分散と週上限の実測 (本 wave では読んでいない)。
2. critic なしの cell の定義 (呼ばないだけ / 性能の写しを足す — 後者は D2256 項 4 を変える)。
3. 段階 D の二値と射程文 (全 cell に載せる / 全 cell から外す)。
4. 評定者 (人 2 名)。

## 6. 段 6 の経緯

(段 6 のレビューの後に追記する)

## 7. 本 wave が閉じないもの

- n の確定・発効・実装・投入。T-2867 本走の score・分散・週上限の読取。
- T-2867 の報告に「LLM は実際と違う読み比率 (50) の配線規模の表示を受け、正しい workload 名を表示されていない」事実を開示すること、
  その影響の評価 (T-2867 の文書は変えていない)。
- 2026-11-02 の S1 縮小案の再提示 (D2283 (ii))。
