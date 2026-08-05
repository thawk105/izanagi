# [T-478] 較正の contract 世代移行 — 裁定パッケージ

2026-08-05 / wave `dev-wave-t478-calibration-contract-generation` / base = local main `44ff1c11`

**本 wave は実装しない。** 成果物はこの設計と、末尾の設計択一 5 件である。
実装は [T-419] U-2 (較正再取得) の wave が所有する。
起票根拠 = [T-452] U-7 = (a) の裁定 (「[T-478] を起票し較正再取得の前提に置く」)。

構成: 段 2 に codex read-only の設計起草を 1 本、段 3 に敵対 2 レンズ (閉包の網羅性 /
正しさ防壁・恒真化) を並列で当て、段 4 で親が裁定した。**両レンズとも NO-GO**、
所見 19 件のうち **real 18 / 部分反証 1 / refuted 0**。逐語は同ディレクトリの
`s2-plan.md` / `s3-lensA.md` / `s3-lensB.md` / `s4-ruling.md`、
親の独立実測は `parent-closure-measured.md` / `parent-design-candidate.md`、
brief は `brief.md`。

---

## 1. 何が壊れているか (実測)

較正 artifact の path と sha256 は env contract の field であり、`contract_sha256` は
**全 field の canonical JSON の sha256** として導出される
(`orchestrator/campaign/env_contract.py:145-160`)。実測値は
pegasus = `e576e9cd1369bba3…`、linux-baremetal = `1b2ee85346a4c867…`。

較正を再登録すると `contract_sha256` が動く。ところが凍結された floor protocol
`output/s8b-freeze/floor_protocol.json` は **その値を bytes の中に内包**しており、
同 file は次の**2 つの相反する要求**を同時に受けている。

- **history 側**: campaign launch は、この file が `pre_oracle_head` の git blob と
  worktree とで **byte 一致**することを要求する (`s8b_floor_campaign.py:1411-1416`)。
  さらに writer は固定 path の create-only である (`:138-149, 566-603`)。
- **current 側**: `validate_protocol` は、この file が内包する `contract_sha256` が
  **現行 registry の値と完全一致**することを要求し、不一致は `FloorContractError` である
  (`s8b_floor_contract.py:139-151`)。

**この 2 条件は較正の再登録後に同時には満たせない。** 旧 bytes を残せば current 側が拒否し、
書き換えれば history 側と `FROZEN_MANIFEST` (23 件、`test_frozen_artifacts.py:38-85,139-153`) と
selector journal の `protocol_sha256`(`261cec1c…`) が同時に破れる。
**これが T-478 が解く本体である。** 敵対レンズ B もこの推論を反証できないと判定した
(第三の道は存在しない、`s3-lensB.md:112`)。

そして `env_contract` の解決経路は `lookup(env_tag)` **だけ**である
(`env_contract.py:202-209`)。contract hash からの逆引きも世代の概念も無い。
production の呼び出しは **21 箇所** (親実測。campaign 18 + T-126 2 + T-419 probe 1)。

### 守る対象は「過去の測定値」ではない

実測: `output/s8b-freeze/` には ratified freeze も完走 campaign 成果物も**存在しない**
(`find output -iname "*ratified*"` = 0 件)。D143 が記録したとおり pegasus の campaign は
まだ build に到達していない。

したがって守るべき「既存 certified 参照」の実体は、**「floor データを見る前に protocol と
selector 予測が確定していた」という事前登録 (blind seal) の性質**である。
移行設計の第一の禁止事項は、較正更新を口実に**実験設計や予測を選び直せる経路を作らないこと**になる。

---

## 2. 参照閉包 (実測)

段 2 が意味的 **47 面**を列挙し、敵対レンズが **8 面**を追加、親が **1 面**を訂正した。
全件表は `s2-plan.md:31-108` (production 34 / artifact・test・docs 13 / 明示除外)、
追加分は `s3-lensA.md:30-66`、親の独立表は `parent-closure-measured.md`。
分類は **(L)** live 照合 / **(P)** 永続記録 / **(G)** golden・pin / **(N)** namespace。

要点だけを再掲する (詳細は上記逐語)。

- **最初の実破断点** = `s8b_floor_contract.py:139-151` (L)。
- **旧 bytes 側** = `floor_protocol.json` / `selector-runs/journal.jsonl` /
  `selector_predictions.json` / `silo_ladder_rung1.json` / raw-bundle receipt (P)。
  **いずれも貼り替えない。**
