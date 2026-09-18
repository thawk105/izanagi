# 段 4 裁定 — [T-2732] verifier の残り 3 file (`__init__.py` / `report.py` / `commit_receipt.py`) を T126 code identity へ加える (40 → 43)

裁定 inbox 再走査 (06:35 JST): `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/` に T-2732 の追加裁定なし (最新 2026-09-17-k2-loop-round2-authorization.md は無関係)。
裁定の正本は `docs/decisions.md` D2120 項 6 (逐語 `verbatim-d2120-item6.md`)。main は base d2ebef7a4 から前進なし (06:44 JST 再確認)。
段 3 の 2 レンズは実装 must-fix 0。訂正は説明範囲に限られる。

## 所見の裁定 (real / refuted、採否、scope)

| ID | 判定 | 採否 | 処置 |
|---|---|---|---|
| A1 3 path 追加 + 独立包含 test 1 本は裁定を満たす。(P1) 新規 1 本 + 既存 4 file test 据え置きは妥当。包含 test は「集合からの脱落検出」であって verifier の判定能力ではない | real | 採用 | plan v2 を確定。記録では包含 test の証明範囲を限定して書く |
| A2 (P3) は先例どおり成立。旧 40-key 形の拒否は `contract.py:533-537` の required set 検査が blob 照合より前 (driver :1437 → :1644-1646 → CLI :1679 rc=2、collector :1487 → :1880-1883 invalid、identity.py:124 → :140 に到達しない) | real | 採用 (記述) | 記録に経路を写す。互換層は作らない。規律 7 により過去測定の無効化に使わない |
| A3 「意味論不変」は identity まで含められない。`t126_driver.py:376-384` の `identity code file missing` / `differs from HEAD` が新たに 3 file へ適用される (正しい向きの fail-closed) | real | 採用 (記述) | I2 を「verifier の trace 判定意味論と `series_identity()` / `verify_recorded_series_identity()` / `_identity_files()` の検証ロジックは不変。identity の受理形 (exact key set) と driver の照合対象は変わる」に改める |
| A4 先例以降 (c09211d17..d2ebef7a4、397 commit、JSON 206 blob) の committed JSON に `code_identity` key 0 件。schema 文字列の出現は contract.py:496 / t126_driver.py:423 / test 2 file。不在主張は調査範囲に限定 | real | 採用 (記述) | 「調査した committed JSON・consumer に修正対象なし。repo 外の旧成果物の存在・利用は未確認」と限定。schema 名据え置きを互換性と説明しない |
| A5 / B4 brief「verifier package 全 7 file」は誤り。tracked は 9 file、追加後は 9 中 7 の個別束縛 | real | 採用 (brief 訂正) | 「verifier の個別束縛を 4 → 7 file に広げる。`__main__.py` / `cli.py` は集合外」に訂正 |
| A6 / B5 brief (P4)「script は path 名を列挙しない」は誤り。submit script :124-134 の 5 path tracked 検査、:149-164 の 7 path disk/blob 照合、t126_qualification.sh:790-802 の固定列挙がある。いずれも required code 集合の複製ではなく件数依存なし | real | 採用 (brief 訂正、script 変更なし) | 「required code 集合を独立に全列挙していない」に訂正。script の変更は足さない |
| A7 Codex 子木 dirt の観測は編集競合評価に限る。「無害」「互換性の証拠」へ一般化しない | real | 採用 (記述) | 「親の観測時点 (06:2x JST) では今回の編集面に未着地の競合を認めなかった」に限定 |
| A8 / B2 brief「焦点走 4 file に drift gate は無い」「campaign_lock 系 test は drift 赤」は過大。実 repo live loader 比較 (`contract_loader_binding.py:526-529`) を持つ test は 11 file の import 元のうち live capture を行う経路 (例 test_p3_b4_raw_record_producer.py:110-112) だけ。焦点走 4 file に当該 import / live capture は無い | real | 採用 (記述 + 実走) | 「実 repo の live loader binding を取得する経路は未 commit 差分で拒否される。焦点走 4 file にはその経路が無い (静的)」に限定し、今回の checkout で焦点走を実走して確認する。先例成功を代用しない |
| A9 `__main__.py` / `cli.py` は確認した T126 経路 (t126_qualification.sh:835 → driver run → pipeline.evaluate → `verify_trace_dir_with_capability`、collector → artifacts.py:24 receipt API) から到達されない。`verifier/__init__.py` は CLI を import しない | real | 採用 | 裁定パッケージは立てない。記録に「集合外の CLI 入口 2 file、T126 経路から到達されず」と事実だけ書く。本 wave にも追加しない (依頼の「本題の 3 path 追加だけ」) |
| B1 「6 file・24 行」は production / test の直接出現に限定。docs archive 5 / decisions 3 行、output/ 45 file は歴史記録。間接 consumer に collector.py:358/473/1168/1487/1515、artifacts.py:1291 (契約関数経由で追随) | real | 採用 (記述) | 記録の consumer 節に限定と補記。歴史記録の件数は書き換えない |
| B3 `_attempt` fixture (:980-982 mkdir parents exist_ok、:1025 generic 書込、:1050-1051 commit、:1085-1088 blob hash) は追加対応不要。basename 重複は衝突しない | real | 採用 | plan 維持 |
| B6 DW-O10 非適用、件数 (40/3/43 → 43/3/46)、anchor、変更前 hash は支持。worktree/process 走査は時点付き実測 | real | 採用 | A7 と同じ限定 |
| B7 変異 N1〜N5 は既存 test 単独では検出されず新 test だけが赤 ({V})、E1 SURVIVED。`cli.py` は tracked (100644、blob 3c600cb4) かつ集合外。anchor は実装後に各 1 回 | real | 採用 | 下の事前登録どおり。実装後 baseline で V の collection と全 `old` の一意性を確認 (DW-M07 の再照合) |
| B8 焦点走・変異は 4 file で足りる。受入全走は縮めない。runner に `--force-dispatch` を明記 | real | 採用 (手順) | 焦点走 = 4 file dispatch、変異 runner argv に `--force-dispatch`、受入は commit 後の通常全走 |

