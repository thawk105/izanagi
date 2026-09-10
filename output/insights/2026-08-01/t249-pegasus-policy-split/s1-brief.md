# 段 1 brief — [T-249] 共有 Pegasus policy のタスク別 file 再編

## 確定済みユーザー裁定 (worklog (94))

択 (b) 採用 — 共有 Pegasus policy をタスク別 file へ再編する。**凍結証拠の意味論には手を入れない。**
分散する設定は**索引 1 つ**で辿れるようにする。(a) binding 設計の見直しは却下済み。

## 前提の実測 (親、本 worktree、`DW-O19` の復元規律で実施)

- `tools/pegasus/policy.json` の現行 sha256 = `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac`。
  T-139 の committed evidence `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` の
  `binding.policy.sha256` と**一致**。凍結 pin は生きている。
- 実編集 (top-level に無害な 1 key 追加) → Pegasus 計算ノード request `876519` で
  **赤はちょうど 2 node**、392 passed:
  `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head`
  (`orchestrator/tests/test_silo_ladder_rung1_evidence.py`) と
  `test_shared_pegasus_policy_owns_no_t126_qualification_keys`
  (`orchestrator/tests/test_t126_pegasus_tools.py:1247`)。両者とも同じ sha256 等値 assert。
  編集は即復元し bytes 一致を確認済み (tree clean)。
- committed な T-126 qualification receipt は存在しない (`output/env/pegasus/qualification` 不在)。
  よって policy.json bytes を pin する **committed 証拠は T-139 の 1 件だけ**。
  ただし `tools/pegasus/policy.json` は `contract.REQUIRED_CODE_IDENTITY_PATHS` の member であり、
  T-126 の series identity preimage に hash が入る (= bytes 変更は series id を変える)。
- 既存の per-task file 先例は `orchestrator/qualification/t126_reservation_policy_v1.json` (D107 決定 1)。
- live な読み手 (shell): `certify_calibration.sh`, `floor_campaign.sh`, `submit_floor.sh`,
  `submit_certify.sh`, `silo_ladder_rung1.sh`, `submit_silo_ladder_rung1.sh`,
  `t126_qualification.sh`, `submit_t126_qualification.sh`, `t141_region_profile.sh`。
  live な読み手 (py): `orchestrator/campaign/silo_ladder_rung1.py`,
  `orchestrator/qualification/{submission,identity,collector,t126_driver}.py`。

## scope (親の provisional 裁定 = 攻撃対象)

- **(P1)** `tools/pegasus/policy.json` の **bytes は不変**とする。key の追加も削除も整形も行わない。
  裁定文の「再編」は file の書換えではなく、**設定の所在と読み手の付け替え**として実装する。
  実装しない場合の成果物影響: 次に Pegasus 設定を触るタスクが共有 policy を編集し、T-139 の
  certified 証拠の `binding.policy` が drift して受入全走が赤になる (実測 request `876519`)。
  それを避けるため証拠側を書き換えれば proof chain が偽装される。
- **(P2)** 本 wave の実装対象は **(i) タスク別 policy file の所在規約、(ii) 索引 1 つ、
  (iii) 索引の機械検査**に限る。既存 live 読み手の付け替え (特に T-126 identity path からの
  policy.json 除去) は **本 wave では行わない** — series identity の preimage 集合変更は受理集合の
  変更で D96 手続を要する。scope 外 real 所見として裁定パッケージへ返す。
  実装しない場合の成果物影響: 索引が無いままだと per-task file が増えたとき「この run を支配した
  予約設定」の再導出先が台帳から辿れず、D107 決定 2 の identity 連鎖が人手依存になる。
- **(P3)** 索引は docs 単独ではなく**機械検査可能な registry** とする (docs だけの索引は腐る)。
  実装しない場合の成果物影響: 未登録の per-task file が生まれても検査が沈黙し、レポートの
  「支配した設定」列挙が実体と乖離する。
- **(P4)** 純増検出力は **未登録 per-task policy file の存在 / 索引 entry の path 不在・untracked**
  だけである。policy.json の byte drift 自体は既存 2 node が既に被覆済みで、**純増ゼロ**。
  新テストで既存被覆を重複させない。

## 不変条件

- `tools/pegasus/policy.json` の bytes、`output/env/pegasus/silo_ladder_rung1/**` の bytes は不変。
- 既存テストの受理集合を拡大も縮小もしない。既存 2 node の赤条件は保つ。
- production 挙動・実験の受理集合・certified 選択・proof chain は変更しない (D107 と同じ射程)。
- `orchestrator/qualification/t126_reservation_policy_v1.json` の内容は不変 (場所も動かさない)。

## 成果物の形

- 索引 file 1 つ (registry) + それを検査する pytest node + 既存正本への短い追記。
- docs: worklog、decisions (D 追加)、insights (逐語・変異台帳)。

## 並列分割方針

実装面は Codex `role=author` 1 単位 (registry + test) を想定。docs は親。
設計択一が割れ、正しさ防壁 (凍結証拠 binding) に隣接するため**軽量版は採らない** —
段 2 プラン起草、段 3 敵対相談 2 本、段 6 敵対レビュー 2 本を行う (`DW-C00`)。