- **golden 側** = `test_frozen_artifacts.py` (23 件 + 独立 exact key-set)、
  `test_env_contract.py` の literal 群、`test_s8b_protocol_builder.py:108-118` の
  `261cec…` pin (G)。
- **namespace 側** = `buildcache.py:650` の `contracts/<contract_sha256>/` (N)。
  世代交代で cache miss になるのは正しい挙動であり破綻ではない。
- **識別子の脱落 (段 2 の重大発見 ID 07)** = campaign ID が env / contract を含まないため、
  同じ `pegasus` tag の新旧世代が**同じ WAL / layout を共有する** (`ident.py` / `loop.py:131-145`)。
- **迂回経路 (レンズ A-3、親が実測確認)** = `run_campaign(..., env_contract=None)` は
  Pegasus site 検査より前に `return None` する (`loop.py:66-67`、既定値は `:106`)。
  contract-bound 性が optional 引数の有無で決まっている。
- **wrapper の取り残し (レンズ B-8、親が実測確認)** =
  `tools/pegasus/floor_campaign.sh:880` が旧 protocol path を固定している。
- **閉包から脱落していた面** = launch certificate (`s8b_launch_cert.py`、consumer は
  `s8b_ratified_freeze.py:2893-2913`)、T-126 の control / series / event / receipt
  (`orchestrator/qualification/` 配下 6 面)。

### 明示的に閉包へ入れないもの (同名の別概念、D75)

- `s8c_preregistration` の `evidence_contract_sha256` — prereg 文書の evidence contract の
  semantic hash であり env contract ではない (`s8c_preregistration.py:330-337`)。
- T-419 probe の `env_contract_sha256` — **`orchestrator/campaign/env_contract.py` の
  source file bytes の sha256** である (`tools/pegasus/probes/t419_probe_causality.py:3532-3534`)。
  親が `sha256sum` で `88d557ba…` の一致を実測した。`expected_` 対がなく比較もされない。
  移行後は「古いが無害な provenance」になる。
- T-126 の `protocol_sha256` — qualification control protocol であり s8b floor protocol ではない。

---

## 3. 既存の世代交代機構 — 新発明ではなく既存型の適用 (親の新事実)

この repo は holdout freeze 族に対して**世代機構を既に完全実装している**
(`orchestrator/campaign/s8b_ratified_freeze.py`)。

- `generation_number` / `supersedes_sha256` / `parent_active_sha256` の単調な pointer 連鎖
  (`:1271-1278` が連番の厳密一致を検査)
- **承認 record を世代文書から分離** — `_FORBIDDEN_GENERATION_KEYS` (`:108-114`) が
  `approved_by` 等の混入を拒否し、承認は別 schema (`_APPROVAL_KEYS`, `:115`) を持つ
- 失効 tombstone と pointer cancel の exact schema (`:120-122`)
- **F5 transition table** (`:128-142`) — `_TRANSITION_V1_TO_G1` / `_TRANSITION_GN_TO_GN1` が
  **「変わってよい JSON Pointer」を完全列挙**し、**列挙外の pointer は前世代と厳密一致**を要求する
- `_TRANSITION_GN_TO_GN1` は `/env_tag` の変更を明示的に拒否し、理由を
  「**環境が変わる = 別実験**」と書いている

**これが敵対レンズ B の must-fix 2 件をそのまま塞ぐ。**

1. **B-1 (successor が attestation を無効化できる)**: env contract の世代交代にも同型の
   transition table を置き、可変 pointer を `/calibration_ref/path` と
   `/calibration_ref/sha256` **だけ**に限定すれば、`attestation_mode` / `isolation_policy` /
   `clocks_per_us` / `numactl` / `env_tag` は列挙外 = 厳密一致となり、攻撃列が構造的に成立しない。
2. **B-4 (blind seal の再発行 / 分割表の書き換え)**: protocol の 18 key のうち
   `/contract_sha256` **だけ**を可変列挙にすれば、「新 protocol の `contract_sha256` を旧値へ
   戻した canonical bytes が旧 bytes と完全一致」というレンズ B の要求と等価になる。
   同時に、親仮説 H1 の弱点 (可変 partition を設計者があとから動かせる) も消える —
   分割は key 集合ではなく **pointer の exact 列挙**であり、列挙自体が凍結対象になるからである。

