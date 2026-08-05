# [T-492] 段 4 裁定 + プラン v2

段 3 の敵対 2 本はいずれも NO-GO。所見を real/refuted・採用/不採用・scope 内/外で裁定した。

## 親裁定の要点 (先に確定した不変条件)

**本 wave は `build_document()` の出力を一切変えない。受理集合を狭めるだけである。**
これにより「凍結 bytes 不変」は副作用ではなく検査可能な性質になる。

> **段 6 レビュー R1 による是正 (2026-08-05)。** 上の一文は不正確だった。
> `generator.sha256` は generator 自身の bytes から作られる (`s1_known_axes_freeze.py` の
> `build_document` 内 `_sha256(ROOT / SCRIPT_REL)`) ため、generator を編集した本 wave では
> **既定引数の `build_document()` / `generate()` が返す `generator.sha256` は必ず変わる**
> (`1d4d45a3…` → 新値)。正しい不変条件は次の 2 つである。
> 1. **凍結済み artifact の bytes を編集しない・再発行しない。**
> 2. **`generator_sha` を明示して射影した `build_document()` では、受理される入力に対し
>    非 metadata field (top-level field、挿入順、trigger entry の name/flags/gate_predicate、
>    `sources` の要素数と内容) が完全に不変である。**
>
> 下流への影響も記録する: 既存凍結物に対する legacy `verify_document()` は、これまでの
> source mismatch より**先に** generator mismatch を返すようになる (診断順と文言が変わる)。
> T-080 receipt が active な公開経路は `/generator/sha256` を静的再構成比較から除外するため、
> certified 選択の値は変わらない。
根拠: `build_document` を再実行するのは draft 経路 `_draft_reconstruct_known_axes`
(t080_freeze_migration.py:1339-1368) だけで、稼働中の receipt gate は
`_verify_reconstruction_static` (:1100-1116) の静的ハッシュ比較である。

親 brief の (P1) は**撤回**する。「build 側 1 箇所で検証層も覆える」は誤りで、
T-080 active 時の公開 gate は `static_gate_adapter` → `_verify_known_schema` (:1803-1814) →
`s1_known_axes_freeze._validate_schema()` を通り、`build_document` も legacy `verify` も呼ばない
(s8b_oracle_driver.py:406)。doc 側検査は `_validate_schema()` に置く。

## 所見の裁定

| # | 所見 | 裁定 |
|---|---|---|
| A-F1 / B-8 | `s8b_holdout_freeze` は known doc の述語を無検査で variant_binding へ複製する | **real・scope 外 → 裁定パッケージ**。本 wave の脅威 (両 provenance 連動 drift) は known producer 経路で閉じる。holdout 単体まで閉じるには `s8b_holdout_freeze.py` の編集が要り、その generator hash pin (`1910fff3…`) は known と同型の巻き込みを起こす。裁定は U-3 を `s1_known_axes_freeze` に限定している |
| A-F2 / B-9 | membership 権威 (`trigger_gate_binding` / `reflux_ir`) が proof chain に帰属せず、`selection_rules` も新規則を記録しない | **real・scope 外 → 裁定パッケージ**。どちらも `build_document()` の出力を変える (sources 追加 / rule 文言)。上の不変条件に反し、かつ次回 refreeze の世代移行 (A-F4) が未裁定のまま先に台帳形を変えることになる。refreeze 移行の裁定に同梱する |
| A-F3 | 親の「1 failed / 222 passed」からの一般化が広すぎ、手続きも未記録 | **real・採用**。結論を「現行 active receipt 経路は live generator drift を許す」へ限定し、手続き (変異行・baseline・runner・対象・skip) を worklog と insight に逐語記録する。legacy S1 / measurement / calibration は live generator hash を見るので、本 wave 後は**拒否理由が 1 つ増える** (既に s8a drift で赤のため能力の純減はない) |
| A-F4 / B-4 | 次回 refreeze は T-080 receipt を必ず無効化する | **real・scope 外 → 裁定パッケージ (P1)**。「T-492 を入れれば次回 refreeze が可能」は**偽**。known→measurement→holdout→manifest/ratified の再発行順と receipt の supersede/retire が別途要る。[T-478] の世代移行設計と同じ面 |
| A-F5 / B-6 | 公開 wiring テストが過剰決定で、検査を消しても generator/source drift で赤いまま (偽の kill) | **real・採用**。`verify_document` は `_validate_schema` を最初に呼ぶ (:720) ので拒否順は正しいが、テストは**診断文言 `正準集合外` を完全一致で固定**し、`build_document` を sentinel にして rebuild 未到達も検査する |
| B-5 | private `_trigger_entries()` 負例だけでは公開 `generate()` の write-before-reject を証明しない | **real・採用**。完全 mock の `generate(output_path)` 負例を 1 本足し、`FreezeError` と `not output_path.exists()` を同時に固定する |
| B-2 | `_verify_worktree_basis_files` は draft/reissue で generator bytes 一致を要求する | **real・採用 (記録のみ)**。本 wave は receipt を再発行しないので blocker でない。制約として worklog に残す |
| B-7 | 正例の多くは既存被覆と重複 | **partial**。「現行 6 値が通る」は受理集合を狭める wave の**承認外過剰拒否の正例** (DW-M01) として必要なので残す。strip 同値の独立テストは既存 (`test_trigger_gate_binding.py:225`) に譲り新設しない |
| A-F6 | canonical だが name と mask が食い違う述語は通る (`name=g_rl` に mask 4 の文) | **real・scope 外 → 裁定パッケージ (P1)**。誤 certification まで到達しうる別面。[T-493] の閉じた権威集合と同じ主題 |
| A 末尾 | P3 の `ROOT` patch は再構成まで進むと `_module_source` が別理由で落ちる | **nit・採用**。patch を `gate_check()` 呼出しの周囲だけに限定する |

