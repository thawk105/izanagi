# Layer3 論文向け証拠整理 (paper evidence dossier)

**日付:** 2026-08-21
**性質:** 既存 artifact のみからの読み取り集約。新しい測定・production code・correctness gate 変更・
既存 S/S' 確定判断の再計算/再主張は一切行っていない。数値・p 値・確定文言はすべて一次資料からの
**転記**であり、本文書はそれらに作用しない (この点は `output/reports/s_prime_final_report.md` §5 が
自分自身について述べる不変条件と同じ形を、本文書にも適用したものである)。
**scope:** layer3 (S/S' 系の確定判断、p2-2・backoff-sweep という既知軸 baseline、p3-s8a layer3 fact
report、D58 screening、H1/H2 正式系列)。

---

## 0. 本文書の生成手順 (provenance)

dev-wave 軽量版で作成。段2 (read-only codex, `gpt-5.6-luna`, reasoning=max) が資料棚卸しと分類初案を
起草し、段3 敵対相談2レンズ (同モデル、`--lane sol`/`--lane luna`、reasoning=max、並列) が独立に
検証した。両レンズが検出した実所見 (citation の系統的なずれ、`S-2` 表記の内部矛盾、
`backoff-sweep-silo-read-heavy-sweep-8ff95955` が screening 実走ではなく build-error である誤認、
`campaign.lock` の field path 誤り、分類境界の不正確さ) はすべて親 (Claude) が一次資料へ直接
あたって裏取りし、本文書の記述はその裏取り後の値・file:line で書き直している。段2 プランの
citation をそのまま転記した箇所はない。実装面 (コード・テスト・スクリプト・設定) の変更は無いため
D95 の Codex author 要件は非該当 (docs-only)。

---

## 1. 用語と分類の定義

本文書は次の4分類語を使う。**この4分類はこの dossier が独自に定義するものであり、
既存 docs の先行する厳密な定義を引き継いだものではない。**

- **certified**: 当該数値・判定が、freeze / 事前登録 schedule / certified 標本限定 / budget などの
  受理 gate を通過し、必要な場合は人間の承認 (adjudication) を経て確定していること。
  **certified は成立を意味しない** — 不成立・棄却という verdict も certified になり得る。
- **confirmatory** (本 dossier 独自の分類语): 既知結果の事前登録付き追試であり、新規発見ではないこと。
  `output/reports/s_prime_final_report.md:50-51` は S-1b について「confirmatory な新発見とは
  呼ばない」と書いているが、これは「confirmatory」を「新発見」との複合語として使った**個別の
  否定文**であり、本 dossier の分類語としての `confirmatory`(=事前登録追試であること自体を指す
  ラベル) とは語の射程が異なる。読者はこの2つの用法を混同しないこと。
- **wiring**: provenance・renderer・schema・運用導線など、測定や判定を成立させるための工学的基盤。
  **性能上の優劣主張には使わない。**
- **known-no-claim**: 未実施・schema/経路非対応・値が資料から確定できない、または実施しないと
  裁定済みであるために、paper claim の根拠にできないもの。

**evidence status (上記4分類) と verdict (成立/不成立/棄却/該当なし) は独立な2軸である。**
分類表は両方を別列に持つ。

**「certified」の二重使用に注意:** p3-s8a layer3 report の `verifications[].certified` は
**個々の run が run-level で serializable と検証された**ことを示す構造化 field であり (行単位の
正しさ検証)、本 dossier が言う **paper-level の `certified` (evidence status)** とは別物である。
以後 `certified verification`(run-level) と `certified evidence status`(本分類) を書き分ける。

**未測定・非対応の語彙は次の4つに限定する** (「該当なし」を未測定の代用にしない):

| 語 | 意味 |
|---|---|
| 未実施 | 当該測定・実験が実行されていない |
| 非対応 | schema・経路が対象を受理せず、値を出せない |
| 不明 | 実施された可能性はあるが、既存資料からは値を確定できない |
| 該当なし | 性質上その項目自体が意味を持たない (verdict 列で「入力側の資料」に使う等) |

---

## 2. S / S' — Holm 族4判定 (確定・human-approved)

**evidence status: certified (human-approved final record, 2026-07-16)。verdict: S' 全体は不成立。**

一次資料: `output/reports/s_prime_final_report.md`(確定報告書)、その一次データ =
`output/reports/s1_direct_comparison/{report.md,report.json}`(生成 head `24202e270782a58343ef016592c1a4ae767ee0ce`、
`output/reports/s1_direct_comparison/report.md:52`)。事前登録 = `docs/phase3-main-experiment.md`。
確定文言 (S-2/S-3 の報告文) = `output/insights/2026-07-13_s6-report-language.md`(2026-07-13 凍結)。

### 2.1 Holm 族4 判定表 (`s_prime_final_report.md:18-23` から転記、無変更)

