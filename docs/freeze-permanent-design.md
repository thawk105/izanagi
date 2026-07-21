# freeze 族の恒久設計 (第 1 設計段パッケージ、[T-080])

**状態: 裁定確定 (2026-07-22) — R1..R16 の全項をユーザーが推奨案で承認** (R7 は (b) の生成基準 tree
照合。記録の正本 = worklog 2026-07-22 (3))。本書は新形式の設計正本であり、次の作業は第 2 設計段
(§13 の exact schema 化)。本書は [T-074] (checker を pin しない設計への移行、2026-07-22 承認) と
[T-075] (dangling `frozen_at_head` の生成手順による根絶、同日承認) の実作業であり、起草時点で
コード・凍結成果物は 1 byte も変えていない。工程は三段である — **本書 (骨格と政策の裁定) →
第 2 設計段 (§13 の exact schema 化と変異事前登録) → 実装 wave 群**。§11 の裁定は骨格と政策を確定する
ものであり、それだけで実装 brief が書ける状態にはならない (第 2 設計段が間に入る)。

起草過程: codex 草案 → 敵対相談 2 本 (両 NO-GO) → 親裁定 → 親起草 v2 → 敵対レビュー 2 本 (両 NO-GO、
計 30 所見) → 全所見反映の本版。逐語は `output/insights/2026-07-22_t080-freeze-permanent-design.md`。

---

## 1. 現状の実測 (2026-07-22、すべて再実測)

### 1.1 dangling anchor は 9 blob / 7 anchor (全滅)

git 履歴上の freeze 発行は known 5 回・measurement 3 回・holdout 1 回の計 **9 blob** であり、記録された
`frozen_at_head` は distinct **7 個、9/9 すべて repo に存在しない** (`git cat-file -t` 不成立、
`git fsck --unreachable --dangling` にも無い)。D71 (7)(b) の「計 6 個」は known の発行回数 + holdout の
数え方であり、measurement の独立発行 3 回 (初出 `4b9d86e`、anchor `02c840c4…`) を落としていた (erratum)。

| family | 発行 commit | raw sha256 (先頭) | 記録 anchor (先頭) |
|---|---|---|---|
| known | `80b3010` (path 初出) | `1622ecad` | `c648bbe2` |
| known | `15fcc08` | `e1b0a534` | `ca921338` |
| known | `8f7fca2` | `7a7458df` | `c890e958` |
| known | `b4e5cb6` | `3eb808b4` | `0f304270` |
| known | `e5dfa84` | `354f4b87` | `2066ce6b` |
| measurement | `4b9d86e` (path 初出) | `09dd1585` | `02c840c4` |
| measurement | `b4e5cb6` | `5c719c07` | `0f304270` |
| measurement | `e5dfa84` | `203de36b` | `2066ce6b` |
| holdout | `911f6bc` (path 初出) | `315b1eb8` | `2e20d441` |

path として git 上の追加 (`--diff-filter=A`) は各 family 1 回だけで、残り 6 行は同一 path への再発行
(上書き) である。freeze commit `e5dfa84` の実親は `9c10b5f` で、ファイルが記録する anchor `2066ce6b`
と別物である。これは「記録 HEAD が最終 commit の親でなく、object も現存しない」ことの直接証拠であり、
**rebase と整合する** (amend・cherry-pick 等の履歴書換えとは区別できない。いずれにせよ [T-075] の
対象事象である)。

### 1.2 自己 pin 構造と連鎖

- 3 成果物とも `generator.sha256` = 自分を検証する checker スクリプト全 bytes の sha256 を持ち、
  verify は自己 hash 照合 (`s1_known_axes_freeze.py:724-727`) を ancestry より先に行う。checker の
  1 byte 修正で canonical が即 verify 不能になる (D72 (2)(10))
- measurement は `implementation_hashes.s1_stats.sha256` で解析スクリプト bytes も pin する (同型の病)。
  なお現行 measurement freeze は **統計の入力観測値も出力判定も一切持たない** — 実測値は WAL 側にあり、
  `s1_report.py` が組み立てる。freeze が固定しているのは cell の識別と schedule だけである (§5 の前提)
- freeze 間 chain 2 本: measurement→known、holdout→known (known bytes の変更は 3 成果物へ波及)
- trust root `V1_FREEZE_SHA256` (`s8b_ratified_freeze.py:62`) = holdout bytes。世代交代許可表
  `_TRANSITION_V1_TO_G1` は **13 pointer** で `/known_axes_freeze/sha256` を含まない (実測。
  D72 (3) の「12 pointer」は現行コードと不一致 = erratum)
- `FROZEN_MANIFEST` (`orchestrator/tests/test_frozen_artifacts.py`) は 8 件 literal pin。検査は
  `len == 8`・各 hash 一致・path prefix・64 hex 形式であり、**「旧 8 key の集合が保たれていること」は
  検査しない** (件数が合えば差替えが通る)
- holdout は `design_source` / `generator` の 2 drift (D73 (1)) が現存し、ancestry 以前に落ちる
- known generator の入力 closure は宣言より広い: `campaign.lock` を読み (`s1_known_axes_freeze.py:157`
  で path 構築、`:160` で読込)、`campaign.pipeline.variant_id` (`:27`) と `campaign.model.Genome`
  (`:26`) を import し、`pipeline.variant_id` はさらに `model.py`・`source_digest.py` に依存する —
  **いずれも 63 source record に無い** (相談 A-7 + レビュー R2-3、親が実測確認)。また出力は glob に
  よる directory 列挙 (「無いこと」を含む負の入力) にも依存する
