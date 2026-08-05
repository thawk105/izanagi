# [T-478] 段 4 裁定

段 3 の敵対 2 レンズは**両方 NO-GO**、所見は計 19 件 (レンズ A 7 件 / レンズ B 12 件)。
親が実測で裏取りしたうえで裁定する。

## 総括

- **real 18 / 部分反証 1 / refuted 0。**
- 採用 16 / scope 外で裁定へ返却 2 (A-1 の U-8 衝突、B-9 の 8c・P3 下流) /
  本 wave で docs 訂正 1 (A-7)。
- **親の新事実 1 件** — この repo には既に世代交代機構の実装済み前例がある (下記 §親 N3)。
  これが レンズ B の must-fix 2 件 (B-1 / B-4) が要求した防壁の実体である。
- **本 wave は実装しない** (段 5・6 を飛ばす)。実装差分がないため変異 matrix と受入全走は射程外。
  ただし docs 訂正 1 件があるため `check_docs.py` と関連テストは走らせる。

## 親の実測による裏取り (子を鵜呑みにしない)

| # | 主張 | 親の実測 | 判定 |
|---|---|---|---|
| P-1 | `run_campaign(..., env_contract=None)` が current contract 検査を迂回する (レンズ A-3) | `loop.py:66-67` が `env_contract is None` で **Pegasus site 検査より前に `return None`**。既定値も `env_contract=None` (`loop.py:106`) | **real** |
| P-2 | production の `lookup` 呼び出し数 | 直接呼び 19 (うち `s8b_floor_contract.py:150` は message 文字列で非 call → 除外して 18)、alias 経由 2 (`pegasus_floor_scoping.py:75`、`p3_s4_loop_trigger_gating.py:324`)、T-126 2、T-419 probe 1 → **合計 21** | 親 brief の 20 は誤り。段 2 の 18 は campaign 配下限定。レンズ A の **21 が正しい**。レンズ B の「全体 18」は誤り |
| P-3 | wrapper が旧 protocol path を固定 (レンズ B-8) | `tools/pegasus/floor_campaign.sh:880` に `PROTOCOL_PATH="output/s8b-freeze/floor_protocol.json"`、`:896` で driver へ渡す | **real** |
| P-4 | launch certificate が閉包から脱落 (レンズ A-5) | `orchestrator/campaign/s8b_launch_cert.py` は実在 (7674 bytes)、consumer は `s8b_ratified_freeze.py:2893-2913` | **real** |
| P-5 | `docs/freeze-permanent-design.md` の `FROZEN_MANIFEST` 記述 (レンズ A-7) | 同文書は「8 件 literal pin」「件数が合えば差替えが通る」と書くが、実装は **23 件** かつ **独立 exact key-set 検査あり** (`test_frozen_artifacts.py:139-153`、`:87-114`) | **real (二重に陳腐化)** |

## 親 N3 — 新事実: 世代交代機構の実装済み前例がある

`orchestrator/campaign/s8b_ratified_freeze.py` は holdout freeze 族に対して、
**既に世代機構を完全実装している**。

- `generation_number` / `supersedes_sha256` / `parent_active_sha256` による単調な pointer 連鎖
  (`:1271-1278` が連番の厳密一致を検査)
- **承認 record を世代文書から分離** — `_FORBIDDEN_GENERATION_KEYS` (`:108-114`) が
  `approved_by` 等の混入を拒否し、`_APPROVAL_KEYS` (`:115`) が別 schema を持つ
- 失効 tombstone と pointer cancel の exact schema (`:120-122`)
- **F5 transition table** (`:128-142`) — `_TRANSITION_V1_TO_G1` / `_TRANSITION_GN_TO_GN1` が
  **「変わってよい JSON Pointer」を完全列挙**し、**列挙外の pointer は前世代と厳密一致**を要求する
- `_TRANSITION_GN_TO_GN1` は `/env_tag` の変更を明示的に拒否し、理由を
  「**環境が変わる = 別実験**」と書いている

### これが裁定に効く 3 点

1. **レンズ B-1 (successor が attestation を無効化できる) の解は新発明でなく既存型の適用**である。
   env contract の世代交代にも同型の transition table を置き、
   `/calibration_ref/path` と `/calibration_ref/sha256` **だけ**を可変列挙にすれば、
   `attestation_mode` / `isolation_policy` / `clocks_per_us` / `numactl` / `env_tag` は
   列挙外 = 厳密一致となり、レンズ B-1 の攻撃列は構造的に成立しなくなる。
