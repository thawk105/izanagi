# [T-492] known 軸凍結の生成・検証層 semantic membership — 逐語と変異台帳

- 対象裁定: 2026-08-05 /rulings、[T-490] U-3 を推奨どおり採用 (択一 (b)) → [T-492] へ分離起票。
- 裁定の正本: `output/insights/2026-08-05_t472-canonical-predicate-consumers.md` §7 U-3。
- branch: `worktree-dev-wave-t492-freeze-semantic-membership`
- 実装 anchor commit: `53b4edd0`
- 本 wave の逐語 (brief / plan / 敵対 2 本 / 実装 / レビュー 2 本 / fix) は同ディレクトリの各ファイル。

## 1. 段 1 前提実測

裁定は「次回 refreeze の前に実装する。今の凍結物は再発行しない」である。検査の呼び出しは
凍結物の generator (`orchestrator/campaign/s1_known_axes_freeze.py`) に足すしかないが、その
sha256 は 3 箇所に pin されている。

- freeze 文書 `output/s1-freeze/known_axes_freeze.json` の `/generator/sha256` = `1d4d45a3…`
- `orchestrator/campaign/t080_freeze_migration.py` の `METADATA_SPECS`
- `orchestrator/tests/test_s8b_oracle_driver.py` の literal

### 実測 A — 現行 6 述語の membership

3 workload × {`system_gate`, `ident_all`} の 6 値はすべて正準かつ **exact** 一致
(`.strip()` 不要)。検査追加で現行 bytes の受理性は変わらない。

### 実測 B — 既存の verify は HEAD で既に赤

`python3 orchestrator/campaign/s1_known_axes_freeze.py verify` は
`orchestrator/campaign/s8a_trigger_sweep.py` の source sha256 不一致で rc=1。
これは T-080 移行 receipt が legitimize している状態で、本番経路は
`s8b_oracle_driver._t080_adapter_refusals` → `static_gate_adapter` が legacy verify を置換する。

### 実測 C — generator を編集したときの影響 (手続きつき)

- 変異: `class FreezeError(RuntimeError):` の直前へコメント 1 行を挿入 (tracked file の一時変異)。
- baseline: `test_s1_known_axes_freeze.py` + `test_t080_freeze_migration.py` = **54 passed**。
- runner: `python3 tools/run_tests.py <7 file> -q` (Pegasus 計算ノードへ dispatch)。
- 対象 7 file: `test_s1_known_axes_freeze.py`, `test_t080_freeze_migration.py`,
  `test_s8b_oracle_driver.py`, `test_frozen_artifacts.py`, `test_s1_measurement_freeze.py`,
  `test_reflux_ir.py`, `test_s8b_oracle_manifest.py`。
- 結果: **1 failed / 222 passed / 1 skipped** (570.67s)。
- 赤 1 本 = `test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7`。
  known-axes leg の期待 refusal が `source sha256 不一致` から `generator sha256 不一致` へ変わり、
  `known_matches == 1` の assert が 0 で落ちた。
- 復元: `git checkout -- orchestrator/campaign/s1_known_axes_freeze.py`、`git status` clean を確認。

**この実測から言えることの限界 (段 3 レンズ A の指摘を採用)。** 言えるのは
「**現行 active な移行 receipt の検証経路は live generator drift を許す**」までである。
`_verify_metadata_closure` は移行基準 commit の blob と比較し、`_verify_reconstruction_static` /
`_without_generator_sha` は `/generator/sha256` を等値比較から除外するためである。
一方 `_verify_worktree_basis_files` は draft / 再発行で worktree bytes 一致を要求するので、
**同じ基準での receipt 再発行はもうできない**。legacy 検証 (measurement / calibration が使う) は
live の generator bytes を直接 hash するため、拒否理由が 1 つ増える (既に別理由で赤のため能力の純減はない)。

## 2. 実装

anchor commit `53b4edd0`。production は `s1_known_axes_freeze.py` の 3 点のみ。