- 消費側: `s8b_oracle_driver.py` は holdout verifier を `:222`、known verifier を `:257` で直接呼ぶ
- `hooks/guard_write.py:91-94` は `output/s8b-freeze/` 配下への直接 Write/Edit を拒否する (F6a)。
  新生成手順はこの hook 契約との整合を要する (§8 step 0)

---

## 2. 設計原則

1. **型分離**: 成果物の field は gate (`G`) と未検証 provenance metadata (`M`) に構造的に分け、
   verifier は `M` を bytes 比較にも機械再構成の入力にも使わない
2. **checker 自己 pin の全廃**: 「成果物が、自分を検証する checker の現行 worktree bytes を gate として
   pin する」構造を全廃する。統計解析 (`s1_stats`) の bytes pin は独立再計算 gate (§5) に置換する。
   **ただし** known の 63 source record 中 24 record (実装 6 ファイル) の raw code pin は本移行では
   入力 closure として残す — これは [T-074] の文言「checker は pin しない」の**部分修正**であり、
   親が独断で決めず R7 として明示裁定に付す
3. **成果物 bytes は外部の二面で固定する**: production 用 literal root registry と `FROZEN_MANIFEST`
   (テスト側 literal)。両者は別 literal として独立保持し (D71 (5) の第三値)、**同一 commit で両面を
   更新することを禁止する** (§7)
4. **生成・受領・承認・発効の commit 分離**: §7 の G/R/A/X topology。人間承認 commit A は
   diff allowlist (approval record のみ) と `AI-Agent: none` を機械検査する (現行 ratified 機構の
   承認分離と同等以上を要求し、`G != A` だけで済ませない)
5. **closed-world 検査**: verify は schema ごとの exact check-ID 集合を持ち、未知・欠落・重複 ID を
   拒否する。ID 集合の正本と required test node の anchor は §10 の機構で固定する (限界も §14 に明示)
6. **fail-closed + 全所見収集**: 前段の失敗が安全に許す範囲で後段も検査し、全所見を構造化して返す。
   例外の文字列一致による判別・握り潰しを禁止する (D73 (2)(3) の恒久対策)

---

## 3. 新形式スキーマ

共通: 新形式は既存 path を上書きせず、版・世代付き別 path に置く (side-by-side、R2)。

- `output/s1-freeze/known_axes_freeze.v2.g1.json` (`schema_version = "s1-known-axes-freeze/v2"`)
- `output/s1-freeze/measurement_freeze.v3.g1.json` (`"s1-measurement-freeze/v3"`)
- `output/s8b-freeze/holdout_freeze.v3.g1.json` (`"8b-holdout-freeze/v3"`)

共通 field (すべて `G`): `schema_version` (exact)、`generation_number`、`supersedes_sha256`
(先代の raw sha256。g1 では legacy 現物の hash)。共通 `M`: `provenance_unverified` —
`{generator: {path, sha256_at_generation}, python_version_at_generation, related_implementations[]}`。
`sha256_at_generation` は発行時の記録であり、現行ファイルとの一致を要求しない (R3)。

### 3.1 known (v2)

現行から: `frozen_at_head` **削除** (§6)、`generator`/`python_version` → `M` へ移動。維持 (`G`):
`what`、`ccbench_pin` (40 桁 full SHA、gitlink と完全一致 — 現行の短縮形は不採用)、`selection_rules`、
`entries` (3 workload × 6 configuration、source record 群含む)、`s1b_pairing`、`reference_values_note`。

**source closure の扱い**: 既知の欠落 — `campaign.lock`、`pipeline.py`、`model.py`、`source_digest.py`
(+ この 4 つからの transitive 依存で出力に影響するもの) — を record へ追加する。ただし **closure の
完全性は機械的に証明できない** (trace は実行された分岐しか観測せず、glob による列挙は「無いこと」への
依存を含む)。よって新形式の立場は「**宣言済み closure**」である: (i) 宣言した record は全件 bytes 照合、
(ii) 列挙依存は holdout の `search.file_enumeration` と同型の**列挙 snapshot** として凍結、(iii) 宣言の
過不足は実装 wave で import graph + I/O trace を**補助として**洗い、最終判断はレビューで行う。
最終的な record 数は生成時に確定する (「63 + 4」を事前確定しない)。24 record / 6 実装ファイルの
raw code pin の扱いは R7 (worktree 照合を維持するか、生成基準 tree (§6 の H_gen) の blob 照合へ
置換するか)。

### 3.2 measurement (v3)

現行から: `frozen_at_head` 削除、`generator`/`python_version`/`implementation_hashes.s1_measurement_freeze`
→ `M`、`implementation_hashes.known_axes_freeze` → top-level `known_axes_freeze = {path, sha256}` (`G`)
に改名 (code pin ではなく上流成果物の output pin であり維持)。維持 (`G`): `cells` (18)、`comparisons`
(12 対)、`s1b_pairing`、`operating_point`、`workload_flags`、`master_seed`、`schedule`、`schedule_hash`、
`ccbench_pin` (known と同一 40 桁)。