| 検定 | 名目 p | Holm 段階 α | 調整済み判定 |
|---|---:|---|---|
| S-1b | 0.000204 | 0.0125 (第1段) | 成立 |
| S-2 | 0.115 | 0.0167 (第2段) | 不成立 (ここで手順打切り) |
| S-1a | 1.0 | (打切り後) | 不成立 |
| S-3 | 1.0 | (打切り後) | 棄却 (退化を示せない) |

`s1_direct_comparison/report.md:24-35` の 12 比較行 (S-1a 9対 + S-1b 3対) が上表の一次データであり、
`report.md:41-42` の family 表 (s1a: 不成立/p=1、s1b: 成立/p=0.000204082) と一致する。
`report.md:5` はこの report 自体が「Holm 族4全体の裁定は行わない」設計であることを明記しており、
族全体の確定は `s_prime_final_report.md` (人間承認) が担う。

### 2.2 S-1a — 既知軸最良の超越 (`s_prime_final_report.md:29-42`)

> 系側 gate 構成 (trigger-gating、`g_rl`/`g_rt`) と既知軸最良3種 (`p2_2_flag_opt`・
> `backoff_fixed_best`・`sort_best`) の直接比較9対 (3対×3workload、事前登録の凍結schedule・
> n=8/セル・certified標本のみ) において、**S-1a は不成立である** (family p = 1.0)。
> vs `sort_best` は3workloadとも優越 (+55.5%〜+98.4%、p_perm=0.000204) だが、
> vs `p2_2_flag_opt` は−9.3%〜−55.1%、vs `backoff_fixed_best` は−36.0%〜−51.9% と劣位。
>
> したがって、**縮小主張 S' の headline は不成立である。**

verdict: **不成立**。evidence status: certified (S1 hard gates 全 pass、
`s1_direct_comparison/report.md:7-18`)。

### 2.3 S-1b — 軸自体の効果 (`s_prime_final_report.md:44-53`)

> 同一コードで gate 述語だけを恒真化した対照 (`ident_all`) との比較3対では、
> **S-1b は成立である** (+60.6%〜+99.9%、family p=0.000204、Holm第1段 α=0.0125通過)。
>
> ただしこの効果は D50 の機械 sweep 偵察 (2026-07-11) で既知であり、本測定は
> **配線確認を含む結果既知の事前登録付き追試であって、confirmatory な新発見とは呼ばない。**

verdict: **成立**。evidence status: certified; claim type = 事前登録追試 (本 dossier の
`confirmatory` 分類に該当。§1 の注意書きのとおり、これは phase3 側の個別文とは別の用法)。

### 2.4 S-2 — 発見の再現性 (`output/insights/2026-07-13_s6-report-language.md:18-27`)

> 提案ラウンドの適格率は本アーム 20/20、対照 C4 で 17/20、片側 Fisher 正確検定の名目 p = 0.115
> (Holm族の段階α最大値0.05を上回り、調整後も非有意)。**S-2 (発見の再現性) は不成立である。**
> 事後の探索的内容分析 (事前登録外) では、C4 の適格 17 束中 6 束が計測ハーネスのみへの提案で
> 適格化していたことが分かった。ハーネスのみ適格を除いた CC 本体換算 (C4=11/20) では p=0.0006 と
> なるが、**これは事後の基準変更を伴う反実仮想であり凍結判定には用いない。**

verdict: **不成立**。evidence status: certified (n=20/アーム完走・判定不能ゼロ、
`2026-07-13_s6-report-language.md:10-13`)。
**s2-plan.md の「主張・条件・再現パラメータ」表が同じ表内で「不成立」と「未検証」を
両方使っていたのは段3両レンズが検出した実在の内部矛盾であり、本文書では正本どおり
「不成立」に統一した。**

### 2.5 S-3 — 帰属の寄与 (`2026-07-13_s6-report-language.md:29-35`)

> 帰属遮断対照 C5 の適格率は 20/20 で本アームと同率 (p=1.0)。**S-3 は棄却される
> (退化を示せない — fail to reject)。** 主張 S から帰属依存節を削除した縮小主張として報告する。

verdict: **棄却 (fail to reject、証拠の不在を不在の証拠と読まない)**。evidence status: certified。

### 2.6 S' 総括と必須併記 (`s_prime_final_report.md:55-64`)

- **S' は不成立** (S-1a 不成立による)。族4のうち成立は S-1b のみ。
- **必須併記 (確定文言の一部、省略不可):** 「適格率次元の発見再現性は未実証のままである」
  (S-1b の成立はこの限界を解消しない。S-1a が不成立となった今回、性能次元でも
  「既知軸最良の超越」は実証されていない)。
- 開示: unstable 標本は除外せず全数保持、retry 全一覧、時間台帳
  spent=22,943.7s / total=43,200s (`s1_direct_comparison/report.md:44-50`)。

---

## 3. S-1 既知軸 baseline の直接入力源 — p2-2 / backoff-sweep / sort-sweep

**evidence status: certified (`output/s1-freeze/known_axes_freeze.json` による機械選定 input、
D52 §2.1)。verdict: 該当なし — これらは S-1a の比較対象を凍結するための入力選定であり、
S/S' 自体の独立した paper claim ではない。**