refuted: 0 件。scope 外の real 所見で裁定パッケージへ送るもの: 0 件 (A9 により CLI 2 file は「穴」に当たらない)。

## 実装方向 (plan v2、段 2 plan を確定)

1. `orchestrator/qualification/contract.py`: `:78 "orchestrator/verifier/parse.py",` の直後 (`:79 "tools/pegasus/policy.json",` の前) に次の 3 行を逐語で追加 (順序もこの通り、4 space indent、各行末 comma):
   ```
       "orchestrator/verifier/__init__.py",
       "orchestrator/verifier/commit_receipt.py",
       "orchestrator/verifier/report.py",
   ```
2. `orchestrator/tests/test_t126_pegasus_tools.py`: `test_required_code_identity_includes_verifier_core_dsg_model_parse` の関数本体 (`:1531`) の直後
   (`test_series_preimage_exact_code_identity_set_tracks_activation_closure` の前、既存の空行 2 行の慣行に合わせる) に次の独立 test を逐語で追加:
   ```
   def test_required_code_identity_includes_verifier_init_report_commit_receipt():
       assert "orchestrator/verifier/__init__.py" in REQUIRED_CODE_IDENTITY_PATHS
       assert "orchestrator/verifier/report.py" in REQUIRED_CODE_IDENTITY_PATHS
       assert "orchestrator/verifier/commit_receipt.py" in REQUIRED_CODE_IDENTITY_PATHS
   ```
   import 追加なし (`:704` で既に import 済み)。docstring・comment は付けない (親が等価変異の anchor に def 行を使う)。他の file・行は変更しない。
3. 通る正例: 変更後の `REQUIRED_CODE_IDENTITY_PATHS` (43 path、和集合 46) で上の test が緑、`test_every_required_identity_path_is_tracked_in_this_repo` は 46 node 緑、
   `test_series_preimage_exact_code_identity_set_tracks_activation_closure` の exact set 比較が緑。拒否の含意: 旧 40-key 形の series-identity は `series identity code_identity required set mismatch` で不受理 (歴史記録は据え置き)。
4. scope 外 (実装しない): `__main__.py` / `cli.py` の追加、census gate、歴史成果物の互換層・二重受理、`schema_version` / hash domain / `series_identity()` ロジック /
   `REQUIRED_SCRIPT_IDENTITY_PATHS` / campaign_lock 閉包 / 凍結 manifest / script の変更、docs archive の件数書き換え。

## 変異事前登録 (DW-M01、実装前に登録)

対象 = 実装 commit 後の `contract.py` と `test_t126_pegasus_tools.py` の tracked 行。harness = `tools/mutation_harness.py` (spec は job dir `mutation-spec-main.json`、
`--runner-mode dispatch`、runner argv = `python3 tools/run_tests.py <4 file> -q -rf --force-dispatch`)。
V = `orchestrator/tests/test_t126_pegasus_tools.py::test_required_code_identity_includes_verifier_init_report_commit_receipt`。

| ID | category | 変異 (contract.py の tracked 行、anchor は 2 行 context) | code 件数 | 期待 node (完全集合) | 期待 |
|---|---|---|---:|---|---|
| N1 | negative | `"orchestrator/verifier/__init__.py",` 行を削除 | 42 | V | KILLED |
| N2 | negative | `"orchestrator/verifier/report.py",` 行を削除 | 42 | V | KILLED |
| N3 | negative | `"orchestrator/verifier/commit_receipt.py",` 行を削除 | 42 | V | KILLED |
| N4 | negative | `"orchestrator/verifier/report.py",` → `"orchestrator/verifier/cli.py",` (tracked 兄弟、件数維持) | 43 | V | KILLED |
| N5 | negative | `"orchestrator/verifier/commit_receipt.py",` → `"orchestrator/verifier/core.py",` (frozenset 重複) | 42 | V | KILLED |
| E1 | positive | test file: V の def 行直後に `    # T-2732 verifier identity coverage.` を挿入 | 43 | (空) | SURVIVED |

単一理由性: N1〜N5 は集合由来の既存 test (fixture・parameter・等価比較) が追随するため V だけが赤になる (新規検出力)。N4 では変異下だけの parametrize node
`test_every_required_identity_path_is_tracked_in_this_repo[orchestrator/verifier/cli.py]` が現れるが緑のはずで、期待 node に登録しない (先例 erratum: 変異下でしか生まれない node は
harness の baseline collection 検査で中止)。存在しない path への置換は登録しない。test 反転 (production 検出の証拠にならない) は登録しない。
E1 を test 側へ置く理由: contract.py は loader 閉包 member で comment 変更でも bytes が変わるため。
走行手順: (1) 実装 commit 後に spec の anchor を再照合 (各 `old` が contract.py にちょうど 1 回、DW-M07)、(2) 本走を上の期待で登録して走らせる (先例は probe を省略し本走のみ。
根拠 = 未 commit の contract.py で焦点走が緑 → この 4 file に HEAD blob 比較の drift gate は無い、を本 wave でも焦点走で実測してから)。契約上の hang risk なし。

## 裁定パッケージ (ユーザーへ返す)

- なし。A9 のとおり `__main__.py` / `cli.py` は T126 経路から到達されない CLI 入口であり、D2091 却下欄が本 wave の 3 file に付けた「実行依存が残る」所見は転用できない。
  事実 (集合外 2 file、到達経路なし) だけを記録に残す。
