# 段 4 裁定 — [T-2076] D1271 + [T-493] sort comparator 権威集合

## 結論

- **[T-2076] は本 wave で実装しない。** 新事実を添えてユーザー再裁定へ返す (裁定パッケージは末尾)。
- **[T-493] は実装する。** 権威集合は trigger 軸と同形の最小形とし、生成側・検証側の両方へ入れる。
- D1271 の「同じ変更単位で行う」条項は本 wave では充足不能と判断した。理由は下記「同一変更単位条項の扱い」。

## real / refuted の裁定

### 親の主張

| # | 主張 | 裁定 | 根拠 |
|---|---|---|---|
| N1 | `trusted_snapshot` / `snapshot_corpus()` は現行コードに不在 | **real** | 実装側 grep hit 0。撤去は T-1574 `36baa7a7b` (2026-08-25) |
| N2 | D1271 の対象は D825 の残余 (relation provenance) だと読み替えてよい | **refuted** | A2-C5。D1271 と D696 の対象は exact に corpus snapshot。読み替えは対象の拡大 |
| N3 | 内容 witness を観測 fd へ出せば親側で照合できる (P1-a) | **refuted** | A2-C1 / 段 2。候補は同じ fd の所有者で、`_broker_frame` は producer provenance を検査しない |
| P1-b | `active_order` と `relation[]` は報告経路に効かない | **real (親が再測して確定)** | `sort_swo_oracle.py:939-946`。`active_order` 由来の添字は dead な `relation[]` にしか使われず、comparator 入力は `(*active_write_set)[lhs_position]` の position 索引。`emit_bool` も position 順。B7 のこの項は **refuted** |
| P1-c | 保証境界を「保証する」側へ移す | **保留** | T-2076 を実装しないので移さない |
| P1-d | 権威集合は `CANDIDATES` から機械導出 | **real** | 採用 |

### 子の所見

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| A2-C1 | P1-a 却下理由は実コードで裏づく | **real** | 採用。P1-a は撤回 |
| A2-C2 | 「任意の行列」は強すぎ、正しくは「各 corpus について comparator の真の関係と無関係な任意の SWO 行列を受理させうる」 | **real** | 親が `_evaluate_executable:2442-2482` で再測。corpus 0/1 間の一致は要求されず、order 一致と SWO 公理だけ。裁定パッケージの文言に採用 |
| A2-C3 | ptrace trap 案は呼出し provenance を証明しない (trap・callsite が同一 TU、隠蔽は防壁でない) | **real** | 採用。段 2 の推奨設計を不採用 |
| A2-C4 | fork 案は成立しない | **real** | 親が再測して確定。(1) 候補文の引数評価 (comparator object 構築) は `sort()` へ入る前に worker 親で起きる。(2) 現行 seccomp は `clone` / `clone3` / `wait4` / `close` を許さず、filter は候補文より前に導入済みで積み増ししか出来ない。fork を可能にするには親側 filter を緩める必要があり、同じ filter が候補式にも適用される。**親の代替案は撤回** |
| A2-C5 | N2 の読み替えは対象拡大。ユーザー再裁定へ戻すべき | **real** | 採用。本裁定の骨格 |
| A2-C6 | membership は exact binding に包含され受理判定上冗長 | **real** | 採用。membership 述語を別に作らず exact binding 一本にする |
| A2-C7 | 段 2 の変異 3 件のうち 2 件は単一理由性を満たさない | **real** | 採用。下記の事前登録で再照準 |
| B-B1 | stock=`None` は実 artifact に対応しない (`stock_common` は name も comparator も持たない) | **real** | 採用。stock 特例を作らない |
| B-B2 | contract consumer の列挙が閉じていない | **real だが本 wave では無効** | T-2076 を実装せず contract を変えないため、consumer 追随は発生しない |
| B-B3 | legacy-v4 は不要 (live artifact 0 件) | **real** | 本 wave では contract を変えないので論点自体が消える |
| B-B4 | `HOLD.HELD=True` で凍結 bytes 検査は held、実効関門ではない | **real (親が再測)** | 採用。「既存 test が bytes 不変を担保する」とは書かない |
| B-B4b | freeze の generator SHA pin は着手前から drift 済み (`1d4d45a3` vs 現行 `a9edc1dc`)、`verify_document` は無条件 `FreezeError` | **real (親が再測)** | 採用。T-493 で generator を編集すれば pin はさらに動くが、**着手前から既に赤**であり本 wave が壊すのではない。`_validate_schema` は generator 検査より前に呼ばれ独立に呼べるので、そこへ入れる価値は残る。「live 凍結文書を端から端まで守る」とは主張しない |
| B-B6 | `SANCTIONED_EXCLUSIONS = ()` で oracle test は受入全走から除外されていない | **real (親が再測)** | 採用。親 brief の D669 記述は stale。訂正する |
| B-B7 | 親アンカー表の行ずれ (A2 の `Known residual` は `:916`、A7 の型検査は `:493`/`:524`、A10 fixture は `:107` まで) | **real** | 採用。実装子へ渡す表を訂正 |
| B-B7b | `active_order` は報告経路に効く | **refuted** | 上記 P1-b のとおり親が再測。エージェントの誤り |
| B/A2 共通 | 段 2 の ptrace 設計は 1 wave の規模を超え、保証も未証明 | **real** | 採用 |

