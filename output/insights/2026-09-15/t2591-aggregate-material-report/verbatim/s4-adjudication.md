# [T-2591] 段 4 裁定 — 集約成果物が材料レポートまで届く正例

基準 main = `0600887d9` (wave 開始後に進んでいないことを段 4 直前に実測)。

## 1. 所見の裁定

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A1 | sol-2 / luna-3 | `report["analysis"]["floor_argument"]` は authority からの**投影**であって、実 evaluator へ渡した引数の観測ではない。これを assert しても「最大床値で解析した」は言えない | real | **採用 (scope 内)** |
| A2 | sol-3 | assert が `document.json_value` (dict) 止まりだと「JSON 成果物 bytes へ届く」を保証しない | real | **採用** |
| A3 | sol-3 | 3 入力が rr5 / rr50 / rr95 であることは helper 任せで、正例側で固定されていない | real | **採用** |
| A4 | sol-9 / luna-4 | markdown 非保証要求の撤回は正しい。ただし markdown の床値・artifact path・hash は**集約 artifact のもの**でなければならない | real | **採用** |
| A5 | sol-10 / luna-5 | `write_material_report` は `build_material_report_document` を呼ばず別に組む。document 到達から publish を推論できない。report は `evidence-only` / `not_in_effect` であり certified ではない | real | **採用 (主張範囲の限定)** |
| A6 | luna 照合表 | 段 2 の `D:53` / `D:73` は誤り。正しくは `IT:53` → `IT:73` → `D:335` → `D:370` | real | **採用 (訂正)** |
| A7 | luna 登録-2 | `nodeid_count` の更新も要る。かつ「登録漏れなら必ず赤」は誤りで、台帳全体が空扱いになり shard 推定が静かに変わる | real | **採用** |
| A8 | luna 親反証-2 | 「`GENERATOR_IDENTITY` が path だから pin は壊れない」の一般化は誤り。`I:1315` 以降は成果物 bytes の hash を検査する | real | **採用 (親の記述を限定)** |
| A9 | luna 親反証-3 | 事前登録がその 5 member pin で縛るのは解析 source 閉包であり材料レポート bytes ではない。一方 §5.1 追補 (d)(e) は集約成果物の path/hash を要求し、floor 欄は未記入 | real | **採用 (親の記述を訂正)** |
| A10 | sol-8 | 親が brief に書いた「許可 monkeypatch は 3 つだけ」は、指定 fixture 内部が既に 3 つ以上を patch している事実と矛盾する | real | **採用 (制約を書き直す)** |
| A11 | sol-5/6 + luna-scope-1 | 既存 helper の Git seam (`subprocess.run` 差替え) は、集約 → レポートの結線を置換しない環境 seam である。外しても増えるのは Git による入力凍結・履歴束縛の検査であって本 wave の機構ではない | real | **採用。ただし対応は下記 2 のとおり** |
| A12 | luna 親反証-1 | 「所有が素集合に割れないから実装子 1 本」は根拠不足。分割可能だが調整費用を避ける判断である | real | **採用 (記述の訂正のみ、方針は不変)** |
| A13 | sol-1 | §3 の assert の多くは集約固有でない。ただし「集約固有でない = 無価値」ではない | real | **採用 (証拠の数え方を限定)** |
| B1 | sol-7 | 「stub を残すと新正例が恒真になる」は成立しない。既存 m9 の緑が新 node の assert を成立させる経路は無い | refuted (親 P1-a の懸念が否定された) | 親 P1-a を維持 |
| B2 | 段 2 §1 + luna-scope-1 | Git seam を条件化し一時 fixture に実 Git repository を作る | real だが **不採用 (scope 外)** | 下記 2 |

## 2. 中心の裁定 — Git seam は条件化せず、既存 helper をそのまま再利用する

段 2 は「親 brief が許可した monkeypatch 3 種に収めるため、`IT:53 _synthetic_source` に
keyword 引数を足して Git seam を条件化し、一時 fixture に実 Git repository を作る」と提案した。
**採らない。** 理由:

1. **親の制約側が誤っていた (A10)。** 「3 つだけ」という数え方は、指定した
   `immutable_publication` fixture が既に admission helper・clone helper・controller invoke を
   patch している事実と矛盾する。数で縛るのが誤りであり、コードを曲げて数に合わせるのは本末転倒である。
2. **実 Git 化は本 wave の機構の識別力を増やさない (A11)。** sol の逐語:
   「Git patch は最大値計算、3 spec 閉包、source 再構成、report 投影を置換しない。
   外して増える検査は Git による入力の凍結・履歴 binding であり、集約 → report の結線そのものではない」。