`known_axes_freeze.json` の `selection_rules` は次を機械的に定義する:

- `p2_2`: 「workload別 `p2-2-silo-<wl>-enumerate-*/runs/wal.jsonl` の COMMIT 済み全 variant から
  `fitness_tps` の一意な argmax を選ぶ」
- `backoff_fixed`: 「workload別 backoff-sweep WAL のうち `backoff_sweep.SWEEP_US` の静的グリッド点
  だけから argmax を選ぶ」
- `sort`: 「`s6_sort_sweep` レポート契約の valid full-order 点から argmax を選ぶ (read-heavy は
  sweep 未実施のため D52 §2.1 が `sk_ad` を事前固定)」

すなわち、下記の測定値は**そのまま** S-1a の `p2_2_flag_opt`/`backoff_fixed_best`/`sort_best`
比較対象になっている。個々の測定自体は実測済みの事実であり、「未測定」ではない。ただし
**paper の headline 主張はこれらの baseline 自体ではなく S-1a/S-1b の比較結果**である。

### 3.1 p2-2 (silo 全探索、known-axis best genome)

一次資料: `output/campaigns/p2-2-summary.md`(自動生成 summary)。calibration:
records=1,000,000、threads=48、clocks_per_us=1800、skew=0.9、between-run floor 3.0%
(within-run 2.28%) (`p2-2-summary.md:7`)。

| workload | 最速 genome | median tps | 2位との差 |
|---|---|---:|---|
| read-heavy | `B0-T-W0` | 8,487,844 | +0.5% は noise 内・非有意 (`p2-2-fitness-read-heavy_report.md:15,23-25`) |
| balanced | `B0-L-W0` | 2,752,621 | 2位比 +7.6% 有意 (p=0.012、`p2-2-fitness-balanced_report.md:15,23-24`) |
| write-heavy | `B0-L-W0` | 1,872,376 | 2位比 +13.0% 有意 (p=0.012、`p2-2-fitness-write-heavy_report.md:15,23-24`) |

### 3.2 backoff-sweep (screening なし、静的 backoff 量 sweep)

一次資料: `output/campaigns/backoff-sweep-silo-<workload>-sweep-<hash>/reports/backoff-sweep-<workload>_report.md`
(screening 無効。`610004b9`(read-heavy)/`484c663e`(balanced)/`493813a7`(write-heavy) の
`campaign.lock#search_config` に `screening` field が無いことで screening 無効と確認できる)。

| workload | 無 backoff | 静的最良 | 判定 |
|---|---:|---|---|
| read-heavy | 8,450,806 tps | 2us=7,889,420 tps | 静的最良でも無backoffに届かず (-6.6%、backoffは純損)。`backoff-sweep-read-heavy_report.md:9-12` |
| balanced | 2,791,760 tps | 5us=3,106,342 tps | 静的backoffが+11.3%上回る (sweet spotあり)。`backoff-sweep-balanced_report.md:9-12` |
| write-heavy | 1,882,125 tps | 10us=2,603,521 tps | 静的backoffが+38.3%上回る (sweet spotあり)。`backoff-sweep-write-heavy_report.md:9-12` |

各 workload の sweep 曲線 (2/5/10/25/50/100us の throughput・abort%・ipc) は各 report の
`:16-23`(read-heavy)・`:16-23`(balanced)・`:16-23`(write-heavy) に保持されている。

### 3.3 sort-sweep (write-set 施錠順序 comparator、known-axis best)

一次資料: `output/campaigns/p3-s6-sort-sweep-{balanced,write-heavy}-sweep-*`(D44 偵察 sweep)。
`campaign.lock#spec_content` はいずれも「preliminary = 事前登録外カテゴリ、断定 verdict なし」
と明記する自己申告を持つ (例: `p3-s6-sort-sweep-balanced-sweep-1b39095e/campaign.lock`)。
`known_axes_freeze.json:167-168` は balanced の `sp_dd` 候補について「remeasure campaign
`p3-s6-sort-sweep-balanced-sweep-1b39095e` で floor 超を再現せず、D46 裁定は差なし」と記録し、
最終的な `sort_best` comparator 選定は同 freeze ファイルの argmax 規則で確定している。
**sort-sweep campaign 自体は preliminary/事前登録外であり、S-1a の入力へ argmax 経由で
反映された後は S1 の certified 経路に属す。sort-sweep 単体を新規 paper claim の根拠にしない。**

---

## 4. p3-s8a layer3 fact report (7 artifacts)

**evidence status: wiring (事実層の機械射影)。verdict: 該当なし (性能優劣やmechanism主張を
含まない)。**

`output/insights/2026-07-16_layer3-mechanism-wiring-design.md:43`(v2 実測結果) が
「p3-s8a-trigger-sweep 系6campaignの実レポート生成、双射pass」と記す対象は次の7ファイルである
(sweep6 + loop1)。

