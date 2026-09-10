# 段 6 review 裁定 — [T-2048]

## 所見裁定

- review A F-01「説明変異の static oracle 欠落」は **real / must-fix / scope 内**として採用した。
  D95 fix worker が既存 `test_pegasus_floor_tools.py` に floor 専用の 2 node を追加し、production calculator
  から導出した値と shell / README のラベル付き関係を照合する。一般 framework・schema は追加していない。
- review B の must-fix は 0。D87 の歴史 bytes、policy、calculator、protocol、freeze は無変更で、
  shell hunk は D95 author patch と byte 一致するという結論を採用した。
- focus review は F-01 を **closed（静的）**、partial/regressed なしと判定した。28200 subtotal の正例を
  通し、M1/M2 は shell node、M3 は README nodeへ単一理由で帰属する。

## 未実走境界

fix worker の `tools/run_tests.py` は qstat preflight failure で rc=16、child test 0 件だった。
これは緑ではない。親が統合 commit 後に同 runner と mutation harness を正規経路で再投入し、
baseline / KILLED / acceptance を実測する。

## 実装 scope

- implementation: `tools/pegasus/floor_campaign.sh` のコメント、
  `orchestrator/tests/test_pegasus_floor_tools.py` の focused oracle（D95 Codex author / fix）。
- docs: `tools/pegasus/README.md` §5 と wave insight（親）。
- 変更しない: scheduler 36000、calculator 30000 + 600、policy、protocol、freeze、D87、official guard。
