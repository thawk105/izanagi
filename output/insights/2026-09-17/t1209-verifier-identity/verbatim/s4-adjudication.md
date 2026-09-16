# 段 4 裁定 — [T-1209] verifier dsg/model/parse を T126 code identity へ含める

裁定 inbox 再走査 (01:0x JST): `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-17-rulings-full5-36rulings.md` #20 が
「裁定 = 含める。条件 = 過去の qualification 成果物は歴史記録として据え置き、以後の取得から新 identity を適用」を持つ。wave 開始後の更新なし。
main は base 1042a1bc9 から前進なし。

## 所見の裁定 (real / refuted、採否、scope)

| ID | 判定 | 採否 | 処置 |
|---|---|---|---|
| A1 旧成果物は現行 verify で `required set mismatch` → invalid (driver verify rc=2 / collector invalid) になる。「歴史記録として据え置き」と「現行契約への適合」を分けて書け | real | 採用 (記述) | 記録 (worklog/insight/decisions) に「bytes と当時の判定は保持、現行 verify は旧 37-key 形を受理しない、これを過去測定の無効化に使わない (規律 7)」を明記。互換層は作らない (P2 維持) |
| A2 「検証意味論に触れない」は対象限定が要る。identity の受理形は 37-key → 40-key へ置換される | real | 採用 (記述) | I2 を「verifier の trace 判定意味論と `series_identity()` の検証ロジックは不変。定数変更で identity の受理形 (exact key set) と driver の disk/blob 照合対象が変わる」に改める |
| A3 DW-O13 は test 単体で終えず production 側の exact 述語も評価せよ | real (部分) | 採用 (評価済み) | DW-O13 の要件を実測で満たす: 入力 field = series-identity.json の `code_identity` (t126_driver `_identity_files` が生成)、値の到達可能性 = 3 path は `git ls-files --error-unmatch` rc=0 で tracked、driver は HEAD blob と disk hash を照合して格納する。受理形は 1 形 (exact set) のまま置換であり、受理形の「増加」ではない。新規 gate は作らない |
| A4 「壊れる既存成果物なし」「live 未実施」は実測範囲を超える一般化 | real | 採用 (記述) | 「tracked JSON に `code_identity` key 0 件。phase3.md:1313 は live qualification を scope 外と記すのみ。repo 外の旧成果物の存在・利用は未確認」に限定 |
| A5 path pin の記述限定 (test の独立列挙は不変 path、schema 文字列据え置きは互換性を意味しない) | real | 採用 (記述) | 記録の pin 節に反映 |
| A6/B4 「series identity が反応しない」は強すぎる (commit/tree 経由では変わる)。contract.py の自己包含、campaign_lock.py:204 は歴史 exact62 側 | real | 採用 (記述) | 「3 file は個別 code hash と `_identity_files()` の disk/blob 照合の対象外」に限定。pin 棚卸しは T126 自己包含 / 現行 loader 閉包 (:107) / 歴史 exact62 (:204) を区別 |
| A7 `__init__.py` / `report.py` / `commit_receipt.py` は実行依存が残るが 3 file 限定は裁定の範囲内 | real | scope 外 → 裁定パッケージ | 実装しない。ユーザーへ「T126 でも直接束縛するか」を別件で返す (下記) |
| B1 consumer 棚卸しの補完 (docs 参照 5 箇所、submit script :149 の 7 path 列挙、submission.py:216 入口、t126_qualification.sh:787) | real | 採用 (記録) | いずれも identity 全集合の複製でなく修正不要。記録に「確認済み・修正不要」で列挙 |
| B2 `_dependency` / `_prologue_value` (test_t126_qualification_driver.py:98-114、code_identity 3 key 固定の部分 fixture) の棚卸し | real | 採用 (記録 + 実走で確認) | 段 5 後の焦点走に test_t126_qualification_driver.py を含めて緑を実測 |
| B3 新包含 test と T126 焦点走は commit 前に実施可、実 repo loader 比較を含む受入は commit 後 | real | 採用 (手順) | 段 5 後: 焦点走 (4 file) → 統合 commit → 段 6 → 変異 → 受入 |
| B5 件数 (37→40、和 40→43) 支持、不在証拠の限定、P4・DW-O10 非適用維持 | real | 採用 | A4 と同じ限定 |
| B6 変異 N1〜N6 有効、N7 は test 反転の確認で production 検出の証拠でない、E1 は等価対照 | real | 採用 | matrix は N1〜N6 (negative/KILLED) + E1 (positive/SURVIVED)。N7 は登録しない (単一理由性、DW-M03) |

## 実装方向 (plan v2、段 2 plan を確定)

1. `orchestrator/qualification/contract.py`: `:75 "orchestrator/verifier/core.py",` の直後に次の 3 行を逐語で追加 (順序もこの通り):
   ```
       "orchestrator/verifier/dsg.py",
       "orchestrator/verifier/model.py",
       "orchestrator/verifier/parse.py",
   ```