**副次的に、案 C (新 env_tag `pegasus-g2`) への反対材料が既存コードの中にある。**
同じ repo の世代機構が `/env_tag` の変更を「別実験」として拒否している。

---

## 4. 推奨機構 — 案 A′

段 2 の推奨 (案 A = env_tag ごとの immutable 世代列 + hash 逆引き + current/history API 分離、
`s2-plan.md:112-216`) に、§3 の transition table 制約と敵対レンズの must-fix を組み込んだ合成案。
レンズ B が求めた「A と H1 の併用」(`s3-lensB.md:121`) もここに含まれる。

### 4.1 構成要素

1. **immutable 世代列と hash 逆引き** — `resolve_by_contract_sha256()` で旧 contract を
   一意に解決できるようにする。骨格は `s2-plan.md:116-146`。
2. **transition predicate (§3)** — successor は可変 pointer 列挙外を前世代と厳密一致。
   可変列挙は `/calibration_ref/path` と `/calibration_ref/sha256` のみ。
3. **型による権限分離 (B-2)** — `HistoricalContract` と `CurrentContract` を別型にし、
   receipt / build / launch / certified 選択の issuer は後者だけを受け取る。
   `allow_historical=True` のような真偽フラグは設けない。命名規約に頼らない。
4. **単一権威 (B-3)** — `REGISTRY` を独立データにせず、**検証済み activation record から導出**する。
   `require_current()` 自体が完全な bundle / closure capability を要求する。
5. **activation receipt (A-2)** — `current generation` と `active generation` を分離する。
   content-addressed な activation receipt を新設し、floor / oracle / P3 / T-126 / selector /
   silo promotion の**全入口が最初の書込み前に同じ migration epoch と bundle SHA を検査**する。
   段 4 の閉包検査が成功したときだけ receipt を発行する。g1 への自動 fallback は設けない。
6. **campaign identity への contract hash 束縛 (ID 07 / A-3)** — campaign preimage に
   `environment_contract_sha256` を含め、g1 / g2 が別 WAL / layout になるようにする。
   併せて contract-bound 性を optional 引数の有無で決めるのをやめる
   (`loop.py:66-67` の `None` 迂回を塞ぐ)。
7. **versioned predicate dispatch (B-5)** — `(schema, formula, predicate_version)` による
   閉じた verifier dispatch と retention。未知版・実装削除・source 消失は明示 `unresolved` とし、
   current verifier への fallback を禁止する。
8. **wrapper の結線 (B-8)** — `floor_campaign.sh` が検証済み activation bundle を一度解決し、
   protocol path / hash / bundle hash を driver と job-result の双方へ渡す。
   自由な path 引数と自動 fallback は禁止。
9. **恒真化を塞ぐ独立検査 (B-6)** — bundle の自己申告集合だけを正本にしない。
   bundle 外の独立 required-role / keyset、非空 cardinality、literal trust root を置く。
   先例は `test_frozen_artifacts.py:87-114` の独立 exact key-set。

### 4.2 旧 artifact の扱い (禁止事項)

- **旧凍結 bytes を貼り替えない。** 旧 evidence の binding を新 SHA へ書き換えない
  (その試行が新較正を使ったという虚偽の履歴になる)。
- 旧 artifact は自己完結した歴史資料として保持し、**current eligibility を外す**。
- 旧 calibration 本体、その source commit と git object、pre-oracle commit、
  legacy evidence bytes を **retention 対象**にする (レンズ A-6)。

---

## 5. 「解決不能」の定義 (三状態)

親 brief の (P3) 「現行コードで verify 可能なら十分」は**不足である** (レンズ B が反証)。
parse と内部 hash 一致だけを verify と呼べてしまうため、恒真な history verifier になる。
段 2 の三状態へ強化する (`s2-plan.md:285-322`)。

1. **`integrity_resolved`** — artifact の contract hash が一意な immutable contract へ解決し、
   calibration path が存在し bytes SHA・schema・cross-field が一致し、
   protocol / journal / receipt / manifest / raw bundle / source commit /
   **launch certificate** の全参照が解決する。