| report | trial | schema | 内容 |
|---|---|---:|---|
| `p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2/reports/layer3_report.json` | `p3-s8a-trigger-sweep-remeasure1` | v2 | variants4/runs4/verifications8/rejects0/aborts0 |
| `p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/reports/layer3_report.json` | `p3-s8a-trigger-sweep` | v2 | variants10/runs9/verifications19/rejects1/aborts1 |
| `p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c/reports/layer3_report.json` | `p3-s8a-trigger-sweep` | v2 | variants10/runs10/verifications20/rejects0/aborts0、within floor は no-matching-env-record |
| `p3-s8a-trigger-sweep-read-heavy-sweep-654d5cd7/reports/layer3_report.json` | `p3-s8a-trigger-sweep-remeasure1` | v2 | variants2/runs2/verifications4/rejects0/aborts0、within floor は no-matching-env-record |
| `p3-s8a-trigger-sweep-write-heavy-sweep-dcd2bbfb/reports/layer3_report.json` | `p3-s8a-trigger-sweep-remeasure1` | v2 | variants3/runs3/verifications6/rejects0/aborts0 |
| `p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8/reports/layer3_report.json` | `p3-s8a-trigger-sweep` | v2 | variants10/runs9/verifications18/rejects1/aborts1 |
| `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/reports/layer3_report.json` | autonomous loop | v1 | variants2/runs2/verifications4/whiteboard2、noise floor 該当なし |

**workload 毎に original (`p3-s8a-trigger-sweep`) + remeasure (`p3-s8a-trigger-sweep-remeasure1`)
の2 campaignが存在する** (合計6 sweep + loop1 = 7)。campaign.lock に seed field は無いため
「別 seed」とは断定できない — 資料から確認できる差は trial (original/remeasure) の違いだけである。

**双射検査:** 各 JSON に `bijection: true` 相当の専用 field は無いが、renderer
(`orchestrator/campaign/layer3_report.py`) の `_assert_bijection`(同ファイル `:218` 付近) が
WAL/whiteboard の expected multiset と report の `source_refs`/`artifact_refs` を突き合わせ、
欠落・重複・余分参照で fails-closed する設計になっている。mechanism-wiring-design.md 側は
この生成時検査の pass を「双射pass」と記しており、JSON 自体に埋め込まれた結果ではない。

**mechanism_hypotheses は7ファイル全てで空配列 `[]`。** `orchestrator/campaign/layer3_schema.json:6`
は `mechanism_hypotheses` を **必須 field** としつつ、`:219` で `maxItems: 0` と定義し、
「原料配線設計 = docs/ 側の設計文書に従い、実装時に v3 へ上げる」と明記する。空である理由は
**「機構仮説なし」という科学的結論ではなく、現行 v2 の予約区画が未実装であること**である
(詳細は §6)。

---

## 5. D58 (bench-first screening v2) — 機構と ablation を分けて記載する

### 5.1 機構: policy 採用・v2 実装・positive control (evidence status: wiring。verdict: 該当なし)

- D58 (`docs/decisions.md:2268-2296`, 2026-07-15): bench-first screening v2 の方針採用。
  「本決定を記録したセッションではコード変更・positive control・計測に着手しない」と明記した後、
  同エントリの状態訂正が「設計v2は監査must-fix対応を含めて実装済みで、positive control
  `backoff-sweep-silo-read-heavy-sweep-6f169f90` により `screen-slower-than-floor` の実発火を
  確認した」と記す (`docs/decisions.md:2290`)。
- positive control 詳細 (`output/insights/2026-07-14_bench-first-screening-design.md:195-200`):
  baseline `84319b1127a6`(BACKOFF_FIXED=-1) median 8,470,959 tps・CV 0.28%・legacy verify
  serializable。対照 `610e879931c4`(BACKOFF_FIXED=100) median 1,912,074 tps・abort_rate 0.0457。
  rr95 の floor `0.0010979692594382789`・`k=1.5` に対し margin −77.4% で `screen-slower-than-floor`
  が発火し、**verify 未実行の uncertified reject** となった (WAL: `6f169f90/runs/wal.jsonl:8-9`)。
- **これは screening 機構が設計どおり動くことの工学的証拠であり、性能への効果 (screeningを
  使うと最終的にどれだけ速く/正しく候補を絞れるか) を主張するものではない。**

### 5.2 ablation 本体: 未実施 (evidence status: known-no-claim。verdict: 不明/未実施)

`output/insights/2026-07-14_bench-first-screening-design.md:202-210` が定義する4基準:

1. 誤棄却ゼロ (screening 却下集合 ⊆ off側で確認された明白劣位集合)
2. 結論不変 (floor超地形の有無判定が on/off で一致)
3. 総機械時間の削減率実測
4. 同一 genome の on/off fitness が floor 内で一致

**これら4基準を満たす測定 artifact は資料上確認できない。**

**2026-08-21 時点の最新状況** (worktree `dev-wave-t1473-d58-ablation-preflight`、
handoff `2026-08-21-t1473-d58-ablation-preflight.md`、**まだ main へ land されていない
docs-only commit `5db135b0`**):

- 旧 g++-13 blocker (`docs/archive/worklog-phase3-0819-701.md` entry701) は T-1444
  (D601/D628/D629、land済み) の site依存 compiler 解決で解消済みと確認。