1. `from campaign import trigger_gate_binding` の追加 (循環なし。`pipeline` 経由で従来から
   transitive に読み込まれている)。
2. `_require_canonical_trigger_predicate(predicate, *, workload, configuration)` —
   `is_canonical_predicate` が偽なら `FreezeError`。診断は述語本文を転載せず
   `entries.{workload}.{configuration}.gate_predicate が正準集合外`。
3. 生成層 `_trigger_entries()` の gate / ident 取得直後、および検証層 `_validate_schema()` の
   entry 構造検査直後 (3 workload × 2 configuration の 6 値) で呼ぶ。

### なぜ検証層は `_validate_schema()` なのか

T-080 receipt が active なとき、公開 gate は
`gate_check` → `_t080_adapter_refusals` → `static_gate_adapter` → `_verify_known_schema` →
`known_module._validate_schema()` を通り、**`verify_document` も `build_document` も呼ばない**。
`verify_document` の内側だけに置くと本番経路を素通りする。親 brief の provisional 裁定 (P1)
「生成側 1 箇所で両層を覆える」は段 2 で否定され、親が撤回した。

## 3. 不変条件の是正 (段 6 レンズ R1)

親が段 4 で書いた「`build_document()` の出力を一切変えない」は**不正確**だった。
`generator.sha256` は generator 自身の bytes から作るため、生成器を編集した時点で既定引数の
構築結果はそのセルだけ必ず変わる (`1d4d45a3…` → 新値)。AST 不変・規則不変は値不変の証明にならない。

正しい 2 条件:

1. 凍結済み artifact の bytes を編集せず再発行しない。
2. `generator_sha` を明示して射影した `build_document()` では、受理される入力に対し
   非 metadata field (top-level field、挿入順、entry の name / flags / 述語、`sources` の
   要素数と内容) が完全に不変である。

下流影響: 既存凍結物への legacy `verify_document()` は source mismatch より**先に**
generator mismatch を返す (診断順と文言が変わる)。T-080 active の公開経路は
`/generator/sha256` を静的再構成比較から除外するため certified 選択の値は変わらない。

## 4. 段 6 が見つけた偽 kill (F113 同型再発)

段 6 レンズ R2 が、変異 harness を走らせる**前に** 3 件を検出した。

1. 生成層負例の `_campaign_file` mock が repo 外の相対 `Path("remeasure")` を返しており、
   検査を消す変異では `re_path.relative_to(ROOT)` の `ValueError` で赤くなっていた
   (受理を観測していない偽 kill)。
2. 公開 `generate()` 負例は mock の side_effect 枯渇で別例外になり、
   `assert not output_path.exists()` が「書き込み前に拒否した」証拠になっていなかった。
3. 公開 `verify_document()` wiring 負例は、検査を消しても generator mismatch で赤いままになる
   過剰決定だった。

是正: (1)(2) は mock を repo 内絶対 path へ直し、検査が無ければ `generate()` が実際に
非正準文書を書き切るところまで mock を閉じた。(3) は診断文言の完全一致を入れたうえで、
**kill ではなく診断感度 pin** として扱う (DW-M08)。

## 5. 構造的に到達できない範囲

公開 `driver.gate_check()` の end-to-end では、非正準述語の負例を作れない。
static adapter は known raw bytes が `t080_freeze_migration.KNOWN_AXES_RAW_SHA256` と
一致することを先に要求するため、文書を改竄すると別の refusal
(`known_axes raw bytes が legacy pin と不一致`) になる。この定数を monkeypatch して
端から端まで通ったように見せることはしなかった。負例は
`static_gate_adapter` → `_verify_known_schema` → `_validate_schema` へ到達する層で固定した
(`test_t080_static_adapter_rejects_noncanonical_known_predicate_as_schema`)。

## 6. 変異台帳

spec は `mutation-spec.json` (是正版、sha256 `10792681…`)、台帳は `mutation-ledger-v2.json`。
初回登録と初回結果は `mutation-spec-v1-erratum.json` / `mutation-ledger-v1-erratum.json` に残す。