2. `orchestrator/tests/test_t126_pegasus_tools.py`: `test_required_code_identity_closes_activation_receipt_imports_without_records` の直後
   (`:1524` の後、`test_series_preimage_exact_code_identity_set_tracks_activation_closure` の前) に次の独立 test を逐語で追加:
   ```
   def test_required_code_identity_includes_verifier_core_dsg_model_parse():
       assert "orchestrator/verifier/core.py" in REQUIRED_CODE_IDENTITY_PATHS
       assert "orchestrator/verifier/dsg.py" in REQUIRED_CODE_IDENTITY_PATHS
       assert "orchestrator/verifier/model.py" in REQUIRED_CODE_IDENTITY_PATHS
       assert "orchestrator/verifier/parse.py" in REQUIRED_CODE_IDENTITY_PATHS
   ```
   import 追加なし。他の file・行は変更しない。
3. 通る正例: 変更後の `REQUIRED_CODE_IDENTITY_PATHS` (40 path) で上の test が緑、`test_every_required_identity_path_is_tracked_in_this_repo` は 43 node 緑。
4. scope 外 (実装しない): `verifier/__init__.py` / `report.py` / `commit_receipt.py` の追加、census gate、歴史成果物の互換層、`schema_version` / hash domain /
   `series_identity()` ロジック / `REQUIRED_SCRIPT_IDENTITY_PATHS` / campaign_lock 閉包 / 凍結 manifest の変更、docs の件数書き換え。

## 変異事前登録 (DW-M01、実装前に登録)

対象 = 実装 commit 後の `contract.py` と `test_t126_pegasus_tools.py` の tracked 行。harness = `tools/mutation_harness.py` (spec は job dir、`--runner-mode dispatch`、
runner argv に `--force-dispatch` と `-rf`)。V = `orchestrator/tests/test_t126_pegasus_tools.py::test_required_code_identity_includes_verifier_core_dsg_model_parse`、
P[x] = `orchestrator/tests/test_t126_pegasus_tools.py::test_every_required_identity_path_is_tracked_in_this_repo[x]`。

| ID | category | 変異 (contract.py の tracked 行) | 期待 node (完全集合) | 期待 |
|---|---|---|---|---|
| N1 | negative | `"orchestrator/verifier/dsg.py",` 行を削除 | V | KILLED |
| N2 | negative | `"orchestrator/verifier/model.py",` 行を削除 | V | KILLED |
| N3 | negative | `"orchestrator/verifier/parse.py",` 行を削除 | V | KILLED |
| N4 | negative | `"orchestrator/verifier/core.py",` 行を削除 | V | KILLED |
| N5 | negative | `"orchestrator/verifier/parse.py"` → `"orchestrator/verifier/pars.py"` (空白を含めない綴り違い) | V、P[orchestrator/verifier/pars.py] | KILLED |
| N6 | negative | `"orchestrator/verifier/model.py",` 行を `"orchestrator/verifier/core.py",` に置換 (frozenset 重複で 39 件) | V | KILLED |
| E1 | positive | test file: V の def 行直後に `    # T-1209 verifier identity coverage.` を挿入 | (空) | SURVIVED |

単一理由性: N1〜N4/N6 は集合由来の既存 test (fixture・parameter・等価比較) が追随するため V だけが赤になる (新規検出力)。N5 は既存 P[pars.py] も赤になる (冗長 gate、
新規検出力には V の分のみ数える)。E1 を test 側へ置く理由: contract.py は loader 閉包 member で comment 変更でも bytes が変わり drift 赤を生むため。
走行手順: (1) 実装 commit 後に spec の anchor を再照合 (DW-M07)、(2) probe 走 (全件 SURVIVED 期待) で観測 node を集め、(3) 本走を上の期待で登録して走らせる。
契約上の hang risk なし。runner の test 選択は段 5 後の焦点走 baseline の所要で決める (候補: 4 file 全体、または B6 の `-k`)。

## 裁定パッケージ (ユーザーへ返す、実装しない)

- **[T-1209 派生] T126 code identity に `orchestrator/verifier/__init__.py` / `report.py` / `commit_receipt.py` を直接束縛するか。**
  現状: pipeline.py:39 は `from ..verifier import` (dispatch 面)、core.py:256/264 は `result_to_dict` / `_domain_digest`、qualification/artifacts.py:855 は `validate_live_receipt`
  に依存し、いずれも T126 の個別 code hash と `_identity_files()` の disk/blob 照合の対象外に残る (superproject commit/tree と兄弟 loader 閉包 D473 では束縛済み)。
  本 wave は裁定逐語 (dsg/model/parse) と依頼の「本題の identity 集合だけ」に従い追加しない。択: (a) 3 file を足す (D473 と対称) / (b) 足さない (commit/tree 束縛で足りる)。
