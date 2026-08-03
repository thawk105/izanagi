静的読解の結論は、cache・WAL・sweep の gate 自体は広く計画されている一方、成果物の正本である試行台帳と Layer 3 proof chain に admission 判定が残らない点が最大の欠落です。また、親 brief の「旧 campaign で実際に拒否を発火させる」という要件と、plan の「ID を変えて旧 directory を orphan 化する」方針は両立しません。

以下、`$JOB` は `/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344`。

## 成果物影響の短評

| 変更群 | 放置時の成果物影響 |
|---|---|
| SourceEvidence / CLI authority | coder-derived bytes が stock と自己申告され、certified 受理集合と provenance が変わる。影響は明確。 |
| cache key / v2 manifest | 別 admission class の binary・`median_tps` が再利用される。影響は明確。 |
| campaign policy / WAL receipt | 別 policy の terminal replay が現在の試行へ付け替わる。影響は明確だが ID 方針が brief と衝突。 |
| overlay / consumer | 旧値を除外する狙いは明確だが、Layer 3 schema・critic の公開 loader・試行台帳 producer が取り残される。 |
| live qualification / S8b identity | live member・oracle の provenance を守る影響は明確。歴史的 source の再測定まで含める部分は scope 拡張。 |
| `variant_id` 非変更 | 実装変更ではなく設計 invariant。独立した成果物影響を書けないため実装項目なら nit。 |
| `backoff_sweep_report` と completeness 内の重複 guard | 上流 reader が必ず guard されるなら受理集合を追加で変えない。現状の記述のままなら nit。 |

## Scope 内の所見

### 1. Critical — canonical な試行台帳 producer が admission chain を通らない

- **Scope:** 内
- **Claim:** plan は completeness の optional な Layer 3 比較だけを変更し、実際に `report.json` を確定する producer と、その campaign 起動を配線対象から落としている。
- **Evidence:** plan は `autonomous_trial_completeness.py:879-999` だけを対象にする（`$JOB/s2-plan.md:312-315`）。しかし通常の completeness は journal／report の整合だけを検査する（`orchestrator/campaign/autonomous_trial_completeness.py:828-865`）。campaign chain は `campaign_output_root` 指定時だけである（同 `:1002-1019`）。producer は基本検査だけを呼んで report を保存する（`orchestrator/campaign/p3_autonomous_workload_trial.py:1141-1151`）。さらに producer は policy を加える前の `cfg` から ID を直接計算し（同 `:1173-1194`）、`drive()` に `BuildRunContext` を渡さない（同 `:1363-1380`）。plan の direct-caller 表にも同ファイルがない（`$JOB/s2-plan.md:252-276`）。
- **Impact:** 放置すると、参照先 Layer 3 が admission 拒否される campaign でも autonomous trial の `report.json` は「complete」な試行台帳として残り、campaign ID・outcome・参照の受理集合が admission-aware な材料集合と食い違う。
- **Suggested fix:** `p3_autonomous_workload_trial.py` を明示的な caller/consumer に追加する。policy を `cfg` に入れてから ID を一度だけ導出し、同じ `BuildRunContext` を全 iteration へ渡す。build-bearing cell は report 保存前に campaign admission／Layer 3 chain を必須検査し、`--no-build` cell は exact な `admission_status: not-applicable` として別形で記録する。

### 2. High — Layer 3 は「拒否する」だけで、判定根拠を proof chain に残さない

- **Scope:** 内
- **Claim:** `build_report()` の先頭に validator を足しても、生成された材料レポートから admission 判定を再現できない。plan は `layer3_schema.json` を変更対象にも所有単位にも入れていない。
- **Evidence:** plan の変更対象は `layer3_report.py` のみ（`$JOB/s2-plan.md:298-300,459-462`）。現行 v2 schema の required fields に admission、policy、overlay provenance はない（`orchestrator/campaign/layer3_schema.json:6-13`）。report が pin する generator は `layer3_report.py` 自身だけで（`orchestrator/campaign/layer3_report.py:408-415`）、`artifact_refs` も campaign directory 内だけを列挙する（同 `:141-146,416-423`）。
- **Impact:** overlay ledger または validator の bytes を差し替えると同じ campaign の受理可否が変わるが、既存 report の値・参照・generator hash からその差を説明できない。したがって「T-316 admission 下の材料」という proof chain にならない。
- **Suggested fix:** schema を v3 に上げ、少なくとも `admission_decision` に policy SHA、attempt receipt SHA 群、lock/WAL SHA、classification、validator identity/SHA、overlay ledger SHA と record key を要求する。`layer3_schema.json` と対応テストを unit 4 の所有へ明記する。