2. **`historically_verified`** — 上に加え、artifact が宣言する **versioned predicate** で
   proof chain を最後まで**再計算**できる。結果は pass / fail のどちらでもよい
   (旧較正が新 policy で失格でも「historical integrity pass / current policy fail」と
   報告できれば解決不能ではない)。
3. **`current_eligible`** — 上に加え、contract hash が `lookup(env_tag)` と一致し、
   現行 attestation / self-comparison / approval / certified gate をすべて通る。

**「解決不能」とは**: hash から contract を一意に得られない / calibration bytes・git blob・
参照 artifact が不在または hash mismatch / versioned verifier を実行できない /
proof-chain の辺を再計算できず記録値どうしの比較に堕する、のいずれかである。

現在の破断点一覧は `s2-plan.md:309-321`。

---

## 6. 移行手順と、その entry condition

段 2 の 6 段手順が起点 (`s2-plan.md:270-283`)。敵対レンズが 3 点を追加した。

### 6.1 U-2 の entry condition (レンズ B-10)

較正の再取得を開始してよいのは、次が**すべて**成立したときだけとする。

- [T-419] R-1 (方式 α) の probe 実装と、計算ノードでの因果実測が完了している
- 正規 CLI の accepted publish receipt がある (`orchestrator/calibrator/cli.py:608-654`)
- 独立な self-comparison が通る
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の既知例外集合が空になる

**直接追加した calibration は、hash が正しくても activation 不能とする。**
D155 決定 (3) が記録したとおり、git 直接追加・attempt からの複製・旧 worktree からの持ち込み・
pin だけの更新は loader も hook も拒否しないためである。

### 6.2 staging の循環依存 (レンズ A-1) — **ユーザー裁定へ返す**

段 2 は g2 を `pending` にしたまま g2 floor protocol を生成する手順を書いたが、
builder は `lookup(env_tag)` = current = g1 から contract hash を取る
(`s8b_floor_campaign.py:365-440`)。**そのままでは g2 closure を生成できない。**
selector seal も同じ builder で再導出するため committed bytes と一致しない
(`s8b_prediction_runner.py:1538-1570`)。

設計上の解は「`pending` を一般 `lookup()` に露出させず、protocol / selector 構築専用の
**型付き staging resolver** を分離する」である。ただしこれを挟むと
**[T-452] U-8 の「campaign を閉じたまま U-2 と pin closure を連続 2 commit」制約と
両立しない可能性がある。** これは承認済み裁定の前提を覆す未見の新事実であり、
親は読み替えず**ユーザー再裁定へ返す** (択一 4)。

### 6.3 巻き戻しの境界 (レンズ B-11)

- **不可逆リスク境界** = pin closure commit。
- **意味的不可逆点** = 最初の g2 receipt / certified 台帳の発行。
- 世代固有 staging root と create-only の abort tombstone を設け、中断した seal は
  削除・再利用せず abandoned として保持する。
- activation 後に g2 receipt または certified result が 1 件でも出たら、
  rollback ではなく **revocation + forward fix** とする。

---

## 7. U-2 実装 wave が事前登録すべき変異候補

**本 wave は実装差分を持たないため、変異 matrix と受入全走は射程外である** (`DW-S04`)。
以下は設計内容としての候補列挙であり、本 wave での変異走行ではない。
U-2 wave が `DW-M01` に従って単一理由性を確認したうえで登録する。

段 2 の 8 件 (`s2-plan.md:208-216`) に加え、敵対レンズが要求した 6 件:

- `g2 = replace(g1, attestation_mode="none", …)` が activation 前に必ず赤になる (B-1)
- production の `require_current` を history resolver へ置換すると赤になる (B-2)
- pointer だけを g2 に変えた状態で、実 `run_campaign` が最初の receipt より前に拒否する (B-3)
- `APPROVED_MASTER_SEED += "-changed"` が必ず赤になる (B-4)
- v2 dispatch entry を削除すると g1 full proof replay が赤になる (B-5)
- `selector_files=[]` / `records=[]` / `GENERATIONS["pegasus"]=(g2,)` が各 1 行で独立に赤になる (B-6)
- rejected attempt の bytes を世代へ直接登録すると activation が必ず赤になる (B-10)

---

## 8. 本設計が保証しない範囲

段 2 の列挙 (`s2-plan.md:329-340`) を採用する。要点:

