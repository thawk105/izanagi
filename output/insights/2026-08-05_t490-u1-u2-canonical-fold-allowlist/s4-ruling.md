# 段 4 裁定 — [T-490] U-1/U-2 (plan v2)

段 2 プラン (plan.md) と段 3 敵対 2 本 (adv_a.md / adv_b.md) を突き合わせた親の裁定。
**plan.md と本書が食い違う場合は本書を優先する。**

## 全体判定

両レンズとも NO-GO。**実装境界 (どこを直すか) は妥当だが、テスト保証が弱い**という点で
2 本が独立に一致した。したがって実装方針は plan.md を採るが、**テストと変異を強化した上で GO** とする。

## 所見の裁定

| # | 出所 | 内容 | 判定 | 扱い |
|---|---|---|---|---|
| F1 | A#1 | `quarantine` は「述語文字列が source へ入る唯一の境界」だが「source が identity へ入る唯一の境界」ではない。既 materialize 済み木を `loop`/`pipeline` へ直接渡す経路には畳み込みが無い | **real** | **scope 外 → 裁定パッケージ (SP1)** |
| F2 | A#2 | `diffq_variant_id` は raw implementation を hash するため、reject 側 ID は多重化が残る | **real** | **scope 外 → 裁定パッケージ (SP2)** |
| F3 | A#3 + B#1 | 段 1 P-D と計画テストは raw SHA / fake resolver であり、本番 `src_token` の分岐を固定していない | **real** | **採用 (MF2)** |
| F4 | A#3 | U-1 の畳み込みは、従来 preprocess/build で落ちうる NBSP・U+3000 等を compiler 到達前に除去するため、**end-to-end 受理集合は U-1 でも変わる**。brief 不変条件 4 の記述が誤り | **real** | **採用 (MF4、文書是正)**。挙動は裁定済み択一 (b) の当然の帰結であり実装は変えない |
| F5 | A#4 + B#2 | `canonicalize_predicate` を `return text.strip()` にする変異と、index の重複 key を黙って上書きする変異が、計画テストを生存する | **real** | **採用 (MF1)** |
| F6 | A#5 | P-F/P-G の件数が measurement freeze だけの過剰一般化。実際は 3 freeze 合計で 16 gate / 8 comparator。ただし定性的結論 (gate は exact、comparator は空白付き) は成立 | **real** | **採用 (MF4、文書是正)** |
| F7 | A#6 | `str` subclass (custom `__hash__`) の既知ラベルが、現行 flags-only から新たに拒否になりうる | **real (nit)** | **不採用**。repo 内に該当 caller が無く、JSON 由来の値は常に plain `str`。現行 4 分岐も hash 判定なので同じ object は今日も分岐に入らない。記録のみ |
| F8 | B#3 | allowlist の drift guard (三集合の等価) は独立性を証明しない。producer 定数を流用する変異と `"system-gate"` だけ拒否する変異が生存 | **real** | **採用 (MF3)** |
| F9 | B#4 | brief の「材料 proof chain も統合される」は過大。raw provenance hash (`entry_sha256` / `binding_sha256` / review receipt / `diffq-*`) は統合されない | **real** | **採用 (MF4、文書是正)** |
| F10 | A#7,8,9 + B#5,6 | 6 構成正例・flags-only 2 構成・comparator 非干渉・fail-closed 例外経路・caller 取り残しなし・純増ゼロではない | **refuted** | 対処不要。純増の根拠として記録する |
| F11 | B#nit | 分割理由 (production 所有の交差) が誤り。交差するのは `test_s1_direct_comparison.py` だけ | **real (nit)** | **採用 (MF4、文書是正)**。単一実装単位の選択自体は維持する |

## 確定した実装内容 (plan v2)

### U-1

1. `orchestrator/campaign/trigger_gate_binding.py` に `canonicalize_predicate(text: object) -> str` を新設する。
   - 内部の private index は `strip 形 -> emitter 未 strip 出力` の dict とする。
   - `CANONICAL_PREDICATES` は従来どおりその **key 集合**の frozenset とし、公開値と受理集合を変えない。
   - 同じ strip key が複数 mask から出たら **import 時に `RuntimeError`** で倒す。
   - 非 `str` / 正準集合外は既存 `_reject()` 経路で拒否する。
   - `expected_predicate_sha256` と `is_canonical_predicate` は変更しない。