## [T-2076] を実装しない理由

D1271 が命じた「基準 snapshot を親側へ移す最小実装」は、対象の識別子が既に存在しないため
**literal には実装対象が無い**。T-1574 が read-only arena で corpus 変異を予防済みで、
D825 はこれを「保証するもの」に入れている。

残る穴は relation provenance であり、これは D1271 が名指しした対象ではない (A2-C5)。
そして本 wave で検討した 3 案はいずれも成立しない。

- 内容 witness を観測 fd へ (親案 P1-a): 候補が同じ fd の所有者で、provenance を作れない。
- broker ptrace trap (段 2 案): trap も callsite も同一 TU にあり、呼出し provenance を証明しない。
- 比較ごとの fork (親の第 2 案): 候補式の引数評価が worker 親で起きるうえ、fork を通すには
  候補にも適用される seccomp filter を緩める必要がある。

**成立しうるのは、受理言語を検証済み IR へ縮め trusted interpreter で評価する案だけ** (D825 の第 1 案、
A2 の推奨)。これは「最小実装」でも「本題の実装だけ」でもなく、受理集合と合成エージェントの
インタフェースを変える大きな設計変更である。DW-S04 と D95 の境界により、親は独断で採らない。

## 同一変更単位条項の扱い

D1271 は T-493 と同じ変更単位を求め、その理由を「別々にすると受入枠を 2 回消費する」と書いている。
T-2076 に実装が無い以上、束ねて節約できる枠は存在せず、条項の前提が消える。
T-493 単独の実装は受入枠を 1 回だけ使い、これは実行可能な最小値である。
よって条項は本 wave では充足不能とし、T-493 を単独で進める。

**この判断は親のものであり、ユーザー裁定ではない。** 裁定パッケージに明記して返す。
T-493 は受理集合を**狭める**方向の変更で、規律 2 と整合し、可逆である。

## [T-493] の実装裁定 (plan v2)

### 採る形

1. 新 module `orchestrator/campaign/sort_comparator_authority.py`。
   `s6_sort_sweep.CANDIDATES` からのみ index を機械導出し、comparator literal を再掲しない。
   import 時に name 重複・implementation 重複を fail-closed で検出する
   (`_build_trigger_name_mask_index` と同形)。
2. 公開 API は **exact binding 一本**: `require_sort_name_comparator_binding(name, comparator)`。
   独立した membership 述語・公開 mapping・stock 特例・`STOCK_IMPL_NOTE` 拒否は作らない
   (A2-C6、B-B1、B-B5)。
3. `s1_known_axes_freeze.py` の**生成側と検証側の両方**へ束縛を入れる。trigger 軸が
   `:591`/`:597` (生成) と `:821` (`_validate_schema`) の両方で検査しているのと同形にする。
   - 生成側: `_sort_entry` の read-heavy 経路 (`:493` 付近、`("sk_ad", comparator)`) と
     main 経路 (`:524` 付近、`(best["name"], comparator)`) の comparator 取得直後。
   - 検証側: `_validate_schema` の workload loop (`:815-827`)、trigger の 2 configuration の後に
     `sort_best` を追加する。
4. 外側 whitespace の同値化はしない。exact bytes 一致とする。
5. authority error は `FreezeError` に変換する。import 時例外は index 構築の不整合だけに限る。

### 不変条件 (実装子に課す)