3. **依頼が scope 外と明示している。** 「本題の実装だけ。仮想リスク向けの gate・検査・台帳・
   一般化の追加は scope 外」。
4. **編集面の衝突を避ける。** `test_p3_b4_floor_artifact_issuer.py` は、同時稼働している 5 本の
   floor 系 wave と最も衝突しやすい共有 helper である。

**したがって seam の許可条件を数でなく位置で定義し直す。**

- **禁止 (機構上の seam):** 集約発行 `issue_aggregate_authoritative_floor`、
  解決 `resolve_preregistered_authoritative_floor`、
  公開 builder `build_material_report_document`、およびその内部の投影・検査関数。
  これらを差し替えた正例は無効とする。
- **許可 (環境 seam、既存 test 群の定型):** calibration loader、Git (`subprocess.run`)、
  `os.fsync`、`R._REPOSITORY_ROOT`、`immutable_publication` fixture 内部の既存 patch。
- **許可 (観測 wrapper):** `R.evaluate_b4_artifacts` を**実物へ委譲する**記録 wrapper
  (既存 m9 が `T:871` で使う定型)。差し替えではなく観測である。A1 の穴はこれで埋める。

**この裁定が証明しないこと**を insight と worklog へ明記する:
3 本の source summary が実 Git に凍結された成果物であること、calibration が真正であること。
いずれも環境 seam のままである。

## 3. プラン v2 (実装子への確定指示)

### 編集面 (3 file、production 変更なし)

1. `orchestrator/tests/test_p3_b4_material_report.py` — 正例 1 本を追加
2. `orchestrator/tests/test_real_repo_serialization.py` —
   `_P3_B4_MATERIAL_REPORT_NODES_GOLDEN` へ新 canonical node を 1 件追加
3. `orchestrator/tests/acceptance_duration_ledger.json` — 新 node の所要 1 件 + `nodeid_count` を +1

`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` は**編集しない** (import して再利用するだけ)。
`orchestrator/campaign/**` は**編集しない**。

### 正例の形

関数名 `test_aggregate_authoritative_floor_reaches_public_material_report`、
置き場所は `T:958` の直前 (既存 m9 の後)。パラメータ化しない。

1. `immutable_publication` fixture の実 publication root を使う
   (実 prerun publication + 実 raw analysis)。
2. `tmp_path` 配下の authority repo で
   **実 `issuer.issue_aggregate_authoritative_floor`** を呼び、3 入力の集約 artifact を発行する。
   入力は `test_p3_b4_floor_artifact_issuer._aggregate_public_sources` を **無改造で** import して使う。
3. 発行された artifact の実 bytes を読み、authority repo の `docs/` に §5 pin 行を書く。
4. **実 `issuer.resolve_preregistered_authoritative_floor`** で解決し、発行結果と一致を確認する。
5. `R._REPOSITORY_ROOT` を authority repo へ向け、
   **実 `R.build_material_report_document(publication_root)`** を直接呼ぶ。
   `T:248 _inputs` / `T:257 _document` の cache は**使わない**。
6. `R.evaluate_b4_artifacts` に**実物へ委譲する記録 wrapper** を掛け、実引数を観測する (A1)。

### assert (最低限これを満たすこと)

- **(a) 実引数の観測 (A1):** 記録 wrapper が捉えた `floor` 引数がちょうど 1 回、
  型が `Fraction`、値が 3 入力の最大と exact 一致。
- **(b) bytes 到達 (A2):** `document.json_bytes` を decode した値で floor 節・
  `certification_scope.not_guaranteed`・`provenance.report_non_guarantees` を確認する。
  `json_value` だけで済ませない。
- **(c) 3 系列の固定 (A3):** 3 pin が指す spec の
  `cells[0].perf_config.workload.ycsb_rratio` が literal `"5"` / `"50"` / `"95"` であること。
  床値が相異なり、**最大が先頭でも末尾でもない**こと (入力順で 第0 < 第2 < 第1)。
- **(d) 集約固有の投影:** `report["floor"]["source"]["schema_version"]` が literal
  `"p3-b4-authoritative-floor/v2"`。`artifact_path` / `artifact_sha256` が
  **発行された集約 artifact の実 path と実 bytes の sha256** と一致。
  `report["floor"]["value"]` が 3 入力の最大の exact ratio。
- **(e) 非保証の完全転記:** `not_guaranteed` と `report_non_guarantees` に、
  `issuer.NON_GUARANTEES` → 各 source の `proof_limitations["items"]` (3 件ぶん、入力順) →
  `issuer.AGGREGATE_NON_GUARANTEES` が**順序どおり**現れる。
  **非最大 source (第0・第2) 固有の項目も含まれる**ことを名指しで確認する。