**新設 (`G`、§5 の前提)**: 現行 freeze は統計の入力も出力も持たないため、v3 で追加する —

- `observations`: cell × repetition の実測値 (schedule と 1:1)。各値に WAL 由来の source pointer
  (env_tag、WAL record 識別子、値の由来 hash) を付け、凍結する
- `analysis_results`: comparison ごとの凍結判定 — statistic (2 倍整数 rank-sum)、p 値の
  numerator/4900、gate 結果、family 判定 (**現行 `s1_stats.family_p` の intersection–union 規約 =
  family 内 `max(p*)`。Holm ではない** — S-2/S-3 を跨ぐ 4-family Holm は measurement freeze の外)、
  および効果量 (現行 `EffectSizes` 相当。効果量を凍結対象から外すと「効果量だけを壊す変更」が
  素通りするため含める)。float は `float.hex()` 表現。exact schema (単位・丸め・WAL pointer の形式)
  は第 2 設計段 (§13)

`implementation_hashes.s1_stats` の bytes pin は廃止し、`M` の `related_implementations` に発行時記録
として残す。

### 3.3 holdout (v3)

現行から: `frozen_at_head` 削除、`generator` → `M`、`lifecycle_stage` (`G`) を新設し
`"pre-measurement" / "ratified-floor"` を明示する (現行の「floor/budget の null 有無から schema を推測」
を廃止)。維持 (`G`): `design_source` (drift は g1 発行時に人間同席で再 pin)、`known_axes_freeze`
(新 known g1 を指す)、`match_convention`、`search`、`holdouts`、`positive_control` (§10)、`derangement`、
`confirmed_by`/`confirmed_at` (§7 の承認に束縛)、`env_tag`/`floor`/`budget`/`floor_protocol`/
`floor_source`/`measurement_closure` (g1 では null/空)、`refreeze_note`/`scope_note`/`binding_rule_note`。
`confirmed_by`/`confirmed_at` は **G 時点の search 同席確認の記録**であり (この時点で bundle は未確定)、
最終的な束縛は A の bundle digest 承認が事後に与える (receipt が confirmed_by と成果物 hash の対応を
記録し、A がそれを含む bundle を承認する)。

**検査の層分離** (レビュー B-9): `unknownness` の検査は「凍結 snapshot の再計算一致」(immutable、
何度でも成立) と「launch 時の live search」(oracle 起動時のみ) に分離する。verify_document が
live search を無条件再実行する現行 v1 の形は踏襲しない — holdout を実走した瞬間に repo 内へ hit が
生じ、g1 が自己失効するため。現行 ratified-v2 が既に持つ分離 (snapshot 検査と launch scan) を踏襲する。
**この分離は static verify の受理集合を広げる** (現行 verify なら拒否する「現在 repo に hit がある
状態」を static には受理し、launch gate だけで拒否する)。この交換は §14 の損失表に明示する。

---

## 4. verify() 契約

- **public loader 一本化**: consumer は `verify_document()` を直接呼ばず、raw bytes を一度だけ読む
  loader を使う。返却は deep-immutable document + raw sha256 + schema/generation + `VerificationReport`。
  失敗は typed `FreezeVerificationError(report)` — 文字列一致での判別を禁止する
- **四型分離**: `candidate` (path 未登録、検証のみ) / `registered-inactive` (literal root 登録済み・
  **人間承認前**) / `approved-inactive` (A 済み・未発効) / `active-official` (現 active bundle の
  構成員) を**別の型**で返し、official 経路は `active-official` 型しか受け取れない (引数指定ミスで
  昇格しない構造)
- **closed-world check registry**: schema ごとに exact check-ID 集合を定義し、report は全 ID を
  ちょうど 1 回ずつ含むこと自体を検査する。`not_evaluated` は `blocked_by` (実在する先行 check ID、
  非循環) を必須とし、error / not_evaluated が 1 件でもあれば失敗。ID 集合の全列挙は第 2 設計段 (§13)
- **検査順**: raw bytes → 外部 root 照合 (不一致でも parse 可能なら後段継続、全所見収集) →
  strict JSON parse (duplicate key / NaN 拒否) → schema dispatch → 入力 pin 群 → 局所 invariant →
  機械再構成 (上流成立時) → generation chain / receipt / active 検査
- **エラー分類**: `document.* / schema.* / output.* / input.* / contract.* / authorization.* /
  lineage.* / environment.git.* / dependency.*` の stable reason code。git 実行障害・非 commit object・
  想定外 object type を内容不一致と混同しない (D73 (3) の恒久対策)
- **git hardening (receipt/履歴監査)**: 検証開始時に単一の検証基準 commit **`H_v`** (検証時 HEAD) を
  捕捉し、履歴 query は **`H_v` から到達可能な graph に限定**する (`--all` の全 ref 探索はしない —
  可変 ref 集合は単一捕捉に固定できない。TOCTOU 拒否)。`refs/replace/*` は無効化に加え**存在自体を
  拒否**、grafts/shallow 拒否、object type と parent count の検査、導入 commit の一意性検査 (§6)。
  現行 ratified verifier (`s8b_ratified_freeze.py:306` 付近) と同等以上。`H_v` は §6 の生成基準
  **`H_gen` (= G^)** とは別物である (X 後の検証では通常一致しない)