2. **レンズ B-4 (blind seal 再発行) の解も同型**である。protocol の 18 key のうち
   `/contract_sha256` だけを可変列挙にすれば、「新 protocol の `contract_sha256` を旧値へ戻した
   canonical bytes が旧 bytes と完全一致」というレンズ B の要求と等価になり、
   かつ **可変 partition を設計者が動かせる** という H1 の弱点 (レンズ B-4 後半) も消える —
   分割は key 集合でなく **pointer の exact 列挙**であり、列挙自体が凍結対象になるからである。
3. **案 C (新 env_tag `pegasus-g2`) への反対材料が既存コードの中にある。**
   同じ repo の世代機構が `/env_tag` 変更を「別実験」として拒否している。
   較正更新のたびに env_tag を増やす案はこの既存規範と衝突する。

**したがって推奨は「案 A の hash 逆引き + current/history 型分離」に、
既存 F5 transition table 型の successor 制約を必須構成要素として組み込んだ合成案**とする。
以後これを **案 A′** と呼ぶ。レンズ B が求めた「A と H1 の併用」も、A′ に含まれる。

## 所見別の裁定

### レンズ A

| # | 内容 | 判定 | 裁定 |
|---|---|---|---|
| A-1 | `pending` 世代から g2 成果物を生成できない (builder が `lookup()` = g1 を引く) | real | **採用 + 一部を裁定へ返却**。設計へ「staging resolver を型付きで分離し、`pending` を一般 `lookup()` に露出させない」を入れる。ただし **U-8 の「連続 2 commit」制約と両立しない可能性**は承認済み裁定の前提を覆す新事実であり、親が読み替えず**ユーザー再裁定へ返す** |
| A-2 | activation / bundle hash が実在する gate 入力になっていない | real | **採用**。`current generation` と `active generation` を分離し、content-addressed な activation receipt を新設。消費する入口を file:line で全列挙する (floor / oracle / P3 / T-126 / selector / silo promotion) |
| A-3 | `env_contract=None` で contract-bound 判定を迂回できる | real (P-1 で親が実測) | **採用**。contract-bound 性を optional 引数の有無で決めない。Pegasus 実測では内部解決で必須化し、hash を layout 生成前に preimage へ入れる |
| A-4 | T-126 の lookup と試行 identity が閉包から脱落 (+ 総数 21) | real (P-2) | **採用**。閉包へ T-126 6 面を追加。総数は 21 で確定 |
| A-5 | launch certificate が proof chain 列挙から脱落 | real (P-4) | **採用**。closure へ certificate の validator (L)(G) と bytes (P) を追加 |
| A-6 | selector 閉包を (N) だけに分類しており source / pre-oracle 実体を落とす | real | **採用**。bundle exact-set に 5 source role・`pre_oracle_head`・parser/protocol blob を明記し、history API は current-worktree verifier でなく commit blob 経路を使う |
| A-7 | `docs/freeze-permanent-design.md` の `FROZEN_MANIFEST` 記述が陳腐化 | real (P-5) | **採用 + 本 wave で訂正**。docs 訂正 1 件のみ実施 (増設でなく erratum)。移行監査が閉包件数を誤るため放置しない |

### レンズ B