### 3. High — critic の rejection／signal loader が raw-WAL bypass のまま残る

- **Scope:** 内
- **Claim:** plan の「workload/bench 共通入口で一度だけ validator」は `load_workload()` 以外の公開 loader を閉じない。
- **Evidence:** plan の指定は `digest.py:192-219,446-452` に限定される（`$JOB/s2-plan.md:302-304`）。一方、`load_rejections`、`load_liveness_rejections`、`load_screen_rejections`、`load_diff_rejections`、`load_verify_abort_signals` はそれぞれ直接 WAL を読む（`orchestrator/critic/digest.py:222-359,387-416`）。CLI と loop もこれらを個別に呼ぶ（同 `:693-700`、`orchestrator/campaign/p3_s4_loop.py:257-264`）。`p3_s4_red.py` にも直接呼出しがある（`orchestrator/campaign/p3_s4_red.py:162-167`）。
- **Impact:** receiptless campaign の verify/abort 情報を critic の次手入力へ還流でき、AI が合成する候補と最終的な試行台帳が、admission-aware な certified 集合とは別の材料に依存する。
- **Suggested fix:** validator 済みの `AdmittedCampaign` または immutable な validated-record view を一度発行し、全 loader がそれしか受け取れない API にする。個々の caller に任意 guard を足す形は避ける。

### 4. High — campaign ID 方針が親 brief の実発火要件を消している

- **Scope:** 内
- **Claim:** plan は identity の一貫性を理由に全 campaign ID を変更するが、その結果、親 brief が要求する旧 3 campaign の resume 拒否は発火せず、旧 directory は単に見えなくなる。
- **Evidence:** brief は ID を維持し、旧 WAL receipt の exact 検査を resume 時に発火させるとしている（`$JOB/s1-brief.md:71-74`）。plan は admission を canonical preimage に入れ（`$JOB/s2-plan.md:209-215`）、全 ID を変更し旧 directory を自動 resume しないと明記する（同 `:367-376,390`）。現行 ID は `search_config` 全体の hash から導出される（`orchestrator/campaign/ident.py:76-103`）。S6/S8a report も現在 config から ID を再計算して path を選ぶ（`orchestrator/campaign/s6_sort_sweep.py:437-450`、`s8a_trigger_sweep.py:486-498`）。
- **Impact:** 旧 checkpoint／WAL に対する「legacy-unclassified 拒否」という監査イベントや参照が残らず、新 namespace で別試行が始まる。旧値を拒否したのか、単に発見しなかったのかが台帳上区別不能になる。
- **Suggested fix:** 親裁定を要求する。ID を変えるなら、起動・report 時に admission 導入前 identity も導出して既存 directory を探索し、発見時は overlay record を伴う構造化 refusal を返す。ID を維持するなら、policy は versioned lock identity として別束縛し、brief の exact resume 検査を採る。両方を同時に主張しない。

### 5. High — overlay の権威と「歴史的 certified」の次元が定義されていない

- **Scope:** 内
- **Claim:** 単一の `classification: legacy-unclassified` だけでは、歴史的 verifier status と T-316 admission status を区別できず、台帳自身の作成権限・改竄検知も proof chain にない。
- **Evidence:** brief は `output/` 台帳を指定する（`$JOB/s1-brief.md:75-77`）が、plan は repo 内の `orchestrator/campaign/legacy_admission_overlay_v1.json` に移し、record は path／ID／lock SHA／WAL SHA／count／classification だけとする（`$JOB/s2-plan.md:282-296`）。実 WAL は receipt を持たない一方、verifier は `certified:true` を記録している（例: `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl:1-5`、sort 同 `:1-6`、trigger 同 `:1-12`）。
- **Impact:** 「当時 verifier-certified だった」という履歴まで否定したように材料レポートが読める一方、ledger bytes の変更だけで現在の選択可否を変えられる。誰の裁定で除外されたかも report から追えない。
- **Suggested fix:** `verification_status` と `admission_status` を別フィールドにし、overlay は後者を `legacy-unclassified` にする deny-only 台帳と明記する。ledger に authority、作成元 commit、入力 hash、生成規則／裁定 ID を持たせ、reader が exact ledger SHA を decision receipt として返す。各 report／台帳はその SHA と validator SHA を pin する。