- **read-heavy (rratio=95) 用の Pegasus calibration が未較正** — `output/env/pegasus/calibration/registered/`
  の既存2件はいずれも balanced (rratio=50) のみ。
- `docs/pegasus-runbook.md:1444-1445` の既知の欠落 (`campaign` dispatch task 未実装) は
  未解消。
- **資源競合:** T-425・T-972 が生存中セッション + 実行中 acceptance job として
  `screening_driver.py`/`between_run_floor.py`/S8b floor 系を同時に改変中と確認され、
  ablation 本走の編集面が競合するため、当該 wave は本走せず zero-diff preflight (docs のみ)
  で中断した。
- D601 (`docs/decisions.md:24160`)・D629 (`docs/decisions.md:25195`)・D630
  (`docs/decisions.md:25217`) は、**ablation 本体の測定結果ではなく**、Pegasus 上で ablation を
  いずれ走らせるための基盤工事 (site依存 compiler 解決、screening 側 attestation 強化、
  campaign advisory flock の target 側修正) である。

**したがって D58 ablation の状態は「政策採用・機構実装・positive control 確認は完了、
4基準の ablation 測定は未実施 (2026-08-21 時点)」である。**

**T-1471 という識別子についての注記:** T-1473 の上記 handoff は、自身の worklog spool fragment
placeholder (`{{T:d58-ablation-pegasus-preflight}}`) について `spool_fold.py --dry-run` が
**「fold 時点の実採番は dry-run 表示 `[T-1471]` だが並行 land でずれうるため確定値として
扱わない」**と明記している。すなわち「T-1471」はどの wave でも**まだ landed な予約番号では
ない**、単なる dry-run 予測値である。本 dossier の作業自体は既存 worklog / decisions / handoff の
どこにも `[T-1471]` として登録された active item ではないため、`docs/spool/worklog/README.md`
の規則 (「`title:` 先頭の `[T-NNN]` は当該 ID が同エントリの次の一手差分で扱う既存 active item の
ときだけ」) に従い、本 dossier の worklog エントリは角括弧 ID を付けずに記録する
(段7 参照)。

---

## 6. mechanism_hypotheses 予約区画・T-1279・T-326

### 6.1 mechanism_hypotheses (evidence status: known-no-claim。verdict: 該当なし・未実装)

`output/insights/2026-07-16_layer3-mechanism-wiring-design.md:1-9` は「分類: 設計。計測ゼロ・
既存凍結に不作用」と自己申告する。同文書 §1(`:11-19`)は「critic の機序帰属は非永続、
coder/planner の構造化出力は proposal file 経由で消費され campaign 成果物として残らない」ため
「renderer がいくら賢くなっても機序仮説を出す原料が存在しない」と述べる。§2(`:21-39`)が
`runs/agent_outputs.jsonl`(v3、`planner_proposed`/`coder_proposed`/`critic_attributed` の3
stage) を実装設計として凍結しているが、**発効は「次に agent 出力が生まれる loop 再走」と同時で
あり、本 dossier 作成時点では未実装。** v2 では `mechanism_hypotheses: []`(maxItems 0) を維持する
(§4 のとおり7 JSON全てで確認済み)。

### 6.2 T-1279 — generated_from_head fallback (evidence status: wiring。verdict: 該当なし)

`output/insights/2026-08-17_t1279-layer3-head-outside-repo/README.md` (2026-08-17、ユーザー裁定
「厳密化しない」の実装)。解決順 (`:38-45`):

```
generated_from_head =
  1. 呼び手の明示引数
  2. campaign directory の git HEAD
  3. campaign が生成器 source repo の外側 かつ lock が authority 付き v2 なら contract_loader_commit
  4. それ以外は fail-closed
```

**「受領証に束縛された certifying 入口では 3 を使わない」(`:47-48`)。** すなわちこの fallback は
**非 certifying・探索的な report 生成経路**に限定され、certifying 入口 (受理集合を経る経路) は
従来どおり明示引数または campaign git HEAD を要求する。変異 matrix は baseline PASSED・
8/8 KILLED (`:52-61`)、M09 (明示値の等価変換) のみ意図どおり SURVIVED。**この修正は report
生成のロバスト性を上げる工学的成果であり、性能・正式 provenance の主張を含まない。**

**参考 (透明性のための注記):** `orchestrator/campaign/layer3_report.py` は本 dossier 作成時点
(2026-08-21) で worktree `dev-wave-t470-accepted-consumer` によって別途編集中である
(`output/insights/2026-08-20_t425-dependency-reaudit/README.md` の記述による)。本 dossier は
renderer を実行せず既存の生成済み report のみを読むため、この並行編集は本 dossier の内容に
影響しない。

### 6.3 T-326 — layer3_report 本体の深い一致強化 (evidence status: known-no-claim。verdict: 該当なし・実施しない決定)