- `output/s1-freeze/known_axes_freeze.json` と `measurement_freeze.json` の bytes を変えない。
- 凍結済み 3 entry (balanced=`sp_dd` 268 bytes、write-heavy / read-heavy=`sk_ad` 262 bytes) が通ること。
- 既存テストの期待値を変えない。受理集合を指示外に変えない。
- `sort_swo_oracle.py` を編集しない (T-2076 は本 wave の scope 外)。
- contract ID / 保証境界 / protocol version に触れない。

### 変異事前登録 (DW-M01、実装前に凍結)

| ID | 変異位置 | 無効化の仕方 | 期待して赤くなる node (完全集合) | 単一理由性の根拠 |
|---|---|---|---|---|
| MUT-1 | `sort_comparator_authority.require_sort_name_comparator_binding` の不一致 raise | raise を no-op にし常に受理させる | `orchestrator/tests/test_s1_known_axes_freeze.py::test_validate_schema_rejects_sort_comparator_outside_authority`, `::test_validate_schema_rejects_sort_name_comparator_mismatch` | 入力の document key・型・name はすべて正当。`_validate_schema` 単体を対象にするので `verify_document` 後段の機械再構成は走らない (A2-C7-3) |
| MUT-2 | 同 module の index 構築時の重複検出 | name 重複・implementation 重複の検出を落とす | `orchestrator/tests/test_sort_comparator_authority.py::test_duplicate_name_is_fail_closed`, `::test_duplicate_implementation_is_fail_closed` | 重複を見る層は他に無い |
| MUT-3 (過剰拒否の正例) | 同 raise | 常に拒否させる | `orchestrator/tests/test_s1_known_axes_freeze.py::test_validate_schema_accepts_frozen_sort_entries`, `orchestrator/tests/test_sort_comparator_authority.py::test_all_fifteen_candidates_bind` | 受理集合を狭める wave の承認外過剰拒否を検出する (DW-M01) |

MUT-1 と MUT-3 は同じ行を逆向きに壊す対であり、累積適用しない。

### 段 2 の変異登録のうち落とすもの

- membership gate の変異 (段 2 の #2): membership 述語自体を作らないため消滅 (A2-C7-2)。
- input witness の変異 (段 2 の #1): T-2076 を実装しないため消滅。

## 分割方針

編集面は `orchestrator/campaign/sort_comparator_authority.py` (新規)、
`orchestrator/campaign/s1_known_axes_freeze.py`、
`orchestrator/tests/test_sort_comparator_authority.py` (新規)、
`orchestrator/tests/test_s1_known_axes_freeze.py` の 4 file。相互に密結合なので
**Codex `role=author` 1 単位**とする。分割しない。

## 裁定パッケージ (ユーザーへ返す)

1. **D1271 の literal な対象は既に存在しない。** 命じられた「基準 snapshot を親側へ移す最小実装」は
   T-1574 (2026-08-25) が read-only arena で先に閉じており、D1271 起票日より前に着地している。
2. **生きている穴は relation provenance で、これは D1271 の対象ではない。**
   現行 oracle は、各 corpus について comparator の真の関係と無関係な任意の SWO 行列を
   候補に報告させうる。`SORT_SWO_GUARANTEE_BOUNDARY` の非保証がこれを既に明記している。
3. **最小実装は存在しない。** 3 案 (fd witness / ptrace trap / 比較ごと fork) はいずれも
   独立 2 レンズと親の再測で不成立。成立しうるのは受理言語を検証済み IR へ縮め
   trusted interpreter で評価する案だけで、これは受理集合と合成エージェントの
   インタフェースを変える大きな設計変更である。
4. **ユーザー裁定が要る択一:** (a) verified IR + trusted interpreter を別 wave の設計として起票するか、
   (b) 非保証のまま運用を続けるか (D1271 は却下済みだが、前提が変わった)、
   (c) 別案があるか。
5. **親が独断した点:** D1271 の「同じ変更単位」条項を充足不能と判断し、T-493 を単独で実装した。
   理由は上記「同一変更単位条項の扱い」。取り消したい場合は revert 可能。
6. **付随して見つかった既存 drift (本 wave 起因ではない):**
   `known_axes_freeze.json` の generator pin (`1d4d45a3`) が現行実装 (`a9edc1dc`) と食い違い、
   `verify_document` は無条件で `FreezeError` になる。凍結 bytes 検査は `HOLD.HELD=True` で held。