- g1 evidence を g2 の current eligibility へ戻すこと。
- 旧較正が新 policy authority や新 self-comparison を満たすこと。
- 歴史的に「certified」と記録された結論の科学的妥当性の再承認。
- scheduler・物理ノード・当時の負荷など、消失した外部環境の再現。
- g1 build cache の g2 再利用 (g2 の cache miss は正しい挙動)。
- T-419 probe の manifest / result を certified proof chain へ昇格すること。
- 旧 calibration file や git object が将来削除された場合の復元
  (retention を破れば明示的に `unresolved` となる)。
- **producer provenance の束縛** (content-addressed path の強制、publish receipt と
  policy source の束縛)。これは [T-452] §7 が独立課題として切り出した別の防壁である。
- **8c / P3 prereg 下流**の contract 世代束縛 (択一 5)。本 wave では実装済みと数えない。
- 旧凍結 bytes の更新、attestation / self-comparison / equality gate の緩和、
  mixed-generation fallback は**一切保証も許可もしない**。

---

## 9. ユーザー裁定へ返す設計択一

| # | 択一 | 親の推奨 | 根拠 |
|---:|---|---|---|
| 1 | **世代機構**: 案 A′ / 案 B (artifact 側 generation tag) / 案 C (新 env_tag `pegasus-g2`) / 案 D (移行せず旧証拠を失格) | **A′** | B は自己申告世代を trust boundary に増やし、旧 artifact 対応には結局 hash 逆引きが要る (`s2-plan.md:237-241`)。C は同じ物理環境の較正更新ごとに env tag が増殖し、既存機構が `/env_tag` 変更を「別実験」として拒否している規範と衝突する。D は §5 の `integrity_resolved` を満たせず非適合 (negative control として残す) |
| 2 | **verify の定義**: 弱い定義 (parse + 内部整合) / 三状態の強い定義 | **強い定義** | 弱い定義は恒真な history verifier を許す (レンズ B-5) |
| 3 | **campaign identity へ `environment_contract_sha256` を必須化** (D13 改訂) | **改訂する** | 現状維持は同じ `pegasus` tag の g1 / g2 が同じ WAL / layout を共有する穴を残す (段 2 ID 07) |
| 4 | **[T-452] U-8 の「連続 2 commit」制約との衝突** — staging resolver を挟むと 2 commit に収まらない可能性がある | **裁定を求める** | 承認済み裁定の前提を覆す未見の新事実であり、親は読み替えない (§6.2) |
| 5 | **8c / P3 prereg 下流の更新時期** — P3 再開時に prereg contract を `CurrentContract` / bundle hash / campaign identity / trial-registry acceptance まで更新するか | **P3 再開時に更新** | 現状は D163 により producer 未接続・P3 FAIL。未処置のまま再開すると将来の試行台帳と certified acceptance が contract 世代を束縛しない (レンズ B-9) |

---

## 10. 成果物影響 (`DW-G05`)

この設計を確定しないまま U-2 へ進むと、較正再取得は §1 の二択に突き当たる —
凍結 seal の連鎖を壊すか、較正を登録できず campaign が開けないか。
どちらでも **certified 選択の再開そのものが不能**になり、Phase 3 の主成果物
(certified 選択結果・proof chain 付き材料レポート・再現可能な試行台帳) が確定しない。

個々の所見を放置した場合の影響は各逐語の「成果物影響」行を正本とする。
特に重いものを 3 つ挙げる。

- **B-1 を放置**: certified 選択が attestation なしの run を受理し、
  材料レポートと試行台帳には一見正しい g2 hash だけが残る。
- **ID 07 / A-3 を放置**: 試行台帳が同じ campaign ID / WAL へ g1 と g2 の値を混在させる。
- **B-4 を放置**: certified 選択の予測と採否が較正とは無関係に変わり、
  selector journal が別実験を同じ移行として記録する。

---

## 11. この wave が触っていないもの

- コード・テスト・凍結成果物・pin・registry — **一切変更していない**。
- 較正の再取得、凍結 bytes の更新、pin の更新 (D155 決定 (5) のとおり)。
- campaign / certified 選択の再開。
- `docs/freeze-permanent-design.md` の `FROZEN_MANIFEST` 記述だけは、
  移行監査が閉包件数を誤るため本 wave で erratum を入れた (レンズ A-7、親が実測確認)。