## プラン v2 (実装する範囲)

### 実装 1 — 権威の import

`orchestrator/campaign/s1_known_axes_freeze.py:24-27` の import 群へ
`from campaign import trigger_gate_binding  # noqa: E402` を追加する。
循環はない (`trigger_gate_binding` → `reflux_ir` → `axis_trigger_gating` で戻り edge なし)。

### 実装 2 — 共通 helper

`FreezeError` 直後 (:77-80 付近) へ追加する。

```python
def _require_canonical_trigger_predicate(
    predicate: object, *, workload: str, configuration: str) -> None:
```

- `trigger_gate_binding.is_canonical_predicate(predicate)` が偽なら `FreezeError`。
- 診断は述語本文を転載せず `entries.{workload}.{configuration}.gate_predicate が正準集合外`。
- 戻り値なし。入力を書き換えない。`canonicalize_predicate` も独自の空白処理も使わない。

### 実装 3 — 生成層

`_trigger_entries()` の `:493` (`gate_predicate` 取得直後、main/remeasure 一致検査より前) と
`:496` (`ident_predicate` 取得直後、同前) で helper を呼ぶ。
`configuration` は `"system_gate"` / `"ident_all"`。

### 実装 4 — 検証層

`_validate_schema()` の entry 構造検査後 (:710-712 の直後) に、3 workload ×
{`system_gate`, `ident_all`} の 6 値を走査して helper を呼ぶ。
record が `Mapping` でなければ `FreezeError`。`sort_best` と backoff には触らない。

### 実装 5 — テスト

すべて `orchestrator/tests/test_s1_known_axes_freeze.py` へ足す (G7 の是正だけ別ファイル)。

- 正例 1 本: 現行凍結 doc の 6 値で `_validate_schema()` が通る (過剰拒否の検出)。
- 生成層負例 2 本: main/remeasure をともに `"izanagi_gate_pass = true;"` にし、
  `system_gate` / `ident_all` を個別に殺す。`_source` と `_module_source` も mock し、
  別理由で落ちないようにする。
- 検証層負例 2 本: 現行 doc を deep-copy して 1 値だけ非正準にし、`_validate_schema()` を直接呼ぶ。
- 公開 producer 負例 1 本: 完全 mock 下で `generate(output_path)` が `FreezeError` を上げ、
  かつ `output_path` が**存在しない**ことを固定する。
- 公開 verifier wiring 1 本: `build_document` を sentinel に差し替え、`verify_document()` が
  `_validate_schema` 段階で落ち、診断が `正準集合外` を含むことを完全一致で固定する。
- 既存 G7 (`test_s8b_oracle_driver.py:2694-2743`) の是正: `historical_bytes` で known generator の
  recorded bytes を stub root へ replay し、`gate_check()` 呼出しの周囲だけ
  `mock.patch.object(driver.s1_known_axes_freeze, "ROOT", root)` を当てる。
  tamper・refusal 4 件・known source mismatch 1 件の期待値は**一字も緩めない**。

## 変異事前登録 (DW-M01)

| ID | 変異 | 期待して赤になる node | 単一理由性 |
|---|---|---|---|
| M1 | `_trigger_entries` の system_gate helper 呼出しを削除 | `test_trigger_entries_rejects_coordinated_noncanonical_system_gate` | 可。synthetic provenance は main/remeasure 一致で、doc 層を呼ばない |
| M2 | 同 ident_all の呼出しを削除 | `..._rejects_coordinated_noncanonical_ident_all` | 可。同上 |
| M3 | `_validate_schema` の 6 値走査を削除 | 検証層負例 2 本 + wiring 1 本 | 可。`_validate_schema` を直接呼ぶため hash・再構成に拒否されない |
| M4 | `_validate_schema` の走査を `system_gate` だけに縮める | 検証層負例のうち ident_all の 1 本 | 可。configuration 別被覆の証拠 |
| M5 | helper 本体を恒真化 (常に return) | M1-M4 の期待 node の和集合 | 可 (理由は「helper が拒否しない」の 1 つ)。call-site 局在は示せないので M1-M4 と併記する |
| M6 | helper を恒偽化 (常に raise) = 過剰拒否 | 正例 1 本 + 既存 freeze consumer 群 | 可。承認外の受理集合縮小を検出する正例側の登録 (DW-M01) |

`test_reflux_ir.py:445-460` は artifact-at-HEAD の pin であり、新 call-site を消しても緑のままなので
kill 判定には登録しない。公開 wiring の 1 本は M3 で殺せるが、単独では generator/source drift でも
赤くなりうるため、診断文言の完全一致を入れて初めて登録対象とする。
