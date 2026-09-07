# 段 1 brief — B-4 権威 floor 成果物の発行と配線

**scope (2 点だけ)。** (1) **発行**: floor 値を「権威ある成果物」として発行する経路を作る。入力は
`orchestrator/campaign/floor_pair_driver.py` が出す `floor-pair-summary/v2` (create-only JSON、
`status="generated"` のとき `candidate_floor` を持つ)。(2) **配線**: `p3_b4_material_report.py` が
その権威成果物を解決・検証し、値を凍結評価器 `evaluate_b4_artifacts(floor=...)` へ**引数として**渡す。
権威成果物が無い間は、現行の正直な不在経路 (`protocol_violation` / `floor_domain_error`) を 1 bit も変えない。

**成果物影響 (DW-G05)。** 現在 production 分析経路は `p3_b4_material_report.py:243` で `floor=None` を渡し、
`p3_b4_analysis_contract.py:323-325` が無条件に `FLOOR_DOMAIN_ERROR` を立てる。**どんな測定を入れても
B-4 の分析 verdict は 1 種類しか出ない。** 放置すると B-4 の材料レポート (Phase 3 主経路の片翼) は
永久に evidence-only のままで、§7.1 の 4 分類は実効化しない。

**確定済みユーザー裁定 (再裁定しない)。**
- D1530 / D1592: 発行と配線は**実 producer の接続と同じ変更単位**で行う。D1592 却下欄が本 wave を名指ししている。
- [T-2289] の closure receipt 接続は**同梱しない** (D1530)。
- D1377: 生成器は floor を caller から受け取らない。CLI 引数も既定値も持たない。→ 値の出所は権威成果物だけ。
- D1383: AI は floor 値を既成事実として埋めない。→ **本 wave は値を焼き込まず、機構だけを作る。**
- D1696: 対照対 driver が検査しない 9 項目は人手責任のまま (見送り)。→ その validator 群は scope 外。
- 規律 2: 正しさゲートを緩める変更は採らない。floor を緩める方向 (tie を減らす方向) の既定値・fallback は禁止。

**不変条件。**
- 分析 5 module の source closure member tuple (`p3_b4_analysis_prereg_consumer.py:98` `_CLOSURE_PATHS` と
  `p3_b4_analysis_path` 側 `_SOURCE_CLOSURE_PATHS` の AST 完全一致) を変えない。**凍結契約 module は非改変。**
- 事前登録 doc を編集しない (批准節は raw bytes 無条件 pin。§5 記入は別 wave [T-2140] の担当)。
- 権威成果物が不在のときの report bytes・verdict を変えない (既存 test が守る)。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない。

**(P1) 親の provisional 裁定 — 段 3 の攻撃対象。**
- **(P1-a) 型の断絶。** driver の `candidate_floor` は **float** (`floor_pair_driver.py:2687`) だが、契約の
  `as_b4_exact_fraction` (`p3_b4_analysis_contract.py:233-253`) は **float を明示的に拒否**し、int /
  `Fraction` / `(int,int)` だけを受ける。**変換を発行段に置かなければ、配線しても恒真に
  `floor_domain_error` のままで機構が空回りする。** provisional: 発行段で**保守側 (切り上げ)** の exact ratio を
  定義済み精度で作る。floor が大きい方が tie が増え主張が弱くなるので、切り上げが規律 2 に沿う。
- **(P1-b) 発行の権威の出所。** provisional: 権威の根拠は事前登録 §5 の floor 行 (artifact path + sha256) とし、
  配線は§5 から解決する (§5.1.1 逐語「§5 の凍結 artifact から読んだ値」)。§5 が未記入 sentinel の間は不在扱い。
  → **caller 自己申告経路を作らない** (D1377)。
- **(P1-c) 採用裁定の束縛。** D1641 第 2 項の採用裁定をどう成果物へ束ねるか。provisional: 発行入力に
  採用記録を要求し、無ければ発行しない。新しい一般化した gate は作らない。

**成果物の形。** 新 issuer module (分析 closure の外) + `p3_b4_material_report.py` の配線 + 双方の test。
docs は insight と `docs/spool/` fragment のみ。

**並列分割。** 段 5 は 2 単位 — A = issuer (発行と exact 変換)、B = 配線と report 射影。編集 file を重ねない。
