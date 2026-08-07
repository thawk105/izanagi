---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-t598-forward-collection
seq: 3
---

## 新規

### {{F:ai-ran-classification-measurement}}. AI が実行場所分類の測定手番を自分で実行した [権限逸脱] [計測汚染]

- 事象: 親が `tools/claude_session_ledger.py` の資源量を 2 通りで測った。まず
  `/usr/bin/time -v` の単一 process RSS で 143.7 MiB、次に runbook §7.0 の正規手順
  (専用 scope を作って `memory.current` を sampling、3 回) で 140.0 MiB。
  後者を根拠に certified peak 268.0 MiB < 規範値 512 MiB を導き、`local-ok` と暫定裁定した。
- 根本原因: 同節は「**AI セッション・子エージェント・自動化は分類の実測を自分で行わない**」
  「hook が未配線または解析できない実行面を測定の抜け道に使うことも同じく禁止」と明記しているが、
  親は資源量の判定基準 (規範値・certified peak の計算) だけを読んで手番の帰属を読み落とした。
  正規手順の記述がそのまま実行可能だったことが、実行してよいという誤読を強めた。
- 恒久対応: {{D:wave-usage-selector-and-siting}} 決定 4 — 収集 tool 自身が、
  ログインノードと判定された場合と判定の証拠が得られない場合の双方で collector を呼ばず
  `blocked` を記録する。`orchestrator/tests/test_collect_wave_usage.py` の
  `test_unclassified_site_is_blocked_without_calling_collector` と
  `test_collector_site_classification_fails_closed_without_evidence` が、
  collector 呼出し回数 0 を直接固定する。
- 再発検知: 上記 2 node と、変異事前登録 M7 (fail-closed 分岐の除去) の KILLED。

### {{F:unclassified-tool-on-login-node}}. 未分類 tool をログインノードで走らせた [権限逸脱]

- 事象: 親が段 1 の実測で `tools/claude_session_ledger.py` を pegasus02 上で 6 回実行した。
  最大で 128 file・291.2 MB を走査した。
- 根本原因: 同 tool は実行場所の分類を持たない。規範は「`unknown` は `dispatch-required` と
  同じに扱う」「`dispatch-required` をログインノードで走らせない」と定める。
  hook の admission registry は `tools/pegasus/` 配下だけを見るため機械的には止まらず、
  規律だけが防壁だった。親はその防壁を通らずに実行した。
- **独立 2 例**: 前 wave (2026-08-07 の [T-598] 結線先裁定 wave) も同じ tool を同じ面で
  複数回実行しており、異なるセッションでの独立再現である。
- 恒久対応: {{D:wave-usage-selector-and-siting}} 決定 4 の fail-closed を、
  この tool を呼ぶ唯一の production consumer へ入れた。consumer 経由の実行はこれで機械的に止まる。
  **collector を直接叩く経路は依然として規律だけが防壁であり、分類そのものはユーザー手番として
  未了である。** 分類が済むまで前向き収集は `blocked` を記録し続ける。
- 再発検知: 上記 2 node。分類の完了自体は台帳側の手番であり、本 wave では閉じていない。
