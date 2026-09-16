# 段 1 brief — [T-2723] floor セル読取経路を §5 の admission 契約へ接続する

- 基準: local main 1042a1bc95057fa03117d504cfa2b0fafaae60d0 (worktree `.claude/worktrees/dev-wave-t2723-floor-cell-admission`、clean、submodule 3 段初期化済み、開始 gate fresh OK)
- 起票: worklog archive 1571 の [T-2723] (T-2464 の段 3/6 が real・scope 外として残した所見)

## 研究前進
B-4 reflux ablation の材料レポート (`p3_b4_material_report.py`) は事前登録 §5 の floor 行から権威 floor を読み、凍結評価器へ渡す。現行の読取 (`p3_b4_floor_artifact_issuer._floor_cell`) は文書全体を `|<label>|` の exact prefix で走査し、§5 見出し境界・固定表の形状・責任者行を見ない (F423 と同型: 文書全体の string search で「本物の箇所」を決める設計)。放置時の成果物影響 (DW-G05): §5 外 (§11 の測定計画例示・追補・fence 内) に同 prefix 行が 1 本置かれると材料レポート生成が `exact 1 件` で止まる (2 本目) か、§5 に行が無くてもそこから floor が採られる (1 本目)。責任者未指名の文書からも floor が受理され、floor 欄の出所が事前登録の発効条件 (D1812 (b)、D2079) と切れる。完了判定: 正例 (現行の実文書 → floor=None、材料レポート不変) と負例 2 型 (§5 外の同 prefix 行だけの文書 / 責任者欠落) が test で示され、変異 matrix で KILLED。

## scope (本題の読取経路だけ)
1. `orchestrator/campaign/p3_b4_admission_record.py`: `assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel` の本体から、(a) §5 境界 (`## 5.`〜`### 5.1`、fence / HTML comment 除外) + 固定表形状 + label 集合 + cell 正規化 (strip + NFKC + default-ignorable 拒否) の解析、(b) 1 cell の受理述語 (責任者行の D2079 1 形 + 一般 sentinel 規則) を helper へ切り出し、既存関数は helper を呼ぶだけにする。**受理集合・error signature (`_SECTION5_SOURCE_CELL_CONTRACT_FAILED`) は不変。**
2. `orchestrator/campaign/p3_b4_floor_artifact_issuer.py`: `_floor_cell` / `resolve_preregistered_authoritative_floor` を (a) 経由に変え、§5 固定表の floor 行 1 セルだけを読む。§5 外の同 prefix 行は文書の一部として無視。責任者行が (b) を通らなければ `B4FloorArtifactError` で拒否。sentinel → None、pin → 既存 `load_authoritative_floor` は不変。
3. tests: 既存 fixture (`test_p3_b4_floor_artifact_issuer._preregistration`、`test_p3_b4_material_report._write_floor_preregistration` / m7 / aggregate 正例) を §5 完全表へ更新 (admission test の `_section5_document` 型を再利用可)。新規: 正例 = 実 repo 文書 `docs/phase3-b4-reflux-ablation-preregistration.md` を読んで None; 負例 = (i) §5 外だけに有効 pin 行がある文書 (§5 は sentinel → None、§5 に floor 行が無い → 拒否)、(ii) 責任者欠落 (`実行責任者 = 未記入、開始時刻 = 未記入` / 行欠落) で有効 pin でも拒否。
4. insight README + worklog / decisions fragment。

scope 外: 他欄の sentinel 検査を floor 経路へ持ち込む (現行文書は floor 含む 6 欄が `未記入` で正例が落ちる)、新しい汎用 validator、事前登録文書の編集、admission 契約の受理集合変更、責任者への意味検証 (D2079 決定 2)。

## 親の provisional 裁定 (攻撃対象)
- (P1) 接続範囲 = 境界 + 形状 + label 集合 + cell 正規化 + 責任者行述語。他欄の値は見ない。
- (P2) floor セルの外周空白は admission と同じく strip し、` 未記入 ` は sentinel (現行は `preregistration_floor_grammar_error`)。pin grammar は strip 後の raw cell (NFKC 前) に `_FLOOR_PIN_RE.fullmatch`。NFKC 後の値は sentinel 判定にだけ使う。既存 test `test_resolver_exact_sentinel_is_the_only_absence` の padded 2 例は期待を変える。
- (P3) 責任者行の判定は admission の述語をそのまま使う (厳しくも緩くもしない)。
- (P4) admission module の bytes が変わるので live projection closure hash (base/sort/trigger) が変わる。§5 expectation 行は `未記入`、committed admission record は 0 件 (`docs/phase3-b4-reflux-ablation-admission-record-*.json` 不在) → 失効対象なし。事前登録文書 bytes は不変 (§5.1.1 pin 不変)。変更前 sha256 (3 module) は tracked file に pin 0 件。
- (P5) decode は admission の `utf-8-sig` に揃える。
- (P6) 段 5 は author 1 本 (2 module + 3 test file は相互依存が強く分割益なし)。

## 不変条件
- 規律 2: 受理集合の変化は「§5 外の行・責任者欠落を拒否」(縮小) と「strip」(admission に揃う 1 点) だけ。admission 関数自身の受理集合は不変 (既存 test 全緑 + 変異で示す)。
- label 集合不変 (D1649)。`PREREGISTRATION_FLOOR_LABEL` は admission の `_SECTION5_LABELS[4]` と同一文字列であることを test で pin。
- 実 repo 文書で `resolve_preregistered_authoritative_floor` → None (材料レポートの legacy 経路不変)。

## 受入・実測
- 焦点走 (login): `test_p3_b4_floor_artifact_issuer.py test_p3_b4_admission_record.py test_p3_b4_material_report.py test_p3_b4_closed_critic.py test_p3_b4_raw_record_producer.py`。受入全走 = `tools/dev_wave_wait.py acceptance --lease-optional -- python3 tools/run_tests.py` (計算ノード)。変異 matrix は container worktree から。