- **path 防壁**: 未検証 document 由来の path は repo-relative 正規化 + `..`/絶対 path 拒否に加え、
  **worktree の file open ではなく git tree の blob 読取で照合する** (symlink 経由の repo 外読取を
  構造的に排除。§6 の基準 tree 照合と同一機構)

---

## 5. 統計 gate — `s1_stats` bytes pin の代替

有限 conformance vector だけへの置換は**不採用** (相談 2 本が独立に BLOCKER: 列挙外入力でだけ誤る実装が
素通りする)。「現行コードでの再計算」も不採用 (code+artifact 同時変更に無力、相談 A-2)。採る形:

- **§3.2 の凍結入出力 + 独立参照実装**: v3 measurement freeze は `observations` (凍結入力) と
  `analysis_results` (凍結出力) を持つ (§3.2)。verifier は `observations` から 12 comparison すべての
  statistic・p numerator・family 判定・**効果量**を、`s1_stats.py` とは**別 module の独立実装**
  (層化 exact permutation 4900 通り + 効果量計算の再実装、レビュー分離) で再計算し、
  `analysis_results` との完全一致を要求する (効果量も再計算主体は同じ独立実装 — 凍結だけして
  再導出しない field を作らない)
- `observations` と WAL の照合は launch/audit 層の検査とし (WAL は freeze の外にある)、static verify は
  「凍結入力 → 凍結出力の再導出一致」を gate とする。**ただし `observations` の WAL 由来 source
  pointer の照合 audit は A (人間承認) の前提検査に含める** — 出所を検証しない観測値の凍結は §6 の
  入力 tree 束縛の抜け道になるため。exact な照合形式は第 2 設計段 (§13)
- conformance vector (strict ordering / tie / 対称 / gate fail / family max / wrong shape / 非有限値 /
  invalid alternative の拒否を含む) は独立実装**自身**の受入テストとして持つ (gate の主体ではない)
- 独立実装の正しさは実装 wave で相互変異 (production 側変異 → verifier 赤 / verifier 側変異 →
  自己検査赤) により裏取りする

**明示する限界**: 独立再計算 oracle を持つのは統計だけである。known の選定 extractor と holdout の
search には独立 oracle が無く、「壊れた extractor + それで生成した成果物 + 追随した literal root」を
機械だけで拒否する層は存在しない。防壁は §7 の承認分離・§10 の変異/golden・レビューであり、
この残余リスクは §14 の損失表に載せてユーザーが受け入れを判断する。

---

## 6. anchoring — `frozen_at_head` の後継

- **成果物からは field 廃止** (P2 維持)。成果物内の自己言及 field としては、生成時に未確定の commit
  SHA を正しく持つ方法が無い (生成時 HEAD は履歴書換えで置き換わった実績 9/9)。dangling の根はこの
  field の存在にある — ただしこの言明は「成果物内の当該 field」に限る狭義であり、receipt 側の
  commit 参照は履歴書換えで壊れうる (fail-closed に検出される。下記)
- **束縛は receipt 層で非自己参照に、かつ生成入力 tree まで行う** (相談 A-7 + レビュー R1-3/R2-4 を
  統合): receipt は各成果物について次を記録し、verifier が再検査する —
  1. **導入 commit `G`**: 版付き新 path は「git 上の追加がちょうど 1 回」であることを要求し、
     **`H_v` (§4) から到達可能な履歴**の `--diff-filter=A` 探索で候補が 1 個・非 merge・
     delete/re-add 無しを検査する (複数候補・merge・再追加は拒否。歴代 legacy path はこの導出が
     効かないため、receipt の legacy inventory には発行 commit を明示記録し「記録どおり blob が
     存在する」ことだけを検査する)
  2. **生成基準 commit `H_gen` = `G^`**: G は first-parent が `H_gen` の非 merge commit であること
  3. **入力 tree 束縛**: 全 source record・`campaign.lock` 等の宣言 closure・ccbench gitlink が
     **`H_gen` の tree の blob/gitlink と一致**すること (worktree 照合ではなく git blob 読取。dirty
     worktree や無関係 tree で生成した成果物を、成果物 blob 一致だけで受理しない)。measurement の
     `observations` は WAL 由来のため tree 束縛の対象外であり、代わりに §5 の A 前 WAL 照合 audit が
     出所を束縛する
  4. 成果物 blob が G の tree に存在し raw sha256 が一致すること
- **限界の明示**: 履歴書換えは receipt の G/H_gen 記録を壊す。これは fail-closed に検出される破損で
  あり、修復は新 receipt の人間承認を要する — 沈黙した dangling (現状) からの改善であって
  「書換え不能」ではない
- [T-075] の裁定文言「生成手順の変更で根絶」に対し、本設計の充足形は「field 廃止 + §7 の publish 手順
  (G を rebase 予定のない位置でのみ作る) + receipt の H_gen-tree 束縛」である。**この充足形でよいかは
  ユーザー明示確認事項 (R1)** — 設計者が「schema 変更 = 手順変更」と独断で読み替えない (レビュー B-14)

---

## 7. 生成・受領・承認・発効 — commit topology (G / R / A / X)

