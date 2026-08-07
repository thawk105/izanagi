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

### {{F:fix-narrowed-acceptance-without-positive-control}}. 段 6 fix が受理集合を縮小したのに正例を登録せず、正当な入力を恒久拒否する退行が緑のまま通りかけた [恒真ゲート] [テスト代表性]

- 事象: 段 6 の fix が、収集 artifact の保存先検査を「祖先に `.git` があれば拒否」へ変えた。
  拒否側のテストだけを足したため全テストが緑になったが、**正当な保存先も拒否**していた。
  実際の保存先 directory には過去の job が残した中身が空の `.git` directory があり、
  repository ではないのにそう判定されていた。この状態で land していれば、
  収集は非 gate なので黙って rc=0 を返し続け、**全 wave で artifact が 1 件も作られない**。
- 根本原因: `DW-M01` は「受理集合を縮小する wave では、承認外の過剰拒否を検出する正例も登録する」と
  定めるが、この義務は**段 4 の変異事前登録の文脈で書かれている**。受理集合の縮小が段 6 の fix で
  初めて生じた場合、事前登録は既に確定しており、正例登録の義務が再発火しない。
- 検出できた理由: 親が fix の前後で同じ probe を走らせ、拒否側だけでなく**受理されるべき path も
  一緒に確認**していた。fix 子の自己申告とテストの緑は、いずれもこの退行を示さなかった。
- 恒久対応: 段 6 の fix が受理集合を縮小したら `DW-M01` の正例登録を再適用する。
  具体の正例は `orchestrator/tests/test_collect_wave_usage.py::test_output_below_empty_git_directory_is_accepted`
  で、変異事前登録では扱わずテストで固定した。
  **`DW-S06-B` への明文化は `docs/dev-wave/**` の byte hard ceiling (25,200) に
  4 bytes しか空きがなく入らない。** F146 と同じく本エントリを恒久対応の所在とし、
  空きが出たときに `DW-S06-B` へ 1 文で統合する。
- 再発検知: 受理集合を縮小する fix の前後で、拒否側と受理側の両方を同じ probe に通す。