`docs/phase3.md:583`: 「`layer3_report` 本体の深い一致強化 — 理由: (124) の裁定 (b) により
**実施しない**。強化は新 verifier 経由だけとし、**既存レポートが値の改変を受理する事実は
所見として記録に残す。**」

**したがって、layer3 report が示す数値は「値が改変されていないことを深く検証された」ものでは
なく、この限界は意図的に解消しないと裁定済みである。** 本 dossier が引用する layer3_report.json
の値も同じ限界を継承する。

---

## 7. H1/H2 正式系列 — 未完了

**evidence status: known-no-claim。verdict: 未実施。**

`docs/phase3-8c-preregistration.md:185-197`(「実走前に数値で埋める欄 (空欄のまま実走しない)」)
は次のフィールドをすべて「未記入」と記す:
累積ベンチ実時間の上限、env_tag、H1/H2 の判定パラメータ、master_seed、検定4点、
未既知性再確認の証跡、swapped 対応表、**実走前に確定する6cell manifest**、実行責任者・開始時刻。

同文書 `:199-215`(「実走の前提条件」)が列挙する未充足の主な条件:

1. H1/H2 の workload 定義 (rr80/rr20、1m records/48threads) が 8c supervisor に未実装
   (現行 `WORKLOADS` は rr50/rr95/rr100 の3点のみ、records/threads も 100k/4 に hard-code)。
2. off/swapped arm が未実装 (識別子だけでなく、真の holdout を跨ぐ byte 同一性の機構化が要る)。
3. 実走前の6cell manifest と append-only trial registry が未存在。

`docs/phase3-s8c-autonomous-trial-runbook.md:203-207`: 「pilot は descriptor-on だけで、
off/swapped arm をまだ持たない」「supervisor crash 後の in-place resume、axis-proposer、
複数軸 population は MVP範囲外」。

**過小申告への注意 (段3レンズAの指摘):** 「完全未着手」と書くと、`output/s8b-freeze/holdout_freeze.json`
(selector predictions・selector-runs journal を含む) や `output/s8c-preregistration/condition-freeze/`
の配線 artifact の存在を隠す。これらは H1/H2 の**受理済み実走セルではなく**、将来の正式系列が
使う予定の upstream/配線 artifact である。`output/campaigns/backoff-repro-silo-{balanced,write-heavy}-repro-*`
(s8b holdout freeze から参照される再現用 campaign) も同様に、**正式 H1/H2 の実行済みセルとしては
数えない。**

**結論:** 正式 H1(rr80)/H2(rr20) × on/off/swapped の6セルについて、受理済みの実走セルは無い。
pilot (rr50/rr95/rr100 系) や上記の配線 artifact は正式系列の代替にならない。

---

## 8. screening 非互換の扱い (`6f169f90` と `8ff95955` を混同しない)

`output/insights/2026-07-16_layer3-mechanism-wiring-design.md:45-48` は、screening payload を
含む `bench_done` が layer3 の閉じた `runs` schema と非互換であり、screening を層3対象にするには
schema 拡張の別裁定が要ると明記する。この非互換のため、両 campaign とも `reports/` ディレクトリ
自体が存在しない (WAL/`campaign.lock` のみ)。

**`6f169f90` と `8ff95955` は性質が異なる (段3両レンズが独立に検出・本文書で一次資料により確定):**

- **`6f169f90`**: D58 decisions 本文が名指しする positive control。WAL は
  `build_start → build_done → verify_done(serializable) → bench_done` まで完走し、対照側で
  `screen-slower-than-floor` が発火した (§5.1)。field path は `campaign.lock` 直下ではなく
  **`search_config.screening`**(baseline_ref/floor/high_abort_factor/k を含む)。
- **`8ff95955`**: `campaign.lock#search_config.screening` は同様に設定されているが、
  **WAL は `build_start` の直後に `abort`(`reason: "build-error"`) で終了している**
  (`runs/wal.jsonl:1-2`)。エラー文面: 「ccbench_commit 不一致: 宣言=`dff0f1e` だが
  submodule HEAD=`d706650cdb31`。誤った版でのビルド/偽キャッシュヒットを防ぐため停止する
  (honest-by-construction)。」**screening・bench は一度も発火していない。**
  D58 decisions 本文はこの個体を positive control として名指ししていない。

**推奨文言:** 「D58 screening の機構発火は `6f169f90` の WAL-level positive control として
確認される。`8ff95955` は同種の screening 設定を lock に持つが、ccbench commit 不一致による
build-error で screening/bench に到達していない、別個体である。両方とも layer3 report を持たず、
paper dossier では layer3 certified result・数値比較・mechanism hypothesis として扱わない。」

---

## 9. 明示的に除外した資料 (scope 外・claim の根拠にしない)

網羅性確認 (段3レンズB) で指摘された、S/S'・layer3・D58・H1/H2 のいずれの claim にも直接使わない
既存 campaign・成果物を、除外理由とともに明記する (完全性のための棚卸しであり、着手・修正は
行わない):