**前段 (step 0)**: `hooks/guard_write.py` は `output/s8b-freeze/` への直接書込を拒否する (F6a)。
新生成手順が書く path (holdout g1・pointer・approval record) の hook 契約整合を先に設計・実装する
(hook の迂回ではなく、hook 側の契約更新として。所有 wave は §12)。

**G (候補生成、AI 可)**: 依存 DAG 順 (known → measurement → holdout) に候補 bundle を生成する。
worktree clean guard は「開始時 snapshot + 事前宣言した bundle-owned path の**新規追加のみ**許す」
形にする — 許可 path 集合は生成開始前に確定・記録し、既生成ファイルの変更・削除・rename・symlink は
拒否、並行 writer は snapshot 差分で検出する。holdout の search 列挙対象と staging path の関係
(staging が列挙や hit 集合を汚さないこと) は第 2 設計段で exact に定める。holdout の repository search
再実行と `confirmed_by`/`confirmed_at` の入力はユーザー同席で行う。既存の existing-file 二層防御は
維持し、「人間が削除して再生成」の運用は廃止 — land 済み世代は削除せず gN+1 を新 path に作る。
candidate は wave branch 上で作ってよいが、**canonical への publish (G の確定) は rebase 予定のない
位置 (local main) でのみ行う**。

**R (receipt、AI 可、G の後)**: G の導入情報 (§6 の G/H_gen/blob) を記録した transition receipt を
独立 commit で追加する。receipt に自己申告 (`verified: true` 等) は置かない。

**literal 面の更新 (R の後、A の前、2 commit に分離)**: production root registry の更新 commit と
`FROZEN_MANIFEST` の更新 commit を**別 commit** にする (単一 commit が両 literal 面を書くことを禁止、
相談 A-2/レビュー R1-8 対応)。この時点では全て `registered-inactive` (§4 の型 — **登録済み・人間承認
前**) であり official 挙動は変わらない。

**A (人間承認)**: 人間が **bundle digest** を承認する。digest の定義: 対象 4 hash (known g1 /
measurement g1 / holdout g1 の raw sha256 + receipt の raw sha256) を固定順で並べた canonical JSON に
domain separator を付けた sha256 (exact 符号化は第 2 設計段)。A commit は G/R/literal commit と
pairwise 非同一で、それらの後裔であり、**diff は approval record 1 ファイルの追加のみ**、
`AI-Agent: none`。現行機構 (`s8b_ratified_freeze.py:1160` 付近) は「approval + pointer の 2 追加」を
許す**類似の** allowlist 検査であり同一ではない — 新設計では pointer 更新は X に分離する。A 承認後の
成果物が `approved-inactive` (§4) になる。承認の意味 (digest 確認のみか、内容の semantic review を
含むか) は R14 の裁定事項。A/R/literal/X の全 commit の parent/diff/merge 制約の exact 化は
第 2 設計段 (§13)。

**X (発効)**: **active-bundle pointer** の更新 commit。pointer は 3 family の raw sha256 組 + 対応する
approval record への参照を持ち、consumer は pointer を**一度だけ読む bundle resolver** で 3 成果物を
同一 pointer 状態から解決する (family 別の個別 resolve を禁止 — 混在の構造的防止はこの resolver 契約が
成立して初めて主張できる)。**bootstrap**: pointer は §8 step 2 で「legacy を指す g0 状態」として
dormant 導入し、step 3 で consumer を pointer 経由へ移行する (この時点の挙動は legacy と同一 =
挙動保存)。X は「pointer 値の g0 → g1 更新」だけの commit になる。X の実行主体 (人間 commit か、
A 後の AI 実行を許すか) は R13 の裁定事項。複数 approved bundle からの一意選択・rollback・fork/gap/
revocation の拒否規則は第 2 設計段で exact 化する (§13)。

## 8. 移行計画 v2 (実装 wave 群の設計)

前提: 各 step は独立に green を保ち、X (発効) までは旧 lane が official のまま。

0. **hook 契約整合** (§7 step 0)
1. **legacy lane の固定**: 現行 3 path・`FROZEN_MANIFEST` 既存 8 件・`V1_FREEZE_SHA256`・旧許可表・
   旧 equality chain は**一切変更しない** (歴史レーン)。legacy loader は「raw bytes exact のみ保証、
   source/head の現在有効性は主張しない」ことを明文化する
