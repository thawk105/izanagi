# 段 1 brief — [T-595] 段 2/3 の reasoning max→high 非劣性評価

起点 main `9cb0f24b` / branch `worktree-dev-wave-t595-reasoning-ab` / 2026-08-07。
`(P1)`〜`(P6)` は**親の provisional 裁定であり段 3 の攻撃対象**である。

## 依頼と確定済み裁定

- 依頼: dev-wave 段 2 (プラン起草) と段 3 (敵対相談) の `reasoning=max` を `high` へ落として
  よいかを `tools/codex_reasoning_ab.py` の paired・blind・非劣性で評価する。
  endpoint に**後段の must-fix 件数と fix 巡回数**を含める (D207)。
- D207 (確定): 既定 effort は観察値で引き下げない。可否は当該装置の paired・blind・非劣性だけが
  決める。**本 wave も既定 (段 2/3 = max、段 5 = high) を変更しない。**
- 規律 2 (不変): 検出力を下げる変更は「正しさゲートを緩める変異」として扱う。

## 実測した前提 (brief 前に一次資料で確認)

1. `tools/codex_reasoning_ab.py` (5390 行) は **T-181 の focused review benchmark に固定**。
   `SESSION_IDS` / `PROMPT_SOURCE` / `CASE_HASHES` / `CASE_NUMSTAT` / `EXPECTED_SCHEDULE` が
   POS/NEG 2 case の literal であり、段 2/段 3 の case family は存在しない。
2. T-181 の台帳は `experiment_complete=false` (rc=24、snapshot oracle replay mismatch)。
   **最終版装置での 10 run 再走が未了**。この未認証性を隠した引用は禁止 (insight README)。
3. 現装置の収集対象は run 単位の資源・機械 decision・R-1 候補・盲検 verdict であり、
   **must-fix 件数と fix 巡回数は収集しない** (下流段の量であるため)。
4. codex 実走はログインノードのみ (計算ノードは外向き DNS 不通、T-181 実測)。
   T-181 の 1 run は CLI reported 180k〜691k token / wall 7〜28 分。
5. pin 閉包 (DW-O09): `tools/codex_reasoning_ab.py` を bytes pin する経路は
   `orchestrator/tests/test_codex_reasoning_ab.py` (72 test) だけ。
   `output/insights/2026-07-30_t181-reasoning-ab/**` を pin する `.py` は無い (docs 参照のみ)。
   durable manifest の再発行は不要。
6. 見送り裁定なし: repo 外 (`rulings-inbox/`、稼働 wave) を機構名 `reasoning` / `reasoning_ab` /
   `非劣性` / `effort` で全文検索し、T-595 の見送り・supersede は 0 件。

## 測定の構造的困難 (この wave の中心論点)

D207 が要求する endpoint は段 2/3 の**下流**にある。must-fix 件数は段 3 (または段 6 レビュー) の
出力、fix 巡回数は段 6 の出力である。段 3 自身が被検体である以上、
「段 2 arm を変えて下流を丸ごと回す」設計は **1 replicate = 1 本の dev-wave 相当**になる。
paired 2 arm × 非劣性に要る n をかけると、実走は本 wave の射程を大きく超える。

## 生死確認の一次結果 (DW-G01、LLM 不使用、2026-08-07 実測)

endpoint の実在 (DW-O13) を歴史成果物で確認した。`/work/1/SFC/tanab/dev-wave-jobs/<wave>/` に
`s2-plan.md` が 37 wave、`s6-rev*.md` (must-fix の出所) と `s6-fix*.md` (fix 巡回の 1 巡 = 1 file)
が残っている。**両 endpoint は実成果物として実在する** — ただし file 命名は wave 間で揺れており
(`s5-impl.md` / `s5-implB.md` 等)、機械集計には正規化が要る。

fix 巡回数の観測分布 (実装を伴う 24 wave、すべて現行の段 2/3 = max 下):
`0×3, 1×4, 2×7, 3×5, 4×4, 7×1` — 平均 2.33、標準偏差およそ 1.6。

**この分散が意味すること:** 巡回数を endpoint にした paired 非劣性で margin を 1 巡に取ると、
片側 5% / 検出力 80% で必要な pair 数は概ね **9〜15 pair = 完全な dev-wave 18〜30 本**になる。
1 本あたり codex 数百万 token・数時間で、しかも実走はログインノード限定である。
**D207 が要求する endpoint をそのまま満たす実験は、単一 wave の射程を桁で超える。**

## provisional 裁定 (攻撃対象)

- **(P1) 本 wave は production 実験を実走しない。** 成果物は (a) 事前登録した実験 protocol、
  (b) 装置側の case family 一般化と新 endpoint 収集、(c) LLM を使わない生死確認までとする。
  実走は予算と時間を伴う別 campaign であり、ユーザーの go 判断に返す。
- **(P2) 段 2 の品質 endpoint は「固定 effort・arm 盲検の敵対レビュアが plan へ挙げる
  must-fix 件数」を一次代理**とする (少ないほど良い)。レビュア自身は max 固定で被検体にしない。
- **(P3) fix 巡回数に代理を置かない。** 代理を作れば D207 が排除したかった「弱い起草が巡回を
  増やす経路」を測らないまま通す。測れないなら**測れないと確定し裁定へ返す**。
- **(P4) 段 3 の endpoint は T-181 型**(既知の埋め込み欠陥に対する検出率 + 偽陽性) とし、
  段 2 の endpoint とは別 case family として設計する。
- **(P5) 非劣性 margin は事前登録し、実走前に凍結**する。事後に決めない。
- **(P6) 生死実験 (DW-G01) を先に置く。** 「歴史 wave の段 2 入力から新規凍結 snapshot を
  build し、現行 oracle で `verify-snapshot` が緑になるか」を LLM 抜きで確認する。
  ここが赤なら装置の一般化が先で、protocol の実装は着手しない。

## 不変条件

- 既定 effort を変更しない。`docs/dev-wave/workers.md` の `DW-S02` / `DW-S03` を書き換えない。
- 装置の既定挙動 (T-181 case の受理集合・rc・凍結値) を回帰させない。既存 72 test は緑を維持。
- T-181 の未認証性を、新 protocol の根拠として洗浄しない。
- 実験の primary は盲検裁定であり、機械層の出力は候補に留める (既存契約を継承)。
- 親は実装面を直接編集しない。実装は Codex `role=author` の子が書く。

## 成果物影響 (DW-G05)

段 3 の検出力が落ちれば、certified 選択・材料レポートを守る must-fix (reward hack・oracle 穴) が
段 4 へ届かず、**受理集合が黙って広がる**。本 wave はその可否を測る装置と事前登録を用意する
ものであり、装置が無いままの引き下げは「観察値で決めた」ことになり D207 違反になる。

## 並列分割方針

段 2 プラン起草 1 本。段 3 は 2 レンズ並列 —
(A) 実験妥当性 (交絡・盲検の破れ・代理 endpoint の妥当性・n と margin)、
(B) 射程と fail-open (P1〜P3 の逃げ、装置一般化の回帰、未認証台帳の洗浄)。
