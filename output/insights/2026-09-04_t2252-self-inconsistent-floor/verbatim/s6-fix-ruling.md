# 段 6 fix 裁定 — [T-2252]

レビュー A: must-fix 無し、nit 1 (g2 正例は実装を空にしても緑 = 過剰除外を検出する正例なので想定どおり、対応不要)。
レビュー B: must-fix 2、nit 3。親の裁定は次のとおり。

| # | 所見 | 性質 | 採否 | fix の内容 |
|---|---|---|---|---|
| F1 | 新 fixture 2 つ (`test_pegasus_g1_series_excludes_direct_within_but_keeps_between` の `within.json`、`test_nested_exploration_root_uses_direct_floor_when_pin_file_is_missing` の `within.json`) が genome 不在の within record を使い、D1538 (今後作られる genome 不在 record は層 3 で拒否) の実装と逆向きのテスト gate になる | real | 採用 | 両 `within.json` に canonical な `"genome": "silo|BACK_OFF=0"` を足す (同 file の between fixture と同じ形)。検出目的 (系列単位除外・between_run 維持・pin-missing でも除外) は不変。protocol_match_basis の assert は足さない |
| F2 | 改訂した `test_pegasus_v2_adds_only_contract_pin_not_registered_glob` は、除外が候補化前に効くため `glob("*.json")` を再帰走査へ壊しても緑のまま。旧契約「registered glob を採らない」の検出力を失った | real | 採用 | 同テストに `floor["search"]["scanned_files"] == 1` (走査したのは g1 pin だけ) を assert する。他の assert は変えない |
| N1 | module docstring が「契約 ref が集合に完全一致した campaign の within-run 候補を全て空にする」「samples/tolerance の再検査はしない」を明記していない | nit | 採用 (docs 文のみ) | `layer3_report.py` の module docstring の D1537 の段落に、その 2 点を 1〜2 文で足す。code は触らない |
| N2 | 波及列挙に `p3_autonomous_workload_trial.py` (render 経由) と `test_p3_autonomous_workload_trial.py` の間接経路が無い | nit | 記録 | 親の焦点走 2 に `test_p3_autonomous_workload_trial.py` を加える。fix 不要 |
| N3 | 実装子報告が generator hash の変化と g1 report の source None 化を成果物影響として書いていない | nit | 記録 | 段 4 裁定と commit message に既に記載。fix 不要 |

production の挙動は 1 bit も変えない (docstring のみ)。したがって変異 spec の anchor は不変のはずだが、
DW-M07 に従い fix 後の最終 commit で anchor と期待 node を再検証してから本走する。