2. **新 module 群 + pointer (g0) + observation schema の dormant 導入**: 新 schema/checker/loader/
   独立統計実装/lineage 契約/active pointer (legacy を指す g0)/**observation 伝播 schema** (WAL
   `campaign-start` の freeze identity/observation field、oracle report/judge の observation 契約、
   calibration の freeze identity 後継) をすべて dormant で追加する。**observation の格納先を X より
   前に用意する** (D73 (4) の伝播条件を発効時点で満たすため — 順序が逆だと「official gate は変わったが
   変化を永続記録できない」段階が生じる。レビュー R1-6/R2-7 対応)
3. **consumer の pointer 化 (挙動保存)**: oracle driver を含む全 consumer を bundle resolver 経由へ
   切替える。pointer は g0 (legacy) のままなので refusal 集合を含む挙動は不変 — これを受入で実測する
4. **候補 bundle 生成 (G)**: §7-G。g1 の値は legacy 現物からの機械射影 + 現行入力の再 pin +
   measurement の凍結入出力 (§3.2) で構成し、新旧 gate projection の一致を receipt verifier が検査する
5. **receipt (R)**: `output/freeze-migrations/legacy-to-permanent-g1.receipt.json`。inventory は
   §1.1 の **9 blob 全件** (発行 commit・path・blob OID・raw sha256・記録 anchor・anchor_status・
   disposition)、successors 3 件 (§6 の G/H_gen/tree 束縛)、projection contract、除去した主張
   (`/frozen_at_head`)、`M` 化した field
6. **literal 面 2 commit**: production root registry / `FROZEN_MANIFEST` を別 commit で更新。
   manifest テストは `len == 12` に加え **旧 8 key ∪ 新 4 key の exact key-set 検査**へ強化する
   (件数だけでは旧 entry の差替えを検出できない — レビュー B-13)
7. **人間承認 (A)**: §7-A の bundle digest 承認 commit
8. **発効 (X)**: pointer g0 → g1。**この step は refusal 集合を変えるため、[T-068] の再裁定 (R10) と
   同時にのみ実行する** (親が先取りして T-068 を実質消化しない — 再裁定停止点)

**再裁定停止点** (worklog の「T-080 設計確定後に再評価」を親が先取りしない):
**[T-077]** — step 4 の人間同席再 pin は解消の**候補**であり、これを十分とみなすかは R11。
**[T-078]** — §10 の外部固定 fixture 契約は再定義の**候補**であり、旧裁定の充足とみなすかは R12。
**[T-068]** — step 8 で不要になる見込みだが、方式 B を実装するか / 恒久設計で superseded とするか /
legacy lane 用に残すかは R10。三件とも本書では閉じない。

## 9. 波及面 (本設計時点の列挙 — 完全性は主張しない。実装 wave 開始時の再列挙が必須)

実装 wave 開始時に `git grep` で**再列挙して本表と突き合わせる**こと (dev-wave 作法)。本設計時点の
列挙 (相談・レビュー 4 本の指摘を統合済み):

- **literal pin**: `test_frozen_artifacts.py` (FROZEN_MANIFEST)、`s8b_ratified_freeze.py`
  (`V1_FREEZE_SHA256`、許可表 2 面、`EQUALITY_CHAIN_ADJACENCY`)、`s8b_approved.py`
- **freeze 間 chain**: `s1_measurement_freeze.py` (known 連鎖)、`s8b_holdout_freeze.py`
  (known 成果物の直接消費 + `docs/phase3-8b-descriptor-design.md` の pin)
- **S-1 系 consumer**: `s1_report.py`、`s1_direct_comparison.py`、`s1_verify_extime_calibration.py`
- **8b 系 consumer**: `s8b_oracle_driver.py`、`s8b_oracle_manifest.py`、`s8b_freeze_io.py`、
  `s8b_floor_contract.py`、`s8b_floor_campaign.py`、`s8b_launch_cert.py`、`s8b_selector_freeze.py`
  (+ `pre_oracle_head` — 実在 commit 要求の隣接 dangling 候補、§13)、`s8b_prediction_runner.py`、
  `s8b_verdict.py`、`s8b_budget.py` (ledger の freeze_sha256 永続化)、`s8b_run_marker.py`
  (path 再読による identity 生成)、`s8b_oracle_artifacts.py`、`s8b_oracle_report.py`、
  `s8b_oracle_judge.py`、`s8b_materialization.py`
- **観測・記録面**: WAL schema 実装 (campaign-start)、calibration 派生
  (`output/env/linux-baremetal/calibration/s1_verify_extime.json` — 歴史物として不変)、
  `output/reports/s1_direct_comparison/report.json` (同)
- **テスト面** (実装 wave で exact 化必須。総称で所有を済ませない): 上記各 module の direct tests、
  `conftest.py` (`REAL_REPO_SERIAL_NODES` 等) と `test_real_repo_serialization.py` の golden 2 面、
  `test_s8b_repo_scan_invariant.py`、`test_hooks.py`、`test_plain_runner_coverage.py`、
  `test_s8b_budget.py`、`test_s8b_oracle_report.py`、`test_s8b_protocol_builder.py`、
  `test_s8b_selector_input.py`、`orchestrator/tests/README.md`
- **hooks**: `hooks/guard_write.py` (§7 step 0)、`hooks/README.md`
- **docs 面**: `docs/README.md` (本書の登録)、`tools/check_docs.py` の LIVING_DOCS への本書追加
  (tools はコードのため実装 wave で行う)

## 10. 過去 failure 型の再発防止 (実装 wave の受入条件)

- **F9 型 (宣言 pin のドリフト未検出)**: 本設計が依拠する検査 (real-repo canonical verify、receipt
  履歴再導出、manifest exact key-set、bundle resolver 整合) は、`test_frozen_artifacts.py` 内の
  literal な **required node manifest** (`REQUIRED_FREEZE_NODES` — `test_file.py::test_name` の
  文字列集合) に登録し、meta-test が「全 node が収集可能である」ことを検査する。本 repo に CI は
  無いため、機械 anchor はこの meta-test と受入全走である。**manifest 自体が同 repo 内の可変コードで
  ある限界は残る** (§14) — 緩和は「node manifest の変更を含む commit は A 型レビュー対象」という
  運用規律であり、機械保証ではない
- **D68 (7) 型 (fixture 隠蔽)**: 新テストで production builder を fixture echo へ monkeypatch する
  こと、production の現行 hash を fixture へ動的注入することを禁止する。外部 I/O・git 値だけを固定し、
  実 extractor と再構成を動かして**独立 golden** と比較する (D73 (6) の形)
- **T-078 型 (恒真 positive control)**: positive control は同じ search 実装が自己生成する値でなく、
  **exact path + bytes hash で root registry に pin された外部固定 fixture** に対する baseline pass /
  単一理由 mutant fail / revert pass の 3 点で成立を示す (fixture と期待値の同時更新は literal 面の
  分離 (§7) で検出面を残す)

## 11. ユーザー裁定 (R1..R16)

**注意**: 推奨案は §3〜§8 の骨格と相互依存している。**非推奨案を選ぶ場合 (特に R2/R4/R5/R9)、
本骨格は成立しないため第 1 設計段への差し戻しになる** — 代替骨格は本書に無い。

**骨格の択一 (R1..R9)**:

- **R1. [T-075] の充足形**: field 廃止 + publish 手順 (G を rebase 予定のない位置でのみ確定) +
  receipt の H_gen-tree 束縛 (§6) を「生成手順の変更で根絶」の履行とみなすか。**推奨: みなす**
- **R2. canonical path**: side-by-side 版付き path (推奨) / 旧 path 上書き (legacy bytes・V1 root・
  旧許可表を壊すため非推奨)
- **R3. code provenance**: `provenance_unverified` として記録保持 (推奨) / 完全削除
- **R4. 統計 gate**: v3 schema へ凍結入出力 (`observations`/`analysis_results`) を追加し独立参照実装で
  再計算 (推奨、§5) / 有限 vector のみ (相談 2 本が BLOCKER) / code-hash registry (自己 pin 問題の
  移動)。推奨案は freeze の形自体の変更 (観測値の凍結) を含むことに注意
- **R5. 承認 topology**: G/R/literal×2/A/X の commit 分離 + A diff allowlist (推奨、§7) /
  現行どおり単一 migration commit (承認分離の退行のため非推奨)
- **R6. 旧 transition/equality**: 凍結保持 + 新契約を別 module に定義 (推奨) / 旧表拡張 (非推奨)
- **R7. [T-074] の部分修正 — 実装 record の raw code pin**: known の 24 record / 6 実装ファイルを
  本移行では入力 closure として残す。これは承認済み文言「checker は pin しない」の**部分修正の再裁定**
  である (択一として隠さない)。選択肢: (a) worktree 照合のまま維持 (現行同等の brittleness が残る) /
  (b) §6 の生成基準 tree (H_gen) の blob 照合へ置換 (checker 修正と無関係に成果物が壊れる病は消え、
  provenance は保たれる。**推奨**) / (c) 全削除 (提示のみ、非推奨) / (d) semantic projection 全面転換
  (将来の別裁定へ)
- **R8. receipt inventory (確認事項)**: 9 blob / 7 anchor 全件を receipt に記録する (§1.1 は実測事実で
  あり択一ではない — 「6 freeze」表記の worklog/D71 への erratum 追記込みで確認を求める)
- **R9. 発効機構**: active-bundle pointer + 単一読取 bundle resolver + g0 bootstrap (推奨、§7-X) /
  consumer 個別切替 (混在が生じるため非推奨)

**運用・境界の裁定 (R10..R16)**:

- **R10. [T-068] の処理**: X (step 8) と同時に「恒久設計により superseded」として閉じる (推奨) /
  方式 B を legacy lane 用に別途実装 / 現状維持
- **R11. [T-077] の処理**: g1 発行時の人間同席再 pin (design_source 再 pin + generator の `M` 化) を
  2 重 drift の解消とみなす (推奨) / 別途の修復を要求
- **R12. [T-078] の処理**: §10 の外部固定 fixture 契約を positive control 再定義として旧裁定の充足と
  みなす (推奨) / 別途裁定
- **R13. X の実行主体**: X (pointer 更新 commit) も人間が行う (推奨 — 発効は不可逆な運用切替のため) /
  A 承認後の AI 実行を許す
- **R14. A 承認の意味**: bundle digest の確認 + 添付レポート (verifier 全緑・projection 一致) の確認
  (推奨) / digest 確認のみ / 内容の semantic review まで人間が行う
- **R15. family 世代政策**: bundle lockstep (3 family の世代を常に一括発効。推奨 — 混在解決規則が
  自明になる) / 整合する任意 tuple (柔軟だが整合規則の exact 化が必要)
- **R16. source closure の恒久限界の受諾**: 宣言済み closure (§3.1) は機械的完全性を証明できない —
  「宣言 record 全照合 + 列挙 snapshot + 機械補助 + レビュー」を closure 保証の恒久形として受け入れる
  か。**推奨: 受け入れる** (代替の「機械的完全証明」は trace の分岐被覆・負の入力の性質上、存在
  しない)。受け入れない場合は R7 (d) の semantic projection 全面転換を先に設計する必要がある

## 12. 実装 wave 分割 (責務案 — exact なファイル所有表は第 2 設計段で確定)

以下は責務の分割案である。**「各 file は一 wave のみ所有」の検証可能な列挙は、第 2 設計段で §9 の
再列挙とともに exact な file 集合として確定する** (本段階で総称のまま「素集合」を主張しない)。

- **W-0**: hook 契約整合 (`hooks/guard_write.py`、`hooks/README.md`、`test_hooks.py`)
- **W-a**: 共通基盤 — loader/四型/エラー分類/check registry (`freeze_permanent_io.py` 新設)、
  `conftest.py` の node manifest 拡張、独立統計実装 (新 module) と相互変異テスト
- **W-b**: known v2 + measurement v3 の schema/generator/verifier (新規ファイル + 各 direct test +
  独立 golden)
- **W-c**: holdout v3 + lineage/approval/active-pointer 契約 (新規ファイル + direct test)
- **W-d**: consumer の pointer 化 (挙動保存、§8 step 3) — S-1 系 + oracle 系 + `s8b_freeze_io.py` +
  observation 伝播の dormant 配線 + **挙動保存を実証する real-repo golden**
  (`test_real_repo_serialization.py` を含む — 挙動保存の検証をこの wave 内で行い、後段へ遅らせない)
- **W-e**: G/R/literal×2/A の実行 (人間同席 wave。receipt・root registry・`test_frozen_artifacts.py`
  を所有)
- **W-f**: X (発効、R10 と同時) + 統合記録 — `orchestrator/tests/README.md`、
  `docs/README.md`/`tools/check_docs.py` 登録、phase doc/worklog/decisions

依存: W-0 → W-a → W-b/W-c (並列可) → **W-d (pointer 化) → W-e (生成・承認)** → W-f (発効)。
§8 の step 順 (2 dormant → 3 pointer 化 → 4..7 G/R/literal/A → 8 X) と一致させる。
`pre_oracle_head` (`s8b_selector_freeze.py`) の内容 pin 化は W-e/W-f の前提タスクとして別掲する (§13)。

## 13. 第 2 設計段の残課題 (R1..R16 裁定後、実装 wave 前に仕様化)

1. lineage/approval/active pointer/receipt の exact schema — 件数・一意性・fork/gap/revocation/
   rollback/**approval の失効 (expiry)** の拒否規則、複数 approved bundle からの一意選択、全 family の
   gN→gN+1 許可面、G/R/literal/A/X の parent/diff/merge 制約
2. bundle digest の exact 符号化 (canonical serialization・domain separator・hash algorithm)
2b. `observations`/`analysis_results` の exact schema (単位・丸め・`float.hex()` 規約・効果量の
   field 構成・WAL source pointer の形式と A 前照合 audit の手順)
3. observation 伝播 (§8 step 2) の WAL/report/judge/calibration 各 exact schema
4. check-ID registry の全列挙 (schema ごと) と required node manifest の初期集合
5. §7-G guard の exact 仕様 (許可 path の事前宣言形式、holdout search と staging の分離)
6. `pre_oracle_head` (`s8b_selector_freeze.py`) の内容 pin 化 — 本設計と同型の dangling 候補
7. source closure の宣言確定 (record 追加分の列挙と列挙 snapshot の形式)
8. §9 の再列挙と W-0..W-f の exact ファイル所有表
9. 実装各 wave の変異テスト事前登録 (B-057。単一理由性の確認込み — 本 wave は実装差分が無いため未登録)

## 14. 損失と限界の明示 (規律 2 の交換条件 — ユーザーが受け入れを判断する)

**v2/v3 形式が現行 gate から失うもの (受理集合の変化)**:

| 現行では拒否される | 新形式では static verify を通りうる | 回収層 |
|---|---|---|
| checker/generator の任意 bytes drift | 挙動を変えない checker 編集 (コメント等) | 意図された緩和 (T-074 の目的そのもの)。**再構成/独立再計算が拒否するのは凍結入出力の判定挙動の変更に限る** — それ以外の挙動 (入力検証・診断等) の drift は素通りする |
| `s1_stats.py` の任意 bytes drift | 凍結入出力の再導出に影響しない変更 (入力検証・将来入力のみの破損等) | 独立実装の受入 vector + 相互変異 (§5)。完全ではない |
| holdout verify 時点の live hit | snapshot 一致だが現在 repo に hit がある状態 | launch 時 live scan (§3.3)。static には受理する交換 |
| (現行も拒否できない) 壊れた extractor + 追随成果物の同時投入 | 同左 | 承認分離 (§7)・golden・レビュー。機械 oracle は無い (§5 の限界) |

**限界**:

- 人間承認は暗号署名ではない。確認者の真正性は repo review 過程に依存する
- literal root 二面は「別 literal・別 commit・別 review 面」であって暗号学的第三者ではない。
  「改竄不能」とは主張しない (D68 (6) と同じ言葉の規律)
- required node manifest・check-ID registry は同 repo 内の可変コードに置かれる。機械 anchor は
  meta-test と受入全走であり、manifest ごと消す変更を機械だけでは拒否できない (運用規律で緩和)
- 履歴書換えは receipt の G/H_gen 記録を壊す (fail-closed 検出、§6)。修復は人間承認の新 receipt
- 悪意ある checker を成果物側から防ぐ設計ではない。防壁は独立再計算 (§5)・相互変異・レビュー分離・
  closed-world registry の組合せである
