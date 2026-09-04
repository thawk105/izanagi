## must-fix

- **対象 (orchestrator/tests/test_layer3_report.py:3560-3565, 3865-3870)**
  **何が問題か:** 新規作成した genome 不在 record を Layer 3 が拒否せず、系列除外後に正常終了することを2テストが要求している。これは「今後作られる genome 不在 record は拒否する」という D1538 と衝突するテスト側の gate である。S4 が許した「genome 付き」の枝を選べば回避できる。
  **放置時の成果物影響 (1 行):** D1538 準拠実装がこの2テストで拒否され、Pegasus g1 系列だけ未知の genome 不在 record を許す例外を要求して材料レポートの発行可能集合を拡大する。
  **修正の向き:** 両 fixture に canonical な `"genome": "silo|BACK_OFF=0"` を追加し、系列除外・between-run 維持・pin-missing の検出目的だけを残す。

- **対象 (orchestrator/tests/test_layer3_report.py:3469-3510)**
  **何が問題か:** `test_pegasus_v2_adds_only_contract_pin_not_registered_glob` は、系列除外によって登録済み g2 まで `layer3_report.py:580-581` で候補化前に捨てるため、`glob("*.json")` を再帰走査へ壊しても現在の assert がすべて通る。元の「registered glob を採らない」検出力と実装子報告の主張が失われている。
  **放置時の成果物影響 (1 行):** registered 再帰走査への退行が見逃され、非除外の健全 campaign で未 pin record が床値候補へ入り、値の変更または重複一致によるレポート拒否を起こし得る。
  **修正の向き:** 現ケースで `floor["search"]["scanned_files"] == 1` を assert し、g1 pin だけを走査したことを保持する。

## nit

- `orchestrator/campaign/layer3_report.py:25-26` は D1537、exact identity、削除条件を正しく記す一方、「契約 ref が集合に完全一致した campaign の within-run 候補を全て空にする」「samples/tolerance の再検査はしない」を明記していない。定数名は分類集合として妥当で、runtime 検査を行う関数とは読めないが、module contract はやや過少記述。
- `s5-author.md:37-50` の波及列挙は不完全。`orchestrator/campaign/p3_autonomous_workload_trial.py:2844` も `render()` 経由で production の `build_report()` を呼ぶ。関連する `test_p3_autonomous_workload_trial.py` の間接経路も列挙されていない。
- 同報告は、全新規 report の `meta.generator.sha256` が変わる点と、g1 report の within-run `source` が path/hash から `None` へ変わる点を成果物影響として記していない。一方、pytest は明確に未実走と書かれており、未実走を緑とした箇所はない。

## 変異の期待 node

- **M1:**
  `orchestrator/tests/test_layer3_report.py::test_pegasus_v2_adds_only_contract_pin_not_registered_glob`
  `orchestrator/tests/test_layer3_report.py::test_pegasus_g1_direct_copy_does_not_restore_within_run_match`
  `orchestrator/tests/test_layer3_report.py::test_pegasus_g1_series_excludes_direct_within_but_keeps_between`
  `orchestrator/tests/test_layer3_report.py::test_nested_exploration_root_resolves_contract_pin_by_suffix`
  `orchestrator/tests/test_layer3_report.py::test_nested_exploration_root_uses_direct_floor_when_pin_file_is_missing`
- **M2:** M1 の5 nodeに加え、`orchestrator/tests/test_layer3_report.py::test_within_run_exclusion_declaration_matches_real_self_failures`
- **M3:**
  `orchestrator/tests/test_layer3_report.py::test_registered_healthy_pegasus_g2_pin_remains_selectable`
  `orchestrator/tests/test_layer3_report.py::test_within_run_exclusion_declaration_matches_real_self_failures`
- **M4:**
  `orchestrator/tests/test_layer3_report.py::test_pegasus_g1_direct_copy_does_not_restore_within_run_match`
  `orchestrator/tests/test_layer3_report.py::test_pegasus_g1_series_excludes_direct_within_but_keeps_between`
  `orchestrator/tests/test_layer3_report.py::test_nested_exploration_root_uses_direct_floor_when_pin_file_is_missing`