| artifact | 除外理由 |
|---|---|
| `output/campaigns/p3-s4-loop-*`、`p3-s5-sort-loop-*`、`p3-kickoff-*` | Phase3 の一般 loop 運用成果物であり、本 dossier が扱う S/S'・layer3 fact-layer・D58・H1/H2 のいずれの一次資料でもない |
| `output/campaigns/p2-5-summary.json` | 別実験 (P2-5) の summary であり本 dossier の scope 外 |
| `output/campaigns/backoff-repro-silo-{balanced,write-heavy}-repro-*` | s8b holdout freeze の再現用 campaign。正式 H1/H2 実走セルではない (§7) |
| `output/campaigns/s1-direct-{floor,block1,block2,develop}-direct-comparison-*` | S1 本体の raw campaign であり、`s1_direct_comparison/report.{md,json}` として既に集約済み。個別 campaign を dossier の一次引用にはしない |
| `output/campaigns/p3-s6-sort-sweep-*` | `sort_best` の入力源だが、campaign 自身は「preliminary、事前登録外、断定 verdict なし」と自己申告 (§3.3)。単体の新規 claim には使わない |

---

## 10. 分類総覧表

| result id | evidence status | verdict | 主な根拠 |
|---|---|---|---|
| S-1a | certified | 不成立 | `s_prime_final_report.md:29-42`、`s1_direct_comparison/report.json` (families.s1a) |
| S-1b | certified; confirmatory (本dossier定義の追試ラベル) | 成立 | `s_prime_final_report.md:44-53` |
| S-2 | certified | 不成立 | `2026-07-13_s6-report-language.md:18-27` |
| S-3 | certified | 棄却 (fail to reject) | `2026-07-13_s6-report-language.md:29-35` |
| S' (族4総合) | certified (human-approved 2026-07-16) | 不成立 | `s_prime_final_report.md:55-64` |
| p2-2 (S-1既知軸input) | certified (D52 §2.1 機械選定) | 該当なし (S-1a入力) | `output/s1-freeze/known_axes_freeze.json`、`p2-2-summary.md` |
| backoff-sweep 通常 (S-1既知軸input) | certified (同上) | 該当なし (S-1a入力) | 同上、各 workload report |
| sort-sweep (S-1既知軸input) | certified化前は known-no-claim (preliminary自己申告)、argmax後は certified input | 該当なし | `known_axes_freeze.json:13,158-168` |
| p3-s8a layer3 fact report (7件) | wiring | 該当なし | `layer3-mechanism-wiring-design.md:43`、各 layer3_report.json |
| mechanism_hypotheses (予約区画) | known-no-claim | 該当なし・未実装 | `layer3-mechanism-wiring-design.md:11-39`、`layer3_schema.json:219` |
| D58 screening 機構 | wiring | 該当なし | `decisions.md:2290`、`bench-first-screening-design.md:195-200` |
| D58 ablation 本体 | known-no-claim | 未実施 | `bench-first-screening-design.md:202-210`、T-1473 handoff |
| T-1279 (fallback修正) | wiring | 該当なし | `t1279-layer3-head-outside-repo/README.md` |
| T-326 (深い一致強化) | known-no-claim | 該当なし・実施しない決定 | `phase3.md:583` |
| H1/H2 正式系列 | known-no-claim | 未実施 | `phase3-8c-preregistration.md:185-215` |
| `6f169f90`(screening WAL) | wiring | 該当なし | `campaign.lock`、`runs/wal.jsonl:8-9` |
| `8ff95955`(build-error WAL) | known-no-claim (screening非発火) | 該当なし | `runs/wal.jsonl:1-2` |

---

## 11. 再現パラメータ

| 系列 | records | threads | 環境 | calibration/floor | ccbench pin |
|---|---:|---:|---|---|---|
| p2-2 (3 workload) | 1,000,000 | 48 | linux-baremetal | between-run 3.0%/within-run 2.28% (skew0.9)、clocks_per_us=1800、extime=3 | campaign 毎の `campaign.lock#ccbench_commit` |
| backoff-sweep 通常 (3 workload) | 1,000,000 | 48 | linux-baremetal | 同上 | `610004b9`: 不明 (lock 未転記)、`484c663e`/`493813a7`: 各 `campaign.lock#ccbench_commit` |
| backoff-sweep `6f169f90` (screening) | 1,000,000 | 48 | linux-baremetal | floor=`0.0010979692594382789`、high_abort_factor=2.0、k=1.5、screening_fixed_us=100 | `d706650` |
| backoff-sweep `8ff95955` (build-error、参考) | 1,000,000 | 48 | linux-baremetal | 同種 screening 設定 (未発火) | 宣言 `dff0f1e` (submodule HEAD `d706650` と不一致のため abort) |
| S1 (S-1a/S-1b) | `output/s1-freeze/measurement_freeze.json`(frozen_at_head `2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1`) の18セル定義を正本とし、本 dossier は独自に record/thread 数を転記・再確認しない | | | | ccbench_pin `d706650cdb31e442bef45b9b4216951d4fb40969` |
| S-2/S-3 | n=20/アーム (main/C4/C5 各20)、判定不能ゼロ | | | | `2026-07-13_s6-report-language.md:10-13` |
| p3-s8a sweep (6件) | 各 campaign の `#workload`/`#meta` 参照 (ccbench `d706650` 系列) | | | | |
| p3-s8a loop (autonomous) | records=100,000、threads=4 (mechanism-wiring-design.md 記載の規模と整合) | | | noise floor は該当キャンペーンに記録なし (`no-matching-env-record`) | |