2. `orchestrator/campaign/p3_s4_loop.py` の `quarantine` で、
   **`marker_id == TRIGGER_MARKER_ID` の membership 検査を通った直後、`render_hole` より前**に
   `implementation = trigger_gate_binding.canonicalize_predicate(implementation)` を置く。
   - 他の marker (sort / backoff) には**一切適用しない**。
3. 他の 2 consumer (`s1_direct_comparison.py:521`、`s1_verify_extime_calibration.py:222`) は変更しない。
   いずれも診断・意味検査であり、実 materialize は共有 `quarantine` に合流する。

### U-2

4. `orchestrator/campaign/s1_direct_comparison.py` に module-private の固定 frozenset を置く。
   - 内容は 6 構成: `backoff_fixed_best` / `ident_all` / `p2_2_flag_opt` / `sort_best` /
     `stock_common` / `system_gate`。
   - **producer 定数 (`s1_measurement_freeze.CONFIGURATIONS` / `s8b_holdout_freeze.VARIANT_NAMES`) を
     import して流用しない。** 将来の producer 拡張を materializer が自動認可すると U-2 の独立閉包を失う
     (plan.md の反論を採用)。独立性はテスト MF3 で behavioral に証明する。
5. `prepare_cell` の `variant` / `configuration` 型検査の直後、flags 解釈・checkout より前に
   allowlist 外を既存 `DriverError` で拒否する。新しい例外型は作らない。
6. `stock_common` / `p2_2_flag_opt` 用の分岐は**追加しない**。現行どおり flags-only の
   `PreparedCell` を yield する。

## must-fix (テスト保証、すべて成果物影響つき)

- **MF1 (F5)** — `canonicalize_predicate` が「index の値 (emitter bytes)」を返すことを証明する。
  現 emitter は 32 本すべて strip 恒等なので、実データだけでは `return text.strip()` と区別できない。
  外周空白を**含む** synthetic index を注入して公開関数を呼び、raw 値が返ることを固定する。
  重複 strip key の `RuntimeError` 負例も追加する。外周空白は P-C の 7 種
  (` ` / `\t` / `\r\n` / `\x0b` / `\x0c` / NBSP / U+3000) をすべて含める。
  - 成果物影響: 将来 emitter が外周空白を正準 bytes にした場合、binding digest は raw emitter を
    hash する一方 materialized source は strip 形になり、材料 proof の predicate/source 対応がずれる。
- **MF2 (F3)** — identity の証明を fake resolver に依存させない。
  (a) 実 `quarantine` で 7 種すべての `edited_text` / `working_diff` が **byte-exact に同一**であること、
  (b) 既存 `_fake_ccbench_repo()` + `_require_g13()` の先例に倣い、**本番 `source_digest.resolve`**
  で exact 形と空白付き形の token が一致することを固定する。(b) が環境都合で実走できない場合は
  skip でなく理由を明記して報告し、緑と数えない。
  - 成果物影響: `pipeline.variant_id` は `src_token` を直接使うため、fake 固有の赤で
    certified 選択・試行台帳の variant 統合を認証してしまう。
- **MF3 (F8)** — allowlist の独立性を behavioral に証明する。
  (a) producer 定数 (`s1_measurement_freeze.CONFIGURATIONS`) を monkeypatch して 7 個目を足しても
  `prepare_cell` がその 7 個目を**拒否し続ける**こと (= 流用変異を殺す)、
  (b) `"system-gate"` を含む**複数の相異なる未知値**が拒否されること (= 単一 literal 拒否変異を殺す)。
  現行三集合の等価テストは drift 可視化として残してよいが、独立性の証明として数えない。
  - 成果物影響: 新 producer configuration や未列挙の未知値が 4 分岐を抜け、flags-only の
    source/token を作り、材料レポートと試行台帳に誤った configuration を載せる。