- **M5:** `orchestrator/tests/test_layer3_report.py::test_pegasus_g1_series_excludes_direct_within_but_keeps_between`
- **M6:** `orchestrator/tests/test_layer3_report.py::test_contract_pin_sha_mismatch_fails_closed_before_floor_use`
- **M7:** `orchestrator/tests/test_layer3_report.py::test_nested_exploration_root_uses_direct_floor_when_pin_file_is_missing`
- **M8:**
  `orchestrator/tests/test_layer3_report.py::test_pegasus_v2_adds_only_contract_pin_not_registered_glob`
  `orchestrator/tests/test_layer3_report.py::test_pegasus_g1_series_excludes_direct_within_but_keeps_between`
  `orchestrator/tests/test_layer3_report.py::test_nested_exploration_root_resolves_contract_pin_by_suffix`
  `orchestrator/tests/test_layer3_report.py::test_nested_exploration_root_uses_direct_floor_when_pin_file_is_missing`
- **M9:** 生存

## 正しく実装されていた点

- D1537 と整合する。`layer3_report.py:524-540` は `_validated_pin_path` を先に完遂し、契約の exact `(path, sha256)` だけで系列除外を決める。production に samples/tolerance、`env_attestation`、effective-clock 述語の再実行はない。
- g2 発効後は、新しい g2-pinned campaign の ref が宣言集合に入らないため g2 pin が採られる。既存 g1-pinned campaign は authority が不変なので、発効後も一致なしのままになる。
- D1374 と整合する。除外理由は成果物へ明記され、既存の `genome-absent-legacy-record` 表示も変更していない。
- D1538 の production surface 自体は変更していない。ただし、must-fix に挙げた2 fixture は将来の D1538 実装を妨げる。
- D437 と整合する。g2 正例は private helper への直接入力だけで、activation、世代切替、上位権限束を変更しない。
- D95 と整合する Codex author 完了報告があり、D387 の receipt・偽造耐性面には変更がない。
- 別名 helper、永続 flag、暗黙 default、新 status、共有台帳、複数理由 key は追加されていない。`exclude_within_run` は exact identity から導く局所 bool に留まる。
- `within_run_exclusion` は within-run のみに付く固定文字列 `"self-inconsistent-calibration"` で、待機中世代などの状態を表さない。
- 改訂 `test_pegasus_v2...` は `layer3_report.py:626-629` の理由追加や `:580-581` の除外を壊すと赤になる。ただし registered-glob の旧契約だけは must-fix のとおり未検出。
- 追加 direct-copy テストと系列単位テストは `layer3_report.py:580-581` を path 単位へ狭める、または削除すると赤になる。
- g2 正例は `layer3_report.py:537-540` を全 pin 除外へ広げると赤になり、宣言束縛テストは `:79-81` の path/hash いずれかを壊すと赤になる。
- nested validated テストは `:580-581` の除外を壊すと赤になり、pin-missing 改訂テストは除外条件へ `pin_path is not None` 相当を加えると赤になる。追加・改訂7件に、実装のどの1行を壊しても赤にならない完全な冗長 gate はない。
- 成果物影響は、今後の Pegasus v2 g1 report の within-run 値・source が `None` となり理由が残ること、および全新規 report の generator hash が変わること。certified 選択結果、受理集合、campaign lock、契約 ref、activation は変わらない。既存7 report・dossier・変異台帳を再発行しない方針と矛盾しない。
- 現物差分は `s5-diff.patch` と逐語一致し、指定2 file 以外の変更は含まれていない。

## 総括

最も重い所見は、2つの synthetic genome 不在 fixture が D1538 と反対向きのテスト gate になる点である。
次に、改訂された registered-glob テストが名前と報告に反して旧走査境界を検出できなくなっている。
production の D1537 実装、検証順、系列単位除外、between-run 維持、固定理由 key は裁定どおりである。
親は修正後、全ファイル走に加えて M5・M6・M7 と、registered 走査を再帰化する probe が期待 node だけを赤にすることを実測すべきである。
本レビューは静的検査のみで、pytest の成否は主張しない。