### 本走 (是正版) — baseline PASSED、6/6 KILLED、node 集合完全一致、SURVIVED 0

repo_head = `53b4edd0d213e2ce37c9b767793eb2b0726a3f3b`。

| ID | 変異 | 期待 = 実測 node 数 | 結果 |
|---|---|---|---|
| M1 | 生成層 system_gate の検査呼出しを削除 | 2 | KILLED |
| M2 | 生成層 ident_all の検査呼出しを削除 | 1 | KILLED |
| M3 | 検証層の 6 値走査を削除 | 4 | KILLED |
| M4 | 検証層の走査を system_gate だけに縮小 | 1 | KILLED |
| M5 | helper 本体を恒真化 (常に return) | 7 | KILLED |
| M6 | helper を恒偽化 (常に raise) = 過剰拒否の正例 | 5 | KILLED |

### erratum — 初回走行の M6 は MISMATCH

初回の M6 事前登録は期待 node を 2 件 (現行 6 値の正例と G7) としたが、実測は 5 件だった。
差分の 3 件は
`test_validate_schema_rejects_noncanonical_system_gate` /
`..._ident_all` /
`test_trigger_entries_rejects_coordinated_noncanonical_ident_all`。

原因は登録側にある。負例は診断文言を**別 workload / 別 configuration まで含めて完全一致**で
固定しているが、helper を恒偽化すると走査の**最初の値** (`entries.balanced.system_gate`) で
必ず落ちるため、期待文言と実際の文言がずれて赤くなる。検査側の欠陥ではない。
初回は M1〜M5 が KILLED、M6 のみ MISMATCH で harness が fail-closed した
(`mutation-ledger-v1-erratum.json`)。登録を是正して全走をやり直し、6/6 KILLED を得た。

## 7. 受入

`python3 tools/run_tests.py -q -rf` を 2 回実走した。

- merge commit `f675df66` (local main `ea83d322` 取り込み後): **6348 passed / 20 skipped** (671.09s)。
- land 直前の merge commit `50cfad5e` (local main `b0a49f0a` 取り込み後): **6420 passed /
  20 skipped** (953.36s)。取り込んだ 6 commit に別 wave の production 変更が含まれるため取り直した。

どちらも赤なし。

段 6 の対象走行 (freeze 系 8 test file) は fix 前 **278 passed / 1 skipped**、
fix 後 **279 passed / 1 skipped** (adapter 層の意味負例 1 本が純増)。

## 8. scope 外と裁定した real 所見 (裁定パッケージ)

いずれも本 wave では実装していない。詳細な根拠は `lensA-out.md` / `lensB-out.md` /
`reviewR1-out.md` / `reviewR2-out.md` に逐語で残す。

1. **次回 refreeze の世代移行 (P1)** — 「semantic membership を入れれば次回 refreeze ができる」は偽。
   再凍結は known raw hash と `/generator/sha256` を変え、旧 raw hash を定数固定している
   T-080 receipt を必ず無効化する。measurement / holdout / manifest / ratified も known raw を
   記録するため、known 単独でも一括でも旧 receipt と不整合になる。旧定数の上書きは過去 receipt の
   意味を後から変えるので採れない。新世代 artifact と transition receipt / trust root 更新が要る。
2. **trigger の name↔mask 束縛 (P1)** — 32 集合内であれば、`name` が指す mask と述語本文の mask が
   食い違っても両 provenance を揃えれば通る。誤 certification まで到達しうる。
3. **holdout 凍結の意味閉包 (P2)** — holdout は known 文書を直接読んで 6 構成を無検査で複製する。
   正規 producer 経由なら今回の生成側検査で守られるが、別途発行された非正準 known 文書を
   直接与えると holdout 単体では受理される。
4. **membership 権威の proof chain 帰属 (P2)** — 権威モジュールが trigger entry の source 記録に
   無く、`selection_rules` も membership 規則を記述しない。是正はいずれも文書構築の出力を
   変えるため、1 の世代移行と同時に裁定する。