- **(f) markdown (A4):** markdown に集約 artifact の実 path・実 sha256・最大 ratio が現れる。
  **非保証の markdown 描画は要求しない** (v1/v2 共通で存在しない既存性質)。
- **期待値は発行結果から逆算しない。** 入力 summary / spec の現物から独立に組み立てる。

### 禁止 (実装子への明示)

- 既存テストの期待値・golden (`_ABSENT_LEGACY_*`、m9 の 4 状態、`_write_floor_preregistration`) を変えない。
- `orchestrator/campaign/**` と `test_p3_b4_floor_artifact_issuer.py` を編集しない。
- 機構上の seam (issuer / resolver / builder) を差し替えない。
- gate・検査・台帳・一般化を新設しない。
- xfail・skip・assert 削除で緑にしない。

## 4. 変異事前登録 (DW-M01 / DW-M08)

本 wave は **production 差分ゼロのテスト強化 wave** である。よって DW-M08 に従い
**新旧両走**を登録する。旧走は「新 node を `--deselect` した同一 spec」とし、
これが変更前 HEAD の test 集合と等価であることを事前に宣言する
(本 wave の test 集合の差分は新 node 1 件と 2 台帳の登録のみであり、
台帳登録は test の受理集合を変えない)。

変異対象はすべて `orchestrator/campaign/p3_b4_material_report.py` (production、本 wave 無改変)。
各変異は「同じ入力を拒否する層が前後にも内側にも無い」ことを実装後に確認する (DW-M01 / F820)。
期待 node は完全集合で登録し、完全一致だけを KILLED とする (DW-M08 / F33)。

| ID | 位置 | 変異 | 新走 期待 | 旧走 期待 | 何を守るか |
|---|---|---|---|---|---|
| M1 | `_authoritative_floor_source` (R:956–960) | `authoritative_floor.schema_version` を literal `B4_FLOOR_ARTIFACT_SCHEMA_VERSION` (v1) へ | KILLED | SURVIVED | 集約 (v2) の schema がレポートへ届くこと |
| M2 | `_apply_authoritative_floor_projection` (R:990–993) | `authoritative_floor.non_guarantees` を `floor_issuer.NON_GUARANTEES` (基底 3 件) へ | KILLED | SURVIVED | 各 source の限界と集約非保証が落ちないこと |
| M3 | `_load_and_evaluate` (R:267–271) | evaluator へ渡す `floor` を `Fraction(0, 1)` へ | KILLED | SURVIVED | 解析が実際に最大床値を受けること (A1) |
| M4 | `_apply_authoritative_floor_projection` (R:973–976) | `ratio` を literal `[0, 1]` へ | KILLED | SURVIVED | レポートの床値が集約値であること |
| M5 | `_render_markdown_with_authoritative_floor` (R:1214–1219) | `authoritative_floor.artifact_path` を literal `"artifacts/b4-floor-zero-boundary.json"` へ | KILLED | SURVIVED | markdown が集約 artifact を指すこと |

5 件はいずれも **m9 の present ケースが床値 `[0,1]` / schema v1 / 基底非保証 / 固定 path の
stub を使っている**ため旧走では発火しない設計である。旧走で KILLED が出たら、
その変異は本正例の検出力の証拠から外し、erratum に残す (DW-M02)。

## 5. 親の記述の訂正 (段 7 へ持ち越す)

- 「材料レポートは certification 成果物」→ 誤り。現物は `certifying=False` /
  `closed_world=False` / `evidence-only` / `preregistration_section_5 = not_in_effect`。
  正しくは「evidence-only の材料レポート」。
- 「集約成果物がレポートへ届くことは一度も実測されていない」→ 静的調査では過去全体を否定できない。
  正しくは「現行 test 集合に集約 artifact を builder へ通す node は存在しない (AST で 31 対 31 を照合)」。
- 「`GENERATOR_IDENTITY` が path だから pin は壊れない」→ 限定する。
  「本 wave は生成器も既存成果物も変更しないので、bytes hash 検査に触れない」。
- 「事前登録は生成器の出力 bytes を pin していない」→ 対象を分ける。
  「材料レポート JSON/Markdown の固定 hash は無い。floor 欄は未記入で、
  §5.1 追補は集約成果物の path/hash を要求する」。
- 段 2 の `D:53` / `D:73` → `IT:53` / `IT:73` / `D:335` / `D:370`。
- 「所有が素集合に割れない」→ 「割れるが、正例 1 本のため調整費用を避けて実装子 1 本」。