| # | 内容 | 判定 | 裁定 |
|---|---|---|---|
| B-1 | successor contract が attestation 無効化まで許す | real | **採用**。親 N3 の transition table 型で解く (可変 pointer は `/calibration_ref/*` のみ) |
| B-2 | history resolver の「検証専用」が命名規約でしかない | real | **採用**。`HistoricalContract` / `CurrentContract` の型分離。issuer は後者だけを受ける |
| B-3 | `GENERATIONS` / `REGISTRY` / bundle activation が三重権威 | real | **採用**。`REGISTRY` を独立データにせず検証済み activation record から導出する |
| B-4 | 案 A は blind seal を再発行し、H1 は分割表を書き換えられる | real (**最重要**) | **採用**。親 N3 の pointer exact 列挙で両方を同時に閉じる。`APPROVED_MASTER_SEED` 等の設計値は列挙外 = 厳密一致 |
| B-5 | `historically_verified` を将来も実行できる機構がない | real | **採用**。`(schema, formula, predicate_version)` の閉じた verifier dispatch と retention を設計に入れる。未知版・消失は明示 `unresolved`、current verifier への fallback 禁止 |
| B-6 | closure 検査に空集合・自己申告の恒真化穴 | real | **採用**。bundle 外の独立 required-role / keyset、非空 cardinality、literal trust root を要求 (先例 = `test_frozen_artifacts.py:87-114` の独立 keyset) |
| B-7 | 案 B / C は別名の二重権威、案 D は非適合 | real | **採用 (提示形として)**。択一は引き続きユーザーへ返すが、B / C / D には敵対レンズの実測反論を併記する。D は negative control として残す |
| B-8 | 実投入 wrapper が新 namespace を読まない | real (P-3) | **採用**。wrapper が検証済み activation bundle を一度解決し、protocol path / hash / bundle hash を driver と job-result の双方へ渡す |
| B-9 | 8c / P3 prereg 下流が contract 世代を束縛しない | real | **scope 外 → 裁定パッケージへ返却**。本 wave では実装済みと数えない |
| B-10 | D155 の観測者効果 blocker が migration entry condition になっていない | real | **採用**。U-2 の entry condition に「R-1 probe 実装 + 因果実測 + CLI accepted publish receipt + 独立 self-comparison + 既知例外集合が空」を全て入れる。直接追加した calibration は hash が正しくても activation 不能とする |
| B-11 | rollback が commit 内中断と activation 後を扱っていない | real | **採用**。世代固有 staging root、create-only abort tombstone、activation 後は rollback でなく revocation + forward fix |
| B-12 | 親の lookup call 数の数え方 | **部分反証** | 親 brief の 20 は**誤り (erratum)**。ただしレンズ B の「全体 18」も誤り。親実測で **21 が正**。両方に erratum を残す |

## brief の erratum

1. **#6 の「campaign 側の呼び出しは 20 箇所」は誤り。** 正しくは campaign 配下 18、
   production 全体 **21** (campaign 18 + T-126 2 + T-419 probe 1)。
2. **#8 の origin ledger は「field 面では実在するが current registry との end-to-end 配線は未実装」**
   と限定する (段 2 の指摘を採用)。
3. **(P3) の「verify 可能なまま」は不足。** parse と内部 hash 一致だけでは恒真な history verifier に
   なる。段 2 の三状態 (`integrity_resolved` / `historically_verified` / `current_eligible`) へ強化し、
   `historically_verified` は versioned predicate の実行可能性まで要求する。
4. **(P2) の H1 は単独では不採用。** 可変 partition を設計者が動かせる穴 (レンズ B-4 後半) があり、
   pointer の exact 列挙 (親 N3) へ置き換える。

## 本 wave の scope 確定

- **実装しない。** 世代機構・activation receipt・型分離・wrapper 修正・T-126 版上げは
  すべて [T-419] U-2 の実装 wave が所有する。
- 本 wave の成果物は **設計 (裁定パッケージ) + docs 訂正 1 件**。
- 実装差分がないため **変異 matrix と受入全走は射程外** (`DW-S04`)。
  U-2 wave が事前登録すべき変異候補は設計文書に列挙する (本 wave の変異走行ではない)。
- docs 訂正があるため `check_docs.py` と関連テストは走らせる。

## ユーザー裁定へ返す択一 (段 9 報告に含める)

1. **世代機構**: 案 A′ (推奨) / 案 B / 案 C / 案 D (negative control)。
2. **verify の定義**: 弱い定義 (parse + 内部整合) か、三状態の強い定義か。推奨は強い定義。
3. **campaign identity への `environment_contract_sha256` 必須化** (D13 改訂)。推奨は改訂。
   現状維持は g1/g2 の WAL 混在穴を残す。
4. **U-8 の「連続 2 commit」制約との衝突** (A-1)。staging resolver を挟むと 2 commit に
   収まらない可能性がある。**承認済み裁定の前提を覆す新事実**のため親は読み替えず返す。
5. **8c / P3 prereg 下流の更新時期** (B-9)。P3 再開時に prereg contract を更新するか。