再現できないパラメータ (資料に値が無い) は上表内で「不明」と明記した。新しい値を補完・推定していない。

---

## 12. file:line / JSON field 索引 (本 dossier の一次引用のみ、親が直接裏取り済み)

### S / S'
- `output/reports/s_prime_final_report.md:18-23,29-42,44-53,55-64,66-72`
- `output/reports/s1_direct_comparison/report.md:5,7-18,20-35,37-42,44-50,52`
- `output/insights/2026-07-13_s6-report-language.md:1-8,10-16,18-27,29-35`
- `docs/phase3-main-experiment.md` (事前登録の正本、個別行は再確認のうえ本文中に転記していない値は参照のみ)

### S-1 既知軸 baseline
- `output/s1-freeze/known_axes_freeze.json` (`selection_rules.p2_2`, `.backoff_fixed`, `.sort`、`sort_best.note` 行)
- `output/campaigns/p2-2-summary.md:1,5-11`
- `output/campaigns/p2-2-silo-{read-heavy,balanced,write-heavy}-enumerate-*/reports/*.md:15,17,23-25`
- `output/campaigns/backoff-sweep-silo-{read-heavy,balanced,write-heavy}-sweep-*/reports/*.md:9-12,16-23`
- `output/campaigns/p3-s6-sort-sweep-{balanced,write-heavy}-sweep-*/campaign.lock`

### layer3 fact-layer / D58 / T-1279 / T-326
- `output/insights/2026-07-16_layer3-mechanism-wiring-design.md:1-9,11-19,21-39,41-49`
- `orchestrator/campaign/layer3_schema.json:6,219`
- `orchestrator/campaign/layer3_report.py` (`build_report` 署名・`_assert_bijection` の存在。行番号は
  段3レンズBが実装バージョン差で不一致を指摘したため、本文書では関数名参照に留める)
- `docs/decisions.md:2268-2296`(D58), `:4235-4264`(D95), `:24160`(D601), `:25195`(D629), `:25217`(D630)
- `output/insights/2026-07-14_bench-first-screening-design.md:195-210`
- 各 `output/campaigns/p3-s8a-trigger-{sweep,loop}-*/reports/layer3_report.json`
  (`#schema_version`, `#meta`, `#workload`, `#runs`, `#verifications`, `#rejects`, `#aborts`,
  `#mechanism_hypotheses`, `#artifact_refs`, `#source_refs`)
- `output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90/{campaign.lock#search_config.screening,runs/wal.jsonl:8-9}`
- `output/campaigns/backoff-sweep-silo-read-heavy-sweep-8ff95955/runs/wal.jsonl:1-2`
- `output/insights/2026-08-17_t1279-layer3-head-outside-repo/README.md:1-8,9-15,36-48,50-65`
- `docs/phase3.md:530,546,583`

### H1/H2 と T-1473
- `docs/phase3-8c-preregistration.md:180-215`
- `docs/phase3-s8c-autonomous-trial-runbook.md:195-210`
- `output/s8b-freeze/holdout_freeze.json`
- `dev-wave-t1473-d58-ablation-preflight` worktree, `docs/handoff/2026-08-21-t1473-d58-ablation-preflight.md`
  (**未 land の handoff。main 取り込み後は本節の記述を再確認する必要がある。**)

### 除外資料の裏取り
- `output/insights/2026-08-20_t425-dependency-reaudit/README.md:143-148` (T-470 が `layer3_report.py` を編集中との記述)

---

## 13. Rule2 / D95 / scope-out / no-push 遵守メモ

- **Rule2:** correctness gate・S/S' の確定判断を緩める記述はない。`certified`(evidence status) と
  `成立`(verdict) を独立させ、run-level `certified verification` と paper-level `certified`
  を書き分けたことで、screening reject や layer3 wiring verification が paper-level の性能主張へ
  昇格しないようにした (§1, §5.1, §6.2)。
- **D95:** 本 wave は docs のみを作成し、コード・テスト・スクリプト・設定の変更を一切含まない。
  Codex 実装子 (段5/6) は不要と裁定し、段2/3 の read-only codex 相談だけを用いた。
- **scope-out:** T-326 (深い一致強化を実施しない決定)、screening schema 非互換、H1/H2 の未充足
  前提条件、D58 ablation の未実施は**記録するだけ**で、修正・再実験・schema 拡張・gate 変更は
  行っていない。
- **no push:** commit のみ行い、remote へは push しない。
- **未測定の明記:** D58 ablation、H1/H2 正式6セル、mechanism_hypotheses、screening 非互換の
  layer3 数値は本文中ですべて「未実施」「非対応」「不明」を用いて明記した (§1 の統制語彙)。