### 6. Medium — 3 runbook の command は残せても、再開と `--no-build` の説明が破綻する

- **Scope:** 内
- **Claim:** plan が親へ回す docs は decisions／phase／worklog／handoff だけで、実運用の 3 runbook を更新対象として列挙していない。
- **Evidence:** docs handoff は `$JOB/s2-plan.md:472-477`。現 runbook は coder build に同じ flag を要求する一方、`--no-build` では不要とする（`docs/phase3-s4b-runbook.md:86-99`、`phase3-s5-sort-runbook.md:136-154`、`phase3-s8a-trigger-runbook.md:78-94`）。S4b は旧 ID 下の checkpoint を後段へ継承すると記す（`phase3-s4b-runbook.md:124-131`）。plan は全 campaign ID を変更する（`$JOB/s2-plan.md:374`）。
- **Impact:** build command の flag 名が維持されても、no-build rehearsal と本 build が同じ policy/ID を共有するか不明で、旧 checkpoint の継承先も誤る。操作者が別 campaign を継続扱いし、試行台帳の参照が分裂する。
- **Suggested fix:** 3 runbook を必須 docs 変更に加え、build／no-build ごとの policy、campaign ID、旧 checkpoint の扱い、legacy refusal の確認方法、新 cache namespace が cold になることを明記する。

### 7. Medium — 実装単位の「素集合」は test/fixture と未所有ファイルで崩れる

- **Scope:** 内
- **Claim:** production file の列挙は概ね分離されているが、behavioral ownership は分離されておらず、重要ファイルにも owner がない。
- **Evidence:** unit 3 は各 driver 固有 test、unit 4 は各 consumer test を所有するとしている（`$JOB/s2-plan.md:454-463`）。しかし `test_p3_s4_loop.py` は driver と `make_critic_digest` を同じファイルで検査する（`orchestrator/tests/test_p3_s4_loop.py:453-462`）。`test_autonomous_trial_completeness.py` も completeness と producer を同時 import／monkeypatch する（`orchestrator/tests/test_autonomous_trial_completeness.py:19-20,932-940,1461-1472`）。さらに `layer3_schema.json` と `p3_autonomous_workload_trial.py` はどの unit にもない。
- **Impact:** unit 3/4 が同じ fixture 契約を別々に変更し、consumer guard を入れる際に producer test が欠落または競合する。結果として schema と試行台帳だけ旧受理集合のまま残り得る。
- **Suggested fix:** file-level ownership表へ落とす。`test_p3_s4_loop.py` の critic 部分は unit 4 に一括所有させるか別 test file に分離する。`layer3_schema.json` は unit 4、autonomous producer とその統合 test は明示した新 unitまたは unit 3/4 の一方だけに割り当てる。

### 8. Medium — 成果物影響を書けない変更は nit に落とし、実際の抜けへ予算を移すべき

- **Scope:** 内
- **Claim:** `backoff_sweep_report.py` の追加変更と deep completeness 内の二重 guard は、plan の説明どおり上流 validator が必須なら独立した受理集合を変えない。
- **Evidence:** `backoff_sweep_report.report_workload()` は `load_workload()` を一度呼ぶだけである（`orchestrator/campaign/backoff_sweep_report.py:35-44`）。fresh Layer 3 比較は既に `build_report()` を必ず呼ぶ（`autonomous_trial_completeness.py:879-901`）。該当提案は `$JOB/s2-plan.md:312-317`。
- **Impact:** その位置へ guard を追加しても certified 値・材料参照・台帳受理集合は変わらず、canonical producer、schema、公開 critic loader の実欠落を覆い隠す。
- **Suggested fix:** consumer 固有の decision receipt を成果物へ追加しない限り、この2項目は nit／継承確認へ格下げする。実装対象は producer、schema、全 raw-WAL loader に振り替える。