- **MF4 (F4/F6/F9/F11)** — 親の記述を一次資料に合わせて是正する (docs、親が行う)。
  - U-1 は **end-to-end 受理集合を変える** (裁定済み択一 (b) の当然の帰結)。
    不変条件は「`is_canonical_predicate` の membership 集合を変えない」に限定する。
  - 統合されるのは **successful materialized source・`src_token`・`pipeline.variant_id`** だけであり、
    raw provenance hash (`entry_sha256` / `binding_sha256` / review receipt / `diffq-*`) は意図的に別のまま。
  - 凍結物の実数は 3 freeze 合計で **16 gate (すべて exact) / 8 comparator (すべて外周空白付き)**。
    `FROZEN_MANIFEST` の 23 件は現行 bytes の pin であって恒久 membership ではない。
  - 単一実装単位の理由は「production 所有の交差」ではなく「`test_s1_direct_comparison.py` の交差」。

## scope 外 real 所見 (裁定パッケージへ、実装しない)

- **SP1 (F1)** — 既 materialize 済み source 木を `loop.run_campaign` / `pipeline.evaluate` へ
  直接渡す経路には畳み込みが無く、`pipeline._require_materialized_trigger_predicate` は hole を
  `.strip()` 比較するため外周空白を保持した source も admission を通る。
  閉じるには build admission 側の受理集合を変える (strip 比較 → exact 比較、または
  post-materialization assertion の新設) 必要があり、**裁定されていない受理集合変更**である。
  [T-492] の semantic membership と同じ面に属する。
- **SP2 (F2)** — `diffq_variant_id` が raw implementation を hash するため、trigger の
  post-membership reject では exact 形と空白付き形が別 reject variant として試行台帳に残る。
  WAL の reject key 導出を変える変更であり、`load_diff_rejections` / critic 参照の consumer を持つ。
- **SP3 (F7)** — `str` subclass の既知ラベル (nit)。実 caller 不在。

## 変異事前登録 (`DW-M01`)

各変異は「位置」「無効化時に赤くなる単一の理由」「前後に同じ入力を拒否する層が無いこと」を
実装後に `tools/mutation_harness.py` で確認する。

| ID | 変異 | 期待 kill テスト | 単一理由性の根拠 |
|---|---|---|---|
| M1 | `quarantine` の正準化代入を削除 | trigger 7 種の materialized bytes 同一性 (MF2a) | 外周空白は membership も diff 検疫も通るため、赤の理由は materialized bytes 差だけ |
| M2 | marker guard を外し全 marker を正準化 | sort comparator 逐語保持テスト | sort は membership を通らない直接境界入力。comparator 改変だけが赤 |
| M3 | `canonicalize_predicate` を `return text.strip()` に変更 | MF1 の synthetic index 注入テスト | 実 emitter は strip 恒等なので実データ経路では等価変異。synthetic index だけが区別する |
| M4 | index builder が重複 key を黙って上書き | MF1 の重複 key `RuntimeError` 負例 | 現行 32 本は一意なので実データでは発火しない。synthetic collision だけが区別する |
| M5 | allowlist の拒否を削除 | 未知 configuration 拒否テスト (MF3b) | freeze verifier を通さない直接入力で flags は有効。現行なら flags-only yield まで到達する |
| M6 | allowlist を `frozenset(s1_measurement_freeze.CONFIGURATIONS)` に置換 | MF3a (producer 定数を 7 値に monkeypatch) | 現行値の等価テストは通るため、この変異を殺せるのは MF3a だけ |
| M7 | allowlist 拒否を `configuration == "system-gate"` だけに縮小 | MF3b の複数未知値 | 単一 literal では 2 つ目の未知値を拒否できない |
| M8 | allowlist から `stock_common` を削除 | 6 構成正例 + flags-only テスト | **受理集合を縮小する wave の過剰拒否検出の正例** (`DW-M01` 要求) |

M1 と M2、M3 と M4 は同一ファイルの複数置換になりうるため、`DW-M04` に従い累積適用し
置換ごとに一意性を assert する。

## 不変条件 (更新版、違反したら停止)

1. `sort_best` の `comparator` bytes に触れない (trigger marker 限定)。
2. 現行 6 構成の受理挙動を変えない。`stock_common` / `p2_2_flag_opt` は flags-only を維持する。
3. 凍結成果物の bytes を変えない。`FROZEN_MANIFEST` 23 件と既存 golden は不変のまま緑。
4. `is_canonical_predicate` の **membership 集合**を変えない (strip 同値受理を維持)。
   end-to-end の受理集合が padded 入力について変わるのは択一 (b) の当然の帰結であり、これは許す。
5. 既存テストの期待値を変更しない。