## 凍結面の独立検算

overlay を `orchestrator/campaign/` に置く限り、凍結族へ自動混入する経路は静的には見当たりません。`FROZEN_MANIFEST` は明示された `output/` 23 path の exact 集合であり（`orchestrator/tests/test_frozen_artifacts.py:38-114,139-153`）、S1 freeze の verifier も生成文書内の明示的 `sources` だけを辿ります（`orchestrator/campaign/s1_known_axes_freeze.py:682-742`）。S8b oracle preimage も schedule／run contract／campaign ID の明示構築で、repo glob はありません（`orchestrator/campaign/s8b_oracle_manifest.py:659-675`）。

したがって「overlay の配置だけで frozen bytes が変わらない」という主張と、「既存成果物の意味上の権威が変わらない」という主張は分ける必要があります。後者は blanket validator により変わります。

## 裁定パッケージ候補（scope 外）

### 9. High — 3 campaign overlay から全 receiptless 歴史成果物への blanket gate 拡張

- **Scope:** 外 — 裁定パッケージ候補
- **Claim:** brief が実測対象とした3 campaignを越え、plan は overlay 非掲載の全 receiptless completed artifact を拒否する。
- **Evidence:** brief の対象は明示した3 loop campaign（`$JOB/s1-brief.md:34-40,75-77`）。plan は非掲載 artifact も positive validator で拒否するとする（`$JOB/s2-plan.md:292-296`）うえ、qualification にも適用する（同 `:319-328`）。
- **Impact:** P2、freeze の材料、その他歴史 campaign の受理集合と参照可能性が一括で変わる。これは3件の T-344 overlay 実装ではなく、repository-wide な歴史成果物の再分類である。
- **Suggested fix:** 裁定選択肢を提示する。推奨は「3件を明示 denyし、新 schema 導入後の成果物には positive receipt を必須化する。その他の歴史 artifact は二次元 status で保持し、certified 選択への利用可否を consumer ごとに明示する」。全面遡及を選ぶなら、全 receiptless artifact と全 consumer の inventory を別 wave で作る。

### 10. High — T126 の新 admitted P2-2 実測と protocol/pin 更新

- **Scope:** 外 — 裁定パッケージ候補
- **Claim:** live qualification member の admission 対応は scope 内だが、歴史的 control source を新測定へ交換するのは新しい実験・protocol 変更である。
- **Evidence:** 現 protocol は `authority: evidence-only/no-promotion`、`historically-within-linux-floor-observational-smoke` と明記し、旧 P2 lock/WAL を pin する（`orchestrator/qualification/t126_control_v1.json:2-6,15-38`）。`select_source_pair()` はその歴史的 verifier／bench evidence を検査する（`orchestrator/qualification/artifacts.py:797-841`）。plan はこれを意図的に拒否し、新 admitted P2-2 の実測と新 protocol/pin を親へ要求する（`$JOB/s2-plan.md:392,474-475`）。
- **Impact:** subject/reference の provenance だけでなく、歴史的 `median_tps`、protocol SHA、series ID、qualification の受理集合が変わる。gate 配線だけでは閉じない。
- **Suggested fix:** 推奨案は、旧 source を `historical-verifier-certified + admission: legacy-unclassified` として evidence-only 用途に限定し、live member build にだけ新 admission を必須化すること。歴史 source も T-316 admission 済みに置換するなら、測定権限・protocol version・pin 更新を別裁定として承認する。

## 総括

最も重い見落としは、canonical autonomous producer が admission-aware campaign chain を検証せずに試行台帳を確定できる点です。Layer 3 を拒否しても台帳が complete のままなら、成果物全体として gate は閉じません。

scope を広げずに閉じられないのは、全歴史 campaign の遡及再分類と T126 historical source の再測定です。両者は T-344 の3件 overlay から分離し、明示裁定にする必要があります。